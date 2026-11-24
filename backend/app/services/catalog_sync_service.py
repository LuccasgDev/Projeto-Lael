"""
Sincronização do catálogo (produtos principais e mimos) com a Scavio Amazon API.

Regras de atualização (nunca sobrescreve dado válido com nulo/vazio):
- preço/imagem: atualiza quando a API retorna valor válido; marca origem 'SCAVIO'.
- preço/imagem com origem 'MANUAL': preservados (o admin assumiu o controle).
- nome: só atualiza se o atual estiver vazio OU se `atualizar_nome=True`.
- ASIN/URL: preenche quando vazio; URL recebe link de afiliado quando ainda não
  possui tag= ou quando está vazia.
- descrição: só preenche se vazia.
- NUNCA toca em quantidades, reservas, números ou status ativo.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.models import ProdutoPrincipal, Mimo, HistoricoAdmin, Admin, utcnow
from backend.app.services import scavio_service

logger = logging.getLogger(__name__)


def _dec(v) -> Optional[Decimal]:
    try:
        return Decimal(str(round(float(v), 2))) if v is not None else None
    except (TypeError, ValueError):
        return None


def _apply_sync(item, data: dict, atualizar_nome: bool = False) -> list[str]:
    """Aplica os dados normalizados da Scavio ao produto/mimo. Retorna campos alterados."""
    alterados = []

    # Preço — respeita origem MANUAL
    novo_preco = _dec(data.get("preco"))
    if novo_preco is not None and novo_preco > 0 and getattr(item, "preco_origem", "SCAVIO") != "MANUAL":
        if item.preco_atual != novo_preco:
            item.preco_atual = novo_preco
            alterados.append("preco_atual")
        item.preco_anterior = _dec(data.get("preco_anterior")) or item.preco_anterior
        item.preco_sincronizado_em = utcnow()
        item.preco_origem = "SCAVIO"
        if "preco_atual" not in alterados and novo_preco == item.preco_atual:
            pass
    elif novo_preco is not None and novo_preco > 0:
        alterados.append("preco_bloqueado_manual")

    # Imagem — respeita origem MANUAL
    nova_img = data.get("imagem_url")
    if nova_img and str(nova_img).startswith("http") and getattr(item, "imagem_origem", "SCAVIO") != "MANUAL":
        if item.imagem_url != nova_img:
            item.imagem_url = nova_img
            alterados.append("imagem_url")
        item.imagem_origem = "SCAVIO"
    elif nova_img and getattr(item, "imagem_origem", "MANUAL") == "MANUAL":
        alterados.append("imagem_bloqueada_manual")

    # Nome — só se vazio ou autorizado
    novo_nome = (data.get("nome") or "").strip()
    if novo_nome and (not item.nome or atualizar_nome):
        if item.nome != novo_nome:
            item.nome = novo_nome[:255]
            alterados.append("nome")

    # ASIN — confirma/preenche
    novo_asin = (data.get("asin") or "").strip().upper()
    if novo_asin and (not item.asin or item.asin.upper() != novo_asin):
        item.asin = novo_asin[:20]
        alterados.append("asin")

    # URL — link de afiliado quando vazia ou sem tag
    nova_url = data.get("link_afiliado") or data.get("url")
    if nova_url and str(nova_url).startswith("http"):
        atual = item.produto_url or ""
        if not atual or "tag=" not in atual:
            item.produto_url = nova_url[:1000]
            alterados.append("produto_url")

    # Descrição — só se vazia
    nova_desc = data.get("descricao")
    if nova_desc and not item.descricao:
        item.descricao = str(nova_desc)[:4000]
        alterados.append("descricao")

    return alterados


async def sync_item(db: Session, item, atualizar_nome: bool = False) -> dict:
    """Sincroniza UM produto/mimo com a Scavio (por ASIN)."""
    asin = (getattr(item, "asin", None) or "").strip()
    if not asin:
        return {"id": item.id, "asin": None, "status": "sem_asin", "alterados": []}

    try:
        data = await scavio_service.fetch_amazon_product_by_asin(asin)
    except Exception as e:
        detail = getattr(e, "detail", str(e))
        logger.warning(f"[SCAVIO-SYNC] falha ASIN {asin}: {detail}")
        return {"id": item.id, "asin": asin, "status": "erro", "erro": str(detail), "alterados": []}

    if not data:
        return {"id": item.id, "asin": asin, "status": "nao_encontrado", "alterados": []}

    alterados = _apply_sync(item, data, atualizar_nome=atualizar_nome)
    db.commit()
    return {
        "id": item.id,
        "asin": asin,
        "status": "sincronizado" if alterados else "sem_alteracoes",
        "alterados": alterados,
        "preco": float(item.preco_atual) if item.preco_atual is not None else None,
        "disponivel": data.get("disponivel"),
    }


async def sync_lote(db: Session, tipo: str, admin: Admin, atualizar_nome: bool = False) -> dict:
    """
    Sincroniza o catálogo: tipo = 'produtos' | 'mimos' | 'todos'.
    Somente itens COM ASIN são consultados (1 crédito cada); itens sem ASIN
    são reportados como 'sem_asin' sem gastar créditos.
    """
    resultados = []
    itens = []
    if tipo in ("produtos", "todos"):
        itens += [("produto", p) for p in db.query(ProdutoPrincipal).all()]
    if tipo in ("mimos", "todos"):
        itens += [("mimo", m) for m in db.query(Mimo).all()]

    for _kind, item in itens:
        res = await sync_item(db, item, atualizar_nome=atualizar_nome)
        res["tipo"] = _kind
        resultados.append(res)

    ok = sum(1 for r in resultados if r["status"] == "sincronizado")
    alterados = sum(1 for r in resultados if r["status"] in ("sincronizado", "sem_alteracoes"))
    db.add(HistoricoAdmin(
        administrador_id=admin.id,
        acao="SCAVIO_SYNC_LOTE",
        descricao=(
            f"Sincronização Scavio ({tipo}): {len(resultados)} itens avaliados, "
            f"{ok} atualizados, {alterados - ok} sem alterações, "
            f"{sum(1 for r in resultados if r['status'] == 'sem_asin')} sem ASIN, "
            f"{sum(1 for r in resultados if r['status'] == 'erro')} com erro."
        ),
        criado_em=utcnow(),
    ))
    db.commit()

    return {
        "tipo": tipo,
        "total": len(resultados),
        "sincronizados": ok,
        "sem_alteracoes": alterados - ok,
        "sem_asin": sum(1 for r in resultados if r["status"] == "sem_asin"),
        "erros": sum(1 for r in resultados if r["status"] == "erro"),
        "itens": resultados,
    }
