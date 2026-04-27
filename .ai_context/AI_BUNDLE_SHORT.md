# agent-orchestrator - AI Bundle Short

Uso: contexto minimo para colar em OpenAI, Gemini, Codex ou outro agente.

## Estado oficial

- Projeto: agent-orchestrator
- Repo: andreyoshimura/agent-orchestrator
- Funcao: orquestrador generico de agentes IA e providers
- Profiles por projeto: `projects/<project_id>/`
- Estado/cache local: `var/state` e `var/cache`

## Ordem de contexto

1. `.ai_context/CONTEXT_MINIMAL.md`
2. `.ai_context/GUARDRAILS.md`
3. `.ai_context/TASK_FORMATS.md`
4. `.ai_context/AI_SYNC.md`
5. `.ai_context/SESSION_STATE.md`

## Comandos seguros

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Guardrails essenciais

- Declarar escopo antes de alterar algo.
- Nao alterar runtime, providers, routing ou budget sem decisao explicita.
- Nao ativar escrita em repositorios-alvo sem autorizacao explicita.
- Nao misturar memoria de projetos diferentes.
- Nao tratar cache/state como fonte absoluta da verdade.
- Nao acionar providers externos sem necessidade clara.

## Politica de economia

- Nao carregar README completo por padrao.
- Nao carregar logs brutos por padrao.
- Nao carregar `var/cache` ou `var/state` completo por padrao.
- Usar o menor contexto suficiente.
