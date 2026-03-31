"""Phase 119: Context builder for competitive landscape + moat assessment.

Context builders are pure data formatters -- no evaluative logic,
no D&O commentary generation. Templates receive pre-computed data.

Phase 119: Stock Drop Catalysts, Competitive Landscape, Alt Data
"""

from __future__ import annotations

from typing import Any

from do_uw.models.state import AnalysisState


def build_competitive_landscape_context(
    state: AnalysisState,
    *,
    signal_results: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build competitive landscape context for template.

    Reads from state.dossier.competitive_landscape and formats
    peer rows and moat dimensions for Jinja2 template consumption.

    Args:
        state: Analysis state with dossier.competitive_landscape populated.
        signal_results: Optional signal results for D&O context (unused here).

    Returns:
        Dict with comp_peers, comp_moats, comp_narrative, comp_do,
        and has_competitive_data flag.
    """
    cl = state.dossier.competitive_landscape
    result: dict[str, Any] = {
        "comp_peers": [],
        "comp_moats": [],
        "comp_narrative": cl.competitive_position_narrative,
        "comp_do": cl.do_commentary,
        "has_competitive_data": bool(cl.peers or cl.moat_dimensions),
    }
    for peer in cl.peers:
        result["comp_peers"].append({
            "company": peer.company_name,
            "ticker": peer.ticker,
            "market_cap": peer.market_cap or "Not Disclosed",
            "revenue": peer.revenue or "Not Disclosed",
            "margin": peer.margin or "Not Disclosed",
            "growth": peer.growth_rate or "Not Disclosed",
            "rd_spend": peer.rd_spend or "Not Disclosed",
            "market_share": peer.market_share or "Not Disclosed",
            "sca_history": peer.sca_history or "Not Disclosed",
            "do_relevance": peer.do_relevance,
        })
    for moat in cl.moat_dimensions:
        result["comp_moats"].append({
            "dimension": moat.dimension,
            "present": "Yes" if moat.present else "No",
            "strength": moat.strength or "N/A",
            "durability": moat.durability or "N/A",
            "evidence": moat.evidence,
            "do_risk": moat.do_risk,
        })
    return result
