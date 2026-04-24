import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.cli import task_cli
from app.commands import assemble_context, diagnose_orchestrator, inspect_project, inspect_task, map_dependencies
from app.core.operational_store import OperationalStore
from app.core.task_runner import TaskRunner
from app.storage.cache_store import CacheStore
from app.storage.state_store import StateStore
from tests.test_helpers import create_test_project_profile


class CommandEntrypointsTest(unittest.TestCase):
    def test_inspect_project_supports_alternate_profile_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
                "AI_REPO_WRITE_ENABLED_ALT": "true",
            }):
                payload = _run_command(
                    inspect_project.main,
                    ["inspect_project.py", "demo"],
                )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["project_id"], "demo")
            self.assertEqual(payload["repo_path_env"], "AI_TARGET_REPO_ALT")
            self.assertTrue(payload["write_enabled"])
            self.assertEqual(payload["target_repo"]["path"], str(repo_root.resolve()))
            self.assertTrue(payload["target_repo"]["exists"])
            self.assertIn("engine.py", payload["target_repo"]["top_level_entries"])

    def test_inspect_task_supports_alternate_profile_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
            }):
                payload = _run_command(
                    inspect_task.main,
                    [
                        "inspect_task.py",
                        "review-file",
                        json.dumps({"query": "engine", "objective": "Revisar engine runtime"}),
                    ],
                )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["project_id"], "demo")
            self.assertEqual(
                payload["inspection"]["local_plan"]["selected_files"],
                ["engine.py"],
            )
            self.assertEqual(payload["inspection"]["context"]["status"], "ready")
            self.assertIn("preferred", payload["inspection"]["route"])

    def test_inspect_task_includes_dependency_map_for_map_dependencies_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            (repo_root / "engine.py").write_text("import os\nfrom app.core import task_runner\n", encoding="utf-8")

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
            }):
                payload = _run_command(
                    inspect_task.main,
                    [
                        "inspect_task.py",
                        "map-dependencies",
                        json.dumps({"file": "engine.py", "objective": "Mapear imports"}),
                    ],
                )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["inspection"]["dependency_map"]["status"], "ok")
            self.assertEqual(payload["inspection"]["dependency_map"]["file"], "engine.py")
            self.assertGreaterEqual(payload["inspection"]["dependency_map"]["total_import_count"], 1)
            self.assertIn("symbols", payload["inspection"]["dependency_map"])
            self.assertIn("calls", payload["inspection"]["dependency_map"])
            self.assertIn("call_relations", payload["inspection"]["dependency_map"])
            self.assertIn("dependency_highlights", payload["inspection"])
            self.assertEqual(payload["inspection"]["dependency_highlights"]["status"], "ready")

    def test_assemble_context_includes_dependency_map_for_map_dependencies_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            (repo_root / "engine.py").write_text("import os\n", encoding="utf-8")

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
            }):
                payload = _run_command(
                    assemble_context.main,
                    [
                        "assemble_context.py",
                        "map-dependencies",
                        json.dumps({"file": "engine.py", "objective": "Mapear imports"}),
                    ],
                )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["dependency_map"]["status"], "ok")
            self.assertEqual(payload["dependency_map"]["file"], "engine.py")
            self.assertIn("symbols", payload["dependency_map"])
            self.assertIn("calls", payload["dependency_map"])
            self.assertIn("call_relations", payload["dependency_map"])
            self.assertIn("dependency_highlights", payload)
            self.assertEqual(payload["dependency_highlights"]["status"], "ready")

    def test_map_dependencies_command_supports_alternate_profile_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            (repo_root / "engine.py").write_text("import os\n", encoding="utf-8")

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
            }):
                payload = _run_command(
                    map_dependencies.main,
                    ["map_dependencies.py", "engine.py"],
                )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["project_id"], "demo")
            self.assertEqual(payload["file"], "engine.py")

    def test_task_cli_includes_dependency_map_for_map_dependencies_task(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            (repo_root / "engine.py").write_text("import os\n", encoding="utf-8")

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
                "AI_CACHE_REUSE_ENABLED": "false",
            }):
                payload = _run_command(
                    task_cli.main,
                    [
                        "task_cli.py",
                        "map-dependencies",
                        json.dumps({"file": "engine.py", "objective": "Mapear imports"}),
                    ],
                )

            self.assertEqual(payload["status"], "stub")
            self.assertEqual(payload["task_type"], "map-dependencies")
            self.assertEqual(payload["output"]["dependency_map"]["status"], "ok")
            self.assertEqual(payload["output"]["dependency_map"]["file"], "engine.py")
            self.assertEqual(payload["output"]["dependency_highlights"]["status"], "ready")

    def test_diagnose_orchestrator_reports_alternate_profile_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            state_store.save(
                "last_task_demo_review-file",
                {
                    "task_type": "review-file",
                    "project_id": "demo",
                    "provider": "claude",
                    "status": "stub",
                    "selected_files": ["engine.py"],
                },
            )
            cache_store.set("demo:review-file:engine", "cached")

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
            }):
                with patch("app.commands.diagnose_orchestrator.StateStore", return_value=state_store):
                    with patch("app.commands.diagnose_orchestrator.CacheStore", return_value=cache_store):
                        payload = _run_command(
                            diagnose_orchestrator.main,
                            ["diagnose_orchestrator.py"],
                        )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["project"]["status"], "ok")
            self.assertEqual(payload["project"]["project_id"], "demo")
            self.assertEqual(payload["project"]["target_repo"], str(repo_root))
            self.assertTrue(payload["project"]["target_repo_exists"])
            self.assertEqual(payload["storage"]["state_key_count"], 1)
            self.assertEqual(payload["storage"]["cache_entry_count"], 1)
            self.assertEqual(
                payload["storage"]["recent_task_states"][0]["selected_files"],
                ["engine.py"],
            )

    def test_inspect_task_returns_structured_error_for_invalid_json_payload(self) -> None:
        payload, exit_code = _invoke_command(
            inspect_task.main,
            ["inspect_task.py", "review-file", '{"query":'],
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["reason"], "invalid json payload: Expecting value")

    def test_inspect_task_returns_structured_error_for_non_object_payload(self) -> None:
        payload, exit_code = _invoke_command(
            inspect_task.main,
            ["inspect_task.py", "review-file", '["engine.py"]'],
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["reason"], "json payload must be an object")

    def test_assemble_context_returns_structured_error_for_non_object_payload(self) -> None:
        payload, exit_code = _invoke_command(
            assemble_context.main,
            ["assemble_context.py", "explain-file", '["engine.py"]'],
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["reason"], "json payload must be an object")

    def test_task_cli_returns_structured_error_for_invalid_json_payload(self) -> None:
        payload, exit_code = _invoke_command(
            task_cli.main,
            ["task_cli.py", "review-file", '{"query":'],
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["reason"], "invalid json payload: Expecting value")

    def test_task_cli_returns_structured_error_for_non_object_payload(self) -> None:
        payload, exit_code = _invoke_command(
            task_cli.main,
            ["task_cli.py", "review-file", '["engine.py"]'],
        )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["reason"], "json payload must be an object")

    def test_inspect_task_returns_structured_error_for_missing_profile(self) -> None:
        with _patched_env({
            "AI_DEFAULT_PROJECT": "missing-project",
            "AI_PROJECTS_ROOT": "projects",
        }):
            payload, exit_code = _invoke_command(
                inspect_task.main,
                ["inspect_task.py", "review-file", "{}"],
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertIn("project profile not found for 'missing-project'", payload["reason"])

    def test_task_cli_returns_structured_error_for_missing_profile(self) -> None:
        with _patched_env({
            "AI_DEFAULT_PROJECT": "missing-project",
            "AI_PROJECTS_ROOT": "projects",
        }):
            payload, exit_code = _invoke_command(
                task_cli.main,
                ["task_cli.py", "review-file", "{}"],
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(payload["status"], "error")
        self.assertIn("project profile not found for 'missing-project'", payload["reason"])

    def test_inspect_task_marks_context_partial_when_target_repo_is_not_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, _ = _create_demo_project(tmpdir)
            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": None,
            }):
                payload = _run_command(
                    inspect_task.main,
                    [
                        "inspect_task.py",
                        "review-file",
                        json.dumps({"query": "engine", "objective": "Revisar engine runtime"}),
                    ],
                )

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["inspection"]["context"]["status"], "partial")
        self.assertEqual(payload["inspection"]["context"]["reason"], "target repo not configured")

    def test_inspect_task_reuses_cached_inspection_within_ttl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            mocked_inspection = {
                "task_type": "review-file",
                "payload": {"query": "engine"},
                "route": {"preferred": "claude", "fallbacks": []},
                "context": {"status": "ready"},
                "local_plan": {"selected_files": ["engine.py"]},
                "providers": [],
            }

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
                "AI_INSPECT_CACHE_REUSE_ENABLED": "true",
                "AI_INSPECT_CACHE_TTL_SEC": "300",
            }):
                with patch("app.commands.inspect_task.CacheStore", return_value=cache_store):
                    with patch.object(TaskRunner, "inspect", return_value=mocked_inspection) as mock_inspect:
                        first = _run_command(
                            inspect_task.main,
                            [
                                "inspect_task.py",
                                "review-file",
                                json.dumps({"query": "engine", "objective": "Revisar engine runtime"}),
                            ],
                        )
                        second = _run_command(
                            inspect_task.main,
                            [
                                "inspect_task.py",
                                "review-file",
                                json.dumps({"query": "engine", "objective": "Revisar engine runtime"}),
                            ],
                        )
                        refreshed = _run_command(
                            inspect_task.main,
                            [
                                "inspect_task.py",
                                "review-file",
                                json.dumps({"query": "engine", "objective": "Revisar engine runtime", "force_refresh": True}),
                            ],
                        )

            self.assertEqual(mock_inspect.call_count, 2)
            self.assertEqual(first["inspection"]["cache"]["hit"], False)
            self.assertEqual(second["inspection"]["cache"]["hit"], True)
            self.assertEqual(refreshed["inspection"]["cache"]["hit"], False)
            self.assertEqual(second["inspection"]["local_plan"]["selected_files"], ["engine.py"])

    def test_inspect_then_task_cli_covers_fallback_and_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            state_store = StateStore(base_dir=f"{tmpdir}/state")
            cache_store = CacheStore(base_dir=f"{tmpdir}/cache")
            operational_store = OperationalStore(state_store=state_store, cache_store=cache_store)

            with _patched_env({
                "AI_PROJECTS_ROOT": str(projects_root),
                "AI_DEFAULT_PROJECT": "demo",
                "AI_TARGET_REPO_ALT": str(repo_root),
                "AI_CACHE_REUSE_ENABLED": "false",
            }):
                inspection = _run_command(
                    inspect_task.main,
                    [
                        "inspect_task.py",
                        "review-file",
                        json.dumps({"query": "engine", "objective": "Revisar engine runtime"}),
                    ],
                )

                with patch("app.core.task_runner.OperationalStore", return_value=operational_store):
                    with patch.object(TaskRunner, "_execute_provider") as mock_execute_provider:
                        mock_execute_provider.side_effect = [
                            {"provider": "claude", "status": "error", "output": {"reason": "network_error:timeout", "failure_type": "network"}},
                            {"provider": "claude", "status": "error", "output": {"reason": "network_error:timeout", "failure_type": "network"}},
                            {"provider": "gemini", "status": "stub", "output": {"mode": "stub"}},
                        ]
                        execution = _run_command(
                            task_cli.main,
                            [
                                "task_cli.py",
                                "review-file",
                                json.dumps({"query": "engine", "objective": "Revisar engine runtime"}),
                            ],
                        )

            self.assertEqual(inspection["status"], "ok")
            self.assertEqual(inspection["inspection"]["route"]["preferred"], "claude")
            self.assertIn("gemini", inspection["inspection"]["route"]["fallbacks"])
            self.assertEqual(execution["status"], "stub")
            self.assertEqual(execution["provider"], "gemini")
            self.assertEqual(
                execution["output"]["provider_attempts"],
                [
                    {"provider": "claude", "attempt": 1, "status": "error", "failure_type": "network"},
                    {"provider": "claude", "attempt": 2, "status": "error", "failure_type": "network"},
                    {"provider": "gemini", "attempt": 1, "status": "stub", "failure_type": "success"},
                ],
            )
            self.assertIn("persistence", execution["output"])
            self.assertTrue(execution["output"]["persistence"]["state_key"].startswith("last_task_demo_"))


def _create_demo_project(tmpdir: str) -> tuple[Path, Path]:
    projects_root = Path(tmpdir) / "profiles"
    create_test_project_profile(projects_root, "demo")

    repo_root = Path(tmpdir) / "repo"
    repo_root.mkdir()
    (repo_root / "engine.py").write_text("print('engine')\n", encoding="utf-8")
    return projects_root, repo_root


class _patched_env:
    def __init__(self, updates: dict[str, str | None]) -> None:
        self._updates = updates
        self._previous: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for key, value in self._updates.items():
            self._previous[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def __exit__(self, exc_type, exc, tb) -> None:
        for key, value in self._previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _run_command(command_main, argv: list[str]) -> dict:
    payload, exit_code = _invoke_command(command_main, argv)
    if exit_code != 0:
        raise AssertionError(f"command failed with exit code {exit_code}: {json.dumps(payload, ensure_ascii=False)}")
    return payload


def _invoke_command(command_main, argv: list[str]) -> tuple[dict, int]:
    stdout = io.StringIO()
    with patch.object(sys, "argv", argv):
        with patch("sys.stdout", new=stdout):
            exit_code = command_main()
    return json.loads(stdout.getvalue()), exit_code


if __name__ == "__main__":
    unittest.main()
