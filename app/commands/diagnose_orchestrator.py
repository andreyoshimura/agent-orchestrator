import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

from app.cli.task_cli import _load_yaml, _resolve_daily_limits
from app.core.budget_manager import BudgetManager
from app.core.operational_store import OperationalStore
from app.core.project_loader import load_runtime_project
from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore


def _safe_load_state(state_store: StateStore, key: str) -> dict:
    payload = state_store.load(key)
    if isinstance(payload, dict):
        return payload
    return {}


def _recent_task_states(state_store: StateStore, limit: int = 5) -> list[dict]:
    keys = state_store.list_keys(prefix="last_task_")
    recent = []
    for key in sorted(keys, reverse=True)[:limit]:
        payload = _safe_load_state(state_store, key)
        metrics = payload.get("execution_metrics", {})
        if not isinstance(metrics, dict):
            metrics = {}
        recent.append({
            "key": key,
            "task_type": payload.get("task_type"),
            "project_id": payload.get("project_id"),
            "provider": payload.get("provider"),
            "status": payload.get("status"),
            "selected_files": payload.get("selected_files", []),
            "execution_metrics": {
                "cache_hit": metrics.get("cache_hit"),
                "planning_ms": metrics.get("planning_ms"),
                "provider_execution_ms": metrics.get("provider_execution_ms"),
                "total_ms": metrics.get("total_ms"),
            },
        })
    return recent


def _recent_task_status_summary(state_store: StateStore, limit: int = 25) -> dict[str, Any]:
    counts: dict[str, int] = {}
    keys = state_store.list_keys(prefix="last_task_")
    for key in sorted(keys, reverse=True)[:limit]:
        payload = _safe_load_state(state_store, key)
        status = payload.get("status")
        normalized = status if isinstance(status, str) and status else "unknown"
        counts[normalized] = counts.get(normalized, 0) + 1
    return {
        "sampled_state_count": min(len(keys), limit),
        "statuses": dict(sorted(counts.items())),
    }


def _proactive_switch_telemetry(state_store: StateStore) -> dict[str, Any]:
    key = f"proactive_switch_metrics_{date.today().isoformat()}"
    payload = state_store.load(key)
    if not isinstance(payload, dict):
        payload = {}
    return {
        "date": payload.get("date", date.today().isoformat()),
        "total_switches": int(payload.get("total_switches", 0)),
        "by_task_type": payload.get("by_task_type", {}),
        "by_primary_provider": payload.get("by_primary_provider", {}),
        "by_fallback_provider": payload.get("by_fallback_provider", {}),
        "by_route": payload.get("by_route", {}),
        "last_event": payload.get("last_event"),
    }


def _budget_alert_threshold_ratio() -> float:
    default = 0.1
    raw = os.getenv("AI_BUDGET_ALERT_THRESHOLD_RATIO")
    if raw is None or raw.strip() == "":
        return default
    try:
        parsed = float(raw)
    except ValueError:
        return default
    return min(max(parsed, 0.0), 1.0)


def _budget_alerts(budget_summary: dict[str, Any], threshold_ratio: float) -> list[dict[str, Any]]:
    providers = budget_summary.get("providers", {})
    if not isinstance(providers, dict):
        return []
    alerts: list[dict[str, Any]] = []
    for provider, details in sorted(providers.items()):
        if not isinstance(details, dict):
            continue
        limit = details.get("limit")
        remaining = details.get("remaining")
        if not isinstance(limit, (int, float)) or not isinstance(remaining, (int, float)) or limit <= 0:
            continue
        remaining_ratio = float(remaining) / float(limit)
        if remaining_ratio > threshold_ratio:
            continue
        alerts.append({
            "provider": provider,
            "severity": "exhausted" if remaining <= 0 else "low_remaining",
            "remaining": float(remaining),
            "limit": float(limit),
            "remaining_ratio": remaining_ratio,
        })
    return alerts


def _daily_token_alert_threshold() -> int:
    default = 0
    raw = os.getenv("AI_DAILY_TOKEN_ALERT_THRESHOLD")
    if raw is None or raw.strip() == "":
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(parsed, 0)


def _proactive_switch_alert_threshold() -> int:
    default = 20
    raw = os.getenv("AI_PROACTIVE_SWITCH_ALERT_THRESHOLD")
    if raw is None or raw.strip() == "":
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return max(parsed, 1)


def _build_health_summary(
    project_status: dict[str, Any],
    storage_health: dict[str, Any],
    budget_alerts: list[dict[str, Any]],
    proactive_switch_total: int = 0,
    proactive_switch_threshold: int = 20,
    daily_token_total: int = 0,
    daily_token_threshold: int = 0,
) -> dict[str, Any]:
    signals: list[str] = []
    if project_status.get("status") != "ok":
        signals.append("project_profile_error")
    if not bool(storage_health.get("cache_index_consistent", True)):
        signals.append("cache_index_inconsistent")
    exhausted_alerts = sum(1 for item in budget_alerts if item.get("severity") == "exhausted")
    if exhausted_alerts > 0:
        signals.append("budget_exhausted")
    low_budget_alerts = sum(1 for item in budget_alerts if item.get("severity") == "low_remaining")
    if low_budget_alerts > 0:
        signals.append("budget_low_remaining")
    if proactive_switch_total >= proactive_switch_threshold:
        signals.append("proactive_switches_high")
    if daily_token_threshold > 0 and daily_token_total >= daily_token_threshold:
        signals.append("daily_tokens_high")
    return {
        "status": "degraded" if signals else "ok",
        "signals": signals,
        "budget_alert_count": len(budget_alerts),
        "budget_exhausted_count": exhausted_alerts,
        "budget_low_remaining_count": low_budget_alerts,
        "proactive_switch_count": proactive_switch_total,
        "daily_token_total": daily_token_total,
        "daily_token_threshold": daily_token_threshold,
    }


def _parse_args(args: list[str]) -> tuple[bool, bool, bool]:
    health_only = "--health-only" in args
    fail_on_degraded = "--fail-on-degraded" in args
    compact = "--compact" in args
    return health_only, fail_on_degraded, compact


def _print_payload(payload: dict[str, Any], compact: bool) -> None:
    if compact:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    health_only, fail_on_degraded, compact = _parse_args(sys.argv[1:])
    state_store = StateStore()
    cache_store = CacheStore()
    budgets_config = _load_yaml("config/budgets.yaml")
    daily_limits = _resolve_daily_limits(budgets_config)
    budget_manager = BudgetManager(daily_limits, state_store=state_store)

    default_project = os.getenv("AI_DEFAULT_PROJECT", "ia-trade")
    try:
        runtime_project = load_runtime_project(default_project)
        project_status = {
            "status": "ok",
            "project_id": runtime_project.project_id,
            "target_repo": runtime_project.target_repo,
            "target_repo_exists": Path(runtime_project.target_repo).exists() if runtime_project.target_repo else False,
            "write_enabled": runtime_project.write_enabled,
        }
    except FileNotFoundError as exc:
        project_status = {
            "status": "error",
            "reason": str(exc),
        }

    indexed_cache_entries = cache_store.list_entries(limit=1000)
    inspect_cache_entries = cache_store.list_entries(prefix="inspect:", limit=1000)
    indexed_with_file_count = sum(
        1
        for entry in indexed_cache_entries
        if (cache_store.base_dir / f"{entry.get('digest', '')}.txt").exists()
    )
    cache_entry_count = cache_store.count()
    storage_health = {
        "cache_index_missing_file_count": max(len(indexed_cache_entries) - indexed_with_file_count, 0),
        "cache_unindexed_file_estimate": max(cache_entry_count - indexed_with_file_count, 0),
        "cache_index_consistent": (
            len(indexed_cache_entries) == cache_entry_count and indexed_with_file_count == cache_entry_count
        ),
    }

    op_store = OperationalStore(state_store=state_store, cache_store=cache_store)
    budget_summary = budget_manager.summary()
    alert_threshold_ratio = _budget_alert_threshold_ratio()
    budget_summary["alert_threshold_ratio"] = alert_threshold_ratio
    budget_summary["alerts"] = _budget_alerts(budget_summary, threshold_ratio=alert_threshold_ratio)
    switch_telemetry = _proactive_switch_telemetry(state_store)
    switch_threshold = _proactive_switch_alert_threshold()
    usage_telemetry = op_store.provider_usage_summary()
    daily_token_total = int(usage_telemetry.get("total_tokens", 0))
    daily_token_threshold = _daily_token_alert_threshold()
    health_summary = _build_health_summary(
        project_status,
        storage_health,
        budget_summary["alerts"],
        proactive_switch_total=int(switch_telemetry.get("total_switches", 0)),
        proactive_switch_threshold=switch_threshold,
        daily_token_total=daily_token_total,
        daily_token_threshold=daily_token_threshold,
    )

    if health_only:
        _print_payload({
            "status": "ok",
            "mode": "health-only",
            "health_summary": health_summary,
            "project": {
                "status": project_status.get("status"),
                "project_id": project_status.get("project_id"),
            },
            "checks": {
                "cache_index_consistent": storage_health["cache_index_consistent"],
                "budget_alert_count": len(budget_summary["alerts"]),
                "proactive_switch_count": int(switch_telemetry.get("total_switches", 0)),
                "proactive_switch_threshold": switch_threshold,
                "daily_token_total": daily_token_total,
                "daily_token_threshold": daily_token_threshold,
            },
        }, compact=compact)
        if fail_on_degraded and health_summary.get("status") == "degraded":
            return 2
        return 0

    result = {
        "status": "ok",
        "health_summary": health_summary,
        "project": project_status,
        "budget": budget_summary,
        "storage": {
            "state_dir": str(state_store.base_dir),
            "state_key_count": len(state_store.list_keys()),
            "cache_dir": str(cache_store.base_dir),
            "cache_entry_count": cache_entry_count,
            "cache_indexed_entry_count": len(indexed_cache_entries),
            "cache_inspect_entry_count": len(inspect_cache_entries),
            "recent_inspect_cache_keys": [
                item.get("key")
                for item in inspect_cache_entries[:5]
            ],
            "recent_task_status_summary": _recent_task_status_summary(state_store),
            "proactive_switch_telemetry": switch_telemetry,
            "proactive_switch_threshold": switch_threshold,
            "provider_usage_telemetry": usage_telemetry,
            "storage_health": storage_health,
            "recent_task_states": _recent_task_states(state_store),
        },
        "config": {
            "routing_exists": Path("config/routing.yaml").exists(),
            "budgets_exists": Path("config/budgets.yaml").exists(),
        },
    }
    _print_payload(result, compact=compact)
    if fail_on_degraded and health_summary.get("status") == "degraded":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
