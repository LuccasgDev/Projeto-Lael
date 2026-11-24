# Docker — referência rápida

## Produção (Proxmox/VPS)

```bash
docker compose up -d --build     # sobe tudo
docker compose ps                # status + health
docker compose logs -f           # logs
docker compose down              # para (dados persistem nos volumes)
docker compose restart           # reinicia
docker compose --profile tunnel up -d   # inclui Cloudflare Tunnel
```

## Desenvolvimento (hot reload)

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
# frontend → http://localhost:3000  |  backend → http://localhost:8000/docs
```

## Arquitetura de rede

- `rifa_network` (bridge interna): frontend ↔ backend ↔ db ↔ proxy ↔ backup.
- **Somente o `proxy` (Caddy) publica portas** (80/443). Se usar Tunnel no lugar do Caddy, o proxy pode ficar desligado — o Tunnel aponta direto para `frontend:3000`.
- O browser acessa `/api` **same-origin**; o Next.js faz proxy para `BACKEND_INTERNAL_URL=http://backend:8000` via `rewrites()` em `next.config.ts`. O backend nunca é exposto.

## Persistência

| Dado | Onde fica |
|---|---|
| PostgreSQL | volume `postgres_data` |
| Backups pg_dump | volume `backups_data` + `./infra/backup` |
| Caddy certs/config | volumes `caddy_data`, `caddy_config` |
| SQLite (dev) | `./rifa_lael.db` montado no container |

**Uploads/comprovantes:** o sistema não armazena arquivos — comprovantes são enviados por WhatsApp e o banco guarda apenas `comprovante_url` (link). Não há volume de uploads necessário hoje; se um upload local for implementado, use um volume nomeado montado em `/app/uploads`.

## Migrations

O backend **não roda Alembic no boot** — rode manualmente após deploy:

```bash
docker compose exec backend alembic upgrade head
# ou via update.sh (já incluído)
```

## Variáveis-chave

Ver `.env.example`. Obrigatórias em produção: `SECRET_KEY`, `POSTGRES_PASSWORD`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`. Opcionais: `SCAVIO_*`, `CLOUDFLARE_TUNNEL_TOKEN`, `SITE_DOMAIN`.
