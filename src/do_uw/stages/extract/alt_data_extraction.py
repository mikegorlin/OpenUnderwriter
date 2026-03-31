"""Phase 119: Alternative data signal extraction from existing state.

Extracts ESG/greenwashing, AI-washing, tariff/trade, and peer SCA
signals from data already present in state. No new acquisition.

Usage:
    extract_alt_data(state)
    # state.alt_data is now populated with all 4 sub-assessments
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.alt_data import (
    AIWashingRisk,
    AltDataAssessments,
    ESGRisk,
    PeerSCACheck,
    TariffExposure,
)
from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# SCA detection keywords for web search scanning
_SCA_KEYWORDS = re.compile(
    r"securities\s+class\s+action|securities\s+fraud|"
    r"shareholder\s+lawsuit|shareholder\s+class\s+action|"
    r"\bSCA\b|10b-5|securities\s+litigation",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Sub-extraction functions
# ---------------------------------------------------------------------------


def _extract_esg(state: AnalysisState) -> ESGRisk:
    """Extract ESG/greenwashing risk from environment assessment + 10-K.

    Sources:
    - state.extracted.environment_assessment.esg_gap_score
    - ESG-related details from environment assessment
    """
    result = ESGRisk()

    # Get esg_gap_score from environment assessment
    env = getattr(getattr(state, "extracted", None), "environment_assessment", None)
    if env and isinstance(env, dict):
        score = env.get("esg_gap_score", 0)
        if isinstance(score, (int, float)):
            if score >= 7:
                result.risk_level = "HIGH"
            elif score >= 4:
                result.risk_level = "MEDIUM"
            else:
                result.risk_level = "LOW"

        # Extract details for controversies
        details = env.get("esg_gap_details", {})
        if isinstance(details, dict):
            if details.get("esg_litigation_present"):
                result.controversies.append("ESG-related litigation identified in portfolio")
            rf_count = details.get("esg_risk_factor_count", 0)
            if rf_count and rf_count > 0:
                result.controversies.append(f"{rf_count} ESG risk factors in 10-K")

    # Build D&O relevance narrative
    if result.risk_level != "LOW":
        risk_desc = "elevated" if result.risk_level == "MEDIUM" else "significant"
        parts = []
        if result.controversies:
            parts.append(f"{len(result.controversies)} ESG concern(s) identified")
        parts.append(
            f"{risk_desc} ESG risk creates potential surface for "
            "greenwashing/ESG-washing securities claims under SEC enforcement focus"
        )
        result.do_relevance = ". ".join(parts)

    return result


def _extract_ai_washing(state: AnalysisState) -> AIWashingRisk:
    """Extract AI-washing risk from existing AI risk assessment.

    Sources:
    - state.extracted.ai_risk (AIRiskAssessment)
    - AI disclosure data within the assessment
    """
    result = AIWashingRisk()

    ai_risk = getattr(getattr(state, "extracted", None), "ai_risk", None)
    if ai_risk is None:
        return result

    result.ai_claims_present = True

    # Extract disclosure data for AI-washing indicators
    disclosure = getattr(ai_risk, "disclosure_data", None)
    if disclosure:
        mention_count = getattr(disclosure, "mention_count", 0) or 0
        opp_mentions = getattr(disclosure, "opportunity_mentions", 0) or 0
        threat_mentions = getattr(disclosure, "threat_mentions", 0) or 0
        sentiment = getattr(disclosure, "sentiment", "UNKNOWN") or "UNKNOWN"

        # Build indicators
        if mention_count > 10:
            result.indicators.append({
                "claim": f"{mention_count} AI mentions in SEC filings",
                "evidence": f"Sentiment: {sentiment}",
                "risk": "HIGH" if mention_count > 20 else "MEDIUM",
            })

        # Assess scienter risk: high opportunity claims with low threat acknowledgment
        # suggests potential AI-washing (overstating AI capabilities)
        if opp_mentions > 0 and threat_mentions > 0:
            ratio = opp_mentions / max(threat_mentions, 1)
            if ratio > 10:
                result.scienter_risk = "HIGH"
                result.indicators.append({
                    "claim": f"Opportunity-to-threat ratio: {ratio:.1f}:1",
                    "evidence": f"{opp_mentions} opportunity vs {threat_mentions} threat mentions",
                    "risk": "HIGH",
                })
            elif ratio > 3:
                result.scienter_risk = "MEDIUM"
                result.indicators.append({
                    "claim": f"Opportunity-to-threat ratio: {ratio:.1f}:1",
                    "evidence": f"{opp_mentions} opportunity vs {threat_mentions} threat mentions",
                    "risk": "MEDIUM",
                })
        elif opp_mentions > 5 and threat_mentions == 0:
            result.scienter_risk = "MEDIUM"
            result.indicators.append({
                "claim": f"{opp_mentions} AI opportunity claims with zero risk acknowledgment",
                "evidence": "No AI threat/risk disclosure found",
                "risk": "MEDIUM",
            })

    # Overall score context
    overall = getattr(ai_risk, "overall_score", 0) or 0
    if overall > 60:
        result.indicators.append({
            "claim": f"AI risk score: {overall:.0f}/100",
            "evidence": "Composite AI transformation risk assessment",
            "risk": "MEDIUM" if overall < 80 else "HIGH",
        })

    # Build D&O relevance
    if result.indicators:
        result.do_relevance = (
            "SEC has intensified enforcement on AI-washing in securities filings. "
            f"Company has {len(result.indicators)} AI-washing indicator(s) that could "
            "support scienter allegations in an SCA if AI-related claims prove exaggerated."
        )

    return result


def _extract_tariff(state: AnalysisState) -> TariffExposure:
    """Extract tariff/trade exposure from environment + geographic data.

    Sources:
    - state.extracted.environment_assessment.geopolitical_risk_score
    - state.company.geographic_footprint
    """
    result = TariffExposure()

    # Get geopolitical_risk_score from environment assessment
    env = getattr(getattr(state, "extracted", None), "environment_assessment", None)
    geo_score = 0
    if env and isinstance(env, dict):
        geo_score = env.get("geopolitical_risk_score", 0)
        if isinstance(geo_score, (int, float)):
            if geo_score >= 3:
                result.risk_level = "HIGH"
                result.supply_chain_exposure = "Significant exposure to sanctioned/restricted countries"
            elif geo_score >= 1:
                result.risk_level = "MEDIUM"
                result.supply_chain_exposure = "Elevated exposure to high-risk geopolitical regions"
            else:
                result.risk_level = "LOW"
                result.supply_chain_exposure = "Minimal geopolitical exposure identified"

        # Extract detail
        details = env.get("geopolitical_details", {})
        if isinstance(details, dict):
            sanctioned = details.get("sanctioned_countries", [])
            high_risk = details.get("high_risk_countries", [])
            if sanctioned:
                result.tariff_risk_factors.extend(
                    [f"Sanctioned country operations: {c}" for c in sanctioned]
                )
            if high_risk:
                result.tariff_risk_factors.extend(
                    [f"High-risk country operations: {c}" for c in high_risk]
                )

    # Map geographic footprint to manufacturing locations
    footprint = getattr(getattr(state, "company", None), "geographic_footprint", None) or []
    for item in footprint:
        val = item.value if hasattr(item, "value") else item
        if isinstance(val, dict):
            jurisdiction = str(val.get("jurisdiction", "") or val.get("region", ""))
            rev_pct = str(val.get("revenue", "") or val.get("percentage", ""))
            if jurisdiction:
                location = jurisdiction
                if rev_pct:
                    location = f"{jurisdiction} ({rev_pct})"
                result.manufacturing_locations.append(location)

                # Set international revenue percentage from non-US operations
                if "united states" not in jurisdiction.lower() and "us" != jurisdiction.lower():
                    if rev_pct:
                        result.international_revenue_pct = rev_pct

    # Build D&O relevance
    if result.risk_level != "LOW":
        risk_desc = "elevated" if result.risk_level == "MEDIUM" else "significant"
        result.do_relevance = (
            f"Company has {risk_desc} tariff/trade exposure. "
            "Tariff-driven revenue impact could trigger SCA if management failed to "
            "adequately disclose supply chain vulnerabilities in forward-looking statements."
        )
        if result.tariff_risk_factors:
            result.do_relevance += f" {len(result.tariff_risk_factors)} specific risk factor(s) identified."

    return result


def _extract_peer_sca(state: AnalysisState) -> PeerSCACheck:
    """Extract peer SCA contagion risk from existing web + litigation data.

    Sources:
    - state.acquired_data.web_search_results for SCA mentions
    - state.company.identity.sic_code for sector classification
    """
    result = PeerSCACheck()

    # Get sector from SIC code
    sic_code = ""
    company = getattr(state, "company", None)
    if company:
        identity = getattr(company, "identity", None)
        if identity:
            sic_sv = getattr(identity, "sic_code", None)
            if sic_sv:
                sic_code = str(sic_sv.value if hasattr(sic_sv, "value") else sic_sv)

            sector_sv = getattr(identity, "sector", None)
            if sector_sv:
                result.sector = str(sector_sv.value if hasattr(sector_sv, "value") else sector_sv)

    if not result.sector and sic_code:
        # Rough SIC-to-sector mapping for sector label
        try:
            from do_uw.stages.resolve.sec_identity import sic_to_sector
            result.sector = sic_to_sector(sic_code)
        except ImportError:
            result.sector = f"SIC {sic_code}"

    # Scan web search results for peer SCA mentions
    web_results = getattr(
        getattr(state, "acquired_data", None), "web_search_results", None
    ) or []

    for item in web_results:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", ""))
        snippet = str(item.get("snippet", ""))
        combined = f"{title} {snippet}"

        if _SCA_KEYWORDS.search(combined):
            result.peer_scas.append({
                "company": title[:80],
                "filing_date": "",
                "allegation": snippet[:200],
            })

    # Classify contagion risk
    sca_count = len(result.peer_scas)
    if sca_count >= 3:
        result.contagion_risk = "HIGH"
    elif sca_count >= 1:
        result.contagion_risk = "MEDIUM"
    else:
        result.contagion_risk = "LOW"

    # Build D&O relevance
    if result.peer_scas:
        result.do_relevance = (
            f"{sca_count} peer SCA(s) identified in {result.sector} sector. "
            "Sector-wide SCA waves increase contagion risk -- similar allegations "
            "may be brought against this company if comparable disclosures or "
            "financial patterns exist."
        )

    return result


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_alt_data(state: AnalysisState) -> None:
    """Extract all alternative data assessments from existing state data.

    Populates state.alt_data with ESG, AI-washing, tariff, and peer SCA.
    All data sourced from already-acquired state -- no new MCP calls.

    Args:
        state: Analysis state with extracted environment assessment,
               AI risk, geographic data, and web search results.
    """
    state.alt_data.esg = _extract_esg(state)
    state.alt_data.ai_washing = _extract_ai_washing(state)
    state.alt_data.tariff = _extract_tariff(state)
    state.alt_data.peer_sca = _extract_peer_sca(state)

    logger.info(
        "Alt data extraction complete: ESG=%s, AI-washing=%s, Tariff=%s, PeerSCA=%s",
        state.alt_data.esg.risk_level,
        state.alt_data.ai_washing.scienter_risk,
        state.alt_data.tariff.risk_level,
        state.alt_data.peer_sca.contagion_risk,
    )


__all__ = ["extract_alt_data"]
