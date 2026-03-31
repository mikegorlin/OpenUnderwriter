"""Tests for Phase 119: Stock drop D&O assessment and pattern narrative generation."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from do_uw.models.common import SourcedValue
from do_uw.models.market_events import StockDropEvent

_NOW = datetime.now(tz=UTC)
from do_uw.stages.benchmark.stock_drop_narrative import (
    generate_drop_do_assessments,
    generate_drop_pattern_narrative,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_drop(
    *,
    trigger_category: str = "unknown",
    trigger_description: str = "Some event",
    drop_pct: float = -10.0,
    date: str = "2025-06-15",
    is_company_specific: bool = True,
    is_market_driven: bool = False,
    abnormal_return_pct: float | None = -8.5,
    is_statistically_significant: bool = True,
    market_pct: float | None = None,
    company_pct: float | None = None,
    from_price: float | None = 100.0,
    close_price: float | None = 90.0,
) -> StockDropEvent:
    return StockDropEvent(
        trigger_category=trigger_category,
        trigger_description=trigger_description,
        drop_pct=SourcedValue(value=drop_pct, source="yfinance", confidence="HIGH", as_of=_NOW),
        date=SourcedValue(value=date, source="yfinance", confidence="HIGH", as_of=_NOW),
        is_company_specific=is_company_specific,
        is_market_driven=is_market_driven,
        abnormal_return_pct=abnormal_return_pct,
        is_statistically_significant=is_statistically_significant,
        market_pct=market_pct,
        company_pct=company_pct,
        from_price=from_price,
        close_price=close_price,
    )


# ---------------------------------------------------------------------------
# generate_drop_do_assessments tests
# ---------------------------------------------------------------------------

class TestGenerateDropDoAssessments:
    """Test D&O assessment generation for each catalyst type."""

    def test_earnings_miss(self) -> None:
        drop = _make_drop(trigger_category="earnings_miss", trigger_description="Q3 EPS missed by $0.15")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert drop.do_assessment != ""
        assert "Acme Corp" in drop.do_assessment
        assert "10(b)" in drop.do_assessment or "10b-5" in drop.do_assessment
        assert "10.0%" in drop.do_assessment or "10%" in drop.do_assessment

    def test_guidance_cut(self) -> None:
        drop = _make_drop(trigger_category="guidance_cut", trigger_description="FY25 guidance lowered $200M")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "safe harbor" in drop.do_assessment.lower()
        assert "Acme Corp" in drop.do_assessment

    def test_restatement(self) -> None:
        drop = _make_drop(trigger_category="restatement", trigger_description="Revenue restatement FY23-FY24")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "Section 11" in drop.do_assessment or "Section 10(b)" in drop.do_assessment
        assert "restatement" in drop.do_assessment.lower()

    def test_litigation(self) -> None:
        drop = _make_drop(trigger_category="litigation", trigger_description="DOJ antitrust investigation")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "Acme Corp" in drop.do_assessment
        assert "litigation" in drop.do_assessment.lower() or "D&O" in drop.do_assessment

    def test_analyst_downgrade(self) -> None:
        drop = _make_drop(trigger_category="analyst_downgrade", trigger_description="Goldman downgrade to Sell")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "downgrade" in drop.do_assessment.lower()
        assert "loss causation" in drop.do_assessment.lower()

    def test_regulatory(self) -> None:
        drop = _make_drop(trigger_category="regulatory", trigger_description="FDA warning letter")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "regulat" in drop.do_assessment.lower()

    def test_management_departure(self) -> None:
        drop = _make_drop(trigger_category="management_departure", trigger_description="CEO resigned")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "D&O" in drop.do_assessment or "coverage" in drop.do_assessment.lower()

    def test_market_wide(self) -> None:
        drop = _make_drop(
            trigger_category="market_wide",
            is_market_driven=True,
            is_company_specific=False,
            market_pct=-6.0,
            company_pct=-4.0,
        )
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "market" in drop.do_assessment.lower()
        assert "loss causation" in drop.do_assessment.lower()

    def test_unknown_company_specific(self) -> None:
        drop = _make_drop(trigger_category="unknown", is_company_specific=True)
        generate_drop_do_assessments([drop], "Acme Corp")
        assert drop.do_assessment != ""
        assert "Acme Corp" in drop.do_assessment

    def test_empty_drops(self) -> None:
        generate_drop_do_assessments([], "Acme Corp")  # No crash

    def test_mutates_in_place(self) -> None:
        drops = [_make_drop(trigger_category="earnings_miss")]
        assert drops[0].do_assessment == ""
        generate_drop_do_assessments(drops, "Acme Corp")
        assert drops[0].do_assessment != ""

    def test_multiple_drops(self) -> None:
        drops = [
            _make_drop(trigger_category="earnings_miss"),
            _make_drop(trigger_category="guidance_cut"),
            _make_drop(trigger_category="restatement"),
        ]
        generate_drop_do_assessments(drops, "Acme Corp")
        for d in drops:
            assert d.do_assessment != ""
            assert "Acme Corp" in d.do_assessment

    def test_includes_date(self) -> None:
        drop = _make_drop(trigger_category="earnings_miss", date="2025-06-15")
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "2025-06-15" in drop.do_assessment

    def test_includes_drop_pct(self) -> None:
        drop = _make_drop(trigger_category="earnings_miss", drop_pct=-12.5)
        generate_drop_do_assessments([drop], "Acme Corp")
        assert "12.5" in drop.do_assessment


# ---------------------------------------------------------------------------
# generate_drop_pattern_narrative tests
# ---------------------------------------------------------------------------

class TestGenerateDropPatternNarrative:
    """Test overall drop pattern narrative generation."""

    def test_empty_drops_returns_empty(self) -> None:
        result = generate_drop_pattern_narrative([], [], "Acme Corp")
        assert result == ""

    def test_empty_patterns_with_drops(self) -> None:
        drops = [_make_drop(is_company_specific=True)]
        result = generate_drop_pattern_narrative([], drops, "Acme Corp")
        assert result != ""
        assert "Acme Corp" in result

    def test_with_patterns(self) -> None:
        patterns = [{"pattern": "cluster", "description": "3 drops in 30 days"}]
        drops = [
            _make_drop(is_company_specific=True),
            _make_drop(is_company_specific=True),
            _make_drop(is_company_specific=False, is_market_driven=True),
        ]
        result = generate_drop_pattern_narrative(patterns, drops, "Acme Corp")
        assert result != ""
        assert "Acme Corp" in result

    def test_counts_company_specific(self) -> None:
        drops = [
            _make_drop(is_company_specific=True),
            _make_drop(is_company_specific=True),
            _make_drop(is_company_specific=False),
        ]
        result = generate_drop_pattern_narrative([], drops, "Acme Corp")
        assert "2" in result  # 2 company-specific

    def test_all_market_driven(self) -> None:
        drops = [
            _make_drop(is_company_specific=False, is_market_driven=True),
            _make_drop(is_company_specific=False, is_market_driven=True),
        ]
        result = generate_drop_pattern_narrative([], drops, "Acme Corp")
        assert result != ""
        # Should mention market-driven nature
