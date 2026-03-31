"""Wave 0 tests for QA-04: threshold_context rendered in red_flags section.

Tests that extract_scoring() includes threshold_context from red_flags.json condition text.
These tests FAIL before Plan 03 implements the fix.
"""
import pytest
from unittest.mock import MagicMock


def _make_mock_state_with_red_flag(flag_id: str, flag_name: str) -> MagicMock:
    state = MagicMock()

    # Set up the red flag mock
    rf = MagicMock()
    rf.flag_id = flag_id
    rf.flag_name = flag_name
    rf.triggered = True
    rf.evidence = ["some evidence"]
    rf.ceiling_applied = None
    rf.max_tier = "4"

    # extract_scoring() uses state.scoring (not state.analysis.scoring)
    sc = state.scoring
    sc.red_flags = [rf]
    sc.factor_scores = []
    sc.patterns_detected = []
    sc.quality_score = 75.0
    sc.composite_score = 75.0
    sc.total_risk_points = 25.0
    sc.tier = None
    sc.binding_ceiling_id = None
    sc.claim_probability = None
    sc.severity_scenarios = None
    sc.risk_type = None
    sc.allegation_mapping = None
    sc.tower_recommendation = None
    sc.calibration_notes = None

    return state


def test_extract_scoring_includes_threshold_context_for_triggered_flag():
    """extract_scoring() red_flags list includes threshold_context from red_flags.json."""
    from do_uw.stages.render.md_renderer_helpers_scoring import extract_scoring
    # CRF-01 is the first CRF trigger — condition text should be in red_flags.json
    state = _make_mock_state_with_red_flag("CRF-01", "Securities Class Action")
    result = extract_scoring(state)
    red_flags = result.get("red_flags", [])
    assert len(red_flags) >= 1
    flag = red_flags[0]
    assert "threshold_context" in flag, "threshold_context key must be present in flag dict"
    assert isinstance(flag["threshold_context"], str)
    # Threshold context should be non-empty for a known CRF trigger
    assert len(flag["threshold_context"]) > 0, "threshold_context should contain CRF condition text"


def test_extract_scoring_threshold_context_empty_for_unknown_crf():
    """Unknown CRF IDs get empty string threshold_context, not KeyError."""
    from do_uw.stages.render.md_renderer_helpers_scoring import extract_scoring
    state = _make_mock_state_with_red_flag("CRF-NONEXISTENT", "Unknown Flag")
    result = extract_scoring(state)
    red_flags = result.get("red_flags", [])
    if red_flags:
        flag = red_flags[0]
        assert flag.get("threshold_context", "") == ""


def test_load_crf_conditions_returns_dict():
    """_load_crf_conditions() loads at least 10 CRF condition entries from red_flags.json."""
    from do_uw.stages.render.md_renderer_helpers_scoring import _load_crf_conditions
    conditions = _load_crf_conditions()
    assert isinstance(conditions, dict)
    assert len(conditions) >= 10, f"Expected >= 10 CRF conditions, got {len(conditions)}"


def test_load_crf_conditions_crf01_has_condition():
    """CRF-01 condition text is non-empty and describes the trigger criterion."""
    from do_uw.stages.render.md_renderer_helpers_scoring import _load_crf_conditions
    conditions = _load_crf_conditions()
    assert "CRF-01" in conditions
    assert len(conditions["CRF-01"]) > 0
