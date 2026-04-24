import os
import tempfile
import unittest
from pathlib import Path

from app.core.project_loader import load_project_profile, load_runtime_project
from tests.test_helpers import create_test_project_profile


class ProjectLoaderTest(unittest.TestCase):
    def test_load_project_profile_reads_expected_fields(self) -> None:
        profile = load_project_profile("ia-trade")

        self.assertEqual(profile.project_id, "ia-trade")
        self.assertEqual(profile.repo_path_env, "AI_TARGET_REPO")
        self.assertIn("projects/ia-trade/memory/facts.md", profile.memory_files)
        self.assertIn("repo_worker", profile.prompt_files)
        self.assertIsInstance(profile.context_rules, dict)

    def test_load_runtime_project_uses_profile_env_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            old_write = os.environ.get("AI_REPO_WRITE_ENABLED")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir
                os.environ["AI_REPO_WRITE_ENABLED"] = "true"

                runtime = load_runtime_project()

                self.assertEqual(runtime.project_id, "ia-trade")
                self.assertEqual(runtime.target_repo, tmpdir)
                self.assertTrue(runtime.write_enabled)
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)
                _restore_env("AI_REPO_WRITE_ENABLED", old_write)

    def test_load_project_profile_raises_for_unknown_project(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_project_profile("missing-project")

    def test_load_runtime_project_supports_alternate_projects_root_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root = Path(tmpdir) / "profiles"
            create_test_project_profile(projects_root, "demo")

            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()

            old_projects_root = os.environ.get("AI_PROJECTS_ROOT")
            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO_ALT")
            old_write = os.environ.get("AI_REPO_WRITE_ENABLED_ALT")
            try:
                os.environ["AI_PROJECTS_ROOT"] = str(projects_root)
                os.environ["AI_DEFAULT_PROJECT"] = "demo"
                os.environ["AI_TARGET_REPO_ALT"] = str(repo_root)
                os.environ["AI_REPO_WRITE_ENABLED_ALT"] = "true"

                runtime = load_runtime_project()

                self.assertEqual(runtime.project_id, "demo")
                self.assertEqual(runtime.target_repo, str(repo_root))
                self.assertTrue(runtime.write_enabled)
                self.assertEqual(runtime.profile.repo_path_env, "AI_TARGET_REPO_ALT")
            finally:
                _restore_env("AI_PROJECTS_ROOT", old_projects_root)
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO_ALT", old_target)
                _restore_env("AI_REPO_WRITE_ENABLED_ALT", old_write)

    def test_load_project_profile_reads_context_rules_from_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root = Path(tmpdir) / "profiles"
            create_test_project_profile(
                projects_root,
                "demo",
                context_rules={
                    "max_target_files": 3,
                    "task_file_limits": {"review-file": 2},
                    "task_queries": {"review-file": ["engine"]},
                    "pinned_files_by_task": {"review-file": ["engine.py"]},
                },
            )

            profile = load_project_profile("demo", projects_root=str(projects_root))

            self.assertEqual(profile.context_rules.get("max_target_files"), 3)
            self.assertEqual(profile.context_rules.get("task_file_limits", {}).get("review-file"), 2)
            self.assertEqual(profile.context_rules.get("task_queries", {}).get("review-file"), ["engine"])


def _restore_env(name: str, value: str | None) -> None:
    if value is None:
        os.environ.pop(name, None)
        return
    os.environ[name] = value


if __name__ == "__main__":
    unittest.main()
