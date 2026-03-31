"""Tests for stock drop time-decay weighting.

Verifies exponential decay with 180-day half-life for D&O relevance scoring.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from do_uw.stages.extract.stock_drop_decay import (
    apply_decay_weights,
    compute_decay_weight,
    compute_decay_weighted_severity,
)
from do_uw.models.market_events import StockDropEvent
from do_uw.models.common import SourcedValue, Confidence


REF_DATE = date(2026, 3, 9)
AS_OF = datetime(2026, 3, 9, tzinfo=UTC)


class TestComputeDecayWeight:
    """Tests for compute_decay_weight."""

    def test_today_returns_1(self) -> None:
        """Drop on reference date has full weight."""
        w = compute_decay_weight("2026-03-09", reference_date=REF_DATE)
        assert w == pytest.approx(1.0, abs=0.01)

    def test_180_days_returns_half(self) -> None:
        """Drop 180 days ago (one half-life) returns ~0.50."""
        # 180 days before 2026-03-09 is 2025-09-10 (approx)
        d = date(2025, 9, 11)  # ~180 days before ref
        days_ago = (REF_DATE - d).days
        w = compute_decay_weight(d.isoformat(), reference_date=REF_DATE)
        assert w == pytest.approx(0.50, abs=0.05)

    def test_360_days_returns_quarter(self) -> None:
        """Drop 360 days ago (two half-lives) returns ~0.25."""
        d = date(2025, 3, 14)  # ~360 days before ref
        w = compute_decay_weight(d.isoformat(), reference_date=REF_DATE)
        assert w == pytest.approx(0.25, abs=0.05)

    def test_future_date_clamped_to_1(self) -> None:
        """Future drop date returns 1.0 (clamped via max(days_ago, 0))."""
        w = compute_decay_weight("2026-04-01", reference_date=REF_DATE)
        assert w == pytest.approx(1.0, abs=0.01)

    def test_none_returns_0(self) -> None:
        """None date returns 0.0."""
        w = compute_decay_weight(None, reference_date=REF_DATE)
        assert w == 0.0

    def test_invalid_date_returns_0(self) -> None:
        """Invalid date string returns 0.0."""
        w = compute_decay_weight("not-a-date", reference_date=REF_DATE)
        assert w == 0.0

    def test_empty_string_returns_0(self) -> None:
        """Empty string returns 0.0."""
        w = compute_decay_weight("", reference_date=REF_DATE)
        assert w == 0.0

    def test_monotonically_decreasing(self) -> None:
        """Weight decreases as date gets older."""
        w1 = compute_decay_weight("2026-02-09", reference_date=REF_DATE)  # 28 days
        w2 = compute_decay_weight("2025-12-09", reference_date=REF_DATE)  # 90 days
        w3 = compute_decay_weight("2025-06-09", reference_date=REF_DATE)  # 273 days
        assert w1 > w2 > w3 > 0.0


class TestComputeDecayWeightedSeverity:
    """Tests for compute_decay_weighted_severity."""

    def test_basic_computation(self) -> None:
        """abs(drop_pct) * decay_weight."""
        result = compute_decay_weighted_severity(-15.0, 0.5)
        assert result == pytest.approx(7.5, abs=0.01)

    def test_full_weight(self) -> None:
        """Full weight preserves magnitude."""
        result = compute_decay_weighted_severity(-20.0, 1.0)
        assert result == pytest.approx(20.0, abs=0.01)

    def test_zero_weight(self) -> None:
        """Zero weight yields zero severity."""
        result = compute_decay_weighted_severity(-20.0, 0.0)
        assert result == pytest.approx(0.0, abs=0.01)


class TestApplyDecayWeights:
    """Tests for apply_decay_weights."""

    def _make_drop(self, date_str: str, drop_pct: float) -> StockDropEvent:
        return StockDropEvent(
            date=SourcedValue(value=date_str, source="test", confidence=Confidence.HIGH, as_of=AS_OF),
            drop_pct=SourcedValue(value=drop_pct, source="test", confidence=Confidence.HIGH, as_of=AS_OF),
        )

    def test_sets_decay_fields(self) -> None:
        """Decay weight and severity are set on each drop."""
        drops = [self._make_drop("2026-03-09", -10.0)]
        result = apply_decay_weights(drops, reference_date=REF_DATE)
        assert result[0].decay_weight is not None
        assert result[0].decay_weight == pytest.approx(1.0, abs=0.01)
        assert result[0].decay_weighted_severity is not None
        assert result[0].decay_weighted_severity == pytest.approx(10.0, abs=0.1)

    def test_sorted_by_severity_descending(self) -> None:
        """More recent same-magnitude drops rank higher."""
        drops = [
            self._make_drop("2025-06-09", -20.0),  # old, ~273 days
            self._make_drop("2026-01-09", -20.0),  # recent, ~59 days
        ]
        result = apply_decay_weights(drops, reference_date=REF_DATE)
        assert result[0].decay_weighted_severity > result[1].decay_weighted_severity  # type: ignore[operator]

    def test_skips_drops_without_date(self) -> None:
        """Drops with no date get decay_weight=0.0."""
        drop = StockDropEvent(
            drop_pct=SourcedValue(value=-10.0, source="test", confidence=Confidence.HIGH, as_of=AS_OF),
        )
        result = apply_decay_weights([drop], reference_date=REF_DATE)
        assert result[0].decay_weight == 0.0

    def test_skips_drops_without_drop_pct(self) -> None:
        """Drops with no drop_pct get severity 0."""
        drop = StockDropEvent(
            date=SourcedValue(value="2026-03-09", source="test", confidence=Confidence.HIGH, as_of=AS_OF),
        )
        result = apply_decay_weights([drop], reference_date=REF_DATE)
        assert result[0].decay_weight is not None
        assert result[0].decay_weighted_severity == pytest.approx(0.0, abs=0.01)
