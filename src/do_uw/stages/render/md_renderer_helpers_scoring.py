"""Scoring extraction -- SHIM.

Canonical implementation moved to context_builders/scoring.py (Phase 58).
This file re-exports for backward compatibility.
"""

from do_uw.stages.render.context_builders.scoring import (
    _load_crf_conditions,
    extract_ai_risk,
    extract_meeting_questions,
    extract_scoring,
)

__all__ = ["extract_ai_risk", "extract_meeting_questions", "extract_scoring"]
