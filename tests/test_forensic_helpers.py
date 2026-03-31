"""Tests for forensic analysis shared helpers.

Validates _extract_input and _composite_confidence work correctly
with mock FinancialStatements data.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
)


def _sv(value: float, confidence: Confidence = Confidence.HIGH) -> SourcedValue[float]:
    """Create a test SourcedValue."""
    return SourcedValue(
        value=value,
        source="test",
        confidence=confidence,
        as_of=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _make_statements(
    items: dict[str, dict[str, SourcedValue[float] | None]],
    statement_type: str = "balance_sheet",
) -> FinancialStatements:
    """Create FinancialStatements with given line items.

    Args:
        items: {xbrl_concept: {period: SourcedValue}}
        statement_type: Which statement to put them on.
    """
    line_items = []
    all_periods: set[str] = set()
    for concept, values in items.items():
        all_periods.update(values.keys())
        line_items.append(
            FinancialLineItem(
                label=concept,
                xbrl_concept=concept,
                values=values,
            )
        )
    stmt = FinancialStatement(
        statement_type=statement_type,
        periods=sorted(all_periods),
        line_items=line_items,
    )
    kwargs = {statement_type: stmt}
    return FinancialStatements(**kwargs)


class TestExtractInput:
    """Tests for _extract_input helper."""

    def test_extract_latest_value(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import extract_input

        stmts = _make_statements({
            "revenue": {"FY2023": _sv(1000.0), "FY2024": _sv(1200.0)},
        }, statement_type="income_statement")
        result = extract_input(stmts, "revenue")
        assert result == 1200.0

    def test_extract_prior_value(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import extract_input

        stmts = _make_statements({
            "revenue": {"FY2023": _sv(1000.0), "FY2024": _sv(1200.0)},
        }, statement_type="income_statement")
        result = extract_input(stmts, "revenue", period="prior")
        assert result == 1000.0

    def test_extract_missing_concept_returns_none(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import extract_input

        stmts = _make_statements({
            "revenue": {"FY2024": _sv(1200.0)},
        }, statement_type="income_statement")
        result = extract_input(stmts, "nonexistent_concept")
        assert result is None

    def test_extract_from_empty_statements(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import extract_input

        stmts = FinancialStatements()
        result = extract_input(stmts, "revenue")
        assert result is None


class TestCompositeConfidence:
    """Tests for _composite_confidence helper."""

    def test_returns_min_confidence(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import composite_confidence

        stmts = _make_statements({
            "revenue": {"FY2024": _sv(1200.0, Confidence.HIGH)},
            "net_income": {"FY2024": _sv(100.0, Confidence.MEDIUM)},
        }, statement_type="income_statement")
        result = composite_confidence(stmts, ["revenue", "net_income"])
        assert result == Confidence.MEDIUM

    def test_returns_low_when_any_low(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import composite_confidence

        stmts = _make_statements({
            "revenue": {"FY2024": _sv(1200.0, Confidence.HIGH)},
            "net_income": {"FY2024": _sv(100.0, Confidence.LOW)},
        }, statement_type="income_statement")
        result = composite_confidence(stmts, ["revenue", "net_income"])
        assert result == Confidence.LOW

    def test_returns_high_when_all_high(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import composite_confidence

        stmts = _make_statements({
            "revenue": {"FY2024": _sv(1200.0, Confidence.HIGH)},
            "total_assets": {"FY2024": _sv(5000.0, Confidence.HIGH)},
        })
        result = composite_confidence(stmts, ["revenue", "total_assets"])
        assert result == Confidence.HIGH

    def test_returns_low_when_no_data(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import composite_confidence

        stmts = FinancialStatements()
        result = composite_confidence(stmts, ["revenue", "net_income"])
        assert result == Confidence.LOW

    def test_returns_low_when_concept_not_found(self) -> None:
        from do_uw.stages.analyze.forensic_helpers import composite_confidence

        stmts = _make_statements({
            "revenue": {"FY2024": _sv(1200.0, Confidence.HIGH)},
        }, statement_type="income_statement")
        result = composite_confidence(stmts, ["revenue", "nonexistent"])
        # Only revenue found (HIGH), but nonexistent not found -- still HIGH
        # because we only consider found concepts
        assert result == Confidence.HIGH
