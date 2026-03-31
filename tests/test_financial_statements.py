"""Tests for financial statement extraction from XBRL Company Facts.

Tests the extract_financial_statements function and its helpers:
period labeling, YoY calculation, deduplication behavior,
extraction reports, and edge cases.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.financial_statements import (
    compute_yoy_change,
    determine_periods,
    extract_financial_statements,
    fiscal_year_label,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_company_facts(*concept_defs: tuple[str, str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Build a synthetic Company Facts API response.

    Each concept_def is (concept_name, unit, entries_list).

    Returns:
        Dict matching the companyfacts API shape.
    """
    us_gaap: dict[str, Any] = {}
    for concept_name, unit, entries in concept_defs:
        us_gaap[concept_name] = {"units": {unit: entries}}

    return {
        "cik": 1234567,
        "entityName": "Test Corp",
        "facts": {"us-gaap": us_gaap},
    }


def _make_entry(
    val: float,
    end: str,
    fy: int,
    form: str = "10-K",
    filed: str = "2025-02-15",
    fp: str = "FY",
    accn: str = "0001234-24-001",
) -> dict[str, Any]:
    """Build a single XBRL fact entry."""
    return {
        "val": val,
        "end": end,
        "fy": fy,
        "fp": fp,
        "form": form,
        "filed": filed,
        "accn": accn,
    }


def _make_state(facts: dict[str, Any] | None = None) -> AnalysisState:
    """Build a minimal AnalysisState with Company Facts data."""
    filings: dict[str, Any] = {}
    if facts is not None:
        filings["company_facts"] = facts

    return AnalysisState(
        ticker="TEST",
        company=CompanyProfile(
            identity=CompanyIdentity(
                ticker="TEST",
                cik=SourcedValue[str](
                    value="0001234567",
                    source="SEC EDGAR",
                    confidence=Confidence.HIGH,
                    as_of=datetime(2024, 1, 1, tzinfo=UTC),
                ),
            )
        ),
        acquired_data=AcquiredData(filings=filings),
    )


# ---------------------------------------------------------------------------
# Multi-concept test data (income + balance + cash flow)
# ---------------------------------------------------------------------------


def _make_multi_statement_facts() -> dict[str, Any]:
    """Build facts covering 3 statements with 2-3 periods each."""
    return _make_company_facts(
        # Income statement concepts
        ("Revenues", "USD", [
            _make_entry(100_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(80_000_000, "2023-12-31", 2023, filed="2024-02-15"),
            _make_entry(60_000_000, "2022-12-31", 2022, filed="2023-02-15"),
        ]),
        ("NetIncomeLoss", "USD", [
            _make_entry(20_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(15_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        ("CostOfRevenue", "USD", [
            _make_entry(50_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(40_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        ("OperatingIncomeLoss", "USD", [
            _make_entry(30_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(25_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        ("EarningsPerShareBasic", "USD/shares", [
            _make_entry(2.50, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(1.80, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        # Balance sheet concepts
        ("Assets", "USD", [
            _make_entry(500_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(450_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        ("Liabilities", "USD", [
            _make_entry(200_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(180_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        ("StockholdersEquity", "USD", [
            _make_entry(300_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(270_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        # Cash flow concepts
        ("NetCashProvidedByUsedInOperatingActivities", "USD", [
            _make_entry(40_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(35_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
        ("PaymentsToAcquirePropertyPlantAndEquipment", "USD", [
            _make_entry(10_000_000, "2024-12-31", 2024, filed="2025-02-15"),
            _make_entry(8_000_000, "2023-12-31", 2023, filed="2024-02-15"),
        ]),
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExtractIncomeStatementMultiPeriod:
    """Income statement extracts multiple periods correctly."""

    def test_extract_income_statement_multi_period(self) -> None:
        facts = _make_multi_statement_facts()
        state = _make_state(facts)
        statements, _reports = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None
        assert income.statement_type == "income"
        assert len(income.periods) >= 2

        # Revenue should be present.
        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        assert len(revenue_items) == 1
        rv = revenue_items[0]
        assert "FY2024" in rv.values
        sv = rv.values["FY2024"]
        assert sv is not None
        assert sv.value == 100_000_000

    def test_three_statements_extracted(self) -> None:
        facts = _make_multi_statement_facts()
        state = _make_state(facts)
        statements, _reports = extract_financial_statements(state)

        assert statements.income_statement is not None
        assert statements.balance_sheet is not None
        assert statements.cash_flow is not None
        assert statements.periods_available >= 2


class TestYoYChangeCalculation:
    """YoY change calculations are correct."""

    def test_yoy_change_calculation(self) -> None:
        facts = _make_multi_statement_facts()
        state = _make_state(facts)
        statements, _ = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None

        # Revenue: (100M - 80M) / |80M| * 100 = 25%
        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        assert len(revenue_items) == 1
        assert revenue_items[0].yoy_change == 25.0

    def test_yoy_change_with_zero_prior(self) -> None:
        """Zero prior period value should produce None (not division error)."""
        periods = ["FY2023", "FY2024"]
        values: dict[str, SourcedValue[float] | None] = {
            "FY2023": SourcedValue[float](
                value=0.0,
                source="test",
                confidence=Confidence.HIGH,
                as_of=datetime(2023, 12, 31, tzinfo=UTC),
            ),
            "FY2024": SourcedValue[float](
                value=100.0,
                source="test",
                confidence=Confidence.HIGH,
                as_of=datetime(2024, 12, 31, tzinfo=UTC),
            ),
        }
        result = compute_yoy_change(values, periods)
        assert result is None


class TestDeduplication:
    """Deduplication logic prefers 10-K and latest filed."""

    def test_deduplication_prefers_10k(self) -> None:
        """10-K entries should be preferred over 10-Q for same period."""
        facts = _make_company_facts(
            ("Revenues", "USD", [
                _make_entry(100_000_000, "2024-12-31", 2024,
                            form="10-K", filed="2025-02-15"),
                # Same period from 10-Q (should be filtered out).
                _make_entry(100_000_000, "2024-12-31", 2024,
                            form="10-Q", filed="2025-04-15"),
                _make_entry(80_000_000, "2023-12-31", 2023,
                            form="10-K", filed="2024-02-15"),
            ]),
        )
        state = _make_state(facts)
        statements, _ = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None
        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        assert len(revenue_items) == 1
        # Should have exactly 2 periods (10-Q filtered out by resolve_concept).
        sv = revenue_items[0].values.get("FY2024")
        assert sv is not None
        assert sv.value == 100_000_000

    def test_deduplication_prefers_latest_filed(self) -> None:
        """When two 10-K entries exist for same period, prefer latest filed."""
        facts = _make_company_facts(
            ("Revenues", "USD", [
                _make_entry(95_000_000, "2024-12-31", 2024,
                            form="10-K", filed="2025-02-15"),
                # Amendment filed later with corrected value.
                _make_entry(100_000_000, "2024-12-31", 2024,
                            form="10-K", filed="2025-05-01",
                            accn="0001234-24-002"),
                _make_entry(80_000_000, "2023-12-31", 2023,
                            form="10-K", filed="2024-02-15"),
            ]),
        )
        state = _make_state(facts)
        statements, _ = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None
        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        sv = revenue_items[0].values.get("FY2024")
        assert sv is not None
        # Latest filed (amendment) should win.
        assert sv.value == 100_000_000


class TestMissingConceptInReport:
    """Missing concepts tracked in ExtractionReport."""

    def test_missing_concept_in_report(self) -> None:
        """Concepts not in facts should appear in missing_fields."""
        # Only provide revenue -- everything else will be missing.
        facts = _make_company_facts(
            ("Revenues", "USD", [
                _make_entry(100_000_000, "2024-12-31", 2024),
            ]),
        )
        state = _make_state(facts)
        _, reports = extract_financial_statements(state)

        income_report = reports[0]
        assert income_report.extractor_name == "income"
        assert "revenue" in income_report.found_fields
        assert "net_income" in income_report.missing_fields


class TestExtractionReportCoveragePercentage:
    """Coverage percentage is correct in extraction reports."""

    def test_extraction_report_coverage_percentage(self) -> None:
        facts = _make_multi_statement_facts()
        state = _make_state(facts)
        _, reports = extract_financial_statements(state)

        # At least income and balance sheet reports should exist.
        assert len(reports) == 3
        for report in reports:
            assert 0.0 <= report.coverage_pct <= 100.0
            assert report.confidence in list(Confidence)


class TestBalanceSheetInstantVsDuration:
    """Balance sheet uses instant-type concepts correctly."""

    def test_balance_sheet_instant_vs_duration(self) -> None:
        facts = _make_multi_statement_facts()
        state = _make_state(facts)
        statements, _ = extract_financial_statements(state)

        bs = statements.balance_sheet
        assert bs is not None
        assert bs.statement_type == "balance_sheet"

        # Total assets should be present (instant concept).
        asset_items = [
            li for li in bs.line_items if li.xbrl_concept == "total_assets"
        ]
        assert len(asset_items) == 1
        assert "FY2024" in asset_items[0].values


class TestSinglePeriodCompany:
    """Newly public companies with only 1 period."""

    def test_single_period_company(self) -> None:
        facts = _make_company_facts(
            ("Revenues", "USD", [
                _make_entry(50_000_000, "2024-12-31", 2024),
            ]),
            ("Assets", "USD", [
                _make_entry(200_000_000, "2024-12-31", 2024),
            ]),
        )
        state = _make_state(facts)
        statements, _ = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None
        assert len(income.periods) == 1
        assert income.periods[0] == "FY2024"

        # YoY change should be None with single period.
        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        assert revenue_items[0].yoy_change is None
        assert statements.periods_available == 1


class TestFallbackTagResolution:
    """Fallback XBRL tags resolve when primary tag is absent."""

    def test_fallback_tag_resolution(self) -> None:
        """Revenue resolves via secondary tag when primary missing."""
        # Use RevenueFromContractWithCustomerExcludingAssessedTax (2nd tag).
        facts = _make_company_facts(
            ("RevenueFromContractWithCustomerExcludingAssessedTax", "USD", [
                _make_entry(100_000_000, "2024-12-31", 2024),
                _make_entry(80_000_000, "2023-12-31", 2023),
            ]),
        )
        state = _make_state(facts)
        statements, reports = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None
        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        assert len(revenue_items) == 1
        assert revenue_items[0].values.get("FY2024") is not None

        # Revenue should be in found_fields.
        income_rpt = reports[0]
        assert "revenue" in income_rpt.found_fields


class TestNoImputationOnMissingData:
    """Missing data is None, never imputed."""

    def test_no_imputation_on_missing_data(self) -> None:
        """Concepts with no data should have empty values dict."""
        facts = _make_company_facts(
            ("Revenues", "USD", [
                _make_entry(100_000_000, "2024-12-31", 2024),
            ]),
        )
        state = _make_state(facts)
        statements, _ = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None

        # net_income concept has no data -- should exist with empty values.
        ni_items = [
            li for li in income.line_items if li.xbrl_concept == "net_income"
        ]
        assert len(ni_items) == 1
        assert ni_items[0].values == {}
        assert ni_items[0].yoy_change is None


class TestNoCompanyFacts:
    """Graceful handling when Company Facts data is absent."""

    def test_no_company_facts_returns_empty(self) -> None:
        state = _make_state(facts=None)
        statements, reports = extract_financial_statements(state)

        assert statements.income_statement is None
        assert statements.balance_sheet is None
        assert statements.cash_flow is None
        assert statements.periods_available == 0
        assert len(reports) == 3


class TestPeriodHelpers:
    """Unit tests for period label helpers."""

    def testfiscal_year_label_from_fy(self) -> None:
        entry: dict[str, Any] = {"fy": 2024, "end": "2024-12-31"}
        assert fiscal_year_label(entry) == "FY2024"

    def testfiscal_year_label_from_end_date(self) -> None:
        entry: dict[str, Any] = {"end": "2024-06-30"}
        assert fiscal_year_label(entry) == "FY2024"

    def testfiscal_year_label_unknown(self) -> None:
        entry: dict[str, Any] = {}
        assert fiscal_year_label(entry) == "FY_UNKNOWN"

    def testdetermine_periods_capped_at_three(self) -> None:
        entries: list[list[dict[str, Any]]] = [
            [
                {"fy": 2021, "end": "2021-12-31"},
                {"fy": 2022, "end": "2022-12-31"},
                {"fy": 2023, "end": "2023-12-31"},
                {"fy": 2024, "end": "2024-12-31"},
            ]
        ]
        periods = determine_periods(entries)
        assert len(periods) == 3
        assert periods == ["FY2022", "FY2023", "FY2024"]


class TestSourcedValueProvenance:
    """Every extracted value has proper source and confidence."""

    def test_sourced_value_has_provenance(self) -> None:
        facts = _make_multi_statement_facts()
        state = _make_state(facts)
        statements, _ = extract_financial_statements(state)

        income = statements.income_statement
        assert income is not None

        revenue_items = [
            li for li in income.line_items if li.xbrl_concept == "revenue"
        ]
        sv = revenue_items[0].values.get("FY2024")
        assert sv is not None
        assert sv.confidence == Confidence.HIGH
        assert "10-K" in sv.source
        assert "CIK" in sv.source
        assert sv.as_of.year == 2024
