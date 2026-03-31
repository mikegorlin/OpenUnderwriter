"""Stock drop detection and trigger attribution helpers.

Companion module to stock_performance.py. Contains the drop detection
algorithms (single-day, multi-day), sector comparison, deduplication,
and trigger attribution logic.

Separated from stock_performance.py for 500-line compliance.
"""

from __future__ import annotations

import math
from typing import Any, cast

from do_uw.models.common import Confidence
from do_uw.models.market_events import (
    DropType,
    StockDropEvent,
)
from do_uw.stages.extract.sourced import (
    sourced_float,
    sourced_str,
)

SOURCE_LABEL = "yfinance market data"

# Default thresholds for stock drop detection.
SINGLE_DAY_THRESHOLD_PCT: float = -5.0

# Multi-day thresholds: period_days -> threshold_pct.
MULTI_DAY_THRESHOLDS: dict[int, float] = {
    2: -10.0,
    5: -15.0,
    20: -25.0,
}


# ---------------------------------------------------------------------------
# Data access helpers
# ---------------------------------------------------------------------------


def get_close_prices(history: dict[str, Any]) -> list[float]:
    """Extract Close prices from history dict, filtering NaN/None."""
    raw = history.get("Close", [])
    if not isinstance(raw, list):
        return []
    typed_raw = cast(list[Any], raw)
    prices: list[float] = []
    for val in typed_raw:
        if val is None:
            continue
        try:
            fval = float(str(val))
        except (TypeError, ValueError):
            continue
        if math.isnan(fval) or math.isinf(fval):
            continue
        prices.append(fval)
    return prices


def get_dates(history: dict[str, Any]) -> list[str]:
    """Extract date strings from history dict."""
    raw = history.get("Date", history.get("index", []))
    if not isinstance(raw, list):
        return []
    typed_raw = cast(list[Any], raw)
    return [str(d) for d in typed_raw]


def compute_daily_returns(prices: list[float]) -> list[float]:
    """Compute daily percentage returns from Close prices."""
    if len(prices) < 2:
        return []
    returns: list[float] = []
    for i in range(1, len(prices)):
        if prices[i - 1] == 0.0:
            returns.append(0.0)
        else:
            pct = (prices[i] - prices[i - 1]) / prices[i - 1] * 100.0
            returns.append(pct)
    return returns


# ---------------------------------------------------------------------------
# Drop detection
# ---------------------------------------------------------------------------


def find_single_day_drops(
    history: dict[str, Any],
    threshold_pct: float = SINGLE_DAY_THRESHOLD_PCT,
) -> list[StockDropEvent]:
    """Find single-day drops exceeding the threshold.

    Iterates Close prices, computes daily returns, flags days
    where the return is <= threshold_pct (e.g., -5%).
    """
    prices = get_close_prices(history)
    dates = get_dates(history)
    returns = compute_daily_returns(prices)

    drops: list[StockDropEvent] = []
    for i, ret in enumerate(returns):
        if ret <= threshold_pct:
            # returns[i] corresponds to prices[i+1] vs prices[i]
            date_idx = i + 1
            date_str = dates[date_idx] if date_idx < len(dates) else ""
            close = prices[date_idx] if date_idx < len(prices) else None
            event = StockDropEvent(
                date=sourced_str(
                    date_str[:10], SOURCE_LABEL, Confidence.MEDIUM
                ),
                drop_pct=sourced_float(
                    round(ret, 2), SOURCE_LABEL, Confidence.MEDIUM
                ),
                drop_type=DropType.SINGLE_DAY,
                period_days=1,
                close_price=close,
            )
            drops.append(event)

    return drops


def find_multi_day_drops(
    history: dict[str, Any],
    periods: list[int] | None = None,
    thresholds: dict[int, float] | None = None,
) -> list[StockDropEvent]:
    """Find multi-day drops exceeding period-specific thresholds.

    For each period length, computes rolling N-day returns and flags
    windows where the total return is below the threshold.
    Deduplicates overlapping windows by keeping the worst.
    """
    if periods is None:
        periods = list(MULTI_DAY_THRESHOLDS.keys())
    if thresholds is None:
        thresholds = MULTI_DAY_THRESHOLDS

    prices = get_close_prices(history)
    dates = get_dates(history)

    if len(prices) < 2:
        return []

    all_drops: list[StockDropEvent] = []

    for period in periods:
        threshold = thresholds.get(period, -20.0)
        if len(prices) <= period:
            continue

        for i in range(period, len(prices)):
            start_price = prices[i - period]
            end_price = prices[i]
            if start_price == 0.0:
                continue
            pct_return = (end_price - start_price) / start_price * 100.0
            if pct_return <= threshold:
                date_str = dates[i] if i < len(dates) else ""
                event = StockDropEvent(
                    date=sourced_str(
                        date_str[:10], SOURCE_LABEL, Confidence.MEDIUM
                    ),
                    drop_pct=sourced_float(
                        round(pct_return, 2),
                        SOURCE_LABEL,
                        Confidence.MEDIUM,
                    ),
                    drop_type=DropType.MULTI_DAY,
                    period_days=period,
                    close_price=end_price,
                )
                all_drops.append(event)

    return _deduplicate_drops(all_drops)


def _deduplicate_drops(
    drops: list[StockDropEvent],
) -> list[StockDropEvent]:
    """Keep only the worst drop per date to avoid overlapping events."""
    by_date: dict[str, StockDropEvent] = {}
    for drop in drops:
        date_key = drop.date.value if drop.date else ""
        existing = by_date.get(date_key)
        drop_val = drop.drop_pct.value if drop.drop_pct else 0.0
        if existing is None:
            by_date[date_key] = drop
        else:
            existing_val = existing.drop_pct.value if existing.drop_pct else 0.0
            if drop_val < existing_val:
                by_date[date_key] = drop
    return list(by_date.values())


# ---------------------------------------------------------------------------
# Sector comparison
# ---------------------------------------------------------------------------


def compute_sector_comparison(
    drop: StockDropEvent,
    sector_history: dict[str, Any],
) -> StockDropEvent:
    """Compare a stock drop against sector ETF on same dates.

    Finds the sector return over the same period and sets
    is_company_specific if the stock drop exceeds sector decline.
    """
    sector_prices = get_close_prices(sector_history)
    sector_dates = get_dates(sector_history)

    if not sector_prices or not sector_dates or not drop.date:
        return drop

    target_date = drop.date.value[:10]
    period = drop.period_days

    end_idx = _find_date_index(sector_dates, target_date)
    if end_idx is None or end_idx < period:
        return drop

    start_idx = end_idx - period
    start_price = sector_prices[start_idx]
    end_price = sector_prices[end_idx]

    if start_price == 0.0:
        return drop

    sector_return = (end_price - start_price) / start_price * 100.0
    drop.sector_return_pct = sourced_float(
        round(sector_return, 2), SOURCE_LABEL, Confidence.MEDIUM
    )

    drop_val = drop.drop_pct.value if drop.drop_pct else 0.0
    drop.is_company_specific = drop_val < sector_return

    return drop


def _find_date_index(
    dates: list[str], target: str,
) -> int | None:
    """Find index of target date in dates list (prefix match)."""
    for i, d in enumerate(dates):
        if d[:10] == target[:10]:
            return i
    return None


# ---------------------------------------------------------------------------
# Trigger attribution
# ---------------------------------------------------------------------------


def attribute_triggers(
    drops: list[StockDropEvent],
    filings: dict[str, Any],
    market_data: dict[str, Any],
) -> list[StockDropEvent]:
    """Search 8-K filings and earnings dates near drop dates.

    For each drop, looks for 8-K filings or earnings dates
    within +/- 3 calendar days as potential triggers. Also
    populates trigger_source_url from 8-K accession numbers.
    """
    eight_k_dates = _get_8k_dates(filings)
    earnings_dates = _get_earnings_dates(market_data)

    for drop in drops:
        if not drop.date:
            continue
        drop_date = drop.date.value[:10]
        result = _find_nearby_event(drop_date, eight_k_dates, earnings_dates)
        if result:
            trigger_label, accession = result
            drop.trigger_event = sourced_str(
                trigger_label, SOURCE_LABEL, Confidence.MEDIUM
            )
            # Populate trigger_source_url from 8-K accession number.
            if accession and trigger_label == "8-K_filing":
                drop.trigger_source_url = (
                    "https://www.sec.gov/cgi-bin/browse-edgar"
                    f"?action=getcompany&accession={accession}&type=8-K"
                )

    return drops


def _get_8k_dates(
    filings: dict[str, Any],
) -> list[tuple[str, str]]:
    """Extract 8-K filing dates and accession numbers from filings data.

    Returns list of (date_str, accession_number) tuples.
    """
    eight_k = filings.get("8-K")
    if isinstance(eight_k, dict):
        typed_8k = cast(dict[str, Any], eight_k)
        date_str = str(typed_8k.get("filing_date", ""))
        accession = str(typed_8k.get("accession_number", ""))
        return [(date_str, accession)] if date_str else []
    if isinstance(eight_k, list):
        typed_list = cast(list[Any], eight_k)
        results: list[tuple[str, str]] = []
        for item in typed_list:
            if isinstance(item, dict):
                typed_item = cast(dict[str, Any], item)
                d = str(typed_item.get("filing_date", ""))
                acc = str(typed_item.get("accession_number", ""))
                if d:
                    results.append((d, acc))
        return results
    docs = filings.get("filing_documents", {})
    if isinstance(docs, dict):
        typed_docs = cast(dict[str, Any], docs)
        eight_k_docs = typed_docs.get("8-K", [])
        if isinstance(eight_k_docs, list):
            typed_8k_docs = cast(list[Any], eight_k_docs)
            return [
                (
                    str(cast(dict[str, Any], doc).get("filing_date", "")),
                    str(cast(dict[str, Any], doc).get("accession_number", "")),
                )
                for doc in typed_8k_docs
                if isinstance(doc, dict)
            ]
    return []


def _get_earnings_dates(market_data: dict[str, Any]) -> list[str]:
    """Extract earnings dates from market data.

    yfinance earnings_dates comes as a dict with keys:
    'Earnings Date', 'EPS Estimate', 'Reported EPS', 'Surprise(%)'
    where 'Earnings Date' is a list of datetime strings.
    """
    ed = market_data.get("earnings_dates", {})
    if isinstance(ed, dict):
        typed_ed = cast(dict[str, Any], ed)
        # Primary: yfinance format with 'Earnings Date' key
        raw = typed_ed.get("Earnings Date",
              typed_ed.get("Date",
              typed_ed.get("index", [])))
        if isinstance(raw, list):
            typed_raw = cast(list[Any], raw)
            return [str(d)[:10] for d in typed_raw if d]
    if isinstance(ed, list):
        return [str(d)[:10] for d in cast(list[Any], ed) if d]
    return []


def _find_nearby_event(
    drop_date: str,
    eight_k_dates: list[tuple[str, str]],
    earnings_dates: list[str],
) -> tuple[str, str] | None:
    """Check if an 8-K or earnings date is near the drop date.

    Uses ±5 day window for 8-K filings and ±5 days for earnings
    to capture market reaction lag (drops often occur 1-2 business
    days after the filing/announcement).

    Returns (trigger_label, accession_or_empty) or None.
    """
    # Check earnings first (higher priority attribution)
    for ed in earnings_dates:
        if _dates_within_days(drop_date, ed[:10], 5):
            return ("earnings_release", "")
    # Then 8-K filings
    for fk_date, fk_accession in eight_k_dates:
        if _dates_within_days(drop_date, fk_date[:10], 5):
            return ("8-K_filing", fk_accession)
    return None


def _dates_within_days(
    date_a: str, date_b: str, max_days: int,
) -> bool:
    """Check if two YYYY-MM-DD dates are within max_days of each other."""
    from datetime import datetime as dt

    try:
        a = dt.strptime(date_a[:10], "%Y-%m-%d")
        b = dt.strptime(date_b[:10], "%Y-%m-%d")
        return abs((a - b).days) <= max_days
    except (ValueError, IndexError):
        return False
