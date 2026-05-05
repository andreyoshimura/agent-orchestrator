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
