"""Pipeline status context builder for audit section (Phase 144-01).

Reads state.stages and produces structured data for rendering a
pipeline execution status table in the worksheet audit section.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import PIPELINE_STAGES, AnalysisState

_STATUS_CLASS_MAP: dict[str, str] = {
    "completed": "status-ok",
    "failed": "status-fail",
    "skipped": "status-skip",
    "pending": "status-pending",
    "running": "status-running",
}


def build_pipeline_status_context(state: AnalysisState) -> list[dict[str, Any]]:
    """Build pipeline execution status for audit section rendering.

    Returns a list of dicts (one per stage) with keys:
        stage, status, duration, error, status_class

    Always returns all 7 stages in pipeline order, even if some are PENDING.
    """
    rows: list[dict[str, Any]] = []
    for stage_name in PIPELINE_STAGES:
        result = state.stages.get(stage_name)
        if result is not None:
            status = result.status.value
            duration = result.duration_seconds
            error = result.error
        else:
            status = "pending"
            duration = None
            error = None

        rows.append({
            "stage": stage_name,
            "status": status,
            "duration": duration,
            "error": error,
            "status_class": _STATUS_CLASS_MAP.get(status, "status-pending"),
        })

    return rows
