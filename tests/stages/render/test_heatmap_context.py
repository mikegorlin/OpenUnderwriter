"""Tests for heatmap context builder (Phase 114-01)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.stages.render.context_builders.heatmap_context import (
    build_heatmap_context,
)


def _make_state(**overrides: Any) -> MagicMock:
    state = MagicMock()
    state.analysis = overrides.get("analysis")
    return state


def _make_brain_signal(signal_id: str, rap_class: str, rap_subcategory: str) -> dict[str, Any]:
    return {
        "id": signal_id,
        "rap_class": rap_class,
        "rap_subcategory": rap_subcategory,
        "evaluation": {"mechanism": "threshold"},
        "epistemology": {"rule_origin": "test", "threshold_basis": "test"},
    }


class TestHeatmapContext:
    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_signals_grouped_by_hae(self, mock_brain: MagicMock) -> None:
        brain_data = {
            "SIG_H": _make_brain_signal("SIG_H", "host", "financial_health"),
            "SIG_A": _make_brain_signal("SIG_A", "agent", "governance_quality"),
            "SIG_E": _make_brain_signal("SIG_E", "environment", "market_conditions"),
        }
        mock_brain.side_effect = lambda sid: brain_data.get(sid)
        sr = {
            "SIG_H": {"status": "TRIGGERED", "threshold_level": "red", "value": 1.0},
            "SIG_A": {"status": "CLEAR", "threshold_level": "", "value": 0.0},
            "SIG_E": {"status": "TRIGGERED", "threshold_level": "yellow", "value": 0.5},
        }
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_heatmap_context(state)
        assert ctx["heatmap_available"] is True
        dim_keys = {d["dimension_key"] for d in ctx["dimensions"]}
        assert "host" in dim_keys
        assert "agent" in dim_keys
        assert "environment" in dim_keys

    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_cell_structure(self, mock_brain: MagicMock) -> None:
        brain_data = {"SIG_X": _make_brain_signal("SIG_X", "host", "financial_health")}
        mock_brain.side_effect = lambda sid: brain_data.get(sid)
        sr = {"SIG_X": {"status": "TRIGGERED", "threshold_level": "red", "value": 42.0}}
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_heatmap_context(state)
        # Find the host dimension and its financial_health row
        host_dim = next(d for d in ctx["dimensions"] if d["dimension_key"] == "host")
        fh_row = next(r for r in host_dim["rows"] if r["subcategory"] == "Financial Health")
        assert fh_row["triggered"] == 1
        assert fh_row["total"] == 1
        # Top triggered signals carry detail
        assert len(fh_row["top_triggered"]) == 1
        assert fh_row["top_triggered"][0]["id"] == "SIG_X"
        assert fh_row["top_triggered"][0]["level"] == "red"

    def test_empty_signals_unavailable(self) -> None:
        analysis = MagicMock()
        analysis.signal_results = {}
        state = _make_state(analysis=analysis)
        ctx = build_heatmap_context(state)
        assert ctx["heatmap_available"] is False

    def test_no_analysis_unavailable(self) -> None:
        state = _make_state(analysis=None)
        ctx = build_heatmap_context(state)
        assert ctx["heatmap_available"] is False

    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_skipped_signals_included(self, mock_brain: MagicMock) -> None:
        brain_data = {"SIG_S": _make_brain_signal("SIG_S", "agent", "insider_activity")}
        mock_brain.side_effect = lambda sid: brain_data.get(sid)
        sr = {"SIG_S": {"status": "SKIPPED", "threshold_level": "", "value": None}}
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_heatmap_context(state)
        assert ctx["heatmap_available"] is True
        agent_dim = next(d for d in ctx["dimensions"] if d["dimension_key"] == "agent")
        ia_row = next(r for r in agent_dim["rows"] if r["subcategory"] == "Insider Activity")
        assert ia_row["skipped"] == 1
