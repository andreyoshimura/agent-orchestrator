import json
import tempfile
import unittest

from app.core.operational_store import OperationalStore
from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore


class OperationalStoreTest(unittest.TestCase):
    def test_state_store_load_returns_empty_dict_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            state_store.path_for("broken").write_text("", encoding="utf-8")

            self.assertEqual(state_store.load("broken"), {})

    def test_persist_task_result_writes_state_and_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            store = OperationalStore(state_store=state_store, cache_store=cache_store)

            refs = store.persist_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
                output={
                    "local_plan": {"selected_files": ["paper_trade.py"]},
                    "provider_result": {"provider": "gemini", "status": "stub"},
                    "provider_attempts": [{"provider": "gemini", "attempt": 1, "status": "stub", "failure_type": "success"}],
                },
            )

            state_payload = state_store.load(refs["state_key"])
            cache_payload = json.loads(cache_store.get(refs["cache_key"]))

            self.assertEqual(state_payload["task_type"], "review-file")
            self.assertEqual(state_payload["selected_files"], ["paper_trade.py"])
            self.assertEqual(cache_payload["summary"]["provider"], "gemini")


if __name__ == "__main__":
    unittest.main()
