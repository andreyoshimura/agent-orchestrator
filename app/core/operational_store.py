import json
from hashlib import sha256
from datetime import date
from typing import Any, Dict

from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore


class OperationalStore:
    def __init__(self, state_store: StateStore | None = None, cache_store: CacheStore | None = None):
        self.state_store = state_store or StateStore()
        self.cache_store = cache_store or CacheStore()

    def persist_task_result(
        self,
        task_type: str,
        project_id: str,
        payload: Dict[str, Any],
        output: Dict[str, Any],
        cache_context: Dict[str, Any] | None = None,
    ) -> Dict[str, str]:
        state_key = f"last_task_{project_id}_{_slug(task_type)}"
        cache_key = self.cache_key(
            task_type=task_type,
            project_id=project_id,
            payload=payload,
            cache_context=cache_context,
        )

        provider_result = output.get("provider_result", {})
        provider_usage = _extract_provider_usage(provider_result)
        state_payload = {
            "task_type": task_type,
            "project_id": project_id,
            "selected_files": output.get("local_plan", {}).get("selected_files", []),
            "provider": provider_result.get("provider"),
            "status": provider_result.get("status"),
            "provider_attempts": output.get("provider_attempts", []),
            "execution_metrics": output.get("execution_metrics", {}),
            "provider_usage": provider_usage,
        }
        cache_payload = {
            "task_type": task_type,
            "project_id": project_id,
            "payload": payload,
            "cache_context": cache_context or {},
            "result": {
                "provider": provider_result.get("provider"),
                "status": provider_result.get("status"),
                "output": output,
            },
            "summary": {
                "selected_files": output.get("local_plan", {}).get("selected_files", []),
                "provider": provider_result.get("provider"),
                "status": provider_result.get("status"),
                "provider_attempts": output.get("provider_attempts", []),
                "execution_metrics": output.get("execution_metrics", {}),
                "provider_usage": provider_usage,
            },
        }

        self.state_store.save(state_key, state_payload)
        self.cache_store.set(cache_key, json.dumps(cache_payload, ensure_ascii=False, indent=2))
        self._record_proactive_switch_telemetry(task_type=task_type, output=output)
        return {
            "state_key": state_key,
            "cache_key": cache_key,
        }

    def load_cached_task_result(
        self,
        task_type: str,
        project_id: str,
        payload: Dict[str, Any],
        cache_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any] | None:
        cache_key = self.cache_key(
            task_type=task_type,
            project_id=project_id,
            payload=payload,
            cache_context=cache_context,
        )
        raw = self.cache_store.get(cache_key)
        if not raw:
            return None
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        result = parsed.get("result", {})
        if not isinstance(result, dict):
            return None
        status = result.get("status")
        provider = result.get("provider")
        output = result.get("output")
        if not isinstance(status, str) or not isinstance(provider, str) or not isinstance(output, dict):
            return None
        return {
            "cache_key": cache_key,
            "provider": provider,
            "status": status,
            "output": output,
        }

    def proactive_switch_summary(self, current_date: str | None = None) -> Dict[str, Any]:
        telemetry = self._load_proactive_switch_telemetry(current_date=current_date)
        return {
            "date": telemetry.get("date", current_date or date.today().isoformat()),
            "total_switches": int(telemetry.get("total_switches", 0)),
            "by_task_type": telemetry.get("by_task_type", {}),
            "by_primary_provider": telemetry.get("by_primary_provider", {}),
            "by_fallback_provider": telemetry.get("by_fallback_provider", {}),
            "by_route": telemetry.get("by_route", {}),
            "last_event": telemetry.get("last_event"),
        }

    def cache_key(
        self,
        task_type: str,
        project_id: str,
        payload: Dict[str, Any],
        cache_context: Dict[str, Any] | None = None,
    ) -> str:
        return self._cache_key(
            task_type=task_type,
            project_id=project_id,
            payload=payload,
            cache_context=cache_context,
        )

    def _cache_key(
        self,
        task_type: str,
        project_id: str,
        payload: Dict[str, Any],
        cache_context: Dict[str, Any] | None = None,
    ) -> str:
        fingerprint_payload = json.dumps(
            {
                "task_type": task_type,
                "project_id": project_id,
                "payload": payload,
                "cache_context": cache_context or {},
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return sha256(fingerprint_payload.encode("utf-8")).hexdigest()

    def _record_proactive_switch_telemetry(self, task_type: str, output: Dict[str, Any]) -> None:
        selection_preview = output.get("selection_preview", {})
        if not isinstance(selection_preview, dict):
            return
        if selection_preview.get("decision") != "switch_now_due_to_budget":
            return

        primary_provider = str(selection_preview.get("primary_provider", "")).strip()
        selected_fallback = selection_preview.get("selected_fallback", {})
        fallback_provider = ""
        if isinstance(selected_fallback, dict):
            fallback_provider = str(selected_fallback.get("provider", "")).strip()
        if not primary_provider or not fallback_provider:
            return

        telemetry = self._load_proactive_switch_telemetry()
        telemetry["date"] = self._current_date()
        telemetry["total_switches"] = int(telemetry.get("total_switches", 0)) + 1
        telemetry["by_task_type"] = _increment_counter(telemetry.get("by_task_type", {}), task_type)
        telemetry["by_primary_provider"] = _increment_counter(telemetry.get("by_primary_provider", {}), primary_provider)
        telemetry["by_fallback_provider"] = _increment_counter(telemetry.get("by_fallback_provider", {}), fallback_provider)
        telemetry["by_route"] = _increment_counter(
            telemetry.get("by_route", {}),
            f"{primary_provider}->{fallback_provider}",
        )
        telemetry["last_event"] = {
            "task_type": task_type,
            "primary_provider": primary_provider,
            "fallback_provider": fallback_provider,
        }
        self.state_store.save(self._proactive_switch_key(), telemetry)

    def _load_proactive_switch_telemetry(self, current_date: str | None = None) -> Dict[str, Any]:
        key = self._proactive_switch_key(current_date=current_date)
        payload = self.state_store.load(key)
        return payload if isinstance(payload, dict) else {}

    def _proactive_switch_key(self, current_date: str | None = None) -> str:
        return f"proactive_switch_metrics_{current_date or self._current_date()}"

    def _current_date(self) -> str:
        return date.today().isoformat()


def _slug(value: str) -> str:
    return value.replace("-", "_").replace("/", "_")


def _extract_provider_usage(provider_result: Dict[str, Any]) -> Dict[str, int] | None:
    output = provider_result.get("output")
    if not isinstance(output, dict):
        return None
    usage = output.get("usage")
    if not isinstance(usage, dict):
        return None
    try:
        return {
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }
    except (TypeError, ValueError):
        return None


def _increment_counter(container: Any, key: str) -> Dict[str, int]:
    if not isinstance(container, dict):
        container = {}
    counts: Dict[str, int] = {}
    for existing_key, existing_value in container.items():
        if isinstance(existing_key, str):
            try:
                counts[existing_key] = int(existing_value)
            except (TypeError, ValueError):
                counts[existing_key] = 0
    counts[key] = counts.get(key, 0) + 1
    return counts
