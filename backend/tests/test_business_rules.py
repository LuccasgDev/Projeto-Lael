from datetime import datetime, timedelta
from conftest import mimo_para_numero
from backend.app.models.models import Numero, Mimo, Reserva, Comprovante, ProdutoPrincipal, utcnow
from backend.app.services.expiration_worker import check_and_expire_reservations


def test_four_acquisition_combinations_and_pix_totals(client, db_session):
    """
    Tests the 4 distinct combinations of (Presente, Mimo) acquisition
    and verifies that valor_pix_total is calculated strictly from Pix choices.
    """
    combinations = [
        ("amazon", "amazon"),
        ("amazon", "pix"),
        ("pix", "amazon"),
        ("pix", "pix"),
        ("local", "local"),
        ("local", "pix"),
        ("amazon", "local"),
    ]

    for idx, (f_pres, f_mimo) in enumerate(combinations, start=1):
        num = db_session.query(Numero).filter(Numero.numero == idx).first()
        # Regra fixa: o mimo correto depende da faixa do número (RN/P fixo, M livre)
        mimo = mimo_para_numero(db_session, num.numero)
        preco_mimo = mimo.preco_atual
        preco_pres = num.produto_principal.preco_atual

        payload = {
            "numero_id": num.id,
            "mimo_id": mimo.id,
            "nome_convidado": f"Convidado {idx}",
            "whatsapp": "85999990000",
            "autoriza_nome_publico": True,
            "forma_presente": f_pres,
            "forma_mimo": f_mimo,
            "consentimento_lgpd": True,
        }

        resp = client.post("/api/public/reserve", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        expected_pix = 0.0
        if f_pres == "pix":
            expected_pix += float(preco_pres)
        if f_mimo == "pix":
            expected_pix += float(preco_mimo)
        expected_pix = round(expected_pix, 2)

        assert data["valor_pix_total"] == expected_pix
        assert data["forma_presente"] == f_pres
        assert data["forma_mimo"] == f_mimo

        # Verify 2 vouchers created
        assert len(data["comprovantes"]) == 2
        tipos = {c["tipo_item"] for c in data["comprovantes"]}
        assert tipos == {"presente", "mimo"}


def test_confirmation_strictly_requires_both_vouchers(client, db_session, admin_headers):
    """
    Verifies that a reservation CANNOT be confirmed until BOTH vouchers are approved.
    """
    num = db_session.query(Numero).filter(Numero.numero == 1).first()
    mimo = mimo_para_numero(db_session, num.numero)

    # Create reservation
    res_resp = client.post("/api/public/reserve", json={
        "numero_id": num.id,
        "mimo_id": mimo.id,
        "nome_convidado": "Pedro Alves",
        "whatsapp": "85988887777",
        "autoriza_nome_publico": False,
        "forma_presente": "pix",
        "forma_mimo": "amazon",
        "consentimento_lgpd": True,
    })
    assert res_resp.status_code == 200
    reserva_id = res_resp.json()["id"]

    # 1. Attempt to confirm immediately (0 vouchers approved) -> MUST FAIL (400)
    conf_resp = client.post(f"/api/admin/reservations/{reserva_id}/confirm", headers=admin_headers)
    assert conf_resp.status_code == 400
    assert "comprovantes" in conf_resp.json()["detail"].lower()

    # Get vouchers
    comps = db_session.query(Comprovante).filter(Comprovante.reserva_id == reserva_id).all()
    comp_pres = next(c for c in comps if c.tipo_item == "presente")
    comp_mimo = next(c for c in comps if c.tipo_item == "mimo")

    # 2. Approve ONLY the first voucher
    act1 = client.post(
        f"/api/admin/comprovantes/{comp_pres.id}/action",
        headers=admin_headers,
        json={"status": "aprovado", "observacao": "Comprovante Pix do presente OK"}
    )
    assert act1.status_code == 200

    # Attempt to confirm with only 1 approved -> MUST STILL FAIL (400)
    conf_resp2 = client.post(f"/api/admin/reservations/{reserva_id}/confirm", headers=admin_headers)
    assert conf_resp2.status_code == 400

    # 3. Approve the second voucher
    act2 = client.post(
        f"/api/admin/comprovantes/{comp_mimo.id}/action",
        headers=admin_headers,
        json={"status": "aprovado", "observacao": "Comprovante Amazon do mimo OK"}
    )
    assert act2.status_code == 200

    # 4. Attempt to confirm with BOTH approved -> MUST SUCCEED (200)
    conf_resp3 = client.post(f"/api/admin/reservations/{reserva_id}/confirm", headers=admin_headers)
    assert conf_resp3.status_code == 200

    # Verify number status is now 'confirmado'
    db_session.refresh(num)
    assert num.status == "confirmado"


def test_automatic_expiration_worker(client, db_session):
    """
    Tests that reservations with expira_em in the past are marked as 'expirada'
    and the number is restored to 'disponivel'.
    """
    num = db_session.query(Numero).filter(Numero.numero == 5).first()
    mimo = mimo_para_numero(db_session, num.numero)

    res_resp = client.post("/api/public/reserve", json={
        "numero_id": num.id,
        "mimo_id": mimo.id,
        "nome_convidado": "Lucas Silva",
        "whatsapp": "85977776666",
        "autoriza_nome_publico": True,
        "forma_presente": "amazon",
        "forma_mimo": "amazon",
        "consentimento_lgpd": True,
    })
    assert res_resp.status_code == 200
    reserva_id = res_resp.json()["id"]

    # Verify number is 'reservado'
    db_session.refresh(num)
    assert num.status == "reservado"

    # Simulate expiration by moving expira_em 5 minutes into the past
    reserva = db_session.query(Reserva).filter(Reserva.id == reserva_id).first()
    reserva.expira_em = utcnow() - timedelta(minutes=5)
    db_session.commit()

    # Run the expiration worker
    expired_count = check_and_expire_reservations(db_session)
    assert expired_count == 1

    # Verify status changed and number is available again
    db_session.refresh(reserva)
    db_session.refresh(num)
    assert reserva.status == "expirada"
    assert num.status == "disponivel"


def test_stock_control_prevents_mimo_overbooking(client, db_session):
    """
    Tests that a mimo with limited quantity cannot be reserved once exhausted.
    """
    # Create an exclusive mimo with stock = 1
    exclusive_mimo = Mimo(
        nome="Mimo Exclusivo Estoque 1",
        preco_atual=50.0,
        quantidade_desejada=1,
        quantidade_comprada_externa=0,
        ativo=True,
    )
    db_session.add(exclusive_mimo)
    db_session.commit()
    db_session.refresh(exclusive_mimo)

    # Faixa M (36-65): mimo à escolha do participante — estoque limitado se aplica
    fralda_m = db_session.query(ProdutoPrincipal).filter(ProdutoPrincipal.tamanho == "M", ProdutoPrincipal.ativo == True).first()
    if fralda_m and fralda_m.preco_atual is None:
        fralda_m.preco_atual = 50.0  # Pix exige preço conhecido (RN-08 v2)
    if not fralda_m:
        fralda_m = ProdutoPrincipal(
            nome="Fralda M Teste", tamanho="M", categoria="Fraldas",
            preco_atual=50.0, quantidade_desejada=30, ativo=True,
        )
        db_session.add(fralda_m)
        db_session.commit()
        db_session.refresh(fralda_m)
    num1 = Numero(numero=40, produto_principal_id=fralda_m.id, status="disponivel")
    num2 = Numero(numero=41, produto_principal_id=fralda_m.id, status="disponivel")
    db_session.add_all([num1, num2])
    db_session.commit()
    db_session.refresh(num1)
    db_session.refresh(num2)

    # 1. First guest reserves -> OK
    resp1 = client.post("/api/public/reserve", json={
        "numero_id": num1.id,
        "mimo_id": exclusive_mimo.id,
        "nome_convidado": "Convidado 1",
        "whatsapp": "85911112222",
        "autoriza_nome_publico": True,
        "forma_presente": "pix",
        "forma_mimo": "pix",
        "consentimento_lgpd": True,
    })
    assert resp1.status_code == 200

    # 2. Second guest tries to choose the same mimo -> MUST FAIL (409 Conflict)
    resp2 = client.post("/api/public/reserve", json={
        "numero_id": num2.id,
        "mimo_id": exclusive_mimo.id,
        "nome_convidado": "Convidado 2",
        "whatsapp": "85933334444",
        "autoriza_nome_publico": True,
        "forma_presente": "pix",
        "forma_mimo": "pix",
        "consentimento_lgpd": True,
    })
    assert resp2.status_code == 409
    assert "esgotou" in resp2.json()["detail"].lower()


def test_extend_and_release_reservation(client, db_session, admin_headers):
    """
    Tests admin extension of deadline and manual release.
    """
    num = db_session.query(Numero).filter(Numero.numero == 7).first()
    mimo = mimo_para_numero(db_session, num.numero)

    res_resp = client.post("/api/public/reserve", json={
        "numero_id": num.id,
        "mimo_id": mimo.id,
        "nome_convidado": "Carla Mendes",
        "whatsapp": "85955554444",
        "autoriza_nome_publico": False,
        "forma_presente": "pix",
        "forma_mimo": "pix",
        "consentimento_lgpd": True,
    })
    reserva_id = res_resp.json()["id"]

    # Extend deadline by 48h
    ext_resp = client.post(
        f"/api/admin/reservations/{reserva_id}/extend",
        headers=admin_headers,
        json={"horas_adicionais": 48}
    )
    assert ext_resp.status_code == 200
    assert "48" in ext_resp.json()["message"]

    # Release reservation
    rel_resp = client.post(
        f"/api/admin/reservations/{reserva_id}/release",
        headers=admin_headers,
        params={"motivo": "Convidado desistiu"}
    )
    assert rel_resp.status_code == 200

    db_session.refresh(num)
    assert num.status == "disponivel"
