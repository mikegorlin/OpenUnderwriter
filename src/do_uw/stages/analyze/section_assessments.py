"""Pre-compute section density assessments for RENDER stage.

Determines three-tier density (CLEAN/ELEVATED/CRITICAL) for each major
worksheet section. RENDER reads these density levels and selects the
appropriate template -- no analytical logic in render.

Stores results in state.analysis.section_densities only.
The deprecated boolean *_clean fields have been removed.
"""

from __future__ import annotations

import logging

from do_uw.models.density import DensityLevel, SectionDensity
from do_uw.models.state import AnalysisState
from do_uw.stages.analyze.section_density_helpers import compute_company_density

logger = logging.getLogger(__name__)


def compute_section_assessments(state: AnalysisState) -> None:
    """Compute three-tier density per section.

    Stores results on:
    - state.analysis.section_densities (three-tier, primary)
    """
    if state.analysis is None:
        return

    # Compute three-tier densities
    gov_density = _compute_governance_density(state)
    lit_density = _compute_litigation_density(state)
    fin_density = _compute_financial_density(state)
    mkt_density = _compute_market_density(state)
    company_density = compute_company_density(state)

    state.analysis.section_densities = {
        "governance": gov_density,
        "litigation": lit_density,
        "financial": fin_density,
        "market": mkt_density,
        "company": company_density,
    }

    logger.info(
        "Section densities: gov=%s, lit=%s, fin=%s, mkt=%s, company=%s",
        gov_density.level,
        lit_density.level,
        fin_density.level,
        mkt_density.level,
        company_density.level,
    )


# ---------------------------------------------------------------------------
# Governance density
# ---------------------------------------------------------------------------


def _compute_governance_density(state: AnalysisState) -> SectionDensity:
    """Three-tier governance density with per-subsection overrides."""
    concerns: list[str] = []
    critical_evidence: list[str] = []
    overrides: dict[str, DensityLevel] = {}

    if state.extracted is None or state.extracted.governance is None:
        # No data -- cannot assess, default ELEVATED (unknown risk)
        return SectionDensity(
            level=DensityLevel.ELEVATED,
            concerns=["Governance data unavailable"],
        )

    gov = state.extracted.governance
    board = gov.board

    # --- 4.1 People Risk (executive forensics, departures, overboarding) ---
    people_concerns: list[str] = []
    people_critical: list[str] = []

    for exec_prof in gov.leadership.executives:
        if exec_prof.prior_litigation:
            people_critical.append(
                f"Executive {_sv_str(exec_prof.name)} has prior litigation"
            )
        if exec_prof.shade_factors:
            people_concerns.append(
                f"Executive {_sv_str(exec_prof.name)} has shade factors"
            )

    if board.overboarded_count is not None and board.overboarded_count.value > 0:
        people_concerns.append(
            f"{board.overboarded_count.value} overboarded directors"
        )
    for d in gov.board_forensics:
        if d.is_overboarded:
            people_concerns.append(f"Board member {_sv_str(d.name)} overboarded")

    # Recent departures
    unplanned = [
        e for e in gov.leadership.executives if e.departure_type == "UNPLANNED"
    ]
    if unplanned:
        people_concerns.append(f"{len(unplanned)} unplanned executive departures")

    if people_critical:
        overrides["4.1_people_risk"] = DensityLevel.CRITICAL
    elif people_concerns:
        overrides["4.1_people_risk"] = DensityLevel.ELEVATED
    else:
        overrides["4.1_people_risk"] = DensityLevel.CLEAN

    # --- 4.2 Structural Governance (independence, duality, committees) ---
    struct_concerns: list[str] = []
    struct_critical: list[str] = []

    if board.independence_ratio is not None:
        ratio = board.independence_ratio.value
        if ratio < 0.50:
            struct_critical.append(
                f"Board independence critically low at {ratio:.0%}"
            )
        elif ratio < 0.75:
            struct_concerns.append(
                f"Board independence below threshold at {ratio:.0%}"
            )
    else:
        struct_concerns.append("Board independence ratio unavailable")

    if board.ceo_chair_duality is not None and board.ceo_chair_duality.value:
        struct_concerns.append("CEO/Chair duality")

    if board.dual_class_structure is not None and board.dual_class_structure.value:
        struct_concerns.append("Dual-class share structure")

    if struct_critical:
        overrides["4.2_structural_governance"] = DensityLevel.CRITICAL
    elif struct_concerns:
        overrides["4.2_structural_governance"] = DensityLevel.ELEVATED
    else:
        overrides["4.2_structural_governance"] = DensityLevel.CLEAN

    # --- 4.3 Transparency (audit quality, restatements, comment letters) ---
    trans_concerns: list[str] = []
    trans_critical: list[str] = []

    if state.extracted.financials and state.extracted.financials.audit:
        audit = state.extracted.financials.audit
        if audit.material_weaknesses:
            trans_critical.append("Material weaknesses in internal controls")
        if audit.restatements:
            trans_critical.append(
                f"{len(audit.restatements)} financial restatements"
            )
        if audit.going_concern is not None and audit.going_concern.value is True:
            trans_critical.append("Going concern opinion")

    # SEC comment letters (from litigation/enforcement data)
    if state.extracted.litigation:
        enf = state.extracted.litigation.sec_enforcement
        if (
            enf.comment_letter_count is not None
            and enf.comment_letter_count.value > 2
        ):
            trans_concerns.append(
                f"{enf.comment_letter_count.value} SEC comment letters"
            )

    if trans_critical:
        overrides["4.3_transparency"] = DensityLevel.CRITICAL
    elif trans_concerns:
        overrides["4.3_transparency"] = DensityLevel.ELEVATED
    else:
        overrides["4.3_transparency"] = DensityLevel.CLEAN

    # --- 4.4 Activist (activist presence) ---
    activist_concerns: list[str] = []
    activist_critical: list[str] = []

    if gov.ownership.known_activists:
        # Active campaigns are CRITICAL, known presence is ELEVATED
        for activist in gov.ownership.known_activists:
            name = activist.value if hasattr(activist, "value") else str(activist)
            activist_critical.append(f"Known activist investor: {name}")

    if activist_critical:
        overrides["4.4_activist"] = DensityLevel.CRITICAL
    elif activist_concerns:
        overrides["4.4_activist"] = DensityLevel.ELEVATED
    else:
        overrides["4.4_activist"] = DensityLevel.CLEAN

    # --- Aggregate governance density ---
    concerns = people_concerns + struct_concerns + trans_concerns + activist_concerns
    critical_evidence = (
        people_critical + struct_critical + trans_critical + activist_critical
    )

    level = _worst_level(list(overrides.values()))

    return SectionDensity(
        level=level,
        subsection_overrides=overrides,
        concerns=concerns,
        critical_evidence=critical_evidence,
    )


# ---------------------------------------------------------------------------
# Litigation density
# ---------------------------------------------------------------------------


def _compute_litigation_density(state: AnalysisState) -> SectionDensity:
    """Three-tier litigation density assessment."""
    concerns: list[str] = []
    critical_evidence: list[str] = []

    if state.extracted is None or state.extracted.litigation is None:
        return SectionDensity(level=DensityLevel.CLEAN)

    lit = state.extracted.litigation

    # Active SCAs -> CRITICAL (canonical active genuine SCA filter)
    from do_uw.stages.render.sca_counter import get_active_genuine_scas
    from do_uw.stages.score.red_flag_gates import _is_regulatory_not_sca

    active_scas = get_active_genuine_scas(state)
    if active_scas:
        critical_evidence.append(
            f"{len(active_scas)} active securities class action(s)"
        )

    # Settled/dismissed SCAs -> ELEVATED (history matters)
    resolved_scas = [
        sca
        for sca in lit.securities_class_actions
        if sca.status is not None and sca.status.value.upper() in ("SETTLED", "DISMISSED")
        and not _is_regulatory_not_sca(sca)
    ]
    if resolved_scas:
        concerns.append(f"{len(resolved_scas)} resolved SCA(s) in history")

    # SEC enforcement beyond comment letters -> CRITICAL
    enforcement = lit.sec_enforcement
    if enforcement.highest_confirmed_stage is not None:
        stage = enforcement.highest_confirmed_stage.value
        if stage in ("FORMAL_INVESTIGATION", "WELLS_NOTICE", "ENFORCEMENT_ACTION"):
            critical_evidence.append(f"SEC enforcement at {stage} stage")
        elif stage in ("COMMENT_LETTER", "INFORMAL_INQUIRY"):
            concerns.append(f"SEC engagement at {stage} stage")

    if enforcement.actions:
        critical_evidence.append(
            f"{len(enforcement.actions)} SEC enforcement action(s)"
        )

    # Active derivative suits -> CRITICAL
    active_derivs = [
        suit
        for suit in lit.derivative_suits
        if suit.status is not None and suit.status.value.upper() == "ACTIVE"
    ]
    if active_derivs:
        critical_evidence.append(
            f"{len(active_derivs)} active derivative suit(s)"
        )

    # Resolved derivative suits -> ELEVATED
    resolved_derivs = [
        suit
        for suit in lit.derivative_suits
        if suit.status is not None
        and suit.status.value.upper() in ("SETTLED", "DISMISSED")
    ]
    if resolved_derivs:
        concerns.append(f"{len(resolved_derivs)} resolved derivative suit(s)")

    # Regulatory proceedings -> ELEVATED at minimum
    if lit.regulatory_proceedings:
        concerns.append(
            f"{len(lit.regulatory_proceedings)} regulatory proceeding(s)"
        )

    # Deal litigation -> ELEVATED
    if lit.deal_litigation:
        concerns.append(f"{len(lit.deal_litigation)} deal litigation matter(s)")

    # Determine level
    if critical_evidence:
        level = DensityLevel.CRITICAL
    elif concerns:
        level = DensityLevel.ELEVATED
    else:
        level = DensityLevel.CLEAN

    return SectionDensity(
        level=level,
        concerns=concerns,
        critical_evidence=critical_evidence,
    )


# ---------------------------------------------------------------------------
# Financial density
# ---------------------------------------------------------------------------


def _compute_financial_density(state: AnalysisState) -> SectionDensity:
    """Three-tier financial density assessment."""
    concerns: list[str] = []
    critical_evidence: list[str] = []

    if state.extracted is None or state.extracted.financials is None:
        return SectionDensity(
            level=DensityLevel.ELEVATED,
            concerns=["Financial data unavailable"],
        )

    financials = state.extracted.financials

    # Distress models
    if financials.distress is not None:
        distress = financials.distress
        models = [
            ("Altman Z-Score", distress.altman_z_score),
            ("Beneish M-Score", distress.beneish_m_score),
            ("Ohlson O-Score", distress.ohlson_o_score),
            ("Piotroski F-Score", distress.piotroski_f_score),
        ]
        for name, model in models:
            if model is None:
                continue
            # Skip partial scores — incomplete inputs produce unreliable zones
            if model.is_partial:
                concerns.append(f"{name} partial (missing: {', '.join(model.missing_inputs)})")
                continue
            zone = model.zone.value
            if zone == "distress":
                critical_evidence.append(f"{name} in DISTRESS zone")
            elif zone == "grey":
                concerns.append(f"{name} in GREY zone")
    else:
        concerns.append("Distress models not computed")

    # Audit red flags
    audit = financials.audit
    if audit is not None:
        if audit.going_concern is not None and audit.going_concern.value is True:
            critical_evidence.append("Going concern opinion")
        if audit.material_weaknesses:
            critical_evidence.append("Material weaknesses in internal controls")
        if audit.restatements:
            concerns.append(f"{len(audit.restatements)} restatement(s)")

    # Determine level
    if critical_evidence:
        level = DensityLevel.CRITICAL
    elif concerns:
        level = DensityLevel.ELEVATED
    else:
        level = DensityLevel.CLEAN

    return SectionDensity(
        level=level,
        concerns=concerns,
        critical_evidence=critical_evidence,
    )


# ---------------------------------------------------------------------------
# Market density
# ---------------------------------------------------------------------------


def _compute_market_density(state: AnalysisState) -> SectionDensity:
    """Three-tier market density assessment."""
    concerns: list[str] = []
    critical_evidence: list[str] = []

    if state.extracted is None or state.extracted.market is None:
        return SectionDensity(
            level=DensityLevel.ELEVATED,
            concerns=["Market data unavailable"],
        )

    market = state.extracted.market

    # Stock drops: >= 10% severe (CRITICAL), any < 10% (ELEVATED)
    drops = market.stock_drops
    all_drops = [*drops.single_day_drops, *drops.multi_day_drops]
    severe = [d for d in all_drops if d.drop_pct and abs(d.drop_pct.value) >= 10]
    moderate = [
        d
        for d in all_drops
        if d.drop_pct and 5 <= abs(d.drop_pct.value) < 10
    ]
    if severe:
        critical_evidence.append(
            f"{len(severe)} stock drop(s) >= 10%"
        )
    if moderate:
        concerns.append(f"{len(moderate)} stock drop(s) 5-10%")

    # Insider cluster selling -> ELEVATED or CRITICAL
    insider = market.insider_analysis
    if insider and insider.cluster_events:
        count = len(insider.cluster_events)
        if count >= 3:
            critical_evidence.append(f"{count} insider cluster selling events")
        else:
            concerns.append(f"{count} insider cluster selling event(s)")

    # Short interest: >= 10% CRITICAL, 5-10% ELEVATED
    si = market.short_interest
    if si and si.short_pct_float:
        pct = si.short_pct_float.value
        if pct >= 10.0:
            critical_evidence.append(f"Short interest at {pct:.1f}%")
        elif pct >= 5.0:
            concerns.append(f"Short interest elevated at {pct:.1f}%")

    # Earnings misses
    eg = market.earnings_guidance
    if eg and eg.quarters:
        recent = eg.quarters[:4]
        big_misses = [
            q
            for q in recent
            if q.miss_magnitude_pct
            and abs(q.miss_magnitude_pct.value) > 10
            and q.result == "MISS"
        ]
        small_misses = [
            q
            for q in recent
            if q.miss_magnitude_pct
            and 5 < abs(q.miss_magnitude_pct.value) <= 10
            and q.result == "MISS"
        ]
        if big_misses:
            critical_evidence.append(
                f"{len(big_misses)} earnings miss(es) > 10%"
            )
        if small_misses:
            concerns.append(f"{len(small_misses)} earnings miss(es) 5-10%")

    # Determine level
    if critical_evidence:
        level = DensityLevel.CRITICAL
    elif concerns:
        level = DensityLevel.ELEVATED
    else:
        level = DensityLevel.CLEAN

    return SectionDensity(
        level=level,
        concerns=concerns,
        critical_evidence=critical_evidence,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv_str(sv: object) -> str:
    """Extract string from a SourcedValue or return fallback."""
    if sv is not None and hasattr(sv, "value"):
        return str(sv.value)  # type: ignore[union-attr]
    return "Unknown"


def _worst_level(levels: list[DensityLevel]) -> DensityLevel:
    """Return the worst (highest severity) density level from a list."""
    if not levels:
        return DensityLevel.CLEAN
    order = {
        DensityLevel.CLEAN: 0,
        DensityLevel.ELEVATED: 1,
        DensityLevel.CRITICAL: 2,
    }
    return max(levels, key=lambda lv: order[lv])
