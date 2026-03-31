"""Per-drop return decomposition into market, sector, and company components.

Reuses compute_return_decomposition from chart_computations to attribute
each stock drop to market-wide, sector-specific, or company-specific causes.
"""

from __future__ import annotations

import logging

from do_uw.models.market_events import StockDropEvent
from do_uw.stages.render.charts.chart_computations import compute_return_decomposition

logger = logging.getLogger(__name__)


def decompose_drop(
    drop: StockDropEvent,
    company_prices: list[float],
    spy_prices: list[float],
    sector_prices: list[float],
    dates: list[str],
) -> StockDropEvent:
    """Decompose a single drop into market/sector/company components.

    For single-day drops: uses prices at idx-1 and idx (2-point window).
    For multi-day drops: uses prices at drop_idx and drop_idx + period_days.

    Args:
        drop: StockDropEvent with date and period_days.
        company_prices: Full company price series aligned with dates.
        spy_prices: Full SPY price series aligned with dates.
        sector_prices: Full sector ETF price series aligned with dates.
        dates: List of date strings (YYYY-MM-DD) aligned with price series.

    Returns:
        Same drop with market_pct, sector_pct, company_pct, is_market_driven set.
    """
    if not drop.date:
        return drop

    drop_date = drop.date.value[:10]

    # Find index of drop date in dates list.
    try:
        idx = dates.index(drop_date)
    except ValueError:
        logger.debug("Drop date %s not found in dates list", drop_date)
        return drop

    # Determine the 2-point price window.
    if drop.period_days > 1:
        # Multi-day: start at drop date, end at drop_date + period_days.
        start_idx = idx
        end_idx = min(idx + drop.period_days, len(dates) - 1)
    else:
        # Single-day: use previous day and drop day.
        if idx < 1:
            return drop
        start_idx = idx - 1
        end_idx = idx

    # Extract 2-point windows for decomposition.
    if end_idx >= len(company_prices) or start_idx >= len(company_prices):
        return drop

    comp_window = [company_prices[start_idx], company_prices[end_idx]]
    spy_window = [spy_prices[start_idx], spy_prices[end_idx]] if len(spy_prices) > end_idx else []
    sector_window = [sector_prices[start_idx], sector_prices[end_idx]] if len(sector_prices) > end_idx else []

    result = compute_return_decomposition(comp_window, spy_window, sector_window)
    if result is None:
        return drop

    drop.market_pct = result["market_contribution"]
    drop.sector_pct = result["sector_contribution"]
    drop.company_pct = result["company_residual"]

    # Market-driven if market contribution accounts for >50% of total absolute drop.
    total_abs = abs(result["total_return"]) if result["total_return"] != 0 else 1.0
    market_abs = abs(result["market_contribution"])
    drop.is_market_driven = (market_abs / total_abs) > 0.5

    return drop


def decompose_drops(
    drops: list[StockDropEvent],
    company_prices: list[float],
    spy_prices: list[float],
    sector_prices: list[float],
    dates: list[str],
) -> list[StockDropEvent]:
    """Decompose a list of drops, skipping those without dates.

    Args:
        drops: List of StockDropEvent instances.
        company_prices: Full company price series.
        spy_prices: Full SPY price series.
        sector_prices: Full sector ETF price series.
        dates: Date strings aligned with price series.

    Returns:
        List of drops with decomposition fields set where possible.
    """
    result: list[StockDropEvent] = []
    for drop in drops:
        if not drop.date:
            result.append(drop)
            continue
        result.append(
            decompose_drop(drop, company_prices, spy_prices, sector_prices, dates)
        )
    return result


__all__ = [
    "decompose_drop",
    "decompose_drops",
]
