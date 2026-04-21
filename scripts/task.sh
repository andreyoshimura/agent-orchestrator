#!/usr/bin/env bash
set -euo pipefail

# Resolve a raiz do projeto e garante imports Python locais.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

# Primeiro argumento = tipo de tarefa.
TASK_TYPE="${1:-}"
shift || true

if [[ -z "${TASK_TYPE}" ]]; then
  echo "usage: scripts/task.sh <task-type> [arg...]"
  exit 1
fi

case "${TASK_TYPE}" in
  explain-file)
    # Lê um arquivo do repo alvo e devolve preview estruturado.
    TARGET_FILE="${1:-README.md}"
    python3 -m app.commands.explain_file "${TARGET_FILE}"
    ;;
  review-file)
    # Faz uma revisão estrutural simples do arquivo alvo.
    TARGET_FILE="${1:-README.md}"
    python3 -m app.commands.review_file "${TARGET_FILE}"
    ;;
  summarize-repo-area)
    # Resume múltiplos arquivos. Sem args, usa defaults do comando.
    if [[ "$#" -eq 0 ]]; then
      python3 -m app.commands.summarize_repo_area
    else
      python3 -m app.commands.summarize_repo_area "$@"
    fi
    ;;
  map-dependencies)
    # Extrai imports locais e externos de um arquivo Python.
    TARGET_FILE="${1:-paper_trade.py}"
    python3 -m app.commands.map_dependencies "${TARGET_FILE}"
    ;;
  list-python-files)
    # Lista arquivos Python válidos do repo alvo.
    python3 -m app.commands.list_python_files
    ;;
  pick-python-file)
    # Procura arquivos Python por nome parcial.
    QUERY="${1:-paper}"
    python3 -m app.commands.pick_python_file "${QUERY}"
    ;;
  review-best-python-match)
    # Procura o melhor candidato por nome parcial e já faz review.
    QUERY="${1:-paper}"
    python3 -m app.commands.review_best_python_match "${QUERY}"
    ;;
  explain-best-python-match)
    # Procura o melhor candidato por nome parcial e já faz preview estrutural.
    QUERY="${1:-paper}"
    python3 -m app.commands.explain_best_python_match "${QUERY}"
    ;;
  inspect-project)
    # Inspeciona o profile atual e o repo alvo configurado.
    PROJECT_ID="${1:-${AI_DEFAULT_PROJECT:-ia-trade}}"
    python3 -m app.commands.inspect_project "${PROJECT_ID}"
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
    python3 -m app.commands.assemble_context "${INNER_TASK_TYPE}" "${PAYLOAD}"
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
    python3 -m app.commands.inspect_task "${INNER_TASK_TYPE}" "${PAYLOAD}"
    ;;
  inspect-budget)
    # Mostra o orçamento diário acumulado e restante por provider.
    python3 -m app.commands.inspect_budget
    ;;
  diagnose-orchestrator)
    # Mostra estado global do orchestrator, budget e persistência local.
    python3 -m app.commands.diagnose_orchestrator
    ;;
  *)
    # Fallback para o roteador genérico.
    if [[ "$#" -eq 0 ]]; then
      PAYLOAD="{}"
    else
      PAYLOAD="$*"
    fi
    python3 -m app.cli.task_cli "${TASK_TYPE}" "${PAYLOAD}"
    ;;
esac
