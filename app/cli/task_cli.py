import json
import sys
from pathlib import Path

import yaml

from app.core.budget_manager import BudgetManager
from app.core.router import Router
from app.core.task_runner import TaskRequest, TaskRunner
from app.storage.audit_log import AuditLog


def _load_yaml(path: str):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: python -m app.cli.task_cli <task-type> <json-payload>")
        return 1

    task_type = sys.argv[1]
    payload = json.loads(sys.argv[2])

    routing = _load_yaml("config/routing.yaml").get("routing", {})
    budgets = _load_yaml("config/budgets.yaml").get("budgets", {})

    daily_limits = {
        "openai": float(budgets.get("openai", {}).get("daily_usd_env", 0) or 0),
        "gemini": float(budgets.get("gemini", {}).get("daily_usd_env", 0) or 0),
        "claude": float(budgets.get("claude", {}).get("daily_usd_env", 0) or 0),
    }

    router = Router(routing)
    budget_manager = BudgetManager(daily_limits)
    runner = TaskRunner(router, budget_manager)
    audit = AuditLog()

    result = runner.run(TaskRequest(task_type=task_type, payload=payload))
    audit.write({
        "task_type": result.task_type,
        "provider": result.provider,
        "status": result.status,
    })
    print(json.dumps({
        "provider": result.provider,
        "task_type": result.task_type,
        "status": result.status,
        "output": result.output,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
