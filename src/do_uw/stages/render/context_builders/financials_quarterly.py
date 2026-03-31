"""Quarterly trend context builder for 8-quarter XBRL data rendering.

Builds template-ready context from QuarterlyStatements (XBRL) with
fallback to yfinance quarterly data. Produces tabbed Income/Balance/
Cash Flow views with sparklines and YoY percentage changes.

Created Phase 73 Plan 01 — surfaces Phase 68 quarterly XBRL data.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.sparklines import render_sparkline
from do_uw.stages.render.formatters import format_currency_accounting as format_currency, format_percentage


# ---------------------------------------------------------------------------
# Metric definitions per tab
# ---------------------------------------------------------------------------

# (concept_key, display_label, format_type, higher_is_better)
_INCOME_METRICS: list[tuple[str, str, str, bool]] = [
    ("Revenues", "Revenue", "currency", True),
    ("CostOfGoodsAndServicesSold", "COGS", "currency", False),
    ("GrossProfit", "Gross Profit", "currency", True),
    ("OperatingIncomeLoss", "Operating Income", "currency", True),
    ("NetIncomeLoss", "Net Income", "currency", True),
    ("EarningsPerShareDiluted", "Diluted EPS", "eps", True),
]

_BALANCE_METRICS: list[tuple[str, str, str, bool]] = [
    ("Assets", "Total Assets", "currency", True),
    ("Liabilities", "Total Liabilities", "currency", False),
    ("StockholdersEquity", "Stockholders' Equity", "currency", True),
    ("CashAndCashEquivalentsAtCarryingValue", "Cash & Equivalents", "currency", True),
    ("LongTermDebt", "Total Debt", "currency", False),
    ("working_capital", "Working Capital", "currency", True),
]

_CASHFLOW_METRICS: list[tuple[str, str, str, bool]] = [
    ("NetCashProvidedByUsedInOperatingActivities", "Operating CF", "currency", True),
    ("PaymentsToAcquirePropertyPlantAndEquipment", "Capital Expenditures", "currency", False),
    ("free_cash_flow", "Free Cash Flow", "currency", True),
    ("NetCashProvidedByUsedInInvestingActivities", "Investing CF", "currency", True),
    ("NetCashProvidedByUsedInFinancingActivities", "Financing CF", "currency", True),
]

# Summary strip: cross-statement key metrics
_SUMMARY_METRICS: list[tuple[str, str, str, str, bool]] = [
    ("Revenues", "Revenue", "income", "currency", True),
    ("NetIncomeLoss", "Net Income", "income", "currency", True),
    ("free_cash_flow", "Free Cash Flow", "cash_flow", "currency", True),
    ("Assets", "Total Assets", "balance", "currency", True),
]


def _fmt_value(value: float | None, fmt: str) -> str:
    """Format a single value based on format type."""
    if value is None:
        return "N/A"
    if fmt == "currency":
        return format_currency(value, compact=True)
    if fmt == "eps":
        return f"${value:.2f}"
    if fmt == "pct":
        return format_percentage(value)
    return f"{value:,.0f}"


def _get_quarter_value(
    quarter: Any,
    concept: str,
    statement_type: str,
) -> float | None:
    """Extract a concept value from a QuarterlyPeriod."""
    stmt_map = {"income": "income", "balance": "balance", "cash_flow": "cash_flow"}
    attr = stmt_map.get(statement_type, statement_type)
    data = getattr(quarter, attr, {})
    sv = data.get(concept)
    if sv is not None:
        return sv.value if hasattr(sv, "value") else sv
    # Derived concepts
    if concept == "free_cash_flow":
        ocf_sv = data.get("NetCashProvidedByUsedInOperatingActivities")
        capex_sv = data.get("PaymentsToAcquirePropertyPlantAndEquipment")
        ocf = (ocf_sv.value if hasattr(ocf_sv, "value") else ocf_sv) if ocf_sv else None
        capex = (capex_sv.value if hasattr(capex_sv, "value") else capex_sv) if capex_sv else None
        if ocf is not None and capex is not None:
            return ocf - abs(capex)
        return ocf  # FCF = OCF if no capex data
    if concept == "working_capital":
        bal = getattr(quarter, "balance", {})
        assets_sv = bal.get("AssetsCurrent")
        liab_sv = bal.get("LiabilitiesCurrent")
        a = (assets_sv.value if hasattr(assets_sv, "value") else assets_sv) if assets_sv else None
        li = (liab_sv.value if hasattr(liab_sv, "value") else liab_sv) if liab_sv else None
        if a is not None and li is not None:
            return a - li
    return None


def _compute_yoy(values: list[float | None]) -> tuple[float | None, str]:
    """Compute YoY % change from first vs 5th element (4 quarters apart).

    Returns (pct_change, direction).
    """
    if len(values) < 5:
        # Fall back to first vs last
        recent = values[0] if values else None
        prior = values[-1] if len(values) > 1 else None
    else:
        recent = values[0]
        prior = values[4]

    if recent is None or prior is None or prior == 0:
        return None, "flat"
    pct = (recent - prior) / abs(prior) * 100
    direction = "up" if pct > 1 else ("down" if pct < -1 else "flat")
    return round(pct, 1), direction


def _build_metric_rows(
    quarters: list[Any],
    metric_defs: list[tuple[str, str, str, bool]],
    statement_type: str,
) -> list[dict[str, Any]]:
    """Build metric row dicts for a statement tab."""
    rows: list[dict[str, Any]] = []
    for concept, label, fmt, higher_better in metric_defs:
        raw_vals: list[float | None] = []
        cells: list[str] = []
        has_any = False

        for q in quarters:
            val = _get_quarter_value(q, concept, statement_type)
            raw_vals.append(val)
            cells.append(_fmt_value(val, fmt))
            if val is not None:
                has_any = True

        if not has_any:
            continue

        # Sparkline from numeric values (chronological order = reversed)
        numeric = [v for v in raw_vals if v is not None]
        spark = render_sparkline(list(reversed(numeric))) if len(numeric) >= 2 else ""

        yoy_pct, yoy_dir = _compute_yoy(raw_vals)
        # Direction-aware coloring: for "lower is better" metrics, flip color
        if not higher_better and yoy_dir != "flat":
            yoy_dir = "down" if yoy_dir == "up" else "up"

        rows.append({
            "label": label,
            "cells": cells,
            "sparkline": spark,
            "yoy_pct": yoy_pct,
            "yoy_direction": yoy_dir,
        })
    return rows


def build_quarterly_trend_context(state: AnalysisState) -> dict[str, Any]:
    """Build 8-quarter trend context from XBRL data with yfinance fallback.

    Returns dict with has_data, periods, summary_strip, and per-tab metrics.
    """
    empty: dict[str, Any] = {
        "has_data": False,
        "periods": [],
        "summary_strip": [],
        "income_metrics": [],
        "balance_metrics": [],
        "cashflow_metrics": [],
    }

    ext = state.extracted
    if ext is None or ext.financials is None:
        return empty

    fin = ext.financials
    qx = fin.quarterly_xbrl
    if qx is None or not qx.quarters:
        # Fallback: return empty — the existing yfinance_quarterly context
        # already handles the yfinance path in financials.py
        return empty

    quarters = qx.quarters  # Most recent first
    periods = [q.fiscal_label for q in quarters]

    # Summary strip
    summary: list[dict[str, Any]] = []
    for concept, label, stmt_type, fmt, higher_better in _SUMMARY_METRICS:
        val = _get_quarter_value(quarters[0], concept, stmt_type)
        raw_vals = [_get_quarter_value(q, concept, stmt_type) for q in quarters]
        yoy_pct, yoy_dir = _compute_yoy(raw_vals)
        if not higher_better and yoy_dir != "flat":
            yoy_dir = "down" if yoy_dir == "up" else "up"
        numeric = [v for v in raw_vals if v is not None]
        spark = render_sparkline(list(reversed(numeric))) if len(numeric) >= 2 else ""
        summary.append({
            "label": label,
            "value": _fmt_value(val, fmt),
            "sparkline": spark,
            "yoy_pct": yoy_pct,
            "yoy_direction": yoy_dir,
        })

    income = _build_metric_rows(quarters, _INCOME_METRICS, "income")
    balance = _build_metric_rows(quarters, _BALANCE_METRICS, "balance")
    cashflow = _build_metric_rows(quarters, _CASHFLOW_METRICS, "cash_flow")

    return {
        "has_data": bool(income or balance or cashflow),
        "periods": periods,
        "summary_strip": summary,
        "income_metrics": income,
        "balance_metrics": balance,
        "cashflow_metrics": cashflow,
    }


__all__ = ["build_quarterly_trend_context"]
