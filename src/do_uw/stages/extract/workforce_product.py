"""Workforce, product, and environmental claims extraction (SECT6-08).

Extracts employment, EEOC, whistleblower, WARN, product recall,
mass tort, environmental, and cybersecurity matters from 10-K
Item 3, Item 1A, 8-K filings, and web search results.

Time horizon: 3 years for workforce/product/environmental matters.

Returns a 3-tuple: (WorkforceProductEnvironmental, list of
WhistleblowerIndicator, ExtractionReport). The sub-orchestrator
unpacks this to populate both the WPE model and the separate
whistleblower_indicators list on LitigationLandscape.

Usage:
    wpe, whistleblowers, report = extract_workforce_product_environmental(state)
    state.extracted.litigation.workforce_product_environmental = wpe
    state.extracted.litigation.whistleblower_indicators.extend(whistleblowers)
"""

from __future__ import annotations

import logging
import re
from typing import Any, cast

from do_uw.models.common import Confidence
from do_uw.models.litigation_details import (
    WhistleblowerIndicator,
    WorkforceProductEnvironmental,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.filing_sections import SECTION_DEFS, extract_section
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Source attribution.
_SOURCE_10K = "10-K Legal Proceedings (Item 3)"
_SOURCE_10K_RF = "10-K Risk Factors (Item 1A)"
_SOURCE_8K = "8-K filing"
_SOURCE_WEB = "web search"

# Expected fields for extraction report.
EXPECTED_FIELDS: list[str] = [
    "employment_matters",
    "eeoc_charges",
    "whistleblower_complaints",
    "warn_notices",
    "product_recalls",
    "mass_tort_exposure",
    "environmental_actions",
    "cybersecurity_incidents",
]

# ---------------------------------------------------------------------------
# Category detection patterns
# ---------------------------------------------------------------------------

CATEGORY_PATTERNS: dict[str, list[tuple[str, str]]] = {
    "employment_matters": [
        (
            r"employment\s+(?:litigation|lawsuit|claim|action)",
            "employment",
        ),
        (
            r"wage\s+(?:and\s+hour|theft)|(?:Fair\s+Labor\s+Standards|FLSA)",
            "wage_hour",
        ),
        (
            r"discrimination\s+(?:suit|claim|action|complaint)",
            "discrimination",
        ),
    ],
    "eeoc_charges": [
        (
            r"(?:EEOC|Equal\s+Employment)\s+(?:charge|complaint|investigation)",
            "eeoc",
        ),
    ],
    "whistleblower_complaints": [
        (
            r"whistleblower\s+(?:complaint|claim|suit|action|award)",
            "whistleblower",
        ),
        (r"qui\s+tam|False\s+Claims\s+Act", "qui_tam"),
        (
            r"SEC\s+whistleblower\s+(?:award|bounty|program)",
            "sec_whistleblower",
        ),
        (
            r"Dodd-Frank\s+(?:whistleblower|retaliation)",
            "dodd_frank_whistleblower",
        ),
    ],
    "warn_notices": [
        (r"WARN\s+(?:Act|notice)|Worker\s+Adjustment", "warn"),
        (r"mass\s+layoff|plant\s+clos(?:ure|ing)", "mass_layoff"),
    ],
    "product_recalls": [
        (r"product\s+recall|recall\s+(?:of|affecting)", "recall"),
        (r"CPSC|Consumer\s+Product\s+Safety", "cpsc"),
    ],
    "mass_tort_exposure": [
        (r"mass\s+tort|multi-?district\s+litigation|MDL", "mass_tort"),
        (
            r"personal\s+injury\s+(?:claim|suit|action)",
            "personal_injury",
        ),
    ],
    "environmental_actions": [
        (
            r"(?:EPA|environmental)\s+(?:enforcement|remediation|cleanup|violation)",
            "environmental",
        ),
        (
            r"Superfund|CERCLA|Clean\s+(?:Air|Water)\s+Act",
            "superfund",
        ),
        (
            r"climate[\-\s]related\s+(?:litigation|lawsuit|claim)",
            "climate",
        ),
    ],
    "cybersecurity_incidents": [
        (
            r"data\s+breach|cybersecurity\s+incident|unauthorized\s+access",
            "data_breach",
        ),
        (
            r"(?:GDPR|CCPA|privacy)\s+(?:violation|penalty|fine)",
            "privacy",
        ),
        (r"ransomware|cyber[\-\s]?attack", "cyber_attack"),
    ],
}

# Max description length.
_MAX_DESC_CHARS = 500

# Whistleblower sub-types that map to WhistleblowerIndicator.
_WHISTLEBLOWER_TYPES: dict[str, str] = {
    "whistleblower": "internal",
    "qui_tam": "qui_tam",
    "sec_whistleblower": "sec_whistleblower",
    "dodd_frank_whistleblower": "sec_whistleblower",
}


# ---------------------------------------------------------------------------
# Text extraction helpers
# ---------------------------------------------------------------------------


def _get_item3_text(state: AnalysisState) -> str:
    """Extract Item 3 (Legal Proceedings) from 10-K filing text."""
    full_text = get_filing_document_text(state, "10-K")
    if not full_text:
        return ""
    for name, start_patterns, end_patterns in SECTION_DEFS:
        if name == "item3":
            return extract_section(full_text, start_patterns, end_patterns)
    return ""


def _get_item1a_text(state: AnalysisState) -> str:
    """Extract Item 1A (Risk Factors) from 10-K filing text."""
    full_text = get_filing_document_text(state, "10-K")
    if not full_text:
        return ""
    for name, start_patterns, end_patterns in SECTION_DEFS:
        if name == "item1a":
            return extract_section(full_text, start_patterns, end_patterns)
    return ""


def _get_8k_texts(state: AnalysisState) -> list[str]:
    """Get text content from 8-K filings."""
    if state.acquired_data is None:
        return []
    docs = state.acquired_data.filing_documents
    filings_8k = docs.get("8-K", [])
    texts: list[str] = []
    for filing in filings_8k:
        text = filing.get("full_text", "")
        if text:
            texts.append(str(text))
    return texts


def _get_web_search_texts(state: AnalysisState) -> list[tuple[str, str]]:
    """Collect text + URL pairs from web search and blind spot results."""
    if state.acquired_data is None:
        return []

    results: list[tuple[str, str]] = []
    for source_dict in [
        state.acquired_data.web_search_results,
        state.acquired_data.blind_spot_results,
    ]:
        for _key, value in source_dict.items():
            if isinstance(value, list):
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

    return results


# ---------------------------------------------------------------------------
# Extraction logic
# ---------------------------------------------------------------------------


def _extract_context(text: str, match_start: int, match_end: int) -> str:
    """Extract sentence context around a regex match, max 500 chars."""
    sent_start = max(0, match_start - 200)
    for i in range(match_start - 1, sent_start, -1):
        if text[i] in ".!?\n" and i < match_start - 1:
            sent_start = i + 1
            break

    sent_end = min(len(text), match_end + 300)
    for i in range(match_end, sent_end):
        if text[i] in ".!?\n":
            sent_end = i + 1
            break

    context = text[sent_start:sent_end].strip()
    if len(context) > _MAX_DESC_CHARS:
        context = context[:_MAX_DESC_CHARS - 3] + "..."
    return context


def _scan_text_for_categories(
    text: str,
    source: str,
    confidence: Confidence,
) -> dict[str, list[tuple[str, str]]]:
    """Scan text for all category patterns.

    Returns dict of category_name -> list of (sub_type, context).
    """
    results: dict[str, list[tuple[str, str]]] = {}
    if not text:
        return results

    for category, patterns in CATEGORY_PATTERNS.items():
        matches: list[tuple[str, str]] = []
        for pattern, sub_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                context = _extract_context(
                    text, match.start(), match.end()
                )
                matches.append((sub_type, context))
        if matches:
            results[category] = matches

    return results


def _create_whistleblower_indicator(
    sub_type: str,
    context: str,
    source: str,
    confidence: Confidence,
) -> WhistleblowerIndicator:
    """Create a WhistleblowerIndicator from a whistleblower match."""
    indicator_type = _WHISTLEBLOWER_TYPES.get(sub_type, "internal")

    return WhistleblowerIndicator(
        indicator_type=sourced_str(indicator_type, source, confidence),
        description=sourced_str(context, source, confidence),
        significance=sourced_str("MEDIUM", source, confidence),
        source=sourced_str(source, source, confidence),
    )


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_workforce_product_environmental(
    state: AnalysisState,
) -> tuple[
    WorkforceProductEnvironmental,
    list[WhistleblowerIndicator],
    ExtractionReport,
]:
    """Extract workforce, product, and environmental claims.

    Searches 10-K Item 3, Item 1A, 8-K filings, and web search
    results for 8 claim categories. Also extracts whistleblower
    indicators as a separate return value.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        3-tuple of (WorkforceProductEnvironmental,
        list of WhistleblowerIndicator, ExtractionReport).
    """
    wpe = WorkforceProductEnvironmental()
    whistleblowers: list[WhistleblowerIndicator] = []
    found_fields: list[str] = []
    warnings: list[str] = []
    source_filing = "10-K Item 3 + Item 1A + 8-K + web search"

    # Collect all text sources with their confidence levels.
    text_sources: list[tuple[str, str, Confidence]] = []

    # 1. Item 3 (Legal Proceedings).
    item3_text = _get_item3_text(state)
    if item3_text:
        text_sources.append((item3_text, _SOURCE_10K, Confidence.HIGH))
    else:
        warnings.append("Item 3 text not available")

    # 2. Item 1A (Risk Factors).
    item1a_text = _get_item1a_text(state)
    if item1a_text:
        text_sources.append(
            (item1a_text, _SOURCE_10K_RF, Confidence.MEDIUM)
        )

    # 3. 8-K filings.
    for filing_text in _get_8k_texts(state):
        text_sources.append((filing_text, _SOURCE_8K, Confidence.MEDIUM))

    # 4. Web search results.
    web_texts = _get_web_search_texts(state)
    for text, _url in web_texts:
        text_sources.append((text, _SOURCE_WEB, Confidence.LOW))

    # Scan all text sources.
    all_findings: dict[str, list[tuple[str, str, str, Confidence]]] = {}
    for text, source, confidence in text_sources:
        category_matches = _scan_text_for_categories(
            text, source, confidence
        )
        for category, matches in category_matches.items():
            if category not in all_findings:
                all_findings[category] = []
            for sub_type, context in matches:
                all_findings[category].append(
                    (sub_type, context, source, confidence)
                )

    # Populate the WPE model and track found fields.
    _populate_wpe(wpe, all_findings, found_fields)

    # Extract whistleblower indicators from whistleblower findings.
    if "whistleblower_complaints" in all_findings:
        for sub_type, context, source, confidence in all_findings[
            "whistleblower_complaints"
        ]:
            indicator = _create_whistleblower_indicator(
                sub_type, context, source, confidence
            )
            whistleblowers.append(indicator)

    report = create_report(
        extractor_name="workforce_product_environmental",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return wpe, whistleblowers, report


def _populate_wpe(
    wpe: WorkforceProductEnvironmental,
    findings: dict[str, list[tuple[str, str, str, Confidence]]],
    found_fields: list[str],
) -> None:
    """Populate WorkforceProductEnvironmental from findings.

    Deduplicates by (sub_type, context_prefix) within each category.
    """
    for category in EXPECTED_FIELDS:
        if category not in findings:
            continue

        seen: set[str] = set()
        field_list = getattr(wpe, category)

        for sub_type, context, source, confidence in findings[category]:
            dedup_key = f"{sub_type}:{context[:100]}"
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            sv = sourced_str(
                f"[{sub_type}] {context}", source, confidence
            )
            field_list.append(sv)

        if field_list:
            found_fields.append(category)
