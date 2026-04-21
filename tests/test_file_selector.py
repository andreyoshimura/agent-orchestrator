import tempfile
import unittest
from pathlib import Path

from app.core.file_selector import auto_select_python_files, choose_best_python_match, collect_python_files


class FileSelectorTest(unittest.TestCase):
    def test_choose_best_python_match_prefers_root_runtime_file(self) -> None:
        files = [
            "analysis/paper_snapshot.py",
            "paper_trade.py",
            "tests/test_paper_trade.py",
        ]
        best = choose_best_python_match("paper", files)

        self.assertIsNotNone(best)
        self.assertEqual(best.file, "paper_trade.py")

    def test_auto_select_python_files_uses_objective_tokens(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "paper_trade.py").write_text("print('paper')\n", encoding="utf-8")
            (root / "risk").mkdir()
            (root / "risk" / "risk_manager.py").write_text("print('risk')\n", encoding="utf-8")
            (root / "analysis").mkdir()
            (root / "analysis" / "risk_snapshot.py").write_text("print('snapshot')\n", encoding="utf-8")

            ranked = auto_select_python_files(
                root=root,
                task_type="review-file",
                objective="Revisar fluxo de risk manager runtime",
                limit=2,
            )

            self.assertTrue(ranked)
            self.assertEqual(ranked[0].file, "risk/risk_manager.py")

    def test_auto_select_python_files_limits_review_file_to_top_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "paper_trade.py").write_text("print('paper')\n", encoding="utf-8")
            (root / "analysis").mkdir()
            (root / "analysis" / "paper_notes.py").write_text("print('notes')\n", encoding="utf-8")

            ranked = auto_select_python_files(
                root=root,
                task_type="review-file",
                objective="Revisar entrypoint paper",
                query="paper",
                limit=5,
            )

            self.assertEqual([item.file for item in ranked], ["paper_trade.py"])

    def test_auto_select_python_files_trims_weak_matches_for_multi_file_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "risk").mkdir()
            (root / "risk" / "risk_manager.py").write_text("print('risk')\n", encoding="utf-8")
            (root / "risk" / "risk_policy.py").write_text("print('policy')\n", encoding="utf-8")
            (root / "analysis").mkdir()
            (root / "analysis" / "risk_snapshot.py").write_text("print('snapshot')\n", encoding="utf-8")

            ranked = auto_select_python_files(
                root=root,
                task_type="review-diff",
                objective="Comparar risk manager e risk policy",
                query="risk",
                limit=5,
            )

            self.assertEqual(
                [item.file for item in ranked],
                ["risk/risk_manager.py", "risk/risk_policy.py"],
            )

    def test_auto_select_python_files_keeps_distinct_comparison_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "risk").mkdir()
            (root / "risk" / "risk_manager.py").write_text("print('risk')\n", encoding="utf-8")
            (root / "risk" / "risk_policy.py").write_text("print('policy')\n", encoding="utf-8")
            (root / "risk" / "risk_report.py").write_text("print('report')\n", encoding="utf-8")

            ranked = auto_select_python_files(
                root=root,
                task_type="review-diff",
                objective="Comparar risk manager e risk policy",
                query="risk",
                limit=2,
            )

            self.assertEqual(
                [item.file for item in ranked],
                ["risk/risk_manager.py", "risk/risk_policy.py"],
            )

    def test_collect_python_files_ignores_virtualenv_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / ".venv").mkdir()
            (root / ".venv" / "ignored.py").write_text("", encoding="utf-8")
            (root / "app.py").write_text("", encoding="utf-8")

            files = collect_python_files(root)

            self.assertEqual(files, ["app.py"])


if __name__ == "__main__":
    unittest.main()
