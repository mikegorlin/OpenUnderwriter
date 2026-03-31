"""LLM-powered SCA extraction from web search results.

Web search results contain rich litigation data (case names, courts,
filing dates, settlement amounts) but in unstructured snippet form that
regex patterns can't reliably parse. This module sends web snippets to
an LLM for structured extraction using the same ExtractedLegalProceeding
schema used for 10-K Item 3 extraction.

Called from extract_litigation.py after regex-based SCA extraction.
Results are LOW confidence and go through the same dedup + quality
filters as all other SCA sources.
"""

from __future__ import annotations

import logging
import os
from typing import Any, cast

from pydantic import BaseModel, Field

from do_uw.models.common import Confidence
from do_uw.models.litigation import CaseDetail
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.llm.schemas.common import ExtractedLegalProceeding

logger = logging.getLogger(__name__)

# Maximum snippets to send in one LLM call (cost/token control)
_MAX_SNIPPETS = 40

# Minimum snippet length to bother sending
_MIN_SNIPPET_LEN = 30

# Keywords that indicate a web result is litigation-related
_LITIGATION_KEYWORDS = {
    "class action",
    "securities",
    "lawsuit",
    "litigation",
    "settlement",
    "complaint",
    "fraud",
    "enforcement",
    "derivative",
    "plaintiff",
    "defendant",
    "court",
    "filed",
    "dismissed",
    "ruling",
    "judge",
    "docket",
    "10b-5",
    "section 11",
    "section 14",
    "sec investigation",
    "shareholder",
    "investor",
    "claim",
}


class WebLitigationExtraction(BaseModel):
    """LLM response schema for web search litigation extraction."""

    cases: list[ExtractedLegalProceeding] = Field(
        default_factory=list,
        description=(
            "Securities class action and other litigation cases found "
            "in the web search results. Only extract cases with specific "
            "details (case name, court, dates, parties). Do NOT invent "
            "cases or infer from generic mentions."
        ),
    )


_SYSTEM_PROMPT = """\
You are a D&O insurance underwriting analyst extracting securities litigation \
data from web search results.

TASK: Extract ALL securities class action (SCA) lawsuits and other significant \
litigation cases mentioned in these web search snippets — BOTH active AND \
historical (settled, dismissed). An SCA is a lawsuit filed on behalf of \
shareholders alleging securities fraud (10b-5, Section 11, Section 14a).

CRITICAL FOR UNDERWRITING: Historical cases are as important as active ones. \
For settled/dismissed cases, extract:
- Settlement amount (in millions USD)
- Outcome: SETTLED with amount, or DISMISSED (motion to dismiss granted)
- Class period start and end dates
- Specific allegations (what was the theory — earnings miss? restatement?)
- Lead plaintiffs law firm if mentioned

RULES:
1. Only extract cases with SPECIFIC details — a real case name, court, \
date, or named parties. Do NOT invent cases from vague mentions.
2. Include the case name exactly as stated (e.g., "Cai v. Visa Inc." or \
"In re Visa Inc. Securities Litigation").
3. For status, use: ACTIVE, SETTLED, DISMISSED, or APPEAL.
4. For settlement_amount, use millions (e.g., 176.0 means $176M).
5. For legal_theories, use standard labels: 10b-5, Section 11, Section 14(a), \
ERISA, ANTITRUST, FCPA, DERIVATIVE_DUTY, PRODUCT_LIABILITY, EMPLOYMENT, \
CYBER_PRIVACY, ENVIRONMENTAL, WHISTLEBLOWER.
6. Distinguish between SECURITIES class actions (10b-5, Section 11, Section 14a) \
and NON-SECURITIES litigation (antitrust, merchant, patent, consumer).
7. If a snippet mentions a settlement, ALWAYS extract the settlement_amount.
8. Do NOT extract the same case twice — deduplicate by case name.
9. If the snippet is too vague to identify a specific case, skip it.
10. Extract class_period_start and class_period_end when mentioned.
11. For DISMISSED cases, note whether it was with or without prejudice.
"""


def extract_web_scas(state: AnalysisState) -> list[CaseDetail]:
    """Extract SCA cases from web search results using LLM.

    Collects litigation-related web snippets from acquired data,
    sends them to the LLM for structured extraction, and converts
    results to CaseDetail objects at LOW confidence.

    Args:
        state: Pipeline state with acquired web search data.

    Returns:
        List of CaseDetail from web search results.
    """
    if state.acquired_data is None:
        return []

    # Guard: LLM dependencies available
    if not os.environ.get("ANTHROPIC_API_KEY"):
        logger.debug("No ANTHROPIC_API_KEY — skipping web SCA LLM extraction")
        return []

    snippets = _collect_litigation_snippets(state)
    if not snippets:
        logger.debug("No litigation-related web snippets to extract")
        return []

    logger.info(
        "SCA-WEB-LLM: Sending %d litigation snippets to LLM",
        len(snippets),
    )

    # Bundle snippets into a single text block
    text_block = _format_snippets(snippets)

    # Call LLM
    extraction = _call_llm(text_block)
    if extraction is None or not extraction.cases:
        logger.info("SCA-WEB-LLM: No cases extracted from web snippets")
        return []

    # Convert to CaseDetail via existing pipeline
    from do_uw.stages.extract.llm_litigation import (
        _is_generic_label,
        _meets_minimum_evidence,
        convert_legal_proceedings,
    )
    from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction

    # Filter before conversion
    valid_procs: list[ExtractedLegalProceeding] = []
    for proc in extraction.cases:
        if not proc.case_name or not proc.case_name.strip():
            continue
        if _is_generic_label(proc.case_name):
            logger.debug(
                "SCA-WEB-LLM: Skipping generic label: %s",
                proc.case_name,
            )
            continue
        if not _meets_minimum_evidence(proc):
            logger.debug(
                "SCA-WEB-LLM: Insufficient evidence: %s",
                proc.case_name[:80],
            )
            continue
        valid_procs.append(proc)

    if not valid_procs:
        logger.info("SCA-WEB-LLM: All extracted cases filtered by quality checks")
        return []

    # Create a minimal TenKExtraction wrapper for convert_legal_proceedings
    fake_extraction = TenKExtraction(legal_proceedings=valid_procs)
    cases = convert_legal_proceedings(fake_extraction)

    # Downgrade all to LOW confidence (web source)
    for case in cases:
        _downgrade_confidence(case)

    logger.info("SCA-WEB-LLM: Extracted %d cases from web snippets", len(cases))
    return cases


def _collect_litigation_snippets(
    state: AnalysisState,
) -> list[dict[str, str]]:
    """Collect litigation-related web search snippets from state.

    Gathers from:
    1. litigation_data["web_results"]
    2. blind_spot_results pre/post_structured litigation category

    Returns list of {title, snippet, url} dicts.
    """
    results: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    acquired = state.acquired_data
    if acquired is None:
        return results

    # 1. Litigation web results (targeted search)
    lit_data = acquired.litigation_data
    web_results = lit_data.get("web_results", [])
    if isinstance(web_results, list):
        for r in cast(list[Any], web_results):
            if isinstance(r, dict):
                _add_if_relevant(r, results, seen_urls)

    # 2. Blind spot litigation results
    blind = acquired.blind_spot_results
    if isinstance(blind, dict):
        for phase_key in ("pre_structured", "post_structured"):
            phase = blind.get(phase_key, {})
            if isinstance(phase, dict):
                lit_results = phase.get("litigation", [])
                if isinstance(lit_results, list):
                    for r in cast(list[Any], lit_results):
                        if isinstance(r, dict):
                            _add_if_relevant(r, results, seen_urls)

    return results[:_MAX_SNIPPETS]


def _add_if_relevant(
    result: dict[str, Any],
    out: list[dict[str, str]],
    seen_urls: set[str],
) -> None:
    """Add a web result if it's litigation-related and not a duplicate."""
    url = str(result.get("url", ""))
    if url in seen_urls:
        return

    title = str(result.get("title", ""))
    snippet = str(result.get("snippet", result.get("description", "")))
    combined = (title + " " + snippet).lower()

    if len(combined) < _MIN_SNIPPET_LEN:
        return

    # Check for litigation relevance
    if not any(kw in combined for kw in _LITIGATION_KEYWORDS):
        return

    seen_urls.add(url)
    out.append({"title": title, "snippet": snippet, "url": url})


def _format_snippets(snippets: list[dict[str, str]]) -> str:
    """Format web snippets into a text block for LLM consumption."""
    parts: list[str] = []
    for i, s in enumerate(snippets, 1):
        parts.append(f"[{i}] {s['title']}\n    URL: {s['url']}\n    {s['snippet']}\n")
    return "\n".join(parts)


def _call_llm(text_block: str) -> WebLitigationExtraction | None:
    """Call LLM to extract litigation cases from web snippets."""
    try:
        from do_uw.stages.extract.llm import ExtractionCache, LLMExtractor

        extractor = LLMExtractor(
            cache=ExtractionCache(),
            budget_usd=0.50,  # Web extraction is cheap (small input)
            rate_limit_tpm=100_000_000,
        )
        result = extractor.extract(
            filing_text=text_block,
            schema=WebLitigationExtraction,
            accession="web_litigation_snippets",
            form_type="WEB_SEARCH",
            system_prompt=_SYSTEM_PROMPT,
            max_tokens=4096,
        )
        return result
    except Exception as exc:
        logger.warning(
            "SCA-WEB-LLM: LLM call failed: %s: %s",
            type(exc).__name__,
            exc,
        )
        return None


def _downgrade_confidence(case: CaseDetail) -> None:
    """Downgrade all SourcedValue fields on a CaseDetail to LOW confidence."""
    from do_uw.models.common import SourcedValue

    web_source_suffix = " (web search, LLM)"

    for field_name in (
        "case_name",
        "court",
        "filing_date",
        "status",
        "settlement_amount",
        "coverage_type",
        "class_period_start",
        "class_period_end",
    ):
        sv = getattr(case, field_name, None)
        if sv is not None and isinstance(sv, SourcedValue):
            object.__setattr__(sv, "confidence", Confidence.LOW)
            object.__setattr__(
                sv,
                "source",
                sv.source + web_source_suffix,
            )

    for sv_list_name in ("allegations", "legal_theories", "named_defendants"):
        sv_list = getattr(case, sv_list_name, [])
        for sv in sv_list:
            if isinstance(sv, SourcedValue):
                object.__setattr__(sv, "confidence", Confidence.LOW)
                object.__setattr__(
                    sv,
                    "source",
                    sv.source + web_source_suffix,
                )
