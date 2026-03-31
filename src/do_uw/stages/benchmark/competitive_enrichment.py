"""Phase 119: Competitive landscape D&O enrichment.

Generates company-specific D&O commentary for the competitive landscape
section of the intelligence dossier: overall do_commentary and per-moat
do_risk narratives explaining what happens if each moat erodes.

Runs in BENCHMARK stage after competitive landscape data is populated.
"""

from __future__ import annotations

import logging

from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)

# Moat dimension -> D&O risk if eroded
_MOAT_DO_RISK: dict[str, str] = {
    "Scale Economics": (
        "Scale erosion triggers revenue compression -> guidance miss -> "
        "Section 10(b) claims from shareholders alleging management concealed "
        "declining competitive position."
    ),
    "Switching Costs": (
        "Low switching costs = customer churn risk -> revenue volatility -> "
        "SCA exposure if management represented customer retention as strong."
    ),
    "Brand Premium": (
        "Brand damage (product recall, scandal) -> stock drop -> D&O claims. "
        "Brand erosion also weakens pricing power, compressing margins and "
        "creating earnings miss risk."
    ),
    "Network Effects": (
        "Network shrinkage accelerates non-linearly -> user/revenue loss -> "
        "Section 10(b) exposure if management touted network growth metrics."
    ),
    "Data Advantage": (
        "Data breach or regulatory restriction -> competitive loss -> "
        "stock decline. Privacy regulation (GDPR, state laws) may force "
        "data deletion that destroys competitive moat."
    ),
    "Regulatory Barrier": (
        "Deregulation removes barrier -> margin compression -> guidance "
        "failure. Regulatory moats are externally controlled -- management "
        "has limited ability to defend."
    ),
    "Distribution Lock": (
        "Channel disruption -> revenue concentration loss -> earnings miss. "
        "If key distribution partners defect, revenue guidance becomes unreliable."
    ),
}


def enrich_competitive_landscape(state: AnalysisState) -> None:
    """Add D&O commentary to competitive landscape data.

    Populates:
    - CompetitiveLandscape.do_commentary: overall narrative
    - MoatDimension.do_risk: per-moat erosion risk (Weak/Moderate only)

    Args:
        state: AnalysisState with dossier.competitive_landscape populated.
    """
    cl = state.dossier.competitive_landscape
    if not cl.peers and not cl.moat_dimensions:
        return

    company = _get_company_name(state)

    # Build do_commentary from peers + moat dimensions
    peer_count = len(cl.peers)
    moat_present = [m for m in cl.moat_dimensions if m.present]
    moat_weak = [
        m for m in cl.moat_dimensions
        if m.present and m.strength == "Weak"
    ]

    parts: list[str] = []
    if peer_count > 0:
        parts.append(
            f"{company} faces competition from {peer_count} identified peer(s)."
        )
    if moat_present:
        names = ", ".join(m.dimension for m in moat_present)
        parts.append(
            f"{len(moat_present)} moat dimension(s) present ({names})."
        )
    if moat_weak:
        parts.append(
            f"WARNING: {len(moat_weak)} moat(s) rated Weak -- "
            f"erosion risk elevated for D&O exposure."
        )

    cl.do_commentary = " ".join(parts)

    # Per-moat do_risk for Weak and Moderate moats
    for moat in cl.moat_dimensions:
        if moat.present and moat.strength in ("Weak", "Moderate"):
            moat.do_risk = _MOAT_DO_RISK.get(
                moat.dimension,
                f"{moat.dimension} erosion creates D&O exposure through "
                f"competitive position deterioration and potential earnings impact.",
            )

    logger.info(
        "Competitive landscape enriched: %d peers, %d moats, %d with do_risk",
        peer_count,
        len(moat_present),
        sum(1 for m in cl.moat_dimensions if m.do_risk),
    )


def _get_company_name(state: AnalysisState) -> str:
    """Extract company name from state with fallback to ticker."""
    if state.company and state.company.identity.legal_name:
        return state.company.identity.legal_name.value
    return state.ticker or "Company"
