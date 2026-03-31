"""Inject amber banners into context sections affected by failed pipeline stages.

When upstream stages (EXTRACT, ANALYZE, SCORE, BENCHMARK) fail, the
worksheet sections that depend on their data should show an informational
banner rather than rendering with stale or empty data. This module maps
stage failures to affected context sections and injects banner text.

Exports:
    STAGE_SECTION_MAP: Mapping of stage names to affected context keys.
    inject_stage_failure_banners: Mutates context dict to add _stage_banner entries.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.common import StageStatus
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Maps each pipeline stage to the context dict keys it populates.
# When a stage fails, all these sections get an amber banner.
STAGE_SECTION_MAP: dict[str, list[str]] = {
    "extract": ["financials", "governance", "market", "litigation", "company"],
    "analyze": ["signal_results", "check_results", "analysis"],
    "score": ["scoring", "factor_scores", "risk_tier", "red_flags"],
    "benchmark": ["peer_comparison", "benchmark"],
}


def inject_stage_failure_banners(
    state: AnalysisState,
    context: dict[str, Any],
) -> None:
    """Add _stage_banner to context sections affected by failed stages.

    Iterates over state.stages looking for FAILED status. For each failed
    stage, injects a human-readable banner string into every affected
    context section (if that section key exists and is a dict).

    The banner text follows the format:
        "Incomplete -- {STAGE} stage did not complete: {error}"
    """
    for stage_name, result in state.stages.items():
        if result.status != StageStatus.FAILED:
            continue
        affected = STAGE_SECTION_MAP.get(stage_name, [])
        for section_key in affected:
            if section_key in context and isinstance(context[section_key], dict):
                context[section_key]["_stage_banner"] = (
                    f"Incomplete -- {stage_name.upper()} stage did not complete: "
                    f"{result.error or 'unknown error'}"
                )
            else:
                logger.debug(
                    "Section %s not in context (stage %s failed)",
                    section_key,
                    stage_name,
                )


__all__ = ["STAGE_SECTION_MAP", "inject_stage_failure_banners"]
