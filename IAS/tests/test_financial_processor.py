
"""
IAS Financial AI Agent
Automated Financial Processor Tests

Developer: Monepha Mitchell
Course: ITAI 2376
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Locate our IAS source code
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from financial_processor import process_financial_file


class TestFinancialProcessor(unittest.TestCase):

    def run_processor(self, csv_content):
        """Create a temporary CSV and process it."""

        with tempfile.TemporaryDirectory() as folder:
            file_path = Path(folder) / "transactions.csv"
            file_path.write_text(
                csv_content,
                encoding="utf-8"
            )
            return process_financial_file(file_path)

    def test_valid_transactions(self):
        """Confirm valid transactions are accepted."""

        results = self.run_processor(
            "date,description,amount\n"
            "2026-11-01,Office Supplies,-100.00\n"
            "2026-11-02,Customer Payment,500.00\n"
        )

        self.assertEqual(
            results["summary"]["valid_transactions"], 2
        )

    def test_income_and_expenses(self):
        """Verify financial calculations."""

        results = self.run_processor(
            "date,description,amount\n"
            "2026-11-01,Revenue,1000.00\n"
            "2026-11-02,Rent,-300.00\n"
        )

        summary = results["summary"]

        self.assertEqual(summary["total_income"], 1000)
        self.assertEqual(summary["total_expenses"], 300)
        self.assertEqual(summary["net_cash_flow"], 700)

    def test_invalid_date(self):
        """Detect invalid transaction dates."""

        results = self.run_processor(
            "date,description,amount\n"
            "2026-11-32,Office Supplies,-50.00\n"
        )

        self.assertEqual(
            results["summary"]["invalid_transactions"], 1
        )

    def test_missing_description(self):
        """Reject missing transaction descriptions."""

        results = self.run_processor(
            "date,description,amount\n"
            "2026-11-01,,-75.00\n"
        )

        self.assertEqual(
            results["summary"]["invalid_transactions"], 1
        )

    def test_duplicate_detection(self):
        """Flag identical transactions for review."""

        results = self.run_processor(
            "date,description,amount\n"
            "2026-11-01,Office Supplies,-100.00\n"
            "2026-11-01,Office Supplies,-100.00\n"
        )

        self.assertEqual(
            results["summary"]["potential_duplicates"], 1
        )
        self.assertEqual(
            results["summary"]["valid_transactions"], 1
        )

    def test_missing_columns(self):
        """Reject files without required columns."""

        with self.assertRaises(ValueError):
            self.run_processor(
                "date,description\n"
                "2026-11-01,Office Supplies\n"
            )

    def test_invalid_amount(self):
        """Reject nonnumeric transaction amounts."""

        results = self.run_processor(
            "date,description,amount\n"
            "2026-11-01,Office Supplies,abc\n"
        )

        self.assertEqual(
            results["summary"]["invalid_transactions"], 1
        )


if __name__ == "__main__":
    unittest.main()
