
"""
Immaculate Automation Solutions (IAS)
Feedback and Memory System

Developer: Monepha Mitchell
Course: ITAI 2376 - AI Agent Capstone

Stores user-approved transaction categorization
corrections and retrieves them for future use.

Uses JSON-based persistent memory and feedback scores.
"""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path


VALID_PROFILES = {"personal", "business"}


class FeedbackMemory:
    """Store and retrieve approved category corrections."""

    def __init__(self, memory_path):
        self.memory_path = Path(memory_path)
        self.memory = self._load_memory()

    def _load_memory(self):
        """Load existing memory or initialize a new one."""

        if not self.memory_path.exists():
            return {
                "personal": {},
                "business": {},
                "feedback": {
                    "approved": 0,
                    "rejected": 0
                }
            }

        try:
            with self.memory_path.open(
                "r", encoding="utf-8"
            ) as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(
                "IAS memory could not be loaded safely."
            ) from error

        if not isinstance(data, dict):
            raise ValueError("Invalid IAS memory format.")

        for profile in VALID_PROFILES:
            if not isinstance(data.get(profile), dict):
                raise ValueError(
                    f"Invalid memory for {profile} profile."
                )

        feedback = data.get("feedback")
        if not isinstance(feedback, dict):
            raise ValueError("Invalid feedback data.")

        for key in ("approved", "rejected"):
            value = feedback.get(key)
            if type(value) is not int or value < 0:
                raise ValueError("Invalid feedback counter.")

        return data

    def _save_memory(self):
        """Save memory using an atomic file replacement."""

        self.memory_path.parent.mkdir(
            parents=True, exist_ok=True
        )

        temporary_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.memory_path.parent,
                prefix=".ias_memory_",
                suffix=".tmp",
                delete=False
            ) as file:
                temporary_path = Path(file.name)
                json.dump(self.memory, file, indent=2)
                file.flush()
                os.fsync(file.fileno())

            os.replace(temporary_path, self.memory_path)

        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    @staticmethod
    def _validate_profile(profile):
        if profile not in VALID_PROFILES:
            raise ValueError(
                "Profile must be 'personal' or 'business'."
            )

    @staticmethod
    def _normalize_description(description):
        if not isinstance(description, str):
            raise ValueError("Description must be text.")

        normalized = " ".join(
            description.casefold().split()
        )

        if not normalized or len(normalized) > 200:
            raise ValueError(
                "Description must contain 1-200 characters."
            )

        return normalized

    def get_category(self, description, profile):
        """Retrieve a previously approved category."""

        self._validate_profile(profile)
        key = self._normalize_description(description)

        record = self.memory[profile].get(key)

        if record is None:
            return None

        return record["category"]

    def record_feedback(
        self,
        description,
        profile,
        category,
        approved
    ):
        """
        Record explicit user feedback.

        approved=True stores an approved category.
        approved=False records rejection only.
        """

        self._validate_profile(profile)
        key = self._normalize_description(description)

        if type(approved) is not bool:
            raise ValueError("Approval must be a boolean.")

        if not isinstance(category, str):
            raise ValueError("Category must be text.")

        category = category.strip()

        if not category or len(category) > 80:
            raise ValueError(
                "Category must contain 1-80 characters."
            )

        if approved:
            self.memory[profile][key] = {
                "category": category,
                "updated_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }

            self.memory["feedback"]["approved"] += 1
            reward = 1

        else:
            self.memory["feedback"]["rejected"] += 1
            reward = 0

        self._save_memory()

        return {
            "description": key,
            "profile": profile,
            "approved": approved,
            "reward": reward
        }

    def apply_memory(self, transaction, profile):
        """
        Apply a previous correction if one exists.

        Returns None when no approved correction exists.
        """

        category = self.get_category(
            transaction["description"],
            profile
        )

        if category is None:
            return None

        return {
            **transaction,
            "profile": profile,
            "category": category,
            "confidence": 1.0,
            "review_required": False,
            "reason": "Previously approved user correction.",
            "source": "memory"
        }

    def get_feedback_summary(self):
        """Report feedback statistics."""

        feedback = self.memory["feedback"]
        approved = feedback["approved"]
        rejected = feedback["rejected"]
        total = approved + rejected

        return {
            "total_feedback": total,
            "approved": approved,
            "rejected": rejected,
            "approval_rate": (
                approved / total if total else 0.0
            ),
            "personal_rules": len(
                self.memory["personal"]
            ),
            "business_rules": len(
                self.memory["business"]
            )
        }
