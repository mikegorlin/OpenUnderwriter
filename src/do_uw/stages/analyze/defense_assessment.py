"""Defense assessment extraction from SEC filings (SECT6-09).

Evaluates litigation defense posture by analyzing forum selection
provisions (DEF 14A), PSLRA safe harbor usage (10-K), truth-on-the-
market defense viability, judge track record, and prior dismissal
success. Produces an overall defense strength rating.

Usage:
    assessment, report = extract_defense_assessment(state)
    state.extracted.litigation.defense = assessment
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.litigation_details import (
    DefenseAssessment,
    ForumProvisions,
)
from do_uw.models.state import AnalysisState
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

_SOURCE_DEF14A = "DEF 14A"
_SOURCE_10K = "10-K"

# Expected extraction report fields.
EXPECTED_FIELDS: list[str] = [
    "forum_provisions",
    "pslra_safe_harbor",
    "truth_on_market",
    "judge_track_record",
    "prior_dismissals",
    "overall_strength",
    "defense_narrative",
]

# --- Regex patterns ---

_FEDERAL_FORUM_RE = re.compile(
    r"(?i)(?:federal\s+forum|Securities\s+Act)"
    r".{0,500}?"
    r"(?:United\s+States\s+federal\s+district\s+court|federal\s+court)",
    re.DOTALL,
)

_EXCLUSIVE_FORUM_RE = re.compile(
    r"(?i)(?:exclusive\s+forum|forum\s+selection)"
    r".{0,500}?"
    r"(?:Court\s+of\s+Chancery|Delaware|state\s+of\s+incorporation)",
    re.DOTALL,
)

_PSLRA_RE = re.compile(
    r"(?i)(?:safe\s+harbor|Private\s+Securities\s+Litigation\s+Reform"
    r"\s+Act|PSLRA|forward[\-\s]looking\s+statement)",
)

_PSLRA_EXPLICIT_RE = re.compile(
    r"(?i)(?:Private\s+Securities\s+Litigation\s+Reform\s+Act|PSLRA)",
)

_CAUTIONARY_SPECIFIC_RE = re.compile(
    r"(?i)(?:may\s+(?:not|differ)|could\s+(?:differ|be\s+adversely)"
    r"|risks?\s+(?:include|factor)|uncertaint(?:y|ies)\s+include"
    r"|subject\s+to\s+risks?|no\s+assurance|cannot\s+guarantee)",
)

_TRUTH_ON_MARKET_RE = re.compile(
    r"(?i)(?:truth[\-\s]on[\-\s]the[\-\s]market"
    r"|already\s+known|public\s+information"
    r"|prior\s+disclosure|analyst\s+reports\s+noted)",
)

_DISMISSAL_RE = re.compile(
    r"(?i)(?:dismissed|motion\s+to\s+dismiss\s+granted"
    r"|judgment\s+in\s+favor\s+of)",
)


def _now() -> datetime:
    return datetime.now(tz=UTC)


# ---------------------------------------------------------------------------
# Forum provision parsing
# ---------------------------------------------------------------------------


def parse_forum_provisions(proxy_text: str) -> ForumProvisions:
    """Parse forum selection provisions from DEF 14A proxy text.

    Searches for federal forum provisions (FFP) and exclusive forum
    provisions (EFP) in charter/bylaw language.

    Args:
        proxy_text: Full text of the DEF 14A proxy statement.

    Returns:
        ForumProvisions with has_federal_forum and has_exclusive_forum.
    """
    provisions = ForumProvisions()

    ffp_match = _FEDERAL_FORUM_RE.search(proxy_text)
    provisions.has_federal_forum = SourcedValue[bool](
        value=ffp_match is not None,
        source=_SOURCE_DEF14A,
        confidence=Confidence.HIGH if ffp_match else Confidence.MEDIUM,
        as_of=_now(),
    )
    if ffp_match:
        context = proxy_text[
            max(0, ffp_match.start() - 50) : ffp_match.end() + 50
        ]
        provisions.federal_forum_details = sourced_str(
            context.strip()[:500], _SOURCE_DEF14A, Confidence.HIGH
        )

    efp_match = _EXCLUSIVE_FORUM_RE.search(proxy_text)
    provisions.has_exclusive_forum = SourcedValue[bool](
        value=efp_match is not None,
        source=_SOURCE_DEF14A,
        confidence=Confidence.HIGH if efp_match else Confidence.MEDIUM,
        as_of=_now(),
    )
    if efp_match:
        context = proxy_text[
            max(0, efp_match.start() - 50) : efp_match.end() + 50
        ]
        provisions.exclusive_forum_details = sourced_str(
            context.strip()[:500], _SOURCE_DEF14A, Confidence.HIGH
        )

    if ffp_match or efp_match:
        provisions.source_document = sourced_str(
            "DEF 14A proxy statement", _SOURCE_DEF14A, Confidence.HIGH
        )

    return provisions


# ---------------------------------------------------------------------------
# PSLRA safe harbor classification
# ---------------------------------------------------------------------------


def classify_pslra_usage(text_10k: str) -> str:
    """Classify PSLRA safe harbor usage from 10-K text.

    Returns one of: STRONG, MODERATE, WEAK, NONE.

    STRONG = explicit PSLRA citation + specific cautionary language.
    MODERATE = generic forward-looking statement disclaimer.
    WEAK = minimal boilerplate only.
    NONE = no safe harbor language found.
    """
    pslra_matches = _PSLRA_RE.findall(text_10k)
    if not pslra_matches:
        return "NONE"

    has_explicit = bool(_PSLRA_EXPLICIT_RE.search(text_10k))
    specific_count = len(_CAUTIONARY_SPECIFIC_RE.findall(text_10k))

    if has_explicit and specific_count >= 3:
        return "STRONG"
    if has_explicit or specific_count >= 2:
        return "MODERATE"
    return "WEAK"


# ---------------------------------------------------------------------------
# Truth-on-the-market defense
# ---------------------------------------------------------------------------


def assess_truth_on_market(text_10k: str) -> str:
    """Assess truth-on-the-market defense viability.

    Returns: VIABLE, PARTIAL, or NOT_APPLICABLE.
    """
    matches = _TRUTH_ON_MARKET_RE.findall(text_10k)
    if len(matches) >= 2:
        return "VIABLE"
    if len(matches) == 1:
        return "PARTIAL"
    return "NOT_APPLICABLE"


# ---------------------------------------------------------------------------
# Prior dismissals
# ---------------------------------------------------------------------------


def check_prior_dismissals(item3_text: str) -> tuple[bool, int]:
    """Check Item 3 for prior dismissal success.

    Returns:
        Tuple of (has_dismissals, dismissal_count).
    """
    matches = _DISMISSAL_RE.findall(item3_text)
    return (len(matches) > 0, len(matches))


# ---------------------------------------------------------------------------
# Overall defense strength
# ---------------------------------------------------------------------------


def compute_defense_strength(
    has_federal_forum: bool,
    has_exclusive_forum: bool,
    pslra_usage: str,
    has_prior_dismissals: bool,
) -> str:
    """Compute overall defense strength rating.

    STRONG: federal forum + PSLRA strong + prior dismissals.
    WEAK: no forum provisions + no safe harbor.
    MODERATE: everything else.
    """
    strong_count = 0
    if has_federal_forum or has_exclusive_forum:
        strong_count += 1
    if pslra_usage == "STRONG":
        strong_count += 1
    if has_prior_dismissals:
        strong_count += 1

    if strong_count >= 3:
        return "STRONG"

    weak_indicators = 0
    if not has_federal_forum and not has_exclusive_forum:
        weak_indicators += 1
    if pslra_usage == "NONE":
        weak_indicators += 1

    if weak_indicators >= 2:
        return "WEAK"
    return "MODERATE"


# ---------------------------------------------------------------------------
# Narrative generation
# ---------------------------------------------------------------------------


def build_defense_narrative(
    has_federal_forum: bool,
    has_exclusive_forum: bool,
    pslra_usage: str,
    truth_viability: str,
    has_prior_dismissals: bool,
    overall_strength: str,
) -> str:
    """Build 2-3 sentence defense posture narrative."""
    parts: list[str] = []

    # Forum provisions
    forum_parts: list[str] = []
    if has_federal_forum:
        forum_parts.append("federal forum provision")
    if has_exclusive_forum:
        forum_parts.append("exclusive forum provision")
    if forum_parts:
        provisions = " and ".join(forum_parts)
        parts.append(f"Company has adopted {provisions}.")
    else:
        parts.append("No forum selection provisions identified.")

    # Safe harbor
    pslra_desc = {
        "STRONG": "with explicit PSLRA citation and specific cautionary language",
        "MODERATE": "with standard forward-looking statement protections",
        "WEAK": "with minimal safe harbor language",
        "NONE": "without meaningful safe harbor protections",
    }
    parts.append(
        f"Safe harbor usage is {pslra_usage} "
        f"{pslra_desc.get(pslra_usage, '')}."
    )

    # Dismissals and truth-on-market
    extras: list[str] = []
    if has_prior_dismissals:
        extras.append("prior dismissal success")
    if truth_viability == "VIABLE":
        extras.append("viable truth-on-the-market defense")
    if extras:
        parts.append(
            f"Additional defense factors include {', '.join(extras)}."
        )

    return " ".join(parts)


# ---------------------------------------------------------------------------
# Main extractor
# ---------------------------------------------------------------------------


def extract_defense_assessment(
    state: AnalysisState,
) -> tuple[DefenseAssessment, ExtractionReport]:
    """Extract defense assessment from SEC filings.

    Analyzes forum provisions (DEF 14A), PSLRA safe harbor (10-K),
    truth-on-the-market viability, prior dismissals, and judge track
    record to produce an overall defense strength assessment.

    Args:
        state: Analysis state with acquired filing data.

    Returns:
        Tuple of (DefenseAssessment, ExtractionReport).
    """
    found: list[str] = []
    warnings: list[str] = []
    assessment = DefenseAssessment()

    # --- 1. Forum provisions from DEF 14A ---
    proxy_text = get_filing_document_text(state, "DEF 14A")
    if proxy_text:
        assessment.forum_provisions = parse_forum_provisions(proxy_text)
        found.append("forum_provisions")
    else:
        assessment.forum_provisions = ForumProvisions()
        warnings.append("No DEF 14A text available for forum provisions")

    has_ffp = _get_bool(assessment.forum_provisions.has_federal_forum)
    has_efp = _get_bool(assessment.forum_provisions.has_exclusive_forum)

    # --- 2. PSLRA safe harbor from 10-K ---
    text_10k = get_filing_document_text(state, "10-K")
    if text_10k:
        pslra_usage = classify_pslra_usage(text_10k)
        assessment.pslra_safe_harbor_usage = sourced_str(
            pslra_usage, _SOURCE_10K, Confidence.HIGH
        )
        found.append("pslra_safe_harbor")
    else:
        pslra_usage = "NONE"
        warnings.append("No 10-K text available for PSLRA analysis")

    # --- 3. Truth-on-the-market viability ---
    if text_10k:
        truth = assess_truth_on_market(text_10k)
        assessment.truth_on_market_viability = sourced_str(
            truth, _SOURCE_10K, Confidence.LOW
        )
        found.append("truth_on_market")
    else:
        truth = "NOT_APPLICABLE"

    # --- 4. Judge track record (LOW confidence, requires active cases) ---
    judge_info = _extract_judge_track_record(state)
    if judge_info:
        assessment.judge_track_record = sourced_str(
            judge_info, "litigation case data", Confidence.LOW
        )
        found.append("judge_track_record")

    # --- 5. Prior dismissals from Item 3 ---
    item3_text = _get_item3_text(text_10k)
    has_dismissals, dismissal_count = check_prior_dismissals(item3_text)
    if has_dismissals:
        assessment.prior_dismissal_success = sourced_str(
            f"Found {dismissal_count} dismissal reference(s) in Item 3",
            _SOURCE_10K,
            Confidence.MEDIUM,
        )
    else:
        assessment.prior_dismissal_success = sourced_str(
            "No prior dismissals identified in Item 3",
            _SOURCE_10K,
            Confidence.MEDIUM,
        )
    found.append("prior_dismissals")

    # --- 6. Overall defense strength ---
    overall = compute_defense_strength(
        has_ffp, has_efp, pslra_usage, has_dismissals
    )
    assessment.overall_defense_strength = sourced_str(
        overall,
        f"{_SOURCE_DEF14A}; {_SOURCE_10K}",
        Confidence.MEDIUM,
    )
    found.append("overall_strength")

    # --- 7. Defense narrative ---
    narrative = build_defense_narrative(
        has_ffp, has_efp, pslra_usage, truth, has_dismissals, overall
    )
    assessment.defense_narrative = sourced_str(
        narrative,
        f"{_SOURCE_DEF14A}; {_SOURCE_10K}",
        Confidence.LOW,
    )
    found.append("defense_narrative")

    # --- Build report ---
    source = _SOURCE_10K
    if proxy_text:
        source = f"{_SOURCE_DEF14A}; {_SOURCE_10K}"
    report = create_report(
        extractor_name="defense_assessment",
        expected=EXPECTED_FIELDS,
        found=found,
        source_filing=source,
        warnings=warnings,
    )
    log_report(report)
    return assessment, report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_bool(sv: SourcedValue[bool] | None) -> bool:
    """Extract bool from optional SourcedValue, defaulting to False."""
    if sv is None:
        return False
    return sv.value


def _get_item3_text(text_10k: str) -> str:
    """Extract Item 3 section from 10-K text.

    Uses simple pattern matching for Item 3 (Legal Proceedings).
    """
    if not text_10k:
        return ""
    from do_uw.stages.extract.filing_sections import extract_section

    item3_start = [
        r"(?i)\bitem\s+3[\.\s:]+legal\s+proceedings\b",
        r"(?i)\bitem\s+3\b(?!\s*[0-9a-z])",
    ]
    item3_end = [
        r"(?i)\bitem\s+3a\b",
        r"(?i)\bitem\s+4\b",
    ]
    return extract_section(text_10k, item3_start, item3_end)


def _extract_judge_track_record(state: AnalysisState) -> str:
    """Extract judge track record from active litigation cases.

    Returns a summary string if a judge is identified, else empty.
    """
    if state.extracted is None or state.extracted.litigation is None:
        return ""

    litigation = state.extracted.litigation
    for case in litigation.securities_class_actions:
        if case.judge is not None and case.judge.value:
            judge_name = case.judge.value
            status = ""
            if case.status is not None:
                status = f" (case status: {case.status.value})"
            return f"Judge {judge_name} assigned{status}"

    return ""
