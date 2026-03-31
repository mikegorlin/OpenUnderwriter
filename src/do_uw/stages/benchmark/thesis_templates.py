"""Underwriting thesis narrative templates by risk type.

Generates a professional 2-3 sentence underwriting thesis filled
with company-specific data from scoring, inherent risk, and allegation
mapping. Templates are rule-based and deterministic (no LLM).

All 7 risk types produce distinct narratives in consulting report tone.
"""

from __future__ import annotations

from do_uw.models.executive_summary import (
    InherentRiskBaseline,
    UnderwritingThesis,
)
from do_uw.models.scoring import FactorScore, Tier
from do_uw.models.scoring_output import (
    AllegationMapping,
    AllegationTheory,
    RiskType,
)

# -----------------------------------------------------------------------
# Risk type display labels
# -----------------------------------------------------------------------

_RISK_TYPE_LABELS: dict[RiskType, str] = {
    RiskType.GROWTH_DARLING: "Growth Darling",
    RiskType.DISTRESSED: "Distressed / Fiduciary Risk",
    RiskType.BINARY_EVENT: "Binary Event Risk",
    RiskType.GUIDANCE_DEPENDENT: "Guidance-Dependent",
    RiskType.REGULATORY_SENSITIVE: "Regulatory-Sensitive",
    RiskType.TRANSFORMATION: "Corporate Transformation",
    RiskType.STABLE_MATURE: "Stable / Mature",
}

# Tier display names
_TIER_LABELS: dict[Tier, str] = {
    Tier.WIN: "preferred",
    Tier.WANT: "favorable",
    Tier.WRITE: "standard",
    Tier.WATCH: "elevated",
    Tier.WALK: "challenged",
    Tier.NO_TOUCH: "critical",
}


# -----------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------


def _tier_label(tier: Tier) -> str:
    """Human-readable tier descriptor."""
    return _TIER_LABELS.get(tier, "standard")


def _top_factor_narrative(top_factor: FactorScore | None) -> str:
    """Build narrative fragment for the top scoring factor."""
    if top_factor is None:
        return "No single factor dominates the risk profile"
    return (
        f"The primary risk driver is {top_factor.factor_name}, "
        f"reflecting significant exposure in this area"
    )


def _primary_theory_narrative(
    mapping: AllegationMapping | None,
) -> tuple[str, str]:
    """Extract primary theory description and evidence.

    Returns (theory_name, evidence_summary).
    """
    if mapping is None or not mapping.theories:
        return ("general D&O liability", "broad risk exposure")

    primary = mapping.primary_exposure
    theory_names: dict[AllegationTheory, str] = {
        AllegationTheory.A_DISCLOSURE: "disclosure-based (10b-5)",
        AllegationTheory.B_GUIDANCE: "guidance/earnings-related",
        AllegationTheory.C_PRODUCT_OPS: "product/operational",
        AllegationTheory.D_GOVERNANCE: "governance/fiduciary",
        AllegationTheory.E_MA: "M&A-related",
    }
    theory_name = theory_names.get(primary, "general D&O liability")

    # Find evidence from the primary theory
    evidence = "identified risk factors"
    for te in mapping.theories:
        if te.theory == primary and te.findings:
            evidence = te.findings[0]
            break

    return (theory_name, evidence)


def _risk_rates(
    inherent_risk: InherentRiskBaseline | None,
) -> tuple[str, str]:
    """Format base rate and adjusted rate for display."""
    if inherent_risk is None:
        return ("N/A", "N/A")
    return (
        f"{inherent_risk.sector_base_rate_pct:.1f}",
        f"{inherent_risk.company_adjusted_rate_pct:.1f}",
    )


def _quality_descriptor(score: float) -> str:
    """Describe quality score range."""
    if score >= 86:
        return "strong risk controls"
    if score >= 71:
        return "above-average risk management"
    if score >= 51:
        return "moderate risk exposure"
    if score >= 31:
        return "elevated risk indicators"
    return "significant risk concentration"


# -----------------------------------------------------------------------
# Per-risk-type template functions
# -----------------------------------------------------------------------


def _growth_darling_thesis(
    score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    mapping: AllegationMapping | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> str:
    """GROWTH_DARLING: high-growth, high-multiple, disclosure risk."""
    theory, evidence = _primary_theory_narrative(mapping)
    base, adjusted = _risk_rates(inherent_risk)
    descriptor = _quality_descriptor(score)
    factor_narrative = _top_factor_narrative(top_factor)

    return (
        f"{company_name} presents as a {_tier_label(tier)} risk "
        f"({score:.0f}/100) with {descriptor} as a high-growth, "
        f"high-multiple issuer. {factor_narrative}. "
        f"The primary allegation exposure is {theory}, "
        f"driven by {evidence}. "
        f"Industry base rate: {base}% | "
        f"Company-adjusted: {adjusted}%."
    )


def _distressed_thesis(
    score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> str:
    """DISTRESSED: fiduciary risk, Side A, indemnification."""
    base, adjusted = _risk_rates(inherent_risk)
    factor_narrative = _top_factor_narrative(top_factor)

    side_a = (
        "heightened"
        if score < 40
        else "elevated" if score < 60 else "standard"
    )

    return (
        f"{company_name} presents elevated fiduciary risk "
        f"({score:.0f}/100, {_tier_label(tier)}) driven by financial "
        f"distress indicators. {factor_narrative}. "
        f"Side A coverage value is {side_a} given indemnification "
        f"capacity concerns. "
        f"Industry base rate: {base}% | "
        f"Company-adjusted: {adjusted}%."
    )


def _binary_event_thesis(
    score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> str:
    """BINARY_EVENT: concentrated risk, event resolution."""
    base, adjusted = _risk_rates(inherent_risk)
    factor_narrative = _top_factor_narrative(top_factor)

    event_desc = "pending material events"
    if top_factor is not None and top_factor.evidence:
        event_desc = top_factor.evidence[0]

    return (
        f"{company_name} faces concentrated binary risk "
        f"({score:.0f}/100, {_tier_label(tier)}) centered on "
        f"{event_desc}. {factor_narrative}. "
        f"Event resolution will materially shift the risk profile "
        f"in either direction. "
        f"Industry base rate: {base}% | "
        f"Company-adjusted: {adjusted}%."
    )


def _guidance_dependent_thesis(
    score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> str:
    """GUIDANCE_DEPENDENT: earnings miss-and-drop scenarios."""
    base, adjusted = _risk_rates(inherent_risk)
    factor_narrative = _top_factor_narrative(top_factor)

    return (
        f"{company_name} presents guidance-dependent risk "
        f"({score:.0f}/100, {_tier_label(tier)}) with elevated "
        f"exposure to earnings miss-and-drop scenarios. "
        f"{factor_narrative}. "
        f"Historical guidance accuracy and stock price sensitivity "
        f"to misses are key underwriting factors. "
        f"Industry base rate: {base}% | "
        f"Company-adjusted: {adjusted}%."
    )


def _regulatory_sensitive_thesis(
    score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> str:
    """REGULATORY_SENSITIVE: regulatory environment, enforcement."""
    base, adjusted = _risk_rates(inherent_risk)
    factor_narrative = _top_factor_narrative(top_factor)

    reg_desc = (
        "active regulatory exposure"
        if score < 50
        else "moderate regulatory sensitivity"
    )

    return (
        f"{company_name} operates in a regulatory-intensive "
        f"environment ({score:.0f}/100, {_tier_label(tier)}) with "
        f"{reg_desc}. {factor_narrative}. "
        f"Regulatory enforcement actions and compliance failures "
        f"represent the primary claim vectors. "
        f"Industry base rate: {base}% | "
        f"Company-adjusted: {adjusted}%."
    )


def _transformation_thesis(
    score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> str:
    """TRANSFORMATION: corporate transition risk."""
    base, adjusted = _risk_rates(inherent_risk)
    factor_narrative = _top_factor_narrative(top_factor)

    return (
        f"{company_name} is undergoing significant corporate "
        f"transformation ({score:.0f}/100, {_tier_label(tier)}) "
        f"creating transition-period risk. {factor_narrative}. "
        f"M&A integration, restructuring execution, and disclosure "
        f"adequacy during transition are key exposures. "
        f"Industry base rate: {base}% | "
        f"Company-adjusted: {adjusted}%."
    )


def _stable_mature_thesis(
    score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> str:
    """STABLE_MATURE: maintain posture, monitor deterioration."""
    base, adjusted = _risk_rates(inherent_risk)
    factor_narrative = _top_factor_narrative(top_factor)

    stability_desc = (
        "consistent risk controls and stable operations"
        if score >= 71
        else "established market position"
        if score >= 51
        else "stable but monitored risk posture"
    )

    return (
        f"{company_name} presents a mature risk profile "
        f"({score:.0f}/100, {_tier_label(tier)}) with "
        f"{stability_desc}. {factor_narrative}. "
        f"The primary underwriting consideration is sustaining "
        f"current risk posture and monitoring for deterioration "
        f"signals. "
        f"Industry base rate: {base}% | "
        f"Company-adjusted: {adjusted}%."
    )


# -----------------------------------------------------------------------
# Public interface
# -----------------------------------------------------------------------


def generate_thesis(
    risk_type: RiskType,
    quality_score: float,
    tier: Tier,
    top_factor: FactorScore | None,
    allegation_mapping: AllegationMapping | None,
    inherent_risk: InherentRiskBaseline | None,
    company_name: str,
) -> UnderwritingThesis:
    """Generate underwriting thesis narrative from risk type template.

    Each risk type has a distinct template filled with company-specific
    data. The thesis sounds like what an underwriter would say in a
    meeting -- professional consulting report tone.

    Args:
        risk_type: Primary risk type classification.
        quality_score: Quality score 0-100.
        tier: Underwriting tier classification.
        top_factor: Highest-deduction factor score (or None).
        allegation_mapping: Allegation theory mapping (or None).
        inherent_risk: Inherent risk baseline (or None).
        company_name: Company legal name for narrative.

    Returns:
        Populated UnderwritingThesis with narrative and metadata.
    """
    top_factor_summary = _top_factor_narrative(top_factor)

    # Dispatch to risk-type-specific template
    if risk_type == RiskType.GROWTH_DARLING:
        narrative = _growth_darling_thesis(
            quality_score, tier, top_factor,
            allegation_mapping, inherent_risk, company_name,
        )
    elif risk_type == RiskType.DISTRESSED:
        narrative = _distressed_thesis(
            quality_score, tier, top_factor,
            inherent_risk, company_name,
        )
    elif risk_type == RiskType.BINARY_EVENT:
        narrative = _binary_event_thesis(
            quality_score, tier, top_factor,
            inherent_risk, company_name,
        )
    elif risk_type == RiskType.GUIDANCE_DEPENDENT:
        narrative = _guidance_dependent_thesis(
            quality_score, tier, top_factor,
            inherent_risk, company_name,
        )
    elif risk_type == RiskType.REGULATORY_SENSITIVE:
        narrative = _regulatory_sensitive_thesis(
            quality_score, tier, top_factor,
            inherent_risk, company_name,
        )
    elif risk_type == RiskType.TRANSFORMATION:
        narrative = _transformation_thesis(
            quality_score, tier, top_factor,
            inherent_risk, company_name,
        )
    else:
        # STABLE_MATURE is the default
        narrative = _stable_mature_thesis(
            quality_score, tier, top_factor,
            inherent_risk, company_name,
        )

    return UnderwritingThesis(
        narrative=narrative,
        risk_type_label=_RISK_TYPE_LABELS.get(risk_type, "Unknown"),
        top_factor_summary=top_factor_summary,
    )


__all__ = ["generate_thesis"]
