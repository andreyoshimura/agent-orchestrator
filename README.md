# agent-orchestrator

Orquestrador genérico de IA e agentes com múltiplos providers para repositórios locais.

## Objetivos

- Rotear tarefas entre múltiplos providers de IA
- Controlar orçamento e uso de tokens
- Manter a memória específica de cada projeto fora do runtime central
- Permanecer plug-and-play e reversível
- Usar acesso somente leitura por padrão nos repositórios-alvo

## Princípios de design

- Somente leitura por padrão
- Sem conversa livre entre providers
- O orchestrator é o único componente autorizado a repassar resumos estruturados entre agentes
- O caminho do repositório-alvo é configurado externamente
- O fallback entre providers é baseado em regras
- Prompts e memória específicos do projeto ficam em `projects/<project_id>/`

## Política de execução

- As preferências e fallbacks de provider por tarefa ficam em `config/routing.yaml`
- O comportamento de retry e fallback também é configurado por tarefa em `routing.<task>.execution`
- o timeout HTTP por tarefa também pode ser configurado em `routing.<task>.execution.provider_timeout_sec`
- O core mantém defaults seguros, mas a política específica de cada tarefa deve ser ajustada na configuração, não codificada diretamente no runtime

## Persistência operacional

- O resultado mais recente de cada tarefa por projeto é persistido em `var/state`
- Fingerprints resumidos de execução de tarefas são armazenados em cache em `var/cache`
- O uso diário de orçamento por provider é persistido em `var/state`
- O `task_cli` pode reutilizar resultado em cache por fingerprint de payload para reduzir reexecução em tarefas repetidas
- O fingerprint de cache também considera assinatura de conteúdo dos arquivos selecionados (hash + metadados), invalidando automaticamente após mudança de arquivo
- Essa persistência é local e reversível; ela existe para reduzir trabalho manual repetido de inspeção entre execuções

## Papéis planejados dos providers

- **Claude free**: review local pequeno, análise de snippets, segunda opinião
- **Gemini**: análise ampla do repositório, mapeamento de dependências, planejamento de refactors maiores
- **OpenAI**: arbitragem, síntese, decisão final

## Tarefas iniciais

- `explain-file`
- `review-snippet`
- `review-diff`
- `map-dependencies`
- `summarize-module`
- `compare-options`
- `final-decision`

## Fluxo local

- `bash scripts/task.sh inspect-project` inspeciona o profile ativo do projeto e valida os arquivos associados
- `bash scripts/task.sh inspect-task <task-type> '<json>'` mostra uma prévia do roteamento, arquivos selecionados, plano local e disponibilidade dos providers para qualquer tarefa
- `bash scripts/task.sh inspect-budget` mostra o gasto diário atual e o orçamento restante por provider
- `bash scripts/task.sh diagnose-orchestrator` mostra diagnósticos de projeto, runtime, configuração e armazenamento
- `bash scripts/healthcheck.sh` roda healthcheck compacto para automação (retorna `2` quando degradado)
- `bash scripts/healthcheck.sh --all` executa `diagnose-orchestrator` + `inspect-project` e agrega saúde em um único payload
- `bash scripts/healthcheck.sh --all --strict` retorna só resumo/checks (sem bloco `results`) para reduzir payload em CI
- `bash scripts/healthcheck.sh --quiet` não imprime output quando tudo está `ok` (útil para cron silencioso)
- `bash scripts/healthcheck.sh --meta` inclui metadados operacionais no payload (`generated_at`, `host`, `project_id`, `argv`)
- `--meta-fields generated_at,project_id` filtra quais campos entram no bloco `meta`
- `--meta-fields all` (ou `*`) usa todos os campos permitidos
- `--meta-drop-nulls` remove campos de `meta` com valor nulo
- `--meta-flatten` promove os campos para o topo como `meta_generated_at`, `meta_project_id`, etc.
- `--meta-prefix ctx_` personaliza o prefixo do flatten (ex.: `ctx_generated_at`)
- `bash scripts/healthcheck.sh --output /tmp/health.json` grava o payload JSON em arquivo
- `bash scripts/healthcheck.sh --output-dir /tmp/healthchecks` grava em arquivo timestampado dentro do diretório
- `bash scripts/healthcheck.sh --output-dir /tmp/healthchecks --latest-link` atualiza `/tmp/healthchecks/latest.json` para o arquivo mais recente
- `bash scripts/healthcheck.sh --output-dir /tmp/healthchecks --latest-link-name atual.json` usa nome customizado para o symlink
- `bash scripts/task.sh assemble-context <task-type> '<json>'` monta um contexto reutilizável de tarefa a partir de fontes globais e do projeto
- `bash scripts/task.sh list-python-files` lista os arquivos Python do repositório-alvo configurado

## Aliases legados

- `bash scripts/task.sh explain-file <file>` continua disponível, mas agora delega para `assemble-context explain-file`
- `bash scripts/task.sh review-file <file>` continua disponível, mas agora delega para `inspect-task review-file`
- `bash scripts/task.sh summarize-repo-area [files...]` continua disponível, mas agora delega para `assemble-context summarize-module`
- `bash scripts/task.sh pick-python-file <query>` continua disponível, mas agora delega para `inspect-task review-file` para inspecionar a seleção automática
- `bash scripts/task.sh explain-best-python-match <query>` continua disponível, mas agora delega para `assemble-context explain-file`
- `bash scripts/task.sh review-best-python-match <query>` continua disponível, mas agora delega para `inspect-task review-file`

## Comandos ainda dedicados

- `bash scripts/task.sh map-dependencies <file.py>` continua como comando dedicado para parsing estrutural via AST, mas agora usa o mesmo carregamento de profile/runtime do fluxo genérico
- internamente, o comando dedicado consome o `dependency_map` produzido pelo fluxo genérico (`TaskRunner.inspect`) para reduzir caminhos especiais

## Recomendações de uso

- prefira `inspect-task` quando quiser entender roteamento, seleção automática de arquivos e plano local
- prefira `assemble-context` quando quiser ver o contexto reutilizável que será entregue ao fluxo central
- use `PYTHON_BIN=/caminho/do/python bash scripts/task.sh ...` se precisar forçar um interpretador específico

## Workflow local recomendado

### 1. Preparar ambiente

```bash
cp .env.example .env
set -a && source .env && set +a
```

- ajuste `AI_DEFAULT_PROJECT` se quiser trocar o profile ativo
- ajuste `AI_TARGET_REPO` para o caminho local do repositório-alvo
- mantenha `AI_REPO_WRITE_ENABLED=false` por padrão
- preencha `OPENAI_MODEL` / `OPENAI_API_KEY`, `GEMINI_MODEL` / `GEMINI_API_KEY` e `CLAUDE_MODEL` / `CLAUDE_API_KEY` apenas para os providers que realmente for usar
- use `OPENAI_API_BASE`, `GEMINI_API_BASE` e `CLAUDE_API_BASE` somente se precisar sobrescrever endpoint padrão (proxy/gateway local)
- `AI_CACHE_REUSE_ENABLED=true` (default no `task_cli`) reutiliza resultado de payload idêntico; use `false` para desativar globalmente
- `AI_INSPECT_CACHE_REUSE_ENABLED=true` (default no `inspect-task`) reutiliza inspeções repetidas por payload
- `AI_INSPECT_CACHE_TTL_SEC=30` controla TTL do cache de inspeção em segundos
- o cache de `inspect-task` também invalida quando o conteúdo dos arquivos selecionados muda

### 2. Retomar sessão

```bash
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator
bash scripts/task.sh inspect-budget
bash scripts/healthcheck.sh
```

- `inspect-project` valida profile, arquivos do projeto e repo alvo, inclui `storage_quicklook` e expõe `health_summary` (`ok`/`degraded`) para leitura rápida
- `diagnose-orchestrator` mostra estado de projeto, storage e execuções recentes
- `diagnose-orchestrator` também mostra métricas de índice de cache, chaves recentes de cache de `inspect-task`, resumo de status recentes e `health_summary` agregado
- `diagnose-orchestrator` também mostra alertas de orçamento (`budget.alerts`) com limiar configurável por `AI_BUDGET_ALERT_THRESHOLD_RATIO` (default `0.1`)
- ambos suportam `--health-only` para retornar payload compacto com `health_summary` e checks essenciais (útil em cron/CI)
- ambos suportam `--fail-on-degraded` para retornar `exit code 2` quando `health_summary.status=degraded` (fail-fast em automação)
- ambos suportam `--compact` para emitir JSON em linha única (útil para pipelines shell)
- `inspect-budget` mostra orçamento diário já consumido por provider
- `healthcheck.sh` retorna payload compacto e código de saída adequado para cron/CI (`0=ok`, `2=degraded`)
- `healthcheck.sh --all` retorna degradado se qualquer check degradar e inclui resultados individuais em `results`
- `healthcheck.sh --all --strict` mantém o mesmo status/exit code, mas omite `results` detalhados
- `healthcheck.sh --quiet` mantém exit code e só imprime JSON quando houver `degraded`/`error`
- `healthcheck.sh --meta` adiciona bloco `meta` útil para trilha operacional em logs/artefatos
- `healthcheck.sh --meta-fields <csv>` permite reduzir esse bloco para campos específicos
- `healthcheck.sh --meta-fields all` (ou `*`) restaura todos os campos suportados
- `healthcheck.sh --meta-drop-nulls` remove campos nulos antes da emissão
- `healthcheck.sh --meta-flatten` evita bloco aninhado e move os campos para o nível raiz
- `healthcheck.sh --meta-prefix <texto>` personaliza o prefixo usado em `--meta-flatten`
- `healthcheck.sh --output <arquivo>` grava payload mesmo com `--quiet` (para auditoria/pipeline)
- `healthcheck.sh --output-dir <diretório>` gera `healthcheck-YYYYmmdd-HHMMSS-<pid>.json` automaticamente
- `healthcheck.sh --latest-link` (com `--output-dir`) mantém um symlink `latest.json` para leitura simples por automações
- `healthcheck.sh --latest-link-name <nome>` personaliza esse nome (ex.: `atual.json`)
- quando usa `--output`/`--output-dir`, o payload também inclui `artifact.path` (e `artifact.latest_link` quando aplicável)

### 3. Inspecionar antes de executar

```bash
bash scripts/task.sh inspect-task review-file '{"query":"paper","objective":"Revisar entrypoint paper"}'
bash scripts/task.sh assemble-context explain-file '{"file":"README.md","objective":"Explicar arquivo"}'
```

- `inspect-task` é o entrypoint principal para entender rota, arquivos selecionados, prompt e disponibilidade de providers
- `inspect-task` suporta cache de inspeção com TTL para reduzir recomputação em chamadas repetidas; use `"force_refresh": true` no payload para bypass
- `inspect-task` também expõe `local_agent_output` (saída estruturada do agente local antes da chamada ao provider)
- `task_cli` agora expõe `execution_metrics` na saída (`planning_ms`, `provider_execution_ms`, `total_ms`, tentativas)
- `assemble-context` é o entrypoint principal para conferir o contexto bruto montado pelo orchestrator
- para `map-dependencies`, ambos também retornam `dependency_map` quando houver arquivo Python selecionado
  - `dependency_map` inclui imports, símbolos, chamadas, `call_relations` priorizadas (`relation_score`/`relation_priority`/`relation_rank`), resumo executivo (`call_relation_summary`) com `risk_flags`, e resolução básica de imports locais para arquivos candidatos no repo
  - `inspect-task` e `assemble-context` também retornam `dependency_highlights` para leitura rápida operacional

### 4. Executar pelo fluxo central

```bash
python3 -m app.cli.task_cli review-file '{"query":"paper","objective":"Revisar entrypoint paper"}'
python3 -m app.cli.task_cli map-dependencies '{"file":"paper_trade.py","objective":"Mapear dependências"}'
```

- esse é o caminho recomendado quando quiser efetivamente passar pelo roteador, orçamento, retry, fallback e persistência operacional
- para forçar reexecução sem cache em uma chamada específica, inclua `"force_refresh": true` no payload JSON

### 5. Usar aliases legados só quando fizer sentido

```bash
bash scripts/task.sh explain-file README.md
bash scripts/task.sh review-file README.md
bash scripts/task.sh pick-python-file paper
```

- esses comandos continuam funcionando, mas hoje são principalmente atalhos para `inspect-task` ou `assemble-context`

### 6. Usar comandos estruturais dedicados

```bash
bash scripts/task.sh summarize-repo-area README.md AGENTS.md
bash scripts/task.sh map-dependencies paper_trade.py
```

- `summarize-repo-area` agora usa o planner genérico para montar contexto multi-arquivo
- `map-dependencies` ainda é útil para parsing estrutural (imports, símbolos e chamadas), com suporte a profiles alternativos via `AI_PROJECTS_ROOT`

## Estrutura do repositório

```text
agent-orchestrator/
  app/
    core/
    providers/
    agents/
    storage/
  config/
  projects/
    ia-trade/
      prompts/
      memory/
  scripts/
  var/
    logs/
    cache/
    state/
  .env.example
  README.md
```

## Defaults de segurança

- `AI_REPO_WRITE_ENABLED=false`
- o uso de providers é opcional e controlado por env/config
- o repositório do projeto é referenciado por caminho, não embutido neste repositório
- este repositório pode ser removido sem tocar no projeto-alvo

## Seleção de profile

- `AI_DEFAULT_PROJECT` seleciona o profile ativo do projeto
- `AI_PROJECTS_ROOT` pode apontar para um diretório alternativo de profiles ao validar múltiplos projetos localmente
- cada `projects/<project_id>/project.yaml` pode definir `context_rules` para customizar seleção de contexto por profile (`max_target_files`, `task_file_limits`, `task_queries`, `pinned_files_by_task`)
- cada `projects/<project_id>/project.yaml` também pode definir `task_prompt_overrides` para mapear `task_type -> prompt/agente`

## Próximo passo

Copie `.env.example` para `.env`, ajuste as chaves dos providers que deseja usar e configure `projects/ia-trade/project.yaml` com o caminho local do repositório-alvo.
