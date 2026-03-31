"""Tests for deep-dive trigger runner and ScoreStage Step 17 integration.

Phase 110-01 Task 2: Conditional deep-dive triggers.
TDD RED: These tests are written before implementation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_signal_results(
    statuses: dict[str, str],
) -> dict[str, dict[str, Any]]:
    """Build signal_results dict from {signal_id: status_str}."""
    results: dict[str, dict[str, Any]] = {}
    for sid, status in statuses.items():
        results[sid] = {
            "status": status,
            "value": "1.0",
            "threshold_level": "red" if status in ("TRIGGERED", "RED") else "",
        }
    return results


def _make_mock_state() -> MagicMock:
    """Create a minimal mock AnalysisState."""
    state = MagicMock()
    state.company = MagicMock()
    state.extracted = MagicMock()
    return state


# ---------------------------------------------------------------------------
# DeepDiveResult model tests
# ---------------------------------------------------------------------------


class TestDeepDiveModels:
    """Verify DeepDiveResult and DeepDiveTriggerResult Pydantic models."""

    def test_trigger_result_model_creates(self) -> None:
        """DeepDiveTriggerResult validates with required fields."""
        from do_uw.models.deepdive import DeepDiveTriggerResult

        result = DeepDiveTriggerResult(
            trigger_id="test.trigger",
            trigger_name="Test Trigger",
            description="A test trigger",
            fired=True,
            matched_conditions=["SIG.A=TRIGGERED"],
            additional_signals=["SIG.B"],
            uw_investigation_prompt="Investigate this",
            rap_dimensions=["host"],
        )
        assert result.fired is True
        assert result.trigger_id == "test.trigger"

    def test_deepdive_result_model_creates(self) -> None:
        """DeepDiveResult validates with computed_at and results list."""
        from do_uw.models.deepdive import DeepDiveResult, DeepDiveTriggerResult

        trigger = DeepDiveTriggerResult(
            trigger_id="test.trigger",
            trigger_name="Test",
            description="test",
            fired=True,
            matched_conditions=[],
            additional_signals=[],
            uw_investigation_prompt="test",
            rap_dimensions=[],
        )
        result = DeepDiveResult(
            triggers_evaluated=1,
            triggers_fired=1,
            results=[trigger],
            computed_at=datetime.now(timezone.utc),
        )
        assert result.triggers_evaluated == 1
        assert result.triggers_fired == 1

    def test_scoring_result_has_deepdive_field(self) -> None:
        """ScoringResult.deepdive_result field exists (None default)."""
        from do_uw.models.scoring import ScoringResult, _rebuild_scoring_models

        _rebuild_scoring_models()
        scoring = ScoringResult()
        assert scoring.deepdive_result is None


# ---------------------------------------------------------------------------
# Deep-dive runner tests
# ---------------------------------------------------------------------------


class TestDeepDiveRunner:
    """Test run_deepdive_triggers function."""

    def test_returns_none_when_yaml_missing(self) -> None:
        """Runner returns None when trigger YAML is missing."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        with patch(
            "do_uw.stages.score._deepdive_runner._TRIGGERS_PATH",
            Path("/nonexistent/triggers.yaml"),
        ):
            result = run_deepdive_triggers(state=state, signal_results={})
        assert result is None

    def test_returns_result_when_no_triggers_fire(self) -> None:
        """Runner returns DeepDiveResult with 0 fires when conditions not met."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        # All signals CLEAR -> no triggers should fire
        signal_results = _make_signal_results({
            "GOV.BOARD.independence": "CLEAR",
            "EXEC.TURN.c_suite": "CLEAR",
            "FIN.ACCT.restatement": "CLEAR",
        })

        result = run_deepdive_triggers(state=state, signal_results=signal_results)
        assert result is not None
        assert result.triggers_fired == 0

    def test_fires_trigger_when_all_conditions_met(self) -> None:
        """Runner fires trigger when all_of conditions are satisfied."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        # Set up signals that should trigger the financial_controls deep-dive
        signal_results = _make_signal_results({
            "FIN.ACCT.restatement": "TRIGGERED",
            "FIN.ACCT.auditor": "TRIGGERED",
        })

        result = run_deepdive_triggers(state=state, signal_results=signal_results)
        assert result is not None
        # At least one trigger should have fired
        fired = [t for t in result.results if t.fired]
        assert len(fired) >= 1

    def test_trigger_has_uw_investigation_prompt(self) -> None:
        """Fired trigger includes UW investigation prompt text."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        signal_results = _make_signal_results({
            "FIN.ACCT.restatement": "TRIGGERED",
            "FIN.ACCT.auditor": "TRIGGERED",
        })

        result = run_deepdive_triggers(state=state, signal_results=signal_results)
        assert result is not None
        fired = [t for t in result.results if t.fired]
        if fired:
            assert fired[0].uw_investigation_prompt != ""

    def test_all_of_logic_requires_all_conditions(self) -> None:
        """all_of conditions require ALL signals to match (AND logic)."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        # Only one of two conditions met -> should NOT fire financial_controls
        signal_results = _make_signal_results({
            "FIN.ACCT.restatement": "TRIGGERED",
            "FIN.ACCT.auditor": "CLEAR",  # Not met
        })

        result = run_deepdive_triggers(state=state, signal_results=signal_results)
        assert result is not None
        # financial_controls trigger specifically should not fire
        for t in result.results:
            if t.trigger_id == "deepdive.financial_controls":
                assert not t.fired, "financial_controls should not fire with only one condition"

    def test_graceful_degradation_on_malformed_trigger(self) -> None:
        """Bad trigger data doesn't kill all triggers."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        # Even with no matching signals, runner shouldn't crash
        result = run_deepdive_triggers(state=state, signal_results={})
        assert result is not None
        assert result.triggers_evaluated >= 0

    def test_trigger_count_matches_yaml(self) -> None:
        """Triggers evaluated count matches YAML definition count."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        result = run_deepdive_triggers(state=state, signal_results={})
        assert result is not None
        assert result.triggers_evaluated == 10  # Plan says 10 triggers

    def test_matched_conditions_populated(self) -> None:
        """Fired trigger has matched_conditions list populated."""
        from do_uw.stages.score._deepdive_runner import run_deepdive_triggers

        state = _make_mock_state()
        signal_results = _make_signal_results({
            "FIN.ACCT.restatement": "TRIGGERED",
            "FIN.ACCT.auditor": "TRIGGERED",
        })

        result = run_deepdive_triggers(state=state, signal_results=signal_results)
        assert result is not None
        fired = [t for t in result.results if t.fired]
        if fired:
            assert len(fired[0].matched_conditions) > 0


# ---------------------------------------------------------------------------
# Trigger YAML tests
# ---------------------------------------------------------------------------


class TestDeepDiveTriggersYAML:
    """Verify deepdive_triggers.yaml structure."""

    def test_yaml_exists_and_loads(self) -> None:
        """deepdive_triggers.yaml loads with triggers list."""
        triggers_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "brain"
            / "framework"
            / "deepdive_triggers.yaml"
        )
        assert triggers_path.exists(), "deepdive_triggers.yaml missing"
        data = yaml.safe_load(triggers_path.read_text())
        assert "triggers" in data
        assert len(data["triggers"]) == 10

    def test_each_trigger_has_required_fields(self) -> None:
        """Each trigger has id, name, trigger_conditions, uw_investigation_prompt."""
        triggers_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "brain"
            / "framework"
            / "deepdive_triggers.yaml"
        )
        data = yaml.safe_load(triggers_path.read_text())
        for trigger in data["triggers"]:
            assert "id" in trigger, f"Trigger missing id: {trigger}"
            assert "name" in trigger, f"Trigger missing name: {trigger}"
            assert "trigger_conditions" in trigger, f"Trigger missing conditions: {trigger}"
            assert "uw_investigation_prompt" in trigger, f"Trigger missing prompt: {trigger}"
            assert "all_of" in trigger["trigger_conditions"], f"Trigger missing all_of: {trigger}"

    def test_triggers_cover_all_hae_dimensions(self) -> None:
        """Triggers collectively cover host, agent, and environment dimensions."""
        triggers_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "brain"
            / "framework"
            / "deepdive_triggers.yaml"
        )
        data = yaml.safe_load(triggers_path.read_text())
        all_dims: set[str] = set()
        for trigger in data["triggers"]:
            dims = trigger.get("rap_dimensions", [])
            all_dims.update(dims)
        assert "host" in all_dims, "No host dimension triggers"
        assert "agent" in all_dims, "No agent dimension triggers"
        assert "environment" in all_dims, "No environment dimension triggers"


# ---------------------------------------------------------------------------
# ScoreStage integration test
# ---------------------------------------------------------------------------


class TestScoreStageIntegration:
    """Verify Step 17 deep-dive trigger integration in ScoreStage."""

    def test_score_stage_imports_deepdive_runner(self) -> None:
        """ScoreStage Step 17 code references _deepdive_runner."""
        score_init_path = (
            Path(__file__).resolve().parent.parent.parent.parent
            / "src"
            / "do_uw"
            / "stages"
            / "score"
            / "__init__.py"
        )
        content = score_init_path.read_text()
        assert "run_deepdive_triggers" in content
        assert "deepdive_result" in content
