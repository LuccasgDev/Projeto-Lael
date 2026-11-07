"""
Cria o primeiro administrador do sistema SEM senha padrão.

Uso:
    python -m backend.app.create_admin <email> <senha> [nome]

Ou via variáveis de ambiente no primeiro boot:
    ADMIN_EMAIL=... ADMIN_PASSWORD=... (usado pelo seed)

Nunca existem credenciais padrão no código.
"""
import sys

from backend.app.database import SessionLocal
from backend.app.models.models import Admin, utcnow
from backend.app.services.auth_service import get_password_hash


def create_admin(email: str, senha: str, nome: str = "Administrador") -> Admin:
    db = SessionLocal()
    try:
        existing = db.query(Admin).filter(Admin.email == email.lower().strip()).first()
        if existing:
            print(f"[CREATE_ADMIN] Administrador '{email}' já existe. Nada foi alterado.")
            return existing
        if len(senha) < 8:
            print("[CREATE_ADMIN] ERRO: a senha deve ter pelo menos 8 caracteres.")
            sys.exit(1)
        admin = Admin(
            nome=nome,
            email=email.lower().strip(),
            senha_hash=get_password_hash(senha),
            ativo=True,
            criado_em=utcnow(),
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"[CREATE_ADMIN] Administrador '{email}' criado com sucesso.")
        return admin
    finally:
        db.close()


def main():
    if len(sys.argv) < 3:
        print("Uso: python -m backend.app.create_admin <email> <senha> [nome]")
        sys.exit(1)
    email, senha = sys.argv[1], sys.argv[2]
    nome = sys.argv[3] if len(sys.argv) > 3 else "Administrador"
    create_admin(email, senha, nome)


if __name__ == "__main__":
    main()
