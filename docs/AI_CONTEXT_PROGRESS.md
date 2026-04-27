# agent-orchestrator - Progresso de contexto IA

Este arquivo registra a implantacao da infraestrutura de continuidade, alinhamento e economia de contexto para OpenAI, Gemini, Codex e outros agentes.

## Estado atual

- Projeto: agent-orchestrator
- Repo: `andreyoshimura/agent-orchestrator`
- Fase concluida: Fase 1 - Contexto IA minimo e guardrails
- Fase atual: Fase 2 - Documentacao operacional

## Objetivo da infraestrutura

- Evitar perda de historico entre sessoes.
- Reduzir consumo de tokens.
- Manter OpenAI, Gemini e Codex alinhados.
- Evitar alteracoes perigosas em runtime, providers, routing, budgets e storage.
- Garantir que memoria de projetos diferentes nao se misture.

## Fase 1 - Contexto IA minimo e guardrails

Status: concluida

Arquivos criados:

- `.ai_context/CONTEXT_MINIMAL.md`
- `.ai_context/GUARDRAILS.md`
- `.ai_context/TASK_FORMATS.md`
- `.ai_context/AI_SYNC.md`
- `.ai_context/SESSION_STATE.md`

Resultado:

- Existe um ponto de entrada minimo para IA.
- Existem guardrails claros para runtime, providers, routing, budget, storage e profiles.
- OpenAI, Gemini e Codex usam o mesmo contrato de contexto.
- O estado da sessao pode ser retomado por `.ai_context/SESSION_STATE.md`.

## Fase 2 - Documentacao operacional

Status: em andamento

Arquivos previstos:

- `docs/AI_CONTEXT_PROGRESS.md`
- `docs/AI_SESSION_WORKFLOW.md`

Objetivo:

- Documentar o fluxo de inicio e fim de sessao.
- Registrar fases concluidas.
- Evitar dependencia de memoria humana.

## Proximas fases previstas

### Fase 3 - Scripts de sessao

Criar:

- `scripts/start_ai_session.sh`
- `scripts/end_ai_session.sh`

Objetivo:

- Automatizar inicio de trabalho com IA.
- Atualizar contexto operacional.
- Persistir onde paramos no encerramento.

### Fase 4 - Bundles IA

Criar:

- `.ai_context/AI_BUNDLE_SHORT.md`
- `.ai_context/AI_BUNDLE.md`
- `scripts/generate_ai_bundle.sh`

Objetivo:

- Permitir copiar contexto unico para IA externa.
- Evitar abrir muitos arquivos manualmente.

## Comandos seguros de retomada

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Regra permanente

Usar o menor contexto suficiente para a tarefa.

Nao carregar por padrao:

- README completo;
- logs brutos;
- `var/cache` completo;
- `var/state` completo;
- memoria de outro projeto.
