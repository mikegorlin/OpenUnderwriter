"""Tests for balance sheet forensic analysis module.

Validates compute_balance_sheet_forensics produces correct metrics,
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
from do_uw.models.xbrl_forensics import BalanceSheetForensics, ForensicMetric


def _sv(value: float, confidence: Confidence = Confidence.HIGH) -> SourcedValue[float]:
    """Create a test SourcedValue."""
    return SourcedValue(
        value=value,
        source="test-xbrl",
        confidence=confidence,
        as_of=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _make_full_statements() -> FinancialStatements:
    """Create FinancialStatements with full data for all 5 metrics."""
    balance_items = [
        FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
            values={"FY2023": _sv(2000.0), "FY2024": _sv(2500.0)}),
        FinancialLineItem(label="Intangible Assets", xbrl_concept="intangible_assets",
            values={"FY2023": _sv(1000.0), "FY2024": _sv(1200.0)}),
        FinancialLineItem(label="Total Assets", xbrl_concept="total_assets",
            values={"FY2023": _sv(10000.0), "FY2024": _sv(12000.0)}),
        FinancialLineItem(label="Operating Lease Liabilities", xbrl_concept="operating_lease_liabilities",
            values={"FY2023": _sv(500.0), "FY2024": _sv(600.0)}),
        FinancialLineItem(label="Current Assets", xbrl_concept="current_assets",
            values={"FY2023": _sv(4000.0), "FY2024": _sv(5000.0)}),
        FinancialLineItem(label="Current Liabilities", xbrl_concept="current_liabilities",
            values={"FY2023": _sv(3000.0), "FY2024": _sv(3500.0)}),
        FinancialLineItem(label="Inventory", xbrl_concept="inventory",
            values={"FY2023": _sv(800.0), "FY2024": _sv(1000.0)}),
        FinancialLineItem(label="Accounts Receivable", xbrl_concept="accounts_receivable",
            values={"FY2023": _sv(1500.0), "FY2024": _sv(1800.0)}),
        FinancialLineItem(label="Accounts Payable", xbrl_concept="accounts_payable",
            values={"FY2023": _sv(700.0), "FY2024": _sv(900.0)}),
    ]
    income_items = [
        FinancialLineItem(label="Revenue", xbrl_concept="revenue",
            values={"FY2023": _sv(8000.0), "FY2024": _sv(9000.0)}),
        FinancialLineItem(label="Cost of Revenue", xbrl_concept="cost_of_revenue",
            values={"FY2023": _sv(5000.0), "FY2024": _sv(5500.0)}),
    ]
    return FinancialStatements(
        balance_sheet=FinancialStatement(
            statement_type="balance_sheet",
            periods=["FY2023", "FY2024"],
            line_items=balance_items,
        ),
        income_statement=FinancialStatement(
            statement_type="income",
            periods=["FY2023", "FY2024"],
            line_items=income_items,
        ),
    )


class TestFullData:
    """Test with complete data: all 5 metrics should compute."""

    def test_all_metrics_computed(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = _make_full_statements()
        result, report = compute_balance_sheet_forensics(stmts)

        assert isinstance(result, BalanceSheetForensics)
        assert result.goodwill_to_assets.value is not None
        assert result.intangible_concentration.value is not None
        assert result.off_balance_sheet_ratio.value is not None
        assert result.cash_conversion_cycle.value is not None
        assert result.working_capital_volatility.value is not None

    def test_goodwill_to_assets_value(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = _make_full_statements()
        result, _ = compute_balance_sheet_forensics(stmts)
        # 2500 / 12000 = 0.2083...
        assert result.goodwill_to_assets.value == pytest.approx(0.2083, abs=0.001)

    def test_intangible_concentration_value(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = _make_full_statements()
        result, _ = compute_balance_sheet_forensics(stmts)
        # (2500 + 1200) / 12000 = 0.3083...
        assert result.intangible_concentration.value == pytest.approx(0.3083, abs=0.001)

    def test_off_balance_sheet_ratio_value(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = _make_full_statements()
        result, _ = compute_balance_sheet_forensics(stmts)
        # 600 / 12000 = 0.05
        assert result.off_balance_sheet_ratio.value == pytest.approx(0.05, abs=0.001)

    def test_extraction_report_shows_coverage(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = _make_full_statements()
        _, report = compute_balance_sheet_forensics(stmts)
        assert report.coverage_pct == 100.0
        assert len(report.found_fields) == 5

    def test_confidence_is_high_from_xbrl(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = _make_full_statements()
        result, _ = compute_balance_sheet_forensics(stmts)
        assert result.goodwill_to_assets.confidence == Confidence.HIGH


class TestMissingData:
    """Test graceful handling of missing data."""

    def test_missing_goodwill_gives_insufficient_data(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = _make_full_statements()
        # Remove goodwill from balance sheet
        assert stmts.balance_sheet is not None
        stmts.balance_sheet.line_items = [
            item for item in stmts.balance_sheet.line_items
            if item.xbrl_concept != "goodwill"
        ]
        result, report = compute_balance_sheet_forensics(stmts)
        assert result.goodwill_to_assets.zone == "insufficient_data"
        # Other metrics should still compute
        assert result.off_balance_sheet_ratio.value is not None

    def test_all_none_returns_defaults(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        stmts = FinancialStatements()
        result, report = compute_balance_sheet_forensics(stmts)
        assert result.goodwill_to_assets.zone == "insufficient_data"
        assert result.intangible_concentration.zone == "insufficient_data"
        assert result.off_balance_sheet_ratio.zone == "insufficient_data"
        assert result.cash_conversion_cycle.zone == "insufficient_data"
        assert result.working_capital_volatility.zone == "insufficient_data"
        assert report.coverage_pct == 0.0


class TestZoneThresholds:
    """Test zone classification for various threshold values."""

    def test_goodwill_danger_zone(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        # GW/TA = 4500/10000 = 0.45 -> danger (>0.40)
        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
                        values={"FY2024": _sv(4500.0)}),
                    FinancialLineItem(label="Total Assets", xbrl_concept="total_assets",
                        values={"FY2024": _sv(10000.0)}),
                ],
            ),
        )
        result, _ = compute_balance_sheet_forensics(stmts)
        assert result.goodwill_to_assets.zone == "danger"

    def test_goodwill_warning_zone(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        # GW/TA = 2500/10000 = 0.25 -> warning (>0.20)
        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
                        values={"FY2024": _sv(2500.0)}),
                    FinancialLineItem(label="Total Assets", xbrl_concept="total_assets",
                        values={"FY2024": _sv(10000.0)}),
                ],
            ),
        )
        result, _ = compute_balance_sheet_forensics(stmts)
        assert result.goodwill_to_assets.zone == "warning"

    def test_goodwill_safe_zone(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        # GW/TA = 1000/10000 = 0.10 -> safe (<=0.20)
        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
                        values={"FY2024": _sv(1000.0)}),
                    FinancialLineItem(label="Total Assets", xbrl_concept="total_assets",
                        values={"FY2024": _sv(10000.0)}),
                ],
            ),
        )
        result, _ = compute_balance_sheet_forensics(stmts)
        assert result.goodwill_to_assets.zone == "safe"

    def test_goodwill_trend_deteriorating(self) -> None:
        from do_uw.stages.analyze.forensic_balance_sheet import (
            compute_balance_sheet_forensics,
        )

        # GW/TA prior = 1000/10000 = 0.10, current = 2000/10000 = 0.20
        # Increase of 10pp -> deteriorating
        stmts = FinancialStatements(
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Goodwill", xbrl_concept="goodwill",
                        values={"FY2023": _sv(1000.0), "FY2024": _sv(2000.0)}),
                    FinancialLineItem(label="Total Assets", xbrl_concept="total_assets",
                        values={"FY2023": _sv(10000.0), "FY2024": _sv(10000.0)}),
                ],
            ),
        )
        result, _ = compute_balance_sheet_forensics(stmts)
        assert result.goodwill_to_assets.trend == "deteriorating"
