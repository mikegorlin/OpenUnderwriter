"""Securities class action (SCA) extractor from EFTS/SCAC, 10-K, and web.

Extracts securities class action lawsuits from three data sources in
priority order:
1. EFTS sec_references (primary -- closest proxy for Stanford SCAC)
2. 10-K Item 3 Legal Proceedings (supplement -- company characterization)
3. Web search / blind spot results (low confidence)

Two-layer classification: coverage_type (CoverageType) + legal_theories
(LegalTheory). Lead counsel tier lookup via lead_counsel_tiers.json.

Covers SECT6-03 for D&O underwriting.

Usage:
    cases, report = extract_securities_class_actions(state)
    state.extracted.litigation.securities_class_actions = cases
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, cast

from do_uw.brain.brain_unified_loader import load_config
from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation import (
    CaseDetail,
    CaseStatus,
    CoverageType,
    LegalTheory,
)
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import sourced_str
from do_uw.stages.extract.validation import (
    ExtractionReport,
    create_report,
    log_report,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TIME_HORIZON_DAYS = 3650  # 10 years

EXPECTED_FIELDS: list[str] = [
    "case_name",
    "case_number",
    "court",
    "filing_date",
    "allegations",
    "status",
    "lead_counsel",
    "coverage_type",
    "legal_theories",
    "settlement_amount",
]

# SCA keyword patterns for EFTS reference parsing.
SCA_KEYWORDS: list[re.Pattern[str]] = [
    re.compile(r"class\s+action", re.IGNORECASE),
    re.compile(r"securities\s+(?:fraud|class\s+action|litigation)", re.IGNORECASE),
    re.compile(r"10b-5|Rule\s+10b-5", re.IGNORECASE),
    re.compile(r"Section\s+11\b", re.IGNORECASE),
    re.compile(r"Section\s+14\(a\)", re.IGNORECASE),
]

# Case name pattern.
CASE_NAME_RE = re.compile(
    r"In\s+re\s+.+?(?:Securities|Litigation|Sec\.\s+Lit\.)",
    re.IGNORECASE,
)

# Court pattern.
COURT_RE = re.compile(
    r"(S\.D\.N\.Y\.|N\.D\.\s*Cal\.|D\.\s*Del\.|C\.D\.\s*Cal\.)",
)

# Filing date pattern.
FILING_DATE_RE = re.compile(
    r"(?:filed|commenced|initiated)\s+(?:on\s+)?"
    r"(\w+\s+\d+,\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})",
    re.IGNORECASE,
)

# Settlement amount pattern.
SETTLEMENT_RE = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)",
    re.IGNORECASE,
)

# Status keyword patterns.
STATUS_KEYWORDS: dict[CaseStatus, list[str]] = {
    CaseStatus.DISMISSED: ["dismissed", "dismissal"],
    CaseStatus.SETTLED: ["settled", "settlement"],
    CaseStatus.ACTIVE: ["pending", "active", "ongoing"],
    CaseStatus.APPEAL: ["appeal", "appellate"],
}

# Legal theory detection patterns.
THEORY_PATTERNS: list[tuple[LegalTheory, re.Pattern[str]]] = [
    (LegalTheory.RULE_10B5, re.compile(r"10b-5|Rule\s+10b-5", re.IGNORECASE)),
    (LegalTheory.SECTION_11, re.compile(r"Section\s+11\b", re.IGNORECASE)),
    (LegalTheory.SECTION_14A, re.compile(r"Section\s+14\(a\)", re.IGNORECASE)),
    (LegalTheory.ERISA, re.compile(r"\bERISA\b", re.IGNORECASE)),
    (LegalTheory.FCPA, re.compile(r"\bFCPA\b|Foreign\s+Corrupt", re.IGNORECASE)),
    (
        LegalTheory.ANTITRUST,
        re.compile(r"\bantitrust\b|Sherman\s+Act", re.IGNORECASE),
    ),
    (
        LegalTheory.CYBER_PRIVACY,
        re.compile(r"data\s+breach|cyber|privacy", re.IGNORECASE),
    ),
]


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------


def load_lead_counsel_tiers() -> dict[str, Any]:
    """Load lead counsel tier configuration.

    Returns:
        Dict with tier_1, tier_2 lists and match_strategy.
    """
    data = load_config("lead_counsel_tiers")
    if not data:
        return {"tier_1": [], "tier_2": [], "tier_3_default": True}
    return data


def lookup_counsel_tier(
    counsel_name: str, tiers: dict[str, Any],
) -> int:
    """Look up lead counsel tier using substring matching.

    Args:
        counsel_name: Name of the law firm.
        tiers: Config dict from lead_counsel_tiers.json.

    Returns:
        Tier number: 1, 2, or 3 (default).
    """
    counsel_lower = counsel_name.lower()
    tier_1 = cast(list[str], tiers.get("tier_1", []))
    for firm in tier_1:
        if firm.lower() in counsel_lower:
            return 1
    tier_2 = cast(list[str], tiers.get("tier_2", []))
    for firm in tier_2:
        if firm.lower() in counsel_lower:
            return 2
    return 3


# ---------------------------------------------------------------------------
# Parsing helpers (used by sca_parsing.py)
# ---------------------------------------------------------------------------


def is_sca_reference(text: str) -> bool:
    """Check if text contains SCA keywords."""
    return any(pattern.search(text) for pattern in SCA_KEYWORDS)


def extract_case_name(text: str) -> str | None:
    """Extract case name from text."""
    match = CASE_NAME_RE.search(text)
    return match.group(0).strip() if match else None


def extract_court(text: str) -> str | None:
    """Extract court from text."""
    match = COURT_RE.search(text)
    return match.group(1).strip() if match else None


def parse_date_str(date_str: str) -> date | None:
    """Parse a date string in various formats."""
    formats = ["%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def extract_filing_date(text: str) -> date | None:
    """Extract filing date from text."""
    match = FILING_DATE_RE.search(text)
    if match:
        return parse_date_str(match.group(1))
    return None


def extract_settlement_amount(text: str) -> float | None:
    """Extract settlement amount in USD."""
    match = SETTLEMENT_RE.search(text)
    if not match:
        return None
    amount_str = match.group(1).replace(",", "")
    multiplier_str = match.group(2).lower()
    try:
        amount = float(amount_str)
    except ValueError:
        return None
    if multiplier_str == "billion":
        return amount * 1_000_000_000
    return amount * 1_000_000


def detect_status(text: str) -> CaseStatus:
    """Detect case status from text keywords."""
    text_lower = text.lower()
    for status, keywords in STATUS_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return status
    return CaseStatus.UNKNOWN


def detect_legal_theories(
    text: str, source: str,
) -> list[SourcedValue[str]]:
    """Detect legal theories from text."""
    theories: list[SourcedValue[str]] = []
    seen: set[str] = set()
    for theory, pattern in THEORY_PATTERNS:
        if pattern.search(text) and theory.value not in seen:
            theories.append(
                sourced_str(theory.value, source, Confidence.MEDIUM)
            )
            seen.add(theory.value)
    return theories


def detect_coverage_type(
    theories: list[SourcedValue[str]],
) -> CoverageType:
    """Determine coverage type from legal theories."""
    theory_values = {t.value for t in theories}
    if LegalTheory.SECTION_11.value in theory_values:
        return CoverageType.SCA_SIDE_C
    if LegalTheory.SECTION_14A.value in theory_values:
        return CoverageType.SCA_SIDE_B
    return CoverageType.SCA_SIDE_A


def is_within_horizon(filing_date: date | None) -> bool:
    """Check if a case is within the 10-year time horizon."""
    if filing_date is None:
        return True  # Include cases without dates (can't exclude)
    cutoff = date.today() - timedelta(days=TIME_HORIZON_DAYS)
    return filing_date >= cutoff


def word_set(text: str) -> set[str]:
    """Extract word set from text for similarity comparison."""
    return set(re.findall(r"\w+", text.lower()))


def word_overlap_pct(text_a: str, text_b: str) -> float:
    """Compute word overlap percentage between two strings."""
    words_a = word_set(text_a)
    words_b = word_set(text_b)
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    return len(intersection) / min(len(words_a), len(words_b))


# ---------------------------------------------------------------------------
# Quality filtering
# ---------------------------------------------------------------------------


def count_populated_fields(case: CaseDetail) -> list[str]:
    """Count which detail fields on a CaseDetail are actually populated.

    Returns a list of field names that have real (non-empty, non-default)
    values. Used to assess whether a case record is viable or hollow.
    """
    populated: list[str] = []
    if case.case_name and case.case_name.value.strip():
        populated.append("case_name")
    if case.case_number and case.case_number.value.strip():
        populated.append("case_number")
    if case.court and case.court.value.strip():
        populated.append("court")
    if case.filing_date:
        populated.append("filing_date")
    if case.class_period_start:
        populated.append("class_period_start")
    if case.class_period_end:
        populated.append("class_period_end")
    if case.status and case.status.value.strip():
        # UNKNOWN status does not count as populated
        if case.status.value != "UNKNOWN":
            populated.append("status")
    if case.settlement_amount:
        populated.append("settlement_amount")
    if case.lead_counsel and case.lead_counsel.value.strip():
        populated.append("lead_counsel")
    if case.allegations:
        populated.append("allegations")
    if case.legal_theories:
        populated.append("legal_theories")
    if case.coverage_type and case.coverage_type.value.strip():
        populated.append("coverage_type")
    return populated


def is_case_viable(case: CaseDetail) -> bool:
    """Check if a case record has enough detail to be useful.

    A case must have at minimum:
    - A case name (non-empty, non-generic)
    - At least ONE of: court, filing_date, status (non-UNKNOWN),
      class_period_start, settlement_amount, lead_counsel
    """
    # Must have a case name.
    if not case.case_name or not case.case_name.value.strip():
        return False
    # Must have at least one detail field beyond case_name.
    populated = count_populated_fields(case)
    detail_fields = [
        f for f in populated if f != "case_name"
        and f != "allegations"
        and f != "legal_theories"
        and f != "coverage_type"
    ]
    return len(detail_fields) >= 1


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def _parse_supabase_cases(state: AnalysisState) -> list[CaseDetail]:
    """Convert Supabase sca_filings data into CaseDetail objects."""
    if state.acquired_data is None:
        return []

    lit_data = state.acquired_data.litigation_data
    supabase_raw = lit_data.get("supabase_cases", [])
    if not isinstance(supabase_raw, list) or not supabase_raw:
        return []

    cases: list[CaseDetail] = []
    for raw in supabase_raw:
        if not isinstance(raw, dict):
            continue

        company = raw.get("company_name", "")
        filing_date = raw.get("filing_date")
        status_str = str(raw.get("case_status", "UNKNOWN")).upper()

        # Map status
        status_map = {
            "ONGOING": CaseStatus.ACTIVE,
            "SETTLED": CaseStatus.SETTLED,
            "DISMISSED": CaseStatus.DISMISSED,
        }
        status = status_map.get(status_str, CaseStatus.UNKNOWN)

        # Build case name
        case_name = f"In re {company} Securities Litigation"
        docket = raw.get("docket_number")
        if docket:
            case_name = f"{case_name} ({docket})"

        # Build allegations list
        allegations: list[SourcedValue[str]] = []
        summary = raw.get("case_summary", "")
        if summary:
            # Extract first 500 chars of summary as allegation description
            allegations.append(sourced_str(
                summary[:500], "Supabase SCA database", Confidence.MEDIUM,
            ))

        allegation_types = []
        if raw.get("allegation_accounting"):
            allegation_types.append("Accounting fraud")
        if raw.get("allegation_insider_trading"):
            allegation_types.append("Insider trading")
        if raw.get("allegation_earnings"):
            allegation_types.append("Earnings misrepresentation")
        if raw.get("allegation_merger"):
            allegation_types.append("Merger/acquisition related")
        if raw.get("allegation_ipo_offering"):
            allegation_types.append("IPO/offering related")
        if allegation_types:
            allegations.append(sourced_str(
                ", ".join(allegation_types), "Supabase SCA database", Confidence.HIGH,
            ))

        # Legal theories
        theories: list[SourcedValue[str]] = []
        if raw.get("allegation_accounting") or raw.get("allegation_earnings"):
            theories.append(sourced_str("10b-5", "Supabase", Confidence.MEDIUM))
        if raw.get("allegation_ipo_offering"):
            theories.append(sourced_str("Section 11", "Supabase", Confidence.MEDIUM))

        # Settlement
        settlement = raw.get("settlement_amount_m")
        settlement_sv = None
        if settlement is not None:
            try:
                from do_uw.stages.extract.sourced import sourced_float
                settlement_sv = sourced_float(
                    float(settlement) * 1_000_000,  # Convert M to USD
                    "Supabase SCA database", Confidence.HIGH,
                )
            except (ValueError, TypeError):
                pass

        # Lead counsel
        counsel = raw.get("lead_counsel")
        counsel_sv = sourced_str(counsel, "Supabase", Confidence.MEDIUM) if counsel else None

        case = CaseDetail(
            case_name=sourced_str(case_name, "Supabase SCA database", Confidence.MEDIUM),
            case_number=sourced_str(docket, "Supabase", Confidence.MEDIUM) if docket else None,
            court=sourced_str(
                raw.get("court") or raw.get("district_court") or "",
                "Supabase", Confidence.MEDIUM,
            ) if (raw.get("court") or raw.get("district_court")) else None,
            filing_date=sourced_str(
                str(filing_date), "Supabase SCA database", Confidence.HIGH,
            ) if filing_date else None,
            class_period_start=sourced_str(
                str(raw["class_period_start"]), "Supabase", Confidence.HIGH,
            ) if raw.get("class_period_start") else None,
            class_period_end=sourced_str(
                str(raw["class_period_end"]), "Supabase", Confidence.HIGH,
            ) if raw.get("class_period_end") else None,
            allegations=allegations,
            status=sourced_str(status.value, "Supabase SCA database", Confidence.HIGH),
            settlement_amount=settlement_sv,
            lead_counsel=counsel_sv,
            legal_theories=theories,
            coverage_type=sourced_str(CoverageType.SCA_SIDE_A.value, "Supabase", Confidence.MEDIUM),
        )
        cases.append(case)

    logger.info(
        "Supabase SCA: %d cases parsed for %s",
        len(cases), state.ticker,
    )
    return cases


def extract_securities_class_actions(
    state: AnalysisState,
) -> tuple[list[CaseDetail], ExtractionReport]:
    """Extract securities class action cases from multiple data sources.

    Parses EFTS/SCAC data (primary), 10-K Item 3 (supplement), and
    web search results for SCA cases. Applies two-layer classification
    (coverage_type + legal_theories), lead counsel tier lookup, and
    deduplication.

    Args:
        state: AnalysisState with acquired_data populated.

    Returns:
        Tuple of (list of CaseDetail, ExtractionReport).
    """
    # Import parsing functions (split module to stay under 500 lines).
    from do_uw.stages.extract.sca_parsing import (
        deduplicate_cases,
        parse_efts_references,
        parse_item3_text,
        parse_web_results,
        sanity_check_cases,
    )

    counsel_tiers = load_lead_counsel_tiers()
    found: list[str] = []
    warnings: list[str] = []
    fallbacks: list[str] = []
    source_filing = "EFTS/SCAC + 10-K Item 3 + web search"

    # 1. Primary: EFTS sec_references.
    efts_cases = parse_efts_references(state, counsel_tiers)
    if efts_cases:
        fallbacks.append("EFTS/SCAC primary")
    else:
        warnings.append("No EFTS/SCAC sec_references found")

    # 2. Supplement: 10-K Item 3.
    item3_cases = parse_item3_text(state)
    if item3_cases:
        fallbacks.append("10-K Item 3 supplement")

    # 3. Web search / blind spots.
    web_cases = parse_web_results(state)
    if web_cases:
        fallbacks.append("web search / blind spots")

    # 4. Supabase claims database (supplementary).
    supabase_cases = _parse_supabase_cases(state)
    if supabase_cases:
        fallbacks.append("Supabase SCA filings database")

    # Deduplicate across sources.
    all_cases = deduplicate_cases(efts_cases, item3_cases, web_cases + supabase_cases)

    # Sanity check: strip implausible settlements, statuses from recent filings.
    all_cases = sanity_check_cases(all_cases)

    # Quality filter: remove hollow case records.
    cases: list[CaseDetail] = []
    fragment_count = 0
    for case in all_cases:
        if is_case_viable(case):
            cases.append(case)
        else:
            fragment_count += 1
    if fragment_count > 0:
        warnings.append(
            f"Filtered {fragment_count} hollow case record(s) "
            "with insufficient detail fields"
        )
        logger.info(
            "SCA quality filter: kept %d viable, filtered %d fragments",
            len(cases), fragment_count,
        )

    # Track found fields using actual populated field counts.
    for case in cases:
        populated = count_populated_fields(case)
        for field_name in populated:
            found.append(field_name)

    # Deduplicate found field names.
    found = sorted(set(found))

    report = create_report(
        extractor_name="securities_class_actions",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source_filing,
        fallbacks_used=fallbacks,
        warnings=warnings,
    )
    log_report(report)

    return cases, report
