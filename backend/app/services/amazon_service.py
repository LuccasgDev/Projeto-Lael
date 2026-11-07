import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from backend.app.models.models import ProdutoPrincipal, Mimo, HistoricoAdmin, Admin, utcnow

logger = logging.getLogger(__name__)

TALIA_REGISTRY_URL = "https://www.amazon.com.br/baby-reg/taliavitria-nascimento-maro-2027-fortaleza/10NOCBS3PDNDW"
LUCAS_REGISTRY_URL = "https://www.amazon.com.br/baby-reg/lucas-gabriel-maro-2027-fortaleza/24ZYPSUDF4A94"


class AmazonSyncResult:
    def __init__(self, success: bool, message: str, products_found: int = 0, diagnostics: Optional[Dict[str, Any]] = None):
        self.success = success
        self.message = message
        self.products_found = products_found
        self.diagnostics = diagnostics or {}


async def check_amazon_registry_accessibility(url: str) -> AmazonSyncResult:
    """
    Investigates and probes the Amazon registry URL.
    Identifies anti-bot protection (WAF / Captcha / Dog page).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            status_code = resp.status_code
            content = resp.text

            is_dog_page = "images-na.ssl-images-amazon.com/images/G/32/error" in content or "errors/500.html" in content
            is_captcha = "validateCaptcha" in content or "Robot Check" in content or "Digite os caracteres que você vê" in content

            if is_dog_page or is_captcha or status_code in [403, 503]:
                return AmazonSyncResult(
                    success=False,
                    message="A Amazon Brasil ativou o bloqueio anti-bot (WAF/CAPTCHA). O acesso direto via web scraping automático foi restringido pela Amazon.",
                    diagnostics={
                        "status_code": status_code,
                        "bloqueio_waf": True,
                        "motivo": "CAPTCHA / Amazon WAF Bot Detection",
                        "recomendacao": "Utilize a importação por JSON/CSV ou atualização direta pelo painel administrativo."
                    }
                )

            # If page loaded normally, parse products if HTML structure is present
            soup = BeautifulSoup(content, "html.parser")
            items = soup.find_all("div", attrs={"data-asin": True})
            return AmazonSyncResult(
                success=True,
                message=f"Página acessada com sucesso. Encontrados {len(items)} itens estruturados.",
                products_found=len(items),
                diagnostics={"status_code": status_code, "bloqueio_waf": False}
            )

    except Exception as e:
        logger.error(f"[AMAZON_SYNC] Erro na consulta de rede: {e}")
        return AmazonSyncResult(
            success=False,
            message=f"Erro de conexão com os servidores da Amazon: {str(e)}",
            diagnostics={"erro": str(e)}
        )


def import_products_from_dict_list(
    db: Session,
    items: List[Dict[str, Any]],
    target_type: str = "principal",  # 'principal' ou 'mimo'
    admin: Optional[Admin] = None
) -> Dict[str, Any]:
    """
    Imports or updates products from a list of dictionaries (JSON/CSV parsed).
    Supports all standard Amazon product attributes.
    """
    created_count = 0
    updated_count = 0
    agora = utcnow()

    ModelClass = ProdutoPrincipal if target_type == "principal" else Mimo

    for item in items:
        asin = item.get("asin")
        nome = item.get("nome") or item.get("title")
        if not nome:
            continue

        preco_raw = item.get("preco_atual") or item.get("price")
        preco = float(preco_raw) if preco_raw not in (None, "", 0, "0") else None
        preco_anterior = item.get("preco_anterior")
        if preco_anterior:
            preco_anterior = float(preco_anterior)

        imagem_url = item.get("imagem_url") or item.get("image")
        produto_url = item.get("produto_url") or item.get("url") or (f"https://www.amazon.com.br/dp/{asin}" if asin else None)
        categoria = item.get("categoria") or item.get("category")
        descricao = item.get("descricao") or item.get("description")
        quantidade_desejada = int(item.get("quantidade_desejada") or item.get("quantity") or 1)
        quantidade_comprada = int(item.get("quantidade_comprada_externa") or item.get("purchased") or 0)

        existing = None
        if asin:
            existing = db.query(ModelClass).filter(ModelClass.asin == asin).first()
        if not existing:
            existing = db.query(ModelClass).filter(ModelClass.nome == nome).first()

        if existing:
            existing.nome = nome
            if preco is not None:
                existing.preco_atual = preco
            if preco_anterior:
                existing.preco_anterior = preco_anterior
            if imagem_url:
                existing.imagem_url = imagem_url
            if produto_url:
                existing.produto_url = produto_url
            if categoria:
                existing.categoria = categoria
            if descricao:
                existing.descricao = descricao
            existing.quantidade_desejada = quantidade_desejada
            existing.quantidade_comprada_externa = quantidade_comprada
            existing.preco_sincronizado_em = agora
            updated_count += 1
        else:
            new_item = ModelClass(
                asin=asin,
                nome=nome,
                descricao=descricao,
                imagem_url=imagem_url,
                produto_url=produto_url,
                categoria=categoria,
                preco_atual=preco,
                preco_anterior=preco_anterior,
                preco_sincronizado_em=agora,
                quantidade_desejada=quantidade_desejada,
                quantidade_comprada_externa=quantidade_comprada,
                ativo=True,
                criado_em=agora,
            )
            db.add(new_item)
            created_count += 1

    admin_nome = admin.nome if admin else "Sistema/Sincronização"
    historico = HistoricoAdmin(
        administrador_id=admin.id if admin else None,
        acao=f"IMPORTACAO_{target_type.upper()}",
        descricao=f"Importação de {target_type}s realizada por {admin_nome}. {created_count} criados, {updated_count} atualizados.",
        criado_em=agora,
    )
    db.add(historico)
    db.commit()

    return {
        "tipo": target_type,
        "criados": created_count,
        "atualizados": updated_count,
        "total_processados": created_count + updated_count,
        "data_sincronizacao": agora.isoformat(),
    }


def manual_update_price(
    db: Session,
    item_id: int,
    target_type: str,
    novo_preco: float,
    admin: Admin
) -> Any:
    """
    Manually updates the price of a product or mimo and stamps the sync date.
    """
    ModelClass = ProdutoPrincipal if target_type == "principal" else Mimo
    item = db.query(ModelClass).filter(ModelClass.id == item_id).first()
    if not item:
        raise ValueError(f"{target_type.capitalize()} não encontrado.")

    agora = utcnow()
    preco_antigo = item.preco_atual
    item.preco_anterior = preco_antigo
    item.preco_atual = round(float(novo_preco), 2)
    item.preco_sincronizado_em = agora

    historico = HistoricoAdmin(
        administrador_id=admin.id,
        acao=f"PRECO_ATUALIZADO_{target_type.upper()}",
        descricao=f"Preço de '{item.nome}' atualizado de R$ {preco_antigo:.2f} para R$ {item.preco_atual:.2f} por {admin.nome}.",
        criado_em=agora,
    )
    db.add(historico)
    db.commit()
    db.refresh(item)
    return item
