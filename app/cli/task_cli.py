import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

from app.core.budget_manager import BudgetManager
from app.core.project_loader import load_runtime_project
from app.core.router import Router
from app.core.task_runner import TaskRequest, TaskRunner
from app.providers.config import load_provider_settings
from app.storage.audit_log import AuditLog
from app.storage.state_store import StateStore


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
    if len(sys.argv) < 2:
        print("usage: python -m app.cli.task_cli <task-type> [json-payload]")
        return 1

    if not _env_bool("AI_ROUTER_ENABLED", True):
        print(json.dumps({"status": "disabled", "reason": "AI_ROUTER_ENABLED=false"}, ensure_ascii=False, indent=2))
        return 0

    task_type = sys.argv[1]

    raw_payload = " ".join(sys.argv[2:]).strip()
    if not raw_payload:
        payload = {}
    else:
        payload = json.loads(raw_payload)

    routing_config = _load_yaml("config/routing.yaml").get("routing", {})
    budgets_config = _load_yaml("config/budgets.yaml")
    runtime_project = load_runtime_project()
    project_id = runtime_project.project_id

    daily_limits = _resolve_daily_limits(budgets_config)
    provider_settings = load_provider_settings()
    router = Router(routing_config)
    budget_manager = BudgetManager(daily_limits, state_store=StateStore())
    runner = TaskRunner(router, budget_manager, provider_settings=provider_settings)
    audit = AuditLog()

    payload = {
        **payload,
        "project_id": project_id,
        "target_repo": runtime_project.target_repo,
        "write_enabled": runtime_project.write_enabled,
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
