import tempfile
import unittest

from app.core.budget_manager import BudgetManager
from app.storage.state_store import StateStore


class BudgetManagerTest(unittest.TestCase):
    def test_record_persists_daily_budget_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=tmpdir)

            first = BudgetManager(
                {"claude": 10.0, "gemini": 5.0},
                state_store=state_store,
                current_date="2026-04-21",
            )
            first.record("claude", 1.5)
            first.record("gemini", 2.0)

            second = BudgetManager(
                {"claude": 10.0, "gemini": 5.0},
                state_store=state_store,
                current_date="2026-04-21",
            )

            self.assertEqual(second.status("claude").spent, 1.5)
            self.assertEqual(second.status("gemini").spent, 2.0)
            self.assertEqual(second.status("claude").remaining, 8.5)
            self.assertTrue(second.status("gemini").available)

    def test_budget_isolated_by_day(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            state_store = StateStore(base_dir=tmpdir)

            today = BudgetManager(
                {"claude": 10.0},
                state_store=state_store,
                current_date="2026-04-21",
            )
            today.record("claude", 4.0)

            tomorrow = BudgetManager(
                {"claude": 10.0},
                state_store=state_store,
                current_date="2026-04-22",
            )

            self.assertEqual(tomorrow.status("claude").spent, 0.0)
            self.assertEqual(tomorrow.status("claude").remaining, 10.0)


if __name__ == "__main__":
    unittest.main()
