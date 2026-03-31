"""CI gate: validate all 514 signals against complete v7.0 schema.

This test suite is the enforcement layer for the RAP taxonomy (Phase 103).
It ensures every signal in brain/signals/**/*.yaml has all required v7.0
fields: rap_class, rap_subcategory, epistemology, evaluation.mechanism.

If a signal is added without these fields, CI will fail immediately.

Phase 103-04: Schema Foundation capstone.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from do_uw.brain.brain_signal_schema import BrainSignalEntry

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SIGNALS_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "do_uw" / "brain" / "signals"
FRAMEWORK_DIR = Path(__file__).resolve().parent.parent.parent / "src" / "do_uw" / "brain" / "framework"

VALID_RAP_CLASSES = {"host", "agent", "environment"}
VALID_MECHANISMS = {"threshold", "peer_comparison", "trend", "conjunction", "absence", "contextual"}

# Minimum signal count -- prevents accidental deletion
MIN_SIGNAL_COUNT = 562

# Distribution sanity bands (wide enough for growth, catch catastrophic errors)
# Updated Phase 110: +48 signals (8 conjunction + 20 absence + 20 contextual)
RAP_DISTRIBUTION_BANDS = {
    "host": (170, 200),
    "agent": (250, 280),
    "environment": (120, 150),
}


# ---------------------------------------------------------------------------
# Module-scoped fixture: load all signals once
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def all_signals() -> list[dict]:
    """Load all signals from YAML files (raw dicts, not Pydantic)."""
    signals: list[dict] = []
    for f in sorted(SIGNALS_DIR.glob("**/*.yaml")):
        data = yaml.safe_load(f.read_text())
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict) and "id" in entry:
                    signals.append(entry)
    return signals


@pytest.fixture(scope="module")
def rap_mapping() -> dict[str, dict[str, str]]:
    """Load rap_signal_mapping.yaml -> {signal_id: {rap_class, rap_subcategory}}."""
    mapping_file = FRAMEWORK_DIR / "rap_signal_mapping.yaml"
    data = yaml.safe_load(mapping_file.read_text())
    result: dict[str, dict[str, str]] = {}
    for entry in data["mappings"]:
        result[entry["signal_id"]] = {
            "rap_class": entry["rap_class"],
            "rap_subcategory": entry["rap_subcategory"],
        }
    return result


@pytest.fixture(scope="module")
def valid_subcategories() -> set[str]:
    """Load valid subcategory IDs from rap_taxonomy.yaml."""
    taxonomy_file = FRAMEWORK_DIR / "rap_taxonomy.yaml"
    data = yaml.safe_load(taxonomy_file.read_text())
    subcats: set[str] = set()
    for category in data.get("categories", []):
        for subcat in category.get("subcategories", []):
            subcats.add(subcat["id"])
    return subcats


# ---------------------------------------------------------------------------
# CI Gate Tests
# ---------------------------------------------------------------------------

@pytest.mark.ci
class TestSignalCount:
    """Guard against accidental signal deletion."""

    def test_signal_count_minimum(self, all_signals: list[dict]) -> None:
        count = len(all_signals)
        assert count >= MIN_SIGNAL_COUNT, (
            f"Signal count {count} is below minimum {MIN_SIGNAL_COUNT}. "
            f"Signals may have been accidentally deleted."
        )


@pytest.mark.ci
class TestRapClassification:
    """Validate RAP taxonomy fields on all signals."""

    def test_all_signals_have_rap_class(self, all_signals: list[dict]) -> None:
        missing = [
            s["id"] for s in all_signals
            if s.get("rap_class") not in VALID_RAP_CLASSES
        ]
        assert len(missing) == 0, (
            f"{len(missing)} signals missing valid rap_class: {missing[:10]}"
        )

    def test_all_signals_have_valid_rap_subcategory(
        self, all_signals: list[dict], valid_subcategories: set[str]
    ) -> None:
        invalid = []
        for s in all_signals:
            subcat = s.get("rap_subcategory")
            if not subcat or subcat not in valid_subcategories:
                invalid.append((s["id"], subcat))
        assert len(invalid) == 0, (
            f"{len(invalid)} signals have invalid rap_subcategory: {invalid[:10]}"
        )

    def test_rap_class_matches_mapping(
        self, all_signals: list[dict], rap_mapping: dict[str, dict[str, str]]
    ) -> None:
        """Ensure YAML rap_class matches the authoritative mapping file."""
        mismatches = []
        for s in all_signals:
            sid = s["id"]
            if sid in rap_mapping:
                expected = rap_mapping[sid]["rap_class"]
                actual = s.get("rap_class")
                if actual != expected:
                    mismatches.append((sid, expected, actual))
        assert len(mismatches) == 0, (
            f"{len(mismatches)} signals have rap_class drift from mapping: {mismatches[:10]}"
        )

    def test_rap_distribution_sanity(self, all_signals: list[dict]) -> None:
        counts: dict[str, int] = {"host": 0, "agent": 0, "environment": 0}
        for s in all_signals:
            rc = s.get("rap_class")
            if rc in counts:
                counts[rc] += 1

        for cls, (lo, hi) in RAP_DISTRIBUTION_BANDS.items():
            assert lo <= counts[cls] <= hi, (
                f"rap_class '{cls}' count {counts[cls]} outside expected band [{lo}, {hi}]. "
                f"Distribution: {counts}"
            )


@pytest.mark.ci
class TestEpistemology:
    """Validate epistemology fields on all signals."""

    def test_all_signals_have_epistemology(self, all_signals: list[dict]) -> None:
        missing = []
        for s in all_signals:
            ep = s.get("epistemology")
            if not isinstance(ep, dict):
                missing.append((s["id"], "no epistemology block"))
            elif not ep.get("rule_origin"):
                missing.append((s["id"], "empty rule_origin"))
            elif not ep.get("threshold_basis"):
                missing.append((s["id"], "empty threshold_basis"))
        assert len(missing) == 0, (
            f"{len(missing)} signals with epistemology issues: {missing[:10]}"
        )


@pytest.mark.ci
class TestEvaluationMechanism:
    """Validate evaluation.mechanism on all signals."""

    def test_all_signals_have_evaluation_mechanism(self, all_signals: list[dict]) -> None:
        missing = []
        for s in all_signals:
            ev = s.get("evaluation")
            if not isinstance(ev, dict):
                missing.append((s["id"], "no evaluation block"))
            elif ev.get("mechanism") not in VALID_MECHANISMS:
                missing.append((s["id"], f"mechanism={ev.get('mechanism')}"))
        assert len(missing) == 0, (
            f"{len(missing)} signals missing valid evaluation.mechanism: {missing[:10]}"
        )


@pytest.mark.ci
class TestPydanticValidation:
    """Validate all signals against BrainSignalEntry Pydantic model."""

    def test_all_signals_validate_against_pydantic(self, all_signals: list[dict]) -> None:
        errors: list[tuple[str, str]] = []
        for s in all_signals:
            try:
                BrainSignalEntry.model_validate(s)
            except ValidationError as e:
                errors.append((s.get("id", "???"), str(e)))
        assert len(errors) == 0, (
            f"{len(errors)} signals failed Pydantic validation:\n"
            + "\n".join(f"  {sid}: {err[:200]}" for sid, err in errors[:5])
        )
