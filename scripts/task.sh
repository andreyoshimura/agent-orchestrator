#!/usr/bin/env bash
set -euo pipefail

# Resolve a raiz do projeto e garante imports Python locais.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

run_module() {
  "${PYTHON_BIN}" -m "$@"
}

json_payload() {
  local query="${1:-}"
  local objective="${2:-}"
  "${PYTHON_BIN}" -c 'import json, sys; print(json.dumps({"query": sys.argv[1], "objective": sys.argv[2]}))' "${query}" "${objective}"
}

json_file_payload() {
  local file="${1:-}"
  local objective="${2:-}"
  "${PYTHON_BIN}" -c 'import json, sys; print(json.dumps({"file": sys.argv[1], "objective": sys.argv[2]}))' "${file}" "${objective}"
}

json_files_payload() {
  local objective="${1:-}"
  shift || true
  "${PYTHON_BIN}" -c 'import json, sys; print(json.dumps({"files": sys.argv[2:], "objective": sys.argv[1]}))' "${objective}" "$@"
}

# Primeiro argumento = tipo de tarefa.
TASK_TYPE="${1:-}"
shift || true

if [[ -z "${TASK_TYPE}" ]]; then
  echo "usage: scripts/task.sh <task-type> [arg...]"
  exit 1
fi

case "${TASK_TYPE}" in
  explain-file)
    # Alias legado: monta contexto genérico para um arquivo explícito.
    TARGET_FILE="${1:-README.md}"
    PAYLOAD="$(json_file_payload "${TARGET_FILE}" "Explain the selected file with minimal context.")"
    run_module app.commands.assemble_context explain-file "${PAYLOAD}"
    ;;
  review-file)
    # Alias legado: usa inspeção genérica do plano local para um arquivo explícito.
    TARGET_FILE="${1:-README.md}"
    PAYLOAD="$(json_file_payload "${TARGET_FILE}" "Review the selected file with minimal context.")"
    run_module app.commands.inspect_task review-file "${PAYLOAD}"
    ;;
  summarize-repo-area)
    # Alias legado: monta contexto genérico para sumarização de múltiplos arquivos.
    if [[ "$#" -eq 0 ]]; then
      PAYLOAD="$(json_files_payload "Summarize the selected repository area." "README.md" "AGENTS.md")"
    else
      PAYLOAD="$(json_files_payload "Summarize the selected repository area." "$@")"
    fi
    run_module app.commands.assemble_context summarize-module "${PAYLOAD}"
    ;;
  map-dependencies)
    # Ferramenta estrutural dedicada: extrai imports locais e externos via AST.
    TARGET_FILE="${1:-paper_trade.py}"
    run_module app.commands.map_dependencies "${TARGET_FILE}"
    ;;
  list-python-files)
    # Lista arquivos Python válidos do repo alvo.
    run_module app.commands.list_python_files
    ;;
  pick-python-file)
    # Alias legado: usa o fluxo genérico para inspecionar a seleção automática.
    QUERY="${1:-paper}"
    PAYLOAD="$(json_payload "${QUERY}" "Inspect the best Python file candidates for this query.")"
    run_module app.commands.inspect_task review-file "${PAYLOAD}"
    ;;
  review-best-python-match)
    # Alias legado: usa a inspeção genérica do plano local para revisar o melhor match.
    QUERY="${1:-paper}"
    PAYLOAD="$(json_payload "${QUERY}" "Review the best Python file match for this query.")"
    run_module app.commands.inspect_task review-file "${PAYLOAD}"
    ;;
  explain-best-python-match)
    # Alias legado: monta contexto genérico do melhor match em vez de usar wrapper dedicado.
    QUERY="${1:-paper}"
    PAYLOAD="$(json_payload "${QUERY}" "Explain the best Python file match for this query.")"
    run_module app.commands.assemble_context explain-file "${PAYLOAD}"
    ;;
  inspect-project)
    # Inspeciona o profile atual e o repo alvo configurado.
    PROJECT_ID="${1:-${AI_DEFAULT_PROJECT:-ia-trade}}"
    run_module app.commands.inspect_project "${PROJECT_ID}"
    ;;
  assemble-context)
    # Monta contexto reutilizável para uma tarefa usando bootstrap, memórias e arquivos alvo.
    INNER_TASK_TYPE="${1:-explain-file}"
    shift || true
    if [[ "$#" -eq 0 ]]; then
      PAYLOAD="{}"
    else
      PAYLOAD="$*"
    fi
    run_module app.commands.assemble_context "${INNER_TASK_TYPE}" "${PAYLOAD}"
    ;;
  inspect-task)
    # Inspeciona rota, contexto, plano local e disponibilidade de providers para qualquer tarefa.
    INNER_TASK_TYPE="${1:-explain-file}"
    shift || true
    if [[ "$#" -eq 0 ]]; then
      PAYLOAD="{}"
    else
      PAYLOAD="$*"
    fi
    run_module app.commands.inspect_task "${INNER_TASK_TYPE}" "${PAYLOAD}"
    ;;
  inspect-budget)
    # Mostra o orçamento diário acumulado e restante por provider.
    run_module app.commands.inspect_budget
    ;;
  diagnose-orchestrator)
    # Mostra estado global do orchestrator, budget e persistência local.
    run_module app.commands.diagnose_orchestrator
    ;;
  *)
    # Fallback para o roteador genérico.
    if [[ "$#" -eq 0 ]]; then
      PAYLOAD="{}"
    else
      PAYLOAD="$*"
    fi
    run_module app.cli.task_cli "${TASK_TYPE}" "${PAYLOAD}"
    ;;
esac
