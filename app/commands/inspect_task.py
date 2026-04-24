import json
import hashlib
import os
import sys
import time
from pathlib import Path

from app.cli.payload_parser import parse_json_payload
from app.cli.task_cli import _env_bool, _load_yaml, _resolve_daily_limits
from app.core.budget_manager import BudgetManager
from app.core.project_loader import load_runtime_project
from app.core.router import Router
from app.core.task_runner import TaskRequest, TaskRunner
from app.providers.config import load_provider_settings
from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.inspect_task <task-type> [json-payload]")
        return 1

    task_type = sys.argv[1]
    raw_payload = " ".join(sys.argv[2:]).strip()
    payload, payload_error = parse_json_payload(raw_payload)
    if payload_error:
        print(json.dumps({"status": "error", "reason": payload_error}, ensure_ascii=False, indent=2))
        return 1

    routing_config = _load_yaml("config/routing.yaml").get("routing", {})
    budgets_config = _load_yaml("config/budgets.yaml")
    try:
        runtime_project = load_runtime_project()
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    provider_settings = load_provider_settings()
    budget_manager = BudgetManager(_resolve_daily_limits(budgets_config), state_store=StateStore())
    runner = TaskRunner(
        router=Router(routing_config),
        budget_manager=budget_manager,
        provider_settings=provider_settings,
    )

    payload = {
        **payload,
        "project_id": runtime_project.project_id,
        "target_repo": runtime_project.target_repo,
        "write_enabled": runtime_project.write_enabled,
    }

    cache_enabled = _env_bool("AI_INSPECT_CACHE_REUSE_ENABLED", True)
    cache_ttl_seconds = _env_int("AI_INSPECT_CACHE_TTL_SEC", 30)
    force_refresh = bool(payload.get("force_refresh"))
    cache_store = CacheStore()
    cache_key = _inspect_cache_key(
        project_id=runtime_project.project_id,
        task_type=task_type,
        payload=payload,
    )
    if cache_enabled and not force_refresh:
        cached_inspection = _load_cached_inspection(
            cache_store=cache_store,
            cache_key=cache_key,
            ttl_seconds=cache_ttl_seconds,
        )
        if cached_inspection is not None:
            result = {
                "status": "ok",
                "project_id": runtime_project.project_id,
                "inspection": {
                    **cached_inspection,
                    "cache": {
                        "hit": True,
                        "ttl_seconds": cache_ttl_seconds,
                    },
                },
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0

    inspection = runner.inspect(TaskRequest(task_type=task_type, payload=payload))
    if cache_enabled and cache_ttl_seconds > 0:
        _save_cached_inspection(
            cache_store=cache_store,
            cache_key=cache_key,
            inspection=inspection,
        )
    inspection = {
        **inspection,
        "cache": {
            "hit": False,
            "ttl_seconds": cache_ttl_seconds,
        },
    }

    result = {
        "status": "ok",
        "project_id": runtime_project.project_id,
        "inspection": inspection,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def _inspect_cache_key(project_id: str, task_type: str, payload: dict) -> str:
    fingerprint = json.dumps(
        {
            "project_id": project_id,
            "task_type": task_type,
            "payload": payload,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
    return f"inspect:{project_id}:{task_type}:{digest}"


def _load_cached_inspection(cache_store: CacheStore, cache_key: str, ttl_seconds: int) -> dict | None:
    if ttl_seconds <= 0:
        return None
    raw = cache_store.get(cache_key)
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    created_at = parsed.get("created_at")
    inspection = parsed.get("inspection")
    target_repo = parsed.get("target_repo", "")
    selected_files = parsed.get("selected_files", [])
    file_signature = parsed.get("file_signature", "")
    if (
        not isinstance(created_at, (int, float))
        or not isinstance(inspection, dict)
        or not isinstance(target_repo, str)
        or not isinstance(selected_files, list)
        or not isinstance(file_signature, str)
    ):
        return None
    if (time.time() - float(created_at)) > ttl_seconds:
        return None
    if file_signature != _cache_file_signature(target_repo, selected_files):
        return None
    return inspection


def _save_cached_inspection(cache_store: CacheStore, cache_key: str, inspection: dict) -> None:
    if not isinstance(inspection, dict):
        return
    target_repo = _target_repo_from_inspection(inspection)
    selected_files = _selected_files_from_inspection(inspection)
    payload = {
        "created_at": time.time(),
        "target_repo": target_repo,
        "selected_files": selected_files,
        "file_signature": _cache_file_signature(target_repo, selected_files),
        "inspection": inspection,
    }
    cache_store.set(
        cache_key,
        json.dumps(payload, ensure_ascii=False, indent=2),
    )


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _target_repo_from_inspection(inspection: dict) -> str:
    context = inspection.get("context", {})
    if not isinstance(context, dict):
        return ""
    target_repo = context.get("target_repo", {})
    if not isinstance(target_repo, dict):
        return ""
    return str(target_repo.get("path", "")).strip()


def _selected_files_from_inspection(inspection: dict) -> list[str]:
    local_plan = inspection.get("local_plan", {})
    if not isinstance(local_plan, dict):
        return []
    selected_files = local_plan.get("selected_files", [])
    if not isinstance(selected_files, list):
        return []
    return [str(item) for item in selected_files if isinstance(item, str)]


def _cache_file_signature(target_repo: str, selected_files: list[object]) -> str:
    repo_root = Path(target_repo).resolve() if target_repo else None
    normalized = [str(item) for item in selected_files if isinstance(item, str)]
    fingerprints: list[dict[str, object]] = []
    for relative_path in normalized:
        if repo_root is None:
            fingerprints.append({"file": relative_path, "exists": False, "reason": "no_repo"})
            continue
        full_path = (repo_root / relative_path).resolve()
        if not str(full_path).startswith(str(repo_root)):
            fingerprints.append({"file": relative_path, "exists": False, "reason": "out_of_repo"})
            continue
        if not full_path.exists() or not full_path.is_file():
            fingerprints.append({"file": relative_path, "exists": False, "reason": "missing"})
            continue
        content = full_path.read_bytes()
        stat = full_path.stat()
        fingerprints.append(
            {
                "file": relative_path,
                "exists": True,
                "size": int(stat.st_size),
                "mtime_ns": int(stat.st_mtime_ns),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    digest_input = json.dumps(fingerprints, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
