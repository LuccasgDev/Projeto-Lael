#!/usr/bin/env bash
# Verificação rápida de saúde local (roda na VM ou via SSH).
set -uo pipefail
cd "$(dirname "$0")/../.."
echo "== containers =="
docker compose ps
echo "== backend /api/health =="
curl -fsS http://localhost/api/health || curl -fsS http://localhost:8000/api/health || echo "FALHA backend"
echo "== frontend =="
curl -fsS -o /dev/null -w "HTTP %{http_code}\n" http://localhost/ || curl -fsS -o /dev/null -w "HTTP %{http_code}\n" http://localhost:3000/ || echo "FALHA frontend"
echo "== disco =="
df -h / | tail -1
