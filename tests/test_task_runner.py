import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.operational_store import OperationalStore
from app.core.budget_manager import BudgetManager
from app.core.router import Router
from app.core.task_runner import TaskRequest, TaskRunner
from app.providers.config import ProviderSettings
from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore
from tests.test_helpers import create_test_project_profile


class TaskRunnerTest(unittest.TestCase):
    def test_inspect_returns_route_local_plan_and_provider_budget_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "claude", "fallback": ["gemini"], "execution": {"max_provider_retries": 1, "fallback_on": ["temporary", "rate_limit"]}}}),
                    budget_manager=BudgetManager({"claude": 2.0, "gemini": 0.0}),
                    provider_settings={
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                        "gemini": ProviderSettings(name="gemini", enabled=False, model="", api_key="", api_base=""),
                    },
                )

                inspection = runner.inspect(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(inspection["route"]["preferred"], "claude")
                self.assertEqual(inspection["route"]["fallbacks"], ["gemini"])
                self.assertEqual(inspection["route"]["provider_timeout_sec"], 30)
                self.assertEqual(inspection["local_plan"]["selected_files"], ["paper_trade.py"])
                self.assertEqual(inspection["context"]["status"], "ready")
                self.assertTrue(inspection["context_sufficiency"]["context_sufficient"])
                self.assertEqual(inspection["local_analysis"]["status"], "ready")
                self.assertEqual(inspection["local_analysis"]["local_agent_output"]["agent"], "micro_reviewer")
                self.assertEqual(inspection["pipeline"]["stages"][0]["stage"], "validate_payload")
                self.assertEqual(
                    inspection["providers"],
                    [
                        {
                            "provider": "claude",
                            "enabled": True,
                            "budget": {
                                "spent": 0.0,
                                "limit": 2.0,
                                "remaining": 2.0,
                                "available": True,
                            },
                            "usable_for_estimated_cost": True,
                        },
                        {
                            "provider": "gemini",
                            "enabled": False,
                            "budget": {
                                "spent": 0.0,
                                "limit": 0.0,
                                "remaining": 0.0,
                                "available": False,
                            },
                            "usable_for_estimated_cost": False,
                        },
                    ],
                )
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_run_returns_local_plan_with_selected_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir
                operational_store = OperationalStore(
                    state_store=StateStore(base_dir=f"{tmpdir}/state"),
                    cache_store=CacheStore(base_dir=f"{tmpdir}/cache"),
                )

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "claude", "fallback": [], "execution": {"max_provider_retries": 1, "fallback_on": ["temporary", "rate_limit", "network", "configuration", "provider_unavailable"]}}}),
                    budget_manager=BudgetManager({"claude": 1.0}),
                    provider_settings={
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                    operational_store=operational_store,
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.status, "stub")
                self.assertEqual(result.output["context"]["status"], "ready")
                self.assertEqual(result.output["local_plan"]["agent_name"], "micro_reviewer")
                self.assertEqual(result.output["local_plan"]["selected_files"], ["paper_trade.py"])
                self.assertIn("You are the micro_reviewer agent.", result.output["local_plan"]["prompt_template_preview"])
                self.assertIn("Review the selected files first", result.output["local_plan"]["recommended_action"])
                self.assertIn("paper_trade.py", result.output["local_plan"]["prompt_preview"])
                self.assertEqual(result.output["local_plan"]["local_agent_output"]["agent"], "micro_reviewer")
                self.assertEqual(result.output["local_plan"]["local_agent_output"]["payload"]["status"], "ready")
                self.assertEqual(result.output["local_analysis"]["status"], "ready")
                self.assertEqual(result.output["local_analysis"]["local_agent_output"]["agent"], "micro_reviewer")
                self.assertTrue(result.output["context_sufficiency"]["context_sufficient"])
                self.assertEqual(result.output["provider_result"]["provider"], "claude")
                self.assertEqual(result.output["provider_result"]["status"], "stub")
                self.assertEqual(result.output["synthesis"]["status"], "ready")
                self.assertEqual(result.output["synthesis"]["mode"], "run")
                self.assertEqual(result.output["synthesis"]["final_provider"], "claude")
                self.assertGreater(result.output["provider_result"]["output"]["prompt_length"], 0)
                self.assertEqual(
                    result.output["provider_result"]["output"]["metadata"]["local_agent_output"]["agent"],
                    "micro_reviewer",
                )
                self.assertEqual(
                    result.output["provider_result"]["output"]["metadata"]["provider_timeout_sec"],
                    30,
                )
                self.assertIn("execution_metrics", result.output)
                self.assertEqual(result.output["execution_metrics"]["cache_hit"], False)
                self.assertGreaterEqual(result.output["execution_metrics"]["planning_ms"], 0)
                self.assertGreaterEqual(result.output["execution_metrics"]["total_ms"], 0)
                self.assertIn("stage_metrics", result.output["execution_metrics"])
                self.assertIn("pipeline", result.output)
                self.assertEqual(result.output["pipeline"]["stages"][0]["stage"], "validate_payload")
                self.assertEqual(result.output["provider_attempts"][0]["provider"], "claude")
                self.assertEqual(result.output["provider_attempts"][0]["attempt"], 1)
                self.assertEqual(result.output["provider_attempts"][0]["status"], "stub")
                self.assertEqual(result.output["provider_attempts"][0]["failure_type"], "success")
                self.assertIn("persistence", result.output)
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_reuses_cached_result_when_enabled(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir
                operational_store = OperationalStore(
                    state_store=StateStore(base_dir=f"{tmpdir}/state"),
                    cache_store=CacheStore(base_dir=f"{tmpdir}/cache"),
                )

                mock_execute_provider.return_value = {"provider": "claude", "status": "stub", "output": {"mode": "stub"}}

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                    budget_manager=BudgetManager({"claude": 1.0}),
                    provider_settings={
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                    operational_store=operational_store,
                    allow_cache_reuse=True,
                )
                request = TaskRequest(
                    task_type="review-file",
                    payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                )
                first = runner.run(request)
                second = runner.run(request)

                self.assertEqual(first.status, "stub")
                self.assertEqual(second.status, "stub")
                self.assertEqual(mock_execute_provider.call_count, 1)
                self.assertEqual(second.output["cache"]["hit"], True)
                self.assertEqual(second.output["execution_metrics"]["cache_hit"], True)
                self.assertIn("provider_attempts", second.output)
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_invalidates_cached_result_when_selected_file_changes(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper-v1')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir
                operational_store = OperationalStore(
                    state_store=StateStore(base_dir=f"{tmpdir}/state"),
                    cache_store=CacheStore(base_dir=f"{tmpdir}/cache"),
                )

                mock_execute_provider.side_effect = [
                    {"provider": "claude", "status": "stub", "output": {"mode": "stub-v1"}},
                    {"provider": "claude", "status": "stub", "output": {"mode": "stub-v2"}},
                ]

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                    budget_manager=BudgetManager({"claude": 1.0}),
                    provider_settings={
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                    operational_store=operational_store,
                    allow_cache_reuse=True,
                )
                request = TaskRequest(
                    task_type="review-file",
                    payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                )

                first = runner.run(request)
                with open(sample_path, "w", encoding="utf-8") as handle:
                    handle.write("print('paper-v2')\n")
                second = runner.run(request)

                self.assertEqual(first.status, "stub")
                self.assertEqual(second.status, "stub")
                self.assertEqual(mock_execute_provider.call_count, 2)
                self.assertEqual(first.output["cache"]["hit"], False)
                self.assertEqual(second.output["cache"]["hit"], False)
                self.assertEqual(first.output["provider_result"]["output"]["mode"], "stub-v1")
                self.assertEqual(second.output["provider_result"]["output"]["mode"], "stub-v2")
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_inspect_marks_context_partial_when_target_repo_is_not_configured(self) -> None:
        old_project = os.environ.get("AI_DEFAULT_PROJECT")
        old_target = os.environ.get("AI_TARGET_REPO")
        try:
            os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
            os.environ.pop("AI_TARGET_REPO", None)

            runner = TaskRunner(
                router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                budget_manager=BudgetManager({"claude": 1.0}),
                provider_settings={
                    "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                },
            )
            inspection = runner.inspect(
                TaskRequest(
                    task_type="review-file",
                    payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                )
            )

            self.assertEqual(inspection["context"]["status"], "partial")
            self.assertEqual(inspection["context"]["reason"], "target repo not configured")
            self.assertEqual(inspection["local_plan"]["status"], "partial")
            self.assertEqual(inspection["local_plan"]["selected_files"], [])
        finally:
            _restore_env("AI_DEFAULT_PROJECT", old_project)
            _restore_env("AI_TARGET_REPO", old_target)

    def test_inspect_marks_context_partial_when_target_repo_path_is_missing(self) -> None:
        old_project = os.environ.get("AI_DEFAULT_PROJECT")
        old_target = os.environ.get("AI_TARGET_REPO")
        try:
            os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
            os.environ["AI_TARGET_REPO"] = "/tmp/path-that-should-not-exist-agent-orchestrator"

            runner = TaskRunner(
                router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                budget_manager=BudgetManager({"claude": 1.0}),
                provider_settings={
                    "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                },
            )
            inspection = runner.inspect(
                TaskRequest(
                    task_type="review-file",
                    payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                )
            )

            self.assertEqual(inspection["context"]["status"], "partial")
            self.assertIn("target repo path not found", inspection["context"]["reason"])
            self.assertEqual(inspection["local_plan"]["status"], "partial")
            self.assertEqual(inspection["local_plan"]["selected_files"], [])
        finally:
            _restore_env("AI_DEFAULT_PROJECT", old_project)
            _restore_env("AI_TARGET_REPO", old_target)

    def test_inspect_returns_unavailable_when_project_profile_is_missing(self) -> None:
        old_project = os.environ.get("AI_DEFAULT_PROJECT")
        try:
            os.environ["AI_DEFAULT_PROJECT"] = "missing-project"

            runner = TaskRunner(
                router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                budget_manager=BudgetManager({"claude": 1.0}),
                provider_settings={
                    "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                },
            )
            inspection = runner.inspect(
                TaskRequest(
                    task_type="review-file",
                    payload={"project_id": "missing-project", "query": "paper"},
                )
            )

            self.assertEqual(inspection["context"]["status"], "unavailable")
            self.assertEqual(inspection["context"]["reason"], "project profile not found")
            self.assertFalse(inspection["context_sufficiency"]["context_sufficient"])
            self.assertEqual(inspection["local_plan"]["status"], "unavailable")
            self.assertEqual(inspection["local_analysis"]["status"], "unavailable")
            self.assertEqual(inspection["synthesis"]["status"], "preview")
            self.assertEqual(inspection["providers"][0]["provider"], "claude")
        finally:
            _restore_env("AI_DEFAULT_PROJECT", old_project)

    def test_inspect_returns_structured_output_for_invalid_payload(self) -> None:
        runner = TaskRunner(
            router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
            budget_manager=BudgetManager({"claude": 1.0}),
            provider_settings={
                "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
            },
        )
        inspection = runner.inspect(
            TaskRequest(
                task_type="review-file",
                payload="invalid",  # type: ignore[arg-type]
            )
        )

        self.assertEqual(inspection["context"]["status"], "unavailable")
        self.assertEqual(inspection["context"]["reason"], "payload must be an object")
        self.assertFalse(inspection["context_sufficiency"]["context_sufficient"])
        self.assertEqual(inspection["synthesis"]["status"], "unavailable")
        self.assertEqual(inspection["pipeline"]["stages"][0]["status"], "error")

    def test_run_uses_alternate_project_root_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root = Path(tmpdir) / "profiles"
            create_test_project_profile(projects_root, "demo")

            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()
            (repo_root / "engine.py").write_text("print('engine')\n", encoding="utf-8")

            old_projects_root = os.environ.get("AI_PROJECTS_ROOT")
            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO_ALT")
            try:
                os.environ["AI_PROJECTS_ROOT"] = str(projects_root)
                os.environ["AI_DEFAULT_PROJECT"] = "demo"
                os.environ["AI_TARGET_REPO_ALT"] = str(repo_root)

                operational_store = OperationalStore(
                    state_store=StateStore(base_dir=f"{tmpdir}/state"),
                    cache_store=CacheStore(base_dir=f"{tmpdir}/cache"),
                )
                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                    budget_manager=BudgetManager({"claude": 1.0}),
                    provider_settings={
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                    operational_store=operational_store,
                )

                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "demo", "query": "engine", "objective": "Revisar engine runtime"},
                    )
                )

                self.assertEqual(result.status, "stub")
                self.assertEqual(result.output["local_plan"]["selected_files"], ["engine.py"])
                self.assertEqual(result.output["context"]["status"], "ready")
                self.assertEqual(result.output["local_plan"]["prompt_name"], "micro_reviewer")
                self.assertEqual(
                    result.output["provider_result"]["output"]["metadata"]["provider_timeout_sec"],
                    30,
                )
            finally:
                _restore_env("AI_PROJECTS_ROOT", old_projects_root)
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO_ALT", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_falls_back_when_preferred_provider_errors(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                mock_execute_provider.side_effect = [
                    {"provider": "gemini", "status": "error", "output": {"reason": "network", "failure_type": "network"}},
                    {"provider": "gemini", "status": "error", "output": {"reason": "network", "failure_type": "network"}},
                    {"provider": "claude", "status": "stub", "output": {"mode": "stub"}},
                ]

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "gemini", "fallback": ["claude"], "execution": {"max_provider_retries": 1, "fallback_on": ["temporary", "rate_limit", "network", "configuration", "provider_unavailable"]}}}),
                    budget_manager=BudgetManager({"gemini": 1.0, "claude": 1.0}),
                    provider_settings={
                        "gemini": ProviderSettings(name="gemini", enabled=True, model="", api_key="", api_base=""),
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.provider, "claude")
                self.assertEqual(result.status, "stub")
                self.assertEqual(
                    result.output["provider_attempts"],
                    [
                        {"provider": "gemini", "attempt": 1, "status": "error", "failure_type": "network"},
                        {"provider": "gemini", "attempt": 2, "status": "error", "failure_type": "network"},
                        {"provider": "claude", "attempt": 1, "status": "stub", "failure_type": "success"},
                    ],
                )
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_skips_disabled_provider_and_uses_fallback(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                mock_execute_provider.return_value = {"provider": "claude", "status": "stub", "output": {"mode": "stub"}}

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "gemini", "fallback": ["claude"], "execution": {"max_provider_retries": 1, "fallback_on": ["temporary", "rate_limit", "network", "configuration", "provider_unavailable"]}}}),
                    budget_manager=BudgetManager({"gemini": 1.0, "claude": 1.0}),
                    provider_settings={
                        "gemini": ProviderSettings(name="gemini", enabled=False, model="", api_key="", api_base=""),
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.provider, "claude")
                self.assertEqual(result.output["provider_attempts"][0]["provider"], "gemini")
                self.assertEqual(result.output["provider_attempts"][0]["attempt"], 0)
                self.assertEqual(result.output["provider_attempts"][0]["status"], "skipped")
                self.assertEqual(result.output["provider_attempts"][0]["reason"], "provider unavailable within current settings or budget")
                self.assertEqual(result.output["provider_attempts"][1]["provider"], "claude")
                self.assertEqual(result.output["provider_attempts"][1]["attempt"], 1)
                self.assertEqual(result.output["provider_attempts"][1]["failure_type"], "success")
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_stops_on_terminal_failure_without_fallback(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                mock_execute_provider.return_value = {
                    "provider": "gemini",
                    "status": "error",
                    "output": {"reason": "http_error:400", "failure_type": "invalid_request"},
                }

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "gemini", "fallback": ["claude"], "execution": {"max_provider_retries": 1, "fallback_on": ["temporary", "rate_limit", "network", "configuration", "provider_unavailable"]}}}),
                    budget_manager=BudgetManager({"gemini": 1.0, "claude": 1.0}),
                    provider_settings={
                        "gemini": ProviderSettings(name="gemini", enabled=True, model="", api_key="", api_base=""),
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.provider, "gemini")
                self.assertEqual(result.status, "degraded")
                self.assertEqual(result.output["synthesis"]["status"], "degraded")
                self.assertEqual(result.output["synthesis"]["final_provider"], "gemini")
                self.assertEqual(
                    result.output["provider_attempts"],
                    [{"provider": "gemini", "attempt": 1, "status": "error", "failure_type": "invalid_request"}],
                )
                self.assertEqual(result.output["provider_result"]["provider"], "gemini")
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_retries_temporary_failure_before_succeeding(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                mock_execute_provider.side_effect = [
                    {"provider": "gemini", "status": "error", "output": {"reason": "network_error:timeout", "failure_type": "network"}},
                    {"provider": "gemini", "status": "stub", "output": {"mode": "stub"}},
                ]

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "gemini", "fallback": ["claude"], "execution": {"max_provider_retries": 1, "fallback_on": ["temporary", "rate_limit", "network", "configuration", "provider_unavailable"]}}}),
                    budget_manager=BudgetManager({"gemini": 1.0, "claude": 1.0}),
                    provider_settings={
                        "gemini": ProviderSettings(name="gemini", enabled=True, model="", api_key="", api_base=""),
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.provider, "gemini")
                self.assertEqual(result.status, "stub")
                self.assertEqual(
                    result.output["provider_attempts"],
                    [
                        {"provider": "gemini", "attempt": 1, "status": "error", "failure_type": "network"},
                        {"provider": "gemini", "attempt": 2, "status": "stub", "failure_type": "success"},
                    ],
                )
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_does_not_fallback_when_failure_type_is_not_allowed(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                mock_execute_provider.side_effect = [
                    {"provider": "gemini", "status": "error", "output": {"reason": "network_error:timeout", "failure_type": "network"}},
                    {"provider": "gemini", "status": "error", "output": {"reason": "network_error:timeout", "failure_type": "network"}},
                ]

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "gemini", "fallback": ["claude"], "execution": {"max_provider_retries": 1, "fallback_on": ["configuration"]}}}),
                    budget_manager=BudgetManager({"gemini": 1.0, "claude": 1.0}),
                    provider_settings={
                        "gemini": ProviderSettings(name="gemini", enabled=True, model="", api_key="", api_base=""),
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.provider, "gemini")
                self.assertEqual(result.status, "degraded")
                self.assertEqual(len(result.output["provider_attempts"]), 2)
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    @patch.object(TaskRunner, "_execute_provider")
    def test_run_falls_back_on_temporary_invalid_response_shape(self, mock_execute_provider) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                mock_execute_provider.side_effect = [
                    {
                        "provider": "gemini",
                        "status": "error",
                        "output": {
                            "reason": "invalid_response_shape:missing_candidates",
                            "failure_type": "temporary",
                        },
                    },
                    {"provider": "claude", "status": "stub", "output": {"mode": "stub"}},
                ]

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "gemini", "fallback": ["claude"], "execution": {"max_provider_retries": 0, "fallback_on": ["temporary"]}}}),
                    budget_manager=BudgetManager({"gemini": 1.0, "claude": 1.0}),
                    provider_settings={
                        "gemini": ProviderSettings(name="gemini", enabled=True, model="", api_key="", api_base=""),
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.provider, "claude")
                self.assertEqual(result.status, "stub")
                self.assertEqual(result.output["provider_attempts"][0]["failure_type"], "temporary")
                self.assertEqual(result.output["provider_attempts"][1]["provider"], "claude")
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_run_degrades_when_provider_settings_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "openai", "fallback": []}}),
                    budget_manager=BudgetManager({"openai": 1.0}),
                    provider_settings={},
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    ),
                    estimated_cost=0.2,
                )

                self.assertEqual(result.provider, "openai")
                self.assertEqual(result.status, "degraded")
                self.assertEqual(
                    result.output["provider_attempts"],
                    [{"provider": "openai", "attempt": 1, "status": "error", "failure_type": "configuration"}],
                )
                self.assertEqual(result.output["provider_result"]["output"]["failure_type"], "configuration")
                self.assertEqual(runner.budget_manager.status("openai").spent, 0.0)
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_run_falls_back_when_provider_name_is_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "missing-provider", "fallback": ["claude"], "execution": {"max_provider_retries": 0, "fallback_on": ["provider_unavailable"]}}}),
                    budget_manager=BudgetManager({"missing-provider": 1.0, "claude": 1.0}),
                    provider_settings={
                        "missing-provider": ProviderSettings(name="missing-provider", enabled=True, model="", api_key="", api_base=""),
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "paper", "objective": "Revisar entrypoint paper"},
                    )
                )

                self.assertEqual(result.provider, "claude")
                self.assertEqual(result.status, "stub")
                self.assertEqual(result.output["provider_attempts"][0]["provider"], "missing-provider")
                self.assertEqual(result.output["provider_attempts"][0]["failure_type"], "provider_unavailable")
                self.assertEqual(result.output["provider_attempts"][1]["provider"], "claude")
                self.assertEqual(result.output["provider_attempts"][1]["failure_type"], "success")
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_run_degrades_when_project_profile_is_missing(self) -> None:
        old_project = os.environ.get("AI_DEFAULT_PROJECT")
        try:
            os.environ["AI_DEFAULT_PROJECT"] = "missing-project"

            budget_manager = BudgetManager({"claude": 1.0})
            runner = TaskRunner(
                router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                budget_manager=budget_manager,
                provider_settings={
                    "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                },
            )
            result = runner.run(
                TaskRequest(
                    task_type="review-file",
                    payload={"project_id": "missing-project", "query": "paper"},
                ),
                estimated_cost=0.2,
            )

            self.assertEqual(result.status, "degraded")
            self.assertEqual(result.output["context"]["status"], "unavailable")
            self.assertEqual(result.output["local_plan"]["status"], "unavailable")
            self.assertFalse(result.output["context_sufficiency"]["context_sufficient"])
            self.assertEqual(result.output["local_analysis"]["status"], "unavailable")
            self.assertEqual(
                result.output["provider_attempts"],
                [{"provider": "claude", "attempt": 1, "status": "skipped", "failure_type": "provider_unavailable"}],
            )
            self.assertEqual(budget_manager.status("claude").spent, 0.0)
        finally:
            _restore_env("AI_DEFAULT_PROJECT", old_project)

    def test_run_marks_context_partial_when_no_target_files_are_selected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "unrelated.py").write_text("print('x')\n", encoding="utf-8")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                runner = TaskRunner(
                    router=Router({"review-file": {"preferred": "claude", "fallback": []}}),
                    budget_manager=BudgetManager({"claude": 1.0}),
                    provider_settings={
                        "claude": ProviderSettings(name="claude", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                result = runner.run(
                    TaskRequest(
                        task_type="review-file",
                        payload={"project_id": "ia-trade", "query": "nonexistent-query-token"},
                    )
                )

                self.assertEqual(result.status, "stub")
                self.assertEqual(result.output["context"]["status"], "partial")
                self.assertEqual(result.output["context"]["reason"], "no target files selected")
                self.assertFalse(result.output["context_sufficiency"]["context_sufficient"])
                self.assertIn("no_target_files_selected", result.output["context_sufficiency"]["missing_context_risks"])
                self.assertEqual(result.output["local_plan"]["selected_files"], [])
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_inspect_includes_dependency_map_for_map_dependencies_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "paper_trade.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("import os\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                runner = TaskRunner(
                    router=Router({"map-dependencies": {"preferred": "gemini", "fallback": []}}),
                    budget_manager=BudgetManager({"gemini": 1.0}),
                    provider_settings={
                        "gemini": ProviderSettings(name="gemini", enabled=True, model="", api_key="", api_base=""),
                    },
                )
                inspection = runner.inspect(
                    TaskRequest(
                        task_type="map-dependencies",
                        payload={"project_id": "ia-trade", "file": "paper_trade.py", "objective": "Mapear dependências"},
                    )
                )

                self.assertEqual(inspection["dependency_map"]["status"], "ok")
                self.assertEqual(inspection["dependency_map"]["file"], "paper_trade.py")
                self.assertEqual(inspection["dependency_highlights"]["status"], "ready")
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
        return
    os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
