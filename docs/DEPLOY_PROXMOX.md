# Deploy no Proxmox (self-hosting)

Guia completo para hospedar o Chá Rifa do Lael em uma VM Ubuntu dentro do Proxmox VE.

## Arquitetura

```
Proxmox VE
└── VM: lael-server (Ubuntu Server 24.04 LTS)
    └── Docker Engine + Compose
        ├── frontend   (Next.js — build de produção)
        ├── backend    (FastAPI/Uvicorn — sem --reload)
        ├── db         (PostgreSQL 16 — dados em volume)
        ├── proxy      (Caddy — HTTPS automático, opcional)
        ├── backup     (pg_dump diário, 14 retenções)
        └── cloudflared (Tunnel — profile opcional)
```

O browser fala **same-origin** com o frontend; o Next.js faz proxy de `/api/*` para o backend via `BACKEND_INTERNAL_URL` (rede Docker interna). O backend **nunca é exposto diretamente**.

## Etapa 1 — Criar a VM

No Proxmox (GUI ou CLI):

- **Nome:** `lael-server`
- **ISO:** Ubuntu Server 24.04 LTS
- **CPU:** 2 vCPU · **RAM:** 4 GB · **Disco:** 32–64 GB
- **Bridge:** `vmbr0` · **IP:** fixo ou reserva DHCP
- **SSH:** habilitado na instalação

## Etapa 2 — Preparar o Ubuntu

```bash
sudo apt update && sudo apt upgrade -y
# Docker oficial
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER   # relogar depois
# Estrutura de diretórios
sudo mkdir -p /opt/backups/projeto-lael /opt/lael
sudo chown -R $USER:$USER /opt/lael /opt/backups
```

Firewall (se usar UFW): libere apenas SSH; o site sai pelo Tunnel ou pelo proxy.

## Etapa 3 — Transferir o projeto

```bash
git clone <URL-DO-REPO> /opt/lael/projeto
cd /opt/lael/projeto
cp .env.example .env
nano .env   # preencher os valores obrigatórios (ver abaixo)
```

## Etapa 4 — Variáveis obrigatórias no `.env`

```env
SECRET_KEY=<openssl rand -hex 32>          # OBRIGATÓRIO — JWT admin
POSTGRES_PASSWORD=<senha forte>            # OBRIGATÓRIO
POSTGRES_USER=lael
POSTGRES_DB=chaderifa
ADMIN_EMAIL=<email do casal>               # cria o 1º admin no boot
ADMIN_PASSWORD=<senha forte>
CORS_ORIGINS=https://seudominio.com.br
SCAVIO_ENABLED=false                        # true só após configurar a key
SCAVIO_API_KEY=
NEXT_PUBLIC_API_URL=/api
SITE_DOMAIN=seudominio.com.br               # ou :80 para teste local
# CLOUDFLARE_TUNNEL_TOKEN=                  # só se usar o Tunnel
```

## Etapa 5 — Subir

```bash
docker compose up -d --build
docker compose ps          # aguardar healthy
docker compose logs -f     # acompanhar logs
```

## Etapa 6 — Testar

- `http://<IP-da-VM>/` → home do site
- `http://<IP-da-VM>/admin` → login do painel
- `curl http://<IP-da-VM>/api/health` → `{"status":"healthy"}`
- Reserve um número de teste → confirme no painel admin.

## Etapa 7 — Publicar (Cloudflare Tunnel)

Ver `docs/CLOUDFLARE_TUNNEL.md`. Resumo: criar tunnel no dashboard Cloudflare, apontar `rifa.seudominio.com.br → http://frontend:3000`, colocar o token em `CLOUDFLARE_TUNNEL_TOKEN` e subir com `docker compose --profile tunnel up -d`.

## Etapa 8 — Backup

```bash
./infra/scripts/backup.sh                 # manual
# O serviço 'backup' do compose já faz pg_dump diário (14 retenções)
```

Restauração: `docs/BACKUP_RESTORE.md`.

## Atualização

```bash
./infra/scripts/update.sh    # backup → git pull → build → migrate → restart → health
```

## Manutenção remota

- **SSH:** acesso direto à VM.
- **Tailscale:** instale na VM e no PC (`tailscale up`) para acessar `http://lael-server:3000` sem expor portas.
- **Logs:** `docker compose logs -f backend|frontend|db`
