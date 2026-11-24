"""
Site settings endpoints — admin (full schema) and public (whitelisted only).

Admin:
  GET    /api/admin/site-settings            → schema + current values
  PUT    /api/admin/site-settings            → bulk update {key: value}
  POST   /api/admin/site-settings/reset/{category} → restore category defaults

Public:
  GET    /api/public/site-settings           → only public-safe fields
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.models import Admin, HistoricoAdmin, utcnow
from backend.app.services.auth_service import get_current_admin
from backend.app.services import site_settings as ss

admin_router = APIRouter(prefix="/admin", tags=["Configurações (Admin)"])
public_router = APIRouter(prefix="/public", tags=["Configurações (Público)"])


class SiteSettingsUpdate(BaseModel):
    configuracoes: Dict[str, Any]


class SiteSettingsResetResponse(BaseModel):
    message: str
    category: str
    reset_count: int


@admin_router.get("/site-settings")
def get_site_settings(
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Full settings schema with current values (admin only)."""
    return ss.get_admin_settings(db)


@admin_router.put("/site-settings")
def update_site_settings(
    payload: SiteSettingsUpdate,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Validate + persist site settings. Unknown/invalid keys are rejected."""
    result = ss.update_settings(db, payload.configuracoes, admin_nome=admin.nome)
    if result["updated"]:
        db.add(HistoricoAdmin(
            administrador_id=admin.id,
            acao="update_site_settings",
            descricao=f"Configurações do site alteradas por {admin.nome}: {', '.join(result['updated'][:30])}",
            criado_em=utcnow(),
        ))
        db.commit()
    return {
        "message": "Configurações atualizadas" if not result["errors"] else "Atualização parcial",
        "updated": result["updated"],
        "errors": result["errors"],
    }


@admin_router.post("/site-settings/reset/{category}", response_model=SiteSettingsResetResponse)
def reset_site_settings_category(
    category: str,
    db: Session = Depends(get_db),
    admin: Admin = Depends(get_current_admin),
):
    """Restore all settings of a category to schema defaults."""
    if category not in ss.SCHEMA_BY_CATEGORY:
        return SiteSettingsResetResponse(
            message=f"Categoria desconhecida: {category}", category=category, reset_count=0
        )
    count = ss.reset_category(db, category)
    db.add(HistoricoAdmin(
        administrador_id=admin.id,
        acao="reset_site_settings",
        descricao=f"Categoria '{category}' restaurada ao padrão por {admin.nome} ({count} campos)",
        criado_em=utcnow(),
    ))
    db.commit()
    return SiteSettingsResetResponse(
        message=f"Categoria '{ss.CATEGORY_LABELS.get(category, category)}' restaurada",
        category=category,
        reset_count=count,
    )


@public_router.get("/site-settings")
def get_public_site_settings(db: Session = Depends(get_db)):
    """
    Public-safe site settings for the frontend.
    NEVER returns private fields, secrets, or admin data.
    """
    return ss.get_public_settings(db)
