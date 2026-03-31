"""Tests for forward guidance detection and mapper gating logic.

Verifies that:
1. detect_forward_guidance() correctly identifies explicit guidance language.
2. Boilerplate "forward-looking statements" disclaimers do NOT trigger detection.
3. compute_guidance_fields() gates FIN.GUIDE signals on provides_forward_guidance.
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.models.common import Confidence
from do_uw.models.market_events import (
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
)
from do_uw.stages.extract.earnings_guidance import detect_forward_guidance
from do_uw.stages.extract.sourced import sourced_float


# ---------------------------------------------------------------------------
# Helper: safe_sourced unwrapper (mirrors production _safe_sourced)
# ---------------------------------------------------------------------------


def _safe_sourced(sv: Any) -> Any:
    """Unwrap a SourcedValue, returning the inner value or None."""
    if sv is None:
        return None
    if hasattr(sv, "value"):
        return sv.value
    return sv


# ---------------------------------------------------------------------------
# detect_forward_guidance tests
# ---------------------------------------------------------------------------


class TestDetectForwardGuidancePositive:
    """Test that explicit guidance language is correctly detected."""

    @pytest.mark.parametrize(
        "text",
        [
            "We expect revenue of $5 billion for fiscal 2026",
            "Our outlook for fiscal 2025 remains positive",
            "The company raises its full-year guidance",
            "We are providing our financial guidance for FY26",
            "We anticipate EPS of $3.50 in the coming year",
            "Full-year 2025 revenue guidance of $10B to $11B",
            "The company reaffirms its full-year guidance",
            "We forecast earnings of $2.00 per share",
            "Fiscal 2025 EPS guidance range of $4.50 to $5.00",
            "We are updating our financial guidance",
        ],
    )
    def test_positive_patterns(self, text: str) -> None:
        assert detect_forward_guidance(text) is True


class TestDetectForwardGuidanceNegative:
    """Test that non-guidance text does NOT trigger detection."""

    @pytest.mark.parametrize(
        "text",
        [
            "The company sells industrial tools",
            "Analysts expect revenue growth next quarter",
            "Total revenue was $4.7 billion for the fiscal year",
            "",
            "   ",
        ],
    )
    def test_negative_patterns(self, text: str) -> None:
        assert detect_forward_guidance(text) is False


class TestForwardLookingBoilerplate:
    """Ensure standard SEC 'forward-looking statements' disclaimers do NOT match."""

    @pytest.mark.parametrize(
        "text",
        [
            (
                "Forward-looking statements involve risks and uncertainties "
                "that could cause actual results to differ materially."
            ),
            (
                "This report contains forward-looking statements within "
                "the meaning of Section 27A of the Securities Act."
            ),
            (
                "Certain statements in this Annual Report are "
                "forward-looking statements as defined in the Private "
                "Securities Litigation Reform Act of 1995."
            ),
        ],
    )
    def test_boilerplate_not_detected(self, text: str) -> None:
        assert detect_forward_guidance(text) is False


# ---------------------------------------------------------------------------
# compute_guidance_fields tests
# ---------------------------------------------------------------------------


def _make_quarter(
    result: str = "BEAT",
    eps_est: float | None = 3.0,
    eps_actual: float | None = 3.2,
    reaction: float | None = 1.5,
) -> EarningsQuarterRecord:
    """Create a test EarningsQuarterRecord."""
    q = EarningsQuarterRecord(quarter="Q1 2025", result=result)
    if eps_est is not None:
        q.consensus_eps_low = sourced_float(eps_est, "test", Confidence.MEDIUM)
        q.consensus_eps_high = sourced_float(eps_est, "test", Confidence.MEDIUM)
    if eps_actual is not None:
        q.actual_eps = sourced_float(eps_actual, "test", Confidence.MEDIUM)
    if reaction is not None:
        q.stock_reaction_pct = sourced_float(reaction, "test", Confidence.LOW)
    return q


class TestComputeGuidanceFieldsNoGuidance:
    """When provides_forward_guidance=False, guidance signals should be gated."""

    def test_guidance_provided_is_no(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=False,
            quarters=[_make_quarter()],
            beat_rate=sourced_float(0.75, "test", Confidence.MEDIUM),
            philosophy="CONSERVATIVE",
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["guidance_provided"] == "No"

    def test_guidance_philosophy_is_na(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=False,
            philosophy="CONSERVATIVE",
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["guidance_philosophy"] == "N/A"

    def test_beat_rate_is_none(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=False,
            beat_rate=sourced_float(0.75, "test", Confidence.MEDIUM),
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["beat_rate"] is None

    def test_analyst_beat_rate_preserved(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=False,
            beat_rate=sourced_float(0.80, "test", Confidence.MEDIUM),
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["analyst_beat_rate"] == 0.80

    def test_post_earnings_drift_still_computed(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=False,
            quarters=[_make_quarter(reaction=2.0), _make_quarter(reaction=-1.0)],
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["post_earnings_drift"] == 0.5


class TestComputeGuidanceFieldsWithGuidance:
    """When provides_forward_guidance=True, all guidance signals compute normally."""

    def test_guidance_provided_yes(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=True,
            quarters=[_make_quarter()],
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["guidance_provided"] == "Yes"

    def test_beat_rate_computed(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=True,
            beat_rate=sourced_float(0.75, "test", Confidence.MEDIUM),
            quarters=[_make_quarter()],
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["beat_rate"] == 0.75

    def test_guidance_philosophy_populated(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=True,
            philosophy="CONSERVATIVE",
            quarters=[_make_quarter()],
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert result["guidance_philosophy"] == "CONSERVATIVE"

    def test_no_analyst_beat_rate_key(self) -> None:
        from do_uw.stages.analyze.signal_mappers_ext import compute_guidance_fields

        eg = EarningsGuidanceAnalysis(
            provides_forward_guidance=True,
            quarters=[_make_quarter()],
        )
        result = compute_guidance_fields(eg, _safe_sourced)
        assert "analyst_beat_rate" not in result
