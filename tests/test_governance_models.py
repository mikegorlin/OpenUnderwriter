"""Tests for governance and governance forensics models.

Validates model instantiation, SourcedValue field usage, JSON
round-trip serialization, list field isolation (no shared
mutable defaults), and Phase 4 forensic sub-models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.governance import (
    BoardProfile,
    CompensationFlags,
    GovernanceData,
)
from do_uw.models.governance_forensics import (
    BoardForensicProfile,
    CompensationAnalysis,
    GovernanceQualityScore,
    LeadershipForensicProfile,
    LeadershipStability,
    NarrativeCoherence,
    OwnershipAnalysis,
    SentimentProfile,
)

NOW = datetime(2025, 1, 15, tzinfo=UTC)


def _sv_str(value: str, source: str = "test") -> SourcedValue[str]:
    """Create a SourcedValue[str] for testing."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.HIGH, as_of=NOW
    )


def _sv_float(value: float, source: str = "test") -> SourcedValue[float]:
    """Create a SourcedValue[float] for testing."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.HIGH, as_of=NOW
    )


def _sv_bool(value: bool, source: str = "test") -> SourcedValue[bool]:
    """Create a SourcedValue[bool] for testing."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.HIGH, as_of=NOW
    )


def _sv_int(value: int, source: str = "test") -> SourcedValue[int]:
    """Create a SourcedValue[int] for testing."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.HIGH, as_of=NOW
    )


def _sv_dict_any(
    value: dict[str, Any], source: str = "test"
) -> SourcedValue[dict[str, Any]]:
    """Create a SourcedValue[dict[str, Any]] for testing."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.HIGH, as_of=NOW
    )


def _sv_dict_str(
    value: dict[str, str], source: str = "test"
) -> SourcedValue[dict[str, str]]:
    """Create a SourcedValue[dict[str, str]] for testing."""
    return SourcedValue(
        value=value, source=source, confidence=Confidence.HIGH, as_of=NOW
    )


# ---------------------------------------------------------------------------
# GovernanceData (top-level container)
# ---------------------------------------------------------------------------


class TestGovernanceData:
    """Tests for GovernanceData model."""

    def test_instantiation_defaults(self) -> None:
        """GovernanceData creates with all default sub-models."""
        gov = GovernanceData()
        assert isinstance(gov.board, BoardProfile)
        assert isinstance(gov.compensation, CompensationFlags)

    def test_phase4_submodels_default(self) -> None:
        """Phase 4 sub-models initialize with proper defaults."""
        gov = GovernanceData()
        assert isinstance(gov.leadership, LeadershipStability)
        assert gov.board_forensics == []
        assert isinstance(gov.comp_analysis, CompensationAnalysis)
        assert isinstance(gov.ownership, OwnershipAnalysis)
        assert isinstance(gov.sentiment, SentimentProfile)
        assert isinstance(gov.narrative_coherence, NarrativeCoherence)
        assert isinstance(gov.governance_score, GovernanceQualityScore)
        assert gov.governance_summary is None

    def test_aggregate_fields(self) -> None:
        """Phase 3 aggregate fields (board, compensation) work with Phase 4."""
        gov = GovernanceData(
            board=BoardProfile(size=_sv_int(9)),
            compensation=CompensationFlags(ceo_pay_ratio=_sv_float(300.0)),
        )
        assert gov.board.size is not None
        assert gov.board.size.value == 9
        assert gov.compensation.ceo_pay_ratio is not None
        assert gov.compensation.ceo_pay_ratio.value == 300.0
        # Phase 4 fields exist with defaults
        assert isinstance(gov.leadership, LeadershipStability)

    def test_json_round_trip(self) -> None:
        """GovernanceData serializes and deserializes cleanly."""
        gov = GovernanceData(governance_summary=_sv_str("Strong governance"))
        data = gov.model_dump(mode="json")
        restored = GovernanceData.model_validate(data)
        assert restored.governance_summary is not None
        assert restored.governance_summary.value == "Strong governance"
        assert isinstance(restored.leadership, LeadershipStability)
        assert isinstance(restored.governance_score, GovernanceQualityScore)


# ---------------------------------------------------------------------------
# LeadershipForensicProfile
# ---------------------------------------------------------------------------


class TestLeadershipForensicProfile:
    """Tests for LeadershipForensicProfile model."""

    def test_instantiation_defaults(self) -> None:
        """Defaults are all None/empty."""
        profile = LeadershipForensicProfile()
        assert profile.name is None
        assert profile.title is None
        assert profile.tenure_start is None
        assert profile.tenure_years is None
        assert profile.is_interim is None
        assert profile.bio_summary is None
        assert profile.prior_litigation == []
        assert profile.prior_enforcement == []
        assert profile.prior_restatements == []
        assert profile.shade_factors == []
        assert profile.departure_type == ""
        assert profile.departure_date is None
        assert profile.departure_context is None

    def test_sourced_value_fields(self) -> None:
        """SourcedValue fields carry provenance."""
        profile = LeadershipForensicProfile(
            name=_sv_str("Jane CEO", source="DEF 14A 2024-04-15"),
            title=_sv_str("CEO & President"),
            tenure_years=5.3,
            prior_litigation=[
                _sv_str("In re OldCorp Sec. Lit. (2019)"),
            ],
            departure_type="ACTIVE",
        )
        assert profile.name is not None
        assert profile.name.value == "Jane CEO"
        assert profile.name.source == "DEF 14A 2024-04-15"
        assert profile.tenure_years == 5.3
        assert len(profile.prior_litigation) == 1
        assert profile.departure_type == "ACTIVE"

    def test_list_field_isolation(self) -> None:
        """Each instance gets its own list (not shared mutable)."""
        a = LeadershipForensicProfile()
        b = LeadershipForensicProfile()
        a.prior_litigation.append(_sv_str("case1"))
        assert len(b.prior_litigation) == 0


# ---------------------------------------------------------------------------
# LeadershipStability
# ---------------------------------------------------------------------------


class TestLeadershipStability:
    """Tests for LeadershipStability model."""

    def test_instantiation_defaults(self) -> None:
        """All fields default to empty/None."""
        ls = LeadershipStability()
        assert ls.executives == []
        assert ls.departures_18mo == []
        assert ls.avg_tenure_years is None
        assert ls.stability_score is None
        assert ls.red_flags == []

    def test_with_executives(self) -> None:
        """Can hold nested LeadershipForensicProfile objects."""
        exec1 = LeadershipForensicProfile(
            name=_sv_str("CEO"), departure_type="ACTIVE"
        )
        exec2 = LeadershipForensicProfile(
            name=_sv_str("Former CFO"), departure_type="UNPLANNED"
        )
        ls = LeadershipStability(
            executives=[exec1],
            departures_18mo=[exec2],
            avg_tenure_years=_sv_float(4.5),
            stability_score=_sv_float(72.0),
        )
        assert len(ls.executives) == 1
        assert len(ls.departures_18mo) == 1
        assert ls.stability_score is not None
        assert ls.stability_score.value == 72.0


# ---------------------------------------------------------------------------
# BoardForensicProfile
# ---------------------------------------------------------------------------


class TestBoardForensicProfile:
    """Tests for BoardForensicProfile model."""

    def test_instantiation_defaults(self) -> None:
        """Defaults are None/empty/False."""
        bp = BoardForensicProfile()
        assert bp.name is None
        assert bp.is_overboarded is False
        assert bp.committees == []
        assert bp.other_boards == []
        assert bp.true_independence_concerns == []

    def test_overboarded_flag(self) -> None:
        """Overboarding flag works correctly."""
        bp = BoardForensicProfile(
            name=_sv_str("Board Member"),
            is_independent=_sv_bool(True),
            other_boards=[
                _sv_str("Acme Inc"),
                _sv_str("Widget Corp"),
                _sv_str("Foo LLC"),
                _sv_str("Bar Inc"),
            ],
            is_overboarded=True,
        )
        assert bp.is_overboarded is True
        assert len(bp.other_boards) == 4

    def test_list_field_isolation(self) -> None:
        """Each instance gets its own lists."""
        a = BoardForensicProfile()
        b = BoardForensicProfile()
        a.committees.append("Audit")
        assert len(b.committees) == 0


# ---------------------------------------------------------------------------
# CompensationAnalysis
# ---------------------------------------------------------------------------


class TestCompensationAnalysis:
    """Tests for CompensationAnalysis model."""

    def test_instantiation_defaults(self) -> None:
        """All fields default to None/empty."""
        ca = CompensationAnalysis()
        assert ca.ceo_total_comp is None
        assert ca.ceo_pay_ratio is None
        assert ca.comp_mix == {}
        assert ca.performance_metrics == []
        assert ca.related_party_transactions == []

    def test_pay_ratio_fields(self) -> None:
        """CEO pay fields work with SourcedValue."""
        ca = CompensationAnalysis(
            ceo_total_comp=_sv_float(15_000_000.0),
            ceo_pay_ratio=_sv_float(312.0),
            ceo_pay_vs_peer_median=_sv_float(1.45),
            say_on_pay_pct=_sv_float(87.3),
            say_on_pay_trend=_sv_str("STABLE"),
            has_clawback=_sv_bool(True),
            clawback_scope=_sv_str("BROADER"),
        )
        assert ca.ceo_total_comp is not None
        assert ca.ceo_total_comp.value == 15_000_000.0
        assert ca.ceo_pay_vs_peer_median is not None
        assert ca.ceo_pay_vs_peer_median.value == 1.45
        assert ca.has_clawback is not None
        assert ca.has_clawback.value is True


# ---------------------------------------------------------------------------
# OwnershipAnalysis
# ---------------------------------------------------------------------------


class TestOwnershipAnalysis:
    """Tests for OwnershipAnalysis model."""

    def test_instantiation_defaults(self) -> None:
        """All fields default to None/empty."""
        oa = OwnershipAnalysis()
        assert oa.institutional_pct is None
        assert oa.insider_pct is None
        assert oa.top_holders == []
        assert oa.known_activists == []
        assert oa.has_dual_class is None
        assert oa.filings_13d_24mo == []
        assert oa.proxy_contests_3yr == []
        assert oa.activist_risk_assessment is None

    def test_activist_risk(self) -> None:
        """Activist risk fields work correctly."""
        oa = OwnershipAnalysis(
            institutional_pct=_sv_float(85.2),
            known_activists=[_sv_str("Elliott Management")],
            activist_risk_assessment=_sv_str("HIGH"),
        )
        assert oa.institutional_pct is not None
        assert oa.institutional_pct.value == 85.2
        assert len(oa.known_activists) == 1
        assert oa.activist_risk_assessment is not None
        assert oa.activist_risk_assessment.value == "HIGH"


# ---------------------------------------------------------------------------
# SentimentProfile
# ---------------------------------------------------------------------------


class TestSentimentProfile:
    """Tests for SentimentProfile model."""

    def test_instantiation_defaults(self) -> None:
        """All fields default to None/empty."""
        sp = SentimentProfile()
        assert sp.management_tone_trajectory is None
        assert sp.qa_evasion_score is None
        assert sp.lm_negative_trend == []
        assert sp.glassdoor_rating is None
        assert sp.news_sentiment is None

    def test_lm_trends(self) -> None:
        """Loughran-McDonald trend lists hold SourcedValues."""
        sp = SentimentProfile(
            lm_negative_trend=[_sv_float(0.032), _sv_float(0.041)],
            lm_uncertainty_trend=[_sv_float(0.015)],
            management_tone_trajectory=_sv_str("DETERIORATING"),
        )
        assert len(sp.lm_negative_trend) == 2
        assert sp.lm_negative_trend[1].value == 0.041
        assert sp.management_tone_trajectory is not None
        assert sp.management_tone_trajectory.value == "DETERIORATING"


# ---------------------------------------------------------------------------
# NarrativeCoherence
# ---------------------------------------------------------------------------


class TestNarrativeCoherence:
    """Tests for NarrativeCoherence model."""

    def test_instantiation_defaults(self) -> None:
        """All fields default to None/empty."""
        nc = NarrativeCoherence()
        assert nc.strategy_vs_results is None
        assert nc.coherence_flags == []
        assert nc.overall_assessment is None

    def test_coherence_assessment(self) -> None:
        """Coherence fields hold alignment signals."""
        nc = NarrativeCoherence(
            strategy_vs_results=_sv_str("MISALIGNED"),
            insider_vs_confidence=_sv_str("DIVERGENT"),
            coherence_flags=[
                _sv_str("Insider sales during upbeat guidance"),
                _sv_str("Headcount cuts despite growth narrative"),
            ],
            overall_assessment=_sv_str("SIGNIFICANT_GAPS"),
        )
        assert len(nc.coherence_flags) == 2
        assert nc.overall_assessment is not None
        assert nc.overall_assessment.value == "SIGNIFICANT_GAPS"


# ---------------------------------------------------------------------------
# GovernanceQualityScore
# ---------------------------------------------------------------------------


class TestGovernanceQualityScore:
    """Tests for GovernanceQualityScore model."""

    def test_instantiation_defaults(self) -> None:
        """Numeric fields default to 0.0, SourcedValues to None."""
        gqs = GovernanceQualityScore()
        assert gqs.independence_score == 0.0
        assert gqs.ceo_chair_score == 0.0
        assert gqs.refreshment_score == 0.0
        assert gqs.overboarding_score == 0.0
        assert gqs.committee_score == 0.0
        assert gqs.say_on_pay_score == 0.0
        assert gqs.tenure_score == 0.0
        assert gqs.total_score is None
        assert gqs.peer_percentile is None

    def test_scored_governance(self) -> None:
        """Score components and total score work together."""
        gqs = GovernanceQualityScore(
            independence_score=15.0,
            ceo_chair_score=10.0,
            refreshment_score=8.0,
            overboarding_score=12.0,
            committee_score=10.0,
            say_on_pay_score=9.0,
            tenure_score=7.0,
            total_score=_sv_float(71.0),
            peer_percentile=_sv_float(62.5),
        )
        assert gqs.total_score is not None
        assert gqs.total_score.value == 71.0
        assert gqs.peer_percentile is not None
        assert gqs.peer_percentile.value == 62.5


# ---------------------------------------------------------------------------
# JSON round-trip for all sub-models
# ---------------------------------------------------------------------------


class TestJsonRoundTrip:
    """Verify JSON serialization/deserialization for all models."""

    def test_leadership_forensic_profile(self) -> None:
        """LeadershipForensicProfile round-trips through JSON."""
        profile = LeadershipForensicProfile(
            name=_sv_str("Test CEO"),
            tenure_years=3.5,
            prior_enforcement=[_sv_str("SEC v. OldCorp")],
            departure_type="ACTIVE",
        )
        data = profile.model_dump(mode="json")
        restored = LeadershipForensicProfile.model_validate(data)
        assert restored.name is not None
        assert restored.name.value == "Test CEO"
        assert restored.tenure_years == 3.5
        assert len(restored.prior_enforcement) == 1

    def test_board_forensic_profile(self) -> None:
        """BoardForensicProfile round-trips through JSON."""
        bp = BoardForensicProfile(
            name=_sv_str("Director"),
            is_overboarded=True,
            committees=["Audit", "Compensation"],
        )
        data = bp.model_dump(mode="json")
        restored = BoardForensicProfile.model_validate(data)
        assert restored.is_overboarded is True
        assert len(restored.committees) == 2

    def test_ownership_analysis(self) -> None:
        """OwnershipAnalysis round-trips with nested dicts."""
        oa = OwnershipAnalysis(
            top_holders=[
                _sv_dict_any({"name": "Vanguard", "pct": 8.5}),
            ],
            filings_13d_24mo=[
                _sv_dict_str({"filer": "Activist Fund", "date": "2024-06-15"}),
            ],
        )
        data = oa.model_dump(mode="json")
        restored = OwnershipAnalysis.model_validate(data)
        assert len(restored.top_holders) == 1
        assert len(restored.filings_13d_24mo) == 1

    def test_full_governance_data(self) -> None:
        """GovernanceData with all sub-models round-trips."""
        gov = GovernanceData(
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(name=_sv_str("CEO"))
                ],
                stability_score=_sv_float(80.0),
            ),
            board_forensics=[
                BoardForensicProfile(name=_sv_str("Director 1")),
            ],
            comp_analysis=CompensationAnalysis(
                ceo_pay_ratio=_sv_float(250.0),
            ),
            ownership=OwnershipAnalysis(
                institutional_pct=_sv_float(82.0),
            ),
            sentiment=SentimentProfile(
                news_sentiment=_sv_str("NEUTRAL"),
            ),
            narrative_coherence=NarrativeCoherence(
                overall_assessment=_sv_str("COHERENT"),
            ),
            governance_score=GovernanceQualityScore(
                total_score=_sv_float(75.0),
            ),
            governance_summary=_sv_str("Strong governance with minor concerns"),
        )
        data = gov.model_dump(mode="json")
        restored = GovernanceData.model_validate(data)

        # Verify deep nesting survived
        assert len(restored.leadership.executives) == 1
        assert restored.leadership.stability_score is not None
        assert restored.leadership.stability_score.value == 80.0
        assert len(restored.board_forensics) == 1
        assert restored.comp_analysis.ceo_pay_ratio is not None
        assert restored.comp_analysis.ceo_pay_ratio.value == 250.0
        assert restored.ownership.institutional_pct is not None
        assert restored.governance_summary is not None
        assert restored.governance_summary.value == "Strong governance with minor concerns"


# ---------------------------------------------------------------------------
# Phase 4 sub-models with Phase 3 aggregate fields
# ---------------------------------------------------------------------------


class TestPhase4WithAggregateFields:
    """Verify Phase 4 forensic sub-models coexist with Phase 3 aggregate fields."""

    def test_phase4_populated(self) -> None:
        """Phase 4 data populates correctly."""
        gov = GovernanceData(
            leadership=LeadershipStability(
                executives=[
                    LeadershipForensicProfile(
                        name=_sv_str("CEO"),
                        title=_sv_str("CEO"),
                        tenure_years=5.0,
                    )
                ],
            ),
        )
        assert len(gov.leadership.executives) == 1
        assert gov.leadership.executives[0].tenure_years == 5.0

    def test_schema_stability(self) -> None:
        """model_json_schema() is valid with current fields."""
        schema = GovernanceData.model_json_schema()
        props = schema["properties"]
        expected = {
            "board", "compensation",
            "leadership", "board_forensics", "comp_analysis",
            "ownership", "sentiment", "narrative_coherence",
            "governance_score", "governance_summary",
        }
        assert expected.issubset(set(props.keys()))
