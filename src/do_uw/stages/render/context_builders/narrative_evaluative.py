"""Evaluative narrative builders -- D&O implication conditions, 5-layer
narrative architecture (verdict, thesis, evidence grid, implications,
deep context).

Extracted from narrative.py (Phase 113-04). Signal access migrated from
raw dict access to _signal_fallback typed consumer API.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._signal_fallback import (
    safe_get_signals_by_prefix,
)


def check_implication_condition(
    state: AnalysisState, section_id: str, condition: str,
    *, _derive_density: Any = None,
) -> bool:
    """Check whether a D&O implication condition is met for a section.

    Uses _signal_fallback typed consumer API for signal checks instead of
    raw dict access.
    """
    from do_uw.stages.render.context_builders.narrative import _derive_section_density
    density_fn = _derive_density or _derive_section_density
    density = density_fn(state, section_id)

    # Executive summary conditions
    if condition == "tier_high":
        if state.scoring and state.scoring.tier:
            tier = str(state.scoring.tier.tier.value).upper()
            return tier in ("WALK", "NO_TOUCH", "WATCH")
        return False
    if condition == "negative_findings":
        if state.scoring and state.scoring.tier:
            tier = str(state.scoring.tier.tier.value).upper()
            if tier in ("WIN", "COMPETE"):
                return False
        if state.executive_summary and state.executive_summary.key_findings:
            return bool(state.executive_summary.key_findings.negatives)
        return False

    # Simple density-driven conditions
    density_elevated = {"ELEVATED", "CRITICAL"}
    _DENSITY_CONDITIONS = {
        "regulatory_heavy", "concentration_risk", "earnings_quality",
        "board_independence", "active_securities", "settlement_history",
        "stock_volatility", "analyst_downgrades", "high_peril",
        "hazard_amplification", "ai_exposure",
    }
    if condition in _DENSITY_CONDITIONS:
        return density in density_elevated
    if condition == "distress_indicators":
        return density == "CRITICAL"
    if condition == "international_ops":
        if state.company and state.company.identity:
            ident = state.company.identity
            if ident.state_of_incorporation and ident.state_of_incorporation.value:
                return False
        return True

    # Signal-driven conditions -- use typed consumer API
    sr = state.analysis.signal_results if state.analysis else None
    _SIGNAL_PATTERNS: dict[str, tuple[list[str], set[str]]] = {
        "restatement_risk": (["restatement", "accounting"], {"TRIGGERED"}),
        "compensation_excess": (["compensation", "pay"], {"TRIGGERED", "ELEVATED"}),
        "insider_activity": (["insider"], {"TRIGGERED"}),
        "regulatory_action": (["enforcement", "sec_action"], {"TRIGGERED"}),
        "short_interest": (["short"], {"TRIGGERED", "ELEVATED"}),
        "data_privacy": (["privacy", "cyber"], {"TRIGGERED", "ELEVATED"}),
    }
    if condition in _SIGNAL_PATTERNS:
        keywords, statuses = _SIGNAL_PATTERNS[condition]
        if sr:
            for key in sr:
                key_lower = key.lower()
                if any(kw in key_lower for kw in keywords):
                    raw = sr[key]
                    if isinstance(raw, dict) and raw.get("status") in statuses:
                        return True
        return False

    # Default: include for ELEVATED+ sections
    return density in density_elevated


# 5-Layer Narrative Architecture (NARR-01, NARR-05, NARR-07)


def determine_verdict(state: AnalysisState, section_id: str, config: dict[str, Any]) -> str:
    """Determine verdict from YAML config: tier_overrides > count > density."""
    from do_uw.stages.render.context_builders.narrative import _derive_section_density
    verdict_cfg = config.get("verdict", {})
    thresholds = verdict_cfg.get("thresholds", {})
    tier_overrides = verdict_cfg.get("tier_overrides", {})
    if tier_overrides and section_id in ("executive_summary", "scoring"):
        tier = ""
        if state.scoring and state.scoring.tier:
            tier = str(state.scoring.tier.tier.value).upper().replace(" ", "_")
        if tier and tier in tier_overrides:
            return str(tier_overrides[tier])
    count_overrides = verdict_cfg.get("count_overrides", {})
    if count_overrides and section_id == "red_flags":
        flags: list[Any] = []
        if state.scoring and state.scoring.red_flags:
            flags = state.scoring.red_flags
        n = len(flags)
        if n >= count_overrides.get("critical_threshold", 5):
            return "CRITICAL"
        if n >= count_overrides.get("concerning_threshold", 2):
            return "CONCERNING"
        return "FAVORABLE"
    return str(thresholds.get(_derive_section_density(state, section_id), "NEUTRAL"))


def build_thesis(state: AnalysisState, section_id: str, config: dict[str, Any]) -> str:
    """Density-driven thesis sentence with confidence-calibrated verbs (NARR-03)."""
    from do_uw.stages.render.context_builders.narrative import (
        _SECTION_NAMES, _derive_section_density, _get_narrative_text, _strip_md,
    )
    if not config.get("thesis_template"):
        return ""
    from do_uw.stages.render.context_builders._bull_bear import calibrate_verb, derive_section_confidence
    density = _derive_section_density(state, section_id)
    name = _SECTION_NAMES.get(section_id, section_id.replace("_", " ").title())
    narrative = _get_narrative_text(state, section_id)
    verb = calibrate_verb(derive_section_confidence(state, section_id))
    if density == "CRITICAL":
        thesis = f"{name} assessment {verb} critical risk factors requiring immediate underwriting attention."
    elif density == "ELEVATED":
        thesis = f"{name} {verb} elevated concern signals that may affect D&O risk profile."
    else:
        thesis = f"{name} {verb} a stable risk profile within standard parameters."
    if narrative:
        clean = _strip_md(narrative)
        parts = [s.strip() for s in clean.replace("\n", " ").split(".") if s.strip()]
        if parts and len(thesis) + len(parts[0]) + 2 < 300:
            thesis = f"{thesis} {parts[0]}."
    return thesis


def collect_evidence(state: AnalysisState, section_id: str) -> list[dict[str, str]]:
    """Collect TRIGGERED/ELEVATED signal evidence for evidence grid."""
    from do_uw.stages.render.context_builders.narrative import (
        _TEMPLATE_KEYS, _derive_section_density,
    )
    items: list[dict[str, str]] = []
    density = _derive_section_density(state, section_id)
    if state.analysis and state.analysis.signal_results:
        from do_uw.stages.render.html_signals import _group_signals_by_section
        grouped = _group_signals_by_section(state.analysis.signal_results, {})
        tpl_key = _TEMPLATE_KEYS.get(section_id, section_id)
        for sig in grouped.get(tpl_key, []):
            if not isinstance(sig, dict):
                continue
            status = sig.get("status", "")
            if status in ("TRIGGERED", "ELEVATED"):
                items.append({
                    "label": sig.get("signal_name", sig.get("signal_id", "Unknown")),
                    "value": sig.get("evidence", status),
                    "source": sig.get("filing_ref", ""),
                    "severity": "HIGH" if status == "TRIGGERED" else "MEDIUM",
                })
    if not items and density in ("CRITICAL", "ELEVATED"):
        sev = "HIGH" if density == "CRITICAL" else "MEDIUM"
        items.append({"label": "Section Risk Level", "value": density,
                       "source": "Density Analysis", "severity": sev})
    return items[:8]


def collect_deep_context(state: AnalysisState, section_id: str) -> list[dict[str, str]]:
    """Collect deep context: full assessment + SCR framework."""
    from do_uw.stages.render.context_builders.narrative import (
        _build_scr_for_section, _get_narrative_text, _strip_md,
    )
    items: list[dict[str, str]] = []
    narrative = _get_narrative_text(state, section_id)
    if narrative:
        clean = _strip_md(narrative)
        # FIX-04: Never truncate analytical content — deep context is inside
        # a collapsible <details> element, so full text is appropriate.
        # Previous 500-char truncation lost critical governance detail for
        # complex companies with extensive board/comp/litigation narratives.
        items.append({"label": "Full Assessment", "content": clean})
    scr = _build_scr_for_section(state, section_id)
    if scr:
        items.append({"label": "Analytical Framework",
                       "content": f"Situation: {scr['situation']} Complication: {scr['complication']} Resolution: {scr['resolution']}"})
    return items
