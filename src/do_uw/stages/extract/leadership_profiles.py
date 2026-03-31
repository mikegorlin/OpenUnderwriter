"""Leadership forensic profile extraction from proxy and 8-K filings.

Extracts C-suite executive profiles from DEF 14A proxy statements,
departure/appointment events from 8-K Item 5.02, and assesses
overall leadership stability with red flag detection.

Covers SECT5-01 (overview), SECT5-02 (executive profiles),
and SECT5-06 (stability analysis) for D&O underwriting.

Usage:
    stability, report = extract_leadership_profiles(state)
    state.extracted.governance.leadership = stability
"""

from __future__ import annotations

import logging
from datetime import datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import (
    LeadershipForensicProfile,
    LeadershipStability,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.leadership_parsing import (
    extract_departures_from_8k,
    extract_executives_from_proxy,
    get_8k_documents,
    search_prior_litigation,
)
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    get_filing_texts,
    get_filings,
    sourced_float,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# Expected fields for the extraction report.
EXPECTED_FIELDS: list[str] = [
    "executives_found",
    "departures_18mo",
    "red_flags",
    "stability_score",
    "prior_litigation_searched",
]

# Red flag deductions from stability_score (out of 100).
_FLAG_DEDUCTIONS: dict[str, int] = {
    "sudden_cfo_departure": 25,
    "cao_departure_after_filing_season": 20,
    "multiple_departures_12mo": 30,
    "cfo_plus_csuite_6mo": 35,
    "mid_term_board_resignation": 15,
    "gc_departure_during_litigation": 25,
    "interim_cfo": 15,
    "interim_ceo": 20,
}


# ---------------------------------------------------------------------------
# Stability assessment
# ---------------------------------------------------------------------------


def _assess_stability(
    executives: list[LeadershipForensicProfile],
    departures: list[LeadershipForensicProfile],
) -> LeadershipStability:
    """Compute leadership stability score and detect red flags.

    Score starts at 100 and is reduced for each red flag detected.
    Flags: sudden CFO departure, CAO departure after filing season,
    3+ departures in 12 months, CFO + another C-suite in 6 months,
    mid-term board resignation, GC departure during litigation.

    Args:
        executives: Currently serving C-suite profiles.
        departures: Recent executive departures (18 months).

    Returns:
        LeadershipStability model with score, flags, and statistics.
    """
    stability = LeadershipStability(
        executives=executives,
        departures_18mo=departures,
    )
    source = "leadership_profiles extractor"
    red_flags: list[SourcedValue[str]] = []
    score = 100

    # Compute average tenure.
    tenures = [
        e.tenure_years for e in executives if e.tenure_years is not None
    ]
    if tenures:
        avg = sum(tenures) / len(tenures)
        stability.avg_tenure_years = sourced_float(
            avg, source, Confidence.MEDIUM
        )
        longest = max(executives, key=lambda e: e.tenure_years or 0)
        shortest = min(executives, key=lambda e: e.tenure_years or 999)
        if longest.name:
            stability.longest_tenured = sourced_str(
                longest.name.value, source, Confidence.MEDIUM
            )
        if shortest.name:
            stability.shortest_tenured = sourced_str(
                shortest.name.value, source, Confidence.MEDIUM
            )

    # Red flag checks.
    _check_cfo_departure(departures, red_flags, score_ref := [score])
    score = score_ref[0]
    _check_cao_departure(departures, red_flags, score_ref := [score])
    score = score_ref[0]
    _check_multiple_departures(departures, red_flags, score_ref := [score])
    score = score_ref[0]
    _check_cfo_plus_csuite(departures, red_flags, score_ref := [score])
    score = score_ref[0]
    _check_gc_departure(departures, red_flags, score_ref := [score])
    score = score_ref[0]
    _check_interim_officers(executives, red_flags, score_ref := [score])
    score = score_ref[0]

    stability.red_flags = red_flags
    stability.stability_score = sourced_float(
        max(0.0, float(score)), source, Confidence.MEDIUM
    )
    return stability


def _check_cfo_departure(
    departures: list[LeadershipForensicProfile],
    flags: list[SourcedValue[str]],
    score: list[int],
) -> None:
    """Check for sudden (unplanned) CFO departure."""
    source = "leadership_profiles extractor"
    cfo_deps = [
        d for d in departures
        if d.title and d.title.value == "CFO"
        and d.departure_type == "UNPLANNED"
    ]
    if cfo_deps:
        flags.append(sourced_str(
            "Sudden CFO departure (unplanned)", source, Confidence.HIGH,
        ))
        score[0] -= _FLAG_DEDUCTIONS["sudden_cfo_departure"]


def _check_cao_departure(
    departures: list[LeadershipForensicProfile],
    flags: list[SourcedValue[str]],
    score: list[int],
) -> None:
    """Check for CAO departure after filing season (Jan-Mar)."""
    source = "leadership_profiles extractor"
    cao_deps = [
        d for d in departures if d.title and d.title.value == "CAO"
    ]
    for dep in cao_deps:
        if dep.departure_date:
            try:
                dep_dt = datetime.strptime(dep.departure_date, "%Y-%m-%d")
                if dep_dt.month in (1, 2, 3):
                    flags.append(sourced_str(
                        f"CAO departure after filing season ({dep.departure_date})",
                        source, Confidence.HIGH,
                    ))
                    score[0] -= _FLAG_DEDUCTIONS["cao_departure_after_filing_season"]
                    break
            except ValueError:
                pass


def _check_multiple_departures(
    departures: list[LeadershipForensicProfile],
    flags: list[SourcedValue[str]],
    score: list[int],
) -> None:
    """Check for 3+ departures in tracking period."""
    if len(departures) >= 3:
        source = "leadership_profiles extractor"
        flags.append(sourced_str(
            f"{len(departures)} executive departures in tracking period",
            source, Confidence.HIGH,
        ))
        score[0] -= _FLAG_DEDUCTIONS["multiple_departures_12mo"]


def _check_cfo_plus_csuite(
    departures: list[LeadershipForensicProfile],
    flags: list[SourcedValue[str]],
    score: list[int],
) -> None:
    """Check for CFO + another C-suite departure together."""
    source = "leadership_profiles extractor"
    cfo_deps = [
        d for d in departures
        if d.title and d.title.value == "CFO"
        and d.departure_type == "UNPLANNED"
    ]
    if cfo_deps and len(departures) >= 2:
        non_cfo = [
            d for d in departures
            if not (d.title and d.title.value == "CFO")
        ]
        if non_cfo:
            flags.append(sourced_str(
                "CFO departure coinciding with other C-suite departure",
                source, Confidence.MEDIUM,
            ))
            score[0] -= _FLAG_DEDUCTIONS["cfo_plus_csuite_6mo"]


def _check_gc_departure(
    departures: list[LeadershipForensicProfile],
    flags: list[SourcedValue[str]],
    score: list[int],
) -> None:
    """Check for General Counsel / CLO departure."""
    gc_deps = [
        d for d in departures if d.title and d.title.value == "CLO"
    ]
    if gc_deps:
        source = "leadership_profiles extractor"
        flags.append(sourced_str(
            "General Counsel / CLO departure",
            source, Confidence.MEDIUM,
        ))
        score[0] -= _FLAG_DEDUCTIONS["gc_departure_during_litigation"]


def _check_interim_officers(
    executives: list[LeadershipForensicProfile],
    flags: list[SourcedValue[str]],
    score: list[int],
) -> None:
    """Check for interim officers in C-suite."""
    source = "leadership_profiles extractor"
    interim_execs = [
        e for e in executives if e.is_interim and e.is_interim.value
    ]
    for ie in interim_execs:
        title = ie.title.value if ie.title else "executive"
        flag_key = "interim_ceo" if title == "CEO" else "interim_cfo"
        flags.append(sourced_str(
            f"Interim {title} serving", source, Confidence.HIGH,
        ))
        score[0] -= _FLAG_DEDUCTIONS.get(flag_key, 10)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_leadership_profiles(
    state: AnalysisState,
) -> tuple[LeadershipStability, ExtractionReport]:
    """Extract leadership profiles and stability analysis.

    Parses DEF 14A proxy statement for C-suite executives and 8-K
    filings for departure events, then assesses overall leadership
    stability with red flag detection.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (LeadershipStability, ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "DEF 14A + 8-K Item 5.02"

    # Get proxy text from filing documents.
    proxy_text = get_filing_document_text(state, "DEF 14A")
    if not proxy_text:
        filings = get_filings(state)
        texts = get_filing_texts(filings)
        proxy_text = str(texts.get("proxy_compensation", ""))
        proxy_gov = str(texts.get("proxy_governance", ""))
        if proxy_gov:
            proxy_text = proxy_text + "\n" + proxy_gov

    # Extract executives from proxy.
    executives = extract_executives_from_proxy(proxy_text)
    if executives:
        found.append("executives_found")
    else:
        warnings.append("No executives extracted from proxy text")

    # Get 8-K texts for departures.
    eight_k_texts: list[str] = list(get_8k_documents(state))
    if not eight_k_texts:
        filings = get_filings(state)
        texts = get_filing_texts(filings)
        for key in ("8-K_item502", "item502", "8-K"):
            val = str(texts.get(key, ""))
            if val.strip():
                eight_k_texts.append(val)

    departures = extract_departures_from_8k(eight_k_texts)
    found.append("departures_18mo")

    # Assess stability.
    stability = _assess_stability(executives, departures)
    if stability.stability_score is not None:
        found.append("stability_score")
    if stability.red_flags:
        found.append("red_flags")

    # Search prior litigation for each executive.
    litigation_searched = False
    for exec_profile in executives:
        if exec_profile.name:
            hits = search_prior_litigation(exec_profile.name.value, state)
            for hit in hits:
                exec_profile.prior_litigation.append(
                    sourced_str(hit, "litigation search", Confidence.LOW)
                )
            litigation_searched = True

    if litigation_searched:
        found.append("prior_litigation_searched")

    report = create_report(
        extractor_name="leadership_profiles",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return stability, report
