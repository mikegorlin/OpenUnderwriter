"""Context builder for dual-voice commentary (Phase 130-02).

Reads pre_computed_commentary from AnalysisState and adds a
``commentary`` dict to the template context. Each key is a section
ID mapping to a serialized SectionCommentary dict.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.assembly_registry import register_builder

logger = logging.getLogger(__name__)

_SECTION_IDS = (
    "executive_brief",
    "financial",
    "market",
    "governance",
    "litigation",
    "scoring",
    "company",
    "meeting_prep",
)


@register_builder
def _build_commentary_context(
    state: AnalysisState,
    context: dict[str, Any],
    chart_dir: Path | None,
) -> None:
    """Add dual-voice commentary to template context."""
    if state.analysis and state.analysis.pre_computed_commentary:
        pcc = state.analysis.pre_computed_commentary
        commentary: dict[str, dict[str, Any]] = {}
        for section_id in _SECTION_IDS:
            sc = getattr(pcc, section_id, None)
            if sc is not None:
                commentary[section_id] = {
                    "what_was_said": sc.what_was_said,
                    "underwriting_commentary": sc.underwriting_commentary,
                    "confidence": sc.confidence,
                    "hallucination_warnings": sc.hallucination_warnings,
                }
        context["commentary"] = commentary
    else:
        context["commentary"] = {}


__all__ = ["_build_commentary_context"]
