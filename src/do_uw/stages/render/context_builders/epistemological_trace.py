"""Epistemological trace context builder (Phase 114-01).

Produces per-signal provenance rows for ALL signals (triggered, clean,
skipped), grouped by H/A/E dimension. Each row provides full audit trail
from raw data through evaluation to score contribution.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_consumer import (
    get_signal_result,
)

logger = logging.getLogger(__name__)

# Map confidence level to source type
_SOURCE_TYPE_MAP: dict[str, str] = {
    "HIGH": "audited",
    "MEDIUM": "unaudited",
    "LOW": "web/derived",
}

# Status sort order: TRIGGERED first, then CLEAR, then others
_STATUS_ORDER: dict[str, int] = {
    "TRIGGERED": 0,
    "CLEAR": 1,
    "SKIPPED": 2,
    "INFO": 3,
}


def build_epistemological_trace(state: AnalysisState) -> dict[str, Any]:
    """Build epistemological trace table from AnalysisState.

    Iterates ALL signal_results and builds provenance rows grouped
    by rap_class (host/agent/environment). Within each group, rows
    are sorted with TRIGGERED first, then by signal_id.

    Returns dict with trace_available, rows_by_dimension, trace_total.
    """
    if state.analysis is None or not state.analysis.signal_results:
        return {"trace_available": False}

    signal_results = state.analysis.signal_results
    if not signal_results:
        return {"trace_available": False}

    # Group rows by dimension
    rows_by_dim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    total = 0

    for sid, raw in signal_results.items():
        if not isinstance(raw, dict):
            continue

        view = get_signal_result(signal_results, sid)
        if view is None:
            continue

        total += 1
        confidence = view.confidence or "MEDIUM"
        source_type = _SOURCE_TYPE_MAP.get(confidence, "unknown")
        dimension = view.rap_class or "unknown"

        # Round float values to avoid raw-float noise in rendered output
        display_value = view.value
        if isinstance(display_value, float):
            display_value = round(display_value, 2)

        rows_by_dim[dimension].append({
            "signal_id": view.signal_id,
            "status": view.status,
            "value": display_value,
            "source": view.source,
            "confidence": confidence,
            "source_type": source_type,
            "threshold_level": view.threshold_level,
            "threshold_context": view.threshold_context,
            "rule_origin": view.epistemology_rule_origin,
            "threshold_basis": view.epistemology_threshold_basis,
            "mechanism": view.mechanism,
            "rap_class": view.rap_class,
            "rap_subcategory": view.rap_subcategory,
            "content_type": view.content_type,
        })

    # Sort within each dimension: TRIGGERED first, then by signal_id
    for dim_rows in rows_by_dim.values():
        dim_rows.sort(key=lambda r: (
            _STATUS_ORDER.get(r["status"], 9),
            r["signal_id"],
        ))

    return {
        "trace_available": True,
        "rows_by_dimension": dict(rows_by_dim),
        "trace_total": total,
    }


__all__ = ["build_epistemological_trace"]
