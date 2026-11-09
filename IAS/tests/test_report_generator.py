
"""
Immaculate Automation Solutions (IAS)
Automated Reporting and Financial Edge-Case Tests

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone
"""

import csv
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from agent_controller import IASAgent
from report_generator import generate_reports


class TestIASReports(unittest.TestCase):

    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)

        self.root = Path(self.workspace.name)
        self.input_file = self.root / "transactions.csv"
        self.output_dir = self.root / "reports"

    def prepare(self, rows, profile="business"):
        """Run IAS on fictional data and export reports."""

        self.input_file.write_text(
            "date,description,amount\n" + rows,
            encoding="utf-8"
        )

        with redirect_stdout(io.StringIO()):
            results = IASAgent(profile).run(self.input_file)

        paths = generate_reports(results, self.output_dir)
        return results, paths

    @staticmethod
    def read_report(path):
        with path.open(
            newline="", encoding="utf-8-sig"
        ) as file:
            return list(csv.DictReader(file))

    def test_four_reports_generated(self):
        """All required CSV exports must exist."""

        _, paths = self.prepare(
            "2026-11-01,Customer Payment,500.00\n"
        )

        self.assertEqual(len(paths), 4)
        self.assertTrue(all(p.is_file() for p in paths.values()))

    def test_financial_totals(self):
        """Exported totals must match expected calculations."""

        _, paths = self.prepare(
            "2026-11-01,Customer Payment,850.00\n"
            "2026-11-02,Office Supplies,-125.50\n"
        )

        rows = self.read_report(paths["summary"])
        totals = {r["metric"]: r["value"] for r in rows}

        self.assertEqual(
            Decimal(totals["Total Income"]),
            Decimal("850.00")
        )
        self.assertEqual(
            Decimal(totals["Total Expenses"]),
            Decimal("125.50")
        )
        self.assertEqual(
            Decimal(totals["Net Cash Flow"]),
            Decimal("724.50")
        )

    def test_transaction_export(self):
        """Transaction exports preserve categories and amounts."""

        _, paths = self.prepare(
            "2026-11-01,Customer Payment,500.00\n"
            "2026-11-02,Office Supplies,-25.00\n"
        )

        rows = self.read_report(paths["transactions"])

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["category"], "Business Revenue")
        self.assertEqual(rows[1]["category"], "Office Supplies")
        self.assertEqual(rows[1]["amount"], "-25.00")

    def test_data_quality_report(self):
        """Invalid records and duplicates must be reported."""

        _, paths = self.prepare(
            "2026-11-01,Customer Payment,500.00\n"
            "2026-11-01,Customer Payment,500.00\n"
            "2026-11-35,Office Supplies,-30.00\n"
        )

        rows = self.read_report(paths["data_quality"])
        types = {r["issue_type"] for r in rows}

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            types,
            {"Invalid Record", "Potential Duplicate"}
        )

    def test_personal_review_queue(self):
        """Unknown transactions must appear in review queue."""

        _, paths = self.prepare(
            "2026-11-01,Equipment Purchase,-300.00\n",
            profile="personal"
        )

        rows = self.read_report(paths["review_queue"])

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["status"], "Pending Review"
        )

    def test_business_loan_requires_review(self):
        """Loan transactions require accounting review."""

        results, paths = self.prepare(
            "2026-11-01,Business Loan,-350.00\n"
        )

        self.assertEqual(len(results["review_items"]), 1)
        self.assertEqual(
            len(self.read_report(paths["review_queue"])),
            1
        )

    def test_transfer_requires_review(self):
        """Internal transfers must be flagged."""

        results, paths = self.prepare(
            "2026-11-01,Internal Transfer,-500.00\n"
        )

        self.assertEqual(
            results["transactions"][0]["category"],
            "Transfers"
        )
        self.assertTrue(
            results["transactions"][0]["review_required"]
        )
        self.assertEqual(
            len(self.read_report(paths["review_queue"])),
            1
        )

    def test_positive_expense_requires_review(self):
        """Unusual amount direction must be flagged."""

        results, _ = self.prepare(
            "2026-11-01,Office Supplies,50.00\n"
        )

        self.assertTrue(
            results["transactions"][0]["review_required"]
        )

    def test_spreadsheet_formula_protection(self):
        """Exported descriptions must not become formulas."""

        _, paths = self.prepare(
            "2026-11-01,=2+2,-10.00\n"
        )

        rows = self.read_report(paths["transactions"])

        self.assertEqual(
            rows[0]["description"],
            "'=2+2"
        )

    def test_header_only_file(self):
        """A CSV with no transactions must not crash."""

        results, paths = self.prepare("")

        self.assertEqual(
            results["summary"]["valid_transactions"], 0
        )
        self.assertEqual(
            results["summary"]["net_cash_flow"],
            Decimal("0")
        )
        self.assertEqual(
            len(self.read_report(paths["transactions"])), 0
        )

    def test_missing_input_file(self):
        """Missing financial files must raise an error."""

        with self.assertRaises(FileNotFoundError):
            IASAgent("business").run(
                self.root / "nonexistent.csv"
            )


if __name__ == "__main__":
    unittest.main()
