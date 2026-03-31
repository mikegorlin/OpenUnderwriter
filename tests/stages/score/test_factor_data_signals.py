"""Unit tests for signal-to-factor aggregation engine.

Tests the aggregate_factor_from_signals function and supporting helpers
that compute factor scores from signal evaluation results.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Helpers: build mock brain signals and signal results
# ---------------------------------------------------------------------------


def _make_brain_signal(
    signal_id: str,
    factors: list[str] | None = None,
    signal_class: str = "evaluative",
    execution_mode: str = "AUTO",
    scoring_weight: float | None = None,
    scoring_contributions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a minimal brain signal dict for testing."""
    sig: dict[str, Any] = {
        "id": signal_id,
        "name": f"Test signal {signal_id}",
        "factors": factors or [],
        "signal_class": signal_class,
        "work_type": "evaluate",
        "execution_mode": execution_mode,
        "evaluation": {"mechanism": "threshold"},
    }
    if scoring_weight is not None or scoring_contributions is not None:
        scoring: dict[str, Any] = {}
        if scoring_weight is not None:
            scoring["weight"] = scoring_weight
        if scoring_contributions is not None:
            scoring["contributions"] = scoring_contributions
        sig["scoring"] = scoring
    return sig


def _make_signal_result(
    status: str = "TRIGGERED",
    threshold_level: str = "red",
    value: Any = 1.0,
) -> dict[str, Any]:
    """Build a minimal signal result dict."""
    return {
        "status": status,
        "threshold_level": threshold_level,
        "value": value,
        "evidence": "test evidence",
    }


# ---------------------------------------------------------------------------
# Factor canonical mapping
# ---------------------------------------------------------------------------


class TestFactorCanonicalMapping:
    """Tests for FACTOR_SHORT_TO_LONG / FACTOR_LONG_TO_SHORT mappings."""

    def test_short_to_long_f1(self) -> None:
        from do_uw.stages.score.factor_data_signals import FACTOR_SHORT_TO_LONG

        assert FACTOR_SHORT_TO_LONG["F1"] == "F1_prior_litigation"

    def test_short_to_long_f10(self) -> None:
        from do_uw.stages.score.factor_data_signals import FACTOR_SHORT_TO_LONG

        assert FACTOR_SHORT_TO_LONG["F10"] == "F10_officer_stability"

    def test_long_to_short_roundtrip(self) -> None:
        from do_uw.stages.score.factor_data_signals import (
            FACTOR_LONG_TO_SHORT,
            FACTOR_SHORT_TO_LONG,
        )

        for short, long in FACTOR_SHORT_TO_LONG.items():
            assert FACTOR_LONG_TO_SHORT[long] == short

    def test_all_10_factors_present(self) -> None:
        from do_uw.stages.score.factor_data_signals import FACTOR_SHORT_TO_LONG

        assert len(FACTOR_SHORT_TO_LONG) == 10
        for i in range(1, 11):
            assert f"F{i}" in FACTOR_SHORT_TO_LONG


# ---------------------------------------------------------------------------
# Threshold to severity mapping
# ---------------------------------------------------------------------------


class TestThresholdToSeverity:
    def test_red_severity(self) -> None:
        from do_uw.stages.score.factor_data_signals import _threshold_to_severity

        assert _threshold_to_severity("red") == 1.0

    def test_yellow_severity(self) -> None:
        from do_uw.stages.score.factor_data_signals import _threshold_to_severity

        assert _threshold_to_severity("yellow") == 0.5

    def test_clear_severity(self) -> None:
        from do_uw.stages.score.factor_data_signals import _threshold_to_severity

        assert _threshold_to_severity("clear") == 0.0

    def test_empty_severity(self) -> None:
        from do_uw.stages.score.factor_data_signals import _threshold_to_severity

        assert _threshold_to_severity("") == 0.0

    def test_case_insensitive(self) -> None:
        from do_uw.stages.score.factor_data_signals import _threshold_to_severity

        assert _threshold_to_severity("RED") == 1.0
        assert _threshold_to_severity("Yellow") == 0.5


# ---------------------------------------------------------------------------
# Aggregate factor from signals
# ---------------------------------------------------------------------------


class TestAggregateFactorFromSignals:
    """Core aggregation logic tests."""

    def _patch_signals(self, signals: list[dict[str, Any]]):
        """Patch get_signals_for_factor to return given signals."""
        return patch(
            "do_uw.stages.score.factor_data_signals.get_signals_for_factor",
            return_value=signals,
        )

    def test_triggered_red_and_yellow_weighted_sum(self) -> None:
        """5 TRIGGERED signals (3 red, 2 yellow) produce correct weighted score."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        signals = [
            _make_brain_signal("SIG.A", factors=["F1"]),
            _make_brain_signal("SIG.B", factors=["F1"]),
            _make_brain_signal("SIG.C", factors=["F1"]),
            _make_brain_signal("SIG.D", factors=["F1"]),
            _make_brain_signal("SIG.E", factors=["F1"]),
        ]
        results: dict[str, Any] = {
            "SIG.A": _make_signal_result("TRIGGERED", "red"),
            "SIG.B": _make_signal_result("TRIGGERED", "red"),
            "SIG.C": _make_signal_result("TRIGGERED", "red"),
            "SIG.D": _make_signal_result("TRIGGERED", "yellow"),
            "SIG.E": _make_signal_result("TRIGGERED", "yellow"),
        }
        max_points = 20.0

        with self._patch_signals(signals):
            data, contribs = aggregate_factor_from_signals(
                "F1_prior_litigation", results, max_points,
            )

        # weighted_severity = 3*1.0 + 2*0.5 = 4.0, total_weight = 5*1.0 = 5.0
        # score = (4.0 / 5.0) * 20 = 16.0
        assert data["signal_score"] == pytest.approx(16.0)
        assert data["use_signal_path"] is True
        assert len(contribs) == 5

    def test_all_clear_returns_zero(self) -> None:
        """All CLEAR signals produce score 0.0."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        signals = [
            _make_brain_signal("SIG.A", factors=["F1"]),
            _make_brain_signal("SIG.B", factors=["F1"]),
        ]
        results: dict[str, Any] = {
            "SIG.A": _make_signal_result("CLEAR", "clear"),
            "SIG.B": _make_signal_result("CLEAR", "clear"),
        }

        with self._patch_signals(signals):
            data, contribs = aggregate_factor_from_signals(
                "F1_prior_litigation", results, 20.0,
            )

        assert data["signal_score"] == 0.0
        assert data["use_signal_path"] is True

    def test_deferred_skipped_excluded_from_denominator(self) -> None:
        """DEFERRED and SKIPPED signals are excluded from coverage denominator."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        signals = [
            _make_brain_signal("SIG.A", factors=["F1"]),
            _make_brain_signal("SIG.B", factors=["F1"]),
            _make_brain_signal("SIG.C", factors=["F1"]),
            _make_brain_signal("SIG.D", factors=["F1"]),
        ]
        results: dict[str, Any] = {
            "SIG.A": _make_signal_result("TRIGGERED", "red"),
            "SIG.B": _make_signal_result("CLEAR", "clear"),
            "SIG.C": _make_signal_result("DEFERRED", ""),
            "SIG.D": _make_signal_result("SKIPPED", ""),
        }

        with self._patch_signals(signals):
            data, contribs = aggregate_factor_from_signals(
                "F1_prior_litigation", results, 20.0,
            )

        # 2 evaluated (A, B) out of 2 evaluable (excluding C, D)
        # Coverage = 2/2 = 1.0 -- above threshold
        assert data["signal_coverage"] == pytest.approx(1.0)
        assert data["use_signal_path"] is True
        # Only 2 contributions (A and B), not 4
        assert len(contribs) == 2

    def test_low_coverage_disables_signal_path(self) -> None:
        """Coverage < 50% sets use_signal_path=False."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        # 4 signals tagged, but only 1 has a result
        signals = [
            _make_brain_signal("SIG.A", factors=["F1"]),
            _make_brain_signal("SIG.B", factors=["F1"]),
            _make_brain_signal("SIG.C", factors=["F1"]),
            _make_brain_signal("SIG.D", factors=["F1"]),
        ]
        results: dict[str, Any] = {
            "SIG.A": _make_signal_result("TRIGGERED", "red"),
            # B, C, D have no results at all
        }

        with self._patch_signals(signals):
            data, contribs = aggregate_factor_from_signals(
                "F1_prior_litigation", results, 20.0,
            )

        # Coverage = 1/4 = 0.25 < 0.50
        assert data["signal_coverage"] == pytest.approx(0.25)
        assert data["use_signal_path"] is False

    def test_scoring_weight_doubles_contribution(self) -> None:
        """Signal with scoring.weight=2.0 contributes double."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        signals = [
            _make_brain_signal("SIG.A", factors=["F1"], scoring_weight=2.0),
            _make_brain_signal("SIG.B", factors=["F1"]),  # default weight=1.0
        ]
        results: dict[str, Any] = {
            "SIG.A": _make_signal_result("TRIGGERED", "red"),
            "SIG.B": _make_signal_result("TRIGGERED", "red"),
        }

        with self._patch_signals(signals):
            data, contribs = aggregate_factor_from_signals(
                "F1_prior_litigation", results, 20.0,
            )

        # weighted_severity = 2.0*1.0 + 1.0*1.0 = 3.0, total_weight = 2.0 + 1.0 = 3.0
        # score = (3.0 / 3.0) * 20 = 20.0
        assert data["signal_score"] == pytest.approx(20.0)

    def test_multi_factor_signal_contributions(self) -> None:
        """Signal with scoring.contributions maps to correct factor."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        signals = [
            _make_brain_signal(
                "SIG.MULTI",
                factors=["F1", "F2"],
                scoring_contributions=[
                    {"factor": "F1", "weight": 0.5},
                    {"factor": "F2", "weight": 1.5},
                ],
            ),
        ]
        results: dict[str, Any] = {
            "SIG.MULTI": _make_signal_result("TRIGGERED", "red"),
        }

        with self._patch_signals(signals):
            data, contribs = aggregate_factor_from_signals(
                "F1_prior_litigation", results, 20.0,
            )

        # For F1: weight = 0.5 (from contributions), severity=1.0
        # score = (0.5 * 1.0) / 0.5 * 20 = 20.0
        assert data["signal_score"] == pytest.approx(20.0)
        assert len(contribs) == 1
        assert contribs[0]["weight"] == pytest.approx(0.5)

    def test_foundational_signals_excluded(self) -> None:
        """INFO/foundational signals (signal_class != evaluative) excluded from scoring."""
        from do_uw.stages.score.factor_data_signals import (
            get_signals_for_factor,
        )

        all_signals = [
            _make_brain_signal("SIG.A", factors=["F1"], signal_class="evaluative"),
            _make_brain_signal("SIG.B", factors=["F1"], signal_class="foundational"),
        ]

        with patch(
            "do_uw.stages.score.factor_data_signals.load_signals",
            return_value={"signals": all_signals},
        ):
            matched = get_signals_for_factor("F1_prior_litigation")

        # Only evaluative and inference signals should be returned
        signal_ids = [s["id"] for s in matched]
        assert "SIG.A" in signal_ids
        assert "SIG.B" not in signal_ids

    def test_inference_signals_included_at_half_weight(self) -> None:
        """Inference signals (conjunction/absence/contextual) included at weight 0.5."""
        from do_uw.stages.score.factor_data_signals import (
            _get_signal_weight,
        )

        inference_sig = _make_brain_signal(
            "SIG.INF", factors=["F1"], signal_class="inference",
        )

        weight = _get_signal_weight(inference_sig, "F1_prior_litigation")
        assert weight == pytest.approx(0.5)

    def test_no_signals_for_factor_returns_no_signal_path(self) -> None:
        """When no signals are tagged for a factor, use_signal_path is False."""
        from do_uw.stages.score.factor_data_signals import (
            aggregate_factor_from_signals,
        )

        with self._patch_signals([]):
            data, contribs = aggregate_factor_from_signals(
                "F1_prior_litigation", {}, 20.0,
            )

        assert data["use_signal_path"] is False
        assert data["signal_score"] == 0.0
        assert len(contribs) == 0
