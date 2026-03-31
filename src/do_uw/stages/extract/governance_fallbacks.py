"""Governance extraction fallback helpers.

Split from extract_governance.py to stay under 500-line limit.
Contains: executive deduplication, tenure parsing, yfinance fallbacks.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from do_uw.models.common import Confidence
from do_uw.models.governance import BoardProfile
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    LeadershipForensicProfile,
    LeadershipStability,
)

if TYPE_CHECKING:
    from do_uw.models.state import AnalysisState

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Tenure parsing from bio text
# ------------------------------------------------------------------


def fill_tenure_from_bio(
    executives: list[LeadershipForensicProfile],
) -> None:
    """Parse tenure_years from bio_summary text patterns.

    LLM-extracted bios contain phrases like:
    - 'CEO since 2011' or 'CFO since January 2025'
    - 'Joined Apple in June 2013'
    - 'joined in 1998'
    - 'assumed current position in October 2024'
    When tenure_years is not set, this function parses the
    earliest year and computes tenure.
    """
    import re
    from datetime import UTC, datetime

    now_year = datetime.now(tz=UTC).year
    # Patterns ordered by specificity (most specific first)
    patterns = [
        # "since [Month] YYYY"
        re.compile(r"\bsince\s+(?:\w+\s+)?(\d{4})\b", re.IGNORECASE),
        # "joined [Company] [as/in] ... YYYY"
        re.compile(r"\bjoined\s+.{1,40}?(?:in\s+)?(?:\w+\s+)?(\d{4})\b", re.IGNORECASE),
        # "assumed [role] in [Month] YYYY" (for current position start)
        re.compile(r"\bassumed\s+.{1,30}?in\s+(?:\w+\s+)?(\d{4})\b", re.IGNORECASE),
        # "Transitioned from ... in [Month] YYYY"
        re.compile(r"\btransitioned\s+.{1,30}?in\s+(?:\w+\s+)?(\d{4})\b", re.IGNORECASE),
    ]

    for ep in executives:
        if ep.tenure_years is not None:
            continue
        bio = ep.bio_summary.value if ep.bio_summary and ep.bio_summary.value else ""
        if not bio:
            continue
        for pat in patterns:
            match = pat.search(bio)
            if match:
                start_year = int(match.group(1))
                if 1950 <= start_year <= now_year:
                    ep.tenure_years = round(now_year - start_year, 1)
                    break


# ------------------------------------------------------------------
# Executive deduplication
# ------------------------------------------------------------------


def dedup_executives(
    executives: list[LeadershipForensicProfile],
) -> list[LeadershipForensicProfile]:
    """Remove phantom/partial executive entries via substring name matching.

    When regex extracts "Cook" and LLM extracts "Tim Cook", keeps the
    longer/better entry. Preference order:
    1. Longer full name (2+ words over 1 word)
    2. More populated fields (title, tenure)
    3. Full title over abbreviation (Chief Executive Officer > CEO)
    """
    if len(executives) <= 1:
        return executives

    keep: list[LeadershipForensicProfile] = []
    removed_indices: set[int] = set()

    for i, exec_a in enumerate(executives):
        if i in removed_indices:
            continue
        name_a = (exec_a.name.value if exec_a.name and exec_a.name.value else "").strip()
        if not name_a:
            keep.append(exec_a)
            continue

        name_a_lower = name_a.lower()
        words_a = name_a.split()
        merged = exec_a

        for j, exec_b in enumerate(executives):
            if j <= i or j in removed_indices:
                continue
            name_b = (exec_b.name.value if exec_b.name and exec_b.name.value else "").strip()
            if not name_b:
                continue

            name_b_lower = name_b.lower()
            words_b = name_b.split()

            # Check if one name is a substring/suffix of the other
            is_substring = (
                name_a_lower in name_b_lower
                or name_b_lower in name_a_lower
            )
            if not is_substring:
                # Also check last-name match (handles "Cook" vs "Tim Cook")
                last_a = words_a[-1].lower() if words_a else ""
                last_b = words_b[-1].lower() if words_b else ""
                is_substring = last_a == last_b and last_a != ""

            if not is_substring:
                continue

            # These are likely the same person — keep the better entry
            merged = _pick_better_executive(merged, exec_b)
            removed_indices.add(j)

        keep.append(merged)

    if removed_indices:
        logger.info(
            "SECT5: Dedup removed %d phantom executive entries",
            len(removed_indices),
        )
    return keep


def _pick_better_executive(
    a: LeadershipForensicProfile,
    b: LeadershipForensicProfile,
) -> LeadershipForensicProfile:
    """Pick the better of two duplicate executive entries."""
    score_a = _executive_quality_score(a)
    score_b = _executive_quality_score(b)
    return a if score_a >= score_b else b


def _executive_quality_score(ep: LeadershipForensicProfile) -> int:
    """Score an executive entry by data quality (higher = better)."""
    score = 0
    name = ep.name.value if ep.name and ep.name.value else ""
    if len(name.split()) >= 2:
        score += 10
    title = ep.title.value if ep.title and ep.title.value else ""
    if title:
        score += 5
        if len(title) > 5:
            score += 3
    if ep.tenure_years is not None and ep.tenure_years < 40:
        score += 2
    if ep.prior_litigation:
        score += 1
    return score


# ------------------------------------------------------------------
# yfinance fallbacks
# ------------------------------------------------------------------


def get_yfinance_info(state: AnalysisState) -> dict[str, object]:
    """Get yfinance info dict from acquired_data."""
    if state.acquired_data is None:
        return {}
    raw = state.acquired_data.market_data.get("info", {})
    if isinstance(raw, dict):
        return raw  # type: ignore[return-value]
    return {}


def fill_executives_from_yfinance(
    state: AnalysisState, leadership: LeadershipStability
) -> None:
    """Populate executives from yfinance companyOfficers when proxy parsing fails."""
    from do_uw.stages.extract.sourced import sourced_str

    info = get_yfinance_info(state)
    officers = info.get("companyOfficers", [])
    if not isinstance(officers, list) or not officers:
        return

    for officer in officers:
        name = officer.get("name", "")
        title = officer.get("title", "")
        if not name or not title:
            continue
        title_upper = title.upper()
        if not any(
            k in title_upper
            for k in ("CEO", "CFO", "COO", "CHIEF", "GENERAL COUNSEL", "SECRETARY")
        ):
            continue

        profile = LeadershipForensicProfile(
            name=sourced_str(name, "yfinance companyOfficers", Confidence.MEDIUM),
            title=sourced_str(title, "yfinance companyOfficers", Confidence.MEDIUM),
        )
        total_pay = officer.get("totalPay")
        if total_pay is not None:
            profile.bio_summary = sourced_str(
                f"Total compensation: ${total_pay:,.0f}",
                "yfinance companyOfficers",
                Confidence.MEDIUM,
            )
        leadership.executives.append(profile)

    if leadership.executives:
        logger.info(
            "SECT5: Populated %d executives from yfinance companyOfficers",
            len(leadership.executives),
        )


def fill_directors_from_yfinance(
    state: AnalysisState,
) -> list[BoardForensicProfile]:
    """Create basic director profiles from yfinance companyOfficers as last resort.

    Only used when both LLM and regex extraction fail. Creates profiles for
    officers with board-related titles (Director, Board, Chairman).
    Returns MEDIUM confidence profiles — better than nothing for named board members.
    """
    from do_uw.stages.extract.sourced import sourced_str

    info = get_yfinance_info(state)
    officers = info.get("companyOfficers", [])
    if not isinstance(officers, list) or not officers:
        return []

    profiles: list[BoardForensicProfile] = []
    _BOARD_KEYWORDS = ("DIRECTOR", "BOARD", "CHAIRMAN", "CHAIRWOMAN", "CHAIR")
    # Also include CEO since they're often on the board
    _CEO_KEYWORDS = ("CEO", "CHIEF EXECUTIVE")

    for officer in officers:
        name = officer.get("name", "")
        title = officer.get("title", "")
        if not name or not title:
            continue
        title_upper = title.upper()
        is_board = any(k in title_upper for k in _BOARD_KEYWORDS)
        is_ceo = any(k in title_upper for k in _CEO_KEYWORDS)
        if not is_board and not is_ceo:
            continue

        src = "yfinance companyOfficers"
        profile = BoardForensicProfile(
            name=sourced_str(name, src, Confidence.MEDIUM),
            is_independent=None,  # Cannot determine from yfinance
        )
        profiles.append(profile)

    if profiles:
        logger.info(
            "SECT5: Populated %d board director profiles from yfinance companyOfficers",
            len(profiles),
        )
    return profiles


def fill_board_from_yfinance(
    state: AnalysisState, board: BoardProfile
) -> None:
    """Fill board fields from yfinance ISS governance scores.

    ISS provides boardRisk (1-10), compensationRisk, shareHolderRightsRisk,
    and overallRisk. Also checks companyOfficers for CEO/Chair duality.
    """
    from datetime import UTC, datetime

    from do_uw.models.common import SourcedValue

    info = get_yfinance_info(state)
    if not info:
        return

    src = "yfinance ISS governance scores"
    conf = Confidence.MEDIUM
    ts = datetime.now(tz=UTC)

    # CEO/Chair duality from companyOfficers
    officers = info.get("companyOfficers", [])
    if isinstance(officers, list):
        for officer in officers:
            title = str(officer.get("title", "")).upper()
            if "CEO" in title and "DIRECTOR" in title:
                board.ceo_chair_duality = SourcedValue[bool](
                    value=True, source=src, confidence=conf, as_of=ts
                )
                logger.info("SECT5: CEO/Chair duality detected from yfinance")
                break
        else:
            board.ceo_chair_duality = SourcedValue[bool](
                value=False, source=src, confidence=conf, as_of=ts
            )

    # ISS risk scores — populate BoardProfile fields
    _ISS_FIELDS: list[tuple[str, str]] = [
        ("auditRisk", "iss_audit_risk"),
        ("boardRisk", "iss_board_risk"),
        ("compensationRisk", "iss_compensation_risk"),
        ("shareHolderRightsRisk", "iss_shareholder_rights_risk"),
        ("overallRisk", "iss_overall_risk"),
    ]
    iss_populated = 0
    for info_key, model_attr in _ISS_FIELDS:
        raw_val = info.get(info_key)
        if raw_val is not None:
            try:
                int_val = int(float(raw_val))
                if 1 <= int_val <= 10:
                    setattr(
                        board,
                        model_attr,
                        SourcedValue[int](
                            value=int_val, source=src, confidence=conf, as_of=ts,
                        ),
                    )
                    iss_populated += 1
            except (ValueError, TypeError):
                pass
    if iss_populated > 0:
        logger.info(
            "SECT5: Populated %d ISS risk scores from yfinance",
            iss_populated,
        )


def fill_tenure_from_board(
    executives: list[LeadershipForensicProfile],
    board_forensics: list | None,
) -> None:
    """Cross-reference executive tenure from board member profiles.

    Many C-suite executives (especially CEO) also sit on the board.
    Board member tenure is reliably extracted from DEF 14A. When exec
    tenure_years is None, we match by name and use board tenure as proxy.
    """
    if not board_forensics:
        return

    from do_uw.models.governance_forensics import BoardForensicProfile

    # Build name→tenure lookup from board members
    board_tenure: dict[str, float] = {}
    for bf in board_forensics:
        if not isinstance(bf, BoardForensicProfile):
            continue
        name = (bf.name.value if bf.name and bf.name.value else "").strip().lower()
        if name and bf.tenure_years and bf.tenure_years.value is not None:
            board_tenure[name] = bf.tenure_years.value
            # Also index by last name for fuzzy matching
            parts = name.split()
            if len(parts) >= 2:
                board_tenure[parts[-1]] = bf.tenure_years.value

    if not board_tenure:
        return

    filled = 0
    for ep in executives:
        if ep.tenure_years is not None:
            continue
        name = (ep.name.value if ep.name and ep.name.value else "").strip().lower()
        if not name:
            continue
        # Try full name match first, then last name
        tenure = board_tenure.get(name)
        if tenure is None:
            parts = name.split()
            if len(parts) >= 2:
                tenure = board_tenure.get(parts[-1])
        if tenure is not None:
            ep.tenure_years = tenure
            filled += 1

    if filled:
        logger.info(
            "SECT5: Cross-referenced tenure for %d executives from board data",
            filled,
        )


# ------------------------------------------------------------------
# Post-extraction validation
# ------------------------------------------------------------------


def validate_executives(
    executives: list[LeadershipForensicProfile],
    *,
    ceo_name_hint: str | None = None,
) -> list[LeadershipForensicProfile]:
    """Validate and clean executive list after extraction.

    Guards against common extraction errors:
    1. Max 1 CEO: keep the one matching ceo_name_hint, or with best quality
    2. Max 1 per C-suite role: reject phantom duplicates
    3. Reject entries with no bio and suspiciously generic names
    """
    if not executives:
        return executives

    # Group by title
    by_title: dict[str, list[tuple[int, LeadershipForensicProfile]]] = {}
    for i, ep in enumerate(executives):
        title = (ep.title.value if ep.title and ep.title.value else "").upper()
        # Normalize title to short form
        if "CHIEF EXECUTIVE" in title or title == "CEO":
            key = "CEO"
        elif "CHIEF FINANCIAL" in title or title == "CFO":
            key = "CFO"
        elif "CHIEF OPERATING" in title or title == "COO":
            key = "COO"
        elif "GENERAL COUNSEL" in title or "CHIEF LEGAL" in title or title == "CLO":
            key = "CLO"
        else:
            key = title or "UNKNOWN"
        by_title.setdefault(key, []).append((i, ep))

    keep_indices: set[int] = set()

    for title_key, entries in by_title.items():
        if len(entries) == 1:
            keep_indices.add(entries[0][0])
            continue

        # Multiple entries for same title — pick the best one
        if title_key == "CEO" and ceo_name_hint:
            # Use LLM ceo_name as ground truth with strict matching:
            # Priority 1: Full name match ("Elon Musk" == "Elon Musk")
            # Priority 2: Last name + first initial ("E. Musk" ~ "Elon Musk")
            # Reject: Last name only ("Kimbal Musk" != "Elon Musk")
            hint_lower = ceo_name_hint.strip().lower()
            hint_parts = hint_lower.split()
            hint_last = hint_parts[-1] if hint_parts else hint_lower
            hint_first_char = hint_parts[0][0] if hint_parts else ""
            matched = None
            # Pass 1: exact full-name match
            for idx, ep in entries:
                name = (ep.name.value if ep.name and ep.name.value else "").lower()
                if name == hint_lower:
                    matched = (idx, ep)
                    break
            # Pass 2: last name + first initial match
            if not matched:
                for idx, ep in entries:
                    name = (ep.name.value if ep.name and ep.name.value else "").lower()
                    name_parts = name.split()
                    name_last = name_parts[-1] if name_parts else name
                    name_first_char = name_parts[0][0] if name_parts else ""
                    if (
                        name_last == hint_last
                        and name_first_char == hint_first_char
                        and hint_first_char
                    ):
                        matched = (idx, ep)
                        break
            if matched:
                keep_indices.add(matched[0])
                removed_names = [
                    ep.name.value for idx, ep in entries
                    if idx != matched[0] and ep.name and ep.name.value
                ]
                if removed_names:
                    logger.warning(
                        "SECT5: Rejected %d duplicate CEO(s): %s "
                        "(kept %s per LLM ceo_name)",
                        len(removed_names),
                        ", ".join(removed_names),
                        matched[1].name.value if matched[1].name else "?",
                    )
                continue
            # No match at all — none of these are the real CEO.
            # Reject all rather than keep the wrong person.
            all_names = [
                ep.name.value for _, ep in entries
                if ep.name and ep.name.value
            ]
            logger.warning(
                "SECT5: Rejected ALL %d CEO candidates %s — "
                "none match LLM ceo_name '%s'",
                len(entries),
                all_names,
                ceo_name_hint,
            )
            continue

        # No ceo_name hint or non-CEO title — pick by quality score
        best_idx, best_ep = max(
            entries, key=lambda t: _executive_quality_score(t[1]),
        )
        keep_indices.add(best_idx)
        removed_count = len(entries) - 1
        if removed_count > 0:
            logger.warning(
                "SECT5: Rejected %d duplicate %s entries (kept %s)",
                removed_count,
                title_key,
                best_ep.name.value if best_ep.name else "?",
            )

    result = [ep for i, ep in enumerate(executives) if i in keep_indices]

    removed = len(executives) - len(result)
    if removed:
        logger.info(
            "SECT5: Validation removed %d phantom executive entries "
            "(%d → %d)",
            removed,
            len(executives),
            len(result),
        )
    return result


__all__ = [
    "dedup_executives",
    "fill_board_from_yfinance",
    "fill_directors_from_yfinance",
    "fill_executives_from_yfinance",
    "fill_tenure_from_bio",
    "fill_tenure_from_board",
    "get_yfinance_info",
    "validate_executives",
]
