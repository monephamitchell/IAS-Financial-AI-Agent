
"""
Immaculate Automation Solutions (IAS)
Automated Agent Controller Tests

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone

Tests the integrated financial agent, including
planning, validation, categorization, memory,
financial safeguards, and error handling.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Allow tests to import the IAS source modules.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from agent_controller import IASAgent
from feedback_memory import FeedbackMemory


class TestIASAgentController(unittest.TestCase):

    def setUp(self):
        """Create an isolated workspace for every test."""
        self.temp_folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_folder.cleanup)

        self.folder = Path(self.temp_folder.name)
        self.csv_path = self.folder / "transactions.csv"
        self.memory_path = self.folder / "memory.json"

    def create_csv(self, rows):
        """Create a fictional financial CSV file."""
        self.csv_path.write_text(
            "date,description,amount\n" + rows,
            encoding="utf-8"
        )
        return self.csv_path

    def test_agent_planning(self):
        """Verify the agent creates its execution plan."""
        agent = IASAgent(profile="business")
        plan = agent.create_plan()

        self.assertEqual(len(plan), 5)
        self.assertIn("Categorize", plan[2])
        self.assertIn("financial report", plan[4])

    def test_business_processing(self):
        """Verify the complete business workflow."""
        path = self.create_csv(
            "2026-11-01,Customer Payment,850.00\n"
            "2026-11-02,Office Supplies,-125.50\n"
        )

        results = IASAgent("business").run(path)

        self.assertEqual(
            results["summary"]["valid_transactions"], 2
        )
        self.assertEqual(
            results["summary"]["net_cash_flow"], 724.50
        )
        self.assertEqual(
            results["transactions"][0]["category"],
            "Business Revenue"
        )
        self.assertEqual(
            results["transactions"][1]["category"],
            "Office Supplies"
        )

    def test_personal_uncategorized_review(self):
        """Verify unknown categories require review."""
        path = self.create_csv(
            "2026-11-01,Office Supplies,-75.00\n"
        )

        results = IASAgent("personal").run(path)

        self.assertEqual(len(results["review_items"]), 1)
        self.assertEqual(
            results["transactions"][0]["category"],
            "Uncategorized"
        )

    def test_memory_changes_categorization(self):
        """Verify approved corrections improve decisions."""
        path = self.create_csv(
            "2026-11-01,Office Supplies,-75.00\n"
        )

        baseline = IASAgent("personal").run(path)

        memory = FeedbackMemory(self.memory_path)
        memory.record_feedback(
            "Office Supplies",
            "personal",
            "Household Supplies",
            True
        )

        improved = IASAgent(
            "personal", self.memory_path
        ).run(path)

        self.assertEqual(len(baseline["review_items"]), 1)
        self.assertEqual(len(improved["review_items"]), 0)

        self.assertEqual(
            improved["transactions"][0]["category"],
            "Household Supplies"
        )
        self.assertEqual(
            improved["transactions"][0]["source"],
            "memory"
        )

    def test_memory_profiles_remain_separate(self):
        """Personal feedback must not change business rules."""
        path = self.create_csv(
            "2026-11-01,Office Supplies,-75.00\n"
        )

        memory = FeedbackMemory(self.memory_path)
        memory.record_feedback(
            "Office Supplies",
            "personal",
            "Household Supplies",
            True
        )

        results = IASAgent(
            "business", self.memory_path
        ).run(path)

        self.assertEqual(
            results["transactions"][0]["category"],
            "Office Supplies"
        )
        self.assertEqual(
            results["transactions"][0]["source"],
            "default_rules"
        )

    def test_loan_payment_safety(self):
        """Remembered loan categories must require review."""
        path = self.create_csv(
            "2026-11-01,Car Loan,-350.00\n"
        )

        memory = FeedbackMemory(self.memory_path)
        memory.record_feedback(
            "Car Loan",
            "personal",
            "Auto Loans",
            True
        )

        results = IASAgent(
            "personal", self.memory_path
        ).run(path)

        self.assertTrue(
            results["transactions"][0]["review_required"]
        )

    def test_transfer_requires_review(self):
        """Transfers must not be treated as ordinary expenses."""
        path = self.create_csv(
            "2026-11-01,Internal Transfer,-500.00\n"
        )

        results = IASAgent("personal").run(path)

        self.assertEqual(
            results["transactions"][0]["category"],
            "Transfers"
        )
        self.assertTrue(
            results["transactions"][0]["review_required"]
        )

    def test_unusual_amount_direction(self):
        """Positive amounts in expense categories need review."""
        path = self.create_csv(
            "2026-11-01,Office Supplies,100.00\n"
        )

        results = IASAgent("business").run(path)

        self.assertTrue(
            results["transactions"][0]["review_required"]
        )

    def test_invalid_and_duplicate_records(self):
        """Verify validation findings reach the agent report."""
        path = self.create_csv(
            "2026-11-01,Customer Payment,500.00\n"
            "2026-11-01,Customer Payment,500.00\n"
            "2026-11-35,Office Supplies,-50.00\n"
        )

        results = IASAgent("business").run(path)

        self.assertEqual(
            results["summary"]["valid_transactions"], 1
        )
        self.assertEqual(len(results["potential_duplicates"]), 1)
        self.assertEqual(len(results["validation_errors"]), 1)

    def test_missing_file(self):
        """Verify missing input files are rejected."""
        agent = IASAgent("business")

        with self.assertRaises(FileNotFoundError):
            agent.run(self.folder / "missing.csv")

    def test_corrupt_memory(self):
        """Verify invalid memory cannot be silently accepted."""
        path = self.create_csv(
            "2026-11-01,Office Supplies,-50.00\n"
        )

        self.memory_path.write_text(
            "{invalid json",
            encoding="utf-8"
        )

        agent = IASAgent("personal", self.memory_path)

        with self.assertRaises(ValueError):
            agent.run(path)

    def test_missing_csv_columns(self):
        """Verify invalid CSV structures are rejected."""
        self.csv_path.write_text(
            "date,description\n"
            "2026-11-01,Office Supplies\n",
            encoding="utf-8"
        )

        with self.assertRaises(ValueError):
            IASAgent("business").run(self.csv_path)


if __name__ == "__main__":
    unittest.main()
