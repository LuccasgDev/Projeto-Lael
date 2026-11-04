import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Admin, Configuracao, ProdutoPrincipal, Mimo, Numero
from backend.app.services.auth_service import get_password_hash, create_access_token
from backend.app.data.seed_data import DEFAULT_CONFIGS, SEED_PRODUTOS_PRINCIPAIS, SEED_MIMOS

from sqlalchemy.pool import StaticPool

TEST_DB_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine_test)
    session = TestingSessionLocal()

    # Seed Admin
    admin = Admin(
        nome="Admin Teste",
        email="admin@teste.com",
        senha_hash=get_password_hash("senha123"),
        ativo=True,
    )
    session.add(admin)

    # Seed Configs
    for k, v in DEFAULT_CONFIGS.items():
        session.add(Configuracao(chave=k, valor=v))

    # Seed Products
    prods = []
    for p in SEED_PRODUTOS_PRINCIPAIS[:3]:
        prod = ProdutoPrincipal(
            asin=p["asin"],
            nome=p["nome"],
            categoria=p["categoria"],
            descricao=p["descricao"],
            preco_atual=p["preco_atual"],
            imagem_url=p["imagem_url"],
            produto_url=p["produto_url"],
            quantidade_desejada=p["quantidade_desejada"],
            ativo=True,
        )
        session.add(prod)
        session.flush()
        prods.append(prod)

    # Seed Mimos
    for m in SEED_MIMOS[:3]:
        mimo = Mimo(
            asin=m["asin"],
            nome=m["nome"],
            categoria=m["categoria"],
            descricao=m["descricao"],
            preco_atual=m["preco_atual"],
            imagem_url=m["imagem_url"],
            produto_url=m["produto_url"],
            quantidade_desejada=m["quantidade_desejada"],
            ativo=True,
        )
        session.add(mimo)

    # Seed 10 Numbers for quick tests
    for i in range(1, 11):
        num = Numero(
            numero=i,
            produto_principal_id=prods[(i - 1) % len(prods)].id,
            status="disponivel"
        )
        session.add(num)

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_headers(db_session):
    admin = db_session.query(Admin).filter(Admin.email == "admin@teste.com").first()
    token = create_access_token({"sub": str(admin.id), "email": admin.email})
    return {"Authorization": f"Bearer {token}"}
