"""Management credibility context builder.

Extracts CredibilityScore data from AnalysisState.forward_looking
into a template-ready dict for rendering the credibility table.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import format_percentage


_CREDIBILITY_CSS: dict[str, str] = {
    "HIGH": "cred-high",
    "MEDIUM": "cred-medium",
    "LOW": "cred-low",
}

_BEAT_MISS_CSS: dict[str, str] = {
    "BEAT": "row-beat",
    "MISS": "row-miss",
    "INLINE": "row-inline",
    "UNKNOWN": "row-unknown",
}


def extract_credibility(
    state: AnalysisState,
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Extract management credibility data for template rendering.

    Reads from state.forward_looking.credibility to produce
    beat rate, quarter records with CSS classes, and credibility level.

    Returns dict with credibility_available, credibility_level,
    credibility_class, beat_rate_pct, quarters_assessed,
    quarter_records (with row_class for each), and source.
    """
    fl = state.forward_looking
    cred = fl.credibility

    if cred is None:
        return {
            "credibility_available": False,
            "credibility_level": "UNKNOWN",
            "credibility_class": "cred-low",
            "beat_rate_pct": "N/A",
            "quarters_assessed": 0,
            "quarter_records": [],
            "source": "",
        }

    # Format quarter records
    quarter_records: list[dict[str, Any]] = []
    for qr in cred.quarter_records:
        magnitude_str = ""
        if qr.magnitude_pct is not None:
            magnitude_str = format_percentage(qr.magnitude_pct)
        quarter_records.append({
            "quarter": qr.quarter or "",
            "metric": qr.metric or "",
            "guided_value": qr.guided_value or "N/A",
            "actual_value": qr.actual_value or "N/A",
            "beat_or_miss": qr.beat_or_miss or "UNKNOWN",
            "magnitude_pct": magnitude_str,
            "row_class": _BEAT_MISS_CSS.get(qr.beat_or_miss, "row-unknown"),
        })

    level = cred.credibility_level or "UNKNOWN"
    return {
        "credibility_available": True,
        "credibility_level": level,
        "credibility_class": _CREDIBILITY_CSS.get(level, "cred-low"),
        "beat_rate_pct": format_percentage(cred.beat_rate_pct),
        "quarters_assessed": cred.quarters_assessed,
        "quarter_records": quarter_records,
        "source": cred.source or "",
    }
