"""Unit tests for the governance converter module.

Tests all converter functions that map DEF14AExtraction fields to
GovernanceData sub-models (BoardForensicProfile, CompensationAnalysis,
BoardProfile, CompensationFlags, OwnershipAnalysis, LeadershipForensicProfile).
"""

from __future__ import annotations

from do_uw.models.common import Confidence
from do_uw.stages.extract.llm.schemas.common import (
    ExtractedCompensation,
    ExtractedDirector,
)
from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction
from do_uw.stages.extract.llm_governance import (
    _parse_pay_ratio,
    convert_board_profile,
    convert_compensation,
    convert_compensation_flags,
    convert_directors,
    convert_neos_to_leaders,
    convert_ownership_from_proxy,
)

_SOURCE = "DEF 14A (LLM)"


def _sample_def14a() -> DEF14AExtraction:
    """Build a realistic DEF14AExtraction for testing."""
    return DEF14AExtraction(
        directors=[
            ExtractedDirector(
                name="Alice Johnson",
                age=58,
                independent=True,
                tenure_years=6.0,
                committees=["Audit", "Nominating"],
                other_boards=["Acme Corp"],
            ),
            ExtractedDirector(
                name="Bob Smith",
                age=62,
                independent=False,
                tenure_years=12.0,
                committees=["Compensation"],
                other_boards=["Initech", "Globex", "Umbrella Corp"],
            ),
            ExtractedDirector(
                name="Carol Lee",
                age=45,
                independent=True,
                tenure_years=1.5,
                committees=["Audit"],
                other_boards=[],
            ),
        ],
        board_size=9,
        independent_count=7,
        classified_board=False,
        ceo_chair_combined=True,
        ceo_name="Bob Smith",
        named_executive_officers=[
            ExtractedCompensation(
                name="Bob Smith",
                title="Chairman and CEO",
                salary=1_500_000.0,
                bonus=750_000.0,
                stock_awards=5_000_000.0,
                option_awards=2_000_000.0,
                non_equity_incentive=1_200_000.0,
                other_comp=150_000.0,
                total_comp=10_600_000.0,
                source_passage="See Summary Compensation Table",
            ),
            ExtractedCompensation(
                name="Diana Prince",
                title="Chief Financial Officer",
                salary=800_000.0,
                bonus=400_000.0,
                stock_awards=2_000_000.0,
                option_awards=500_000.0,
                other_comp=50_000.0,
                total_comp=3_750_000.0,
                source_passage="CFO compensation details",
            ),
        ],
        ceo_pay_ratio="275:1",
        say_on_pay_approval_pct=92.3,
        golden_parachute_total=25_000_000.0,
        officers_directors_ownership_pct=4.7,
        has_clawback=True,
        clawback_scope="BROADER",
    )


# ---------------------------------------------------------------
# convert_directors tests
# ---------------------------------------------------------------


def test_convert_directors_basic() -> None:
    """Three directors convert with correct names, independence, committees."""
    extraction = _sample_def14a()
    profiles = convert_directors(extraction)

    assert len(profiles) == 3

    alice = profiles[0]
    assert alice.name is not None
    assert alice.name.value == "Alice Johnson"
    assert alice.is_independent is not None
    assert alice.is_independent.value is True
    assert alice.committees == ["Audit", "Nominating"]
    assert alice.is_overboarded is False  # 1 other + 1 this = 2, < 4

    bob = profiles[1]
    assert bob.name is not None
    assert bob.name.value == "Bob Smith"
    assert bob.is_independent is not None
    assert bob.is_independent.value is False
    assert bob.is_overboarded is True  # 3 other + 1 this = 4, >= 4

    carol = profiles[2]
    assert carol.name is not None
    assert carol.name.value == "Carol Lee"
    assert carol.tenure_years is not None
    assert carol.tenure_years.value == 1.5
    assert carol.is_overboarded is False  # 0 other + 1 this = 1, < 4


def test_convert_directors_skips_empty_name() -> None:
    """Directors with empty name are skipped."""
    extraction = DEF14AExtraction(
        directors=[
            ExtractedDirector(name="", independent=True, tenure_years=5.0),
            ExtractedDirector(name="  ", independent=True, tenure_years=3.0),
            ExtractedDirector(name="Valid Name", independent=True),
        ],
    )
    profiles = convert_directors(extraction)

    assert len(profiles) == 1
    assert profiles[0].name is not None
    assert profiles[0].name.value == "Valid Name"


def test_convert_directors_qualification_tags() -> None:
    """qualification_tags mapped from ExtractedDirector to BoardForensicProfile."""
    extraction = DEF14AExtraction(
        directors=[
            ExtractedDirector(
                name="Alice Johnson",
                age=58,
                independent=True,
                qualification_tags=["financial_expert", "prior_c_suite"],
            ),
            ExtractedDirector(
                name="Bob Smith",
                age=62,
                independent=False,
                qualification_tags=[],
            ),
            ExtractedDirector(
                name="Carol Lee",
                age=45,
                independent=True,
                qualification_tags=["industry_expertise", "technology", "public_company_experience"],
            ),
        ],
    )
    profiles = convert_directors(extraction)

    assert len(profiles) == 3

    # Alice: multiple tags
    assert profiles[0].qualification_tags == ["financial_expert", "prior_c_suite"]

    # Bob: empty tags (should be empty list, not None)
    assert profiles[1].qualification_tags == []
    assert isinstance(profiles[1].qualification_tags, list)

    # Carol: three tags
    assert profiles[2].qualification_tags == [
        "industry_expertise", "technology", "public_company_experience"
    ]


def test_convert_directors_age_mapping() -> None:
    """Age mapped from ExtractedDirector to BoardForensicProfile with MEDIUM confidence."""
    extraction = DEF14AExtraction(
        directors=[
            ExtractedDirector(
                name="Alice Johnson",
                age=58,
                independent=True,
            ),
            ExtractedDirector(
                name="Bob Smith",
                age=None,  # No age
                independent=False,
            ),
        ],
    )
    profiles = convert_directors(extraction)

    assert len(profiles) == 2

    # Alice: age populated with MEDIUM confidence
    assert profiles[0].age is not None
    assert profiles[0].age.value == 58
    assert profiles[0].age.source == _SOURCE
    assert profiles[0].age.confidence == Confidence.MEDIUM

    # Bob: age is None when not provided
    assert profiles[1].age is None


def test_convert_directors_sourced_values() -> None:
    """All SourcedValue fields have correct source and confidence."""
    extraction = _sample_def14a()
    profiles = convert_directors(extraction)

    alice = profiles[0]

    # name SourcedValue
    assert alice.name is not None
    assert alice.name.source == _SOURCE
    assert alice.name.confidence == Confidence.HIGH

    # tenure_years SourcedValue
    assert alice.tenure_years is not None
    assert alice.tenure_years.source == _SOURCE
    assert alice.tenure_years.confidence == Confidence.HIGH

    # is_independent SourcedValue
    assert alice.is_independent is not None
    assert alice.is_independent.source == _SOURCE
    assert alice.is_independent.confidence == Confidence.HIGH

    # other_boards SourcedValue list
    assert len(alice.other_boards) == 1
    assert alice.other_boards[0].source == _SOURCE
    assert alice.other_boards[0].confidence == Confidence.HIGH
    assert alice.other_boards[0].value == "Acme Corp"


# ---------------------------------------------------------------
# convert_board_profile tests
# ---------------------------------------------------------------


def test_convert_board_profile() -> None:
    """Board profile has correct aggregate metrics."""
    extraction = _sample_def14a()
    profile = convert_board_profile(extraction)

    assert profile.size is not None
    assert profile.size.value == 9

    assert profile.independence_ratio is not None
    assert abs(profile.independence_ratio.value - 7 / 9) < 0.001

    # avg tenure: (6.0 + 12.0 + 1.5) / 3 = 6.5
    assert profile.avg_tenure_years is not None
    assert abs(profile.avg_tenure_years.value - 6.5) < 0.001

    assert profile.ceo_chair_duality is not None
    assert profile.ceo_chair_duality.value is True

    assert profile.overboarded_count is not None
    assert profile.overboarded_count.value == 1  # Bob with 3 other boards

    assert profile.classified_board is not None
    assert profile.classified_board.value is False


def test_convert_board_profile_handles_missing() -> None:
    """When board_size is None, size and independence_ratio stay None."""
    extraction = DEF14AExtraction()  # All defaults (None)
    profile = convert_board_profile(extraction)

    assert profile.size is None
    assert profile.independence_ratio is None
    assert profile.avg_tenure_years is None  # No directors
    assert profile.ceo_chair_duality is None
    assert profile.classified_board is None
    # overboarded_count is 0 (computed from empty director list)
    assert profile.overboarded_count is not None
    assert profile.overboarded_count.value == 0


# ---------------------------------------------------------------
# convert_compensation tests
# ---------------------------------------------------------------


def test_convert_compensation_ceo_found() -> None:
    """CEO identified by title, salary/bonus/equity/total populated."""
    extraction = _sample_def14a()
    comp = convert_compensation(extraction)

    assert comp.ceo_salary is not None
    assert comp.ceo_salary.value == 1_500_000.0

    assert comp.ceo_bonus is not None
    assert comp.ceo_bonus.value == 750_000.0

    # equity = stock_awards (5M) + option_awards (2M) = 7M
    assert comp.ceo_equity is not None
    assert comp.ceo_equity.value == 7_000_000.0

    assert comp.ceo_other is not None
    assert comp.ceo_other.value == 150_000.0

    assert comp.ceo_total_comp is not None
    assert comp.ceo_total_comp.value == 10_600_000.0

    # Verify sourced values
    assert comp.ceo_salary.source == _SOURCE
    assert comp.ceo_salary.confidence == Confidence.HIGH


def test_convert_compensation_no_ceo() -> None:
    """When no NEO has CEO in title, ceo fields stay None."""
    extraction = DEF14AExtraction(
        named_executive_officers=[
            ExtractedCompensation(
                name="Jane Doe",
                title="Chief Financial Officer",
                salary=500_000.0,
                total_comp=2_000_000.0,
            ),
        ],
    )
    comp = convert_compensation(extraction)

    assert comp.ceo_salary is None
    assert comp.ceo_bonus is None
    assert comp.ceo_equity is None
    assert comp.ceo_total_comp is None


def test_convert_compensation_pay_ratio() -> None:
    """CEO pay ratio '275:1' parsed to 275.0."""
    extraction = _sample_def14a()
    comp = convert_compensation(extraction)

    assert comp.ceo_pay_ratio is not None
    assert comp.ceo_pay_ratio.value == 275.0
    assert comp.ceo_pay_ratio.source == _SOURCE


def test_convert_compensation_clawback() -> None:
    """Clawback fields populated from extraction."""
    extraction = _sample_def14a()
    comp = convert_compensation(extraction)

    assert comp.has_clawback is not None
    assert comp.has_clawback.value is True
    assert comp.has_clawback.source == _SOURCE
    assert comp.has_clawback.confidence == Confidence.HIGH

    assert comp.clawback_scope is not None
    assert comp.clawback_scope.value == "BROADER"


# ---------------------------------------------------------------
# convert_compensation_flags tests
# ---------------------------------------------------------------


def test_convert_compensation_flags() -> None:
    """CompensationFlags: say-on-pay, pay ratio, golden parachute."""
    extraction = _sample_def14a()
    flags = convert_compensation_flags(extraction)

    assert flags.say_on_pay_support_pct is not None
    assert flags.say_on_pay_support_pct.value == 92.3
    assert flags.say_on_pay_support_pct.source == _SOURCE

    assert flags.ceo_pay_ratio is not None
    assert flags.ceo_pay_ratio.value == 275.0

    assert flags.golden_parachute_value is not None
    assert flags.golden_parachute_value.value == 25_000_000.0


# ---------------------------------------------------------------
# convert_ownership_from_proxy tests
# ---------------------------------------------------------------


def test_convert_ownership_from_proxy() -> None:
    """Insider_pct set; other fields remain defaults."""
    extraction = _sample_def14a()
    ownership = convert_ownership_from_proxy(extraction)

    assert ownership.insider_pct is not None
    assert ownership.insider_pct.value == 4.7
    assert ownership.insider_pct.source == _SOURCE
    assert ownership.insider_pct.confidence == Confidence.HIGH

    # Other fields should be at defaults (None).
    assert ownership.institutional_pct is None
    assert ownership.has_dual_class is None
    assert len(ownership.known_activists) == 0


# ---------------------------------------------------------------
# convert_neos_to_leaders tests
# ---------------------------------------------------------------


def test_convert_neos_to_leaders() -> None:
    """2 NEOs become 2 LeadershipForensicProfile with name, title."""
    extraction = _sample_def14a()
    leaders = convert_neos_to_leaders(extraction)

    assert len(leaders) == 2

    ceo = leaders[0]
    assert ceo.name is not None
    assert ceo.name.value == "Bob Smith"
    assert ceo.title is not None
    assert ceo.title.value == "Chairman and CEO"
    assert ceo.bio_summary is not None
    assert ceo.bio_summary.value == "See Summary Compensation Table"
    assert ceo.name.source == _SOURCE
    assert ceo.name.confidence == Confidence.HIGH

    cfo = leaders[1]
    assert cfo.name is not None
    assert cfo.name.value == "Diana Prince"
    assert cfo.title is not None
    assert cfo.title.value == "Chief Financial Officer"


# ---------------------------------------------------------------
# _parse_pay_ratio tests
# ---------------------------------------------------------------


def test_parse_pay_ratio_variants() -> None:
    """All pay ratio formats parsed correctly."""
    # Colon format
    assert _parse_pay_ratio("123:1") == 123.0
    assert _parse_pay_ratio("1,234:1") == 1234.0

    # "to" format
    assert _parse_pay_ratio("123 to 1") == 123.0
    assert _parse_pay_ratio("1,234 to 1") == 1234.0

    # Bare number
    assert _parse_pay_ratio("123") == 123.0

    # None and invalid
    assert _parse_pay_ratio(None) is None
    assert _parse_pay_ratio("invalid") is None
    assert _parse_pay_ratio("") is None
