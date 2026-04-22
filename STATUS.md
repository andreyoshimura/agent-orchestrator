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

## Próximo foco

- reduzir seleção manual de contexto
- aumentar autonomia do fluxo local
- evoluir o core sem acoplar o orchestrator ao profile `ia-trade`
- consolidar aliases legados sobre `inspect-task` / `assemble-context`

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
  - ampliar cenários de erro também nos entrypoints CLI e no carregamento de payload inválido
  - depois ampliar confiabilidade operacional do fluxo completo

## Encerramento do dia

- data do checkpoint: `2026-04-21`
- último bloco concluído:
  - persistência diária de budget
  - diagnósticos operacionais
  - `inspect-task`
  - suporte/testes para múltiplos profiles via `AI_PROJECTS_ROOT`
  - cobertura dos comandos CLI com profile alternativo
  - consolidação de aliases legados (`explain-file`, `review-file`) sobre o fluxo genérico
  - consolidação de alias legado (`summarize-repo-area`) sobre o fluxo genérico
  - consolidação de aliases legados (`pick-python-file`, `explain-best-python-match`, `review-best-python-match`) sobre o fluxo genérico
  - documentação do workflow recomendado de uso local
  - decisão de manter `map-dependencies` como ferramenta estrutural dedicada
- ponto exato para retomar amanhã:
  - ampliar cenários de erro também nos entrypoints CLI e no carregamento de payload inválido
  - depois revisar se vale criar um task-type genérico de análise estrutural para reduzir a excepcionalidade de `map-dependencies`

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
