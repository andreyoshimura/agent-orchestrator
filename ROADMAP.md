# Roadmap

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
  - payload JSON inválido agora retorna erro estruturado nos entrypoints genéricos
  - profile inválido agora retorna erro estruturado nos entrypoints genéricos
  - execução com target repo não configurado agora está coberta nos testes de entrypoint

## Fase 2 - Montagem automática de contexto

- `[x]` criar um montador global de contexto por tarefa
- `[x]` combinar bootstrap global + profile do projeto + memória + arquivos selecionados
- `[x]` mover heurísticas de seleção/ranking para `app/core/`
- `[ ]` permitir regras específicas por profile sem contaminar a camada global

## Fase 3 - Execução real do fluxo

- `[~]` transformar `TaskRunner` em executor real de pipeline
- `[~]` conectar agentes ao carregamento de prompts e memória do projeto
- `[x]` padronizar interface de providers além do status `stub`
- `[~]` adicionar fallback real entre providers
- `[~]` externalizar retry/fallback policy para configuração por tarefa

## Fase 4 - Persistência e autonomia

- `[x]` persistir orçamento diário em `var/state`
- `[~]` persistir cache de contexto e resultados reutilizáveis
- `[~]` criar comandos de diagnóstico do estado global do orchestrator
- `[~]` reduzir dependência de wrappers manuais para tarefas recorrentes
  - aliases legados de arquivo explícito agora delegam para `inspect-task` / `assemble-context`
  - aliases legados de seleção Python agora delegam para `inspect-task` / `assemble-context`
  - `summarize-repo-area` agora delega para `assemble-context summarize-module`
  - `map-dependencies` permanece dedicado para parsing estrutural via AST, mas agora compartilha runtime/profile e inspeção estrutural com entrypoints genéricos

## Fase 5 - Confiabilidade

- `[~]` ampliar testes para comandos, ranking e montagem de contexto
- `[x]` cobrir cenários sem `AI_TARGET_REPO` e sem profile válido nos entrypoints genéricos
- `[~]` cobrir payload JSON inválido e payload não-objeto nos entrypoints genéricos
- `[x]` validar comportamento com múltiplos profiles além de `ia-trade`
- `[x]` documentar workflow recomendado de uso local

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
- redução de excepcionalidade de `map-dependencies`:
  - parser estrutural extraído para `app/core/dependency_mapper.py`
  - `inspect-task map-dependencies` e `assemble-context map-dependencies` retornam `dependency_map`
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
