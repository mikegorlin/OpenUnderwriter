"""AI patent activity parser -- parse pre-fetched USPTO patent records.

Parses raw USPTO patent result dicts (fetched in ACQUIRE stage and stored
at state.acquired_data.patent_data) into the AIPatentActivity model.

When no USPTO data is available, falls back to:
1. 10-K filing text extraction for patent mentions near AI keywords
2. Web search results from blind-spot discovery

Patent data from USPTO is MEDIUM confidence; fallback data is LOW.

Part of the SECT8 AI Transformation Risk Factor extraction pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from do_uw.models.ai_risk import AIPatentActivity
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.ai_patent_fallback import (
    extract_from_10k_text,
    extract_from_web_search,
)
from do_uw.stages.extract.validation import ExtractionReport, create_report

logger = logging.getLogger(__name__)

_MAX_RECENT_FILINGS = 20

# Date formats used by USPTO API
_DATE_FORMATS: list[str] = ["%Y-%m-%d", "%m-%d-%Y", "%Y%m%d"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_patent_activity(
    state: AnalysisState,
    raw_results: list[dict[str, Any]] | None = None,
) -> tuple[AIPatentActivity, ExtractionReport]:
    """Parse AI patent activity from pre-fetched USPTO data.

    Args:
        state: Pipeline state with company identity and acquired_data.
        raw_results: Pre-fetched USPTO results from ACQUIRE stage.
                     Defaults to state.acquired_data.patent_data if None.

    Returns:
        Tuple of (AIPatentActivity, ExtractionReport).
    """
    expected_fields = ["patent_count", "filings", "trend"]

    # Resolve raw_results from acquired_data if not provided directly.
    if raw_results is None:
        if state.acquired_data is not None:
            raw_results = state.acquired_data.patent_data
        else:
            raw_results = []

    patent_data: AIPatentActivity | None = None
    source_filing = "USPTO Patent Application API"
    fallbacks_used: list[str] = []
    warnings: list[str] = []

    if raw_results:
        patent_data = _parse_results(raw_results)
    else:
        warnings.append("USPTO API data not available")
        # Fallback 1: Extract from 10-K text
        patent_data = extract_from_10k_text(state)
        if patent_data is not None:
            source_filing = "10-K filing text (patent mentions)"
            fallbacks_used.append("10-K text extraction")
            logger.info("SECT8: Patent data extracted from 10-K text")
        else:
            # Fallback 2: Extract from web search results
            patent_data = extract_from_web_search(state)
            if patent_data is not None:
                source_filing = "Web search results"
                fallbacks_used.append("web search results")
                logger.info("SECT8: Patent data extracted from web search")

    if patent_data is None:
        patent_data = AIPatentActivity()
        warnings.append("All patent data sources failed")

    found_fields: list[str] = []
    if patent_data.ai_patent_count > 0:
        found_fields.append("patent_count")
    if patent_data.recent_filings:
        found_fields.append("filings")
    if patent_data.filing_trend != "UNKNOWN":
        found_fields.append("trend")

    report = create_report(
        extractor_name="ai_patent",
        expected=expected_fields,
        found=found_fields,
        source_filing=source_filing,
        fallbacks_used=fallbacks_used if fallbacks_used else None,
        warnings=warnings if warnings else None,
    )

    logger.info(
        "SECT8: Patent activity extracted -- %d AI patents, trend=%s",
        patent_data.ai_patent_count,
        patent_data.filing_trend,
    )
    return patent_data, report


def _parse_results(
    results: list[dict[str, Any]],
) -> AIPatentActivity:
    """Parse USPTO API results into AIPatentActivity model.

    Args:
        results: List of patent result dicts from USPTO API.

    Returns:
        Populated AIPatentActivity.
    """
    ai_patent_count = len(results)

    # Build recent filings list
    recent_filings: list[dict[str, str]] = []
    # Sort by filing date descending if available
    sorted_results = sorted(
        results,
        key=lambda r: str(r.get("patentApplicationNumber", r.get("filingDate", ""))),
        reverse=True,
    )

    for record in sorted_results[:_MAX_RECENT_FILINGS]:
        filing = {
            "patent_number": str(
                record.get(
                    "patentApplicationNumber",
                    record.get("patentNumber", ""),
                )
            ),
            "filing_date": str(record.get("filingDate", "")),
            "title": str(record.get("inventionTitle", record.get("title", ""))),
        }
        recent_filings.append(filing)

    # Determine filing trend
    filing_trend = _compute_filing_trend(results)

    return AIPatentActivity(
        ai_patent_count=ai_patent_count,
        recent_filings=recent_filings,
        filing_trend=filing_trend,
    )


def _compute_filing_trend(results: list[dict[str, Any]]) -> str:
    """Compute filing trend by comparing recent vs older patents.

    If filings in last 2 years > filings in 2-4 years ago: INCREASING.
    If less: DECREASING. Otherwise: STABLE. Returns UNKNOWN if no dates.
    """
    if not results:
        return "UNKNOWN"

    recent_count = 0  # last 2 years
    older_count = 0  # 2-4 years ago
    now = datetime.now()

    for record in results:
        date_str = str(record.get("filingDate", ""))
        if not date_str:
            continue
        try:
            filing_date = _parse_date(date_str)
            if filing_date is None:
                continue
            years_ago = (now - filing_date).days / 365.25
            if years_ago <= 2.0:
                recent_count += 1
            elif years_ago <= 4.0:
                older_count += 1
        except (ValueError, TypeError):
            continue

    if recent_count == 0 and older_count == 0:
        return "UNKNOWN"
    if older_count == 0:
        return "INCREASING" if recent_count > 0 else "UNKNOWN"
    if recent_count > older_count:
        return "INCREASING"
    if recent_count < older_count:
        return "DECREASING"
    return "STABLE"


def _parse_date(date_str: str) -> datetime | None:
    """Try multiple date formats for USPTO dates."""
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None
