"""Management credibility pattern classification context builder.

Extends existing credibility_context.py with pattern classification
(Consistent Beater, Sandbagging, Unreliable, Deteriorating) and
quarter-by-quarter table for template rendering.

Phase 136: Forward-Looking and Integration
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import safe_float
from do_uw.stages.render.state_paths import get_forward_looking

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern classification
# ---------------------------------------------------------------------------

_PATTERN_COLOR: dict[str, str] = {
    "CONSISTENT_BEATER": "#16A34A",
    "SANDBAGGING": "#D97706",
    "UNRELIABLE": "#DC2626",
    "DETERIORATING": "#DC2626",
    "INSUFFICIENT_DATA": "#9CA3AF",
    "MIXED": "#6B7280",
}

_PATTERN_LABEL: dict[str, str] = {
    "CONSISTENT_BEATER": "Consistent Beater",
    "SANDBAGGING": "Sandbagging",
    "UNRELIABLE": "Unreliable",
    "DETERIORATING": "Deteriorating",
    "INSUFFICIENT_DATA": "Insufficient Data",
    "MIXED": "Mixed",
}

_BEAT_MISS_CSS: dict[str, str] = {
    "BEAT": "row-beat",
    "MISS": "row-miss",
    "INLINE": "row-inline",
    "UNKNOWN": "row-unknown",
}


def _classify_pattern(
    quarters: list[Any],
    beat_rate: float,
    quarters_assessed: int,
) -> str:
    """Classify management credibility pattern.

    Evaluation order:
    1. Insufficient Data (< 4 quarters)
    2. Deteriorating (most specific pattern)
    3. Unreliable (miss_rate > 25%)
    4. Sandbagging (high beat rate, large magnitude)
    5. Consistent Beater (high beat rate, small magnitude)
    6. Mixed (default)
    """
    if quarters_assessed < 4:
        return "INSUFFICIENT_DATA"

    # Check Deteriorating: last 2+ misses after 4+ consecutive beats
    if len(quarters) >= 6:
        beat_or_miss_seq = [
            getattr(q, "beat_or_miss", "UNKNOWN") for q in quarters
        ]
        # Count trailing misses
        trailing_misses = 0
        for bm in reversed(beat_or_miss_seq):
            if bm == "MISS":
                trailing_misses += 1
            else:
                break
        # Count consecutive beats before the trailing misses
        if trailing_misses >= 2:
            prior_seq = beat_or_miss_seq[: len(beat_or_miss_seq) - trailing_misses]
            consecutive_beats = 0
            for bm in reversed(prior_seq):
                if bm == "BEAT":
                    consecutive_beats += 1
                else:
                    break
            if consecutive_beats >= 4:
                return "DETERIORATING"

    # Check Unreliable: miss_rate > 25%
    miss_rate = 1.0 - (beat_rate / 100.0) if beat_rate <= 100.0 else 0.0
    if miss_rate > 0.25:
        return "UNRELIABLE"

    # Compute average beat magnitude for Sandbagging vs Consistent Beater
    beat_magnitudes: list[float] = []
    for q in quarters:
        bm = getattr(q, "beat_or_miss", "UNKNOWN")
        mag = getattr(q, "magnitude_pct", None)
        if bm == "BEAT" and mag is not None:
            beat_magnitudes.append(safe_float(mag, 0.0))

    avg_magnitude = (
        sum(beat_magnitudes) / len(beat_magnitudes) if beat_magnitudes else 0.0
    )

    # Sandbagging: beat_rate > 80% AND avg magnitude >= 10%
    if beat_rate > 80.0 and avg_magnitude >= 10.0:
        return "SANDBAGGING"

    # Consistent Beater: beat_rate > 75% AND avg magnitude < 10%
    if beat_rate > 75.0 and avg_magnitude < 10.0:
        return "CONSISTENT_BEATER"

    return "MIXED"


def _build_quarter_table(quarters: list[Any]) -> list[dict[str, Any]]:
    """Build quarter table with CSS classes for template rendering."""
    table: list[dict[str, Any]] = []
    for q in quarters:
        guided = getattr(q, "guided_value", "N/A") or "N/A"
        actual = getattr(q, "actual_value", "N/A") or "N/A"
        bm = getattr(q, "beat_or_miss", "UNKNOWN") or "UNKNOWN"
        mag = getattr(q, "magnitude_pct", None)

        # Compute delta string
        delta = ""
        try:
            g_val = safe_float(guided.replace("$", "").replace(",", ""), None)
            a_val = safe_float(actual.replace("$", "").replace(",", ""), None)
            if g_val is not None and a_val is not None:
                diff = a_val - g_val
                delta = f"{diff:+.2f}"
        except (ValueError, AttributeError):
            pass

        magnitude_str = ""
        if mag is not None:
            magnitude_str = f"{safe_float(mag, 0.0):.1f}%"

        table.append({
            "quarter": getattr(q, "quarter", "") or "",
            "guidance": guided,
            "actual": actual,
            "delta": delta,
            "magnitude": magnitude_str,
            "beat_or_miss": bm,
            "row_class": _BEAT_MISS_CSS.get(bm, "row-unknown"),
        })
    return table


def build_forward_credibility(state: AnalysisState) -> dict[str, Any]:
    """Build enhanced credibility context with pattern classification.

    Reads from state.forward_looking.credibility to produce pattern
    classification, quarter table, and cumulative beat/miss string.

    Returns:
        Dict with credibility_available, pattern, pattern_label,
        pattern_color, beat_rate_pct, quarters_assessed, quarter_table,
        cumulative_pattern, source.
    """
    fl = get_forward_looking(state)
    cred = fl.credibility if fl else None

    if cred is None:
        return {
            "credibility_available": False,
            "pattern": "INSUFFICIENT_DATA",
            "pattern_label": "Insufficient Data",
            "pattern_color": _PATTERN_COLOR["INSUFFICIENT_DATA"],
            "beat_rate_pct": "N/A",
            "quarters_assessed": 0,
            "quarter_table": [],
            "cumulative_pattern": "",
            "source": "",
        }

    quarters = getattr(cred, "quarter_records", []) or []
    beat_rate_pct = safe_float(getattr(cred, "beat_rate_pct", 0.0), 0.0)
    quarters_assessed = int(safe_float(getattr(cred, "quarters_assessed", 0), 0))

    # Classify pattern
    pattern = _classify_pattern(quarters, beat_rate_pct, quarters_assessed)
    pattern_label = _PATTERN_LABEL.get(pattern, "Mixed")
    pattern_color = _PATTERN_COLOR.get(pattern, "#6B7280")

    # Build quarter table
    quarter_table = _build_quarter_table(quarters)

    # Build cumulative pattern string (e.g., "BBBMM")
    cumulative = ""
    for q in quarters:
        bm = getattr(q, "beat_or_miss", "UNKNOWN") or "UNKNOWN"
        if bm == "BEAT":
            cumulative += "B"
        elif bm == "MISS":
            cumulative += "M"
        elif bm == "INLINE":
            cumulative += "I"
        else:
            cumulative += "?"

    # Format beat rate
    beat_rate_str = f"{beat_rate_pct:.0f}%" if beat_rate_pct > 0 else "N/A"

    return {
        "credibility_available": True,
        "pattern": pattern,
        "pattern_label": pattern_label,
        "pattern_color": pattern_color,
        "beat_rate_pct": beat_rate_str,
        "quarters_assessed": quarters_assessed,
        "quarter_table": quarter_table,
        "cumulative_pattern": cumulative,
        "source": getattr(cred, "source", "") or "",
    }


__all__ = ["build_forward_credibility"]
