"""Regulatory proceedings extraction (SECT6-06).

Extracts non-SEC regulatory proceedings from 10-K Item 3 (Legal
Proceedings), Item 1A (Risk Factors), 8-K filings, and web search
results. Covers DOJ, FTC, FDA, EPA, CFPB, OCC, OSHA, EEOC, state
AG, FCPA, NHTSA, and FERC enforcement actions.

Time horizon: 5 years for regulatory proceedings.

Agency patterns, classification helpers, and text scanning logic
are in regulatory_extract_patterns.py (split for 500-line compliance).

Usage:
    proceedings, report = extract_regulatory_proceedings(state)
    state.extracted.litigation.regulatory_proceedings_detail = proceedings
"""

from __future__ import annotations

import logging
from typing import Any, cast

from do_uw.models.common import Confidence
from do_uw.models.litigation_details import RegulatoryProceeding
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.filing_sections import SECTION_DEFS, extract_section
from do_uw.stages.extract.regulatory_extract_patterns import (
    _SOURCE_8K,
    _SOURCE_10K,
    _SOURCE_10K_RF,
    _SOURCE_WEB,
    EXPECTED_FIELDS,
    _agency_to_report_field,
    _scan_text_for_agencies,
)
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_filing_documents,
    get_filing_texts,
    get_filings,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------


def _get_item3_text(state: AnalysisState) -> str:
    """Get Item 3 (Legal Proceedings) text.

    Uses pre-parsed filing_texts from ACQUIRE stage first, falling
    back to section extraction from the full 10-K document.
    """
    # Prefer pre-parsed section text.
    filings = get_filings(state)
    ft = get_filing_texts(filings)
    text = ft.get("item3", "") or ft.get("10-K_item3", "")
    if text:
        return str(text)
    # Fallback: extract from full 10-K.
    full_text = get_filing_document_text(state, "10-K")
    if not full_text:
        return ""
    for name, start_patterns, end_patterns in SECTION_DEFS:
        if name == "item3":
            return extract_section(full_text, start_patterns, end_patterns)
    return ""


def _get_item1a_text(state: AnalysisState) -> str:
    """Get Item 1A (Risk Factors) text.

    Uses pre-parsed filing_texts from ACQUIRE stage first, falling
    back to section extraction from the full 10-K document.
    """
    filings = get_filings(state)
    ft = get_filing_texts(filings)
    text = ft.get("item1a", "") or ft.get("10-K_item1a", "")
    if text:
        return str(text)
    full_text = get_filing_document_text(state, "10-K")
    if not full_text:
        return ""
    for name, start_patterns, end_patterns in SECTION_DEFS:
        if name == "item1a":
            return extract_section(full_text, start_patterns, end_patterns)
    return ""


def _get_8k_texts(state: AnalysisState) -> list[str]:
    """Get text content from 8-K filings."""
    docs = get_filing_documents(state)
    filings_8k = docs.get("8-K", [])
    texts: list[str] = []
    for filing in filings_8k:
        text = filing.get("full_text", "")
        if text:
            texts.append(str(text))
    return texts


def _get_web_search_texts(state: AnalysisState) -> list[tuple[str, str]]:
    """Collect text + URL pairs from web search and blind spot results.

    Returns list of (combined_text, url) tuples.
    """
    if state.acquired_data is None:
        return []

    results: list[tuple[str, str]] = []

    for source_dict in [
        state.acquired_data.web_search_results,
        state.acquired_data.blind_spot_results,
    ]:
        for _key, value in source_dict.items():
            _collect_search_items(value, results)

    return results


def _collect_search_items(
    value: Any,
    results: list[tuple[str, str]],
) -> None:
    """Recursively collect (text, url) pairs from search result values.

    Handles both flat lists and nested dicts (e.g. blind_spot_results
    has structure {"pre_structured": {"litigation": [...], ...}, ...}).
    """
    if isinstance(value, dict):
        typed_dict = cast(dict[str, Any], value)
        for _sub_key, sub_val in typed_dict.items():
            _collect_search_items(sub_val, results)
    elif isinstance(value, list):
        typed_list = cast(list[Any], value)
        for item in typed_list:
            if isinstance(item, dict):
                item_dict = cast(dict[str, Any], item)
                title = str(item_dict.get("title", ""))
                desc = str(item_dict.get("description", ""))
                snippet = str(item_dict.get("snippet", ""))
                url = str(item_dict.get("url", ""))
                combined = f"{title} {desc} {snippet}"
                if combined.strip():
                    results.append((combined, url))
            elif isinstance(item, str):
                results.append((item, ""))
    elif isinstance(value, str):
        results.append((value, ""))


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_regulatory_proceedings(
    state: AnalysisState,
) -> tuple[list[RegulatoryProceeding], ExtractionReport]:
    """Extract regulatory proceedings from filings and web search.

    Searches 10-K Item 3, Item 1A, 8-K filings, and web search
    results for regulatory agency proceedings. Creates typed
    RegulatoryProceeding records with agency classification,
    proceeding type, and penalty amounts.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (list of RegulatoryProceeding, ExtractionReport).
    """
    all_proceedings: list[RegulatoryProceeding] = []
    found_fields: list[str] = []
    warnings: list[str] = []
    source_filing = "10-K Item 3 + Item 1A + 8-K + web search"

    # 1. Item 3 (Legal Proceedings).
    item3_text = _get_item3_text(state)
    if item3_text:
        procs = _scan_text_for_agencies(
            item3_text, _SOURCE_10K, Confidence.HIGH
        )
        all_proceedings.extend(procs)
    else:
        warnings.append("Item 3 text not available")

    # 2. Item 1A (Risk Factors) for "under investigation" language.
    item1a_text = _get_item1a_text(state)
    if item1a_text:
        procs = _scan_text_for_agencies(
            item1a_text, _SOURCE_10K_RF, Confidence.MEDIUM
        )
        all_proceedings.extend(procs)

    # 3. 8-K filings for regulatory event disclosures.
    for filing_text in _get_8k_texts(state):
        procs = _scan_text_for_agencies(
            filing_text, _SOURCE_8K, Confidence.MEDIUM
        )
        all_proceedings.extend(procs)

    # 4. Web search and blind spot results.
    web_texts = _get_web_search_texts(state)
    for text, _url in web_texts:
        procs = _scan_text_for_agencies(text, _SOURCE_WEB, Confidence.LOW)
        all_proceedings.extend(procs)

    # 5. Deduplicate by agency (keep first occurrence per agency).
    seen_agencies: set[str] = set()
    deduped: list[RegulatoryProceeding] = []
    for proc in all_proceedings:
        agency_val = proc.agency.value if proc.agency else "unknown"
        # Use agency + first 100 chars of description as dedup key.
        desc_val = (
            proc.description.value[:100] if proc.description else ""
        )
        dedup_key = f"{agency_val}:{desc_val}"
        if dedup_key not in seen_agencies:
            seen_agencies.add(dedup_key)
            deduped.append(proc)

    # 6. Track found agency types.
    for proc in deduped:
        if proc.agency:
            field_name = _agency_to_report_field(proc.agency.value)
            if field_name not in found_fields:
                found_fields.append(field_name)

    report = create_report(
        extractor_name="regulatory_proceedings",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return deduped, report
