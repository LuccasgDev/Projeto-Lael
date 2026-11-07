"""
Testes da correção do fluxo (CORREÇÃO OBRIGATÓRIA v2):

REGRA INEGOCIÁVEL: o número define a fralda; o convidado escolhe o mimo separadamente;
o catálogo de mimos é retornado COMPLETO (sem limite/paginação que esconda itens).

- Número 01 → fralda RN; 11 → RN+; 21 → P; 51 → M; 76 → G.
- Nenhum número tem um mimo como fralda.
- Importação por texto cria TODOS os itens; a API não corta o catálogo.
"""
import pytest

from backend.app.data.seed_data import SEED_FRALDAS_REAIS, gerar_faixas_fraldas
from backend.app.models.models import Numero, Mimo, ProdutoPrincipal


class TestFaixasDeNumeros:
    def test_faixas_continuas_da_lista_real(self):
        """01–10 RN · 11–20 RN+ · 21–50 P · 51–75 M · 76–100 G — nunca intercalados."""
        class F:
            def __init__(self, tamanho, qtd):
                self.tamanho, self.quantidade_desejada = tamanho, qtd

        fraldas = [F("RN", 10), F("RN+", 10), F("P", 30), F("M", 25), F("G", 25)]
        faixas = gerar_faixas_fraldas(fraldas)
        esperado = [("RN", 1, 10), ("RN+", 11, 20), ("P", 21, 50), ("M", 51, 75), ("G", 76, 100)]
        for faixa, (tam, ini, fim) in zip(faixas, esperado):
            assert faixa["fralda"].tamanho == tam
            assert faixa["inicio"] == ini
            assert faixa["fim"] == fim
        # faixas contíguas e total = 100
        assert faixas[0]["inicio"] == 1
        for a, b in zip(faixas, faixas[1:]):
            assert b["inicio"] == a["fim"] + 1
        assert faixas[-1]["fim"] == 100


class TestMapeamentoNumeroFralda:
    @pytest.fixture()
    def grade_real(self, db_session):
        """Monta a grade 01–100 com as fraldas reais do seed, via gerar_faixas_fraldas."""
        fraldas_map = []
        for f in SEED_FRALDAS_REAIS:
            prod = ProdutoPrincipal(
                asin=f["asin"], nome=f["nome"], tamanho=f["tamanho"],
                ordem_exibicao=f["ordem_exibicao"], categoria="Fraldas",
                preco_atual=f["preco_atual"], produto_url=f["produto_url"],
                quantidade_desejada=f["quantidade_desejada"], ativo=f["ativo"],
            )
            db_session.add(prod)
            db_session.flush()
            fraldas_map.append(prod)

        for faixa in gerar_faixas_fraldas(sorted(fraldas_map, key=lambda x: x.ordem_exibicao)):
            for num in range(faixa["inicio"], faixa["fim"] + 1):
                n = db_session.query(Numero).filter(Numero.numero == num).first()
                if n:
                    n.produto_principal_id = faixa["fralda"].id
                else:
                    db_session.add(Numero(numero=num, produto_principal_id=faixa["fralda"].id, status="disponivel"))
        db_session.commit()
        return fraldas_map

    def test_numero_01_e_fralda_rn(self, client, grade_real):
        r = client.get("/api/public/numbers/1")
        assert r.status_code == 200
        p = r.json()["produto_principal"]
        assert "Pampers Primeiros Dias" in p["nome"]
        assert p["tamanho"] == "RN"
        assert p["categoria"] == "Fraldas"

    def test_numero_11_e_fralda_rn_mais(self, client, grade_real):
        p = client.get("/api/public/numbers/11").json()["produto_principal"]
        assert "RN+" in p["nome"]
        assert p["tamanho"] == "RN+"

    def test_numero_21_e_fralda_p(self, client, grade_real):
        p = client.get("/api/public/numbers/21").json()["produto_principal"]
        assert "Premium Care P" in p["nome"]
        assert p["tamanho"] == "P"

    def test_numero_51_e_fralda_m(self, client, grade_real):
        p = client.get("/api/public/numbers/51").json()["produto_principal"]
        assert "Confort Sec M" in p["nome"]
        assert p["tamanho"] == "M"
        assert p["preco_atual"] is None  # sem preço na lista — admin informa manual

    def test_numero_76_e_fralda_g(self, client, grade_real):
        p = client.get("/api/public/numbers/76").json()["produto_principal"]
        assert "Pants G" in p["nome"]
        assert p["tamanho"] == "G"

    def test_numero_91_tambem_e_fralda_g(self, client, grade_real):
        """76–100 são todos G: o número 91 não tem produto próprio."""
        p = client.get("/api/public/numbers/91").json()["produto_principal"]
        assert "Pants G" in p["nome"]
        assert p["tamanho"] == "G"

    def test_nenhuma_fralda_e_um_mimo(self, client, db_session, grade_real):
        """Nenhum ASIN de mimo pode estar associado a números como fralda."""
        asins_mimos = {m.asin for m in db_session.query(Mimo).all() if m.asin}
        asins_fraldas = {p.asin for p in grade_real if p.asin}
        assert asins_mimos.isdisjoint(asins_fraldas)
        # A grade inteira só aponta para produtos da categoria Fraldas
        for n in db_session.query(Numero).all():
            if n.produto_principal_id:
                prod = db_session.get(ProdutoPrincipal, n.produto_principal_id)
                assert prod.categoria == "Fraldas"


class TestCatalogoCompleto:
    def test_importacao_texto_importa_todos_os_itens(self, client, db_session, admin_headers):
        """A importação por texto deve criar TODOS os itens; a API não pode cortar o catálogo."""
        texto = "\n".join([
            f"Mimo Teste {i:02d}; {'1' if i % 2 else '3'}; R$ {10 + i},90"
            for i in range(1, 13)
        ])
        r = client.post("/api/sync/import-texto?tipo=mimo", json={"texto": texto}, headers=admin_headers)
        assert r.status_code == 200, r.text
        assert r.json()["criados"] == 12

        # API devolve o catálogo completo (sem limite de resultados)
        mimos = client.get("/api/public/mimos").json()
        nomes = {m["nome"] for m in mimos}
        for i in range(1, 13):
            assert f"Mimo Teste {i:02d}" in nomes

        # Unidades totais preservadas (6 itens de 3 + 6 de 1 = 24) — RN-09
        importados = [m for m in mimos if m["nome"].startswith("Mimo Teste")]
        unidades = sum(m["disponibilidade_restante"] for m in importados)
        assert unidades == 24

    def test_importacao_nao_duplica_em_nova_passada(self, client, db_session, admin_headers):
        """Reimportar a mesma lista NÃO cria registros duplicados (atualiza em vez disso)."""
        texto = "Toalha com Capuz; 1; R$ 39,90\nMordedor Gel; 3; R$ 15,00\n"
        r1 = client.post("/api/sync/import-texto?tipo=mimo", json={"texto": texto}, headers=admin_headers)
        assert r1.status_code == 200
        r2 = client.post("/api/sync/import-texto?tipo=mimo", json={"texto": texto}, headers=admin_headers)
        assert r2.status_code == 200
        data = r2.json()
        assert data["criados"] == 0
        assert data["atualizados"] == 2

        nomes = [m["nome"] for m in client.get("/api/public/mimos").json()]
        assert nomes.count("Toalha com Capuz") == 1
        assert nomes.count("Mordedor Gel") == 1
