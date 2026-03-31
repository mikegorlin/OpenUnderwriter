"""Gap search result applicator for the ANALYZE stage.

Applies AcquiredData.brain_targeted_search results to SKIPPED SignalResults.
Called after execute_signals() in AnalyzeStage.run() so that signal_results
reflects web evidence where structured sources had no data.

Stage boundary: gap search STORES results in ACQUIRE (brain_targeted_search).
Re-evaluation APPLIES them in ANALYZE (signal_results update).
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def apply_gap_search_results(
    acquired_data: Any,
    analysis_results: Any,
) -> dict[str, int]:
    """Apply brain_targeted_search results to SKIPPED signal_results.

    Only updates checks whose current status is SKIPPED and whose
    gap result has a valid suggested_status (TRIGGERED or CLEAR).
    Non-SKIPPED checks are never overwritten.

    Args:
        acquired_data: AcquiredData instance (has brain_targeted_search).
        analysis_results: AnalysisResults instance (has signal_results dict).

    Returns:
        Summary dict with keys: updated, triggered, clear.
    """
    gap_results = acquired_data.brain_targeted_search
    if not gap_results:
        return {"updated": 0, "triggered": 0, "clear": 0}

    updated = triggered = clear = 0
    for signal_id, gap_result in gap_results.items():
        signal_result = analysis_results.signal_results.get(signal_id)
        if signal_result is None:
            continue  # Check not in results (shouldn't happen but guard it)
        if signal_result.get("status") != "SKIPPED":
            continue  # Only update SKIPPED checks — never overwrite real data

        new_status = gap_result.get("suggested_status")
        if new_status not in ("TRIGGERED", "CLEAR"):
            continue  # No valid suggestion — leave as SKIPPED

        domain = gap_result.get("domain", "web")
        source_str = f"WEB (gap): {domain}" if domain else "WEB (gap)"

        signal_result["status"] = new_status
        signal_result["confidence"] = "LOW"
        signal_result["source"] = source_str
        signal_result["data_status"] = "EVALUATED"
        signal_result["data_status_reason"] = "Resolved via gap search"
        matched = gap_result.get("keywords_matched", False)
        signal_result["evidence"] = (
            f"Resolved via web search: {'confirmed' if matched else 'not confirmed'}"
        )

        updated += 1
        if new_status == "TRIGGERED":
            triggered += 1
        else:
            clear += 1

    if updated > 0:
        logger.info(
            "Gap re-evaluation: %d signals updated (%d TRIGGERED, %d CLEAR)",
            updated,
            triggered,
            clear,
        )

    return {"updated": updated, "triggered": triggered, "clear": clear}


__all__ = ["apply_gap_search_results"]
