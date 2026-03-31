"""Data extraction layer for Bloomberg dark theme stock charts.

Separates data extraction from matplotlib rendering. Provides:
- ChartData: dataclass holding all series and metadata for one chart
- extract_chart_data: reads AnalysisState, returns ChartData
- compute_chart_stats: calculates header metrics (price, returns, alpha)
- index_to_base: indexes a price series to a starting value (100)
- aggregate_weekly: reduces daily data to weekly for 5Y charts

Computation functions (beta, volatility, drawdown) live in
chart_computations.py and are re-exported here for convenience.

All data access uses get_close_prices() / get_dates() from stock_drops.py
which handle the column-oriented yfinance dict format correctly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from do_uw.models.market_events import StockDropEvent
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.stock_drops import get_close_prices, get_dates
from do_uw.stages.render.charts.chart_computations import (
    compute_annualized_vol,
    compute_beta,
    compute_drawdown_series,
    compute_idiosyncratic_vol,
    compute_rolling_volatility,
    compute_sector_beta,
)

# Minimum data points required to render a chart.
_MIN_POINTS = 5

# 5Y chart drop thresholds: only show >10% single-day or >15% cumulative.
_5Y_SINGLE_THRESHOLD = -10.0
_5Y_CUMULATIVE_THRESHOLD = -15.0

# Market-wide drops need higher threshold (less D&O relevant).
_MARKET_WIDE_THRESHOLD = -10.0


@dataclass
class ChartData:
    """All series data needed to render one stock chart period."""

    dates: list[datetime]
    prices: list[float]
    etf_dates: list[datetime] | None
    etf_prices: list[float] | None
    etf_ticker: str
    spy_dates: list[datetime] | None
    spy_prices: list[float] | None
    drops: list[StockDropEvent]
    ticker: str
    period: str  # "1Y" or "5Y"

    # Volume data aligned with dates.
    volumes: list[float] = field(default_factory=list)

    # Earnings event markers: {date, surprise_pct, eps_estimate, reported_eps}.
    earnings_events: list[dict[str, Any]] = field(default_factory=list)

    # Litigation event markers: {date, case_name, case_type}.
    litigation_events: list[dict[str, Any]] = field(default_factory=list)

    # SCA class period ranges: {start, end, case_name} for chart shading.
    class_periods: list[dict[str, Any]] = field(default_factory=list)

    # Beta and volatility metrics.
    company_beta: float | None = None
    sector_beta: float | None = None
    company_vol_90d: float | None = None
    sector_vol_90d: float | None = None
    idiosyncratic_vol: float | None = None


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------


def extract_chart_data(
    state: AnalysisState, period: str,
) -> ChartData | None:
    """Extract and prepare all data needed for a stock chart.

    Reads acquired_data.market_data using the CORRECT keys:
    - Company: history_1y / history_5y
    - Sector ETF: sector_history_1y / sector_history_5y
    - SPY: spy_history_1y / spy_history_5y
    - ETF ticker: sector_etf

    For 5Y charts, aggregates to weekly data points.

    Returns:
        ChartData ready for rendering, or None if insufficient data.
    """
    acquired = state.acquired_data
    if acquired is None:
        return None

    market_data: dict[str, Any] = acquired.market_data

    # Company price history -- use correct keys.
    _HIST_KEYS = {"1Y": "history_1y", "2Y": "history_2y", "5Y": "history_5y"}
    hist_key = _HIST_KEYS.get(period, "history_1y")
    company_hist: dict[str, Any] = market_data.get(hist_key, {})
    if not isinstance(company_hist, dict):
        return None

    raw_prices = get_close_prices(company_hist)
    raw_dates_str = get_dates(company_hist)
    if len(raw_prices) < _MIN_POINTS or len(raw_dates_str) < _MIN_POINTS:
        return None

    dates = _parse_dates(raw_dates_str)
    min_len = min(len(dates), len(raw_prices))
    dates = dates[:min_len]
    prices = raw_prices[:min_len]

    # Volume data from company history.
    raw_volumes = _get_volumes(company_hist)
    volumes = raw_volumes[:min_len] if raw_volumes else []

    # Sector ETF history.
    _ETF_KEYS = {"1Y": "sector_history_1y", "2Y": "sector_history_2y", "5Y": "sector_history_5y"}
    etf_key = _ETF_KEYS.get(period, "sector_history_1y")
    etf_hist: dict[str, Any] = market_data.get(etf_key, {})
    etf_ticker = str(market_data.get("sector_etf", ""))
    etf_dates: list[datetime] | None = None
    etf_prices: list[float] | None = None

    if isinstance(etf_hist, dict) and etf_ticker:
        e_prices = get_close_prices(etf_hist)
        e_dates_str = get_dates(etf_hist)
        if len(e_prices) >= _MIN_POINTS:
            e_dates = _parse_dates(e_dates_str)
            etf_prices = e_prices[: len(e_dates)]
            etf_dates = e_dates

    # SPY history.
    _SPY_KEYS = {"1Y": "spy_history_1y", "2Y": "spy_history_2y", "5Y": "spy_history_5y"}
    spy_key = _SPY_KEYS.get(period, "spy_history_1y")
    spy_hist: dict[str, Any] = market_data.get(spy_key, {})
    spy_dates: list[datetime] | None = None
    spy_prices: list[float] | None = None

    if isinstance(spy_hist, dict):
        s_prices = get_close_prices(spy_hist)
        s_dates_str = get_dates(spy_hist)
        if len(s_prices) >= _MIN_POINTS:
            s_dates = _parse_dates(s_dates_str)
            spy_prices = s_prices[: len(s_dates)]
            spy_dates = s_dates

    # Drop events filtered by period.
    drops = _filter_drops_for_period(state, period)

    # Earnings events from market_data.
    earnings_events = _extract_earnings_events(market_data, dates)

    # Litigation events from extracted litigation data.
    litigation_events = _extract_litigation_events(state, dates)

    # SCA class period ranges for chart shading.
    class_periods = _extract_class_periods(state, dates)

    # Beta and volatility computations (pre-aggregation for accuracy).
    company_beta = _extract_company_beta(market_data)
    sector_beta_val = compute_sector_beta(etf_prices, spy_prices)
    company_vol_90d = compute_annualized_vol(prices, 90)
    sector_vol_90d = compute_annualized_vol(etf_prices, 90) if etf_prices else None
    idiosyncratic_vol_val = compute_idiosyncratic_vol(prices, spy_prices)

    # 5Y: aggregate to weekly.
    if period == "5Y":
        # Save pre-aggregation dates for volume sum.
        pre_agg_dates = dates[:]
        dates, prices = aggregate_weekly(dates, prices)
        if volumes:
            _, volumes = aggregate_weekly_sum(pre_agg_dates, volumes)
            volumes = volumes[:len(dates)]
        if etf_dates and etf_prices:
            etf_dates, etf_prices = aggregate_weekly(etf_dates, etf_prices)
        if spy_dates and spy_prices:
            spy_dates, spy_prices = aggregate_weekly(spy_dates, spy_prices)

    if len(prices) < _MIN_POINTS:
        return None

    return ChartData(
        dates=dates,
        prices=prices,
        etf_dates=etf_dates,
        etf_prices=etf_prices,
        etf_ticker=etf_ticker,
        spy_dates=spy_dates,
        spy_prices=spy_prices,
        drops=drops,
        ticker=state.ticker,
        period=period,
        volumes=volumes,
        earnings_events=earnings_events,
        litigation_events=litigation_events,
        class_periods=class_periods,
        company_beta=company_beta,
        sector_beta=sector_beta_val,
        company_vol_90d=company_vol_90d,
        sector_vol_90d=sector_vol_90d,
        idiosyncratic_vol=idiosyncratic_vol_val,
    )


# ---------------------------------------------------------------------------
# Stats computation
# ---------------------------------------------------------------------------


def compute_chart_stats(
    data: ChartData,
    state: AnalysisState | None = None,
) -> dict[str, str | float | None]:
    """Compute key metrics for the stats header above the chart.

    Returns dict with formatted values:
    - current_price, high_52w, low_52w, total_return_pct
    - sector_return_pct, alpha_pct (all as formatted strings or "N/A")
    - When state is provided: market_contribution, sector_contribution,
      company_residual, mdd_ratio, sector_mdd, max_drawdown
    """
    stats: dict[str, str | float | None] = {}

    if not data.prices:
        return {"current_price": "N/A"}

    current = data.prices[-1]
    start = data.prices[0]
    stats["current_price"] = round(current, 2)
    stats["high_52w"] = round(max(data.prices), 2)
    stats["low_52w"] = round(min(data.prices), 2)

    if start > 0:
        total_return = (current - start) / start * 100.0
        stats["total_return_pct"] = round(total_return, 1)
    else:
        stats["total_return_pct"] = None

    # Sector ETF return.
    if data.etf_prices and len(data.etf_prices) >= 2:
        etf_start = data.etf_prices[0]
        etf_end = data.etf_prices[-1]
        if etf_start > 0:
            sector_ret = (etf_end - etf_start) / etf_start * 100.0
            stats["sector_return_pct"] = round(sector_ret, 1)
        else:
            stats["sector_return_pct"] = None
    else:
        stats["sector_return_pct"] = None

    # Alpha = company return - sector return.
    tr = stats.get("total_return_pct")
    sr = stats.get("sector_return_pct")
    if isinstance(tr, (int, float)) and isinstance(sr, (int, float)):
        stats["alpha_pct"] = round(float(tr) - float(sr), 1)
    else:
        stats["alpha_pct"] = None

    # Return decomposition and MDD ratio from state (when available).
    if state is not None and state.extracted and state.extracted.market:
        stock = state.extracted.market.stock
        period = data.period

        # Return decomposition: market, sector, company-specific.
        if period == "1Y":
            mkt_sv = stock.returns_1y_market
            sec_sv = stock.returns_1y_sector
            co_sv = stock.returns_1y_company
            mdd_sv = stock.mdd_ratio_1y
            smdd_sv = stock.sector_mdd_1y
            dd_sv = stock.max_drawdown_1y
        else:
            mkt_sv = stock.returns_5y_market
            sec_sv = stock.returns_5y_sector
            co_sv = stock.returns_5y_company
            mdd_sv = stock.mdd_ratio_5y
            smdd_sv = stock.sector_mdd_5y
            dd_sv = stock.max_drawdown_5y

        stats["market_contribution"] = mkt_sv.value if mkt_sv is not None else None
        stats["sector_contribution"] = sec_sv.value if sec_sv is not None else None
        stats["company_residual"] = co_sv.value if co_sv is not None else None
        stats["mdd_ratio"] = mdd_sv.value if mdd_sv is not None else None
        stats["sector_mdd"] = smdd_sv.value if smdd_sv is not None else None
        stats["max_drawdown"] = dd_sv.value if dd_sv is not None else None

    return stats


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------


def index_to_base(
    prices: list[float], base_value: float = 100.0,
) -> list[float]:
    """Index a price series so the first value equals base_value."""
    if not prices or prices[0] <= 0:
        return prices
    factor = base_value / prices[0]
    return [p * factor for p in prices]


def aggregate_weekly(
    dates: list[datetime], prices: list[float],
) -> tuple[list[datetime], list[float]]:
    """Group daily data by ISO week, keep last entry per week."""
    if not dates:
        return dates, prices

    weekly_dates: list[datetime] = []
    weekly_prices: list[float] = []

    current_week: tuple[int, int] | None = None
    last_date: datetime | None = None
    last_price: float = 0.0

    for dt_val, price in zip(dates, prices):
        week_key = dt_val.isocalendar()[:2]
        if current_week != week_key:
            if last_date is not None:
                weekly_dates.append(last_date)
                weekly_prices.append(last_price)
            current_week = week_key
        last_date = dt_val
        last_price = price

    if last_date is not None:
        weekly_dates.append(last_date)
        weekly_prices.append(last_price)

    return weekly_dates, weekly_prices


def aggregate_weekly_sum(
    dates_orig: list[datetime], values: list[float],
) -> tuple[list[datetime], list[float]]:
    """Group daily data by ISO week, summing values (for volume)."""
    if not dates_orig or not values:
        return [], []

    weekly_dates: list[datetime] = []
    weekly_values: list[float] = []

    current_week: tuple[int, int] | None = None
    last_date: datetime | None = None
    week_sum: float = 0.0

    min_len = min(len(dates_orig), len(values))
    for dt_val, val in zip(dates_orig[:min_len], values[:min_len]):
        week_key = dt_val.isocalendar()[:2]
        if current_week != week_key:
            if last_date is not None:
                weekly_dates.append(last_date)
                weekly_values.append(week_sum)
            current_week = week_key
            week_sum = 0.0
        last_date = dt_val
        week_sum += val

    if last_date is not None:
        weekly_dates.append(last_date)
        weekly_values.append(week_sum)

    return weekly_dates, weekly_values


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _get_volumes(history: dict[str, Any]) -> list[float]:
    """Extract Volume column from yfinance history dict."""
    raw = history.get("Volume", [])
    if not isinstance(raw, list):
        return []
    result: list[float] = []
    for v in raw:
        try:
            fv = float(v)
            if math.isnan(fv) or math.isinf(fv):
                result.append(0.0)
            else:
                result.append(fv)
        except (TypeError, ValueError):
            result.append(0.0)
    return result


def _extract_litigation_events(
    state: AnalysisState,
    chart_dates: list[datetime],
) -> list[dict[str, Any]]:
    """Extract litigation filing events from state, filtered to chart range.

    Reads securities_class_actions and derivative_suits from
    state.extracted.litigation. Each case with a filing_date within
    the chart date range becomes an event marker.

    Returns:
        Sorted list of event dicts with keys: date, case_name, case_type.
    """
    if not chart_dates:
        return []

    extracted = state.extracted if state else None
    if extracted is None:
        return []

    litigation = getattr(extracted, "litigation", None)
    if litigation is None:
        return []

    start_date = chart_dates[0]
    end_date = chart_dates[-1]
    events: list[dict[str, Any]] = []

    # Combine all case lists that have filing dates.
    all_cases: list[Any] = []
    for attr in ("securities_class_actions", "derivative_suits"):
        cases = getattr(litigation, attr, None)
        if cases:
            all_cases.extend(cases)

    for case in all_cases:
        filing_sv = getattr(case, "filing_date", None)
        if filing_sv is None or filing_sv.value is None:
            continue

        filing_date = filing_sv.value
        # Convert date to datetime for comparison with chart dates.
        dt = datetime.combine(filing_date, datetime.min.time())

        if dt < start_date or dt > end_date:
            continue

        # Extract case_name from SourcedValue or plain string.
        raw_name = getattr(case, "case_name", None)
        if raw_name is not None and hasattr(raw_name, "value"):
            case_name = str(raw_name.value) if raw_name.value else "Filing"
        elif isinstance(raw_name, str):
            case_name = raw_name
        else:
            case_name = "Filing"

        # Extract case_type from coverage_type SourcedValue.
        raw_type = getattr(case, "coverage_type", None)
        if raw_type is not None and hasattr(raw_type, "value"):
            case_type = str(raw_type.value) if raw_type.value else None
        elif isinstance(raw_type, str):
            case_type = raw_type
        else:
            case_type = None

        events.append({
            "date": dt,
            "case_name": case_name,
            "case_type": case_type,
        })

    events.sort(key=lambda e: e["date"])
    return events


def _extract_class_periods(
    state: AnalysisState,
    chart_dates: list[datetime],
) -> list[dict[str, Any]]:
    """Extract SCA class period date ranges for chart shading.

    Reads from both extracted litigation SCAs and Supabase cases.
    Each class period with start AND end dates within or overlapping
    the chart range becomes a shading region.
    """
    if not chart_dates:
        return []

    try:
        from do_uw.stages.render.sca_counter import get_active_genuine_scas
    except ImportError:
        return []

    active = get_active_genuine_scas(state)
    if not active:
        return []

    chart_start = chart_dates[0]
    chart_end = chart_dates[-1]
    periods: list[dict[str, Any]] = []

    for sca in active:
        cp_start_raw = None
        cp_end_raw = None
        case_name = ""

        if isinstance(sca, dict):
            cp_start_raw = sca.get("class_period_start")
            cp_end_raw = sca.get("class_period_end")
            case_name = sca.get("case_name", "") or ""
        else:
            s = getattr(sca, "class_period_start", None)
            cp_start_raw = s.value if hasattr(s, "value") else s
            e = getattr(sca, "class_period_end", None)
            cp_end_raw = e.value if hasattr(e, "value") else e
            cn = getattr(sca, "case_name", None)
            case_name = cn.value if hasattr(cn, "value") else (cn or "")

        if not cp_start_raw or not cp_end_raw:
            continue

        try:
            if isinstance(cp_start_raw, str):
                dt_start = datetime.fromisoformat(str(cp_start_raw)[:10])
            else:
                dt_start = datetime.combine(cp_start_raw, datetime.min.time())
            if isinstance(cp_end_raw, str):
                dt_end = datetime.fromisoformat(str(cp_end_raw)[:10])
            else:
                dt_end = datetime.combine(cp_end_raw, datetime.min.time())
        except (ValueError, TypeError):
            continue

        # Include if any overlap with chart range.
        if dt_end < chart_start or dt_start > chart_end:
            continue

        # Clamp to chart range.
        vis_start = max(dt_start, chart_start)
        vis_end = min(dt_end, chart_end)

        periods.append({
            "start": vis_start,
            "end": vis_end,
            "case_name": str(case_name)[:40] if case_name else "SCA",
        })

    return periods


def _extract_earnings_events(
    market_data: dict[str, Any],
    chart_dates: list[datetime],
) -> list[dict[str, Any]]:
    """Extract earnings events from market_data, filtered to chart range.

    Handles three formats:
    1. Column-oriented dict: {"Earnings Date": [...], "Surprise(%)": [...], ...}
       (yfinance get_earnings_dates() → DataFrame.to_dict("list"))
    2. Row-oriented dict: {date_str: info_dict, ...}
    3. List of dicts: [{date: ..., surprise_pct: ...}, ...]
    """
    raw_earnings = market_data.get("earnings_dates")
    if not raw_earnings or not isinstance(raw_earnings, (dict, list)):
        return []

    if not chart_dates:
        return []

    start_date = chart_dates[0]
    end_date = chart_dates[-1]
    events: list[dict[str, Any]] = []

    if isinstance(raw_earnings, dict):
        # Check for column-oriented format (most common from yfinance)
        date_col = raw_earnings.get("Earnings Date")
        if isinstance(date_col, (list, dict)):
            # Column-oriented: {"Earnings Date": [...], "Surprise(%)": [...]}
            dates_list = list(date_col.values()) if isinstance(date_col, dict) else date_col
            surprise_col = raw_earnings.get("Surprise(%)", {})
            surprises = list(surprise_col.values()) if isinstance(surprise_col, dict) else (surprise_col if isinstance(surprise_col, list) else [])
            estimate_col = raw_earnings.get("EPS Estimate", {})
            estimates = list(estimate_col.values()) if isinstance(estimate_col, dict) else (estimate_col if isinstance(estimate_col, list) else [])
            reported_col = raw_earnings.get("Reported EPS", {})
            reporteds = list(reported_col.values()) if isinstance(reported_col, dict) else (reported_col if isinstance(reported_col, list) else [])

            for i, date_val in enumerate(dates_list):
                dt = _parse_single_date(str(date_val))
                if dt is None or dt < start_date or dt > end_date:
                    continue
                events.append({
                    "date": dt,
                    "surprise_pct": _safe_float(surprises[i]) if i < len(surprises) else None,
                    "eps_estimate": _safe_float(estimates[i]) if i < len(estimates) else None,
                    "reported_eps": _safe_float(reporteds[i]) if i < len(reporteds) else None,
                })
        else:
            # Row-oriented: {date_str: info_dict, ...}
            for date_key, info in raw_earnings.items():
                dt = _parse_single_date(str(date_key))
                if dt is None or dt < start_date or dt > end_date:
                    continue
                event: dict[str, Any] = {"date": dt}
                if isinstance(info, dict):
                    event["surprise_pct"] = _safe_float(info.get("surprise_pct") or info.get("Surprise(%)"))
                    event["eps_estimate"] = _safe_float(info.get("eps_estimate") or info.get("EPS Estimate"))
                    event["reported_eps"] = _safe_float(info.get("reported_eps") or info.get("Reported EPS"))
                events.append(event)
    elif isinstance(raw_earnings, list):
        for item in raw_earnings:
            if not isinstance(item, dict):
                continue
            date_val = item.get("date") or item.get("Earnings Date")
            dt = _parse_single_date(str(date_val)) if date_val else None
            if dt is None or dt < start_date or dt > end_date:
                continue
            events.append({
                "date": dt,
                "surprise_pct": _safe_float(item.get("surprise_pct") or item.get("Surprise(%)")),
                "eps_estimate": _safe_float(item.get("eps_estimate") or item.get("EPS Estimate")),
                "reported_eps": _safe_float(item.get("reported_eps") or item.get("Reported EPS")),
            })

    events.sort(key=lambda e: e["date"])
    return events


def _extract_company_beta(market_data: dict[str, Any]) -> float | None:
    """Get company beta from yfinance info dict."""
    info = market_data.get("info")
    if not isinstance(info, dict):
        return None
    return _safe_float(info.get("beta"))


def _parse_dates(date_strings: list[str]) -> list[datetime]:
    """Parse date strings to datetime objects, skipping unparseable."""
    result: list[datetime] = []
    for ds in date_strings:
        try:
            dt = datetime.fromisoformat(ds[:10])
            result.append(dt)
        except (ValueError, TypeError):
            continue
    return result


def _parse_single_date(date_str: str) -> datetime | None:
    """Parse a single date string to datetime."""
    try:
        return datetime.fromisoformat(date_str[:10])
    except (ValueError, TypeError):
        return None


def _safe_float(val: Any) -> float | None:
    """Convert value to float, returning None on failure or NaN."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _filter_drops_for_period(
    state: AnalysisState, period: str,
) -> list[StockDropEvent]:
    """Get drop events filtered by chart period thresholds.

    Market-wide drops (SPY also fell >3%) use a higher threshold
    (-10%) since they're less D&O relevant than company-specific drops.
    """
    market = state.extracted.market if state.extracted else None
    if market is None:
        return []

    all_drops: list[StockDropEvent] = []
    analysis = market.stock_drops

    all_drops.extend(analysis.single_day_drops)
    all_drops.extend(analysis.multi_day_drops)

    filtered: list[StockDropEvent] = []
    for drop in all_drops:
        pct = drop.drop_pct.value if drop.drop_pct else 0.0
        cum = drop.cumulative_pct

        # Market-wide drops need higher threshold (less D&O relevant)
        # UNLESS the drop is also company-specific (stock fell more than market).
        if drop.is_market_wide and not drop.is_company_specific:
            threshold = _MARKET_WIDE_THRESHOLD
        elif period == "5Y":
            threshold = _5Y_SINGLE_THRESHOLD
        else:
            # 1Y company-specific or mixed: default -5% (all drops pass)
            threshold = -5.0

        if pct <= threshold:
            filtered.append(drop)
            continue

        # 5Y cumulative threshold for multi-day slides.
        if period == "5Y" and cum is not None and cum <= _5Y_CUMULATIVE_THRESHOLD:
            filtered.append(drop)

    return filtered


__all__ = [
    "ChartData",
    "aggregate_weekly",
    "aggregate_weekly_sum",
    "compute_beta",
    "compute_chart_stats",
    "compute_drawdown_series",
    "compute_rolling_volatility",
    "extract_chart_data",
    "index_to_base",
]
