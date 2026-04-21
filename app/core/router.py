from dataclasses import dataclass
from typing import Dict, List


@dataclass
class RouteDecision:
    task_type: str
    provider: str
    fallbacks: List[str]


class Router:
    def __init__(self, routing_config: Dict[str, Dict[str, object]]):
        self.routing_config = routing_config

    def decide(self, task_type: str) -> RouteDecision:
        entry = self.routing_config.get(task_type, {})
        provider = str(entry.get("preferred", "gemini"))
        fallbacks = list(entry.get("fallback", []))
        return RouteDecision(task_type=task_type, provider=provider, fallbacks=fallbacks)
