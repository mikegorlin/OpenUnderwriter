"""Leadership profile parsing helpers for proxy and 8-K filings.

Low-level text parsing functions for extracting executive names,
titles, tenure, departures, and dates from SEC filing text.
Split from leadership_profiles.py to stay under 500-line limit.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any, cast

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance_forensics import LeadershipForensicProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import now, sourced_str

logger = logging.getLogger(__name__)

# C-suite title patterns (regex fragments).
CSUITE_PATTERNS: list[tuple[str, str]] = [
    (r"chief executive officer|(?<!\w)ceo(?!\w)", "CEO"),
    (r"chief financial officer|(?<!\w)cfo(?!\w)", "CFO"),
    (r"chief operating officer|(?<!\w)coo(?!\w)", "COO"),
    (r"chief legal officer|(?<!\w)clo(?!\w)|general counsel", "CLO"),
    (r"chief accounting officer|(?<!\w)cao(?!\w)", "CAO"),
    (r"chief technology officer|(?<!\w)cto(?!\w)", "CTO"),
    (r"chief information officer|(?<!\w)cio(?!\w)", "CIO"),
    (r"president", "President"),
]

# Words that regex falsely matches as person names.
_NON_NAME_WORDS: frozenset[str] = frozenset({
    # Common English words
    "from", "our", "the", "this", "that", "with", "and", "for",
    "its", "his", "her", "who", "has", "had", "was", "are", "not",
    "but", "may", "will", "any", "all", "each", "such", "also",
    # Filing structure terms
    "proxy", "statement", "annual", "meeting", "table", "contents",
    "message", "board", "directors", "executive", "officers",
    "compensation", "committee", "corporate", "governance",
    "stock", "ownership", "election", "audit", "report",
    "chief", "senior", "vice", "general", "counsel",
    "summary", "total", "base", "fiscal", "current", "former",
    "independent", "non", "lead", "section", "item", "part",
    "schedule", "exhibit", "pursuant", "aggregate", "average",
    # Award/Grant/Plan/Program terms (compensation tables)
    "interim", "performance", "incentive", "award",
    "grant", "equity", "deferred", "restricted", "option",
    "plan", "program", "agreement", "target", "threshold",
    "maximum", "vesting", "bonus", "salary", "retention",
    "severance", "termination", "payout", "accrued",
    # Industry/business terms
    "space", "exploration", "technologies", "holdings",
    "industries", "capital", "global", "international",
    "services", "solutions", "systems", "group", "energy",
    "motors", "financial", "resources", "management",
    "partners", "ventures", "enterprises", "associates",
    "corporation", "incorporated", "limited", "company",
    # Additional SEC filing vocabulary
    "outstanding", "exercisable", "forfeited", "granted",
    "vested", "unvested", "convertible", "cumulative",
    "incremental", "supplemental", "additional", "estimated",
    # Honorifics / salutations (catches malformed "Musk Mr" etc.)
    "mr", "mrs", "ms", "dr", "jr", "sr", "ii", "iii", "iv",
    # Locations, company names, and role fragments that regex falsely captures
    "cupertino", "seattle", "redmond", "mountain", "view",
    "menlo", "palo", "alto", "san", "francisco", "jose",
    "new", "york", "austin", "chicago", "boston", "dallas",
    "apple", "google", "amazon", "microsoft", "meta",
    "tesla", "nvidia", "oracle", "intel", "cisco",
    "secretary", "treasurer", "controller", "registrant",
    "assignee", "principal", "deputy", "assistant",
    # LLM extraction garbage — company/org names and proxy terminology
    "association", "brands", "materials", "proposals", "networks",
    "fund", "ratio", "sky", "succession", "reserve",
    "juniper", "redwood", "western", "partner", "nova",
    "trust", "foundation", "institute", "university", "college",
    "bank", "insurance", "mutual", "investments", "advisors",
})


def extract_executives_from_proxy(
    proxy_text: str,
) -> list[LeadershipForensicProfile]:
    """Parse DEF 14A proxy text to extract C-suite executive profiles.

    Searches proxy text for officer names and titles via regex.
    Infers tenure from bio text patterns like 'appointed in 2020'.

    Args:
        proxy_text: Full text of DEF 14A proxy statement.

    Returns:
        List of LeadershipForensicProfile for each identified executive.
    """
    if not proxy_text.strip():
        return []

    executives: list[LeadershipForensicProfile] = []
    seen_names: set[str] = set()
    rejected_count = 0
    source = "DEF 14A proxy statement"
    paragraphs = re.split(r"\n\s*\n|\r\n\s*\r\n", proxy_text)

    for para in paragraphs:
        for pattern, title_label in CSUITE_PATTERNS:
            if not re.search(pattern, para, re.IGNORECASE):
                continue
            name = _extract_name_near_title(para, pattern)
            if not name:
                rejected_count += 1
                continue
            if name in seen_names:
                continue
            seen_names.add(name)
            tenure_years = _infer_tenure_from_bio(para)
            # Only flag as interim if "interim" directly precedes THIS
            # executive's specific title (not just any title in the paragraph)
            title_words = title_label.lower().split()
            is_interim = bool(
                re.search(
                    r"\binterim\s+" + re.escape(title_words[0]),
                    para, re.IGNORECASE,
                )
            ) if title_words else False
            # Sanity: nobody is interim for >3 years
            if is_interim and tenure_years is not None and tenure_years > 3:
                is_interim = False
            profile = LeadershipForensicProfile(
                name=sourced_str(name, source, Confidence.MEDIUM),
                title=sourced_str(title_label, source, Confidence.MEDIUM),
                tenure_years=tenure_years,
                is_interim=SourcedValue[bool](
                    value=is_interim, source=source,
                    confidence=Confidence.MEDIUM, as_of=now(),
                ),
                departure_type="ACTIVE",
            )
            if tenure_years is not None:
                current_year = datetime.now(tz=UTC).year
                start_year = current_year - int(tenure_years)
                profile.tenure_start = sourced_str(
                    f"{start_year}-01-01", source, Confidence.LOW,
                )
            executives.append(profile)

    if rejected_count > 0:
        logger.info(
            "Leadership extraction: rejected %d candidate name(s) "
            "that failed validation",
            rejected_count,
        )

    return executives


def is_valid_person_name(candidate: str) -> bool:
    """Validate that a candidate string looks like a person name.

    Rejects common non-name words, section headers, title fragments,
    and compensation terminology that regex falsely matches as names.

    Structural checks:
    - 2-4 words, each starting uppercase
    - No word purely numeric
    - Average word length >= 3 chars (rejects "At Or" etc.)
    - No word in SEC filing vocabulary blocklist
    """
    parts = candidate.strip().split()
    if len(parts) < 2 or len(parts) > 4:
        return False
    # Every word must start with uppercase (real name check).
    if not all(p[0].isupper() for p in parts if p):
        return False
    # Reject if any word is purely numeric.
    if any(p.isdigit() for p in parts):
        return False
    # Reject if any word is a known non-name word (case-insensitive).
    if any(p.lower() in _NON_NAME_WORDS for p in parts):
        return False
    # Average word length must be >= 3 chars (rejects "At Or", "So On").
    avg_len = sum(len(p) for p in parts) / len(parts)
    if avg_len < 3.0:
        return False
    # Reject single-char words other than middle initials.
    # Allow one single-char word (middle initial like "J." or "J")
    single_char_count = sum(
        1 for p in parts if len(p.rstrip(".")) <= 1
    )
    if single_char_count > 1:
        return False
    return True


def _extract_name_near_title(paragraph: str, title_pattern: str) -> str:
    """Extract a person's name near a C-suite title mention.

    Uses three strategies in priority order:
    1. Name immediately before title (e.g., 'Tim Cook Chief Executive Officer')
    2. Name within 80 chars after title (e.g., 'CEO ... Tim Cook')
    3. Honorific pattern (e.g., 'Mr. Cook')

    Names are validated to reject common non-name words.
    """
    # Build case-insensitive title regex for locating the title.
    title_re = re.compile(title_pattern, re.IGNORECASE)

    # Pattern 1: "Name Title" — name capture is CASE-SENSITIVE.
    # We find the title position, then look backward for a name.
    title_match = title_re.search(paragraph)
    if title_match:
        before = paragraph[max(0, title_match.start() - 60) : title_match.start()]
        # Look for "Firstname Lastname" right before the title.
        name_before = re.search(
            r"([A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+)\s*[,\-\s]*$",
            before,
        )
        if name_before and is_valid_person_name(name_before.group(1)):
            return name_before.group(1).strip()

    # Pattern 2: "Title ... Name" (within 80 chars) — CASE-SENSITIVE.
    if title_match:
        after = paragraph[title_match.end() : title_match.end() + 80]
        name_after = re.search(
            r"[,\s]+([A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+)",
            after,
        )
        if name_after and is_valid_person_name(name_after.group(1)):
            return name_after.group(1).strip()

    # Pattern 3: "Mr./Ms./Dr. Firstname Lastname" — require 2+ words
    honorific = re.search(
        r"(?:Mr|Ms|Mrs|Dr)\.\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        paragraph,
    )
    if honorific and is_valid_person_name(honorific.group(1).strip()):
        return honorific.group(1).strip()
    return ""


def _infer_tenure_from_bio(text: str) -> float | None:
    """Infer tenure in years from bio text."""
    patterns = [
        r"(?:appointed|named|became|elected|promoted).*?(?:in|since)\s+(\d{4})",
        r"(?:joined|serving since|has served since)\s+(\d{4})",
        r"(?:appointed|named).*?(?:January|February|March|April|May|June|"
        r"July|August|September|October|November|December)\s+(\d{4})",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            current_year = datetime.now(tz=UTC).year
            tenure = current_year - year
            if 0 <= tenure < 50:
                return float(tenure)
    return None


def extract_departures_from_8k(
    eight_k_texts: list[str],
) -> list[LeadershipForensicProfile]:
    """Parse 8-K Item 5.02 filings for departure/appointment events.

    Classifies departures as PLANNED (retirement, personal reasons)
    or UNPLANNED (all other departures).
    """
    departures: list[LeadershipForensicProfile] = []
    source = "8-K Item 5.02"
    seen_names: set[str] = set()
    planned_keywords = [
        "retire", "retirement", "personal reasons",
        "end of term", "planned transition", "succession plan",
    ]

    for text in eight_k_texts:
        if not text.strip():
            continue
        if not re.search(r"item\s*5\.02", text, re.IGNORECASE):
            continue
        text_lower = text.lower()
        is_planned = any(kw in text_lower for kw in planned_keywords)
        departure_type = "PLANNED" if is_planned else "UNPLANNED"
        name = _extract_departure_name(text)
        if not name or name in seen_names:
            continue
        seen_names.add(name)
        title = _infer_title_from_context(text)
        dep_date = _extract_date_from_text(text)
        profile = LeadershipForensicProfile(
            name=sourced_str(name, source, Confidence.HIGH),
            title=sourced_str(title, source, Confidence.HIGH)
            if title else None,
            departure_type=departure_type,
            departure_date=dep_date,
            departure_context=sourced_str(
                text[:500].strip(), source, Confidence.HIGH
            ),
        )
        departures.append(profile)

    return departures


def _extract_departure_name(text: str) -> str:
    """Extract departing executive name from 8-K text."""
    match = re.search(
        r"(?:departure|resignation|termination|retirement)"
        r"\s+of\s+([A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+)",
        text,
    )
    if match:
        return match.group(1).strip()
    match = re.search(
        r"([A-Z][a-z]+\s+(?:[A-Z]\.?\s+)?[A-Z][a-z]+)"
        r"[\s,]+(?:has\s+)?(?:resigned|departed|retired|stepped down)",
        text,
    )
    if match:
        return match.group(1).strip()
    return ""


def _infer_title_from_context(text: str) -> str:
    """Infer C-suite title from 8-K departure context."""
    for pattern, label in CSUITE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return label
    return ""


def _extract_date_from_text(text: str) -> str | None:
    """Extract a date from filing text in ISO format."""
    patterns = [
        r"effective\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"as of\s+(\w+\s+\d{1,2},?\s+\d{4})",
        r"(\d{4}-\d{2}-\d{2})",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            raw = match.group(1).strip()
            if re.match(r"\d{4}-\d{2}-\d{2}", raw):
                return raw
            try:
                dt = datetime.strptime(
                    raw.replace(",", ""), "%B %d %Y"
                )
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
    return None


def search_prior_litigation(
    name: str, state: AnalysisState,
) -> list[str]:
    """Search acquired data for prior litigation involving an executive.

    Searches litigation_data, web_search_results, and blind_spot_results
    for case-insensitive substring matches on executive's last name.
    """
    if not name or state.acquired_data is None:
        return []
    parts = name.strip().split()
    last_name = parts[-1] if parts else name
    last_lower = last_name.lower()
    matches: list[str] = []
    _search_dict_for_name(
        state.acquired_data.litigation_data, last_lower, matches
    )
    _search_dict_for_name(
        state.acquired_data.web_search_results, last_lower, matches
    )
    _search_dict_for_name(
        state.acquired_data.blind_spot_results, last_lower, matches
    )
    return matches


def _search_dict_for_name(
    data: dict[str, Any], name_lower: str, results: list[str],
) -> None:
    """Recursively search a dict for name substring matches."""
    for key, value in data.items():
        if isinstance(value, str) and name_lower in value.lower():
            results.append(f"{key}: {value[:200]}")
        elif isinstance(value, dict):
            typed_dict = cast(dict[str, Any], value)
            _search_dict_for_name(typed_dict, name_lower, results)
        elif isinstance(value, list):
            typed_list = cast(list[Any], value)
            for item in typed_list:
                if isinstance(item, str) and name_lower in item.lower():
                    results.append(f"{key}: {item[:200]}")
                elif isinstance(item, dict):
                    typed_item = cast(dict[str, Any], item)
                    _search_dict_for_name(
                        typed_item, name_lower, results
                    )


def get_8k_documents(state: AnalysisState) -> list[str]:
    """Get all 8-K full text documents from acquired data."""
    from do_uw.stages.extract.sourced import get_filing_documents

    docs = get_filing_documents(state)
    texts: list[str] = []
    for doc in docs.get("8-K", []):
        text = str(doc.get("full_text", ""))
        if text.strip():
            texts.append(text)
    return texts
