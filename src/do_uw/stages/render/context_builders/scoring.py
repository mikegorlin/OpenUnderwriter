"""Scoring context builder for D&O worksheet rendering.

Extracts scoring data from AnalysisState into template-ready dicts.
AI risk, meeting questions, and scoring helpers live in scoring_evaluative.py.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.charts.factor_bars import render_factor_bar
from do_uw.stages.render.formatters import format_percentage

# Re-export evaluative builders for backward compatibility
from do_uw.stages.render.context_builders.scoring_evaluative import (  # noqa: F401
    _load_crf_conditions,
    build_allegation_map,
    build_severity_scenarios,
    build_tower_recommendation,
    extract_ai_risk,
    extract_meeting_questions,
    extract_scoring_do_context,
    format_pattern_description,
    generate_tier_explanation,
)

# Insolvency CRF flag IDs that should be suppressed when company is healthy
_INSOLVENCY_CRF_IDS = {"CRF-13"}
_INSOLVENCY_CRF_KEYWORDS = {"distress", "insolvency", "going concern"}


def _should_suppress_insolvency_crf_flag(
    state: AnalysisState,
    rf: Any,
) -> bool:
    """Suppress insolvency/distress CRF when company is clearly healthy.

    Delegates to the canonical should_suppress_insolvency() in red_flag_gates.py.
    Only applies to CRFs with insolvency-related IDs or keywords.
    """
    from do_uw.stages.score.red_flag_gates import should_suppress_insolvency

    flag_id = getattr(rf, "flag_id", "") or ""
    flag_name = (getattr(rf, "flag_name", "") or "").lower()

    # Only target insolvency-related CRFs
    if flag_id not in _INSOLVENCY_CRF_IDS and not any(
        kw in flag_name for kw in _INSOLVENCY_CRF_KEYWORDS
    ):
        return False

    return should_suppress_insolvency(state)


def _get_distress_metrics(state: AnalysisState) -> tuple[float | None, float | None]:
    """Extract Altman Z-Score and current ratio from state for insolvency check.

    DEPRECATED: Use should_suppress_insolvency() from red_flag_gates.py instead.
    Kept for backward compatibility with crf_bar_context.py imports.
    """
    from do_uw.stages.score.red_flag_gates import should_suppress_insolvency as _ssi

    altman_z: float | None = None
    current_ratio: float | None = None

    if state.extracted and state.extracted.financials:
        fin = state.extracted.financials
        # Altman Z
        distress = getattr(fin, "distress", None)
        if distress is not None:
            az = getattr(distress, "altman_z_score", None)
            if az is not None:
                score_val = getattr(az, "score", None)
                if score_val is not None:
                    raw = getattr(score_val, "value", score_val)
                    try:
                        altman_z = float(raw)
                    except (TypeError, ValueError):
                        pass
        # Current ratio from liquidity
        liq = getattr(fin, "liquidity", None)
        if liq is not None:
            liq_val = liq.value if hasattr(liq, "value") else liq
            if isinstance(liq_val, dict):
                cr = liq_val.get("current_ratio")
                if cr is not None:
                    try:
                        current_ratio = float(cr)
                    except (TypeError, ValueError):
                        pass

    return altman_z, current_ratio


def _rename_f4(fs: Any) -> str:
    """Dynamically rename F4 based on what actually triggered.

    IPO, SPAC, and M&A are very different risk profiles.
    A 40-year-old company shouldn't show 'IPO/SPAC/M&A' when only M&A triggered.
    """
    evidence_text = " ".join(str(e) for e in (fs.evidence or []))
    rules_text = " ".join(str(r) for r in (fs.rules_triggered or []))
    combined = (evidence_text + " " + rules_text).lower()

    has_ipo = any(x in combined for x in ["ipo", "section 11", "offering"])
    has_spac = "spac" in combined
    has_ma = any(x in combined for x in ["m&a", "acquisition", "merger", "goodwill"])
    has_insider = any(x in combined for x in ["insider", "selling", "cluster"])

    parts: list[str] = []
    if has_ipo:
        parts.append("IPO Exposure")
    if has_spac:
        parts.append("SPAC")
    if has_ma:
        parts.append("M&A Exposure")

    if parts:
        return " & ".join(parts)

    # Signal-driven path: check signal contributions for actual trigger type
    contribs = getattr(fs, "signal_contributions", None) or []
    signal_ids = " ".join(str(c.get("signal_id", "") if isinstance(c, dict) else getattr(c, "signal_id", ""))
                         for c in contribs).lower()
    if any(x in signal_ids for x in ["ipo", "offering"]):
        return "IPO Exposure"
    if any(x in signal_ids for x in ["ma_history", "goodwill", "acquisition"]):
        return "M&A Exposure"
    if has_insider or "insider" in signal_ids:
        return "Insider Trading"

    # True fallback
    if fs.points_deducted and fs.points_deducted > 0:
        return "Transaction Risk"
    return "IPO/SPAC/M&A"


def extract_scoring(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Extract scoring data for template.

    Returns tier, composite, factors with full detail, red_flags,
    patterns, allegation_map, claim_probability, severity_scenarios,
    risk_type, calibration_notes.
    """
    sc = state.scoring
    if sc is None:
        return {}

    # Factor scores with evidence
    factors: list[dict[str, Any]] = []
    for fs in sc.factor_scores:
        pct_raw = round(fs.points_deducted / fs.max_points * 100) if fs.max_points > 0 else 0
        if pct_raw >= 75:
            risk_level = "TRIGGERED"
        elif pct_raw >= 50:
            risk_level = "ELEVATED"
        else:
            risk_level = "INFO"
        top_evidence = ""
        if fs.evidence:
            top_evidence = fs.evidence[0]
        sub_comps: list[dict[str, str]] = []
        if fs.sub_components:
            for comp_name, comp_val in fs.sub_components.items():
                sub_comps.append({"name": comp_name.replace("_", " ").title(), "value": f"{comp_val:.1f}"})
        rules = fs.rules_triggered[:5] if fs.rules_triggered else []
        # SVG factor bar (INFO-03)
        bar_svg = render_factor_bar(fs.points_deducted, fs.max_points)
        # Dynamic F4 rename: show what actually triggered, not the full "IPO/SPAC/M&A"
        display_name = fs.factor_name
        if fs.factor_id in ("F4", "F.4") and fs.factor_name and "IPO" in fs.factor_name:
            display_name = _rename_f4(fs)
        factor_dict: dict[str, Any] = {
            "id": fs.factor_id, "name": display_name,
            "score": f"{fs.points_deducted:.1f}", "max": f"{fs.max_points}",
            "pct": pct_raw, "risk_level": risk_level, "weight": f"{fs.max_points}",
            "pct_used": f"{pct_raw}%", "top_evidence": top_evidence,
            "all_evidence": fs.evidence[:5] if fs.evidence else [],
            "sub_components": sub_comps, "rules_triggered": rules,
            "factor_weight_pct": f"{fs.max_points}%",
            "bar_svg": bar_svg,
        }
        # Signal attribution (only for signal-driven factors)
        if fs.scoring_method == "signal_driven":
            sorted_contribs = sorted(fs.signal_contributions, key=lambda c: c.get("contribution", 0.0), reverse=True)
            confidence_pct_val = round(fs.signal_coverage * 100)
            factor_dict["signal_attribution"] = {
                "scoring_method": "signal_driven",
                "top_3_signals": sorted_contribs[:3],
                "full_signal_count": len(fs.signal_contributions),
                "evaluated_count": len(fs.signal_contributions),
                "signal_coverage": fs.signal_coverage,
                "confidence_pct": f"{confidence_pct_val}%",
            }
        factors.append(factor_dict)

    # Annotate factors with F/S role dimensions from risk_model.yaml
    try:
        from pathlib import Path
        import yaml
        risk_model_path = Path(__file__).parent.parent.parent.parent / "brain" / "framework" / "risk_model.yaml"
        if risk_model_path.exists():
            with open(risk_model_path) as f:
                rm = yaml.safe_load(f)
            factor_dims = rm.get("factor_dimensions", {})
            for factor in factors:
                factor["role"] = factor_dims.get(factor["id"], {}).get("role", "")
    except Exception:
        pass

    # Red flags with ceiling detail and CRF condition text
    # Suppress insolvency CRF (CRF-13) when Altman Z > 3.0 and current ratio > 0.5
    # Use resolved ceiling from ceiling_details (size-adjusted) instead of raw config
    crf_conditions = _load_crf_conditions()
    resolved_ceiling = None
    if sc.ceiling_details:
        for cd in sc.ceiling_details:
            resolved_val = getattr(cd, "resolved_ceiling", None) or getattr(cd, "ceiling", None)
            if resolved_val is not None:
                resolved_ceiling = resolved_val
                break
    # Fall back to quality_score if ceiling_details not available (score IS the ceiling-adjusted value)
    if resolved_ceiling is None and sc.quality_score is not None:
        resolved_ceiling = int(sc.quality_score)

    red_flags = [
        {"id": rf.flag_id, "name": rf.flag_name or rf.flag_id,
         "description": "; ".join(rf.evidence) if rf.evidence else "",
         "ceiling": str(resolved_ceiling) if resolved_ceiling else "N/A",
         "max_tier": rf.max_tier or "N/A",
         "threshold_context": crf_conditions.get(rf.flag_id, "")}
        for rf in sc.red_flags
        if rf.triggered and not _should_suppress_insolvency_crf_flag(state, rf)
    ]

    # Patterns
    patterns = [
        {"name": p.pattern_name or p.pattern_id, "description": format_pattern_description(p)}
        for p in sc.patterns_detected
        if p.detected and (p.triggers_matched or (p.score_impact and any(v != 0 for v in p.score_impact.values())))
    ]

    # Risk findings from red_flag_summary
    risk_findings: list[dict[str, str]] = []
    if sc.red_flag_summary and sc.red_flag_summary.items:
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MODERATE": 2, "LOW": 3}
        for fi in sorted(sc.red_flag_summary.items, key=lambda fi: sev_order.get(str(fi.severity), 9)):
            risk_findings.append({
                "description": fi.description, "source": fi.source,
                "severity": str(fi.severity), "scoring_impact": fi.scoring_impact,
            })

    # Apply industry-specific tier ceiling (catches pre-scored data from pipeline)
    tier_display = sc.tier.tier if sc.tier else "N/A"
    tier_action = sc.tier.action if sc.tier else "N/A"
    tier_prob = sc.tier.probability_range if sc.tier else "N/A"
    playbook = getattr(state, "active_playbook_id", "") or ""
    if "BIOTECH" in playbook.upper() and tier_display in ("WIN", "WRITE"):
        # Check pre-revenue
        _has_rev = False
        if state.extracted and state.extracted.financials:
            _ann = getattr(state.extracted.financials, "annual_financials", None)
            if _ann:
                _av = _ann.value if hasattr(_ann, "value") else _ann
                if isinstance(_av, dict):
                    _r = _av.get("revenue")
                    if _r and isinstance(_r, dict) and float(_r.get("value", 0) or 0) > 10_000_000:
                        _has_rev = True
                    elif _r and isinstance(_r, (int, float)) and _r > 10_000_000:
                        _has_rev = True
        if not _has_rev:
            tier_display = "WATCH"
            tier_action = "Pre-revenue biotech ceiling — write carefully, senior review required"
            tier_prob = "8.3-11.9%"

    result: dict[str, Any] = {
        "quality_score": f"{sc.quality_score:.1f}", "composite_score": f"{sc.composite_score:.1f}",
        "total_risk_points": f"{sc.total_risk_points:.1f}",
        "tier": tier_display,
        "factors": factors, "red_flags": red_flags,
        "risk_findings": risk_findings, "patterns": patterns,
    }

    if sc.tier:
        result["tier_action"] = tier_action or "N/A"
        result["tier_probability_range"] = tier_prob or "N/A"
        result["tier_score_range"] = f"{sc.tier.score_range_low} - {sc.tier.score_range_high}"

    result["binding_ceiling"] = sc.binding_ceiling_id or "None"

    if sc.claim_probability:
        cp = sc.claim_probability
        result["claim_probability"] = {
            "band": cp.band.value,
            "range": f"{cp.range_low_pct:.1f}% - {cp.range_high_pct:.1f}%",
            "industry_base": format_percentage(cp.industry_base_rate_pct),
        }

    # D&O context for scoring tables (pass scoring for per-factor detail)
    result.update(extract_scoring_do_context(signal_results, scoring=sc))

    # Tier explanation narrative (Phase 116-05)
    result["tier_explanation"] = generate_tier_explanation(sc)

    # Delegated evaluative builders
    result.update(build_severity_scenarios(sc))
    if sc.risk_type:
        result["risk_type_primary"] = sc.risk_type.primary.value
        result["risk_type_secondary"] = sc.risk_type.secondary.value if sc.risk_type.secondary else None
    result.update(build_allegation_map(sc))
    result.update(build_tower_recommendation(sc))
    if sc.calibration_notes:
        result["calibration_notes"] = sc.calibration_notes

    # Peril-organized scoring (Phase 42)
    try:
        from do_uw.stages.render.scoring_peril_data import extract_peril_scoring
        peril_data = extract_peril_scoring(state)
        if peril_data:
            result["peril_scoring"] = peril_data
    except ImportError:
        pass

    return result


__all__ = [
    "_load_crf_conditions",
    "extract_ai_risk",
    "extract_meeting_questions",
    "extract_scoring",
]
