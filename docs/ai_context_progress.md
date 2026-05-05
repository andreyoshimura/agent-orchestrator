# agent-orchestrator - Progresso de contexto IA

Este arquivo registra a implantacao da infraestrutura de continuidade, alinhamento e economia de contexto para OpenAI, Gemini, Codex e outros agentes.

## Estado atual

- Projeto: agent-orchestrator
- Repo: `andreyoshimura/agent-orchestrator`
- Fase concluida: Fase 4 - Bundles IA
- Proxima fase obrigatoria: nenhuma
- Status: infraestrutura IA basica completa

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

Status: concluida

Arquivos criados:

- `docs/ai_context_progress.md`
- `docs/ai_session_workflow.md`

Resultado:

- Fluxo de inicio e fim de sessao documentado.
- Fases concluidas registradas.
- Processo nao depende mais de memoria humana.

## Fase 3 - Scripts de sessao

Status: concluida

Arquivos criados:

- `scripts/start_ai_session.sh`
- `scripts/end_ai_session.sh`

Resultado:

- Inicio de sessao automatizado com diagnosticos seguros.
- Prompt pronto para IA impresso no terminal.
- Encerramento de sessao atualiza `.ai_context/SESSION_STATE.md`.

Uso:

```bash
bash scripts/start_ai_session.sh
bash scripts/end_ai_session.sh "resumo curto da sessao"
```

## Fase 4 - Bundles IA

Status: concluida

Arquivos criados:

- `.ai_context/AI_BUNDLE_SHORT.md`
- `.ai_context/AI_BUNDLE.md`
- `scripts/generate_ai_bundle.sh`

Resultado:

- Contexto portavel para OpenAI, Gemini, Codex e outros agentes.
- Bundle curto para uso diario.
- Bundle completo para sessoes longas.
- Menos necessidade de abrir varios arquivos manualmente.

Uso:

```bash
bash scripts/generate_ai_bundle.sh
```

## Fluxo diario recomendado

Inicio:

```bash
bash scripts/start_ai_session.sh
```

Depois copiar o prompt impresso para OpenAI/Gemini/Codex.

Fim:

```bash
bash scripts/end_ai_session.sh "resumo do que foi feito"
```

## Comandos seguros de retomada

```bash
bash scripts/healthcheck.sh --all --strict
bash scripts/task.sh inspect-project
bash scripts/task.sh diagnose-orchestrator --health-only
bash scripts/task.sh inspect-budget
```

## Proximas fases opcionais

Nenhuma fase obrigatoria no momento.

Possiveis evolucoes futuras:

- copiar prompt automaticamente para clipboard;
- abrir bundle automaticamente no terminal/editor;
- integrar com tmux ou workflow local;
- adicionar validacao automatica dos arquivos `.ai_context`.

## Regra permanente

Usar o menor contexto suficiente para a tarefa.

Nao carregar por padrao:

- README completo;
- logs brutos;
- `var/cache` completo;
- `var/state` completo;
- memoria de outro projeto.
