"""Litigation converter: TenKExtraction -> LitigationLandscape sub-models.

Maps flat LLM-extracted 10-K fields into rich domain models consumed by
the scoring engine and worksheet renderer. Also handles cross-domain
DEF 14A forum provision mapping.

Public functions:
- convert_legal_proceedings  -> list[CaseDetail]
- convert_contingencies      -> list[ContingentLiability]
- convert_risk_factors       -> list[RiskFactorProfile]
- convert_forum_provisions   -> ForumProvisions

Private helpers:
- _parse_date        -> date | None
- _infer_legal_theories -> list[str]
- _infer_coverage_type  -> str
"""

from __future__ import annotations

import logging
from datetime import date, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import CaseDetail
from do_uw.models.litigation_details import ContingentLiability, ForumProvisions
from do_uw.models.state import RiskFactorProfile
from do_uw.stages.extract.llm.schemas.common import (
    ExtractedContingency,
    ExtractedLegalProceeding,
    ExtractedRiskFactor,
)
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.sourced import (
    now,
    sourced_float,
    sourced_str,
)

logger = logging.getLogger(__name__)

_LLM_SOURCE = "10-K (LLM)"
_DEF14A_SOURCE = "DEF 14A (LLM)"

# ---------------------------------------------------------------------------
# Generic label set -- case names that indicate boilerplate, not real cases
# ---------------------------------------------------------------------------

_GENERIC_LABELS = {
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


def _is_generic_label(name: str) -> bool:
    """True if case name is a generic label, not a real case name."""
    return name.strip().lower() in _GENERIC_LABELS


def _meets_minimum_evidence(proc: ExtractedLegalProceeding) -> bool:
    """Check if a legal proceeding has enough specifics to be a real case.

    Minimum evidence per user decision:
    - Named parties (plaintiff name or 'class of shareholders') AND
    - Court/jurisdiction AND
    - Approximate filing date

    Borderline (named parties but missing court/date) returns True
    but should be flagged as LOW confidence by caller.
    """
    has_named_parties = bool(
        proc.case_name
        and proc.case_name.strip()
        and not _is_generic_label(proc.case_name)
    )
    has_court = bool(proc.court and proc.court.strip())
    has_filing_date = bool(proc.filing_date and proc.filing_date.strip())

    # Must at least have named parties to be considered
    if not has_named_parties:
        return False

    # Named parties + (court OR filing_date) = sufficient evidence
    return has_court or has_filing_date


def _is_borderline_evidence(proc: ExtractedLegalProceeding) -> bool:
    """True if proceeding has some specifics but is missing court/docket.

    Borderline = named parties present but NEITHER court NOR filing_date.
    Per user decision, these are kept at LOW confidence, not dropped.
    """
    has_named_parties = bool(
        proc.case_name
        and proc.case_name.strip()
        and not _is_generic_label(proc.case_name)
    )
    has_court = bool(proc.court and proc.court.strip())
    has_filing_date = bool(proc.filing_date and proc.filing_date.strip())
    return has_named_parties and not has_court and not has_filing_date

# ---------------------------------------------------------------------------
# Legal theory keyword mapping (case-insensitive)
# ---------------------------------------------------------------------------

_THEORY_KEYWORDS: dict[str, list[str]] = {
    "RULE_10B5": ["10b-5", "10(b)", "rule 10b"],
    "SECTION_11": ["section 11"],
    "SECTION_14A": ["section 14"],
    "ERISA": ["erisa"],
    "ANTITRUST": ["antitrust", "anti-trust", "sherman act", "clayton act"],
    "FCPA": ["fcpa", "foreign corrupt"],
    "PRODUCT_LIABILITY": ["product liability"],
    "CYBER_PRIVACY": ["cyber", "data breach", "privacy"],
    "DERIVATIVE_DUTY": ["derivative", "fiduciary duty", "breach of duty"],
    "EMPLOYMENT_DISCRIMINATION": [
        "employment discrimination",
        "title vii",
        "ada",
        "adea",
    ],
    "ENVIRONMENTAL": ["environmental", "cercla", "clean air", "clean water"],
    "WHISTLEBLOWER": ["whistleblower", "qui tam", "false claims"],
}

# D&O relevance mapping: category -> do_relevance
_DO_RELEVANCE: dict[str, str] = {
    "LITIGATION": "HIGH",
    "REGULATORY": "HIGH",
    "FINANCIAL": "MEDIUM",
    "CYBER": "MEDIUM",
    "OPERATIONAL": "LOW",
    "ESG": "LOW",
    "AI": "LOW",
    "OTHER": "LOW",
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_date(date_str: str | None) -> date | None:
    """Parse 'YYYY-MM-DD' string to a date object.

    Returns None on parse failure or None/empty input.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        logger.debug("Failed to parse date: %s", date_str)
        return None


def _sourced_date(
    d: date, source: str, confidence: Confidence = Confidence.HIGH
) -> SourcedValue[date]:
    """Create a SourcedValue[date] with current timestamp."""
    return SourcedValue[date](
        value=d, source=source, confidence=confidence, as_of=now()
    )


def _sourced_bool(
    value: bool, source: str, confidence: Confidence = Confidence.HIGH
) -> SourcedValue[bool]:
    """Create a SourcedValue[bool] with current timestamp."""
    return SourcedValue[bool](
        value=value, source=source, confidence=confidence, as_of=now()
    )


def _infer_legal_theories(text: str) -> list[str]:
    """Infer legal theories from allegation/case text via keyword matching.

    Case-insensitive. Returns a deduplicated list of theory string values
    matching ``LegalTheory`` enum members.
    """
    if not text:
        return []
    lower = text.lower()
    theories: list[str] = []
    for theory, keywords in _THEORY_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                theories.append(theory)
                break  # One match per theory is enough
    return theories


def _infer_coverage_type(theories: list[str]) -> str:
    """Infer D&O coverage type from legal theories.

    Priority:
    1. Securities theories -> SCA_SIDE_C
    2. Derivative duty -> DERIVATIVE_SIDE_A
    3. ERISA / employment -> EMPLOYMENT_ENTITY
    4. Product liability -> PRODUCT_ENTITY
    5. Default -> REGULATORY_ENTITY
    """
    securities = {"RULE_10B5", "SECTION_11", "SECTION_14A"}
    if securities.intersection(theories):
        return "SCA_SIDE_C"
    if "DERIVATIVE_DUTY" in theories:
        return "DERIVATIVE_SIDE_A"
    if "ERISA" in theories or "EMPLOYMENT_DISCRIMINATION" in theories:
        return "EMPLOYMENT_ENTITY"
    if "PRODUCT_LIABILITY" in theories:
        return "PRODUCT_ENTITY"
    # Default to COMMERCIAL_ENTITY, not REGULATORY_ENTITY.
    # REGULATORY_ENTITY triggers filtering in signal_mappers which drops
    # legitimate litigation (antitrust class actions, merchant suits, etc.)
    return "COMMERCIAL_ENTITY"


# ---------------------------------------------------------------------------
# Public converters
# ---------------------------------------------------------------------------


def convert_legal_proceedings(
    extraction: TenKExtraction,
) -> list[CaseDetail]:
    """Convert TenKExtraction.legal_proceedings to CaseDetail list.

    Skips proceedings that fail minimum evidence check (no named parties
    or generic labels). Downgrades confidence to LOW for borderline cases
    (named parties but missing court/docket).
    """
    results: list[CaseDetail] = []
    dropped = 0
    for proc in extraction.legal_proceedings:
        if not proc.case_name or not proc.case_name.strip():
            dropped += 1
            continue
        # Borderline cases (named parties but no court/date) are kept
        # at LOW confidence per user decision -- check before dropping
        if _is_borderline_evidence(proc):
            logger.info(
                "LIT: Borderline evidence for %s — keeping at LOW confidence",
                proc.case_name[:80],
            )
            detail = _convert_one_proceeding(proc, confidence=Confidence.LOW)
            results.append(detail)
            continue
        if not _meets_minimum_evidence(proc):
            logger.info(
                "LIT: Dropping hollow legal proceeding: %s (insufficient evidence)",
                proc.case_name[:80],
            )
            dropped += 1
            continue
        detail = _convert_one_proceeding(proc)
        results.append(detail)
    if dropped:
        logger.info("LIT: Dropped %d hollow/boilerplate legal proceedings", dropped)
    return results


def _convert_one_proceeding(
    proc: ExtractedLegalProceeding,
    confidence: Confidence = Confidence.HIGH,
) -> CaseDetail:
    """Map a single ExtractedLegalProceeding to CaseDetail."""
    # Infer theories from allegations, case_name, and explicit field
    theory_text = " ".join(
        filter(None, [proc.allegations, proc.case_name])
    )
    theories_from_text = _infer_legal_theories(theory_text)
    # Also include any explicitly listed legal theories from the schema
    all_theories = list(dict.fromkeys(theories_from_text + proc.legal_theories))

    coverage = _infer_coverage_type(all_theories)

    # Build SourcedValue lists
    allegations_list: list[SourcedValue[str]] = []
    if proc.allegations:
        allegations_list.append(
            sourced_str(proc.allegations, _LLM_SOURCE, confidence)
        )

    legal_theory_svs = [
        sourced_str(t, _LLM_SOURCE, confidence) for t in all_theories
    ]

    named_defendant_svs = [
        sourced_str(d, _LLM_SOURCE, confidence)
        for d in proc.named_defendants
        if d.strip()
    ]

    # Parse dates
    filing_date_val = _parse_date(proc.filing_date)
    class_start_val = _parse_date(proc.class_period_start)
    class_end_val = _parse_date(proc.class_period_end)

    return CaseDetail(
        case_name=sourced_str(proc.case_name, _LLM_SOURCE, confidence),
        court=(
            sourced_str(proc.court, _LLM_SOURCE, confidence)
            if proc.court
            else None
        ),
        filing_date=(
            _sourced_date(filing_date_val, _LLM_SOURCE, confidence)
            if filing_date_val
            else None
        ),
        allegations=allegations_list,
        status=(
            sourced_str(proc.status, _LLM_SOURCE, confidence)
            if proc.status
            else None
        ),
        settlement_amount=(
            sourced_float(proc.settlement_amount, _LLM_SOURCE, confidence)
            if proc.settlement_amount is not None
            else None
        ),
        class_period_start=(
            _sourced_date(class_start_val, _LLM_SOURCE, confidence)
            if class_start_val
            else None
        ),
        class_period_end=(
            _sourced_date(class_end_val, _LLM_SOURCE, confidence)
            if class_end_val
            else None
        ),
        named_defendants=named_defendant_svs,
        legal_theories=legal_theory_svs,
        coverage_type=sourced_str(coverage, _LLM_SOURCE, confidence),
    )


def convert_contingencies(
    extraction: TenKExtraction,
) -> list[ContingentLiability]:
    """Convert TenKExtraction.contingent_liabilities to domain models.

    Skips entries with empty description. Maps ExtractedContingency
    fields to ContingentLiability with full source attribution.
    """
    results: list[ContingentLiability] = []
    for c in extraction.contingent_liabilities:
        if not c.description or not c.description.strip():
            continue
        liability = _convert_one_contingency(c)
        results.append(liability)
    return results


def _convert_one_contingency(c: ExtractedContingency) -> ContingentLiability:
    """Map a single ExtractedContingency to ContingentLiability."""
    return ContingentLiability(
        description=sourced_str(c.description, _LLM_SOURCE, Confidence.HIGH),
        contingency_type=(
            sourced_str(c.contingency_type, _LLM_SOURCE, Confidence.HIGH)
            if c.contingency_type
            else None
        ),
        asc_450_classification=(
            sourced_str(c.classification, _LLM_SOURCE, Confidence.HIGH)
            if c.classification
            else None
        ),
        accrued_amount=(
            sourced_float(c.accrued_amount, _LLM_SOURCE, Confidence.HIGH)
            if c.accrued_amount is not None
            else None
        ),
        range_low=(
            sourced_float(c.range_low, _LLM_SOURCE, Confidence.HIGH)
            if c.range_low is not None
            else None
        ),
        range_high=(
            sourced_float(c.range_high, _LLM_SOURCE, Confidence.HIGH)
            if c.range_high is not None
            else None
        ),
        source_note=(
            sourced_str(c.source_passage, _LLM_SOURCE, Confidence.HIGH)
            if c.source_passage
            else None
        ),
    )


def convert_risk_factors(
    extraction: TenKExtraction,
) -> list[RiskFactorProfile]:
    """Convert TenKExtraction.risk_factors to RiskFactorProfile list.

    Skips entries with empty title. Infers D&O relevance from category:
    LITIGATION/REGULATORY -> HIGH, FINANCIAL/CYBER -> MEDIUM, else LOW.
    """
    results: list[RiskFactorProfile] = []
    for rf in extraction.risk_factors:
        if not rf.title or not rf.title.strip():
            continue
        profile = _convert_one_risk_factor(rf)
        results.append(profile)
    return results


def _convert_one_risk_factor(rf: ExtractedRiskFactor) -> RiskFactorProfile:
    """Map a single ExtractedRiskFactor to RiskFactorProfile."""
    do_relevance = _DO_RELEVANCE.get(rf.category.upper(), "LOW")
    return RiskFactorProfile(
        title=rf.title,
        category=rf.category,
        severity=rf.severity,
        is_new_this_year=rf.is_new_this_year,
        do_relevance=do_relevance,
        source_passage=rf.source_passage,
        source=_LLM_SOURCE,
    )


def convert_forum_provisions(
    extraction: DEF14AExtraction,
) -> ForumProvisions:
    """Convert DEF 14A forum/exclusive forum fields to ForumProvisions.

    Cross-domain: DEF 14A proxy data populating a litigation defense model.
    Maps exclusive_forum_provision (bool) and forum_selection_clause (str)
    to the ForumProvisions model with DEF 14A source attribution.
    """
    has_exclusive: SourcedValue[bool] | None = None
    if extraction.exclusive_forum_provision is not None:
        has_exclusive = _sourced_bool(
            extraction.exclusive_forum_provision,
            _DEF14A_SOURCE,
            Confidence.HIGH,
        )

    exclusive_details: SourcedValue[str] | None = None
    if extraction.forum_selection_clause:
        exclusive_details = sourced_str(
            extraction.forum_selection_clause,
            _DEF14A_SOURCE,
            Confidence.HIGH,
        )

    return ForumProvisions(
        has_exclusive_forum=has_exclusive,
        exclusive_forum_details=exclusive_details,
        source_document=sourced_str(
            "DEF 14A proxy statement", _DEF14A_SOURCE, Confidence.HIGH
        ),
    )
