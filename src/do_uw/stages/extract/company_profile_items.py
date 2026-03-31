"""Item-level parsing functions for company profile extraction.

Split from company_profile.py (Phase 45, 500-line rule).
Contains data resolution helpers: employee count validation,
GICS code resolution, NAICS code resolution, and business
description extraction.
"""

from __future__ import annotations

import logging
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    get_filing_texts,
    get_filings,
    get_info_dict,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
)

logger = logging.getLogger(__name__)


def _validate_employee_count(
    llm_count: int | None,
    revenue: float | None,
    yfinance_count: int | None,
) -> int | None:
    """Validate employee count against revenue and yfinance data.

    Catches cases where LLM returns truncated numbers (62 instead of 62000).
    For example, a filing that says "approximately 62 thousand employees"
    may be extracted as just 62.

    Args:
        llm_count: Employee count from LLM extraction.
        revenue: Market cap or revenue as a proxy for company size (USD).
        yfinance_count: Employee count from yfinance (cross-validation).

    Returns:
        Validated employee count, or None if no data available.
    """
    if llm_count is None:
        return yfinance_count  # Fall back to yfinance

    # If we have yfinance data, use it as a cross-check
    if yfinance_count is not None and yfinance_count > 100:
        ratio = llm_count / yfinance_count if yfinance_count > 0 else 0.0
        if ratio < 0.01:  # LLM count is <1% of yfinance -- likely truncated
            logger.warning(
                "Employee count %d likely truncated (yfinance: %d). "
                "Using yfinance value.",
                llm_count,
                yfinance_count,
            )
            return yfinance_count

    # Heuristic: company with >$10B revenue/market_cap shouldn't have <100 employees
    if revenue is not None and revenue > 10_000_000_000 and llm_count < 100:
        logger.warning(
            "Employee count %d implausibly low for $%.0fB company. "
            "Possible truncated number (thousands -> raw).",
            llm_count,
            revenue / 1_000_000_000,
        )
        # Try multiplying by 1000 as heuristic fix
        return llm_count * 1000

    return llm_count


def _resolve_gics_code(
    profile: CompanyProfile,
    info: dict[str, Any],
) -> SourcedValue[str] | None:
    """Resolve GICS industry code from SIC mapping.

    Strategy: look up company's SIC code in config/sic_gics_mapping.json.
    yfinance provides sector/industry names but not the 8-digit GICS code,
    so the SIC->GICS mapping is the primary path.

    Returns SourcedValue[str] or None if no mapping found.
    """
    import json
    from pathlib import Path

    sic_raw = (
        profile.identity.sic_code.value
        if profile.identity.sic_code is not None
        else None
    )
    if sic_raw is None:
        return None

    sic_str = str(sic_raw).strip()
    if not sic_str:
        return None

    brain_mapping = Path(__file__).parent.parent.parent / "brain" / "config" / "sic_gics_mapping.json"
    config_mapping = Path(__file__).parent.parent.parent / "config" / "sic_gics_mapping.json"
    mapping_path = brain_mapping if brain_mapping.exists() else config_mapping
    if not mapping_path.exists():
        logger.debug("SIC->GICS mapping file not found: %s", mapping_path)
        return None

    try:
        data = json.loads(mapping_path.read_text())
        mappings = data.get("mappings", {})
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Error loading SIC->GICS mapping: %s", exc)
        return None

    entry = mappings.get(sic_str)
    if entry is None:
        logger.debug("No GICS mapping for SIC %s", sic_str)
        return None

    gics_code = str(entry.get("gics", ""))
    if not gics_code:
        return None

    return sourced_str(
        gics_code,
        f"SIC->GICS mapping (SIC {sic_str})",
        Confidence.MEDIUM,
    )


def _resolve_naics_code(
    profile: CompanyProfile,
) -> SourcedValue[str] | None:
    """Resolve NAICS code from SIC->NAICS crosswalk.

    Returns SourcedValue[str] or None if no mapping found.
    """
    import json
    from pathlib import Path

    sic_raw = (
        profile.identity.sic_code.value
        if profile.identity.sic_code is not None
        else None
    )
    if sic_raw is None:
        return None

    sic_str = str(sic_raw).strip()
    if not sic_str:
        return None

    brain_mapping_path = Path(__file__).parent.parent.parent / "brain" / "config" / "sic_naics_mapping.json"
    config_mapping_path = Path(__file__).parent.parent.parent / "config" / "sic_naics_mapping.json"
    mapping_path = brain_mapping_path if brain_mapping_path.exists() else config_mapping_path
    if not mapping_path.exists():
        logger.debug("SIC->NAICS mapping file not found: %s", mapping_path)
        return None

    try:
        data = json.loads(mapping_path.read_text())
        mappings = data.get("mappings", {})
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Error loading SIC->NAICS mapping: %s", exc)
        return None

    entry = mappings.get(sic_str)
    if entry is None:
        logger.debug("No NAICS mapping for SIC %s", sic_str)
        return None

    naics_code = str(entry.get("naics", ""))
    if not naics_code:
        return None

    return sourced_str(
        naics_code,
        f"SIC->NAICS crosswalk (SIC {sic_str})",
        Confidence.MEDIUM,
    )


def _extract_business_description(
    state: AnalysisState,
) -> tuple[SourcedValue[str] | None, ExtractionReport]:
    """Extract business description from 10-K Item 1 text."""
    filings = get_filings(state)
    filing_texts = get_filing_texts(filings)
    item1 = str(filing_texts.get("10-K_item1", ""))
    if not item1:
        item1 = str(filing_texts.get("item1", ""))

    info = get_info_dict(state)
    yf_summary = str(info.get("longBusinessSummary", ""))

    found: list[str] = []
    fallbacks: list[str] = []
    result: SourcedValue[str] | None = None

    # Prefer yfinance longBusinessSummary (clean narrative) over raw 10-K
    # Item 1 text (SEC filing markup dump). The LLM enrichment pass will
    # replace this with a richer narrative when available.
    if yf_summary.strip():
        result = sourced_str(yf_summary.strip(), "yfinance", Confidence.MEDIUM)
        found.append("business_description")
    elif item1.strip():
        # Raw Item 1 text is a poor fallback -- only used if yfinance unavailable.
        # Will be replaced by LLM extraction in _enrich_from_llm().
        result = sourced_str(item1.strip()[:2000], "10-K Item 1 (raw)", Confidence.LOW)
        found.append("business_description")
        fallbacks.append("raw_item1_text")

    return result, create_report(
        extractor_name="business_description", expected=["business_description"],
        found=found,
        source_filing="yfinance" if yf_summary.strip() else "10-K Item 1",
        fallbacks_used=fallbacks,
    )


__all__ = [
    "_extract_business_description",
    "_resolve_gics_code",
    "_resolve_naics_code",
    "_validate_employee_count",
]
