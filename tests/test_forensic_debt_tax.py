"""Tests for debt/tax forensic analysis module.

Validates compute_debt_tax_forensics produces correct metrics,
zones, trends, and handles missing data gracefully.
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
from do_uw.models.xbrl_forensics import DebtTaxForensics


def _sv(value: float, confidence: Confidence = Confidence.HIGH) -> SourcedValue[float]:
    """Create a test SourcedValue."""
    return SourcedValue(
        value=value,
        source="test-xbrl",
        confidence=confidence,
        as_of=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _make_full_statements() -> FinancialStatements:
    """Create statements with data for all 5 debt/tax metrics."""
    income_items = [
        FinancialLineItem(label="EBIT", xbrl_concept="ebit",
            values={"FY2023": _sv(1200.0), "FY2024": _sv(1500.0)}),
        FinancialLineItem(label="Interest Expense", xbrl_concept="interest_expense",
            values={"FY2023": _sv(200.0), "FY2024": _sv(250.0)}),
        FinancialLineItem(label="Income Tax", xbrl_concept="income_tax_expense",
            values={"FY2023": _sv(200.0), "FY2024": _sv(250.0)}),
        FinancialLineItem(label="Pretax Income", xbrl_concept="pretax_income",
            values={"FY2023": _sv(1000.0), "FY2024": _sv(1250.0)}),
        FinancialLineItem(label="Revenue", xbrl_concept="revenue",
            values={"FY2023": _sv(8000.0), "FY2024": _sv(9000.0)}),
    ]
    balance_items = [
        FinancialLineItem(label="Short-term Debt", xbrl_concept="short_term_debt",
            values={"FY2024": _sv(500.0)}),
        FinancialLineItem(label="Total Debt", xbrl_concept="total_debt",
            values={"FY2024": _sv(3000.0)}),
        FinancialLineItem(label="Equity", xbrl_concept="stockholders_equity",
            values={"FY2024": _sv(5000.0)}),
        FinancialLineItem(label="Deferred Tax Liability", xbrl_concept="deferred_tax_liability",
            values={"FY2023": _sv(400.0), "FY2024": _sv(500.0)}),
        FinancialLineItem(label="Pension Liability", xbrl_concept="pension_liability",
            values={"FY2024": _sv(600.0)}),
    ]
    return FinancialStatements(
        income_statement=FinancialStatement(
            statement_type="income",
            periods=["FY2023", "FY2024"],
            line_items=income_items,
        ),
        balance_sheet=FinancialStatement(
            statement_type="balance_sheet",
            periods=["FY2023", "FY2024"],
            line_items=balance_items,
        ),
    )


class TestInterestCoverage:
    """Test interest coverage computation and zones."""

    def test_danger_low_coverage(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="EBIT", xbrl_concept="ebit",
                        values={"FY2024": _sv(120.0)}),
                    FinancialLineItem(label="Interest", xbrl_concept="interest_expense",
                        values={"FY2024": _sv(100.0)}),
                ],
            ),
        )
        # Coverage = 120/100 = 1.2 -> danger (<1.5)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.interest_coverage.zone == "danger"
        assert result.interest_coverage.value == pytest.approx(1.2, abs=0.01)

    def test_warning_moderate_coverage(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="EBIT", xbrl_concept="ebit",
                        values={"FY2024": _sv(250.0)}),
                    FinancialLineItem(label="Interest", xbrl_concept="interest_expense",
                        values={"FY2024": _sv(100.0)}),
                ],
            ),
        )
        # Coverage = 2.5 -> warning (>=1.5 but <3.0)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.interest_coverage.zone == "warning"

    def test_safe_high_coverage(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="EBIT", xbrl_concept="ebit",
                        values={"FY2024": _sv(500.0)}),
                    FinancialLineItem(label="Interest", xbrl_concept="interest_expense",
                        values={"FY2024": _sv(100.0)}),
                ],
            ),
        )
        # Coverage = 5.0 -> safe (>=3.0)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.interest_coverage.zone == "safe"

    def test_coverage_trend(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = _make_full_statements()
        result, _ = compute_debt_tax_forensics(stmts)
        # EBIT/interest improved from 1200/200=6.0 to 1500/250=6.0 -> stable
        assert result.interest_coverage.trend is not None


class TestDebtMaturityConcentration:
    """Test debt maturity concentration."""

    def test_danger_high_short_term(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="ST Debt", xbrl_concept="short_term_debt",
                        values={"FY2024": _sv(1800.0)}),
                    FinancialLineItem(label="Total Debt", xbrl_concept="total_debt",
                        values={"FY2024": _sv(3000.0)}),
                ],
            ),
        )
        # 1800/3000 = 0.60 -> danger (>0.50)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.debt_maturity_concentration.zone == "danger"

    def test_safe_low_short_term(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="ST Debt", xbrl_concept="short_term_debt",
                        values={"FY2024": _sv(300.0)}),
                    FinancialLineItem(label="Total Debt", xbrl_concept="total_debt",
                        values={"FY2024": _sv(3000.0)}),
                ],
            ),
        )
        # 300/3000 = 0.10 -> safe (<=0.30)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.debt_maturity_concentration.zone == "safe"


class TestETRAnomaly:
    """Test effective tax rate anomaly detection."""

    def test_danger_low_etr(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Tax", xbrl_concept="income_tax_expense",
                        values={"FY2024": _sv(80.0)}),
                    FinancialLineItem(label="Pretax", xbrl_concept="pretax_income",
                        values={"FY2024": _sv(1000.0)}),
                ],
            ),
        )
        # ETR = 80/1000 = 0.08, deviation = abs(0.08 - 0.21) = 0.13 -> danger (>0.10)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.etr_anomaly.zone == "danger"

    def test_safe_normal_etr(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Tax", xbrl_concept="income_tax_expense",
                        values={"FY2024": _sv(200.0)}),
                    FinancialLineItem(label="Pretax", xbrl_concept="pretax_income",
                        values={"FY2024": _sv(1000.0)}),
                ],
            ),
        )
        # ETR = 200/1000 = 0.20, deviation = abs(0.20 - 0.21) = 0.01 -> safe
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.etr_anomaly.zone == "safe"

    def test_warning_moderate_deviation(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Tax", xbrl_concept="income_tax_expense",
                        values={"FY2024": _sv(280.0)}),
                    FinancialLineItem(label="Pretax", xbrl_concept="pretax_income",
                        values={"FY2024": _sv(1000.0)}),
                ],
            ),
        )
        # ETR = 0.28, deviation = 0.07 -> warning (>0.05 but <=0.10)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.etr_anomaly.zone == "warning"


class TestPensionUnderfunding:
    """Test pension underfunding metric."""

    def test_danger_high_underfunding(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Pension", xbrl_concept="pension_liability",
                        values={"FY2024": _sv(1800.0)}),
                    FinancialLineItem(label="Equity", xbrl_concept="stockholders_equity",
                        values={"FY2024": _sv(5000.0)}),
                ],
            ),
        )
        # 1800/5000 = 0.36 -> danger (>0.30)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.pension_underfunding.zone == "danger"

    def test_safe_low_pension(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Pension", xbrl_concept="pension_liability",
                        values={"FY2024": _sv(500.0)}),
                    FinancialLineItem(label="Equity", xbrl_concept="stockholders_equity",
                        values={"FY2024": _sv(5000.0)}),
                ],
            ),
        )
        # 500/5000 = 0.10 -> safe (<=0.15)
        result, _ = compute_debt_tax_forensics(stmts)
        assert result.pension_underfunding.zone == "safe"


class TestMissingPhase67Concepts:
    """Test graceful handling of Phase 67 concepts that may be None."""

    def test_missing_deferred_tax_still_computes_others(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="EBIT", xbrl_concept="ebit",
                        values={"FY2024": _sv(500.0)}),
                    FinancialLineItem(label="Interest", xbrl_concept="interest_expense",
                        values={"FY2024": _sv(100.0)}),
                ],
            ),
        )
        result, _ = compute_debt_tax_forensics(stmts)
        # Interest coverage should compute; deferred_tax + pension = insufficient
        assert result.interest_coverage.zone != "insufficient_data"
        assert result.deferred_tax_growth.zone == "insufficient_data"
        assert result.pension_underfunding.zone == "insufficient_data"


class TestAllMissing:
    """Test completely empty statements."""

    def test_all_none_returns_insufficient_data(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = FinancialStatements()
        result, report = compute_debt_tax_forensics(stmts)
        assert result.interest_coverage.zone == "insufficient_data"
        assert result.debt_maturity_concentration.zone == "insufficient_data"
        assert result.etr_anomaly.zone == "insufficient_data"
        assert result.deferred_tax_growth.zone == "insufficient_data"
        assert result.pension_underfunding.zone == "insufficient_data"
        assert report.coverage_pct == 0.0


class TestExtractionReport:
    """Test ExtractionReport coverage."""

    def test_full_data_report(self) -> None:
        from do_uw.stages.analyze.forensic_debt_tax import (
            compute_debt_tax_forensics,
        )

        stmts = _make_full_statements()
        _, report = compute_debt_tax_forensics(stmts)
        assert report.extractor_name == "forensic_debt_tax"
        assert len(report.found_fields) > 0
