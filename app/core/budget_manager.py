from dataclasses import dataclass
from typing import Dict


@dataclass
class BudgetStatus:
    provider: str
    spent: float
    limit: float

    @property
    def remaining(self) -> float:
        return max(self.limit - self.spent, 0.0)

    @property
    def available(self) -> bool:
        return self.remaining > 0


class BudgetManager:
    def __init__(self, daily_limits: Dict[str, float]):
        self.daily_limits = daily_limits
        self.spent: Dict[str, float] = {provider: 0.0 for provider in daily_limits}

    def status(self, provider: str) -> BudgetStatus:
        limit = float(self.daily_limits.get(provider, 0.0))
        spent = float(self.spent.get(provider, 0.0))
        return BudgetStatus(provider=provider, spent=spent, limit=limit)

    def can_use(self, provider: str, estimated_cost: float = 0.0) -> bool:
        status = self.status(provider)
        return status.remaining >= estimated_cost

    def record(self, provider: str, cost: float) -> None:
        self.spent[provider] = float(self.spent.get(provider, 0.0)) + float(cost)
