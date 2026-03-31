"""Tests for Phase 119 stock catalyst + performance summary context builders."""

from __future__ import annotations

import pytest

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.stock_catalyst_context import (
    build_stock_catalyst_context,
    build_stock_performance_summary,
)


@pytest.fixture
def state() -> AnalysisState:
    return AnalysisState(ticker="TEST")


# ---------------------------------------------------------------------------
# build_stock_catalyst_context
# ---------------------------------------------------------------------------


class TestBuildStockCatalystContext:
    def test_empty_input(self, state: AnalysisState) -> None:
        result = build_stock_catalyst_context(state)
        assert result["enhanced_drop_events"] == []
        assert result["stock_patterns"] == []
        assert result["drop_narrative"] == ""
        assert result["has_catalyst_data"] is False

    def test_with_drop_events_no_assessment(self, state: AnalysisState) -> None:
        events = [{"date": "2025-01-15", "drop_pct": "8.3%", "do_assessment": ""}]
        result = build_stock_catalyst_context(state, drop_events=events)
        assert result["enhanced_drop_events"] == events
        assert result["has_catalyst_data"] is False

    def test_with_drop_events_with_assessment(self, state: AnalysisState) -> None:
        events = [
            {
                "date": "2025-01-15",
                "drop_pct": "8.3%",
                "trigger": "Earnings Miss",
                "do_assessment": "Revenue miss of 12% creates 10b-5 exposure.",
            }
        ]
        result = build_stock_catalyst_context(state, drop_events=events)
        assert result["has_catalyst_data"] is True

    def test_with_patterns(self, state: AnalysisState) -> None:
        patterns = [
            {
                "type": "multi_day_cluster",
                "description": "3 drops within 5 days",
                "dates": "2025-01-10, 2025-01-12, 2025-01-14",
                "do_relevance": "Strengthens corrective disclosure theory.",
            }
        ]
        result = build_stock_catalyst_context(state, patterns=patterns)
        assert len(result["stock_patterns"]) == 1

    def test_with_narrative(self, state: AnalysisState) -> None:
        result = build_stock_catalyst_context(
            state, drop_narrative="Stock declined 27.9% over 326 trading days."
        )
        assert result["drop_narrative"] == "Stock declined 27.9% over 326 trading days."


# ---------------------------------------------------------------------------
# build_stock_performance_summary
# ---------------------------------------------------------------------------


class TestBuildStockPerformanceSummary:
    def test_empty_input(self, state: AnalysisState) -> None:
        result = build_stock_performance_summary(state)
        assert result["horizons"] == []
        assert result["analyst"] == {}
        assert result["has_performance_data"] is False

    def test_with_horizon_returns(self, state: AnalysisState) -> None:
        returns = {"1D": 0.5, "5D": -1.2, "1M": 3.4, "52W": None}
        result = build_stock_performance_summary(state, multi_horizon_returns=returns)
        assert result["has_performance_data"] is True
        assert len(result["horizons"]) == 4
        assert result["horizons"][0] == {"label": "1D", "return_pct": "+0.50%"}
        assert result["horizons"][1] == {"label": "5D", "return_pct": "-1.20%"}
        assert result["horizons"][3] == {"label": "52W", "return_pct": "N/A"}

    def test_with_analyst_consensus(self, state: AnalysisState) -> None:
        consensus = {
            "consensus_label": "Overweight",
            "mean_target": 185.0,
            "coverage_count": 15,
            "narrative": "Analyst consensus is Overweight.",
        }
        result = build_stock_performance_summary(state, analyst_consensus=consensus)
        assert result["has_performance_data"] is True
        assert result["analyst"]["consensus_label"] == "Overweight"
        assert result["analyst"]["narrative"] == "Analyst consensus is Overweight."

    def test_with_both(self, state: AnalysisState) -> None:
        returns = {"1M": 5.0}
        consensus = {"consensus_label": "Buy", "narrative": "Strong buy."}
        result = build_stock_performance_summary(
            state, multi_horizon_returns=returns, analyst_consensus=consensus
        )
        assert result["has_performance_data"] is True
        assert len(result["horizons"]) == 1
        assert result["analyst"]["consensus_label"] == "Buy"
