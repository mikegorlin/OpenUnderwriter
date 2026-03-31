"""Tests for board governance and ownership structure extraction.

Covers 12 tests:
Board (5): governance score high, score low, overboarding detection,
    weights from config, missing proxy fallback
Ownership (7): institutional holders, activist detected, 13D filing,
    13G-to-13D conversion, dual class, activist risk LOW, missing data graceful
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    OwnershipAnalysis,
)
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.board_governance import (
    compute_governance_score,
    extract_board_governance,
    load_governance_weights,
    score_overboarding,
)
from do_uw.stages.extract.ownership_structure import (
    assess_activist_risk,
    check_for_activists,
    extract_dual_class,
    extract_from_institutional_holders,
    extract_ownership,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sv_str(val: str) -> SourcedValue[str]:
    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _sv_float(val: float) -> SourcedValue[float]:
    return SourcedValue[float](
        value=val, source="test", confidence=Confidence.MEDIUM,
        as_of=datetime.now(tz=UTC),
    )


def _sv_bool(val: bool) -> SourcedValue[bool]:
    return SourcedValue[bool](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_state(
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    market_info: dict[str, Any] | None = None,
    institutional_holders: dict[str, Any] | None = None,
    proxy_text: str = "",
) -> AnalysisState:
    """Build a minimal AnalysisState for testing."""
    filings: dict[str, Any] = {}
    market_data: dict[str, Any] = {}
    if market_info is not None:
        market_data["info"] = market_info
    if institutional_holders is not None:
        market_data["institutional_holders"] = institutional_holders

    fd: dict[str, list[dict[str, str]]] = filing_documents or {}
    if proxy_text:
        fd["DEF 14A"] = [{"full_text": proxy_text, "filing_date": "2025-04-01",
                          "accession": "0001-25-000001", "form_type": "DEF 14A"}]

    identity = CompanyIdentity(
        ticker="TEST", cik=_sv_str("0001234567"),
        sic_code=_sv_str("7372"), sector=_sv_str("TECH"),
    )
    state = AnalysisState(
        ticker="TEST",
        company=CompanyProfile(identity=identity),
        acquired_data=AcquiredData(
            filings=filings,
            market_data=market_data,
            filing_documents=fd,
        ),
    )
    return state


def _make_board_profile(
    name: str,
    independent: bool = True,
    tenure: float = 7.0,
    committees: list[str] | None = None,
    other_boards: int = 0,
) -> BoardForensicProfile:
    """Create a test BoardForensicProfile."""
    p = BoardForensicProfile()
    p.name = _sv_str(name)
    p.is_independent = _sv_bool(independent)
    p.tenure_years = _sv_float(tenure)
    p.committees = committees or []
    for i in range(other_boards):
        p.other_boards.append(_sv_str(f"Other Corp {i}"))
    p.is_overboarded = (other_boards + 1) >= 4
    return p


# ---------------------------------------------------------------------------
# Board governance tests (5)
# ---------------------------------------------------------------------------


class TestBoardGovernanceScoreHigh:
    """Test governance score with ideal board composition."""

    def test_high_governance_score(self) -> None:
        profiles = [
            _make_board_profile("Alice Smith", True, 7.0, ["Audit"]),
            _make_board_profile("Bob Jones", True, 5.0, ["Compensation"]),
            _make_board_profile("Carol White", True, 8.0, ["Nominating/Governance"]),
            _make_board_profile("Dave Brown", True, 3.0, []),
            _make_board_profile("Eve Green", False, 10.0, []),
        ]
        weights = {
            "independence": 0.20, "ceo_chair": 0.15, "refreshment": 0.10,
            "overboarding": 0.10, "committee_structure": 0.15,
            "say_on_pay": 0.15, "tenure": 0.15,
        }
        thresholds = {
            "independence_high": 0.75, "independence_medium": 0.50,
            "overboarded_boards": 4, "refreshment_new_directors_3yr": 2,
            "tenure_ideal_min": 5, "tenure_ideal_max": 10,
            "tenure_concern_max": 15,
            "say_on_pay_strong": 90.0, "say_on_pay_concern": 70.0,
        }
        comp = CompensationAnalysis()
        comp.say_on_pay_pct = _sv_float(95.0)

        score = compute_governance_score(profiles, comp, weights, thresholds)
        assert score.total_score is not None
        assert score.total_score.value >= 70.0  # High governance
        assert score.independence_score == 10.0  # 4/5 = 80% >= 75%


class TestBoardGovernanceScoreLow:
    """Test governance score with poor board composition."""

    def test_low_governance_score(self) -> None:
        profiles = [
            _make_board_profile("Alice Smith", False, 16.0, []),
            _make_board_profile("Bob Jones", False, 18.0, [], other_boards=5),
            _make_board_profile("Carol White", False, 20.0, [], other_boards=4),
        ]
        weights = {
            "independence": 0.20, "ceo_chair": 0.15, "refreshment": 0.10,
            "overboarding": 0.10, "committee_structure": 0.15,
            "say_on_pay": 0.15, "tenure": 0.15,
        }
        thresholds = {
            "independence_high": 0.75, "independence_medium": 0.50,
            "overboarded_boards": 4, "refreshment_new_directors_3yr": 2,
            "tenure_ideal_min": 5, "tenure_ideal_max": 10,
            "tenure_concern_max": 15,
            "say_on_pay_strong": 90.0, "say_on_pay_concern": 70.0,
        }
        comp = CompensationAnalysis()
        comp.say_on_pay_pct = _sv_float(55.0)

        score = compute_governance_score(profiles, comp, weights, thresholds)
        assert score.total_score is not None
        assert score.total_score.value < 40.0  # Low governance
        assert score.independence_score == 3.0  # 0% independent


class TestOverboardingDetection:
    """Test overboarding score with mixed board."""

    def test_overboarding_detected(self) -> None:
        profiles = [
            _make_board_profile("Alice Smith", other_boards=5),  # Overboarded
            _make_board_profile("Bob Jones", other_boards=0),
            _make_board_profile("Carol White", other_boards=0),
            _make_board_profile("Dave Brown", other_boards=0),
        ]
        score = score_overboarding(profiles)
        assert score < 10.0  # Should be penalized (1/4 = 25%)
        assert score == 4.0  # 25% overboarded


class TestWeightsFromConfig:
    """Test that config weights are loaded correctly."""

    def test_load_governance_weights(self) -> None:
        weights, thresholds = load_governance_weights()
        assert "independence" in weights
        assert "ceo_chair" in weights
        total = sum(weights.values())
        assert abs(total - 1.0) < 0.01  # Weights should sum to ~1.0
        assert thresholds["independence_high"] == 0.75
        assert thresholds["say_on_pay_strong"] == 90.0


class TestMissingProxyFallback:
    """Test graceful handling when no proxy text available."""

    def test_no_proxy_returns_empty_profiles(self) -> None:
        state = _make_state()
        (profiles, gov_score), report = extract_board_governance(state)
        assert profiles == []
        assert gov_score.total_score is None
        assert "No DEF 14A text" in report.fallbacks_used[0]


# ---------------------------------------------------------------------------
# Ownership structure tests (7)
# ---------------------------------------------------------------------------


class TestInstitutionalHolders:
    """Test institutional holder extraction from yfinance data."""

    def test_extract_top_holders(self) -> None:
        holders_data: dict[str, Any] = {
            "Holder": ["Vanguard Group", "BlackRock", "State Street"],
            "% Out": [0.08, 0.07, 0.05],
            "Shares": [10000000, 9000000, 7000000],
            "Value": [1e9, 9e8, 7e8],
        }
        result = extract_from_institutional_holders(holders_data)
        assert len(result) == 3
        assert result[0].value["name"] == "Vanguard Group"
        assert result[0].value["pct_out"] == 0.08


class TestActivistDetected:
    """Test activist investor matching."""

    def test_activist_match(self) -> None:
        holders: list[SourcedValue[dict[str, Any]]] = [
            SourcedValue[dict[str, Any]](
                value={"name": "Elliott Investment Management LP"},
                source="test", confidence=Confidence.MEDIUM,
                as_of=datetime.now(tz=UTC),
            ),
            SourcedValue[dict[str, Any]](
                value={"name": "Vanguard Group"},
                source="test", confidence=Confidence.MEDIUM,
                as_of=datetime.now(tz=UTC),
            ),
        ]
        activists = ["Elliott Management", "Carl Icahn", "ValueAct Capital"]
        matches = check_for_activists(holders, activists)
        assert len(matches) == 1
        assert "Elliott" in matches[0].value


class TestFilings13D:
    """Test 13D filing extraction from filing documents."""

    def test_13d_filing_detected(self) -> None:
        fd: dict[str, list[dict[str, str]]] = {
            "SC 13D": [{
                "full_text": "FILED BY: Starboard Value LP\nSome other text",
                "filing_date": "2025-06-15",
                "accession": "0001-25-000002",
                "form_type": "SC 13D",
            }],
        }
        state = _make_state(filing_documents=fd)
        ownership, report = extract_ownership(state)
        assert len(ownership.filings_13d_24mo) == 1
        assert "13d_filings" in report.found_fields


class TestConversion13GTo13D:
    """Test 13G-to-13D conversion detection."""

    def test_conversion_detected(self) -> None:
        fd: dict[str, list[dict[str, str]]] = {
            "SC 13G": [{
                "full_text": "FILED BY: Trian Fund Management\nPassive position",
                "filing_date": "2025-01-10",
                "accession": "0001-25-000003",
                "form_type": "SC 13G",
            }],
            "SC 13D": [{
                "full_text": "FILED BY: Trian Fund Management\nActivist position",
                "filing_date": "2025-06-15",
                "accession": "0001-25-000004",
                "form_type": "SC 13D",
            }],
        }
        state = _make_state(filing_documents=fd)
        ownership, _report = extract_ownership(state)
        assert len(ownership.conversions_13g_to_13d) == 1
        conv = ownership.conversions_13g_to_13d[0].value
        assert "Trian" in conv.get("filer", "")


class TestDualClass:
    """Test dual-class share structure detection."""

    def test_dual_class_from_proxy(self) -> None:
        proxy = (
            "The Company has two classes of common stock. "
            "Class A Common Stock holders have one vote per share. "
            "Class B Common Stock holders have 10 votes per share and "
            "collectively control approximately 85.2% of all voting power."
        )
        has_dual, _control_pct, _econ_pct = extract_dual_class(proxy, {})
        assert has_dual is True


class TestActivistRiskLow:
    """Test activist risk assessment returns LOW with no signals."""

    def test_no_activist_signals(self) -> None:
        ownership = OwnershipAnalysis()
        ownership.institutional_pct = _sv_float(60.0)
        risk = assess_activist_risk(ownership)
        assert risk == "LOW"


class TestMissingDataGraceful:
    """Test graceful handling when all data sources are empty."""

    def test_empty_state_returns_valid(self) -> None:
        state = _make_state()
        ownership, report = extract_ownership(state)
        assert ownership.activist_risk_assessment is not None
        assert ownership.activist_risk_assessment.value == "LOW"
        assert ownership.has_dual_class is not None
        assert ownership.has_dual_class.value is False
        assert report.coverage_pct > 0  # Some fields always found
