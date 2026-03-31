"""Allegation theory mapping and risk type classification.

Maps scoring findings to 5 D&O allegation theories (SECT7-05)
and classifies into 7 risk archetypes (SECT7-04).

Theories: A=Disclosure, B=Guidance, C=Product/Ops, D=Governance, E=M&A.
Archetypes: DISTRESSED, BINARY_EVENT, GROWTH_DARLING, GUIDANCE_DEPENDENT,
REGULATORY_SENSITIVE, TRANSFORMATION, STABLE_MATURE.
"""

from __future__ import annotations

import logging

from do_uw.models.company import CompanyProfile
from do_uw.models.scoring import FactorScore, PatternMatch, RedFlagResult
from do_uw.models.scoring_output import (
    AllegationMapping,
    AllegationTheory,
    RiskType,
    RiskTypeClassification,
    TheoryExposure,
)
from do_uw.models.state import ExtractedData

logger = logging.getLogger(__name__)

# Theory-to-factor mapping
_THEORY_FACTORS: dict[AllegationTheory, list[str]] = {
    AllegationTheory.A_DISCLOSURE: ["F1", "F3", "F5"],
    AllegationTheory.B_GUIDANCE: ["F2", "F5"],
    AllegationTheory.C_PRODUCT_OPS: ["F7", "F8"],
    AllegationTheory.D_GOVERNANCE: ["F9", "F10"],
    AllegationTheory.E_MA: ["F4"],
}

# Patterns that boost specific theories
_THEORY_PATTERNS: dict[AllegationTheory, list[str]] = {
    AllegationTheory.A_DISCLOSURE: [
        "PATTERN.FIN.EARNINGS_QUALITY_DETERIORATION",
        "PATTERN.STOCK.EVENT_COLLAPSE",
    ],
    AllegationTheory.B_GUIDANCE: [
        "PATTERN.FIN.GUIDANCE_MANIPULATION",
        "PATTERN.FWD.FORWARD_INDICATOR_CLUSTER",
    ],
    AllegationTheory.C_PRODUCT_OPS: [
        "PATTERN.BIZ.AI_WASHING_RISK",
        "PATTERN.BIZ.CONCENTRATION_RISK",
    ],
    AllegationTheory.D_GOVERNANCE: [
        "PATTERN.GOV.TURNOVER_STRESS",
        "PATTERN.GOV.PROXY_ADVISOR_RISK",
    ],
    AllegationTheory.E_MA: ["PATTERN.STOCK.IPO_SPAC_LIFECYCLE"],
}

# Regulated industry SIC ranges
_REGULATED_RANGES: list[tuple[int, int]] = [
    (2830, 2836),  # Pharmaceutical
    (6020, 6029),  # Banking
    (6311, 6399),  # Insurance
    (4911, 4941),  # Utilities
    (1311, 1382),  # Energy / oil & gas
]


# -----------------------------------------------------------------------
# Public API: Allegation mapping
# -----------------------------------------------------------------------


def map_allegations(
    factor_scores: list[FactorScore],
    patterns: list[PatternMatch],
    red_flags: list[RedFlagResult],
    extracted: ExtractedData,
) -> AllegationMapping:
    """Map all findings to 5 allegation theories with exposure levels."""
    factor_map = {fs.factor_id: fs for fs in factor_scores}
    pattern_map = {p.pattern_id: p for p in patterns}

    theories: list[TheoryExposure] = []
    max_points = 0.0
    max_theory = AllegationTheory.A_DISCLOSURE

    for theory in AllegationTheory:
        exposure = _evaluate_theory(
            theory, factor_map, pattern_map, red_flags, extracted
        )
        theories.append(exposure)
        total = _theory_points(theory, factor_map)
        if total > max_points:
            max_points = total
            max_theory = theory

    return AllegationMapping(
        theories=theories,
        primary_exposure=max_theory,
        concentration_analysis=_build_concentration_analysis(theories),
        needs_calibration=True,
    )


def _evaluate_theory(
    theory: AllegationTheory,
    factor_map: dict[str, FactorScore],
    pattern_map: dict[str, PatternMatch],
    red_flags: list[RedFlagResult],
    extracted: ExtractedData,
) -> TheoryExposure:
    """Evaluate a single allegation theory."""
    factor_ids = _THEORY_FACTORS.get(theory, [])
    pattern_ids = _THEORY_PATTERNS.get(theory, [])
    total_pts = 0.0
    findings: list[str] = []
    factor_sources: list[str] = []

    for fid in factor_ids:
        fs = factor_map.get(fid)
        if fs is not None and fs.points_deducted > 0:
            total_pts += fs.points_deducted
            factor_sources.append(fid)
            for ev in fs.evidence[:2]:
                findings.append(f"{fid}: {ev}")

    has_critical_pattern = False
    for pid in pattern_ids:
        pm = pattern_map.get(pid)
        if pm is not None and pm.detected:
            has_critical_pattern = True
            findings.append(f"Pattern {pm.pattern_name}: {pm.severity} severity")

    if theory == AllegationTheory.D_GOVERNANCE:
        for rf in red_flags:
            if rf.triggered and rf.flag_id in ("CRF-4", "CRF-5"):
                findings.append(f"Red flag {rf.flag_id}: {rf.flag_name}")

    _add_extracted_evidence(theory, extracted, findings)
    level = _determine_exposure_level(total_pts, has_critical_pattern)
    return TheoryExposure(
        theory=theory, exposure_level=level,
        findings=findings, factor_sources=factor_sources,
    )


def _theory_points(
    theory: AllegationTheory, factor_map: dict[str, FactorScore],
) -> float:
    """Sum factor points for a theory."""
    return sum(
        factor_map[fid].points_deducted
        for fid in _THEORY_FACTORS.get(theory, [])
        if fid in factor_map
    )


def _determine_exposure_level(total_pts: float, has_critical: bool) -> str:
    """HIGH >= 8 or critical pattern; MODERATE 3-7; LOW 0-2."""
    if total_pts >= 8 or has_critical:
        return "HIGH"
    if total_pts >= 3:
        return "MODERATE"
    return "LOW"


def _add_extracted_evidence(
    theory: AllegationTheory, extracted: ExtractedData, findings: list[str],
) -> None:
    """Add theory-specific evidence from extracted data."""
    if theory == AllegationTheory.C_PRODUCT_OPS:
        lit = extracted.litigation
        if lit is not None and lit.regulatory_proceedings:
            findings.append(
                f"{len(lit.regulatory_proceedings)} regulatory proceedings"
            )
    elif theory == AllegationTheory.D_GOVERNANCE:
        gov = extracted.governance
        if gov is not None and gov.leadership.departures_18mo:
            findings.append(
                f"{len(gov.leadership.departures_18mo)} executive departures in 18 months"
            )
    elif theory == AllegationTheory.E_MA:
        lit = extracted.litigation
        if lit is not None and lit.deal_litigation:
            findings.append(
                f"{len(lit.deal_litigation)} deal-related litigation matters"
            )


def _build_concentration_analysis(theories: list[TheoryExposure]) -> str:
    """Build narrative summarizing exposure concentration."""
    high = [t for t in theories if t.exposure_level == "HIGH"]
    mod = [t for t in theories if t.exposure_level == "MODERATE"]
    if not high and not mod:
        return "Low exposure across all allegation theories."
    parts: list[str] = []
    if high:
        parts.append(f"HIGH exposure in: {', '.join(t.theory.value for t in high)}")
    if mod:
        parts.append(f"MODERATE exposure in: {', '.join(t.theory.value for t in mod)}")
    return ". ".join(parts) + "."


# -----------------------------------------------------------------------
# Public API: Risk type classification
# -----------------------------------------------------------------------


def classify_risk_type(
    extracted: ExtractedData,
    company: CompanyProfile | None,
    factor_scores: list[FactorScore],
    patterns: list[PatternMatch],
) -> RiskTypeClassification:
    """Classify company into one of 7 risk archetypes (rule-based).

    Priority: DISTRESSED > BINARY_EVENT > GROWTH_DARLING >
    GUIDANCE_DEPENDENT > REGULATORY_SENSITIVE > TRANSFORMATION >
    STABLE_MATURE.
    """
    factor_map = {fs.factor_id: fs for fs in factor_scores}
    candidates: list[tuple[RiskType, list[str]]] = []

    checks: list[tuple[RiskType, list[str] | None]] = [
        (RiskType.DISTRESSED, _check_distressed(extracted, factor_map)),
        (RiskType.BINARY_EVENT, _check_binary_event(extracted)),
        (RiskType.GROWTH_DARLING, _check_growth_darling(extracted, company)),
        (RiskType.GUIDANCE_DEPENDENT, _check_guidance_dependent(extracted, factor_map)),
        (RiskType.REGULATORY_SENSITIVE, _check_regulatory(extracted, company, factor_map)),
        (RiskType.TRANSFORMATION, _check_transformation(extracted, company)),
    ]
    for risk_type, ev in checks:
        if ev:
            candidates.append((risk_type, ev))

    if not candidates:
        primary = RiskType.STABLE_MATURE
        evidence = ["No specific risk archetype triggers detected"]
    else:
        primary = candidates[0][0]
        evidence = candidates[0][1]

    secondary = candidates[1][0] if len(candidates) > 1 else None
    return RiskTypeClassification(
        primary=primary, secondary=secondary,
        evidence=evidence, needs_calibration=True,
    )


# -----------------------------------------------------------------------
# Risk type check helpers
# -----------------------------------------------------------------------


def _check_distressed(
    extracted: ExtractedData, factor_map: dict[str, FactorScore],
) -> list[str] | None:
    """Going concern OR Altman Z distress OR F8 >= 6."""
    evidence: list[str] = []
    fin = extracted.financials
    if fin is not None:
        gc = fin.audit.going_concern
        if gc is not None and gc.value is True:
            evidence.append("Going concern opinion present")
        az = fin.distress.altman_z_score
        if az is not None and az.zone == "distress" and not az.is_partial:
            evidence.append(f"Altman Z-Score in distress zone (score={az.score})")
    f8 = factor_map.get("F8")
    if f8 is not None and f8.points_deducted >= 6:
        evidence.append(f"F8 financial distress: {f8.points_deducted} points")
    return evidence if evidence else None


def _check_binary_event(extracted: ExtractedData) -> list[str] | None:
    """Active Section 11 windows OR SEC enforcement at WELLS_NOTICE+."""
    evidence: list[str] = []
    mkt = extracted.market
    if mkt is not None:
        cm = mkt.capital_markets
        if cm.active_section_11_windows > 0:
            evidence.append(f"{cm.active_section_11_windows} active Section 11 windows")
    lit = extracted.litigation
    if lit is not None:
        pp = lit.sec_enforcement.pipeline_position
        if pp is not None and pp.value.upper() in (
            "WELLS_NOTICE", "ENFORCEMENT_ACTION", "COMPLAINT",
        ):
            evidence.append(f"SEC enforcement at {pp.value} stage")
    return evidence if evidence else None


def _check_growth_darling(
    extracted: ExtractedData, company: CompanyProfile | None,
) -> list[str] | None:
    """Revenue growth > 20% AND years public < 5."""
    rev_growth = _get_revenue_yoy(extracted)
    if rev_growth is None or rev_growth <= 20:
        return None
    if company is None or company.years_public is None:
        return None
    yrs = company.years_public.value
    if yrs >= 5:
        return None
    return [f"Revenue growth {rev_growth:.1f}% YoY", f"{yrs} years public"]


def _check_guidance_dependent(
    extracted: ExtractedData, factor_map: dict[str, FactorScore],
) -> list[str] | None:
    """F5 > 0 AND company issues guidance."""
    f5 = factor_map.get("F5")
    if f5 is None or f5.points_deducted <= 0:
        return None
    mkt = extracted.market
    if mkt is None:
        return None
    phil = mkt.earnings_guidance.philosophy
    if not phil or phil.upper() == "NO_GUIDANCE":
        return None
    return [
        f"F5 guidance misses: {f5.points_deducted} points",
        f"Issues guidance (philosophy: {phil})",
    ]


def _check_regulatory(
    extracted: ExtractedData,
    company: CompanyProfile | None,
    factor_map: dict[str, FactorScore],
) -> list[str] | None:
    """Regulated SIC OR F1 enforcement rules triggered."""
    evidence: list[str] = []
    sic = _get_sic_code(company)
    if sic is not None and is_regulated_industry(sic):
        evidence.append(f"Regulated industry SIC: {sic}")
    f1 = factor_map.get("F1")
    if f1 is not None and f1.points_deducted > 0:
        for rule in f1.rules_triggered:
            if "enforcement" in rule.lower() or "regulatory" in rule.lower():
                evidence.append(f"F1 regulatory enforcement: {rule}")
                break
    return evidence if evidence else None


def _check_transformation(
    extracted: ExtractedData, company: CompanyProfile | None,
) -> list[str] | None:
    """CEO < 12 months OR recent major M&A."""
    evidence: list[str] = []
    gov = extracted.governance
    if gov is not None:
        # Use Phase 4 leadership.executives (LeadershipForensicProfile)
        for ep in gov.leadership.executives:
            if ep.title is not None:
                title = ep.title.value.upper()
                if "CEO" in title or "CHIEF EXECUTIVE" in title:
                    if ep.tenure_years is not None and ep.tenure_years < 1.0:
                        months = ep.tenure_years * 12
                        evidence.append(
                            f"CEO tenure {months:.0f} months (new leadership)"
                        )
    mkt = extracted.market
    if mkt is not None:
        for offering in mkt.capital_markets.offerings_3yr:
            if offering.offering_type.upper() in ("MERGER", "ACQUISITION", "SPAC"):
                evidence.append(f"Recent {offering.offering_type} activity")
                break
    return evidence if evidence else None


# -----------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------


def is_regulated_industry(sic_code: int) -> bool:
    """Check if SIC code falls in regulated industry ranges."""
    return any(low <= sic_code <= high for low, high in _REGULATED_RANGES)


def _get_sic_code(company: CompanyProfile | None) -> int | None:
    """Extract integer SIC code from company identity."""
    if company is None:
        return None
    sic_sv = company.identity.sic_code
    if sic_sv is None:
        return None
    try:
        return int(sic_sv.value)
    except (ValueError, TypeError):
        return None


def _get_revenue_yoy(extracted: ExtractedData) -> float | None:
    """Get year-over-year revenue growth percentage."""
    fin = extracted.financials
    if fin is None:
        return None
    inc = fin.statements.income_statement
    if inc is None:
        return None
    for item in inc.line_items:
        if item.label.lower() in ("total revenue", "revenue", "net revenue"):
            return item.yoy_change
    return None
