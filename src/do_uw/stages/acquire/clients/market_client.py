"""yfinance market data acquisition client.

Retrieves stock prices, company info, insider transactions, institutional
holders, analyst recommendations, and news from Yahoo Finance via yfinance.

Also acquires sector ETF and S&P 500 (SPY) benchmark history for
chart comparison and market-wide event tagging.

All yfinance calls are wrapped in try/except -- yfinance is unstable and
Yahoo Finance can change their internal API without notice. Partial data
is returned on failure; the gate system handles completeness checks.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from do_uw.cache.sqlite_cache import AnalysisCache
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Cache TTL: 5 business days in seconds (7 calendar days to be safe).
MARKET_DATA_TTL = 7 * 24 * 3600


# Map yfinance sector names to brain/sectors.json sector codes.
_YFINANCE_SECTOR_TO_CODE: dict[str, str] = {
    "Technology": "TECH",
    "Healthcare": "HLTH",
    "Financial Services": "FINS",
    "Industrials": "INDU",
    "Energy": "ENGY",
    "Consumer Cyclical": "CONS",
    "Consumer Defensive": "STPL",
    "Basic Materials": "MATL",
    "Utilities": "UTIL",
    "Real Estate": "REIT",
    "Communication Services": "COMM",
}


def _resolve_sector_etf(sector: str) -> str | None:
    """Resolve yfinance sector name to primary sector ETF ticker.

    Reads brain/config/sectors.json to look up the primary ETF for the
    sector. Returns None if sector is unknown or mapping not found.
    """
    code = _YFINANCE_SECTOR_TO_CODE.get(sector)
    if code is None:
        return None

    try:
        from do_uw.brain.brain_unified_loader import load_config

        sectors_data = load_config("sectors")
        etf_info = sectors_data.get("sector_etfs", {}).get(code, {})
        primary = etf_info.get("primary")
        if isinstance(primary, str) and primary:
            return primary
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        logger.warning("Failed to resolve sector ETF for %s: %s", sector, exc)

    return None


class MarketDataClient:
    """Yahoo Finance market data acquisition client.

    Collects: company info, price history (1y and 5y), insider
    transactions, institutional holders, analyst recommendations,
    recent news articles, sector ETF history, and S&P 500 benchmark
    history.
    """

    @property
    def name(self) -> str:
        """Client name for logging and identification."""
        return "market_data"

    def acquire(
        self,
        state: AnalysisState,
        cache: AnalysisCache | None = None,
    ) -> dict[str, Any]:
        """Acquire market data for the given ticker.

        Args:
            state: Analysis state with ticker symbol.
            cache: Optional cache for storing/retrieving results.

        Returns:
            Dict with keys: info, history_1y, history_2y, history_5y,
            insider_transactions, institutional_holders,
            recommendations, news, sector_etf, sector_history_1y,
            sector_history_2y, sector_history_5y, spy_history_1y,
            spy_history_2y, spy_history_5y.
            Missing keys indicate yfinance failures for that
            data category.
        """
        ticker = state.ticker
        today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
        cache_key = f"yfinance:{ticker}:market:{today}"

        # Check cache first.
        if cache is not None:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for market data: %s", cache_key)
                return dict(cached)

        logger.info("Acquiring market data for %s via yfinance", ticker)
        result = _collect_yfinance_data(ticker)

        # Cache on success (even partial data is worth caching).
        if cache is not None and result:
            cache.set(
                cache_key,
                result,
                source="yfinance",
                ttl=MARKET_DATA_TTL,
            )

        return result


def _collect_yfinance_data(ticker: str) -> dict[str, Any]:
    """Collect all available market data from yfinance.

    Each data category is fetched independently with its own
    try/except. Partial results are returned on individual failures.
    """
    import yfinance as yf  # type: ignore[import-untyped]
    import socket

    # Set global socket timeout to prevent indefinite hanging
    socket.setdefaulttimeout(30.0)  # 30 seconds

    result: dict[str, Any] = {}
    yf_ticker = yf.Ticker(ticker)

    # Company info dict (179 keys including governance scores, officers, ratios).
    result["info"] = _safe_get_info(yf_ticker)

    # Price history: 1 year daily.
    result["history_1y"] = _safe_get_history(yf_ticker, "1y")

    # Price history: 5 year daily.
    result["history_5y"] = _safe_get_history(yf_ticker, "5y")

    # Price history: 2 year daily (for drop detection lookback).
    result["history_2y"] = _safe_get_history(yf_ticker, "2y")

    # Insider transactions.
    result["insider_transactions"] = _safe_get_dataframe(yf_ticker, "insider_transactions")

    # Institutional holders.
    result["institutional_holders"] = _safe_get_dataframe(yf_ticker, "institutional_holders")

    # Analyst recommendations.
    result["recommendations"] = _safe_get_dataframe(yf_ticker, "recommendations")

    # News articles.
    result["news"] = _safe_get_news(yf_ticker)

    # Earnings dates (Phase 4: market analysis).
    result["earnings_dates"] = _safe_get_earnings_dates(yf_ticker)

    # Analyst price targets (Phase 4: market analysis).
    result["analyst_price_targets"] = _safe_get_analyst_targets(yf_ticker)

    # Upgrades and downgrades (Phase 4: market analysis).
    result["upgrades_downgrades"] = _safe_get_dataframe(yf_ticker, "upgrades_downgrades")

    # --- Financial statements (annual + quarterly) ---
    result["income_stmt"] = _safe_get_financial_stmt(yf_ticker, "income_stmt")
    result["quarterly_income_stmt"] = _safe_get_financial_stmt(yf_ticker, "quarterly_income_stmt")
    result["balance_sheet"] = _safe_get_financial_stmt(yf_ticker, "balance_sheet")
    result["quarterly_balance_sheet"] = _safe_get_financial_stmt(
        yf_ticker, "quarterly_balance_sheet"
    )
    result["cashflow"] = _safe_get_financial_stmt(yf_ticker, "cashflow")
    result["quarterly_cashflow"] = _safe_get_financial_stmt(yf_ticker, "quarterly_cashflow")

    # --- Ownership data ---
    result["major_holders"] = _safe_get_dataframe(yf_ticker, "major_holders")
    result["mutualfund_holders"] = _safe_get_dataframe(yf_ticker, "mutualfund_holders")

    # --- Corporate actions ---
    result["dividends"] = _safe_get_series(yf_ticker, "dividends")
    result["splits"] = _safe_get_series(yf_ticker, "splits")
    result["calendar"] = _safe_get_calendar(yf_ticker)

    # --- Earnings & analyst estimate data ---
    result["earnings_history"] = _safe_get_dataframe(yf_ticker, "earnings_history")
    result["eps_trend"] = _safe_get_dataframe(yf_ticker, "eps_trend")
    result["eps_revisions"] = _safe_get_dataframe(yf_ticker, "eps_revisions")
    result["growth_estimates"] = _safe_get_dataframe(yf_ticker, "growth_estimates")
    result["revenue_estimate"] = _safe_get_dataframe(yf_ticker, "revenue_estimate")
    result["earnings_estimate"] = _safe_get_dataframe(yf_ticker, "earnings_estimate")

    # --- Sector ETF comparison data ---
    info = result.get("info", {})
    sector = info.get("sector", "") if isinstance(info, dict) else ""
    sector_etf = _resolve_sector_etf(sector)
    if sector_etf:
        result["sector_etf"] = sector_etf
        etf_ticker = yf.Ticker(sector_etf)
        result["sector_history_1y"] = _safe_get_history(etf_ticker, "1y")
        result["sector_history_5y"] = _safe_get_history(etf_ticker, "5y")
        result["sector_history_2y"] = _safe_get_history(etf_ticker, "2y")
        logger.info("Acquired sector ETF data: %s (%s)", sector_etf, sector)
    else:
        logger.info("No sector ETF mapping for sector: %r", sector)

    # --- S&P 500 benchmark (always acquire) ---
    spy = yf.Ticker("SPY")
    result["spy_history_1y"] = _safe_get_history(spy, "1y")
    result["spy_history_5y"] = _safe_get_history(spy, "5y")
    result["spy_history_2y"] = _safe_get_history(spy, "2y")

    # --- Extract short interest data for MARKET_SHORT source detection ---
    result["short_interest"] = _extract_short_interest_from_info(result.get("info", {}))

    return result


def _safe_get_info(yf_ticker: Any) -> dict[str, Any]:
    """Safely retrieve ticker.info dict."""
    try:
        info: object = yf_ticker.info
        if isinstance(info, dict):
            return cast(dict[str, Any], info)
        return {}
    except Exception as exc:
        logger.warning("yfinance info failed: %s", exc)
        return {}


def _extract_short_interest_from_info(info: dict[str, Any]) -> dict[str, Any]:
    """Extract short interest metrics from yfinance info dict.

    Returns a dict with keys: short_pct_float, days_to_cover, shares_short,
    shares_short_prior, short_pct_shares_out, trend_6m (if computable).
    Used for MARKET_SHORT source detection in orchestrator.
    """
    if not info:
        return {}

    result: dict[str, Any] = {}

    # Short percent of float
    short_pct = info.get("shortPercentOfFloat")
    if short_pct is not None:
        try:
            result["short_pct_float"] = float(short_pct) * 100.0
        except (ValueError, TypeError):
            pass

    # Days to cover (shortRatio)
    short_ratio = info.get("shortRatio")
    if short_ratio is not None:
        try:
            result["days_to_cover"] = float(short_ratio)
        except (ValueError, TypeError):
            pass

    # Share counts
    shares_short = info.get("sharesShort")
    if shares_short is not None:
        try:
            result["shares_short"] = int(float(shares_short))
        except (ValueError, TypeError):
            pass

    shares_prior = info.get("sharesShortPriorMonth")
    if shares_prior is not None:
        try:
            result["shares_short_prior"] = int(float(shares_prior))
        except (ValueError, TypeError):
            pass

    # Percent of shares out
    short_pct_out = info.get("sharesPercentSharesOut")
    if short_pct_out is not None:
        try:
            result["short_pct_shares_out"] = float(short_pct_out) * 100.0
        except (ValueError, TypeError):
            pass

    # Trend computation if we have both current and prior
    if "shares_short" in result and "shares_short_prior" in result:
        current = result["shares_short"]
        prior = result["shares_short_prior"]
        if prior > 0:
            change_pct = ((current - prior) / prior) * 100.0
            if change_pct > 10.0:
                result["trend_6m"] = "RISING"
            elif change_pct < -10.0:
                result["trend_6m"] = "DECLINING"
            else:
                result["trend_6m"] = "STABLE"
        else:
            result["trend_6m"] = "STABLE"

    return result


def _safe_get_history(yf_ticker: Any, period: str) -> dict[str, Any]:
    """Safely retrieve price history and convert DataFrame to dict."""
    try:
        df = yf_ticker.history(period=period)
        if df is not None and not df.empty:
            return _dataframe_to_dict(df)
        return {}
    except Exception as exc:
        logger.warning("yfinance history(%s) failed: %s", period, exc)
        return {}


def _safe_get_dataframe(yf_ticker: Any, attr_name: str) -> dict[str, Any]:
    """Safely retrieve a DataFrame attribute and convert to dict."""
    try:
        df = getattr(yf_ticker, attr_name, None)
        if df is not None and hasattr(df, "empty") and not df.empty:
            return _dataframe_to_dict(df)
        return {}
    except Exception as exc:
        logger.warning("yfinance %s failed: %s", attr_name, exc)
        return {}


def _safe_get_news(yf_ticker: Any) -> list[dict[str, Any]]:
    """Safely retrieve news articles."""
    try:
        news: object = yf_ticker.news
        if isinstance(news, list):
            return cast(list[dict[str, Any]], news)
        return []
    except Exception as exc:
        logger.warning("yfinance news failed: %s", exc)
        return []


def _safe_get_earnings_dates(yf_ticker: Any) -> dict[str, Any]:
    """Safely retrieve earnings dates via get_earnings_dates().

    yfinance's get_earnings_dates() can raise KeyError or return
    unexpected data depending on version. Wrap defensively.
    """
    try:
        df = yf_ticker.get_earnings_dates(limit=20)
        if df is not None and hasattr(df, "empty") and not df.empty:
            return _dataframe_to_dict(df)
        return {}
    except Exception as exc:
        logger.warning("yfinance get_earnings_dates failed: %s", exc)
        return {}


def _safe_get_analyst_targets(yf_ticker: Any) -> dict[str, Any]:
    """Safely retrieve analyst price targets.

    Tries yf_ticker.analyst_price_targets (DataFrame) first.
    Falls back to extracting from info dict keys if the attribute
    is unavailable or returns empty.
    """
    try:
        targets = getattr(yf_ticker, "analyst_price_targets", None)
        if targets is not None and hasattr(targets, "empty") and not targets.empty:
            return _dataframe_to_dict(targets)
    except Exception as exc:
        logger.warning("yfinance analyst_price_targets failed: %s", exc)

    # Fallback: extract from info dict.
    try:
        info: object = yf_ticker.info
        if isinstance(info, dict):
            info_dict = cast(dict[str, Any], info)
            fallback: dict[str, Any] = {}
            for key in (
                "targetMeanPrice",
                "targetMedianPrice",
                "targetHighPrice",
                "targetLowPrice",
                "currentPrice",
            ):
                val = info_dict.get(key)
                if val is not None:
                    fallback[key] = val
            if fallback:
                return fallback
    except Exception as exc:
        logger.warning("yfinance analyst target fallback failed: %s", exc)

    return {}


def _safe_get_financial_stmt(yf_ticker: Any, attr_name: str) -> dict[str, Any]:
    """Safely retrieve a financial statement DataFrame.

    Financial statements (income_stmt, balance_sheet, cashflow and their
    quarterly variants) have Timestamp columns and a string index.  We
    transpose so rows are line items and columns are period dates, then
    convert to a JSON-friendly dict.
    """
    try:
        df = getattr(yf_ticker, attr_name, None)
        if df is not None and hasattr(df, "empty") and not df.empty:
            return _financial_stmt_to_dict(df)
        return {}
    except Exception as exc:
        logger.warning("yfinance %s failed: %s", attr_name, exc)
        return {}


def _safe_get_series(yf_ticker: Any, attr_name: str) -> dict[str, Any]:
    """Safely retrieve a Series attribute (dividends, splits) as dict."""
    try:
        series = getattr(yf_ticker, attr_name, None)
        if series is not None and hasattr(series, "empty") and not series.empty:
            # Convert to {date_str: value} dict
            result: dict[str, Any] = {}
            for idx, val in series.items():
                result[str(idx)] = float(val) if val is not None else None
            return result
        return {}
    except Exception as exc:
        logger.warning("yfinance %s failed: %s", attr_name, exc)
        return {}


def _safe_get_calendar(yf_ticker: Any) -> dict[str, Any]:
    """Safely retrieve ticker.calendar dict."""
    try:
        cal = getattr(yf_ticker, "calendar", None)
        if isinstance(cal, dict):
            # Convert date objects to strings for JSON serialization
            result: dict[str, Any] = {}
            for k, v in cal.items():
                if hasattr(v, "isoformat"):
                    result[k] = v.isoformat()
                elif isinstance(v, list):
                    result[k] = [x.isoformat() if hasattr(x, "isoformat") else x for x in v]
                else:
                    result[k] = v
            return result
        return {}
    except Exception as exc:
        logger.warning("yfinance calendar failed: %s", exc)
        return {}


def _financial_stmt_to_dict(df: Any) -> dict[str, Any]:
    """Convert a financial statement DataFrame to JSON-serializable dict.

    yfinance financial statements have line-item names as index and
    Timestamp period-end dates as columns.  We produce:
      {"periods": ["2025-09-30", ...], "line_items": {"Revenue": [val, ...], ...}}
    """
    try:
        periods = [str(c.date()) if hasattr(c, "date") else str(c) for c in df.columns]
        line_items: dict[str, list[Any]] = {}
        for idx_label in df.index:
            row = df.loc[idx_label]
            vals: list[Any] = []
            for v in row:
                if v is None or (hasattr(v, "__class__") and v.__class__.__name__ == "NaTType"):
                    vals.append(None)
                else:
                    try:
                        vals.append(float(v))
                    except (ValueError, TypeError):
                        vals.append(None)
            line_items[str(idx_label)] = vals
        return {"periods": periods, "line_items": line_items}
    except Exception as exc:
        logger.warning("Financial statement conversion failed: %s", exc)
        return {}


def _dataframe_to_dict(df: Any) -> dict[str, Any]:
    """Convert a pandas DataFrame to a JSON-serializable dict.

    Handles datetime index and columns by converting to ISO strings.
    """
    try:
        # Reset index to make it a column, then convert.
        df_reset = df.reset_index()
        # Convert datetime columns to ISO strings.
        for col in df_reset.columns:
            if hasattr(df_reset[col], "dt"):
                df_reset[col] = df_reset[col].astype(str)
        records: dict[str, Any] = df_reset.to_dict(orient="list")
        return records
    except Exception as exc:
        logger.warning("DataFrame conversion failed: %s", exc)
        return {}
