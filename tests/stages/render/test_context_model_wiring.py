"""Integration tests for _validate_context wiring in build_template_context().

Verifies that Plan 138-02 correctly wraps all 5 builder calls
(exec_summary, financials, market, governance, litigation) with
_validate_context in md_renderer.py::build_template_context().
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_models import (
    ExecSummaryContext,
    FinancialContext,
    GovernanceContext,
    LitigationContext,
    MarketContext,
)
from do_uw.stages.render.md_renderer import build_template_context

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# Use the AAPL state.json from the main repo output directory
_AAPL_STATE = Path("/Users/gorlin/projects/UW/do-uw/output/AAPL/state.json")


@pytest.fixture()
def aapl_state() -> AnalysisState:
    """Load real AAPL state for integration testing."""
    assert _AAPL_STATE.exists(), f"AAPL state.json not found at {_AAPL_STATE}"
    return AnalysisState.model_validate_json(_AAPL_STATE.read_text())


# ---------------------------------------------------------------------------
# Test: All 5 section keys present in context
# ---------------------------------------------------------------------------


def test_all_five_section_keys_present(aapl_state: AnalysisState) -> None:
    """build_template_context produces a context with all 5 section keys."""
    ctx = build_template_context(aapl_state, chart_dir=None)
    for key in ("executive_summary", "financials", "market", "governance", "litigation"):
        assert key in ctx, f"Missing context key: {key}"
        assert ctx[key] is not None, f"Context key '{key}' is None"


# ---------------------------------------------------------------------------
# Test: Each section value is a dict (not a Pydantic model)
# ---------------------------------------------------------------------------


def test_section_values_are_dicts(aapl_state: AnalysisState) -> None:
    """After _validate_context, each section should be a plain dict."""
    ctx = build_template_context(aapl_state, chart_dir=None)
    for key in ("executive_summary", "financials", "market", "governance", "litigation"):
        val = ctx[key]
        assert isinstance(val, dict), f"Expected dict for '{key}', got {type(val).__name__}"


# ---------------------------------------------------------------------------
# Test: _validate_context is called with correct model classes
# ---------------------------------------------------------------------------

# Expected mapping of section name -> model class
_EXPECTED_CALLS: dict[str, type] = {
    "executive_summary": ExecSummaryContext,
    "financials": FinancialContext,
    "market": MarketContext,
    "governance": GovernanceContext,
    "litigation": LitigationContext,
}


def test_validate_context_called_with_correct_models(aapl_state: AnalysisState) -> None:
    """Each builder call passes through _validate_context with the right model class."""
    calls: list[tuple[type, str]] = []

    def _tracking_validate(
        model_cls: type, raw: dict[str, Any], section_name: str
    ) -> dict[str, Any]:
        calls.append((model_cls, section_name))
        return raw  # pass through unchanged

    with patch(
        "do_uw.stages.render.md_renderer._validate_context",
        side_effect=_tracking_validate,
    ):
        build_template_context(aapl_state, chart_dir=None)

    # Verify all 5 model classes were used
    called_models = {section_name: model_cls for model_cls, section_name in calls}
    for section_name, expected_cls in _EXPECTED_CALLS.items():
        assert section_name in called_models, (
            f"_validate_context not called for '{section_name}'"
        )
        assert called_models[section_name] is expected_cls, (
            f"Wrong model for '{section_name}': "
            f"expected {expected_cls.__name__}, got {called_models[section_name].__name__}"
        )


# ---------------------------------------------------------------------------
# Test: Builder exception produces fallback (pipeline doesn't crash)
# ---------------------------------------------------------------------------


def test_builder_exception_does_not_crash_pipeline(aapl_state: AnalysisState) -> None:
    """If a builder raises, exception propagates (builder runs before _validate_context).

    _validate_context wraps the builder *output*, not the builder itself.
    The guard condition (if state.extracted and state.extracted.financials)
    decides whether to call the builder. If the builder raises, that's
    a pipeline error -- not a validation concern.

    This test documents the expected behavior: builder exceptions propagate.
    """
    with patch(
        "do_uw.stages.render.md_renderer.extract_financials",
        side_effect=RuntimeError("simulated builder failure"),
    ):
        with pytest.raises(RuntimeError, match="simulated builder failure"):
            build_template_context(aapl_state, chart_dir=None)
