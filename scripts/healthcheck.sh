#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  while IFS= read -r _line || [[ -n "$_line" ]]; do
    [[ "$_line" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${_line//[[:space:]]/}" ]] && continue
    _varname="${_line%%=*}"
    _varname="${_varname#"${_varname%%[![:space:]]*}"}"
    [[ -z "$_varname" ]] && continue
    if [[ -z "${!_varname+x}" ]]; then
      export "$_line" 2>/dev/null || true
    fi
  done < "${ROOT_DIR}/.env"
  unset _line _varname
fi

usage() {
  cat <<'EOF'
usage: scripts/healthcheck.sh [--inspect-project|--all] [--compact] [--strict] [--quiet] [--meta] [--meta-fields <csv>] [--meta-drop-nulls] [--meta-flatten] [--meta-prefix <text>] [--output <file>|--output-dir <dir>] [--latest-link] [--latest-link-name <name>] [project-id]

Default behavior:
  - Runs diagnose-orchestrator in health-only mode.
  - Exits with code 2 when health is degraded.

Options:
  --inspect-project   Use inspect-project health-only check instead of diagnose-orchestrator.
  --all               Run diagnose-orchestrator and inspect-project and aggregate the result.
  --compact           Emit single-line JSON output.
  --strict            With --all, omit detailed results and emit only summary/checks.
  --quiet             Suppress output when final status is ok (exit code 0).
  --meta              Add metadata block: generated_at, host, project_id, argv.
  --meta-fields <csv> Comma-separated subset of meta fields to include (or all/*).
  --meta-drop-nulls   Remove null values from metadata fields before output.
  --meta-flatten      Promote meta fields to top-level keys as meta_<field>.
  --meta-prefix <txt> Prefix used by --meta-flatten (default: meta_).
  --output <file>     Write the resulting JSON payload to a file.
  --output-dir <dir>  Write the payload to a timestamped file in a directory.
  --latest-link       With --output-dir, update latest.json symlink to newest payload.
  --latest-link-name  Symlink filename used with --latest-link (default: latest.json).
  -h, --help          Show this help.
EOF
}

MODE="diagnose"
PROJECT_ID="${AI_DEFAULT_PROJECT:-ia-trade}"
COMPACT=0
STRICT=0
QUIET=0
META=0
META_FIELDS="generated_at,host,project_id,argv,scope"
META_DROP_NULLS=0
META_FLATTEN=0
META_PREFIX="meta_"
OUTPUT_PATH=""
OUTPUT_DIR=""
LATEST_LINK=0
LATEST_LINK_NAME="latest.json"
RESOLVED_OUTPUT_PATH=""
RESOLVED_LATEST_LINK_PATH=""
PYTHON_BIN="${PYTHON_BIN:-python3}"
ORIGINAL_ARGS=("$@")

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --inspect-project)
      MODE="inspect-project"
      shift
      ;;
    --compact)
      COMPACT=1
      shift
      ;;
    --all)
      MODE="all"
      shift
      ;;
    --strict)
      STRICT=1
      shift
      ;;
    --quiet)
      QUIET=1
      shift
      ;;
    --meta)
      META=1
      shift
      ;;
    --meta-fields)
      if [[ "$#" -lt 2 ]]; then
        echo "error: --meta-fields requires a comma-separated value list" >&2
        exit 1
      fi
      META=1
      META_FIELDS="$2"
      shift 2
      ;;
    --meta-drop-nulls)
      META=1
      META_DROP_NULLS=1
      shift
      ;;
    --meta-flatten)
      META=1
      META_FLATTEN=1
      shift
      ;;
    --meta-prefix)
      if [[ "$#" -lt 2 ]]; then
        echo "error: --meta-prefix requires a prefix value" >&2
        exit 1
      fi
      META=1
      META_FLATTEN=1
      META_PREFIX="$2"
      shift 2
      ;;
    --output)
      if [[ "$#" -lt 2 ]]; then
        echo "error: --output requires a file path" >&2
        exit 1
      fi
      OUTPUT_PATH="$2"
      shift 2
      ;;
    --output-dir)
      if [[ "$#" -lt 2 ]]; then
        echo "error: --output-dir requires a directory path" >&2
        exit 1
      fi
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --latest-link)
      LATEST_LINK=1
      shift
      ;;
    --latest-link-name)
      if [[ "$#" -lt 2 ]]; then
        echo "error: --latest-link-name requires a name" >&2
        exit 1
      fi
      LATEST_LINK_NAME="$2"
      LATEST_LINK=1
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      PROJECT_ID="$1"
      shift
      ;;
  esac
done

if [[ -n "${OUTPUT_PATH}" && -n "${OUTPUT_DIR}" ]]; then
  echo "error: use either --output or --output-dir, not both" >&2
  exit 1
fi
if [[ "${META}" -eq 1 ]]; then
  env META_FIELDS="${META_FIELDS}" "${PYTHON_BIN}" -c '
import os
import sys
allowed = {"generated_at", "host", "project_id", "argv", "scope"}
raw = os.environ.get("META_FIELDS", "")
if raw.strip().lower() in {"all", "*"}:
    sys.exit(0)
fields = [item.strip() for item in raw.split(",") if item.strip()]
if not fields:
    sys.exit(1)
for field in fields:
    if field not in allowed:
        sys.exit(2)
' || {
    case "$?" in
      1) echo "error: --meta-fields must include at least one valid field" >&2 ;;
      2) echo "error: --meta-fields contains unsupported keys (allowed: generated_at,host,project_id,argv,scope)" >&2 ;;
      *) echo "error: invalid --meta-fields value" >&2 ;;
    esac
    exit 1
  }
fi
if [[ -z "${META_PREFIX}" || "${META_PREFIX}" == *" "* || "${META_PREFIX}" == *"/"* ]]; then
  echo "error: --meta-prefix must be non-empty and must not contain spaces or '/'" >&2
  exit 1
fi
if [[ -z "${LATEST_LINK_NAME}" || "${LATEST_LINK_NAME}" == *"/"* ]]; then
  echo "error: --latest-link-name must be a simple filename" >&2
  exit 1
fi
if [[ "${LATEST_LINK}" -eq 1 && -z "${OUTPUT_DIR}" ]]; then
  echo "error: --latest-link requires --output-dir" >&2
  exit 1
fi

FLAGS=(--health-only --fail-on-degraded)
if [[ "${COMPACT}" -eq 1 ]]; then
  FLAGS+=(--compact)
fi

run_capture() {
  local out_var="$1"
  local rc_var="$2"
  shift 2
  local captured_out
  local captured_rc
  set +e
  captured_out="$("$@" 2>&1)"
  captured_rc=$?
  set -e
  printf -v "${out_var}" '%s' "${captured_out}"
  printf -v "${rc_var}" '%s' "${captured_rc}"
}

prepare_output_paths() {
  RESOLVED_OUTPUT_PATH="${OUTPUT_PATH}"
  RESOLVED_LATEST_LINK_PATH=""
  if [[ -n "${OUTPUT_DIR}" ]]; then
    mkdir -p "${OUTPUT_DIR}"
    local ts
    ts="$(date '+%Y%m%d-%H%M%S')"
    RESOLVED_OUTPUT_PATH="${OUTPUT_DIR}/healthcheck-${ts}-${$}.json"
    if [[ "${LATEST_LINK}" -eq 1 ]]; then
      RESOLVED_LATEST_LINK_PATH="${OUTPUT_DIR}/${LATEST_LINK_NAME}"
    fi
  fi
}

add_meta_if_enabled() {
  local raw_payload="$1"
  local scope="$2"
  if [[ "${META}" -ne 1 ]]; then
    printf '%s' "${raw_payload}"
    return
  fi
  local argv_text="scripts/healthcheck.sh"
  if [[ "${#ORIGINAL_ARGS[@]}" -gt 0 ]]; then
    argv_text+=" ${ORIGINAL_ARGS[*]}"
  fi
  env \
    RAW_PAYLOAD="${raw_payload}" \
    COMPACT="${COMPACT}" \
    PROJECT_ID_INPUT="${PROJECT_ID}" \
    ARGV_TEXT="${argv_text}" \
    META_FIELDS="${META_FIELDS}" \
    META_DROP_NULLS="${META_DROP_NULLS}" \
    META_FLATTEN="${META_FLATTEN}" \
    META_PREFIX="${META_PREFIX}" \
    SCOPE="${scope}" \
    "${PYTHON_BIN}" -c '
import json
import os
import socket
from datetime import datetime, timezone

raw_payload = os.environ.get("RAW_PAYLOAD", "")
compact = os.environ.get("COMPACT", "0") == "1"
project_id_input = os.environ.get("PROJECT_ID_INPUT", "")
argv_text = os.environ.get("ARGV_TEXT", "scripts/healthcheck.sh")
scope = os.environ.get("SCOPE", "")
meta_fields = [item.strip() for item in os.environ.get("META_FIELDS", "").split(",") if item.strip()]
if not meta_fields or os.environ.get("META_FIELDS", "").strip().lower() in {"all", "*"}:
    meta_fields = ["generated_at", "host", "project_id", "argv", "scope"]
meta_drop_nulls = os.environ.get("META_DROP_NULLS", "0") == "1"
meta_flatten = os.environ.get("META_FLATTEN", "0") == "1"
meta_prefix = os.environ.get("META_PREFIX", "meta_")

try:
    payload = json.loads(raw_payload)
except json.JSONDecodeError:
    payload = {"status": "error", "raw_output": raw_payload}

if not isinstance(payload, dict):
    payload = {"status": "error", "raw_output": raw_payload}

project_id = payload.get("project_id")
if not isinstance(project_id, str) or not project_id:
    project = payload.get("project")
    if isinstance(project, dict):
        p = project.get("project_id")
        if isinstance(p, str) and p:
            project_id = p
if (not isinstance(project_id, str) or not project_id) and project_id_input:
    project_id = project_id_input

meta_source = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "host": socket.gethostname(),
    "project_id": project_id if isinstance(project_id, str) and project_id else None,
    "argv": argv_text,
    "scope": scope or None,
}
filtered_meta = {key: meta_source.get(key) for key in meta_fields}
if meta_drop_nulls:
    filtered_meta = {key: value for key, value in filtered_meta.items() if value is not None}
if meta_flatten:
    for key, value in filtered_meta.items():
        payload[f"{meta_prefix}{key}"] = value
else:
    payload["meta"] = filtered_meta

if compact:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
else:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
'
}

add_artifact_if_enabled() {
  local raw_payload="$1"
  if [[ -z "${RESOLVED_OUTPUT_PATH}" ]]; then
    printf '%s' "${raw_payload}"
    return
  fi
  env \
    RAW_PAYLOAD="${raw_payload}" \
    COMPACT="${COMPACT}" \
    ARTIFACT_PATH="${RESOLVED_OUTPUT_PATH}" \
    ARTIFACT_LATEST_LINK="${RESOLVED_LATEST_LINK_PATH}" \
    "${PYTHON_BIN}" -c '
import json
import os

raw_payload = os.environ.get("RAW_PAYLOAD", "")
compact = os.environ.get("COMPACT", "0") == "1"
artifact_path = os.environ.get("ARTIFACT_PATH", "")
artifact_latest = os.environ.get("ARTIFACT_LATEST_LINK", "")

try:
    payload = json.loads(raw_payload)
except json.JSONDecodeError:
    payload = {"status": "error", "raw_output": raw_payload}

if not isinstance(payload, dict):
    payload = {"status": "error", "raw_output": raw_payload}

artifact = {"path": artifact_path}
if artifact_latest:
    artifact["latest_link"] = artifact_latest
payload["artifact"] = artifact

if compact:
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
else:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
'
}

write_output_file() {
  local payload="$1"
  if [[ -z "${RESOLVED_OUTPUT_PATH}" ]]; then
    return
  fi
  printf '%s\n' "${payload}" > "${RESOLVED_OUTPUT_PATH}"
  if [[ "${LATEST_LINK}" -eq 1 && -n "${RESOLVED_LATEST_LINK_PATH}" ]]; then
    ln -sfn "$(basename "${RESOLVED_OUTPUT_PATH}")" "${RESOLVED_LATEST_LINK_PATH}"
  fi
}

prepare_output_paths

if [[ "${MODE}" == "all" ]]; then
  diagnose_output=""
  diagnose_rc=0
  inspect_output=""
  inspect_rc=0

  run_capture diagnose_output diagnose_rc bash scripts/task.sh diagnose-orchestrator "${FLAGS[@]}"
  run_capture inspect_output inspect_rc bash scripts/task.sh inspect-project "${PROJECT_ID}" "${FLAGS[@]}"

  final_rc=0
  if [[ "${diagnose_rc}" -eq 2 || "${inspect_rc}" -eq 2 ]]; then
    final_rc=2
  fi
  if [[ "${diagnose_rc}" -ne 0 && "${diagnose_rc}" -ne 2 ]]; then
    final_rc=1
  fi
  if [[ "${inspect_rc}" -ne 0 && "${inspect_rc}" -ne 2 ]]; then
    final_rc=1
  fi

  aggregate_output=""
  aggregate_rc=0
  run_capture aggregate_output aggregate_rc env \
  DIAGNOSE_OUTPUT="${diagnose_output}" \
  DIAGNOSE_RC="${diagnose_rc}" \
  INSPECT_OUTPUT="${inspect_output}" \
  INSPECT_RC="${inspect_rc}" \
  FINAL_RC="${final_rc}" \
  COMPACT="${COMPACT}" \
  STRICT="${STRICT}" \
  "${PYTHON_BIN}" -c '
import json
import os

def parse_payload(raw: str):
    try:
        payload = json.loads(raw)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass
    return {"status": "error", "raw_output": raw}

diagnose_payload = parse_payload(os.environ.get("DIAGNOSE_OUTPUT", ""))
inspect_payload = parse_payload(os.environ.get("INSPECT_OUTPUT", ""))
diagnose_rc = int(os.environ.get("DIAGNOSE_RC", "1"))
inspect_rc = int(os.environ.get("INSPECT_RC", "1"))
final_rc = int(os.environ.get("FINAL_RC", "1"))
compact = os.environ.get("COMPACT", "0") == "1"
strict = os.environ.get("STRICT", "0") == "1"

signals: list[str] = []
if diagnose_rc == 2:
    signals.append("diagnose_degraded")
if inspect_rc == 2:
    signals.append("inspect_project_degraded")
if diagnose_rc not in (0, 2):
    signals.append("diagnose_command_error")
if inspect_rc not in (0, 2):
    signals.append("inspect_project_command_error")

aggregate = {
    "status": "ok" if final_rc in (0, 2) else "error",
    "mode": "health-only",
    "scope": "all",
    "health_summary": {
        "status": "ok" if final_rc == 0 else ("degraded" if final_rc == 2 else "error"),
        "signals": signals,
    },
    "checks": {
        "diagnose_orchestrator": {
            "exit_code": diagnose_rc,
            "health_status": diagnose_payload.get("health_summary", {}).get("status"),
        },
        "inspect_project": {
            "exit_code": inspect_rc,
            "health_status": inspect_payload.get("health_summary", {}).get("status"),
        },
    },
}

if not strict:
    aggregate["results"] = {
        "diagnose_orchestrator": diagnose_payload,
        "inspect_project": inspect_payload,
    }

if compact:
    print(json.dumps(aggregate, ensure_ascii=False, separators=(",", ":")))
else:
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
'
  if [[ "${aggregate_rc}" -ne 0 ]]; then
    printf '%s\n' "${aggregate_output}" >&2
    exit 1
  fi
  aggregate_output="$(add_meta_if_enabled "${aggregate_output}" "all")"
  aggregate_output="$(add_artifact_if_enabled "${aggregate_output}")"
  write_output_file "${aggregate_output}"
  if [[ "${QUIET}" -ne 1 || "${final_rc}" -ne 0 ]]; then
    printf '%s\n' "${aggregate_output}"
  fi
  exit "${final_rc}"
fi

if [[ "${MODE}" == "inspect-project" ]]; then
  output=""
  rc=0
  run_capture output rc bash scripts/task.sh inspect-project "${PROJECT_ID}" "${FLAGS[@]}"
  output="$(add_meta_if_enabled "${output}" "inspect-project")"
  output="$(add_artifact_if_enabled "${output}")"
  write_output_file "${output}"
  if [[ "${QUIET}" -ne 1 || "${rc}" -ne 0 ]]; then
    printf '%s\n' "${output}"
  fi
  exit "${rc}"
fi

output=""
rc=0
run_capture output rc bash scripts/task.sh diagnose-orchestrator "${FLAGS[@]}"
output="$(add_meta_if_enabled "${output}" "diagnose-orchestrator")"
output="$(add_artifact_if_enabled "${output}")"
write_output_file "${output}"
if [[ "${QUIET}" -ne 1 || "${rc}" -ne 0 ]]; then
  printf '%s\n' "${output}"
fi
exit "${rc}"
