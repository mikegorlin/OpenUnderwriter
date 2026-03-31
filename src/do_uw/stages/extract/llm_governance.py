"""Governance converter: DEF14AExtraction -> GovernanceData sub-models.

Maps flat LLM-extracted proxy statement fields into rich domain models
consumed by the scoring engine and worksheet renderer. Every field gets
HIGH confidence and 'DEF 14A (LLM)' source attribution.

Public functions:
- convert_directors       -> list[BoardForensicProfile]
- convert_board_profile   -> BoardProfile
- convert_compensation    -> CompensationAnalysis
- convert_compensation_flags -> CompensationFlags
- convert_ownership_from_proxy -> OwnershipAnalysis
- convert_neos_to_leaders -> list[LeadershipForensicProfile]
"""

from __future__ import annotations

import logging
import re
import statistics

from do_uw.models.common import Confidence, SourcedValue

logger = logging.getLogger(__name__)
from do_uw.models.governance import BoardProfile, CompensationFlags
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    LeadershipForensicProfile,
    OwnershipAnalysis,
)
from do_uw.stages.extract.leadership_parsing import is_valid_person_name
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.sourced import (
    now,
    sourced_float,
    sourced_int,
    sourced_str,
)

_LLM_SOURCE = "DEF 14A (LLM)"

# Regex patterns for CEO pay ratio parsing.
_PAY_RATIO_COLON = re.compile(r"^\s*([\d,]+(?:\.\d+)?)\s*:\s*1\s*$")
_PAY_RATIO_TO = re.compile(r"^\s*([\d,]+(?:\.\d+)?)\s+to\s+1\s*$", re.IGNORECASE)
_PAY_RATIO_BARE = re.compile(r"^\s*([\d,]+(?:\.\d+)?)\s*$")

# Overboarding threshold: 4+ total public board seats.
_OVERBOARD_THRESHOLD = 4


def _sourced_bool(value: bool) -> SourcedValue[bool]:
    """Create a SourcedValue[bool] with LLM source and HIGH confidence."""
    return SourcedValue[bool](
        value=value,
        source=_LLM_SOURCE,
        confidence=Confidence.HIGH,
        as_of=now(),
    )


def _parse_pay_ratio(ratio_str: str | None) -> float | None:
    """Parse CEO pay ratio string to a float.

    Accepts formats: "123:1", "123 to 1", or bare "123".
    Returns None on parse failure or None input.
    """
    if ratio_str is None:
        return None
    # Try "123:1" format.
    m = _PAY_RATIO_COLON.match(ratio_str)
    if m:
        return float(m.group(1).replace(",", ""))
    # Try "123 to 1" format.
    m = _PAY_RATIO_TO.match(ratio_str)
    if m:
        return float(m.group(1).replace(",", ""))
    # Try bare number.
    m = _PAY_RATIO_BARE.match(ratio_str)
    if m:
        return float(m.group(1).replace(",", ""))
    return None


def convert_directors(
    extraction: DEF14AExtraction,
) -> list[BoardForensicProfile]:
    """Convert extracted directors to BoardForensicProfile list.

    Validates director names using is_valid_person_name() to reject
    LLM hallucinations, section headers, and non-name strings.
    Validates tenure bounds (0-50 years). Computes overboarding from
    other_boards count (4+ total public boards = overboarded).
    """
    profiles: list[BoardForensicProfile] = []
    rejected = 0
    for d in extraction.directors:
        if not d.name or not d.name.strip():
            continue
        # Validate name looks like an actual person
        if not is_valid_person_name(d.name.strip()):
            rejected += 1
            continue
        # Validate tenure bounds (0-50 years)
        tenure = d.tenure_years
        if tenure is not None and (tenure < 0 or tenure > 50):
            logger.warning(
                "SECT5: Rejecting unreasonable board tenure %.1f for %s",
                tenure, d.name,
            )
            tenure = None
        profile = BoardForensicProfile(
            name=sourced_str(d.name, _LLM_SOURCE, Confidence.HIGH),
            tenure_years=(
                sourced_float(tenure, _LLM_SOURCE, Confidence.HIGH)
                if tenure is not None
                else None
            ),
            is_independent=(
                _sourced_bool(d.independent) if d.independent is not None else None
            ),
            committees=list(d.committees),
            other_boards=[
                sourced_str(b, _LLM_SOURCE, Confidence.HIGH) for b in d.other_boards
            ],
            is_overboarded=(len(d.other_boards) + 1) >= _OVERBOARD_THRESHOLD,
            qualifications=(
                sourced_str(d.qualifications, _LLM_SOURCE, Confidence.HIGH)
                if d.qualifications
                else None
            ),
            qualification_tags=list(d.qualification_tags),
            age=(
                sourced_int(d.age, _LLM_SOURCE, Confidence.MEDIUM)
                if d.age is not None
                else None
            ),
        )
        profiles.append(profile)
    if rejected:
        logger.warning(
            "SECT5: Rejected %d director names that failed person-name validation",
            rejected,
        )
    # Sanity: board size should be 3-25. If wildly off, data may be garbage.
    if len(profiles) > 25:
        logger.warning(
            "SECT5: LLM extracted %d directors (>25) — likely parsing error, "
            "truncating to first 25",
            len(profiles),
        )
        profiles = profiles[:25]
    return profiles


def convert_board_profile(
    extraction: DEF14AExtraction,
    company_name: str | None = None,
) -> BoardProfile:
    """Convert extraction metadata to aggregate BoardProfile.

    Computes independence_ratio from independent_count / board_size,
    avg_tenure from director tenure values, and overboarded_count
    from directors with 4+ total board seats.

    company_name is accepted for callsite compatibility but not used
    by this function (context is embedded in _LLM_SOURCE).
    """
    # Sanity: board size 3-25 for public companies.
    size: SourcedValue[int] | None = None
    if extraction.board_size is not None:
        if 3 <= extraction.board_size <= 25:
            size = sourced_int(extraction.board_size, _LLM_SOURCE, Confidence.HIGH)
        else:
            logger.warning(
                "SECT5: Rejecting unreasonable board_size=%d",
                extraction.board_size,
            )

    independence_ratio: SourcedValue[float] | None = None
    if (
        extraction.independent_count is not None
        and extraction.board_size is not None
        and extraction.board_size > 0
    ):
        ratio = extraction.independent_count / extraction.board_size
        if 0 <= ratio <= 1:
            independence_ratio = sourced_float(ratio, _LLM_SOURCE, Confidence.HIGH)

    # Compute average tenure from directors with tenure data.
    tenures = [
        d.tenure_years
        for d in extraction.directors
        if d.tenure_years is not None
    ]
    avg_tenure: SourcedValue[float] | None = None
    if tenures:
        avg_tenure = sourced_float(
            statistics.mean(tenures), _LLM_SOURCE, Confidence.HIGH
        )

    ceo_chair: SourcedValue[bool] | None = None
    if extraction.ceo_chair_combined is not None:
        ceo_chair = _sourced_bool(extraction.ceo_chair_combined)

    # Count overboarded directors.
    overboarded = sum(
        1
        for d in extraction.directors
        if (len(d.other_boards) + 1) >= _OVERBOARD_THRESHOLD
    )
    overboarded_sv: SourcedValue[int] | None = sourced_int(
        overboarded, _LLM_SOURCE, Confidence.HIGH
    )

    classified: SourcedValue[bool] | None = None
    if extraction.classified_board is not None:
        classified = _sourced_bool(extraction.classified_board)

    # Board attendance (sanity: 0-100%)
    board_attendance_pct_sv: SourcedValue[float] | None = None
    if extraction.board_attendance_pct is not None:
        if 0.0 <= extraction.board_attendance_pct <= 100.0:
            board_attendance_pct_sv = sourced_float(
                extraction.board_attendance_pct, _LLM_SOURCE, Confidence.HIGH
            )

    board_meetings_held_sv: SourcedValue[int] | None = None
    if extraction.board_meetings_held is not None:
        board_meetings_held_sv = sourced_int(
            extraction.board_meetings_held, _LLM_SOURCE, Confidence.HIGH
        )

    directors_below_75_sv: SourcedValue[int] | None = None
    if extraction.directors_below_75_pct_attendance is not None:
        directors_below_75_sv = sourced_int(
            extraction.directors_below_75_pct_attendance, _LLM_SOURCE, Confidence.HIGH
        )

    # Diversity (sanity: 0-100%)
    board_gender_diversity_pct_sv: SourcedValue[float] | None = None
    if extraction.board_gender_diversity_pct is not None:
        if 0.0 <= extraction.board_gender_diversity_pct <= 100.0:
            board_gender_diversity_pct_sv = sourced_float(
                extraction.board_gender_diversity_pct, _LLM_SOURCE, Confidence.HIGH
            )

    board_racial_diversity_pct_sv: SourcedValue[float] | None = None
    if extraction.board_racial_diversity_pct is not None:
        if 0.0 <= extraction.board_racial_diversity_pct <= 100.0:
            board_racial_diversity_pct_sv = sourced_float(
                extraction.board_racial_diversity_pct, _LLM_SOURCE, Confidence.HIGH
            )

    # Anti-takeover provisions
    poison_pill_sv: SourcedValue[bool] | None = None
    if extraction.poison_pill is not None:
        poison_pill_sv = _sourced_bool(extraction.poison_pill)

    supermajority_sv: SourcedValue[bool] | None = None
    if extraction.supermajority_voting is not None:
        supermajority_sv = _sourced_bool(extraction.supermajority_voting)

    blank_check_sv: SourcedValue[bool] | None = None
    if extraction.blank_check_preferred is not None:
        blank_check_sv = _sourced_bool(extraction.blank_check_preferred)

    forum_clause_sv: SourcedValue[str] | None = None
    if extraction.forum_selection_clause is not None:
        forum_clause_sv = sourced_str(
            extraction.forum_selection_clause, _LLM_SOURCE, Confidence.HIGH
        )

    exclusive_forum_sv: SourcedValue[bool] | None = None
    if extraction.exclusive_forum_provision is not None:
        exclusive_forum_sv = _sourced_bool(extraction.exclusive_forum_provision)

    shareholder_proposal_count_sv: SourcedValue[int] | None = None
    if extraction.shareholder_proposal_count is not None:
        shareholder_proposal_count_sv = sourced_int(
            extraction.shareholder_proposal_count, _LLM_SOURCE, Confidence.HIGH
        )

    # Additional governance provisions (new fields)
    proxy_access_sv: SourcedValue[str] | None = None
    if hasattr(extraction, "proxy_access_threshold") and extraction.proxy_access_threshold:
        proxy_access_sv = sourced_str(
            extraction.proxy_access_threshold, _LLM_SOURCE, Confidence.HIGH
        )

    special_mtg_sv: SourcedValue[str] | None = None
    if hasattr(extraction, "special_meeting_threshold") and extraction.special_meeting_threshold:
        special_mtg_sv = sourced_str(
            extraction.special_meeting_threshold, _LLM_SOURCE, Confidence.HIGH
        )

    written_consent_sv: SourcedValue[bool] | None = None
    if hasattr(extraction, "written_consent_allowed") and extraction.written_consent_allowed is not None:
        written_consent_sv = _sourced_bool(extraction.written_consent_allowed)

    bylaw_sv: SourcedValue[str] | None = None
    if hasattr(extraction, "bylaw_amendment_provisions") and extraction.bylaw_amendment_provisions:
        bylaw_sv = sourced_str(
            extraction.bylaw_amendment_provisions, _LLM_SOURCE, Confidence.HIGH
        )

    succession_sv: SourcedValue[bool] | None = None
    if hasattr(extraction, "ceo_succession_plan") and extraction.ceo_succession_plan is not None:
        succession_sv = _sourced_bool(extraction.ceo_succession_plan)

    hedging_sv: SourcedValue[bool] | None = None
    if hasattr(extraction, "hedging_prohibition") and extraction.hedging_prohibition is not None:
        hedging_sv = _sourced_bool(extraction.hedging_prohibition)

    pledging_sv: SourcedValue[bool] | None = None
    if hasattr(extraction, "pledging_prohibition") and extraction.pledging_prohibition is not None:
        pledging_sv = _sourced_bool(extraction.pledging_prohibition)

    return BoardProfile(
        size=size,
        independence_ratio=independence_ratio,
        avg_tenure_years=avg_tenure,
        ceo_chair_duality=ceo_chair,
        overboarded_count=overboarded_sv,
        classified_board=classified,
        board_attendance_pct=board_attendance_pct_sv,
        board_meetings_held=board_meetings_held_sv,
        directors_below_75_pct_attendance=directors_below_75_sv,
        board_gender_diversity_pct=board_gender_diversity_pct_sv,
        board_racial_diversity_pct=board_racial_diversity_pct_sv,
        poison_pill=poison_pill_sv,
        supermajority_voting=supermajority_sv,
        blank_check_preferred=blank_check_sv,
        forum_selection_clause=forum_clause_sv,
        exclusive_forum_provision=exclusive_forum_sv,
        shareholder_proposal_count=shareholder_proposal_count_sv,
        proxy_access_threshold=proxy_access_sv,
        special_meeting_threshold=special_mtg_sv,
        written_consent_allowed=written_consent_sv,
        bylaw_amendment_provisions=bylaw_sv,
        ceo_succession_plan=succession_sv,
        hedging_prohibition=hedging_sv,
        pledging_prohibition=pledging_sv,
    )


def _is_ceo(title: str | None) -> bool:
    """Check if a title indicates the Chief Executive Officer."""
    if title is None:
        return False
    upper = title.upper()
    return "CEO" in upper or "CHIEF EXECUTIVE" in upper


def convert_compensation(extraction: DEF14AExtraction) -> CompensationAnalysis:
    """Convert NEO compensation data to CompensationAnalysis.

    Identifies the CEO among named_executive_officers by title matching.
    Populates salary, bonus, equity (stock + options), other, and total.
    """
    ceo_salary: SourcedValue[float] | None = None
    ceo_bonus: SourcedValue[float] | None = None
    ceo_equity: SourcedValue[float] | None = None
    ceo_other: SourcedValue[float] | None = None
    ceo_total: SourcedValue[float] | None = None

    # Find CEO among NEOs.
    for neo in extraction.named_executive_officers:
        if _is_ceo(neo.title):
            if neo.salary is not None:
                ceo_salary = sourced_float(
                    neo.salary, _LLM_SOURCE, Confidence.HIGH
                )
            if neo.bonus is not None:
                ceo_bonus = sourced_float(
                    neo.bonus, _LLM_SOURCE, Confidence.HIGH
                )
            # Equity = stock_awards + option_awards.
            stock = neo.stock_awards or 0.0
            options = neo.option_awards or 0.0
            equity_total = stock + options
            if neo.stock_awards is not None or neo.option_awards is not None:
                ceo_equity = sourced_float(
                    equity_total, _LLM_SOURCE, Confidence.HIGH
                )
            if neo.other_comp is not None:
                ceo_other = sourced_float(
                    neo.other_comp, _LLM_SOURCE, Confidence.HIGH
                )
            if neo.total_comp is not None:
                ceo_total = sourced_float(
                    neo.total_comp, _LLM_SOURCE, Confidence.HIGH
                )
            break

    # Pay ratio (sanity: 1-5000 range — highest real ratios ~3000:1).
    pay_ratio_val = _parse_pay_ratio(extraction.ceo_pay_ratio)
    ceo_pay_ratio: SourcedValue[float] | None = None
    if pay_ratio_val is not None:
        if 1 <= pay_ratio_val <= 5000:
            ceo_pay_ratio = sourced_float(
                pay_ratio_val, _LLM_SOURCE, Confidence.HIGH
            )
        else:
            logger.warning(
                "SECT5: Rejecting unreasonable pay ratio %.0f:1", pay_ratio_val,
            )

    # Say-on-pay (sanity: 0-100%).
    say_on_pay: SourcedValue[float] | None = None
    if extraction.say_on_pay_approval_pct is not None:
        sop = extraction.say_on_pay_approval_pct
        if 0 <= sop <= 100:
            say_on_pay = sourced_float(sop, _LLM_SOURCE, Confidence.HIGH)
        else:
            logger.warning(
                "SECT5: Rejecting unreasonable say-on-pay %.1f%%", sop,
            )

    # Clawback fields.
    has_clawback: SourcedValue[bool] | None = None
    if extraction.has_clawback is not None:
        has_clawback = _sourced_bool(extraction.has_clawback)

    clawback_scope: SourcedValue[str] | None = None
    if extraction.clawback_scope is not None:
        clawback_scope = sourced_str(
            extraction.clawback_scope, _LLM_SOURCE, Confidence.HIGH
        )

    return CompensationAnalysis(
        ceo_salary=ceo_salary,
        ceo_bonus=ceo_bonus,
        ceo_equity=ceo_equity,
        ceo_other=ceo_other,
        ceo_total_comp=ceo_total,
        ceo_pay_ratio=ceo_pay_ratio,
        say_on_pay_pct=say_on_pay,
        has_clawback=has_clawback,
        clawback_scope=clawback_scope,
    )


def convert_compensation_flags(
    extraction: DEF14AExtraction,
) -> CompensationFlags:
    """Convert extraction fields to CompensationFlags.

    Populates say-on-pay support %, CEO pay ratio, and golden parachute
    value from DEF 14A proxy statement data.
    """
    say_on_pay: SourcedValue[float] | None = None
    if extraction.say_on_pay_approval_pct is not None:
        sop = extraction.say_on_pay_approval_pct
        if 0 <= sop <= 100:
            say_on_pay = sourced_float(sop, _LLM_SOURCE, Confidence.HIGH)

    pay_ratio_val = _parse_pay_ratio(extraction.ceo_pay_ratio)
    ceo_pay_ratio: SourcedValue[float] | None = None
    if pay_ratio_val is not None and 1 <= pay_ratio_val <= 5000:
        ceo_pay_ratio = sourced_float(
            pay_ratio_val, _LLM_SOURCE, Confidence.HIGH
        )

    golden_parachute: SourcedValue[float] | None = None
    if extraction.golden_parachute_total is not None:
        gp = extraction.golden_parachute_total
        # Sanity: golden parachutes range $0 to ~$500M
        if 0 <= gp <= 500_000_000:
            golden_parachute = sourced_float(gp, _LLM_SOURCE, Confidence.HIGH)
        else:
            logger.warning(
                "SECT5: Rejecting unreasonable golden parachute $%.0f", gp,
            )

    return CompensationFlags(
        say_on_pay_support_pct=say_on_pay,
        ceo_pay_ratio=ceo_pay_ratio,
        golden_parachute_value=golden_parachute,
    )


def convert_ownership_from_proxy(
    extraction: DEF14AExtraction,
) -> OwnershipAnalysis:
    """Convert proxy ownership data to OwnershipAnalysis.

    Only populates insider_pct from the proxy statement. Institutional
    ownership comes from yfinance, activist data from 13D/G extractors.
    """
    insider_pct: SourcedValue[float] | None = None
    if extraction.officers_directors_ownership_pct is not None:
        insider_pct = sourced_float(
            extraction.officers_directors_ownership_pct,
            _LLM_SOURCE,
            Confidence.HIGH,
        )
    return OwnershipAnalysis(insider_pct=insider_pct)


def convert_neos_to_leaders(
    extraction: DEF14AExtraction,
) -> list[LeadershipForensicProfile]:
    """Convert NEOs to LeadershipForensicProfile list.

    Creates supplemental leadership profiles from proxy statement data.
    These supplement (not replace) profiles from the leadership extractor.
    """
    leaders: list[LeadershipForensicProfile] = []
    for neo in extraction.named_executive_officers:
        if not neo.name or not neo.name.strip():
            continue
        if not is_valid_person_name(neo.name.strip()):
            continue
        # Prefer background (experience/qualifications) over source_passage (comp data)
        bio_text = neo.background if hasattr(neo, "background") and neo.background else ""
        if not bio_text and neo.source_passage:
            bio_text = neo.source_passage
        profile = LeadershipForensicProfile(
            name=sourced_str(neo.name, _LLM_SOURCE, Confidence.HIGH),
            title=(
                sourced_str(neo.title, _LLM_SOURCE, Confidence.HIGH)
                if neo.title
                else None
            ),
            bio_summary=(
                sourced_str(bio_text, _LLM_SOURCE, Confidence.HIGH)
                if bio_text
                else None
            ),
        )
        leaders.append(profile)
    return leaders
