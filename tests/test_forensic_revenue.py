"""Tests for revenue quality forensic analysis module.

Validates compute_revenue_forensics produces correct metrics,
zones, and handles missing data gracefully.
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
from do_uw.models.xbrl_forensics import ForensicMetric, RevenueForensics


def _sv(value: float, confidence: Confidence = Confidence.HIGH) -> SourcedValue[float]:
    """Create a test SourcedValue."""
    return SourcedValue(
        value=value,
        source="test-xbrl",
        confidence=confidence,
        as_of=datetime(2025, 1, 1, tzinfo=UTC),
    )


def _make_full_statements() -> FinancialStatements:
    """Create FinancialStatements with full data for all 4 metrics."""
    income_items = [
        FinancialLineItem(label="Revenue", xbrl_concept="revenue",
            values={"FY2023": _sv(8000.0), "FY2024": _sv(9000.0)}),
        FinancialLineItem(label="Gross Profit", xbrl_concept="gross_profit",
            values={"FY2023": _sv(3200.0), "FY2024": _sv(3400.0)}),
    ]
    balance_items = [
        FinancialLineItem(label="AR", xbrl_concept="accounts_receivable",
            values={"FY2023": _sv(1200.0), "FY2024": _sv(1500.0)}),
        FinancialLineItem(label="Deferred Revenue", xbrl_concept="deferred_revenue",
            values={"FY2023": _sv(500.0), "FY2024": _sv(600.0)}),
    ]
    cash_items = [
        FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
            values={"FY2023": _sv(1200.0), "FY2024": _sv(1350.0)}),
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
            line_items=cash_items,
        ),
    )


class TestFullData:
    """Test with complete data: all 4 metrics should compute."""

    def test_all_metrics_computed(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        stmts = _make_full_statements()
        result, report = compute_revenue_forensics(stmts)

        assert isinstance(result, RevenueForensics)
        assert result.deferred_revenue_divergence.value is not None
        assert result.channel_stuffing_indicator.value is not None
        assert result.margin_compression.value is not None
        assert result.ocf_revenue_ratio.value is not None

    def test_ocf_revenue_ratio_value(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        stmts = _make_full_statements()
        result, _ = compute_revenue_forensics(stmts)
        # 1350 / 9000 = 0.15
        assert result.ocf_revenue_ratio.value == pytest.approx(0.15, abs=0.001)

    def test_extraction_report_shows_coverage(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        stmts = _make_full_statements()
        _, report = compute_revenue_forensics(stmts)
        assert report.coverage_pct == 100.0
        assert len(report.found_fields) == 4


class TestChannelStuffing:
    """Test channel stuffing indicator."""

    def test_ar_growing_3x_revenue_is_danger(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        # AR grows 100% (500->1000), revenue grows 10% (1000->1100)
        # ratio = 1.0 / 0.1 = 10.0 -> danger
        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={"FY2023": _sv(1000.0), "FY2024": _sv(1100.0)}),
                    FinancialLineItem(label="GP", xbrl_concept="gross_profit",
                        values={"FY2023": _sv(400.0), "FY2024": _sv(440.0)}),
                ],
            ),
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="AR", xbrl_concept="accounts_receivable",
                        values={"FY2023": _sv(500.0), "FY2024": _sv(1000.0)}),
                ],
            ),
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
                        values={"FY2024": _sv(100.0)}),
                ],
            ),
        )
        result, _ = compute_revenue_forensics(stmts)
        assert result.channel_stuffing_indicator.zone == "danger"


class TestMarginCompression:
    """Test margin compression detection."""

    def test_four_declining_periods_is_danger(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        # 4 periods of declining gross margin
        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2021", "FY2022", "FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={
                            "FY2021": _sv(1000.0), "FY2022": _sv(1050.0),
                            "FY2023": _sv(1100.0), "FY2024": _sv(1150.0),
                        }),
                    FinancialLineItem(label="GP", xbrl_concept="gross_profit",
                        values={
                            "FY2021": _sv(500.0), "FY2022": _sv(480.0),
                            "FY2023": _sv(450.0), "FY2024": _sv(400.0),
                        }),
                ],
            ),
        )
        result, _ = compute_revenue_forensics(stmts)
        assert result.margin_compression.zone == "danger"
        assert result.margin_compression.trend == "deteriorating"


class TestOCFRevenue:
    """Test OCF/revenue ratio zone classification."""

    def test_danger_zone(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        # OCF/revenue = 30/1000 = 0.03 -> danger (<0.05)
        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={"FY2024": _sv(1000.0)}),
                ],
            ),
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
                        values={"FY2024": _sv(30.0)}),
                ],
            ),
        )
        result, _ = compute_revenue_forensics(stmts)
        assert result.ocf_revenue_ratio.zone == "danger"

    def test_warning_zone(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        # OCF/revenue = 80/1000 = 0.08 -> warning (0.05-0.10)
        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={"FY2024": _sv(1000.0)}),
                ],
            ),
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
                        values={"FY2024": _sv(80.0)}),
                ],
            ),
        )
        result, _ = compute_revenue_forensics(stmts)
        assert result.ocf_revenue_ratio.zone == "warning"

    def test_safe_zone(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        # OCF/revenue = 150/1000 = 0.15 -> safe (>=0.10)
        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={"FY2024": _sv(1000.0)}),
                ],
            ),
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
                        values={"FY2024": _sv(150.0)}),
                ],
            ),
        )
        result, _ = compute_revenue_forensics(stmts)
        assert result.ocf_revenue_ratio.zone == "safe"


class TestMissingData:
    """Test graceful handling of missing data."""

    def test_missing_deferred_revenue(self) -> None:
        from do_uw.stages.analyze.forensic_revenue import (
            compute_revenue_forensics,
        )

        # No deferred revenue -> that metric insufficient_data
        stmts = FinancialStatements(
            income_statement=FinancialStatement(
                statement_type="income",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="Revenue", xbrl_concept="revenue",
                        values={"FY2023": _sv(1000.0), "FY2024": _sv(1100.0)}),
                    FinancialLineItem(label="GP", xbrl_concept="gross_profit",
                        values={"FY2023": _sv(400.0), "FY2024": _sv(440.0)}),
                ],
            ),
            balance_sheet=FinancialStatement(
                statement_type="balance_sheet",
                periods=["FY2023", "FY2024"],
                line_items=[
                    FinancialLineItem(label="AR", xbrl_concept="accounts_receivable",
                        values={"FY2023": _sv(200.0), "FY2024": _sv(250.0)}),
                ],
            ),
            cash_flow=FinancialStatement(
                statement_type="cash_flow",
                periods=["FY2024"],
                line_items=[
                    FinancialLineItem(label="OCF", xbrl_concept="operating_cash_flow",
                        values={"FY2024": _sv(120.0)}),
                ],
            ),
        )
        result, report = compute_revenue_forensics(stmts)
        assert result.deferred_revenue_divergence.zone == "insufficient_data"
        # Other metrics should still work
        assert result.ocf_revenue_ratio.value is not None
        assert result.channel_stuffing_indicator.value is not None
