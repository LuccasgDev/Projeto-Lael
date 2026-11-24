import os
from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    PROJECT_NAME: str = "Chá Rifa do Lael"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./rifa_lael.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "lael-super-secret-security-key-2027-cha-de-bebe-fortaleza")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS — restrito às origens de publicação; sobrescreva via variável de ambiente
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v
    
    # Business Rules
    DEFAULT_RESERVATION_HOURS: int = 72
    TOTAL_NUMBERS: int = 100

    # Scavio Amazon API (painel admin — busca de produtos para o catálogo)
    # A chave NUNCA vai para o frontend, banco ou logs. Sem chave → integração desativada.
    SCAVIO_ENABLED: bool = False
    SCAVIO_API_KEY: str = ""
    SCAVIO_BASE_URL: str = "https://api.scavio.dev"
    SCAVIO_AMAZON_ENDPOINT: str = "/api/v1/amazon/search"
    SCAVIO_AMAZON_PRODUCT_ENDPOINT: str = "/api/v1/amazon/product"
    SCAVIO_TIMEOUT_SECONDS: float = 20.0
    SCAVIO_CACHE_TTL_SECONDS: int = 300  # cache em memória de pesquisas idênticas

    # Amazon Associates — geração do link de afiliado
    AMAZON_ASSOCIATE_TAG: str = "projetolael-20"
    AMAZON_MARKETPLACE: str = "BR"
    
    # Expiration Worker Interval in Seconds
    EXPIRATION_WORKER_INTERVAL: int = 60
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
