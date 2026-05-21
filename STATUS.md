# Status

## AI session note

For daily AI continuity, also check:

- `.ai_context/SESSION_STATE.md`
- `.ai_context/AI_SYNC.md`
- `docs/ai_context_progress.md`
- `docs/ai_session_workflow.md`

This file remains the development status and technical checkpoint log.
The `.ai_context/` files are the shared working context for OpenAI, Gemini, Codex and other agents.

---

## Resumo atual

- o fluxo manual foi levado até cerca da etapa 23
- já existem commands para `explain` / `review` / `summarize` / `map` / `list` / `pick` / `review-best` / `explain-best`
- o uso local do repo alvo `../IA-Trade` já foi validado
- o ranking já foi ajustado para preferir arquivos mais centrais
- `paper` tende a priorizar `paper_trade.py`
- `risk` tende a priorizar `risk/risk_manager.py`

## Direção do projeto

- o `agent-orchestrator` ainda não está finalizado
- a continuidade do desenvolvimento deve acontecer localmente neste repositório
- `IA-Trade` é apenas o primeiro profile em `projects/ia-trade`
- a camada global deve continuar genérica
- qualquer regra específica de projeto deve permanecer isolada em `projects/<project_id>/`
- o runtime agora pode trocar a raiz de profiles via `AI_PROJECTS_ROOT`
- a suíte já valida um segundo profile além de `ia-trade` usando raiz temporária
- `openai`, `gemini` e `claude` agora suportam execução live quando configurados (`model` + `api_key`)
- cada provider agora aceita override opcional de endpoint via `*_API_BASE`
- o runtime de providers agora isola exceções internas e respostas JSON inválidas para evitar quebra do pipeline

## Próximo foco

- reduzir seleção manual de contexto
- aumentar autonomia do fluxo local
- evoluir o core sem acoplar o orchestrator ao profile `ia-trade`
- consolidar aliases legados sobre `inspect-task` / `assemble-context`
- seleção dinâmica de provedor/modelo com consulta ao `BudgetManager` já está ativa no `TaskRunner`
- a troca agora é proativa, com threshold configurável por tarefa, por exemplo `gemini-3-flash-preview -> gemini-3.1-flash-lite-preview` quando o `Flash` estiver perto do limite
- manter a lista de fallbacks configurada por tarefa como fonte de ordem preferencial, sem mexer na estrutura do pipeline
- ampliar cobertura de testes para ranking e montagem de contexto no core
- ampliar cobertura de confiabilidade para `TaskRunner` e persistência operacional
- evitar consumo indevido de budget quando provider não executa de fato
- reduzir a excepcionalidade de `map-dependencies` no fluxo local
- ampliar parsing estrutural de `map-dependencies` para símbolos e chamadas
- incluir resolução cross-file básica de imports locais no `dependency_map`
- incluir `call_relations` no `dependency_map` para relacionar chamadas e imports locais resolvidos
- incluir `target_symbols` por import local resolvido para enriquecer contexto semântico
- priorizar `call_relations` com score/rank para leitura operacional
- adicionar `call_relation_summary` para leitura executiva de risco estrutural
- sinalizar `risk_flags` para relações não resolvidas de maior impacto
- incluir `dependency_highlights` para leitura rápida em entrypoints genéricos
- reduzir excepcionalidade de `map-dependencies` entre entrypoints genéricos e fluxo central

## Checkpoint de retomada

- paramos no fim da `Fase 4` e avanço inicial da `Fase 5`
- o pipeline central já faz:
  - carregamento de profile
  - montagem automática de contexto
  - seleção/ranking centralizado de arquivos
  - plano local com prompt real do profile
  - execução padronizada de providers
  - fallback real entre providers
  - retry curto configurável por tarefa
  - seleção proativa de provider/modelo por budget headroom, com threshold por tarefa
  - `inspect-task` agora também expõe `selection_preview` para mostrar quando a troca proativa vai acontecer
  - persistência operacional básica em `var/state` e `var/cache`
  - persistência diária de orçamento por provider em `var/state`
  - inspeção genérica de rota/plano/contexto para qualquer tarefa
  - suporte a `AI_PROJECTS_ROOT` para validar múltiplos profiles
  - testes cobrindo profile alternativo além de `ia-trade`
- o ponto em aberto para a próxima sessão é revisar se vale refinar o threshold por profile ou por task-type quando aparecerem métricas reais de uso
- o ponto em aberto para a próxima sessão também inclui considerar métricas explícitas de consumo por modelo/tarefa se quisermos aproximar melhor o caso `tokens` além de budget
- o próximo passo recomendado ao retomar é consolidar cenários restantes de confiabilidade no core (principalmente fluxos de comparação estrutural)
- o próximo passo recomendado ao retomar também é manter cobertura explícita para profile inválido, payload inválido e execução com target repo não configurado
- o próximo passo recomendado ao retomar também é revisar a política de invalidação de cache em casos de arquivos não selecionados, mas semanticamente relevantes

## Atualização de continuidade

- data da retomada: `2026-04-24`
- checkpoint desta sessão: fallback proativo por budget headroom implementado no `TaskRunner`, com threshold configurável por tarefa e preservando retry/fallback atuais
- bloco concluído nesta sessão:
  - runtime de providers generalizado para múltiplas contas por adapter (`type` em `config/providers.yaml` + fallback por prefixo `<provider>_...`)
  - suporte explícito a `gemini_v2` no config/env/budget com reaproveitamento do adapter `gemini`
  - providers endurecidos para resposta parcial (JSON válido com campos ausentes/shape inválido) com erro estruturado:
    - `openai`: `missing_output_text` e `output_text_not_string`
    - `gemini`: `missing_candidates` e `candidates_not_list`
    - `claude`: `missing_content` e `content_not_list`
  - `TaskRunner.inspect` e `TaskRunner.run` agora incluem `dependency_map` + `dependency_highlights` para `map-dependencies` no fluxo genérico
  - `inspect-task` deixou de ter lógica dedicada para `map-dependencies`, consumindo o caminho genérico do runner
  - `routing.yaml` passou a declarar `review-file` explicitamente e ampliou fallback de `map-dependencies` para `claude` + `openai`
  - `TaskRunner` agora seleciona provider/modelo de forma proativa por headroom de budget, com `budget_switch_threshold_ratio` por tarefa
  - `inspect-task` agora mostra um `selection_preview` direto, com a decisão de manter o primário ou trocar para fallback antes da execução
  - `diagnose-orchestrator` agora expõe `proactive_switch_telemetry` com contagem diária de trocas antecipadas
  - `OperationalStore` agora persiste snapshot do resultado e permite lookup por fingerprint (`load_cached_task_result`)
  - `TaskRunner` ganhou reutilização opcional de cache (`allow_cache_reuse`) e `task_cli` ativa por padrão com `AI_CACHE_REUSE_ENABLED` (desligável)
  - o cache agora invalida por assinatura de conteúdo dos arquivos selecionados (hash + metadados), além do payload
  - `inspect-task` agora suporta cache com TTL (`AI_INSPECT_CACHE_REUSE_ENABLED` / `AI_INSPECT_CACHE_TTL_SEC`) e bypass por `"force_refresh": true`
  - o cache do `inspect-task` agora também valida assinatura de conteúdo dos arquivos selecionados para evitar hit stale
  - `StateStore` e `CacheStore` agora usam gravação atômica (`temp file` + `replace`) para reduzir risco de corrupção em concorrência leve
  - cobertura de testes ampliada para leitura/escrita concorrente leve em storage local
  - cobertura E2E ampliada para cache do `task_cli`:
    - hit quando os arquivos selecionados não mudam
    - miss automático quando o conteúdo do arquivo selecionado muda
  - bloco principal da `Fase 5` (confiabilidade) considerado fechado no estado atual do projeto local
  - `context_rules` por profile agora estão ativos no `ContextBuilder` para customização por projeto sem acoplamento global
    - limites por tarefa (`task_file_limits`)
    - queries por tarefa (`task_queries`)
    - arquivos priorizados por tarefa (`pinned_files_by_task`)
  - `task_prompt_overrides` por profile agora permite escolher prompt/agente por tipo de tarefa sem alterar a camada global
  - agentes locais agora retornam saída estruturada (`local_agent_output`) além de prompt, e isso já entra no `local_plan` e no metadata do provider
- `diagnose-orchestrator` agora expõe métricas de índice de cache (`cache_indexed_entry_count`, `cache_inspect_entry_count`) e chaves recentes de cache de inspeção
- `diagnose-orchestrator` agora também inclui `recent_task_status_summary` e `storage_health` para sinalizar inconsistências entre arquivos de cache e índice local
- `diagnose-orchestrator` agora também inclui alertas de orçamento (`budget.alerts`) com limiar configurável por `AI_BUDGET_ALERT_THRESHOLD_RATIO`
- `inspect-project` agora inclui `storage_quicklook` com `recent_task_status_summary` e `storage_health` para inspeção rápida de retomada
- `diagnose-orchestrator` e `inspect-project` agora expõem `health_summary` agregado (`ok`/`degraded`) com sinais operacionais para automação
- `diagnose-orchestrator` e `inspect-project` agora suportam `--health-only` para saída compacta de automação (checks essenciais + `health_summary`)
- `diagnose-orchestrator` e `inspect-project` agora suportam `--fail-on-degraded` para retornar `exit code 2` quando o estado agregado estiver degradado
- `scripts/healthcheck.sh` agora encapsula o healthcheck compacto para CI/cron com retorno `0/2` e modo opcional `--inspect-project`
- `diagnose-orchestrator`, `inspect-project` e `scripts/healthcheck.sh` agora suportam `--compact` para JSON em linha única
- `scripts/healthcheck.sh` agora suporta `--all` para rodar `diagnose-orchestrator` + `inspect-project` e agregar resultado com status único (`ok`/`degraded`/`error`)
- `scripts/healthcheck.sh` agora suporta `--strict` (com `--all`) para suprimir `results` detalhados e manter payload mínimo de CI
- `scripts/healthcheck.sh` agora suporta `--quiet` para não emitir output quando o status final estiver `ok`
- `scripts/healthcheck.sh` agora suporta `--output <arquivo>` para persistir o payload JSON gerado em disco
- `scripts/healthcheck.sh` agora também suporta `--output-dir <diretório>` para gravar arquivo timestampado por execução
- `scripts/healthcheck.sh` agora suporta `--latest-link` (com `--output-dir`) para atualizar `latest.json` automaticamente
- `scripts/healthcheck.sh` agora suporta `--latest-link-name <nome>` para personalizar o symlink de último resultado
- `scripts/healthcheck.sh` agora suporta `--meta` para incluir metadados operacionais (`generated_at`, `host`, `project_id`, `argv`) no JSON
- `scripts/healthcheck.sh` agora suporta `--meta-fields <csv>` para filtrar quais campos de `meta` serão emitidos
- `scripts/healthcheck.sh` agora aceita `--meta-fields all` (ou `*`) como atalho para todos os campos suportados
- `scripts/healthcheck.sh` agora suporta `--meta-drop-nulls` para suprimir valores nulos no bloco/flatten de metadados
- `scripts/healthcheck.sh` agora suporta `--meta-flatten` para promover `meta` ao nível raiz com prefixo `meta_`
- `scripts/healthcheck.sh` agora suporta `--meta-prefix <texto>` para customizar o prefixo usado no flatten
- `scripts/healthcheck.sh` agora inclui `artifact.path` (e `artifact.latest_link` quando disponível) no payload ao gravar saída em arquivo
- `TaskRunner` agora expõe pipeline multiestágio explícito em `run`/`inspect` (`pipeline.stage_metrics` + `pipeline.stages`)
- `TaskRunner` agora expõe `context_sufficiency` estruturado (`context_sufficient`, `selected_files`, `missing_context_risks`, `reason`)
- `local_agent_output` agora também aparece no estágio explícito `local_analysis` (mantendo compatibilidade com `local_plan`)
- `TaskRunner` agora expõe `synthesis` em `run`/`inspect` para formalizar a etapa de síntese/arbitragem final sem remover campos antigos
  - `TaskRunner` agora publica `execution_metrics` por execução (planejamento, tentativas de provider e tempo total), com persistência no `OperationalStore`
  - `map-dependencies` legado agora usa `TaskRunner.inspect` internamente para consumir `dependency_map` do fluxo genérico
  - timeout de provider por tarefa (`provider_timeout_sec`) agora é lido de `routing.<task>.execution` e aplicado no runtime HTTP dos providers
  - cobertura E2E ampliada para sequência `inspect-task -> task_cli` com degradação + fallback + persistência
- suíte atual: `python3 -m unittest -q` com `120` testes (`OK`)

## Checkpoint final desta sessão

- estado do worktree: limpo
- branch atual: `main`
- remoto: `origin/main` estava atrás e foi sincronizado depois dos últimos commits locais
- ponto exato para retomar:
  - avançar Fase 3 com execução multiestágio mais rica antes do provider
  - definir se vale transformar a saída estruturada local em um estágio explícito do pipeline
  - manter o padrão atual de confiabilidade, cache e diagnóstico como base estável

## Encerramento do dia

- data do checkpoint: `2026-04-22`
- último bloco concluído:
  - fechamento do bloco de `dependency_map` com `call_relations`, `target_symbols`, `call_relation_summary`, `risk_flags` e `dependency_highlights`
  - parser de payload JSON centralizado nos entrypoints
  - execução live também para `claude` e `gemini` (além de `openai`), com fallback para `stub` quando não configurado
  - suporte opcional a override de endpoint por provider via `*_API_BASE`
  - robustez adicional de providers para exceções internas e resposta JSON inválida/shape inesperado
  - cobertura de testes ampliada para providers e para payload inválido/não-objeto nos entrypoints
  - commits publicados em `main`: `1bd020d`, `bd718a0`, `9ea1a51`, `4a4d75b`
  - suíte passando: `python3 -m unittest -q` com `81` testes (`OK`)
- ponto exato para retomar amanhã:
  - consolidar cenários restantes de confiabilidade no core (`TaskRunner` + `OperationalStore`) com foco em fluxos degradados/fallback
  - endurecer providers para respostas parciais (JSON válido, mas sem campos esperados) com erro estruturado consistente
  - revisar se vale criar task-type genérico de análise estrutural para reduzir a excepcionalidade de `map-dependencies`

## Arquivos-chave para retomar rápido

- `docs/roadmap.md`
- `STATUS.md`
- `app/core/project_loader.py`
- `config/routing.yaml`
- `app/core/task_runner.py`
- `app/core/provider_failure_policy.py`
- `app/core/operational_store.py`
- `app/core/context_builder.py`
- `app/core/file_selector.py`

## Checkpoint final desta sessão

- data do checkpoint: `2026-04-24`
- branch: `main`
- remoto: `origin/main` atualizado com o commit `38ea6e4` (`Add proactive budget-based provider switching`)
- suíte validada antes do push: `python3 -m unittest -q` com `126` testes (`OK`)
- o que foi entregue nesta sessão:
  - seleção proativa de provider/modelo por budget headroom no `TaskRunner`
  - threshold configurável por tarefa em `routing.<task>.execution.budget_switch_threshold_ratio`
  - preview operacional da decisão em `inspect-task` e `task_cli` via `selection_preview`
  - telemetria diária de trocas proativas em `diagnose-orchestrator`
  - persistência da telemetria no `OperationalStore`
  - documentação atualizada em `README.md`, `STATUS.md` e `docs/roadmap.md`
- onde paramos:
  - o fluxo funcional já está pronto e publicado no remoto
  - o próximo trabalho, se retomarmos, é refinar a política de troca por modelo/tarefa e evoluir o alerta/telemetria de uso
- ponto exato para retomada:
  - revisar se vale diferenciar threshold por profile ou task-type com base em uso real
  - considerar telemetria/alerta adicional quando a troca proativa ficar acima do esperado
  - manter o padrão atual de confiabilidade, cache e diagnóstico como base estável

## Checkpoint final desta sessão

- data do checkpoint: `2026-04-25`
- branch: `main`
- estado do worktree: com alterações locais (ainda não commitadas)
- o que foi entregue nesta sessão:
  - integração nativa de `openrouter` como provider de primeira classe no runtime
  - novo adapter em `app/providers/openrouter_provider.py` com:
    - endpoint default `https://openrouter.ai/api/v1/chat/completions`
    - parsing robusto para múltiplos formatos de resposta (`message.content` string/lista e fallback `choices[].text`)
    - `max_tokens` padrão reduzido para `2048` (evitando erro de crédito por limite excessivo)
  - registro/configuração completa do provider:
    - `config/providers.yaml` com `OPENROUTER_*`
    - `config/budgets.yaml` com `BUDGET_OPENROUTER_DAILY_USD` e `MAX_CONTEXT_FILES_OPENROUTER`
    - `.env.example` atualizado com variáveis de OpenRouter
  - roteamento atualizado para incluir `openrouter` em fallbacks por tarefa (`config/routing.yaml`)
  - documentação atualizada no `README.md` para refletir o novo provider
  - cobertura de testes ampliada para OpenRouter (`tests/test_providers.py`, `tests/test_provider_config.py`)
- validação executada nesta sessão:
  - testes unitários de providers/config passando localmente
  - smoke test live do `task_cli` forçando rota para `openrouter` concluído com `status=completed`
- observações operacionais para continuidade:
  - desabilitações de `OPENAI_ENABLED`/`GEMINI_ENABLED` usadas durante smoke tests foram temporárias por comando; `.env` permanece com os providers habilitados
  - `OPENROUTER_MODEL` foi ajustado para um model id válido (`openrouter/pareto-code`) para validação live
- ponto exato para retomada:
  - opcional: mover `provider_max_tokens` para política por tarefa em `routing.<task>.execution`
  - opcional: adicionar classificação específica de erro para `HTTP 402` (insufficient credits) em providers
  - opcional: incluir telemetry de custo/tokens retornados pelo OpenRouter no `OperationalStore`

## Checkpoint final desta sessão

- data do checkpoint: `2026-05-20`
- branch: `main`
- remoto: `origin/main` sincronizado com o commit `8381685` (`feat(security): sanitize target-file content against secrets and prompt injection`)
- suíte validada antes do push: `python3 -m unittest discover -s tests` com `189` testes totais — `179` passando e `10` erros pré-existentes em `tests/test_task_script.py` (caminho hard-coded `SD200` vs `SD2001`, não relacionado ao runtime)
- o que foi entregue nesta sessão (4 de 8 tarefas do `ROADMAP.md`):
  - `#1` Telemetria de uso normalizada para Claude, OpenAI e Gemini no
    mesmo schema unificado já produzido pelo OpenRouter
    (`{prompt_tokens, completion_tokens, total_tokens}`)
  - `#2` Sinal `daily_tokens_high` no `health_summary`, configurável
    via `AI_DAILY_TOKEN_ALERT_THRESHOLD` (default `0` = desabilitado);
    `--health-only` agora expõe `daily_token_total` /
    `daily_token_threshold` no bloco `checks`
  - `#3` Resolução hierárquica de `provider_max_tokens` em 7 níveis
    (`projeto.tarefa.modelo` → `projeto.tarefa` → `projeto.default` →
    `routing.<task>.execution.provider_max_tokens_by_provider.<provider>`
    → `routing.<task>.execution.provider_max_tokens` →
    `routing._defaults.provider_max_tokens` → fallback `2048`); o
    `TaskRunner` agora resolve por provider candidato no loop
  - `#4` `ContextSanitizer` em `app/core/security.py`, integrado ao
    `ContextBuilder` para sanitizar **apenas** TARGET_FILES; cobre
    secrets (Anthropic, OpenAI, AWS, GitHub, Slack, Google, JWT,
    Bearer, DB URLs, blocos PEM) e prompt-injection (override de
    instruções, role override, `<|system|>`); modos `redact` (default)
    / `block` / `audit` via `AI_CONTEXT_SECURITY_MODE`; documentos
    operadores (`docs/`, project memory, prompts) ficam intactos por
    design
- documentação consolidada:
  - `ROADMAP.md` no topo com 8 tarefas estruturadas (`e6cce98`)
  - `docs/security.md` (novo) com contrato completo do sanitizer
  - `docs/references.md` atualizado com `AI_DAILY_TOKEN_ALERT_THRESHOLD`,
    `AI_CONTEXT_SECURITY_MODE` e tabela de hierarquia de
    `provider_max_tokens`
- commits publicados nesta sessão em `main`:
  - `fb6c88a feat(providers): normalize usage telemetry for Claude, OpenAI and Gemini`
  - `e6cce98 docs: add structured ROADMAP with 8 phased development tasks`
  - `57fa941 feat(observability): daily token alert signal in health_summary`
  - `48fc194 docs: clarify alert scope as daily token limit (not USD cost)`
  - `41b6363 feat(routing): resolve provider_max_tokens through a 7-level hierarchy`
  - `8381685 feat(security): sanitize target-file content against secrets and prompt injection`
- progresso global do roadmap: `4/8` tarefas concluídas (50%)
- ponto exato para retomar amanhã:
  - `#5` Expandir seleção de arquivos para além de Python (TypeScript,
    Go, Java, C++) — começa pelo `file_selector` e pelas heuristics
    de ranking
  - `#6` Streaming de execução para tarefas longas (Claude/OpenAI
    primeiro), com pipeline que suporte interrupção graceful
  - `#7` Formato de output produtizado para auditorias/revisões
    (schema JSON estável + template de relatório)
  - `#8` Avaliação da integração com GitHub PR (depende de `#7`)
- backlog técnico identificado:
  - corrigir `tests/test_task_script.py:238` (caminho hard-coded
    `SD200`) que está bloqueando os 10 testes E2E de subprocess
  - quando houver demanda real, expandir `ContextSanitizer` com
    regras opt-in via `project.yaml` (gancho já existe no construtor)
  - quando houver catálogo de preços por modelo, dá pra reativar a
    discussão de custo USD em cima de `daily_token_total`
