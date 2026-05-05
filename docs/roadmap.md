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

## Checkpoint final desta sessão

- data do checkpoint: `2026-05-04`
- commit: pendente
- remoto: pendente push
- bloco concluído:
  - `provider_max_tokens` por tarefa no `routing.<task>.execution` — flui via `RouteDecision` até cada provider
  - HTTP `402` mapeado para `insufficient_credits` em todos os providers; adicionado a `FALLBACK_FAILURE_TYPES`
  - usage metrics do OpenRouter (`prompt_tokens`, `completion_tokens`, `total_tokens`) extraídos e incluídos no `output`
  - `OperationalStore.persist_task_result` extrai `provider_usage` e acumula em `provider_usage_metrics_{date}`
  - `diagnose-orchestrator` expõe `provider_usage_telemetry` no bloco `storage` e nos checks do modo `--health-only`
  - `AI_PROACTIVE_SWITCH_ALERT_THRESHOLD` (default 20) adicionado; sinal `proactive_switches_high` no `health_summary`
  - docs reorganizados em `docs/` (architecture, operations, roadmap, checklist, references, bootstrap, ai workflows)
  - README reescrito em ~45 linhas
  - `AI_BUNDLE_SHORT.md` e `generate_ai_bundle.sh` atualizados para referenciar nova estrutura de docs
  - target_repo_not_configured e cache_index_inconsistent eliminados do healthcheck
  - `.env` carregado como fallback (sem sobrescrever vars já exportadas) em `task.sh` e `healthcheck.sh`
  - `purge-cache` exposto em `task.sh` com `CacheStore.purge_unindexed()`
- evidência de validação:
  - `150` testes passando
  - `healthcheck --all --strict` retornando `ok` sem sinais
  - `inspect-task review-file` executando sem erros
- onde continuar depois:
  - refinar threshold de `provider_max_tokens` por profile/model
  - adicionar usage telemetry para providers além do OpenRouter (Claude, Gemini, OpenAI)
  - alertas de custo/token diário no `health_summary`
  - explorar streaming de providers para tarefas longas
