"""Tests for Beneish decomposition forensic analysis (FRNSC-05, FRNSC-07).

Tests:
- Beneish components populated from compute_m_score
- Primary driver identification
- Trajectory across periods
- SGI-driven context note
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
    }
    balance_concepts = {
        "total_assets", "current_assets", "current_liabilities",
        "property_plant_equipment", "accounts_receivable",
        "total_liabilities", "long_term_debt", "goodwill",
        "stockholders_equity",
    }
    cf_concepts = {"operating_cash_flow", "capital_expenditures", "acquisitions_net"}

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
            # Default: put on balance sheet
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


# -- DistressResult.components tests --

class TestDistressResultComponents:
    """Test that compute_m_score populates components dict."""

    def test_components_populated(self) -> None:
        from do_uw.stages.analyze.financial_formulas import compute_m_score

        inputs = {
            "accounts_receivable": 20.0, "accounts_receivable_prior": 15.0,
            "revenue": 100.0, "revenue_prior": 80.0,
            "gross_profit": 40.0, "gross_profit_prior": 30.0,
            "current_assets": 80.0, "current_assets_prior": 70.0,
            "property_plant_equipment": 100.0, "property_plant_equipment_prior": 90.0,
            "total_assets": 200.0, "total_assets_prior": 180.0,
            "depreciation_amortization": 10.0, "depreciation_amortization_prior": 8.0,
            "sga_expense": 15.0, "sga_expense_prior": 12.0,
            "net_income": 20.0, "operating_cash_flow": 25.0,
            "total_liabilities": 100.0, "total_liabilities_prior": 95.0,
        }
        result = compute_m_score(inputs)
        assert result.score is not None
        assert len(result.components) == 8
        assert "dsri" in result.components
        assert "tata" in result.components

    def test_components_empty_when_insufficient(self) -> None:
        from do_uw.stages.analyze.financial_formulas import compute_m_score

        result = compute_m_score({"revenue": 100.0})
        assert result.score is None
        assert result.components == {}

    def test_components_backward_compatible(self) -> None:
        from do_uw.models.financials import DistressResult
        result = DistressResult()
        assert result.components == {}


# -- Beneish decomposition tests --

class TestBeneishDecomposition:
    """Test compute_beneish_decomposition."""

    def test_decomposition_all_indices(self) -> None:
        from do_uw.stages.analyze.forensic_beneish import compute_beneish_decomposition

        latest = {
            "revenue": 100.0, "gross_profit": 40.0, "sga_expense": 15.0,
            "depreciation_amortization": 10.0, "net_income": 20.0,
            "accounts_receivable": 20.0, "current_assets": 80.0,
            "property_plant_equipment": 100.0, "total_assets": 200.0,
            "total_liabilities": 100.0, "operating_cash_flow": 25.0,
        }
        prior = {
            "revenue": 80.0, "gross_profit": 30.0, "sga_expense": 12.0,
            "depreciation_amortization": 8.0,
            "accounts_receivable": 15.0, "current_assets": 70.0,
            "property_plant_equipment": 90.0, "total_assets": 180.0,
            "total_liabilities": 95.0,
        }
        stmts = _make_statements(latest, prior)
        beneish, report = compute_beneish_decomposition(stmts)

        assert beneish.composite_score is not None
        assert beneish.dsri is not None
        assert beneish.gmi is not None
        assert beneish.aqi is not None
        assert beneish.sgi is not None
        assert beneish.depi is not None
        assert beneish.sgai is not None
        assert beneish.tata is not None
        assert beneish.lvgi is not None
        assert beneish.zone in ("safe", "manipulation_likely")

    def test_primary_driver_identified(self) -> None:
        from do_uw.stages.analyze.forensic_beneish import compute_beneish_decomposition

        latest = {
            "revenue": 100.0, "gross_profit": 40.0, "sga_expense": 15.0,
            "depreciation_amortization": 10.0, "net_income": 20.0,
            "accounts_receivable": 20.0, "current_assets": 80.0,
            "property_plant_equipment": 100.0, "total_assets": 200.0,
            "total_liabilities": 100.0, "operating_cash_flow": 25.0,
        }
        prior = {
            "revenue": 80.0, "gross_profit": 30.0, "sga_expense": 12.0,
            "depreciation_amortization": 8.0,
            "accounts_receivable": 15.0, "current_assets": 70.0,
            "property_plant_equipment": 90.0, "total_assets": 180.0,
            "total_liabilities": 95.0,
        }
        stmts = _make_statements(latest, prior)
        beneish, _ = compute_beneish_decomposition(stmts)

        assert beneish.primary_driver is not None
        assert beneish.primary_driver in {
            "dsri", "gmi", "aqi", "sgi", "depi", "sgai", "tata", "lvgi",
        }

    def test_trajectory_across_periods(self) -> None:
        from do_uw.stages.analyze.forensic_beneish import compute_beneish_decomposition

        latest = {
            "revenue": 100.0, "gross_profit": 40.0, "sga_expense": 15.0,
            "depreciation_amortization": 10.0, "net_income": 20.0,
            "accounts_receivable": 20.0, "current_assets": 80.0,
            "property_plant_equipment": 100.0, "total_assets": 200.0,
            "total_liabilities": 100.0, "operating_cash_flow": 25.0,
        }
        prior = {
            "revenue": 80.0, "gross_profit": 30.0, "sga_expense": 12.0,
            "depreciation_amortization": 8.0,
            "accounts_receivable": 15.0, "current_assets": 70.0,
            "property_plant_equipment": 90.0, "total_assets": 180.0,
            "total_liabilities": 95.0,
        }
        stmts = _make_statements(latest, prior)
        beneish, _ = compute_beneish_decomposition(stmts)

        # With 2 periods we get trajectory entries
        assert isinstance(beneish.trajectory, list)

    def test_insufficient_data(self) -> None:
        from do_uw.stages.analyze.forensic_beneish import compute_beneish_decomposition

        stmts = _make_statements({"revenue": 100.0})
        beneish, report = compute_beneish_decomposition(stmts)

        assert beneish.zone == "insufficient_data"
        assert beneish.composite_score is None


# -- M&A forensics tests --

class TestMAForensics:
    """Test compute_ma_forensics."""

    def test_serial_acquirer_detection(self) -> None:
        from do_uw.stages.analyze.forensic_ma import compute_ma_forensics

        # Create statements with acquisitions_net in multiple periods
        latest = {
            "acquisitions_net": -500.0, "goodwill": 300.0,
            "revenue": 1000.0, "total_assets": 2000.0,
        }
        prior = {
            "acquisitions_net": -300.0, "goodwill": 200.0,
            "revenue": 900.0, "total_assets": 1800.0,
        }
        stmts = _make_statements(latest, prior)
        ma, report = compute_ma_forensics(stmts)

        # With only 2 periods, not enough for serial acquirer
        assert ma.is_serial_acquirer is False
        assert ma.total_acquisition_spend is not None

    def test_no_acquisitions(self) -> None:
        from do_uw.stages.analyze.forensic_ma import compute_ma_forensics

        stmts = _make_statements({"revenue": 1000.0, "total_assets": 2000.0})
        ma, report = compute_ma_forensics(stmts)

        assert ma.is_serial_acquirer is False
        assert ma.total_acquisition_spend is None
