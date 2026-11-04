import csv
import io
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from backend.app.database import get_db
from backend.app.models.models import Admin, ProdutoPrincipal, Mimo
from backend.app.services.auth_service import get_current_admin
from backend.app.services.amazon_service import (
    TALIA_REGISTRY_URL, LUCAS_REGISTRY_URL,
    check_amazon_registry_accessibility,
    import_products_from_dict_list
)

router = APIRouter(prefix="/sync", tags=["Sincronização Amazon"])


@router.get("/status")
async def get_sync_status(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Returns current sync diagnostics, last update timestamps and Amazon accessibility.
    """
    last_produto = db.query(ProdutoPrincipal).order_by(ProdutoPrincipal.preco_sincronizado_em.desc()).first()
    last_mimo = db.query(Mimo).order_by(Mimo.preco_sincronizado_em.desc()).first()

    return {
        "urls_configuradas": {
            "talia_presentes_principais": TALIA_REGISTRY_URL,
            "lucas_mimos": LUCAS_REGISTRY_URL,
        },
        "ultima_sincronizacao_produtos": last_produto.preco_sincronizado_em.isoformat() if last_produto and last_produto.preco_sincronizado_em else None,
        "ultima_sincronizacao_mimos": last_mimo.preco_sincronizado_em.isoformat() if last_mimo and last_mimo.preco_sincronizado_em else None,
        "metodos_disponiveis": [
            "Importação JSON estruturada",
            "Importação de planilha CSV",
            "Atualização manual de preços no painel",
            "Sonda de conectividade de rede com a Amazon"
        ]
    }


@router.post("/probe-amazon")
async def probe_amazon_registry(
    lista: str = Query("talia", regex="^(talia|lucas)$"),
    admin: Admin = Depends(get_current_admin)
):
    """
    Performs a real HTTP probe on the Amazon registry URL to check if Amazon WAF is blocking.
    """
    url = TALIA_REGISTRY_URL if lista == "talia" else LUCAS_REGISTRY_URL
    result = await check_amazon_registry_accessibility(url)

    return {
        "lista": lista,
        "url": url,
        "sucesso": result.success,
        "mensagem": result.message,
        "produtos_encontrados": result.products_found,
        "diagnostico": result.diagnostics,
    }


@router.post("/import-json")
def import_json_endpoint(
    payload: List[Dict[str, Any]],
    tipo: str = Query("principal", regex="^(principal|mimo)$"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Imports or updates products from a JSON payload.
    """
    res = import_products_from_dict_list(db, payload, target_type=tipo, admin=admin)
    return res


@router.post("/import-csv")
async def import_csv_endpoint(
    file: UploadFile = File(...),
    tipo: str = Query("principal", regex="^(principal|mimo)$"),
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin)
):
    """
    Imports or updates products from an uploaded CSV file.
    """
    contents = await file.read()
    decoded = contents.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded), delimiter=";" if ";" in decoded else ",")

    items = []
    for row in reader:
        items.append({
            "asin": row.get("asin") or row.get("ASIN"),
            "nome": row.get("nome") or row.get("Nome") or row.get("title") or row.get("Title"),
            "preco_atual": row.get("preco_atual") or row.get("Preco") or row.get("price") or 0.0,
            "preco_anterior": row.get("preco_anterior") or row.get("Preco Anterior"),
            "imagem_url": row.get("imagem_url") or row.get("Imagem") or row.get("image"),
            "produto_url": row.get("produto_url") or row.get("Link") or row.get("url"),
            "categoria": row.get("categoria") or row.get("Categoria"),
            "descricao": row.get("descricao") or row.get("Descricao"),
            "quantidade_desejada": row.get("quantidade_desejada") or row.get("Quantidade") or 1,
            "quantidade_comprada_externa": row.get("quantidade_comprada_externa") or row.get("Comprada Externa") or 0,
        })

    res = import_products_from_dict_list(db, items, target_type=tipo, admin=admin)
    return res
