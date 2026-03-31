"""Return correlation metrics context builder for market section.

Computes correlation vs SPY and sector ETF, R-squared, idiosyncratic
risk percentage, and provides D&O litigation interpretation.

Phase 133-02: STOCK-08 requirement.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.chart_computations import (
    compute_beta,
    compute_correlation,
    compute_daily_returns,
    compute_r_squared,
)
from do_uw.stages.render.formatters import safe_float


def build_correlation_metrics(state: AnalysisState) -> dict[str, Any]:
    """Build correlation metrics card context.

    Computes:
    - Correlation vs SPY (market)
    - Correlation vs sector ETF (if available)
    - R-squared (% of variance explained by market)
    - Idiosyncratic risk % (1 - R-squared)
    - Beta
    - D&O litigation interpretation

    Returns:
        Dict with "correlation_metrics" key containing template-ready data,
        or empty dict if insufficient price data.
    """
    # Extract price arrays for correlation computation.
    # NOTE: get_market_history accessor requires a "Date" key and returns the
    # full history dict.  Correlation only needs Close arrays (no Date needed),
    # so we read the raw market_data dict directly for all three series.
    company_prices: list[float] = []
    spy_prices: list[float] = []
    sector_prices: list[float] = []

    if state.acquired_data and state.acquired_data.market_data:
        md = state.acquired_data.market_data
        if isinstance(md, dict):
            hist_1y = md.get("history_1y", {})
            company_prices = hist_1y.get("Close", []) if isinstance(hist_1y, dict) else []

            spy_hist = md.get("spy_history_1y", md.get("spy_data", {}))
            if isinstance(spy_hist, dict):
                spy_prices = spy_hist.get("Close", [])

            sector_hist = md.get("sector_history_1y", md.get("sector_etf_history", {}))
            if isinstance(sector_hist, dict):
                sector_prices = sector_hist.get("Close", [])

    if len(company_prices) < 30:
        # Fall back to extracted beta if available
        if state.extracted and state.extracted.market:
            stock = state.extracted.market.stock
            beta_val = stock.beta.value if stock.beta else None
            if beta_val is not None:
                return {"correlation_metrics": {
                    "corr_spy": "N/A",
                    "corr_sector": "N/A",
                    "r_squared": "N/A",
                    "idiosyncratic_pct": "N/A",
                    "beta": f"{beta_val:.2f}",
                    "interpretation": (
                        "Insufficient price history for correlation analysis. "
                        f"Beta of {beta_val:.2f} provides limited insight into "
                        "market vs company-specific return attribution."
                    ),
                }}
        return {}

    # Compute correlations
    corr_spy = compute_correlation(company_prices, spy_prices) if len(spy_prices) >= 30 else None
    corr_sector = compute_correlation(company_prices, sector_prices) if len(sector_prices) >= 30 else None
    r_squared = compute_r_squared(company_prices, spy_prices) if len(spy_prices) >= 30 else None

    # Compute beta
    comp_returns = compute_daily_returns(company_prices)
    spy_returns = compute_daily_returns(spy_prices) if spy_prices else []
    beta = compute_beta(comp_returns, spy_returns) if spy_returns else None

    # Fall back to extracted beta
    if beta is None and state.extracted and state.extracted.market:
        stock = state.extracted.market.stock
        beta = safe_float(stock.beta.value if stock.beta else None, None)

    # Idiosyncratic risk
    idiosyncratic_pct = (1.0 - r_squared) * 100.0 if r_squared is not None else None

    # Build interpretation
    interpretation = _build_interpretation(idiosyncratic_pct, corr_spy, beta)

    return {"correlation_metrics": {
        "corr_spy": f"{corr_spy:.2f}" if corr_spy is not None else "N/A",
        "corr_sector": f"{corr_sector:.2f}" if corr_sector is not None else "N/A",
        "r_squared": f"{r_squared:.2f}" if r_squared is not None else "N/A",
        "idiosyncratic_pct": f"{idiosyncratic_pct:.0f}%" if idiosyncratic_pct is not None else "N/A",
        "beta": f"{beta:.2f}" if beta is not None else "N/A",
        "interpretation": interpretation,
    }}


def _build_interpretation(
    idiosyncratic_pct: float | None,
    corr_spy: float | None,
    beta: float | None,
) -> str:
    """Build D&O litigation interpretation of correlation metrics."""
    if idiosyncratic_pct is None:
        if beta is not None:
            return (
                f"Beta of {beta:.2f} but insufficient data for full correlation analysis. "
                "Loss causation assessment requires longer price history."
            )
        return "Insufficient data for correlation analysis."

    if idiosyncratic_pct > 70:
        return (
            "Company-specific factors dominate returns — harder for plaintiffs "
            "to attribute losses to market-wide factors but also harder to "
            "use Truth on the Market defense"
        )
    if idiosyncratic_pct > 40:
        return (
            "Mixed market/company-specific return drivers — loss causation "
            "arguments viable for both plaintiff and defense"
        )
    return (
        "Returns largely track market/sector — strong basis for loss "
        "causation defense under Dura Pharmaceuticals"
    )
