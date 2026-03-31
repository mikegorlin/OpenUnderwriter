"""Board member parsing from proxy statements.

Extracts director profiles from DEF 14A proxy text by splitting
director biographical blocks and parsing individual attributes
(independence, tenure, committees, other boards, prior litigation).
"""

from __future__ import annotations

import logging
import re

from do_uw.models.common import Confidence, SourcedValue

logger = logging.getLogger(__name__)
from do_uw.models.governance_forensics import BoardForensicProfile
from do_uw.models.state import AnalysisState
from do_uw.stages.extract.sourced import (
    now,
    sourced_float,
    sourced_str,
)

# Phrases that look like names but are section headers or non-name words.
_SKIP_PHRASES: set[str] = {
    "Annual Meeting", "Board Directors", "Corporate Governance",
    "Executive Officers", "Proxy Statement", "Stock Ownership",
    "Compensation Committee", "Audit Committee", "Election Directors",
    "General Counsel", "Chief Financial", "Chief Executive",
    "Table Contents", "Proxy Summary", "Career Highlights",
    "Key Skills", "Other Public", "Director Since",
}
# Words that are never part of a person's name.
_NON_NAME_WORDS: frozenset[str] = frozenset({
    "the", "and", "for", "our", "from", "with", "this", "that",
    "its", "has", "had", "was", "are", "not", "but", "may",
    "annual", "meeting", "proxy", "statement", "table", "contents",
    "executive", "officers", "compensation", "committee", "corporate",
    "governance", "stock", "ownership", "election", "audit", "report",
    "board", "directors", "chief", "senior", "vice", "general",
    "counsel", "career", "highlights", "key", "skills", "other",
    "public", "company", "boards", "none", "director", "since",
    "proposal", "vote", "voting", "approval", "binding", "advisory",
    "resolution", "ratification", "management", "stockholder",
    "shareholder", "amendment", "article", "section", "item",
    "regarding", "related", "pursuant", "fiscal", "year",
})

# Committee name patterns for matching.
_COMMITTEE_MAP: dict[str, list[str]] = {
    "Audit": ["audit committee", "audit and finance committee"],
    "Compensation": [
        "compensation committee", "human resources committee",
        "human capital committee",
    ],
    "Nominating/Governance": [
        "nominating committee", "governance committee",
        "nominating and governance", "nominating and corporate governance",
    ],
    "Risk": ["risk committee", "risk management committee"],
}


# ---------------------------------------------------------------------------
# Board parsing from proxy text
# ---------------------------------------------------------------------------


def extract_board_from_proxy(
    proxy_text: str,
    state: AnalysisState,
) -> list[BoardForensicProfile]:
    """Parse proxy statement for director profiles."""
    if not proxy_text.strip():
        return []

    source = "DEF 14A proxy statement"
    blocks = _split_director_blocks(proxy_text)
    profiles = [_parse_director_block(n, b, source) for n, b in blocks]

    if not profiles:
        profiles = _fallback_director_extraction(proxy_text, source)

    # Completeness check: cross-reference extracted count against mentions
    # of "director nominees" or board size in the proxy text
    _check_board_completeness(proxy_text, profiles)
    return profiles


def _check_board_completeness(
    proxy_text: str,
    profiles: list[BoardForensicProfile],
) -> None:
    """Log a warning if proxy mentions more directors than we extracted.

    Searches for patterns like 'X director nominees', 'board of X directors',
    or 'our X-member board' and compares against extracted count.
    """
    text_lower = proxy_text.lower()
    expected = _extract_expected_board_size(text_lower)
    if expected is not None and expected > len(profiles) and len(profiles) > 0:
        logger.warning(
            "SECT5: Board completeness check: proxy mentions %d directors "
            "but only %d were extracted (potential drop: %d missing)",
            expected,
            len(profiles),
            expected - len(profiles),
        )


def _extract_expected_board_size(text_lower: str) -> int | None:
    """Extract expected board size from proxy text patterns."""
    patterns = [
        r"(\d{1,2})\s+director\s+nominees?",
        r"board\s+(?:of|consists?\s+of)\s+(\d{1,2})\s+(?:directors?|members?)",
        r"(\d{1,2})\s*-?\s*member\s+board",
        r"(\d{1,2})\s+nominees?\s+for\s+election",
    ]
    for pat in patterns:
        m = re.search(pat, text_lower)
        if m:
            val = int(m.group(1))
            if 3 <= val <= 25:
                return val
    return None


def _is_likely_person_name(candidate: str) -> bool:
    """Check if a string looks like a real person name."""
    parts = candidate.strip().split()
    if len(parts) < 2:
        return False
    # Every word must start with uppercase (or be ALL-CAPS).
    if not all(p[0].isupper() for p in parts if p):
        return False
    # Reject if any word is a known non-name word (case-insensitive).
    if any(p.lower() in _NON_NAME_WORDS for p in parts):
        return False
    # Reject if it matches a skip phrase (case-insensitive).
    candidate_title = candidate.title()
    if candidate_title in _SKIP_PHRASES:
        return False
    # Reject very short "names" (e.g., "At Or").
    if all(len(p) <= 3 for p in parts):
        return False
    # ALL-CAPS strings with 4+ words are likely headings, not names.
    if candidate == candidate.upper() and len(parts) > 3:
        return False
    return True


def _split_director_blocks(text: str) -> list[tuple[str, str]]:
    """Split proxy text into (name, bio_block) tuples.

    Handles both mixed-case ("Elon Musk") and ALL-CAPS ("ELON MUSK")
    director name formats commonly found in SEC proxy statements.
    """
    # Name pattern: mixed-case OR ALL-CAPS (2-5 words, space-separated).
    _name_pat = (
        r"(?:[A-Z][a-z]+(?:[ ]+[A-Z][a-z]+){1,4}"
        r"|[A-Z]{2,}(?:[ ]+[A-Z]{2,}){1,4})"
    )
    # Age pattern: "age 54", "Age 54", "Age: 54" (colon optional).
    _age_pat = r"(?:,?\s*(?:age|Age):?\s*(\d{2,3}))"

    pattern = (
        r"(?:^|\n)\s*(" + _name_pat + r")"
        r"(?:" + _age_pat + r")?"
        r"([\s\S]*?)(?=(?:\n\s*(?:" + _name_pat + r")"
        r"(?:" + _age_pat + r"))|$)"
    )
    results: list[tuple[str, str]] = []
    for m in re.findall(pattern, text):
        name = m[0].strip()
        block = m[2] if len(m) > 2 else ""
        # Normalize ALL-CAPS names to title case for display.
        display_name = name.title() if name == name.upper() else name
        if len(name) > 5 and _is_likely_person_name(name):
            results.append((display_name, str(block)))
    return results[:20]


def _parse_director_block(
    name: str, block: str, source: str,
) -> BoardForensicProfile:
    """Parse a single director's biographical block."""
    profile = BoardForensicProfile()
    profile.name = sourced_str(name, source, Confidence.HIGH)

    bl = block.lower()
    if "independent" in bl:
        is_ind = "not independent" not in bl and "non-independent" not in bl
        profile.is_independent = SourcedValue[bool](
            value=is_ind, source=source,
            confidence=Confidence.HIGH, as_of=now(),
        )
    elif "employee" in bl:
        profile.is_independent = SourcedValue[bool](
            value=False, source=source,
            confidence=Confidence.HIGH, as_of=now(),
        )

    tenure = _extract_director_tenure(block)
    if tenure is not None:
        profile.tenure_years = sourced_float(tenure, source, Confidence.MEDIUM)

    profile.committees = _extract_committees(block)

    other_boards = _extract_other_boards(block)
    for bn in other_boards:
        profile.other_boards.append(sourced_str(bn, source, Confidence.MEDIUM))
    profile.is_overboarded = (len(other_boards) + 1) >= 4

    _check_prior_litigation(profile, name, block, source)
    return profile


def _extract_director_tenure(block: str) -> float | None:
    """Extract director tenure in years from bio block."""
    from datetime import UTC, datetime

    patterns = [
        r"director since (\d{4})",
        r"member of (?:the |our )?board since (\d{4})",
        r"served (?:on|as) (?:the |our )?board since (\d{4})",
        r"appointed (?:to the board |as director )?in (\d{4})",
        r"joined (?:the |our )?board in (\d{4})",
    ]
    for pat in patterns:
        m = re.search(pat, block, re.IGNORECASE)
        if m:
            tenure = float(datetime.now(tz=UTC).year - int(m.group(1)))
            if 0 < tenure < 60:
                return tenure
    return None


def _extract_committees(block: str) -> list[str]:
    """Extract committee memberships from director block."""
    bl = block.lower()
    return [name for name, pats in _COMMITTEE_MAP.items() if any(p in bl for p in pats)]


def _extract_other_boards(block: str) -> list[str]:
    """Extract other public board seats from director bio."""
    boards: list[str] = []
    patterns = [
        r"(?:serves|served) on the (?:board|boards) of(?: directors of)?"
        r"\s+([A-Z][A-Za-z &.,]+(?:Inc\.|Corp\.|Co\.|Ltd\.)?)",
        r"director of\s+([A-Z][A-Za-z &.,]+(?:Inc\.|Corp\.|Co\.|Ltd\.)?)",
        r"board member of\s+([A-Z][A-Za-z &.,]+(?:Inc\.|Corp\.|Co\.|Ltd\.)?)",
    ]
    for pat in patterns:
        for m in re.findall(pat, block):
            bn = m.strip().rstrip(",. ")
            if bn and len(bn) > 3:
                boards.append(bn)
    return boards[:10]


def _check_prior_litigation(
    profile: BoardForensicProfile, name: str, block: str, source: str,
) -> None:
    """Check for prior litigation keywords in director bio."""
    bl = block.lower()
    for term in ("securities litigation", "class action", "sec enforcement",
                 "sec investigation", "restatement", "fraud", "settlement"):
        if term in bl:
            profile.prior_litigation.append(
                sourced_str(f"{name}: '{term}' found in bio", source, Confidence.LOW)
            )


def _fallback_director_extraction(
    text: str, source: str,
) -> list[BoardForensicProfile]:
    """Simple fallback: extract names from director nominee sections."""
    section = re.search(
        r"(?:nominees? for election|director nominees?)"
        r"([\s\S]{0,5000}?)(?:executive officers?|compensation)",
        text, re.IGNORECASE,
    )
    if not section:
        return []

    # Match mixed-case ("Elon Musk") and ALL-CAPS ("ELON MUSK") names.
    name_pattern = (
        r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b"
        r"|\b([A-Z]{2,}(?:\s+[A-Z]{2,}){1,3})\b"
    )
    seen: set[str] = set()
    profiles: list[BoardForensicProfile] = []
    for m in re.findall(name_pattern, section.group(1)):
        raw_name = (m[0] or m[1]).strip()
        # Normalize ALL-CAPS to title case for display.
        display_name = raw_name.title() if raw_name == raw_name.upper() else raw_name
        if display_name not in seen and _is_likely_person_name(raw_name):
            seen.add(display_name)
            p = BoardForensicProfile()
            p.name = sourced_str(display_name, source, Confidence.LOW)
            profiles.append(p)
    return profiles[:20]
