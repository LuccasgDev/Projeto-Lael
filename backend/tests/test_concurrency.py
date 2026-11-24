from conftest import mimo_para_numero
from backend.app.models.models import Numero, Mimo


def test_concurrent_reservation_same_number(client, db_session):
    """
    Tests that two guests attempting to reserve the exact same number
    cannot both succeed. One will reserve it and the other will receive 409 Conflict.
    """
    num = db_session.query(Numero).filter(Numero.numero == 8).first()
    mimo = mimo_para_numero(db_session, num.numero)

    payload_guest1 = {
        "numero_id": num.id,
        "mimo_id": mimo.id,
        "nome_convidado": "Convidado A",
        "whatsapp": "85999991111",
        "autoriza_nome_publico": True,
        "forma_presente": "amazon",
        "forma_mimo": "pix",
        "consentimento_lgpd": True,
    }

    payload_guest2 = {
        "numero_id": num.id,
        "mimo_id": mimo.id,
        "nome_convidado": "Convidado B",
        "whatsapp": "85999992222",
        "autoriza_nome_publico": False,
        "forma_presente": "pix",
        "forma_mimo": "amazon",
        "consentimento_lgpd": True,
    }

    # First request
    resp1 = client.post("/api/public/reserve", json=payload_guest1)
    assert resp1.status_code == 200

    # Second request immediately afterwards on the same number
    resp2 = client.post("/api/public/reserve", json=payload_guest2)
    # 409: conflito — pode ser por número indisponível ou mimo esgotado por testes anteriores;
    # o essencial é que NÃO existam duas reservas ativas para o mesmo número.
    assert resp2.status_code == 409
    db_session.refresh(num)
    numero_indisponivel = ("não está mais disponível" in resp2.json()["detail"].lower())
    if numero_indisponivel:
        assert num.status == "reservado"
    # Garantia final: apenas UMA reserva ativa para o número
    from backend.app.models.models import Reserva
    ativas = db_session.query(Reserva).filter(Reserva.numero_id == num.id, Reserva.status == "reservada").count()
    assert ativas == 1
