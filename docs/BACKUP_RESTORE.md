# Backup e restauração

## O que é salvo

- **PostgreSQL** — dump consistente via `pg_dump -F c` (não é cópia crua do arquivo).
- **Configs** — `.env.example` e `infra/Caddyfile` (o `.env` real deve ser guardado separadamente e com segurança).
- O serviço `backup` do compose faz isso **automaticamente 1×/dia** e mantém 14 dumps no volume `backups_data`.

## Backup manual

```bash
./infra/scripts/backup.sh                      # destino padrão /opt/backups/projeto-lael
./infra/scripts/backup.sh /mnt/disco/backup    # destino customizado
```

## Copiar backups para fora da VM (recomendado)

```bash
# via SCP/rsync para outro servidor ou máquina local
rsync -avz /opt/backups/projeto-lael/ usuario@outro-host:/backups/lael/
```

## Restaurar

```bash
./infra/scripts/restore.sh /opt/backups/projeto-lael/chaderifa_AAAAMMDD_HHMMSS.dump
```

O script pede confirmação digitando `RESTAURAR`, derruba conexões ativas, recria o schema e restaura o dump.

## Verificar integridade de um dump

```bash
# dentro do container db
pg_restore -l /caminho/do/arquivo.dump | head   # lista o conteúdo sem restaurar
```

## Backup antes de atualização

O `infra/scripts/update.sh` já executa `backup.sh` antes de qualquer `git pull`. Se o healthcheck falhar após o update, faça rollback:

```bash
git checkout <commit-anterior>
docker compose build && docker compose up -d
./infra/scripts/restore.sh <dump-feito-antes-do-update>   # se necessário
```

## Recuperação em VM nova

1. Instalar Docker + clonar repo (ver `DEPLOY_PROXMOX.md`).
2. Restaurar o dump: `./infra/scripts/restore.sh <dump>`.
3. `docker compose up -d` e testar `/api/health`.
