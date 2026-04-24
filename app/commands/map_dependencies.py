import json
import os
import sys

from app.cli.task_cli import _load_yaml, _resolve_daily_limits
from app.core.budget_manager import BudgetManager
from app.core.project_loader import load_runtime_project
from app.core.router import Router
from app.core.task_runner import TaskRequest, TaskRunner
from app.providers.config import load_provider_settings
from app.storage.state_store import StateStore


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 -m app.commands.map_dependencies <relative-path.py>")
        return 1

    relative_path = sys.argv[1]

    try:
        runtime_project = load_runtime_project(os.getenv("AI_DEFAULT_PROJECT", "ia-trade"))
    except FileNotFoundError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, ensure_ascii=False, indent=2))
        return 1

    routing_config = _load_yaml("config/routing.yaml").get("routing", {})
    budgets_config = _load_yaml("config/budgets.yaml")
    provider_settings = load_provider_settings()
    budget_manager = BudgetManager(_resolve_daily_limits(budgets_config), state_store=StateStore())
    runner = TaskRunner(
        router=Router(routing_config),
        budget_manager=budget_manager,
        provider_settings=provider_settings,
    )
    inspection = runner.inspect(
        TaskRequest(
            task_type="map-dependencies",
            payload={
                "project_id": runtime_project.project_id,
                "target_repo": runtime_project.target_repo,
                "write_enabled": runtime_project.write_enabled,
                "file": relative_path,
                "objective": "Map local and external dependencies for the selected file.",
            },
        )
    )
    mapping = inspection.get("dependency_map", {})
    if not isinstance(mapping, dict):
        mapping = {"status": "error", "reason": "dependency map unavailable"}
    if mapping.get("status") != "ok":
        print(json.dumps(mapping, ensure_ascii=False, indent=2))
        return 1

    result = {
        "status": "ok",
        "project_id": runtime_project.project_id,
        "target_repo": runtime_project.target_repo,
        **mapping,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
