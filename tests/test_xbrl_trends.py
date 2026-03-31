"""Tests for XBRL quarterly trend computation.

Covers QoQ, YoY, acceleration, sequential pattern detection,
and the integrated compute_trends / compute_all_trends functions.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import QuarterlyPeriod, QuarterlyStatements
from do_uw.stages.extract.xbrl_trends import (
    TrendResult,
    compute_acceleration,
    compute_all_trends,
    compute_qoq,
    compute_trends,
    compute_yoy,
    detect_sequential_pattern,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime.now(tz=UTC)


def _sv(val: float) -> SourcedValue[float]:
    """Shortcut to build a SourcedValue for testing."""
    return SourcedValue(
        value=val,
        source="TEST",
        confidence=Confidence.HIGH,
        as_of=_NOW,
    )


def _make_quarter(
    fy: int,
    fq: int,
    income: dict[str, float] | None = None,
    balance: dict[str, float] | None = None,
    cash_flow: dict[str, float] | None = None,
) -> QuarterlyPeriod:
    """Build a minimal QuarterlyPeriod for tests."""
    return QuarterlyPeriod(
        fiscal_year=fy,
        fiscal_quarter=fq,
        fiscal_label=f"Q{fq} FY{fy}",
        calendar_period=f"CY{fy}Q{fq}",
        period_end=f"{fy}-{fq * 3:02d}-28",
        income={k: _sv(v) for k, v in (income or {}).items()},
        balance={k: _sv(v) for k, v in (balance or {}).items()},
        cash_flow={k: _sv(v) for k, v in (cash_flow or {}).items()},
    )


# ---------------------------------------------------------------------------
# Test 1: compute_qoq with normal values
# ---------------------------------------------------------------------------


class TestComputeQoQ:
    def test_normal_values(self) -> None:
        """QoQ with [100, 110, 105, 120] => correct sequential % changes.

        values[0] is most recent. QoQ[0] = None (no prior).
        QoQ[1] = (110 - 105) / |105| * 100 = 4.76...
        QoQ[2] = (105 - 120) / |120| * 100 = -12.5
        QoQ[3] = None (no prior for oldest)
        """
        result = compute_qoq([100, 110, 105, 120])
        assert result[0] is None  # most recent has no prior
        assert result[-1] is None  # oldest has no prior
        # 110 vs 105: (110-105)/|105|*100
        assert result[1] == pytest.approx(4.7619, rel=1e-2)
        # 105 vs 120: (105-120)/|120|*100
        assert result[2] == pytest.approx(-12.5, rel=1e-2)

    # Test 2: handles None values
    def test_none_values(self) -> None:
        result = compute_qoq([100, None, 105, 120])
        assert result[0] is None  # no valid prior (None)
        assert result[1] is None  # current is None
        assert result[2] == pytest.approx(-12.5, rel=1e-2)
        assert result[3] is None  # oldest

    # Test 3: handles zero prior value (denominator)
    def test_zero_prior(self) -> None:
        # [100, 50, 0] -- values[2]=0 is denominator for result[1]
        result = compute_qoq([100, 50, 0])
        assert result[0] is None  # most recent endpoint
        assert result[1] is None  # 50 vs 0 => zero denominator
        assert result[2] is None  # oldest


# ---------------------------------------------------------------------------
# Test 4-5: compute_yoy
# ---------------------------------------------------------------------------


class TestComputeYoY:
    def _quarters_8(self) -> list[QuarterlyPeriod]:
        """8 quarters: Q4 FY2025 down to Q1 FY2024, most recent first."""
        quarters = []
        for fy, fq in [
            (2025, 4),
            (2025, 3),
            (2025, 2),
            (2025, 1),
            (2024, 4),
            (2024, 3),
            (2024, 2),
            (2024, 1),
        ]:
            quarters.append(
                _make_quarter(
                    fy,
                    fq,
                    income={"revenue": fy * 100 + fq * 10},
                )
            )
        return quarters

    def test_yoy_matches_same_quarter(self) -> None:
        """Q4 FY2025 matches Q4 FY2024, Q3 FY2025 matches Q3 FY2024, etc."""
        quarters = self._quarters_8()
        result = compute_yoy(quarters, "revenue", "income")
        # Q4 FY2025 (202540) vs Q4 FY2024 (202440): (202540-202440)/|202440|*100
        assert result[0] is not None
        assert result[0] == pytest.approx(
            (202540 - 202440) / abs(202440) * 100, rel=1e-3
        )
        # Q1 FY2024 (202410) has no prior Q1 FY2023
        assert result[7] is None

    def test_yoy_no_prior_year(self) -> None:
        """Only 4 quarters => no YoY possible for any."""
        quarters = self._quarters_8()[:4]  # Only FY2025
        result = compute_yoy(quarters, "revenue", "income")
        assert all(v is None for v in result)


# ---------------------------------------------------------------------------
# Test 6: compute_acceleration
# ---------------------------------------------------------------------------


class TestComputeAcceleration:
    def test_speeding_up(self) -> None:
        """Most recent QoQ > prior QoQ => positive acceleration."""
        # qoq_changes[0]=None, [1]=10.0, [2]=5.0
        result = compute_acceleration([None, 10.0, 5.0])
        assert result is not None
        assert result == pytest.approx(5.0)  # 10 - 5

    def test_slowing_down(self) -> None:
        result = compute_acceleration([None, 3.0, 8.0])
        assert result is not None
        assert result == pytest.approx(-5.0)  # 3 - 8

    def test_insufficient_data(self) -> None:
        result = compute_acceleration([None])
        assert result is None


# ---------------------------------------------------------------------------
# Test 7-10: detect_sequential_pattern
# ---------------------------------------------------------------------------


class TestDetectSequentialPattern:
    def test_compression_4_consecutive(self) -> None:
        """4+ consecutive negative QoQ on margin concept => 'compression'."""
        qoq = [None, -2.0, -3.0, -1.5, -0.5, 2.0]
        pattern, count = detect_sequential_pattern(qoq, "gross_margin")
        assert pattern == "compression"
        assert count >= 4

    def test_deceleration_revenue_growth(self) -> None:
        """4+ consecutive negative on revenue_growth => 'deceleration'."""
        qoq = [None, -1.0, -2.0, -3.0, -4.0]
        pattern, count = detect_sequential_pattern(qoq, "revenue_growth")
        assert pattern == "deceleration"
        assert count >= 4

    def test_deterioration_cash_flow(self) -> None:
        """4+ consecutive negative on operating_cash_flow => 'deterioration'."""
        qoq = [None, -5.0, -3.0, -8.0, -1.0, 2.0]
        pattern, count = detect_sequential_pattern(qoq, "operating_cash_flow")
        assert pattern == "deterioration"
        assert count >= 4

    def test_fewer_than_threshold(self) -> None:
        """Only 3 consecutive negatives => no pattern."""
        qoq = [None, -2.0, -3.0, -1.5, 2.0, -0.5]
        pattern, count = detect_sequential_pattern(qoq, "gross_margin")
        assert pattern is None
        assert count == 0


# ---------------------------------------------------------------------------
# Test 11: compute_trends (integrated)
# ---------------------------------------------------------------------------


class TestComputeTrends:
    def test_integrates_all_metrics(self) -> None:
        """compute_trends returns TrendResult with QoQ, YoY, accel, pattern."""
        quarters = []
        for fy, fq in [
            (2025, 4),
            (2025, 3),
            (2025, 2),
            (2025, 1),
            (2024, 4),
            (2024, 3),
            (2024, 2),
            (2024, 1),
        ]:
            quarters.append(
                _make_quarter(
                    fy,
                    fq,
                    income={"revenue": float(fy * 100 + fq * 10)},
                )
            )

        result = compute_trends(quarters, "revenue", "income")
        assert isinstance(result, TrendResult)
        assert result.concept == "revenue"
        assert len(result.qoq_changes) == 8
        assert len(result.yoy_changes) == 8
        # acceleration should be computable (8 quarters of data)
        # pattern may or may not exist depending on values


# ---------------------------------------------------------------------------
# Test 12: compute_all_trends
# ---------------------------------------------------------------------------


class TestComputeAllTrends:
    def test_processes_all_concepts(self) -> None:
        """compute_all_trends returns dict keyed by concept for every concept with 2+ quarters."""
        quarters = []
        for fy, fq in [(2025, 2), (2025, 1)]:
            quarters.append(
                _make_quarter(
                    fy,
                    fq,
                    income={"revenue": float(fy * 100 + fq * 10)},
                    balance={"total_assets": float(fy * 1000 + fq * 100)},
                )
            )

        qs = QuarterlyStatements(
            quarters=quarters,
            concepts_resolved=2,
            concepts_attempted=2,
        )
        result = compute_all_trends(qs)
        assert "revenue" in result
        assert "total_assets" in result
        assert isinstance(result["revenue"], TrendResult)
        assert isinstance(result["total_assets"], TrendResult)
