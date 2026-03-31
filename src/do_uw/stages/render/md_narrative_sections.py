"""Narrative section generators for D&O underwriting worksheet.

Split from md_narrative.py for 500-line compliance.
Contains governance, litigation, scoring, and company narratives.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.formatters import format_currency, format_percentage, safe_float


def _sv(obj: Any, field: str, default: Any = None) -> Any:
    """Safely get a SourcedValue .value from a Pydantic model or dict."""
    if isinstance(obj, dict):
        raw = obj.get(field)
        if isinstance(raw, dict):
            return raw.get("value", default)
        return raw if raw is not None else default
    attr = getattr(obj, field, None)
    if attr is None:
        return default
    return getattr(attr, "value", attr)


def governance_narrative(
    state_or_dict: AnalysisState | dict[str, Any],
) -> str:
    """Generate interpretive governance narrative."""
    if isinstance(state_or_dict, dict):
        return _governance_narrative_from_dict(state_or_dict)
    return _governance_narrative_from_state(state_or_dict)


def _governance_narrative_from_state(state: AnalysisState) -> str:
    """Generate governance narrative from typed state data."""
    if not state.extracted or not state.extracted.governance:
        return ""
    gov = state.extracted.governance
    board = gov.board
    comp = gov.comp_analysis
    gs = gov.governance_score
    parts: list[str] = []

    # Overall governance score
    if gs.total_score is not None:
        score_val = safe_float(gs.total_score.value)
        label = f"{score_val:.0f}/100"
        if score_val >= 80:
            parts.append(
                f"Governance quality is strong ({label}), reflecting"
                " robust board independence, appropriate compensation"
                " practices, and effective oversight structures."
            )
        elif score_val >= 60:
            parts.append(
                f"Governance quality is moderate ({label}). Core"
                " structural elements are sound but secondary indicators"
                " suggest areas for improvement."
            )
        elif score_val >= 40:
            parts.append(
                f"Governance quality is below average ({label}),"
                " indicating structural weaknesses that elevate D&O"
                " claim risk through potential oversight failures."
            )
        else:
            parts.append(
                f"**Governance concern** ({label}): Weak governance"
                " structures materially increase the probability of"
                " shareholder derivative actions and regulatory scrutiny."
            )

    # Board composition
    if board.independence_ratio is not None:
        ind_val = safe_float(board.independence_ratio.value) * 100
        ind_str = format_percentage(ind_val)
        if ind_val >= 80:
            parts.append(
                f"Board independence of {ind_str} substantially exceeds"
                " the NYSE minimum of 50% and typical large-cap median"
                " of approximately 73%."
            )
        elif ind_val < 50:
            parts.append(
                f"Board independence of {ind_str} is below NYSE listing"
                " requirements, creating significant governance"
                " concentration risk."
            )

    if board.size is not None:
        size = int(board.size.value)
        if size < 5:
            parts.append(
                f"Board size of {size} is unusually small, limiting"
                " committee capacity and oversight effectiveness."
            )

    # CEO/Chair duality
    if board.ceo_chair_duality and board.ceo_chair_duality.value:
        parts.append(
            "CEO/Chair duality concentrates decision-making authority"
            " and reduces board independence in practice -- a common"
            " factor in derivative litigation alleging inadequate"
            " board oversight."
        )

    # Overboarding
    if board.overboarded_count is not None and int(board.overboarded_count.value) > 0:
        count = int(board.overboarded_count.value)
        if count > 0:
            parts.append(
                f"{count} director(s) serve on 4+ public boards"
                " (overboarded), raising attention dilution concerns."
            )

    # Anti-takeover provisions
    if board.classified_board and board.classified_board.value:
        parts.append(
            "The classified (staggered) board structure is an"
            " anti-takeover provision that can limit shareholder"
            " ability to effect governance changes."
        )
    if board.dual_class_structure and board.dual_class_structure.value:
        parts.append(
            "Dual-class share structure concentrates voting control"
            " with insiders, reducing external governance pressure."
        )

    # Compensation alignment
    if comp.say_on_pay_pct is not None:
        sop_val = safe_float(comp.say_on_pay_pct.value)
        sop_str = format_percentage(sop_val)
        if sop_val >= 90:
            parts.append(
                f"Say-on-pay approval of {sop_str} indicates strong"
                " shareholder alignment with compensation practices"
                " (S&P 500 median: approximately 88%)."
            )
        elif sop_val < 70:
            parts.append(
                f"**Compensation concern**: Say-on-pay approval of"
                f" only {sop_str} signals meaningful shareholder"
                " dissatisfaction with executive compensation,"
                " a common precursor to derivative actions."
            )

    if comp.ceo_total_comp is not None:
        ceo_val = safe_float(comp.ceo_total_comp.value)
        # Filter out year-as-comp extraction bugs
        if ceo_val > 50_000 and not (1990 <= ceo_val <= 2035):
            ceo_str = format_currency(ceo_val, compact=True)
            equity_pct = ""
            if comp.comp_mix and comp.comp_mix.get("equity"):
                eq = comp.comp_mix["equity"]
                equity_pct = f", {format_percentage(eq)} equity-based"
            parts.append(
                f"CEO total compensation: {ceo_str}{equity_pct}."
            )

    # D&O conclusion
    if parts:
        risk_flags: list[str] = []
        if board.ceo_chair_duality and board.ceo_chair_duality.value:
            risk_flags.append("CEO/Chair duality")
        if board.overboarded_count is not None and int(board.overboarded_count.value) > 0:
            risk_flags.append("overboarded directors")
        if comp.say_on_pay_pct is not None and safe_float(comp.say_on_pay_pct.value) < 70:
            risk_flags.append("low say-on-pay approval")
        if risk_flags:
            flags = ", ".join(risk_flags)
            parts.append(
                f"D&O governance risk factors: {flags}."
            )

    return " ".join(p for p in parts if p)


def _governance_narrative_from_dict(gov: dict[str, Any]) -> str:
    """Legacy wrapper for dict-based governance narrative."""
    if not gov:
        return ""
    parts: list[str] = []
    score = gov.get("governance_score")
    if score:
        parts.append(f"Governance quality score: {score}.")
    duality = gov.get("ceo_duality")
    if duality == "Yes":
        parts.append(
            "CEO/Chair duality concentrates decision-making authority."
        )
    sop = gov.get("say_on_pay")
    if sop and sop != "N/A":
        parts.append(f"Say-on-pay approval: {sop}.")
    return " ".join(parts) if parts else ""


def litigation_narrative(
    state_or_dict: AnalysisState | dict[str, Any],
) -> str:
    """Generate litigation section narrative."""
    if isinstance(state_or_dict, dict):
        return _litigation_narrative_from_dict(state_or_dict)
    return _litigation_narrative_from_state(state_or_dict)


def _litigation_narrative_from_state(state: AnalysisState) -> str:
    """Generate litigation narrative from typed state data."""
    if not state.extracted or not state.extracted.litigation:
        return ""
    lit = state.extracted.litigation
    parts: list[str] = []

    # Active SCA summary — canonical active genuine SCA filter
    from do_uw.stages.render.sca_counter import get_active_genuine_scas

    scas = lit.securities_class_actions
    active_scas = get_active_genuine_scas(state)
    if active_scas:
        c = active_scas[0]
        # Handle both dict and Pydantic object forms
        if isinstance(c, dict):
            cn = c.get("case_name", {})
            name = cn.get("value", cn) if isinstance(cn, dict) else str(cn) if cn else "unnamed case"
        else:
            name = c.case_name.value if c.case_name else "unnamed case"
        parts.append(
            f"The company faces {len(active_scas)} active securities"
            f" class action(s). The primary case, {name},"
        )
        if isinstance(c, dict):
            cp_start = c.get("class_period_start", {})
            cp_end = c.get("class_period_end", {})
            start = cp_start.get("value") if isinstance(cp_start, dict) else cp_start
            end = cp_end.get("value") if isinstance(cp_end, dict) else cp_end
            cp_days = c.get("class_period_days")
        else:
            start = c.class_period_start.value if c.class_period_start else None
            end = c.class_period_end.value if c.class_period_end else None
            cp_days = c.class_period_days if hasattr(c, "class_period_days") else None
        if start and end:
            days = f" ({cp_days} days)" if cp_days else ""
            parts[-1] += (
                f" covers a class period from {start} to {end}{days}."
            )
        else:
            parts[-1] += " is currently pending."

        lc = _sv(c, "lead_counsel")
        if lc:
            tier_note = ""
            lct = _sv(c, "lead_counsel_tier")
            if lct:
                tier_note = f" (Tier {lct} plaintiff firm)"
            parts.append(f"Lead counsel: {lc}{tier_note}.")
    elif not scas:
        parts.append(
            "No active securities class actions identified."
            " Clean litigation history is a positive D&O underwriting signal."
        )

    # SEC enforcement pipeline
    sec = lit.sec_enforcement
    if sec:
        stage = _sv(sec, "highest_confirmed_stage")
        if stage and stage not in ("NONE", ""):
            parts.append(
                f"SEC enforcement pipeline position: {stage}."
            )
            if stage in ("WELLS_NOTICE", "ENFORCEMENT_ACTION"):
                parts.append(
                    "This is a critical-level regulatory risk that"
                    " typically triggers CRF red flag ceiling activation."
                )

    # Derivative suits
    derivs = lit.derivative_suits
    if derivs:
        parts.append(
            f"{len(derivs)} derivative action(s) pending, alleging"
            " breach of fiduciary duty by directors and officers."
        )

    # Industry claim patterns
    if lit.industry_patterns:
        claim_descs: list[str] = []
        for p in lit.industry_patterns[:3]:
            if p.legal_theory:
                claim_descs.append(str(p.legal_theory.value))
            elif p.description:
                claim_descs.append(str(p.description.value))
        if claim_descs:
            parts.append(
                f"Industry claim exposure: {', '.join(claim_descs)}."
            )

    # SOL windows
    open_sols = [w for w in lit.sol_map if w.window_open]
    if open_sols:
        parts.append(
            f"{len(open_sols)} statute of limitations window(s) remain"
            " open, meaning new claims can still be filed for past"
            " events. Under claims-made D&O policy, coverage is"
            " triggered when a claim is reported during the policy"
            " period."
        )

    # Defense assessment
    if lit.defense and lit.defense.overall_defense_strength:
        da = str(lit.defense.overall_defense_strength.value)
        if da:
            parts.append(f"Defense quality assessment: {da}.")

    # Litigation reserve
    if lit.total_litigation_reserve and lit.total_litigation_reserve.value:
        reserve = format_currency(
            lit.total_litigation_reserve.value, compact=True
        )
        parts.append(f"Total litigation reserve: {reserve}.")

    return " ".join(p for p in parts if p)


def _litigation_narrative_from_dict(lit: dict[str, Any]) -> str:
    """Legacy wrapper for dict-based litigation narrative."""
    if not lit:
        return ""
    parts: list[str] = []
    active = lit.get("active_summary", "")
    if "No active litigation" in active:
        parts.append(
            "No active litigation identified."
            " Clean litigation history is a positive D&O signal."
        )
    cases = lit.get("cases", [])
    if cases:
        parts.append(f"{len(cases)} litigation matter(s) identified.")
    open_count = lit.get("open_sol_count", 0)
    if open_count > 0:
        parts.append(
            f"{open_count} statute of limitations window(s) remain open."
        )
    return " ".join(parts) if parts else ""


def scoring_narrative(state: AnalysisState) -> str:
    """Generate scoring tier and risk factor narrative."""
    if not state.scoring:
        return ""
    sc = state.scoring
    parts: list[str] = []

    # Tier classification
    if sc.tier:
        tier = sc.tier.tier
        score = sc.quality_score
        parts.append(
            f"Underwriting tier: **{tier}** (quality score:"
            f" {score:.1f}/100)."
        )
        if sc.tier.action:
            parts.append(f"Recommended action: {sc.tier.action}.")
        if sc.tier.probability_range:
            parts.append(
                f"Expected claim probability band:"
                f" {sc.tier.probability_range}."
            )

    # Top contributing risk factors
    if sc.factor_scores:
        sorted_factors = sorted(
            sc.factor_scores,
            key=lambda f: f.points_deducted,
            reverse=True,
        )
        top_factors = [
            f for f in sorted_factors if f.points_deducted > 0
        ][:3]
        if top_factors:
            factor_desc = "; ".join(
                f"{f.factor_name} ({f.factor_id}:"
                f" -{f.points_deducted:.1f} pts)"
                for f in top_factors
            )
            parts.append(f"Top risk contributors: {factor_desc}.")

    # Active patterns
    active_patterns = [p for p in sc.patterns_detected if p.detected]
    if active_patterns:
        pattern_names = [p.pattern_name or p.pattern_id for p in active_patterns]
        parts.append(
            f"Active composite patterns: {', '.join(pattern_names)}."
        )

    # Red flag gates
    triggered_flags = [f for f in sc.red_flags if f.triggered]
    if triggered_flags:
        flag_desc = "; ".join(
            f"{f.flag_name or f.flag_id}"
            + (f" (ceiling: {f.ceiling_applied})" if f.ceiling_applied else "")
            for f in triggered_flags
        )
        parts.append(f"**Red flag gates active**: {flag_desc}.")
        if sc.binding_ceiling_id:
            parts.append(
                f"Binding ceiling: {sc.binding_ceiling_id}."
            )

    # Claim probability
    if sc.claim_probability:
        cp = sc.claim_probability
        parts.append(
            f"Claim probability band: {cp.band}"
            f" ({format_percentage(cp.range_low_pct)}-"
            f"{format_percentage(cp.range_high_pct)})."
        )

    return " ".join(p for p in parts if p)


def company_narrative(state: AnalysisState) -> str:
    """Generate company profile D&O narrative."""
    if not state.company:
        return ""
    prof = state.company
    identity = prof.identity
    parts: list[str] = []

    # Business description
    legal_name = (
        identity.legal_name.value if identity.legal_name else "The company"
    )
    if prof.business_description and prof.business_description.value:
        desc = str(prof.business_description.value)
        parts.append(f"{legal_name}: {desc}")

    # Revenue concentration
    if prof.revenue_segments:
        segs = prof.revenue_segments[:3]
        total_rev = sum(
            float(s.value.get("revenue", 0) or 0) for s in prof.revenue_segments
        )
        seg_parts: list[str] = []
        for seg_sv in segs:
            seg = seg_sv.value
            name = seg.get("name", seg.get("segment", ""))
            pct = seg.get("percentage", seg.get("pct"))
            if pct is None and total_rev > 0:
                rev = seg.get("revenue")
                if rev is not None:
                    pct = float(rev) / total_rev * 100
            if name and pct is not None:  # pct may be None from dict
                seg_parts.append(f"{name} ({format_percentage(float(pct))})")  # type: ignore[arg-type]
        if seg_parts:
            parts.append(
                f"Revenue concentration: {', '.join(seg_parts)}."
            )

    # Geographic risk
    if prof.geographic_footprint:
        intl = [
            g.value for g in prof.geographic_footprint
            if str(g.value.get("jurisdiction", g.value.get("region", ""))).lower() not in ("us", "united states", "domestic")
        ]
        if intl:
            intl_count = len(intl)
            parts.append(
                f"{intl_count} international geography segment(s),"
                " creating cross-border regulatory exposure."
            )

    # FPI status
    if identity.is_fpi:
        parts.append(
            "The company is a Foreign Private Issuer (FPI), filing"
            " 20-F/6-K instead of 10-K/10-Q. FPI status affects"
            " governance requirements, reporting frequency, and"
            " D&O coverage structure."
        )

    # Market cap and filer category
    if prof.market_cap is not None:
        mc_str = format_currency(float(prof.market_cap.value), compact=True)
        cat = ""
        if prof.filer_category and prof.filer_category.value:
            cat = f" ({prof.filer_category.value})"
        parts.append(f"Market capitalization: {mc_str}{cat}.")

    # D&O exposure factors
    if prof.do_exposure_factors:
        factors = [
            f.value.get("factor", "").replace("_", " ").title()
            for f in prof.do_exposure_factors
            if f.value.get("factor")
        ][:5]
        if factors:
            parts.append(
                f"D&O exposure factors: {', '.join(factors)}."
            )

    # Risk classification
    if prof.risk_classification and prof.risk_classification.value:
        rc = prof.risk_classification.value
        parts.append(f"Risk classification: {rc}.")

    return " ".join(p for p in parts if p)


__all__ = [
    "company_narrative",
    "governance_narrative",
    "litigation_narrative",
    "scoring_narrative",
]
