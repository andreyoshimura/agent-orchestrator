# agent-orchestrator - Session State

Este arquivo registra onde paramos entre sessoes de trabalho com IA.

## Ultima atualizacao

- timestamp_local: pendente
- timestamp_utc: pendente

## Estado oficial

- Projeto: agent-orchestrator
- Repo: `andreyoshimura/agent-orchestrator`
- Funcao: orquestrador generico de agentes IA e providers
- Profiles por projeto: `projects/<project_id>/`
- Estado local: `var/state`
- Cache local: `var/cache`

## Onde paramos

- Fase 1 da infraestrutura IA em implantacao.
- Arquivos ja criados:
  - `.ai_context/CONTEXT_MINIMAL.md`
  - `.ai_context/GUARDRAILS.md`
  - `.ai_context/TASK_FORMATS.md`
  - `.ai_context/AI_SYNC.md`
  - `.ai_context/SESSION_STATE.md`

## Guardrails conhecidos

- Nao alterar runtime central sem escopo claro.
- Nao alterar roteamento ou limites sem decisao explicita.
- Nao ativar escrita em repositorios-alvo sem autorizacao explicita.
- Nao misturar memoria de projetos diferentes.
- Nao acionar providers externos sem necessidade clara.

## Proximo passo recomendado

- Criar documentacao de continuidade:
  - `docs/AI_CONTEXT_PROGRESS.md`
  - `docs/AI_SESSION_WORKFLOW.md`

## Comandos seguros para retomada

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Nao fazer

- Nao editar runtime, routing, providers ou budget sem escopo claro.
- Nao apagar `var/cache` ou `var/state` sem pedido explicito.
- Nao carregar logs brutos por padrao.
- Nao copiar contexto de outro projeto.
