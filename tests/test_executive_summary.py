"""Tests for executive summary: key findings, thesis, summary builder.

Validates:
- Key negatives selection with multi-signal ranking
- Key positives from positive indicator catalog
- Thesis generation for all 7 risk types
- Summary builder end-to-end with mocked state
- Serialization round-trip
- Deal context placeholder behavior
- BenchmarkStage state completeness after full run
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.executive_summary import (
    ExecutiveSummary,
    InherentRiskBaseline,
)
from do_uw.models.financials import (
    AuditProfile,
    ExtractedFinancials,
    PeerCompany,
    PeerGroup,
)
from do_uw.models.governance import GovernanceData
from do_uw.models.governance_forensics import GovernanceQualityScore
from do_uw.models.litigation import LitigationLandscape
from do_uw.models.market import (
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.scoring import (
    FactorScore,
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.scoring_output import (
    AllegationMapping,
    AllegationTheory,
    FlaggedItem,
    FlagSeverity,
    RedFlagSummary,
    RiskType,
    RiskTypeClassification,
    TheoryExposure,
)
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.benchmark.key_findings import (
    select_key_negatives,
    select_key_positives,
)
from do_uw.stages.benchmark.summary_builder import build_executive_summary
from do_uw.stages.benchmark.thesis_templates import generate_thesis

NOW = datetime.now(tz=UTC)


def _sv_float(val: float, src: str = "test") -> SourcedValue[float]:
    return SourcedValue(
        value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW,
    )


def _sv_str(val: str, src: str = "test") -> SourcedValue[str]:
    return SourcedValue(
        value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW,
    )


def _sv_int(val: int, src: str = "test") -> SourcedValue[int]:
    return SourcedValue(
        value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW,
    )


def _sv_bool(val: bool, src: str = "test") -> SourcedValue[bool]:
    return SourcedValue(
        value=val, source=src, confidence=Confidence.MEDIUM, as_of=NOW,
    )


def _make_inherent_risk() -> InherentRiskBaseline:
    """Create sample inherent risk for testing."""
    return InherentRiskBaseline(
        sector_base_rate_pct=6.0,
        market_cap_multiplier=1.0,
        market_cap_adjusted_rate_pct=6.0,
        score_multiplier=0.75,
        company_adjusted_rate_pct=4.5,
        sector_name="Technology",
        market_cap_tier="MID",
    )


def _make_factor_scores() -> list[FactorScore]:
    """Create sample factor scores with varying deductions."""
    return [
        FactorScore(
            factor_name="Stock Decline",
            factor_id="F2",
            max_points=15,
            points_deducted=10.0,
            evidence=["30% decline from 52-week high"],
        ),
        FactorScore(
            factor_name="Restatement/Audit",
            factor_id="F3",
            max_points=12,
            points_deducted=6.0,
            evidence=["Material weakness disclosed"],
        ),
        FactorScore(
            factor_name="Governance",
            factor_id="F9",
            max_points=10,
            points_deducted=2.0,
            evidence=["Minor governance concerns"],
        ),
    ]


def _make_flagged_items() -> list[FlaggedItem]:
    """Create sample flagged items with varying severity."""
    return [
        FlaggedItem(
            description="Active securities class action filed 2025",
            source="SECT6",
            severity=FlagSeverity.CRITICAL,
            scoring_impact="CRF-1: ceiling 30",
            allegation_theory="A_DISCLOSURE",
            trajectory="NEW",
        ),
        FlaggedItem(
            description="CFO departure during restatement period",
            source="SECT5",
            severity=FlagSeverity.HIGH,
            scoring_impact="F9: +5 points",
            allegation_theory="D_GOVERNANCE",
            trajectory="WORSENING",
        ),
        FlaggedItem(
            description="Short interest elevated at 12% of float",
            source="SECT4",
            severity=FlagSeverity.MODERATE,
            scoring_impact="F6: +3 points",
            allegation_theory="B_GUIDANCE",
            trajectory="STABLE",
        ),
    ]


def _make_allegation_mapping() -> AllegationMapping:
    """Create sample allegation mapping."""
    return AllegationMapping(
        theories=[
            TheoryExposure(
                theory=AllegationTheory.A_DISCLOSURE,
                exposure_level="HIGH",
                findings=["Revenue recognition concerns"],
            ),
            TheoryExposure(
                theory=AllegationTheory.B_GUIDANCE,
                exposure_level="MODERATE",
                findings=["Guidance miss pattern"],
            ),
            TheoryExposure(
                theory=AllegationTheory.D_GOVERNANCE,
                exposure_level="MODERATE",
                findings=["Leadership turnover"],
            ),
        ],
        primary_exposure=AllegationTheory.A_DISCLOSURE,
    )


def _make_sectors_config() -> dict:
    """Minimal sectors.json config for testing."""
    return {
        "claim_base_rates": {"TECH": 6.0, "DEFAULT": 3.9},
        "market_cap_filing_multipliers": {
            "mega": {"min_cap": 50000000000, "multiplier": 1.56},
            "large": {"min_cap": 10000000000, "multiplier": 1.28},
            "mid": {"min_cap": 2000000000, "multiplier": 1.00},
            "small": {"min_cap": 500000000, "multiplier": 0.90},
            "micro": {"min_cap": 0, "multiplier": 0.77},
        },
        "short_interest": {
            "TECH": {"normal": 4, "elevated": 7, "high": 10},
            "DEFAULT": {"normal": 3, "elevated": 5, "high": 8},
        },
        "volatility_90d": {
            "TECH": {"typical": 2.5, "elevated": 4, "high": 6},
            "DEFAULT": {"typical": 2.5, "elevated": 4, "high": 6},
        },
        "leverage_debt_ebitda": {
            "TECH": {"normal": 2.0, "elevated": 3.0, "critical": 4.0},
            "DEFAULT": {"normal": 2.5, "elevated": 4.0, "critical": 5.5},
        },
        "sector_codes": {
            "mappings": {"TECH": "Technology"},
        },
    }


def _make_scoring_config() -> dict:
    """Minimal scoring.json config for testing."""
    return {
        "severity_ranges": {
            "by_market_cap": [
                {
                    "tier": "MID",
                    "min_cap_b": 2,
                    "max_cap_b": 10,
                    "base_range_m": [8, 40],
                },
            ],
        },
    }


def _make_complete_state(
    quality_score: float = 55.0,
    tier: Tier = Tier.WRITE,
) -> AnalysisState:
    """Create a state with all necessary data for benchmark tests."""
    state = AnalysisState(ticker="TEST")

    for stage in ["resolve", "acquire", "extract", "analyze", "score"]:
        state.mark_stage_running(stage)
        state.mark_stage_completed(stage)

    state.company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="TEST",
            legal_name=_sv_str("Test Corp"),
            sic_code=_sv_str("3571"),
            sector=_sv_str("TECH"),
            exchange=_sv_str("NASDAQ"),
        ),
        market_cap=_sv_float(5_000_000_000.0),
        employee_count=_sv_int(10000),
    )

    state.scoring = ScoringResult(
        quality_score=quality_score,
        composite_score=quality_score,
        tier=TierClassification(
            tier=tier,
            score_range_low=51,
            score_range_high=70,
        ),
        factor_scores=_make_factor_scores(),
        red_flag_summary=RedFlagSummary(
            items=_make_flagged_items(),
            critical_count=1,
            high_count=1,
            moderate_count=1,
        ),
        allegation_mapping=_make_allegation_mapping(),
        risk_type=RiskTypeClassification(primary=RiskType.GROWTH_DARLING),
    )

    state.extracted = ExtractedData(
        financials=ExtractedFinancials(
            audit=AuditProfile(),  # Clean audit
            peer_group=PeerGroup(
                target_ticker="TEST",
                peers=[
                    PeerCompany(
                        ticker="PEER1", name="Peer One",
                        market_cap=3e9, revenue=1e9,
                    ),
                ],
            ),
        ),
        market=MarketSignals(
            stock=StockPerformance(
                volatility_90d=_sv_float(2.0),
            ),
            short_interest=ShortInterestProfile(
                short_pct_float=_sv_float(3.0),
            ),
        ),
        governance=GovernanceData(
            governance_score=GovernanceQualityScore(
                total_score=_sv_float(72.0),
            ),
        ),
        litigation=LitigationLandscape(),
    )

    return state


# -----------------------------------------------------------------------
# Key Negatives Tests
# -----------------------------------------------------------------------


class TestSelectKeyNegatives:
    """Tests for select_key_negatives function."""

    def test_from_flagged_items(self) -> None:
        """Creates findings from FlaggedItem list with varying severity."""
        flags = RedFlagSummary(items=_make_flagged_items())
        result = select_key_negatives(
            flags, [], [], _make_allegation_mapping(),
        )
        assert len(result) == 3
        # CRITICAL + NEW should rank highest
        assert result[0].evidence_narrative == (
            "Active securities class action filed 2025"
        )

    def test_from_factor_scores(self) -> None:
        """Creates findings from high-deduction factor scores."""
        factors = _make_factor_scores()
        result = select_key_negatives(None, factors, [], None)
        # F2 (10 pts) and F3 (6 pts) should appear, F9 (2 pts) below threshold
        assert len(result) == 2
        assert "F2" in result[0].scoring_impact

    def test_fewer_than_five(self) -> None:
        """Returns all items when fewer than 5 available."""
        flags = RedFlagSummary(
            items=[
                FlaggedItem(
                    description="Single issue",
                    source="SECT3",
                    severity=FlagSeverity.MODERATE,
                ),
            ],
        )
        result = select_key_negatives(flags, [], [], None)
        assert len(result) == 1

    def test_empty_inputs(self) -> None:
        """Returns empty list when no inputs."""
        result = select_key_negatives(None, [], [], None)
        assert result == []

    def test_ranking_order(self) -> None:
        """Results are sorted by composite ranking score descending."""
        flags = RedFlagSummary(items=_make_flagged_items())
        result = select_key_negatives(
            flags,
            _make_factor_scores(),
            [],
            _make_allegation_mapping(),
        )
        scores = [f.ranking_score for f in result]
        assert scores == sorted(scores, reverse=True)


# -----------------------------------------------------------------------
# Key Positives Tests
# -----------------------------------------------------------------------


class TestSelectKeyPositives:
    """Tests for select_key_positives function."""

    def test_clean_company(self) -> None:
        """State with clean data detects multiple positives."""
        state = _make_complete_state()
        result = select_key_positives(state, [])
        # Should detect: no_active_sca, clean_audit, low_short_interest,
        # strong_governance, stable_leadership, low_volatility,
        # no_sec_enforcement
        assert len(result) >= 5

    def test_problematic_company(self) -> None:
        """State with issues detects fewer positives."""
        state = _make_complete_state()
        # Add active SCA
        assert state.extracted is not None
        assert state.extracted.litigation is not None
        from do_uw.models.litigation import CaseDetail
        state.extracted.litigation.securities_class_actions = [
            CaseDetail(case_name=_sv_str("Test v. TestCorp")),
        ]
        # Remove clean audit (add material weakness)
        assert state.extracted.financials is not None
        state.extracted.financials.audit.material_weaknesses = [
            _sv_str("Material weakness in revenue recognition"),
        ]

        result = select_key_positives(state, [])
        # no_active_sca and clean_audit should NOT appear
        conditions = [
            f.scoring_impact for f in result
        ]
        assert "Positive: no_active_sca" not in conditions
        assert "Positive: clean_audit" not in conditions

    def test_sorted_by_relevance(self) -> None:
        """Results are sorted by scoring relevance descending."""
        state = _make_complete_state()
        result = select_key_positives(state, [])
        scores = [f.ranking_score for f in result]
        assert scores == sorted(scores, reverse=True)

    def test_max_five(self) -> None:
        """Returns at most 5 positives."""
        state = _make_complete_state()
        result = select_key_positives(state, [])
        assert len(result) <= 5


# -----------------------------------------------------------------------
# Thesis Generation Tests
# -----------------------------------------------------------------------


class TestGenerateThesis:
    """Tests for generate_thesis function."""

    def test_growth_darling(self) -> None:
        """GROWTH_DARLING template mentions high-growth."""
        thesis = generate_thesis(
            risk_type=RiskType.GROWTH_DARLING,
            quality_score=55.0,
            tier=Tier.WRITE,
            top_factor=_make_factor_scores()[0],
            allegation_mapping=_make_allegation_mapping(),
            inherent_risk=_make_inherent_risk(),
            company_name="Test Corp",
        )
        assert "high-growth" in thesis.narrative
        assert "Test Corp" in thesis.narrative
        assert thesis.risk_type_label == "Growth Darling"
        assert len(thesis.narrative) > 50

    def test_distressed(self) -> None:
        """DISTRESSED template mentions fiduciary risk and Side A."""
        thesis = generate_thesis(
            risk_type=RiskType.DISTRESSED,
            quality_score=25.0,
            tier=Tier.WALK,
            top_factor=_make_factor_scores()[0],
            allegation_mapping=None,
            inherent_risk=_make_inherent_risk(),
            company_name="Troubled Inc",
        )
        assert "fiduciary risk" in thesis.narrative
        assert "Side A" in thesis.narrative
        assert "Troubled Inc" in thesis.narrative

    def test_all_risk_types(self) -> None:
        """All 7 risk types produce non-empty distinct narratives."""
        narratives: set[str] = set()
        for rt in RiskType:
            thesis = generate_thesis(
                risk_type=rt,
                quality_score=60.0,
                tier=Tier.WRITE,
                top_factor=None,
                allegation_mapping=None,
                inherent_risk=_make_inherent_risk(),
                company_name="Test Co",
            )
            assert thesis.narrative, f"Empty narrative for {rt}"
            assert len(thesis.narrative) > 30
            assert thesis.risk_type_label != ""
            narratives.add(thesis.narrative)
        # All 7 should be distinct
        assert len(narratives) == 7

    def test_no_top_factor(self) -> None:
        """Thesis handles None top_factor gracefully."""
        thesis = generate_thesis(
            risk_type=RiskType.STABLE_MATURE,
            quality_score=80.0,
            tier=Tier.WANT,
            top_factor=None,
            allegation_mapping=None,
            inherent_risk=None,
            company_name="Stable Corp",
        )
        assert "No single factor" in thesis.narrative

    def test_no_inherent_risk(self) -> None:
        """Thesis handles None inherent_risk gracefully."""
        thesis = generate_thesis(
            risk_type=RiskType.STABLE_MATURE,
            quality_score=75.0,
            tier=Tier.WANT,
            top_factor=None,
            allegation_mapping=None,
            inherent_risk=None,
            company_name="Test",
        )
        assert "N/A" in thesis.narrative


# -----------------------------------------------------------------------
# Summary Builder Tests
# -----------------------------------------------------------------------


class TestBuildExecutiveSummary:
    """Tests for build_executive_summary function."""

    def test_complete_summary(self) -> None:
        """Full summary has all 5 SECT1 sub-sections populated."""
        state = _make_complete_state()
        inherent_risk = _make_inherent_risk()

        summary = build_executive_summary(state, inherent_risk)

        assert summary.snapshot is not None
        assert summary.snapshot.ticker == "TEST"
        assert summary.snapshot.company_name == "Test Corp"

        assert summary.inherent_risk is not None
        assert summary.inherent_risk.sector_base_rate_pct == 6.0

        assert summary.key_findings is not None
        assert isinstance(summary.key_findings.negatives, list)
        assert isinstance(summary.key_findings.positives, list)

        assert summary.thesis is not None
        assert len(summary.thesis.narrative) > 0
        assert summary.thesis.risk_type_label == "Growth Darling"

        assert summary.deal_context is not None
        assert summary.deal_context.is_placeholder is True

    def test_serializes_roundtrip(self) -> None:
        """model_dump_json() round-trips successfully."""
        state = _make_complete_state()
        inherent_risk = _make_inherent_risk()

        summary = build_executive_summary(state, inherent_risk)
        json_str = summary.model_dump_json()

        restored = ExecutiveSummary.model_validate_json(json_str)
        assert restored.snapshot is not None
        assert restored.snapshot.ticker == "TEST"
        assert restored.thesis is not None
        assert len(restored.thesis.narrative) > 0
        assert restored.deal_context.is_placeholder is True

    def test_deal_context_placeholder(self) -> None:
        """DealContext is always placeholder in ticker-only mode."""
        state = _make_complete_state()
        inherent_risk = _make_inherent_risk()

        summary = build_executive_summary(state, inherent_risk)

        assert summary.deal_context.is_placeholder is True
        assert summary.deal_context.layer_quoted == ""
        assert summary.deal_context.premium == ""

    def test_no_scoring_data(self) -> None:
        """Summary handles None scoring gracefully."""
        state = AnalysisState(ticker="EMPTY")
        state.scoring = None
        inherent_risk = _make_inherent_risk()

        summary = build_executive_summary(state, inherent_risk)

        assert summary.snapshot is not None
        assert summary.snapshot.ticker == "EMPTY"
        assert summary.key_findings is not None
        assert summary.key_findings.negatives == []
        assert summary.thesis is not None
        assert "STABLE" in summary.thesis.risk_type_label.upper()

    def test_key_findings_counts(self) -> None:
        """Key findings has expected counts for test data."""
        state = _make_complete_state()
        inherent_risk = _make_inherent_risk()

        summary = build_executive_summary(state, inherent_risk)

        # Dedup merges overlapping flagged items with high-deduction factors
        assert len(summary.key_findings.negatives) == 4  # type: ignore[union-attr]
        # Clean company has multiple positives
        assert len(summary.key_findings.positives) >= 3  # type: ignore[union-attr]


# -----------------------------------------------------------------------
# BenchmarkStage State Completeness Test
# -----------------------------------------------------------------------


class TestStateCompleteness:
    """Tests for state completeness after BenchmarkStage runs."""

    @patch("do_uw.stages.benchmark.BrainLoader")
    def test_state_completeness_after_benchmark(
        self, mock_loader_cls: object,
    ) -> None:
        """After full pipeline, state has all SECT1 data for rendering."""
        mock_loader = MagicMock()
        mock_brain = MagicMock()
        mock_brain.sectors = _make_sectors_config()
        mock_brain.scoring = _make_scoring_config()
        mock_loader.load_all.return_value = mock_brain
        assert isinstance(mock_loader_cls, MagicMock)
        mock_loader_cls.return_value = mock_loader

        from do_uw.stages.benchmark import BenchmarkStage

        state = _make_complete_state()
        stage = BenchmarkStage()
        stage.run(state)

        # SECT1 fields
        assert state.executive_summary is not None
        assert state.executive_summary.snapshot is not None
        assert state.executive_summary.inherent_risk is not None
        assert state.executive_summary.key_findings is not None
        assert state.executive_summary.thesis is not None
        assert state.executive_summary.deal_context is not None
        assert state.executive_summary.deal_context.is_placeholder is True

        # Key findings populated
        assert len(state.executive_summary.key_findings.negatives) > 0
        assert len(state.executive_summary.key_findings.positives) > 0

        # Thesis populated
        assert len(state.executive_summary.thesis.narrative) > 50
        assert state.executive_summary.thesis.risk_type_label != ""

        # SECT2-SECT7 data exists
        assert state.company is not None
        assert state.extracted is not None
        assert state.scoring is not None
        assert state.benchmark is not None
