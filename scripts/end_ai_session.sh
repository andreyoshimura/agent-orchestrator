#!/usr/bin/env bash
set -euo pipefail

# agent-orchestrator AI session shutdown.
#
# Purpose:
# - persist where we stopped working;
# - avoid relying on human memory;
# - keep a minimal last-session state for the next interaction.
#
# This script updates:
#   .ai_context/SESSION_STATE.md
#
# Usage:
#   bash scripts/end_ai_session.sh "short summary"

if [[ $# -lt 1 ]]; then
  echo "Usage: end_ai_session.sh \"summary of session\""
  exit 1
fi

SUMMARY="$1"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

FILE=".ai_context/SESSION_STATE.md"

if [[ ! -f "$FILE" ]]; then
  echo "[AI-SESSION] SESSION_STATE.md not found"
  exit 1
fi

TIMESTAMP_LOCAL="$(date '+%Y-%m-%d %H:%M:%S')"
TIMESTAMP_UTC="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"

TMP_FILE="${FILE}.tmp"

{
  echo "# agent-orchestrator - Session State"
  echo
  echo "## Ultima atualizacao"
  echo
  echo "- timestamp_local: $TIMESTAMP_LOCAL"
  echo "- timestamp_utc: $TIMESTAMP_UTC"
  echo
  echo "## Resumo da ultima sessao"
  echo
  echo "- $SUMMARY"
  echo
  echo "## Observacao"
  echo
  echo "Arquivo atualizado automaticamente via script de encerramento."
  echo
} > "$TMP_FILE"

mv "$TMP_FILE" "$FILE"

echo "[AI-SESSION] Session state updated"
