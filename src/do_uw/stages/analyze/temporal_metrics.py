"""Metric extraction helpers for temporal change detection.

Extracts multi-period financial data from ExtractedData for use by
the TemporalAnalyzer. Each extractor pulls a specific financial metric
across available periods (FY Prior, FY Latest, potentially YTD).

All extractors return list[tuple[str, float]] -- period label and value --
or empty list when data is insufficient for temporal analysis (<2 points).

Split from temporal_engine.py for 500-line compliance.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from do_uw.models.financials import (
        FinancialLineItem,
        FinancialStatement,
        FinancialStatements,
    )
    from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)

# Direction map: which direction constitutes worsening for each metric.
# Used by TemporalAnalyzer to determine adverse vs. favorable moves.
METRIC_DIRECTIONS: dict[str, Literal["higher_is_worse", "lower_is_worse"]] = {
    "revenue_growth": "lower_is_worse",
    "gross_margin": "lower_is_worse",
    "operating_margin": "lower_is_worse",
    "dso_days": "higher_is_worse",
    "operating_cash_flow": "lower_is_worse",
    "net_income_cfo_divergence": "higher_is_worse",
    "working_capital": "lower_is_worse",
    "debt_ratio": "higher_is_worse",
}


def extract_temporal_metrics(
    extracted: ExtractedData,
) -> dict[str, list[tuple[str, float]]]:
    """Extract all available temporal metrics from ExtractedData.

    Returns dict mapping metric name to list of (period_label, value) tuples.
    Metrics with fewer than 2 data points are excluded.

    Args:
        extracted: Structured data from the EXTRACT stage.

    Returns:
        Dict of metric_name -> [(period, value), ...] ordered oldest to newest.
    """
    if extracted.financials is None:
        logger.info("No financial data available for temporal analysis")
        return {}

    statements = extracted.financials.statements

    extractors: dict[
        str, Any
    ] = {
        "revenue_growth": _extract_revenue_trend,
        "gross_margin": _extract_gross_margin_trend,
        "operating_margin": _extract_operating_margin_trend,
        "dso_days": _extract_dso_trend,
        "operating_cash_flow": _extract_operating_cash_flow_trend,
        "net_income_cfo_divergence": _extract_net_income_cfo_divergence,
        "working_capital": _extract_working_capital_trend,
        "debt_ratio": _extract_debt_ratio_trend,
    }

    results: dict[str, list[tuple[str, float]]] = {}

    for name, extractor in extractors.items():
        try:
            data_points = extractor(statements)
            if len(data_points) >= 2:
                results[name] = data_points
        except Exception:
            logger.debug("Extractor %s failed", name, exc_info=True)

    logger.info(
        "Extracted temporal data for %d/%d metrics",
        len(results),
        len(extractors),
    )
    return results


# ---------------------------------------------------------------------------
# Individual metric extractors
# ---------------------------------------------------------------------------


def _find_line_item(
    statement: FinancialStatement | None,
    labels: list[str],
) -> FinancialLineItem | None:
    """Find a line item by matching against a list of possible labels.

    Case-insensitive substring matching against the line item label.

    Args:
        statement: The financial statement to search.
        labels: List of label substrings to match (tried in order).

    Returns:
        First matching FinancialLineItem, or None.
    """
    if statement is None:
        return None

    for target_label in labels:
        target_lower = target_label.lower()
        for item in statement.line_items:
            if target_lower in item.label.lower():
                return item
    return None


def _extract_values_across_periods(
    item: FinancialLineItem | None,
    periods: list[str],
) -> list[tuple[str, float]]:
    """Extract numeric values for a line item across given periods.

    Unwraps SourcedValue wrappers safely. Returns list of
    (period, value) tuples for periods where data exists.

    Args:
        item: The line item to extract from.
        periods: Ordered period labels to check.

    Returns:
        List of (period, value) tuples, oldest to newest.
    """
    if item is None:
        return []

    result: list[tuple[str, float]] = []
    for period in periods:
        sv = item.values.get(period)
        if sv is not None:
            try:
                result.append((period, float(sv.value)))
            except (TypeError, ValueError):
                continue
    return result


def _get_periods(statement: FinancialStatement | None) -> list[str]:
    """Get available periods from a statement, reversed to oldest-first.

    Financial statements typically list newest first (e.g., ['FY2024', 'FY2023']).
    We reverse to get oldest-first for temporal analysis.
    """
    if statement is None:
        return []
    # Reverse so oldest is first
    return list(reversed(statement.periods))


def _extract_revenue_trend(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract revenue across available periods from income statement.

    Looks for line items labeled "Revenue", "Total Revenue",
    "Net Revenue", "Sales".
    """
    income = statements.income_statement
    periods = _get_periods(income)
    item = _find_line_item(income, ["total revenue", "net revenue", "revenue", "sales"])
    return _extract_values_across_periods(item, periods)


def _extract_gross_margin_trend(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract gross margin percentage across periods.

    Computes gross margin as (gross_profit / revenue) * 100.
    Falls back to (revenue - cost_of_revenue) / revenue * 100.
    """
    income = statements.income_statement
    periods = _get_periods(income)

    revenue_item = _find_line_item(
        income, ["total revenue", "net revenue", "revenue", "sales"]
    )
    gross_profit_item = _find_line_item(income, ["gross profit"])
    cost_item = _find_line_item(
        income, ["cost of revenue", "cost of goods", "cost of sales", "cogs"]
    )

    result: list[tuple[str, float]] = []
    for period in periods:
        revenue_sv = revenue_item.values.get(period) if revenue_item else None
        gp_sv = gross_profit_item.values.get(period) if gross_profit_item else None

        if revenue_sv is not None and gp_sv is not None:
            try:
                rev = float(revenue_sv.value)
                gp = float(gp_sv.value)
                if rev != 0:
                    result.append((period, (gp / rev) * 100.0))
                    continue
            except (TypeError, ValueError):
                pass

        # Fallback: revenue - cost
        if revenue_sv is not None and cost_item is not None:
            cost_sv = cost_item.values.get(period)
            if cost_sv is not None:
                try:
                    rev = float(revenue_sv.value)
                    cost = float(cost_sv.value)
                    if rev != 0:
                        result.append((period, ((rev - cost) / rev) * 100.0))
                except (TypeError, ValueError):
                    pass

    return result


def _extract_operating_margin_trend(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract operating margin percentage across periods.

    Computes as (operating_income / revenue) * 100.
    """
    income = statements.income_statement
    periods = _get_periods(income)

    revenue_item = _find_line_item(
        income, ["total revenue", "net revenue", "revenue", "sales"]
    )
    op_income_item = _find_line_item(
        income, ["operating income", "income from operations", "operating profit"]
    )

    result: list[tuple[str, float]] = []
    for period in periods:
        if revenue_item is None or op_income_item is None:
            continue
        rev_sv = revenue_item.values.get(period)
        op_sv = op_income_item.values.get(period)
        if rev_sv is not None and op_sv is not None:
            try:
                rev = float(rev_sv.value)
                op = float(op_sv.value)
                if rev != 0:
                    result.append((period, (op / rev) * 100.0))
            except (TypeError, ValueError):
                pass

    return result


def _extract_dso_trend(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract days sales outstanding across periods.

    DSO = (accounts_receivable / revenue) * 365
    Uses balance sheet for AR and income statement for revenue.
    """
    income = statements.income_statement
    balance = statements.balance_sheet
    income_periods = _get_periods(income)
    balance_periods = _get_periods(balance)

    revenue_item = _find_line_item(
        income, ["total revenue", "net revenue", "revenue", "sales"]
    )
    ar_item = _find_line_item(
        balance, ["accounts receivable", "trade receivables", "receivables"]
    )

    if revenue_item is None or ar_item is None:
        return []

    # Use periods available in both statements
    common_periods = [p for p in income_periods if p in balance_periods]

    result: list[tuple[str, float]] = []
    for period in common_periods:
        rev_sv = revenue_item.values.get(period)
        ar_sv = ar_item.values.get(period)
        if rev_sv is not None and ar_sv is not None:
            try:
                rev = float(rev_sv.value)
                ar = float(ar_sv.value)
                if rev != 0:
                    result.append((period, (ar / rev) * 365.0))
            except (TypeError, ValueError):
                pass

    return result


def _extract_operating_cash_flow_trend(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract operating cash flow across periods from cash flow statement."""
    cf = statements.cash_flow
    periods = _get_periods(cf)
    item = _find_line_item(
        cf,
        [
            "net cash from operating",
            "cash from operations",
            "operating cash flow",
            "net cash provided by operating",
        ],
    )
    return _extract_values_across_periods(item, periods)


def _extract_net_income_cfo_divergence(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract net income / operating cash flow ratio across periods.

    Higher ratio indicates divergence (higher_is_worse). A ratio > 1
    means net income exceeds cash flow, suggesting accrual-based
    earnings inflation.
    """
    income = statements.income_statement
    cf = statements.cash_flow
    income_periods = _get_periods(income)
    cf_periods = _get_periods(cf)

    ni_item = _find_line_item(income, ["net income", "net earnings", "net profit"])
    cfo_item = _find_line_item(
        cf,
        [
            "net cash from operating",
            "cash from operations",
            "operating cash flow",
            "net cash provided by operating",
        ],
    )

    if ni_item is None or cfo_item is None:
        return []

    common_periods = [p for p in income_periods if p in cf_periods]

    result: list[tuple[str, float]] = []
    for period in common_periods:
        ni_sv = ni_item.values.get(period)
        cfo_sv = cfo_item.values.get(period)
        if ni_sv is not None and cfo_sv is not None:
            try:
                ni = float(ni_sv.value)
                cfo = float(cfo_sv.value)
                if cfo != 0:
                    result.append((period, abs(ni / cfo)))
            except (TypeError, ValueError):
                pass

    return result


def _extract_working_capital_trend(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract working capital (current assets - current liabilities) across periods."""
    balance = statements.balance_sheet
    periods = _get_periods(balance)

    ca_item = _find_line_item(balance, ["total current assets", "current assets"])
    cl_item = _find_line_item(
        balance, ["total current liabilities", "current liabilities"]
    )

    if ca_item is None or cl_item is None:
        return []

    result: list[tuple[str, float]] = []
    for period in periods:
        ca_sv = ca_item.values.get(period)
        cl_sv = cl_item.values.get(period)
        if ca_sv is not None and cl_sv is not None:
            try:
                ca = float(ca_sv.value)
                cl = float(cl_sv.value)
                result.append((period, ca - cl))
            except (TypeError, ValueError):
                pass

    return result


def _extract_debt_ratio_trend(
    statements: FinancialStatements,
) -> list[tuple[str, float]]:
    """Extract total debt / total assets ratio across periods.

    Higher is worse -- indicates increasing leverage.
    """
    balance = statements.balance_sheet
    periods = _get_periods(balance)

    debt_item = _find_line_item(
        balance,
        ["total debt", "total liabilities", "long-term debt", "total borrowings"],
    )
    assets_item = _find_line_item(balance, ["total assets"])

    if debt_item is None or assets_item is None:
        return []

    result: list[tuple[str, float]] = []
    for period in periods:
        debt_sv = debt_item.values.get(period)
        assets_sv = assets_item.values.get(period)
        if debt_sv is not None and assets_sv is not None:
            try:
                debt = float(debt_sv.value)
                assets = float(assets_sv.value)
                if assets != 0:
                    result.append((period, debt / assets))
            except (TypeError, ValueError):
                pass

    return result


__all__ = [
    "METRIC_DIRECTIONS",
    "extract_temporal_metrics",
]
