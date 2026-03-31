"""Signal heatmap summary context builder (Phase 114-01).

Groups ALL signal results by H/A/E dimension and rap_subcategory
into a summary table showing triggered/clear/info/skipped counts
and coverage percentage per subcategory.
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

# Display order for H/A/E dimensions
_DIM_ORDER = {"host": 0, "agent": 1, "environment": 2}

# Humanize subcategory names
_SUB_LABELS: dict[str, str] = {
    "dependencies": "Business Dependencies",
    "identity": "Company Identity",
    "structure": "Corporate Structure",
    "environment_exposure": "Environment Exposure",
    "governance_structure": "Governance Structure",
    "financials": "Financial Metrics",
    "data_foundation": "Data Foundation",
    "corporate_events": "Corporate Events",
    "financial_conduct": "Financial Conduct",
    "disclosure_conduct": "Disclosure Conduct",
    "executive_conduct": "Executive Conduct",
    "governance_events": "Governance Events",
    "compensation_decisions": "Compensation",
    "litigation_actions": "Litigation Actions",
    "peer_context": "Peer Context",
    "external_warnings": "External Warnings",
    "ownership": "Ownership Structure",
    "defense_posture": "Defense Posture",
    "market_signals": "Market Signals",
    "market_patterns": "Market Patterns",
}


def _humanize_sub(raw: str) -> str:
    """Convert raw subcategory key to human-readable label."""
    return _SUB_LABELS.get(raw, raw.replace("_", " ").title())


def build_heatmap_context(state: AnalysisState) -> dict[str, Any]:
    """Build signal heatmap summary from AnalysisState.

    Returns a summary table grouped by H/A/E dimension, with
    per-subcategory counts (triggered, clear, info, skipped)
    and coverage percentages.
    """
    if state.analysis is None or not state.analysis.signal_results:
        return {"heatmap_available": False}

    signal_results = state.analysis.signal_results
    if not signal_results:
        return {"heatmap_available": False}

    # Aggregate: {rap_class: {rap_subcategory: {status: count}}}
    counts: dict[str, dict[str, dict[str, int]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(int))
    )
    # Track top triggered signals per subcategory for drill-down
    top_triggered: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )

    for sid, raw in signal_results.items():
        if not isinstance(raw, dict):
            continue
        view = get_signal_result(signal_results, sid)
        if view is None:
            continue

        rap_class = (view.rap_class or "unknown").lower()
        rap_sub = view.rap_subcategory or "uncategorized"
        if "." in rap_sub:
            rap_sub = rap_sub.split(".", 1)[1]

        status = (view.status or "SKIPPED").upper()
        # Normalize status buckets
        if status == "TRIGGERED":
            counts[rap_class][rap_sub]["triggered"] += 1
            top_triggered[rap_class][rap_sub].append({
                "id": view.signal_id,
                "evidence": view.evidence or "",
                "level": view.threshold_level or "",
            })
        elif status == "CLEAR":
            counts[rap_class][rap_sub]["clear"] += 1
        elif status == "INFO":
            counts[rap_class][rap_sub]["info"] += 1
        else:
            counts[rap_class][rap_sub]["skipped"] += 1

    if not counts:
        return {"heatmap_available": False}

    # Build summary rows grouped by dimension
    dimensions: list[dict[str, Any]] = []
    dim_totals: dict[str, dict[str, int]] = {}

    for dim in sorted(counts.keys(), key=lambda d: _DIM_ORDER.get(d, 99)):
        dim_label = dim.title()
        rows: list[dict[str, Any]] = []
        dim_total = {"triggered": 0, "clear": 0, "info": 0, "skipped": 0}

        for sub in sorted(counts[dim].keys()):
            c = counts[dim][sub]
            triggered = c.get("triggered", 0)
            clear = c.get("clear", 0)
            info = c.get("info", 0)
            skipped = c.get("skipped", 0)
            total = triggered + clear + info + skipped
            evaluated = triggered + clear + info
            coverage = round(evaluated / total * 100) if total > 0 else 0

            # Top triggered for this subcategory (max 3)
            top = sorted(
                top_triggered[dim].get(sub, []),
                key=lambda t: {"red": 3, "yellow": 2, "orange": 1}.get(
                    t.get("level", ""), 0
                ),
                reverse=True,
            )[:3]

            rows.append({
                "subcategory": _humanize_sub(sub),
                "triggered": triggered,
                "clear": clear,
                "info": info,
                "skipped": skipped,
                "total": total,
                "coverage": coverage,
                "top_triggered": top,
                "has_risk": triggered > 0,
            })

            dim_total["triggered"] += triggered
            dim_total["clear"] += clear
            dim_total["info"] += info
            dim_total["skipped"] += skipped

        # Sort: subcategories with triggered signals first, then by total desc
        rows.sort(key=lambda r: (-r["triggered"], -r["total"]))

        total_all = sum(dim_total.values())
        evaluated_all = dim_total["triggered"] + dim_total["clear"] + dim_total["info"]
        dim_coverage = round(evaluated_all / total_all * 100) if total_all > 0 else 0

        dimensions.append({
            "dimension": dim_label,
            "dimension_key": dim,
            "rows": rows,
            "totals": dim_total,
            "total_signals": total_all,
            "coverage": dim_coverage,
        })
        dim_totals[dim] = dim_total

    # Grand totals
    grand = {"triggered": 0, "clear": 0, "info": 0, "skipped": 0}
    for dt in dim_totals.values():
        for k in grand:
            grand[k] += dt[k]
    grand_total = sum(grand.values())
    grand_evaluated = grand["triggered"] + grand["clear"] + grand["info"]
    grand_coverage = round(grand_evaluated / grand_total * 100) if grand_total > 0 else 0

    return {
        "heatmap_available": True,
        "dimensions": dimensions,
        "grand_totals": grand,
        "grand_total_signals": grand_total,
        "grand_coverage": grand_coverage,
    }


__all__ = ["build_heatmap_context"]
