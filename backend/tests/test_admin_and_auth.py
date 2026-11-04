def test_admin_login_and_token(client):
    # Valid login
    resp = client.post("/api/auth/login", json={
        "email": "admin@teste.com",
        "senha": "senha123"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Invalid password
    bad_resp = client.post("/api/auth/login", json={
        "email": "admin@teste.com",
        "senha": "senha-errada"
    })
    assert bad_resp.status_code == 401


def test_protected_routes_require_auth(client):
    resp = client.get("/api/admin/dashboard")
    assert resp.status_code == 401


def test_dashboard_and_settings(client, admin_headers):
    # Dashboard
    dash_resp = client.get("/api/admin/dashboard", headers=admin_headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "total_numeros" in dash_data
    assert "numeros_disponiveis" in dash_data

    # Update settings
    cfg_resp = client.put(
        "/api/admin/config",
        headers=admin_headers,
        json={"configuracoes": {"whatsapp_casal": "85988889999", "chave_pix": "novo@pix.com"}}
    )
    assert cfg_resp.status_code == 200

    # Verify public config reflects updated settings
    pub_cfg = client.get("/api/public/config")
    assert pub_cfg.status_code == 200
    assert pub_cfg.json()["whatsapp_casal"] == "85988889999"
    assert pub_cfg.json()["chave_pix"] == "novo@pix.com"


def test_export_endpoints(client, admin_headers):
    # Export CSV
    csv_resp = client.get("/api/admin/export/reservations?format_type=csv", headers=admin_headers)
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]

    # Export Excel
    xlsx_resp = client.get("/api/admin/export/reservations?format_type=xlsx", headers=admin_headers)
    assert xlsx_resp.status_code == 200
    assert "openxmlformats" in xlsx_resp.headers["content-type"]

    # Export Pix CSV
    pix_resp = client.get("/api/admin/export/pix?format_type=csv", headers=admin_headers)
    assert pix_resp.status_code == 200
    assert "text/csv" in pix_resp.headers["content-type"]
