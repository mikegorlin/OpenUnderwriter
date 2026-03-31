"""Tests for pattern firing panel context builder (109-03).

Tests build_pattern_context() function that transforms PatternEngineResult
into template-ready data for the 10-card firing panel grid.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.patterns import PatternEngineResult
from do_uw.stages.score.pattern_engine import ArchetypeResult, EngineResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine_result(
    engine_id: str,
    engine_name: str,
    *,
    fired: bool = False,
    confidence: float = 0.0,
    headline: str = "",
    findings: list[dict[str, Any]] | None = None,
) -> EngineResult:
    """Build an EngineResult."""
    return EngineResult(
        engine_id=engine_id,
        engine_name=engine_name,
        fired=fired,
        confidence=confidence,
        headline=headline or f"{engine_name} {'match' if fired else 'not fired'}",
        findings=findings or [],
    )


def _make_archetype_result(
    archetype_id: str,
    archetype_name: str,
    *,
    fired: bool = False,
    signals_matched: int = 0,
    signals_required: int = 18,
    recommendation_floor: str | None = None,
    confidence: float = 0.0,
    matched_signal_ids: list[str] | None = None,
    historical_cases: list[str] | None = None,
) -> ArchetypeResult:
    """Build an ArchetypeResult."""
    return ArchetypeResult(
        archetype_id=archetype_id,
        archetype_name=archetype_name,
        fired=fired,
        signals_matched=signals_matched,
        signals_required=signals_required,
        matched_signal_ids=matched_signal_ids or [],
        recommendation_floor=recommendation_floor,
        confidence=confidence,
        historical_cases=historical_cases or [],
    )


def _make_pattern_engine_result(
    *,
    n_engines_fired: int = 1,
    n_archetypes_fired: int = 1,
) -> PatternEngineResult:
    """Build a PatternEngineResult with mix of fired/not-fired."""
    engines = [
        _make_engine_result(
            "conjunction_scan",
            "Conjunction Scan",
            fired=(0 < n_engines_fired),
            confidence=0.75,
            headline="3 CLEAR signals co-firing across 2 RAP categories",
            findings=[
                {"signal_id": "FIN.FORENSIC.m_score_composite", "rap_class": "agent"},
                {"signal_id": "GOV.BOARD.independence", "rap_class": "host"},
            ],
        ),
        _make_engine_result(
            "peer_outlier",
            "Peer Outlier",
            fired=(1 < n_engines_fired),
            confidence=0.6,
            headline="Revenue growth z-score = 3.2 vs peers",
        ),
        _make_engine_result(
            "migration_drift",
            "Migration Drift",
            fired=False,
            confidence=0.0,
            headline="Insufficient quarterly data",
        ),
        _make_engine_result(
            "precedent_match",
            "Precedent Match",
            fired=(2 < n_engines_fired),
            confidence=0.52,
            headline="Top match: Valeant 2015 (52%)",
            findings=[
                {
                    "case_name": "Valeant 2015",
                    "similarity": 0.52,
                    "outcome": "$1.2B settlement",
                    "note": "channel stuffing via Philidor",
                },
                {
                    "case_name": "Luckin Coffee 2020",
                    "similarity": 0.41,
                    "outcome": "$180M settlement",
                    "note": "fabricated revenue transactions",
                },
                {
                    "case_name": "Under Armour 2019",
                    "similarity": 0.35,
                    "outcome": "$434M settlement",
                    "note": "revenue acceleration",
                },
            ],
        ),
    ]

    archetypes = [
        _make_archetype_result(
            "desperate_growth_trap",
            "Desperate Growth Trap",
            fired=(0 < n_archetypes_fired),
            signals_matched=7,
            signals_required=18,
            recommendation_floor="ELEVATED",
            confidence=0.39,
            matched_signal_ids=[
                "FIN.QUALITY.revenue_recognition_risk",
                "FIN.FORENSIC.m_score_composite",
            ],
            historical_cases=["Valeant 2015", "Luckin Coffee 2020"],
        ),
        _make_archetype_result(
            "governance_vacuum",
            "Governance Vacuum",
            fired=False,
            signals_matched=2,
            signals_required=18,
        ),
        _make_archetype_result(
            "post_spac_hangover",
            "Post-SPAC Hangover",
            fired=False,
            signals_matched=0,
            signals_required=14,
        ),
        _make_archetype_result(
            "accounting_time_bomb",
            "Accounting Time Bomb",
            fired=(1 < n_archetypes_fired),
            signals_matched=5,
            signals_required=19,
            recommendation_floor="ELEVATED",
            confidence=0.26,
        ),
        _make_archetype_result(
            "regulatory_reckoning",
            "Regulatory Reckoning",
            fired=False,
            signals_matched=1,
            signals_required=18,
        ),
        _make_archetype_result(
            "ai_mirage",
            "AI Mirage",
            fired=False,
            signals_matched=0,
            signals_required=15,
        ),
    ]

    return PatternEngineResult(
        engine_results=engines,
        archetype_results=archetypes,
        computed_at=datetime.now(timezone.utc),
    )


def _make_mock_state(
    *,
    has_scoring: bool = True,
    has_pattern_result: bool = True,
    n_engines_fired: int = 1,
    n_archetypes_fired: int = 1,
) -> MagicMock:
    """Build a mock state with pattern_engine_result."""
    state = MagicMock()
    if not has_scoring:
        state.scoring = None
        return state

    state.scoring = MagicMock()
    if not has_pattern_result:
        state.scoring.pattern_engine_result = None
        return state

    state.scoring.pattern_engine_result = _make_pattern_engine_result(
        n_engines_fired=n_engines_fired,
        n_archetypes_fired=n_archetypes_fired,
    )
    return state


# ---------------------------------------------------------------------------
# Tests: basic context building
# ---------------------------------------------------------------------------

class TestBuildPatternContext:
    """Tests for build_pattern_context()."""

    def test_returns_10_items(self) -> None:
        """State with pattern_engine_result => dict with 10 items."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state()
        ctx = build_pattern_context(state)

        assert ctx["patterns_available"] is True
        assert len(ctx["items"]) == 10

    def test_4_engines_then_6_archetypes_order(self) -> None:
        """4 engine items + 6 archetype items in correct order."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state()
        ctx = build_pattern_context(state)
        items = ctx["items"]

        # First 4 are engines
        for item in items[:4]:
            assert item["type"] == "engine"

        # Last 6 are archetypes
        for item in items[4:]:
            assert item["type"] == "archetype"

    def test_fired_engine_has_match_status(self) -> None:
        """Fired engine has status='MATCH', confidence > 0."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(n_engines_fired=1)
        ctx = build_pattern_context(state)
        items = ctx["items"]

        conj = [i for i in items if i.get("engine_id") == "conjunction_scan"]
        assert len(conj) == 1
        assert conj[0]["status"] == "MATCH"
        assert conj[0]["confidence_pct"] > 0

    def test_not_fired_engine_has_headline(self) -> None:
        """NOT_FIRED engine has status='NOT_FIRED', headline present."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(n_engines_fired=0)
        ctx = build_pattern_context(state)
        items = ctx["items"]

        # All engines should be NOT_FIRED
        engine_items = [i for i in items if i["type"] == "engine"]
        for item in engine_items:
            assert item["status"] == "NOT_FIRED"
            assert item["headline"]  # Non-empty headline

    def test_fired_archetype_has_match_badge(self) -> None:
        """Fired archetype has match_badge like '7/18'."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(n_archetypes_fired=1)
        ctx = build_pattern_context(state)
        items = ctx["items"]

        dgt = [i for i in items if i.get("archetype_id") == "desperate_growth_trap"]
        assert len(dgt) == 1
        assert dgt[0]["status"] == "MATCH"
        assert dgt[0]["match_badge"] == "7/18"
        assert dgt[0]["recommendation_floor"] == "ELEVATED"

    def test_not_fired_archetype_has_match_badge(self) -> None:
        """NOT_FIRED archetype has match_badge like '2/18'."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(n_archetypes_fired=0)
        ctx = build_pattern_context(state)
        items = ctx["items"]

        gov = [i for i in items if i.get("archetype_id") == "governance_vacuum"]
        assert len(gov) == 1
        assert gov[0]["status"] == "NOT_FIRED"
        assert gov[0]["match_badge"] == "2/18"

    def test_precedent_match_findings_formatted(self) -> None:
        """Precedent Match findings formatted with case name + similarity + outcome."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(n_engines_fired=3)
        ctx = build_pattern_context(state)
        items = ctx["items"]

        prec = [i for i in items if i.get("engine_id") == "precedent_match"]
        assert len(prec) == 1
        assert prec[0]["status"] == "MATCH"
        # Should have findings with case details
        assert prec[0]["has_detail"] is True
        findings = prec[0]["findings"]
        assert len(findings) >= 2
        # Check first finding has expected keys
        first = findings[0]
        assert "case_name" in first or "similarity" in first


# ---------------------------------------------------------------------------
# Tests: edge cases
# ---------------------------------------------------------------------------

class TestPatternContextEdgeCases:
    """Tests for edge cases and missing data."""

    def test_no_scoring_returns_unavailable(self) -> None:
        """State with no scoring => patterns_available=False."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(has_scoring=False)
        ctx = build_pattern_context(state)

        assert ctx["patterns_available"] is False

    def test_no_pattern_result_returns_unavailable(self) -> None:
        """State with scoring but no pattern_engine_result => patterns_available=False."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(has_scoring=True, has_pattern_result=False)
        ctx = build_pattern_context(state)

        assert ctx["patterns_available"] is False

    def test_summary_stats_computed(self) -> None:
        """Summary stats engines_fired, archetypes_fired, highest_floor computed correctly."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(n_engines_fired=2, n_archetypes_fired=1)
        ctx = build_pattern_context(state)

        assert ctx["engines_fired"] == 2
        assert ctx["archetypes_fired"] == 1
        assert ctx["highest_floor"] == "ELEVATED"
        assert ctx["any_pattern_fired"] is True

    def test_no_fired_patterns_summary(self) -> None:
        """No fired patterns => engines_fired=0, any_pattern_fired=False."""
        from do_uw.stages.render.context_builders.pattern_context import (
            build_pattern_context,
        )

        state = _make_mock_state(n_engines_fired=0, n_archetypes_fired=0)
        ctx = build_pattern_context(state)

        assert ctx["engines_fired"] == 0
        assert ctx["archetypes_fired"] == 0
        assert ctx["highest_floor"] is None
        assert ctx["any_pattern_fired"] is False
