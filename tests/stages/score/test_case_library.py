"""Tests for case_library.yaml validation and integrity.

Validates that the 20-case seed library loads correctly, all entries
conform to CaseLibraryEntry Pydantic schema, and confidence tiers
have the required minimum signal profiles.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from do_uw.models.patterns import CaseLibraryEntry

# Path to the case library YAML
CASE_LIBRARY_PATH = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "do_uw"
    / "brain"
    / "framework"
    / "case_library.yaml"
)

# Valid claim types from case_library_design.yaml
VALID_CLAIM_TYPES = {
    "securities_fraud_10b5",
    "section_11_offering",
    "derivative_caremark",
    "derivative_waste",
    "merger_objection",
    "regulatory_enforcement",
    "erisa",
    "whistleblower_retaliation",
    "other",
}


@pytest.fixture(scope="module")
def case_library() -> list[dict]:
    """Load case library YAML."""
    raw = yaml.safe_load(CASE_LIBRARY_PATH.read_text())
    return raw["cases"]


class TestCaseLibraryLoads:
    """Tests for YAML loading and basic structure."""

    def test_yaml_loads_successfully(self, case_library: list[dict]) -> None:
        """Case library YAML loads without error."""
        assert isinstance(case_library, list)

    def test_has_20_entries(self, case_library: list[dict]) -> None:
        """Case library has exactly 20 seed cases."""
        assert len(case_library) == 20

    def test_unique_case_ids(self, case_library: list[dict]) -> None:
        """All case_id values are unique."""
        ids = [c["case_id"] for c in case_library]
        assert len(ids) == len(set(ids))


class TestCaseLibrarySchema:
    """Tests for Pydantic schema validation."""

    def test_all_entries_validate(self, case_library: list[dict]) -> None:
        """Every entry validates against CaseLibraryEntry."""
        for entry in case_library:
            parsed = CaseLibraryEntry.model_validate(entry)
            assert parsed.case_id == entry["case_id"]

    def test_all_claim_types_valid(self, case_library: list[dict]) -> None:
        """All claim_types are in the valid enum set."""
        for entry in case_library:
            assert entry["claim_type"] in VALID_CLAIM_TYPES, (
                f"{entry['case_id']} has invalid claim_type: {entry['claim_type']}"
            )

    def test_signal_profile_has_valid_statuses(
        self, case_library: list[dict]
    ) -> None:
        """Signal profile status values are RED/YELLOW/CLEAR/UNKNOWN."""
        valid_statuses = {"RED", "YELLOW", "CLEAR", "UNKNOWN"}
        for entry in case_library:
            for signal_id, status in entry["signal_profile"].items():
                assert status in valid_statuses, (
                    f"{entry['case_id']}.{signal_id} has invalid status: {status}"
                )


class TestCaseLibraryConfidence:
    """Tests for confidence tier requirements."""

    def test_six_high_confidence_entries(self, case_library: list[dict]) -> None:
        """At least 6 entries have signal_profile_confidence=HIGH."""
        high_entries = [
            c for c in case_library
            if c["signal_profile_confidence"] == "HIGH"
        ]
        assert len(high_entries) >= 6

    def test_high_confidence_have_50_plus_signals(
        self, case_library: list[dict]
    ) -> None:
        """HIGH confidence entries have 50+ signals in their profile."""
        for entry in case_library:
            if entry["signal_profile_confidence"] == "HIGH":
                signal_count = len(entry["signal_profile"])
                assert signal_count >= 50, (
                    f"{entry['case_id']} is HIGH confidence but has only "
                    f"{signal_count} signals (need 50+)"
                )

    def test_medium_confidence_entries(self, case_library: list[dict]) -> None:
        """At least 14 entries have signal_profile_confidence=MEDIUM."""
        medium_entries = [
            c for c in case_library
            if c["signal_profile_confidence"] == "MEDIUM"
        ]
        assert len(medium_entries) >= 14

    def test_medium_confidence_have_10_plus_signals(
        self, case_library: list[dict]
    ) -> None:
        """MEDIUM confidence entries have 10+ signals in their profile."""
        for entry in case_library:
            if entry["signal_profile_confidence"] == "MEDIUM":
                signal_count = len(entry["signal_profile"])
                assert signal_count >= 10, (
                    f"{entry['case_id']} is MEDIUM confidence but has only "
                    f"{signal_count} signals (need 10+)"
                )


class TestCaseLibraryOutcomes:
    """Tests for outcome data integrity."""

    def test_all_have_outcome(self, case_library: list[dict]) -> None:
        """Every entry has an outcome dict."""
        for entry in case_library:
            assert "outcome" in entry
            assert isinstance(entry["outcome"], dict)

    def test_settlements_have_amount(self, case_library: list[dict]) -> None:
        """Settlement outcomes have a settlement_amount."""
        for entry in case_library:
            if entry["outcome"].get("type") == "settlement":
                assert entry["outcome"].get("settlement_amount") is not None, (
                    f"{entry['case_id']} is settlement but missing settlement_amount"
                )
