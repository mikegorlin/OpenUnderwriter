"""Pure SEC filing document fetcher -- downloads full documents by accession.

Downloads the FULL primary document for each SEC filing and stores it
as plain text keyed by accession number. No section parsing happens here;
that is the EXTRACT stage's responsibility.

Also handles Exhibit 21 (subsidiary list) as a special-case fetch since
it's a separate document within the 10-K filing index.
"""

from __future__ import annotations

import logging
import re
from typing import Any, TypedDict, cast

from do_uw.stages.acquire.rate_limiter import sec_get, sec_get_text

TYPE_CHECKING = False
if TYPE_CHECKING:
    from do_uw.cache.sqlite_cache import AnalysisCache

logger = logging.getLogger(__name__)

# SEC filing index URL pattern.
SEC_INDEX_URL = (
    "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/index.json"
)

# Default TTL for filing documents: 14 months.
_DEFAULT_DOC_TTL = 14 * 30 * 24 * 3600


class FilingDocument(TypedDict):
    """A downloaded SEC filing document."""

    accession: str
    filing_date: str
    form_type: str
    full_text: str


def fetch_filing_document(
    primary_doc_url: str,
    accession: str,
    form_type: str,
    filing_date: str,
    cache: AnalysisCache | None = None,
    ttl: int = _DEFAULT_DOC_TTL,
) -> FilingDocument | None:
    """Fetch a single filing's full primary document.

    Downloads the complete HTML/XML document from SEC EDGAR,
    strips HTML to plain text, and returns a FilingDocument.

    Args:
        primary_doc_url: Full URL to the filing's primary document.
        accession: SEC accession number (e.g., '0001234567-24-000123').
        form_type: SEC form type (e.g., '10-K', 'DEF 14A').
        filing_date: Filing date as ISO string.
        cache: Optional cache for storing/retrieving documents.
        ttl: Cache TTL in seconds.

    Returns:
        FilingDocument with full_text, or None on fetch failure.
    """
    if not primary_doc_url:
        return None

    cache_key = f"sec:filing_doc:{accession}"

    # Check cache first.
    if cache is not None:
        cached = cache.get(cache_key)
        if cached is not None and isinstance(cached, dict):
            logger.debug("Cache hit for filing document %s", accession)
            cached_dict = cast(dict[str, Any], cached)
            return FilingDocument(
                accession=str(cached_dict.get("accession", accession)),
                filing_date=str(cached_dict.get("filing_date", filing_date)),
                form_type=str(cached_dict.get("form_type", form_type)),
                full_text=str(cached_dict.get("full_text", "")),
            )

    logger.info("Fetching %s document %s", form_type, accession)
    try:
        html = sec_get_text(primary_doc_url)
    except Exception:
        logger.warning(
            "Failed to fetch %s document %s from %s",
            form_type, accession, primary_doc_url,
        )
        return None

    if not html:
        return None

    # Form 4 documents should be raw XML for parser; skip HTML stripping.
    if form_type == "4" and _looks_like_xml(html):
        text = html
    else:
        text = strip_html(html)
    doc = FilingDocument(
        accession=accession,
        filing_date=filing_date,
        form_type=form_type,
        full_text=text,
    )

    # Cache the document.
    if cache is not None:
        cache.set(
            cache_key,
            dict(doc),
            source=f"sec_edgar:filing_doc:{form_type}",
            ttl=ttl,
        )

    return doc


def fetch_all_filing_documents(
    filings_metadata: dict[str, Any],
    cik: str,
    cache: AnalysisCache | None = None,
) -> dict[str, list[FilingDocument]]:
    """Fetch full documents for all filing types in metadata.

    Iterates over all filing types, downloads each filing's primary
    document, and returns them grouped by form type.

    Args:
        filings_metadata: Dict keyed by filing type, each containing
            a list of filing metadata dicts with primary_doc_url.
        cik: Company CIK (unpadded).
        cache: Optional cache for storing/retrieving documents.

    Returns:
        Dict keyed by form type (e.g., '10-K', 'DEF 14A') with
        list of FilingDocument dicts for each.
    """
    from do_uw.stages.acquire.clients.sec_client import CACHE_TTLS

    result: dict[str, list[FilingDocument]] = {}
    total_fetched = 0
    form_types_processed = 0

    for form_type, filings_raw in filings_metadata.items():
        # Skip non-filing keys (company_facts, filing_texts, exhibit_21).
        if form_type in {
            "company_facts", "filing_texts", "exhibit_21", "filing_documents"
        }:
            continue
        if not isinstance(filings_raw, list):
            continue

        ttl = CACHE_TTLS.get(form_type, _DEFAULT_DOC_TTL)
        docs: list[FilingDocument] = []
        typed_filings = cast(list[object], filings_raw)

        for filing_obj in typed_filings:
            if not isinstance(filing_obj, dict):
                continue
            filing = cast(dict[str, Any], filing_obj)
            url = str(filing.get("primary_doc_url", ""))
            accession = str(filing.get("accession_number", ""))
            filing_date = str(filing.get("filing_date", ""))

            if not url or not accession:
                continue

            doc = fetch_filing_document(
                primary_doc_url=url,
                accession=accession,
                form_type=form_type,
                filing_date=filing_date,
                cache=cache,
                ttl=ttl,
            )
            if doc is not None:
                docs.append(doc)
                total_fetched += 1

        if docs:
            result[form_type] = docs
            form_types_processed += 1

    logger.info(
        "Fetched %d documents across %d filing types",
        total_fetched, form_types_processed,
    )
    return result


def fetch_exhibit_21(
    filings_metadata: dict[str, Any],
    cik: str,
    cache: AnalysisCache | None = None,
) -> str:
    """Fetch Exhibit 21 (subsidiaries list) from most recent 10-K.

    Uses the filing index JSON to find the Exhibit 21 document,
    then fetches its text content.

    Args:
        filings_metadata: Dict keyed by filing type with filing metadata.
        cik: Company CIK (unpadded).
        cache: Optional cache.

    Returns:
        Raw Exhibit 21 text, or empty string if not found.
    """
    latest = _get_latest_annual(filings_metadata)
    if latest is None:
        return ""

    accession = str(latest.get("accession_number", ""))
    if not accession:
        return ""

    # Check cache first.
    cache_key = f"sec:exhibit_21:{accession}"
    if cache is not None:
        cached = cache.get(cache_key)
        if cached is not None and isinstance(cached, str):
            logger.debug("Cache hit for Exhibit 21 %s", accession)
            return cached

    # Build filing index URL.
    acc_no_dashes = accession.replace("-", "")
    cik_raw = cik.lstrip("0") or "0"
    index_url = SEC_INDEX_URL.format(cik=cik_raw, accession=acc_no_dashes)

    logger.info("Fetching filing index for Exhibit 21: %s", index_url)
    try:
        index_data = sec_get(index_url)
    except Exception:
        logger.warning("Failed to fetch filing index for Exhibit 21")
        return ""

    # Search for Exhibit 21 in the filing directory.
    exhibit_url = _find_exhibit_21_url(index_data, cik_raw, acc_no_dashes)
    if not exhibit_url:
        logger.info("No Exhibit 21 found in filing index")
        return ""

    logger.info("Fetching Exhibit 21 text from %s", exhibit_url)
    try:
        html = sec_get_text(exhibit_url)
    except Exception:
        logger.warning("Failed to fetch Exhibit 21 text")
        return ""

    text = strip_html(html) if html else ""

    # Cache the result.
    if cache is not None and text:
        cache.set(
            cache_key,
            text,
            source="sec_edgar:exhibit_21",
            ttl=14 * 30 * 24 * 3600,
        )

    return text


def _looks_like_xml(content: str) -> bool:
    """Check if content appears to be XML (Form 4 ownership document)."""
    trimmed = content.strip()[:500]
    return (
        trimmed.startswith("<?xml")
        or "<ownershipDocument>" in trimmed
        or "<ownershipDocument " in trimmed
    )


def strip_html(html: str) -> str:
    """Remove HTML tags and normalize whitespace.

    Simple regex-based approach. Does not handle all edge cases
    but sufficient for SEC filing text extraction.
    """
    # Remove script and style blocks.
    text = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I
    )
    # Remove HTML tags.
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode common HTML entities.
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#160;", " ")
    text = text.replace("&quot;", '"')
    text = text.replace("&#8217;", "'")
    text = text.replace("&#8220;", '"')
    text = text.replace("&#8221;", '"')
    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _get_latest_annual(
    filings_metadata: dict[str, Any],
) -> dict[str, str] | None:
    """Get the most recent annual filing metadata dict."""
    from typing import cast

    for form_type in ("10-K", "20-F"):
        raw = filings_metadata.get(form_type)
        if raw is None or not isinstance(raw, list) or not raw:
            continue
        typed_list = cast(list[object], raw)
        first = typed_list[0]
        if isinstance(first, dict):
            return cast(dict[str, str], first)
    return None


def _find_exhibit_21_url(
    index_data: dict[str, Any],
    cik: str,
    acc_no_dashes: str,
) -> str:
    """Find Exhibit 21 document URL from filing index JSON.

    Args:
        index_data: Parsed filing index JSON.
        cik: CIK (unpadded).
        acc_no_dashes: Accession number without dashes.

    Returns:
        Full URL to Exhibit 21 document, or empty string.
    """
    directory = index_data.get("directory", {})
    items: list[dict[str, Any]] = directory.get("item", [])

    base_url = (
        f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc_no_dashes}"
    )

    for item in items:
        name = str(item.get("name", "")).lower()
        # Exhibit 21 filenames typically contain "ex21" or "exhibit21".
        if "ex21" in name or "exhibit21" in name or "ex-21" in name:
            return f"{base_url}/{item.get('name', '')}"

    return ""
