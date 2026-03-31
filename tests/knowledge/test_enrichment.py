"""Tests validating enriched signals.json correctness and classification distribution.

Verifies that all 400 checks have content_type, depth, data_strategy.field_key
(where applicable), and pattern_ref (for INFERENCE_PATTERN). Ensures enrichment
script did not remove any existing fields, distributions match expected counts,
and the pipeline still works with enriched checks.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from do_uw.knowledge.signal_definition import SignalDefinition, ContentType, DepthLevel
from do_uw.stages.analyze.signal_field_routing import FIELD_FOR_CHECK

CHECKS_JSON = Path(__file__).parent.parent.parent / "src" / "do_uw" / "brain" / "config" / "signals.json"

# Existing fields that must be preserved on every check after enrichment
REQUIRED_FIELDS = {
    "id",
    "name",
    "section",
    "factors",
    "required_data",
    "data_locations",
    "threshold",
    "execution_mode",
    "category",
    "signal_type",
    "hazard_or_signal",
    "plaintiff_lenses",
}


@pytest.fixture(scope="module")
def checks() -> list[dict[str, Any]]:
    """Load all signals from brain/signals.json."""
    with open(CHECKS_JSON) as f:
        data = json.load(f)
    return data["signals"]


class TestContentType:
    """Tests for content_type enrichment field."""

    def test_all_checks_have_content_type(self, checks: list[dict[str, Any]]) -> None:
        """Every check must have a content_type field with a valid value."""
        valid_types = {ct.value for ct in ContentType}
        for check in checks:
            assert "content_type" in check, f"Check {check['id']} missing content_type"
            assert check["content_type"] in valid_types, (
                f"Check {check['id']} has invalid content_type: {check['content_type']}"
            )

    def test_content_type_distribution(self, checks: list[dict[str, Any]]) -> None:
        """Verify expected content type distribution."""
        from collections import Counter

        ct_counts = Counter(c["content_type"] for c in checks)
        assert ct_counts["MANAGEMENT_DISPLAY"] == 98
        assert ct_counts["INFERENCE_PATTERN"] == 21
        assert ct_counts["EVALUATIVE_CHECK"] == 281  # 276 + 4 governance (Phase 40) + 1 reclassified
        assert sum(ct_counts.values()) == 400

    def test_management_display_checks_mostly_no_factors(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """Most MANAGEMENT_DISPLAY checks have empty factors (64 of 99).

        35 MD checks retain factors from pre-reclassification (e.g., GOV.INSIDER,
        FWRD.MACRO sector overlay checks). These are display-oriented checks
        that still map to scoring factors for contextual weighting.
        """
        md_with_factors = sum(
            1
            for c in checks
            if c["content_type"] == "MANAGEMENT_DISPLAY" and c.get("factors")
        )
        md_total = sum(
            1 for c in checks if c["content_type"] == "MANAGEMENT_DISPLAY"
        )
        assert md_total == 98, f"Expected 98 MD checks, got {md_total}"
        assert md_with_factors == 35, (
            f"Expected 35 MD checks with factors, got {md_with_factors}"
        )

    def test_management_display_checks_mostly_context_display(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """Most MANAGEMENT_DISPLAY checks have category CONTEXT_DISPLAY (94 of 99).

        5 MD checks have DECISION_DRIVING category (FIN.GUIDE.philosophy,
        GOV.ACTIVIST.schedule_13g, GOV.INSIDER.form4_filings,
        GOV.INSIDER.10b5_plans, FWRD.EVENT.proxy_deadline).
        """
        md_not_cd = sum(
            1
            for c in checks
            if c["content_type"] == "MANAGEMENT_DISPLAY"
            and c.get("category") != "CONTEXT_DISPLAY"
        )
        # Some MANAGEMENT_DISPLAY checks are DECISION_DRIVING (e.g. display
        # data that directly informs scoring decisions)
        assert md_not_cd <= 25, (
            f"Expected <= 25 MD checks with non-CONTEXT_DISPLAY category, got {md_not_cd}"
        )


class TestDepth:
    """Tests for depth enrichment field."""

    def test_all_checks_have_depth(self, checks: list[dict[str, Any]]) -> None:
        """Every check must have a depth field with value 1-4."""
        for check in checks:
            assert "depth" in check, f"Check {check['id']} missing depth"
            assert check["depth"] in (1, 2, 3, 4), (
                f"Check {check['id']} has invalid depth: {check['depth']}"
            )

    def test_depth_distribution(self, checks: list[dict[str, Any]]) -> None:
        """Verify depth level distribution."""
        from collections import Counter

        depth_counts = Counter(c["depth"] for c in checks)
        assert depth_counts[1] == 20  # DISPLAY
        assert depth_counts[2] == 269  # COMPUTE
        assert depth_counts[3] == 61  # INFER (+1 governance Phase 40)
        assert depth_counts[4] == 50  # HUNT (+3 governance Phase 40)
        assert sum(depth_counts.values()) == 400


class TestFieldKey:
    """Tests for data_strategy.field_key migration."""

    def test_field_key_coverage(self, checks: list[dict[str, Any]]) -> None:
        """Exactly 259 checks must have data_strategy.field_key populated."""
        count = sum(
            1
            for c in checks
            if c.get("data_strategy") and c["data_strategy"].get("field_key")
        )
        assert count == 284, f"Expected 284 checks with field_key, got {count}"

    def test_field_key_values_match_routing(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """Every FIELD_FOR_CHECK entry with a signal must match data_strategy.field_key."""
        check_by_id = {c["id"]: c for c in checks}
        for signal_id, expected_field in FIELD_FOR_CHECK.items():
            check = check_by_id.get(signal_id)
            if check is None:
                # FIELD_FOR_CHECK may reference signals not yet in signals.json
                continue
            ds = check.get("data_strategy")
            assert ds is not None, (
                f"Check {signal_id} has no data_strategy but is in FIELD_FOR_CHECK"
            )
            assert ds.get("field_key") == expected_field, (
                f"Check {signal_id}: field_key mismatch. "
                f"Expected {expected_field!r}, got {ds.get('field_key')!r}"
            )

    def test_field_key_checks_have_primary_source(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """Checks with field_key should also have primary_source set."""
        for check in checks:
            ds = check.get("data_strategy")
            if ds and ds.get("field_key"):
                if check.get("required_data"):
                    # primary_source must be one of the required_data entries
                    assert ds.get("primary_source") in check["required_data"], (
                        f"Check {check['id']}: primary_source {ds.get('primary_source')!r} "
                        f"not in required_data {check['required_data']}"
                    )


class TestPatternRef:
    """Tests for pattern_ref on INFERENCE_PATTERN checks."""

    # 2 INFERENCE_PATTERN signals from Plan 33-03 lack pattern_ref:
    # LIT.PATTERN.peer_contagion, LIT.PATTERN.temporal_correlation
    _IP_MISSING_PATTERN_REF = {
        "LIT.PATTERN.peer_contagion",
        "LIT.PATTERN.temporal_correlation",
    }

    def test_inference_pattern_signals_have_pattern_ref(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """INFERENCE_PATTERN checks must have pattern_ref set (except 2 known gaps)."""
        missing: list[str] = []
        for check in checks:
            if check["content_type"] == "INFERENCE_PATTERN":
                if check["id"] in self._IP_MISSING_PATTERN_REF:
                    continue  # Known gap from Plan 33-03
                if not check.get("pattern_ref"):
                    missing.append(check["id"])
                else:
                    assert isinstance(check["pattern_ref"], str), (
                        f"Check {check['id']}: pattern_ref must be a string"
                    )
        assert not missing, (
            f"Unexpected INFERENCE_PATTERN checks missing pattern_ref: {missing}"
        )

    def test_known_stock_pattern_refs(self, checks: list[dict[str, Any]]) -> None:
        """Known STOCK.PATTERN.* checks must have specific pattern_ref values."""
        expected = {
            "STOCK.PATTERN.event_collapse": "EVENT_COLLAPSE",
            "STOCK.PATTERN.informed_trading": "INFORMED_TRADING",
            "STOCK.PATTERN.cascade": "PRICE_CASCADE",
            "STOCK.PATTERN.death_spiral": "DEATH_SPIRAL",
            "STOCK.PATTERN.short_attack": "SHORT_ATTACK",
            "STOCK.PATTERN.peer_divergence": "PEER_DIVERGENCE",
        }
        check_by_id = {c["id"]: c for c in checks}
        for signal_id, expected_ref in expected.items():
            check = check_by_id.get(signal_id)
            assert check is not None, f"Check {signal_id} not found"
            assert check.get("pattern_ref") == expected_ref, (
                f"Check {signal_id}: expected pattern_ref {expected_ref!r}, "
                f"got {check.get('pattern_ref')!r}"
            )

    def test_non_pattern_signals_no_pattern_ref(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """Non-INFERENCE_PATTERN checks should not have pattern_ref."""
        for check in checks:
            if check["content_type"] != "INFERENCE_PATTERN":
                assert not check.get("pattern_ref"), (
                    f"Non-pattern check {check['id']} has pattern_ref: {check.get('pattern_ref')}"
                )


class TestModelValidation:
    """Tests for SignalDefinition model validation of enriched checks."""

    def test_all_checks_validate_against_model(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """All 400 enriched checks must validate against SignalDefinition model."""
        errors = []
        for check in checks:
            try:
                SignalDefinition.model_validate(check)
            except Exception as e:
                errors.append(f"{check['id']}: {e}")
        assert not errors, f"Validation errors:\n" + "\n".join(errors[:10])

    def test_validated_checks_preserve_content_type(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """Validated SignalDefinition instances should have correct content_type."""
        for check in checks:
            cd = SignalDefinition.model_validate(check)
            assert cd.content_type.value == check["content_type"], (
                f"Check {check['id']}: content_type mismatch after validation"
            )

    def test_validated_checks_preserve_depth(
        self, checks: list[dict[str, Any]]
    ) -> None:
        """Validated SignalDefinition instances should have correct depth."""
        for check in checks:
            cd = SignalDefinition.model_validate(check)
            assert cd.depth.value == check["depth"], (
                f"Check {check['id']}: depth mismatch after validation"
            )


class TestExistingFieldsPreserved:
    """Tests that enrichment did not remove any existing fields."""

    def test_existing_fields_preserved(self, checks: list[dict[str, Any]]) -> None:
        """Every check must still have all required pre-enrichment fields."""
        for check in checks:
            missing = REQUIRED_FIELDS - set(check.keys())
            assert not missing, (
                f"Check {check['id']} missing fields after enrichment: {missing}"
            )

    def test_claims_correlation_preserved(self, checks: list[dict[str, Any]]) -> None:
        """Claims correlation should be preserved where it exists."""
        has_cc = sum(1 for c in checks if "claims_correlation" in c)
        assert has_cc > 0, "No checks have claims_correlation - field may have been removed"

    def test_tier_preserved(self, checks: list[dict[str, Any]]) -> None:
        """Tier field should be preserved on all checks."""
        for check in checks:
            assert "tier" in check, f"Check {check['id']} missing tier field"


class TestPipelineNotBroken:
    """Tests that the check engine still works with enriched checks."""

    def test_execute_signals_with_empty_data(self) -> None:
        """Execute checks with minimal ExtractedData -- should produce SKIPPED, not crashes."""
        import json

        from do_uw.models.state import ExtractedData
        from do_uw.stages.analyze.signal_engine import execute_signals

        with open(CHECKS_JSON) as f:
            data = json.load(f)

        checks = data["signals"]
        extracted = ExtractedData()

        # Should not raise -- all checks will be SKIPPED due to missing data
        results = execute_signals(checks, extracted)
        assert len(results) > 0, "execute_signals returned no results"
        # All should be SKIPPED or have some status -- no crashes
        for r in results:
            assert r.status is not None, f"Check result has no status"
