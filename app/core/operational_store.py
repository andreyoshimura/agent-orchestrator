import json
from hashlib import sha256
from typing import Any, Dict

from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore


class OperationalStore:
    def __init__(self, state_store: StateStore | None = None, cache_store: CacheStore | None = None):
        self.state_store = state_store or StateStore()
        self.cache_store = cache_store or CacheStore()

    def persist_task_result(self, task_type: str, project_id: str, payload: Dict[str, Any], output: Dict[str, Any]) -> Dict[str, str]:
        state_key = f"last_task_{project_id}_{_slug(task_type)}"
        cache_key = self._cache_key(task_type=task_type, project_id=project_id, payload=payload)

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

    def _cache_key(self, task_type: str, project_id: str, payload: Dict[str, Any]) -> str:
        fingerprint_payload = json.dumps(
            {"task_type": task_type, "project_id": project_id, "payload": payload},
            ensure_ascii=False,
            sort_keys=True,
        )
        return sha256(fingerprint_payload.encode("utf-8")).hexdigest()


def _slug(value: str) -> str:
    return value.replace("-", "_").replace("/", "_")
