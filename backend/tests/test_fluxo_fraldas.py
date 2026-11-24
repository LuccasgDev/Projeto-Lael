"""
Testes do fluxo corrigido (REGRA FIXA do Chá Rifa do Lael):

REGRA INEGOCIÁVEL: o número define a fralda (faixa fixa) e, fora da faixa M,
também define o mimo; na faixa M o convidado escolhe o mimo separadamente.
O catálogo de mimos é retornado COMPLETO (sem limite/paginação que esconda itens).

- 01–05 → RN · 06–35 → P · 36–65 → M · 66–100 → G.
- Nenhum número tem um mimo como fralda.
- Importação por texto cria TODOS os itens; a API não corta o catálogo.
"""
import pytest

from backend.app.data.seed_data import SEED_FRALDAS_REAIS
from backend.app.models.models import Numero, Mimo, ProdutoPrincipal
from backend.app.services.numero_regra import FAIXAS_NUMEROS, classificar_numero


class TestFaixasDeNumeros:
    def test_faixas_fixas_fixas(self):
        """RN 01-05 · P 06-35 · M 36-65 · G 66-100 — fixas e contíguas."""
        esperado = [("RN", 1, 5), ("P", 6, 35), ("M", 36, 65), ("G", 66, 100)]
        assert [(f["tamanho"], f["inicio"], f["fim"]) for f in FAIXAS_NUMEROS] == esperado
        assert FAIXAS_NUMEROS[0]["inicio"] == 1
        for a, b in zip(FAIXAS_NUMEROS, FAIXAS_NUMEROS[1:]):
            assert b["inicio"] == a["fim"] + 1
        assert FAIXAS_NUMEROS[-1]["fim"] == 100

    @pytest.mark.parametrize("numero,tamanho", [
        (1, "RN"), (5, "RN"), (6, "P"), (35, "P"),
        (36, "M"), (65, "M"), (66, "G"), (100, "G"),
    ])
    def test_limites_das_faixas(self, numero, tamanho):
        assert classificar_numero(numero)["tamanho"] == tamanho


class TestMapeamentoNumeroFralda:
    @pytest.fixture()
    def grade_real(self, db_session):
        """Monta a grade 01–100 com as fraldas reais do seed, via FAIXAS_NUMEROS."""
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
        db_session.commit()

        fralda_por_tamanho = {p.tamanho: p for p in fraldas_map if p.ativo}
        for faixa in FAIXAS_NUMEROS:
            fralda = fralda_por_tamanho[faixa["tamanho"]]
            for num in range(faixa["inicio"], faixa["fim"] + 1):
                n = db_session.query(Numero).filter(Numero.numero == num).first()
                if n:
                    n.produto_principal_id = fralda.id
                else:
                    db_session.add(Numero(numero=num, produto_principal_id=fralda.id, status="disponivel"))
        db_session.commit()
        return fraldas_map

    def test_numero_01_e_fralda_rn(self, client, grade_real):
        r = client.get("/api/public/numbers/1")
        assert r.status_code == 200
        p = r.json()["produto_principal"]
        assert "Pampers Primeiros Dias" in p["nome"]
        assert p["tamanho"] == "RN"
        assert p["categoria"] == "Fraldas"

    def test_numero_06_e_fralda_p(self, client, grade_real):
        p = client.get("/api/public/numbers/6").json()["produto_principal"]
        assert "Premium Care P" in p["nome"]
        assert p["tamanho"] == "P"

    def test_numero_36_e_fralda_m(self, client, grade_real):
        p = client.get("/api/public/numbers/36").json()["produto_principal"]
        assert "Confort Sec M" in p["nome"]
        assert p["tamanho"] == "M"
        assert p["preco_atual"] is None  # sem preço na lista — admin informa manual

    def test_numero_66_e_fralda_g(self, client, grade_real):
        p = client.get("/api/public/numbers/66").json()["produto_principal"]
        assert "Pants G" in p["nome"]
        assert p["tamanho"] == "G"

    def test_numero_100_tambem_e_fralda_g(self, client, grade_real):
        p = client.get("/api/public/numbers/100").json()["produto_principal"]
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
