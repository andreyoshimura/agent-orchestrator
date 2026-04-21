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
  - cobrir comandos CLI (`inspect-project`, `inspect-task`, `diagnose-orchestrator`) em cenários reais com profile alternativo
  - reduzir wrappers legados já substituíveis por inspeção genérica
  - depois ampliar confiabilidade operacional do fluxo completo

## Encerramento do dia

- data do checkpoint: `2026-04-21`
- último bloco concluído:
  - persistência diária de budget
  - diagnósticos operacionais
  - `inspect-task`
  - suporte/testes para múltiplos profiles via `AI_PROJECTS_ROOT`
- ponto exato para retomar amanhã:
  - iniciar pela cobertura dos comandos CLI usando profile alternativo e repo configurado
  - depois revisar quais wrappers ainda podem ser removidos sem perder usabilidade local

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
