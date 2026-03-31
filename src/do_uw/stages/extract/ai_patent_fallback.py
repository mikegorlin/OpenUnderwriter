"""AI patent fallback extractors -- 10-K text and web search.

When the USPTO IBD API is unavailable (discontinued May 2025), these
fallback extractors attempt to find AI patent information from:
1. 10-K filing text: searches for patent mentions near AI/ML keywords
2. Web search results: scans blind-spot discovery results for patent info

All fallback data is LOW confidence since it relies on text pattern
matching rather than a structured patent database.

Part of the SECT8 AI Transformation Risk Factor extraction pipeline.
"""

from __future__ import annotations

import logging
import re
from typing import Any, cast

from do_uw.models.ai_risk import AIPatentActivity
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import get_filing_document_text

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex patterns for AI + patent text scanning
# ---------------------------------------------------------------------------

_AI_KEYWORDS_RE = re.compile(
    r"(?:artificial intelligence|machine learning|deep learning"
    r"|neural network|generative AI|AI[- ](?:powered|driven|enabled|based)"
    r"|natural language processing|computer vision|large language model"
    r"|AI model|ML model)",
    re.IGNORECASE,
)

# Patterns to extract patent counts from text (e.g., "125 patents",
# "filed 30 patent applications")
_PATENT_COUNT_RE = re.compile(
    r"(?:(?:hold|own|maintain|possess|have|filed|granted|issued|awarded|received)"
    r"\s+(?:approximately\s+|over\s+|more than\s+|about\s+)?"
    r"(\d[\d,]*)\s+(?:AI\s+|machine learning\s+)?patent"
    r"|(\d[\d,]*)\s+(?:AI\s+|machine learning\s+)?patent"
    r"(?:s|\s+application)?(?:\s+(?:filed|granted|pending|issued)))",
    re.IGNORECASE,
)

# Broader patent mention (just "patent" near AI keywords)
_PATENT_MENTION_RE = re.compile(r"\bpatent(?:s|ed)?\b", re.IGNORECASE)

_CONTEXT_WINDOW = 300  # chars around AI keyword to look for patent mentions


# ---------------------------------------------------------------------------
# 10-K text fallback
# ---------------------------------------------------------------------------


def extract_from_10k_text(
    state: AnalysisState,
) -> AIPatentActivity | None:
    """Extract AI patent info from 10-K filing text.

    Searches 10-K text for patent mentions near AI/ML keywords.
    Returns AIPatentActivity with LOW confidence data, or None if
    no relevant text is found.
    """
    text = get_filing_document_text(state, "10-K")
    if not text or len(text) < 200:
        return None

    # Find all AI keyword positions
    ai_positions: list[int] = [m.start() for m in _AI_KEYWORDS_RE.finditer(text)]
    if not ai_positions:
        return None

    # Look for patent mentions near AI keywords
    patent_mentions = 0
    extracted_count: int | None = None
    snippets: list[str] = []

    for pos in ai_positions:
        window_start = max(0, pos - _CONTEXT_WINDOW)
        window_end = min(len(text), pos + _CONTEXT_WINDOW)
        window = text[window_start:window_end]

        # Check for patent mentions in this window
        patent_hits = _PATENT_MENTION_RE.findall(window)
        if patent_hits:
            patent_mentions += len(patent_hits)

            # Try to extract a specific count
            count_match = _PATENT_COUNT_RE.search(window)
            if count_match:
                raw_count = count_match.group(1) or count_match.group(2)
                if raw_count:
                    parsed = int(raw_count.replace(",", ""))
                    if extracted_count is None or parsed > extracted_count:
                        extracted_count = parsed

            # Capture snippet for recent_filings context
            snippet = window.strip()
            if len(snippet) > 200:
                snippet = snippet[:200] + "..."
            if len(snippets) < 5:
                snippets.append(snippet)

    if patent_mentions == 0:
        return None

    ai_patent_count = extracted_count if extracted_count is not None else 0

    recent_filings: list[dict[str, str]] = []
    for i, snippet in enumerate(snippets):
        recent_filings.append(
            {
                "patent_number": f"10-K-mention-{i + 1}",
                "filing_date": "",
                "title": snippet[:100],
            }
        )

    logger.info(
        "SECT8: 10-K text fallback found %d patent mentions (extracted count: %s)",
        patent_mentions,
        extracted_count,
    )

    return AIPatentActivity(
        ai_patent_count=ai_patent_count,
        recent_filings=recent_filings,
        filing_trend="UNKNOWN",
    )


# ---------------------------------------------------------------------------
# Web search fallback
# ---------------------------------------------------------------------------


def extract_from_web_search(
    state: AnalysisState,
) -> AIPatentActivity | None:
    """Extract AI patent info from web search results.

    Looks through blind-spot web search results for patent-related
    content. Returns AIPatentActivity with LOW confidence data, or
    None if no relevant results are found.
    """
    if state.acquired_data is None:
        return None

    web_results = state.acquired_data.web_search_results
    if not web_results:
        return None

    patent_mentions = 0
    snippets: list[str] = []
    extracted_count: int | None = None

    for _key, result_group in web_results.items():
        entries = _extract_entries(result_group)
        for entry in entries:
            text = _entry_to_text(entry)
            if not text:
                continue

            # Check if text contains both patent and AI keywords
            has_patent = _PATENT_MENTION_RE.search(text) is not None
            has_ai = _AI_KEYWORDS_RE.search(text) is not None

            if has_patent and has_ai:
                patent_mentions += 1

                # Try to extract a count
                count_match = _PATENT_COUNT_RE.search(text)
                if count_match:
                    raw_count = count_match.group(1) or count_match.group(2)
                    if raw_count:
                        parsed = int(raw_count.replace(",", ""))
                        if extracted_count is None or parsed > extracted_count:
                            extracted_count = parsed

                if len(snippets) < 5:
                    snippet = text[:150].strip()
                    snippets.append(snippet)

    if patent_mentions == 0:
        return None

    ai_patent_count = extracted_count if extracted_count is not None else 0

    recent_filings: list[dict[str, str]] = []
    for i, snippet in enumerate(snippets):
        recent_filings.append(
            {
                "patent_number": f"web-search-{i + 1}",
                "filing_date": "",
                "title": snippet[:100],
            }
        )

    logger.info(
        "SECT8: Web search fallback found %d patent mentions (extracted count: %s)",
        patent_mentions,
        extracted_count,
    )

    return AIPatentActivity(
        ai_patent_count=ai_patent_count,
        recent_filings=recent_filings,
        filing_trend="UNKNOWN",
    )


# ---------------------------------------------------------------------------
# Web search result parsing helpers
# ---------------------------------------------------------------------------


def _extract_entries(result_group: Any) -> list[Any]:
    """Extract a flat list of result entries from a result group.

    Web search results may be a list of dicts, a dict with a list
    value, or nested structures. This normalizes them.
    """
    if isinstance(result_group, list):
        return cast(list[Any], result_group)
    if isinstance(result_group, dict):
        group_dict = cast(dict[str, Any], result_group)
        # Try common keys for result lists
        for key in ("results", "items", "entries", "data"):
            val = group_dict.get(key)
            if isinstance(val, list):
                return cast(list[Any], val)
        # If the dict itself looks like a single result, wrap it
        if "title" in group_dict or "snippet" in group_dict:
            return [group_dict]
    return []


def _entry_to_text(entry: Any) -> str:
    """Convert a web search result entry to searchable text."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        entry_dict = cast(dict[str, Any], entry)
        parts: list[str] = []
        for key in ("title", "snippet", "description", "content", "body"):
            val = entry_dict.get(key)
            if val and isinstance(val, str):
                parts.append(val)
        return " ".join(parts)
    return ""
