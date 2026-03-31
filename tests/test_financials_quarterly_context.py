"""Tests for quarterly trend context builder (Phase 73)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from do_uw.stages.render.context_builders.financials_quarterly import (
    build_quarterly_trend_context,
)


def _make_quarter(fiscal_year: int, fiscal_quarter: int, income: dict | None = None, balance: dict | None = None, cash_flow: dict | None = None):
    """Create a mock QuarterlyPeriod."""
    q = MagicMock()
    q.fiscal_year = fiscal_year
    q.fiscal_quarter = fiscal_quarter
    q.fiscal_label = f"Q{fiscal_quarter} FY{fiscal_year}"
    q.calendar_period = f"CY{fiscal_year}Q{fiscal_quarter}"
    q.period_end = f"{fiscal_year}-03-31"
    q.income = income or {}
    q.balance = balance or {}
    q.cash_flow = cash_flow or {}
    return q


def _sv(value: float) -> MagicMock:
    """Create a mock SourcedValue."""
    sv = MagicMock()
    sv.value = value
    return sv


class TestBuildQuarterlyTrendContextEmpty:
    """Test graceful fallback when data is missing."""

    def test_no_extracted(self):
        state = MagicMock()
        state.extracted = None
        result = build_quarterly_trend_context(state)
        assert result["has_data"] is False

    def test_no_financials(self):
        state = MagicMock()
        state.extracted.financials = None
        result = build_quarterly_trend_context(state)
        assert result["has_data"] is False

    def test_no_quarterly_xbrl(self):
        state = MagicMock()
        state.extracted.financials.quarterly_xbrl = None
        result = build_quarterly_trend_context(state)
        assert result["has_data"] is False

    def test_empty_quarters(self):
        state = MagicMock()
        state.extracted.financials.quarterly_xbrl.quarters = []
        result = build_quarterly_trend_context(state)
        assert result["has_data"] is False


class TestBuildQuarterlyTrendContextWithData:
    """Test context building with mock quarterly data."""

    def _make_state(self) -> MagicMock:
        state = MagicMock()
        quarters = []
        for i in range(8):
            fy = 2025 if i < 4 else 2024
            fq = 4 - (i % 4)
            rev = 1000.0 + i * 50  # Descending revenue (most recent = 1000)
            ni = 100.0 + i * 10
            q = _make_quarter(
                fy, fq,
                income={
                    "Revenues": _sv(rev),
                    "NetIncomeLoss": _sv(ni),
                },
                balance={
                    "Assets": _sv(5000.0 + i * 100),
                },
                cash_flow={
                    "NetCashProvidedByUsedInOperatingActivities": _sv(200.0 + i * 20),
                    "PaymentsToAcquirePropertyPlantAndEquipment": _sv(50.0),
                },
            )
            quarters.append(q)
        state.extracted.financials.quarterly_xbrl.quarters = quarters
        return state

    def test_has_data(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        assert result["has_data"] is True

    def test_periods_count(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        assert len(result["periods"]) == 8

    def test_summary_strip(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        assert len(result["summary_strip"]) == 4
        labels = [s["label"] for s in result["summary_strip"]]
        assert "Revenue" in labels
        assert "Net Income" in labels

    def test_income_metrics(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        assert len(result["income_metrics"]) >= 2  # Revenue + Net Income at minimum

    def test_balance_metrics(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        assert len(result["balance_metrics"]) >= 1  # Total Assets

    def test_cashflow_metrics(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        assert len(result["cashflow_metrics"]) >= 1  # Operating CF

    @patch("do_uw.stages.render.context_builders.financials_quarterly.render_sparkline")
    def test_sparkline_called(self, mock_spark):
        mock_spark.return_value = "<svg>mock</svg>"
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        assert mock_spark.called

    def test_yoy_direction(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        # Revenue is descending from older to newer in our mock, so YoY should show direction
        for metric in result["income_metrics"]:
            assert metric["yoy_direction"] in ("up", "down", "flat")

    def test_metric_cells_match_periods(self):
        state = self._make_state()
        result = build_quarterly_trend_context(state)
        n_periods = len(result["periods"])
        for metric in result["income_metrics"]:
            assert len(metric["cells"]) == n_periods
