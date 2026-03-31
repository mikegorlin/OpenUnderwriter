"""Governance extraction sub-orchestrator (SECT5).

Calls all SECT5 extractors in dependency order, collects
ExtractionReports, and assembles a populated GovernanceData model.

Narrative coherence runs last because it reads sentiment and other
governance sub-models from state.extracted.governance.

After all extractors complete, generates a rule-based governance
summary synthesizing 5 key dimensions.
"""

from __future__ import annotations

import logging

from do_uw.models.common import Confidence
from do_uw.models.governance import BoardProfile, CompensationFlags, GovernanceData
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    GovernanceQualityScore,
    LeadershipStability,
    NarrativeCoherence,
    OwnershipAnalysis,
    SentimentProfile,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.governance_fallbacks import (
    dedup_executives,
    fill_board_from_yfinance,
    fill_directors_from_yfinance,
    fill_executives_from_yfinance,
    fill_tenure_from_bio,
    fill_tenure_from_board,
    validate_executives,
)
from do_uw.stages.extract.governance_narrative import generate_governance_summary
from do_uw.stages.extract.validation import ExtractionReport

logger = logging.getLogger(__name__)


def run_governance_extractors(
    state: AnalysisState,
    reports: list[ExtractionReport],
    manifest: object | None = None,
) -> GovernanceData:
    """Run all SECT5 governance extractors in dependency order.

    Each extractor is wrapped in try/except so a single failure
    does not abort the entire governance extraction pass.  On failure
    the default (empty) sub-model is used and a warning is logged.

    After all extractors finish, a rule-based governance_summary is
    generated synthesizing leadership, board, compensation, ownership,
    and sentiment/coherence findings.

    Args:
        state: Pipeline state with acquired data.
        reports: Mutable report list -- each extractor appends its report.

    Returns:
        Populated GovernanceData instance.
    """
    gov = GovernanceData()

    # Log brain requirements for this domain if manifest provided
    if manifest is not None:
        from do_uw.stages.extract.extraction_manifest import ExtractionManifest

        if isinstance(manifest, ExtractionManifest):
            reqs = manifest.get_requirements_for_source("SEC_DEF14A")
            if reqs:
                logger.info(
                    "SECT5: Brain needs %d fields from DEF 14A",
                    len(reqs),
                )

    # Pre-deserialize LLM result (once for all extractors)
    from do_uw.stages.extract.llm_helpers import get_llm_def14a

    llm_def14a = get_llm_def14a(state)

    # 1. Leadership profiles and stability
    # LLM extraction is PRIMARY (produces richer data with bios, proper titles).
    # Regex is FALLBACK only when LLM yields no results.
    if llm_def14a and llm_def14a.named_executive_officers:
        from do_uw.stages.extract.llm_governance import convert_neos_to_leaders

        llm_leaders = convert_neos_to_leaders(llm_def14a)
        if llm_leaders:
            from do_uw.models.governance_forensics import LeadershipStability

            gov.leadership = LeadershipStability(executives=llm_leaders)
            logger.info(
                "SECT5: %d executives from LLM extraction (primary)",
                len(llm_leaders),
            )
            # Supplement with regex for departures and stability flags
            regex_stability = _run_leadership(state, reports)
            if regex_stability.departures_18mo:
                gov.leadership.departures_18mo = regex_stability.departures_18mo
            if regex_stability.red_flags:
                gov.leadership.red_flags = regex_stability.red_flags
            if regex_stability.stability_score is not None:
                gov.leadership.stability_score = regex_stability.stability_score
        else:
            gov.leadership = _run_leadership(state, reports)
    else:
        gov.leadership = _run_leadership(state, reports)

    # Post-extraction validation: enforce max 1 CEO, cross-validate
    # against LLM ceo_name, reject phantom entries
    ceo_name_hint = llm_def14a.ceo_name if llm_def14a else None
    gov.leadership.executives = validate_executives(
        gov.leadership.executives, ceo_name_hint=ceo_name_hint,
    )

    # Dedup: remove partial/phantom entries that are substrings
    gov.leadership.executives = dedup_executives(gov.leadership.executives)

    # Post-dedup: fill tenure_years from bio_summary "since YYYY" text
    fill_tenure_from_bio(gov.leadership.executives)

    # Fallback: populate executives from yfinance companyOfficers when
    # proxy parsing yields no results (closes GOV.EXEC, EXEC.TENURE gaps)
    if not gov.leadership.executives:
        fill_executives_from_yfinance(state, gov.leadership)

    # 2. Compensation analysis (needed by board governance scorer)
    if llm_def14a and llm_def14a.named_executive_officers:
        from do_uw.stages.extract.llm_governance import convert_compensation

        gov.comp_analysis = convert_compensation(llm_def14a)
        _add_llm_report(
            reports, "compensation_analysis", "DEF 14A (LLM)", gov.comp_analysis
        )
        logger.info("SECT5-05: Compensation from LLM extraction")
    else:
        gov.comp_analysis = _run_compensation(state, reports)

    # 2b. ECD inline XBRL extraction (HIGH confidence, overrides LLM)
    try:
        from do_uw.stages.extract.ecd_parser import (
            extract_ecd_from_proxy,
            merge_ecd_into_compensation,
        )

        ecd_data, ecd_report = extract_ecd_from_proxy(state)
        reports.append(ecd_report)
        if ecd_data:
            gov.ecd = ecd_data
            merge_ecd_into_compensation(ecd_data, gov.comp_analysis)
            logger.info(
                "SECT5-ECD: %d fields from inline XBRL",
                len([k for k in ecd_data if k not in ("source", "confidence", "pvp_table")]),
            )
    except Exception:
        logger.warning("SECT5-ECD: ECD XBRL extraction failed", exc_info=True)

    # 3. Board governance + quality score
    if llm_def14a and llm_def14a.directors:
        from do_uw.stages.extract.llm_governance import (
            convert_board_profile,
            convert_directors,
        )

        gov.board_forensics = convert_directors(llm_def14a)
        gov.board = convert_board_profile(llm_def14a)

        # If LLM extracted directors but all were rejected by name validation,
        # fall through to regex parsing as backup.
        if not gov.board_forensics:
            logger.warning(
                "SECT5: LLM returned %d directors but all failed validation "
                "— falling back to regex parsing",
                len(llm_def14a.directors),
            )
            profiles, score = _run_board_governance(
                state, reports, gov.comp_analysis
            )
            gov.board_forensics = profiles
            if score.total_score is not None:
                gov.governance_score = score
        else:
            try:
                from do_uw.stages.extract.board_governance import (
                    compute_governance_score,
                    load_governance_weights,
                )

                weights, thresholds = load_governance_weights()
                gov.governance_score = compute_governance_score(
                    gov.board_forensics, gov.comp_analysis, weights, thresholds
                )
            except Exception:
                logger.warning(
                    "Governance scoring failed with LLM data", exc_info=True
                )
        _add_llm_report(
            reports, "board_governance", "DEF 14A (LLM)", gov.board
        )
        logger.info("SECT5-03/07: Board governance from LLM extraction")
    else:
        profiles, score = _run_board_governance(
            state, reports, gov.comp_analysis
        )
        gov.board_forensics = profiles
        gov.governance_score = score

    # Fallback: populate individual director profiles from yfinance
    # when both LLM and regex extraction yielded no directors
    if not gov.board_forensics:
        logger.warning(
            "SECT5: No directors from LLM or regex — trying yfinance fallback"
        )
        gov.board_forensics = fill_directors_from_yfinance(state)

    # Fallback: fill board fields from yfinance ISS scores + companyOfficers
    # when proxy/LLM extraction left board data empty
    if gov.board.size is None:
        fill_board_from_yfinance(state, gov.board)

    # Cross-reference executive tenure from board member data
    # (many C-suite executives also sit on the board)
    fill_tenure_from_board(gov.leadership.executives, gov.board_forensics)

    # 4. Ownership structure and activist risk
    gov.ownership = _run_ownership(state, reports)

    # Supplement with LLM proxy ownership data
    if llm_def14a and llm_def14a.officers_directors_ownership_pct is not None:
        from do_uw.stages.extract.llm_governance import (
            convert_ownership_from_proxy,
        )

        llm_ownership = convert_ownership_from_proxy(llm_def14a)
        if llm_ownership.insider_pct and not gov.ownership.insider_pct:
            gov.ownership.insider_pct = llm_ownership.insider_pct

    # Populate compensation flags from LLM
    if llm_def14a:
        from do_uw.stages.extract.llm_governance import (
            convert_compensation_flags,
        )

        gov.compensation = convert_compensation_flags(llm_def14a)

    # 5. Sentiment analysis
    gov.sentiment = _run_sentiment(state, reports)

    # Write intermediate governance to state so narrative coherence
    # can read sub-models from state.extracted.governance.
    _ensure_extracted_governance(state, gov)

    # 6. Narrative coherence (MUST be last -- reads other sub-models)
    gov.narrative_coherence = _run_narrative_coherence(state, reports)

    # Generate rule-based governance summary
    gov.governance_summary = generate_governance_summary(gov)

    return gov


# ------------------------------------------------------------------
# Individual extractor wrappers
# ------------------------------------------------------------------


def _run_leadership(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> LeadershipStability:
    """Extract leadership profiles and stability."""
    try:
        from do_uw.stages.extract.leadership_profiles import (
            extract_leadership_profiles,
        )

        stability, report = extract_leadership_profiles(state)
        reports.append(report)
        logger.info("SECT5-01/02/06: Leadership profiles extracted")
        return stability
    except Exception:
        logger.warning(
            "SECT5-01/02/06: Leadership extraction failed",
            exc_info=True,
        )
        return LeadershipStability()


def _run_compensation(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> CompensationAnalysis:
    """Extract compensation analysis."""
    try:
        from do_uw.stages.extract.compensation_analysis import (
            extract_compensation,
        )

        analysis, report = extract_compensation(state)
        reports.append(report)
        logger.info("SECT5-05: Compensation analysis extracted")
        return analysis
    except Exception:
        logger.warning(
            "SECT5-05: Compensation extraction failed",
            exc_info=True,
        )
        return CompensationAnalysis()


def _run_board_governance(
    state: AnalysisState,
    reports: list[ExtractionReport],
    compensation: CompensationAnalysis | None,
) -> tuple[list[BoardForensicProfile], GovernanceQualityScore]:
    """Extract board governance profiles and quality score."""
    try:
        from do_uw.stages.extract.board_governance import (
            extract_board_governance,
        )

        (profiles, score), report = extract_board_governance(
            state, compensation=compensation
        )
        reports.append(report)
        logger.info("SECT5-03/07: Board governance extracted")
        return profiles, score
    except Exception:
        logger.warning(
            "SECT5-03/07: Board governance extraction failed",
            exc_info=True,
        )
        return [], GovernanceQualityScore()


def _run_ownership(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> OwnershipAnalysis:
    """Extract ownership structure and activist risk."""
    try:
        from do_uw.stages.extract.ownership_structure import (
            extract_ownership,
        )

        analysis, report = extract_ownership(state)
        reports.append(report)
        logger.info("SECT5-08: Ownership structure extracted")
        return analysis
    except Exception:
        logger.warning(
            "SECT5-08: Ownership extraction failed",
            exc_info=True,
        )
        return OwnershipAnalysis()


def _run_sentiment(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> SentimentProfile:
    """Extract multi-source sentiment profile."""
    try:
        from do_uw.stages.analyze.sentiment_analysis import (
            extract_sentiment,
        )

        profile, report = extract_sentiment(state)
        reports.append(report)
        logger.info("SECT5-04/09: Sentiment analysis extracted")
        return profile
    except Exception:
        logger.warning(
            "SECT5-04/09: Sentiment extraction failed",
            exc_info=True,
        )
        return SentimentProfile()


def _run_narrative_coherence(
    state: AnalysisState,
    reports: list[ExtractionReport],
) -> NarrativeCoherence:
    """Assess narrative coherence (must run after sentiment and other extractors)."""
    try:
        from do_uw.stages.analyze.narrative_coherence import (
            assess_narrative_coherence,
        )

        coherence, report = assess_narrative_coherence(state)
        reports.append(report)
        logger.info("SECT5-10: Narrative coherence assessed")
        return coherence
    except Exception:
        logger.warning(
            "SECT5-10: Narrative coherence assessment failed",
            exc_info=True,
        )
        return NarrativeCoherence()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _ensure_extracted_governance(
    state: AnalysisState, gov: GovernanceData
) -> None:
    """Write intermediate governance to state for narrative coherence."""
    from do_uw.models.state import ExtractedData

    if state.extracted is None:
        state.extracted = ExtractedData()
    state.extracted.governance = gov


def _add_llm_report(
    reports: list[ExtractionReport],
    extractor_name: str,
    source: str,
    model: BoardProfile | CompensationFlags | CompensationAnalysis,
) -> None:
    """Create extraction report from LLM-populated model."""
    fields = type(model).model_fields
    found = [
        name for name in fields if getattr(model, name, None) is not None
    ]
    reports.append(
        ExtractionReport(
            extractor_name=extractor_name,
            expected_fields=list(fields.keys()),
            found_fields=found,
            missing_fields=[f for f in fields if f not in found],
            unexpected_fields=[],
            coverage_pct=(
                len(found) / len(fields) * 100.0 if fields else 100.0
            ),
            confidence=Confidence.HIGH,
            source_filing=source,
        )
    )
