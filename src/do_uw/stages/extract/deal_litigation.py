"""Deal litigation extraction (SECT6-07).

Extracts M&A and deal-related litigation from 10-K Item 3 (Legal
Proceedings), 8-K filings, and web search results. Covers merger
objections, appraisal actions, disclosure-only settlements, Revlon
claims, and fiduciary duty challenges.

Time horizon: 5 years for deal litigation.

Usage:
    cases, report = extract_deal_litigation(state)
    state.extracted.litigation.deal_litigation = cases
"""

from __future__ import annotations

import logging
import re
from typing import Any, cast

from do_uw.models.common import Confidence
from do_uw.models.litigation_details import DealLitigation
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.filing_sections import SECTION_DEFS, extract_section
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_filing_documents,
    sourced_float,
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
_SOURCE_8K = "8-K filing"
_SOURCE_WEB = "web search"

# Expected fields for extraction report.
EXPECTED_FIELDS: list[str] = [
    "merger_objection",
    "appraisal",
    "disclosure_only",
    "revlon",
    "fiduciary",
    "settlement_amount",
]

# ---------------------------------------------------------------------------
# Deal litigation detection patterns
# ---------------------------------------------------------------------------

DEAL_PATTERNS: list[tuple[str, str]] = [
    (
        r"merger\s+(?:objection|challenge|litigation|lawsuit)",
        "merger_objection",
    ),
    (
        r"(?:appraisal|Section\s+262)\s+(?:action|proceeding|petition|demand)",
        "appraisal",
    ),
    (r"disclosure[\-\s]+only\s+settlement", "disclosure_only"),
    (r"[Rr]evlon\s+(?:duty|claim|standard|breach)", "revlon"),
    (
        r"fiduciary\s+duty\s+(?:challenge|claim|breach)"
        r".*(?:merger|acquisition|deal|transaction)",
        "fiduciary",
    ),
]

# Settlement amount extraction pattern.
_SETTLEMENT_PATTERN = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)", re.IGNORECASE
)

# Court detection patterns.
_COURT_PATTERNS: list[tuple[str, str]] = [
    (r"Delaware\s+(?:Court\s+of\s+)?Chancery", "Delaware Chancery"),
    (r"Court\s+of\s+Chancery", "Delaware Chancery"),
    (r"S\.D\.N\.Y\.", "S.D.N.Y."),
    (r"N\.D\.\s*Cal\.", "N.D. Cal."),
    (r"(?:United\s+States\s+)?District\s+Court", "U.S. District Court"),
]

# Max description length.
_MAX_DESC_CHARS = 500


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
    """Collect text + URL pairs from web search and blind spot results."""
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


def _extract_settlement_amount(context: str) -> float | None:
    """Extract settlement amount from context text."""
    match = _SETTLEMENT_PATTERN.search(context)
    if not match:
        return None

    amount_str = match.group(1).replace(",", "")
    multiplier_str = match.group(2).lower()

    try:
        amount = float(amount_str)
    except ValueError:
        return None

    if multiplier_str == "billion":
        amount *= 1_000_000_000.0
    elif multiplier_str == "million":
        amount *= 1_000_000.0

    return amount


def _detect_court(context: str) -> str | None:
    """Detect court name from text context."""
    for pattern, court_name in _COURT_PATTERNS:
        if re.search(pattern, context, re.IGNORECASE):
            return court_name
    return None


def _extract_deal_name(context: str) -> str | None:
    """Try to extract deal name from context.

    Looks for patterns like "the merger with X" or "acquisition of X".
    """
    deal_match = re.search(
        r"(?:merger|acquisition|deal|transaction)\s+"
        r"(?:with|of|by|involving)\s+([A-Z][A-Za-z\s&]+?)(?:\s*[,.]|\s+(?:for|in|on))",
        context,
    )
    if deal_match:
        name = deal_match.group(1).strip()
        if len(name) > 100:
            name = name[:97] + "..."
        return name
    return None


def _scan_text_for_deal_litigation(
    text: str,
    source: str,
    confidence: Confidence,
) -> list[DealLitigation]:
    """Scan text for deal litigation patterns, return cases."""
    cases: list[DealLitigation] = []
    if not text:
        return cases

    for pattern, lit_type in DEAL_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            settlement = _extract_settlement_amount(context)
            court = _detect_court(context)
            deal_name = _extract_deal_name(context)

            case = DealLitigation(
                litigation_type=sourced_str(lit_type, source, confidence),
                description=sourced_str(context, source, confidence),
                status=sourced_str("disclosed", source, confidence),
            )

            if deal_name:
                case.deal_name = sourced_str(
                    deal_name, source, confidence
                )
            if court:
                case.court = sourced_str(court, source, confidence)
            if settlement is not None:
                case.settlement_amount = sourced_float(
                    settlement, source, confidence
                )

            cases.append(case)

    return cases


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_deal_litigation(
    state: AnalysisState,
) -> tuple[list[DealLitigation], ExtractionReport]:
    """Extract M&A and deal-related litigation.

    Searches 10-K Item 3, 8-K filings, and web search results for
    deal litigation patterns. Creates typed DealLitigation records
    with litigation type, court, and settlement amounts.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (list of DealLitigation, ExtractionReport).
    """
    all_cases: list[DealLitigation] = []
    found_fields: list[str] = []
    warnings: list[str] = []
    source_filing = "10-K Item 3 + 8-K + web search"

    # 1. Item 3 (Legal Proceedings).
    item3_text = _get_item3_text(state)
    if item3_text:
        cases = _scan_text_for_deal_litigation(
            item3_text, _SOURCE_10K, Confidence.HIGH
        )
        all_cases.extend(cases)
    else:
        warnings.append("Item 3 text not available")

    # 2. 8-K filings.
    for filing_text in _get_8k_texts(state):
        cases = _scan_text_for_deal_litigation(
            filing_text, _SOURCE_8K, Confidence.MEDIUM
        )
        all_cases.extend(cases)

    # 3. Web search results.
    web_texts = _get_web_search_texts(state)
    for text, _url in web_texts:
        cases = _scan_text_for_deal_litigation(
            text, _SOURCE_WEB, Confidence.LOW
        )
        all_cases.extend(cases)

    # 4. Deduplicate by type + description prefix.
    seen: set[str] = set()
    deduped: list[DealLitigation] = []
    for case in all_cases:
        lit_type = (
            case.litigation_type.value if case.litigation_type else "unknown"
        )
        desc_prefix = (
            case.description.value[:100] if case.description else ""
        )
        key = f"{lit_type}:{desc_prefix}"
        if key not in seen:
            seen.add(key)
            deduped.append(case)

    # 5. Track found litigation types.
    for case in deduped:
        if case.litigation_type:
            field_name = case.litigation_type.value
            if field_name not in found_fields:
                found_fields.append(field_name)
        if case.settlement_amount is not None:
            if "settlement_amount" not in found_fields:
                found_fields.append("settlement_amount")

    report = create_report(
        extractor_name="deal_litigation",
        expected=EXPECTED_FIELDS,
        found=found_fields,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return deduped, report
