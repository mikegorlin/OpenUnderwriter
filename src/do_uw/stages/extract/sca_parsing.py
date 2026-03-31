"""SCA source-specific parsers and deduplication logic.

Parses securities class action data from three sources:
1. EFTS sec_references (primary)
2. 10-K Item 3 (supplement)
3. Web search / blind spot results (low confidence)

Split from sca_extractor.py to stay under 500-line limit.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import CaseDetail
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.filing_sections import SECTION_DEFS, extract_section
from do_uw.stages.extract.sca_extractor import (
    SCA_KEYWORDS,
    detect_coverage_type,
    detect_legal_theories,
    detect_status,
    extract_case_name,
    extract_court,
    extract_filing_date,
    extract_settlement_amount,
    is_sca_reference,
    is_within_horizon,
    lookup_counsel_tier,
    word_overlap_pct,
)
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    now,
    sourced_float,
    sourced_int,
    sourced_str,
)

# ---------------------------------------------------------------------------
# Source-specific parsers
# ---------------------------------------------------------------------------


def parse_efts_references(
    state: AnalysisState,
    counsel_tiers: dict[str, Any],
) -> list[CaseDetail]:
    """Parse EFTS sec_references for SCA cases (primary source)."""
    if state.acquired_data is None:
        return []

    lit_data = state.acquired_data.litigation_data
    refs = lit_data.get("sec_references")
    if not isinstance(refs, list):
        return []

    cases: list[CaseDetail] = []
    typed_refs = cast(list[Any], refs)
    source = "EFTS/SCAC sec_references"

    for ref in typed_refs:
        ref_text = str(ref) if not isinstance(ref, str) else ref
        if not is_sca_reference(ref_text):
            continue

        case = _build_case_from_text(ref_text, source, Confidence.MEDIUM)

        # Time horizon filtering.
        if case.filing_date and not is_within_horizon(case.filing_date.value):
            continue

        # Lead counsel lookup.
        counsel_match = re.search(
            r"(?:lead\s+counsel|plaintiff.s?\s+counsel)[:\s]+([^.;]+)",
            ref_text, re.IGNORECASE,
        )
        if counsel_match:
            counsel_name = counsel_match.group(1).strip()
            case.lead_counsel = sourced_str(
                counsel_name, source, Confidence.MEDIUM,
            )
            tier = lookup_counsel_tier(counsel_name, counsel_tiers)
            case.lead_counsel_tier = sourced_int(
                tier, source, Confidence.MEDIUM,
            )

        # Class period computation.
        if case.class_period_start and case.class_period_end:
            delta = (
                case.class_period_end.value - case.class_period_start.value
            )
            case.class_period_days = delta.days

        cases.append(case)

    return cases


def parse_item3_text(
    state: AnalysisState,
) -> list[CaseDetail]:
    """Parse 10-K Item 3 for SCA mentions (supplemental source)."""
    full_text = get_filing_document_text(state, "10-K")
    if not full_text:
        return []

    # Extract Item 3 section using SECTION_DEFS.
    item3_def = next(
        (d for d in SECTION_DEFS if d[0] == "item3"), None,
    )
    if item3_def is None:
        return []

    item3_text = extract_section(full_text, item3_def[1], item3_def[2])
    if not item3_text:
        return []

    cases: list[CaseDetail] = []
    source = "10-K Item 3 Legal Proceedings"

    # Split into paragraphs for individual case detection.
    paragraphs = re.split(r"\n\s*\n", item3_text)
    for para in paragraphs:
        if not is_sca_reference(para):
            continue

        case = _build_case_from_text(para, source, Confidence.MEDIUM)
        if case.filing_date and not is_within_horizon(case.filing_date.value):
            continue
        cases.append(case)

    return cases


def _collect_blind_spot_texts(
    value: Any,
    results: list[str],
) -> None:
    """Recursively collect text strings from blind spot result values.

    Handles both flat lists and nested dicts (e.g. blind_spot_results
    has structure {"pre_structured": {"litigation": [...], ...}, ...}).
    """
    if isinstance(value, dict):
        typed_dict = cast(dict[str, Any], value)
        for _sub_key, sub_val in typed_dict.items():
            _collect_blind_spot_texts(sub_val, results)
    elif isinstance(value, list):
        for item in cast(list[Any], value):
            results.append(str(item))
    elif isinstance(value, str):
        results.append(value)


def parse_web_results(
    state: AnalysisState,
) -> list[CaseDetail]:
    """Parse web search and blind spot results for SCA mentions."""
    if state.acquired_data is None:
        return []

    cases: list[CaseDetail] = []
    source = "web search"

    # Check litigation web_results.
    web_results = state.acquired_data.litigation_data.get("web_results")
    # Check blind spot results.
    blind_results = state.acquired_data.blind_spot_results

    all_results: list[str] = []
    if isinstance(web_results, list):
        for r in cast(list[Any], web_results):
            all_results.append(str(r))
    if blind_results:
        _collect_blind_spot_texts(blind_results, all_results)

    for result_text in all_results:
        if not is_sca_reference(result_text):
            continue

        case = _build_case_from_text(result_text, source, Confidence.LOW)
        if case.filing_date and not is_within_horizon(case.filing_date.value):
            continue
        cases.append(case)

    return cases


# ---------------------------------------------------------------------------
# Case construction helper
# ---------------------------------------------------------------------------


def _build_case_from_text(
    text: str, source: str, confidence: Confidence,
) -> CaseDetail:
    """Build a CaseDetail from text with given source and confidence.

    Extracts case name, court, filing date, settlement amount,
    status, legal theories, coverage type, and allegations.
    Filters out cases outside the 10-year time horizon by
    returning a CaseDetail that the caller should check.
    """
    case = CaseDetail()

    case_name = extract_case_name(text)
    if case_name:
        case.case_name = sourced_str(case_name, source, confidence)

    court = extract_court(text)
    if court:
        case.court = sourced_str(court, source, confidence)

    filing_date = extract_filing_date(text)
    if filing_date:
        if not is_within_horizon(filing_date):
            # Mark with a sentinel date to signal filtering.
            case.filing_date = SourcedValue[date](
                value=filing_date, source=source,
                confidence=confidence, as_of=now(),
            )
            # Caller checks is_within_horizon on the case.
        else:
            case.filing_date = SourcedValue[date](
                value=filing_date, source=source,
                confidence=confidence, as_of=now(),
            )

    settlement = extract_settlement_amount(text)
    if settlement is not None:
        case.settlement_amount = sourced_float(
            settlement, source, confidence,
        )

    # Status detection.
    status = detect_status(text)
    case.status = sourced_str(status.value, source, confidence)

    # Two-layer classification.
    theories = detect_legal_theories(text, source)
    case.legal_theories = theories
    coverage = detect_coverage_type(theories)
    case.coverage_type = sourced_str(
        coverage.value, source, confidence,
    )

    # Allegations from SCA keywords found.
    for pattern in SCA_KEYWORDS:
        match = pattern.search(text)
        if match:
            case.allegations.append(
                sourced_str(match.group(0), source, confidence)
            )

    return case


# ---------------------------------------------------------------------------
# Deduplication
# ---------------------------------------------------------------------------


def get_case_key(case: CaseDetail) -> str:
    """Get a key for deduplication (case name + filing year).

    Including filing year prevents merging distinct cases with similar
    names (e.g., "In re Apple Inc. Securities Litigation" filed in
    2006 vs 2019 vs 2025 are three different cases).
    """
    parts: list[str] = []
    if case.case_name:
        parts.append(case.case_name.value.lower())
    if case.filing_date:
        # Extract year from filing date
        date_str = str(case.filing_date.value)
        year = date_str[:4] if len(date_str) >= 4 else ""
        if year:
            parts.append(year)
    if not parts:
        if case.court:
            parts.append(case.court.value)
    return " ".join(parts).lower() if parts else ""


def _extract_filing_year(case: CaseDetail) -> int | None:
    """Extract filing year from a CaseDetail."""
    if not case.filing_date:
        return None
    date_str = str(case.filing_date.value)
    try:
        return int(date_str[:4])
    except (ValueError, IndexError):
        return None


def deduplicate_cases(
    efts_cases: list[CaseDetail],
    item3_cases: list[CaseDetail],
    web_cases: list[CaseDetail],
) -> list[CaseDetail]:
    """Deduplicate cases across sources, preferring EFTS data.

    When two cases from different sources have >80% word overlap
    in their case names, they are treated as the same case.
    EFTS data is preferred as the primary record; Item 3 data
    enriches missing fields.
    """
    merged: list[CaseDetail] = list(efts_cases)

    for candidate in item3_cases + web_cases:
        candidate_key = get_case_key(candidate)
        if not candidate_key:
            merged.append(candidate)
            continue

        found_match = False
        for existing in merged:
            existing_key = get_case_key(existing)
            if not existing_key:
                continue
            if word_overlap_pct(candidate_key, existing_key) > 0.80:
                # Check if filing years differ — if so, these are distinct cases
                c_year = _extract_filing_year(candidate)
                e_year = _extract_filing_year(existing)
                if c_year and e_year and abs(c_year - e_year) > 1:
                    continue  # Different filing years = different cases

                # Enrich existing with missing fields from candidate.
                _enrich_case(existing, candidate)
                found_match = True
                break

        if not found_match:
            merged.append(candidate)

    return merged


def _enrich_case(primary: CaseDetail, secondary: CaseDetail) -> None:
    """Enrich primary case with fields from secondary (if missing)."""
    if not primary.court and secondary.court:
        primary.court = secondary.court
    if not primary.filing_date and secondary.filing_date:
        primary.filing_date = secondary.filing_date
    if not primary.settlement_amount and secondary.settlement_amount:
        primary.settlement_amount = secondary.settlement_amount
    if not primary.lead_counsel and secondary.lead_counsel:
        primary.lead_counsel = secondary.lead_counsel
    if not primary.lead_counsel_tier and secondary.lead_counsel_tier:
        primary.lead_counsel_tier = secondary.lead_counsel_tier
    if not primary.case_number and secondary.case_number:
        primary.case_number = secondary.case_number
    # Merge allegations (deduplicated).
    existing_allegations = {a.value for a in primary.allegations}
    for allegation in secondary.allegations:
        if allegation.value not in existing_allegations:
            primary.allegations.append(allegation)
            existing_allegations.add(allegation.value)
    # Merge legal theories.
    existing_theories = {t.value for t in primary.legal_theories}
    for theory in secondary.legal_theories:
        if theory.value not in existing_theories:
            primary.legal_theories.append(theory)
            existing_theories.add(theory.value)


def sanity_check_cases(cases: list[CaseDetail]) -> list[CaseDetail]:
    """Post-dedup sanity checks to catch data quality issues.

    1. Strip LOW confidence settlements from recently filed cases.
       SCA settlements take 3-5 years minimum. A $490M settlement
       on a case filed 9 months ago is a web search hallucination.
    2. Strip SETTLED status from cases filed within 2 years (same reason).
    """
    from datetime import date as _date, timedelta

    cutoff = _date.today() - timedelta(days=730)  # 2 years

    for case in cases:
        if not case.filing_date:
            continue
        filed = case.filing_date.value
        if filed > cutoff:
            # Recently filed — settlement claims are suspect
            if (
                case.settlement_amount
                and case.settlement_amount.confidence.value == "LOW"
            ):
                logger.info(
                    "Sanity check: stripping LOW-confidence settlement ($%.0fM) "
                    "from recently filed case %s (filed %s)",
                    case.settlement_amount.value / 1e6,
                    case.case_name.value if case.case_name else "?",
                    filed,
                )
                case.settlement_amount = None
            if (
                case.status
                and case.status.value == "SETTLED"
                and case.status.confidence.value == "LOW"
            ):
                logger.info(
                    "Sanity check: overriding LOW-confidence SETTLED status "
                    "to PENDING for recently filed case %s",
                    case.case_name.value if case.case_name else "?",
                )
                case.status = SourcedValue[str](
                    value="PENDING",
                    source=case.status.source,
                    confidence=case.status.confidence,
                    as_of=case.status.as_of,
                )

    return cases
