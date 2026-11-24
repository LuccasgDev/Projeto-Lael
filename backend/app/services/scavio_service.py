"""
Serviço de integração com a Scavio Amazon API.

Documentação oficial: https://scavio.dev/docs/amazon-api e /docs/amazon-product

- Busca de produtos: POST {SCAVIO_BASE_URL}/api/v1/amazon/search
  Body: {"query": "...", "country": "br"} — 1 crédito por requisição.
- Detalhe por ASIN: POST {SCAVIO_BASE_URL}/api/v1/amazon/product
  Body: {"asin": "...", "country": "br"} — aceita também "query" como alias.
- Autenticação: header `Authorization: Bearer <SCAVIO_API_KEY>`.

Regras de segurança:
- A API Key nunca aparece em logs, respostas ou frontend.
- Nenhuma chamada é feita na inicialização do app nem em background —
  somente mediante solicitação explícita do administrador.
- Cache em memória (TTL curto) evita créditos duplicados em pesquisas idênticas.
- Não há scraping, CAPTCHA ou contorno de proteções da Amazon.
"""
import re
import time
import logging
from typing import Optional

import httpx
from fastapi import HTTPException, status

from backend.app.config import settings

logger = logging.getLogger(__name__)

ASIN_PATTERN = re.compile(r"^[A-Z0-9]{10}$")
AMAZON_URL_ASIN_PATTERN = re.compile(r"/(?:dp|gp/product|product)/([A-Z0-9]{10})", re.IGNORECASE)
MAX_QUERY_LEN = 500

# Cache em memória simples: chave -> (timestamp, resultado_normalizado)
_search_cache: dict[str, tuple[float, list]] = {}


def scavio_status() -> dict:
    """Status da integração SEM expor a API Key."""
    if not settings.SCAVIO_ENABLED:
        return {"enabled": False, "configured": False, "status": "desativada"}
    if not settings.SCAVIO_API_KEY:
        return {"enabled": True, "configured": False, "status": "sem_api_key"}
    return {"enabled": True, "configured": True, "status": "configurada"}


def _extract_asin(query: str) -> Optional[str]:
    """Detecta ASIN puro ou ASIN embutido em URL da Amazon (suporte a /dp/, /gp/product)."""
    q = query.strip()
    if ASIN_PATTERN.match(q):
        return q.upper()
    m = AMAZON_URL_ASIN_PATTERN.search(q)
    if m:
        return m.group(1).upper()
    return None


def add_affiliate_tag(url: Optional[str], tag: Optional[str] = None) -> Optional[str]:
    """
    Gera o link de afiliado adicionando `tag=<associate_tag>` à URL da Amazon,
    preservando parâmetros existentes e sem duplicar a tag.
    """
    if not url or not (tag or settings.AMAZON_ASSOCIATE_TAG):
        return url
    tag = tag or settings.AMAZON_ASSOCIATE_TAG
    try:
        from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
        parts = urlparse(url)
        if not parts.scheme or not parts.netloc:
            return url  # URL inválida/relativa: não altera
        params = parse_qsl(parts.query, keep_blank_values=True)
        # Remove tag existente para não duplicar
        params = [(k, v) for k, v in params if k.lower() != "tag"]
        params.append(("tag", tag))
        new_query = urlencode(params)
        return urlunparse(parts._replace(query=new_query))
    except Exception:
        return url


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.SCAVIO_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _map_status_error(status_code: int) -> HTTPException:
    """Traduz códigos HTTP da Scavio em mensagens seguras (sem vazar a key)."""
    if status_code == 401:
        return HTTPException(status_code=502, detail="Scavio: autenticação inválida (verifique SCAVIO_API_KEY).")
    if status_code == 403:
        return HTTPException(status_code=502, detail="Scavio: acesso negado à API (verifique a chave/plano).")
    if status_code == 429:
        return HTTPException(status_code=429, detail="Scavio: limite de requisições atingido. Aguarde e tente novamente.")
    if status_code >= 500:
        return HTTPException(status_code=502, detail="Scavio: erro temporário no serviço. Tente novamente em instantes.")
    return HTTPException(status_code=502, detail=f"Scavio: erro na requisição (HTTP {status_code}).")


def _parse_price(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def _normalize_search_item(item: dict) -> dict:
    """Normaliza um item da resposta de /amazon/search (campos tolerantes a ausência)."""
    asin = item.get("asin") or item.get("ASIN")
    url = item.get("url") or item.get("link") or item.get("product_url")
    if asin and not url:
        url = f"https://www.amazon.com.br/dp/{asin}"
    return {
        "nome": item.get("title") or item.get("name") or item.get("product_title"),
        "asin": asin,
        "url": url,
        "link_afiliado": add_affiliate_tag(url),
        "imagem_url": item.get("image") or item.get("image_url") or item.get("thumbnail"),
        "descricao": item.get("description") or item.get("snippet"),
        "preco": _parse_price(item.get("price")),
        "preco_anterior": _parse_price(item.get("list_price") or item.get("original_price") or item.get("was_price")),
        "moeda": item.get("currency"),
        "avaliacao": _parse_price(item.get("rating")),
        "total_avaliacoes": item.get("reviews_count") or item.get("review_count") or item.get("ratings_count"),
        "marca": item.get("brand"),
        "disponivel": item.get("availability") not in (None, "", "Indisponível", "Unavailable"),
        "origem": "search",
    }


def _normalize_product_detail(data: dict) -> dict:
    """Normaliza a resposta de /amazon/product (detalhe por ASIN)."""
    url = data.get("url")
    asin = data.get("asin")
    if asin and not url:
        url = f"https://www.amazon.com.br/dp/{asin}"
    desc = data.get("description")
    features = data.get("features")
    if not desc and isinstance(features, list) and features:
        desc = "\n".join(str(f) for f in features[:10])
    images = data.get("images")
    image = data.get("image") or (images[0] if isinstance(images, list) and images else None)
    return {
        "nome": data.get("title") or data.get("name"),
        "asin": asin,
        "url": url,
        "link_afiliado": add_affiliate_tag(url),
        "imagem_url": image,
        "descricao": desc,
        "preco": _parse_price(data.get("price")),
        "preco_anterior": _parse_price(data.get("list_price")),
        "moeda": data.get("currency"),
        "avaliacao": _parse_price(data.get("rating")),
        "total_avaliacoes": data.get("reviews_count") or data.get("review_count"),
        "marca": data.get("brand"),
        "disponivel": data.get("availability") not in (None, "", "Indisponível", "Unavailable", "Out of Stock"),
        "origem": "product",
    }


async def _scavio_post(path: str, payload: dict) -> dict:
    """POST autenticado à Scavio com timeout e tratamento de erros."""
    url = settings.SCAVIO_BASE_URL.rstrip("/") + path
    try:
        async with httpx.AsyncClient(timeout=settings.SCAVIO_TIMEOUT_SECONDS) as client:
            resp = await client.post(url, json=payload, headers=_headers())
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Scavio: tempo limite excedido na consulta. Tente novamente.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Scavio: falha de comunicação com o serviço.")

    if resp.status_code != 200:
        raise _map_status_error(resp.status_code)

    try:
        body = resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Scavio: resposta inválida (JSON malformado).")
    if not isinstance(body, dict):
        raise HTTPException(status_code=502, detail="Scavio: resposta vazia ou inesperada.")
    return body


async def fetch_amazon_product_by_asin(asin: str) -> Optional[dict]:
    """
    Busca o detalhe de UM produto Amazon por ASIN via Scavio
    (POST /api/v1/amazon/product — 1 crédito). Retorna dict normalizado
    ou None se o produto não for encontrado / dados vazios.
    """
    status_info = scavio_status()
    if not status_info["configured"]:
        return None
    asin = (asin or "").strip().upper()
    if not ASIN_PATTERN.match(asin):
        return None
    country = (settings.AMAZON_MARKETPLACE or "BR").lower()
    body = await _scavio_post(settings.SCAVIO_AMAZON_PRODUCT_ENDPOINT, {"asin": asin, "country": country})
    data = body.get("data") or {}
    if not data:
        return None
    normalized = _normalize_product_detail(data)
    normalized["disponivel"] = data.get("availability") not in (None, "", "Indisponível", "Unavailable", "Out of Stock")
    return normalized


async def search_amazon(query: str) -> dict:
    """
    Pesquisa produtos Amazon via Scavio.

    - Query = ASIN ou URL Amazon → endpoint de DETALHE do produto (1 crédito).
    - Demais queries → endpoint de BUSCA (1 crédito por página).
    - Cache em memória evita créditos duplicados em pesquisas idênticas (TTL configurável).
    """
    status_info = scavio_status()
    if not status_info["configured"]:
        if status_info["status"] == "desativada":
            raise HTTPException(status_code=503, detail="Integração Scavio desativada (SCAVIO_ENABLED=false).")
        raise HTTPException(status_code=503, detail="Scavio: API Key não configurada (SCAVIO_API_KEY).")

    query = (query or "").strip()
    if not query or len(query) > MAX_QUERY_LEN:
        raise HTTPException(status_code=400, detail=f"Consulta inválida: informe texto de 1 a {MAX_QUERY_LEN} caracteres.")

    cache_key = f"{query.lower()}|{settings.AMAZON_MARKETPLACE}"
    now = time.time()
    cached = _search_cache.get(cache_key)
    if cached and (now - cached[0]) < settings.SCAVIO_CACHE_TTL_SECONDS:
        return {"products": cached[1], "total": len(cached[1]), "cached": True, "credits_remaining": None}

    country = (settings.AMAZON_MARKETPLACE or "BR").lower()
    asin = _extract_asin(query)

    if asin:
        body = await _scavio_post(settings.SCAVIO_AMAZON_PRODUCT_ENDPOINT, {"asin": asin, "country": country})
        data = body.get("data") or {}
        products = [_normalize_product_detail(data)] if data else []
        credits_remaining = body.get("credits_remaining")
    else:
        body = await _scavio_post(
            settings.SCAVIO_AMAZON_ENDPOINT,
            {"query": query, "country": country},
        )
        data = body.get("data") or {}
        raw_products = data.get("products") or []
        products = [_normalize_search_item(p) for p in raw_products if isinstance(p, dict)]
        credits_remaining = body.get("credits_remaining")

    _search_cache[cache_key] = (now, products)
    # Limita o tamanho do cache em memória
    if len(_search_cache) > 200:
        oldest = sorted(_search_cache.items(), key=lambda kv: kv[1][0])[:50]
        for k, _ in oldest:
            _search_cache.pop(k, None)

    logger.info(f"[SCAVIO] consulta '{query[:60]}' → {len(products)} produto(s) normalizados")
    return {"products": products, "total": len(products), "cached": False, "credits_remaining": credits_remaining}
