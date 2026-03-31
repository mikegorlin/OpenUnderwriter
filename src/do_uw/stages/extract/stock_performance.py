"""Stock performance extraction for SECT4-01, SECT4-02, SECT4-03.

Identifies significant stock declines in trailing 18 months, compares
against sector ETF to determine company-specific drops, and computes
performance table metrics (returns, beta, volatility, max drawdown).

Stock drops are the #1 trigger for D&O securities class actions.

Drop detection helpers are in stock_drops.py (500-line split).

Usage:
    perf, drops, report = extract_stock_performance(state)
    state.extracted.market.stock = perf
    state.extracted.market.stock_drops = drops
"""

from __future__ import annotations

import logging
import math
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market import StockPerformance
from do_uw.models.market_events import (
    DropType,
    StockDropAnalysis,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filings,
    get_market_data,
    now,
    sourced_float,
)
from do_uw.stages.extract.stock_drop_analysis import (
    compute_recovery_days,
    group_consecutive_drops,
    tag_market_wide_events,
)
from do_uw.stages.render.charts.chart_computations import (
    classify_vol_regime,
    compute_abnormal_return,
    compute_ddl_exposure,
    compute_ewma_volatility,
)
from do_uw.stages.extract.stock_drop_enrichment import enrich_all_drops
from do_uw.stages.extract.stock_drops import (
    SOURCE_LABEL,
    attribute_triggers,
    compute_daily_returns,
    compute_sector_comparison,
    find_multi_day_drops,
    find_single_day_drops,
    get_close_prices,
    get_dates,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)


def _get_8k_docs_for_reverse_lookup(state: AnalysisState) -> list[dict[str, Any]]:
    """Get 8-K filing documents from acquired data for reverse lookup."""
    if state.acquired_data is None:
        return []
    docs = state.acquired_data.filing_documents.get("8-K", [])
    if not isinstance(docs, list):
        return []
    return cast(list[dict[str, Any]], docs)


def _get_web_results_for_reverse_lookup(state: AnalysisState) -> list[dict[str, Any]]:
    """Get web search results from acquired data for reverse lookup."""
    if state.acquired_data is None:
        return []
    raw = state.acquired_data.web_search_results
    if isinstance(raw, list):
        return cast(list[dict[str, Any]], raw)
    if isinstance(raw, dict):
        all_results: list[dict[str, Any]] = []
        for _key, val in raw.items():
            if isinstance(val, list):
                all_results.extend(cast(list[dict[str, Any]], val))
        return all_results
    return []


# Expected fields for the extraction report.
EXPECTED_FIELDS: list[str] = [
    "single_day_drops",
    "multi_day_drops",
    "current_price",
    "returns_1y",
    "beta",
    "volatility_90d",
    "max_drawdown_1y",
]


# ---------------------------------------------------------------------------
# Performance metrics
# ---------------------------------------------------------------------------


def _compute_performance_metrics(
    history_1y: dict[str, Any],
    history_5y: dict[str, Any],
    info: dict[str, Any],
    market_data: dict[str, Any] | None = None,
) -> StockPerformance:
    """Compute returns, beta, volatility, and max drawdown.

    Populates a StockPerformance model from price histories
    and the yfinance info dict. When market_data is provided,
    also computes return decomposition and MDD ratio.
    """
    perf = StockPerformance()
    prices_1y = get_close_prices(history_1y)
    prices_5y = get_close_prices(history_5y)
    dates_1y = get_dates(history_1y)

    # Detect limited trading history (recent IPO).
    # If 1Y and 5Y have same length, company has < 1 year of history.
    trading_days = len(prices_1y)
    perf.trading_days_available = trading_days
    if dates_1y:
        perf.first_trading_date = dates_1y[0][:10]
    has_full_year = trading_days >= 250
    # 5Y data is distinct only if it has meaningfully more data than 1Y.
    has_distinct_5y = len(prices_5y) > len(prices_1y) + 20

    # Current price from info or latest close.
    current = _extract_float(info, "currentPrice")
    if current is None and prices_1y:
        current = prices_1y[-1]
    if current is not None:
        perf.current_price = sourced_float(
            round(current, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # 52-week high/low — use yfinance values which cover actual available period.
    high_52w = _extract_float(info, "fiftyTwoWeekHigh")
    if high_52w is not None:
        perf.high_52w = sourced_float(
            round(high_52w, 2), SOURCE_LABEL, Confidence.MEDIUM
        )
    low_52w = _extract_float(info, "fiftyTwoWeekLow")
    if low_52w is not None:
        perf.low_52w = sourced_float(
            round(low_52w, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Decline from 52-week high.
    if current is not None and high_52w is not None and high_52w > 0:
        decline = (current - high_52w) / high_52w * 100.0
        perf.decline_from_high_pct = sourced_float(
            round(decline, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Return since available history (labeled as 1Y even if shorter — rendering adjusts).
    if len(prices_1y) >= 2:
        ret_1y = (prices_1y[-1] - prices_1y[0]) / prices_1y[0] * 100.0
        perf.returns_1y = sourced_float(
            round(ret_1y, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # 5-year return — only if we have distinct 5Y data.
    if has_distinct_5y and len(prices_5y) >= 2:
        ret_5y = (prices_5y[-1] - prices_5y[0]) / prices_5y[0] * 100.0
        perf.returns_5y = sourced_float(
            round(ret_5y, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # YTD return.
    ytd_ret = _extract_float(info, "ytdReturn")
    if ytd_ret is not None:
        perf.returns_ytd = sourced_float(
            round(ytd_ret * 100.0, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Beta from info dict.
    beta = _extract_float(info, "beta")
    if beta is not None:
        perf.beta = sourced_float(
            round(beta, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Volatility — use min(90, available) window for recent IPOs.
    vol_window = min(90, trading_days - 1) if trading_days > 30 else 90
    vol = compute_volatility(prices_1y, window=vol_window)
    if vol is not None:
        perf.volatility_90d = sourced_float(
            round(vol, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Max drawdown (available history, labeled as 1Y).
    mdd = compute_max_drawdown(prices_1y)
    if mdd is not None:
        perf.max_drawdown_1y = sourced_float(
            round(mdd, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Max drawdown (5 year) — only if distinct data.
    if has_distinct_5y:
        mdd_5y = compute_max_drawdown(prices_5y)
        if mdd_5y is not None:
            perf.max_drawdown_5y = sourced_float(
                round(mdd_5y, 2), SOURCE_LABEL, Confidence.MEDIUM
            )

    # --- Easy-win yfinance fields (DN-032, DN-034) ---
    _populate_easy_win_fields(perf, info)

    # --- Return decomposition and MDD ratio (require market_data) ---
    if market_data is not None:
        _compute_decomposition_and_mdd(perf, prices_1y, prices_5y, market_data)

    return perf


def _populate_easy_win_fields(
    perf: StockPerformance, info: dict[str, Any],
) -> None:
    """Populate easy-win fields from yfinance info dict.

    These are data points already acquired by yfinance but not previously
    stored in the state model (DN-032 volume, DN-034 valuation ratios).
    """
    from do_uw.stages.extract.sourced import sourced_int

    # Average daily volume (DN-032)
    avg_vol = _extract_float(info, "averageDailyVolume10Day")
    if avg_vol is None:
        avg_vol = _extract_float(info, "averageVolume")
    if avg_vol is not None and avg_vol > 0:
        perf.avg_daily_volume = sourced_int(
            int(avg_vol), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Valuation ratios (DN-034)
    trailing_pe = _extract_float(info, "trailingPE")
    if trailing_pe is not None:
        perf.pe_ratio = sourced_float(
            round(trailing_pe, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    forward_pe = _extract_float(info, "forwardPE")
    if forward_pe is not None:
        perf.forward_pe = sourced_float(
            round(forward_pe, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    ev_ebitda = _extract_float(info, "enterpriseToEbitda")
    if ev_ebitda is not None:
        perf.ev_ebitda = sourced_float(
            round(ev_ebitda, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    peg = _extract_float(info, "pegRatio")
    if peg is None:
        peg = _extract_float(info, "trailingPegRatio")
    if peg is not None:
        perf.peg_ratio = sourced_float(
            round(peg, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Additional valuation ratios
    ptb = _extract_float(info, "priceToBook")
    if ptb is not None:
        perf.price_to_book = sourced_float(
            round(ptb, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    pts = _extract_float(info, "priceToSalesTrailing12Months")
    if pts is not None:
        perf.price_to_sales = sourced_float(
            round(pts, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    etr = _extract_float(info, "enterpriseToRevenue")
    if etr is not None:
        perf.enterprise_to_revenue = sourced_float(
            round(etr, 2), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Profitability margins
    pm = _extract_float(info, "profitMargins")
    if pm is not None:
        perf.profit_margin = sourced_float(
            round(pm, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    om = _extract_float(info, "operatingMargins")
    if om is not None:
        perf.operating_margin = sourced_float(
            round(om, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    gm = _extract_float(info, "grossMargins")
    if gm is not None:
        perf.gross_margin = sourced_float(
            round(gm, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    roe = _extract_float(info, "returnOnEquity")
    if roe is not None:
        perf.return_on_equity = sourced_float(
            round(roe, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    roa = _extract_float(info, "returnOnAssets")
    if roa is not None:
        perf.return_on_assets = sourced_float(
            round(roa, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Growth metrics
    revg = _extract_float(info, "revenueGrowth")
    if revg is not None:
        perf.revenue_growth = sourced_float(
            round(revg, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    earng = _extract_float(info, "earningsGrowth")
    if earng is not None:
        perf.earnings_growth = sourced_float(
            round(earng, 4), SOURCE_LABEL, Confidence.MEDIUM
        )

    # Scale metrics
    mcap = _extract_float(info, "marketCap")
    if mcap is not None:
        perf.market_cap_yf = sourced_float(
            mcap, SOURCE_LABEL, Confidence.MEDIUM
        )

    ev = _extract_float(info, "enterpriseValue")
    if ev is not None:
        perf.enterprise_value = sourced_float(
            ev, SOURCE_LABEL, Confidence.MEDIUM
        )

    fte = _extract_float(info, "fullTimeEmployees")
    if fte is not None:
        perf.employee_count_yf = sourced_int(
            int(fte), SOURCE_LABEL, Confidence.MEDIUM
        )


def _compute_decomposition_and_mdd(
    perf: StockPerformance,
    prices_1y: list[float],
    prices_5y: list[float],
    market_data: dict[str, Any],
) -> None:
    """Compute return decomposition and MDD ratio from market data.

    Populates returns_Ny_market/sector/company and mdd_ratio_Ny fields
    on StockPerformance.
    """
    from do_uw.stages.render.charts.chart_computations import (
        compute_mdd_ratio,
        compute_return_decomposition,
    )

    # Helper to get close prices from a market_data key.
    def _prices_from_key(key: str) -> list[float]:
        raw = market_data.get(key, {})
        hist = cast(dict[str, Any], raw) if isinstance(raw, dict) else {}
        return get_close_prices(hist) if hist else []

    spy_prices_1y = _prices_from_key("spy_history_1y")
    sector_prices_1y = _prices_from_key("sector_history_1y")
    spy_prices_5y = _prices_from_key("spy_history_5y")
    sector_prices_5y = _prices_from_key("sector_history_5y")

    # For recent IPOs, trim benchmark series to match company's actual
    # trading period (align from end so dates match).
    n_company = len(prices_1y)
    if n_company < len(spy_prices_1y):
        spy_prices_1y = spy_prices_1y[-n_company:]
    if n_company < len(sector_prices_1y):
        sector_prices_1y = sector_prices_1y[-n_company:]

    has_distinct_5y = len(prices_5y) > n_company + 20

    # --- 1Y Return decomposition (uses actual available period) ---
    if prices_1y and spy_prices_1y and sector_prices_1y:
        decomp_1y = compute_return_decomposition(
            prices_1y, spy_prices_1y, sector_prices_1y,
        )
        if decomp_1y is not None:
            perf.returns_1y_market = sourced_float(
                round(decomp_1y["market_contribution"], 2),
                SOURCE_LABEL, Confidence.MEDIUM,
            )
            perf.returns_1y_sector = sourced_float(
                round(decomp_1y["sector_contribution"], 2),
                SOURCE_LABEL, Confidence.MEDIUM,
            )
            perf.returns_1y_company = sourced_float(
                round(decomp_1y["company_residual"], 2),
                SOURCE_LABEL, Confidence.MEDIUM,
            )

    # --- 5Y Return decomposition — only when distinct data exists ---
    if has_distinct_5y and prices_5y and spy_prices_5y and sector_prices_5y:
        decomp_5y = compute_return_decomposition(
            prices_5y, spy_prices_5y, sector_prices_5y,
        )
        if decomp_5y is not None:
            perf.returns_5y_market = sourced_float(
                round(decomp_5y["market_contribution"], 2),
                SOURCE_LABEL, Confidence.MEDIUM,
            )
            perf.returns_5y_sector = sourced_float(
                round(decomp_5y["sector_contribution"], 2),
                SOURCE_LABEL, Confidence.MEDIUM,
            )
            perf.returns_5y_company = sourced_float(
                round(decomp_5y["company_residual"], 2),
                SOURCE_LABEL, Confidence.MEDIUM,
            )

    # --- Sector MDD and MDD ratio ---
    if sector_prices_1y:
        smdd_1y = compute_max_drawdown(sector_prices_1y)
        if smdd_1y is not None:
            perf.sector_mdd_1y = sourced_float(
                round(smdd_1y, 2), SOURCE_LABEL, Confidence.MEDIUM,
            )

    if has_distinct_5y and sector_prices_5y:
        smdd_5y = compute_max_drawdown(sector_prices_5y)
        if smdd_5y is not None:
            perf.sector_mdd_5y = sourced_float(
                round(smdd_5y, 2), SOURCE_LABEL, Confidence.MEDIUM,
            )

    # MDD ratio (available period).
    if prices_1y and sector_prices_1y:
        ratio_1y = compute_mdd_ratio(prices_1y, sector_prices_1y)
        if ratio_1y is not None:
            perf.mdd_ratio_1y = sourced_float(
                round(ratio_1y, 4), SOURCE_LABEL, Confidence.MEDIUM,
            )

    # MDD ratio 5Y — only when distinct data.
    if has_distinct_5y and prices_5y and sector_prices_5y:
        ratio_5y = compute_mdd_ratio(prices_5y, sector_prices_5y)
        if ratio_5y is not None:
            perf.mdd_ratio_5y = sourced_float(
                round(ratio_5y, 4), SOURCE_LABEL, Confidence.MEDIUM,
            )


def _compute_sector_derived_metrics(
    perf: StockPerformance,
    market_data: dict[str, Any],
    history_1y: dict[str, Any],
) -> None:
    """Compute sector-relative beta, vol, and idiosyncratic vol.

    These metrics require sector ETF and SPY price series alongside
    the company's own prices. Results are stored on StockPerformance.
    """
    from do_uw.stages.render.charts.chart_computations import (
        compute_annualized_vol,
        compute_idiosyncratic_vol,
        compute_sector_beta,
    )

    prices_1y = get_close_prices(history_1y)
    if not prices_1y:
        return

    # Get SPY prices.
    raw_spy = market_data.get("spy_history_1y", {})
    spy_hist = cast(dict[str, Any], raw_spy) if isinstance(raw_spy, dict) else {}
    spy_prices = get_close_prices(spy_hist) if spy_hist else []

    # Get sector ETF prices.
    raw_sector = market_data.get(
        "sector_history_1y", market_data.get("sector_history", {}),
    )
    sector_hist = cast(dict[str, Any], raw_sector) if isinstance(raw_sector, dict) else {}
    sector_prices = get_close_prices(sector_hist) if sector_hist else []

    # Sector beta (sector ETF vs SPY).
    if sector_prices and spy_prices:
        sb = compute_sector_beta(sector_prices, spy_prices)
        if sb is not None:
            perf.sector_beta = sourced_float(
                round(sb, 4), SOURCE_LABEL, Confidence.MEDIUM,
            )
            # Beta ratio = company beta / sector beta.
            if perf.beta is not None and sb > 0:
                br = perf.beta.value / sb
                perf.beta_ratio = sourced_float(
                    round(br, 4), SOURCE_LABEL, Confidence.MEDIUM,
                )

    # Sector 90-day volatility.
    if sector_prices:
        sv = compute_annualized_vol(sector_prices, window=90)
        if sv is not None:
            perf.sector_vol_90d = sourced_float(
                round(sv, 4), SOURCE_LABEL, Confidence.MEDIUM,
            )

    # Idiosyncratic volatility.
    if spy_prices:
        iv = compute_idiosyncratic_vol(prices_1y, spy_prices)
        if iv is not None:
            perf.idiosyncratic_vol = sourced_float(
                round(iv, 4), SOURCE_LABEL, Confidence.MEDIUM,
            )


def _find_price_index(dates: list[str], target: str) -> int | None:
    """Find index of target date in dates list (prefix match)."""
    for i, d in enumerate(dates):
        if d[:10] == target[:10]:
            return i
    return None


def _extract_float(d: dict[str, Any], key: str) -> float | None:
    """Safely extract a float from a dict."""
    val = d.get(key)
    if val is None:
        return None
    try:
        fval = float(val)
        if math.isnan(fval) or math.isinf(fval):
            return None
        return fval
    except (TypeError, ValueError):
        return None


def compute_volatility(
    prices: list[float], window: int = 90,
) -> float | None:
    """Compute annualized volatility from trailing N-day returns.

    Volatility = stdev(daily_returns) * sqrt(252).
    Uses the last `window` trading days of prices.
    """
    if len(prices) < max(window, 2):
        if len(prices) < 2:
            return None
        subset = prices
    else:
        subset = prices[-window:]

    returns = compute_daily_returns(subset)
    if len(returns) < 2:
        return None

    mean_r = sum(returns) / len(returns)
    variance = sum((r - mean_r) ** 2 for r in returns) / (len(returns) - 1)
    daily_vol = math.sqrt(variance)
    annualized = daily_vol * math.sqrt(252)
    return annualized


def compute_max_drawdown(prices: list[float]) -> float | None:
    """Compute maximum peak-to-trough drawdown as a percentage.

    Returns a negative number (e.g., -25.3 for a 25.3% drawdown).
    """
    if len(prices) < 2:
        return None

    peak = prices[0]
    max_dd = 0.0

    for price in prices[1:]:
        if price > peak:
            peak = price
        if peak > 0:
            dd = (price - peak) / peak * 100.0
            if dd < max_dd:
                max_dd = dd

    return max_dd if max_dd < 0.0 else None


# ---------------------------------------------------------------------------
# Phase 89: EWMA volatility, abnormal returns, DDL exposure
# ---------------------------------------------------------------------------


def _compute_ewma_and_regime(
    perf: StockPerformance,
    history: dict[str, Any],
) -> None:
    """Compute EWMA volatility and classify regime on StockPerformance."""
    prices = get_close_prices(history)
    if len(prices) < 30:
        return

    ewma_series = compute_ewma_volatility(prices)
    if not ewma_series:
        return

    # Store current EWMA vol (last value).
    last_val = ewma_series[-1]
    if last_val > 0:
        perf.ewma_vol_current = sourced_float(
            round(last_val, 2), SOURCE_LABEL, Confidence.MEDIUM,
        )

    # Classify regime.
    regime, duration = classify_vol_regime(ewma_series)
    perf.vol_regime = SourcedValue[str](
        value=regime,
        source=SOURCE_LABEL,
        confidence=Confidence.MEDIUM,
        as_of=now(),
    )
    perf.vol_regime_duration_days = duration


def _compute_abnormal_returns_for_drops(
    drops: StockDropAnalysis,
    drop_history: dict[str, Any],
    market_data: dict[str, Any],
) -> None:
    """Compute abnormal returns for each drop event using market model."""
    from do_uw.stages.render.charts.chart_computations import (
        compute_daily_returns as compute_decimal_returns,
    )

    prices = get_close_prices(drop_history)
    dates = get_dates(drop_history)

    # Get SPY prices aligned to the same period (prefer 2Y).
    raw_spy = market_data.get("spy_history_2y") or market_data.get("spy_history_1y", {})
    spy_history = cast(dict[str, Any], raw_spy) if isinstance(raw_spy, dict) else {}
    spy_prices = get_close_prices(spy_history) if spy_history else []

    if len(prices) < 2 or len(spy_prices) < 2:
        return

    # Use decimal returns (not percentage) for market model AR computation.
    company_returns = compute_decimal_returns(prices)
    spy_returns = compute_decimal_returns(spy_prices)

    # Align returns to same length (from the end).
    min_len = min(len(company_returns), len(spy_returns))
    if min_len < 60:
        return
    comp_ret = company_returns[-min_len:]
    mkt_ret = spy_returns[-min_len:]
    # returns[i] = (prices[i+1] - prices[i])/prices[i], so
    # the return ON dates[i+1] is returns[i].
    # For aligned returns trimmed from end: return_dates[j] = dates[offset + j + 1]
    # where offset = len(company_returns) - min_len.
    offset = len(company_returns) - min_len
    # return_dates[j] corresponds to comp_ret[j]
    return_dates = dates[offset + 1 : offset + 1 + min_len]

    all_events = drops.single_day_drops + drops.multi_day_drops
    for evt in all_events:
        if not evt.date or not evt.drop_pct:
            continue
        event_date = evt.date.value[:10]
        # Find index in return_dates.
        event_idx: int | None = None
        for i, d in enumerate(return_dates):
            if d[:10] == event_date:
                event_idx = i
                break
        if event_idx is None:
            continue

        result = compute_abnormal_return(comp_ret, mkt_ret, event_idx)
        if result is None:
            continue

        ar_pct, t_stat, is_sig = result
        evt.abnormal_return_pct = round(ar_pct, 2)
        evt.abnormal_return_t_stat = round(t_stat, 2)
        evt.is_statistically_significant = is_sig


def _compute_ddl_for_drops(
    drops: StockDropAnalysis,
    perf: StockPerformance,
) -> None:
    """Compute DDL/MDL exposure from worst drop and market cap."""
    if not drops.worst_single_day or not drops.worst_single_day.drop_pct:
        return
    if not perf.market_cap_yf:
        return

    market_cap = perf.market_cap_yf.value
    worst_drop_pct = drops.worst_single_day.drop_pct.value

    max_drawdown_pct: float | None = None
    if perf.max_drawdown_1y is not None:
        max_drawdown_pct = perf.max_drawdown_1y.value

    ddl_result = compute_ddl_exposure(market_cap, worst_drop_pct, max_drawdown_pct)

    drops.ddl_exposure = sourced_float(
        round(ddl_result["ddl_amount"], 2),  # type: ignore[arg-type]
        SOURCE_LABEL + "/computed",
        Confidence.MEDIUM,
    )

    if ddl_result["mdl_amount"] is not None:
        drops.mdl_exposure = sourced_float(
            round(ddl_result["mdl_amount"], 2),  # type: ignore[arg-type]
            SOURCE_LABEL + "/computed",
            Confidence.MEDIUM,
        )

    drops.ddl_settlement_estimate = sourced_float(
        round(ddl_result["settlement_estimate"], 2),  # type: ignore[arg-type]
        SOURCE_LABEL + "/computed",
        Confidence.MEDIUM,
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_stock_performance(
    state: AnalysisState,
) -> tuple[StockPerformance, StockDropAnalysis, ExtractionReport]:
    """Extract stock performance metrics and drop events.

    Populates StockPerformance (SECT4-01/02) and StockDropAnalysis
    (SECT4-03) from acquired market data.

    Args:
        state: AnalysisState with acquired_data.market_data populated.

    Returns:
        Tuple of (StockPerformance, StockDropAnalysis, ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "yfinance market data (history_1y, history_2y, history_5y, info)"

    market_data = get_market_data(state)
    filings = get_filings(state)

    raw_1y = market_data.get("history_1y", {})
    history_1y = cast(dict[str, Any], raw_1y) if isinstance(raw_1y, dict) else {}
    raw_2y = market_data.get("history_2y", {})
    history_2y = cast(dict[str, Any], raw_2y) if isinstance(raw_2y, dict) else {}
    raw_5y = market_data.get("history_5y", {})
    history_5y = cast(dict[str, Any], raw_5y) if isinstance(raw_5y, dict) else {}
    raw_info = market_data.get("info", {})
    info = cast(dict[str, Any], raw_info) if isinstance(raw_info, dict) else {}

    # Handle empty data gracefully.
    if not history_1y and not info:
        warnings.append("No market data available (history_1y and info empty)")
        perf = StockPerformance()
        drops = StockDropAnalysis()
        report = create_report(
            extractor_name="stock_performance",
            expected=EXPECTED_FIELDS,
            found=found,
            source_filing=source_filing,
            warnings=warnings,
        )
        log_report(report)
        return perf, drops, report

    # 1. Compute performance metrics (with decomposition + MDD ratio).
    perf = _compute_performance_metrics(history_1y, history_5y, info, market_data)

    if perf.current_price is not None:
        found.append("current_price")
    if perf.returns_1y is not None:
        found.append("returns_1y")
    if perf.beta is not None:
        found.append("beta")
    if perf.volatility_90d is not None:
        found.append("volatility_90d")
    if perf.max_drawdown_1y is not None:
        found.append("max_drawdown_1y")
    if perf.returns_1y_market is not None:
        found.append("returns_decomposition_1y")
    if perf.mdd_ratio_1y is not None:
        found.append("mdd_ratio")

    # 1a. Sector beta, beta ratio, idiosyncratic vol, sector vol.
    _compute_sector_derived_metrics(perf, market_data, history_1y)

    # 1c. EWMA volatility and regime classification (Phase 89).
    _compute_ewma_and_regime(perf, history_2y if history_2y else history_1y)

    # 1b. Volume spike detection.
    # Check for pre-correlated spikes from ACQUIRE (includes catalyst data).
    pre_correlated = market_data.get("volume_spike_events")
    if pre_correlated and isinstance(pre_correlated, list):
        perf.volume_spike_count = len(pre_correlated)
        perf.volume_spike_events = pre_correlated
    elif history_1y:
        from do_uw.stages.extract.volume_spikes import detect_volume_spikes

        spike_events = detect_volume_spikes(history_1y)
        perf.volume_spike_count = len(spike_events)
        perf.volume_spike_events = spike_events

    # 2. Find stock drops (prefer 2Y lookback, fall back to 1Y).
    drop_history = history_2y if history_2y else history_1y
    single_drops = find_single_day_drops(drop_history)
    multi_drops = find_multi_day_drops(drop_history)

    # 3. Compare against sector ETF if available.
    # Prefer 2Y sector history for drop comparison; fall back to 1Y/legacy.
    raw_sector = market_data.get("sector_history_2y")
    if not raw_sector:
        raw_sector = market_data.get(
            "sector_history_1y", market_data.get("sector_history", {})
        )
    sector_history = cast(dict[str, Any], raw_sector) if isinstance(raw_sector, dict) else {}
    if sector_history:
        single_drops = [
            compute_sector_comparison(d, sector_history)
            for d in single_drops
        ]
        multi_drops = [
            compute_sector_comparison(d, sector_history)
            for d in multi_drops
        ]

    # 4. Attribute triggers (8-K, earnings).
    all_drops = single_drops + multi_drops
    all_drops = attribute_triggers(all_drops, filings, market_data)
    single_drops = [
        d for d in all_drops if d.drop_type == DropType.SINGLE_DAY
    ]
    multi_drops = [
        d for d in all_drops if d.drop_type == DropType.MULTI_DAY
    ]

    # 5. Compute recovery time for each drop.
    prices_1y = get_close_prices(history_1y)
    dates_1y = get_dates(history_1y)
    for drop in single_drops + multi_drops:
        if not drop.date:
            continue
        drop_date = drop.date.value[:10]
        drop_idx = _find_price_index(dates_1y, drop_date)
        if drop_idx is not None:
            drop.recovery_days = compute_recovery_days(
                prices_1y, drop_idx, drop.period_days
            )

    # 6. Group consecutive single-day drops into multi-day events.
    # Preserve original single-day drops for worst_single_day identification.
    original_single_drops = list(single_drops)
    grouped_singles = group_consecutive_drops(
        single_drops, prices_1y, dates_1y
    )
    # Any grouped events that became MULTI_DAY get added to multi_drops.
    new_multis_from_group = [
        d for d in grouped_singles if d.drop_type == DropType.MULTI_DAY
    ]
    if new_multis_from_group:
        multi_drops = multi_drops + new_multis_from_group
        # Remove the constituent single-day drops that were merged.
        # Keep only singles that weren't part of any group.
        remaining_singles = [
            d for d in grouped_singles if d.drop_type == DropType.SINGLE_DAY
        ]
        single_drops = remaining_singles

    # 7. Tag market-wide events using SPY history (prefer 2Y).
    raw_spy = market_data.get("spy_history_2y") or market_data.get("spy_history_1y", {})
    spy_history = cast(dict[str, Any], raw_spy) if isinstance(raw_spy, dict) else {}
    if spy_history:
        single_drops = tag_market_wide_events(single_drops, spy_history)
        multi_drops = tag_market_wide_events(multi_drops, spy_history)

    # 8. Enrich drops with 8-K content and web search context.
    all_enrichable = single_drops + multi_drops
    all_enrichable = enrich_all_drops(all_enrichable, state)
    single_drops = [
        d for d in all_enrichable if d.drop_type == DropType.SINGLE_DAY
    ]
    multi_drops = [
        d for d in all_enrichable if d.drop_type == DropType.MULTI_DAY
    ]

    # 8a. Phase 90: Decompose drops into market/sector/company components.
    drop_prices = get_close_prices(drop_history)
    drop_dates = get_dates(drop_history)
    raw_spy_2y = market_data.get("spy_history_2y") or market_data.get("spy_history_1y", {})
    spy_hist_for_decomp = cast(dict[str, Any], raw_spy_2y) if isinstance(raw_spy_2y, dict) else {}
    spy_prices_for_decomp = get_close_prices(spy_hist_for_decomp) if spy_hist_for_decomp else []
    raw_sector_2y = market_data.get("sector_history_2y") or market_data.get(
        "sector_history_1y", market_data.get("sector_history", {})
    )
    sector_hist_for_decomp = cast(dict[str, Any], raw_sector_2y) if isinstance(raw_sector_2y, dict) else {}
    sector_prices_for_decomp = get_close_prices(sector_hist_for_decomp) if sector_hist_for_decomp else []

    if drop_prices and spy_prices_for_decomp and sector_prices_for_decomp:
        from do_uw.stages.extract.stock_drop_decomposition import decompose_drops
        all_for_decomp = single_drops + multi_drops
        all_for_decomp = decompose_drops(
            all_for_decomp, drop_prices, spy_prices_for_decomp, sector_prices_for_decomp, drop_dates,
        )
        single_drops = [d for d in all_for_decomp if d.drop_type == DropType.SINGLE_DAY]
        multi_drops = [d for d in all_for_decomp if d.drop_type == DropType.MULTI_DAY]

    # 8b. Phase 90: Apply time-decay weights.
    from do_uw.stages.extract.stock_drop_decay import apply_decay_weights
    all_for_decay = single_drops + multi_drops
    all_for_decay = apply_decay_weights(all_for_decay)
    single_drops = [d for d in all_for_decay if d.drop_type == DropType.SINGLE_DAY]
    multi_drops = [d for d in all_for_decay if d.drop_type == DropType.MULTI_DAY]

    # 8c. Phase 90: Corrective disclosure reverse lookup.
    from do_uw.stages.extract.stock_drop_enrichment import enrich_drops_with_reverse_lookup
    docs_8k = _get_8k_docs_for_reverse_lookup(state)
    web_results_for_reverse = _get_web_results_for_reverse_lookup(state)
    company_name = state.company.identity.legal_name.value if state.company and state.company.identity.legal_name else ""
    all_for_reverse = single_drops + multi_drops
    all_for_reverse = enrich_drops_with_reverse_lookup(
        all_for_reverse, docs_8k, web_results_for_reverse, company_name,
    )
    single_drops = [d for d in all_for_reverse if d.drop_type == DropType.SINGLE_DAY]
    multi_drops = [d for d in all_for_reverse if d.drop_type == DropType.MULTI_DAY]

    if single_drops:
        found.append("single_day_drops")
    if multi_drops:
        found.append("multi_day_drops")

    # 9. Build drop analysis.
    drops = StockDropAnalysis(
        single_day_drops=single_drops,
        multi_day_drops=multi_drops,
    )

    # Use original_single_drops for worst identification (before grouping).
    all_singles_for_worst = original_single_drops if original_single_drops else single_drops
    if all_singles_for_worst:
        drops.worst_single_day = min(
            all_singles_for_worst,
            key=lambda d: d.drop_pct.value if d.drop_pct else 0.0,
        )
    if multi_drops:
        drops.worst_multi_day = min(
            multi_drops,
            key=lambda d: d.drop_pct.value if d.drop_pct else 0.0,
        )

    # 10. Compute abnormal returns for each drop event (Phase 89).
    _compute_abnormal_returns_for_drops(
        drops, drop_history, market_data,
    )

    # 11. Compute DDL/MDL exposure from worst drop + market cap (Phase 89).
    _compute_ddl_for_drops(drops, perf)

    # Log summary.
    total_drops = len(single_drops) + len(multi_drops)
    if total_drops > 0:
        logger.info(
            "Stock performance: %d drops (%d single, %d multi)",
            total_drops, len(single_drops), len(multi_drops),
        )
        if drops.worst_single_day and drops.worst_single_day.drop_pct:
            logger.warning(
                "Worst single-day drop: %.1f%%",
                drops.worst_single_day.drop_pct.value,
            )

    # Populate single_day_events on perf for worksheet.
    for sd in single_drops:
        date_val = sd.date.value if sd.date else ""
        drop_val = sd.drop_pct.value if sd.drop_pct else 0.0
        trigger_val = sd.trigger_event.value if sd.trigger_event else ""
        event_dict: dict[str, float | str] = {
            "date": date_val,
            "change_pct": drop_val,
            "trigger": trigger_val,
        }
        perf.single_day_events.append(
            SourcedValue[dict[str, float | str]](
                value=event_dict,
                source=SOURCE_LABEL,
                confidence=Confidence.MEDIUM,
                as_of=now(),
            )
        )

    report = create_report(
        extractor_name="stock_performance",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return perf, drops, report
