"""Tests for adversarial critique context builder (110-02).

Tests build_adversarial_context() function that transforms AdversarialResult
into template-ready data for the Devil's Advocate section + inline caveat badges.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_caveat(
    *,
    caveat_type: str = "false_positive",
    target_signal_id: str = "",
    headline: str = "Test caveat",
    explanation: str = "Test explanation",
    confidence: float = 0.5,
    severity: str = "info",
    evidence: list[str] | None = None,
    narrative_source: str = "template",
) -> Any:
    """Create an AdversarialResult Caveat."""
    from do_uw.models.adversarial import Caveat

    return Caveat(
        caveat_type=caveat_type,
        target_signal_id=target_signal_id,
        headline=headline,
        explanation=explanation,
        confidence=confidence,
        severity=severity,
        evidence=evidence or [],
        narrative_source=narrative_source,
    )


def _make_adversarial_result(
    caveats: list[Any] | None = None,
    *,
    summary: str = "Test summary",
) -> Any:
    """Create an AdversarialResult."""
    from do_uw.models.adversarial import AdversarialResult

    caveat_list = caveats or []
    fp = sum(1 for c in caveat_list if c.caveat_type == "false_positive")
    fn = sum(1 for c in caveat_list if c.caveat_type == "false_negative")
    ct = sum(1 for c in caveat_list if c.caveat_type == "contradiction")
    dc = sum(1 for c in caveat_list if c.caveat_type == "data_completeness")

    return AdversarialResult(
        caveats=caveat_list,
        false_positive_count=fp,
        false_negative_count=fn,
        contradiction_count=ct,
        completeness_issues=dc,
        summary=summary,
        computed_at=datetime.now(timezone.utc),
    )


def _make_mock_state(
    adversarial_result: Any | None = "UNSET",
) -> MagicMock:
    """Create mock AnalysisState with optional adversarial_result."""
    from do_uw.models.scoring import _rebuild_scoring_models

    _rebuild_scoring_models()
    from do_uw.models.scoring import ScoringResult

    state = MagicMock()
    sr = ScoringResult()
    if adversarial_result != "UNSET":
        sr.adversarial_result = adversarial_result
    state.scoring = sr
    return state


# ---------------------------------------------------------------------------
# Context builder tests
# ---------------------------------------------------------------------------


class TestBuildAdversarialContext:
    """Tests for build_adversarial_context."""

    def test_returns_unavailable_when_scoring_none(self) -> None:
        """Returns adversarial_available=False when scoring is None."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        state = MagicMock()
        state.scoring = None
        result = build_adversarial_context(state)
        assert result["adversarial_available"] is False

    def test_returns_unavailable_when_result_none(self) -> None:
        """Returns adversarial_available=False when adversarial_result is None."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        state = _make_mock_state(adversarial_result=None)
        result = build_adversarial_context(state)
        assert result["adversarial_available"] is False

    def test_returns_available_with_caveats(self) -> None:
        """Returns adversarial_available=True with populated caveats."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(caveat_type="false_positive", headline="FP1"),
            _make_caveat(caveat_type="false_negative", headline="FN1"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        assert result["adversarial_available"] is True
        assert result["total_caveats"] == 2
        assert len(result["caveats"]) == 2

    def test_empty_adversarial_result(self) -> None:
        """Returns available=True with empty caveats list."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        ar = _make_adversarial_result([])
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        assert result["adversarial_available"] is True
        assert result["total_caveats"] == 0
        assert result["caveats"] == []

    def test_filters_by_caveat_type(self) -> None:
        """Filters caveats into type-specific lists."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(caveat_type="false_positive"),
            _make_caveat(caveat_type="false_positive"),
            _make_caveat(caveat_type="false_negative"),
            _make_caveat(caveat_type="contradiction"),
            _make_caveat(caveat_type="data_completeness"),
            _make_caveat(caveat_type="data_completeness"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        assert len(result["false_positives"]) == 2
        assert len(result["false_negatives"]) == 1
        assert len(result["contradictions"]) == 1
        assert len(result["completeness_issues"]) == 2

    def test_sorts_by_severity_then_confidence(self) -> None:
        """Caveats sorted: warning > caution > info, then by confidence desc."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(severity="info", confidence=0.9, headline="Low sev high conf"),
            _make_caveat(severity="warning", confidence=0.3, headline="High sev low conf"),
            _make_caveat(severity="caution", confidence=0.7, headline="Mid sev"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        headlines = [c["headline"] for c in result["caveats"]]
        assert headlines[0] == "High sev low conf"  # warning first
        assert headlines[1] == "Mid sev"  # caution second
        assert headlines[2] == "Low sev high conf"  # info last

    def test_summary_passed_through(self) -> None:
        """Summary string from AdversarialResult is passed to context."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        ar = _make_adversarial_result([], summary="Overall looks good")
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        assert result["summary"] == "Overall looks good"


# ---------------------------------------------------------------------------
# Caveat index tests (for inline badges)
# ---------------------------------------------------------------------------


class TestCaveatIndex:
    """Tests for caveat_index keyed by target_signal_id."""

    def test_caveat_index_keyed_by_signal(self) -> None:
        """caveat_index contains caveats keyed by target_signal_id."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(target_signal_id="SIG.A", headline="Caveat for A"),
            _make_caveat(target_signal_id="SIG.B", headline="Caveat for B"),
            _make_caveat(target_signal_id="SIG.A", headline="Another for A"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        idx = result["caveat_index"]
        assert "SIG.A" in idx
        assert len(idx["SIG.A"]) == 2
        assert "SIG.B" in idx
        assert len(idx["SIG.B"]) == 1

    def test_caveat_index_excludes_empty_signal_id(self) -> None:
        """caveat_index excludes caveats without target_signal_id."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(target_signal_id="SIG.A", headline="Has ID"),
            _make_caveat(target_signal_id="", headline="No ID"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        idx = result["caveat_index"]
        assert "SIG.A" in idx
        assert "" not in idx

    def test_caveat_index_empty_when_no_targets(self) -> None:
        """caveat_index is empty when no caveats have target_signal_id."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(target_signal_id="", headline="General caveat"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        assert result["caveat_index"] == {}


# ---------------------------------------------------------------------------
# Template-ready dict structure tests
# ---------------------------------------------------------------------------


class TestCaveatDictStructure:
    """Tests for the template-ready caveat dict structure."""

    def test_caveat_dict_has_all_fields(self) -> None:
        """Each caveat dict has all required template fields."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [_make_caveat()]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        c = result["caveats"][0]
        expected_keys = {
            "caveat_type", "target_signal_id", "headline", "explanation",
            "confidence", "confidence_pct", "evidence", "severity",
            "narrative_source", "type_label", "type_color",
        }
        assert expected_keys.issubset(set(c.keys()))

    def test_type_label_mapping(self) -> None:
        """type_label correctly maps caveat types to display labels."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(caveat_type="false_positive"),
            _make_caveat(caveat_type="false_negative"),
            _make_caveat(caveat_type="contradiction"),
            _make_caveat(caveat_type="data_completeness"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        labels = {c["caveat_type"]: c["type_label"] for c in result["caveats"]}
        assert labels["false_positive"] == "Possible FP"
        assert labels["false_negative"] == "Blind Spot"
        assert labels["contradiction"] == "Contradicts"
        assert labels["data_completeness"] == "Data Gap"

    def test_type_color_mapping(self) -> None:
        """type_color correctly maps caveat types to CSS color classes."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [
            _make_caveat(caveat_type="false_positive"),
            _make_caveat(caveat_type="false_negative"),
            _make_caveat(caveat_type="contradiction"),
            _make_caveat(caveat_type="data_completeness"),
        ]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        colors = {c["caveat_type"]: c["type_color"] for c in result["caveats"]}
        assert colors["false_positive"] == "amber"
        assert colors["false_negative"] == "blue"
        assert colors["contradiction"] == "purple"
        assert colors["data_completeness"] == "gray"

    def test_confidence_pct_is_integer(self) -> None:
        """confidence_pct is rounded integer percentage."""
        from do_uw.stages.render.context_builders.adversarial_context import (
            build_adversarial_context,
        )

        caveats = [_make_caveat(confidence=0.756)]
        ar = _make_adversarial_result(caveats)
        state = _make_mock_state(adversarial_result=ar)

        result = build_adversarial_context(state)
        assert result["caveats"][0]["confidence_pct"] == 76
