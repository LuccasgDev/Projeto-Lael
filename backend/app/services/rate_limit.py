"""
Rate limiting simples em memória (escala pequena: dezenas a centenas de acessos).

Aplicado a endpoints sensíveis a abuso:
- POST /api/auth/login   (ataques de força bruta)
- POST /api/public/reserve (spam de reservas)

Para instâncias múltiplas, trocar por um limitador compartilhado — fora do escopo
do MVP (sem Redis/filas externas por decisão de arquitetura).
"""
import time
import threading
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window = window_seconds
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.max_requests:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


# Login: no máximo 5 tentativas por IP a cada 5 minutos
login_limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=300)
# Reserva: no máximo 10 tentativas por IP por minuto
reserve_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60)


def enforce_rate_limit(request: Request, limiter: SlidingWindowRateLimiter, detail: str) -> None:
    client_ip = request.client.host if request.client else "unknown"
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    if not limiter.check(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )
