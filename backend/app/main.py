import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from backend.app.config import settings
from backend.app.data.seed_data import init_database_seed
from backend.app.services.expiration_worker import start_expiration_worker
from backend.app.routers import (
    public_router, auth_router, admin_router, sync_router
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize tables & seeds
    logger.info("Iniciando Chá de Rifa do Lael API...")
    try:
        init_database_seed()
    except Exception as e:
        logger.error(f"Erro ao inicializar banco: {e}")

    # Launch background expiration worker
    expiration_task = asyncio.create_task(start_expiration_worker())
    
    yield

    # Shutdown
    logger.info("Encerrando aplicação...")
    expiration_task.cancel()
    try:
        await expiration_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API do sistema web do Chá de Rifa do Lael — Fortaleza/CE (Março 2027)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local development and mobile web access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(public_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(admin_router, prefix=settings.API_PREFIX)
app.include_router(sync_router, prefix=settings.API_PREFIX)


@app.get("/")
def root():
    return {
        "projeto": settings.PROJECT_NAME,
        "versao": settings.VERSION,
        "evento": "Chá de Rifa do Lael - Março de 2027 (Fortaleza - CE)",
        "documentacao": "/docs",
        "status": "online"
    }


@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "cha-de-rifa-backend"}
