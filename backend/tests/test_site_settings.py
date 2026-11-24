"""
Testes do sistema de configurações dinâmicas do site (site_settings).
"""
import pytest
from sqlalchemy.orm import Session

from backend.app.models.models import Configuracao
from backend.app.services import site_settings as ss


class TestSiteSettingsPublicEndpoint:
    def test_public_retorna_apenas_campos_publicos(self, client):
        res = client.get("/api/public/site-settings")
        assert res.status_code == 200
        data = res.json()
        # Categorias públicas presentes
        assert "premio" in data and "popup" in data and "evento" in data
        # Campo privado NÃO deve aparecer (site.pix.chave é public=False)
        assert "chave" not in data.get("pix", {})

    def test_public_defaults(self, client):
        data = client.get("/api/public/site-settings").json()
        assert data["premio"]["valor"] == "R$ 250,00"
        assert data["popup"]["ativo"] is True
        assert data["sistema"]["modo_manutencao"] is False


class TestSiteSettingsAdminEndpoint:
    def test_admin_retorna_schema_completo(self, client, admin_headers):
        res = client.get("/api/admin/site-settings", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert "categories" in data and "fields" in data
        assert "site.premio.valor" in data["fields"]
        # Campo privado aparece no admin (com 🔒 no front)
        assert "site.pix.chave" in data["fields"]

    def test_admin_exige_auth(self, client):
        assert client.get("/api/admin/site-settings").status_code in (401, 403)

    def test_update_e_persistencia(self, client, admin_headers, db_session):
        res = client.put(
            "/api/admin/site-settings",
            headers=admin_headers,
            json={"configuracoes": {"site.premio.valor": "R$ 500,00"}},
        )
        assert res.status_code == 200
        assert "site.premio.valor" in res.json()["updated"]

        # Persiste no banco
        cfg = db_session.query(Configuracao).filter(Configuracao.chave == "site.premio.valor").first()
        assert cfg is not None and cfg.valor == "R$ 500,00"

        # Público reflete
        pub = client.get("/api/public/site-settings").json()
        assert pub["premio"]["valor"] == "R$ 500,00"

    def test_update_rejeita_chave_desconhecida(self, client, admin_headers):
        res = client.put(
            "/api/admin/site-settings",
            headers=admin_headers,
            json={"configuracoes": {"site.inexistente.campo": "x"}},
        )
        assert res.status_code == 200
        assert len(res.json()["errors"]) == 1

    def test_update_valida_booleano_e_cor(self, client, admin_headers):
        res = client.put(
            "/api/admin/site-settings",
            headers=admin_headers,
            json={"configuracoes": {
                "site.popup.ativo": "talvez",
                "site.aparencia.cor_primaria": "azul",
            }},
        )
        errors = res.json()["errors"]
        assert len(errors) == 2

    def test_write_through_alias_legado(self, client, admin_headers, db_session):
        """site.evento.nome deve sincronizar com a chave legada nome_evento."""
        client.put(
            "/api/admin/site-settings",
            headers=admin_headers,
            json={"configuracoes": {"site.evento.nome": "Chá do Enzo"}},
        )
        legacy = db_session.query(Configuracao).filter(Configuracao.chave == "nome_evento").first()
        assert legacy is not None and legacy.valor == "Chá do Enzo"

    def test_reset_categoria(self, client, admin_headers, db_session):
        client.put(
            "/api/admin/site-settings",
            headers=admin_headers,
            json={"configuracoes": {"site.premio.valor": "R$ 999,00"}},
        )
        res = client.post("/api/admin/site-settings/reset/premio", headers=admin_headers)
        assert res.status_code == 200
        # Após reset, valor volta ao default do schema
        pub = client.get("/api/public/site-settings").json()
        assert pub["premio"]["valor"] == "R$ 250,00"


class TestSiteSettingsBackendEffects:
    def test_reserva_bloqueada_quando_desativada(self, client, db_session):
        """site.reserva.ativa=false deve impedir novas reservas (HTTP 403)."""
        from backend.app.services.site_settings import update_settings
        from backend.app.models.models import Numero, Mimo
        from backend.app.services.numero_regra import resolver_mimo_fixo

        update_settings(db_session, {"site.reserva.ativa": False})

        num = db_session.query(Numero).filter(Numero.status == "disponivel").first()
        assert num is not None
        mimo = resolver_mimo_fixo(db_session, num.numero) or db_session.query(Mimo).first()

        r = client.post("/api/public/reserve", json={
            "numero_id": num.id,
            "mimo_id": mimo.id,
            "nome_convidado": "Teste Bloqueio",
            "whatsapp": "85999990000",
            "autoriza_nome_publico": False,
            "forma_presente": "amazon",
            "forma_mimo": "amazon",
            "consentimento_lgpd": True,
        })
        assert r.status_code == 403
        assert "encerradas" in r.json()["detail"].lower() or "temporariamente" in r.json()["detail"].lower()

        # Reativa e confirma que o bloqueio era a causa (não outro erro)
        update_settings(db_session, {"site.reserva.ativa": True})
