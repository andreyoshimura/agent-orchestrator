#!/usr/bin/env bash
set -euo pipefail

echo "agent-orchestrator status"
echo "AI_ROUTER_ENABLED=${AI_ROUTER_ENABLED:-unset}"
echo "AI_DEFAULT_PROJECT=${AI_DEFAULT_PROJECT:-unset}"
echo "AI_TARGET_REPO=${AI_TARGET_REPO:-unset}"
echo "AI_REPO_WRITE_ENABLED=${AI_REPO_WRITE_ENABLED:-unset}"
