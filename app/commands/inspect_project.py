import json
import os
import sys
from pathlib import Path
from typing import Any

from app.core.project_loader import load_runtime_project
from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore


def _path_status(path: Path) -> dict:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
    }


def _target_repo_summary(target_repo: str) -> dict:
    if not target_repo:
        return {
            "configured": False,
            "path": "",
            "exists": False,
            "is_dir": False,
            "top_level_entries": [],
        }

    path = Path(target_repo).resolve()
    entries = []
    if path.exists() and path.is_dir():
        entries = sorted(item.name for item in path.iterdir())[:20]

    return {
        "configured": True,
        "path": str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "top_level_entries": entries,
    }


def _safe_load_state(state_store: StateStore, key: str) -> dict:
    payload = state_store.load(key)
    if isinstance(payload, dict):
        return payload
    return {}


def _recent_task_status_summary(state_store: StateStore, limit: int = 10) -> dict[str, Any]:
    counts: dict[str, int] = {}
    keys = state_store.list_keys(prefix="last_task_")
    for key in sorted(keys, reverse=True)[:limit]:
        payload = _safe_load_state(state_store, key)
        status = payload.get("status")
        normalized = status if isinstance(status, str) and status else "unknown"
        counts[normalized] = counts.get(normalized, 0) + 1
    return {
        "sampled_state_count": min(len(keys), limit),
        "statuses": dict(sorted(counts.items())),
    }


def _storage_health_quicklook(cache_store: CacheStore) -> dict[str, Any]:
    indexed_entries = cache_store.list_entries(limit=1000)
    indexed_with_file_count = sum(
        1
        for entry in indexed_entries
        if (cache_store.base_dir / f"{entry.get('digest', '')}.txt").exists()
    )
    cache_entry_count = cache_store.count()
    return {
        "cache_entry_count": cache_entry_count,
        "cache_indexed_entry_count": len(indexed_entries),
        "cache_index_missing_file_count": max(len(indexed_entries) - indexed_with_file_count, 0),
        "cache_unindexed_file_estimate": max(cache_entry_count - indexed_with_file_count, 0),
        "cache_index_consistent": (
            len(indexed_entries) == cache_entry_count and indexed_with_file_count == cache_entry_count
        ),
    }


def _build_health_summary(target_repo: dict[str, Any], storage_health: dict[str, Any], profile_files: dict[str, Any]) -> dict[str, Any]:
    signals: list[str] = []
    if not bool(target_repo.get("configured")):
        signals.append("target_repo_not_configured")
    elif not bool(target_repo.get("exists")):
        signals.append("target_repo_missing")
    if not bool(storage_health.get("cache_index_consistent", True)):
        signals.append("cache_index_inconsistent")

    missing_profile_files = 0
    fixed_paths = ["project_yaml", "bootstrap", "agent_context"]
    for key in fixed_paths:
        item = profile_files.get(key, {})
        if isinstance(item, dict) and not bool(item.get("exists", False)):
            missing_profile_files += 1
    memory_files = profile_files.get("memory_files", [])
    if isinstance(memory_files, list):
        missing_profile_files += sum(
            1
            for item in memory_files
            if isinstance(item, dict) and not bool(item.get("exists", False))
        )
    prompt_files = profile_files.get("prompt_files", {})
    if isinstance(prompt_files, dict):
        missing_profile_files += sum(
            1
            for item in prompt_files.values()
            if isinstance(item, dict) and not bool(item.get("exists", False))
        )
    if missing_profile_files > 0:
        signals.append("profile_files_missing")

    return {
        "status": "degraded" if signals else "ok",
        "signals": signals,
        "missing_profile_file_count": missing_profile_files,
    }


def _parse_args(args: list[str]) -> tuple[str | None, bool, bool, bool]:
    project_id: str | None = None
    health_only = False
    fail_on_degraded = False
    compact = False
    for arg in args:
        if arg == "--health-only":
            health_only = True
            continue
        if arg == "--fail-on-degraded":
            fail_on_degraded = True
            continue
        if arg == "--compact":
            compact = True
            continue
        if project_id is None:
            project_id = arg
    return project_id, health_only, fail_on_degraded, compact


def _print_payload(payload: dict[str, Any], compact: bool) -> None:
    if compact:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    project_id_arg, health_only, fail_on_degraded, compact = _parse_args(sys.argv[1:])
    project_id = project_id_arg or os.getenv("AI_DEFAULT_PROJECT", "ia-trade")

    try:
        runtime = load_runtime_project(project_id=project_id)
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    profile = runtime.profile
    state_store = StateStore()
    cache_store = CacheStore()
    memory_status = [_path_status(Path(path)) for path in profile.memory_files]
    prompt_status = {
        name: _path_status(Path(path))
        for name, path in profile.prompt_files.items()
    }
    target_repo = _target_repo_summary(runtime.target_repo)
    storage_health = _storage_health_quicklook(cache_store)
    profile_files = {
        "project_yaml": _path_status(profile.project_yaml_path),
        "bootstrap": _path_status(profile.bootstrap_path),
        "agent_context": _path_status(profile.agent_context_path),
        "memory_files": memory_status,
        "prompt_files": prompt_status,
    }

    result = {
        "status": "ok",
        "project_id": profile.project_id,
        "display_name": profile.display_name,
        "project_dir": str(profile.project_dir),
        "default_mode": profile.default_mode,
        "agent_profile": profile.agent_profile,
        "repo_path_env": profile.repo_path_env,
        "write_enabled_env": profile.write_enabled_env,
        "write_enabled": runtime.write_enabled,
        "profile_files": profile_files,
        "target_repo": target_repo,
        "health_summary": _build_health_summary(target_repo, storage_health, profile_files),
        "storage_quicklook": {
            "state_dir": str(state_store.base_dir),
            "cache_dir": str(cache_store.base_dir),
            "recent_task_status_summary": _recent_task_status_summary(state_store),
            "storage_health": storage_health,
        },
    }

    if health_only:
        _print_payload({
            "status": "ok",
            "mode": "health-only",
            "project_id": profile.project_id,
            "health_summary": result["health_summary"],
            "checks": {
                "target_repo_exists": bool(target_repo.get("exists", False)),
                "cache_index_consistent": bool(storage_health.get("cache_index_consistent", True)),
            },
        }, compact=compact)
        if result["health_summary"].get("status") == "degraded" and fail_on_degraded:
            return 2
        return 0

    _print_payload(result, compact=compact)
    if result["health_summary"].get("status") == "degraded" and fail_on_degraded:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
