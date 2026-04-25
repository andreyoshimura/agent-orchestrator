from datetime import date
from dataclasses import dataclass
from typing import Dict

from app.storage.state_store import StateStore


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

    @property
    def remaining_ratio(self) -> float:
        if self.limit <= 0:
            return 0.0
        return max(min(self.remaining / self.limit, 1.0), 0.0)


class BudgetManager:
    def __init__(
        self,
        daily_limits: Dict[str, float],
        state_store: StateStore | None = None,
        current_date: str | None = None,
    ):
        self.daily_limits = daily_limits
        self.state_store = state_store or StateStore()
        self.current_date = current_date or date.today().isoformat()
        self.state_key = f"daily_budget_{self.current_date}"
        self.spent: Dict[str, float] = {provider: 0.0 for provider in daily_limits}
        self._load()

    def status(self, provider: str) -> BudgetStatus:
        limit = float(self.daily_limits.get(provider, 0.0))
        spent = float(self.spent.get(provider, 0.0))
        return BudgetStatus(provider=provider, spent=spent, limit=limit)

    def can_use(self, provider: str, estimated_cost: float = 0.0) -> bool:
        status = self.status(provider)
        return status.remaining >= estimated_cost

    def record(self, provider: str, cost: float) -> None:
        self.spent[provider] = float(self.spent.get(provider, 0.0)) + float(cost)
        self._persist()

    def summary(self) -> Dict[str, object]:
        return {
            "date": self.current_date,
            "providers": {
                provider: {
                    "spent": self.status(provider).spent,
                    "limit": self.status(provider).limit,
                    "remaining": self.status(provider).remaining,
                    "available": self.status(provider).available,
                    "remaining_ratio": self.status(provider).remaining_ratio,
                }
                for provider in sorted(self.daily_limits)
            },
        }

    def _load(self) -> None:
        persisted = self.state_store.load(self.state_key)
        providers = persisted.get("providers", {})
        if not isinstance(providers, dict):
            return
        for provider in self.daily_limits:
            self.spent[provider] = float(providers.get(provider, 0.0))

    def _persist(self) -> None:
        self.state_store.save(
            self.state_key,
            {
                "date": self.current_date,
                "providers": {
                    provider: float(self.spent.get(provider, 0.0))
                    for provider in sorted(self.daily_limits)
                },
            },
        )
