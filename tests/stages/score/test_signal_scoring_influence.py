"""Integration tests proving score changes with signal status (FSCORE-02).

Verifies that the composite score demonstrably changes when signals
TRIGGER vs when they are all CLEAR.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest


def _make_brain_signal(
    signal_id: str,
    factors: list[str] | None = None,
) -> dict[str, Any]:
    """Build a minimal brain signal dict for testing."""
    return {
        "id": signal_id,
        "name": f"Test signal {signal_id}",
        "factors": factors or [],
        "signal_class": "evaluative",
        "work_type": "evaluate",
        "execution_mode": "AUTO",
        "evaluation": {"mechanism": "threshold"},
    }


def _make_signal_result(
    status: str = "TRIGGERED",
    threshold_level: str = "red",
) -> dict[str, Any]:
    return {
        "status": status,
        "threshold_level": threshold_level,
        "value": 1.0,
        "evidence": "test evidence",
    }


class TestSignalScoringInfluence:
    """FSCORE-02: Score must change when signals TRIGGER vs CLEAR."""

    def test_all_triggered_vs_all_clear_produces_different_scores(self) -> None:
        """Composite score differs between all-TRIGGERED and all-CLEAR signal sets."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        # Create 5 evaluative signals for F1
        signals = [
            _make_brain_signal(f"SIG.{i}", factors=["F1"])
            for i in range(5)
        ]

        # All TRIGGERED (red)
        triggered_results: dict[str, Any] = {
            f"SIG.{i}": _make_signal_result("TRIGGERED", "red")
            for i in range(5)
        }

        # All CLEAR
        clear_results: dict[str, Any] = {
            f"SIG.{i}": _make_signal_result("CLEAR", "clear")
            for i in range(5)
        }

        with patch(
            "do_uw.stages.score.factor_data_signals.get_signals_for_factor",
            return_value=signals,
        ):
            trig_data, _ = aggregate_factor_from_signals(
                "F1_prior_litigation", triggered_results, 20.0,
            )
            clear_data, _ = aggregate_factor_from_signals(
                "F1_prior_litigation", clear_results, 20.0,
            )

        # Both should use signal path (coverage = 100%)
        assert trig_data["use_signal_path"] is True
        assert clear_data["use_signal_path"] is True

        # TRIGGERED score should be max_points (all red)
        assert trig_data["signal_score"] == pytest.approx(20.0)
        # CLEAR score should be 0
        assert clear_data["signal_score"] == pytest.approx(0.0)
        # They must differ
        assert trig_data["signal_score"] != clear_data["signal_score"]

    def test_mixed_signals_produce_intermediate_score(self) -> None:
        """Mix of TRIGGERED and CLEAR produces score between 0 and max_points."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        signals = [
            _make_brain_signal(f"SIG.{i}", factors=["F1"])
            for i in range(4)
        ]

        mixed_results: dict[str, Any] = {
            "SIG.0": _make_signal_result("TRIGGERED", "red"),
            "SIG.1": _make_signal_result("TRIGGERED", "yellow"),
            "SIG.2": _make_signal_result("CLEAR", "clear"),
            "SIG.3": _make_signal_result("CLEAR", "clear"),
        }

        with patch(
            "do_uw.stages.score.factor_data_signals.get_signals_for_factor",
            return_value=signals,
        ):
            data, _ = aggregate_factor_from_signals(
                "F1_prior_litigation", mixed_results, 20.0,
            )

        # (1.0 + 0.5 + 0.0 + 0.0) / 4.0 * 20 = 7.5
        assert 0.0 < data["signal_score"] < 20.0
        assert data["signal_score"] == pytest.approx(7.5)
