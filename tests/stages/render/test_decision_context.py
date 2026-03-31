"""Tests for decision context builder (Phase 114-01)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.decision_context import (
    build_decision_context,
)


def _make_state(**overrides: Any) -> MagicMock:
    state = MagicMock()
    state.scoring = overrides.get("scoring")
    return state


class TestDecisionContext:
    def test_tier_distribution(self) -> None:
        sc = MagicMock()
        sc.tier = MagicMock()
        sc.tier.tier = "STANDARD"
        state = _make_state(scoring=sc)
        ctx = build_decision_context(state)
        td = ctx["tier_distribution"]
        assert "PREFERRED" in td
        assert "STANDARD" in td
        assert "PROHIBITED" in td
        # Percentages should roughly sum to 100
        total = sum(td.values())
        assert abs(total - 100) < 1

    def test_current_tier_from_scoring(self) -> None:
        sc = MagicMock()
        sc.tier = MagicMock()
        sc.tier.tier = "ELEVATED"
        state = _make_state(scoring=sc)
        ctx = build_decision_context(state)
        assert ctx["current_tier"] == "ELEVATED"
        assert ctx["decision_available"] is True

    def test_posture_fields_empty(self) -> None:
        sc = MagicMock()
        sc.tier = MagicMock()
        sc.tier.tier = "STANDARD"
        state = _make_state(scoring=sc)
        ctx = build_decision_context(state)
        assert ctx["posture_fields"] == {}

    def test_no_scoring_unavailable(self) -> None:
        state = _make_state(scoring=None)
        ctx = build_decision_context(state)
        assert ctx["decision_available"] is False
