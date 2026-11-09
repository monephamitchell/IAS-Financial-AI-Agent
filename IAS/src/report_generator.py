"""
Immaculate Automation Solutions (IAS)
Financial Report Generator

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone

Exports financial summaries, categorized transactions,
human review queues, and validation findings to CSV.
"""

import csv
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path


def safe_csv_value(value):
    """
    Convert values safely for spreadsheet exports.

    Prevent transaction text from being interpreted
    as spreadsheet formulas when CSV files are opened.
    """
    if value is None:
        return ""

    if isinstance(value, Decimal):
        return f"{value:.2f}"

    text = str(value)

    if isinstance(value, str) and (
        text.lstrip().startswith(("=", "+", "-", "@"))
        or text.startswith(("\t", "\r", "\n"))
    ):
        return "'" + text

    return text


def write_csv(file_path, headers, rows):
    """Write CSV records with consistent formatting."""

    with Path(file_path).open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=headers,
            extrasaction="ignore"
        )

        writer.writeheader()

        for row in rows:
            writer.writerow({
                header: safe_csv_value(row.get(header))
                for header in headers
            })


def generate_reports(results, output_directory):
    """
    Generate four CSV reports from IAS agent results.

    The results dictionary comes from IASAgent.run().
    """

    output_directory = Path(output_directory)

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    profile = results["profile"]
    summary = results["summary"]
    transactions = results["transactions"]

    timestamp = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d_%H%M%S_%f")

    prefix = f"IAS_{profile}_{timestamp}"

    # -----------------------------------------
    # Report 1: Financial Summary
    # -----------------------------------------

    summary_path = (
        output_directory / f"{prefix}_summary.csv"
    )

    summary_rows = [
        {"metric": "Financial Profile", "value": profile},
        {
            "metric": "Valid Transactions",
            "value": summary["valid_transactions"]
        },
        {
            "metric": "Invalid Transactions",
            "value": summary["invalid_transactions"]
        },
        {
            "metric": "Potential Duplicates",
            "value": summary["potential_duplicates"]
        },
        {
            "metric": "Total Income",
            "value": summary["total_income"]
        },
        {
            "metric": "Total Expenses",
            "value": summary["total_expenses"]
        },
        {
            "metric": "Net Cash Flow",
            "value": summary["net_cash_flow"]
        },
        {
            "metric": "Transactions Requiring Review",
            "value": len(results["review_items"])
        }
    ]

    write_csv(
        summary_path,
        ["metric", "value"],
        summary_rows
    )

    # -----------------------------------------
    # Report 2: Categorized Transactions
    # -----------------------------------------

    transactions_path = (
        output_directory / f"{prefix}_transactions.csv"
    )

    transaction_rows = []

    for item in transactions:
        transaction_rows.append({
            "date": item["date"],
            "description": item["description"],
            "amount": item["amount"],
            "profile": item["profile"],
            "category": item["category"],
            "source": item.get("source", ""),
            "review_required": item["review_required"],
            "review_reason": item["reason"]
        })

    transaction_headers = [
        "date",
        "description",
        "amount",
        "profile",
        "category",
        "source",
        "review_required",
        "review_reason"
    ]

    write_csv(
        transactions_path,
        transaction_headers,
        transaction_rows
    )

    # -----------------------------------------
    # Report 3: Human Review Queue
    # -----------------------------------------

    review_path = (
        output_directory / f"{prefix}_review_queue.csv"
    )

    review_rows = []

    for item in results["review_items"]:
        review_rows.append({
            "date": item["date"],
            "description": item["description"],
            "amount": item["amount"],
            "suggested_category": item["category"],
            "reason": item["reason"],
            "status": "Pending Review"
        })

    write_csv(
        review_path,
        [
            "date",
            "description",
            "amount",
            "suggested_category",
            "reason",
            "status"
        ],
        review_rows
    )

    # -----------------------------------------
    # Report 4: Data Quality Findings
    # -----------------------------------------

    quality_path = (
        output_directory / f"{prefix}_data_quality.csv"
    )

    quality_rows = []

    for error in results["validation_errors"]:
        quality_rows.append({
            "issue_type": "Invalid Record",
            "source_row": error["row"],
            "description": "",
            "amount": "",
            "details": "; ".join(error["errors"])
        })

    for duplicate in results["potential_duplicates"]:
        transaction = duplicate["transaction"]

        quality_rows.append({
            "issue_type": "Potential Duplicate",
            "source_row": duplicate["row"],
            "description": transaction["description"],
            "amount": transaction["amount"],
            "details": "Possible duplicate; verify manually."
        })

    write_csv(
        quality_path,
        [
            "issue_type",
            "source_row",
            "description",
            "amount",
            "details"
        ],
        quality_rows
    )

    return {
        "summary": summary_path,
        "transactions": transactions_path,
        "review_queue": review_path,
        "data_quality": quality_path
    }


if __name__ == "__main__":
    import argparse
    from agent_controller import IASAgent

    parser = argparse.ArgumentParser(
        description="IAS Financial Report Generator"
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
        "--output",
        type=Path,
        default=Path("IAS/reports")
    )

    args = parser.parse_args()

    try:
        agent = IASAgent(profile=args.profile)

        results = agent.run(args.file)

        reports = generate_reports(
            results,
            args.output
        )

        print("\nIAS REPORT EXPORT COMPLETE")

        for report_type, path in reports.items():
            print(f"{report_type}: {path}")

    except (OSError, ValueError, csv.Error) as error:
        print(f"IAS report generation failed: {error}")
        raise SystemExit(1)
