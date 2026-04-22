import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.commands import diagnose_orchestrator, inspect_project, inspect_task
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
    stdout = io.StringIO()
    with patch.object(sys, "argv", argv):
        with patch("sys.stdout", new=stdout):
            exit_code = command_main()
    if exit_code != 0:
        raise AssertionError(f"command failed with exit code {exit_code}: {stdout.getvalue()}")
    return json.loads(stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
