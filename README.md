# Chá de Rifa do Lael 👶✨

Plataforma web full-stack completa, responsiva e pronta para uso em produção, desenvolvida para gerenciar a escolha de presentes e a arrecadação do chá de bebê do **Lael**, previsto para março de 2027, em Fortaleza — CE.

---

## 🌟 Principais Recursos

- **Grade Interativa de 01 a 100:** Visualização em tempo real dos números com 3 estados coloridos (*Disponível em verde*, *Reservado em amarelo*, *Confirmado em cinza*).
- **Escolha 100% Independente de Aquisição:** O convidado escolhe separadamente para o Presente Principal e para o Mimo se deseja comprar pela Amazon ou pagar via Pix (suporte a todas as 4 combinações possíveis).
- **Cálculo Transacional de Pix:** Valores congelados no ato da reserva, calculando o total Pix exclusivamente sobre os itens selecionados nesta modalidade.
- **Dois Comprovantes Obrigatórios:** Rastreamento individual do comprovante do presente e do comprovante do mimo. A confirmação da reserva exige estritamente a aprovação de ambos.
- **Expiração Automática em 72 Horas:** *Background worker* no backend que monitora e libera números expirados sem intervenção manual.
- **Painel Administrativo Completo:** Dashboard de métricas financeiras, aprovação de comprovantes, extensão de prazos, liberação manual, edição de preços e configurações sem alterar código.
- **Exportação de Relatórios:** Download com 1 clique de planilhas formatadas em **CSV** e **Excel (.xlsx)** para controle financeiro e lista de convidados.
- **Integração com WhatsApp:** Geração automática de deep-link com mensagem pré-formatada contendo todos os dados da reserva para envio direto aos pais.
- **LGPD e Privacidade:** Consentimento explícito obrigatório e proteção de dados sensíveis na visualização pública.

---

## 🛠️ Tecnologias Utilizadas

### Backend
- **Linguagem:** Python 3.12
- **Framework:** FastAPI
- **ORM & Banco:** SQLAlchemy 2.0 (com suporte dual a PostgreSQL 16 e SQLite)
- **Validação:** Pydantic V2
- **Segurança:** Hashing `bcrypt`, autenticação JWT (`python-jose`)
- **Tarefas em Segundo Plano:** `asyncio` worker nativo

### Frontend
- **Framework:** Next.js 16 (App Router)
- **Biblioteca:** React 19 + TypeScript
- **Estilização:** Tailwind CSS v4 com paleta personalizada sofisticada
- **Ícones:** Lucide React
- **Efeitos:** Canvas Confetti

### DevOps & Infraestrutura
- **Containers:** Docker & Docker Compose
- **Servidor Web / Proxy:** Caddy / Uvicorn

---

## 🚀 Como Executar o Projeto

### Opção 1: Execução Rápida Local (Sem Docker)

Consulte o [Guia de Instalação Local](docs/LOCAL_SETUP.md) para detalhes passo a passo.

```powershell
# 1. Backend
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:PYTHONPATH=".."
$env:SEED_DEMO="true"
python -c "from backend.app.data.seed_data import init_database_seed; init_database_seed()"
# Administrador (obrigatório, sem senha padrão):
python -m backend.app.create_admin admin@chaderifa.com.br SUA_SENHA_FORTE
uvicorn backend.app.main:app --reload --port 8000

# 2. Frontend (em outro terminal)
cd frontend
npm install
npm run dev
```

Acesse:
- **Site do Convidado:** `http://localhost:3000`
- **Painel do Casal:** `http://localhost:3000/admin` (crie o administrador com `python -m backend.app.create_admin <email> <senha>` — não existe senha padrão)
- **Documentação Swagger:** `http://localhost:8000/docs`

---

### Opção 2: Execução com Docker Compose

Consulte o [Guia de Execução com Docker](docs/DOCKER_GUIDE.md).

```bash
docker compose up -d --build
```

---

## 🧪 Suíte de Testes Automatizados

O sistema conta com testes automatizados cobrindo todas as regras de negócio críticas:

```powershell
$env:PYTHONPATH="."
.\backend\venv\Scripts\pytest -v backend\tests
```

**Resultado dos testes (última execução): 17/17 backend + 8/8 frontend passando.**

> ⚠️ Concorrência real contra PostgreSQL requer `TEST_DATABASE_URL` apontando para um PostgreSQL (Docker indisponível na máquina de desenvolvimento — ver `docs/STATUS.md`).
- ✅ 4 combinações de formas de aquisição e cálculo do Pix.
- ✅ Exigência estrita de aprovação dos 2 comprovantes para confirmação.
- ✅ Worker de expiração automática de 72 horas.
- ✅ Controle de estoque e bloqueio de overbooking de mimos.
- ✅ Proteção contra reservas simultâneas no mesmo número (concorrência).
- ✅ Extensão de prazos e liberação manual.
- ✅ Autenticação administrativa e rotas protegidas.
- ✅ Exportação de planilhas CSV e XLSX.

---

## 📚 Documentação Completa

- [Arquitetura do Sistema](docs/ARCHITECTURE.md)
- [Relatório de Integração com a Amazon](docs/AMAZON_INTEGRATION.md)
- [Guia de Instalação Local](docs/LOCAL_SETUP.md)
- [Guia do Docker Compose](docs/DOCKER_GUIDE.md)
- [Manual de Administração para os Pais (Talia & Lucas)](docs/ADMIN_MANUAL.md)
- [Guia de Deploy em Produção e Backup](docs/PRODUCTION_DEPLOYMENT.md)
