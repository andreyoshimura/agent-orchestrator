import os
import tempfile
import unittest
from pathlib import Path

from app.core.context_builder import ContextBuilder
from app.core.project_loader import load_runtime_project
from tests.test_helpers import create_test_project_profile


class ContextBuilderTest(unittest.TestCase):
    def test_build_includes_global_and_project_sections(self) -> None:
        old_project = os.environ.get("AI_DEFAULT_PROJECT")
        old_target = os.environ.get("AI_TARGET_REPO")
        try:
            os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
            os.environ.pop("AI_TARGET_REPO", None)

            bundle = ContextBuilder(load_runtime_project()).build(
                task_type="explain-file",
                payload={},
            )

            self.assertIn("GLOBAL_BOOTSTRAP", bundle.sections)
            self.assertIn("PROJECT_BOOTSTRAP", bundle.sections)
            self.assertIn("PROJECT_AGENT_CONTEXT", bundle.sections)
            self.assertEqual(bundle.prompt_name, "repo_worker")
            self.assertIn("You are the repo_worker agent.", bundle.prompt_text)
        finally:
            _restore_env("AI_DEFAULT_PROJECT", old_project)
            _restore_env("AI_TARGET_REPO", old_target)

    def test_build_reads_target_files_when_repo_is_configured(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            sample_path = os.path.join(tmpdir, "sample.py")
            with open(sample_path, "w", encoding="utf-8") as handle:
                handle.write("print('ok')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                bundle = ContextBuilder(load_runtime_project()).build(
                    task_type="review-file",
                    payload={"file": "sample.py"},
                )

                self.assertIn("TARGET_FILE::sample.py", bundle.sections)
                self.assertEqual(bundle.prompt_name, "micro_reviewer")
                self.assertIn("You are the micro_reviewer agent.", bundle.prompt_text)
                self.assertIn("print('ok')", bundle.context_text)
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_build_auto_selects_target_file_from_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paper_path = os.path.join(tmpdir, "paper_trade.py")
            with open(paper_path, "w", encoding="utf-8") as handle:
                handle.write("print('paper')\n")
            os.mkdir(os.path.join(tmpdir, "analysis"))
            with open(os.path.join(tmpdir, "analysis", "paper_notes.py"), "w", encoding="utf-8") as handle:
                handle.write("print('notes')\n")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                bundle = ContextBuilder(load_runtime_project()).build(
                    task_type="review-file",
                    payload={"query": "paper", "objective": "Revisar entrypoint paper"},
                )

                self.assertIn("TARGET_FILE::paper_trade.py", bundle.sections)
                self.assertEqual(bundle.files, ["paper_trade.py"])
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_build_uses_alternate_profile_root_from_env(self) -> None:
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

                bundle = ContextBuilder(load_runtime_project()).build(
                    task_type="review-file",
                    payload={"query": "engine", "objective": "Revisar engine runtime"},
                )

                self.assertEqual(bundle.project_id, "demo")
                self.assertEqual(bundle.files, ["engine.py"])
                self.assertIn("TARGET_FILE::engine.py", bundle.sections)
                self.assertIn("facts for demo", bundle.context_text)
            finally:
                _restore_env("AI_PROJECTS_ROOT", old_projects_root)
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO_ALT", old_target)

    def test_build_respects_profile_context_rules_for_task_limit_and_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root = Path(tmpdir) / "profiles"
            create_test_project_profile(
                projects_root,
                "demo",
                context_rules={
                    "max_target_files": 4,
                    "task_file_limits": {"review-file": 2},
                    "task_queries": {"review-file": ["engine"]},
                },
            )

            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()
            (repo_root / "engine.py").write_text("print('engine')\n", encoding="utf-8")
            (repo_root / "engine_service.py").write_text("print('service')\n", encoding="utf-8")
            (repo_root / "other.py").write_text("print('other')\n", encoding="utf-8")

            old_projects_root = os.environ.get("AI_PROJECTS_ROOT")
            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO_ALT")
            try:
                os.environ["AI_PROJECTS_ROOT"] = str(projects_root)
                os.environ["AI_DEFAULT_PROJECT"] = "demo"
                os.environ["AI_TARGET_REPO_ALT"] = str(repo_root)

                bundle = ContextBuilder(load_runtime_project()).build(
                    task_type="review-file",
                    payload={"objective": "Comparar engine e service"},
                )

                self.assertLessEqual(len(bundle.files), 2)
                self.assertIn("engine.py", bundle.files)
                self.assertIn("engine_service.py", bundle.files)
                self.assertIn("TARGET_FILE::engine.py", bundle.sections)
            finally:
                _restore_env("AI_PROJECTS_ROOT", old_projects_root)
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO_ALT", old_target)

    def test_build_prioritizes_pinned_files_from_profile_context_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root = Path(tmpdir) / "profiles"
            create_test_project_profile(
                projects_root,
                "demo",
                context_rules={
                    "max_target_files": 2,
                    "task_file_limits": {"review-file": 2},
                    "task_queries": {"review-file": ["engine"]},
                    "pinned_files_by_task": {"review-file": ["risk_manager.py"]},
                },
            )

            repo_root = Path(tmpdir) / "repo"
            repo_root.mkdir()
            (repo_root / "engine.py").write_text("print('engine')\n", encoding="utf-8")
            (repo_root / "risk_manager.py").write_text("print('risk')\n", encoding="utf-8")

            old_projects_root = os.environ.get("AI_PROJECTS_ROOT")
            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO_ALT")
            try:
                os.environ["AI_PROJECTS_ROOT"] = str(projects_root)
                os.environ["AI_DEFAULT_PROJECT"] = "demo"
                os.environ["AI_TARGET_REPO_ALT"] = str(repo_root)

                bundle = ContextBuilder(load_runtime_project()).build(
                    task_type="review-file",
                    payload={"objective": "Revisar runtime"},
                )

                self.assertEqual(bundle.files[0], "risk_manager.py")
                self.assertIn("TARGET_FILE::risk_manager.py", bundle.sections)
            finally:
                _restore_env("AI_PROJECTS_ROOT", old_projects_root)
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO_ALT", old_target)

    def test_build_uses_task_prompt_override_from_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            projects_root = Path(tmpdir) / "profiles"
            create_test_project_profile(
                projects_root,
                "demo",
                task_prompt_overrides={"review-file": "repo_worker"},
            )

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

                bundle = ContextBuilder(load_runtime_project()).build(
                    task_type="review-file",
                    payload={"query": "engine"},
                )

                self.assertEqual(bundle.prompt_name, "repo_worker")
                self.assertIn("You are the repo_worker agent.", bundle.prompt_text)
            finally:
                _restore_env("AI_PROJECTS_ROOT", old_projects_root)
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO_ALT", old_target)

    def test_build_deduplicates_explicit_files_and_respects_max_target_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.py").write_text("print('a')\n", encoding="utf-8")
            (Path(tmpdir) / "b.py").write_text("print('b')\n", encoding="utf-8")
            (Path(tmpdir) / "c.py").write_text("print('c')\n", encoding="utf-8")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                bundle = ContextBuilder(load_runtime_project(), max_target_files=2).build(
                    task_type="review-file",
                    payload={"files": ["a.py", "a.py", "b.py", "c.py"]},
                )

                self.assertEqual(bundle.files, ["a.py", "b.py"])
                self.assertIn("TARGET_FILE::a.py", bundle.sections)
                self.assertIn("TARGET_FILE::b.py", bundle.sections)
                self.assertNotIn("TARGET_FILE::c.py", bundle.sections)
            finally:
                _restore_env("AI_DEFAULT_PROJECT", old_project)
                _restore_env("AI_TARGET_REPO", old_target)

    def test_build_skips_missing_explicit_files_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "present.py").write_text("print('ok')\n", encoding="utf-8")

            old_project = os.environ.get("AI_DEFAULT_PROJECT")
            old_target = os.environ.get("AI_TARGET_REPO")
            try:
                os.environ["AI_DEFAULT_PROJECT"] = "ia-trade"
                os.environ["AI_TARGET_REPO"] = tmpdir

                bundle = ContextBuilder(load_runtime_project()).build(
                    task_type="review-file",
                    payload={"files": ["missing.py", "present.py"]},
                )

                self.assertEqual(bundle.files, ["missing.py", "present.py"])
                self.assertNotIn("TARGET_FILE::missing.py", bundle.sections)
                self.assertIn("TARGET_FILE::present.py", bundle.sections)
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
