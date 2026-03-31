"""Shared helpers for forensic analysis modules.

Extracted from financial_models.py to avoid duplication across forensic
modules. All forensic modules import from here instead of reaching into
financial_models private functions.

Functions:
- find_line_item: Find a line item by XBRL concept
- get_latest_value: Most recent period value
- get_prior_value: Second-most-recent period value
- extract_input: Safely extract a financial value by concept
- collect_all_period_values: Get all period values for a concept
- composite_confidence: Min confidence across multiple concepts
"""

from __future__ import annotations

import logging

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    FinancialLineItem,
    FinancialStatements,
)

logger = logging.getLogger(__name__)

# Confidence priority for min() computation.
_CONFIDENCE_PRIORITY: dict[Confidence, int] = {
    Confidence.LOW: 0,
    Confidence.MEDIUM: 1,
    Confidence.HIGH: 2,
}


def find_line_item(
    items: list[FinancialLineItem],
    concept: str,
) -> FinancialLineItem | None:
    """Find a line item by XBRL concept name."""
    for item in items:
        if item.xbrl_concept == concept:
            return item
    return None


def get_latest_value(item: FinancialLineItem) -> float | None:
    """Get the most recent period value from a line item."""
    if not item.values:
        return None
    sorted_keys = sorted(item.values.keys())
    for key in reversed(sorted_keys):
        sv = item.values.get(key)
        if sv is not None:
            return sv.value
    return None


def get_prior_value(item: FinancialLineItem) -> float | None:
    """Get the second-most-recent period value from a line item."""
    if not item.values or len(item.values) < 2:
        return None
    sorted_keys = sorted(item.values.keys())
    if len(sorted_keys) < 2:
        return None
    sv = item.values.get(sorted_keys[-2])
    if sv is not None:
        return sv.value
    return None


def extract_input(
    statements: FinancialStatements,
    concept: str,
    period: str = "latest",
) -> float | None:
    """Safely extract a financial value by concept name.

    Searches across income statement, balance sheet, and cash flow.

    Args:
        statements: The financial statements to search.
        concept: XBRL concept name (e.g., "revenue", "total_assets").
        period: "latest" or "prior".

    Returns:
        Float value if found, None otherwise.
    """
    for stmt in [
        statements.income_statement,
        statements.balance_sheet,
        statements.cash_flow,
    ]:
        if stmt is None:
            continue
        item = find_line_item(stmt.line_items, concept)
        if item is None:
            continue
        if period == "prior":
            val = get_prior_value(item)
        else:
            val = get_latest_value(item)
        if val is not None:
            return val
    return None


def collect_all_period_values(
    statements: FinancialStatements,
    concept: str,
) -> list[tuple[str, float]]:
    """Get all period values for a concept, sorted by period.

    Returns:
        List of (period_label, value) tuples, oldest first.
    """
    for stmt in [
        statements.income_statement,
        statements.balance_sheet,
        statements.cash_flow,
    ]:
        if stmt is None:
            continue
        item = find_line_item(stmt.line_items, concept)
        if item is None:
            continue
        result: list[tuple[str, float]] = []
        for key in sorted(item.values.keys()):
            sv = item.values.get(key)
            if sv is not None:
                result.append((key, sv.value))
        if result:
            return result
    return []


def composite_confidence(
    statements: FinancialStatements,
    concepts: list[str],
) -> Confidence:
    """Compute composite confidence as min of all input confidences.

    Per FRNSC-06: composite confidence cannot exceed weakest input.
    Only considers concepts actually found in the statements.

    Args:
        statements: Financial statements to search.
        concepts: List of XBRL concept names used as inputs.

    Returns:
        Minimum confidence across all found concepts, or LOW if none found.
    """
    confidences: list[Confidence] = []
    for concept in concepts:
        for stmt in [
            statements.income_statement,
            statements.balance_sheet,
            statements.cash_flow,
        ]:
            if stmt is None:
                continue
            for item in stmt.line_items:
                if item.xbrl_concept == concept:
                    for sv in item.values.values():
                        if sv is not None:
                            confidences.append(sv.confidence)
    if not confidences:
        return Confidence.LOW
    return min(confidences, key=lambda c: _CONFIDENCE_PRIORITY[c])
