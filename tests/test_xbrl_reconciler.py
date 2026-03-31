"""Tests for XBRL/LLM reconciler -- XBRL-wins precedence + yfinance cross-validation.

Covers:
- XBRL always wins when both XBRL and LLM have a value
- LLM fallback at MEDIUM confidence when XBRL absent
- Divergence logging with magnitude and direction
- yfinance cross-validation with 7-day date tolerance
- ReconciliationReport aggregate statistics
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import QuarterlyPeriod, QuarterlyStatements, QuarterlyUpdate
from do_uw.stages.extract.xbrl_llm_reconciler import (
    ReconciliationReport,
    cross_validate_yfinance,
    reconcile_quarterly,
    reconcile_value,
)


def _sv(value: float, source: str = "XBRL", confidence: str = "HIGH") -> SourcedValue[float]:
    """Helper to build a SourcedValue quickly."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=Confidence(confidence),
        as_of=datetime(2026, 1, 1, tzinfo=UTC),
    )


# ---------------------------------------------------------------------------
# Test 1: XBRL wins when both present
# ---------------------------------------------------------------------------
class TestReconcileValue:
    def test_xbrl_wins_when_both_present(self) -> None:
        xbrl = _sv(1000.0, "XBRL CIK123")
        result, msgs = reconcile_value(xbrl, 999.0, "revenue", "Q1 FY2025")
        assert result is not None
        assert result.value == 1000.0
        assert result.confidence == Confidence.HIGH

    # Test 2: LLM fallback at MEDIUM confidence
    def test_llm_fallback_when_xbrl_absent(self) -> None:
        result, msgs = reconcile_value(None, 500.0, "revenue", "Q1 FY2025")
        assert result is not None
        assert result.value == 500.0
        assert result.confidence == Confidence.MEDIUM
        assert any("fallback" in m.lower() for m in msgs)

    # Test 3: Both absent returns None
    def test_both_absent_returns_none(self) -> None:
        result, msgs = reconcile_value(None, None, "revenue", "Q1 FY2025")
        assert result is None
        assert len(msgs) == 0

    # Test 4: Divergence message includes concept, period, values, % diff
    def test_divergence_message_details(self) -> None:
        xbrl = _sv(1000.0, "XBRL CIK123")
        result, msgs = reconcile_value(xbrl, 1200.0, "revenue", "Q1 FY2025")
        assert len(msgs) == 1
        msg = msgs[0]
        assert "revenue" in msg
        assert "Q1 FY2025" in msg
        assert "1000" in msg or "1,000" in msg
        assert "1200" in msg or "1,200" in msg
        assert "%" in msg

    # Test 5: No divergence when values within 1%
    def test_no_divergence_within_threshold(self) -> None:
        xbrl = _sv(1000.0, "XBRL CIK123")
        result, msgs = reconcile_value(xbrl, 1005.0, "revenue", "Q1 FY2025")
        assert result is not None
        assert result.value == 1000.0
        assert len(msgs) == 0


# ---------------------------------------------------------------------------
# Test 6-8: yfinance cross-validation
# ---------------------------------------------------------------------------
class TestCrossValidateYfinance:
    def test_matches_periods_within_7day_tolerance(self) -> None:
        quarters = QuarterlyStatements(
            quarters=[
                QuarterlyPeriod(
                    fiscal_year=2025,
                    fiscal_quarter=1,
                    fiscal_label="Q1 FY2025",
                    calendar_period="CY2024Q4",
                    period_end="2024-12-28",
                    income={"revenue": _sv(1000.0)},
                    balance={},
                    cash_flow={},
                ),
            ],
        )
        yf_data = [
            {
                "period_end": "2024-12-31",
                "Total Revenue": 1050.0,
                "Net Income": 200.0,
            },
        ]
        report = cross_validate_yfinance(quarters, yf_data)
        assert report.total_comparisons >= 1

    def test_logs_discrepancy_over_threshold(self) -> None:
        quarters = QuarterlyStatements(
            quarters=[
                QuarterlyPeriod(
                    fiscal_year=2025,
                    fiscal_quarter=1,
                    fiscal_label="Q1 FY2025",
                    calendar_period="CY2024Q4",
                    period_end="2024-12-28",
                    income={"revenue": _sv(1000.0), "net_income": _sv(100.0)},
                    balance={},
                    cash_flow={},
                ),
            ],
        )
        yf_data = [
            {
                "period_end": "2024-12-31",
                "Total Revenue": 1200.0,
                "Net Income": 100.0,
            },
        ]
        report = cross_validate_yfinance(quarters, yf_data)
        assert report.divergences >= 1
        assert any("revenue" in m.lower() for m in report.messages)

    def test_handles_no_yfinance_match(self) -> None:
        quarters = QuarterlyStatements(
            quarters=[
                QuarterlyPeriod(
                    fiscal_year=2025,
                    fiscal_quarter=1,
                    fiscal_label="Q1 FY2025",
                    calendar_period="CY2024Q4",
                    period_end="2024-12-28",
                    income={"revenue": _sv(1000.0)},
                    balance={},
                    cash_flow={},
                ),
            ],
        )
        # yfinance date far away -- no match within 7 days
        yf_data = [
            {
                "period_end": "2024-06-30",
                "Total Revenue": 900.0,
            },
        ]
        report = cross_validate_yfinance(quarters, yf_data)
        assert report.total_comparisons == 0
        assert report.divergences == 0


# ---------------------------------------------------------------------------
# Test 9: ReconciliationReport tracks aggregates
# ---------------------------------------------------------------------------
class TestReconciliationReport:
    def test_report_tracks_aggregates(self) -> None:
        quarters = QuarterlyStatements(
            quarters=[
                QuarterlyPeriod(
                    fiscal_year=2025,
                    fiscal_quarter=1,
                    fiscal_label="Q1 FY2025",
                    calendar_period="CY2024Q4",
                    period_end="2024-12-28",
                    income={"revenue": _sv(1000.0), "net_income": _sv(100.0)},
                    balance={},
                    cash_flow={},
                ),
            ],
        )
        llm_updates = [
            QuarterlyUpdate(
                quarter="Q1 FY2025",
                period_end="2024-12-28",
                filing_date="2025-01-30",
                revenue=_sv(1200.0, "10-Q LLM", "MEDIUM"),
                net_income=_sv(100.5, "10-Q LLM", "MEDIUM"),
                eps=None,
            ),
        ]
        report = reconcile_quarterly(quarters, llm_updates)
        assert report.total_comparisons >= 2
        assert report.xbrl_wins >= 2
        # revenue diverges >1%, net_income within 1%
        assert report.divergences >= 1
        assert len(report.messages) >= 1
