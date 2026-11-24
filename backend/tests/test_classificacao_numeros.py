"""
Testes da regra FIXA número → tamanho de fralda + mimo (Chá Rifa do Lael):

    01–05  → RN  + sabonete líquido p/ recém-nascido (mimo fixo)
    06–35  → P   + pomada antiassadura (mimo fixo)
    36–65  → M   + mimo à escolha do participante
    66–100 → G   + lenços umedecidos (mimo fixo)

- Limites das faixas e pontos intermediários.
- Backend rejeita mimo divergente fora da faixa M (classificação manipulada).
- API expõe tamanho/mimo correto na grade e no detalhe do número.
"""
import pytest

from conftest import mimo_para_numero
from backend.app.models.models import Numero, Mimo, ProdutoPrincipal
from backend.app.services.numero_regra import classificar_numero, FAIXAS_NUMEROS


class TestClassificacaoCentral:
    @pytest.mark.parametrize("numero,esperado", [
        (1, "RN"), (5, "RN"),
        (6, "P"), (35, "P"),
        (36, "M"), (65, "M"),
        (66, "G"), (100, "G"),
        # intermediários
        (3, "RN"), (20, "P"), (50, "M"), (80, "G"),
    ])
    def test_tamanho_por_numero(self, numero, esperado):
        assert classificar_numero(numero)["tamanho"] == esperado

    @pytest.mark.parametrize("numero,modo", [
        (1, "fixo"), (5, "fixo"),
        (6, "fixo"), (35, "fixo"),
        (36, "escolha"), (65, "escolha"),
        (66, "fixo"), (100, "fixo"),
    ])
    def test_mimo_modo_por_numero(self, numero, modo):
        assert classificar_numero(numero)["mimo_modo"] == modo

    def test_faixas_cobrem_1_a_100_sem_sobreposicao(self):
        assert FAIXAS_NUMEROS[0]["inicio"] == 1
        assert FAIXAS_NUMEROS[-1]["fim"] == 100
        for a, b in zip(FAIXAS_NUMEROS, FAIXAS_NUMEROS[1:]):
            assert b["inicio"] == a["fim"] + 1

    def test_numero_fora_da_faixa_rejeitado(self):
        for invalido in (0, -1, 101, 200):
            with pytest.raises(ValueError):
                classificar_numero(invalido)


class TestApiExpoeClassificacao:
    def test_grade_traz_tamanho_e_mimo(self, client, db_session):
        items = {n["numero"]: n for n in client.get("/api/public/numbers").json()}
        # conftest semeia números 1–10
        assert items[1]["produto_tamanho"] == "RN"
        assert items[1]["mimo_nome"]  # mimo fixo RN
        assert items[6]["produto_tamanho"] == "P"
        assert items[6]["mimo_nome"]

    def test_detalhe_mimo_fixo_e_livre(self, client, db_session):
        d1 = client.get("/api/public/numbers/1").json()
        assert d1["mimo_livre"] is False
        assert d1["mimo_fixo"] is not None
        assert d1["produto_principal"]["tamanho"] == "RN"

        # Número da faixa M → mimo livre (cria número 40 se necessário)
        fralda_m = db_session.query(ProdutoPrincipal).filter(
            ProdutoPrincipal.tamanho == "M", ProdutoPrincipal.ativo == True).first()
        num40 = db_session.query(Numero).filter(Numero.numero == 40).first()
        if not num40:
            num40 = Numero(numero=40, produto_principal_id=fralda_m.id, status="disponivel")
            db_session.add(num40)
            db_session.commit()
        d40 = client.get("/api/public/numbers/40").json()
        assert d40["mimo_livre"] is True
        assert d40["mimo_fixo"] is None
        assert d40["produto_principal"]["tamanho"] == "M"


class TestValidacaoMimoFixo:
    def _payload(self, num_id, mimo_id, nome="Convidado"):
        return {
            "numero_id": num_id,
            "mimo_id": mimo_id,
            "nome_convidado": nome,
            "whatsapp": "85999990000",
            "autoriza_nome_publico": True,
            "forma_presente": "amazon",
            "forma_mimo": "amazon",
            "consentimento_lgpd": True,
        }

    def test_mimo_errado_fora_da_faixa_m_rejeitado(self, client, db_session):
        """Número RN não pode usar mimo arbitrário — o backend impõe o fixo."""
        num = db_session.query(Numero).filter(Numero.numero == 1).first()
        mimo_errado = db_session.query(Mimo).filter(Mimo.categoria != "Mimo fixo do número").first()
        resp = client.post("/api/public/reserve", json=self._payload(num.id, mimo_errado.id))
        assert resp.status_code == 400
        assert "mimo" in resp.json()["detail"].lower()

    def test_mimo_fixo_correto_reserva(self, client, db_session):
        num = db_session.query(Numero).filter(Numero.numero == 2).first()
        mimo = mimo_para_numero(db_session, num.numero)
        resp = client.post("/api/public/reserve", json=self._payload(num.id, mimo.id))
        assert resp.status_code == 200, resp.text
        assert resp.json()["mimo_nome"] == mimo.nome

    def test_faixa_m_aceita_mimo_livre(self, client, db_session):
        fralda_m = db_session.query(ProdutoPrincipal).filter(
            ProdutoPrincipal.tamanho == "M", ProdutoPrincipal.ativo == True).first()
        num = Numero(numero=42, produto_principal_id=fralda_m.id, status="disponivel")
        db_session.add(num)
        db_session.commit()
        db_session.refresh(num)

        mimo_livre = db_session.query(Mimo).filter(Mimo.categoria != "Mimo fixo do número").first()
        resp = client.post("/api/public/reserve", json=self._payload(num.id, mimo_livre.id))
        assert resp.status_code == 200, resp.text
        assert resp.json()["mimo_nome"] == mimo_livre.nome
