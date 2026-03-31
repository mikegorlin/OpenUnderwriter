"""Quick screen context builder.

Extracts QuickScreenResult from AnalysisState.forward_looking into
template-ready dicts for nuclear triggers, trigger matrix, and
prospective checks rendering.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from do_uw.models.state import AnalysisState


_FLAG_CSS: dict[str, str] = {
    "RED": "flag-red",
    "YELLOW": "flag-yellow",
}

_STATUS_CSS: dict[str, str] = {
    "GREEN": "status-green",
    "YELLOW": "status-yellow",
    "RED": "status-red",
    "UNKNOWN": "status-unknown",
}

_NUCLEAR_TOTAL = 5


def _format_nuclear_triggers(
    state: AnalysisState,
) -> dict[str, Any]:
    """Format nuclear trigger checks with display string."""
    qs = state.forward_looking.quick_screen
    if qs is None:
        return {
            "nuclear_triggers": [],
            "nuclear_fired_count": 0,
            "nuclear_total": _NUCLEAR_TOTAL,
            "nuclear_clean": True,
            "nuclear_display": f"0/{_NUCLEAR_TOTAL} nuclear triggers fired",
        }

    triggers: list[dict[str, Any]] = []
    for nt in qs.nuclear_triggers:
        triggers.append({
            "trigger_id": nt.trigger_id or "",
            "name": nt.name or "",
            "fired": nt.fired,
            "evidence": nt.evidence or "",
            "source": nt.source or "",
            "icon": "fired" if nt.fired else "clean",
        })

    fired = qs.nuclear_fired_count
    total = max(len(qs.nuclear_triggers), _NUCLEAR_TOTAL)
    is_clean = fired == 0

    if is_clean:
        display = f"0/{total} nuclear triggers fired"
    else:
        display = f"{fired}/{total} NUCLEAR TRIGGERS FIRED"

    return {
        "nuclear_triggers": triggers,
        "nuclear_fired_count": fired,
        "nuclear_total": total,
        "nuclear_clean": is_clean,
        "nuclear_display": display,
    }


def _format_trigger_matrix(
    state: AnalysisState,
) -> dict[str, Any]:
    """Format trigger matrix with flag CSS classes and section grouping."""
    qs = state.forward_looking.quick_screen
    if qs is None:
        return {
            "trigger_matrix": [],
            "trigger_matrix_by_section": {},
            "red_count": 0,
            "yellow_count": 0,
            "total_flags": 0,
        }

    matrix: list[dict[str, Any]] = []
    by_section: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in qs.trigger_matrix:
        flag_level = (row.flag_level or "").upper()
        item = {
            "signal_id": row.signal_id or "",
            "signal_name": row.signal_name or "",
            "flag_level": flag_level,
            "flag_class": _FLAG_CSS.get(flag_level, "flag-yellow"),
            "section": row.section or "Other",
            "section_anchor": row.section_anchor or "",
            "do_context": row.do_context or "",
        }
        matrix.append(item)
        section_key = row.section or "Other"
        by_section[section_key].append(item)

    return {
        "trigger_matrix": matrix,
        "trigger_matrix_by_section": dict(by_section),
        "red_count": qs.red_count,
        "yellow_count": qs.yellow_count,
        "total_flags": qs.red_count + qs.yellow_count,
    }


def _format_prospective_checks(
    state: AnalysisState,
) -> dict[str, Any]:
    """Format prospective checks with status CSS classes."""
    qs = state.forward_looking.quick_screen
    if qs is None:
        return {
            "prospective_checks": [],
            "has_prospective_checks": False,
        }

    checks: list[dict[str, Any]] = []
    for pc in qs.prospective_checks:
        status = (pc.status or "UNKNOWN").upper()
        checks.append({
            "check_name": pc.check_name or "",
            "finding": pc.finding or "",
            "status": status,
            "status_class": _STATUS_CSS.get(status, "status-unknown"),
            "source": pc.source or "",
        })

    return {
        "prospective_checks": checks,
        "has_prospective_checks": len(checks) > 0,
    }


def extract_quick_screen(
    state: AnalysisState,
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Extract quick screen data for template rendering.

    Reads from state.forward_looking.quick_screen to produce
    nuclear triggers with clean/fired display, trigger matrix
    grouped by section, and prospective checks with status classes.

    Returns dict with nuclear_triggers, trigger_matrix,
    trigger_matrix_by_section, prospective_checks, and counts.
    """
    result: dict[str, Any] = {}

    qs = state.forward_looking.quick_screen
    result["quick_screen_available"] = qs is not None

    # Nuclear triggers
    result.update(_format_nuclear_triggers(state))

    # Trigger matrix
    result.update(_format_trigger_matrix(state))

    # Prospective checks
    result.update(_format_prospective_checks(state))

    return result
