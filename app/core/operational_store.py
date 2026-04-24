import json
from hashlib import sha256
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

        state_payload = {
            "task_type": task_type,
            "project_id": project_id,
            "selected_files": output.get("local_plan", {}).get("selected_files", []),
            "provider": output.get("provider_result", {}).get("provider"),
            "status": output.get("provider_result", {}).get("status"),
            "provider_attempts": output.get("provider_attempts", []),
        }
        cache_payload = {
            "task_type": task_type,
            "project_id": project_id,
            "payload": payload,
            "cache_context": cache_context or {},
            "result": {
                "provider": output.get("provider_result", {}).get("provider"),
                "status": output.get("provider_result", {}).get("status"),
                "output": output,
            },
            "summary": {
                "selected_files": output.get("local_plan", {}).get("selected_files", []),
                "provider": output.get("provider_result", {}).get("provider"),
                "status": output.get("provider_result", {}).get("status"),
                "provider_attempts": output.get("provider_attempts", []),
            },
        }

        self.state_store.save(state_key, state_payload)
        self.cache_store.set(cache_key, json.dumps(cache_payload, ensure_ascii=False, indent=2))
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


def _slug(value: str) -> str:
    return value.replace("-", "_").replace("/", "_")
