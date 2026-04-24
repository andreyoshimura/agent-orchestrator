# Status

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
  - persistência operacional básica em `var/state` e `var/cache`
  - persistência diária de orçamento por provider em `var/state`
  - inspeção genérica de rota/plano/contexto para qualquer tarefa
  - suporte a `AI_PROJECTS_ROOT` para validar múltiplos profiles
  - testes cobrindo profile alternativo além de `ia-trade`
- o próximo passo recomendado ao retomar é:
  - consolidar cenários restantes de confiabilidade no core (principalmente fluxos de comparação estrutural)
  - manter cobertura explícita para profile inválido, payload inválido e execução com target repo não configurado
  - revisar política de invalidação de cache em casos de arquivos não selecionados, mas semanticamente relevantes

## Atualização de continuidade

- data da retomada: `2026-04-24`
- bloco concluído nesta sessão:
  - providers endurecidos para resposta parcial (JSON válido com campos ausentes/shape inválido) com erro estruturado:
    - `openai`: `missing_output_text` e `output_text_not_string`
    - `gemini`: `missing_candidates` e `candidates_not_list`
    - `claude`: `missing_content` e `content_not_list`
  - `TaskRunner.inspect` e `TaskRunner.run` agora incluem `dependency_map` + `dependency_highlights` para `map-dependencies` no fluxo genérico
  - `inspect-task` deixou de ter lógica dedicada para `map-dependencies`, consumindo o caminho genérico do runner
  - `routing.yaml` passou a declarar `review-file` explicitamente e ampliou fallback de `map-dependencies` para `claude` + `openai`
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
  - `TaskRunner` agora publica `execution_metrics` por execução (planejamento, tentativas de provider e tempo total), com persistência no `OperationalStore`
  - `map-dependencies` legado agora usa `TaskRunner.inspect` internamente para consumir `dependency_map` do fluxo genérico
  - timeout de provider por tarefa (`provider_timeout_sec`) agora é lido de `routing.<task>.execution` e aplicado no runtime HTTP dos providers
  - cobertura E2E ampliada para sequência `inspect-task -> task_cli` com degradação + fallback + persistência
- suíte atual: `python3 -m unittest -q` com `94` testes (`OK`)

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

- `ROADMAP.md`
- `STATUS.md`
- `app/core/project_loader.py`
- `config/routing.yaml`
- `app/core/task_runner.py`
- `app/core/provider_failure_policy.py`
- `app/core/operational_store.py`
- `app/core/context_builder.py`
- `app/core/file_selector.py`
