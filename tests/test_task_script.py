import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_helpers import create_test_project_profile


class TaskScriptTest(unittest.TestCase):
    def test_legacy_summarize_repo_area_alias_uses_generic_context_assembly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            (repo_root / "README.md").write_text("# Demo repo\n", encoding="utf-8")
            payload = _run_task_script(
                [
                    "summarize-repo-area",
                    "README.md",
                    "engine.py",
                ],
                {
                    "AI_PROJECTS_ROOT": str(projects_root),
                    "AI_DEFAULT_PROJECT": "demo",
                    "AI_TARGET_REPO_ALT": str(repo_root),
                },
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["task_type"], "summarize-module")
            self.assertEqual(payload["files"], ["README.md", "engine.py"])
            self.assertIn("TARGET_FILE::README.md", payload["sections"])
            self.assertIn("TARGET_FILE::engine.py", payload["sections"])

    def test_legacy_explain_file_alias_uses_generic_context_assembly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            payload = _run_task_script(
                [
                    "explain-file",
                    "engine.py",
                ],
                {
                    "AI_PROJECTS_ROOT": str(projects_root),
                    "AI_DEFAULT_PROJECT": "demo",
                    "AI_TARGET_REPO_ALT": str(repo_root),
                },
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["task_type"], "explain-file")
            self.assertEqual(payload["files"], ["engine.py"])
            self.assertIn("TARGET_FILE::engine.py", payload["sections"])

    def test_legacy_review_file_alias_uses_generic_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            payload = _run_task_script(
                [
                    "review-file",
                    "engine.py",
                ],
                {
                    "AI_PROJECTS_ROOT": str(projects_root),
                    "AI_DEFAULT_PROJECT": "demo",
                    "AI_TARGET_REPO_ALT": str(repo_root),
                },
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["inspection"]["task_type"], "review-file")
            self.assertEqual(payload["inspection"]["local_plan"]["selected_files"], ["engine.py"])
            self.assertEqual(payload["inspection"]["context"]["status"], "ready")

    def test_legacy_pick_python_file_alias_uses_generic_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            payload = _run_task_script(
                [
                    "pick-python-file",
                    "engine",
                ],
                {
                    "AI_PROJECTS_ROOT": str(projects_root),
                    "AI_DEFAULT_PROJECT": "demo",
                    "AI_TARGET_REPO_ALT": str(repo_root),
                },
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["inspection"]["task_type"], "review-file")
            self.assertEqual(payload["inspection"]["local_plan"]["selected_files"], ["engine.py"])
            self.assertEqual(payload["inspection"]["context"]["status"], "ready")

    def test_legacy_explain_best_python_match_alias_uses_generic_context_assembly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            payload = _run_task_script(
                [
                    "explain-best-python-match",
                    "engine",
                ],
                {
                    "AI_PROJECTS_ROOT": str(projects_root),
                    "AI_DEFAULT_PROJECT": "demo",
                    "AI_TARGET_REPO_ALT": str(repo_root),
                },
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["task_type"], "explain-file")
            self.assertEqual(payload["files"], ["engine.py"])
            self.assertIn("TARGET_FILE::engine.py", payload["sections"])

    def test_legacy_review_best_python_match_alias_uses_generic_inspection(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root, repo_root = _create_demo_project(tmpdir)
            payload = _run_task_script(
                [
                    "review-best-python-match",
                    "engine",
                ],
                {
                    "AI_PROJECTS_ROOT": str(projects_root),
                    "AI_DEFAULT_PROJECT": "demo",
                    "AI_TARGET_REPO_ALT": str(repo_root),
                },
            )

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["inspection"]["task_type"], "review-file")
            self.assertEqual(payload["inspection"]["local_plan"]["selected_files"], ["engine.py"])
            self.assertEqual(payload["inspection"]["context"]["status"], "ready")


def _create_demo_project(tmpdir: str) -> tuple[Path, Path]:
    projects_root = Path(tmpdir) / "profiles"
    create_test_project_profile(projects_root, "demo")

    repo_root = Path(tmpdir) / "repo"
    repo_root.mkdir()
    (repo_root / "engine.py").write_text("print('engine')\n", encoding="utf-8")
    return projects_root, repo_root


def _run_task_script(args: list[str], env_updates: dict[str, str]) -> dict:
    env = os.environ.copy()
    env.update(env_updates)
    env["PYTHON_BIN"] = sys.executable

    result = subprocess.run(
        ["bash", "scripts/task.sh", *args],
        cwd="/media/msx/SD200/VSCODE/github/agent-orchestrator",
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise AssertionError(
            f"task.sh failed with exit code {result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
