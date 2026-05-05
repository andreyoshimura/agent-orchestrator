#!/usr/bin/env bash
set -euo pipefail

# Generate AI bundles for external usage

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

SHORT_OUT=".ai_context/AI_BUNDLE_SHORT.md"
FULL_OUT=".ai_context/AI_BUNDLE.md"

# SHORT bundle (static already, just confirm exists)
echo "[AI-BUNDLE] short bundle ready: $SHORT_OUT"

# FULL bundle (light aggregation)
{
  echo "# agent-orchestrator - AI Bundle (Generated)"
  echo
  echo "## CONTEXT_MINIMAL"
  cat .ai_context/CONTEXT_MINIMAL.md
  echo
  echo "## GUARDRAILS"
  cat .ai_context/GUARDRAILS.md
  echo
  echo "## TASK_FORMATS"
  cat .ai_context/TASK_FORMATS.md
  echo
  echo "## AI_SYNC"
  cat .ai_context/AI_SYNC.md
  echo
  echo "## SESSION_STATE"
  cat .ai_context/SESSION_STATE.md
  echo
  echo "## DOCS INDEX"
  echo
  for doc in docs/architecture.md docs/operations.md docs/roadmap.md docs/checklist.md docs/references.md; do
    if [[ -f "$doc" ]]; then
      echo "### $doc"
      cat "$doc"
      echo
    fi
  done
} > "$FULL_OUT"

echo "[AI-BUNDLE] full bundle generated: $FULL_OUT"
