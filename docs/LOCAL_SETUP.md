# Guia de Instalação e Execução Local

Este guia detalha como executar a aplicação **Chá de Rifa do Lael** localmente na sua máquina sem necessidade obrigatória de Docker.

---

## 1. Pré-Requisitos

- **Python 3.12+** instalado.
- **Node.js 20+** e **npm 10+** instalados.
- **Git** instalado.

---

## 2. Passo a Passo do Backend

### 2.1 Criar e Ativar o Ambiente Virtual (se necessário)

No diretório raiz do projeto:

```powershell
# Criação do ambiente virtual
python -m venv backend\venv

# Ativação no Windows PowerShell
.\backend\venv\Scripts\Activate.ps1
```

### 2.2 Instalar as Dependências

```powershell
pip install -r backend\requirements.txt
```

### 2.3 Inicializar o Banco de Dados e Carga Inicial (Seed)

O banco de dados SQLite local será criado automaticamente com 100 números, produtos reais da Amazon, mimos e o usuário administrador padrão:

```powershell
$env:PYTHONPATH="."
.\backend\venv\Scripts\python -c "from backend.app.data.seed_data import init_database_seed; init_database_seed()"
```

### 2.4 Executar o Servidor Backend

```powershell
$env:PYTHONPATH="."
.\backend\venv\Scripts\uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

A documentação interativa da API estará acessível em:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **Healthcheck:** `http://localhost:8000/api/health`

---

## 3. Passo a Passo do Frontend

Abra um novo terminal PowerShell:

```powershell
cd frontend
npm install
npm run dev
```

O site estará disponível em:
- **Site Público:** `http://localhost:3000`
- **Painel Administrativo:** `http://localhost:3000/admin`

---

## 4. Credenciais de Acesso ao Painel

- **URL:** `http://localhost:3000/admin`
- **E-mail:** `admin@chaderifa.com.br`
- **Senha:** a que você definir ao criar o administrador (`python -m backend.app.create_admin`) — não existe senha padrão

---

## 5. Como Executar os Testes Automatizados

Para rodar a suíte completa de testes unitários e de integração:

```powershell
$env:PYTHONPATH="."
.\backend\venv\Scripts\pytest -v backend\tests
```
