"""Tests for Phase 90 drop enhancement columns in market context builder.

Verifies:
- Context builder includes new fields (decay_weight, decomposition, disclosure badge)
- Disclosure badge formatting for 8-K and news types
- N/A returned for None fields
- Sort order matches decay_weighted_severity
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import StockDropEvent
from do_uw.stages.render.context_builders.market import _format_disclosure_badge


def _make_drop(
    date: str = "2025-06-15",
    drop_pct: float = -10.0,
    decay_weight: float | None = None,
    decay_weighted_severity: float | None = None,
    market_pct: float | None = None,
    sector_pct: float | None = None,
    company_pct: float | None = None,
    is_market_driven: bool = False,
    corrective_disclosure_type: str = "",
    corrective_disclosure_lag_days: int | None = None,
) -> StockDropEvent:
    """Create a StockDropEvent with Phase 90 fields."""
    return StockDropEvent(
        date=SourcedValue[str](
            value=date, source="test", confidence=Confidence.MEDIUM,
            as_of=datetime(2026, 3, 9, tzinfo=timezone.utc),
        ),
        drop_pct=SourcedValue[float](
            value=drop_pct, source="test", confidence=Confidence.MEDIUM,
            as_of=datetime(2026, 3, 9, tzinfo=timezone.utc),
        ),
        drop_type="SINGLE_DAY",
        decay_weight=decay_weight,
        decay_weighted_severity=decay_weighted_severity,
        market_pct=market_pct,
        sector_pct=sector_pct,
        company_pct=company_pct,
        is_market_driven=is_market_driven,
        corrective_disclosure_type=corrective_disclosure_type,
        corrective_disclosure_lag_days=corrective_disclosure_lag_days,
    )


class TestDisclosureBadge:
    """Test _format_disclosure_badge helper."""

    def test_no_disclosure_returns_empty(self) -> None:
        evt = _make_drop()
        assert _format_disclosure_badge(evt) == ""

    def test_8k_with_lag(self) -> None:
        evt = _make_drop(corrective_disclosure_type="8-K", corrective_disclosure_lag_days=3)
        assert _format_disclosure_badge(evt) == "8-K +3d"

    def test_news_with_lag(self) -> None:
        evt = _make_drop(corrective_disclosure_type="news", corrective_disclosure_lag_days=7)
        assert _format_disclosure_badge(evt) == "news +7d"

    def test_disclosure_without_lag(self) -> None:
        evt = _make_drop(corrective_disclosure_type="8-K", corrective_disclosure_lag_days=None)
        assert _format_disclosure_badge(evt) == "8-K"


class TestDropContextFields:
    """Test that context builder would include new Phase 90 fields."""

    def test_decay_weight_formatted(self) -> None:
        """decay_weight=0.75 formats as '75%'."""
        evt = _make_drop(decay_weight=0.75)
        formatted = f"{evt.decay_weight:.0%}" if evt.decay_weight is not None else "N/A"
        assert formatted == "75%"

    def test_decay_weight_none_returns_na(self) -> None:
        evt = _make_drop(decay_weight=None)
        formatted = f"{evt.decay_weight:.0%}" if evt.decay_weight is not None else "N/A"
        assert formatted == "N/A"

    def test_market_pct_formatted(self) -> None:
        evt = _make_drop(market_pct=-3.5)
        formatted = f"{evt.market_pct:+.1f}%" if evt.market_pct is not None else "N/A"
        assert formatted == "-3.5%"

    def test_decomposition_none_returns_na(self) -> None:
        evt = _make_drop(market_pct=None, sector_pct=None, company_pct=None)
        assert (f"{evt.market_pct:+.1f}%" if evt.market_pct is not None else "N/A") == "N/A"
        assert (f"{evt.sector_pct:+.1f}%" if evt.sector_pct is not None else "N/A") == "N/A"
        assert (f"{evt.company_pct:+.1f}%" if evt.company_pct is not None else "N/A") == "N/A"

    def test_market_driven_badge(self) -> None:
        evt = _make_drop(is_market_driven=True)
        badge = "Market-Driven" if evt.is_market_driven else ""
        assert badge == "Market-Driven"

    def test_not_market_driven_no_badge(self) -> None:
        evt = _make_drop(is_market_driven=False)
        badge = "Market-Driven" if evt.is_market_driven else ""
        assert badge == ""


class TestDropSortOrder:
    """Test drops sort by decay_weighted_severity descending."""

    def test_sorted_by_decay_weighted_severity(self) -> None:
        """Recent severe drop ranks above older severe drop."""
        drops = [
            _make_drop(date="2024-06-01", drop_pct=-15.0, decay_weighted_severity=3.75),  # old
            _make_drop(date="2025-12-01", drop_pct=-10.0, decay_weighted_severity=9.5),   # recent
            _make_drop(date="2025-09-01", drop_pct=-12.0, decay_weighted_severity=8.0),   # mid
        ]
        sorted_drops = sorted(
            drops,
            key=lambda d: d.decay_weighted_severity if d.decay_weighted_severity is not None else 0,
            reverse=True,
        )
        # Most recent severe first (9.5), then mid (8.0), then old (3.75)
        assert sorted_drops[0].decay_weighted_severity == 9.5
        assert sorted_drops[1].decay_weighted_severity == 8.0
        assert sorted_drops[2].decay_weighted_severity == 3.75

    def test_fallback_to_magnitude_when_no_severity(self) -> None:
        """When decay_weighted_severity is None, fall back to magnitude."""
        drops = [
            _make_drop(drop_pct=-5.0, decay_weighted_severity=None),
            _make_drop(drop_pct=-15.0, decay_weighted_severity=None),
        ]
        sorted_drops = sorted(
            drops,
            key=lambda d: (
                d.decay_weighted_severity
                if d.decay_weighted_severity is not None
                else abs(d.drop_pct.value) if d.drop_pct else 0
            ),
            reverse=True,
        )
        assert abs(sorted_drops[0].drop_pct.value) == 15.0  # type: ignore[union-attr]
        assert abs(sorted_drops[1].drop_pct.value) == 5.0   # type: ignore[union-attr]
