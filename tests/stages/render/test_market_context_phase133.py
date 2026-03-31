"""Tests for Phase 133-02 market context builders.

Covers volume anomalies, EPS revision trends, analyst targets,
correlation metrics, and earnings trust narrative builders.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from do_uw.models.state import AnalysisState

from do_uw.stages.render.context_builders._market_acquired_data import (
    build_analyst_targets,
    build_earnings_trust,
    build_eps_revision_trends,
)
from do_uw.stages.render.context_builders._market_correlation import (
    build_correlation_metrics,
)
from do_uw.stages.render.context_builders._market_volume import (
    build_volume_anomalies,
)


def _make_state(**overrides):
    """Build a minimal mock AnalysisState."""
    state = MagicMock(spec=AnalysisState(ticker="SPEC"))
    state.extracted = MagicMock()
    state.extracted.market = MagicMock()
    state.extracted.market.stock = MagicMock()
    state.extracted.market.stock.current_price = MagicMock()
    state.extracted.market.stock.current_price.value = 100.0
    state.extracted.market.stock.beta = MagicMock()
    state.extracted.market.stock.beta.value = 1.15
    state.extracted.market.stock.volume_spike_events = []
    state.extracted.market.eight_k_items = None
    state.extracted.market.earnings_guidance = MagicMock()
    state.extracted.market.earnings_guidance.quarters = []
    state.extracted.market.earnings_guidance.beat_rate = None
    state.extracted.market.earnings_guidance.consecutive_miss_count = 0
    state.acquired_data = MagicMock()
    state.acquired_data.market_data = {}
    state.ticker = "TEST"
    state.company = MagicMock()
    state.company.name = "Test Corp"
    for k, v in overrides.items():
        parts = k.split(".")
        obj = state
        for p in parts[:-1]:
            obj = getattr(obj, p)
        setattr(obj, parts[-1], v)
    return state


class TestBuildVolumeAnomalies:
    """Test volume anomaly builder."""

    def test_with_spikes(self):
        state = _make_state()
        state.extracted.market.stock.volume_spike_events = [
            {
                "date": "2025-03-15",
                "volume": 5_000_000,
                "avg_volume": 1_000_000,
                "volume_multiple": 5.0,
                "price_change_pct": -4.2,
            },
            {
                "date": "2025-02-10",
                "volume": 2_500_000,
                "avg_volume": 1_000_000,
                "volume_multiple": 2.5,
                "price_change_pct": 1.3,
            },
        ]
        result = build_volume_anomalies(state)
        assert "volume_anomalies" in result
        rows = result["volume_anomalies"]
        assert len(rows) == 2
        assert rows[0]["multiple"] == "5.0x"
        assert rows[0]["severity"] == "high"
        assert rows[1]["severity"] == "low"  # 2.5x with +1.3% doesn't meet medium threshold

    def test_empty_no_spikes(self):
        state = _make_state()
        state.extracted.market.stock.volume_spike_events = []
        result = build_volume_anomalies(state)
        assert result == {}


class TestBuildEpsRevisionTrends:
    """Test EPS revision trends builder."""

    def test_with_data(self):
        state = _make_state()
        state.acquired_data.market_data = {
            "eps_revisions": {
                "upLast7days": {"0q": 3, "+1q": 2, "0y": 5, "+1y": 4},
                "downLast7days": {"0q": 1, "+1q": 0, "0y": 2, "+1y": 1},
                "upLast30days": {"0q": 8, "+1q": 6, "0y": 10, "+1y": 9},
                "downLast30days": {"0q": 2, "+1q": 1, "0y": 3, "+1y": 2},
            }
        }
        result = build_eps_revision_trends(state)
        assert "eps_revisions" in result
        rows = result["eps_revisions"]
        assert len(rows) == 4
        assert rows[0]["period"] == "Current Qtr"
        assert rows[0]["net_direction"] == "up"  # 8 - 2 = 6 > 0

    def test_empty_no_data(self):
        state = _make_state()
        state.acquired_data.market_data = {}
        result = build_eps_revision_trends(state)
        assert result == {}


class TestBuildAnalystTargets:
    """Test analyst price target builder."""

    def test_with_targets(self):
        state = _make_state()
        state.acquired_data.market_data = {
            "analyst_price_targets": {
                "low": 80.0,
                "current": 120.0,
                "high": 160.0,
                "numberOfAnalysts": 25,
            }
        }
        result = build_analyst_targets(state)
        assert "analyst_targets" in result
        at = result["analyst_targets"]
        assert at["low"] == "$80.00"
        assert at["mean"] == "$120.00"
        assert at["high"] == "$160.00"
        assert at["upside_pct"] == "+20.0%"  # (120-100)/100 * 100
        assert at["analyst_count"] == 25

    def test_empty_no_data(self):
        state = _make_state()
        state.acquired_data.market_data = {}
        result = build_analyst_targets(state)
        assert result == {}


class TestBuildCorrelationMetrics:
    """Test correlation metrics builder."""

    def test_with_price_data(self):
        # Generate synthetic price data with known correlation
        import math
        n = 252
        base = [100.0 + i * 0.1 + math.sin(i / 10) * 2 for i in range(n)]
        spy = [100.0 + i * 0.08 + math.sin(i / 10) * 1.5 for i in range(n)]
        sector = [100.0 + i * 0.09 + math.sin(i / 10) * 1.8 for i in range(n)]

        state = _make_state()
        state.acquired_data.market_data = {
            "history_1y": {"Close": base},
            "spy_history_1y": {"Close": spy},
            "sector_history_1y": {"Close": sector},
        }
        result = build_correlation_metrics(state)
        assert "correlation_metrics" in result
        cm = result["correlation_metrics"]
        assert cm["corr_spy"] != "N/A"
        assert cm["r_squared"] != "N/A"
        assert cm["idiosyncratic_pct"] != "N/A"
        assert cm["interpretation"]  # Non-empty interpretation

    def test_insufficient_data_falls_back_to_beta(self):
        state = _make_state()
        state.acquired_data.market_data = {
            "history_1y": {"Close": [100.0, 101.0]},  # Too short
        }
        result = build_correlation_metrics(state)
        assert "correlation_metrics" in result
        assert result["correlation_metrics"]["beta"] == "1.15"

    def test_no_data_returns_empty(self):
        state = _make_state()
        state.extracted.market.stock.beta = None
        state.acquired_data.market_data = {}
        result = build_correlation_metrics(state)
        assert result == {}


class TestBuildEarningsTrust:
    """Test earnings trust narrative builder."""

    def test_beat_distrust_pattern(self):
        """Mock quarters where company beats but stock sells off."""
        state = _make_state()
        quarters = []
        for i in range(8):
            q = MagicMock()
            q.quarter = f"Q{(i % 4) + 1} 2025"
            q.consensus_eps_low = MagicMock()
            q.consensus_eps_low.value = 1.0
            q.consensus_eps_high = MagicMock()
            q.consensus_eps_high.value = 1.1
            q.actual_eps = MagicMock()
            q.actual_eps.value = 1.2  # Always beats
            q.result = "BEAT"
            q.stock_reaction_pct = MagicMock()
            q.stock_reaction_pct.value = -2.5  # Stock drops on beat
            q.miss_magnitude_pct = None
            # These fields may not exist yet
            q.next_day_return_pct = None
            q.week_return_pct = None
            quarters.append(q)

        state.extracted.market.earnings_guidance.quarters = quarters
        state.extracted.market.earnings_guidance.beat_rate = MagicMock()
        state.extracted.market.earnings_guidance.beat_rate.value = 1.0
        state.extracted.market.earnings_guidance.consecutive_miss_count = 0

        result = build_earnings_trust(state)
        assert "earnings_trust_narrative" in result
        assert "distrust" in result["earnings_trust_narrative"].lower()
        assert "earnings_reaction" in result
        assert len(result["earnings_reaction"]) == 8

    def test_empty_quarters(self):
        state = _make_state()
        state.extracted.market.earnings_guidance.quarters = []
        result = build_earnings_trust(state)
        assert result == {}

    def test_build_earnings_trust_populates_multi_window_returns(self):
        """STOCK-04 gap closure: verify compute_earnings_reactions() is called
        and multi-window returns appear in reaction rows."""
        state = _make_state()

        # Create quarters with dates matching price history, no pre-populated returns
        quarters = []
        for i, date_str in enumerate(["2025-01-15", "2025-04-15"]):
            q = MagicMock()
            q.quarter = date_str
            q.consensus_eps_low = MagicMock()
            q.consensus_eps_low.value = 1.0
            q.consensus_eps_high = MagicMock()
            q.consensus_eps_high.value = 1.1
            q.actual_eps = MagicMock()
            q.actual_eps.value = 1.15
            q.result = "BEAT"
            q.stock_reaction_pct = MagicMock()
            q.stock_reaction_pct.value = 2.5
            q.miss_magnitude_pct = None
            q.next_day_return_pct = None  # Not pre-populated
            q.week_return_pct = None  # Not pre-populated
            quarters.append(q)

        state.extracted.market.earnings_guidance.quarters = quarters
        state.extracted.market.earnings_guidance.beat_rate = MagicMock()
        state.extracted.market.earnings_guidance.beat_rate.value = 1.0
        state.extracted.market.earnings_guidance.consecutive_miss_count = 0

        # Build price history covering both earnings dates
        # ~100 trading days from 2024-12-01 to 2025-05-01
        import datetime
        dates_dict = {}
        closes_dict = {}
        base_date = datetime.date(2024, 12, 1)
        idx = 0
        price = 100.0
        while base_date <= datetime.date(2025, 5, 1):
            # Skip weekends
            if base_date.weekday() < 5:
                dates_dict[str(idx)] = base_date.isoformat()
                closes_dict[str(idx)] = price + (idx % 7) * 0.5
                idx += 1
            base_date += datetime.timedelta(days=1)

        state.acquired_data.market_data = {
            "history_1y": {"Date": dates_dict, "Close": closes_dict},
            "earnings_dates": {},  # Empty, forcing fallback to quarter dates
        }

        result = build_earnings_trust(state)

        assert "earnings_reaction" in result
        rows = result["earnings_reaction"]
        assert len(rows) == 2

        # At least one row should have computed next_day_return and week_return
        has_next_day = any(r["next_day_return"] != "N/A" for r in rows)
        has_week = any(r["week_return"] != "N/A" for r in rows)
        assert has_next_day, f"Expected non-N/A next_day_return, got: {rows}"
        assert has_week, f"Expected non-N/A week_return, got: {rows}"

        # Day-of return should still be populated (no regression)
        has_day_of = any(r["day_of_return"] != "N/A" for r in rows)
        assert has_day_of, f"Expected non-N/A day_of_return, got: {rows}"
