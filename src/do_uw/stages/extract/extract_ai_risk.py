"""AI risk extraction sub-orchestrator (SECT8).

Calls all SECT8 extractors in dependency order, collects
ExtractionReports, and assembles a populated AIRiskAssessment model.

Follows the exact same pattern as extract_market.py / extract_governance.py:
each extractor wrapped in try/except so a single failure does not abort
the entire AI risk extraction pass.
"""

from __future__ import annotations

import logging

from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.validation import ExtractionReport

logger = logging.getLogger(__name__)


def run_ai_risk_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> AIRiskAssessment:
    """Run all SECT8 AI risk extractors in dependency order.

    Each extractor is wrapped in try/except so a single failure
    does not abort the entire AI risk extraction pass.  On failure
    the default (empty) sub-model is used and a warning is logged.

    Args:
        state: Pipeline state with acquired data.
        reports: Mutable report list -- each extractor appends its report.

    Returns:
        Populated AIRiskAssessment instance.
    """
    # 1. AI disclosure analysis (must run first -- competitive needs it)
    disclosure = _run_disclosure(state, reports)

    # 1b. Supplement AI disclosure with LLM risk factors categorized as AI
    _supplement_ai_risk_factors(state, disclosure)

    # 2. Patent activity
    patent = _run_patent(state, reports)

    # 3. Competitive position (depends on disclosure data)
    competitive = _run_competitive(state, reports, disclosure)

    # Determine which data sources contributed
    data_sources: list[str] = []
    if disclosure.mention_count > 0:
        data_sources.append("10-K Item 1A AI disclosures")
    if patent.ai_patent_count > 0:
        data_sources.append("USPTO patent filings")
    if competitive.adoption_stance != "UNKNOWN":
        data_sources.append("Peer competitive comparison")

    peer_available = competitive.adoption_stance != "UNKNOWN"

    # Disclosure trend mirrors the YoY trend from disclosure extractor
    disclosure_trend = disclosure.yoy_trend

    return AIRiskAssessment(
        disclosure_data=disclosure,
        patent_activity=patent,
        competitive_position=competitive,
        peer_comparison_available=peer_available,
        disclosure_trend=disclosure_trend,
        data_sources=data_sources,
        # Scoring fields (overall_score, sub_dimensions, narrative)
        # are left at defaults -- scored in SCORE stage via Plan 01's engine
    )


# ------------------------------------------------------------------
# LLM AI risk factor supplement
# ------------------------------------------------------------------


def _supplement_ai_risk_factors(
    state: AnalysisState, disclosure: AIDisclosureData,
) -> None:
    """Add LLM-extracted AI risk factors to disclosure data.

    Finds risk factors with category 'AI' from the 10-K LLM extraction
    and appends their titles to disclosure.risk_factors if not already
    present. Provides richer context than keyword counting alone.
    """
    from do_uw.stages.extract.llm_helpers import get_llm_ten_k

    llm_ten_k = get_llm_ten_k(state)
    if llm_ten_k is None or not llm_ten_k.risk_factors:
        return

    ai_factors = [
        rf for rf in llm_ten_k.risk_factors
        if rf.category and rf.category.upper() == "AI"
    ]
    if not ai_factors:
        return

    existing_lower = {rf.lower() for rf in disclosure.risk_factors}
    added = 0
    for af in ai_factors:
        title = af.title.strip()
        if title and title.lower() not in existing_lower:
            disclosure.risk_factors.append(title)
            existing_lower.add(title.lower())
            added += 1

    if added > 0:
        logger.info("SECT8: Supplemented AI risk with %d LLM AI factors", added)


# ------------------------------------------------------------------
# Individual extractor wrappers
# ------------------------------------------------------------------


def _run_disclosure(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> AIDisclosureData:
    """Extract AI disclosure data from 10-K Item 1A."""
    try:
        from do_uw.stages.extract.ai_disclosure_extract import (
            extract_ai_disclosures,
        )

        disclosure, disc_report = extract_ai_disclosures(state)
        reports.append(disc_report)
        logger.info("SECT8-01: AI disclosure extracted")
        return disclosure
    except Exception:
        logger.warning(
            "SECT8-01: AI disclosure extraction failed",
            exc_info=True,
        )
        return AIDisclosureData()


def _run_patent(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> AIPatentActivity:
    """Parse patent activity from pre-fetched ACQUIRE stage data."""
    try:
        from do_uw.stages.extract.ai_patent_extract import (
            extract_patent_activity,
        )

        # Pass pre-fetched results from ACQUIRE stage; empty list is safe.
        raw = (
            state.acquired_data.patent_data
            if state.acquired_data is not None
            else []
        )
        patent, patent_report = extract_patent_activity(state, raw_results=raw)
        reports.append(patent_report)
        logger.info("SECT8-02: Patent activity extracted")
        return patent
    except Exception:
        logger.warning(
            "SECT8-02: Patent activity extraction failed",
            exc_info=True,
        )
        return AIPatentActivity()


def _run_competitive(
    state: AnalysisState,
    reports: list[ExtractionReport],
    disclosure: AIDisclosureData,
) -> AICompetitivePosition:
    """Assess competitive AI position relative to peers."""
    try:
        from do_uw.stages.extract.ai_competitive_extract import (
            assess_competitive_position,
        )

        competitive, comp_report = assess_competitive_position(
            state, disclosure
        )
        reports.append(comp_report)
        logger.info("SECT8-03: Competitive position assessed")
        return competitive
    except Exception:
        logger.warning(
            "SECT8-03: Competitive position assessment failed",
            exc_info=True,
        )
        return AICompetitivePosition()
