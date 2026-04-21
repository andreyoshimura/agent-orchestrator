#!/usr/bin/env bash
set -euo pipefail

TASK_TYPE="${1:-}"
shift || true

if [[ -z "${TASK_TYPE}" ]]; then
  echo "usage: scripts/task.sh <task-type> [json-payload]"
  exit 1
fi

PAYLOAD="${1:-{}}"

python -m app.cli.task_cli "${TASK_TYPE}" "${PAYLOAD}"
