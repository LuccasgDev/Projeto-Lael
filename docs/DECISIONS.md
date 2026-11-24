# Decisões e Premissas — Chá Rifa do Lael

Registro de decisões técnicas e de produto tomadas durante a implementação,
com as premissas adotadas quando faltava informação do usuário.

> **v2 (06/11/2026):** os 100 números passaram a representar FRALDAS da lista da
> Talia (RN-01 v2), o mimo é escolhido depois do número (RN-02 v2), e foram
> adicionadas as regras RN-10 (compra externa) e RN-11 (alerta de capacidade).
> **v2 final (§4):** a grade é SIMPLES e única (01–100, sem cabeçalhos de tamanho —
> a fralda só aparece depois do clique) e a reserva acontece em DOIS popups
> em sequência (mimo → dados+pagamento).

## Decisões de arquitetura

| # | Decisão | Justificativa |
|---|---------|---------------|
| D-01 | Backend FastAPI + SQLAlchemy 2 + Alembic; frontend Next.js 16 (App Router) + TypeScript + Tailwind | Stack definida no briefing |
| D-02 | PostgreSQL em produção; SQLite **apenas** para desenvolvimento local | Docker indisponível na máquina de desenvolvimento durante a implementação (comando `docker` não existe no PATH). Testes de concorrência **reais** exigem PostgreSQL; no ambiente atual só é possível executá-los contra SQLite — limitação declarada em `docs/STATUS.md` |
| D-03 | Dinheiro em `Numeric(10,2)` (Decimal), nunca float | Requisito do briefing; evita erro de ponto flutuante em valores Pix |
| D-04 | Índice único parcial `uq_reserva_ativa_por_numero` (`numero_id` WHERE `status='reservada'`) | Uma reserva ativa por número garantida no BANCO, não no frontend |
| D-05 | Expiração por worker agendado **e** verificada em toda leitura pública e na criação de reserva (RN-06) | Nunca depende do navegador; reads idempotentes |
| D-06 | Token de acompanhamento: `token_urlsafe(24)`, apenas o **hash SHA-256** é persistido | Link secreto não adivinhável sem login (§4); vazamento do banco não expõe os links |
| D-07 | Rate limiting em memória (janela deslizante): login 5/5min, reserva 10/min por IP | Escala pequena; sem Redis/filas externas por decisão do briefing. Para múltiplas réplicas, trocar por limitador compartilhado |
| D-08 | Sessão admin via JWT Bearer em `Authorization` header | Alternativa a cookie+CSRF documentada no briefing ("ou alternativa equivalente"); token nunca em localStorage de terceiros |
| D-09 | CORS restrito via `CORS_ORIGINS` (vírgula-separada); sem `allow_origins=["*"]` | §7 Segurança |
| D-10 | Proxy Caddy com HTTPS automático + serviço `backup` (pg_dump diário, 14 cópias) no Compose | §7; backup agendado dentro do Compose sem serviços externos |
| D-11 | **v2:** `tamanho` e `ordem_exibicao` em `produtos_principais`; números gerados das quantidades por tamanho (10 RN+ / 30 P / 25 M / 25 G / 10 a definir) | RN-01 v2; ordem editável no painel |
| D-12 | **v2:** `preco_atual` NULÁVEL — a fralda M aparecia como "Ver opções" na Amazon; Pix é bloqueado para item sem preço (frontend e backend) e o casal informa o valor manualmente | RN-08 v2 |
| D-13 | **v2:** número pode ficar `compra_externa` (cinza, `origem_ocupacao` registrada); mimo tem `quantidade_comprada_externa` ajustável no painel | RN-10 |
| D-14 | **v2:** dashboard compara mimos disponíveis × números não confirmados e exibe alerta quando insuficiente; sem exceção de reserva sem mimo até decisão do casal | RN-11 |
| D-15 | **v2 final:** grade pública simples (01–100, estados por cor+ícone+aria-label); fralda revelada só no popup — atendendo ao §4 final, que revogou o agrupamento por tamanho da versão anterior da v2 | §4 v2 |
| D-16 | **v2 final:** modal de reserva em 2 popups (mimo → resumo+pagamento+identificação numa tela), com retorno automático ao popup certo quando o número ou mimo é tomado (409 tratado por mensagem) | §4 v2 |
| D-17 | **v2 final:** importação de mimos por TEXTO colado (`POST /api/sync/import-texto`, formato `Nome; qtd; preço`), além de CSV/JSON; preço ausente fica NULO (nunca R$ 0 disfarçado) | §3 v2 |
| D-18 | `preco_manual` do modelo sugerido é atendido por "Informar Preço" no painel, que grava em `preco_atual` com `preco_sincronizado_em` = agora (mesma garantia do RN-08 sem duplicar coluna) | §7: "adapte se preservar as regras" |
| D-19 | **07/11:** `POST /api/admin/numeros/regenerar-faixas` reagrupa números `disponivel` em faixas contínuas por `ordem_exibicao`/`quantidade_desejada`; `reservado`/`confirmado`/`compra_externa` nunca são tocados e disponíveis fora das faixas ficam sem fralda | RN-01: "ajusta os números sem afetar reservas existentes" |
| D-20 | **07/11:** `PUT /admin/produtos/{id}` e `PUT /admin/mimos/{id}` passaram a persistir `tamanho`/`ordem_exibicao` (produtos) e todos os campos editáveis (mimos); antes só o preço era alterável no painel | §5: tudo se administra sem tocar no banco |

## Decisões de produto / dados

| # | Decisão | Justificativa |
|---|---------|---------------|
| P-00 | **v2:** o seed usa os dados REAIS das fraldas da tabela do briefing v2 (5 itens: RN `B07GQB93FT` 10un R$39,98 · RN+ `B0GY6GG8R7` 10un R$45,13 · P `B07GQ136TS` 30un R$54,99 · M `B07D3SVCTZ` 25un sem preço · G `B07X83MH7M` 25un R$93,90), gerando as faixas 01–10/11–20/21–50/51–75/76–100. **Os arquivos `fraldas.csv`/`mimos.csv` citados como anexos NÃO foram encontrados no ambiente** — as fraldas entraram pelo texto do prompt; os 58 mimos vieram do texto colado da lista (07/11). Mimos DEMO existem só em desenvolvimento e são desativados quando há dados reais | §3.7 v2 |
|---|---------|---------------|
| P-01 | **Sem senha padrão.** Admin criado só via `ADMIN_EMAIL`+`ADMIN_PASSWORD` no boot ou `python -m backend.app.create_admin` | §5: "sem senha padrão". A senha `admin123` de versões anteriores foi eliminada do código e da documentação |
| P-02 | Seed de produtos **DEMO** (ASINs/preços exemplificativos) existe apenas em desenvolvimento (`SEED_DEMO=true` e/ou `ENVIRONMENT != production`). Nunca são apresentados como reais; em produção não são criados | §3.7: "Dados de demonstração só existem num seed rotulado como DEMO, desligado em produção" |
| P-03 | Integração Amazon isolada atrás de `amazon_service` (ManualImport via CSV/JSON obrigatória; sincronização automática condicionada a acesso legítimo) | §3.3–3.5; ver `docs/AMAZON_INTEGRATION.md` |
| P-04 | Preço de referência congelado na reserva (`preco_*_reserva`) e exibido com `preco_sincronizado_em` | RN-08 |
| P-05 | Atualização da grade por **polling a cada 12s** (não SSE) | Requisito admite 10–15s ou SSE; polling é suficiente para dezenas–centenas de acessos e não exige conexões persistentes |
| P-06 | Comprovantes ficam no WhatsApp no MVP; campo `comprovante_url` já existe para upload futuro com serviço de armazenamento abstrato | §7 LGPD/segurança |
| P-07 | LGPD: consentimento registrado com versão do texto (`consentimento_versao`) e data; rotina `python -m backend.app.anonymize_data` anonimiza nome/WhatsApp após período configurável (`retencao_dias_preservacao`, padrão 180 dias) | §7 |
| P-08 | Nome público exibido como "PrimeiroNome ÚltimaInicial." e somente com autorização explícita | §7: público não vê dados de outros convidados |
| P-09 | **07/11:** mimos reais semeados de `mimos_reais.py` (58 itens/113 un/7 categorias, texto colado da lista). Casamento por NOME; campos vazios só são preenchidos, edição manual prevalece. Sufixo " \| variantes" do título Amazon removido; "Somente N em estoque" (estoque Amazon) ignorado; "Ver opções de compra" → preço nulo | §3: fonte de verdade são os dados copiados; não inventar campos ausentes |

## Premissas pendentes do usuário

- ~~Lista real de mimos~~ **RESOLVIDO (07/11):** lista colada pelo casal; 58 mimos reais em `backend/app/data/mimos_reais.py` (113 unidades, 7 categorias). ASIN/imagem/link pendentes de complemento manual no painel.
- **Chave Pix, WhatsApp do casal e mensagens:** valores de exemplo em `configuracoes`; o casal deve editar no painel (Configurações).
- **Domínio/HTTPS:** Caddy preparado; o domínio real deve ser definido em `infra/Caddyfile` (`SITE_DOMAIN`) na publicação.
