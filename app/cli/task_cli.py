import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from app.core.budget_manager import BudgetManager
from app.core.router import Router
from app.core.task_runner import TaskRequest, TaskRunner
from app.storage.audit_log import AuditLog


def _load_yaml(path: str) -> Dict[str, Any]:
    loaded = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return loaded or {}


def _env_float(name: str, default: float = 0.0) -> float:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _resolve_daily_limits(config: Dict[str, Any]) -> Dict[str, float]:
    budgets = config.get("budgets", {})
    return {
        provider: _env_float(details.get("daily_usd_env", ""), 0.0)
        for provider, details in budgets.items()
    }


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: python -m app.cli.task_cli <task-type> <json-payload>")
        return 1

    if not _env_bool("AI_ROUTER_ENABLED", True):
        print(json.dumps({"status": "disabled", "reason": "AI_ROUTER_ENABLED=false"}, ensure_ascii=False, indent=2))
        return 0

    task_type = sys.argv[1]
    payload = json.loads(sys.argv[2])

    routing_config = _load_yaml("config/routing.yaml").get("routing", {})
    budgets_config = _load_yaml("config/budgets.yaml")
    project_id = os.getenv("AI_DEFAULT_PROJECT", "ia-trade")
    project_config = _load_yaml(f"projects/{project_id}/project.yaml")

    daily_limits = _resolve_daily_limits(budgets_config)
    router = Router(routing_config)
    budget_manager = BudgetManager(daily_limits)
    runner = TaskRunner(router, budget_manager)
    audit = AuditLog()

    payload = {
        **payload,
        "project_id": project_id,
        "target_repo": os.getenv("AI_TARGET_REPO", ""),
        "write_enabled": _env_bool(project_config.get("write_enabled_env", "AI_REPO_WRITE_ENABLED"), False),
    }

    result = runner.run(TaskRequest(task_type=task_type, payload=payload))
    audit.write({
        "task_type": result.task_type,
        "provider": result.provider,
        "status": result.status,
        "project_id": project_id,
        "target_repo": payload.get("target_repo", ""),
    })
    print(json.dumps({
        "provider": result.provider,
        "task_type": result.task_type,
        "status": result.status,
        "project_id": project_id,
        "output": result.output,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
