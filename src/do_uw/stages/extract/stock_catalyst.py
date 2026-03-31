"""Phase 119: Stock drop catalyst enrichment and pattern detection.

Enriches existing StockDropEvent objects with from_price, volume,
and detects notable stock patterns for D&O assessment.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from do_uw.models.market_events import StockDropEvent
from do_uw.stages.render.formatters import safe_float


# ---------------------------------------------------------------------------
# Drop enrichment: populate from_price and volume from yfinance history
# ---------------------------------------------------------------------------


def enrich_drops_with_prices_and_volume(
    drops: list[StockDropEvent],
    history: dict[str, Any],
) -> None:
    """Populate from_price and volume on each drop event from yfinance history.

    Mutates drops in-place. Does not return a value.

    Args:
        drops: List of StockDropEvent to enrich.
        history: yfinance history dict with Date, Close, Volume lists.
    """
    date_list, close_list, volume_list = _extract_history_lists(history)
    if not date_list:
        return

    # Build date -> index lookup
    date_to_idx: dict[str, int] = {}
    for i, d in enumerate(date_list):
        date_to_idx[d[:10]] = i

    for drop in drops:
        if not drop.date:
            continue
        date_str = str(drop.date.value)[:10]
        _enrich_single_drop(drop, date_str, date_to_idx, close_list, volume_list)


def _extract_history_lists(
    history: dict[str, Any],
) -> tuple[list[str], list[float], list[int]]:
    """Extract Date, Close, Volume lists from history dict."""
    raw_dates = history.get("Date", history.get("index", []))
    raw_closes = history.get("Close", [])
    raw_volumes = history.get("Volume", [])

    if not isinstance(raw_dates, list) or not isinstance(raw_closes, list):
        return [], [], []

    dates = [str(d)[:10] for d in raw_dates]
    closes = [safe_float(c) for c in raw_closes]
    volumes: list[int] = []
    if isinstance(raw_volumes, list):
        for v in raw_volumes:
            try:
                volumes.append(int(safe_float(v)))
            except (TypeError, ValueError):
                volumes.append(0)
    else:
        volumes = [0] * len(dates)

    return dates, closes, volumes


def _enrich_single_drop(
    drop: StockDropEvent,
    date_str: str,
    date_to_idx: dict[str, int],
    closes: list[float],
    volumes: list[int],
) -> None:
    """Populate from_price and volume on a single drop event."""
    drop_idx = date_to_idx.get(date_str)
    if drop_idx is None:
        return

    period = drop.period_days

    if period <= 1:
        # Single-day drop: from_price = prior day close, volume = drop day volume
        if drop_idx > 0:
            drop.from_price = closes[drop_idx - 1]
        if drop_idx < len(volumes):
            drop.volume = volumes[drop_idx]
    else:
        # Multi-day drop ending at drop_idx, spanning 'period' days.
        # Period start index = drop_idx - period + 1 (but clamped to 0).
        start_idx = max(0, drop_idx - period + 1)

        # from_price = close of day before period start
        prior_idx = start_idx - 1
        if prior_idx >= 0:
            drop.from_price = closes[prior_idx]

        # volume = max volume over the period
        period_volumes = volumes[start_idx : drop_idx + 1]
        if period_volumes:
            drop.volume = max(period_volumes)


# ---------------------------------------------------------------------------
# Pattern detection: identify notable stock patterns from drops
# ---------------------------------------------------------------------------


def detect_stock_patterns(
    drops: list[StockDropEvent],
    *,
    trading_days_available: int | None = None,
) -> list[dict[str, str]]:
    """Detect notable stock patterns from drop events.

    Returns list of pattern dicts with keys:
    type, description, dates, do_relevance
    """
    patterns: list[dict[str, str]] = []
    if not drops:
        return patterns

    # Parse dates for analysis
    dated_drops = _parse_drop_dates(drops)
    if not dated_drops:
        return patterns

    # Sort by date
    dated_drops.sort(key=lambda x: x[1])

    # Post-IPO arc
    pattern = _detect_post_ipo_arc(dated_drops, trading_days_available)
    if pattern:
        patterns.append(pattern)

    # Multi-day cluster
    cluster_patterns = _detect_multi_day_clusters(dated_drops)
    patterns.extend(cluster_patterns)

    # Support level
    pattern = _detect_support_levels(drops)
    if pattern:
        patterns.append(pattern)

    # Lockup expiry
    pattern = _detect_lockup_expiry(dated_drops, trading_days_available)
    if pattern:
        patterns.append(pattern)

    return patterns


def _parse_drop_dates(
    drops: list[StockDropEvent],
) -> list[tuple[StockDropEvent, datetime]]:
    """Parse drop dates, filtering out drops without valid dates."""
    result: list[tuple[StockDropEvent, datetime]] = []
    for drop in drops:
        if not drop.date:
            continue
        try:
            dt = datetime.strptime(str(drop.date.value)[:10], "%Y-%m-%d")
            result.append((drop, dt))
        except (ValueError, IndexError):
            continue
    return result


def _detect_post_ipo_arc(
    dated_drops: list[tuple[StockDropEvent, datetime]],
    trading_days_available: int | None,
) -> dict[str, str] | None:
    """Detect post-IPO arc: many drops in early trading history."""
    if trading_days_available is None or trading_days_available >= 500:
        return None

    if len(dated_drops) < 3:
        return None

    # Check how many drops in first 180 calendar days from earliest drop
    earliest = dated_drops[0][1]
    drops_in_window = [
        (d, dt) for d, dt in dated_drops if (dt - earliest).days <= 180
    ]

    if len(drops_in_window) >= 3:
        dates_str = ", ".join(dt.strftime("%Y-%m-%d") for _, dt in drops_in_window)
        return {
            "type": "post_ipo_arc",
            "description": (
                f"{len(drops_in_window)} stock drops in first 180 days of trading "
                f"({trading_days_available} trading days available). "
                "Post-IPO volatility pattern indicates heightened Section 11 exposure."
            ),
            "dates": dates_str,
            "do_relevance": (
                "Post-IPO price declines within 1-3 year Section 11 window "
                "significantly increase D&O claim frequency. Plaintiff firms "
                "actively monitor newly public companies for filing opportunities."
            ),
        }
    return None


def _detect_multi_day_clusters(
    dated_drops: list[tuple[StockDropEvent, datetime]],
) -> list[dict[str, str]]:
    """Detect clusters of drops within 5 calendar days of each other."""
    patterns: list[dict[str, str]] = []
    if len(dated_drops) < 2:
        return patterns

    # Group drops that are within 5 calendar days
    i = 0
    while i < len(dated_drops):
        cluster = [dated_drops[i]]
        j = i + 1
        while j < len(dated_drops):
            # Check if next drop is within 5 days of last cluster member
            if (dated_drops[j][1] - cluster[-1][1]).days <= 5:
                cluster.append(dated_drops[j])
                j += 1
            else:
                break

        if len(cluster) >= 2:
            dates_str = ", ".join(dt.strftime("%Y-%m-%d") for _, dt in cluster)
            patterns.append({
                "type": "multi_day_cluster",
                "description": (
                    f"{len(cluster)} drops within a tight window "
                    f"({(cluster[-1][1] - cluster[0][1]).days} calendar days). "
                    "Concentrated selling pressure may indicate material non-public event."
                ),
                "dates": dates_str,
                "do_relevance": (
                    "Clustered drops strengthen plaintiff case for corrective "
                    "disclosure theory -- rapid price adjustment suggests market "
                    "was absorbing previously concealed information."
                ),
            })

        i = j if j > i + 1 else i + 1

    return patterns


def _detect_support_levels(
    drops: list[StockDropEvent],
) -> dict[str, str] | None:
    """Detect support level: >=2 drops bounce near same close price (+/-3%)."""
    priced_drops = [
        d for d in drops if d.close_price is not None and d.close_price > 0
    ]
    if len(priced_drops) < 2:
        return None

    # Check all pairs for close prices within 3%
    for i in range(len(priced_drops)):
        for j in range(i + 1, len(priced_drops)):
            p1 = priced_drops[i].close_price
            p2 = priced_drops[j].close_price
            if p1 is None or p2 is None:
                continue
            avg = (p1 + p2) / 2
            if avg == 0:
                continue
            diff_pct = abs(p1 - p2) / avg * 100
            if diff_pct <= 3.0:
                d1 = str(priced_drops[i].date.value)[:10] if priced_drops[i].date else "?"
                d2 = str(priced_drops[j].date.value)[:10] if priced_drops[j].date else "?"
                return {
                    "type": "support_level",
                    "description": (
                        f"Multiple drops bounce near ${avg:.2f} support level "
                        f"(prices within 3%). Dates: {d1}, {d2}."
                    ),
                    "dates": f"{d1}, {d2}",
                    "do_relevance": (
                        "A tested support level that eventually breaks triggers "
                        "larger price declines and increases DDL exposure. "
                        "Technical traders amplify the selling pressure."
                    ),
                }
    return None


def _detect_lockup_expiry(
    dated_drops: list[tuple[StockDropEvent, datetime]],
    trading_days_available: int | None,
) -> dict[str, str] | None:
    """Detect lockup expiry: drop near 180 calendar days post-IPO."""
    if trading_days_available is None or trading_days_available >= 500:
        return None

    if len(dated_drops) < 2:
        return None

    earliest_date = dated_drops[0][1]

    for drop, dt in dated_drops[1:]:
        days_since_first = (dt - earliest_date).days
        if 170 <= days_since_first <= 190:
            date_str = dt.strftime("%Y-%m-%d")
            return {
                "type": "lockup_expiry",
                "description": (
                    f"Stock drop on {date_str} occurred ~{days_since_first} days "
                    f"after earliest trading date, coinciding with typical "
                    f"180-day IPO lockup expiration period."
                ),
                "dates": date_str,
                "do_relevance": (
                    "Lockup expiry selling by insiders is a key D&O risk factor. "
                    "If insiders sold ahead of negative news, plaintiff firms "
                    "may allege informed trading under Section 10(b)."
                ),
            }
    return None
