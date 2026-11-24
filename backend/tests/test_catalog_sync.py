"""
Testes da sincronização do catálogo via Scavio — mocks, zero créditos.
Cobre: sync individual, lote, regras de preservação (MANUAL vs SCAVIO),
sem ASIN, produto não encontrado, erro da API, auth admin.
"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from backend.app.config import settings
from backend.app.models.models import ProdutoPrincipal, Mimo
from backend.app.services import scavio_service, catalog_sync_service


def _resp(json_body, status=200):
    req = httpx.Request("POST", "https://api.scavio.dev/api/v1/amazon/product")
    return httpx.Response(status, json=json_body, request=req)


PRODUCT_BODY = {
    "data": {
        "asin": "B07GQB93FT",
        "title": "Pampers Primeiros Dias RN Novo Nome",
        "url": "https://www.amazon.com.br/dp/B07GQB93FT",
        "description": "Descrição nova",
        "price": 45.90,
        "list_price": 60.00,
        "currency": "BRL",
        "rating": 4.9,
        "reviews_count": 500,
        "brand": "Pampers",
        "availability": "In Stock",
        "image": "https://img/nova.jpg",
    },
    "credits_remaining": 40,
}


@pytest.fixture
def scavio_on(monkeypatch):
    monkeypatch.setattr(settings, "SCAVIO_ENABLED", True)
    monkeypatch.setattr(settings, "SCAVIO_API_KEY", "sk_test_fake")
    monkeypatch.setattr(settings, "SCAVIO_CACHE_TTL_SECONDS", 0)
    scavio_service._search_cache.clear()
    yield
    scavio_service._search_cache.clear()


def _patch_client(resp=None, exc=None):
    mock_post = AsyncMock(return_value=resp) if exc is None else AsyncMock(side_effect=exc)
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.post = mock_post
    return patch("httpx.AsyncClient", return_value=client)


class TestSyncItem:
    @pytest.mark.asyncio
    async def test_atualiza_preco_e_imagem(self, db_session, scavio_on):
        prod = ProdutoPrincipal(
            nome="Fralda X", asin="B07GQB93FT", categoria="Fraldas",
            preco_atual=39.98, imagem_url="https://img/velha.jpg",
            quantidade_desejada=5, ativo=True,
        )
        db_session.add(prod)
        db_session.commit()
        db_session.refresh(prod)

        with _patch_client(resp=_resp(PRODUCT_BODY)):
            res = await catalog_sync_service.sync_item(db_session, prod)

        db_session.refresh(prod)
        assert res["status"] == "sincronizado"
        assert float(prod.preco_atual) == 45.90
        assert prod.imagem_url == "https://img/nova.jpg"
        assert prod.preco_origem == "SCAVIO"
        assert prod.imagem_origem == "SCAVIO"
        assert prod.preco_sincronizado_em is not None
        # Nome NÃO sobrescrito (já preenchido, atualizar_nome=False)
        assert prod.nome == "Fralda X"
        # URL ganhou tag de afiliado
        assert "tag=projetolael-20" in (prod.produto_url or "")

    @pytest.mark.asyncio
    async def test_preserva_origem_manual(self, db_session, scavio_on):
        prod = ProdutoPrincipal(
            nome="Fralda Manual", asin="B07GQB93FT", categoria="Fraldas",
            preco_atual=10.00, imagem_url="https://img/manual.jpg",
            preco_origem="MANUAL", imagem_origem="MANUAL",
            quantidade_desejada=5, ativo=True,
        )
        db_session.add(prod)
        db_session.commit()
        db_session.refresh(prod)

        with _patch_client(resp=_resp(PRODUCT_BODY)):
            res = await catalog_sync_service.sync_item(db_session, prod)

        db_session.refresh(prod)
        assert float(prod.preco_atual) == 10.00  # preservado
        assert prod.imagem_url == "https://img/manual.jpg"  # preservada
        assert prod.preco_origem == "MANUAL"

    @pytest.mark.asyncio
    async def test_sem_asin_nao_gasta_credito(self, db_session, scavio_on):
        mimo = Mimo(nome="Mimo sem ASIN", categoria="Teste", quantidade_desejada=1, ativo=True)
        db_session.add(mimo)
        db_session.commit()
        db_session.refresh(mimo)
        with _patch_client(resp=_resp(PRODUCT_BODY)) as patcher:
            with patcher:
                res = await catalog_sync_service.sync_item(db_session, mimo)
        assert res["status"] == "sem_asin"

    @pytest.mark.asyncio
    async def test_nao_encontrado(self, db_session, scavio_on):
        prod = ProdutoPrincipal(
            nome="Fralda Y", asin="B000000000", categoria="Fraldas",
            quantidade_desejada=5, ativo=True,
        )
        db_session.add(prod)
        db_session.commit()
        db_session.refresh(prod)
        with _patch_client(resp=_resp({"data": {}})):
            res = await catalog_sync_service.sync_item(db_session, prod)
        assert res["status"] == "nao_encontrado"

    @pytest.mark.asyncio
    async def test_erro_api_reportado(self, db_session, scavio_on):
        prod = ProdutoPrincipal(
            nome="Fralda Z", asin="B07GQB93FT", categoria="Fraldas",
            quantidade_desejada=5, ativo=True,
        )
        db_session.add(prod)
        db_session.commit()
        db_session.refresh(prod)
        with _patch_client(resp=_resp({"error": "x"}, status=500)):
            res = await catalog_sync_service.sync_item(db_session, prod)
        assert res["status"] == "erro"
        assert res["erro"]


class TestSyncLoteEEndpoints:
    @pytest.mark.asyncio
    async def test_lote_produtos(self, client, db_session, admin_headers, scavio_on):
        # Produto com ASIN do seed de teste (fraldas RN tem ASIN real)
        with _patch_client(resp=_resp(PRODUCT_BODY)):
            r = client.post("/api/admin/scavio/sync/lote", json={"tipo": "produtos"}, headers=admin_headers)
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total"] >= 1
        assert "sincronizados" in data
        # HistoricoAdmin registrado
        assert db_session.query(__import__("backend.app.models.models", fromlist=["HistoricoAdmin"]).HistoricoAdmin).filter_by(acao="SCAVIO_SYNC_LOTE").count() >= 1

    def test_lote_exige_admin(self, client):
        assert client.post("/api/admin/scavio/sync/lote", json={"tipo": "todos"}).status_code == 401
        assert client.post("/api/admin/scavio/sync/produto/1").status_code == 401
        assert client.get("/api/admin/scavio/sync/status").status_code == 401

    def test_sync_individual_endpoint(self, client, db_session, admin_headers, scavio_on):
        prod = db_session.query(ProdutoPrincipal).first()
        prod.asin = "B07GQB93FT"
        db_session.commit()
        with _patch_client(resp=_resp(PRODUCT_BODY)):
            r = client.post(f"/api/admin/scavio/sync/produto/{prod.id}", headers=admin_headers)
        assert r.status_code == 200, r.text
        assert r.json()["status"] in ("sincronizado", "sem_alteracoes")
