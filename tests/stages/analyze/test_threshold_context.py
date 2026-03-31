"""Tests for SignalResult.threshold_context field (QA-03).

These tests are RED until Plan 47-02 adds threshold_context to SignalResult
and wires _apply_traceability() to populate it.
"""
import pytest
from do_uw.stages.analyze.signal_results import SignalResult, SignalStatus


def test_signal_result_has_threshold_context_field():
    """SignalResult model has threshold_context field with default empty string."""
    result = SignalResult(signal_id="TEST.CHECK", signal_name="Test Check", status=SignalStatus.CLEAR)
    assert hasattr(result, "threshold_context")
    assert result.threshold_context == ""


def test_threshold_context_empty_for_clear_check():
    """CLEAR checks have empty threshold_context."""
    result = SignalResult(signal_id="TEST.CHECK", signal_name="Test Check", status=SignalStatus.CLEAR)
    result.threshold_context = ""
    assert result.threshold_context == ""


def test_threshold_context_empty_for_skipped_check():
    """SKIPPED checks have empty threshold_context."""
    result = SignalResult(signal_id="TEST.CHECK", signal_name="Test Check", status=SignalStatus.SKIPPED)
    assert result.threshold_context == ""


def test_threshold_context_populated_for_triggered_check():
    """TRIGGERED checks should have non-empty threshold_context after _apply_traceability()."""
    # This test becomes GREEN when _apply_traceability() populates threshold_context
    from do_uw.stages.analyze.signal_engine import _apply_traceability
    result = SignalResult(
        signal_id="GOV.BOARD.tenure",
        signal_name="Board Tenure",
        status=SignalStatus.TRIGGERED,
        threshold_level="red",
    )
    signal_def = {
        "id": "GOV.BOARD.tenure",
        "threshold": {
            "red": "Average tenure >15 years (entrenchment risk)",
            "yellow": "Average tenure >10 years",
        },
    }
    result = _apply_traceability(result, signal_def, "threshold")
    assert result.threshold_context != ""
    assert "red" in result.threshold_context
    assert "entrenchment" in result.threshold_context


def test_threshold_context_format():
    """threshold_context format: '{level}: {criterion text}'."""
    from do_uw.stages.analyze.signal_engine import _apply_traceability
    result = SignalResult(
        signal_id="GOV.BOARD.tenure",
        signal_name="Board Tenure",
        status=SignalStatus.TRIGGERED,
        threshold_level="yellow",
    )
    signal_def = {
        "id": "GOV.BOARD.tenure",
        "threshold": {"yellow": "Average tenure >10 years"},
    }
    result = _apply_traceability(result, signal_def, "threshold")
    assert result.threshold_context.startswith("yellow:")
