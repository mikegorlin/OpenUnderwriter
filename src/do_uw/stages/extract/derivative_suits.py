"""Derivative suit and fiduciary claim extraction from 10-K and web.

Extracts shareholder derivative lawsuits, Section 220 books-and-records
demands, and Caremark/fiduciary duty claims from 10-K Item 3 and web
search results.

Covers SECT6-05 for D&O underwriting.

Usage:
    cases, report = extract_derivative_suits(state)
    state.extracted.litigation.derivative_suits = cases
"""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    CaseStatus,
    CoverageType,
    LegalTheory,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.filing_sections import SECTION_DEFS, extract_section
from do_uw.stages.extract.sourced import (
    get_filing_document_text,
    sourced_str,
)
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIME_HORIZON_DAYS = 1825  # 5 years for derivative suits

EXPECTED_FIELDS: list[str] = [
    "case_name",
    "court",
    "filing_date",
    "allegations",
    "status",
    "coverage_type",
    "section_220_demands",
]

# Derivative suit detection patterns.
DERIVATIVE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(
        r"derivative\s+(?:action|suit|complaint|claim|litigation)",
        re.IGNORECASE,
    ),
    re.compile(
        r"[Ss]ection\s+220\s+(?:books?\s+and\s+records?|demand)",
        re.IGNORECASE,
    ),
    re.compile(
        r"[Cc]aremark|oversight\s+duty|fiduciary\s+duty\s+(?:claim|breach)",
        re.IGNORECASE,
    ),
    re.compile(
        r"demand\s+(?:refusal|futility|refused|rejected)",
        re.IGNORECASE,
    ),
    re.compile(
        r"Court\s+of\s+Chancery|Delaware\s+(?:Chancery|court)",
        re.IGNORECASE,
    ),
]

# Section 220 specific pattern.
SECTION_220_RE = re.compile(
    r"[Ss]ection\s+220\s+(?:books?\s+and\s+records?|demand"
    r"|inspection\s+right)",
    re.IGNORECASE,
)

# Caremark claim pattern.
CAREMARK_RE = re.compile(
    r"[Cc]aremark|oversight\s+(?:duty|claim|liability)",
    re.IGNORECASE,
)

# Court detection (derivative suits often in Delaware).
COURT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("Delaware Court of Chancery", re.compile(
        r"Court\s+of\s+Chancery|Delaware\s+Chancery",
        re.IGNORECASE,
    )),
    ("D. Del.", re.compile(
        r"D\.\s*Del\.|District\s+of\s+Delaware",
        re.IGNORECASE,
    )),
    ("S.D.N.Y.", re.compile(
        r"S\.D\.N\.Y\.|Southern\s+District.*New\s+York",
        re.IGNORECASE,
    )),
    ("N.D. Cal.", re.compile(
        r"N\.D\.\s*Cal\.|Northern\s+District.*California",
        re.IGNORECASE,
    )),
    ("C.D. Cal.", re.compile(
        r"C\.D\.\s*Cal\.|Central\s+District.*California",
        re.IGNORECASE,
    )),
]

# Case name pattern (derivative cases).
DERIV_CASE_NAME_RE = re.compile(
    r"(?:In\s+re\s+.+?(?:Derivative|Stockholder|Shareholder))"
    r"|(?:\w+\s+v\.\s+.+?)(?:\s*,|\s*$|\s*\.)",
    re.IGNORECASE,
)

# Status keyword patterns.
STATUS_KEYWORDS: dict[CaseStatus, list[str]] = {
    CaseStatus.DISMISSED: ["dismissed", "dismissal"],
    CaseStatus.SETTLED: ["settled", "settlement"],
    CaseStatus.ACTIVE: ["pending", "active", "ongoing"],
    CaseStatus.APPEAL: ["appeal", "appellate"],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_derivative_reference(text: str) -> bool:
    """Check if text contains derivative suit keywords."""
    return any(pattern.search(text) for pattern in DERIVATIVE_PATTERNS)


def _detect_status(text: str) -> CaseStatus:
    """Detect case status from text keywords."""
    text_lower = text.lower()
    for status, keywords in STATUS_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return status
    return CaseStatus.UNKNOWN


def _extract_court(text: str) -> str | None:
    """Extract court from text."""
    for court_name, pattern in COURT_PATTERNS:
        if pattern.search(text):
            return court_name
    return None


def _extract_case_name(text: str) -> str | None:
    """Extract derivative case name from text."""
    match = DERIV_CASE_NAME_RE.search(text)
    if match:
        name = match.group(0).strip().rstrip(",.")
        if len(name) > 10:
            return name[:200]
    return None


def _is_within_horizon(filing_date: date | None) -> bool:
    """Check if a case is within the 5-year time horizon."""
    if filing_date is None:
        return True
    cutoff = date.today() - timedelta(days=TIME_HORIZON_DAYS)
    return filing_date >= cutoff


def _determine_coverage_type(text: str) -> CoverageType:
    """Determine derivative coverage type from context."""
    text_lower = text.lower()
    # Side A: individual directors/officers named.
    if any(kw in text_lower for kw in [
        "individual capacity", "individual defendant",
        "director defendant", "officer defendant",
    ]):
        return CoverageType.DERIVATIVE_SIDE_A
    # Default to Side B for derivative suits.
    return CoverageType.DERIVATIVE_SIDE_B


def _detect_theories(
    text: str, source: str,
) -> list[SourcedValue[str]]:
    """Detect legal theories applicable to derivative suits."""
    theories: list[SourcedValue[str]] = []
    seen: set[str] = set()

    # Always add DERIVATIVE_DUTY for derivative suits.
    theories.append(
        sourced_str(
            LegalTheory.DERIVATIVE_DUTY.value,
            source, Confidence.MEDIUM,
        )
    )
    seen.add(LegalTheory.DERIVATIVE_DUTY.value)

    # Check for additional theories.
    theory_checks: list[tuple[LegalTheory, re.Pattern[str]]] = [
        (LegalTheory.ERISA, re.compile(r"\bERISA\b", re.IGNORECASE)),
        (LegalTheory.FCPA, re.compile(
            r"\bFCPA\b|Foreign\s+Corrupt", re.IGNORECASE,
        )),
        (LegalTheory.ANTITRUST, re.compile(
            r"\bantitrust\b|Sherman\s+Act", re.IGNORECASE,
        )),
        (LegalTheory.CYBER_PRIVACY, re.compile(
            r"data\s+breach|cyber|privacy", re.IGNORECASE,
        )),
    ]
    for theory, pattern in theory_checks:
        if pattern.search(text) and theory.value not in seen:
            theories.append(
                sourced_str(theory.value, source, Confidence.MEDIUM)
            )
            seen.add(theory.value)

    return theories


def _word_overlap_pct(text_a: str, text_b: str) -> float:
    """Compute word overlap percentage for deduplication."""
    words_a = set(re.findall(r"\w+", text_a.lower()))
    words_b = set(re.findall(r"\w+", text_b.lower()))
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


# ---------------------------------------------------------------------------
# Source parsers
# ---------------------------------------------------------------------------


def _parse_item3(state: AnalysisState) -> list[CaseDetail]:
    """Parse 10-K Item 3 for derivative suit mentions."""
    full_text = get_filing_document_text(state, "10-K")
    if not full_text:
        return []

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

    paragraphs = re.split(r"\n\s*\n", item3_text)
    for para in paragraphs:
        if not _is_derivative_reference(para):
            continue

        case = _build_case(para, source, Confidence.MEDIUM)
        if case.filing_date and not _is_within_horizon(
            case.filing_date.value,
        ):
            continue
        cases.append(case)

    return cases


def _parse_web_results(state: AnalysisState) -> list[CaseDetail]:
    """Parse web search results for derivative suit mentions."""
    if state.acquired_data is None:
        return []

    cases: list[CaseDetail] = []
    source = "web search"

    all_texts: list[str] = []

    web_results = state.acquired_data.litigation_data.get("web_results")
    if isinstance(web_results, list):
        for r in cast(list[Any], web_results):
            all_texts.append(str(r))

    blind = state.acquired_data.blind_spot_results
    if blind:
        for _key, val in blind.items():
            if isinstance(val, str):
                all_texts.append(val)
            elif isinstance(val, list):
                for item in cast(list[Any], val):
                    all_texts.append(str(item))

    for text in all_texts:
        if not _is_derivative_reference(text):
            continue
        case = _build_case(text, source, Confidence.LOW)
        if case.filing_date and not _is_within_horizon(
            case.filing_date.value,
        ):
            continue
        cases.append(case)

    return cases


def _build_case(
    text: str, source: str, confidence: Confidence,
) -> CaseDetail:
    """Build a CaseDetail from derivative suit text."""
    case = CaseDetail()

    case_name = _extract_case_name(text)
    if case_name:
        case.case_name = sourced_str(case_name, source, confidence)

    court = _extract_court(text)
    if court:
        case.court = sourced_str(court, source, confidence)

    status = _detect_status(text)
    case.status = sourced_str(status.value, source, confidence)

    coverage = _determine_coverage_type(text)
    case.coverage_type = sourced_str(
        coverage.value, source, confidence,
    )

    theories = _detect_theories(text, source)
    case.legal_theories = theories

    # Section 220 demand detection.
    if SECTION_220_RE.search(text):
        case.key_rulings.append(
            sourced_str(
                "Section 220 books-and-records demand",
                source, confidence,
            )
        )

    # Caremark detection.
    if CAREMARK_RE.search(text):
        case.allegations.append(
            sourced_str("Caremark oversight claim", source, confidence)
        )

    # General derivative allegation.
    if re.search(r"derivative\s+(?:action|suit)", text, re.IGNORECASE):
        case.allegations.append(
            sourced_str("Shareholder derivative action", source, confidence)
        )

    return case


def _deduplicate(
    item3_cases: list[CaseDetail],
    web_cases: list[CaseDetail],
) -> list[CaseDetail]:
    """Deduplicate derivative suit cases, preferring Item 3 data."""
    merged: list[CaseDetail] = list(item3_cases)

    for candidate in web_cases:
        candidate_name = (
            candidate.case_name.value.lower()
            if candidate.case_name else ""
        )
        if not candidate_name:
            merged.append(candidate)
            continue

        found = False
        for existing in merged:
            existing_name = (
                existing.case_name.value.lower()
                if existing.case_name else ""
            )
            if existing_name and _word_overlap_pct(
                candidate_name, existing_name,
            ) > 0.80:
                found = True
                break

        if not found:
            merged.append(candidate)

    return merged


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def extract_derivative_suits(
    state: AnalysisState,
) -> tuple[list[CaseDetail], ExtractionReport]:
    """Extract derivative suits and fiduciary claims.

    Searches 10-K Item 3 and web results for derivative actions,
    Section 220 demands, and Caremark claims. Deduplicates across
    sources with Item 3 preferred.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (list of CaseDetail, ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    source_filing = "10-K Item 3 + web search"

    item3_cases = _parse_item3(state)
    web_cases = _parse_web_results(state)

    cases = _deduplicate(item3_cases, web_cases)

    # Track section 220 demands separately.
    section_220_count = sum(
        1 for c in cases
        if any(
            "Section 220" in kr.value
            for kr in c.key_rulings
        )
    )

    # Track found fields.
    for case in cases:
        if case.case_name:
            found.append("case_name")
        if case.court:
            found.append("court")
        if case.filing_date:
            found.append("filing_date")
        if case.allegations:
            found.append("allegations")
        if case.status:
            found.append("status")
        if case.coverage_type:
            found.append("coverage_type")

    if section_220_count > 0:
        found.append("section_220_demands")

    found = sorted(set(found))

    if not cases:
        warnings.append("No derivative suits found")

    report = create_report(
        extractor_name="derivative_suits",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        warnings=warnings,
    )
    log_report(report)

    return cases, report
