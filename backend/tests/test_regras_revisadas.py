"""
Testes das correções do prompt revisado:
- RN-06: expiração verificada na leitura e na reserva (nunca no navegador)
- Integridade: índice único parcial (uma reserva ativa por número)
- §4: página de acompanhamento por link secreto (token com hash)
- §5/§7: rate limiting no login e na criação de reserva
- RN-01: alteração da quantidade de números preservando reservas
"""
import pytest
from datetime import timedelta
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from conftest import mimo_para_numero
from backend.app.models.models import Numero, Mimo, Reserva, utcnow
from backend.app.services.rate_limit import login_limiter, reserve_limiter


@pytest.fixture(autouse=True)
def _reset_limiters():
    login_limiter.reset()
    reserve_limiter.reset()
    yield
    login_limiter.reset()
    reserve_limiter.reset()


def _reserve_payload(num_id, mimo_id, nome="Convidado Teste"):
    return {
        "numero_id": num_id,
        "mimo_id": mimo_id,
        "nome_convidado": nome,
        "whatsapp": "85999990000",
        "autoriza_nome_publico": True,
        "forma_presente": "pix",
        "forma_mimo": "amazon",
        "consentimento_lgpd": True,
    }


class TestExpiracaoNaLeituraEReserva:
    def test_grid_expira_reserva_vencida(self, client, db_session):
        """RN-06: a leitura da grade expira reservas vencidas e devolve o número."""
        num = db_session.query(Numero).filter(Numero.numero == 5).first()
        mimo = mimo_para_numero(db_session, num.numero)
        num.status = "reservado"
        reserva = Reserva(
            numero_id=num.id, mimo_id=mimo.id, nome_convidado="Antiga",
            whatsapp="85999990001", forma_presente="pix", forma_mimo="pix",
            preco_presente_reserva=10, preco_mimo_reserva=10, valor_pix_total=10,
            status="reservada", criada_em=utcnow(),
            expira_em=utcnow() - timedelta(minutes=5),
        )
        db_session.add(reserva)
        db_session.commit()

        resp = client.get("/api/public/numbers")
        assert resp.status_code == 200
        item = next(n for n in resp.json() if n["numero"] == 5)
        assert item["status"] == "disponivel"

        db_session.refresh(reserva)
        assert reserva.status == "expirada"
        # Histórico preservado (RN-06)
        assert reserva.nome_convidado == "Antiga"

    def test_reserva_bloqueada_com_expiracao_pendente(self, client, db_session):
        """RN-06: reservar um número com reserva vencida NÃO herdada — a antiga expira e a nova entra."""
        num = db_session.query(Numero).filter(Numero.numero == 6).first()
        mimo = mimo_para_numero(db_session, num.numero)
        num.status = "reservado"
        db_session.add(Reserva(
            numero_id=num.id, mimo_id=mimo.id, nome_convidado="Vencida",
            whatsapp="85999990002", forma_presente="pix", forma_mimo="pix",
            preco_presente_reserva=10, preco_mimo_reserva=10, valor_pix_total=10,
            status="reservada", criada_em=utcnow(),
            expira_em=utcnow() - timedelta(minutes=1),
        ))
        db_session.commit()

        # Sem a checagem na reserva, este POST retornaria 409; com ela, deve criar a nova reserva.
        resp = client.post("/api/public/reserve", json=_reserve_payload(num.id, mimo.id))
        assert resp.status_code == 200, resp.text
        db_session.expire_all()
        antigas = db_session.query(Reserva).filter(
            Reserva.numero_id == num.id, Reserva.status == "expirada"
        ).count()
        assert antigas == 1


class TestIndiceUnicoParcial:
    def test_uma_unica_reserva_ativa_por_numero_no_banco(self, db_session):
        """Garantia no BANCO (não no backend): segunda reserva 'reservada' para o mesmo número falha."""
        num = db_session.query(Numero).filter(Numero.numero == 7).first()
        mimo = mimo_para_numero(db_session, num.numero)
        base = dict(
            numero_id=num.id, mimo_id=mimo.id, nome_convidado="A",
            whatsapp="85999990003", forma_presente="pix", forma_mimo="pix",
            preco_presente_reserva=10, preco_mimo_reserva=10, valor_pix_total=10,
            status="reservada", criada_em=utcnow(), expira_em=utcnow() + timedelta(hours=72),
        )
        db_session.add(Reserva(**base))
        db_session.commit()

        segundo = dict(base, nome_convidado="B")
        db_session.add(Reserva(**segundo))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

        # Estados terminais NÃO violam o índice (expirada preservada + nova reserva OK)
        db_session.add(Reserva(**dict(base, status="expirada")))
        db_session.commit()  # já existe uma 'reservada'; adicionando 'expirada' não conflita


class TestAcompanhamento:
    def test_link_secreto_funciona_e_token_nao_fica_salvo(self, client, db_session):
        num = db_session.query(Numero).filter(Numero.numero == 9).first()
        mimo = mimo_para_numero(db_session, num.numero)
        resp = client.post("/api/public/reserve", json=_reserve_payload(num.id, mimo.id))
        assert resp.status_code == 200
        token = resp.json()["token_acompanhamento"]
        assert token  # token devolvido UMA vez ao convidado

        # O token puro não pode estar no banco
        raw = db_session.query(Reserva).filter(
            Reserva.token_acompanhamento_hash == token
        ).first()
        assert raw is None

        # O link secreto funciona
        r2 = client.get(f"/api/public/acompanhamento/{token}")
        assert r2.status_code == 200
        assert r2.json()["numero"] == num.numero

        # Token inválido → 404
        assert client.get("/api/public/acompanhamento/nao-existe-token").status_code == 404


class TestRateLimiting:
    def test_login_limitado_apos_tentativas(self, client):
        for _ in range(5):
            client.post("/api/auth/login", json={"email": "admin@teste.com", "senha": "errada"})
        resp = client.post("/api/auth/login", json={"email": "admin@teste.com", "senha": "errada"})
        assert resp.status_code == 429

    def test_reserva_limitada(self, client, db_session):
        num = db_session.query(Numero).filter(Numero.numero == 10).first()
        mimo = mimo_para_numero(db_session, num.numero)
        for _ in range(10):
            client.post(
                "/api/public/reserve",
                json=_reserve_payload(num.id, mimo.id, nome=f"G{len(reserve_limiter._hits)}"),
            )
        resp = client.post("/api/public/reserve", json=_reserve_payload(num.id, mimo.id))
        assert resp.status_code == 429


class TestRN01QuantidadeNumeros:
    def test_aumentar_e_diminuir_preservando_reservas(self, client, db_session, admin_headers):
        # Diminui para 12: números 13..100 disponíveis devem ser removidos
        resp = client.put("/api/admin/numeros/quantidade", json={"total": 12}, headers=admin_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["total"] == 12

        # Reserva um número e depois reduz abaixo dele: reserva PRESERVADA
        num = db_session.query(Numero).filter(Numero.numero == 3).first()
        mimo = mimo_para_numero(db_session, num.numero)
        r = client.post("/api/public/reserve", json=_reserve_payload(num.id, mimo.id))
        assert r.status_code == 200

        resp2 = client.put("/api/admin/numeros/quantidade", json={"total": 2}, headers=admin_headers)
        assert resp2.status_code == 200
        assert resp2.json()["preservados_reservados_ou_confirmados"] >= 1

        db_session.expire_all()
        sobrevivente = db_session.query(Numero).filter(Numero.numero == 3).first()
        assert sobrevivente is not None
        assert sobrevivente.status == "reservado"
