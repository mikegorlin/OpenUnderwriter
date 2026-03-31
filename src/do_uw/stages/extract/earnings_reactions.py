"""Earnings reaction multi-window return computation.

Computes day-of, next-day, and 1-week stock returns around each
earnings date. Used by SECT4-06 earnings guidance analysis to
quantify market reaction to earnings announcements.

Uses the same yfinance dict-of-dicts history format as volume_spikes.py.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compute_earnings_reactions(
    earnings_dates: list[str] | dict[str, Any],
    history: dict[str, Any],
) -> list[dict[str, Any]]:
    """Compute multi-window returns around each earnings date.

    For each earnings date found in the price history:
    - day_of_return: (close[T] - close[T-1]) / close[T-1] * 100
    - next_day_return: (close[T+1] - close[T-1]) / close[T-1] * 100
    - week_return: (close[T+5] - close[T-1]) / close[T-1] * 100

    All returns are measured relative to the pre-earnings close (T-1)
    to capture the full reaction, not just the intraday move.

    Args:
        earnings_dates: List of date strings (YYYY-MM-DD) or yfinance
            dict-of-dicts format (e.g. {"0": "2025-01-10", "1": ...}).
        history: yfinance history dict-of-dicts with Date and Close columns.

    Returns:
        List of dicts with date, day_of_return, next_day_return, week_return.
        Dates not found in history or at index 0 (no prior close) are skipped.
    """
    # Normalize earnings_dates to a list of strings
    dates_list = _normalize_dates(earnings_dates)
    if not dates_list:
        return []

    # Extract dates and closes from history
    hist_dates = _extract_dates(history)
    hist_closes = _extract_closes(history)

    if len(hist_dates) < 2 or len(hist_closes) < 2:
        return []

    # Build date -> index lookup
    date_to_idx: dict[str, int] = {}
    for i, d in enumerate(hist_dates):
        # Normalize date string (strip time part if present)
        clean = d[:10] if len(d) >= 10 else d
        date_to_idx[clean] = i

    results: list[dict[str, Any]] = []
    for edate in dates_list:
        clean_edate = edate[:10] if len(edate) >= 10 else edate
        idx = date_to_idx.get(clean_edate)

        if idx is None:
            # Try to find nearest trading day (within 3 days forward)
            idx = _find_nearest_trading_day(clean_edate, date_to_idx)

        if idx is None or idx < 1:
            # No prior close available
            continue

        pre_close = hist_closes[idx - 1]
        if pre_close <= 0:
            continue

        n = len(hist_closes)

        # Day-of return
        day_of = (hist_closes[idx] - pre_close) / pre_close * 100.0

        # Next-day return (T+1, clamped to end of series)
        next_idx = min(idx + 1, n - 1)
        next_day = (hist_closes[next_idx] - pre_close) / pre_close * 100.0

        # Week return (T+5, clamped to end of series)
        week_idx = min(idx + 5, n - 1)
        week_ret = (hist_closes[week_idx] - pre_close) / pre_close * 100.0

        results.append({
            "date": clean_edate,
            "day_of_return": round(day_of, 4),
            "next_day_return": round(next_day, 4),
            "week_return": round(week_ret, 4),
        })

    logger.info(
        "EARNINGS: Computed reactions for %d/%d earnings dates",
        len(results),
        len(dates_list),
    )
    return results


def _normalize_dates(
    earnings_dates: list[str] | dict[str, Any],
) -> list[str]:
    """Convert earnings_dates from various formats to a plain list of strings."""
    if isinstance(earnings_dates, dict):
        # yfinance format: {"Earnings Date": ["2026-01-29 16:00:00-04:00", ...], ...}
        if "Earnings Date" in earnings_dates:
            ed = earnings_dates["Earnings Date"]
            if isinstance(ed, list):
                return [str(d) for d in ed if d]
            if isinstance(ed, dict):
                keys = sorted(ed.keys(), key=lambda k: int(k) if str(k).isdigit() else k)
                return [str(ed[k]) for k in keys if ed[k]]
        # Numeric-keyed dict-of-dicts format: {"0": "2025-01-10", ...}
        keys = sorted(earnings_dates.keys(), key=lambda k: int(k) if str(k).isdigit() else k)
        return [str(earnings_dates[k]) for k in keys]
    if isinstance(earnings_dates, list):
        return [str(d) for d in earnings_dates]
    return []


def _extract_dates(history: dict[str, Any]) -> list[str]:
    """Extract date column from yfinance history (list or dict-of-dicts)."""
    date_data = history.get("Date", {})
    if isinstance(date_data, list):
        return [str(d) for d in date_data]
    if isinstance(date_data, dict):
        keys = sorted(date_data.keys(), key=lambda k: int(k) if str(k).isdigit() else k)
        return [str(date_data.get(k, "")) for k in keys]
    return []


def _extract_closes(history: dict[str, Any]) -> list[float]:
    """Extract Close column from yfinance history (list or dict-of-dicts)."""
    close_data = history.get("Close", {})
    if isinstance(close_data, list):
        return [float(v or 0) for v in close_data]
    if isinstance(close_data, dict):
        keys = sorted(close_data.keys(), key=lambda k: int(k) if str(k).isdigit() else k)
        return [float(close_data.get(k, 0) or 0) for k in keys]
    return []


def _find_nearest_trading_day(
    target_date: str,
    date_to_idx: dict[str, int],
) -> int | None:
    """Find nearest trading day index within 3 calendar days forward.

    Handles weekends/holidays: if earnings reported on Friday after
    close, the reaction is on Monday.
    """
    try:
        year, month, day = int(target_date[:4]), int(target_date[5:7]), int(target_date[8:10])
    except (ValueError, IndexError):
        return None

    # Check up to 3 days forward
    for offset in range(1, 4):
        d = day + offset
        # Simple month overflow handling (good enough for 3-day lookahead)
        m, y = month, year
        if d > 28:
            # Could overflow, try both current and next month
            candidate = f"{y:04d}-{m:02d}-{d:02d}"
            idx = date_to_idx.get(candidate)
            if idx is not None:
                return idx
            # Try next month day 1-3
            m += 1
            if m > 12:
                m = 1
                y += 1
            for nd in range(1, 4):
                candidate = f"{y:04d}-{m:02d}-{nd:02d}"
                idx = date_to_idx.get(candidate)
                if idx is not None:
                    return idx
        else:
            candidate = f"{y:04d}-{m:02d}-{d:02d}"
            idx = date_to_idx.get(candidate)
            if idx is not None:
                return idx

    return None


__all__ = ["compute_earnings_reactions"]
