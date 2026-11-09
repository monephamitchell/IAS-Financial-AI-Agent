
"""
Immaculate Automation Solutions (IAS)
Financial Data Processor

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone

Purpose:
Import, validate, and summarize financial transactions
from CSV files.

This module is part of the IAS Financial AI Agent.
"""

import csv
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED_COLUMNS = {"date", "description", "amount"}


def validate_transaction(row, row_number):
    """Validate one financial transaction."""

    errors = []

    transaction_date = (row.get("date") or "").strip()
    description = (row.get("description") or "").strip()
    amount_text = (row.get("amount") or "").strip()

    try:
        date.fromisoformat(transaction_date)
    except ValueError:
        errors.append("Invalid date. Use YYYY-MM-DD.")

    if not description:
        errors.append("Transaction description is missing.")

    try:
        amount = Decimal(amount_text)
        if not amount.is_finite():
            errors.append("Amount must be a finite number.")
    except InvalidOperation:
        amount = None
        errors.append("Invalid or missing transaction amount.")

    if errors:
        return None, {
            "row": row_number,
            "errors": errors,
        }

    return {
        "date": transaction_date,
        "description": description,
        "amount": amount,
    }, None


def process_financial_file(file_path):
    """Import, validate, and summarize a CSV file."""

    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Financial file not found: {file_path}"
        )

    valid_transactions = []
    errors = []
    duplicates = []
    seen_transactions = set()

    with file_path.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:

        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            raise ValueError("CSV file is empty.")

        columns = {
            column.strip().lower()
            for column in reader.fieldnames
            if column is not None
        }

        missing_columns = REQUIRED_COLUMNS - columns

        if missing_columns:
            raise ValueError(
                f"Missing required columns: "
                f"{sorted(missing_columns)}"
            )

        for row_number, raw_row in enumerate(reader, start=2):

            row = {
                key.strip().lower(): value
                for key, value in raw_row.items()
                if key is not None
            }

            transaction, error = validate_transaction(
                row, row_number
            )

            if error:
                errors.append(error)
                continue

            transaction_key = (
                transaction["date"],
                transaction["description"].casefold(),
                transaction["amount"],
            )

            if transaction_key in seen_transactions:
                duplicates.append({
                    "row": row_number,
                    "transaction": transaction,
                })
                continue

            seen_transactions.add(transaction_key)
            valid_transactions.append(transaction)

    income = sum(
        (
            item["amount"]
            for item in valid_transactions
            if item["amount"] > 0
        ),
        Decimal("0"),
    )

    expenses = sum(
        (
            -item["amount"]
            for item in valid_transactions
            if item["amount"] < 0
        ),
        Decimal("0"),
    )

    summary = {
        "valid_transactions": len(valid_transactions),
        "invalid_transactions": len(errors),
        "potential_duplicates": len(duplicates),
        "total_income": income,
        "total_expenses": expenses,
        "net_cash_flow": income - expenses,
    }

    return {
        "transactions": valid_transactions,
        "errors": errors,
        "duplicates": duplicates,
        "summary": summary,
    }


def display_summary(results):
    """Display financial processing results."""

    print("\nIAS FINANCIAL PROCESSING REPORT")
    print("-" * 40)

    for key, value in results["summary"].items():
        label = key.replace("_", " ").title()

        if isinstance(value, Decimal):
            print(f"{label}: ${value:,.2f}")
        else:
            print(f"{label}: {value}")

    if results["errors"]:
        print("\nVALIDATION ERRORS")
        for error in results["errors"]:
            print(f"Row {error['row']}: {error['errors']}")

    if results["duplicates"]:
        print("\nPOTENTIAL DUPLICATES")
        for duplicate in results["duplicates"]:
            print(f"Row {duplicate['row']}: Review required")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="IAS Financial CSV Processor"
    )
    parser.add_argument(
        "file",
        help="Path to a financial CSV file"
    )
    args = parser.parse_args()

    try:
        results = process_financial_file(args.file)
        display_summary(results)
    except (OSError, ValueError, csv.Error) as error:
        print(f"IAS processing error: {error}")
        raise SystemExit(1)
