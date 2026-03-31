"""Tests for management credibility scoring engine.

Tests cover:
- Beat rate computation from earnings history
- Credibility level classification (HIGH/MEDIUM/LOW/UNKNOWN)
- Quarter record population with beat/miss and magnitude
- Edge cases: no data, all beats, all misses
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.forward_looking import CredibilityQuarter, CredibilityScore
from do_uw.models.market_events import (
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
    EarningsResult,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.analyze.credibility_engine import compute_credibility_score


def _sv_float(val: float) -> SourcedValue[float]:
    """Create a sourced float for test data."""
    from datetime import UTC, datetime

    return SourcedValue[float](
        value=val,
        source="test",
        confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )


def _make_quarter(
    quarter: str,
    estimate: float | None,
    actual: float,
    result: str = "",
) -> EarningsQuarterRecord:
    """Build a quarter record with optional estimate."""
    rec = EarningsQuarterRecord(
        quarter=quarter,
        actual_eps=_sv_float(actual),
        result=result,
    )
    if estimate is not None:
        rec.consensus_eps_low = _sv_float(estimate)
        rec.consensus_eps_high = _sv_float(estimate)
    return rec


def _make_state_with_guidance(
    quarters: list[EarningsQuarterRecord],
) -> AnalysisState:
    """Build AnalysisState with earnings guidance data."""
    state = AnalysisState(ticker="TEST")

    # Build proper extracted data with market signals
    from do_uw.models.market import MarketSignals
    from do_uw.models.state import ExtractedData

    extracted = ExtractedData()
    market = MarketSignals()
    guidance = EarningsGuidanceAnalysis(quarters=quarters)
    market.earnings_guidance = guidance
    extracted.market = market
    state.extracted = extracted

    return state


class TestComputeCredibilityScore:
    """Tests for compute_credibility_score."""

    def test_8_quarters_6_beats_returns_medium(self) -> None:
        """8 quarters with 6 beats (75%) returns MEDIUM credibility."""
        quarters = [
            _make_quarter("Q1 2024", 1.00, 1.10, EarningsResult.BEAT),
            _make_quarter("Q2 2024", 1.20, 1.30, EarningsResult.BEAT),
            _make_quarter("Q3 2024", 1.10, 1.05, EarningsResult.MISS),
            _make_quarter("Q4 2024", 1.15, 1.20, EarningsResult.BEAT),
            _make_quarter("Q1 2023", 0.90, 0.95, EarningsResult.BEAT),
            _make_quarter("Q2 2023", 0.95, 0.90, EarningsResult.MISS),
            _make_quarter("Q3 2023", 0.85, 0.90, EarningsResult.BEAT),
            _make_quarter("Q4 2023", 0.80, 0.85, EarningsResult.BEAT),
        ]
        state = _make_state_with_guidance(quarters)
        result = compute_credibility_score(state)

        assert isinstance(result, CredibilityScore)
        assert result.beat_rate_pct == pytest.approx(75.0)
        assert result.credibility_level == "MEDIUM"
        assert result.quarters_assessed == 8

    def test_high_beat_rate_returns_high(self) -> None:
        """>80% beat rate returns HIGH credibility."""
        quarters = [
            _make_quarter(f"Q{i} 2024", 1.00, 1.10, EarningsResult.BEAT)
            for i in range(1, 6)
        ]
        state = _make_state_with_guidance(quarters)
        result = compute_credibility_score(state)

        assert result.credibility_level == "HIGH"
        assert result.beat_rate_pct > 80.0

    def test_low_beat_rate_returns_low(self) -> None:
        """<50% beat rate returns LOW credibility."""
        quarters = [
            _make_quarter("Q1 2024", 1.00, 0.80, EarningsResult.MISS),
            _make_quarter("Q2 2024", 1.00, 0.85, EarningsResult.MISS),
            _make_quarter("Q3 2024", 1.00, 0.90, EarningsResult.MISS),
            _make_quarter("Q4 2024", 1.00, 1.10, EarningsResult.BEAT),
        ]
        state = _make_state_with_guidance(quarters)
        result = compute_credibility_score(state)

        assert result.credibility_level == "LOW"
        assert result.beat_rate_pct < 50.0

    def test_no_quarters_returns_unknown(self) -> None:
        """No quarters data returns UNKNOWN credibility with 0 assessed."""
        state = _make_state_with_guidance([])
        result = compute_credibility_score(state)

        assert result.credibility_level == "UNKNOWN"
        assert result.quarters_assessed == 0
        assert result.beat_rate_pct == 0.0

    def test_quarter_records_populated(self) -> None:
        """Quarter records have beat_or_miss and magnitude_pct populated."""
        quarters = [
            _make_quarter("Q1 2024", 1.00, 1.10, EarningsResult.BEAT),
            _make_quarter("Q2 2024", 1.00, 0.90, EarningsResult.MISS),
        ]
        state = _make_state_with_guidance(quarters)
        result = compute_credibility_score(state)

        assert len(result.quarter_records) == 2
        rec_beat = result.quarter_records[0]
        assert isinstance(rec_beat, CredibilityQuarter)
        assert rec_beat.beat_or_miss == "BEAT"
        assert rec_beat.magnitude_pct is not None
        assert rec_beat.magnitude_pct > 0  # beat = positive magnitude

        rec_miss = result.quarter_records[1]
        assert rec_miss.beat_or_miss == "MISS"
        assert rec_miss.magnitude_pct is not None

    def test_inline_result_classification(self) -> None:
        """Results within 1% are classified as INLINE."""
        quarters = [
            _make_quarter("Q1 2024", 1.00, 1.005, EarningsResult.MEET),
        ]
        state = _make_state_with_guidance(quarters)
        result = compute_credibility_score(state)

        assert len(result.quarter_records) >= 1
        # MEET results are classified as INLINE in credibility
        rec = result.quarter_records[0]
        assert rec.beat_or_miss == "INLINE"

    def test_exact_80_pct_is_medium(self) -> None:
        """Exactly 80% beat rate is MEDIUM (>80 required for HIGH)."""
        quarters = [
            _make_quarter("Q1 2024", 1.00, 1.10, EarningsResult.BEAT),
            _make_quarter("Q2 2024", 1.00, 1.10, EarningsResult.BEAT),
            _make_quarter("Q3 2024", 1.00, 1.10, EarningsResult.BEAT),
            _make_quarter("Q4 2024", 1.00, 1.10, EarningsResult.BEAT),
            _make_quarter("Q1 2023", 1.00, 0.80, EarningsResult.MISS),
        ]
        state = _make_state_with_guidance(quarters)
        result = compute_credibility_score(state)

        assert result.beat_rate_pct == pytest.approx(80.0)
        assert result.credibility_level == "MEDIUM"

    def test_no_extracted_data_returns_unknown(self) -> None:
        """State with no extracted data returns UNKNOWN gracefully."""
        state = AnalysisState(ticker="TEST")
        result = compute_credibility_score(state)

        assert result.credibility_level == "UNKNOWN"
        assert result.quarters_assessed == 0
