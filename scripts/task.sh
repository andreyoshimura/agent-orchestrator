#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

TASK_TYPE="${1:-}"
shift || true

if [[ -z "${TASK_TYPE}" ]]; then
  echo "usage: scripts/task.sh <task-type> [json-payload]"
  exit 1
fi

PAYLOAD="${1:-{}}"

python -m app.cli.task_cli "${TASK_TYPE}" "${PAYLOAD}"
