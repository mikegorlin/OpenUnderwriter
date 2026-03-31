"""Enhanced stock drop analysis: recovery, grouping, market-wide tagging.

Companion to stock_drops.py. Provides:
- compute_recovery_days: Trading days to recover to pre-drop price.
- group_consecutive_drops: Merge consecutive single-day drops into events.
- tag_market_wide_events: Flag drops correlating with SPY declines.

Separated from stock_drops.py for 500-line compliance.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.market_events import (
    DropType,
    StockDropEvent,
)
from do_uw.stages.extract.stock_drops import (
    compute_daily_returns,
    get_close_prices,
    get_dates,
)

# ---------------------------------------------------------------------------
# Recovery time
# ---------------------------------------------------------------------------


def compute_recovery_days(
    prices: list[float],
    drop_idx: int,
    period_days: int = 1,
) -> int | None:
    """Compute trading days until stock recovered to pre-drop price.

    Args:
        prices: List of close prices (same order as dates).
        drop_idx: Index in prices where the drop ended.
        period_days: Duration of the drop event (for multi-day drops,
            the pre-drop price is taken from before the slide).

    Returns:
        Number of trading days to recover, or None if never recovered.
    """
    pre_drop_idx = max(0, drop_idx - period_days)
    if pre_drop_idx >= len(prices) or drop_idx >= len(prices):
        return None

    pre_drop_price = prices[pre_drop_idx]
    if pre_drop_price <= 0:
        return None

    for i in range(drop_idx + 1, len(prices)):
        if prices[i] >= pre_drop_price:
            return i - drop_idx

    return None


# ---------------------------------------------------------------------------
# Consecutive drop grouping
# ---------------------------------------------------------------------------


def group_consecutive_drops(
    drops: list[StockDropEvent],
    prices: list[float],
    dates: list[str],
) -> list[StockDropEvent]:
    """Group consecutive single-day drops into multi-day events.

    When drops occur on consecutive trading days (or within a 2-day
    gap), they are merged into a single event with cumulative_pct.

    Args:
        drops: Single-day drop events, sorted by date.
        prices: Close price list.
        dates: Date string list (parallel to prices).

    Returns:
        List of drops with consecutive ones merged.
    """
    if not drops:
        return []

    from datetime import datetime as dt

    # Sort by date.
    def _drop_date(d: StockDropEvent) -> str:
        return d.date.value[:10] if d.date else ""

    sorted_drops = sorted(drops, key=_drop_date)

    # Build date -> index mapping for prices.
    date_to_idx: dict[str, int] = {}
    for i, d in enumerate(dates):
        date_to_idx[d[:10]] = i

    grouped: list[StockDropEvent] = []
    current_group: list[StockDropEvent] = [sorted_drops[0]]

    for drop in sorted_drops[1:]:
        prev_date = _drop_date(current_group[-1])
        curr_date = _drop_date(drop)

        try:
            prev_dt = dt.strptime(prev_date, "%Y-%m-%d")
            curr_dt = dt.strptime(curr_date, "%Y-%m-%d")
            gap_days = (curr_dt - prev_dt).days
        except (ValueError, IndexError):
            gap_days = 999

        # Within 4 calendar days = consecutive (accounts for weekends).
        if gap_days <= 4:
            current_group.append(drop)
        else:
            grouped.append(_merge_group(current_group, prices, dates, date_to_idx))
            current_group = [drop]

    grouped.append(_merge_group(current_group, prices, dates, date_to_idx))
    return grouped


def _merge_group(
    group: list[StockDropEvent],
    prices: list[float],
    dates: list[str],
    date_to_idx: dict[str, int],
) -> StockDropEvent:
    """Merge a group of consecutive drops into one event."""
    if len(group) == 1:
        return group[0]

    # Use first drop's date as the event date.
    first = group[0]
    last = group[-1]

    first_date = first.date.value[:10] if first.date else ""
    last_date = last.date.value[:10] if last.date else ""

    # Compute cumulative decline from pre-first-drop to post-last-drop.
    first_idx = date_to_idx.get(first_date)
    last_idx = date_to_idx.get(last_date)

    cumulative = None
    if first_idx is not None and last_idx is not None:
        pre_idx = max(0, first_idx - 1)
        if pre_idx < len(prices) and last_idx < len(prices) and prices[pre_idx] > 0:
            cumulative = (
                (prices[last_idx] - prices[pre_idx]) / prices[pre_idx] * 100.0
            )
            cumulative = round(cumulative, 2)

    # Keep trigger from the worst single-day drop.
    worst = min(
        group, key=lambda d: d.drop_pct.value if d.drop_pct else 0.0
    )

    merged = StockDropEvent(
        date=first.date,
        drop_pct=worst.drop_pct,
        drop_type=DropType.MULTI_DAY,
        period_days=sum(d.period_days for d in group),
        sector_return_pct=first.sector_return_pct,
        is_company_specific=first.is_company_specific,
        trigger_event=worst.trigger_event,
        trigger_source_url=worst.trigger_source_url,
        close_price=last.close_price,
        cumulative_pct=cumulative,
    )
    return merged


# ---------------------------------------------------------------------------
# Market-wide event tagging
# ---------------------------------------------------------------------------


def tag_market_wide_events(
    drops: list[StockDropEvent],
    spy_history: dict[str, Any],
) -> list[StockDropEvent]:
    """Tag drops that correlate with broad market declines.

    If SPY dropped more than 3% on the same day as a stock drop,
    the event is tagged as market-wide (not company-specific).

    Args:
        drops: Drop events to check.
        spy_history: SPY price history dict (Close, Date keys).

    Returns:
        Updated drops with is_market_wide set where applicable.
    """
    spy_prices = get_close_prices(spy_history)
    spy_dates = get_dates(spy_history)
    spy_returns = compute_daily_returns(spy_prices)

    if not spy_returns or not spy_dates:
        return drops

    # Build date -> SPY return mapping.
    # spy_returns[i] corresponds to spy_dates[i+1] (return from day i to i+1).
    date_to_return: dict[str, float] = {}
    for i, ret in enumerate(spy_returns):
        date_idx = i + 1
        if date_idx < len(spy_dates):
            date_to_return[spy_dates[date_idx][:10]] = ret

    for drop in drops:
        if not drop.date:
            continue
        drop_date = drop.date.value[:10]
        spy_ret = date_to_return.get(drop_date)
        if spy_ret is not None and spy_ret <= -3.0:
            drop.is_market_wide = True

    return drops
