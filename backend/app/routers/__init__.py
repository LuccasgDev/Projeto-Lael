from backend.app.routers.public import router as public_router
from backend.app.routers.auth import router as auth_router
from backend.app.routers.admin import router as admin_router
from backend.app.routers.sync import router as sync_router
from backend.app.routers.scavio import router as scavio_router
from backend.app.routers.site_settings import admin_router as site_admin_router, public_router as site_public_router

__all__ = ["public_router", "auth_router", "admin_router", "sync_router", "scavio_router", "site_admin_router", "site_public_router"]
