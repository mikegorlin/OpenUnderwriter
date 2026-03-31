"""Tests for peer percentile context builder."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from do_uw.models.scoring import FramesPercentileResult
from do_uw.stages.render.context_builders.financials_peers import (
    build_peer_percentile_context,
)


def _make_state(
    frames: dict[str, FramesPercentileResult] | None = None,
    sic_code: str | None = None,
) -> MagicMock:
    """Create a minimal mock AnalysisState for testing."""
    state = MagicMock()
    if frames is not None:
        state.benchmark.frames_percentiles = frames
    else:
        state.benchmark = None
    if sic_code:
        state.company.sic_code = sic_code
    else:
        state.company = None
    return state


def test_returns_no_data_when_benchmark_absent() -> None:
    """Should return has_data=False when no benchmark data exists."""
    state = _make_state()
    result = build_peer_percentile_context(state)
    assert result["has_data"] is False
    assert result["metrics"] == []
    assert result["filer_count"] == 0


def test_returns_no_data_when_frames_empty() -> None:
    """Should return has_data=False when frames_percentiles is empty dict."""
    state = _make_state(frames={})
    result = build_peer_percentile_context(state)
    assert result["has_data"] is False


def test_direction_aware_coloring_favorable_high() -> None:
    """Operating margin in bottom 25% should get red (high is good, low = risky)."""
    frames = {
        "operating_margin": FramesPercentileResult(
            overall=15.0,
            sector=None,
            peer_count_overall=5000,
            company_value=0.05,
            higher_is_better=True,
        ),
    }
    state = _make_state(frames=frames)
    result = build_peer_percentile_context(state)
    assert result["has_data"] is True
    m = result["metrics"][0]
    assert m["risk_color"] == "var(--do-risk-red)"
    assert m["favorable_direction"] == "high"


def test_direction_aware_coloring_unfavorable_high() -> None:
    """Debt-to-equity in top 25% should get red (high is bad)."""
    frames = {
        "debt_to_equity": FramesPercentileResult(
            overall=85.0,
            sector=60.0,
            peer_count_overall=4000,
            peer_count_sector=200,
            company_value=3.5,
            higher_is_better=False,
        ),
    }
    state = _make_state(frames=frames)
    result = build_peer_percentile_context(state)
    m = result["metrics"][0]
    assert m["risk_color"] == "var(--do-risk-red)"
    assert m["favorable_direction"] == "low"


def test_direction_aware_coloring_neutral() -> None:
    """Revenue (size metric) should always get navy regardless of percentile."""
    frames = {
        "revenue": FramesPercentileResult(
            overall=10.0,
            sector=None,
            peer_count_overall=6000,
            company_value=500_000_000,
            higher_is_better=True,
        ),
    }
    state = _make_state(frames=frames)
    result = build_peer_percentile_context(state)
    m = result["metrics"][0]
    assert m["risk_color"] == "var(--do-navy)"
    assert m["favorable_direction"] == "neutral"


def test_percentile_formatting() -> None:
    """Overall and sector percentiles should be rounded."""
    frames = {
        "net_income": FramesPercentileResult(
            overall=72.345,
            sector=55.789,
            peer_count_overall=5000,
            peer_count_sector=300,
            company_value=1_000_000,
            higher_is_better=True,
        ),
    }
    state = _make_state(frames=frames)
    result = build_peer_percentile_context(state)
    m = result["metrics"][0]
    assert m["overall"] == 72.3
    assert m["sector"] == 55.8


def test_full_metric_set() -> None:
    """With all 15 metrics present, all should appear in order."""
    keys = [
        "revenue", "net_income", "operating_income", "operating_margin",
        "net_margin", "roe", "total_assets", "total_equity",
        "total_liabilities", "debt_to_equity", "current_ratio",
        "cash_from_operations", "rd_expense", "current_assets",
        "current_liabilities",
    ]
    frames = {
        k: FramesPercentileResult(
            overall=50.0,
            peer_count_overall=5000,
            company_value=100.0,
        )
        for k in keys
    }
    state = _make_state(frames=frames)
    result = build_peer_percentile_context(state)
    assert len(result["metrics"]) == 15
    assert result["filer_count"] == 5000


def test_company_value_formatting() -> None:
    """Currency metrics formatted with $, ratios with x, margins with %."""
    frames = {
        "revenue": FramesPercentileResult(
            overall=50.0, peer_count_overall=5000, company_value=5_000_000_000,
        ),
        "current_ratio": FramesPercentileResult(
            overall=50.0, peer_count_overall=5000, company_value=1.85,
        ),
        "operating_margin": FramesPercentileResult(
            overall=50.0, peer_count_overall=5000, company_value=0.15,
        ),
    }
    state = _make_state(frames=frames)
    result = build_peer_percentile_context(state)
    by_key = {m["key"]: m for m in result["metrics"]}
    assert "$" in by_key["revenue"]["company_value"]
    assert "x" in by_key["current_ratio"]["company_value"]
    # operating_margin uses format_percentage
    assert "%" in by_key["operating_margin"]["company_value"]
