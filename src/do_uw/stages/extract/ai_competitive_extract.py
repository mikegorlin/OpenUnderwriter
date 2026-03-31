"""AI competitive position extractor -- peer-relative AI comparison.

Compares the company's AI engagement level against peers using
disclosure mention counts.  Returns UNKNOWN when peer data is not
available (the normal case for single-ticker analysis).

Part of the SECT8 AI Transformation Risk Factor extraction pipeline.
"""

from __future__ import annotations

import logging

from do_uw.models.ai_risk import AICompetitivePosition, AIDisclosureData
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

_MAX_PEERS = 5


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def assess_competitive_position(
    state: AnalysisState,
    company_disclosure: AIDisclosureData,
) -> tuple[AICompetitivePosition, ExtractionReport]:
    """Assess AI competitive position relative to peers.

    Compares company AI mention count against peer averages.
    Returns UNKNOWN stance when peer data is unavailable (normal case).

    Args:
        state: Pipeline state with extracted financials (peer group).
        company_disclosure: Company's AI disclosure data.

    Returns:
        Tuple of (AICompetitivePosition, ExtractionReport).
    """
    expected_fields = ["peer_comparison", "adoption_stance"]
    company_mentions = company_disclosure.mention_count

    # Get peer group from extracted financials
    peer_mentions = _collect_peer_mentions(state)

    if not peer_mentions:
        logger.info(
            "SECT8: No peer AI mention data available; "
            "competitive position set to UNKNOWN"
        )
        return (
            AICompetitivePosition(
                company_ai_mentions=company_mentions,
                adoption_stance="UNKNOWN",
            ),
            create_report(
                extractor_name="ai_competitive",
                expected=expected_fields,
                found=[],
                source_filing="peer_comparison",
                warnings=["No peer data available for AI comparison"],
            ),
        )

    # Compute peer statistics
    peer_values = list(peer_mentions.values())
    peer_avg = sum(peer_values) / len(peer_values) if peer_values else 0.0

    # Percentile rank
    below_count = sum(1 for v in peer_values if v < company_mentions)
    percentile = (below_count / len(peer_values)) * 100.0

    # Adoption stance classification
    has_patents = _has_patent_activity(state)
    stance = _classify_adoption(company_mentions, peer_avg, has_patents)

    found_fields = ["peer_comparison", "adoption_stance"]

    position = AICompetitivePosition(
        company_ai_mentions=company_mentions,
        peer_avg_mentions=peer_avg,
        peer_mention_counts=peer_mentions,
        percentile_rank=percentile,
        adoption_stance=stance,
    )

    report = create_report(
        extractor_name="ai_competitive",
        expected=expected_fields,
        found=found_fields,
        source_filing="peer_comparison",
    )

    logger.info(
        "SECT8: Competitive position -- stance=%s, percentile=%.0f, "
        "company=%d, peer_avg=%.1f",
        stance,
        percentile,
        company_mentions,
        peer_avg,
    )
    return position, report


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _collect_peer_mentions(state: AnalysisState) -> dict[str, int]:
    """Collect AI mention counts from peer filings if available.

    Checks peer 10-K documents in filing_documents for AI keywords.
    Returns empty dict if no peer filing data is available.
    """
    if state.extracted is None or state.extracted.financials is None:
        return {}

    peer_group = state.extracted.financials.peer_group
    if peer_group is None or not peer_group.peers:
        return {}

    if state.acquired_data is None:
        return {}

    # Check if we have peer filing documents
    peer_mentions: dict[str, int] = {}
    peers_checked = 0

    for peer in peer_group.peers[:_MAX_PEERS]:
        ticker = peer.ticker
        # Peer filings might be stored under peer ticker key
        peer_docs = state.acquired_data.filing_documents.get(
            f"10-K_{ticker}", []
        )
        if not peer_docs:
            continue

        # Count AI mentions in peer's most recent 10-K
        sorted_docs = sorted(
            peer_docs,
            key=lambda d: d.get("filing_date", ""),
            reverse=True,
        )
        full_text = sorted_docs[0].get("full_text", "")
        if full_text:
            count = _count_ai_mentions(full_text)
            peer_mentions[ticker] = count
            peers_checked += 1

    return peer_mentions


def _count_ai_mentions(text: str) -> int:
    """Count AI keyword mentions in text (lightweight version)."""
    import re

    keywords = [
        "artificial intelligence",
        "machine learning",
        "generative AI",
        "deep learning",
        "neural network",
        "AI model",
        "AI system",
        "AI technology",
    ]
    total = 0
    for kw in keywords:
        total += len(re.findall(rf"\b{re.escape(kw)}\b", text, re.IGNORECASE))
    return total


def _has_patent_activity(state: AnalysisState) -> bool:
    """Check if company has any AI patent activity."""
    if state.extracted is None or state.extracted.ai_risk is None:
        return False
    return state.extracted.ai_risk.patent_activity.ai_patent_count > 0


def _classify_adoption(
    company_mentions: int,
    peer_avg: float,
    has_patents: bool,
) -> str:
    """Classify AI adoption stance relative to peers.

    LEADING: mentions > 1.5x peer avg AND has patent activity
    INLINE: mentions within 0.5x-1.5x of peer avg
    LAGGING: mentions < 0.5x of peer avg
    UNKNOWN: insufficient data
    """
    if peer_avg <= 0:
        return "UNKNOWN"

    ratio = company_mentions / peer_avg
    if ratio > 1.5 and has_patents:
        return "LEADING"
    if ratio < 0.5:
        return "LAGGING"
    return "INLINE"
