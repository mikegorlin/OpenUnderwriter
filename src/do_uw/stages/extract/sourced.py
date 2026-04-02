"""Shared SourcedValue factory functions for extraction modules.

Provides typed constructors for SourcedValue wrappers used across
company_profile.py and profile_helpers.py. Avoids duplicating these
helper functions in multiple extraction files.
"""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.state import AnalysisState

# Zero-width spaces → newline (paragraph separators in SEC filings).
_ZWSP_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]+")
# Thin/figure/punctuation spaces → regular space.
_THIN_SPACE_RE = re.compile(r"[\u2009\u2007\u2008\u205f\u00a0]+")
# Collapse runs of spaces/tabs into a single space.
_MULTI_SPACE_RE = re.compile(r"[ \t]+")
# Collapse 3+ newlines into double newline.
_MULTI_NL_RE = re.compile(r"\n{3,}")


def now() -> datetime:
    """Current UTC datetime."""
    return datetime.now(tz=UTC)


def sourced_str(
    value: str, source: str, confidence: Confidence = Confidence.HIGH
) -> SourcedValue[str]:
    """Create a SourcedValue[str] with current timestamp."""
    return SourcedValue[str](
        value=value, source=source, confidence=confidence, as_of=now()
    )


def sourced_int(
    value: int, source: str, confidence: Confidence = Confidence.HIGH
) -> SourcedValue[int]:
    """Create a SourcedValue[int] with current timestamp."""
    return SourcedValue[int](
        value=value, source=source, confidence=confidence, as_of=now()
    )


def sourced_float(
    value: float, source: str, confidence: Confidence = Confidence.HIGH
) -> SourcedValue[float]:
    """Create a SourcedValue[float] with current timestamp."""
    return SourcedValue[float](
        value=value, source=source, confidence=confidence, as_of=now()
    )


def sourced_dict(
    value: dict[str, str | float],
    source: str,
    confidence: Confidence = Confidence.HIGH,
) -> SourcedValue[dict[str, str | float]]:
    """Create a SourcedValue wrapping a dict[str, str | float]."""
    return SourcedValue[dict[str, str | float]](
        value=value, source=source, confidence=confidence, as_of=now()
    )


def sourced_str_dict(
    value: dict[str, str],
    source: str,
    confidence: Confidence = Confidence.LOW,
) -> SourcedValue[dict[str, str]]:
    """Create a SourcedValue wrapping a dict[str, str]."""
    return SourcedValue[dict[str, str]](
        value=value, source=source, confidence=confidence, as_of=now()
    )


def get_filings(state: AnalysisState) -> dict[str, Any]:
    """Safely get filings dict from acquired data."""
    if state.acquired_data is None:
        return {}
    return dict(state.acquired_data.filings)


def get_market_data(state: AnalysisState) -> dict[str, Any]:
    """Safely get market_data dict from acquired data."""
    if state.acquired_data is None:
        return {}
    return dict(state.acquired_data.market_data)


def get_filing_texts(filings: dict[str, Any]) -> dict[str, Any]:
    """Get filing_texts dict from filings, safely cast."""
    from typing import cast

    raw = filings.get("filing_texts")
    if raw is not None and isinstance(raw, dict):
        return cast(dict[str, Any], raw)
    return {}


def ensure_filing_texts(state: AnalysisState) -> None:
    """Build filing_texts from filing_documents if not already present.

    When ACQUIRE stores full document text in filing_documents but
    doesn't split it into section-keyed filing_texts, this function
    bridges the gap by running extract_10k_sections() on the full text
    and storing the result in state.acquired_data.filings["filing_texts"].

    Called once at the start of EXTRACT stage so all downstream extractors
    get section-keyed text automatically.
    """
    import logging

    from do_uw.stages.extract.filing_sections import extract_10k_sections

    log = logging.getLogger(__name__)

    if state.acquired_data is None:
        return

    # Already has filing_texts? Nothing to do.
    existing = state.acquired_data.filings.get("filing_texts")
    if existing and isinstance(existing, dict) and len(existing) > 0:
        return

    texts: dict[str, str] = {}

    # Build from filing_documents (full_text per filing type)
    docs = state.acquired_data.filing_documents or {}

    # 10-K: extract sections from full text
    tenk_docs = docs.get("10-K", [])
    if isinstance(tenk_docs, list):
        for doc in tenk_docs:
            if isinstance(doc, dict):
                full = doc.get("full_text", "")
                if full and len(full) > 500:
                    sections = extract_10k_sections(full)
                    texts.update(sections)
                    log.info(
                        "Built %d section texts from 10-K full_text (%d chars)",
                        len(sections), len(full),
                    )
                    break  # Use first (most recent) 10-K

    # DEF 14A: store as proxy text
    proxy_docs = docs.get("DEF 14A", [])
    if isinstance(proxy_docs, list):
        for doc in proxy_docs:
            if isinstance(doc, dict):
                full = doc.get("full_text", "")
                if full and len(full) > 500:
                    texts["proxy_compensation"] = full[:50000]
                    texts["proxy_governance"] = full[:50000]
                    log.info("Built proxy texts from DEF 14A (%d chars)", len(full))
                    break

    # 8-K: store for leadership/event extraction
    eightk_docs = docs.get("8-K", [])
    if isinstance(eightk_docs, list):
        for i, doc in enumerate(eightk_docs[:5]):
            if isinstance(doc, dict):
                full = doc.get("full_text", "")
                if full and len(full) > 200:
                    texts[f"8-K_{i}"] = full[:20000]

    if texts:
        state.acquired_data.filings["filing_texts"] = texts
        log.info("Populated filing_texts with %d entries", len(texts))


def get_info_dict(state: AnalysisState) -> dict[str, Any]:
    """Get the yfinance info dict, safely cast."""
    from typing import cast

    market = get_market_data(state)
    raw = market.get("info")
    if raw is not None and isinstance(raw, dict):
        return cast(dict[str, Any], raw)
    return {}


def rehydrate_company_facts(state: AnalysisState) -> None:
    """Re-load company_facts from SQLite cache if missing from state.

    The pipeline strips large blobs (company_facts ~4MB) from state.json
    to keep file sizes manageable. When resuming from EXTRACT, this data
    must be re-hydrated from the SQLite cache where ACQUIRE stored it.

    Called once at the start of EXTRACT stage alongside ensure_filing_texts().
    """
    import logging

    log = logging.getLogger(__name__)

    if state.acquired_data is None:
        return

    # Already present? Nothing to do.
    existing = state.acquired_data.filings.get("company_facts")
    if existing and isinstance(existing, dict):
        return

    # Get CIK from company identity.
    cik: str | None = None
    if state.company and state.company.identity.cik:
        cik = state.company.identity.cik.value
    if not cik:
        log.debug("No CIK available; cannot rehydrate company_facts")
        return

    # Pad CIK to 10 digits for cache key.
    padded_cik = cik.zfill(10)
    cache_key = f"sec:company_facts:{padded_cik}"

    try:
        from pathlib import Path

        from do_uw.cache.sqlite_cache import AnalysisCache

        cache = AnalysisCache(Path(".cache/analysis.db"))
        cached = cache.get(cache_key)
        if cached is not None and isinstance(cached, dict):
            state.acquired_data.filings["company_facts"] = cached
            log.info(
                "Rehydrated company_facts from cache (%d taxonomies)",
                len(cached.get("facts", {})),
            )
        else:
            log.info("No cached company_facts for CIK %s", padded_cik)
    except Exception:
        log.warning(
            "Failed to rehydrate company_facts from cache",
            exc_info=True,
        )


def get_company_facts(state: AnalysisState) -> dict[str, Any]:
    """Get company facts XBRL data from filings."""
    from typing import cast

    filings = get_filings(state)
    raw = filings.get("company_facts")
    if raw is not None and isinstance(raw, dict):
        return cast(dict[str, Any], raw)
    return {}


def get_filing_documents(
    state: AnalysisState,
) -> dict[str, list[dict[str, Any]]]:
    """Get full filing documents from acquired data.

    Returns the filing_documents dict keyed by form type, each
    containing a list of FilingDocument dicts with accession,
    filing_date, form_type, and full_text fields.
    """
    from typing import cast

    if state.acquired_data is None:
        return {}
    try:
        raw = state.acquired_data.filing_documents
    except AttributeError:
        raw = None
    if raw:
        return cast(dict[str, list[dict[str, Any]]], raw)
    # Fallback: check filings dict (in case stored there instead).
    filings = get_filings(state)
    fd = filings.get("filing_documents")
    if fd is not None and isinstance(fd, dict):
        return cast(dict[str, list[dict[str, Any]]], fd)
    return {}


def normalize_filing_text(raw: str) -> str:
    """Decode HTML entities and normalize whitespace in filing text.

    SEC EDGAR filing text frequently contains HTML character entities
    (&#8203; zero-width space, &#8201; thin space, &#8226; bullet, etc.)
    and may have zero newlines. This function:
    1. Decodes HTML entities to Unicode.
    2. Converts zero-width / thin spaces to paragraph breaks.
    3. Collapses excessive whitespace.
    """
    if not raw:
        return raw
    # Decode HTML entities (&#8203; → \u200b, etc.).
    text = html.unescape(raw)
    # Convert zero-width spaces to newlines (paragraph separators).
    text = _ZWSP_RE.sub("\n", text)
    # Convert thin/figure/non-breaking spaces to regular spaces.
    text = _THIN_SPACE_RE.sub(" ", text)
    # Collapse multiple spaces/tabs on a line.
    text = _MULTI_SPACE_RE.sub(" ", text)
    # Collapse 3+ newlines into double newline.
    text = _MULTI_NL_RE.sub("\n\n", text)
    return text.strip()


def get_filing_document_text(
    state: AnalysisState,
    form_type: str,
    index: int = 0,
) -> str:
    """Get full text of the Nth filing of a given form type.

    Convenience function for extractors that need the complete
    text of a specific filing document. Applies HTML entity
    decoding and whitespace normalization.

    Args:
        state: Analysis state with acquired data.
        form_type: SEC form type (e.g., 'DEF 14A', '8-K').
        index: Zero-based index into the list of filings
            for that type (0 = most recent).

    Returns:
        Full plain-text content, or empty string if not available.
    """
    docs = get_filing_documents(state)
    filings = docs.get(form_type, [])
    if index < len(filings):
        raw = str(filings[index].get("full_text", ""))
        return normalize_filing_text(raw)
    return ""
