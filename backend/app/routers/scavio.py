"""
Rotas administrativas da integração Scavio Amazon API.

- GET  /admin/scavio/status  → status da integração (nunca expõe a API Key)
- POST /admin/scavio/search  → pesquisa produtos Amazon (nome, palavra-chave,
                               ASIN ou URL) e retorna dados normalizados + link de afiliado.

Nenhuma rota é pública; todas exigem autenticação administrativa.
Nenhuma chamada à Scavio ocorre na inicialização ou em background.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.database import get_db
from backend.app.models.models import Admin
from backend.app.schemas.schemas import (
    ScavioSearchRequest, ScavioSearchResponse, ScavioStatusResponse,
    ScavioSyncLoteRequest, ScavioSyncLoteResponse, ScavioSyncItemResult,
)
from backend.app.services.auth_service import get_current_admin
from backend.app.services import scavio_service, catalog_sync_service
from backend.app.models.models import ProdutoPrincipal, Mimo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/scavio", tags=["Scavio Amazon"])


@router.get("/status", response_model=ScavioStatusResponse)
def scavio_status(
    admin: Admin = Depends(get_current_admin),
):
    """Status da integração Scavio — sem expor a API Key."""
    info = scavio_service.scavio_status()
    return ScavioStatusResponse(
        enabled=info["enabled"],
        configured=info["configured"],
        status=info["status"],
        marketplace=settings.AMAZON_MARKETPLACE,
        associate_tag=settings.AMAZON_ASSOCIATE_TAG,
    )


@router.post("/search", response_model=ScavioSearchResponse)
async def scavio_search(
    payload: ScavioSearchRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Pesquisa produtos Amazon via Scavio.

    Aceita nome do produto, palavra-chave, ASIN ou URL da Amazon.
    ASIN/URL → detalhe do produto; texto → busca. Cada chamada custa 1 crédito
    (cache em memória evita duplicatas dentro do TTL).
    """
    result = await scavio_service.search_amazon(payload.query)
    return ScavioSearchResponse(
        products=result["products"],
        total=result["total"],
        cached=result["cached"],
        credits_remaining=result["credits_remaining"],
    )


# ==================== SINCRONIZAÇÃO DO CATÁLOGO ====================

@router.post("/sync/produto/{produto_id}", response_model=ScavioSyncItemResult)
async def sync_produto(
    produto_id: int,
    atualizar_nome: bool = False,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Sincroniza UM produto principal com a Scavio (por ASIN — 1 crédito)."""
    produto = db.query(ProdutoPrincipal).filter(ProdutoPrincipal.id == produto_id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    res = await catalog_sync_service.sync_item(db, produto, atualizar_nome=atualizar_nome)
    res["tipo"] = "produto"
    return ScavioSyncItemResult(**res)


@router.post("/sync/mimo/{mimo_id}", response_model=ScavioSyncItemResult)
async def sync_mimo(
    mimo_id: int,
    atualizar_nome: bool = False,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Sincroniza UM mimo com a Scavio (por ASIN — 1 crédito)."""
    mimo = db.query(Mimo).filter(Mimo.id == mimo_id).first()
    if not mimo:
        raise HTTPException(status_code=404, detail="Mimo não encontrado")
    res = await catalog_sync_service.sync_item(db, mimo, atualizar_nome=atualizar_nome)
    res["tipo"] = "mimo"
    return ScavioSyncItemResult(**res)


@router.post("/sync/lote", response_model=ScavioSyncLoteResponse)
async def sync_lote(
    payload: ScavioSyncLoteRequest,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """
    Sincroniza o catálogo em lote: 'produtos' | 'mimos' | 'todos'.
    1 crédito Scavio por item COM ASIN; itens sem ASIN são ignorados.
    Somente o administrador dispara — nunca automático.
    """
    if payload.tipo not in ("produtos", "mimos", "todos"):
        raise HTTPException(status_code=400, detail="tipo deve ser 'produtos', 'mimos' ou 'todos'")
    result = await catalog_sync_service.sync_lote(
        db, payload.tipo, admin, atualizar_nome=payload.atualizar_nome
    )
    return ScavioSyncLoteResponse(**result)


@router.get("/sync/status")
def sync_status(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Últimas sincronizações registradas + contadores do catálogo."""
    from backend.app.models.models import HistoricoAdmin
    logs = (
        db.query(HistoricoAdmin)
        .filter(HistoricoAdmin.acao == "SCAVIO_SYNC_LOTE")
        .order_by(HistoricoAdmin.criado_em.desc())
        .limit(10)
        .all()
    )
    total_com_asin = (
        db.query(ProdutoPrincipal).filter(ProdutoPrincipal.asin.isnot(None), ProdutoPrincipal.asin != "").count()
        + db.query(Mimo).filter(Mimo.asin.isnot(None), Mimo.asin != "").count()
    )
    return {
        "catalogo_com_asin": total_com_asin,
        "catalogo_total": db.query(ProdutoPrincipal).count() + db.query(Mimo).count(),
        "ultimas_sincronizacoes": [
            {"id": l.id, "descricao": l.descricao, "criado_em": l.criado_em.isoformat() if l.criado_em else None}
            for l in logs
        ],
    }
