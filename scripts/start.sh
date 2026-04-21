#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "${ROOT_DIR}/var/logs" "${ROOT_DIR}/var/cache" "${ROOT_DIR}/var/state"

echo "agent-orchestrator initialized"
echo "logs: ${ROOT_DIR}/var/logs"
echo "cache: ${ROOT_DIR}/var/cache"
echo "state: ${ROOT_DIR}/var/state"
