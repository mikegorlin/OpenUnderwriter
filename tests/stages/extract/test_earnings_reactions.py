"""Tests for earnings reaction multi-window return computation.

Tests compute_earnings_reactions() which takes earnings dates and price
history, returning day-of, next-day, and week returns for each date.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from do_uw.models.common import SourcedValue
from do_uw.models.market_events import EarningsQuarterRecord
from do_uw.stages.extract.earnings_reactions import compute_earnings_reactions

_NOW = datetime(2025, 1, 15, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helper: build a simple price history dict (yfinance dict-of-dicts format)
# ---------------------------------------------------------------------------


def _make_history(
    dates: list[str], closes: list[float],
) -> dict[str, dict[str, float | str]]:
    """Build a yfinance-style dict-of-dicts history."""
    date_col = {str(i): d for i, d in enumerate(dates)}
    close_col = {str(i): c for i, c in enumerate(closes)}
    return {"Date": date_col, "Close": close_col}


# ---------------------------------------------------------------------------
# Test 1: EarningsQuarterRecord accepts new fields
# ---------------------------------------------------------------------------


def test_earnings_quarter_record_new_fields_default_none() -> None:
    """EarningsQuarterRecord has next_day_return_pct and week_return_pct with default None."""
    record = EarningsQuarterRecord()
    assert record.next_day_return_pct is None
    assert record.week_return_pct is None


def test_earnings_quarter_record_new_fields_with_values() -> None:
    """EarningsQuarterRecord accepts SourcedValue[float] for new fields."""
    record = EarningsQuarterRecord(
        next_day_return_pct=SourcedValue(value=3.5, source="yfinance", confidence="MEDIUM", as_of=_NOW),
        week_return_pct=SourcedValue(value=-2.1, source="yfinance", confidence="MEDIUM", as_of=_NOW),
    )
    assert record.next_day_return_pct is not None
    assert record.next_day_return_pct.value == 3.5
    assert record.week_return_pct is not None
    assert record.week_return_pct.value == -2.1


# ---------------------------------------------------------------------------
# Test 2: compute_earnings_reactions with 3 dates and 60 days of history
# ---------------------------------------------------------------------------


def test_compute_earnings_reactions_three_dates() -> None:
    """3 earnings dates with 60+ days of price data returns 3 records."""
    # 70 trading days of simple prices
    dates = [f"2025-01-{i+1:02d}" for i in range(31)] + [
        f"2025-02-{i+1:02d}" for i in range(28)
    ] + [f"2025-03-{i+1:02d}" for i in range(11)]
    closes = [100.0 + i * 0.5 for i in range(70)]
    history = _make_history(dates, closes)

    # 3 earnings dates within the range
    earnings_dates = ["2025-01-10", "2025-01-20", "2025-02-10"]

    results = compute_earnings_reactions(earnings_dates, history)
    assert len(results) == 3
    for r in results:
        assert "date" in r
        assert "day_of_return" in r
        assert "next_day_return" in r
        assert "week_return" in r


# ---------------------------------------------------------------------------
# Test 3: Friday earnings -> next-day from nearest following trading day
# ---------------------------------------------------------------------------


def test_compute_earnings_reactions_friday_handling() -> None:
    """Earnings on a date computes next_day from the next available close."""
    # Sequence: T-1, T (earnings), T+1, T+2, ...
    dates = [
        "2025-01-09",  # idx 0 (T-1)
        "2025-01-10",  # idx 1 (T, earnings day = Friday)
        "2025-01-13",  # idx 2 (T+1 = Monday)
        "2025-01-14",  # idx 3
        "2025-01-15",  # idx 4
        "2025-01-16",  # idx 5
        "2025-01-17",  # idx 6
        "2025-01-20",  # idx 7 (T+5-ish from Monday)
        "2025-01-21",  # idx 8
    ]
    closes = [100.0, 105.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions(["2025-01-10"], history)
    assert len(results) == 1
    r = results[0]

    # day_of = (close[T] - close[T-1]) / close[T-1] * 100 = (105 - 100)/100 * 100 = 5.0
    assert abs(r["day_of_return"] - 5.0) < 0.01

    # next_day = (close[T+1] - close[T-1]) / close[T-1] * 100 = (107-100)/100*100 = 7.0
    assert abs(r["next_day_return"] - 7.0) < 0.01


# ---------------------------------------------------------------------------
# Test 4: Earnings date outside price range returns nothing for that date
# ---------------------------------------------------------------------------


def test_compute_earnings_reactions_outside_range() -> None:
    """Earnings date not in price history is skipped."""
    dates = ["2025-01-10", "2025-01-11", "2025-01-12"]
    closes = [100.0, 101.0, 102.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions(["2024-06-01"], history)
    assert len(results) == 0


# ---------------------------------------------------------------------------
# Test 5: Empty earnings_dates returns empty list
# ---------------------------------------------------------------------------


def test_compute_earnings_reactions_empty_dates() -> None:
    """Empty earnings_dates list returns empty result."""
    dates = ["2025-01-10", "2025-01-11"]
    closes = [100.0, 101.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions([], history)
    assert results == []


# ---------------------------------------------------------------------------
# Test 6: Day-of return formula
# ---------------------------------------------------------------------------


def test_day_of_return_formula() -> None:
    """Day-of return = (close[T] - close[T-1]) / close[T-1] * 100."""
    dates = ["2025-01-09", "2025-01-10", "2025-01-13", "2025-01-14",
             "2025-01-15", "2025-01-16", "2025-01-17", "2025-01-20"]
    closes = [50.0, 55.0, 56.0, 57.0, 58.0, 59.0, 60.0, 61.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions(["2025-01-10"], history)
    assert len(results) == 1
    # (55 - 50) / 50 * 100 = 10.0
    assert abs(results[0]["day_of_return"] - 10.0) < 0.01


# ---------------------------------------------------------------------------
# Test 7: Next-day return formula
# ---------------------------------------------------------------------------


def test_next_day_return_formula() -> None:
    """Next-day return = (close[T+1] - close[T-1]) / close[T-1] * 100."""
    dates = ["2025-01-09", "2025-01-10", "2025-01-13", "2025-01-14",
             "2025-01-15", "2025-01-16", "2025-01-17", "2025-01-20"]
    closes = [50.0, 55.0, 53.0, 57.0, 58.0, 59.0, 60.0, 61.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions(["2025-01-10"], history)
    assert len(results) == 1
    # (53 - 50) / 50 * 100 = 6.0
    assert abs(results[0]["next_day_return"] - 6.0) < 0.01


# ---------------------------------------------------------------------------
# Test 8: Week return formula
# ---------------------------------------------------------------------------


def test_week_return_formula() -> None:
    """Week return = (close[T+5] - close[T-1]) / close[T-1] * 100 or nearest available."""
    dates = ["2025-01-09", "2025-01-10", "2025-01-13", "2025-01-14",
             "2025-01-15", "2025-01-16", "2025-01-17", "2025-01-20"]
    closes = [50.0, 55.0, 53.0, 57.0, 58.0, 59.0, 60.0, 61.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions(["2025-01-10"], history)
    assert len(results) == 1
    # T is idx 1, T+5 is idx 6 (close = 60.0), T-1 is idx 0 (close = 50.0)
    # (60 - 50) / 50 * 100 = 20.0
    assert abs(results[0]["week_return"] - 20.0) < 0.01


# ---------------------------------------------------------------------------
# Test: idx=0 (first day is earnings, no prior day) -> skip
# ---------------------------------------------------------------------------


def test_first_day_earnings_skipped() -> None:
    """If earnings is the first date in history, skip (no T-1 close)."""
    dates = ["2025-01-10", "2025-01-13"]
    closes = [100.0, 101.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions(["2025-01-10"], history)
    assert len(results) == 0


# ---------------------------------------------------------------------------
# Test: Week return clamps when near end of series
# ---------------------------------------------------------------------------


def test_week_return_clamps_near_end() -> None:
    """Week return uses last available price when T+5 is beyond series."""
    dates = ["2025-01-09", "2025-01-10", "2025-01-13", "2025-01-14"]
    closes = [100.0, 110.0, 115.0, 120.0]
    history = _make_history(dates, closes)

    results = compute_earnings_reactions(["2025-01-10"], history)
    assert len(results) == 1
    # T is idx 1, T-1 is idx 0 (100). T+5 would be idx 6, clamped to idx 3 (120)
    # week_return = (120 - 100)/100 * 100 = 20.0
    assert abs(results[0]["week_return"] - 20.0) < 0.01
