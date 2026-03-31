"""BUILD-08 verification scaffold: H/A/E radar chart context builder.

Tests are xfail until Plan 04 creates the hae_context.py module and
wires build_hae_context into the context builders package.
"""

from __future__ import annotations

import pytest



def test_hae_context_import() -> None:
    """build_hae_context should be importable from context_builders."""
    from do_uw.stages.render.context_builders import build_hae_context  # noqa: F401



def test_hae_context_no_scoring() -> None:
    """State with scoring=None returns hae_available=False."""
    from do_uw.stages.render.context_builders import build_hae_context

    # Minimal state mock with scoring=None
    class _FakeState:
        scoring = None

    result = build_hae_context(_FakeState())  # type: ignore[arg-type]
    assert result["hae_available"] is False



def test_hae_context_no_hae_result() -> None:
    """State with scoring but no hae_result returns hae_available=False."""
    from do_uw.stages.render.context_builders import build_hae_context

    class _FakeScoring:
        hae_result = None

    class _FakeState:
        scoring = _FakeScoring()

    result = build_hae_context(_FakeState())  # type: ignore[arg-type]
    assert result["hae_available"] is False



def test_hae_context_with_data() -> None:
    """State with valid hae_result returns populated context dict."""
    from do_uw.stages.render.context_builders import build_hae_context

    class _FakeHAE:
        host_composite = 0.35
        agent_composite = 0.55
        environment_composite = 0.20
        host_scores = {}
        agent_scores = {}
        environment_scores = {}

    class _FakeScoring:
        hae_result = _FakeHAE()

    class _FakeState:
        scoring = _FakeScoring()

    result = build_hae_context(_FakeState())  # type: ignore[arg-type]
    assert result["hae_available"] is True
    assert "host_composite" in result
    assert "agent_composite" in result
    assert "environment_composite" in result
    assert "radar_labels" in result
    assert "radar_values" in result
