#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

rm -rf "${ROOT_DIR}/var/cache" || true
rm -rf "${ROOT_DIR}/var/state" || true

echo "Local cache and state removed."
echo "To fully remove the orchestrator, delete this repository directory."
