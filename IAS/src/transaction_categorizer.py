"""
Immaculate Automation Solutions (IAS)
Transaction Categorization Engine

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone

Supports personal and business financial profiles.
Version 1: Rule-based categorization with human review.
"""

import re
from collections import Counter


PERSONAL_RULES = {
    "Housing": [
        "rent", "mortgage", "apartment lease"
    ],
    "Utilities": [
        "electricity", "electric bill", "water bill",
        "internet service", "utility bill", "natural gas"
    ],
    "Subscriptions": [
        "netflix", "spotify", "hulu",
        "streaming", "subscription", "membership"
    ],
    "Auto Loans": [
        "car loan", "auto loan", "vehicle finance"
    ],
    "Insurance": [
        "insurance", "geico", "progressive",
        "state farm"
    ],
    "Transportation": [
        "gas station", "fuel", "parking", "toll", "uber"
    ],
    "Groceries": [
        "grocery", "supermarket", "kroger",
        "heb", "h-e-b", "aldi"
    ],
    "Dining": [
        "restaurant", "takeout", "doordash", "dining"
    ],
    "Healthcare": [
        "pharmacy", "medical", "doctor", "dental"
    ],
    "Debt Payments": [
        "credit card payment", "personal loan"
    ],
    "Shopping": [
        "clothing", "retail purchase", "shopping"
    ],
    "Entertainment": [
        "movie theater", "concert", "recreation"
    ],
    "Income": [
        "salary", "paycheck", "direct deposit payroll",
        "customer payment", "consulting revenue"
    ],
}

BUSINESS_RULES = {
    "Business Revenue": [
        "customer payment", "client payment",
        "sales revenue", "consulting revenue",
        "service income"
    ],
    "Payroll": [
        "employee wages", "payroll expense",
        "staff salary"
    ],
    "Office Supplies": [
        "office supplies", "printer paper",
        "stationery"
    ],
    "Utilities": [
        "internet service", "electricity",
        "water bill", "utility bill"
    ],
    "Software & Subscriptions": [
        "software subscription", "cloud hosting",
        "accounting software", "saas"
    ],
    "Business Insurance": [
        "business insurance", "liability insurance",
        "commercial auto insurance"
    ],
    "Rent & Facilities": [
        "office rent", "facility maintenance",
        "commercial lease"
    ],
    "Professional Services": [
        "accounting services", "legal services",
        "consulting fees"
    ],
    "Advertising & Marketing": [
        "advertising", "marketing campaign",
        "google ads"
    ],
    "Equipment": [
        "equipment purchase", "computer equipment",
        "machinery"
    ],
    "Travel & Transportation": [
        "business travel", "airfare",
        "business parking"
    ],
    "Loan Payments": [
        "business loan", "loan repayment"
    ],
    "Taxes & Fees": [
        "business tax", "license fee", "permit fee"
    ],
    "Bank & Processing Fees": [
        "bank fee", "processing fee",
        "merchant fee"
    ],
}

# These descriptions may require special accounting treatment.
REVIEW_CATEGORIES = {
    "Auto Loans",
    "Debt Payments",
    "Loan Payments",
}

TRANSFER_TERMS = [
    "account transfer",
    "internal transfer",
    "savings transfer",
    "transfer between accounts",
]


def contains_term(description, term):
    """Match a complete word or phrase, ignoring case."""
    pattern = (
        r"(?<!\w)" + re.escape(term) + r"(?!\w)"
    )
    return bool(re.search(pattern, description, re.IGNORECASE))


def categorize_transaction(transaction, profile="business"):
    """
    Suggest a category for a validated transaction.

    Confidence is a rule-match indicator, not a
    statistically calibrated probability.
    """

    profile = profile.strip().lower()

    if profile not in ("personal", "business"):
        raise ValueError(
            "Profile must be 'personal' or 'business'."
        )

    description = transaction["description"].strip()
    amount = transaction["amount"]

    if any(
        contains_term(description, term)
        for term in TRANSFER_TERMS
    ):
        return {
            **transaction,
            "profile": profile,
            "category": "Transfers",
            "confidence": 1.0,
            "review_required": True,
            "reason": "Verify transfer and accounting treatment.",
        }

    rules = (
        PERSONAL_RULES
        if profile == "personal"
        else BUSINESS_RULES
    )

    matches = []

    for category, terms in rules.items():
        if any(
            contains_term(description, term)
            for term in terms
        ):
            matches.append(category)

    if len(matches) == 0:
        category = "Uncategorized"
        reason = "No matching categorization rule."
        confidence = 0.0
        review_required = True

    elif len(matches) > 1:
        category = "Uncategorized"
        reason = (
            "Multiple possible categories: "
            + ", ".join(matches)
        )
        confidence = 0.0
        review_required = True

    else:
        category = matches[0]
        confidence = 1.0
        review_required = category in REVIEW_CATEGORIES

        reason = (
            "Special accounting review required."
            if review_required
            else "Matched a category rule."
        )

        # Do not classify negative amounts as revenue
        # or positive amounts as ordinary expenses
        # without human review.
        revenue_categories = {
            "Income", "Business Revenue"
        }

        if (
            (category in revenue_categories and amount < 0)
            or
            (category not in revenue_categories and amount > 0)
        ):
            review_required = True
            reason = "Unusual amount direction; verify transaction."

    return {
        **transaction,
        "profile": profile,
        "category": category,
        "confidence": confidence,
        "review_required": review_required,
        "reason": reason,
    }


def categorize_transactions(transactions, profile="business"):
    """Categorize a collection of valid transactions."""

    results = [
        categorize_transaction(item, profile)
        for item in transactions
    ]

    counts = Counter(
        item["category"] for item in results
    )

    review_count = sum(
        item["review_required"] for item in results
    )

    return {
        "transactions": results,
        "category_counts": dict(counts),
        "total_categorized": len(results),
        "review_required": review_count,
    }


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from financial_processor import process_financial_file

    parser = argparse.ArgumentParser(
        description="IAS Transaction Categorizer"
    )

    parser.add_argument("file", type=Path)
    parser.add_argument(
        "--profile",
        choices=["personal", "business"],
        default="business"
    )

    args = parser.parse_args()

    processed = process_financial_file(args.file)

    results = categorize_transactions(
        processed["transactions"],
        profile=args.profile
    )

    print(f"\nIAS {args.profile.upper()} CATEGORIZATION REPORT")
    print("-" * 55)

    for item in results["transactions"]:
        status = (
            "REVIEW" if item["review_required"]
            else "MATCHED"
        )
        print(
            f"{item['description']:<26} "
            f"{item['category']:<26} {status}"
        )

    print("\nCategory counts:", results["category_counts"])
    print("Transactions processed:", results["total_categorized"])
    print("Requiring review:", results["review_required"])


# --------------------------------------------------
# IAS MEMORY-INTEGRATED CATEGORIZATION
# --------------------------------------------------

from feedback_memory import FeedbackMemory


def categorize_with_memory(
    transactions,
    profile,
    memory_path
):
    """
    Categorize transactions using approved memory
    before falling back to default category rules.
    """

    memory = FeedbackMemory(memory_path)
    categorized = []

    for transaction in transactions:

        remembered = memory.apply_memory(
            transaction, profile
        )

        if remembered is not None:
            result = remembered.copy()

            # Financially sensitive categories still
            # require human review.
            if result["category"] in REVIEW_CATEGORIES:
                result["review_required"] = True
                result["reason"] = (
                    "Remembered category requires "
                    "financial review."
                )

        else:
            result = categorize_transaction(
                transaction, profile
            )
            result["source"] = "default_rules"

        categorized.append(result)

    return categorized
