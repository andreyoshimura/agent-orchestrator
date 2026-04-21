import json
import os
from pathlib import Path

from app.cli.task_cli import _load_yaml, _resolve_daily_limits
from app.core.budget_manager import BudgetManager
from app.core.project_loader import load_runtime_project
from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore


def _safe_load_state(state_store: StateStore, key: str) -> dict:
    payload = state_store.load(key)
    if isinstance(payload, dict):
        return payload
    return {}


def _recent_task_states(state_store: StateStore, limit: int = 5) -> list[dict]:
    keys = state_store.list_keys(prefix="last_task_")
    recent = []
    for key in sorted(keys, reverse=True)[:limit]:
        payload = _safe_load_state(state_store, key)
        recent.append({
            "key": key,
            "task_type": payload.get("task_type"),
            "project_id": payload.get("project_id"),
            "provider": payload.get("provider"),
            "status": payload.get("status"),
            "selected_files": payload.get("selected_files", []),
        })
    return recent


def main() -> int:
    state_store = StateStore()
    cache_store = CacheStore()
    budgets_config = _load_yaml("config/budgets.yaml")
    daily_limits = _resolve_daily_limits(budgets_config)
    budget_manager = BudgetManager(daily_limits, state_store=state_store)

    default_project = os.getenv("AI_DEFAULT_PROJECT", "ia-trade")
    try:
        runtime_project = load_runtime_project(default_project)
        project_status = {
            "status": "ok",
            "project_id": runtime_project.project_id,
            "target_repo": runtime_project.target_repo,
            "target_repo_exists": Path(runtime_project.target_repo).exists() if runtime_project.target_repo else False,
            "write_enabled": runtime_project.write_enabled,
        }
    except FileNotFoundError as exc:
        project_status = {
            "status": "error",
            "reason": str(exc),
        }

    result = {
        "status": "ok",
        "project": project_status,
        "budget": budget_manager.summary(),
        "storage": {
            "state_dir": str(state_store.base_dir),
            "state_key_count": len(state_store.list_keys()),
            "cache_dir": str(cache_store.base_dir),
            "cache_entry_count": cache_store.count(),
            "recent_task_states": _recent_task_states(state_store),
        },
        "config": {
            "routing_exists": Path("config/routing.yaml").exists(),
            "budgets_exists": Path("config/budgets.yaml").exists(),
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
