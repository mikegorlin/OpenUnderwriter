"""Tests for stage failure banner injection into render context.

Verifies that when pipeline stages fail, affected worksheet sections
get amber "Incomplete" banners with the stage name and error message.
"""

from __future__ import annotations

from typing import Any

import pytest

from do_uw.models.common import StageResult, StageStatus
from do_uw.stages.render.context_builders.stage_failure_banners import (
    STAGE_SECTION_MAP,
    inject_stage_failure_banners,
)


def _make_state_with_stages(
    stage_statuses: dict[str, tuple[StageStatus, str | None]],
) -> Any:
    """Build a minimal mock state with given stage statuses.

    Each entry: stage_name -> (status, error_message).
    """
    from unittest.mock import MagicMock

    state = MagicMock()
    stages: dict[str, StageResult] = {}
    for name, (status, error) in stage_statuses.items():
        stages[name] = StageResult(stage=name, status=status, error=error)
    state.stages = stages
    return state


def test_extract_failed_adds_banners_to_affected_sections() -> None:
    """Test 1: extract FAILED adds _stage_banner to financials, governance, market, litigation."""
    state = _make_state_with_stages({
        "extract": (StageStatus.FAILED, "connection timeout"),
    })
    context: dict[str, Any] = {
        "financials": {"revenue": "N/A"},
        "governance": {"board": []},
        "market": {"price": 0},
        "litigation": {"cases": []},
        "company": {"name": "Test"},
    }
    inject_stage_failure_banners(state, context)

    for key in ("financials", "governance", "market", "litigation", "company"):
        assert "_stage_banner" in context[key], f"Missing banner in {key}"
        assert "EXTRACT" in context[key]["_stage_banner"]
        assert "connection timeout" in context[key]["_stage_banner"]


def test_score_failed_adds_banners_to_scoring_sections() -> None:
    """Test 2: score FAILED adds _stage_banner to scoring, factor_scores, risk_tier."""
    state = _make_state_with_stages({
        "score": (StageStatus.FAILED, "missing factor weights"),
    })
    context: dict[str, Any] = {
        "scoring": {"total": 0},
        "factor_scores": {"f1": 0},
        "risk_tier": {"tier": "N/A"},
        "red_flags": {"items": []},
    }
    inject_stage_failure_banners(state, context)

    for key in ("scoring", "factor_scores", "risk_tier", "red_flags"):
        assert "_stage_banner" in context[key], f"Missing banner in {key}"
        assert "SCORE" in context[key]["_stage_banner"]


def test_all_completed_no_banners() -> None:
    """Test 3: All stages COMPLETED adds NO _stage_banner to any section."""
    state = _make_state_with_stages({
        "extract": (StageStatus.COMPLETED, None),
        "analyze": (StageStatus.COMPLETED, None),
        "score": (StageStatus.COMPLETED, None),
        "benchmark": (StageStatus.COMPLETED, None),
    })
    context: dict[str, Any] = {
        "financials": {"revenue": 100},
        "scoring": {"total": 85},
    }
    inject_stage_failure_banners(state, context)

    for section in context.values():
        if isinstance(section, dict):
            assert "_stage_banner" not in section


def test_banner_text_format() -> None:
    """Test 4: Banner text contains stage name and error message."""
    state = _make_state_with_stages({
        "extract": (StageStatus.FAILED, "connection timeout"),
    })
    context: dict[str, Any] = {
        "financials": {"revenue": "N/A"},
    }
    inject_stage_failure_banners(state, context)

    banner = context["financials"]["_stage_banner"]
    assert banner == "Incomplete -- EXTRACT stage did not complete: connection timeout"


def test_missing_context_key_does_not_crash() -> None:
    """Test 5: inject_stage_failure_banners does not crash when context section key doesn't exist."""
    state = _make_state_with_stages({
        "extract": (StageStatus.FAILED, "timeout"),
    })
    # Context is missing all the section keys that extract maps to
    context: dict[str, Any] = {"unrelated": "value"}

    # Should not raise
    inject_stage_failure_banners(state, context)
    assert "_stage_banner" not in context.get("unrelated", {})
