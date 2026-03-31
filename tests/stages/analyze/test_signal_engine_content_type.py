"""Tests for content-type-aware evaluation dispatch in check engine.

Phase 32-05: Verifies that the check engine dispatches to different
evaluation paths based on content_type:
- MANAGEMENT_DISPLAY -> evaluate_management_display() -> INFO/SKIPPED
- EVALUATIVE_CHECK -> evaluate_signal() -> threshold evaluation (unchanged)
- INFERENCE_PATTERN -> evaluate_signal() -> threshold evaluation (for now)

These tests verify ADDITIVE behavior: the default EVALUATIVE_CHECK path
is completely unchanged. Only MANAGEMENT_DISPLAY gets new treatment.
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.stages.analyze.signal_engine import (
    evaluate_signal,
    evaluate_management_display,
)
from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus


# ---------------------------------------------------------------------------
# Fixtures: minimal check config dicts
# ---------------------------------------------------------------------------


def _make_check(
    signal_id: str = "TEST.CHECK.001",
    name: str = "Test Check",
    content_type: str = "EVALUATIVE_CHECK",
    section: int = 3,
    factors: list[str] | None = None,
    threshold: dict[str, Any] | None = None,
    execution_mode: str = "AUTO",
    **extra: Any,
) -> dict[str, Any]:
    """Build a minimal check config dict for testing."""
    check: dict[str, Any] = {
        "id": signal_id,
        "name": name,
        "content_type": content_type,
        "section": section,
        "factors": factors or [],
        "threshold": threshold or {"type": "info"},
        "execution_mode": execution_mode,
        "required_data": [],
        "data_locations": {},
    }
    check.update(extra)
    return check


# ---------------------------------------------------------------------------
# MANAGEMENT_DISPLAY tests
# ---------------------------------------------------------------------------


class TestManagementDisplayWithData:
    """MANAGEMENT_DISPLAY check with data present -> INFO status."""

    def test_returns_info_status(self) -> None:
        """MD check with data should produce INFO status."""
        check = _make_check(
            signal_id="BIZ.PROF.revenue_segments",
            name="Revenue Segments",
            content_type="MANAGEMENT_DISPLAY",
        )
        data = {"revenue_segments": "Technology: 60%, Services: 40%"}
        result = evaluate_management_display(check, data)
        assert result.status == SignalStatus.INFO

    def test_evidence_contains_management_display(self) -> None:
        """Evidence should indicate management display."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"value": "Some display value"}
        result = evaluate_management_display(check, data)
        assert "Management display" in result.evidence

    def test_value_captured(self) -> None:
        """The data value should be captured in the result."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"revenue": 1234567.89}
        result = evaluate_management_display(check, data)
        assert result.value == 1234567.89

    def test_source_set_to_data_key(self) -> None:
        """Source should be set to the data key that provided the value."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"geographic_footprint": "North America: 70%, EMEA: 30%"}
        result = evaluate_management_display(check, data)
        assert result.source == "geographic_footprint"

    def test_factors_preserved(self) -> None:
        """Factors from check config should be on the result."""
        check = _make_check(
            content_type="MANAGEMENT_DISPLAY",
            factors=["F1", "F2"],
        )
        data = {"value": "data"}
        result = evaluate_management_display(check, data)
        assert result.factors == ["F1", "F2"]

    def test_section_preserved(self) -> None:
        """Section from check config should be on the result."""
        check = _make_check(
            content_type="MANAGEMENT_DISPLAY",
            section=1,
        )
        data = {"value": "data"}
        result = evaluate_management_display(check, data)
        assert result.section == 1

    def test_signal_id_and_name_preserved(self) -> None:
        """signal_id and signal_name should match the check config."""
        check = _make_check(
            signal_id="BIZ.PROF.exec_list",
            name="Executive List",
            content_type="MANAGEMENT_DISPLAY",
        )
        data = {"exec_list": "CEO: John Doe"}
        result = evaluate_management_display(check, data)
        assert result.signal_id == "BIZ.PROF.exec_list"
        assert result.signal_name == "Executive List"

    def test_needs_calibration_false(self) -> None:
        """MD checks never need calibration."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"value": "data"}
        result = evaluate_management_display(check, data)
        assert result.needs_calibration is False

    def test_no_threshold_evaluation(self) -> None:
        """MD check with thresholds should still produce INFO, not TRIGGERED."""
        check = _make_check(
            content_type="MANAGEMENT_DISPLAY",
            threshold={"type": "tiered", "red": ">50%", "yellow": ">25%"},
        )
        # Even with data that would trigger thresholds, result is INFO
        data = {"value": 99.9}
        result = evaluate_management_display(check, data)
        assert result.status == SignalStatus.INFO
        assert result.threshold_level == ""  # No threshold level set

    def test_string_value_coerced(self) -> None:
        """String values should be captured as-is."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"description": "Multi-line\ncompany description"}
        result = evaluate_management_display(check, data)
        assert result.value == "Multi-line\ncompany description"

    def test_dict_value_coerced_to_string(self) -> None:
        """Dict values should be stringified."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"segments": {"tech": 60, "services": 40}}
        result = evaluate_management_display(check, data)
        # coerce_value converts dicts to str
        assert isinstance(result.value, str)

    def test_skips_none_values_finds_first_real(self) -> None:
        """When first data value is None, should find next non-None."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"empty_field": None, "real_field": "actual data"}
        result = evaluate_management_display(check, data)
        assert result.status == SignalStatus.INFO
        assert result.source == "real_field"


class TestManagementDisplayWithoutData:
    """MANAGEMENT_DISPLAY check with data absent -> SKIPPED status."""

    def test_returns_skipped_status(self) -> None:
        """MD check with no data should produce SKIPPED status."""
        check = _make_check(
            signal_id="BIZ.PROF.geographic",
            name="Geographic Footprint",
            content_type="MANAGEMENT_DISPLAY",
        )
        data = {"geographic_footprint": None}
        result = evaluate_management_display(check, data)
        assert result.status == SignalStatus.SKIPPED

    def test_skipped_on_empty_data(self) -> None:
        """MD check with empty data dict should produce SKIPPED."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data: dict[str, Any] = {}
        result = evaluate_management_display(check, data)
        assert result.status == SignalStatus.SKIPPED

    def test_skipped_on_all_none(self) -> None:
        """MD check where all data values are None should produce SKIPPED."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"field1": None, "field2": None, "field3": None}
        result = evaluate_management_display(check, data)
        assert result.status == SignalStatus.SKIPPED

    def test_skipped_has_data_unavailable_status(self) -> None:
        """SKIPPED MD check should have DATA_UNAVAILABLE data_status."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"field": None}
        result = evaluate_management_display(check, data)
        assert result.data_status == "DATA_UNAVAILABLE"


# ---------------------------------------------------------------------------
# EVALUATIVE_CHECK tests (default path -- must be unchanged)
# ---------------------------------------------------------------------------


class TestEvaluativeCheckUnchanged:
    """EVALUATIVE_CHECK evaluation should be identical to existing behavior."""

    def test_tiered_threshold_still_triggers(self) -> None:
        """EC check with numeric data exceeding red threshold -> TRIGGERED."""
        check = _make_check(
            signal_id="FIN.LEV.ratio",
            name="Leverage Ratio",
            content_type="EVALUATIVE_CHECK",
            threshold={"type": "tiered", "red": ">5.0", "yellow": ">3.0"},
        )
        data = {"leverage_ratio": 7.5}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.TRIGGERED
        assert result.threshold_level == "red"

    def test_tiered_threshold_clears(self) -> None:
        """EC check with value within thresholds -> CLEAR."""
        check = _make_check(
            content_type="EVALUATIVE_CHECK",
            threshold={"type": "tiered", "red": ">5.0", "yellow": ">3.0"},
        )
        data = {"value": 1.5}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.CLEAR

    def test_info_threshold_returns_info(self) -> None:
        """EC check with info threshold type -> INFO."""
        check = _make_check(
            content_type="EVALUATIVE_CHECK",
            threshold={"type": "info"},
        )
        data = {"value": "some info"}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.INFO

    def test_missing_data_returns_skipped(self) -> None:
        """EC check with all None data -> SKIPPED."""
        check = _make_check(
            content_type="EVALUATIVE_CHECK",
            threshold={"type": "tiered", "red": ">5.0"},
        )
        data = {"value": None}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.SKIPPED

    def test_boolean_threshold_triggers(self) -> None:
        """EC check with boolean threshold -> TRIGGERED when True."""
        check = _make_check(
            content_type="EVALUATIVE_CHECK",
            threshold={"type": "boolean", "red": "True condition", "clear": "False condition"},
        )
        data = {"flag": True}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.TRIGGERED


# ---------------------------------------------------------------------------
# INFERENCE_PATTERN tests (delegates to evaluate_signal for now)
# ---------------------------------------------------------------------------


class TestInferencePatternDelegates:
    """INFERENCE_PATTERN checks should delegate to evaluate_signal() (for now).

    Phase 32 scope: evaluate individual signal same as evaluative.
    Pattern composition remains in SCORE stage.
    """

    def test_ip_check_with_tiered_threshold_triggers(self) -> None:
        """IP check with exceeding value -> TRIGGERED (same as EC)."""
        check = _make_check(
            signal_id="FIN.FRAUD.earnings_restatement",
            name="Earnings Restatement Pattern",
            content_type="INFERENCE_PATTERN",
            threshold={"type": "tiered", "red": ">3", "yellow": ">1"},
            pattern_ref="PAT.FRAUD.earnings_restatement",
        )
        data = {"restatement_count": 5}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.TRIGGERED

    def test_ip_check_with_info_threshold(self) -> None:
        """IP check with info threshold -> INFO."""
        check = _make_check(
            content_type="INFERENCE_PATTERN",
            threshold={"type": "info"},
        )
        data = {"signal": "detected"}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.INFO

    def test_ip_check_with_no_data_skips(self) -> None:
        """IP check with no data -> SKIPPED."""
        check = _make_check(
            content_type="INFERENCE_PATTERN",
            threshold={"type": "tiered", "red": ">1"},
        )
        data = {"signal": None}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.SKIPPED


# ---------------------------------------------------------------------------
# Default content_type behavior
# ---------------------------------------------------------------------------


class TestDefaultContentType:
    """Checks with no content_type field should default to EVALUATIVE_CHECK."""

    def test_no_content_type_field_triggers_like_ec(self) -> None:
        """Check without content_type behaves as EVALUATIVE_CHECK."""
        check = _make_check(
            threshold={"type": "tiered", "red": ">5.0", "yellow": ">3.0"},
        )
        # Remove content_type to test default behavior
        del check["content_type"]
        data = {"value": 7.5}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.TRIGGERED

    def test_no_content_type_field_skips_like_ec(self) -> None:
        """Check without content_type skips on missing data like EC."""
        check = _make_check(
            threshold={"type": "tiered", "red": ">5.0"},
        )
        del check["content_type"]
        data = {"value": None}
        result = evaluate_signal(check, data)
        assert result.status == SignalStatus.SKIPPED


# ---------------------------------------------------------------------------
# Traceability and classification metadata
# ---------------------------------------------------------------------------


class TestManagementDisplayTraceability:
    """Verify that traceability chain is populated for MD checks."""

    def test_trace_evaluation_set_for_info(self) -> None:
        """INFO MD check should have management_display trace."""
        check = _make_check(
            content_type="MANAGEMENT_DISPLAY",
            required_data=["SEC_10K"],
        )
        data = {"value": "present"}
        result = evaluate_management_display(check, data)
        assert "management_display" in result.trace_evaluation

    def test_trace_evaluation_set_for_skipped(self) -> None:
        """SKIPPED MD check should have skipped trace."""
        check = _make_check(content_type="MANAGEMENT_DISPLAY")
        data = {"value": None}
        result = evaluate_management_display(check, data)
        assert "skipped" in result.trace_evaluation

    def test_classification_metadata_applied(self) -> None:
        """Classification metadata from check config should be on result."""
        check = _make_check(
            content_type="MANAGEMENT_DISPLAY",
            category="CONTEXT_DISPLAY",
            signal_type="STRUCTURAL",
            hazard_or_signal="HAZARD",
        )
        data = {"value": "present"}
        result = evaluate_management_display(check, data)
        assert result.category == "CONTEXT_DISPLAY"
        assert result.signal_type == "STRUCTURAL"
        assert result.hazard_or_signal == "HAZARD"
