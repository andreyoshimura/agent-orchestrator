# agent-orchestrator - AI Bundle (Generated)

## CONTEXT_MINIMAL
# agent-orchestrator - Contexto minimo

Use este arquivo como primeiro contexto para OpenAI, Gemini, Codex ou outro agente.

## Projeto

`agent-orchestrator` e um orquestrador generico de agentes de IA com multiplos providers para repositorios locais.

## Objetivos

- Rotear tarefas entre providers.
- Controlar orcamento e uso de tokens.
- Manter memoria especifica por projeto fora do runtime central.
- Permanecer plug-and-play e reversivel.
- Operar com leitura por padrao nos repositorios-alvo.

## Estado atual

- Repo: `andreyoshimura/agent-orchestrator`
- Branch padrao: `main`
- Profiles por projeto: `projects/<project_id>/`
- Estado local: `var/state`
- Cache local: `var/cache`

## Comandos seguros principais

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Estrutura principal

- `app/core/`: runtime central e roteamento.
- `app/providers/`: adapters de providers.
- `app/agents/`: agentes locais.
- `app/storage/`: estado, cache e persistencia.
- `config/`: configuracoes de providers, rotas e limites.
- `projects/`: profiles e memoria por projeto.
- `scripts/`: entrypoints operacionais.
- `var/`: dados locais de execucao.

## Regras criticas

- Nao alterar runtime central sem escopo claro.
- Nao alterar roteamento ou limites sem decisao explicita.
- Nao ativar escrita em repositorios-alvo sem autorizacao explicita.
- Nao executar chamadas externas se a tarefa for apenas documental.
- Nao misturar memoria de projetos diferentes.

## Politica de contexto

Use o menor contexto suficiente para a tarefa.

Nao carregar por padrao:

- README completo
- `var/cache`
- `var/state` completo
- logs brutos
- arquivos locais sensiveis

## GUARDRAILS
# agent-orchestrator - Guardrails

Use este arquivo como fonte central das regras de seguranca para agentes IA neste repositorio.

## Escopo obrigatorio

Antes de analisar ou alterar algo, declarar escopo:

- DOCS
- RUNTIME
- PROVIDERS
- ROUTING
- BUDGET
- PROJECT_PROFILE
- STORAGE
- SCRIPTS

Se o escopo nao estiver claro, parar e pedir delimitacao.

## Regras gerais

- Nao alterar runtime central sem objetivo e rollback claros.
- Nao alterar roteamento sem explicar impacto em fallback, custo e comportamento.
- Nao alterar limites de orcamento sem decisao explicita.
- Nao misturar memoria de projetos diferentes.
- Nao tratar cache ou state local como fonte absoluta da verdade.
- Nao ampliar acesso de escrita em repositorios-alvo sem autorizacao explicita.

## Providers

- Nao adicionar, remover ou priorizar provider sem registrar motivo.
- Nao assumir que todo provider esta disponivel.
- Sempre considerar fallback, timeout e budget headroom.
- Nao fazer chamada externa quando a tarefa for apenas documental ou estrutural.

## Configuracao

- Alteracoes em `config/` exigem justificativa curta.
- Separar mudanca de politica de roteamento de mudanca de runtime.
- Preferir configuracao a codigo quando a regra for operacional.

## Projetos alvo

- Profiles ficam em `projects/<project_id>/`.
- Memoria especifica de um projeto nao deve contaminar outro projeto.
- O caminho do repo alvo deve ser tratado como configuracao externa.

## Storage local

- `var/cache` pode ser descartavel.
- `var/state` e persistencia operacional local, mas pode estar desatualizado.
- Antes de concluir problema operacional, rodar healthcheck/diagnostico.

## Comandos seguros

Preferir:

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Nao fazer por padrao

- Nao fazer deploy.
- Nao executar automacao destrutiva.
- Nao apagar cache/state sem pedido explicito.
- Nao editar configuracao sensivel.
- Nao ativar escrita em repositorios-alvo sem pedido explicito.
- Nao rodar tarefas que chamem providers externos sem necessidade clara.

## TASK_FORMATS
# agent-orchestrator - Task Formats

Define formatos padrao para respostas de IA neste repositorio, com foco em clareza, baixo consumo de tokens e seguranca operacional.

## Formato padrao

### Diagnostico

- Maximo 5 linhas.
- Explicar o ponto central sem recontar o projeto inteiro.

### Evidencia

- Maximo 5 bullets.
- Citar arquivos, comandos ou outputs relevantes.

### Acao recomendada

- Maximo 5 bullets.
- Deve ser executavel e segura.

### Risco

- Maximo 3 bullets.
- Explicar impacto em runtime, providers, routing, budget ou storage quando aplicavel.

### Proximo passo

- Uma unica acao concreta.

## Formato para alteracao de codigo

Responder com:

1. Escopo declarado.
2. Arquivos afetados.
3. Motivo da alteracao.
4. Risco operacional.
5. Como validar.

## Formato para diagnostico operacional

Responder com:

1. Comando executado.
2. Status observado.
3. Evidencia.
4. Hipotese.
5. Proximo passo seguro.

## Regras de economia de contexto

- Nao repetir README inteiro.
- Nao listar estrutura completa sem necessidade.
- Nao colar logs longos.
- Nao abrir `var/cache` ou `var/state` por padrao.
- Nao explicar conceitos ja documentados, apenas apontar para o arquivo relevante.

## Quando pedir mais contexto

Pedir somente o arquivo ou comando minimo necessario.

Evitar pedidos amplos como:

- "mande o repo todo"
- "liste todos os arquivos"
- "cole todos os logs"

## Respostas longas

Somente responder longo se o usuario pedir explicitamente:

- detalhado
- completo
- profundo
- auditoria completa

Caso contrario, manter resposta compacta.

## AI_SYNC
# agent-orchestrator - AI Sync

Fonte comum de alinhamento para OpenAI, Gemini, Codex e outros agentes trabalhando neste repositorio.

## Regra principal

Todas as IAs devem usar a mesma ordem de contexto:

1. `.ai_context/CONTEXT_MINIMAL.md`
2. `.ai_context/GUARDRAILS.md`
3. `.ai_context/TASK_FORMATS.md`
4. `.ai_context/AI_SYNC.md`
5. `.ai_context/SESSION_STATE.md`, se existir
6. `docs/ai_context_progress.md`, se existir

## Estado oficial

- Projeto: agent-orchestrator
- Repo: `andreyoshimura/agent-orchestrator`
- Funcao: orquestrador generico de agentes IA e providers
- Acesso a repositorios-alvo: leitura por padrao
- Memoria especifica por projeto: `projects/<project_id>/`
- Estado/cache local: `var/state` e `var/cache`

## Fonte de verdade por assunto

- Contexto minimo: `.ai_context/CONTEXT_MINIMAL.md`
- Guardrails: `.ai_context/GUARDRAILS.md`
- Formato de resposta: `.ai_context/TASK_FORMATS.md`
- Estado da sessao: `.ai_context/SESSION_STATE.md`
- Progresso da infraestrutura IA: `docs/ai_context_progress.md`
- Workflow humano: `docs/ai_session_workflow.md`
- Documentacao ampla do projeto: `README.md`

## Politica para agentes

- Nao manter memorias divergentes entre OpenAI, Gemini e Codex.
- Nao duplicar roadmap ou README em arquivos de memoria.
- Atualizar `SESSION_STATE.md` ao encerrar sessoes relevantes.
- Atualizar este arquivo se mudar o fluxo oficial de contexto.

## Fluxo operacional seguro

Antes de diagnostico operacional, preferir comandos seguros:

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Politica de economia

- Nao carregar README completo por padrao.
- Nao carregar logs brutos por padrao.
- Nao carregar `var/cache` ou `var/state` completo por padrao.
- Nao acionar providers externos sem necessidade clara.
- Usar o menor contexto suficiente para a tarefa.

## Proxima acao padrao

Ao iniciar nova sessao:

1. Rodar `bash scripts/start_ai_session.sh`, quando existir.
2. Ler `.ai_context/SESSION_STATE.md`.
3. Confirmar estado, pendencias e proximo passo antes de alterar arquivos.

## SESSION_STATE
# agent-orchestrator - Session State

## Ultima atualizacao

- timestamp_local: 2026-04-27 16:58:02
- timestamp_utc: 2026-04-27T19:58:02Z

## Resumo da ultima sessao

- Infraestrutura IA completa ate Fase 4; entrypoints antigos integrados: CODEX_BOOTSTRAP, STATUS, ROADMAP, README e scripts/status; pendencias operacionais: target_repo_not_configured e cache_index_inconsistent no healthcheck.

## Observacao

Arquivo atualizado automaticamente via script de encerramento.


## DOCS INDEX

### docs/architecture.md
# Architecture

## Overview

`agent-orchestrator` is a generic multi-provider AI routing layer for local repositories. It loads project-specific context, selects relevant files, routes tasks to the best available provider, and persists results locally.

## Layer separation

### Global layer (`app/`)
Belongs to the orchestrator — reusable across all projects:
- Provider integration and fallback
- Routing and budget logic
- Context loading and file selection
- Task pipeline and persistence

### Project layer (`projects/<project_id>/`)
Belongs to a specific project — never bleeds into the global layer:
- Project context and memory
- Prompt templates per agent role
- File selection rules (`context_rules` in `project.yaml`)
- Playbooks

## Component map

```
app/
  cli/          task_cli.py — CLI entrypoint for all tasks
  commands/     one module per task type (inspect, diagnose, review, explain, purge...)
  core/         runtime: task_runner, context_builder, file_selector, project_loader
  providers/    HTTP adapters: openai, gemini, claude, openrouter
  agents/       local agents: repo_worker, micro_reviewer, arbiter
  storage/      StateStore, CacheStore (atomic writes, fingerprint-based cache)

config/
  providers.yaml    provider registry (type, env var names)
  routing.yaml      task → preferred+fallback providers, retry/timeout/budget policy
  budgets.yaml      daily budget limits per provider

projects/
  <project_id>/
    project.yaml          profile metadata, env var names, memory/prompt file lists
    AGENT_CONTEXT.md      project context loaded into every agent
    CODEX_BOOTSTRAP.md    project-specific Codex bootstrap
    memory/               facts, guardrails, architecture notes
    prompts/              repo_worker, micro_reviewer, arbiter
    playbooks/            optional task playbooks

var/
  state/    daily budget usage, recent task results
  cache/    task result cache (_index.json + fingerprint-keyed .txt files)
  logs/     audit log (jsonl)
```

## Task execution pipeline

```
task_cli → TaskRunner.run()
  1. validate_payload
  2. load_runtime_profile
  3. build_context         (ContextBuilder: bootstrap + memory + selected files)
  4. evaluate_context_sufficiency
  5. local_analysis        (local agents: repo_worker → micro_reviewer → arbiter)
  6. provider_execution    (with retry + budget-aware fallback)
  7. synthesize_result
  8. persistence           (StateStore + CacheStore)
  9. return_diagnostics
```

## Provider selection

Each task has a `preferred` provider and `fallback` list in `config/routing.yaml`.

Before executing, `TaskRunner` checks `BudgetManager`:
- If the preferred provider is above `budget_switch_threshold_ratio`, switches proactively to the first viable fallback.
- On provider failure, retries up to `max_provider_retries` before falling through to the next fallback.
- Fallback types: `temporary`, `rate_limit`, `network`, `configuration`, `provider_unavailable`.

## Cache invalidation

Cache keys are fingerprints of:
- task type + payload fields
- content hash + metadata of selected files

A cache hit is only valid when file content has not changed since the last run.
Orphaned cache files (not in `_index.json`) can be removed with `bash scripts/task.sh purge-cache`.

## Context assembly

`ContextBuilder.build()` assembles context in this order:
1. Global bootstrap (`docs/bootstrap.md`)
2. Project bootstrap (`projects/<id>/CODEX_BOOTSTRAP.md`)
3. Project agent context (`projects/<id>/AGENT_CONTEXT.md`)
4. Project memory files
5. Project prompt for the task's agent role
6. Selected target repo files (ranked by `FileSelector`)

File selection is governed by `context_rules` in `project.yaml`:
- `max_target_files`
- `task_file_limits`
- `task_queries`
- `pinned_files_by_task`

### docs/operations.md
# Operations

## Session start

```bash
bash scripts/start_ai_session.sh
```

Runs healthcheck, diagnostics, budget inspection, regenerates AI bundles, and prints the resume prompt for the AI tool.

## Healthcheck

```bash
bash scripts/healthcheck.sh --all --strict   # CI-friendly summary only
bash scripts/healthcheck.sh --all            # full payload
bash scripts/healthcheck.sh --quiet          # silent when ok
```

Returns exit code `0` (ok) or `2` (degraded).

## Task commands

```bash
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
bash scripts/task.sh inspect-task <task-type> '<json>'
bash scripts/task.sh purge-cache
```

## Available task types

| Command | Description |
|---|---|
| `explain-file` | Explain a specific file |
| `review-file` | Review a specific file |
| `summarize-repo-area` | Summarize multiple files |
| `map-dependencies` | Extract imports, symbols, call graph |
| `list-python-files` | List Python files in target repo |
| `pick-python-file` | Find best Python file for a query |
| `review-best-python-match` | Review best Python match for a query |
| `explain-best-python-match` | Explain best Python match for a query |
| `inspect-project` | Inspect active profile and target repo state |
| `inspect-task` | Preview routing + context for any task |
| `inspect-budget` | Show daily budget usage per provider |
| `diagnose-orchestrator` | Full orchestrator diagnostics |
| `assemble-context` | Build context bundle for a task |
| `purge-cache` | Remove orphaned cache files |

## AI bundle generation

```bash
bash scripts/generate_ai_bundle.sh
```

Regenerates `.ai_context/AI_BUNDLE_SHORT.md` and `.ai_context/AI_BUNDLE.md`.

## Session end

```bash
bash scripts/end_ai_session.sh "summary of what was done"
```

Updates `.ai_context/SESSION_STATE.md`.

## Key paths

| Path | Purpose |
|---|---|
| `.env` | Local environment variables (gitignored) |
| `.env.example` | Template for env vars |
| `config/routing.yaml` | Task routing policy |
| `config/providers.yaml` | Provider registry |
| `config/budgets.yaml` | Daily budget limits |
| `var/state/` | Persistent operational state |
| `var/cache/` | Task result cache |
| `var/logs/` | Audit log |
| `projects/ia-trade/` | IA-Trade project profile |

## Routing policy (per task)

Fields in `config/routing.yaml` under `routing.<task>.execution`:

| Field | Purpose |
|---|---|
| `preferred` | Primary provider |
| `fallback` | Ordered fallback list |
| `max_provider_retries` | Retries before falling to next provider |
| `provider_timeout_sec` | HTTP timeout per provider call |
| `budget_switch_threshold_ratio` | Switch proactively when budget headroom is below this ratio |
| `fallback_on` | Error types that trigger fallback |

## Cache control env vars

| Variable | Purpose |
|---|---|
| `AI_CACHE_REUSE_ENABLED` | Enable task result caching (default: true) |
| `AI_INSPECT_CACHE_REUSE_ENABLED` | Enable inspect-task caching |
| `AI_INSPECT_CACHE_TTL_SEC` | TTL for inspect-task cache |

### docs/roadmap.md
# Roadmap

## AI context note

This roadmap tracks product/runtime evolution of the orchestrator.
AI workflow infrastructure is tracked separately in:

- `docs/ai_context_progress.md`
- `.ai_context/AI_SYNC.md`
- `docs/ai_session_workflow.md`

Do not confuse roadmap phases below with AI-context infrastructure phases.

---

## Status

- `[x]` concluído
- `[~]` parcial / existente, mas ainda incompleto no fluxo global
- `[ ]` pendente

## Fase 0 - Base local e comandos iniciais

- `[x]` preparar ambiente local
- `[x]` validar acesso ao repo alvo `../IA-Trade`
- `[x]` ligar leitura real via `ContextManager`
- `[x]` criar `explain_file.py`
- `[x]` ligar `explain-file` no `task.sh`
- `[x]` criar `review_file.py`
- `[x]` ligar `review-file` no `task.sh`
- `[x]` criar `summarize_repo_area.py`
- `[x]` ligar `summarize-repo-area` no `task.sh`
- `[x]` criar `map_dependencies.py`
- `[x]` ligar `map-dependencies` no `task.sh`
- `[x]` criar `list_python_files.py`
- `[x]` filtrar `venv/`, `site-packages/` etc em `list_python_files.py`
- `[x]` ligar `list-python-files` no `task.sh`
- `[x]` criar `pick_python_file.py`
- `[x]` ligar `pick-python-file` no `task.sh`
- `[x]` criar `review_best_python_match.py`
- `[x]` ligar `review-best-python-match` no `task.sh`
- `[x]` melhorar o ranking/desempate
- `[x]` fazer `review_best_python_match.py` usar o ranking novo
- `[x]` validar o fluxo central com o ranking novo
- `[x]` criar `explain_best_python_match.py`
- `[x]` ligar `explain-best-python-match` no `task.sh`

## Fase 1 - Estrutura global do orchestrator

- `[x]` centralizar carregamento de profile/projeto no core
- `[x]` criar inspeção reutilizável do projeto ativo (`inspect-project`)
- `[x]` ligar o CLI genérico ao loader central de projeto
- `[x]` adicionar testes mínimos para o carregamento de profiles
- `[~]` manter a camada global genérica e `ia-trade` apenas como primeiro profile

## Estado atual

### O que já existe

- comandos locais úteis para inspeção e revisão de arquivos Python e textos do repo alvo
- leitura real de arquivos via `ContextManager`
- ranking básico de arquivos Python por nome e heurísticas simples
- roteamento por tipo de tarefa
- budget manager básico em memória
- budget diário persistido em `var/state`
- auditoria simples em `var/logs/audit.jsonl`
- profiles por projeto em `projects/<project_id>/`
- primeiro profile funcional em `projects/ia-trade/`

### O que ainda está incompleto

- agentes ainda são stubs
- integração de providers ainda é síncrona e sem streaming
- `TaskRunner` ainda planeja, mas não executa um workflow completo
- seleção de contexto ainda é básica e pouco orientada por tarefa
- budget/estado não persistem por dia entre execuções
- cobertura de testes ainda é muito pequena

## Próximas prioridades

## Onde Paramos

- checkpoint atual: fim da `Fase 4` e avanço inicial da `Fase 5`
- próximo bloco a implementar:
  - redução adicional de wrappers manuais ainda restantes
  - ampliar confiabilidade operacional do fluxo completo
  - plugar seleção dinâmica de provedor/modelo no `TaskRunner`, consultando `BudgetManager` antes de cada tentativa para trocar automaticamente quando o primário estourar orçamento ou limite de tokens
  - deixar essa troca proativa, no estilo `Flash -> Flash Lite`, antes do erro de quota/budget
  - preservar a ordem configurada de fallbacks por tarefa como base da decisão
  - payload JSON inválido agora retorna erro estruturado nos entrypoints genéricos
  - profile inválido agora retorna erro estruturado nos entrypoints genéricos
  - execução com target repo não configurado agora está coberta nos testes de entrypoint

## Fase 2 - Montagem automática de contexto

- `[x]` criar um montador global de contexto por tarefa
- `[x]` combinar bootstrap global + profile do projeto + memória + arquivos selecionados
- `[x]` mover heurísticas de seleção/ranking para `app/core/`
- `[x]` permitir regras específicas por profile sem contaminar a camada global
  - `context_rules` em `project.yaml` agora suporta:
    - `max_target_files`
    - `task_file_limits`
    - `task_queries`
    - `pinned_files_by_task`
  - `task_prompt_overrides` em `project.yaml` agora permite selecionar prompt/agente por `task_type` no profile

## Fase 3 - Execução real do fluxo

- `[~]` transformar `TaskRunner` em executor real de pipeline
  - `TaskRunner.run` agora publica `execution_metrics` (`planning_ms`, `provider_execution_ms`, `total_ms`, `attempt_metrics`, `cache_hit`)
  - `OperationalStore` persiste `execution_metrics` no estado e no resumo de cache
  - pipeline explícito agora já cobre estágios:
    - `validate_payload`
    - `load_runtime_profile`
    - `build_context`
    - `evaluate_context_sufficiency`
    - `local_analysis`
    - `provider_execution`
    - `synthesize_result`
    - `persistence`
    - `return_diagnostics`
  - `run`/`inspect` agora incluem `pipeline` + `stage_metrics` e objeto `context_sufficiency`
  - `run`/`inspect` agora também incluem `synthesis` para formalizar a etapa de síntese/arbitragem final
- `[~]` conectar agentes ao carregamento de prompts e memória do projeto
  - `build_local_task_plan` agora retorna `local_agent_output` estruturado por agente (`repo_worker`, `micro_reviewer`, `arbiter`)
  - `TaskRunner` repassa `local_agent_output` no plano local e no metadata enviado ao provider
  - `local_agent_output` agora também aparece como estágio explícito (`local_analysis`) no runtime
- `[x]` padronizar interface de providers além do status `stub`
- `[x]` permitir múltiplas contas por adapter sem novo código (mapeamento `type` + resolução por prefixo em nomes `<provider>_...`)
- `[~]` adicionar fallback real entre providers
- próximo ajuste: tornar a troca entre providers sensível ao orçamento disponível por tentativa, com troca antecipada de modelo quando o primário estiver perto do limite, sem refatorar a estrutura do pipeline
- `[~]` externalizar retry/fallback policy para configuração por tarefa
  - `provider_timeout_sec` por tarefa agora está disponível no `routing.<task>.execution` e aplicado no runtime de providers

## Fase 4 - Persistência e autonomia

- `[x]` persistir orçamento diário em `var/state`
- `[~]` persistir cache de contexto e resultados reutilizáveis
  - lookup por fingerprint de payload agora disponível em `OperationalStore`
  - `task_cli` já pode reutilizar cache por padrão (`AI_CACHE_REUSE_ENABLED`, com `force_refresh` no payload para bypass)
  - fingerprint agora incorpora assinatura de conteúdo dos arquivos selecionados para invalidação automática
- `[~]` criar comandos de diagnóstico do estado global do orchestrator
- `[~]` criar comandos de diagnóstico do estado global do orchestrator
  - `diagnose-orchestrator` agora inclui métricas de índice de cache e chaves recentes de cache `inspect`
  - `diagnose-orchestrator` agora agrega resumo de status recentes (`recent_task_status_summary`) e sinais de consistência do cache (`storage_health`)
  - `diagnose-orchestrator` agora agrega alertas de orçamento (`budget.alerts`) com limiar configurável (`AI_BUDGET_ALERT_THRESHOLD_RATIO`)
  - `inspect-project` agora inclui `storage_quicklook` com resumo de status recente e sinais de consistência do cache para retomada rápida
  - `diagnose-orchestrator` e `inspect-project` agora incluem `health_summary` agregado (`ok`/`degraded`) para leitura operacional rápida
  - `diagnose-orchestrator` e `inspect-project` agora suportam `--health-only` para payload compacto em automações (cron/CI)
  - `diagnose-orchestrator` e `inspect-project` agora suportam `--fail-on-degraded` para fail-fast em automações quando a saúde agregada estiver degradada
  - `scripts/healthcheck.sh` agora oferece wrapper de automação para CI/cron com saída compacta e retorno `0/2` (inclui opção `--inspect-project`)
  - `diagnose-orchestrator`, `inspect-project` e `scripts/healthcheck.sh` agora suportam `--compact` para emissão de JSON em linha única
  - `scripts/healthcheck.sh` agora suporta `--all` para agregar `diagnose-orchestrator` + `inspect-project` em um status unificado
  - `scripts/healthcheck.sh --all` agora suporta `--strict` para emitir somente resumo/checks sem `results` detalhados
  - `scripts/healthcheck.sh` agora suporta `--quiet` para modo silencioso quando saúde final estiver `ok`
  - `scripts/healthcheck.sh` agora suporta `--output <arquivo>` para persistência do payload JSON em automações
  - também suporta `--output-dir <diretório>` para arquivo timestampado por execução
  - e `--latest-link` para manter symlink fixo `latest.json` para o último resultado
  - com `--latest-link-name <nome>` para personalizar o symlink de leitura
  - e `--meta` para anexar metadados operacionais no payload de healthcheck
  - com `--meta-fields <csv>` para emissão seletiva de campos no bloco `meta`
  - com `--meta-fields all`/`*` para seleção total explícita de campos de metadados
  - com `--meta-drop-nulls` para remover chaves nulas na emissão
  - e `--meta-flatten` para emissão sem bloco aninhado (`meta_*` no topo)
  - e `--meta-prefix <texto>` para personalizar o prefixo aplicado no flatten
  - payload de healthcheck agora inclui `artifact.path`/`artifact.latest_link` quando há saída em arquivo
- `[~]` reduzir recomputação de inspeção local
  - `inspect-task` agora suporta cache com TTL por payload e bypass via `force_refresh`
  - cache de inspeção agora invalida automaticamente quando arquivos selecionados mudam
- `[~]` reduzir dependência de wrappers manuais para tarefas recorrentes
  - aliases legados de arquivo explícito agora delegam para `inspect-task` / `assemble-context`
  - aliases legados de seleção Python agora delegam para `inspect-task` / `assemble-context`
  - `summarize-repo-area` agora delega para `assemble-context summarize-module`
  - `map-dependencies` permanece dedicado para UX/compatibilidade, mas agora usa `TaskRunner.inspect` e consome `dependency_map` do fluxo genérico

## Fase 5 - Confiabilidade

- `[x]` ampliar testes para comandos, ranking e montagem de contexto
- `[x]` cobrir cenários sem `AI_TARGET_REPO` e sem profile válido nos entrypoints genéricos
- `[x]` cobrir payload JSON inválido e payload não-objeto nos entrypoints genéricos
- `[x]` validar comportamento com múltiplos profiles além de `ia-trade`
- `[x]` documentar workflow recomendado de uso local
- `[x]` endurecer providers para respostas parciais (campos ausentes / shape inválido) com erro estruturado consistente
- `[x]` cobrir fallback em cenário de resposta parcial classificada como temporária
- `[x]` cobrir fluxo E2E `inspect-task -> task_cli` com degradação, fallback e persistência
- `[x]` cobrir concorrência leve de persistência local (`StateStore`/`CacheStore`)
- `[x]` cobrir cache E2E do `task_cli` para hit/miss conforme mudança de arquivos selecionados

### Avanços recentes de confiabilidade

- cobertura ampliada para ranking:
  - inferência de queries com deduplicação e prioridade da query explícita
  - comportamento quando objetivo só contém tokens curtos (sem seleção indevida)
- cobertura ampliada para montagem de contexto:
  - deduplicação de `files` explícitos respeitando `max_target_files`
  - tolerância a arquivos explícitos inexistentes sem falha do fluxo
- cobertura ampliada para `TaskRunner` e persistência operacional:
  - execução degradada quando profile não existe (`project profile not found`)
  - contexto parcial quando não há arquivos selecionados no repo configurado
  - persistência resiliente para saída degradada sem `provider_result`
  - chave de cache determinística para payloads com ordem diferente de campos
  - consumo de budget não é mais registrado quando provider está indisponível/configuração inválida
  - escrita atômica em `StateStore`/`CacheStore` para reduzir risco de leitura parcial em concorrência leve
- redução de excepcionalidade de `map-dependencies`:
  - parser estrutural extraído para `app/core/dependency_mapper.py`
  - `inspect-task map-dependencies` e `assemble-context map-dependencies` retornam `dependency_map`
  - `task_cli map-dependencies` agora também retorna `dependency_map` e `dependency_highlights` pelo fluxo genérico do `TaskRunner`
  - comando legado `map-dependencies` agora usa `load_runtime_project` e funciona com profiles alternativos
  - `dependency_map` agora inclui também símbolos (`functions/classes/methods`) e chamadas locais/por atributo
  - `dependency_map` agora também resolve imports locais para caminhos candidatos (grafo cross-file básico)
  - `dependency_map` agora inclui `call_relations` para ligar chamadas detectadas aos imports locais resolvidos
  - imports locais resolvidos agora incluem `target_symbols` (funções/classes exportadas do arquivo alvo)
  - `call_relations` agora saem priorizadas com `relation_score`, `relation_priority` e `relation_rank`
  - `call_relation_summary` adiciona leitura executiva por prioridade e top relação detectada
  - `call_relation_summary` agora inclui `risk_flags` para sinalizar relações não resolvidas com maior criticidade
  - `inspect-task` e `assemble-context` agora incluem `dependency_highlights` para consumo operacional rápido
- cobertura ampliada de providers:
  - `openai`, `gemini` e `claude` agora suportam execução live via HTTP quando `model` e `api_key` estão configurados
  - classificação de erro HTTP por tipo (`rate_limit`, `authorization`, `invalid_request`, `temporary`)
  - `*_API_BASE` opcional para override de endpoint por provider
  - respostas inválidas de provider (JSON malformado/shape inesperado) agora retornam erro estruturado sem interromper o pipeline
  - respostas parciais de provider (campos ausentes/shape de campos inválido) agora retornam erro estruturado sem falso `completed`
  - exceções internas de provider agora são isoladas em `BaseProvider.run` com falha classificada como temporária

## Evidências do que foi baixado

- `scripts/start.sh` já prepara `var/logs`, `var/cache` e `var/state`
- `../IA-Trade` existe no workspace atual e o acesso local foi validado
- `app/core/context_manager.py` já faz leitura real de arquivos do repo alvo
- `scripts/task.sh` já expõe:
  - `explain-file`
  - `review-file`
  - `summarize-repo-area`
  - `map-dependencies`
  - `list-python-files`
  - `pick-python-file`
  - `review-best-python-match`
  - `explain-best-python-match`
  - `inspect-project`
  - `assemble-context`
- `app/commands/pick_python_file.py` já implementa filtro de diretórios ignorados e ranking com desempate por score
- `app/core/context_builder.py` já combina bootstrap global, bootstrap do projeto, `AGENT_CONTEXT`, memórias e arquivos alvo
- `app/core/file_selector.py` centraliza coleta, ranking e seleção automática de arquivos Python
- `scripts/task.sh inspect-task` já permite inspecionar qualquer task sem criar wrapper dedicado
- `AI_PROJECTS_ROOT` já permite validar e carregar roots alternativos de profiles no runtime

## Checkpoint final desta sessão

- data do checkpoint: `2026-04-24`
- commit publicado: `38ea6e4` (`Add proactive budget-based provider switching`)
- remoto sincronizado: `origin/main`
- estado funcional entregue:
  - fallback proativo por budget headroom implementado no `TaskRunner`
  - preview explícito da decisão em `inspect-task` e `task_cli`
  - `selection_preview` com decisões operacionais curtas: `keep_primary`, `switch_now_due_to_budget`, `defer_switch_no_viable_fallback`
  - `diagnose-orchestrator` com telemetria diária de trocas proativas
  - persistência de métricas no `OperationalStore`
  - documentação e testes atualizados
- estado da validação:
  - suíte completa passando com `126` testes
- onde continuar depois:
  - refinar threshold por profile ou task-type
  - ajustar a heurística para ficar mais próxima de consumo real por modelo/tarefa
  - opcionalmente adicionar alerta quando a telemetria de trocas proativas crescer demais no dia

## Checkpoint final desta sessão

- data do checkpoint: `2026-04-25`
- estado de publicação: mudanças prontas localmente (pendente commit/push)
- bloco concluído:
  - suporte nativo a `openrouter` no runtime de providers
  - provider `openrouter` com parsing tolerante a formatos alternativos de `choices/message.content`
  - ajuste de proteção de custo/limite com `max_tokens=2048` no adapter OpenRouter
  - inclusão de `openrouter` no registro de providers, budget/config e fallback de rotas
  - atualização de docs e testes específicos do novo provider
- evidência de validação:
  - suíte de testes de providers/config passando
  - execução live de `task_cli compare-options` forçando `openrouter` finalizando com `status=completed`
- onde continuar depois:
  - tornar `provider_max_tokens` configurável por tarefa no `routing.<task>.execution`
  - classificar `HTTP 402` como falha operacional específica (crédito insuficiente)
  - persistir métricas de custo/tokens do OpenRouter no `OperationalStore` para diagnóstico diário

### docs/checklist.md
# Operational Checklist

## Before starting a session

- [ ] Run `bash scripts/start_ai_session.sh`
- [ ] Healthcheck is `ok`: `bash scripts/healthcheck.sh --all --strict`
- [ ] Project profile loaded: `bash scripts/task.sh inspect-project`
- [ ] No budget exhausted: `bash scripts/task.sh inspect-budget`
- [ ] Read `.ai_context/SESSION_STATE.md` to confirm where we left off
- [ ] `AI_TARGET_REPO` is set and target repo is accessible

## Before making changes

- [ ] Declare scope: DOCS / RUNTIME / PROVIDERS / ROUTING / BUDGET / PROJECT_PROFILE / STORAGE / SCRIPTS
- [ ] Use `inspect-task` to preview routing before executing live tasks
- [ ] Confirm whether the change is global layer or project layer — not both
- [ ] Changes to `config/` require a short justification
- [ ] Changes to `app/core/` require explicit rollback plan

## After a session

- [ ] Run `bash scripts/end_ai_session.sh "summary"`
- [ ] Commit with a scope-prefixed message (e.g., `feat(core):`, `fix(providers):`, `docs:`)
- [ ] Push to remote if the session is complete
- [ ] Verify `bash scripts/healthcheck.sh --all --strict` returns `ok`

## Periodic maintenance

- [ ] `bash scripts/task.sh purge-cache` when cache grows large
- [ ] `bash scripts/task.sh inspect-budget` to review daily spend
- [ ] `bash scripts/generate_ai_bundle.sh` after significant doc changes
- [ ] Review `.ai_context/SESSION_STATE.md` for stale state

## Adding a new project profile

- [ ] Create `projects/<project_id>/project.yaml`
- [ ] Add `AGENT_CONTEXT.md`, `CODEX_BOOTSTRAP.md`
- [ ] Add `memory/` and `prompts/` directories
- [ ] Set `AI_DEFAULT_PROJECT=<project_id>` in `.env`
- [ ] Run `bash scripts/task.sh inspect-project` to validate

### docs/references.md
# References

## Repository

- Repo: `andreyoshimura/agent-orchestrator`
- Branch: `main`
- First project profile: `projects/ia-trade/`
- Target repo (ia-trade): configured via `AI_TARGET_REPO` (default: `../IA-Trade`)

## Providers

| Provider | Type | Config prefix | Role |
|---|---|---|---|
| OpenAI | `openai` | `OPENAI_*` | Arbitration, final decision |
| Gemini | `gemini` | `GEMINI_*` | Large repo analysis, dependency mapping |
| Gemini V2 | `gemini` | `GEMINI_V2_*` | Second Gemini account, same adapter |
| Claude | `claude` | `CLAUDE_*` | Local review, snippet analysis |
| OpenRouter | `openrouter` | `OPENROUTER_*` | Multi-model fallback, OpenAI-compatible route |

## Configuration files

| File | Purpose |
|---|---|
| `config/providers.yaml` | Provider registry: type, env var names |
| `config/routing.yaml` | Task → provider mapping, retry, timeout, budget threshold |
| `config/budgets.yaml` | Daily budget caps, max context files per provider |
| `.env` | Active credentials and toggles (gitignored) |
| `.env.example` | Template |

## Project profile structure

```
projects/<project_id>/
  project.yaml          required: profile metadata, env var names, memory/prompt lists
  AGENT_CONTEXT.md      project context loaded into every agent
  CODEX_BOOTSTRAP.md    Codex-specific bootstrap for this project
  memory/
    facts.md            key project facts
    guardrails.md       project-specific guardrails
  prompts/
    repo_worker.md
    micro_reviewer.md
    arbiter.md
  playbooks/            optional task playbooks
```

## Key environment variables

| Variable | Default | Purpose |
|---|---|---|
| `AI_TARGET_REPO` | — | Path to the target repository |
| `AI_DEFAULT_PROJECT` | `ia-trade` | Active project profile ID |
| `AI_PROJECTS_ROOT` | — | Override root for project profiles |
| `AI_ROUTER_ENABLED` | `true` | Enable task router |
| `AI_REPO_WRITE_ENABLED` | `false` | Enable write access to target repo |
| `AI_CACHE_REUSE_ENABLED` | `true` | Enable task result caching |
| `AI_INSPECT_CACHE_REUSE_ENABLED` | — | Enable inspect-task caching |
| `AI_INSPECT_CACHE_TTL_SEC` | — | TTL for inspect-task cache entries |
| `AI_BUDGET_ALERT_THRESHOLD_RATIO` | — | Budget alert threshold ratio |
| `BUDGET_<PROVIDER>_DAILY_USD` | — | Daily budget cap per provider |
| `MAX_CONTEXT_FILES_<PROVIDER>` | — | Max files sent to each provider |
| `<PROVIDER>_ENABLED` | — | Toggle provider on/off |
| `<PROVIDER>_MODEL` | — | Model alias for provider |
| `<PROVIDER>_API_KEY` | — | API credentials |
| `<PROVIDER>_API_BASE` | — | Optional endpoint override |

## Model aliases (current `.env`)

| Alias | Provider |
|---|---|
| `high_reasoning` | OpenAI |
| `code_heavy` | Gemini / Gemini V2 |
| `cheap_local_reviewer` | Claude |
| `openrouter/pareto-code` | OpenRouter |

## Key source files

| File | Role |
|---|---|
| `app/core/task_runner.py` | Main pipeline executor |
| `app/core/context_builder.py` | Context assembly |
| `app/core/file_selector.py` | File ranking and selection |
| `app/core/project_loader.py` | Profile loading |
| `app/core/provider_failure_policy.py` | Fallback/retry policy |
| `app/core/operational_store.py` | State + cache persistence |
| `config/routing.yaml` | Routing rules |

