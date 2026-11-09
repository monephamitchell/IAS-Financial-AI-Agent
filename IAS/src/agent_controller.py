
"""
Immaculate Automation Solutions (IAS)
AI Financial Agent Controller

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone

Architecture: Planning -> Execution -> Review -> Reporting

Coordinates financial processing, categorization,
feedback memory, and financial safety checks.
"""

import argparse
import csv
from pathlib import Path

from financial_processor import process_financial_file
from transaction_categorizer import (
    REVIEW_CATEGORIES,
    TRANSFER_TERMS,
    categorize_transaction,
    categorize_with_memory,
    contains_term,
)


class IASAgent:
    """Coordinate the IAS financial automation workflow."""

    def __init__(self, profile="business", memory_path=None):
        if profile not in ("personal", "business"):
            raise ValueError("Invalid financial profile.")

        self.profile = profile
        self.memory_path = memory_path
        self.execution_log = []

    def log(self, message):
        """Record and display an agent action."""
        self.execution_log.append(message)
        print(f"[IAS] {message}")

    def create_plan(self):
        """Choose the sequence of financial tools."""

        plan = [
            "Import and validate financial transactions",
            "Calculate financial totals",
            "Categorize validated transactions",
            "Apply financial safety checks",
            "Generate financial report",
        ]

        self.log("Planning financial processing workflow")

        for step_number, step in enumerate(plan, start=1):
            self.log(f"Plan {step_number}: {step}")

        return plan

    def enforce_review(self, item):
        """
        Prevent remembered categories from bypassing
        financial review safeguards.
        """

        item = item.copy()
        description = item["description"]
        amount = item["amount"]
        category = item["category"]

        reasons = []

        if item["review_required"]:
            reasons.append(item["reason"])

        if category in REVIEW_CATEGORIES:
            reasons.append("Loan or debt classification requires review.")

        if any(
            contains_term(description, term)
            for term in TRANSFER_TERMS
        ):
            reasons.append("Verify transfer accounting treatment.")

        if contains_term(description, "loan"):
            reasons.append("Verify principal and interest treatment.")

        revenue_categories = {"Income", "Business Revenue"}

        if category in revenue_categories and amount < 0:
            reasons.append("Negative revenue requires review.")

        if (
            category not in revenue_categories
            and category not in ("Transfers", "Uncategorized")
            and amount > 0
        ):
            reasons.append("Positive amount in expense category.")

        # Compare with the default rules to preserve
        # underlying financial safety warnings.
        baseline = categorize_transaction(item, self.profile)

        if (
            baseline["review_required"]
            and baseline["category"] != "Uncategorized"
        ):
            reasons.append(
                "Default financial safety rule requires review."
            )

        if reasons:
            item["review_required"] = True
            item["reason"] = "; ".join(dict.fromkeys(reasons))

        return item

    def run(self, file_path):
        """Execute the complete IAS agent workflow."""

        self.execution_log = []
        self.create_plan()

        self.log("Starting financial data validation")
        processed = process_financial_file(file_path)

        transactions = processed["transactions"]
        summary = processed["summary"]

        self.log(
            f"Validated {len(transactions)} unique transactions"
        )

        if processed["errors"]:
            self.log(
                f"Flagged {len(processed['errors'])} invalid records"
            )

        if processed["duplicates"]:
            self.log(
                f"Flagged {len(processed['duplicates'])} potential duplicates"
            )

        self.log("Starting transaction categorization")

        if self.memory_path is not None:
            categorized = categorize_with_memory(
                transactions,
                self.profile,
                self.memory_path,
            )
            self.log("Applied approved feedback memory")
        else:
            categorized = [
                {
                    **categorize_transaction(item, self.profile),
                    "source": "default_rules",
                }
                for item in transactions
            ]
            self.log("Used default categorization rules")

        self.log("Running financial safety checks")

        categorized = [
            self.enforce_review(item)
            for item in categorized
        ]

        review_items = [
            item for item in categorized
            if item["review_required"]
        ]

        self.log(
            f"Identified {len(review_items)} transactions "
            "requiring human review"
        )

        self.log("Financial report generated")

        return {
            "profile": self.profile,
            "summary": summary,
            "transactions": categorized,
            "review_items": review_items,
            "validation_errors": processed["errors"],
            "potential_duplicates": processed["duplicates"],
            "execution_log": self.execution_log.copy(),
        }


def display_agent_report(results):
    """Display an understandable financial report."""

    print("\n" + "=" * 55)
    print("IMMACULATE AUTOMATION SOLUTIONS")
    print("IAS FINANCIAL AGENT REPORT")
    print("=" * 55)

    print(f"Financial Profile: {results['profile'].title()}")

    summary = results["summary"]

    print("\nFINANCIAL SUMMARY")
    print(f"Valid Transactions: {summary['valid_transactions']}")
    print(f"Invalid Transactions: {summary['invalid_transactions']}")
    print(f"Potential Duplicates: {summary['potential_duplicates']}")
    print(f"Total Income: ${summary['total_income']:,.2f}")
    print(f"Total Expenses: ${summary['total_expenses']:,.2f}")
    print(f"Net Cash Flow: ${summary['net_cash_flow']:,.2f}")

    print("\nTRANSACTION CATEGORIES")

    for item in results["transactions"]:
        status = (
            "REVIEW" if item["review_required"]
            else "MATCHED"
        )

        print(
            f"{item['description']}: "
            f"{item['category']} [{status}]"
        )

    print("\nREVIEW SUMMARY")
    print(
        f"Transactions requiring review: "
        f"{len(results['review_items'])}"
    )

    for item in results["review_items"]:
        print(f"- {item['description']}: {item['reason']}")

    print(
        f"Invalid records: {len(results['validation_errors'])}"
    )
    print(
        f"Potential duplicates: "
        f"{len(results['potential_duplicates'])}"
    )

    print("\nHuman approval is required before")
    print("acting on flagged financial transactions.")
    print("IAS does not move money or execute payments.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="IAS Financial Automation Agent"
    )

    parser.add_argument(
        "file",
        type=Path,
        help="Input financial CSV file"
    )

    parser.add_argument(
        "--profile",
        choices=["personal", "business"],
        default="business"
    )

    parser.add_argument(
        "--memory",
        type=Path,
        default=None,
        help="Optional local JSON memory file"
    )

    args = parser.parse_args()

    try:
        agent = IASAgent(
            profile=args.profile,
            memory_path=args.memory,
        )

        results = agent.run(args.file)
        display_agent_report(results)

    except (OSError, ValueError, csv.Error, KeyError) as error:
        print(f"\nIAS AGENT ERROR: {error}")
        print("Processing stopped. Review the input and retry.")
        raise SystemExit(1)
