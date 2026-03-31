"""Tests for capital allocation forensic analysis module.

Validates compute_capital_allocation_forensics produces correct metrics,
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
from do_uw.models.xbrl_forensics import CapitalAllocationForensics


def _sv(value: float, confidence: Confidence = Confidence.HIGH) -> SourcedValue[float]:
    """Create a test SourcedValue."""
    return SourcedValue(
        value=value,
        source="test-xbrl",
        confidence=confidence,
        as_of=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _make_roic_statements(
    ebit: float = 1500.0,
    tax: float = 300.0,
    pretax: float = 1400.0,
    equity: float = 5000.0,
    total_debt: float = 3000.0,
    cash: float = 1000.0,
    ebit_prior: float = 1200.0,
    tax_prior: float = 250.0,
    pretax_prior: float = 1100.0,
    equity_prior: float = 4500.0,
    total_debt_prior: float = 2800.0,
    cash_prior: float = 900.0,
) -> FinancialStatements:
    """Create statements for ROIC testing."""
    return FinancialStatements(
        income_statement=FinancialStatement(
            statement_type="income",
            periods=["FY2023", "FY2024"],
            line_items=[
                FinancialLineItem(label="EBIT", xbrl_concept="ebit",
                    values={"FY2023": _sv(ebit_prior), "FY2024": _sv(ebit)}),
                FinancialLineItem(label="Income Tax", xbrl_concept="income_tax_expense",
                    values={"FY2023": _sv(tax_prior), "FY2024": _sv(tax)}),
                FinancialLineItem(label="Pretax Income", xbrl_concept="pretax_income",
                    values={"FY2023": _sv(pretax_prior), "FY2024": _sv(pretax)}),
            ],
        ),
        balance_sheet=FinancialStatement(
            statement_type="balance_sheet",
            periods=["FY2023", "FY2024"],
            line_items=[
                FinancialLineItem(label="Equity", xbrl_concept="stockholders_equity",
                    values={"FY2023": _sv(equity_prior), "FY2024": _sv(equity)}),
                FinancialLineItem(label="Total Debt", xbrl_concept="total_debt",
                    values={"FY2023": _sv(total_debt_prior), "FY2024": _sv(total_debt)}),
                FinancialLineItem(label="Cash", xbrl_concept="cash_and_equivalents",
                    values={"FY2023": _sv(cash_prior), "FY2024": _sv(cash)}),
            ],
        ),
    )


def _make_full_statements() -> FinancialStatements:
    """Create FinancialStatements with data for all 4 metrics."""
    income_items = [
        FinancialLineItem(label="EBIT", xbrl_concept="ebit",
            values={"FY2023": _sv(1200.0), "FY2024": _sv(1500.0)}),
        FinancialLineItem(label="Income Tax", xbrl_concept="income_tax_expense",
            values={"FY2023": _sv(250.0), "FY2024": _sv(300.0)}),
        FinancialLineItem(label="Pretax Income", xbrl_concept="pretax_income",
            values={"FY2023": _sv(1100.0), "FY2024": _sv(1400.0)}),
        FinancialLineItem(label="Revenue", xbrl_concept="revenue",
            values={"FY2023": _sv(8000.0), "FY2024": _sv(9000.0)}),
    ]
    balance_items = [
        FinancialLineItem(label="Equity", xbrl_concept="stockholders_equity",
            values={"FY2023": _sv(4500.0), "FY2024": _sv(5000.0)}),
        FinancialLineItem(label="Total Debt", xbrl_concept="total_debt",
            values={"FY2023": _sv(2800.0), "FY2024": _sv(3000.0)}),
        FinancialLineItem(label="Cash", xbrl_concept="cash_and_equivalents",
            values={"FY2023": _sv(900.0), "FY2024": _sv(1000.0)}),
        FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
            values={"FY2023": _sv(2000.0), "FY2024": _sv(2500.0)}),
        FinancialLineItem(label="Shares Outstanding", xbrl_concept="shares_outstanding",
            values={"FY2023": _sv(100.0), "FY2024": _sv(90.0)}),
    ]
    cf_items = [
        FinancialLineItem(label="Share Repurchases", xbrl_concept="share_repurchases",
            values={"FY2023": _sv(-500.0), "FY2024": _sv(-800.0)}),
        FinancialLineItem(label="Operating Cash Flow", xbrl_concept="operating_cash_flow",
            values={"FY2023": _sv(1800.0), "FY2024": _sv(2000.0)}),
        FinancialLineItem(label="Capital Expenditures", xbrl_concept="capital_expenditures",
            values={"FY2023": _sv(-400.0), "FY2024": _sv(-500.0)}),
        FinancialLineItem(label="Dividends Paid", xbrl_concept="dividends_paid",
            values={"FY2023": _sv(-300.0), "FY2024": _sv(-400.0)}),
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
        cash_flow=FinancialStatement(
            statement_type="cash_flow",
            periods=["FY2023", "FY2024"],
            line_items=cf_items,
        ),
    )


class TestROIC:
    """Test ROIC computation and zone classification."""

    def test_roic_safe_zone(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        # EBIT=1500, tax_rate=300/1400=0.2143, NOPAT=1500*(1-0.2143)=1178.6
        # Invested capital = 5000+3000-1000 = 7000
        # ROIC = 1178.6/7000 = 0.1684 -> safe (>= 0.10)
        stmts = _make_roic_statements()
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.roic.value is not None
        assert result.roic.value == pytest.approx(0.1684, abs=0.01)
        assert result.roic.zone == "safe"

    def test_roic_warning_zone(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        # EBIT=500, tax_rate=0.21 (statutory fallback), NOPAT=500*0.79=395
        # IC=5000+3000-1000=7000, ROIC=395/7000=0.0564 -> warning
        stmts = _make_roic_statements(ebit=500.0, tax=0.0, pretax=0.0)
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.roic.value is not None
        assert result.roic.zone == "warning"

    def test_roic_danger_zone(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        # EBIT=200, NOPAT~158, IC=7000, ROIC=0.0226 -> danger (<0.05)
        stmts = _make_roic_statements(ebit=200.0, tax=0.0, pretax=0.0)
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.roic.zone == "danger"

    def test_roic_trend(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = _make_roic_statements()
        result, _ = compute_capital_allocation_forensics(stmts)
        # ROIC improved from prior period -- trend should be set
        assert result.roic.trend is not None


class TestAcquisitionEffectiveness:
    """Test acquisition effectiveness (goodwill growth vs revenue growth)."""

    def test_danger_goodwill_growing_3x_revenue(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={"FY2023": _sv(8000.0), "FY2024": _sv(8800.0)}),  # 10% growth
                ],
            ),
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
                        values={"FY2023": _sv(2000.0), "FY2024": _sv(2600.0)}),  # 30% growth
                ],
            ),
        )
        result, _ = compute_capital_allocation_forensics(stmts)
        # 30% / 10% = 3.0 -> danger (> 2.0)
        assert result.acquisition_effectiveness.zone == "danger"

    def test_safe_proportional_growth(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={"FY2023": _sv(8000.0), "FY2024": _sv(8800.0)}),  # 10%
                ],
            ),
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
                        values={"FY2023": _sv(2000.0), "FY2024": _sv(2200.0)}),  # 10%
                ],
            ),
        )
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.acquisition_effectiveness.zone == "safe"


class TestBuybackTiming:
    """Test buyback timing quality with market data."""

    def test_danger_overpaying(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Shares", xbrl_concept="shares_outstanding",
                        values={"FY2023": _sv(100.0), "FY2024": _sv(90.0)}),  # 10 retired
                ],
            ),
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Repurchases", xbrl_concept="share_repurchases",
                        values={"FY2023": _sv(-500.0), "FY2024": _sv(-1400.0)}),
                ],
            ),
        )
        # implied_price = 1400/10 = 140, avg_close = 100 -> premium 1.4 -> danger
        market_data = {"avg_close": 100.0}
        result, _ = compute_capital_allocation_forensics(stmts, market_data=market_data)
        assert result.buyback_timing.zone == "danger"
        assert result.buyback_timing.value == pytest.approx(1.4, abs=0.01)

    def test_no_repurchases_not_applicable(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = FinancialStatements(
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Repurchases", xbrl_concept="share_repurchases",
                        values={"FY2024": _sv(0.0)}),
                ],
            ),
        )
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.buyback_timing.zone == "not_applicable"

    def test_no_market_data_still_computes(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = _make_full_statements()
        result, _ = compute_capital_allocation_forensics(stmts, market_data=None)
        # Without market data, can't compute premium -- insufficient_data
        assert result.buyback_timing.zone == "insufficient_data"


class TestDividendSustainability:
    """Test dividend payout ratio vs FCF."""

    def test_danger_over_100_pct(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = FinancialStatements(
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
                        values={"FY2024": _sv(500.0)}),
                    FinancialLineItem(label="Capex", xbrl_concept="capital_expenditures",
                        values={"FY2024": _sv(-200.0)}),
                    FinancialLineItem(label="Dividends", xbrl_concept="dividends_paid",
                        values={"FY2024": _sv(-400.0)}),
                ],
            ),
        )
        # FCF = 500 - 200 = 300, payout = 400/300 = 1.33 -> danger
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.dividend_sustainability.zone == "danger"

    def test_safe_low_payout(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = FinancialStatements(
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
                        values={"FY2024": _sv(2000.0)}),
                    FinancialLineItem(label="Capex", xbrl_concept="capital_expenditures",
                        values={"FY2024": _sv(-500.0)}),
                    FinancialLineItem(label="Dividends", xbrl_concept="dividends_paid",
                        values={"FY2024": _sv(-300.0)}),
                ],
            ),
        )
        # FCF = 2000 - 500 = 1500, payout = 300/1500 = 0.20 -> safe
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.dividend_sustainability.zone == "safe"
        assert result.dividend_sustainability.value == pytest.approx(0.20, abs=0.01)


class TestMissingData:
    """Test graceful handling of all None inputs."""

    def test_all_none_returns_insufficient_data(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = FinancialStatements()
        result, report = compute_capital_allocation_forensics(stmts)
        assert result.roic.zone == "insufficient_data"
        assert result.acquisition_effectiveness.zone == "insufficient_data"
        # No repurchase/dividend data -> not_applicable (no activity detected)
        assert result.buyback_timing.zone == "not_applicable"
        assert result.dividend_sustainability.zone == "not_applicable"

    def test_confidence_is_min_of_inputs(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        # Mix HIGH and MEDIUM confidence
        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="EBIT", xbrl_concept="ebit",
                        values={"FY2024": _sv(1500.0, Confidence.HIGH)}),
                    FinancialLineItem(label="Tax", xbrl_concept="income_tax_expense",
                        values={"FY2024": _sv(300.0, Confidence.MEDIUM)}),
                    FinancialLineItem(label="Pretax", xbrl_concept="pretax_income",
                        values={"FY2024": _sv(1400.0, Confidence.HIGH)}),
                ],
            ),
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Equity", xbrl_concept="stockholders_equity",
                        values={"FY2024": _sv(5000.0, Confidence.HIGH)}),
                    FinancialLineItem(label="Debt", xbrl_concept="total_debt",
                        values={"FY2024": _sv(3000.0, Confidence.HIGH)}),
                    FinancialLineItem(label="Cash", xbrl_concept="cash_and_equivalents",
                        values={"FY2024": _sv(1000.0, Confidence.HIGH)}),
                ],
            ),
        )
        result, _ = compute_capital_allocation_forensics(stmts)
        assert result.roic.confidence == Confidence.MEDIUM


class TestExtractionReport:
    """Test ExtractionReport coverage tracking."""

    def test_full_data_report(self) -> None:
        from do_uw.stages.analyze.forensic_capital_alloc import (
            compute_capital_allocation_forensics,
        )

        stmts = _make_full_statements()
        market_data = {"avg_close": 100.0}
        result, report = compute_capital_allocation_forensics(stmts, market_data=market_data)
        assert report.extractor_name == "forensic_capital_alloc"
        assert len(report.found_fields) > 0
