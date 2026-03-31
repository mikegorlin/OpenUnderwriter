"""Tests for stock performance and drop detection extractors.

Covers: single/multi-day drops, stable stock, performance metrics,
max drawdown, sector comparison, trigger attribution, missing data,
extraction report, NaN handling, daily returns, worst drop ID.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.market_events import DropType
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.stock_drops import (
    compute_daily_returns,
    compute_sector_comparison,
    find_multi_day_drops,
    find_single_day_drops,
    get_close_prices,
)
from do_uw.stages.extract.stock_performance import (
    EXPECTED_FIELDS,
    compute_max_drawdown,
    compute_volatility,
    extract_stock_performance,
)

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_state(
    market_data: dict[str, Any] | None = None,
    filings: dict[str, Any] | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState for stock performance testing."""
    identity = CompanyIdentity(
        ticker="TEST",
        cik=_sourced_str("0001234567"),
        sic_code=_sourced_str("7372"),
        sector=_sourced_str("TECH"),
    )
    profile = CompanyProfile(identity=identity)

    return AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=AcquiredData(
            market_data=market_data or {},
            filings=filings or {},
        ),
    )


def _make_history(
    prices: list[float],
    start_date: str = "2025-01-02",
) -> dict[str, Any]:
    """Build a synthetic price history dict matching yfinance format.

    Creates dates incrementing by 1 day from start_date.
    """
    dates: list[str] = []
    base_year = int(start_date[:4])
    base_month = int(start_date[5:7])
    base_day = int(start_date[8:10])

    for i in range(len(prices)):
        day = base_day + i
        month = base_month
        year = base_year
        # Simple overflow -- good enough for test data.
        while day > 28:
            day -= 28
            month += 1
        while month > 12:
            month -= 12
            year += 1
        dates.append(f"{year:04d}-{month:02d}-{day:02d}")

    return {
        "Close": prices,
        "Date": dates,
        "Open": prices,
        "High": [p * 1.01 for p in prices],
        "Low": [p * 0.99 for p in prices],
        "Volume": [1000000] * len(prices),
    }


class TestSingleDayDrops:
    """Test single-day drop detection."""

    def test_single_day_drops_detected(self) -> None:
        """Synthetic history with known drops: -6%, -12%, -25%."""
        # Build prices: 100 -> 94 (-6%) -> 94 -> 82.72 (-12%) -> 82.72 -> 62.04 (-25%)
        prices = [100.0, 94.0, 94.0, 82.72, 82.72, 62.04]
        history = _make_history(prices)

        drops = find_single_day_drops(history, threshold_pct=-5.0)

        assert len(drops) == 3
        for drop in drops:
            assert drop.drop_type == DropType.SINGLE_DAY
            assert drop.period_days == 1
            assert drop.drop_pct is not None
            assert drop.drop_pct.value < -5.0
            assert drop.date is not None

    def test_no_drops_stable_stock(self) -> None:
        """Flat price returns empty drop lists."""
        prices = [100.0, 100.5, 101.0, 100.8, 100.3, 100.7]
        history = _make_history(prices)

        drops = find_single_day_drops(history, threshold_pct=-5.0)

        assert len(drops) == 0

    def test_threshold_boundary(self) -> None:
        """Drop exactly at threshold is included (-5.0%)."""
        prices = [100.0, 95.0]  # Exactly -5%
        history = _make_history(prices)

        drops = find_single_day_drops(history, threshold_pct=-5.0)

        assert len(drops) == 1
        assert drops[0].drop_pct is not None
        assert drops[0].drop_pct.value == -5.0


class TestMultiDayDrops:
    """Test multi-day drop detection."""

    def test_multi_day_drops_detected(self) -> None:
        """Synthetic 5-day declining sequence exceeding -15% threshold."""
        # 5-day decline: 100 -> 95 -> 91 -> 87 -> 84 -> 80 = -20%
        prices = [100.0, 95.0, 91.0, 87.0, 84.0, 80.0, 80.0]
        history = _make_history(prices)

        drops = find_multi_day_drops(
            history,
            periods=[5],
            thresholds={5: -15.0},
        )

        assert len(drops) >= 1
        for drop in drops:
            assert drop.drop_type == DropType.MULTI_DAY
            assert drop.period_days == 5
            assert drop.drop_pct is not None
            assert drop.drop_pct.value <= -15.0

    def test_multi_day_no_drops(self) -> None:
        """Gradually rising prices produce no multi-day drops."""
        prices = [100.0 + i * 0.5 for i in range(30)]
        history = _make_history(prices)

        drops = find_multi_day_drops(history)

        assert len(drops) == 0


class TestPerformanceMetrics:
    """Test performance metric computations."""

    def test_performance_metrics_computed(self) -> None:
        """Returns, volatility, max drawdown from known price series."""
        # 1-year: start 100, end 120 -> +20% return
        prices_1y = [100.0 + i * 0.5 for i in range(252)]
        # Inject a drawdown: prices drop from day 100 to 130
        for i in range(100, 131):
            prices_1y[i] = prices_1y[100] - (i - 100) * 1.0

        history_1y = _make_history(prices_1y)
        info: dict[str, Any] = {
            "currentPrice": prices_1y[-1],
            "beta": 1.15,
            "fiftyTwoWeekHigh": max(prices_1y),
            "fiftyTwoWeekLow": min(prices_1y),
        }

        state = _make_state(
            market_data={"history_1y": history_1y, "info": info}
        )
        perf, _, _report = extract_stock_performance(state)

        assert perf.current_price is not None
        assert perf.returns_1y is not None
        assert perf.beta is not None
        assert perf.beta.value == 1.15
        assert perf.volatility_90d is not None
        assert perf.max_drawdown_1y is not None
        assert perf.max_drawdown_1y.value < 0.0

    def test_max_drawdown_calculation(self) -> None:
        """Known peak-to-trough sequence produces correct drawdown."""
        # Peak at 200, trough at 120 -> -40% drawdown
        prices = [100.0, 150.0, 200.0, 160.0, 120.0, 140.0, 180.0]
        mdd = compute_max_drawdown(prices)

        assert mdd is not None
        assert mdd == -40.0

    def test_max_drawdown_no_drawdown(self) -> None:
        """Monotonically increasing prices return None drawdown."""
        prices = [100.0, 110.0, 120.0, 130.0]
        mdd = compute_max_drawdown(prices)

        assert mdd is None

    def test_volatility_computation(self) -> None:
        """Volatility is computed and is positive for varying prices."""
        prices = [100.0, 102.0, 98.0, 103.0, 97.0, 105.0, 94.0, 106.0]
        vol = compute_volatility(prices, window=90)

        assert vol is not None
        assert vol > 0.0

    def test_volatility_insufficient_data(self) -> None:
        """Volatility returns None with < 2 prices."""
        assert compute_volatility([100.0], window=90) is None
        assert compute_volatility([], window=90) is None


class TestSectorComparison:
    """Test sector ETF comparison logic."""

    def test_sector_comparison(self) -> None:
        """Mock sector history: stock drops more than sector -> company-specific."""
        from do_uw.models.market_events import StockDropEvent
        from do_uw.stages.extract.sourced import sourced_float, sourced_str

        drop = StockDropEvent(
            date=sourced_str("2025-06-10", "test", Confidence.MEDIUM),
            drop_pct=sourced_float(-15.0, "test", Confidence.MEDIUM),
            drop_type=DropType.SINGLE_DAY,
            period_days=1,
        )

        # Sector only dropped -2% on same day.
        sector_history: dict[str, Any] = {
            "Close": [100.0, 98.0],
            "Date": ["2025-06-09", "2025-06-10"],
        }

        result = compute_sector_comparison(drop, sector_history)

        assert result.is_company_specific is True
        assert result.sector_return_pct is not None
        assert result.sector_return_pct.value == -2.0

    def test_sector_comparison_not_company_specific(self) -> None:
        """Sector dropped more than company -> not company-specific."""
        from do_uw.models.market_events import StockDropEvent
        from do_uw.stages.extract.sourced import sourced_float, sourced_str

        drop = StockDropEvent(
            date=sourced_str("2025-06-10", "test", Confidence.MEDIUM),
            drop_pct=sourced_float(-5.0, "test", Confidence.MEDIUM),
            drop_type=DropType.SINGLE_DAY,
            period_days=1,
        )

        # Sector dropped -8%.
        sector_history: dict[str, Any] = {
            "Close": [100.0, 92.0],
            "Date": ["2025-06-09", "2025-06-10"],
        }

        result = compute_sector_comparison(drop, sector_history)

        assert result.is_company_specific is False


class TestTriggerAttribution:
    """Test trigger attribution from 8-K and earnings dates."""

    def test_trigger_attribution_earnings(self) -> None:
        """Drop near earnings date gets 'earnings_release' trigger."""
        prices = [100.0, 93.0]  # -7% drop on 2025-06-11
        history = _make_history(prices, start_date="2025-06-10")

        filings: dict[str, Any] = {}
        market_data: dict[str, Any] = {
            "history_1y": history,
            "info": {"currentPrice": 93.0},
            "earnings_dates": {"Date": ["2025-06-11"]},
        }

        state = _make_state(market_data=market_data, filings=filings)
        _, drops, _ = extract_stock_performance(state)

        sd = drops.single_day_drops
        assert len(sd) >= 1
        assert sd[0].trigger_event is not None
        assert sd[0].trigger_event.value == "earnings_release"

    def test_trigger_attribution_8k(self) -> None:
        """Drop near 8-K filing date gets '8-K_filing' trigger."""
        prices = [100.0, 92.0]  # -8% drop on 2025-03-16
        history = _make_history(prices, start_date="2025-03-15")

        filings: dict[str, Any] = {
            "8-K": {"filing_date": "2025-03-16"},
        }
        market_data: dict[str, Any] = {
            "history_1y": history,
            "info": {"currentPrice": 92.0},
        }

        state = _make_state(market_data=market_data, filings=filings)
        _, drops, _ = extract_stock_performance(state)

        sd = drops.single_day_drops
        assert len(sd) >= 1
        assert sd[0].trigger_event is not None
        assert sd[0].trigger_event.value == "8-K_filing"


class TestGracefulHandling:
    """Test graceful handling of missing or bad data."""

    def test_missing_data_graceful(self) -> None:
        """Empty market_data returns empty results and a report."""
        state = _make_state(market_data={})
        perf, drops, report = extract_stock_performance(state)

        assert perf.current_price is None
        assert len(drops.single_day_drops) == 0
        assert len(drops.multi_day_drops) == 0
        assert report.extractor_name == "stock_performance"
        assert report.coverage_pct == 0.0

    def test_null_prices_handled(self) -> None:
        """None/NaN values in Close prices don't crash."""
        import math

        history: dict[str, Any] = {
            "Close": [100.0, None, float("nan"), 95.0, None, 90.0],
            "Date": [
                "2025-01-01", "2025-01-02", "2025-01-03",
                "2025-01-04", "2025-01-05", "2025-01-06",
            ],
        }

        prices = get_close_prices(history)

        # Only valid floats should remain.
        assert len(prices) == 3
        assert all(not math.isnan(p) for p in prices)
        assert prices == [100.0, 95.0, 90.0]

    def test_no_acquired_data(self) -> None:
        """State with acquired_data=None returns empty results."""
        state = AnalysisState(ticker="TEST")
        perf, drops, report = extract_stock_performance(state)

        assert perf.current_price is None
        assert len(drops.single_day_drops) == 0
        assert report.coverage_pct == 0.0


class TestExtractionReport:
    """Test ExtractionReport coverage tracking."""

    def test_extraction_report_coverage(self) -> None:
        """Report tracks expected vs found fields correctly."""
        prices = [100.0 + i * 0.3 for i in range(252)]
        history_1y = _make_history(prices)
        info: dict[str, Any] = {
            "currentPrice": prices[-1],
            "beta": 1.2,
        }

        state = _make_state(
            market_data={"history_1y": history_1y, "info": info}
        )
        _, _, report = extract_stock_performance(state)

        assert report.extractor_name == "stock_performance"
        assert set(report.expected_fields) == set(EXPECTED_FIELDS)
        # Should find at least current_price, returns_1y, beta, volatility, max_drawdown
        assert "current_price" in report.found_fields
        assert "returns_1y" in report.found_fields
        assert "beta" in report.found_fields
        assert report.coverage_pct > 0.0

    def test_report_all_fields_found(self) -> None:
        """With drops + metrics, coverage is 100%."""
        # Prices with a big drop to trigger single_day_drops.
        prices = [100.0] * 10 + [80.0] + [80.0] * 240
        # Also need a multi-day drop: 5-day drop from 100 to 80 = -20%
        prices[0:6] = [100.0, 97.0, 93.0, 90.0, 87.0, 80.0]
        history = _make_history(prices)

        info: dict[str, Any] = {
            "currentPrice": 80.0,
            "beta": 1.3,
        }

        state = _make_state(
            market_data={"history_1y": history, "info": info}
        )
        _, _, report = extract_stock_performance(state)

        # Should find single_day_drops + most metrics.
        assert "single_day_drops" in report.found_fields
        assert "current_price" in report.found_fields


class TestDailyReturns:
    """Test daily returns computation helper."""

    def test_daily_returns(self) -> None:
        """Compute daily returns from known prices."""
        prices = [100.0, 110.0, 99.0]
        returns = compute_daily_returns(prices)

        assert len(returns) == 2
        assert abs(returns[0] - 10.0) < 0.01  # 100 -> 110 = +10%
        assert abs(returns[1] - (-10.0)) < 0.01  # 110 -> 99 = -10%

    def test_daily_returns_empty(self) -> None:
        """Empty or single price returns empty list."""
        assert compute_daily_returns([]) == []
        assert compute_daily_returns([100.0]) == []


class TestWorstDropIdentification:
    """Test that worst_single_day and worst_multi_day are set correctly."""

    def test_worst_single_day_identified(self) -> None:
        """Worst single-day drop is correctly identified."""
        # Three drops: -6%, -12%, -25%
        prices = [100.0, 94.0, 94.0, 82.72, 82.72, 62.04]
        history = _make_history(prices)

        state = _make_state(
            market_data={
                "history_1y": history,
                "info": {"currentPrice": 62.04},
            }
        )
        _, drops, _ = extract_stock_performance(state)

        assert drops.worst_single_day is not None
        assert drops.worst_single_day.drop_pct is not None
        # The -25% drop should be the worst.
        assert drops.worst_single_day.drop_pct.value < -20.0
