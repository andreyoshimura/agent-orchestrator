from dataclasses import dataclass
from typing import Dict, List

DEFAULT_PROVIDER_MAX_TOKENS = 2048


@dataclass
class RouteDecision:
    task_type: str
    provider: str
    fallbacks: List[str]
    max_provider_retries: int
    fallback_on: List[str]
    provider_timeout_sec: int
    budget_switch_threshold_ratio: float
    provider_max_tokens: int


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
        provider_timeout_sec = int(execution.get("provider_timeout_sec", 30))
        budget_switch_threshold_ratio = float(execution.get("budget_switch_threshold_ratio", 0.25))
        if budget_switch_threshold_ratio < 0:
            budget_switch_threshold_ratio = 0.0
        if budget_switch_threshold_ratio > 1:
            budget_switch_threshold_ratio = 1.0
        provider_max_tokens = self.resolve_max_tokens(task_type, provider)
        return RouteDecision(
            task_type=task_type,
            provider=provider,
            fallbacks=fallbacks,
            max_provider_retries=max_provider_retries,
            fallback_on=fallback_on,
            provider_timeout_sec=provider_timeout_sec,
            budget_switch_threshold_ratio=budget_switch_threshold_ratio,
            provider_max_tokens=provider_max_tokens,
        )

    def resolve_max_tokens(
        self,
        task_type: str,
        provider_name: str,
        profile_overrides: Dict[str, object] | None = None,
    ) -> int:
        """Resolve provider_max_tokens through a hierarchy of overrides.

        Precedence (most specific wins):
        1. profile.<task>.by_provider.<provider>
        2. profile.<task>.default
        3. profile.default
        4. routing.<task>.execution.provider_max_tokens_by_provider.<provider>
        5. routing.<task>.execution.provider_max_tokens
        6. routing._defaults.provider_max_tokens
        7. DEFAULT_PROVIDER_MAX_TOKENS (2048)
        """
        candidates: list[object] = []

        if isinstance(profile_overrides, dict):
            task_override = profile_overrides.get(task_type)
            if isinstance(task_override, dict):
                by_provider = task_override.get("by_provider")
                if isinstance(by_provider, dict):
                    candidates.append(by_provider.get(provider_name))
                candidates.append(task_override.get("default"))
            elif task_override is not None:
                candidates.append(task_override)
            candidates.append(profile_overrides.get("default"))

        entry = self.routing_config.get(task_type, {})
        execution = entry.get("execution", {}) if isinstance(entry, dict) else {}
        if isinstance(execution, dict):
            by_provider = execution.get("provider_max_tokens_by_provider")
            if isinstance(by_provider, dict):
                candidates.append(by_provider.get(provider_name))
            candidates.append(execution.get("provider_max_tokens"))

        defaults = self.routing_config.get("_defaults", {})
        if isinstance(defaults, dict):
            candidates.append(defaults.get("provider_max_tokens"))

        for candidate in candidates:
            value = _coerce_positive_int(candidate)
            if value is not None:
                return value
        return DEFAULT_PROVIDER_MAX_TOKENS


def _coerce_positive_int(raw_value: object) -> int | None:
    if raw_value is None:
        return None
    try:
        value = int(raw_value)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value
