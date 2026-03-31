"""Tests for CRF bar context builder (Phase 114-01)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.crf_bar_context import (
    build_crf_bar_context,
)


def _make_state(**overrides: Any) -> MagicMock:
    state = MagicMock()
    state.scoring = overrides.get("scoring")
    return state


class TestCrfBarContext:
    def test_crf_vetoes_extracted(self) -> None:
        sc = MagicMock()
        hae = MagicMock()
        veto1 = MagicMock()
        veto1.is_active = True
        veto1.crf_id = "CRF-RESTATEMENT"
        veto1.condition = "Restatement detected"
        veto2 = MagicMock()
        veto2.is_active = True
        veto2.crf_id = "CRF-SEC-ENFORCEMENT"
        veto2.condition = "SEC enforcement action"
        hae.crf_vetoes = [veto1, veto2]
        sc.hae_result = hae
        sc.red_flags = []
        state = _make_state(scoring=sc)
        ctx = build_crf_bar_context(state)
        ids = [a["id"] for a in ctx["alerts"]]
        assert "CRF-RESTATEMENT" in ids
        assert "CRF-SEC-ENFORCEMENT" in ids
        # CRF vetoes should be CRITICAL severity
        for a in ctx["alerts"]:
            if a["id"].startswith("CRF-"):
                assert a["severity"] == "CRITICAL"

    def test_red_flags_extracted(self) -> None:
        sc = MagicMock()
        sc.hae_result = None
        rf = MagicMock()
        rf.flag_id = "RED_FLAG_1"
        rf.flag_name = "Test Flag"
        rf.triggered = True
        rf.evidence = ["Some evidence"]
        sc.red_flags = [rf]
        state = _make_state(scoring=sc)
        ctx = build_crf_bar_context(state)
        assert len(ctx["alerts"]) == 1
        assert ctx["alerts"][0]["severity"] == "HIGH"

    def test_section_links(self) -> None:
        sc = MagicMock()
        hae = MagicMock()
        veto1 = MagicMock()
        veto1.is_active = True
        veto1.crf_id = "CRF-RESTATEMENT"
        veto1.condition = "Restatement detected"
        veto2 = MagicMock()
        veto2.is_active = True
        veto2.crf_id = "CRF-MATERIAL-WEAKNESS"
        veto2.condition = "Material weakness"
        hae.crf_vetoes = [veto1, veto2]
        sc.hae_result = hae
        sc.red_flags = []
        state = _make_state(scoring=sc)
        ctx = build_crf_bar_context(state)
        links = {a["id"]: a["section_link"] for a in ctx["alerts"]}
        assert links["CRF-RESTATEMENT"] == "#financial-health"
        assert links["CRF-MATERIAL-WEAKNESS"] == "#financial-health"

    def test_no_scoring_empty_alerts(self) -> None:
        state = _make_state(scoring=None)
        ctx = build_crf_bar_context(state)
        assert ctx["alerts"] == []
