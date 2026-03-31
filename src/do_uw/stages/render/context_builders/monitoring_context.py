"""Monitoring triggers context builder.

Extracts MonitoringTrigger list from AnalysisState.forward_looking
into a template-ready dict for rendering the monitoring triggers table.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation.

Phase 117: Forward-Looking Risk Framework
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState


def extract_monitoring_triggers(
    state: AnalysisState,
    signal_results: dict[str, Any],
) -> dict[str, Any]:
    """Extract monitoring trigger data for template rendering.

    Reads from state.forward_looking.monitoring_triggers to produce
    a list of trigger dicts with name, action, threshold, current value,
    and source.

    Returns dict with monitoring_available, triggers (list of dicts),
    and trigger_count.
    """
    fl = state.forward_looking
    triggers: list[dict[str, Any]] = []

    # Pre-compute filtered SCA count for trigger correction
    from do_uw.stages.render.sca_counter import count_active_genuine_scas
    _filtered_sca_count: int | None = count_active_genuine_scas(state)

    for mt in fl.monitoring_triggers:
        # Fix stale beat-rate values stored as decimal (0.917) formatted as "1%"
        current = mt.current_value or "N/A"
        if mt.trigger_name and "EPS" in (mt.trigger_name or ""):
            import re as _re
            pct_match = _re.search(r'(\d+(?:\.\d+)?)%', current)
            if pct_match:
                pct_val = float(pct_match.group(1))
                if pct_val < 5:  # Clearly a decimal that wasn't converted
                    eg = getattr(getattr(state.extracted, "market", None), "earnings_guidance", None)
                    if eg and eg.beat_rate:
                        raw = eg.beat_rate.value if hasattr(eg.beat_rate, "value") else eg.beat_rate
                        if isinstance(raw, (int, float)):
                            fixed_pct = raw * 100 if raw <= 1.0 else raw
                            current = f"Beat rate: {fixed_pct:.1f}%"
        # Fix stale SCA count: re-derive from filtered litigation data
        if mt.trigger_name and "SCA" in (mt.trigger_name or "") and _filtered_sca_count is not None:
            import re as _re_sca
            sca_match = _re_sca.search(r'(\d+)\s+active\s+SCA', current)
            if sca_match:
                current = current.replace(
                    sca_match.group(0),
                    f"{_filtered_sca_count} active SCA",
                )
        triggers.append({
            "trigger_name": mt.trigger_name or "Unknown",
            "action": mt.action or "",
            "threshold": mt.threshold or "",
            "current_value": current,
            "source": mt.source or "",
        })

    return {
        "monitoring_available": len(triggers) > 0,
        "triggers": triggers,
        "trigger_count": len(triggers),
    }
