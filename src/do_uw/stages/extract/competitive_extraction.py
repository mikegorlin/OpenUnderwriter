"""Phase 119: Competitive landscape extraction from 10-K Item 1.

LLM extracts competitive landscape data from the Business Description
section of the most recent 10-K filing. Populates
state.dossier.competitive_landscape with peers, moat dimensions,
and competitive position narrative.

Usage:
    await extract_competitive_landscape(state)
    # state.dossier.competitive_landscape is now populated
"""

from __future__ import annotations

import json
import logging
from typing import Any

from do_uw.models.competitive_landscape import (
    CompetitiveLandscape,
    MoatDimension,
    PeerRow,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import get_filing_documents

logger = logging.getLogger(__name__)

_FILING_TYPES = ("10-K", "20-F")

_MOAT_DIMENSIONS = [
    "Data Advantage",
    "Switching Costs",
    "Scale Economics",
    "Brand Premium",
    "Network Effects",
    "Regulatory Barrier",
    "Distribution Lock",
]

_COMPETITIVE_PROMPT = """Extract competitive landscape from this 10-K filing section.

Analytical Context:
Company: {company_name} ({ticker})
Sector: {sector}
Revenue: {revenue}
{scoring_context}

From the Business Description / Competition section, extract:

1. COMPETITORS: List 4+ named competitors. For each provide:
   - company_name: Official name
   - ticker: Stock ticker if known, else ""
   - market_cap: If mentioned, else "Not Disclosed"
   - revenue: If mentioned, else "Not Disclosed"
   - margin: If mentioned, else "Not Disclosed"
   - growth_rate: If mentioned, else "Not Disclosed"
   - rd_spend: If mentioned, else "Not Disclosed"
   - market_share: If mentioned, else "Not Disclosed"
   - stock_performance: "Not Disclosed" (we don't have peer data)
   - sca_history: "Not Disclosed" (checked separately)

2. MOAT DIMENSIONS: For each of these 7 dimensions, assess based on 10-K evidence:
   {moat_dims}
   For each: present (true/false), strength (Strong/Moderate/Weak), durability (High/Medium/Low), evidence (specific quote or fact from 10-K)

3. COMPETITIVE POSITION: A 2-3 sentence narrative describing this company's competitive position, referencing specific advantages/vulnerabilities from the 10-K.

CRITICAL: Use "Not Disclosed" for any metric not explicitly stated in the filing. Do NOT guess or estimate financial figures. Mark confidence as MEDIUM for all LLM-extracted data.

Respond in JSON format:
{{
  "peers": [{{...}}],
  "moat_dimensions": [{{...}}],
  "competitive_position_narrative": "..."
}}"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_analytical_context(state: AnalysisState) -> dict[str, str]:
    """Build QUAL-03 analytical context from state."""
    company = state.company
    company_name = ""
    ticker = ""

    if company:
        ticker = getattr(company.identity, "ticker", "") or ""
        legal_name = getattr(company.identity, "legal_name", None)
        if legal_name and hasattr(legal_name, "value"):
            company_name = str(legal_name.value or "")

    sector = ""
    if company:
        sector_sv = getattr(company.identity, "sector", None)
        if sector_sv and hasattr(sector_sv, "value"):
            sector = str(sector_sv.value or "")

    revenue = "Not available"
    extracted = getattr(state, "extracted", None)
    if extracted:
        financials = getattr(extracted, "financials", None)
        if financials:
            statements = getattr(financials, "statements", None) or []
            for stmt in statements:
                rev_val = getattr(stmt, "revenue", None)
                if rev_val is not None:
                    try:
                        rv = float(rev_val)
                        if rv > 1_000_000:
                            revenue = f"${rv / 1_000_000:.1f}M"
                        else:
                            revenue = f"${rv:,.0f}"
                    except (ValueError, TypeError):
                        pass
                    break

    scoring_context = "Not yet scored"
    scoring = getattr(state, "scoring", None)
    if scoring:
        score = getattr(scoring, "composite_score", None)
        if score is not None:
            tier = getattr(scoring, "tier", "")
            scoring_context = f"Score: {score}, Tier: {tier}"

    return {
        "company_name": company_name,
        "ticker": ticker,
        "sector": sector,
        "revenue": revenue,
        "scoring_context": scoring_context,
    }


def _get_filing_text(state: AnalysisState) -> tuple[str, str]:
    """Get the best available 10-K/20-F filing text and accession.

    Returns (full_text, accession) or ("", "") if unavailable.
    """
    filing_docs = get_filing_documents(state)

    for form_type in _FILING_TYPES:
        docs = filing_docs.get(form_type, [])
        if not isinstance(docs, list):
            continue
        for doc in docs[:1]:
            if not isinstance(doc, dict):
                continue
            full_text = doc.get("full_text", "")
            accession = doc.get("accession", "")
            if full_text and accession:
                return full_text, accession

    return "", ""


def _run_competitive_llm(
    filing_text: str,
    accession: str,
    prompt: str,
) -> dict[str, Any] | None:
    """Run LLM extraction for competitive landscape.

    Returns parsed JSON dict or None on failure.
    """
    try:
        from pathlib import Path

        from do_uw.stages.extract.llm import ExtractionCache, LLMExtractor

        cache = ExtractionCache(db_path=Path(".cache/analysis.db"))
        extractor = LLMExtractor(cache=cache, rate_limit_tpm=100_000_000)

        # Use raw JSON extraction (no schema class needed)
        result = extractor.extract_raw(
            filing_text=filing_text,
            accession=accession,
            form_type="10-K-competitive",
            system_prompt=prompt,
            max_tokens=4096,
        )
        if isinstance(result, str):
            return json.loads(result)  # type: ignore[no-any-return]
        if isinstance(result, dict):
            return result  # type: ignore[return-value]
    except Exception:
        logger.warning(
            "Competitive landscape LLM extraction failed for %s",
            accession,
            exc_info=True,
        )
    return None


def _parse_peers(raw_peers: list[dict[str, Any]]) -> list[PeerRow]:
    """Parse raw peer dicts into PeerRow models."""
    peers: list[PeerRow] = []
    for raw in raw_peers:
        if not isinstance(raw, dict):
            continue
        peers.append(
            PeerRow(
                company_name=str(raw.get("company_name", "")),
                ticker=str(raw.get("ticker", "")),
                market_cap=str(raw.get("market_cap", "Not Disclosed")),
                revenue=str(raw.get("revenue", "Not Disclosed")),
                margin=str(raw.get("margin", "Not Disclosed")),
                growth_rate=str(raw.get("growth_rate", "Not Disclosed")),
                rd_spend=str(raw.get("rd_spend", "Not Disclosed")),
                market_share=str(raw.get("market_share", "Not Disclosed")),
                stock_performance=str(raw.get("stock_performance", "Not Disclosed")),
                sca_history=str(raw.get("sca_history", "Not Disclosed")),
            )
        )
    return peers


def _parse_moat_dimensions(raw_dims: list[dict[str, Any]]) -> list[MoatDimension]:
    """Parse raw moat dimension dicts into MoatDimension models."""
    dims: list[MoatDimension] = []
    for raw in raw_dims:
        if not isinstance(raw, dict):
            continue
        dims.append(
            MoatDimension(
                dimension=str(raw.get("dimension", "")),
                present=bool(raw.get("present", False)),
                strength=str(raw.get("strength", "")),
                durability=str(raw.get("durability", "")),
                evidence=str(raw.get("evidence", "")),
                do_risk=str(raw.get("do_risk", "")),
            )
        )
    return dims


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def extract_competitive_landscape(state: AnalysisState) -> None:
    """Extract competitive landscape from 10-K and populate state.dossier.competitive_landscape.

    Orchestrates LLM extraction from the Business Description / Competition
    section of the most recent 10-K filing. Falls back gracefully to
    empty CompetitiveLandscape if no filing text is available.

    Args:
        state: Analysis state with acquired filing documents.
    """
    filing_text, accession = _get_filing_text(state)

    if not filing_text:
        logger.info("No 10-K text available for competitive landscape extraction.")
        return

    # Build prompt with QUAL-03 analytical context
    ctx = _get_analytical_context(state)
    moat_dims_str = "\n   ".join(f"- {d}" for d in _MOAT_DIMENSIONS)
    prompt = _COMPETITIVE_PROMPT.format(
        moat_dims=moat_dims_str,
        **ctx,
    )

    # Run LLM extraction
    result = _run_competitive_llm(filing_text, accession, prompt)
    if result is None:
        logger.warning("Competitive landscape LLM extraction returned None for %s", accession)
        return

    # Parse results into typed models
    raw_peers = result.get("peers", [])
    raw_dims = result.get("moat_dimensions", [])
    narrative = str(result.get("competitive_position_narrative", ""))

    peers = _parse_peers(raw_peers) if isinstance(raw_peers, list) else []
    moat_dims = _parse_moat_dimensions(raw_dims) if isinstance(raw_dims, list) else []

    # Populate state
    cl = state.dossier.competitive_landscape
    cl.peers = peers
    cl.moat_dimensions = moat_dims
    cl.competitive_position_narrative = narrative

    # Build D&O commentary from competitive position
    strong_moats = [m.dimension for m in moat_dims if m.present and m.strength == "Strong"]
    weak_areas = [m.dimension for m in moat_dims if not m.present]
    do_parts: list[str] = []
    if strong_moats:
        do_parts.append(
            f"Strong moats ({', '.join(strong_moats)}) reduce competitive disruption SCA risk"
        )
    if weak_areas:
        do_parts.append(
            f"Absent moats ({', '.join(weak_areas)}) increase vulnerability to market share loss claims"
        )
    if len(peers) > 0:
        do_parts.append(f"{len(peers)} named competitors identified from 10-K")
    cl.do_commentary = ". ".join(do_parts) + "." if do_parts else ""

    logger.info(
        "Competitive landscape extraction complete: %d peers, %d moat dimensions",
        len(peers),
        len(moat_dims),
    )


__all__ = ["extract_competitive_landscape"]
