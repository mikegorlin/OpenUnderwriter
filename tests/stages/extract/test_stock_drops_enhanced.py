"""Tests for enhanced stock drop analysis: recovery, grouping, market-wide.

Covers compute_recovery_days, group_consecutive_drops, and
tag_market_wide_events from stock_drop_analysis.py. Uses synthetic
price data to verify each function's behavior.
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import DropType, StockDropEvent
from do_uw.stages.extract.stock_drop_analysis import (
    compute_recovery_days,
    group_consecutive_drops,
    tag_market_wide_events,
)

_NOW = datetime(2025, 6, 15, tzinfo=UTC)


def _sv_str(value: str) -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    return SourcedValue(
        value=value,
        source="TEST",
        confidence=Confidence.MEDIUM,
        as_of=_NOW,
    )


def _sv_float(value: float) -> SourcedValue[float]:
    """Create a test SourcedValue[float]."""
    return SourcedValue(
        value=value,
        source="TEST",
        confidence=Confidence.MEDIUM,
        as_of=_NOW,
    )


def _make_drop(
    date: str,
    drop_pct: float,
    period_days: int = 1,
    drop_type: str = DropType.SINGLE_DAY,
) -> StockDropEvent:
    """Create a StockDropEvent for testing."""
    return StockDropEvent(
        date=_sv_str(date),
        drop_pct=_sv_float(drop_pct),
        drop_type=drop_type,
        period_days=period_days,
    )


# ---------------------------------------------------------------------------
# Recovery time tests
# ---------------------------------------------------------------------------


class TestComputeRecoveryDays:
    """Tests for compute_recovery_days."""

    def test_compute_recovery_days_normal(self) -> None:
        """Stock recovers to pre-drop level after 4 trading days."""
        # Prices: [100, 90, 85, 88, 92, 95, 100, 105]
        # Drop at index 2 (85), pre-drop at index 0 (100), period_days=2
        # Recovery at index 6 (100 >= 100) -> 6 - 2 = 4 trading days
        prices = [100.0, 90.0, 85.0, 88.0, 92.0, 95.0, 100.0, 105.0]
        result = compute_recovery_days(prices, drop_idx=2, period_days=2)
        assert result == 4

    def test_compute_recovery_days_never_recovered(self) -> None:
        """Stock never recovers to pre-drop level -> None."""
        prices = [100.0, 90.0, 85.0, 82.0, 80.0]
        result = compute_recovery_days(prices, drop_idx=2, period_days=2)
        assert result is None

    def test_compute_recovery_days_single_day(self) -> None:
        """Single-day drop with period_days=1 looks at previous day price."""
        # Pre-drop at index 1 (95), drop at index 2 (85)
        # Recovery at index 4 (96 >= 95) -> 4 - 2 = 2 trading days
        prices = [100.0, 95.0, 85.0, 90.0, 96.0]
        result = compute_recovery_days(prices, drop_idx=2, period_days=1)
        assert result == 2

    def test_compute_recovery_days_immediate(self) -> None:
        """Stock recovers the very next day -> 1 trading day."""
        prices = [100.0, 80.0, 100.0]
        result = compute_recovery_days(prices, drop_idx=1, period_days=1)
        assert result == 1

    def test_compute_recovery_days_out_of_bounds(self) -> None:
        """Drop index beyond price list length returns None."""
        prices = [100.0, 90.0]
        result = compute_recovery_days(prices, drop_idx=5, period_days=1)
        assert result is None


# ---------------------------------------------------------------------------
# Consecutive drop grouping tests
# ---------------------------------------------------------------------------


class TestGroupConsecutiveDrops:
    """Tests for group_consecutive_drops."""

    def test_group_consecutive_drops(self) -> None:
        """Three consecutive daily drops merge into one multi-day event."""
        drops = [
            _make_drop("2025-01-06", -6.0),
            _make_drop("2025-01-07", -5.5),
            _make_drop("2025-01-08", -7.0),
        ]
        # Prices: index 0=2025-01-05, 1=2025-01-06, 2=2025-01-07, 3=2025-01-08
        prices = [100.0, 94.0, 88.8, 82.6]
        dates = ["2025-01-05", "2025-01-06", "2025-01-07", "2025-01-08"]

        grouped = group_consecutive_drops(drops, prices, dates)

        assert len(grouped) == 1
        merged = grouped[0]
        # period_days = sum of individual (1+1+1 = 3)
        assert merged.period_days == 3
        # drop_type should be MULTI_DAY for merged group
        assert merged.drop_type == DropType.MULTI_DAY
        # cumulative_pct computed from pre-first (100) to last (82.6)
        # = (82.6 - 100) / 100 * 100 = -17.4
        assert merged.cumulative_pct is not None
        assert abs(merged.cumulative_pct - (-17.4)) < 0.1
        # Worst single-day drop is -7.0
        assert merged.drop_pct is not None
        assert merged.drop_pct.value == -7.0

    def test_group_non_consecutive_drops(self) -> None:
        """Drops separated by 5+ days remain as separate events."""
        drops = [
            _make_drop("2025-01-06", -6.0),
            _make_drop("2025-01-15", -8.0),
        ]
        prices = [
            100.0, 94.0, 95.0, 96.0, 97.0, 98.0,
            99.0, 100.0, 99.5, 92.0,
        ]
        dates = [
            "2025-01-05", "2025-01-06", "2025-01-07", "2025-01-08",
            "2025-01-09", "2025-01-10", "2025-01-13", "2025-01-14",
            "2025-01-15", "2025-01-16",
        ]

        grouped = group_consecutive_drops(drops, prices, dates)

        # Should produce 2 separate events (not merged)
        assert len(grouped) == 2
        # Both should remain SINGLE_DAY since groups of size 1
        assert grouped[0].drop_type == DropType.SINGLE_DAY
        assert grouped[1].drop_type == DropType.SINGLE_DAY

    def test_group_empty_list(self) -> None:
        """Empty drop list returns empty."""
        grouped = group_consecutive_drops([], [100.0, 90.0], ["2025-01-01", "2025-01-02"])
        assert grouped == []


# ---------------------------------------------------------------------------
# Market-wide event tagging tests
# ---------------------------------------------------------------------------


class TestTagMarketWideEvents:
    """Tests for tag_market_wide_events."""

    def test_tag_market_wide_events(self) -> None:
        """SPY -4% on same day -> is_market_wide = True."""
        drops = [_make_drop("2025-03-15", -6.0)]

        # SPY history: day before +0%, day of -4%
        spy_history = {
            "Date": ["2025-03-14", "2025-03-15"],
            "Close": [500.0, 480.0],  # -4% return on 2025-03-15
        }

        result = tag_market_wide_events(drops, spy_history)

        assert len(result) == 1
        assert result[0].is_market_wide is True

    def test_tag_company_specific_event(self) -> None:
        """SPY +0.5% on same day -> is_market_wide stays False."""
        drops = [_make_drop("2025-03-15", -6.0)]

        spy_history = {
            "Date": ["2025-03-14", "2025-03-15"],
            "Close": [500.0, 502.5],  # +0.5% return on 2025-03-15
        }

        result = tag_market_wide_events(drops, spy_history)

        assert len(result) == 1
        assert result[0].is_market_wide is False

    def test_tag_market_wide_exactly_minus_3(self) -> None:
        """SPY exactly -3% on same day -> is_market_wide = True (threshold is <=)."""
        drops = [_make_drop("2025-03-15", -5.0)]

        spy_history = {
            "Date": ["2025-03-14", "2025-03-15"],
            "Close": [500.0, 485.0],  # exactly -3%
        }

        result = tag_market_wide_events(drops, spy_history)

        assert len(result) == 1
        assert result[0].is_market_wide is True

    def test_tag_no_spy_data(self) -> None:
        """Empty SPY history -> no tagging, is_market_wide stays False."""
        drops = [_make_drop("2025-03-15", -6.0)]
        spy_history: dict[str, list[str | float]] = {"Date": [], "Close": []}

        result = tag_market_wide_events(drops, spy_history)

        assert len(result) == 1
        assert result[0].is_market_wide is False
