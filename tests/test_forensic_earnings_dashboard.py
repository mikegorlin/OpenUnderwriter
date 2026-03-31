"""Tests for earnings quality dashboard forensic analysis (FRNSC-09).

Tests:
- Sloan accruals zones
- Cash flow manipulation index zones
- SBC/revenue with None (insufficient_data)
- Non-GAAP gap always limited
"""

from __future__ import annotations

import pytest

from do_uw.models.financials import FinancialLineItem, FinancialStatement, FinancialStatements
from do_uw.models.common import Confidence, SourcedValue


def _sv(val: float) -> SourcedValue[float]:
    """Create a SourcedValue for testing."""
    from datetime import UTC, datetime
    return SourcedValue(
        value=val,
        source="test",
        confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_statements(
    latest: dict[str, float],
    prior: dict[str, float] | None = None,
) -> FinancialStatements:
    """Build minimal FinancialStatements from concept->value dicts."""
    periods = ["FY2023", "FY2024"] if prior else ["FY2024"]
    income_items: list[FinancialLineItem] = []
    balance_items: list[FinancialLineItem] = []
    cf_items: list[FinancialLineItem] = []

    income_concepts = {
        "revenue", "gross_profit", "sga_expense",
        "depreciation_amortization", "net_income", "cost_of_revenue",
        "stock_based_compensation",
    }
    balance_concepts = {
        "total_assets", "current_assets", "current_liabilities",
        "property_plant_equipment", "accounts_receivable",
        "total_liabilities",
    }
    cf_concepts = {
        "operating_cash_flow", "capital_expenditures",
        "investing_cash_flow",
    }

    all_concepts = set(latest.keys())
    if prior:
        all_concepts |= set(prior.keys())

    for concept in all_concepts:
        values: dict[str, SourcedValue[float] | None] = {}
        if prior and concept in prior:
            values["FY2023"] = _sv(prior[concept])
        if concept in latest:
            values["FY2024"] = _sv(latest[concept])

        item = FinancialLineItem(
            label=concept,
            xbrl_concept=concept,
            values=values,
        )

        if concept in income_concepts:
            income_items.append(item)
        elif concept in balance_concepts:
            balance_items.append(item)
        elif concept in cf_concepts:
            cf_items.append(item)
        else:
            balance_items.append(item)

    return FinancialStatements(
        income_statement=FinancialStatement(
            statement_type="income",
            periods=periods,
            line_items=income_items,
        ),
        balance_sheet=FinancialStatement(
            statement_type="balance_sheet",
            periods=periods,
            line_items=balance_items,
        ),
        cash_flow=FinancialStatement(
            statement_type="cash_flow",
            periods=periods,
            line_items=cf_items,
        ),
        periods_available=len(periods),
    )


class TestSloanAccruals:
    """Test Sloan accruals ratio computation and zones."""

    def test_safe_zone(self) -> None:
        from do_uw.stages.analyze.forensic_earnings_dashboard import compute_earnings_dashboard

        # Sloan = (NI - CFO - CFI) / avg_TA
        # = (100 - 90 - (-5)) / ((1000 + 900) / 2) = 15 / 950 = 0.0158 -> safe
        stmts = _make_statements(
            latest={
                "net_income": 100.0, "operating_cash_flow": 90.0,
                "investing_cash_flow": -5.0, "total_assets": 1000.0,
                "revenue": 500.0,
            },
            prior={"total_assets": 900.0, "revenue": 450.0},
        )
        dashboard, report = compute_earnings_dashboard(stmts)
        assert dashboard.sloan_accruals.zone == "safe"
        assert dashboard.sloan_accruals.value is not None
        assert abs(dashboard.sloan_accruals.value) < 0.10

    def test_danger_zone(self) -> None:
        from do_uw.stages.analyze.forensic_earnings_dashboard import compute_earnings_dashboard

        # Sloan = (100 - 20 - (-5)) / ((200 + 180) / 2) = 85 / 190 = 0.447 -> danger
        stmts = _make_statements(
            latest={
                "net_income": 100.0, "operating_cash_flow": 20.0,
                "investing_cash_flow": -5.0, "total_assets": 200.0,
                "revenue": 500.0,
            },
            prior={"total_assets": 180.0, "revenue": 450.0},
        )
        dashboard, _ = compute_earnings_dashboard(stmts)
        assert dashboard.sloan_accruals.zone == "danger"


class TestCashFlowManipulation:
    """Test cash flow manipulation index."""

    def test_safe_ocf_ni_ratio(self) -> None:
        from do_uw.stages.analyze.forensic_earnings_dashboard import compute_earnings_dashboard

        stmts = _make_statements(
            latest={
                "net_income": 100.0, "operating_cash_flow": 120.0,
                "total_assets": 1000.0, "revenue": 500.0,
            },
            prior={"total_assets": 900.0},
        )
        dashboard, _ = compute_earnings_dashboard(stmts)
        assert dashboard.cash_flow_manipulation.zone == "safe"
        assert dashboard.cash_flow_manipulation.value == pytest.approx(1.2)

    def test_danger_low_ratio(self) -> None:
        from do_uw.stages.analyze.forensic_earnings_dashboard import compute_earnings_dashboard

        stmts = _make_statements(
            latest={
                "net_income": 100.0, "operating_cash_flow": 30.0,
                "total_assets": 1000.0, "revenue": 500.0,
            },
            prior={"total_assets": 900.0},
        )
        dashboard, _ = compute_earnings_dashboard(stmts)
        assert dashboard.cash_flow_manipulation.zone == "danger"


class TestSBCRevenue:
    """Test SBC/revenue ratio."""

    def test_no_sbc_data(self) -> None:
        from do_uw.stages.analyze.forensic_earnings_dashboard import compute_earnings_dashboard

        stmts = _make_statements(
            latest={
                "net_income": 100.0, "operating_cash_flow": 120.0,
                "total_assets": 1000.0, "revenue": 500.0,
            },
            prior={"total_assets": 900.0},
        )
        dashboard, _ = compute_earnings_dashboard(stmts)
        assert dashboard.sbc_revenue_ratio.zone == "insufficient_data"

    def test_high_sbc(self) -> None:
        from do_uw.stages.analyze.forensic_earnings_dashboard import compute_earnings_dashboard

        stmts = _make_statements(
            latest={
                "net_income": 100.0, "operating_cash_flow": 120.0,
                "total_assets": 1000.0, "revenue": 500.0,
                "stock_based_compensation": 60.0,  # 12% of revenue
            },
            prior={"total_assets": 900.0},
        )
        dashboard, _ = compute_earnings_dashboard(stmts)
        assert dashboard.sbc_revenue_ratio.zone == "danger"
        assert dashboard.sbc_revenue_ratio.value == pytest.approx(0.12)


class TestNonGAAPGap:
    """Test non-GAAP gap always flagged as limited."""

    def test_always_limited(self) -> None:
        from do_uw.stages.analyze.forensic_earnings_dashboard import compute_earnings_dashboard

        stmts = _make_statements(
            latest={
                "net_income": 100.0, "operating_cash_flow": 120.0,
                "total_assets": 1000.0, "revenue": 500.0,
            },
            prior={"total_assets": 900.0},
        )
        dashboard, _ = compute_earnings_dashboard(stmts)
        assert dashboard.non_gaap_gap.zone == "limited_data"
        assert dashboard.non_gaap_gap.confidence == Confidence.LOW
