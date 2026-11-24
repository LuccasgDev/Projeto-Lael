"""
Testes das regras da v2 do prompt:
- RN-01 v2: números gerados das fraldas, agrupados por tamanho, grade retorna tamanho
- RN-08 v2: Pix bloqueado quando o preço é nulo (ex.: fralda M "Ver opções")
- RN-10: número marcado como compra externa (cinza, origem registrada) e desmarcação
- RN-10: ajuste de estoque externo de mimo
- RN-11: alerta de capacidade (mimos disponíveis × números não confirmados)
"""
import pytest
from datetime import timedelta
from conftest import mimo_para_numero

from backend.app.models.models import Numero, Mimo, ProdutoPrincipal, Reserva, utcnow
from backend.app.services.rate_limit import login_limiter, reserve_limiter


@pytest.fixture(autouse=True)
def _reset_limiters():
    login_limiter.reset()
    reserve_limiter.reset()
    yield
    login_limiter.reset()
    reserve_limiter.reset()


def _reserve_payload(num_id, mimo_id, nome="Convidado v2", forma_pres="amazon", forma_mimo="amazon"):
    return {
        "numero_id": num_id,
        "mimo_id": mimo_id,
        "nome_convidado": nome,
        "whatsapp": "85999990000",
        "autoriza_nome_publico": True,
        "forma_presente": forma_pres,
        "forma_mimo": forma_mimo,
        "consentimento_lgpd": True,
    }


class TestFraldasRN01:
    def test_grid_retorna_tamanho_e_grupo(self, client, db_session):
        resp = client.get("/api/public/numbers")
        assert resp.status_code == 200
        items = resp.json()
        primeiro = items[0]
        assert "produto_tamanho" in primeiro
        assert "produto_id" in primeiro

    def test_fralda_sem_preco_aceita_amazon_mas_bloqueia_pix(self, client, db_session):
        """RN-08 v2: preço nulo — Amazon ok, Pix bloqueado. Usa faixa RN (regra fixa)."""
        fralda_sem_preco = ProdutoPrincipal(
            asin="B00TESTE01", nome="Fralda RN sem preço (teste)", tamanho="RN",
            ordem_exibicao=99, categoria="Fraldas", preco_atual=None,
            quantidade_desejada=5, ativo=True,
        )
        db_session.add(fralda_sem_preco)
        db_session.commit()
        db_session.refresh(fralda_sem_preco)

        num = db_session.query(Numero).filter(Numero.numero == 5).first()
        num2 = db_session.query(Numero).filter(Numero.numero == 4).first()
        num.produto_principal_id = fralda_sem_preco.id
        num2.produto_principal_id = fralda_sem_preco.id
        mimo = mimo_para_numero(db_session, num.numero)  # RN → mimo fixo
        db_session.commit()

        # Amazon OK
        r1 = client.post("/api/public/reserve", json=_reserve_payload(num.id, mimo.id, forma_pres="amazon"))
        assert r1.status_code == 200, r1.text
        assert r1.json()["preco_presente_reserva"] == 0

        # Outro número da mesma fralda, tentando Pix → 400
        r2 = client.post("/api/public/reserve", json=_reserve_payload(num2.id, mimo.id, nome="G2", forma_pres="pix"))
        assert r2.status_code == 400
        assert "preço" in r2.json()["detail"].lower()


class TestRegenerarFaixas:
    def test_regera_preservando_reservas_e_compra_externa(self, client, db_session, admin_headers):
        """RN-01: regerar faixas reatribui disponíveis e preserva reservado/confirmado/externo."""
        fralda_rn = db_session.query(ProdutoPrincipal).filter(ProdutoPrincipal.tamanho == "RN", ProdutoPrincipal.ativo == True).first()
        num_res = db_session.query(Numero).filter(Numero.numero == 4).first()
        num_ext = db_session.query(Numero).filter(Numero.numero == 5).first()
        mimo = mimo_para_numero(db_session, num_res.numero)

        r = client.post("/api/public/reserve", json=_reserve_payload(num_res.id, mimo.id))
        assert r.status_code == 200
        num_ext.status = "compra_externa"
        num_ext.origem_ocupacao = "Teste externo"
        db_session.commit()

        resp = client.post("/api/admin/numeros/regenerar-faixas", headers=admin_headers)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["numeros_preservados"] >= 2  # reservado + compra_externa

        db_session.refresh(num_res)
        db_session.refresh(num_ext)
        assert num_res.status == "reservado"
        assert num_res.produto_principal_id == fralda_rn.id
        assert num_ext.status == "compra_externa"

    def test_exige_admin(self, client, db_session):
        resp = client.post("/api/admin/numeros/regenerar-faixas")
        assert resp.status_code in (401, 403)


class TestCompraExternaRN10:
    def test_marcar_e_desmarcar_numero(self, client, db_session, admin_headers):
        num = db_session.query(Numero).filter(Numero.numero == 7).first()
        # Marca
        r = client.post(f"/api/admin/numeros/{num.id}/compra-externa",
                        json={"marcar": True, "origem": "Avó comprou na Amazon"},
                        headers=admin_headers)
        assert r.status_code == 200
        db_session.refresh(num)
        assert num.status == "compra_externa"
        assert num.origem_ocupacao == "Avó comprou na Amazon"

        # Grade mostra o número como indisponível (cinza)
        grid = client.get("/api/public/numbers").json()
        item = next(n for n in grid if n["numero"] == 7)
        assert item["status"] == "compra_externa"

        # Desmarca
        r2 = client.post(f"/api/admin/numeros/{num.id}/compra-externa",
                         json={"marcar": False}, headers=admin_headers)
        assert r2.status_code == 200
        db_session.refresh(num)
        assert num.status == "disponivel"
        assert num.origem_ocupacao is None

    def test_nao_marca_numero_com_reserva_ativa(self, client, db_session, admin_headers):
        num = db_session.query(Numero).filter(Numero.numero == 8).first()
        mimo = mimo_para_numero(db_session, num.numero)
        r = client.post("/api/public/reserve", json=_reserve_payload(num.id, mimo.id))
        assert r.status_code == 200
        r2 = client.post(f"/api/admin/numeros/{num.id}/compra-externa",
                         json={"marcar": True}, headers=admin_headers)
        assert r2.status_code == 400

    def test_ajuste_estoque_externo_mimo(self, client, db_session, admin_headers):
        mimo = db_session.query(Mimo).filter(Mimo.categoria != "Mimo fixo do número").first()
        r = client.put(f"/api/admin/mimos/{mimo.id}/estoque-externo",
                       json={"quantidade_comprada_externa": 1}, headers=admin_headers)
        assert r.status_code == 200
        mimos = client.get("/api/public/mimos").json()
        alvo = next(m for m in mimos if m["id"] == mimo.id)
        assert alvo["disponibilidade_restante"] == mimo.quantidade_desejada - 1


class TestAlertaCapacidadeRN11:
    def test_alerta_quando_mimos_insuficientes(self, client, db_session, admin_headers):
        # Conftest cria 10 números e 3 mimos com quantidades 15+12+10=37 → sem alerta
        r = client.get("/api/admin/dashboard", headers=admin_headers)
        assert r.status_code == 200
        data = r.json()
        assert "alerta_capacidade_mimos" in data
        assert "mimos_disponiveis_total" in data
        assert "numeros_nao_confirmados" in data
        assert data["mimos_disponiveis_total"] >= data["numeros_nao_confirmados"]
        assert data["alerta_capacidade_mimos"] is False

    def test_alerta_dispara_com_mimos_esgotados(self, client, db_session, admin_headers):
        # Esgota todos os mimos: coloca desejada = comprada_externa
        for m in db_session.query(Mimo).all():
            m.quantidade_desejada = 1
            m.quantidade_comprada_externa = 1
        db_session.commit()
        r = client.get("/api/admin/dashboard", headers=admin_headers)
        data = r.json()
        assert data["mimos_disponiveis_total"] == 0
        assert data["numeros_nao_confirmados"] > 0
        assert data["alerta_capacidade_mimos"] is True
