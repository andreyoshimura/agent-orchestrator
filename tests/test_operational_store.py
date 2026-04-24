from concurrent.futures import ThreadPoolExecutor
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

    def test_persist_task_result_handles_degraded_output_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            store = OperationalStore(state_store=state_store, cache_store=cache_store)

            refs = store.persist_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
                output={
                    "provider_attempts": [{"provider": "claude", "attempt": 1, "status": "skipped", "failure_type": "provider_unavailable"}],
                },
            )

            state_payload = state_store.load(refs["state_key"])
            cache_payload = json.loads(cache_store.get(refs["cache_key"]))

            self.assertEqual(state_payload["provider"], None)
            self.assertEqual(state_payload["status"], None)
            self.assertEqual(state_payload["selected_files"], [])
            self.assertEqual(cache_payload["summary"]["provider"], None)
            self.assertEqual(cache_payload["summary"]["status"], None)
            self.assertEqual(cache_payload["summary"]["selected_files"], [])

    def test_persist_task_result_reuses_state_key_and_fingerprints_cache_by_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            store = OperationalStore(state_store=state_store, cache_store=cache_store)

            refs_a = store.persist_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
                output={"provider_result": {"provider": "gemini", "status": "stub"}},
            )
            refs_b = store.persist_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "risk"},
                output={"provider_result": {"provider": "claude", "status": "stub"}},
            )

            self.assertEqual(refs_a["state_key"], refs_b["state_key"])
            self.assertNotEqual(refs_a["cache_key"], refs_b["cache_key"])

    def test_cache_fingerprint_is_stable_for_payload_key_order(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            store = OperationalStore(state_store=state_store, cache_store=cache_store)

            refs_a = store.persist_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper", "objective": "x"},
                output={"provider_result": {"provider": "gemini", "status": "stub"}},
            )
            refs_b = store.persist_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"objective": "x", "query": "paper"},
                output={"provider_result": {"provider": "gemini", "status": "stub"}},
            )

            self.assertEqual(refs_a["cache_key"], refs_b["cache_key"])

    def test_cache_fingerprint_changes_when_cache_context_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            store = OperationalStore(state_store=state_store, cache_store=cache_store)

            key_a = store.cache_key(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
                cache_context={"signature": "abc"},
            )
            key_b = store.cache_key(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
                cache_context={"signature": "def"},
            )

            self.assertNotEqual(key_a, key_b)

    def test_load_cached_task_result_returns_persisted_output_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            store = OperationalStore(state_store=state_store, cache_store=cache_store)

            store.persist_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
                output={
                    "local_plan": {"selected_files": ["paper_trade.py"]},
                    "provider_result": {"provider": "gemini", "status": "stub", "output": {"mode": "stub"}},
                    "provider_attempts": [{"provider": "gemini", "attempt": 1, "status": "stub", "failure_type": "success"}],
                },
            )
            cached = store.load_cached_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
            )

            self.assertIsNotNone(cached)
            cached = cached or {}
            self.assertEqual(cached["provider"], "gemini")
            self.assertEqual(cached["status"], "stub")
            self.assertEqual(cached["output"]["provider_result"]["provider"], "gemini")

    def test_load_cached_task_result_returns_none_for_invalid_cached_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            store = OperationalStore(state_store=state_store, cache_store=cache_store)

            cache_key = store.cache_key(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
            )
            cache_store.set(cache_key, "not-json")

            cached = store.load_cached_task_result(
                task_type="review-file",
                project_id="ia-trade",
                payload={"query": "paper"},
            )
            self.assertIsNone(cached)

    def test_state_store_handles_light_concurrent_writes_without_invalid_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            key = "concurrent"
            state_store.save(key, {"value": -1, "text": "seed"})

            def writer(i: int) -> None:
                state_store.save(key, {"value": i, "text": "x" * 128})

            def reader() -> dict:
                return state_store.load(key)

            with ThreadPoolExecutor(max_workers=8) as executor:
                for i in range(120):
                    executor.submit(writer, i)
                    payload = executor.submit(reader).result()
                    self.assertIsInstance(payload, dict)
                    self.assertIn("value", payload)
                    self.assertIn("text", payload)

            final_payload = state_store.load(key)
            self.assertIsInstance(final_payload.get("value"), int)
            self.assertEqual(final_payload.get("text"), "x" * 128)

    def test_cache_store_handles_light_concurrent_writes_without_partial_reads(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            key = "concurrent-cache"
            cache_store.set(key, json.dumps({"value": -1, "kind": "seed"}))

            def writer(i: int) -> None:
                cache_store.set(key, json.dumps({"value": i, "kind": "cache"}))

            def reader() -> dict:
                raw = cache_store.get(key)
                self.assertIsNotNone(raw)
                return json.loads(raw or "{}")

            with ThreadPoolExecutor(max_workers=8) as executor:
                for i in range(120):
                    writer_future = executor.submit(writer, i)
                    writer_future.result()
                    payload = executor.submit(reader).result()
                    self.assertIn("value", payload)
                    self.assertEqual(payload.get("kind"), "cache")

            final_payload = json.loads(cache_store.get(key) or "{}")
            self.assertIsInstance(final_payload.get("value"), int)
            self.assertEqual(final_payload.get("kind"), "cache")


if __name__ == "__main__":
    unittest.main()
