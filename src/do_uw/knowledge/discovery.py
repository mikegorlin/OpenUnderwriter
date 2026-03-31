"""Automatic blind spot discovery and ingestion hook.

Post-acquisition hook that filters blind spot search results for
high D&O relevance, fetches content, and feeds through the LLM
ingestion pipeline to generate proposals. All operations are
non-blocking: failures for individual URLs are logged and skipped.

IMPORTANT: This does NOT auto-change anything. Only creates proposals
in brain_proposals table with INCUBATING status for human review.

Functions:
    process_blind_spot_discoveries: Main hook for ACQUIRE stage
    get_discovery_summary: Format discoveries for worksheet display
"""

from __future__ import annotations

import logging
from typing import Any, cast

logger = logging.getLogger(__name__)

# Keywords indicating high D&O relevance in search results.
_DO_KEYWORDS: list[str] = [
    "litigation",
    "lawsuit",
    "sec",
    "enforcement",
    "fraud",
    "settlement",
    "investigation",
    "short seller",
    "activist",
    "whistleblower",
    "subpoena",
    "restatement",
    "securities class action",
    "derivative suit",
    "insider trading",
    "material weakness",
    "accounting irregularity",
    "regulatory action",
    "class period",
    "wells notice",
]

# Minimum relevance score (0-10) to trigger ingestion.
_RELEVANCE_THRESHOLD = 5


def _score_relevance(title: str, snippet: str) -> int:
    """Score D&O relevance of a search result based on keyword density.

    Checks title and snippet for presence of D&O-relevant keywords.
    Title matches count double since they indicate higher relevance.

    Args:
        title: Search result title.
        snippet: Search result snippet/description.

    Returns:
        Relevance score 0-10.
    """
    title_lower = title.lower()
    snippet_lower = snippet.lower()
    score = 0

    for keyword in _DO_KEYWORDS:
        if keyword in title_lower:
            score += 2  # Title matches weight double
        elif keyword in snippet_lower:
            score += 1

    # Cap at 10
    return min(score, 10)


def process_blind_spot_discoveries(
    blind_spot_results: dict[str, Any],
    ticker: str,
) -> list[dict[str, Any]]:
    """Process blind spot search results through ingestion pipeline.

    Filters for high D&O relevance results, fetches content, and runs
    LLM extraction to generate proposals. All operations are non-blocking.

    IMPORTANT: Does NOT auto-change anything. Only creates proposals
    in brain_proposals as INCUBATING for human review.

    Args:
        blind_spot_results: Dict from state.acquired_data.blind_spot_results.
            Contains nested dicts like {category: [result_dicts]}.
        ticker: Stock ticker for context.

    Returns:
        List of discovery summaries:
            [{url, title, event_type, proposals_generated}]
    """
    discoveries: list[dict[str, Any]] = []

    # Collect all search results from pre_structured and post_structured
    all_results: list[dict[str, str]] = []
    for key in ("pre_structured", "post_structured"):
        raw = blind_spot_results.get(key)
        if not isinstance(raw, dict):
            continue
        category_results = cast(dict[str, list[dict[str, str]]], raw)
        for _category, results in category_results.items():
            all_results.extend(results)

    if not all_results:
        logger.debug("No blind spot results to process for %s", ticker)
        return discoveries

    # Filter for high-relevance results
    high_relevance: list[tuple[dict[str, str], int]] = []
    for result in all_results:
        title = result.get("title", "")
        snippet = result.get("snippet", "")
        score = _score_relevance(title, snippet)
        if score >= _RELEVANCE_THRESHOLD:
            high_relevance.append((result, score))

    if not high_relevance:
        logger.info(
            "No high-relevance blind spot results for %s "
            "(%d results scored below threshold %d)",
            ticker,
            len(all_results),
            _RELEVANCE_THRESHOLD,
        )
        return discoveries

    logger.info(
        "Found %d high-relevance blind spot results for %s "
        "(out of %d total)",
        len(high_relevance),
        ticker,
        len(all_results),
    )

    # Process each high-relevance result
    for result, _score in high_relevance:
        url = result.get("url", "")
        title = result.get("title", "Unknown")

        if not url:
            continue

        discovery = _process_single_result(url, title, ticker)
        if discovery is not None:
            discoveries.append(discovery)

    logger.info(
        "Processed %d discoveries for %s",
        len(discoveries),
        ticker,
    )
    return discoveries


def _process_single_result(
    url: str,
    title: str,
    ticker: str,
) -> dict[str, Any] | None:
    """Process a single high-relevance search result.

    Fetches URL content and runs LLM extraction. Non-blocking:
    returns None on any failure.
    """
    try:
        from do_uw.knowledge.ingestion_llm import (
            extract_document_intelligence,
            fetch_url_content,
            store_proposals,
        )
    except ImportError:
        logger.warning(
            "ingestion_llm not available; skipping discovery for %s", url
        )
        return None

    # Fetch content
    try:
        content = fetch_url_content(url)
    except Exception as exc:
        logger.debug(
            "Failed to fetch %s: %s", url, exc
        )
        return {
            "url": url,
            "title": title,
            "event_type": "FETCH_FAILED",
            "proposals_generated": 0,
        }

    # Extract intelligence via LLM
    try:
        result = extract_document_intelligence(content, "BLIND_SPOT_DISCOVERY")
    except Exception as exc:
        logger.debug(
            "LLM extraction failed for %s: %s", url, exc
        )
        return {
            "url": url,
            "title": title,
            "event_type": "EXTRACTION_FAILED",
            "proposals_generated": 0,
        }

    # Store proposals if any were generated
    proposals_count = 0
    if result.proposed_new_checks:
        try:
            from do_uw.brain.brain_writer import BrainWriter

            writer = BrainWriter()
            proposals_count = store_proposals(
                writer, result, f"blind_spot:{ticker}:{title[:50]}"
            )
            writer.close()
        except Exception as exc:
            logger.debug(
                "Failed to store proposals from %s: %s", url, exc
            )

    return {
        "url": url,
        "title": title,
        "event_type": result.event_type,
        "proposals_generated": proposals_count,
    }


def get_discovery_summary(discoveries: list[dict[str, Any]]) -> str:
    """Format discoveries into a human-readable summary string.

    Args:
        discoveries: List of discovery dicts from process_blind_spot_discoveries.

    Returns:
        Summary string for worksheet display, e.g.:
        "3 documents analyzed, 2 proposals generated from blind spot search"
    """
    if not discoveries:
        return ""

    total_docs = len(discoveries)
    total_proposals = sum(
        d.get("proposals_generated", 0) for d in discoveries
    )

    parts: list[str] = []
    parts.append(f"{total_docs} document(s) analyzed")
    parts.append(f"{total_proposals} proposal(s) generated")
    parts.append("from blind spot search")

    return ", ".join(parts)
