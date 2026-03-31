"""H/A/E radar chart context builder.

Extracts Host, Agent, and Environment composite scores from the
ScoringLensResult on state.scoring.hae_result for radar chart rendering
in Phase 114 templates.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState


def build_hae_context(state: AnalysisState) -> dict[str, Any]:
    """Extract H/A/E composite scores for radar chart rendering."""
    if state.scoring is None:
        return {"hae_available": False}

    hae_result = getattr(state.scoring, "hae_result", None)
    if hae_result is None:
        return {"hae_available": False}

    # ScoringLensResult stores composites as dict with host/agent/environment keys
    composites = getattr(hae_result, "composites", {}) or {}
    host = composites.get("host", 0.0)
    agent = composites.get("agent", 0.0)
    environment = composites.get("environment", 0.0)

    # Also check direct attributes (test mocks may use these)
    if not composites:
        host = getattr(hae_result, "host_composite", 0.0)
        agent = getattr(hae_result, "agent_composite", 0.0)
        environment = getattr(hae_result, "environment_composite", 0.0)

    tier = getattr(hae_result, "tier", "N/A")
    product_score = getattr(hae_result, "product_score", 0.0)
    crf_vetoes = getattr(hae_result, "crf_vetoes", []) or []

    return {
        "hae_available": True,
        "host_composite": host,
        "agent_composite": agent,
        "environment_composite": environment,
        "probability": product_score,
        "tier": str(tier),
        "crf_vetoes": [str(v) for v in crf_vetoes],
        # Radar chart data points (3 axes)
        "radar_labels": ["Host (Structural)", "Agent (Behavioral)", "Environment (External)"],
        "radar_values": [host, agent, environment],
    }
