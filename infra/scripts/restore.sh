#!/usr/bin/env bash
# Restauração do backup PostgreSQL. USO COM CUIDADO — sobrescreve o banco atual.
# Uso: ./infra/scripts/restore.sh /opt/backups/projeto-lael/chaderifa_AAAAMMDD_HHMMSS.dump
set -euo pipefail
DUMP="${1:?Informe o arquivo .dump}"
[ -f "$DUMP" ] || { echo "Arquivo não encontrado: $DUMP"; exit 1; }
cd "$(dirname "$0")/../.."

echo "ATENÇÃO: isso vai restaurar o banco sobre os dados atuais."
read -r -p "Digite RESTAURAR para confirmar: " CONF
[ "$CONF" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }

docker compose exec -T db psql -U "${POSTGRES_USER:-lael}" -d postgres \
  -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='${POSTGRES_DB:-chaderifa}' AND pid <> pg_backend_pid();" || true
docker compose exec -T db psql -U "${POSTGRES_USER:-lael}" -d "${POSTGRES_DB:-chaderifa}" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T db pg_restore -U "${POSTGRES_USER:-lael}" -d "${POSTGRES_DB:-chaderifa}" --no-owner < "$DUMP"
echo "[restore] concluído. Verifique: curl http://localhost/api/health"
