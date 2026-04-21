import json

from app.cli.task_cli import _load_yaml, _resolve_daily_limits
from app.core.budget_manager import BudgetManager


def main() -> int:
    budgets_config = _load_yaml("config/budgets.yaml")
    daily_limits = _resolve_daily_limits(budgets_config)
    budget_manager = BudgetManager(daily_limits)

    print(json.dumps({
        "status": "ok",
        "budget": budget_manager.summary(),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
