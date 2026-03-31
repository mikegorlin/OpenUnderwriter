"""DDL/MTL (Dollar Damage Line / Maximum Tolerable Loss) context builder.

Calculates securities class action damage exposure from price history:
- Current active exposure: if a suit was filed TODAY, what's the damage window?
- Volume-weighted DDL = shares traded during class period × average overpayment
- Settlement range estimates (2-5% of DDL)
- Prior SCA class period exclusions (damage clock reset)
- Multiple exposure windows (from 2Y high, from recent local peak)

Rework: 2026-03-17 workshop directive — DDL/MTL is core underwriting intelligence.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float
from do_uw.stages.render.formatters_numeric import format_currency

logger = logging.getLogger(__name__)

# Settlement as % of DDL (Cornerstone Research empirical data)
_SETTLEMENT_PCT_LOW = 0.02  # 2% — typical weak case
_SETTLEMENT_PCT_HIGH = 0.05  # 5% — strong plaintiff case


def build_ddl_context(state: AnalysisState) -> dict[str, Any]:
    """Build DDL/MTL analysis from price history and litigation data.

    Primary framing: if a securities class action was filed TODAY,
    what is the potential damage exposure?
    """
    prices = _get_price_history(state)
    if not prices:
        return {"available": False}

    dates, closes, volumes = prices
    shares = _get_shares_outstanding(state)
    sca_exclusions = _get_sca_exclusions(state)
    current_price = closes[-1]
    high_2y = max(closes)

    # Find exposure windows
    exposures = _build_exposure_windows(dates, closes, volumes, shares, sca_exclusions)

    if not exposures:
        return {
            "available": True,
            "has_exposure": False,
            "current_price": round(current_price, 2),
            "high_2y": round(high_2y, 2),
        }

    # Primary = the window with the largest current DDL
    primary = exposures[0]

    # Chart data
    chart_data = _build_chart_data(dates, closes, exposures)

    return {
        "available": True,
        "has_exposure": True,
        "primary": primary,
        "exposures": exposures,
        "exposure_count": len(exposures),
        "current_price": round(current_price, 2),
        "high_2y": round(high_2y, 2),
        "low_2y": round(min(closes), 2),
        "pct_below_high": round((1 - current_price / high_2y) * 100, 1),
        "shares_outstanding": shares,
        "shares_fmt": _fmt_shares(shares),
        "sca_exclusions": sca_exclusions,
        "has_sca_exclusions": len(sca_exclusions) > 0,
        "chart_data": chart_data,
    }


def _build_exposure_windows(
    dates: list[str],
    closes: list[float],
    volumes: list[int],
    shares: int,
    sca_exclusions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    """Build exposure windows: if a suit was filed today, what are the
    possible class periods and their DDL?

    Returns up to 3 windows sorted by DDL (largest first):
    1. From 2Y all-time high (maximum possible class period)
    2. From most recent local peak (most likely class period)
    3. From 6-month high (conservative/recent window)
    """
    current_idx = len(closes) - 1
    current_price = closes[current_idx]
    windows: list[dict[str, Any]] = []

    # Find the earliest allowed start date (after any prior SCA class period end)
    earliest_allowed = dates[0]
    for exc in sca_exclusions:
        class_end = exc.get("class_end", "")
        if class_end and class_end > earliest_allowed:
            earliest_allowed = class_end

    # Window 1: From 2Y all-time high
    high_2y = max(closes)
    high_2y_idx = closes.index(high_2y)
    if dates[high_2y_idx] >= earliest_allowed and high_2y_idx < current_idx:
        drop_pct = (high_2y - current_price) / high_2y
        if drop_pct >= 0.05:  # At least 5% drop
            w = _calc_window(
                dates, closes, volumes, shares,
                high_2y_idx, current_idx,
                "Maximum Exposure (from 2Y high)",
            )
            if w:
                windows.append(w)

    # Window 2: Most recent local peak (look backward from today for highest point
    # before the current decline started)
    recent_peak_val = current_price
    recent_peak_idx = current_idx
    # Walk backward to find where the current decline started
    for i in range(current_idx, -1, -1):
        if closes[i] > recent_peak_val:
            recent_peak_val = closes[i]
            recent_peak_idx = i

    if (
        recent_peak_idx != high_2y_idx
        and dates[recent_peak_idx] >= earliest_allowed
        and recent_peak_idx < current_idx
    ):
        drop_pct = (recent_peak_val - current_price) / recent_peak_val
        if drop_pct >= 0.05:
            w = _calc_window(
                dates, closes, volumes, shares,
                recent_peak_idx, current_idx,
                "Current Decline (from recent peak)",
            )
            if w:
                windows.append(w)

    # Window 3: 6-month window
    six_mo_idx = max(0, current_idx - 126)
    six_mo_high = max(closes[six_mo_idx:])
    six_mo_high_idx = six_mo_idx + closes[six_mo_idx:].index(six_mo_high)
    if (
        six_mo_high_idx != high_2y_idx
        and six_mo_high_idx != recent_peak_idx
        and dates[six_mo_high_idx] >= earliest_allowed
        and six_mo_high_idx < current_idx
    ):
        drop_pct = (six_mo_high - current_price) / six_mo_high
        if drop_pct >= 0.05:
            w = _calc_window(
                dates, closes, volumes, shares,
                six_mo_high_idx, current_idx,
                "Recent Window (6-month)",
            )
            if w:
                windows.append(w)

    # Sort by DDL descending
    windows.sort(key=lambda w: w["ddl_raw"], reverse=True)

    # Deduplicate windows that share the same peak
    seen_peaks: set[int] = set()
    deduped: list[dict[str, Any]] = []
    for w in windows:
        if w["peak_idx"] not in seen_peaks:
            seen_peaks.add(w["peak_idx"])
            deduped.append(w)

    return deduped[:3]


def _calc_window(
    dates: list[str],
    closes: list[float],
    volumes: list[int],
    shares: int,
    peak_idx: int,
    current_idx: int,
    label: str,
) -> dict[str, Any] | None:
    """Calculate DDL metrics for a single exposure window."""
    peak_price = closes[peak_idx]
    current_price = closes[current_idx]
    price_drop = peak_price - current_price
    drop_pct = price_drop / peak_price if peak_price > 0 else 0

    if drop_pct < 0.05:
        return None

    duration = current_idx - peak_idx

    # Volume during class period
    period_vols = volumes[peak_idx : current_idx + 1]
    total_vol = sum(period_vols)
    avg_vol = total_vol / len(period_vols) if period_vols else 0
    turnover = total_vol / shares if shares else 0

    # DDL = shares traded × average overpayment (half the total drop)
    ddl = total_vol * (price_drop / 2)

    # Settlement range
    settlement_low = ddl * _SETTLEMENT_PCT_LOW
    settlement_high = ddl * _SETTLEMENT_PCT_HIGH

    return {
        "label": label,
        "peak_date": dates[peak_idx][:10],
        "peak_price": round(peak_price, 2),
        "peak_idx": peak_idx,
        "current_price": round(current_price, 2),
        "drop_pct": round(drop_pct * 100, 1),
        "duration_days": duration,
        "total_volume": total_vol,
        "total_volume_fmt": _fmt_shares(total_vol),
        "avg_daily_volume": int(avg_vol),
        "turnover": round(turnover, 2),
        "ddl_raw": ddl,
        "ddl_fmt": format_currency(ddl, compact=True),
        "settlement_low": format_currency(settlement_low, compact=True),
        "settlement_high": format_currency(settlement_high, compact=True),
        "settlement_low_raw": settlement_low,
        "settlement_high_raw": settlement_high,
    }


def _get_price_history(
    state: AnalysisState,
) -> tuple[list[str], list[float], list[int]] | None:
    """Extract price history from acquired market data."""
    if not state.acquired_data:
        return None

    md = getattr(state.acquired_data, "market_data", None)
    if not md or not isinstance(md, dict):
        return None

    for key in ["history_2y", "history_1y", "history_5y"]:
        hist = md.get(key, {})
        if not isinstance(hist, dict):
            continue

        dates_raw = hist.get("Date", [])
        closes_raw = hist.get("Close", [])
        volumes_raw = hist.get("Volume", [])

        if not dates_raw or not closes_raw:
            continue

        dates = [str(d)[:10] for d in dates_raw]
        closes = [safe_float(c) for c in closes_raw]
        volumes = [int(v) for v in volumes_raw] if volumes_raw else [0] * len(closes)

        if len(dates) >= 20:
            return dates, closes, volumes

    return None


def _get_shares_outstanding(state: AnalysisState) -> int:
    """Get shares outstanding from market data info."""
    if not state.acquired_data:
        return 0

    md = getattr(state.acquired_data, "market_data", None)
    if not md or not isinstance(md, dict):
        return 0

    info = md.get("info", {})
    if not isinstance(info, dict):
        return 0

    shares = info.get("sharesOutstanding", 0)
    if not shares:
        shares = info.get("floatShares", 0)
    return int(shares) if shares else 0


def _get_sca_exclusions(state: AnalysisState) -> list[dict[str, str]]:
    """Get prior SCA class periods that reset the damage clock."""
    exclusions: list[dict[str, str]] = []

    if not state.extracted or not state.extracted.litigation:
        return exclusions

    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    lit = state.extracted.litigation
    scas = getattr(lit, "securities_class_actions", None) or []

    for case in scas:
        # Only count genuine SCAs for damage clock reset
        if _is_regulatory_not_sca(case):
            continue
        if not isinstance(case, dict):
            case_dict = case.__dict__ if hasattr(case, "__dict__") else {}
        else:
            case_dict = case

        class_start = case_dict.get("class_period_start")
        class_end = case_dict.get("class_period_end")

        if class_start and class_end:
            exclusions.append({
                "case_name": str(case_dict.get("case_name", "Unknown"))[:60],
                "class_start": str(class_start)[:10],
                "class_end": str(class_end)[:10],
                "status": str(case_dict.get("status", "Unknown")),
                "settlement": str(case_dict.get("settlement_amount", "N/A")),
            })

    return exclusions


def _fmt_shares(n: int | float) -> str:
    """Format share count compactly."""
    n = safe_float(n)
    if n >= 1e9:
        return f"{n / 1e9:.1f}B"
    if n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.0f}K"
    return f"{n:,.0f}"


def _build_chart_data(
    dates: list[str],
    closes: list[float],
    exposures: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build chart data with damage periods for SVG rendering."""
    damage_periods = []
    for exp in exposures:
        damage_periods.append({
            "start_idx": exp["peak_idx"],
            "end_idx": len(closes) - 1,  # Always extends to today
            "start_date": exp["peak_date"],
            "end_date": dates[-1][:10],
            "drop_pct": exp["drop_pct"],
            "label": exp["label"],
        })

    return {
        "dates": dates,
        "closes": closes,
        "damage_periods": damage_periods,
        "total_points": len(dates),
    }


__all__ = ["build_ddl_context"]
