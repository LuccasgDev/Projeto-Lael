#!/usr/bin/env bash
# Atualização segura: backup -> git pull -> rebuild -> migrate -> restart -> health.
# Uso: ./infra/scripts/update.sh [branch]
set -euo pipefail
BRANCH="${1:-main}"
cd "$(dirname "$0")/../.."

echo "[update] 1/6 backup pré-atualização"
./infra/scripts/backup.sh || echo "[update] backup falhou — abortando por segurança" && exit 1

echo "[update] 2/6 git fetch/pull ($BRANCH)"
git fetch origin && git checkout "$BRANCH" && git pull origin "$BRANCH"

echo "[update] 3/6 rebuild das imagens"
docker compose build

echo "[update] 4/6 migrations (Alembic — aditivas)"
docker compose run --rm backend alembic upgrade head || echo "[update] alembic falhou — verifique manualmente"

echo "[update] 5/6 restart"
docker compose up -d

echo "[update] 6/6 healthcheck"
sleep 10
curl -fsS http://localhost/api/health && echo " [OK]" || { echo "[update] FALHA no healthcheck — considere rollback (git checkout versão anterior + rebuild)"; exit 1; }
echo "[update] concluído."
