"""
Testes da integração Scavio Amazon API — SEM créditos reais.
O httpx.AsyncClient é mockado; nenhum request sai da máquina de teste.
Cobre: desativada, sem key, busca válida, ASIN/URL→detalhe, vazio,
401/403/429/5xx, timeout, JSON inválido, normalização, afiliado, auth admin.
"""
import pytest
from unittest.mock import AsyncMock, patch
import httpx

from backend.app.config import settings
from backend.app.services import scavio_service


# ---------- helpers ----------

def _mock_response(status=200, json_body=None, text=""):
    req = httpx.Request("POST", "https://api.scavio.dev/api/v1/amazon/search")
    return httpx.Response(status, json=json_body, request=req) if json_body is not None else httpx.Response(status, text=text, request=req)


def _patch_client(resp=None, exc=None):
    """Retorna patch de httpx.AsyncClient.post → resp ou exc."""
    mock_post = AsyncMock(return_value=resp) if exc is None else AsyncMock(side_effect=exc)
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    client.post = mock_post
    return patch("httpx.AsyncClient", return_value=client), mock_post


@pytest.fixture
def scavio_on(monkeypatch):
    monkeypatch.setattr(settings, "SCAVIO_ENABLED", True)
    monkeypatch.setattr(settings, "SCAVIO_API_KEY", "sk_test_fake")
    monkeypatch.setattr(settings, "SCAVIO_CACHE_TTL_SECONDS", 0)  # desliga cache entre testes
    scavio_service._search_cache.clear()
    yield
    scavio_service._search_cache.clear()


SEARCH_BODY = {
    "data": {
        "query": "fralda pampers",
        "products": [
            {
                "asin": "B07GQB93FT",
                "title": "Pampers Primeiros Dias RN, 36 un",
                "url": "https://www.amazon.com.br/dp/B07GQB93FT",
                "image": "https://img/1.jpg",
                "price": 39.98,
                "list_price": 52.83,
                "currency": "BRL",
                "rating": 4.8,
                "reviews_count": 1234,
                "brand": "Pampers",
            }
        ],
    },
    "credits_remaining": 49,
}

PRODUCT_BODY = {
    "data": {
        "asin": "B07GQB93FT",
        "title": "Pampers Primeiros Dias RN, 36 un",
        "url": "https://www.amazon.com.br/dp/B07GQB93FT",
        "description": "Fralda para recém-nascidos.",
        "features": ["Hipoalergênica"],
        "price": 39.98,
        "list_price": 52.83,
        "currency": "BRL",
        "rating": 4.8,
        "reviews_count": 1234,
        "brand": "Pampers",
        "availability": "In Stock",
        "image": "https://img/1.jpg",
    },
    "credits_remaining": 48,
}


# ---------- status / configuração ----------

def test_desativada_sem_key(monkeypatch):
    monkeypatch.setattr(settings, "SCAVIO_ENABLED", False)
    assert scavio_service.scavio_status()["status"] == "desativada"


def test_sem_api_key(monkeypatch):
    monkeypatch.setattr(settings, "SCAVIO_ENABLED", True)
    monkeypatch.setattr(settings, "SCAVIO_API_KEY", "")
    st = scavio_service.scavio_status()
    assert st["status"] == "sem_api_key"
    assert st["configured"] is False


def test_status_endpoint_admin(client, db_session, admin_headers, monkeypatch):
    monkeypatch.setattr(settings, "SCAVIO_ENABLED", False)
    r = client.get("/api/admin/scavio/status", headers=admin_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "desativada"
    assert "api_key" not in str(data).lower() or "SCAVIO_API_KEY" not in data.get("status", "")
    # Nunca retorna a chave
    assert "sk_" not in str(data)


def test_status_exige_admin(client):
    assert client.get("/api/admin/scavio/status").status_code == 401
    assert client.post("/api/admin/scavio/search", json={"query": "x"}).status_code == 401


# ---------- busca ----------

@pytest.mark.asyncio
async def test_busca_valida_normaliza(scavio_on):
    patcher, mock_post = _patch_client(resp=_mock_response(200, SEARCH_BODY))
    with patcher:
        res = await scavio_service.search_amazon("fralda pampers")
    assert res["total"] == 1
    p = res["products"][0]
    assert p["asin"] == "B07GQB93FT"
    assert p["nome"].startswith("Pampers")
    assert p["preco"] == 39.98
    assert p["preco_anterior"] == 52.83
    assert p["avaliacao"] == 4.8
    assert p["total_avaliacoes"] == 1234
    # link de afiliado com a tag configurada
    assert "tag=projetolael-20" in p["link_afiliado"]
    # verificou autenticação Bearer (e nunca vaza a key na URL)
    call = mock_post.call_args
    assert call.kwargs["headers"]["Authorization"] == "Bearer sk_test_fake"
    assert "sk_test_fake" not in call.args[0]


@pytest.mark.asyncio
async def test_busca_vazia(scavio_on):
    patcher, _ = _patch_client(resp=_mock_response(200, {"data": {"products": []}, "credits_remaining": 49}))
    with patcher:
        res = await scavio_service.search_amazon("produto inexistente xyz")
    assert res["total"] == 0
    assert res["products"] == []


@pytest.mark.asyncio
async def test_asin_usa_endpoint_de_detalhe(scavio_on):
    patcher, mock_post = _patch_client(resp=_mock_response(200, PRODUCT_BODY))
    with patcher:
        res = await scavio_service.search_amazon("B07GQB93FT")
    assert res["total"] == 1
    # endpoint de produto (detalhe), não de busca
    assert "/amazon/product" in mock_post.call_args.args[0]
    p = res["products"][0]
    assert p["origem"] == "product"
    assert p["descricao"] == "Fralda para recém-nascidos."


@pytest.mark.asyncio
async def test_url_amazon_extrai_asin(scavio_on):
    patcher, mock_post = _patch_client(resp=_mock_response(200, PRODUCT_BODY))
    with patcher:
        res = await scavio_service.search_amazon("https://www.amazon.com.br/dp/B07GQB93FT?th=1")
    assert res["total"] == 1
    assert "/amazon/product" in mock_post.call_args.args[0]
    assert mock_post.call_args.kwargs["json"]["asin"] == "B07GQB93FT"


@pytest.mark.asyncio
async def test_erro_401(scavio_on):
    patcher, _ = _patch_client(resp=_mock_response(401, {"error": "unauthorized"}))
    with patcher:
        with pytest.raises(Exception) as e:
            await scavio_service.search_amazon("fralda")
    assert "autenticação" in str(e.value.detail).lower()


@pytest.mark.asyncio
async def test_erro_429(scavio_on):
    patcher, _ = _patch_client(resp=_mock_response(429, {}))
    with patcher:
        with pytest.raises(Exception) as e:
            await scavio_service.search_amazon("fralda")
    assert e.value.status_code == 429


@pytest.mark.asyncio
async def test_erro_500(scavio_on):
    patcher, _ = _patch_client(resp=_mock_response(500, {}))
    with patcher:
        with pytest.raises(Exception) as e:
            await scavio_service.search_amazon("fralda")
    assert "temporário" in str(e.value.detail).lower() or e.value.status_code == 502


@pytest.mark.asyncio
async def test_timeout(scavio_on):
    patcher, _ = _patch_client(exc=httpx.TimeoutException("timeout"))
    with patcher:
        with pytest.raises(Exception) as e:
            await scavio_service.search_amazon("fralda")
    assert e.value.status_code == 504


@pytest.mark.asyncio
async def test_json_invalido(scavio_on):
    req = httpx.Request("POST", "https://api.scavio.dev/x")
    resp = httpx.Response(200, content=b"not json", request=req)
    patcher, _ = _patch_client(resp=resp)
    with patcher:
        with pytest.raises(Exception) as e:
            await scavio_service.search_amazon("fralda")
    assert "JSON" in str(e.value.detail) or "inválid" in str(e.value.detail).lower()


@pytest.mark.asyncio
async def test_query_invalida(scavio_on):
    with pytest.raises(Exception) as e:
        await scavio_service.search_amazon("   ")
    assert e.value.status_code == 400
    with pytest.raises(Exception):
        await scavio_service.search_amazon("x" * 600)


# ---------- cache ----------

@pytest.mark.asyncio
async def test_cache_evita_duplicata(scavio_on, monkeypatch):
    monkeypatch.setattr(settings, "SCAVIO_CACHE_TTL_SECONDS", 300)
    patcher, mock_post = _patch_client(resp=_mock_response(200, SEARCH_BODY))
    with patcher:
        r1 = await scavio_service.search_amazon("fralda pampers")
        r2 = await scavio_service.search_amazon("fralda pampers")
    assert r1["cached"] is False
    assert r2["cached"] is True
    assert mock_post.call_count == 1  # só 1 crédito gasto


# ---------- link afiliado ----------

def test_affiliate_tag_basica():
    url = scavio_service.add_affiliate_tag("https://www.amazon.com.br/dp/B07GQB93FT")
    assert "tag=projetolael-20" in url


def test_affiliate_tag_preserva_params_e_nao_duplica():
    url = scavio_service.add_affiliate_tag(
        "https://www.amazon.com.br/dp/B07GQB93FT?th=1&tag=outra-20"
    )
    assert url.count("tag=") == 1
    assert "tag=projetolael-20" in url
    assert "th=1" in url


def test_affiliate_tag_url_invalida_nao_quebra():
    assert scavio_service.add_affiliate_tag(None) is None
    assert scavio_service.add_affiliate_tag("nao-e-url") == "nao-e-url"
