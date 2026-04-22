import tempfile
import unittest
from pathlib import Path

from app.core.dependency_mapper import classify_import, map_python_dependencies, summarize_dependency_map


class DependencyMapperTest(unittest.TestCase):
    def test_classify_import_marks_known_roots_as_local(self) -> None:
        self.assertEqual(classify_import("app.core.task_runner"), "local")
        self.assertEqual(classify_import("analysis.snapshot"), "local")
        self.assertEqual(classify_import("requests"), "external")

    def test_map_python_dependencies_reads_and_classifies_imports(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "local_module.py").write_text("def helper():\n    return 1\n", encoding="utf-8")
            (root / "app" / "core").mkdir(parents=True, exist_ok=True)
            (root / "app" / "core" / "task_runner.py").write_text("def main():\n    return 0\n", encoding="utf-8")
            (root / "sample.py").write_text(
                "\n".join(
                    [
                        "import os",
                        "import app.core.task_runner as runner",
                        "from .local_module import helper",
                        "",
                        "def local_helper():",
                        "    return os.getcwd()",
                        "",
                        "class Runner:",
                        "    def run(self):",
                        "        return local_helper()",
                        "",
                        "local_helper()",
                        "helper()",
                        "runner.main()",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            payload = map_python_dependencies(str(root), "sample.py")

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["file"], "sample.py")
            self.assertEqual(payload["total_import_count"], 3)
            self.assertEqual(payload["local_import_count"], 2)
            self.assertEqual(payload["external_import_count"], 1)
            self.assertEqual(payload["symbols"]["top_level_functions"], ["local_helper"])
            self.assertEqual(payload["symbols"]["classes"], ["Runner"])
            self.assertEqual(payload["symbols"]["methods"], ["Runner.run"])
            self.assertIn("local_helper", payload["calls"]["named_calls"])
            self.assertIn("os.getcwd", payload["calls"]["attribute_calls"])
            self.assertEqual(payload["calls"]["local_named_call_count"], 1)
            self.assertEqual(payload["local_import_resolved_count"], 2)
            self.assertEqual(payload["local_import_unresolved_count"], 0)
            self.assertEqual(len(payload["local_import_targets"]), 2)
            self.assertEqual(payload["call_relation_count"], 2)
            self.assertEqual(payload["resolved_call_relation_count"], 2)
            self.assertEqual(payload["unresolved_call_relation_count"], 0)
            self.assertEqual(
                {item["call"] for item in payload["call_relations"]},
                {"helper", "runner.main"},
            )
            relations = payload["call_relations"]
            self.assertEqual(relations[0]["relation_rank"], 1)
            self.assertEqual(relations[1]["relation_rank"], 2)
            self.assertGreaterEqual(relations[0]["relation_score"], relations[1]["relation_score"])
            self.assertEqual(relations[0]["relation_priority"], "high")
            self.assertIn(relations[1]["relation_priority"], {"high", "medium"})
            self.assertTrue(all("target_symbol_match" in relation for relation in relations))
            self.assertTrue(all("call_frequency" in relation for relation in relations))
            self.assertIn("call_relation_summary", payload)
            self.assertEqual(payload["call_relation_summary"]["top_relation"]["relation_rank"], 1)
            self.assertEqual(
                payload["call_relation_summary"]["by_priority"]["high"]
                + payload["call_relation_summary"]["by_priority"]["medium"]
                + payload["call_relation_summary"]["by_priority"]["low"],
                payload["call_relation_count"],
            )
            self.assertEqual(payload["call_relation_summary"]["risk_flags"]["has_structural_risk"], False)
            targets = {item["import"]: item for item in payload["local_import_targets"]}
            self.assertIn(".local_module", targets)
            self.assertIn("app.core.task_runner", targets)
            self.assertIn("helper", targets[".local_module"]["target_symbols"]["functions"])
            self.assertIn("main", targets["app.core.task_runner"]["target_symbols"]["functions"])

    def test_map_python_dependencies_flags_unresolved_high_frequency_calls(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "sample.py").write_text(
                "\n".join(
                    [
                        "from app.missing import ghost",
                        "ghost()",
                        "ghost()",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            payload = map_python_dependencies(str(root), "sample.py")

            self.assertEqual(payload["status"], "ok")
            self.assertEqual(payload["call_relation_count"], 1)
            self.assertEqual(payload["call_relations"][0]["call_frequency"], 2)
            self.assertEqual(payload["call_relations"][0]["target_exists"], False)
            self.assertTrue(payload["call_relation_summary"]["risk_flags"]["has_structural_risk"])
            self.assertEqual(
                payload["call_relation_summary"]["risk_flags"]["unresolved_high_frequency"][0]["call"],
                "ghost",
            )

    def test_summarize_dependency_map_returns_executive_view(self) -> None:
        summary = summarize_dependency_map(
            {
                "status": "ok",
                "file": "sample.py",
                "total_import_count": 3,
                "local_import_count": 2,
                "external_import_count": 1,
                "call_relation_count": 2,
                "resolved_call_relation_count": 1,
                "unresolved_call_relation_count": 1,
                "call_relation_summary": {
                    "by_priority": {"high": 1, "medium": 1, "low": 0},
                    "top_relation": {"call": "helper", "relation_rank": 1},
                    "risk_flags": {"has_structural_risk": True},
                },
            }
        )

        self.assertEqual(summary["status"], "ready")
        self.assertEqual(summary["file"], "sample.py")
        self.assertEqual(summary["import_counts"]["total"], 3)
        self.assertEqual(summary["relation_counts"]["unresolved"], 1)
        self.assertEqual(summary["priority_counts"]["high"], 1)
        self.assertTrue(summary["has_structural_risk"])
        self.assertEqual(summary["top_relation"]["call"], "helper")

    def test_map_python_dependencies_returns_structured_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            (root / "broken.py").write_text("from app.core import (\n", encoding="utf-8")

            self.assertEqual(
                map_python_dependencies("", "broken.py"),
                {"status": "error", "reason": "target repo not configured"},
            )
            self.assertEqual(
                map_python_dependencies(str(root), ""),
                {"status": "error", "reason": "target file not provided"},
            )
            self.assertEqual(
                map_python_dependencies(str(root), "notes.md"),
                {"status": "error", "reason": "target file must be a .py file"},
            )
            self.assertEqual(
                map_python_dependencies(str(root), "missing.py")["status"],
                "error",
            )
            self.assertIn(
                "syntax error while parsing file",
                map_python_dependencies(str(root), "broken.py")["reason"],
            )


if __name__ == "__main__":
    unittest.main()
