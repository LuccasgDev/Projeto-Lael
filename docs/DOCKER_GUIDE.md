# Guia de Execução com Docker e Docker Compose

O projeto conta com configuração completa de containers para execução padronizada em qualquer servidor Linux, Windows ou macOS com suporte a Docker.

---

## 1. Arquitetura dos Containers

O arquivo `docker-compose.yml` orquestra três serviços integrados em uma rede isolada (`rifa_network`):

1. **`db` (PostgreSQL 16 Alpine):**
   - Banco de dados relacional principal para produção.
   - Volume nomeado persistente `postgres_data`.
   - Healthcheck nativo com `pg_isready`.
2. **`backend` (FastAPI / Python 3.12 Slim):**
   - Imagem otimizada multi-stage.
   - Aguarda o banco de dados estar 100% saudável antes de iniciar.
   - Inicializa as tabelas, seeds e o worker de expiração em segundo plano.
3. **`frontend` (Next.js 16 / Node.js 20 Alpine):**
   - Imagem de produção compilada com Turbopack.
   - Executa como usuário não-root (`nextjs`) para máxima segurança.

---

## 2. Comandos para Execução

### 2.1 Configurar o Arquivo `.env`

Copie o arquivo de exemplo:

```bash
cp .env.example .env
```

### 2.2 Subir os Containers em Segundo Plano

```bash
docker compose up -d --build
```

### 2.3 Verificar o Status dos Serviços

```bash
docker compose ps
```

### 2.4 Acompanhar os Logs da Aplicação

```bash
# Logs de todos os serviços:
docker compose logs -f

# Logs específicos do backend:
docker compose logs -f backend

# Logs do worker de expiração:
docker compose logs -f backend | grep EXPIRATION_WORKER
```

---

## 3. URLs de Acesso

- **Aplicação Pública:** `http://localhost:3000`
- **Painel Administrativo:** `http://localhost:3000/admin`
- **Swagger Docs:** `http://localhost:8000/docs`
- **Healthcheck:** `http://localhost:8000/api/health`

---

## 4. Parar ou Reiniciar os Serviços

```bash
# Para pausar mantendo os dados no volume:
docker compose stop

# Para derrubar os containers preservando os dados:
docker compose down

# Para reiniciar um serviço específico:
docker compose restart backend
```
