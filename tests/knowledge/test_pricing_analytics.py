"""Tests for the market positioning analytics engine."""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.knowledge.pricing_analytics import (
    MarketPositionEngine,
    _classify_confidence,
    _t_value,
    compute_market_position,
    compute_trends,
)
from do_uw.knowledge.pricing_store import PricingStore
from do_uw.models.pricing import MarketCapTier, QuoteInput, QuoteStatus


class TestTValueLookup:
    """Test t-distribution critical value lookup."""

    def test_t_value_exact_match(self) -> None:
        """Exact table entries return correct values."""
        assert _t_value(2) == 4.303
        assert _t_value(10) == 2.228
        assert _t_value(30) == 2.042
        assert _t_value(100) == 1.984

    def test_t_value_below_two(self) -> None:
        """n < 2 returns 0.0."""
        assert _t_value(0) == 0.0
        assert _t_value(1) == 0.0

    def test_t_value_above_hundred(self) -> None:
        """n > 100 returns normal approximation 1.96."""
        assert _t_value(101) == 1.96
        assert _t_value(500) == 1.96

    def test_t_value_interpolation(self) -> None:
        """Intermediate values are interpolated."""
        t12 = _t_value(12)
        # Should be between t(10)=2.228 and t(15)=2.145
        assert 2.145 < t12 < 2.228


class TestClassifyConfidence:
    """Test confidence level classification."""

    def test_insufficient(self) -> None:
        assert _classify_confidence(0) == "INSUFFICIENT"
        assert _classify_confidence(2) == "INSUFFICIENT"

    def test_low(self) -> None:
        assert _classify_confidence(3) == "LOW"
        assert _classify_confidence(9) == "LOW"

    def test_medium(self) -> None:
        assert _classify_confidence(10) == "MEDIUM"
        assert _classify_confidence(49) == "MEDIUM"

    def test_high(self) -> None:
        assert _classify_confidence(50) == "HIGH"
        assert _classify_confidence(100) == "HIGH"


class TestComputeMarketPosition:
    """Test pure market position computation."""

    def test_insufficient_data(self) -> None:
        """2 rates returns INSUFFICIENT with None stats."""
        pos = compute_market_position([0.05, 0.06])
        assert pos.peer_count == 2
        assert pos.confidence_level == "INSUFFICIENT"
        assert pos.median_rate_on_line is None
        assert pos.ci_low is None
        assert pos.trend_direction == "INSUFFICIENT_DATA"

    def test_empty_rates(self) -> None:
        """Empty list returns INSUFFICIENT."""
        pos = compute_market_position([])
        assert pos.peer_count == 0
        assert pos.confidence_level == "INSUFFICIENT"
        assert pos.median_rate_on_line is None

    def test_low_confidence(self) -> None:
        """5 rates gives LOW confidence with computed stats."""
        rates = [0.04, 0.05, 0.06, 0.07, 0.08]
        pos = compute_market_position(rates)
        assert pos.peer_count == 5
        assert pos.confidence_level == "LOW"
        assert pos.median_rate_on_line == 0.06
        assert pos.mean_rate_on_line is not None
        assert pos.ci_low is not None
        assert pos.ci_high is not None
        assert pos.ci_low < pos.mean_rate_on_line < pos.ci_high

    def test_sufficient_data(self) -> None:
        """10+ rates gives MEDIUM confidence with full stats."""
        rates = [0.03, 0.04, 0.045, 0.05, 0.055,
                 0.06, 0.065, 0.07, 0.075, 0.08]
        pos = compute_market_position(rates)
        assert pos.peer_count == 10
        assert pos.confidence_level == "MEDIUM"
        assert pos.median_rate_on_line is not None
        assert pos.mean_rate_on_line is not None
        assert pos.ci_low is not None
        assert pos.ci_high is not None
        assert pos.percentile_25 is not None
        assert pos.percentile_75 is not None
        assert pos.min_rate == 0.03
        assert pos.max_rate == 0.08
        # CI should bracket mean
        assert pos.ci_low < pos.mean_rate_on_line < pos.ci_high

    def test_high_confidence(self) -> None:
        """60 rates gives HIGH confidence."""
        import random
        rng = random.Random(42)  # noqa: S311
        rates = [0.05 + rng.gauss(0, 0.01) for _ in range(60)]
        pos = compute_market_position(rates)
        assert pos.peer_count == 60
        assert pos.confidence_level == "HIGH"
        assert pos.ci_low is not None
        assert pos.ci_high is not None
        # CI should be tighter than the full range
        assert pos.ci_high - pos.ci_low < pos.max_rate - pos.min_rate  # type: ignore[operator]

    def test_trend_hardening(self) -> None:
        """Rising rates across halves detected as HARDENING."""
        # First half: lower rates, second half: higher rates
        rates = [0.04, 0.042, 0.043, 0.041, 0.045,
                 0.06, 0.062, 0.065, 0.058, 0.061]
        dates = [
            datetime(2025, 1, i + 1, tzinfo=UTC) for i in range(5)
        ] + [
            datetime(2025, 7, i + 1, tzinfo=UTC) for i in range(5)
        ]
        pos = compute_market_position(rates, dates)
        assert pos.trend_direction == "HARDENING"
        assert pos.trend_magnitude_pct is not None
        assert pos.trend_magnitude_pct > 5.0
        assert "2025-01" in pos.data_window
        assert "2025-07" in pos.data_window

    def test_trend_softening(self) -> None:
        """Falling rates across halves detected as SOFTENING."""
        rates = [0.08, 0.079, 0.082, 0.081, 0.078,
                 0.05, 0.052, 0.048, 0.051, 0.053]
        dates = [
            datetime(2025, 1, i + 1, tzinfo=UTC) for i in range(5)
        ] + [
            datetime(2025, 7, i + 1, tzinfo=UTC) for i in range(5)
        ]
        pos = compute_market_position(rates, dates)
        assert pos.trend_direction == "SOFTENING"
        assert pos.trend_magnitude_pct is not None
        assert pos.trend_magnitude_pct < -5.0

    def test_stable_trend(self) -> None:
        """Small change between halves gives STABLE."""
        rates = [0.050, 0.051, 0.049, 0.052, 0.050,
                 0.051, 0.050, 0.052, 0.049, 0.051]
        dates = [
            datetime(2025, 1, i + 1, tzinfo=UTC) for i in range(5)
        ] + [
            datetime(2025, 7, i + 1, tzinfo=UTC) for i in range(5)
        ]
        pos = compute_market_position(rates, dates)
        assert pos.trend_direction == "STABLE"

    def test_single_period_no_trend(self) -> None:
        """Data from one half-year period cannot establish trend."""
        rates = [0.04, 0.05, 0.06, 0.07, 0.08]
        # All dates in same half-year — no trend possible
        dates = [
            datetime(2025, 2, i + 1, tzinfo=UTC) for i in range(5)
        ]
        pos = compute_market_position(rates, dates)
        assert pos.trend_direction == "INSUFFICIENT_DATA"
        assert pos.trend_magnitude_pct is None

    def test_no_dates_no_trend(self) -> None:
        """Rates without dates cannot establish trend."""
        rates = [0.04, 0.05, 0.06, 0.07, 0.08]
        pos = compute_market_position(rates)
        assert pos.trend_direction == "INSUFFICIENT_DATA"
        assert pos.trend_magnitude_pct is None


class TestComputeTrends:
    """Test trend computation from rate/date pairs."""

    def test_multiple_periods(self) -> None:
        """Rates across 3 half-years produce 3 TrendPoints."""
        data: list[tuple[float, datetime]] = [
            (0.04, datetime(2024, 3, 1, tzinfo=UTC)),
            (0.045, datetime(2024, 5, 1, tzinfo=UTC)),
            (0.05, datetime(2024, 9, 1, tzinfo=UTC)),
            (0.052, datetime(2024, 11, 1, tzinfo=UTC)),
            (0.06, datetime(2025, 2, 1, tzinfo=UTC)),
            (0.058, datetime(2025, 4, 1, tzinfo=UTC)),
        ]
        points = compute_trends(data)
        assert len(points) == 3
        assert points[0].period == "2024-H1"
        assert points[0].count == 2
        assert points[1].period == "2024-H2"
        assert points[1].count == 2
        assert points[2].period == "2025-H1"
        assert points[2].count == 2

    def test_empty_data(self) -> None:
        """Empty input returns empty list."""
        assert compute_trends([]) == []

    def test_single_period(self) -> None:
        """All data in one period returns one point."""
        data: list[tuple[float, datetime]] = [
            (0.04, datetime(2025, 1, 15, tzinfo=UTC)),
            (0.05, datetime(2025, 3, 15, tzinfo=UTC)),
        ]
        points = compute_trends(data)
        assert len(points) == 1
        assert points[0].period == "2025-H1"
        assert points[0].count == 2


class TestMarketPositionEngine:
    """Integration tests with PricingStore."""

    def _make_quote(
        self,
        ticker: str,
        premium: float,
        limit: float,
        effective: datetime,
        cap_tier: MarketCapTier = MarketCapTier.LARGE,
        sector: str | None = "TECH",
        quality_score: float | None = None,
    ) -> QuoteInput:
        return QuoteInput(
            ticker=ticker,
            company_name=f"{ticker} Inc.",
            effective_date=effective,
            quote_date=effective,
            status=QuoteStatus.QUOTED,
            total_limit=limit,
            total_premium=premium,
            market_cap_tier=cap_tier,
            sector=sector,
            quality_score=quality_score,
            source="test",
        )

    def test_integration_market_position(self) -> None:
        """Engine queries store and returns valid MarketPosition."""
        store = PricingStore(db_path=None)

        # Add 5 quotes with different rates
        for i in range(5):
            q = self._make_quote(
                ticker=f"T{i}",
                premium=50_000 + i * 10_000,
                limit=1_000_000,
                effective=datetime(2025, 6, i + 1, tzinfo=UTC),
            )
            store.add_quote(q)

        engine = MarketPositionEngine(store)
        pos = engine.get_market_position(
            market_cap_tier="LARGE", sector="TECH"
        )

        assert pos.peer_count == 5
        assert pos.confidence_level == "LOW"
        assert pos.median_rate_on_line is not None
        assert pos.mean_rate_on_line is not None
        assert pos.ci_low is not None

    def test_integration_trends(self) -> None:
        """Engine computes trends from store data."""
        store = PricingStore(db_path=None)

        # Add quotes across two half-years
        dates_h1 = [datetime(2025, i, 1, tzinfo=UTC) for i in range(1, 4)]
        dates_h2 = [datetime(2025, i, 1, tzinfo=UTC) for i in range(7, 10)]

        for i, dt in enumerate(dates_h1 + dates_h2):
            q = self._make_quote(
                ticker=f"T{i}",
                premium=50_000 + i * 5_000,
                limit=1_000_000,
                effective=dt,
            )
            store.add_quote(q)

        engine = MarketPositionEngine(store)
        trends = engine.get_trends(
            market_cap_tier="LARGE", sector="TECH"
        )

        assert trends.total_quotes == 6
        assert len(trends.points) == 2
        assert trends.segment_label == "LARGE / TECH"

    def test_get_position_for_analysis(self) -> None:
        """Convenience method returns position for company profile."""
        store = PricingStore(db_path=None)

        for i in range(4):
            q = self._make_quote(
                ticker=f"T{i}",
                premium=60_000,
                limit=1_000_000,
                effective=datetime(2025, 6, i + 1, tzinfo=UTC),
            )
            store.add_quote(q)

        engine = MarketPositionEngine(store)
        pos = engine.get_position_for_analysis(
            ticker="AAPL",
            quality_score=65.0,
            market_cap_tier="LARGE",
            sector="TECH",
        )
        assert pos.peer_count == 4
        assert pos.confidence_level == "LOW"
