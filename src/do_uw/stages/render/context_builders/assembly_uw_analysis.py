"""Assembly builder: UW Analysis context.

Registers uw_analysis context into the HTML template context.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.assembly_registry import register_builder
from do_uw.stages.render.context_builders.uw_analysis import build_uw_analysis_context

logger = logging.getLogger(__name__)


@register_builder
def _assemble_uw_analysis(
    state: AnalysisState,
    context: dict[str, Any],
    chart_dir: Path | None = None,
) -> None:
    """Add uw_analysis context for the experimental layout section."""
    try:
        context["uw_analysis"] = build_uw_analysis_context(
            state, canonical=context.get("_canonical_obj"),
        )
    except Exception:
        logger.warning("UW analysis context builder failed", exc_info=True)
        context["uw_analysis"] = None
