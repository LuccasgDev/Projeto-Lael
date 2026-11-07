import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Admin, Configuracao, ProdutoPrincipal, Mimo, Numero
from backend.app.services.auth_service import get_password_hash, create_access_token
from backend.app.data.seed_data import DEFAULT_CONFIGS, SEED_FRALDAS_REAIS, SEED_MIMOS_DEMO

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

    # Seed Products (fraldas reais do seed — RN, RN+ e P, todas com preço)
    prods = []
    for p in SEED_FRALDAS_REAIS[:3]:
        prod = ProdutoPrincipal(
            asin=p["asin"],
            nome=p["nome"],
            tamanho=p["tamanho"],
            ordem_exibicao=p["ordem_exibicao"],
            categoria=p["categoria"],
            descricao=p["descricao"],
            preco_atual=p["preco_atual"],
            imagem_url=p.get("imagem_url"),
            produto_url=p["produto_url"],
            quantidade_desejada=p["quantidade_desejada"],
            ativo=True,
        )
        session.add(prod)
        session.flush()
        prods.append(prod)

    # Seed Mimos (lista DEMO)
    for m in SEED_MIMOS_DEMO[:3]:
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
    # Seed 10 Numbers — faixa real RN (01–10) aponta para a fralda RN (prods[0]),
    # que tem preço definido; testes que precisam de fralda sem preço a criam.
    for i in range(1, 11):
        num = Numero(
            numero=i,
            produto_principal_id=prods[0].id,
            status="disponivel"
        )
        session.add(num)

    session.commit()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    # Limpa limitadores de taxa entre testes (estado global em memória)
    from backend.app.services.rate_limit import reserve_limiter, login_limiter
    reserve_limiter.reset()
    login_limiter.reset()

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
