"""Adversarial critique context builder for Devil's Advocate section + inline badges.

Phase 110-02: Extracts AdversarialResult from AnalysisState into template-ready
dict for the Devil's Advocate Jinja2 section and inline caveat badge rendering.

Follows pattern_context.py pattern: returns dict with availability flag,
template-ready data, and summary stats.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState

__all__ = [
    "build_adversarial_context",
]

logger = logging.getLogger(__name__)

# Severity ordering for sorting (higher = more severe)
_SEVERITY_ORDER: dict[str, int] = {
    "warning": 2,
    "caution": 1,
    "info": 0,
}

# Display labels per caveat type
_TYPE_LABELS: dict[str, str] = {
    "false_positive": "Possible FP",
    "false_negative": "Blind Spot",
    "contradiction": "Contradicts",
    "data_completeness": "Data Gap",
}

# CSS color classes per caveat type
_TYPE_COLORS: dict[str, str] = {
    "false_positive": "amber",
    "false_negative": "blue",
    "contradiction": "purple",
    "data_completeness": "gray",
}


def build_adversarial_context(state: AnalysisState) -> dict[str, Any]:
    """Build Devil's Advocate template context from AnalysisState.

    If adversarial data is unavailable (scoring is None or adversarial_result
    is None), returns minimal dict with adversarial_available=False.

    Args:
        state: AnalysisState with scoring.adversarial_result populated.

    Returns:
        Dict with all template data for Devil's Advocate section + caveat_index.
    """
    if state.scoring is None:
        return {"adversarial_available": False}

    adversarial_result = getattr(state.scoring, "adversarial_result", None)
    if adversarial_result is None:
        return {"adversarial_available": False}

    # Build template-ready caveat dicts
    all_caveats: list[dict[str, Any]] = []
    for caveat in adversarial_result.caveats:
        all_caveats.append(_caveat_to_dict(caveat))

    # Sort by severity (warning > caution > info) then confidence descending
    all_caveats.sort(
        key=lambda c: (
            _SEVERITY_ORDER.get(c["severity"], 0),
            c["confidence"],
        ),
        reverse=True,
    )

    # Filter by type
    false_positives = [c for c in all_caveats if c["caveat_type"] == "false_positive"]
    false_negatives = [c for c in all_caveats if c["caveat_type"] == "false_negative"]
    contradictions = [c for c in all_caveats if c["caveat_type"] == "contradiction"]
    completeness_issues = [c for c in all_caveats if c["caveat_type"] == "data_completeness"]

    # Build caveat_index: keyed by target_signal_id for inline badge rendering
    caveat_index: dict[str, list[dict[str, Any]]] = {}
    for caveat_dict in all_caveats:
        sig_id = caveat_dict.get("target_signal_id", "")
        if sig_id:
            if sig_id not in caveat_index:
                caveat_index[sig_id] = []
            caveat_index[sig_id].append(caveat_dict)

    return {
        "adversarial_available": True,
        "caveats": all_caveats,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "contradictions": contradictions,
        "completeness_issues": completeness_issues,
        "summary": adversarial_result.summary,
        "total_caveats": len(all_caveats),
        "caveat_index": caveat_index,
    }


def _caveat_to_dict(caveat: Any) -> dict[str, Any]:
    """Convert a Caveat Pydantic model to a template-ready dict."""
    return {
        "caveat_type": caveat.caveat_type,
        "target_signal_id": caveat.target_signal_id,
        "headline": caveat.headline,
        "explanation": caveat.explanation,
        "confidence": caveat.confidence,
        "confidence_pct": round(caveat.confidence * 100),
        "evidence": caveat.evidence,
        "severity": caveat.severity,
        "narrative_source": caveat.narrative_source,
        "type_label": _TYPE_LABELS.get(caveat.caveat_type, "Caveat"),
        "type_color": _TYPE_COLORS.get(caveat.caveat_type, "gray"),
    }
