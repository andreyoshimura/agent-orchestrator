#!/usr/bin/env bash
set -euo pipefail

# agent-orchestrator AI session bootstrap.
#
# Purpose:
# - prepare the repo before starting work with OpenAI, Gemini, Codex, or another AI agent;
# - run safe health and diagnostic commands;
# - print a ready-to-copy resume prompt.
#
# Safe behavior:
# - this script does not deploy;
# - this script does not change runtime, routing, providers or budgets;
# - this script does not mutate target repositories;
# - it only runs read-oriented diagnostics.
#
# Daily usage:
#   bash scripts/start_ai_session.sh

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

run_safe() {
  local label="$1"
  shift
  echo "[AI-SESSION] ${label}"
  "$@" || true
}

echo "[AI-SESSION] Starting session for agent-orchestrator"

if [[ -f scripts/generate_ai_bundle.sh ]]; then
  run_safe "Generating AI bundles" bash scripts/generate_ai_bundle.sh
fi

run_safe "Healthcheck" bash scripts/healthcheck.sh --all --strict
run_safe "Inspect project" bash scripts/task.sh inspect-project
run_safe "Diagnose orchestrator" bash scripts/task.sh diagnose-orchestrator --health-only
run_safe "Inspect budget" bash scripts/task.sh inspect-budget

echo "[AI-SESSION] Session context ready"
echo
cat <<'PROMPT'
================ COPY THIS TO THE AI TOOL ================
Retome o agent-orchestrator usando o contexto do repo.

Leia primeiro:
- .ai_context/SESSION_STATE.md
- .ai_context/AI_SYNC.md
- .ai_context/CONTEXT_MINIMAL.md
- .ai_context/GUARDRAILS.md
- .ai_context/TASK_FORMATS.md
- docs/AI_CONTEXT_PROGRESS.md

Antes de alterar qualquer coisa, me diga:
- estado atual
- onde paramos
- alertas ou degradacoes operacionais
- pendencias
- proximo passo recomendado

Regras:
- Nao altere arquivos ainda.
- Nao altere runtime, providers, routing ou budget.
- Nao acione providers externos sem necessidade clara.
- Nao misture memoria de outro projeto.
- Use o menor contexto suficiente.
================ END PROMPT ==============================
PROMPT
