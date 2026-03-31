"""Agency detection patterns and matching helpers for regulatory extraction.

Split from regulatory_extract.py (Phase 45, 500-line rule).
Contains agency regex patterns, classification helpers, and the text
scanning function. Main orchestrator remains in regulatory_extract.py.
"""

from __future__ import annotations

import re

from do_uw.models.common import Confidence
from do_uw.models.litigation_details import RegulatoryProceeding
from do_uw.stages.extract.sourced import sourced_float, sourced_str

# Source attribution prefix.
_SOURCE_10K = "10-K Legal Proceedings (Item 3)"
_SOURCE_10K_RF = "10-K Risk Factors (Item 1A)"
_SOURCE_8K = "8-K filing"
_SOURCE_WEB = "web search"

# Expected fields for extraction report.
EXPECTED_FIELDS: list[str] = [
    "doj",
    "ftc",
    "fda",
    "epa",
    "cfpb",
    "occ",
    "state_ag",
    "fcpa",
    "eeoc",
    "osha",
    "nhtsa",
    "ferc",
]

# ---------------------------------------------------------------------------
# Agency detection patterns
# ---------------------------------------------------------------------------

# Allow up to 5 intervening words between agency name and action keyword.
# Possessive 's is optional after acronyms (e.g., "NHTSA's").
_GAP = r"(?:'s)?(?:\s+\S+){0,5}\s+"

AGENCY_PATTERNS: list[tuple[str, str]] = [
    (
        r"(?:DOJ|Department\s+of\s+Justice)" + _GAP
        + r"(?:investigation|inquiry|prosecution|indictment|settlement"
        r"|subpoena|probe|action|lawsuit|complaint|penalty|fine)",
        "DOJ",
    ),
    (r"(?:FCPA|Foreign\s+Corrupt\s+Practices)", "DOJ_FCPA"),
    (
        r"(?:FTC|Federal\s+Trade\s+Commission)" + _GAP
        + r"(?:investigation|enforcement|consent|order|complaint"
        r"|probe|action|settlement|penalty|fine|lawsuit|ruling)",
        "FTC",
    ),
    (
        r"(?:FDA|Food\s+and\s+Drug\s+Administration)" + _GAP
        + r"(?:warning|inspection|483|consent\s+decree|recall"
        r"|enforcement|action|letter|audit|penalty|violation)",
        "FDA",
    ),
    (
        r"(?:EPA|Environmental\s+Protection\s+Agency)" + _GAP
        + r"(?:enforcement|violation|consent|remediation|Superfund"
        r"|action|penalty|fine|settlement|order)",
        "EPA",
    ),
    (
        r"(?:CFPB|Consumer\s+Financial\s+Protection)" + _GAP
        + r"(?:enforcement|consent|investigation|examination"
        r"|action|order|penalty|complaint|fine)",
        "CFPB",
    ),
    (
        r"(?:OCC|Office\s+of\s+the\s+Comptroller)" + _GAP
        + r"(?:enforcement|consent|examination|order"
        r"|action|penalty|fine|cease)",
        "OCC",
    ),
    (
        r"(?:OSHA|Occupational\s+Safety)" + _GAP
        + r"(?:citation|violation|inspection|penalty"
        r"|investigation|fine|action|complaint)",
        "OSHA",
    ),
    (
        r"(?:state\s+attorney|attorney\s+general)" + _GAP
        + r"(?:investigation|action|suit|enforcement|settlement"
        r"|complaint|subpoena|probe|lawsuit|penalty|fine)",
        "STATE_AG",
    ),
    (
        r"(?:EEOC|Equal\s+Employment\s+Opportunity)" + _GAP
        + r"(?:charge|complaint|investigation|consent"
        r"|action|lawsuit|settlement|penalty)",
        "EEOC",
    ),
    (
        r"(?:NHTSA|National\s+Highway\s+Traffic\s+Safety"
        r"(?:\s+Administration)?)" + _GAP
        + r"(?:investigation|recall|defect|probe|penalty"
        r"|inquiry|enforcement|consent|order|action"
        r"|report|requirement|review|audit|ruling|fine)",
        "NHTSA",
    ),
    (
        r"(?:FERC|Federal\s+Energy\s+Regulatory"
        r"(?:\s+Commission)?)" + _GAP
        + r"(?:enforcement|investigation|order|penalty"
        r"|violation|inquiry|proceeding|action|fine|ruling)",
        "FERC",
    ),
]

# Proceeding type classification keywords.
_TYPE_KEYWORDS: list[tuple[str, str]] = [
    ("consent decree", "consent_decree"),
    ("consent order", "consent_decree"),
    ("settlement", "penalty"),
    ("penalty", "penalty"),
    ("fine", "penalty"),
    ("enforcement action", "enforcement"),
    ("enforcement", "enforcement"),
    ("investigation", "investigation"),
    ("inquiry", "investigation"),
    ("prosecution", "enforcement"),
    ("indictment", "enforcement"),
    ("recall", "enforcement"),
    ("defect", "investigation"),
]

# Penalty amount extraction pattern.
_PENALTY_PATTERN = re.compile(
    r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)", re.IGNORECASE
)

# Max description length.
_MAX_DESC_CHARS = 500

# News article byline/title patterns that should not be treated as
# regulatory proceedings.  Matches common journalist bylines, article
# titles in quotes, and media outlet names.
_NEWS_ARTICLE_PATTERN = re.compile(
    r"^[A-Z][a-z]+\s+[A-Z][a-z]+\s+(?:and|,)\s+[A-Z][a-z]+\s+[A-Z][a-z]+,"
    r"|^By\s+[A-Z]"
    r"|\u201c[^\\u201d]{10,}\u201d"
    r"|Wall\s+Street\s+Journal|Reuters\b|Bloomberg\b|Associated\s+Press"
    r"|CNBC\b|Yahoo\s+Finance|MarketWatch",
    re.IGNORECASE,
)

# Reverse patterns: action keyword BEFORE agency name.
# Catches "investigation by NHTSA", "subpoena from DOJ", etc.
_REVERSE_GAP = r"(?:\s+\S+){0,3}\s+(?:by|from|of|with)\s+"
_AGENCY_ACRONYMS: list[tuple[str, str]] = [
    (r"DOJ|Department\s+of\s+Justice", "DOJ"),
    (r"FTC|Federal\s+Trade\s+Commission", "FTC"),
    (r"FDA|Food\s+and\s+Drug\s+Administration", "FDA"),
    (r"EPA|Environmental\s+Protection\s+Agency", "EPA"),
    (r"CFPB|Consumer\s+Financial\s+Protection", "CFPB"),
    (r"OSHA|Occupational\s+Safety", "OSHA"),
    (r"EEOC|Equal\s+Employment\s+Opportunity", "EEOC"),
    (r"NHTSA|National\s+Highway\s+Traffic\s+Safety", "NHTSA"),
    (r"FERC|Federal\s+Energy\s+Regulatory", "FERC"),
]

_ACTION_WORDS = (
    r"(?:investigation|enforcement|subpoena|probe|inquiry|action|recall"
    r"|penalty|fine|settlement|complaint|lawsuit|order|violation)"
)

REVERSE_PATTERNS: list[tuple[str, str]] = [
    (
        _ACTION_WORDS + _REVERSE_GAP + r"(?:" + acronym + r")",
        agency,
    )
    for acronym, agency in _AGENCY_ACRONYMS
]


# ---------------------------------------------------------------------------
# Extraction logic helpers
# ---------------------------------------------------------------------------


def _extract_context(text: str, match_start: int, match_end: int) -> str:
    """Extract sentence context around a regex match, max 500 chars."""
    # Find sentence boundaries.
    # Look backward for sentence start.
    sent_start = max(0, match_start - 200)
    for i in range(match_start - 1, sent_start, -1):
        if text[i] in ".!?\n" and i < match_start - 1:
            sent_start = i + 1
            break

    # Look forward for sentence end.
    sent_end = min(len(text), match_end + 300)
    for i in range(match_end, sent_end):
        if text[i] in ".!?\n":
            sent_end = i + 1
            break

    context = text[sent_start:sent_end].strip()
    if len(context) > _MAX_DESC_CHARS:
        context = context[:_MAX_DESC_CHARS - 3] + "..."
    return context


def _classify_proceeding_type(context: str) -> str:
    """Classify proceeding type from text context."""
    context_lower = context.lower()
    for keyword, ptype in _TYPE_KEYWORDS:
        if keyword in context_lower:
            return ptype
    return "investigation"


def _extract_penalty_amount(context: str) -> float | None:
    """Extract penalty amount from context text.

    Matches patterns like $50 million, $1.2 billion.
    Returns amount in USD (millions/billions converted).
    """
    match = _PENALTY_PATTERN.search(context)
    if not match:
        return None

    amount_str = match.group(1).replace(",", "")
    multiplier_str = match.group(2).lower()

    try:
        amount = float(amount_str)
    except ValueError:
        return None

    if multiplier_str == "billion":
        amount *= 1_000_000_000.0
    elif multiplier_str == "million":
        amount *= 1_000_000.0

    return amount


def _agency_to_report_field(agency: str) -> str:
    """Map agency code to expected field name for ExtractionReport."""
    mapping: dict[str, str] = {
        "DOJ": "doj",
        "DOJ_FCPA": "fcpa",
        "FTC": "ftc",
        "FDA": "fda",
        "EPA": "epa",
        "CFPB": "cfpb",
        "OCC": "occ",
        "OSHA": "osha",
        "STATE_AG": "state_ag",
        "EEOC": "eeoc",
        "NHTSA": "nhtsa",
        "FERC": "ferc",
    }
    return mapping.get(agency, agency.lower())


def _scan_text_for_agencies(
    text: str,
    source: str,
    confidence: Confidence,
) -> list[RegulatoryProceeding]:
    """Scan text for agency pattern matches, return proceedings."""
    proceedings: list[RegulatoryProceeding] = []
    if not text:
        return proceedings

    all_patterns = list(AGENCY_PATTERNS) + REVERSE_PATTERNS
    for pattern, agency in all_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context = _extract_context(text, match.start(), match.end())
            # Skip news article bylines/titles from web search
            if _NEWS_ARTICLE_PATTERN.search(context):
                continue
            proceeding_type = _classify_proceeding_type(context)
            penalty = _extract_penalty_amount(context)

            proc = RegulatoryProceeding(
                agency=sourced_str(agency, source, confidence),
                proceeding_type=sourced_str(
                    proceeding_type, source, confidence
                ),
                description=sourced_str(context, source, confidence),
                status=sourced_str("disclosed", source, confidence),
                coverage_type=sourced_str(
                    "REGULATORY_ENTITY", source, confidence
                ),
                do_implications=sourced_str(
                    f"{agency} {proceeding_type} may trigger entity "
                    f"coverage under D&O policy",
                    source,
                    confidence,
                ),
            )

            if penalty is not None:
                proc.penalties = sourced_float(penalty, source, confidence)

            proceedings.append(proc)

    return proceedings


__all__ = [
    "AGENCY_PATTERNS",
    "EXPECTED_FIELDS",
    "REVERSE_PATTERNS",
    "_SOURCE_8K",
    "_SOURCE_10K",
    "_SOURCE_10K_RF",
    "_SOURCE_WEB",
    "_agency_to_report_field",
    "_scan_text_for_agencies",
]
