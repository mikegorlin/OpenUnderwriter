"""Extract 8-quarter trending data from yfinance market data.

Reads quarterly_income_stmt, quarterly_balance_sheet, and quarterly_cashflow
from state.acquired_data.market_data and produces a list of per-quarter dicts
with key financial metrics. yfinance data is already in raw USD — no unit
normalization needed (unlike LLM-extracted 10-Q data).

Stored in state.extracted.financials.yfinance_quarterly for the context
builder and 8-quarter trending table template.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Metric definitions: (key_in_output, yfinance_line_item_name, statement)
_INCOME_METRICS: list[tuple[str, str]] = [
    ("revenue", "Total Revenue"),
    ("gross_profit", "Gross Profit"),
    ("operating_income", "Operating Income"),
    ("net_income", "Diluted NI Availto Com Stockholders"),
    ("ebitda", "EBITDA"),
    ("diluted_eps", "Diluted EPS"),
]

_BALANCE_METRICS: list[tuple[str, str]] = [
    ("total_assets", "Total Assets"),
    ("total_debt", "Total Debt"),
    ("stockholders_equity", "Stockholders Equity"),
]

_CASHFLOW_METRICS: list[tuple[str, str]] = [
    ("operating_cashflow", "Operating Cash Flow"),
    ("capex", "Capital Expenditure"),
    ("free_cashflow", "Free Cash Flow"),
]


def extract_yfinance_quarterly(
    state: AnalysisState,
) -> list[dict[str, Any]]:
    """Extract up to 8 quarters of financial data from yfinance.

    Returns a list of dicts, one per quarter, ordered most recent first.
    Each dict has 'period' (date string) plus metric keys.
    """
    if state.acquired_data is None:
        return []

    md = state.acquired_data.market_data
    if not md:
        return []

    income = md.get("quarterly_income_stmt", {})
    balance = md.get("quarterly_balance_sheet", {})
    cashflow = md.get("quarterly_cashflow", {})

    # Determine periods from income statement (authoritative)
    periods: list[str] = income.get("periods", [])
    if not periods:
        logger.debug("No quarterly income statement periods in market_data")
        return []

    # Limit to 8 quarters
    periods = periods[:8]
    income_items = income.get("line_items", {})
    balance_items = balance.get("line_items", {})
    balance_periods = balance.get("periods", [])
    cashflow_items = cashflow.get("line_items", {})
    cashflow_periods = cashflow.get("periods", [])

    quarters: list[dict[str, Any]] = []
    for i, period in enumerate(periods):
        q: dict[str, Any] = {"period": period}

        # Income statement metrics
        for key, yf_name in _INCOME_METRICS:
            vals = income_items.get(yf_name, [])
            q[key] = vals[i] if i < len(vals) else None

        # Compute margins if we have revenue
        rev = q.get("revenue")
        gp = q.get("gross_profit")
        oi = q.get("operating_income")
        if rev and rev > 0:
            if gp is not None:
                q["gross_margin"] = gp / rev * 100
            if oi is not None:
                q["operating_margin"] = oi / rev * 100

        # Balance sheet metrics (match by period)
        bi = _period_index(balance_periods, period)
        for key, yf_name in _BALANCE_METRICS:
            vals = balance_items.get(yf_name, [])
            q[key] = vals[bi] if bi is not None and bi < len(vals) else None

        # Cash flow metrics (match by period)
        ci = _period_index(cashflow_periods, period)
        for key, yf_name in _CASHFLOW_METRICS:
            vals = cashflow_items.get(yf_name, [])
            q[key] = vals[ci] if ci is not None and ci < len(vals) else None

        quarters.append(q)

    logger.info(
        "yfinance quarterly: %d quarters extracted (%s to %s)",
        len(quarters),
        quarters[-1]["period"] if quarters else "?",
        quarters[0]["period"] if quarters else "?",
    )

    return quarters


def _period_index(periods: list[str], target: str) -> int | None:
    """Find index of target period in a period list, or None."""
    try:
        return periods.index(target)
    except ValueError:
        return None
