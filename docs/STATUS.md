# Status do Projeto — Chá de Rifa do Lael

Última atualização: 07/11/2026 (v2 — fraldas E mimos reais semeados, faixas regeráveis, edição no painel; testes executados)

> **Estado de execução:** em 07/11/2026 a suíte FOI executada nesta máquina:
> backend **36/36 testes passando** (pytest, SQLite em memória — sem PostgreSQL/Docker
> no ambiente) e frontend **build OK + 8/8 Vitest**. Ressalva mantida: os testes de
> concorrência rodaram contra SQLite; para PostgreSQL real use `TEST_DATABASE_URL`.

## Fase 1 — Estrutura ✅
- Repositório, backend/, frontend/, infra/, docs/ organizados.
- Docker Compose com db (PostgreSQL 16), backend, frontend, proxy Caddy (HTTPS) e serviço de backup `pg_dump` diário (14 cópias).
- `.env.example` completo, sem segredos reais.

## Fase 2 — Banco e API ✅
- Modelos com `Numeric(10,2)` para dinheiro, CHECK constraints e índice único parcial (1 reserva ativa por número).
- Alembic configurado; migração inicial `924d4a3ff1ee` cria o schema novo e atualiza bancos legados in-place (sem apagar dados de desenvolvimento).
- Fluxo reserva → comprovantes → confirmação; estoque; expiração (worker + leitura + reserva); prorrogação; liberação.
- Autenticação JWT; auditoria (`historico_administrativo`); rate limiting (login/reserva); CORS restrito.
- Admin cria administrador via env ou CLI — **sem senha padrão**.

## Fase 3 — Dados da Amazon ✅ (com alternativa documentada)
- Investigação e limitações documentadas em `docs/AMAZON_INTEGRATION.md`.
- Importação manual CSV/JSON operacional via painel/API (`ManualImport`); `AmazonSync` só executa verificação de acessibilidade legítima.
- Dados DEMO rotulados, criados somente fora de produção (`SEED_DEMO`).

## Fase 4 — Site público ✅
- Home, grade 01–100 com legenda sempre visível e estados por cor+texto+ícone (aria-label).
- Polling a cada 12s; número tomado durante a decisão → mensagem amigável (409 tratado no modal).
- Modal de reserva com 5 etapas (presente, mimo, resumo, identificação+consentimento, confirmação).
- WhatsApp com mensagem pronta; página de acompanhamento `/acompanhamento?t=...` (sem login, token com hash no banco).

## Fase 5 — Painel administrativo ✅
- Login protegido, dashboard, reservas (aprovar/rejeitar comprovantes, confirmar, liberar, estender, histórico), produtos/mimos, configurações, exportação CSV/XLSX, auditoria.
- RN-01: endpoint `PUT /api/admin/numeros/quantidade` altera o total preservando reservas existentes.
- **07/11:** fraldas e mimos agora têm EDIÇÃO completa no painel (nome, tamanho/ordem, quantidades, compradas externas, link, imagem, ativo) via `PUT /api/admin/produtos/{id}` e `PUT /api/admin/mimos/{id}` — antes só o preço era editável.
- **07/11:** novo endpoint `POST /api/admin/numeros/regenerar-faixas` + botão "Regerar faixas" — reagrupa os números em faixas contínuas por `ordem_exibicao`/`quantidade_desejada`, preservando reservado/confirmado/compra externa (RN-01).

## Fase 6 — Design e refinamento ✅
- Paleta do briefing como tokens; mobile-first; responsivo até desktop (incluindo painel).
- Acessibilidade: aria-labels com estado textual, foco visível, labels, `prefers-reduced-motion` respeitado nas animações de confete/grade.

## Fase 7 — Testes ✅ (com ressalva de ambiente)
- Backend: **36/36 testes passando** (pytest, executado em 07/11/2026). Cobrem: 4 combinações de aquisição + cálculo Pix, 2 comprovantes obrigatórios, expiração automática e na leitura/reserva, estoque/overbooking, concorrência no mesmo número, prorrogação/liberação, auth/rotas, exportações, índice único parcial, acompanhamento por token, rate limiting, RN-01 (quantidade total, reatribuição, regeneração de faixas preservando reservas e compra externa), Pix bloqueado sem preço, compra externa RN-10 e alerta de capacidade RN-11.
- Frontend: **8/8 testes passando** (Vitest + Testing Library): grade, legenda, estados por texto, seleção, badges de status, formatação BRL.
- **Ressalva honesta:** a máquina atual NÃO tem Docker nem PostgreSQL instalados (`docker: command not found`; não há `C:\Program Files\PostgreSQL`). Os testes de concorrência rodaram contra SQLite em memória. A suíte está pronta para rodar contra PostgreSQL real: defina `TEST_DATABASE_URL=postgresql+psycopg2://...` antes de executar o pytest — nesse modo os testes de concorrência usam múltiplas conexões reais. Rodar em uma máquina com Docker (`docker compose up db`) e executar o pytest com `TEST_DATABASE_URL` apontando para ela.
- Testes E2E Playwright: **não executados** (download de navegadores não realizado neste ambiente). Suíte de componentes cobre os fluxos críticos de UI.

## Fase 8 — Produção ✅ (preparado; publicação pendente de domínio)
- Compose de produção com HTTPS (Caddy), health checks, volumes, backup agendado.
- Guia de publicação e restauração em `docs/PRODUCTION_DEPLOYMENT.md`.
- Publicação efetiva depende de servidor/domínio do casal (fora do escopo: "não publique em serviços externos").

## Pendências que dependem do usuário
0. ~~Lista real de mimos do Lucas~~ **RESOLVIDO (07/11):** o casal colou o texto da lista da Amazon no chat. Os **58 mimos reais** (113 unidades, 7 categorias) estão em `backend/app/data/mimos_reais.py` e são semeados sempre (produção inclusa). Regras de leitura documentadas no cabeçalho do arquivo: "0 de N" = quantidade desejada; "De: R$" = preço anterior; "Ver opções" = preço nulo; "Somente N em estoque" ignorado. ASIN/imagem/link não vieram no texto — o casal pode completar no painel (Mimos → Editar). Os 10 mimos DEMO foram desativados nos bancos de dev.
1. ~~Fralda RN~~ **RESOLVIDO (07/11):** a tabela completa da lista da Talia veio no briefing v2 — as 5 fraldas estão no seed com ASINs e preços reais: RN `B07GQB93FT` (01–10, R$ 39,98), RN+ `B0GY6GG8R7` (11–20, R$ 45,13), P `B07GQ136TS` (21–50, R$ 54,99), M `B07D3SVCTZ` (51–75, sem preço), G `B07X83MH7M` (76–100, R$ 93,90). Bancos de dev reconciliados.
2. ~~5º item (91–100)~~ **RESOLVIDO (07/11):** era a fralda G — não existe mais placeholder inativo.
3. **Preço da fralda M** (Pampers Confort Sec): "Ver opções" na Amazon em 06/11/2026 — informar manualmente no painel (Fraldas → Informar Preço) para habilitar Pix nesse tamanho.
4. Dados de Pix, WhatsApp do casal e mensagens nas Configurações do painel.
5. Criar o primeiro administrador (env ou CLI) no ambiente de produção.
6. Servidor com Docker + domínio para publicar; nessa máquina, rodar a suíte com PostgreSQL real.
7. Aplicar migrações e validar: ver seção "Como validar" abaixo.

## Como validar (comandos prontos — CMD, na pasta do projeto)

```bat
cd "C:\Users\Admin\Documents\Rifa Lael"

REM 1. Migração (se ainda não aplicou)
backend\venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head

REM 2. Testes backend (esperado: 36 passando)
set PYTHONPATH=.
backend\venv\Scripts\python.exe -m pytest backend/tests -q

REM 3. Build do frontend (esperado: compila sem erros)
cd frontend && npm run build && npx vitest run && cd ..
```
