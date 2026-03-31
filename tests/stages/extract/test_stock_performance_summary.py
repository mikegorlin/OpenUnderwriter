"""Tests for multi-horizon returns and analyst consensus structuring.

Phase 119-02 Task 2: TDD tests for compute_multi_horizon_returns()
and build_analyst_consensus() including narrative generation (STOCK-06).
"""

from __future__ import annotations

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import AnalystSentimentProfile
from do_uw.stages.extract.stock_performance_summary import (
    _generate_analyst_narrative,
    build_analyst_consensus,
    compute_multi_horizon_returns,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _sourced_float(val: float) -> SourcedValue[float]:
    return SourcedValue[float](
        value=val, source="test", confidence=Confidence.MEDIUM, as_of="2025-01-01",
    )


def _sourced_int(val: int) -> SourcedValue[int]:
    return SourcedValue[int](
        value=val, source="test", confidence=Confidence.MEDIUM, as_of="2025-01-01",
    )


def _sourced_str(val: str) -> SourcedValue[str]:
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.MEDIUM, as_of="2025-01-01",
    )


def _make_profile(
    coverage: int = 15,
    consensus: str = "Overweight",
    rec_mean: float = 2.1,
    target_mean: float = 185.0,
    target_high: float = 220.0,
    target_low: float = 150.0,
    upgrades: int = 3,
    downgrades: int = 1,
) -> AnalystSentimentProfile:
    return AnalystSentimentProfile(
        coverage_count=_sourced_int(coverage),
        consensus=_sourced_str(consensus),
        recommendation_mean=_sourced_float(rec_mean),
        target_price_mean=_sourced_float(target_mean),
        target_price_high=_sourced_float(target_high),
        target_price_low=_sourced_float(target_low),
        recent_upgrades=upgrades,
        recent_downgrades=downgrades,
    )


# ---------------------------------------------------------------------------
# compute_multi_horizon_returns
# ---------------------------------------------------------------------------


class TestMultiHorizonReturns:
    """Tests for compute_multi_horizon_returns."""

    def test_empty_prices(self) -> None:
        """Empty price list returns empty dict."""
        assert compute_multi_horizon_returns([]) == {}

    def test_single_price(self) -> None:
        """Single price (< 2) returns empty dict."""
        assert compute_multi_horizon_returns([100.0]) == {}

    def test_short_list_1d_only(self) -> None:
        """3-price list can compute 1D return only."""
        result = compute_multi_horizon_returns([100.0, 102.0, 105.0])
        assert "1D" in result
        assert result["1D"] is not None
        # 1D return: (105 - 102) / 102 * 100 = ~2.94%
        assert abs(result["1D"] - 2.94) < 0.1

    def test_all_horizons_with_enough_data(self) -> None:
        """With >252 prices, all 6 horizons are populated."""
        # Generate 300 prices from 100 to ~130 (linear ramp)
        prices = [100.0 + i * 0.1 for i in range(300)]
        result = compute_multi_horizon_returns(prices)
        for key in ["1D", "5D", "1M", "3M", "6M", "52W"]:
            assert key in result, f"Missing horizon: {key}"
            assert result[key] is not None, f"None for horizon: {key}"

    def test_insufficient_data_returns_none(self) -> None:
        """Horizons beyond available data return None."""
        # 10 prices: can compute 1D and 5D, not 1M (21) or beyond
        prices = [100.0 + i for i in range(10)]
        result = compute_multi_horizon_returns(prices)
        assert result["1D"] is not None
        assert result["5D"] is not None
        assert result["1M"] is None
        assert result["3M"] is None
        assert result["6M"] is None
        assert result["52W"] is None

    def test_since_ipo_added_for_recent_listing(self) -> None:
        """Since IPO return added when trading_days < 252."""
        prices = [100.0, 110.0, 120.0]
        result = compute_multi_horizon_returns(prices, trading_days_available=100)
        assert "Since IPO" in result
        # (120 - 100) / 100 * 100 = 20.0%
        assert result["Since IPO"] == 20.0

    def test_no_since_ipo_for_established(self) -> None:
        """No Since IPO key when trading_days >= 252."""
        prices = [100.0, 110.0, 120.0]
        result = compute_multi_horizon_returns(prices, trading_days_available=300)
        assert "Since IPO" not in result

    def test_zero_prior_price(self) -> None:
        """Zero prior price returns None for that horizon."""
        # First price is 0: Since IPO would divide by zero
        prices = [0.0, 100.0, 120.0]
        result = compute_multi_horizon_returns(prices, trading_days_available=100)
        assert result.get("Since IPO") is None or "Since IPO" not in result


# ---------------------------------------------------------------------------
# build_analyst_consensus
# ---------------------------------------------------------------------------


class TestBuildAnalystConsensus:
    """Tests for build_analyst_consensus."""

    def test_empty_profile(self) -> None:
        """Empty profile returns empty dict."""
        empty = AnalystSentimentProfile()
        result = build_analyst_consensus(empty)
        assert result == {}

    def test_full_profile(self) -> None:
        """Full profile returns structured dict with all keys."""
        profile = _make_profile()
        market_data = {
            "recommendations_summary": {
                "period": ["0m"],
                "strongBuy": [5],
                "buy": [7],
                "hold": [2],
                "sell": [1],
                "strongSell": [0],
            },
        }
        result = build_analyst_consensus(profile, market_data=market_data, current_price=162.0)

        assert "rating_distribution" in result
        assert "mean_target" in result
        assert "high_target" in result
        assert "low_target" in result
        assert "upside_pct" in result
        assert "coverage_count" in result
        assert "consensus_label" in result
        assert "narrative" in result

    def test_rating_distribution_from_recommendations_summary(self) -> None:
        """Rating distribution sourced from recommendations_summary, NOT recommendations."""
        profile = _make_profile()
        market_data = {
            "recommendations_summary": {
                "period": ["0m"],
                "strongBuy": [5],
                "buy": [7],
                "hold": [2],
                "sell": [1],
                "strongSell": [0],
            },
            # This should NOT be used for counts
            "recommendations": {
                "firm": ["Goldman"],
                "toGrade": ["Overweight"],
                "fromGrade": ["Equal-Weight"],
                "action": ["up"],
            },
        }
        result = build_analyst_consensus(profile, market_data=market_data, current_price=162.0)
        dist = result["rating_distribution"]
        assert dist["strongBuy"] == 5
        assert dist["buy"] == 7
        assert dist["hold"] == 2
        assert dist["sell"] == 1
        assert dist["strongSell"] == 0

    def test_upside_calculation(self) -> None:
        """Upside pct computed from target mean vs current price."""
        profile = _make_profile(target_mean=185.0)
        result = build_analyst_consensus(profile, current_price=162.0)
        # (185 - 162) / 162 * 100 = ~14.2%
        assert result["upside_pct"] is not None
        assert abs(result["upside_pct"] - 14.2) < 0.2

    def test_narrative_present(self) -> None:
        """Narrative key (STOCK-06) present and non-empty with full data."""
        profile = _make_profile()
        result = build_analyst_consensus(profile, current_price=162.0)
        assert "narrative" in result
        assert len(result["narrative"]) > 0
        assert "Overweight" in result["narrative"]

    def test_no_bare_float(self) -> None:
        """Verify no bare float() in the module source (uses safe_float)."""
        import inspect
        import do_uw.stages.extract.stock_performance_summary as mod

        source = inspect.getsource(mod)
        import re
        # Find lines with bare float() that are not safe_float()
        bare_floats: list[str] = []
        for line in source.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("def "):
                continue
            if "float(" in stripped and "safe_float(" not in stripped:
                if re.search(r'(?<!safe_)float\(', stripped):
                    bare_floats.append(stripped)
        assert len(bare_floats) == 0, f"Found bare float() calls: {bare_floats}"


# ---------------------------------------------------------------------------
# _generate_analyst_narrative
# ---------------------------------------------------------------------------


class TestGenerateAnalystNarrative:
    """Tests for _generate_analyst_narrative (STOCK-06)."""

    def test_full_data(self) -> None:
        """Full data produces comprehensive narrative."""
        narrative = _generate_analyst_narrative(
            consensus_label="Overweight",
            recommendation_mean=2.1,
            mean_target=185.0,
            current_price=162.0,
            upside_pct=14.2,
            upgrades=3,
            downgrades=1,
            coverage_count=15,
        )
        assert "Overweight" in narrative
        assert "2.1" in narrative
        assert "$185" in narrative
        assert "14.2" in narrative
        assert "15 analysts" in narrative

    def test_partial_data_consensus_only(self) -> None:
        """Partial data: only consensus label."""
        narrative = _generate_analyst_narrative(
            consensus_label="Buy",
            recommendation_mean=None,
            mean_target=None,
            current_price=None,
            upside_pct=None,
            upgrades=0,
            downgrades=0,
            coverage_count=None,
        )
        assert "Buy" in narrative
        assert len(narrative) > 0

    def test_partial_data_targets_only(self) -> None:
        """Partial data: consensus + target price, no upgrades."""
        narrative = _generate_analyst_narrative(
            consensus_label="Hold",
            recommendation_mean=3.0,
            mean_target=100.0,
            current_price=110.0,
            upside_pct=-9.1,
            upgrades=0,
            downgrades=0,
            coverage_count=None,
        )
        assert "Hold" in narrative
        assert "$100" in narrative
        assert "downside" in narrative

    def test_no_data_returns_empty(self) -> None:
        """No consensus label and no recommendation mean -> empty string."""
        narrative = _generate_analyst_narrative(
            consensus_label="",
            recommendation_mean=None,
            mean_target=None,
            current_price=None,
            upside_pct=None,
            upgrades=0,
            downgrades=0,
            coverage_count=None,
        )
        assert narrative == ""

    def test_upgrades_downgrades_included(self) -> None:
        """Upgrades/downgrades mentioned when present."""
        narrative = _generate_analyst_narrative(
            consensus_label="Overweight",
            recommendation_mean=2.0,
            mean_target=None,
            current_price=None,
            upside_pct=None,
            upgrades=5,
            downgrades=2,
            coverage_count=None,
        )
        assert "5 upgrade" in narrative
        assert "2 downgrade" in narrative
