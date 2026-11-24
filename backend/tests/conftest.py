import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.models import Admin, Configuracao, ProdutoPrincipal, Mimo, Numero
from backend.app.services.auth_service import get_password_hash, create_access_token
from backend.app.data.seed_data import DEFAULT_CONFIGS, SEED_FRALDAS_REAIS, SEED_MIMOS_DEMO
from backend.app.services.numero_regra import (
    FAIXAS_NUMEROS, MIMO_FIXO_PADRAO, classificar_numero, resolver_mimo_fixo,
)

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
    for p in SEED_FRALDAS_REAIS:
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
            ativo=p["ativo"],
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

    # Seed mimos FIXOS da regra (RN/P/G) — nomes canônicos das configurações
    for faixa in FAIXAS_NUMEROS:
        if faixa["tamanho"] == "M":
            continue
        tam = faixa["tamanho"]
        session.add(Mimo(
            nome=MIMO_FIXO_PADRAO[tam],
            categoria="Mimo fixo do número",
            descricao=f"Mimo fixo da faixa {tam} (regra do evento).",
            preco_atual=20.0,
            quantidade_desejada=faixa["fim"] - faixa["inicio"] + 1,
            ativo=True,
        ))
    session.flush()

    # Seed 10 Numbers — faixa fixa: 01–05 RN, 06–10 P
    fraldas_por_tamanho = {p.tamanho: p for p in prods}
    for i in range(1, 11):
        tam = classificar_numero(i)["tamanho"]
        num = Numero(
            numero=i,
            produto_principal_id=fraldas_por_tamanho[tam].id,
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


def mimo_para_numero(db, numero: int):
    """
    Retorna o mimo correto para reservar um número, respeitando a regra fixa:
    RN/P/G → mimo fixo da faixa; M → qualquer mimo ativo (escolha livre).
    """
    classif = classificar_numero(numero)
    if classif["mimo_modo"] == "fixo":
        mimo = resolver_mimo_fixo(db, classif["tamanho"])
        assert mimo is not None, f"Mimo fixo {classif['tamanho']} não encontrado no seed de teste"
        return mimo
    return db.query(Mimo).first()


@pytest.fixture(scope="function")
def admin_headers(db_session):
    admin = db_session.query(Admin).filter(Admin.email == "admin@teste.com").first()
    token = create_access_token({"sub": str(admin.id), "email": admin.email})
    return {"Authorization": f"Bearer {token}"}
