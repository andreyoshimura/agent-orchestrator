import json
import sys

from app.cli.payload_parser import parse_json_payload
from app.cli.task_cli import _load_yaml, _resolve_daily_limits
from app.core.budget_manager import BudgetManager
from app.core.project_loader import load_runtime_project
from app.core.router import Router
from app.core.task_runner import TaskRequest, TaskRunner
from app.providers.config import load_provider_settings
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

    inspection = runner.inspect(TaskRequest(task_type=task_type, payload=payload))

    result = {
        "status": "ok",
        "project_id": runtime_project.project_id,
        "inspection": inspection,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
