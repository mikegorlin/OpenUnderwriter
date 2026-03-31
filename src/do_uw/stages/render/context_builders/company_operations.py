"""Operational and structural complexity context builders.

Extracts subsidiary structure, workforce distribution, VIE/SPE indicators,
disclosure complexity, and off-balance-sheet exposure into template-ready dicts.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_result,
    safe_get_signals_by_prefix,
)
from do_uw.stages.render.context_builders._signal_consumer import (
    signal_to_display_level,
)
from do_uw.stages.render.formatters import safe_float


def _build_operational_complexity(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Build operational complexity context from BIZ.OPS signal results.

    Reads text_signals for evaluated BIZ.OPS values and constructs
    a template-ready dict with composite score, component data, and
    OPS-01 structural indicators.

    Returns (ops_dict, has_data) tuple for template consumption.
    """
    prof = state.company
    if prof is None:
        return {}, False

    # Subsidiary structure
    sub_data: dict[str, Any] = {}
    if prof.subsidiary_structure is not None:
        sub_data = prof.subsidiary_structure.value or {}

    # Workforce distribution
    wf_data: dict[str, Any] = {}
    if prof.workforce_distribution is not None:
        wf_data = prof.workforce_distribution.value or {}

    # Operational resilience
    res_data: dict[str, Any] = {}
    if prof.operational_resilience is not None:
        res_data = prof.operational_resilience.value or {}

    has_data = bool(sub_data or wf_data or res_data)
    if not has_data:
        return {}, False

    # Compute composite score inline
    jurisdiction_count = sub_data.get("jurisdiction_count", 0) or 0
    high_reg_count = sub_data.get("high_reg_count", 0) or 0
    international_pct = wf_data.get("international_pct", 0) or 0
    unionized_pct = wf_data.get("unionized_pct", 0) or 0
    # Canonical employee count: state.company.employee_count (XBRL/yfinance),
    # fallback to workforce_distribution.total_employees (LLM extraction).
    total_employees = (
        prof.employee_count.value if prof.employee_count is not None
        else wf_data.get("total_employees")
    )
    geo_score = res_data.get("geographic_concentration_score", 0) or 0
    supply_chain_depth = res_data.get("supply_chain_depth", "moderate")
    overall_assessment = res_data.get("overall_assessment", "ADEQUATE")

    # Primary: prof.revenue_segments; fallback: dossier segment_dossiers
    segment_count = len(prof.revenue_segments) if prof.revenue_segments else 0
    if segment_count == 0 and state.dossier and state.dossier.segment_dossiers:
        segment_count = len(state.dossier.segment_dossiers)
    if segment_count == 0 and state.extracted and state.extracted.financials:
        # Check extracted financial segments as last resort
        fin_segs = getattr(state.extracted.financials, "revenue_segments", None)
        if fin_segs:
            segment_count = len(fin_segs)

    # Reconcile supply_chain_depth with complexity score: "shallow"
    # contradicts a high-complexity company.  Pre-compute base score
    # (same formula as the full composite below, minus VIE/dual-class).
    _pre = (min(5, jurisdiction_count // 5) + min(3, high_reg_count // 2)
            + min(3, segment_count // 2)
            + min(3, int(safe_float(international_pct) / 20))
            + (2 if safe_float(unionized_pct) > 20 else 0))
    if supply_chain_depth == "shallow" and _pre >= 8:
        supply_chain_depth = "deep"
    elif supply_chain_depth == "shallow" and _pre >= 5:
        supply_chain_depth = "moderate"

    # VIE presence from text signals
    vie_present = False
    if state.extracted is not None:
        vie_sig = state.extracted.text_signals.get("vie_spe")
        if isinstance(vie_sig, dict) and vie_sig.get("present"):
            vie_present = True

    # Dual-class from governance
    dual_class = False
    if state.extracted is not None and state.extracted.governance is not None:
        dc_val = getattr(state.extracted.governance, "dual_class", None)
        if dc_val is not None:
            raw = dc_val.value if hasattr(dc_val, "value") else dc_val
            dual_class = bool(raw)

    # Compute composite (0-20 scale)
    score = 0
    score += min(5, jurisdiction_count // 5)
    score += min(3, high_reg_count // 2)
    score += min(3, segment_count // 2)
    score += min(3, int(safe_float(international_pct) / 20))
    if vie_present:
        score += 2
    if dual_class:
        score += 2
    if safe_float(unionized_pct) > 20:
        score += 2

    # Enrich with BIZ.OPS signals if available
    ops_signals = safe_get_signals_by_prefix(signal_results, "BIZ.OPS.")
    for sig in ops_signals:
        if sig.status == "TRIGGERED" and sig.value is not None:
            try:
                sig_score = safe_float(sig.value)
                if sig_score > score:
                    score = int(sig_score)
            except (ValueError, TypeError):
                pass

    # Map composite score to level and color
    if score >= 15:
        composite_level = "HIGH"
        composite_color = "red"
    elif score >= 8:
        composite_level = "MODERATE"
        composite_color = "amber"
    else:
        composite_level = "LOW"
        composite_color = "green"

    # OPS-01 structural indicators
    holding_depth = 0
    obs_exposure = 0
    if state.extracted is not None:
        ts = state.extracted.text_signals
        h_sig = ts.get("holding_layers")
        if isinstance(h_sig, dict) and h_sig.get("present"):
            holding_depth = h_sig.get("mention_count", 0)
        obs_sig = ts.get("obs_guarantees")
        if isinstance(obs_sig, dict) and obs_sig.get("present"):
            obs_exposure = obs_sig.get("mention_count", 0)

    indicators = [
        {"name": "VIE / SPE", "present": vie_present, "level": "red" if vie_present else "green"},
        {"name": "Dual-Class", "present": dual_class, "level": "red" if dual_class else "green"},
        {"name": "Holding Depth", "present": holding_depth > 0, "level": "amber" if holding_depth > 0 else "green"},
        {"name": "OBS Exposure", "present": obs_exposure > 0, "level": "amber" if obs_exposure > 0 else "green"},
    ]

    ops_dict: dict[str, Any] = {
        "composite_score": score,
        "composite_level": composite_level,
        "composite_color": composite_color,
        "jurisdiction_count": jurisdiction_count,
        "high_reg_count": high_reg_count,
        "total_employees": total_employees,
        "international_pct": international_pct,
        "unionized_pct": unionized_pct,
        "geographic_concentration_score": geo_score,
        "supply_chain_depth": supply_chain_depth,
        "overall_assessment": overall_assessment,
        "segment_count": segment_count,
        "indicators": indicators,
    }

    return ops_dict, True


def _build_structural_complexity(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], bool]:
    """Build structural complexity context from text_signals.

    Reads 5 text signal dimensions (disclosure_complexity, nongaap_measures,
    related_party_transactions, obs_guarantees, holding_layers) and produces
    template-ready dicts with scores, levels, and colors.

    Returns (complexity_dict, has_data) tuple for template consumption.
    """
    if state.extracted is None:
        return {}, False

    ts = state.extracted.text_signals

    def _signal_info(key: str) -> tuple[int, bool]:
        """Extract mention_count and present from a text signal."""
        sig = ts.get(key, {})
        if isinstance(sig, dict):
            return sig.get("mention_count", 0) or 0, bool(sig.get("present"))
        return 0, False

    def _to_level_color(count: int) -> tuple[str, str]:
        """Map count to level/color."""
        if count >= 3:
            return "HIGH", "red"
        elif count >= 1:
            return "MODERATE", "amber"
        return "LOW", "green"

    # Disclosure complexity
    dc_count, dc_present = _signal_info("disclosure_complexity")
    dc_sig = ts.get("disclosure_complexity", {}) or {}
    rf_count = dc_sig.get("risk_factor_count", 0) if isinstance(dc_sig, dict) else 0
    ca_count = dc_sig.get("critical_accounting_count", 0) if isinstance(dc_sig, dict) else 0
    fls_density = dc_sig.get("fls_density", 0) if isinstance(dc_sig, dict) else 0
    disclosure_score = (rf_count or 0) + (ca_count or 0) + (fls_density or 0)
    dc_level, dc_color = _to_level_color(disclosure_score)

    disclosure_dict = {
        "score": disclosure_score,
        "level": dc_level,
        "color": dc_color,
        "risk_factor_count": rf_count,
        "critical_accounting_count": ca_count,
        "fls_density": fls_density,
        "present": dc_present,
    }

    # Non-GAAP measures
    ng_count, ng_present = _signal_info("nongaap_measures")
    ng_level, ng_color = _to_level_color(ng_count)
    nongaap_dict = {
        "count": ng_count,
        "level": ng_level,
        "color": ng_color,
        "present": ng_present,
    }

    # Related party transactions
    rp_count, rp_present = _signal_info("related_party_transactions")
    rp_level, rp_color = _to_level_color(rp_count)
    related_dict = {
        "count": rp_count,
        "level": rp_level,
        "color": rp_color,
        "present": rp_present,
    }

    # Off-balance-sheet exposure
    obs_count, obs_present = _signal_info("obs_guarantees")
    obs_level, obs_color = _to_level_color(obs_count)
    obs_dict = {
        "score": obs_count,
        "level": obs_level,
        "color": obs_color,
        "present": obs_present,
    }

    # Holding structure depth
    hl_count, hl_present = _signal_info("holding_layers")
    hl_level, hl_color = _to_level_color(hl_count)
    holding_dict = {
        "count": hl_count,
        "level": hl_level,
        "color": hl_color,
        "present": hl_present,
    }

    # Enrich with BIZ.STRUCTURE signals if available
    struct_signals = safe_get_signals_by_prefix(signal_results, "BIZ.STRUCTURE.")
    for sig in struct_signals:
        if sig.status == "TRIGGERED":
            _level = signal_to_display_level(sig.status, sig.threshold_level)

    has_data = any([dc_present, ng_present, rp_present, obs_present, hl_present])

    return {
        "disclosure_complexity": disclosure_dict,
        "nongaap": nongaap_dict,
        "related_parties": related_dict,
        "obs_exposure": obs_dict,
        "holding_structure": holding_dict,
    }, has_data


__all__ = [
    "_build_operational_complexity",
    "_build_structural_complexity",
]
