"""Validation tests for Phase 26 signal classification metadata.

Validates that all signals in brain/signals.json have complete
multi-dimensional classification metadata (category, plaintiff_lenses,
signal_type, hazard_or_signal) and that the classification is internally
consistent.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from do_uw.stages.analyze.signal_results import (
    SignalCategory,
    SignalResult,
    SignalStatus,
    HazardOrSignal,
    PlaintiffLens,
    SignalType,
)

CHECKS_PATH = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config" / "signals.json"
CLASSIFICATION_PATH = (
    Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config" / "signal_classification.json"
)


@pytest.fixture()
def checks() -> list[dict[str, object]]:
    """Load all signals from brain/signals.json."""
    with open(CHECKS_PATH) as f:
        data = json.load(f)
    return data["signals"]


@pytest.fixture()
def classification_config() -> dict[str, object]:
    """Load classification config."""
    with open(CLASSIFICATION_PATH) as f:
        return json.load(f)


class TestClassificationCompleteness:
    """Every check must have all 4 classification fields populated."""

    def test_all_checks_have_category(self, checks: list[dict[str, object]]) -> None:
        """Every check must have a non-empty category field."""
        missing = [c["id"] for c in checks if not c.get("category")]
        assert missing == [], f"Checks missing category: {missing}"

    def test_all_checks_have_plaintiff_lenses(
        self, checks: list[dict[str, object]]
    ) -> None:
        """Every check must have at least 1 plaintiff lens."""
        missing = [c["id"] for c in checks if not c.get("plaintiff_lenses")]
        assert missing == [], f"Checks missing plaintiff_lenses: {missing}"

    def test_all_checks_have_signal_type(
        self, checks: list[dict[str, object]]
    ) -> None:
        """Every check must have a non-empty signal_type field."""
        missing = [c["id"] for c in checks if not c.get("signal_type")]
        assert missing == [], f"Checks missing signal_type: {missing}"

    def test_all_checks_have_hazard_or_signal(
        self, checks: list[dict[str, object]]
    ) -> None:
        """Every check must have a non-empty hazard_or_signal field."""
        missing = [c["id"] for c in checks if not c.get("hazard_or_signal")]
        assert missing == [], f"Checks missing hazard_or_signal: {missing}"


class TestClassificationConsistency:
    """Classification values must use controlled vocabularies."""

    def test_valid_categories(self, checks: list[dict[str, object]]) -> None:
        """All categories must be valid SignalCategory values."""
        valid = {e.value for e in SignalCategory}
        invalid = [
            (c["id"], c["category"])
            for c in checks
            if c.get("category") not in valid
        ]
        assert invalid == [], f"Invalid categories: {invalid}"

    def test_valid_plaintiff_lenses(self, checks: list[dict[str, object]]) -> None:
        """All plaintiff lenses must be valid PlaintiffLens values."""
        valid = {e.value for e in PlaintiffLens}
        invalid = []
        for c in checks:
            for lens in c.get("plaintiff_lenses", []):
                if lens not in valid:
                    invalid.append((c["id"], lens))
        assert invalid == [], f"Invalid plaintiff lenses: {invalid}"

    def test_valid_signal_types(self, checks: list[dict[str, object]]) -> None:
        """All signal types must be valid SignalType values."""
        valid = {e.value for e in SignalType}
        invalid = [
            (c["id"], c["signal_type"])
            for c in checks
            if c.get("signal_type") not in valid
        ]
        assert invalid == [], f"Invalid signal types: {invalid}"

    def test_valid_hazard_or_signal(self, checks: list[dict[str, object]]) -> None:
        """All hazard_or_signal must be valid HazardOrSignal values."""
        valid = {e.value for e in HazardOrSignal}
        invalid = [
            (c["id"], c["hazard_or_signal"])
            for c in checks
            if c.get("hazard_or_signal") not in valid
        ]
        assert invalid == [], f"Invalid hazard_or_signal: {invalid}"


class TestDecisionDrivingChecks:
    """DECISION_DRIVING checks must have factor mappings."""

    def test_decision_driving_have_factors(
        self, checks: list[dict[str, object]]
    ) -> None:
        """DECISION_DRIVING checks that are EVALUATIVE_CHECK content_type
        must have non-empty factors (exception: MANUAL_ONLY execution mode).

        MANAGEMENT_DISPLAY and INFERENCE_PATTERN content types provide
        context that drives decisions but don't map to scoring factors.
        """
        violations = [
            c["id"]
            for c in checks
            if c.get("category") == "DECISION_DRIVING"
            and not c.get("factors")
            and c.get("execution_mode") != "MANUAL_ONLY"
            and c.get("content_type") == "EVALUATIVE_CHECK"
        ]
        assert violations == [], f"DECISION_DRIVING without factors: {violations}"


class TestDeprecatedChecks:
    """No deprecated check IDs should exist in signals.json."""

    def test_no_deprecated_checks(
        self,
        checks: list[dict[str, object]],
        classification_config: dict[str, object],
    ) -> None:
        """None of the deprecated IDs should exist in signals.json."""
        deprecated_ids = set(classification_config.get("deprecated_signal_ids", []))
        found = [c["id"] for c in checks if c["id"] in deprecated_ids]
        assert found == [], f"Deprecated checks still present: {found}"


class TestCategoryCounts:
    """Category distribution should be reasonable."""

    def test_category_counts(self, checks: list[dict[str, object]]) -> None:
        """Category counts should be within expected ranges."""
        from collections import Counter

        cats = Counter(c["category"] for c in checks)
        dd = cats.get("DECISION_DRIVING", 0)
        cd = cats.get("CONTEXT_DISPLAY", 0)
        total = len(checks)

        # Ranges accommodate actual classification (DD includes all factored checks)
        assert 100 <= dd <= 300, f"DECISION_DRIVING count {dd} outside range 100-300"
        assert 80 <= cd <= 300, f"CONTEXT_DISPLAY count {cd} outside range 80-300"
        assert 300 <= total <= 400, f"Total active count {total} outside range 300-400"


class TestPlaintiffLensCoverage:
    """All 7 plaintiff lenses must have at least one mapped check."""

    def test_plaintiff_lens_coverage(self, checks: list[dict[str, object]]) -> None:
        """All 7 plaintiff lenses must have at least 1 check mapped."""
        all_lenses: set[str] = set()
        for c in checks:
            for lens in c.get("plaintiff_lenses", []):
                all_lenses.add(lens)

        expected = {e.value for e in PlaintiffLens}
        missing = expected - all_lenses
        assert missing == set(), f"Plaintiff lenses with no checks: {missing}"


class TestSignalResultBackwardCompat:
    """Creating a SignalResult without new fields must succeed."""

    def test_signal_result_backward_compat(self) -> None:
        """SignalResult without new Phase 26 fields should use defaults."""
        result = SignalResult(
            signal_id="TEST.001",
            signal_name="Test Check",
            status=SignalStatus.CLEAR,
        )
        assert result.category == ""
        assert result.plaintiff_lenses == []
        assert result.signal_type == ""
        assert result.hazard_or_signal == ""
        assert result.temporal_classification == ""

    def test_signal_result_with_new_fields(self) -> None:
        """SignalResult with new Phase 26 fields should accept them."""
        result = SignalResult(
            signal_id="TEST.002",
            signal_name="Test Check 2",
            status=SignalStatus.TRIGGERED,
            category="DECISION_DRIVING",
            plaintiff_lenses=["SHAREHOLDERS", "REGULATORS"],
            signal_type="FORENSIC",
            hazard_or_signal="SIGNAL",
        )
        assert result.category == "DECISION_DRIVING"
        assert result.plaintiff_lenses == ["SHAREHOLDERS", "REGULATORS"]
        assert result.signal_type == "FORENSIC"
        assert result.hazard_or_signal == "SIGNAL"
