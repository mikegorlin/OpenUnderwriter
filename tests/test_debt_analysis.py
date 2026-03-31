"""Tests for debt analysis extraction -- liquidity, leverage, debt, refinancing.

Tests the extract_debt_analysis function and its sub-extractors:
liquidity ratios, leverage ratios with flags, text-based debt structure
parsing, and refinancing risk assessment.

All tests use synthetic FinancialStatement data -- no network calls.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.financials import (
    ExtractedFinancials,
    FinancialLineItem,
    FinancialStatement,
    FinancialStatements,
)
from do_uw.models.state import AcquiredData, AnalysisState, ExtractedData
from do_uw.stages.extract.debt_analysis import extract_debt_analysis
from do_uw.stages.extract.debt_text_parsing import (
    extract_refinancing_risk,
)

# ---------------------------------------------------------------------------
# Test data helpers
# ---------------------------------------------------------------------------


def _sv(val: float, period_end: str = "2024-12-31") -> SourcedValue[float]:
    """Create a test SourcedValue[float]."""
    return SourcedValue[float](
        value=val,
        source="test 10-K",
        confidence=Confidence.HIGH,
        as_of=datetime.fromisoformat(period_end).replace(tzinfo=UTC),
    )


def _line_item(
    label: str,
    concept: str,
    values: dict[str, float],
) -> FinancialLineItem:
    """Create a FinancialLineItem from a {period: value} dict."""
    sv_values: dict[str, SourcedValue[float] | None] = {
        period: _sv(val) for period, val in values.items()
    }
    return FinancialLineItem(
        label=label,
        xbrl_concept=concept,
        values=sv_values,
    )


def _make_test_statements(
    *,
    current_assets: float = 500.0,
    current_liabilities: float = 200.0,
    inventory: float = 100.0,
    cash: float = 150.0,
    total_assets: float = 1000.0,
    stockholders_equity: float = 400.0,
    long_term_debt: float = 300.0,
    short_term_debt: float = 0.0,
    total_debt: float | None = None,
    operating_income: float = 100.0,
    depreciation: float = 20.0,
    interest_expense: float = 30.0,
    revenue: float = 500.0,
    operating_cash_flow: float = 120.0,
    include_balance_sheet: bool = True,
    include_income: bool = True,
    include_cash_flow: bool = True,
) -> FinancialStatements:
    """Build a FinancialStatements with known values for testing."""
    period = "FY2024"

    # Balance sheet
    bs_items: list[FinancialLineItem] = []
    if include_balance_sheet:
        bs_items = [
            _line_item("Current Assets", "current_assets", {period: current_assets}),
            _line_item(
                "Current Liabilities", "current_liabilities",
                {period: current_liabilities},
            ),
            _line_item("Inventory", "inventory", {period: inventory}),
            _line_item("Cash", "cash_and_equivalents", {period: cash}),
            _line_item("Total Assets", "total_assets", {period: total_assets}),
            _line_item(
                "Stockholders Equity", "stockholders_equity",
                {period: stockholders_equity},
            ),
            _line_item("Long-term Debt", "long_term_debt", {period: long_term_debt}),
            _line_item("Short-term Debt", "short_term_debt", {period: short_term_debt}),
        ]
        if total_debt is not None:
            bs_items.append(
                _line_item("Total Debt", "total_debt", {period: total_debt})
            )

    bs = (
        FinancialStatement(
            statement_type="balance_sheet",
            periods=[period],
            line_items=bs_items,
            filing_source="Test 10-K CIK0001234",
        )
        if include_balance_sheet
        else None
    )

    # Income statement
    inc_items: list[FinancialLineItem] = []
    if include_income:
        inc_items = [
            _line_item("Revenue", "revenue", {period: revenue}),
            _line_item("Operating Income", "operating_income", {period: operating_income}),
            _line_item("Interest Expense", "interest_expense", {period: interest_expense}),
        ]

    inc = (
        FinancialStatement(
            statement_type="income",
            periods=[period],
            line_items=inc_items,
            filing_source="Test 10-K CIK0001234",
        )
        if include_income
        else None
    )

    # Cash flow statement
    cf_items: list[FinancialLineItem] = []
    if include_cash_flow:
        cf_items = [
            _line_item(
                "Operating Cash Flow", "operating_cash_flow",
                {period: operating_cash_flow},
            ),
            _line_item("D&A", "depreciation_amortization", {period: depreciation}),
        ]

    cf = (
        FinancialStatement(
            statement_type="cash_flow",
            periods=[period],
            line_items=cf_items,
            filing_source="Test 10-K CIK0001234",
        )
        if include_cash_flow
        else None
    )

    return FinancialStatements(
        income_statement=inc,
        balance_sheet=bs,
        cash_flow=cf,
        periods_available=1,
    )


def _make_state(
    statements: FinancialStatements | None = None,
    filing_texts: dict[str, str] | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState with financials and optional texts."""
    filings: dict[str, Any] = {}
    if filing_texts is not None:
        filings["filing_texts"] = filing_texts

    financials = ExtractedFinancials()
    if statements is not None:
        financials.statements = statements

    return AnalysisState(
        ticker="TEST",
        company=CompanyProfile(
            identity=CompanyIdentity(
                ticker="TEST",
                cik=SourcedValue[str](
                    value="0001234",
                    source="SEC EDGAR",
                    confidence=Confidence.HIGH,
                    as_of=datetime(2024, 1, 1, tzinfo=UTC),
                ),
            )
        ),
        acquired_data=AcquiredData(filings=filings),
        extracted=ExtractedData(financials=financials),
    )


# ---------------------------------------------------------------------------
# Liquidity tests (SECT3-08)
# ---------------------------------------------------------------------------


class TestCurrentRatio:
    """Current ratio = Current Assets / Current Liabilities."""

    def test_current_ratio(self) -> None:
        stmts = _make_test_statements(
            current_assets=500, current_liabilities=200
        )
        state = _make_state(stmts)
        liq, _lev, _ds, _ref, _rpts = extract_debt_analysis(state)

        assert liq is not None
        assert liq.value["current_ratio"] == 2.5


class TestQuickRatio:
    """Quick ratio = (Current Assets - Inventory) / Current Liabilities."""

    def test_quick_ratio(self) -> None:
        stmts = _make_test_statements(
            current_assets=500, current_liabilities=200, inventory=100
        )
        state = _make_state(stmts)
        liq, _lev, _ds, _ref, _rpts = extract_debt_analysis(state)

        assert liq is not None
        # (500 - 100) / 200 = 2.0
        assert liq.value["quick_ratio"] == 2.0


class TestCashRatio:
    """Cash ratio = Cash / Current Liabilities."""

    def test_cash_ratio(self) -> None:
        stmts = _make_test_statements(
            cash=150, current_liabilities=200
        )
        state = _make_state(stmts)
        liq, _lev, _ds, _ref, _rpts = extract_debt_analysis(state)

        assert liq is not None
        # 150 / 200 = 0.75
        assert liq.value["cash_ratio"] == 0.75


class TestLiquidityMissingInputs:
    """Missing balance sheet -> all liquidity ratios None."""

    def test_liquidity_missing_inputs(self) -> None:
        stmts = _make_test_statements(include_balance_sheet=False)
        state = _make_state(stmts)
        liq, _lev, _ds, _ref, reports = extract_debt_analysis(state)

        assert liq is None
        # Liquidity report is first
        liq_report = reports[0]
        assert liq_report.extractor_name == "liquidity"
        assert liq_report.coverage_pct == 0.0


# ---------------------------------------------------------------------------
# Leverage tests (SECT3-09)
# ---------------------------------------------------------------------------


class TestDebtToEquity:
    """D/E = Total Debt / Stockholders' Equity."""

    def test_debt_to_equity(self) -> None:
        stmts = _make_test_statements(
            long_term_debt=300, stockholders_equity=400
        )
        state = _make_state(stmts)
        _liq, lev, _ds, _ref, _rpts = extract_debt_analysis(state)

        assert lev is not None
        # 300 / 400 = 0.75
        assert lev.value["debt_to_equity"] == 0.75


class TestDebtToEBITDA:
    """D/EBITDA = Total Debt / (Operating Income + D&A)."""

    def test_debt_to_ebitda(self) -> None:
        stmts = _make_test_statements(
            long_term_debt=300, operating_income=100, depreciation=20
        )
        state = _make_state(stmts)
        _liq, lev, _ds, _ref, _rpts = extract_debt_analysis(state)

        assert lev is not None
        # 300 / (100 + 20) = 2.5
        assert lev.value["debt_to_ebitda"] == 2.5


class TestInterestCoverage:
    """Interest Coverage = EBIT / Interest Expense."""

    def test_interest_coverage(self) -> None:
        stmts = _make_test_statements(
            operating_income=100, interest_expense=30
        )
        state = _make_state(stmts)
        _liq, lev, _ds, _ref, _rpts = extract_debt_analysis(state)

        assert lev is not None
        # 100 / 30 = 3.3333
        cov = lev.value["interest_coverage"]
        assert cov is not None
        assert round(cov, 2) == 3.33


class TestInterestCoverageZeroExpense:
    """Interest expense = 0 -> 'No debt service' flag."""

    def test_interest_coverage_zero_expense(self) -> None:
        stmts = _make_test_statements(
            operating_income=100, interest_expense=0
        )
        state = _make_state(stmts)
        _liq, lev, _ds, _ref, reports = extract_debt_analysis(state)

        assert lev is not None
        # interest_coverage should be None (handled specially)
        assert lev.value["interest_coverage"] is None

        # Should still be in found_fields and have the warning
        lev_report = reports[1]
        assert "interest_coverage" in lev_report.found_fields
        assert any(
            "No debt service" in w for w in lev_report.warnings
        )


class TestLeverageFlagsHigh:
    """D/EBITDA > 4.0 triggers warning flag."""

    def test_leverage_flags_high(self) -> None:
        # D/EBITDA = 600 / (100 + 20) = 5.0 > 4.0
        stmts = _make_test_statements(
            long_term_debt=600, operating_income=100, depreciation=20
        )
        state = _make_state(stmts)
        _liq, _lev, _ds, _ref, reports = extract_debt_analysis(state)

        lev_report = reports[1]
        assert any("Debt-to-EBITDA" in w and "4.0" in w for w in lev_report.warnings)


# ---------------------------------------------------------------------------
# Refinancing risk tests (SECT3-11)
# ---------------------------------------------------------------------------


class TestRefinancingRiskFromMaturity:
    """Near-term maturity > available cash -> HIGH risk."""

    def test_refinancing_risk_from_maturity(self) -> None:
        current_year = datetime.now(tz=UTC).year
        near_year = str(current_year + 1)

        # Debt structure with near-term maturity
        ds_value: dict[str, Any] = {
            "maturity_schedule": {near_year: 500.0},
            "interest_rates": {"fixed_rates": [], "floating_rates": []},
            "covenants": {"mentioned": False},
            "credit_facility": {"detected": False, "amount": None},
        }
        debt_structure = SourcedValue[dict[str, Any]](
            value=ds_value,
            source="test",
            confidence=Confidence.MEDIUM,
            as_of=datetime.now(tz=UTC),
        )

        # Cash = 100, no credit facility, maturity = 500 -> HIGH
        ref, report = extract_refinancing_risk(
            debt_structure=debt_structure,
            liquidity=None,
            cash_value=100.0,
            credit_facility_amount=None,
        )

        assert ref is not None
        assert ref.value["risk_level"] in ("HIGH", "CRITICAL")
        assert ref.value["near_term_maturities"] == 500.0
        assert report.coverage_pct == 100.0  # all 4 fields found


class TestRefinancingRiskNotAvailable:
    """No debt structure -> refinancing risk not available."""

    def test_refinancing_risk_not_available(self) -> None:
        ref, report = extract_refinancing_risk(
            debt_structure=None,
            liquidity=None,
            cash_value=100.0,
            credit_facility_amount=None,
        )

        assert ref is None
        assert report.extractor_name == "refinancing_risk"
        assert report.coverage_pct == 0.0
        assert any(
            "depends on debt structure" in w for w in report.warnings
        )


# ---------------------------------------------------------------------------
# Coverage reporting tests
# ---------------------------------------------------------------------------


class TestExtractionReportCoverage:
    """All expected ratios computed -> HIGH coverage."""

    def test_extraction_report_coverage(self) -> None:
        stmts = _make_test_statements(
            total_debt=300,
            current_assets=500,
            current_liabilities=200,
            cash=150,
            inventory=100,
            stockholders_equity=400,
            total_assets=1000,
            operating_income=100,
            depreciation=20,
            interest_expense=30,
            revenue=500,
        )
        state = _make_state(stmts)
        liq, lev, _ds, _ref, reports = extract_debt_analysis(state)

        assert liq is not None
        assert lev is not None

        # Liquidity report (first) should have high coverage
        liq_report = reports[0]
        assert liq_report.extractor_name == "liquidity"
        assert liq_report.coverage_pct >= 80.0

        # Leverage report (second) should have high coverage
        lev_report = reports[1]
        assert lev_report.extractor_name == "leverage"
        assert lev_report.coverage_pct >= 80.0


# ---------------------------------------------------------------------------
# No-imputation test
# ---------------------------------------------------------------------------


class TestNoImputation:
    """Missing balance sheet data -> None values, never fabricated."""

    def test_no_imputation(self) -> None:
        # Balance sheet with only current_assets -- missing everything else
        bs = FinancialStatement(
            statement_type="balance_sheet",
            periods=["FY2024"],
            line_items=[
                _line_item("Current Assets", "current_assets", {"FY2024": 500.0}),
            ],
            filing_source="Test",
        )
        stmts = FinancialStatements(
            balance_sheet=bs,
            income_statement=None,
            cash_flow=None,
            periods_available=1,
        )
        state = _make_state(stmts)
        liq, lev, _ds, _ref, _rpts = extract_debt_analysis(state)

        # Liquidity should be None (can't compute ratios without CL)
        assert liq is None

        # Leverage should be None (no debt, no equity data)
        assert lev is None


# ---------------------------------------------------------------------------
# Debt structure text parsing test
# ---------------------------------------------------------------------------


class TestDebtStructureTextParsing:
    """Text-based debt structure extraction from filing text."""

    def test_debt_structure_extracts_from_text(self) -> None:
        filing_text = (
            "The Company has a revolving credit facility of $500 million. "
            "The term loan of $200 million matures in 2026. "
            "The senior notes of $300 million due 2028. "
            "Interest rate is 4.5% per annum on the fixed rate notes. "
            "The variable rate borrowings bear interest at SOFR plus 1.5%. "
            "The Company must maintain a debt covenant ratio of 3.5x."
        )
        state = _make_state(
            statements=_make_test_statements(),
            filing_texts={"item7": filing_text},
        )
        _liq, _lev, ds, _ref, reports = extract_debt_analysis(state)

        assert ds is not None
        assert ds.confidence == Confidence.MEDIUM

        # Debt structure report is third
        ds_report = reports[2]
        assert ds_report.extractor_name == "debt_structure"
        assert ds_report.coverage_pct > 0.0

    def test_no_filing_text_returns_none(self) -> None:
        state = _make_state(
            statements=_make_test_statements(),
            filing_texts={},
        )
        _liq, _lev, ds, _ref, reports = extract_debt_analysis(state)

        assert ds is None
        ds_report = reports[2]
        assert ds_report.coverage_pct == 0.0
