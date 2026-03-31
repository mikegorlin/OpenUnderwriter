"""Filing text fetcher -- backward-compatible wrapper for 10-K sections.

Delegates full document fetching to filing_fetcher.py and section
parsing to extract/filing_sections.py. Maintains the same public API
(fetch_filing_texts, fetch_filing_content) so existing Phase 3
extractors continue to work without changes.

Phase 4 refactor: Section parsing moved to extract/filing_sections.py,
Exhibit 21 and HTML stripping moved to filing_fetcher.py.
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.stages.acquire.clients.filing_fetcher import (
    fetch_exhibit_21,
    strip_html,
)
from do_uw.stages.acquire.rate_limiter import sec_get_text
from do_uw.stages.extract.filing_sections import extract_10k_sections

TYPE_CHECKING = False
if TYPE_CHECKING:
    from do_uw.cache.sqlite_cache import AnalysisCache

logger = logging.getLogger(__name__)


def fetch_filing_texts(
    filings_metadata: dict[str, Any],
    cik: str,
) -> dict[str, str]:
    """Fetch most recent 10-K text and parse into key sections.

    Downloads the primary document of the most recent annual filing
    and extracts Item 1, Item 7, and Item 9A sections.

    Args:
        filings_metadata: Dict keyed by filing type, each containing
            a list of filing metadata dicts with primary_doc_url.
        cik: Company CIK (unpadded) for URL construction.

    Returns:
        Dict with section keys: "10-K_item1", "10-K_item7",
        "10-K_item9a", "item1", "item7" (aliases).
        Empty dict if no annual filing available.
    """
    # Find most recent annual filing (domestic 10-K or FPI 20-F).
    form_type = "10-K"
    latest = _get_latest_filing(filings_metadata, "10-K")
    if latest is None:
        latest = _get_latest_filing(filings_metadata, "20-F")
        form_type = "20-F"
    if latest is None:
        logger.info("No annual filing found for text extraction")
        return {}

    url = str(latest.get("primary_doc_url", ""))
    if not url:
        logger.warning("Annual filing has no primary_doc_url")
        return {}

    filing_date = str(latest.get("filing_date", "unknown"))
    accession = str(latest.get("accession_number", ""))
    source_ref = f"{form_type} {filing_date} {accession}"

    logger.info("Fetching %s text from %s", form_type, url)
    try:
        html = sec_get_text(url)
    except Exception:
        logger.warning("Failed to fetch %s text from %s", form_type, url)
        return {}

    if not html:
        return {}

    # Strip HTML to plain text for section parsing.
    text = strip_html(html)

    # Delegate section parsing to extract/filing_sections.py.
    sections = extract_10k_sections(text)
    sections["_source"] = source_ref

    return sections


def fetch_filing_content(
    filings_metadata: dict[str, Any],
    cik: str,
    cache: AnalysisCache | None = None,
) -> tuple[dict[str, str], str]:
    """Fetch filing text content with caching (10-K sections + Exhibit 21).

    Orchestrates fetch_filing_texts() and fetch_exhibit_21() with a
    caching layer. Called by SECFilingClient.acquire().

    Args:
        filings_metadata: Dict from SEC client acquire(), keyed by
            filing type.
        cik: Company CIK (unpadded).
        cache: Optional cache for storing results.

    Returns:
        Tuple of (filing_texts dict, exhibit_21 text).
    """
    latest_10k = _get_latest_filing(filings_metadata, "10-K")
    if latest_10k is None:
        latest_10k = _get_latest_filing(filings_metadata, "20-F")
    if latest_10k is None:
        return {}, ""

    accession = str(latest_10k.get("accession_number", ""))
    if not accession:
        return {}, ""

    cache_key_texts = f"sec:filing_texts:{accession}"
    cache_key_ex21 = f"sec:exhibit_21:{accession}"
    ttl = 14 * 30 * 24 * 3600  # 14 months (same as 10-K)

    filing_texts: dict[str, str] = {}
    exhibit_21 = ""

    # Check cache.
    if cache is not None:
        cached_texts = cache.get(cache_key_texts)
        if cached_texts is not None and isinstance(cached_texts, dict):
            filing_texts = {
                str(k): str(v)
                for k, v in cast(dict[str, Any], cached_texts).items()
            }
        cached_ex21 = cache.get(cache_key_ex21)
        if cached_ex21 is not None and isinstance(cached_ex21, str):
            exhibit_21 = cached_ex21

    if filing_texts and exhibit_21:
        logger.debug("Cache hit for filing text content")
        return filing_texts, exhibit_21

    # Fetch if not cached.
    if not filing_texts:
        logger.info("Fetching 10-K text sections for CIK %s", cik)
        filing_texts = fetch_filing_texts(filings_metadata, cik)
        if cache is not None and filing_texts:
            cache.set(
                cache_key_texts,
                filing_texts,
                source="sec_edgar:filing_text",
                ttl=ttl,
            )

    if not exhibit_21:
        logger.info("Fetching Exhibit 21 for CIK %s", cik)
        exhibit_21 = fetch_exhibit_21(filings_metadata, cik, cache)

    return filing_texts, exhibit_21


def _get_latest_filing(
    filings_metadata: dict[str, Any],
    form_type: str,
) -> dict[str, str] | None:
    """Get the most recent filing metadata dict for a given form type.

    Args:
        filings_metadata: Dict keyed by filing type.
        form_type: Filing type to look up (e.g., "10-K").

    Returns:
        Filing metadata dict, or None if not found.
    """
    raw = filings_metadata.get(form_type)
    if raw is None or not isinstance(raw, list) or not raw:
        return None
    typed_list = cast(list[object], raw)
    first = typed_list[0]
    if not isinstance(first, dict):
        return None
    return cast(dict[str, str], first)
