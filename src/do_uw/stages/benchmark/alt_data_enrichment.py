"""Phase 119: Alternative data D&O relevance enrichment.

Generates company-specific D&O relevance narratives for each alt data
assessment: ESG risk, AI-washing risk, tariff exposure, and peer SCA
contagion.

Runs in BENCHMARK stage. Each assessment gets a do_relevance string
explaining the specific D&O litigation theories triggered by the finding.
"""

from __future__ import annotations

import logging

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


def enrich_alt_data(state: AnalysisState) -> None:
    """Add D&O relevance narratives to all alt data assessments.

    Populates do_relevance on ESG, AI-washing, tariff, and peer SCA
    sub-assessments. Each narrative references company name and specific
    data from the assessment.

    Args:
        state: AnalysisState with alt_data populated.
    """
    company = _get_company_name(state)
    ad = state.alt_data

    _enrich_esg(ad.esg, company)
    _enrich_ai_washing(ad.ai_washing, company)
    _enrich_tariff(ad.tariff, company)
    _enrich_peer_sca(ad.peer_sca, company)

    logger.info("Alt data D&O enrichment complete for %s", company)


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name from state with fallback to ticker."""
    if state.company and state.company.identity.legal_name:
        return state.company.identity.legal_name.value
    return state.ticker or "Company"


# ---------------------------------------------------------------------------
# Sub-enrichment functions
# ---------------------------------------------------------------------------


def _enrich_esg(esg: object, company: str) -> None:
    """Enrich ESG risk with D&O relevance."""
    from do_uw.models.alt_data import ESGRisk

    if not isinstance(esg, ESGRisk):
        return

    if esg.risk_level != "LOW" or esg.controversies:
        controv_count = len(esg.controversies)
        esg.do_relevance = (
            f"{company} ESG risk: {esg.risk_level}. "
            f"{controv_count} controvers{'y' if controv_count == 1 else 'ies'} identified. "
            "ESG gaps create shareholder derivative suit exposure under Caremark "
            "duty of oversight. Greenwashing claims trigger SEC enforcement + "
            "consumer class actions that compound D&O exposure."
        )
    else:
        esg.do_relevance = (
            f"{company} ESG profile: LOW risk. "
            "No significant controversies identified."
        )


def _enrich_ai_washing(ai: object, company: str) -> None:
    """Enrich AI-washing risk with D&O relevance."""
    from do_uw.models.alt_data import AIWashingRisk

    if not isinstance(ai, AIWashingRisk):
        return

    if ai.ai_claims_present:
        indicator_count = len(ai.indicators)
        ai.do_relevance = (
            f"{company} makes AI-related claims "
            f"({indicator_count} indicator{'s' if indicator_count != 1 else ''}). "
            f"Scienter risk: {ai.scienter_risk}. "
            "AI claims without substantive evidence create 10(b) fraud exposure -- "
            "SEC has signaled AI-washing enforcement priority. "
            "Plaintiff attorneys pattern-match AI claims to stock drop to SCA filing."
        )
    else:
        ai.do_relevance = (
            f"No AI-related claims detected for {company}."
        )


def _enrich_tariff(tariff: object, company: str) -> None:
    """Enrich tariff exposure with D&O relevance."""
    from do_uw.models.alt_data import TariffExposure

    if not isinstance(tariff, TariffExposure):
        return

    if tariff.risk_level != "LOW":
        tariff.do_relevance = (
            f"{company} tariff exposure: {tariff.risk_level}. "
            f"Supply chain: {tariff.supply_chain_exposure or 'Unknown'}. "
            f"International revenue: {tariff.international_revenue_pct or 'N/A'}. "
            "Tariff escalation threatens revenue guidance accuracy -- "
            "management failure to disclose known supply chain risk "
            "creates Section 10(b) omission liability."
        )
    else:
        tariff.do_relevance = (
            f"{company} tariff exposure: LOW. "
            "Limited international/supply chain risk."
        )


def _enrich_peer_sca(peer_sca: object, company: str) -> None:
    """Enrich peer SCA contagion with D&O relevance."""
    from do_uw.models.alt_data import PeerSCACheck

    if not isinstance(peer_sca, PeerSCACheck):
        return

    peer_count = len(peer_sca.peer_scas)
    if peer_count > 0:
        peer_sca.do_relevance = (
            f"{peer_count} active SCA(s) against {company}'s sector peers. "
            f"Contagion risk: {peer_sca.contagion_risk}. "
            "Sector SCA activity indicates plaintiff attorney focus on this "
            "industry -- successful peer settlements establish precedent "
            "and attract copycat filings."
        )
    else:
        peer_sca.do_relevance = (
            f"No active SCAs against {company}'s sector peers. "
            "Low contagion risk."
        )
