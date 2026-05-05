# agent-orchestrator - Workflow diario de sessao IA

Este arquivo documenta como iniciar e encerrar sessoes com OpenAI, Gemini, Codex ou outro agente sem depender de memoria humana.

## Inicio do dia

Quando os scripts de sessao existirem, use:

```bash
bash scripts/start_ai_session.sh
```

Enquanto o script ainda nao existir, use manualmente:

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

Depois, na IA, envie:

```text
Retome o agent-orchestrator usando o contexto do repo.

Leia primeiro:
- .ai_context/SESSION_STATE.md
- .ai_context/AI_SYNC.md
- .ai_context/CONTEXT_MINIMAL.md
- .ai_context/GUARDRAILS.md
- .ai_context/TASK_FORMATS.md
- docs/ai_context_progress.md

Antes de alterar qualquer coisa, me diga:
- estado atual
- onde paramos
- alertas ou degradacoes operacionais
- pendencias
- proximo passo recomendado

Nao altere arquivos ainda.
Nao altere runtime, providers, routing ou budget.
Nao acione providers externos sem necessidade clara.
Nao misture memoria de outro projeto.
```

## Durante o trabalho

Regras:

- declarar escopo antes de alterar algo;
- separar DOCS, RUNTIME, PROVIDERS, ROUTING, BUDGET, PROJECT_PROFILE, STORAGE e SCRIPTS;
- usar comandos de inspecao antes de execucao;
- nao alterar configuracao operacional sem justificativa;
- nao tratar cache ou state como fonte absoluta da verdade;
- usar o menor contexto suficiente.

## Fim do dia

Quando o script existir, use:

```bash
bash scripts/end_ai_session.sh "resumo curto do que foi feito hoje"
```

Enquanto o script ainda nao existir, atualize manualmente:

```text
.ai_context/SESSION_STATE.md
```

Inclua:

- timestamp;
- escopo trabalhado;
- arquivos alterados;
- decisoes tomadas;
- validacoes executadas;
- pendencias;
- proximo passo recomendado.

## Arquivos de referencia

- `.ai_context/SESSION_STATE.md`: onde paramos.
- `.ai_context/AI_SYNC.md`: alinhamento comum entre OpenAI, Gemini e Codex.
- `.ai_context/CONTEXT_MINIMAL.md`: contexto minimo.
- `.ai_context/GUARDRAILS.md`: regras de seguranca.
- `.ai_context/TASK_FORMATS.md`: formato de resposta.
- `docs/ai_context_progress.md`: fases e progresso.

## Regra permanente

Se estiver em duvida, comece com:

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

Depois leia `.ai_context/SESSION_STATE.md` e confirme onde paramos antes de alterar arquivos.
