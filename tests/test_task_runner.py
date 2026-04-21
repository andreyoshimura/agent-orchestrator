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
                self.assertEqual(inspection["local_plan"]["selected_files"], ["paper_trade.py"])
                self.assertEqual(inspection["context"]["status"], "ready")
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
                self.assertEqual(result.output["provider_result"]["provider"], "claude")
                self.assertEqual(result.output["provider_result"]["status"], "stub")
                self.assertGreater(result.output["provider_result"]["output"]["prompt_length"], 0)
                self.assertEqual(result.output["provider_attempts"][0]["provider"], "claude")
                self.assertEqual(result.output["provider_attempts"][0]["attempt"], 1)
                self.assertEqual(result.output["provider_attempts"][0]["status"], "stub")
                self.assertEqual(result.output["provider_attempts"][0]["failure_type"], "success")
                self.assertIn("persistence", result.output)
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


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
        return
    os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
