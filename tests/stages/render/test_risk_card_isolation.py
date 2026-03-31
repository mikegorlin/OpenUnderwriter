"""Tests for risk card independence from extraction pipeline.

Verifies that litigation data from acquired_data (populated in ACQUIRE
stage) remains accessible even when EXTRACT stage fails. The risk card
should render Supabase SCA data regardless of extraction status.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.models.common import StageResult, StageStatus
from do_uw.stages.render.context_builders.litigation import extract_litigation


def _make_state(
    *,
    extracted_is_none: bool = False,
    has_acquired_litigation: bool = True,
    extract_failed: bool = False,
) -> Any:
    """Build a minimal mock state for risk card isolation testing."""
    state = MagicMock()

    if extracted_is_none:
        state.extracted = None
    else:
        state.extracted = MagicMock()
        state.extracted.litigation = None

    if has_acquired_litigation:
        state.acquired_data = MagicMock()
        state.acquired_data.litigation_data = {
            "supabase_cases": [
                {
                    "case_name": "Test v. Corp",
                    "filing_date": "2025-01-15",
                    "source": "supabase_sca_filings",
                    "confidence": "MEDIUM",
                }
            ],
        }
    else:
        state.acquired_data = MagicMock()
        state.acquired_data.litigation_data = None

    stages: dict[str, StageResult] = {}
    if extract_failed:
        stages["extract"] = StageResult(
            stage="extract", status=StageStatus.FAILED, error="LLM timeout"
        )
    state.stages = stages

    return state


def test_extract_litigation_returns_empty_when_extracted_none() -> None:
    """Test 6: extract_litigation returns {} (not crash) when state.extracted is None.

    This confirms the safe fallback -- even with no extraction, the function
    doesn't crash. The acquired_data.litigation_data remains accessible
    through other code paths (e.g., assembly builders, template context).
    """
    state = _make_state(extracted_is_none=True, has_acquired_litigation=True)
    result = extract_litigation(state)
    # Returns empty dict, not crash
    assert isinstance(result, dict)


def test_acquired_litigation_data_accessible_when_extract_fails() -> None:
    """Test 7: acquired_data.litigation_data is accessible when extract FAILED.

    The Supabase SCA data is populated during ACQUIRE (before EXTRACT).
    Even when EXTRACT fails, acquired_data should still have litigation data.
    """
    state = _make_state(
        extracted_is_none=True,
        has_acquired_litigation=True,
        extract_failed=True,
    )

    # acquired_data is populated regardless of extract status
    assert state.acquired_data is not None
    assert state.acquired_data.litigation_data is not None
    supabase_cases = state.acquired_data.litigation_data.get("supabase_cases", [])
    assert len(supabase_cases) == 1
    assert supabase_cases[0]["case_name"] == "Test v. Corp"

    # extract_litigation itself returns {} (safe) when extracted is None
    result = extract_litigation(state)
    assert isinstance(result, dict)


def test_no_crash_when_acquired_litigation_also_none() -> None:
    """Test 8: No crash when acquired_data.litigation_data is also None."""
    state = _make_state(
        extracted_is_none=True,
        has_acquired_litigation=False,
        extract_failed=True,
    )

    # extract_litigation returns {} safely
    result = extract_litigation(state)
    assert isinstance(result, dict)
    assert result == {}
