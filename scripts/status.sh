#!/usr/bin/env bash
set -euo pipefail

echo "agent-orchestrator status"
echo "AI_ROUTER_ENABLED=${AI_ROUTER_ENABLED:-unset}"
echo "AI_DEFAULT_PROJECT=${AI_DEFAULT_PROJECT:-unset}"
echo "AI_TARGET_REPO=${AI_TARGET_REPO:-unset}"
echo "AI_REPO_WRITE_ENABLED=${AI_REPO_WRITE_ENABLED:-unset}"
echo
echo "AI session workflow:"
echo "  start: bash scripts/start_ai_session.sh"
echo "  end:   bash scripts/end_ai_session.sh \"summary of session\""
echo
echo "Safe diagnostics:"
echo "  bash scripts/healthcheck.sh --all --strict"
echo "  bash scripts/task.sh inspect-project"
echo "  bash scripts/task.sh diagnose-orchestrator --health-only"
echo "  bash scripts/task.sh inspect-budget"
