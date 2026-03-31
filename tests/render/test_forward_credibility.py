"""Tests for forward credibility context builder.

Verifies that build_forward_credibility() classifies management guidance
patterns and produces quarter-by-quarter tables with CSS classes.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders._forward_credibility import (
    build_forward_credibility,
)


def _make_quarter(
    quarter: str,
    guided: str,
    actual: str,
    beat_or_miss: str,
    magnitude_pct: float | None = None,
) -> MagicMock:
    """Build a mock CredibilityQuarter."""
    q = MagicMock()
    q.quarter = quarter
    q.metric = "EPS"
    q.guided_value = guided
    q.actual_value = actual
    q.beat_or_miss = beat_or_miss
    q.magnitude_pct = magnitude_pct
    q.source = "yfinance"
    return q


def _make_state(
    quarters: list[MagicMock] | None = None,
    beat_rate_pct: float = 75.0,
    credibility_level: str = "HIGH",
    quarters_assessed: int | None = None,
    credibility_none: bool = False,
) -> MagicMock:
    """Build mock AnalysisState with credibility data."""
    state = MagicMock()

    if credibility_none:
        state.forward_looking.credibility = None
        return state

    cred = MagicMock()
    cred.beat_rate_pct = beat_rate_pct
    cred.credibility_level = credibility_level
    cred.quarter_records = quarters or []
    cred.quarters_assessed = quarters_assessed if quarters_assessed is not None else len(quarters or [])
    cred.source = "yfinance + 8-K LLM"
    state.forward_looking.credibility = cred

    return state


class TestBuildForwardCredibility:
    """Tests for build_forward_credibility."""

    def test_returns_dict_with_required_keys(self) -> None:
        quarters = [
            _make_quarter("Q1 2025", "$1.00", "$1.10", "BEAT", 10.0),
            _make_quarter("Q2 2025", "$1.05", "$1.15", "BEAT", 9.5),
            _make_quarter("Q3 2025", "$1.10", "$1.20", "BEAT", 9.1),
            _make_quarter("Q4 2025", "$1.15", "$1.25", "BEAT", 8.7),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=100.0)
        result = build_forward_credibility(state)
        assert isinstance(result, dict)
        assert "credibility_available" in result
        assert "pattern" in result
        assert "pattern_label" in result
        assert "beat_rate_pct" in result
        assert "quarters_assessed" in result
        assert "quarter_table" in result
        assert "cumulative_pattern" in result

    def test_consistent_beater_pattern(self) -> None:
        """beat_rate > 0.75 AND avg magnitude < 10% -> Consistent Beater."""
        quarters = [
            _make_quarter("Q1", "$1.00", "$1.05", "BEAT", 5.0),
            _make_quarter("Q2", "$1.00", "$1.08", "BEAT", 8.0),
            _make_quarter("Q3", "$1.00", "$1.03", "BEAT", 3.0),
            _make_quarter("Q4", "$1.00", "$1.06", "BEAT", 6.0),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=100.0)
        result = build_forward_credibility(state)
        assert result["pattern"] == "CONSISTENT_BEATER"
        assert result["pattern_label"] == "Consistent Beater"

    def test_sandbagging_pattern(self) -> None:
        """beat_rate > 0.80 AND avg magnitude >= 10% -> Sandbagging."""
        quarters = [
            _make_quarter("Q1", "$1.00", "$1.20", "BEAT", 20.0),
            _make_quarter("Q2", "$1.00", "$1.15", "BEAT", 15.0),
            _make_quarter("Q3", "$1.00", "$1.12", "BEAT", 12.0),
            _make_quarter("Q4", "$1.00", "$1.18", "BEAT", 18.0),
            _make_quarter("Q5", "$1.00", "$1.11", "BEAT", 11.0),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=100.0)
        result = build_forward_credibility(state)
        assert result["pattern"] == "SANDBAGGING"
        assert result["pattern_label"] == "Sandbagging"

    def test_unreliable_pattern(self) -> None:
        """miss_rate > 0.25 -> Unreliable."""
        quarters = [
            _make_quarter("Q1", "$1.00", "$0.90", "MISS", 10.0),
            _make_quarter("Q2", "$1.00", "$1.05", "BEAT", 5.0),
            _make_quarter("Q3", "$1.00", "$0.85", "MISS", 15.0),
            _make_quarter("Q4", "$1.00", "$1.02", "BEAT", 2.0),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=50.0)
        result = build_forward_credibility(state)
        assert result["pattern"] == "UNRELIABLE"
        assert result["pattern_label"] == "Unreliable"

    def test_deteriorating_pattern(self) -> None:
        """Last 2+ quarters are misses after 4+ consecutive beats -> Deteriorating."""
        quarters = [
            _make_quarter("Q1", "$1.00", "$1.05", "BEAT", 5.0),
            _make_quarter("Q2", "$1.00", "$1.06", "BEAT", 6.0),
            _make_quarter("Q3", "$1.00", "$1.04", "BEAT", 4.0),
            _make_quarter("Q4", "$1.00", "$1.07", "BEAT", 7.0),
            _make_quarter("Q5", "$1.00", "$0.95", "MISS", 5.0),
            _make_quarter("Q6", "$1.00", "$0.92", "MISS", 8.0),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=66.7)
        result = build_forward_credibility(state)
        assert result["pattern"] == "DETERIORATING"
        assert result["pattern_label"] == "Deteriorating"

    def test_insufficient_data_pattern(self) -> None:
        """Fewer than 4 quarters -> Insufficient Data."""
        quarters = [
            _make_quarter("Q1", "$1.00", "$1.05", "BEAT", 5.0),
            _make_quarter("Q2", "$1.00", "$1.06", "BEAT", 6.0),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=100.0, quarters_assessed=2)
        result = build_forward_credibility(state)
        assert result["pattern"] == "INSUFFICIENT_DATA"
        assert result["pattern_label"] == "Insufficient Data"

    def test_quarter_table_has_required_keys(self) -> None:
        quarters = [
            _make_quarter("Q1 2025", "$1.00", "$1.10", "BEAT", 10.0),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=100.0, quarters_assessed=1)
        result = build_forward_credibility(state)
        row = result["quarter_table"][0]
        assert "quarter" in row
        assert "guidance" in row
        assert "actual" in row
        assert "delta" in row
        assert "magnitude" in row
        assert "beat_or_miss" in row
        assert "row_class" in row

    def test_cumulative_pattern_string(self) -> None:
        quarters = [
            _make_quarter("Q1", "$1.00", "$1.05", "BEAT", 5.0),
            _make_quarter("Q2", "$1.00", "$0.90", "MISS", 10.0),
            _make_quarter("Q3", "$1.00", "$1.03", "BEAT", 3.0),
        ]
        state = _make_state(quarters=quarters, beat_rate_pct=66.7, quarters_assessed=3)
        result = build_forward_credibility(state)
        assert result["cumulative_pattern"] == "BMB"

    def test_unavailable_when_no_credibility(self) -> None:
        state = _make_state(credibility_none=True)
        result = build_forward_credibility(state)
        assert result["credibility_available"] is False
