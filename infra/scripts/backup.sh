#!/usr/bin/env bash
# Backup manual do Chá Rifa do Lael (PostgreSQL via pg_dump + configs).
# Uso: ./infra/scripts/backup.sh [diretorio_destino]
set -euo pipefail

DEST="${1:-/opt/backups/projeto-lael}"
STAMP="$(date +%Y%m%d_%H%M%S)"
mkdir -p "$DEST"
cd "$(dirname "$0")/../.."

echo "[backup] destino: $DEST"

# 1) Dump do PostgreSQL (consistente, dentro do container db)
docker compose exec -T db pg_dump -U "${POSTGRES_USER:-lael}" -d "${POSTGRES_DB:-chaderifa}" -F c \
  > "$DEST/chaderifa_${STAMP}.dump"

# 2) Configs necessárias para restaurar (.env SEM secrets de terceiros é opcional;
#    inclua o .env real apenas se o destino for seguro)
cp .env.example "$DEST/env_example_${STAMP}.txt" 2>/dev/null || true
cp infra/Caddyfile "$DEST/Caddyfile_${STAMP}" 2>/dev/null || true

# 3) Retenção: mantém últimos 14 dumps
ls -1t "$DEST"/chaderifa_*.dump 2>/dev/null | tail -n +15 | xargs -r rm -f

echo "[backup] OK -> $DEST/chaderifa_${STAMP}.dump"
