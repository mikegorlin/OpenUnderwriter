"""Phase 119: Context builders for alternative data assessments.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Four alt data assessments: ESG, AI-washing, tariff exposure, peer SCA contagion.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState


def build_esg_context(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ESG / greenwashing risk context for template.

    Args:
        state: Analysis state with alt_data.esg populated.
        signal_results: Optional signal results (unused).

    Returns:
        Dict with esg_risk_level, esg_controversies, esg_ratings,
        esg_greenwashing, esg_do_relevance, and has_esg_data flag.
    """
    esg = state.alt_data.esg
    return {
        "esg_risk_level": esg.risk_level,
        "esg_controversies": esg.controversies,
        "esg_ratings": [{"agency": k, "rating": v} for k, v in esg.ratings.items()],
        "esg_greenwashing": esg.greenwashing_indicators,
        "esg_do_relevance": esg.do_relevance,
        "has_esg_data": esg.risk_level != "LOW" or bool(esg.controversies),
    }


def build_ai_washing_context(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build AI-washing risk context for template.

    Args:
        state: Analysis state with alt_data.ai_washing populated.
        signal_results: Optional signal results (unused).

    Returns:
        Dict with ai_claims_present, ai_indicators, ai_scienter_risk,
        ai_do_relevance, and has_ai_data flag.
    """
    ai = state.alt_data.ai_washing
    return {
        "ai_claims_present": ai.ai_claims_present,
        "ai_indicators": ai.indicators,
        "ai_scienter_risk": ai.scienter_risk,
        "ai_do_relevance": ai.do_relevance,
        "has_ai_data": ai.ai_claims_present,
    }


def build_tariff_context(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build tariff / trade exposure context for template.

    Args:
        state: Analysis state with alt_data.tariff populated.
        signal_results: Optional signal results (unused).

    Returns:
        Dict with tariff_risk_level, tariff_supply_chain,
        tariff_manufacturing, tariff_intl_revenue, tariff_factors,
        tariff_do_relevance, and has_tariff_data flag.
    """
    t = state.alt_data.tariff
    return {
        "tariff_risk_level": t.risk_level,
        "tariff_supply_chain": t.supply_chain_exposure or "Not assessed",
        "tariff_manufacturing": t.manufacturing_locations,
        "tariff_intl_revenue": t.international_revenue_pct or "N/A",
        "tariff_factors": t.tariff_risk_factors,
        "tariff_do_relevance": t.do_relevance,
        "has_tariff_data": t.risk_level != "LOW",
    }


def build_peer_sca_context(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build peer SCA contagion context for template.

    Args:
        state: Analysis state with alt_data.peer_sca populated.
        signal_results: Optional signal results (unused).

    Returns:
        Dict with peer_scas, peer_sector, peer_contagion_risk,
        peer_do_relevance, and has_peer_sca flag.
    """
    p = state.alt_data.peer_sca
    return {
        "peer_scas": p.peer_scas,
        "peer_sector": p.sector,
        "peer_contagion_risk": p.contagion_risk,
        "peer_do_relevance": p.do_relevance,
        "has_peer_sca": bool(p.peer_scas),
    }
