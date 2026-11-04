from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import Admin
from backend.app.schemas.schemas import AdminLoginRequest, TokenResponse, AdminUserResponse
from backend.app.services.auth_service import verify_password, create_access_token, get_current_admin

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/login", response_model=TokenResponse)
def login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == payload.email.lower().strip()).first()
    if not admin or not verify_password(payload.senha, admin.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not admin.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário administrativo desativado",
        )

    token = create_access_token(data={"sub": str(admin.id), "email": admin.email})

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        admin_id=admin.id,
        admin_nome=admin.nome,
        admin_email=admin.email
    )


@router.get("/me", response_model=AdminUserResponse)
def get_current_admin_user(current_admin: Admin = Depends(get_current_admin)):
    return current_admin
