from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RouteDecision:
    task_type: str
    provider: str
    fallbacks: List[str]
    max_provider_retries: int
    fallback_on: List[str]


class Router:
    def __init__(self, routing_config: Dict[str, Dict[str, object]]):
        self.routing_config = routing_config

    def decide(self, task_type: str) -> RouteDecision:
        entry = self.routing_config.get(task_type, {})
        provider = str(entry.get("preferred", "gemini"))
        fallbacks = list(entry.get("fallback", []))
        execution = entry.get("execution", {})
        if not isinstance(execution, dict):
            execution = {}
        max_provider_retries = int(execution.get("max_provider_retries", 1))
        fallback_on = list(execution.get("fallback_on", ["temporary", "rate_limit", "network", "configuration", "provider_unavailable"]))
        return RouteDecision(
            task_type=task_type,
            provider=provider,
            fallbacks=fallbacks,
            max_provider_retries=max_provider_retries,
            fallback_on=fallback_on,
        )
