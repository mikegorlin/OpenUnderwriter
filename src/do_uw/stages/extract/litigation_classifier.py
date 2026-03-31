"""Unified post-extraction litigation classifier (Phase 140).

Runs AFTER all individual extractors complete on the fully-populated
LitigationLandscape. Provides four public functions called in order:

1. classify_all_cases -- reclassify by legal theory + filter boilerplate
2. deduplicate_all_cases -- universal dedup across all case lists
3. disambiguate_by_year -- append filing year to case names
4. flag_missing_fields -- queue cases with gaps for ACQUIRE recovery

All functions mutate the landscape in place (no return values).
Does NOT import any ACQUIRE-stage modules (respects pipeline boundary).
"""

from __future__ import annotations

import logging
import re
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    CoverageType,
    LegalTheory,
    LitigationLandscape,
)
from do_uw.stages.extract.sca_extractor import word_overlap_pct
from do_uw.stages.extract.sourced import sourced_str

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEDUP_THRESHOLD = 0.70

CRITICAL_FIELDS = [
    "case_number",
    "court",
    "class_period_start",
    "class_period_end",
    "named_defendants",
]

# Extended theory patterns -- covers all 12 LegalTheory values.
# Securities theories inherited from sca_extractor.THEORY_PATTERNS;
# derivative/regulatory theories added here.
EXTENDED_THEORY_PATTERNS: list[tuple[LegalTheory, re.Pattern[str]]] = [
    # Securities theories
    (LegalTheory.RULE_10B5, re.compile(r"10b-5|Rule\s+10b-5", re.IGNORECASE)),
    (LegalTheory.SECTION_11, re.compile(r"Section\s+11\b", re.IGNORECASE)),
    (LegalTheory.SECTION_14A, re.compile(r"Section\s+14\(a\)", re.IGNORECASE)),
    # Derivative theories
    (
        LegalTheory.DERIVATIVE_DUTY,
        re.compile(
            r"derivative|fiduciary\s+duty|breach\s+of\s+duty|Caremark|oversight",
            re.IGNORECASE,
        ),
    ),
    # Regulatory/enforcement theories
    (LegalTheory.FCPA, re.compile(r"\bFCPA\b|Foreign\s+Corrupt", re.IGNORECASE)),
    (
        LegalTheory.ANTITRUST,
        re.compile(r"\bantitrust\b|Sherman\s+Act", re.IGNORECASE),
    ),
    (LegalTheory.ERISA, re.compile(r"\bERISA\b", re.IGNORECASE)),
    (
        LegalTheory.CYBER_PRIVACY,
        re.compile(r"data\s+breach|cyber|privacy", re.IGNORECASE),
    ),
    (
        LegalTheory.ENVIRONMENTAL,
        re.compile(r"\benvironmental\b|EPA|CERCLA|Superfund", re.IGNORECASE),
    ),
    (
        LegalTheory.PRODUCT_LIABILITY,
        re.compile(r"product\s+liability|recall|mass\s+tort", re.IGNORECASE),
    ),
    (
        LegalTheory.EMPLOYMENT_DISCRIMINATION,
        re.compile(
            r"employment|EEOC|Title\s+VII|discrimination",
            re.IGNORECASE,
        ),
    ),
    (
        LegalTheory.WHISTLEBLOWER,
        re.compile(
            r"whistleblower|qui\s+tam|Dodd-Frank\s+retaliation",
            re.IGNORECASE,
        ),
    ),
]

# Boilerplate labels from llm_litigation._GENERIC_LABELS
_BOILERPLATE_LABELS: set[str] = {
    "legal settlement",
    "unspecified legal matter",
    "shareholder derivative action",
    "general litigation",
    "routine legal proceedings",
    "various legal proceedings",
    "legal proceedings",
    "litigation matters",
    "legal matters",
    "regulatory matters",
    "pending litigation",
    "ordinary course litigation",
}

# Boilerplate patterns from signal_mappers_ext._BOILERPLATE_PATTERNS
_BOILERPLATE_PATTERNS: tuple[str, ...] = (
    "NORMAL COURSE OF BUSINESS",
    "GENERAL LITIGATION AND CLAIMS",
    "ROUTINE LITIGATION",
    "ORDINARY COURSE",
    "SUBJECT TO VARIOUS LEGAL PROCEEDINGS",
    "FROM TIME TO TIME",
    "PARTY TO LEGAL MATTERS",
    "LEGAL MATTERS ARISING",
    "INVOLVED IN LITIGATION",
    "SUBJECT TO CLAIMS",
    "LEGAL PROCEEDINGS AND CLAIMS",
    "INVOLVED IN CERTAIN LEGAL",
    "SUBJECT TO VARIOUS LEGAL",
    "PARTY TO CERTAIN LEGAL",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_all_cases(landscape: LitigationLandscape) -> None:
    """Reclassify all cases by legal theory and filter boilerplate (D-01, D-07).

    Iterates securities_class_actions + derivative_suits. For each case:
    1. Gather text evidence from case_name, allegations, existing theories
    2. Detect theories using EXTENDED_THEORY_PATTERNS
    3. If new detection confidence >= existing, overwrite (Pitfall 3)
    4. Infer coverage_type from theories + named_defendants
    5. Filter boilerplate cases to unclassified_reserves
    """
    boilerplate_cases: list[CaseDetail] = []

    for list_name, case_list in _case_detail_lists(landscape):
        keep: list[CaseDetail] = []
        for case in case_list:
            # Gather text evidence
            text = _gather_evidence_text(case)

            # Detect theories
            new_theories = _detect_theories(text)

            # Boilerplate check: no theories matched AND name is generic
            if not new_theories and _is_boilerplate(case):
                boilerplate_cases.append(case)
                logger.debug(
                    "Classifier: boilerplate filtered: %s",
                    _case_name_str(case),
                )
                continue

            # Overwrite only if new confidence >= existing (Pitfall 3)
            existing_max_conf = _max_confidence(case.legal_theories)
            new_conf = Confidence.MEDIUM  # regex-based detection

            if not case.legal_theories or _conf_rank(new_conf) >= _conf_rank(existing_max_conf):
                if new_theories:
                    case.legal_theories = new_theories
            else:
                # Keep existing higher-confidence theories, but add any
                # new theories not already present
                existing_values = {t.value for t in case.legal_theories}
                for t in new_theories:
                    if t.value not in existing_values:
                        case.legal_theories.append(t)

            # Infer coverage type
            coverage = _infer_coverage_type(
                case.legal_theories, case.named_defendants
            )
            existing_cov_conf = (
                case.coverage_type.confidence
                if case.coverage_type and hasattr(case.coverage_type, "confidence")
                else None
            )
            if existing_cov_conf is None or _conf_rank(new_conf) >= _conf_rank(existing_cov_conf):
                case.coverage_type = sourced_str(
                    coverage.value, "unified_classifier", Confidence.MEDIUM
                )

            keep.append(case)
            logger.debug(
                "Classifier: %s -> theories=%s coverage=%s",
                _case_name_str(case),
                [t.value for t in case.legal_theories],
                coverage.value,
            )

        # Update the list in place
        if list_name == "sca":
            landscape.securities_class_actions = keep
        elif list_name == "derivative":
            landscape.derivative_suits = keep

    # Move boilerplate to unclassified_reserves
    landscape.unclassified_reserves.extend(boilerplate_cases)


def deduplicate_all_cases(landscape: LitigationLandscape) -> None:
    """Deduplicate across all case lists (D-03, D-04).

    Collects all CaseDetail from SCAs + derivatives with origin tag.
    Clusters by case name similarity + filing year. Merges fields
    from secondary into primary (highest confidence wins).
    Redistributes back to appropriate lists.

    MUST run BEFORE disambiguate_by_year (Pitfall 2).
    """
    # Collect all cases with origin tags
    tagged: list[tuple[str, CaseDetail]] = []
    for case in landscape.securities_class_actions:
        tagged.append(("sca", case))
    for case in landscape.derivative_suits:
        tagged.append(("derivative", case))

    if len(tagged) <= 1:
        return

    # Build clusters of similar cases
    used: set[int] = set()
    clusters: list[list[tuple[str, CaseDetail]]] = []

    for i in range(len(tagged)):
        if i in used:
            continue
        cluster = [tagged[i]]
        used.add(i)

        for j in range(i + 1, len(tagged)):
            if j in used:
                continue
            if _are_similar(tagged[i][1], tagged[j][1]):
                cluster.append(tagged[j])
                used.add(j)

        clusters.append(cluster)

    # Merge each cluster into primary
    sca_results: list[CaseDetail] = []
    derivative_results: list[CaseDetail] = []

    for cluster in clusters:
        if len(cluster) == 1:
            origin, case = cluster[0]
            if origin == "sca":
                sca_results.append(case)
            else:
                derivative_results.append(case)
            continue

        # Select primary: highest confidence case_name
        primary_idx = 0
        primary_conf = _case_confidence(cluster[0][1])
        for idx in range(1, len(cluster)):
            conf = _case_confidence(cluster[idx][1])
            if _conf_rank(conf) > _conf_rank(primary_conf):
                primary_idx = idx
                primary_conf = conf

        _primary_origin, primary_case = cluster[primary_idx]

        # Merge all secondaries into primary
        for idx in range(len(cluster)):
            if idx == primary_idx:
                continue
            _origin, secondary = cluster[idx]
            _enrich_case_confidence(primary_case, secondary)

        logger.debug(
            "Dedup: merged %d cases -> %s",
            len(cluster),
            _case_name_str(primary_case),
        )

        # Route to appropriate list based on coverage_type
        if primary_case.coverage_type and "DERIVATIVE" in primary_case.coverage_type.value:
            derivative_results.append(primary_case)
        else:
            sca_results.append(primary_case)

    landscape.securities_class_actions = sca_results
    landscape.derivative_suits = derivative_results


def disambiguate_by_year(landscape: LitigationLandscape) -> None:
    """Append filing year to all case names (D-05).

    Iterates SCAs + derivatives. For each case with a case_name
    that doesn't already end with (YYYY), appends the year from
    filing_date (or class_period_start/end as fallback).
    """
    for _list_name, case_list in _case_detail_lists(landscape):
        for case in case_list:
            _append_year_to_name(case)


def flag_missing_fields(landscape: LitigationLandscape) -> None:
    """Flag cases with missing critical fields for ACQUIRE recovery (D-06).

    Checks case_number, court, class_period_start, class_period_end,
    named_defendants. Cases with gaps get queued in
    landscape.cases_needing_recovery for web search on next run.

    Does NOT make API calls (respects ACQUIRE boundary, Pitfall 4).
    """
    for _list_name, case_list in _case_detail_lists(landscape):
        for case in case_list:
            missing = _find_missing_fields(case)
            if missing:
                recovery_entry: dict[str, Any] = {
                    "case_name": _case_name_str(case),
                    "missing_fields": missing,
                    "source_list": _case_source(case),
                }
                landscape.cases_needing_recovery.append(recovery_entry)
                logger.debug(
                    "Missing fields: %s -> %s",
                    _case_name_str(case),
                    missing,
                )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _case_detail_lists(
    landscape: LitigationLandscape,
) -> list[tuple[str, list[CaseDetail]]]:
    """Return CaseDetail lists with origin tags."""
    return [
        ("sca", landscape.securities_class_actions),
        ("derivative", landscape.derivative_suits),
    ]


def _gather_evidence_text(case: CaseDetail) -> str:
    """Gather all text evidence from a case for theory detection."""
    parts: list[str] = []
    if case.case_name and case.case_name.value:
        parts.append(case.case_name.value)
    for allegation in case.allegations:
        parts.append(allegation.value)
    for theory in case.legal_theories:
        parts.append(theory.value)
    return " ".join(parts)


def _detect_theories(text: str) -> list[SourcedValue[str]]:
    """Detect legal theories using extended patterns."""
    theories: list[SourcedValue[str]] = []
    seen: set[str] = set()
    for theory, pattern in EXTENDED_THEORY_PATTERNS:
        if pattern.search(text) and theory.value not in seen:
            theories.append(
                sourced_str(theory.value, "unified_classifier", Confidence.MEDIUM)
            )
            seen.add(theory.value)
    return theories


def _infer_coverage_type(
    theories: list[SourcedValue[str]],
    named_defendants: list[SourcedValue[str]],
) -> CoverageType:
    """Infer D&O coverage side from theories + defendants."""
    theory_values = {t.value for t in theories}
    has_individual_defendants = len(named_defendants) > 0

    # Derivative cases
    if LegalTheory.DERIVATIVE_DUTY.value in theory_values:
        return (
            CoverageType.DERIVATIVE_SIDE_A
            if has_individual_defendants
            else CoverageType.DERIVATIVE_SIDE_B
        )

    # SEC enforcement / FCPA
    if LegalTheory.FCPA.value in theory_values:
        return (
            CoverageType.SEC_ENFORCEMENT_A
            if has_individual_defendants
            else CoverageType.SEC_ENFORCEMENT_B
        )

    # Securities class actions
    if LegalTheory.SECTION_11.value in theory_values:
        return CoverageType.SCA_SIDE_C
    if LegalTheory.SECTION_14A.value in theory_values:
        return CoverageType.SCA_SIDE_B
    if LegalTheory.RULE_10B5.value in theory_values:
        return (
            CoverageType.SCA_SIDE_A
            if has_individual_defendants
            else CoverageType.SCA_SIDE_C
        )

    # Regulatory / entity coverage
    if LegalTheory.ENVIRONMENTAL.value in theory_values:
        return CoverageType.REGULATORY_ENTITY
    if LegalTheory.EMPLOYMENT_DISCRIMINATION.value in theory_values:
        return CoverageType.EMPLOYMENT_ENTITY
    if LegalTheory.PRODUCT_LIABILITY.value in theory_values:
        return CoverageType.PRODUCT_ENTITY
    if LegalTheory.ANTITRUST.value in theory_values:
        return CoverageType.REGULATORY_ENTITY
    if LegalTheory.ERISA.value in theory_values:
        return CoverageType.REGULATORY_ENTITY
    if LegalTheory.CYBER_PRIVACY.value in theory_values:
        return CoverageType.REGULATORY_ENTITY
    if LegalTheory.WHISTLEBLOWER.value in theory_values:
        return CoverageType.REGULATORY_ENTITY

    # Default
    return (
        CoverageType.SCA_SIDE_A
        if has_individual_defendants
        else CoverageType.REGULATORY_ENTITY
    )


def _is_boilerplate(case: CaseDetail) -> bool:
    """Check if a case is boilerplate (D-07).

    A case is boilerplate if:
    1. Its name matches generic labels OR boilerplate patterns, AND
    2. It does NOT have populated detail fields (Pitfall 5)
    """
    name = _case_name_str(case)
    if not name:
        return True

    name_lower = name.strip().lower()
    name_upper = name.strip().upper()

    is_generic = name_lower in _BOILERPLATE_LABELS
    is_pattern = any(pat in name_upper for pat in _BOILERPLATE_PATTERNS)

    if not is_generic and not is_pattern:
        return False

    # Pitfall 5: If case has detail fields, it's NOT boilerplate
    has_court = case.court is not None and bool(case.court.value.strip())
    has_date = case.filing_date is not None
    has_settlement = case.settlement_amount is not None

    if has_court or has_date or has_settlement:
        return False

    return True


def _case_name_str(case: CaseDetail) -> str:
    """Get case name string safely."""
    if case.case_name and case.case_name.value:
        return case.case_name.value
    return ""


def _case_source(case: CaseDetail) -> str:
    """Get source string from case."""
    if case.case_name and case.case_name.source:
        return case.case_name.source
    return "unknown"


def _max_confidence(
    theories: list[SourcedValue[str]],
) -> Confidence | None:
    """Get highest confidence from a list of SourcedValues."""
    if not theories:
        return None
    best = Confidence.LOW
    for t in theories:
        if _conf_rank(t.confidence) > _conf_rank(best):
            best = t.confidence
    return best


def _conf_rank(conf: Confidence | None) -> int:
    """Rank confidence for comparison."""
    if conf is None:
        return -1
    return {"LOW": 0, "MEDIUM": 1, "HIGH": 2}.get(conf.value, -1)


def _case_confidence(case: CaseDetail) -> Confidence:
    """Get the confidence of a case's primary identifier (case_name)."""
    if case.case_name and hasattr(case.case_name, "confidence"):
        return case.case_name.confidence
    return Confidence.LOW


def _are_similar(case_a: CaseDetail, case_b: CaseDetail) -> bool:
    """Check if two cases are similar enough to be duplicates."""
    name_a = _case_name_str(case_a)
    name_b = _case_name_str(case_b)
    if not name_a or not name_b:
        return False

    # Word overlap check
    overlap = word_overlap_pct(name_a, name_b)
    if overlap < DEDUP_THRESHOLD:
        return False

    # Filing year check: >1 year apart = different cases
    year_a = _extract_year(case_a)
    year_b = _extract_year(case_b)
    if year_a and year_b and abs(year_a - year_b) > 1:
        return False

    return True


def _enrich_case_confidence(
    primary: CaseDetail, secondary: CaseDetail
) -> None:
    """Enrich primary with fields from secondary, highest confidence wins (D-04)."""
    # For each field, keep highest confidence
    if secondary.court and (
        not primary.court
        or _conf_rank(secondary.court.confidence) > _conf_rank(primary.court.confidence)
    ):
        primary.court = secondary.court

    if secondary.case_number and (
        not primary.case_number
        or _conf_rank(secondary.case_number.confidence)
        > _conf_rank(primary.case_number.confidence)
    ):
        primary.case_number = secondary.case_number

    if secondary.filing_date and (
        not primary.filing_date
        or _conf_rank(secondary.filing_date.confidence)
        > _conf_rank(primary.filing_date.confidence)
    ):
        primary.filing_date = secondary.filing_date

    if secondary.settlement_amount and (
        not primary.settlement_amount
        or _conf_rank(secondary.settlement_amount.confidence)
        > _conf_rank(primary.settlement_amount.confidence)
    ):
        primary.settlement_amount = secondary.settlement_amount

    if secondary.lead_counsel and (
        not primary.lead_counsel
        or _conf_rank(secondary.lead_counsel.confidence)
        > _conf_rank(primary.lead_counsel.confidence)
    ):
        primary.lead_counsel = secondary.lead_counsel

    if secondary.status and (
        not primary.status
        or _conf_rank(secondary.status.confidence) > _conf_rank(primary.status.confidence)
    ):
        primary.status = secondary.status

    if secondary.case_name and (
        not primary.case_name
        or _conf_rank(secondary.case_name.confidence) > _conf_rank(primary.case_name.confidence)
    ):
        primary.case_name = secondary.case_name

    # Merge allegations
    existing_allegations = {a.value for a in primary.allegations}
    for allegation in secondary.allegations:
        if allegation.value not in existing_allegations:
            primary.allegations.append(allegation)
            existing_allegations.add(allegation.value)

    # Merge legal theories
    existing_theories = {t.value for t in primary.legal_theories}
    for theory in secondary.legal_theories:
        if theory.value not in existing_theories:
            primary.legal_theories.append(theory)
            existing_theories.add(theory.value)

    # Merge named defendants
    existing_defendants = {d.value for d in primary.named_defendants}
    for defendant in secondary.named_defendants:
        if defendant.value not in existing_defendants:
            primary.named_defendants.append(defendant)
            existing_defendants.add(defendant.value)


def _append_year_to_name(case: CaseDetail) -> None:
    """Append filing year to case name per D-05."""
    if not case.case_name or not case.case_name.value:
        return

    name = case.case_name.value
    # Don't double-add year if already present
    if re.search(r"\(\d{4}\)\s*$", name):
        return

    year = _extract_year(case)
    if year:
        case.case_name = SourcedValue[str](
            value=f"{name} ({year})",
            source=case.case_name.source,
            confidence=case.case_name.confidence,
            as_of=case.case_name.as_of,
        )


def _extract_year(case: CaseDetail) -> int | None:
    """Extract year from filing_date, class_period_start, or class_period_end."""
    if case.filing_date:
        return case.filing_date.value.year
    if case.class_period_start:
        return case.class_period_start.value.year
    if case.class_period_end:
        return case.class_period_end.value.year
    return None


def _find_missing_fields(case: CaseDetail) -> list[str]:
    """Check which critical fields are missing."""
    missing: list[str] = []
    if not case.case_number or not case.case_number.value.strip():
        missing.append("case_number")
    if not case.court or not case.court.value.strip():
        missing.append("court")
    if not case.class_period_start:
        missing.append("class_period_start")
    if not case.class_period_end:
        missing.append("class_period_end")
    if not case.named_defendants:
        missing.append("named_defendants")
    return missing
