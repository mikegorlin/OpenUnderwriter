"""Tests for epistemological trace context builder (Phase 114-01)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.stages.render.context_builders.epistemological_trace import (
    build_epistemological_trace,
)


def _make_state(**overrides: Any) -> MagicMock:
    state = MagicMock()
    state.analysis = overrides.get("analysis")
    return state


def _make_brain(signal_id: str, rap_class: str, rap_sub: str) -> dict[str, Any]:
    return {
        "id": signal_id,
        "rap_class": rap_class,
        "rap_subcategory": rap_sub,
        "evaluation": {"mechanism": "threshold"},
        "epistemology": {"rule_origin": "SEC practice", "threshold_basis": "SCAC data"},
    }


class TestEpistemologicalTrace:
    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_all_statuses_included(self, mock_brain: MagicMock) -> None:
        """Triggered, clean, and skipped signals all appear in trace."""
        brains = {
            "SIG_T": _make_brain("SIG_T", "host", "financial_health"),
            "SIG_C": _make_brain("SIG_C", "agent", "governance_quality"),
            "SIG_S": _make_brain("SIG_S", "environment", "market_conditions"),
        }
        mock_brain.side_effect = lambda sid: brains.get(sid)
        sr = {
            "SIG_T": {"status": "TRIGGERED", "threshold_level": "red", "value": 1.0,
                       "source": "10-K", "confidence": "HIGH"},
            "SIG_C": {"status": "CLEAR", "threshold_level": "", "value": 0.0,
                       "source": "DEF 14A", "confidence": "MEDIUM"},
            "SIG_S": {"status": "SKIPPED", "threshold_level": "", "value": None,
                       "source": "", "confidence": "LOW"},
        }
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_epistemological_trace(state)
        assert ctx["trace_available"] is True
        all_ids = [r["signal_id"] for dim_rows in ctx["rows_by_dimension"].values() for r in dim_rows]
        assert "SIG_T" in all_ids
        assert "SIG_C" in all_ids
        assert "SIG_S" in all_ids

    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_grouped_by_hae(self, mock_brain: MagicMock) -> None:
        brains = {
            "SIG_H": _make_brain("SIG_H", "host", "fh"),
            "SIG_A": _make_brain("SIG_A", "agent", "gq"),
        }
        mock_brain.side_effect = lambda sid: brains.get(sid)
        sr = {
            "SIG_H": {"status": "TRIGGERED", "threshold_level": "red", "value": 1.0,
                       "source": "s", "confidence": "HIGH"},
            "SIG_A": {"status": "CLEAR", "threshold_level": "", "value": 0.0,
                       "source": "s", "confidence": "MEDIUM"},
        }
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_epistemological_trace(state)
        assert "host" in ctx["rows_by_dimension"]
        assert "agent" in ctx["rows_by_dimension"]

    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_row_fields(self, mock_brain: MagicMock) -> None:
        brains = {"SIG_X": _make_brain("SIG_X", "host", "fh")}
        mock_brain.side_effect = lambda sid: brains.get(sid)
        sr = {"SIG_X": {"status": "TRIGGERED", "threshold_level": "red", "value": 42.0,
                         "source": "10-K", "confidence": "HIGH"}}
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_epistemological_trace(state)
        row = ctx["rows_by_dimension"]["host"][0]
        assert row["signal_id"] == "SIG_X"
        assert row["status"] == "TRIGGERED"
        assert row["source"] == "10-K"
        assert row["confidence"] == "HIGH"
        assert row["source_type"] == "audited"
        assert row["rule_origin"] == "SEC practice"
        assert row["threshold_basis"] == "SCAC data"
        assert row["rap_class"] == "host"
        assert row["rap_subcategory"] == "fh"

    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_source_type_mapping(self, mock_brain: MagicMock) -> None:
        brains = {
            "H": _make_brain("H", "host", "x"),
            "M": _make_brain("M", "host", "x"),
            "L": _make_brain("L", "host", "x"),
        }
        mock_brain.side_effect = lambda sid: brains.get(sid)
        sr = {
            "H": {"status": "CLEAR", "threshold_level": "", "value": 0, "source": "s", "confidence": "HIGH"},
            "M": {"status": "CLEAR", "threshold_level": "", "value": 0, "source": "s", "confidence": "MEDIUM"},
            "L": {"status": "CLEAR", "threshold_level": "", "value": 0, "source": "s", "confidence": "LOW"},
        }
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_epistemological_trace(state)
        rows = ctx["rows_by_dimension"]["host"]
        types = {r["signal_id"]: r["source_type"] for r in rows}
        assert types["H"] == "audited"
        assert types["M"] == "unaudited"
        assert types["L"] == "web/derived"

    @patch("do_uw.stages.render.context_builders._signal_consumer._get_brain_signal")
    def test_trace_total_count(self, mock_brain: MagicMock) -> None:
        brains = {
            "S1": _make_brain("S1", "host", "x"),
            "S2": _make_brain("S2", "agent", "y"),
        }
        mock_brain.side_effect = lambda sid: brains.get(sid)
        sr = {
            "S1": {"status": "TRIGGERED", "threshold_level": "red", "value": 1.0, "source": "s", "confidence": "HIGH"},
            "S2": {"status": "CLEAR", "threshold_level": "", "value": 0, "source": "s", "confidence": "MEDIUM"},
        }
        analysis = MagicMock()
        analysis.signal_results = sr
        state = _make_state(analysis=analysis)
        ctx = build_epistemological_trace(state)
        assert ctx["trace_total"] == 2

    def test_no_analysis_unavailable(self) -> None:
        state = _make_state(analysis=None)
        ctx = build_epistemological_trace(state)
        assert ctx["trace_available"] is False
