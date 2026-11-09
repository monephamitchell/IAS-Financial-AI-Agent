
"""
Immaculate Automation Solutions (IAS)
Feedback Learning Evaluation

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone

Compares IAS transaction classification accuracy
before and after user-approved feedback.

Uses synthetic data and a temporary memory file.
"""

import csv
import sys
import tempfile
from pathlib import Path

# Import the IAS application modules.
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src")
)

from agent_controller import IASAgent
from feedback_memory import FeedbackMemory


# Synthetic evaluation records with known correct labels.
# These evaluation records are separate from the
# feedback examples, but some descriptions repeat.

EVALUATION_DATA = [
    ("2026-11-01", "Office Supplies", "-45.00",
     "Household Supplies"),
    ("2026-11-02", "Customer Payment", "900.00",
     "Income"),
    ("2026-11-03", "Internet Service", "-85.00",
     "Utilities"),
    ("2026-11-04", "Software Subscription", "-19.99",
     "Subscriptions"),
    ("2026-11-05", "Pet Food", "-42.50",
     "Pet Supplies"),
    ("2026-11-06", "Consulting Revenue", "450.00",
     "Income"),
    ("2026-11-07", "Netflix", "-17.99",
     "Subscriptions"),
    ("2026-11-08", "Office Supplies", "-30.00",
     "Household Supplies"),
]


def create_evaluation_csv(file_path):
    """Write synthetic transactions to a CSV file."""

    with file_path.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.writer(file)
        writer.writerow(["date", "description", "amount"])

        for date, description, amount, category in EVALUATION_DATA:
            writer.writerow([date, description, amount])


def evaluate(results, expected_data):
    """Compare the agent's categories to known labels."""

    transactions = results["transactions"]

    if len(transactions) != len(expected_data):
        raise AssertionError(
            "Transaction count differs from evaluation data."
        )

    correct = 0
    comparisons = []

    for actual, expected in zip(transactions, expected_data):
        expected_category = expected[3]
        predicted_category = actual["category"]

        is_correct = predicted_category == expected_category

        if is_correct:
            correct += 1

        comparisons.append({
            "description": actual["description"],
            "expected": expected_category,
            "predicted": predicted_category,
            "correct": is_correct,
        })

    total = len(expected_data)

    return {
        "correct": correct,
        "total": total,
        "accuracy": correct / total if total else 0.0,
        "review_count": len(results["review_items"]),
        "comparisons": comparisons,
    }


def print_results(title, evaluation):
    """Display readable evaluation findings."""

    print("\n" + "=" * 55)
    print(title)
    print("=" * 55)

    for item in evaluation["comparisons"]:
        status = "CORRECT" if item["correct"] else "INCORRECT"

        print(
            f"{item['description']}: "
            f"{item['predicted']} "
            f"(Expected: {item['expected']}) "
            f"[{status}]"
        )

    print(
        f"\nCorrect classifications: "
        f"{evaluation['correct']}/{evaluation['total']}"
    )

    print(
        f"Accuracy: {evaluation['accuracy']:.1%}"
    )

    print(
        f"Transactions requiring review: "
        f"{evaluation['review_count']}"
    )


def run_experiment():
    """Measure categorization before and after feedback."""

    with tempfile.TemporaryDirectory() as folder:

        folder = Path(folder)
        csv_path = folder / "IAS_evaluation.csv"
        memory_path = folder / "IAS_feedback.json"

        create_evaluation_csv(csv_path)

        # Step 1: Evaluate without learned corrections.
        baseline_agent = IASAgent(profile="personal")
        baseline_results = baseline_agent.run(csv_path)

        before = evaluate(
            baseline_results,
            EVALUATION_DATA
        )

        print_results("BEFORE FEEDBACK", before)

        # Step 2: Simulate approved feedback from
        # earlier transactions with matching descriptions.
        memory = FeedbackMemory(memory_path)

        feedback_examples = [
            ("Office Supplies", "Household Supplies"),
            ("Pet Food", "Pet Supplies"),
        ]

        for description, category in feedback_examples:
            memory.record_feedback(
                description=description,
                profile="personal",
                category=category,
                approved=True
            )

        # Step 3: Run the evaluation transactions again,
        # now using stored corrections.
        improved_agent = IASAgent(
            profile="personal",
            memory_path=memory_path
        )

        improved_results = improved_agent.run(csv_path)

        after = evaluate(
            improved_results,
            EVALUATION_DATA
        )

        print_results("AFTER FEEDBACK", after)

        # Step 4: Calculate measurable improvement.
        change = (
            after["accuracy"] - before["accuracy"]
        ) * 100

        print("\n" + "=" * 55)
        print("IAS FEEDBACK EVALUATION SUMMARY")
        print("=" * 55)

        print(f"Baseline accuracy: {before['accuracy']:.1%}")
        print(f"After feedback: {after['accuracy']:.1%}")
        print(f"Improvement: {change:.1f} percentage points")

        print(
            f"Reviews before feedback: "
            f"{before['review_count']}"
        )

        print(
            f"Reviews after feedback: "
            f"{after['review_count']}"
        )

        print(
            "Feedback examples recorded:",
            len(feedback_examples)
        )

        # Verify the expected controlled experiment.
        assert before["correct"] == 5
        assert after["correct"] == 8
        assert before["review_count"] == 3
        assert after["review_count"] == 0

        print("\nIAS FEEDBACK EVALUATION PASSED")
        print(
            "Note: Improvement is demonstrated for "
            "previously corrected descriptions only."
        )


if __name__ == "__main__":
    run_experiment()
