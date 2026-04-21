from dataclasses import dataclass
from typing import Dict, Optional

from app.core.router import Router
from app.core.budget_manager import BudgetManager


@dataclass
class TaskRequest:
    task_type: str
    payload: Dict[str, object]


@dataclass
class TaskResult:
    provider: str
    task_type: str
    status: str
    output: Dict[str, object]


class TaskRunner:
    def __init__(self, router: Router, budget_manager: BudgetManager):
        self.router = router
        self.budget_manager = budget_manager

    def run(self, request: TaskRequest, estimated_cost: float = 0.0) -> TaskResult:
        decision = self.router.decide(request.task_type)
        chosen_provider: Optional[str] = None

        if self.budget_manager.can_use(decision.provider, estimated_cost):
            chosen_provider = decision.provider
        else:
            for fallback in decision.fallbacks:
                if self.budget_manager.can_use(fallback, estimated_cost):
                    chosen_provider = fallback
                    break

        if not chosen_provider:
            return TaskResult(
                provider="none",
                task_type=request.task_type,
                status="degraded",
                output={"reason": "no provider available within budget"},
            )

        self.budget_manager.record(chosen_provider, estimated_cost)
        return TaskResult(
            provider=chosen_provider,
            task_type=request.task_type,
            status="planned",
            output={"payload": request.payload},
        )
