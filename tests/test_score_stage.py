"""Tests for SCORE stage: factor scoring, CRF gates, tier classification.

Covers 10-factor scoring engine, red flag gate evaluation, tier
classification, and scoring model serialization.
"""

from __future__ import annotations

from datetime import UTC, datetime

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.financials import AuditProfile, ExtractedFinancials
from do_uw.models.litigation import (
    CaseDetail,
    LitigationLandscape,
)
from do_uw.models.market import (
    InsiderTradingProfile,
    MarketSignals,
    ShortInterestProfile,
    StockPerformance,
)
from do_uw.models.market_events import (
    EarningsGuidanceAnalysis,
    EarningsQuarterRecord,
)
from do_uw.models.scoring import (
    AllegationMapping,
    AllegationTheory,
    ClaimProbability,
    FactorScore,
    FlaggedItem,
    FlagSeverity,
    PatternMatch,
    ProbabilityBand,
    RedFlagResult,
    RedFlagSummary,
    RiskType,
    RiskTypeClassification,
    ScoringResult,
    SeverityScenario,
    SeverityScenarios,
    TheoryExposure,
    Tier,
    TierClassification,
    TowerPosition,
    TowerRecommendation,
)
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.score.factor_scoring import (
    _get_sector_code,
    _score_factor,
    score_all_factors,
)
from do_uw.stages.score.red_flag_gates import (
    _normalize_crf_id,
    apply_crf_ceilings,
    evaluate_red_flag_gates,
)
from do_uw.stages.score.tier_classification import (
    classify_tier,
    compute_claim_probability,
)

NOW = datetime.now(tz=UTC)


def _sv(value: object, source: str = "test", conf: Confidence = Confidence.HIGH) -> SourcedValue:  # type: ignore[type-arg]
    """Shorthand to create a SourcedValue for testing."""
    return SourcedValue(
        value=value,
        source=source,
        confidence=conf,
        as_of=NOW,
    )


def _load_scoring_config() -> dict:  # type: ignore[type-arg]
    """Load the real scoring.json for testing."""
    import json
    from pathlib import Path

    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
    with (brain_dir / "scoring.json").open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def _load_sectors_config() -> dict:  # type: ignore[type-arg]
    """Load the real sectors.json for testing."""
    import json
    from pathlib import Path

    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
    with (brain_dir / "sectors.json").open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def _minimal_extracted() -> ExtractedData:
    """Create minimal ExtractedData with all None sub-models."""
    return ExtractedData()


def _make_company(
    sector: str = "TECH", market_cap: float = 5e9
) -> CompanyProfile:
    """Create a CompanyProfile with given sector and market cap."""
    return CompanyProfile(
        identity=CompanyIdentity(
            ticker="TEST",
            sector=_sv(sector),
        ),
        market_cap=_sv(market_cap),
    )


# -----------------------------------------------------------------------
# Model serialization tests
# -----------------------------------------------------------------------


class TestScoringModels:
    """Test that all new Pydantic models serialize/deserialize."""

    def test_risk_type_enum(self) -> None:
        assert RiskType.BINARY_EVENT == "BINARY_EVENT"
        assert RiskType.DISTRESSED == "DISTRESSED"

    def test_risk_type_classification(self) -> None:
        rtc = RiskTypeClassification(
            primary=RiskType.GROWTH_DARLING,
            secondary=RiskType.GUIDANCE_DEPENDENT,
            evidence=["High growth", "Frequent guidance"],
        )
        data = rtc.model_dump()
        assert data["primary"] == "GROWTH_DARLING"
        restored = RiskTypeClassification.model_validate(data)
        assert restored.primary == RiskType.GROWTH_DARLING

    def test_probability_band_enum(self) -> None:
        assert ProbabilityBand.VERY_HIGH == "VERY_HIGH"

    def test_claim_probability(self) -> None:
        cp = ClaimProbability(
            band=ProbabilityBand.MODERATE,
            range_low_pct=2.0,
            range_high_pct=5.0,
            industry_base_rate_pct=3.5,
        )
        data = cp.model_dump()
        assert data["band"] == "MODERATE"
        restored = ClaimProbability.model_validate(data)
        assert restored.range_low_pct == 2.0

    def test_severity_scenario(self) -> None:
        ss = SeverityScenario(
            percentile=50, label="median", ddl_amount=1e7
        )
        assert ss.percentile == 50

    def test_severity_scenarios(self) -> None:
        svs = SeverityScenarios(
            market_cap=5e9,
            decline_scenarios={"10%": 5e8, "20%": 1e9},
        )
        data = svs.model_dump()
        assert data["market_cap"] == 5e9

    def test_tower_position_enum(self) -> None:
        assert TowerPosition.PRIMARY == "PRIMARY"
        assert TowerPosition.DECLINE == "DECLINE"

    def test_tower_recommendation(self) -> None:
        tr = TowerRecommendation(
            recommended_position=TowerPosition.MID_EXCESS,
            minimum_attachment="$15M",
        )
        assert tr.needs_calibration is True

    def test_flag_severity_enum(self) -> None:
        assert FlagSeverity.CRITICAL == "CRITICAL"

    def test_flagged_item(self) -> None:
        fi = FlaggedItem(
            description="Active SCA",
            source="Stanford SCAC",
            severity=FlagSeverity.CRITICAL,
        )
        assert fi.trajectory == "STABLE"

    def test_red_flag_summary(self) -> None:
        rfs = RedFlagSummary(critical_count=1, high_count=2)
        assert rfs.moderate_count == 0

    def test_allegation_theory_enum(self) -> None:
        assert AllegationTheory.A_DISCLOSURE == "A_DISCLOSURE"
        assert AllegationTheory.E_MA == "E_MA"

    def test_allegation_mapping(self) -> None:
        am = AllegationMapping(
            theories=[
                TheoryExposure(
                    theory=AllegationTheory.A_DISCLOSURE,
                    exposure_level="HIGH",
                    findings=["Restatement"],
                )
            ],
            primary_exposure=AllegationTheory.A_DISCLOSURE,
        )
        data = am.model_dump()
        restored = AllegationMapping.model_validate(data)
        assert len(restored.theories) == 1

    def test_scoring_result_has_new_fields(self) -> None:
        sr = ScoringResult()
        assert sr.risk_type is None
        assert sr.allegation_mapping is None
        assert sr.claim_probability is None
        assert sr.severity_scenarios is None
        assert sr.tower_recommendation is None
        assert sr.red_flag_summary is None
        assert sr.calibration_notes == []
        assert sr.binding_ceiling_id is None


# -----------------------------------------------------------------------
# FactorScore creation tests
# -----------------------------------------------------------------------


class TestFactorScore:
    """Test FactorScore model."""

    def test_create_factor_score(self) -> None:
        fs = FactorScore(
            factor_name="Prior Litigation",
            factor_id="F1",
            max_points=20,
            points_deducted=15.0,
            evidence=["Settled SCA <3 years"],
            rules_triggered=["F1-002"],
        )
        assert fs.points_deducted == 15.0
        assert fs.factor_id == "F1"


# -----------------------------------------------------------------------
# Factor scoring engine tests
# -----------------------------------------------------------------------


class TestScoreAllFactors:
    """Test the 10-factor scoring engine."""

    def test_all_none_produces_10_zero_scores(self) -> None:
        """Minimal ExtractedData -> all factors score 0."""
        config = _load_scoring_config()
        sectors = _load_sectors_config()
        extracted = _minimal_extracted()

        scores = score_all_factors(config, extracted, None, sectors)
        assert len(scores) == 10
        for fs in scores:
            # F9 and F10 might match "strong governance" or "stable" rules
            # but those give 0 points
            assert fs.points_deducted == 0.0, (
                f"{fs.factor_id} had {fs.points_deducted} points with no data"
            )

    def test_f1_active_sca_scores_20(self) -> None:
        """F1 with active SCA -> 20 points (max)."""
        config = _load_scoring_config()
        sectors = _load_sectors_config()
        extracted = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(
                        case_name=_sv("In re Test Corp"),
                        status=_sv("ACTIVE"),
                    )
                ]
            )
        )
        factor_cfg = config["factors"]["F1_prior_litigation"]
        score = _score_factor(
            "F1_prior_litigation", factor_cfg, extracted, None, sectors
        )
        assert score.points_deducted == 20.0
        assert "F1-001" in score.rules_triggered

    def test_f2_45pct_decline_scores_9(self) -> None:
        """F2 with 45% decline -> 9 points (40-50% range)."""
        config = _load_scoring_config()
        sectors = _load_sectors_config()
        extracted = ExtractedData(
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(45.0),
                )
            )
        )
        factor_cfg = config["factors"]["F2_stock_decline"]
        score = _score_factor(
            "F2_stock_decline", factor_cfg, extracted, None, sectors
        )
        assert score.points_deducted == 9.0
        assert "F2-003" in score.rules_triggered

    def test_f2_insider_amplifier_cluster_selling(self) -> None:
        """F2 with 45% decline + cluster selling -> 2.0x multiplier, capped at 15."""
        config = _load_scoring_config()
        sectors = _load_sectors_config()
        extracted = ExtractedData(
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(45.0),
                ),
                insider_trading=InsiderTradingProfile(
                    cluster_events=[_sv({"insiders": "CEO,CFO,COO", "count": 3.0})],
                ),
            )
        )
        factor_cfg = config["factors"]["F2_stock_decline"]
        score = _score_factor(
            "F2_stock_decline", factor_cfg, extracted, None, sectors
        )
        # Base 9 * 2.0x = 18, capped at 15
        assert score.points_deducted == 15.0
        assert score.sub_components.get("insider_multiplier") == 2.0

    def test_f2_max_points_cap(self) -> None:
        """F2 score cannot exceed max_points (15)."""
        config = _load_scoring_config()
        sectors = _load_sectors_config()
        # 65% decline = 15 base, no amplifier needed to test cap
        extracted = ExtractedData(
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(65.0),
                ),
            )
        )
        factor_cfg = config["factors"]["F2_stock_decline"]
        score = _score_factor(
            "F2_stock_decline", factor_cfg, extracted, None, sectors
        )
        assert score.points_deducted == 15.0

    def test_f5_three_misses_scores_6(self) -> None:
        """F5 with 3 misses -> 6 points."""
        config = _load_scoring_config()
        sectors = _load_sectors_config()
        quarters = [
            EarningsQuarterRecord(quarter=f"Q{i} 2025", result="MISS")
            for i in range(1, 4)
        ]
        extracted = ExtractedData(
            market=MarketSignals(
                earnings_guidance=EarningsGuidanceAnalysis(quarters=quarters)
            )
        )
        factor_cfg = config["factors"]["F5_guidance_misses"]
        score = _score_factor(
            "F5_guidance_misses", factor_cfg, extracted, None, sectors
        )
        assert score.points_deducted == 6.0
        assert "F5-002" in score.rules_triggered

    def test_f6_3x_sector_scores_4(self) -> None:
        """F6 with short interest 3x sector -> 4 points."""
        config = _load_scoring_config()
        sectors = _load_sectors_config()
        extracted = ExtractedData(
            market=MarketSignals(
                short_interest=ShortInterestProfile(
                    short_pct_float=_sv(15.0),
                    vs_sector_ratio=_sv(3.5),
                )
            )
        )
        factor_cfg = config["factors"]["F6_short_interest"]
        score = _score_factor(
            "F6_short_interest", factor_cfg, extracted, None, sectors
        )
        assert score.points_deducted == 4.0
        assert "F6-R01" in score.rules_triggered


class TestGetSectorCode:
    """Test sector code extraction helper."""

    def test_none_company_returns_default(self) -> None:
        assert _get_sector_code(None) == "DEFAULT"

    def test_company_with_sector(self) -> None:
        company = _make_company(sector="TECH")
        assert _get_sector_code(company) == "TECH"

    def test_company_without_sector(self) -> None:
        company = CompanyProfile(
            identity=CompanyIdentity(ticker="TEST"),
        )
        assert _get_sector_code(company) == "DEFAULT"


# -----------------------------------------------------------------------
# CRF Red Flag Gate tests
# -----------------------------------------------------------------------


def _load_red_flags_config() -> dict:  # type: ignore[type-arg]
    """Load the real red_flags.json for testing."""
    import json
    from pathlib import Path

    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
    with (brain_dir / "red_flags.json").open() as f:
        return json.load(f)  # type: ignore[no-any-return]


class TestNormalizeCrfId:
    """Test CRF ID normalization between scoring.json and red_flags.json."""

    def test_normalize_crf_001(self) -> None:
        assert _normalize_crf_id("CRF-001") == "CRF-1"

    def test_normalize_crf_01(self) -> None:
        assert _normalize_crf_id("CRF-01") == "CRF-1"

    def test_normalize_crf_11(self) -> None:
        assert _normalize_crf_id("CRF-11") == "CRF-11"

    def test_normalize_crf_011(self) -> None:
        assert _normalize_crf_id("CRF-011") == "CRF-11"


class TestEvaluateRedFlagGates:
    """Test CRF gate evaluation against extracted data."""

    def test_active_sca_triggers_crf1(self) -> None:
        """Active SCA triggers CRF-1, ceiling 30."""
        rf_config = _load_red_flags_config()
        sc_config = _load_scoring_config()
        extracted = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(
                        case_name=_sv("In re Test Corp"),
                        status=_sv("ACTIVE"),
                    )
                ]
            )
        )
        results = evaluate_red_flag_gates(
            rf_config, sc_config, extracted, None
        )
        # Find CRF-1
        crf1 = [r for r in results if r.flag_id == "CRF-1"]
        assert len(crf1) == 1
        assert crf1[0].triggered is True
        assert crf1[0].ceiling_applied == 30

    def test_going_concern_triggers_crf4(self) -> None:
        """Going concern triggers CRF-4, ceiling 50."""
        rf_config = _load_red_flags_config()
        sc_config = _load_scoring_config()
        extracted = ExtractedData(
            financials=ExtractedFinancials(
                audit=AuditProfile(going_concern=_sv(True))
            )
        )
        results = evaluate_red_flag_gates(
            rf_config, sc_config, extracted, None
        )
        crf4 = [r for r in results if r.flag_id == "CRF-4"]
        assert len(crf4) == 1
        assert crf4[0].triggered is True
        assert crf4[0].ceiling_applied == 50

    def test_no_triggers_all_false(self) -> None:
        """Minimal extracted data triggers no CRFs."""
        rf_config = _load_red_flags_config()
        sc_config = _load_scoring_config()
        extracted = _minimal_extracted()
        results = evaluate_red_flag_gates(
            rf_config, sc_config, extracted, None
        )
        assert len(results) == 17  # CRF-1 through CRF-17
        for r in results:
            assert r.triggered is False
            assert r.ceiling_applied is None


class TestApplyCrfCeilings:
    """Test CRF ceiling application logic."""

    def test_two_triggers_lowest_wins(self) -> None:
        """Two triggered CRFs -> lowest ceiling wins."""
        results = [
            RedFlagResult(
                flag_id="CRF-1",
                triggered=True,
                ceiling_applied=30,
                max_tier="WALK",
            ),
            RedFlagResult(
                flag_id="CRF-4",
                triggered=True,
                ceiling_applied=50,
                max_tier="WATCH",
            ),
        ]
        quality, binding = apply_crf_ceilings(85.0, results)
        assert quality == 30.0
        assert binding == "CRF-1"

    def test_no_triggers_score_unchanged(self) -> None:
        """No triggered CRFs -> score unchanged, no binding."""
        results = [
            RedFlagResult(flag_id="CRF-1", triggered=False),
            RedFlagResult(flag_id="CRF-4", triggered=False),
        ]
        quality, binding = apply_crf_ceilings(85.0, results)
        assert quality == 85.0
        assert binding is None

    def test_ceiling_below_composite(self) -> None:
        """Ceiling clips composite score down."""
        results = [
            RedFlagResult(
                flag_id="CRF-4",
                triggered=True,
                ceiling_applied=50,
                max_tier="WATCH",
            ),
        ]
        quality, binding = apply_crf_ceilings(75.0, results)
        assert quality == 50.0
        assert binding == "CRF-4"

    def test_ceiling_above_composite(self) -> None:
        """Ceiling above composite -> composite unchanged."""
        results = [
            RedFlagResult(
                flag_id="CRF-4",
                triggered=True,
                ceiling_applied=50,
                max_tier="WATCH",
            ),
        ]
        quality, binding = apply_crf_ceilings(40.0, results)
        assert quality == 40.0
        assert binding == "CRF-4"


# -----------------------------------------------------------------------
# Tier classification tests
# -----------------------------------------------------------------------


class TestClassifyTier:
    """Test tier classification from quality scores."""

    def test_score_90_is_win(self) -> None:
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(90.0, tiers)
        assert result.tier == Tier.WIN
        assert result.score_range_low == 86
        assert result.score_range_high == 100

    def test_score_45_is_watch(self) -> None:
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(45.0, tiers)
        assert result.tier == Tier.WATCH

    def test_score_5_is_no_touch(self) -> None:
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(5.0, tiers)
        assert result.tier == Tier.NO_TOUCH

    def test_score_71_is_want(self) -> None:
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(71.0, tiers)
        assert result.tier == Tier.WANT

    def test_score_55_is_write(self) -> None:
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(55.0, tiers)
        assert result.tier == Tier.WRITE

    def test_score_20_is_walk(self) -> None:
        tiers = _load_scoring_config()["tiers"]
        result = classify_tier(20.0, tiers)
        assert result.tier == Tier.WALK


class TestComputeClaimProbability:
    """Test claim probability computation from tier."""

    def test_win_tier_low_band(self) -> None:
        tier = TierClassification(
            tier=Tier.WIN,
            score_range_low=86,
            score_range_high=100,
            probability_range="<2%",
        )
        prob = compute_claim_probability(tier, None, {})
        assert prob.band == ProbabilityBand.LOW
        assert prob.range_low_pct == 0.0
        assert prob.range_high_pct == 2.0
        assert prob.needs_calibration is True

    def test_watch_tier_high_band(self) -> None:
        tier = TierClassification(
            tier=Tier.WATCH,
            score_range_low=31,
            score_range_high=50,
            probability_range="10-15%",
        )
        prob = compute_claim_probability(tier, None, {})
        assert prob.band == ProbabilityBand.HIGH
        assert prob.range_low_pct == 10.0
        assert prob.range_high_pct == 15.0


# -----------------------------------------------------------------------
# ScoreStage orchestrator tests
# -----------------------------------------------------------------------


class TestScoreStageRun:
    """Test ScoreStage.run with mocked config."""

    def test_score_stage_populates_state(self) -> None:
        """ScoreStage.run populates state.scoring with all expected fields."""

        from do_uw.models.common import StageStatus
        from do_uw.stages.score import ScoreStage

        # Create state with analyze completed
        state = AnalysisState(ticker="TEST")
        state.mark_stage_running("analyze")
        state.mark_stage_completed("analyze")
        state.extracted = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(
                        case_name=_sv("In re Test Corp"),
                        status=_sv("ACTIVE"),
                    )
                ]
            )
        )

        # Uses real brain files via BrainKnowledgeLoader
        stage = ScoreStage()
        stage.run(state)

        # Verify scoring result populated
        assert state.scoring is not None
        assert len(state.scoring.factor_scores) == 10
        assert len(state.scoring.red_flags) == 17  # CRF-1 through CRF-17
        assert state.scoring.tier is not None
        assert state.scoring.claim_probability is not None

        # Active SCA should trigger CRF-1 ceiling (30)
        assert state.scoring.quality_score <= 30.0
        assert state.scoring.binding_ceiling_id == "CRF-1"
        assert state.scoring.tier.tier in (Tier.WALK, Tier.NO_TOUCH)

        # F1 should score 20 points (active SCA)
        f1 = [f for f in state.scoring.factor_scores if f.factor_id == "F1"]
        assert len(f1) == 1
        assert f1[0].points_deducted == 20.0

        # Calibration note present
        assert len(state.scoring.calibration_notes) > 0

        # Stage should be completed
        assert (
            state.stages["score"].status == StageStatus.COMPLETED
        )

    def test_score_stage_full_pipeline_all_fields(self) -> None:
        """ScoreStage.run populates ALL scoring fields (06-04 complete)."""
        from do_uw.models.common import StageStatus
        from do_uw.stages.score import ScoreStage

        state = AnalysisState(ticker="TEST")
        state.mark_stage_running("analyze")
        state.mark_stage_completed("analyze")
        state.extracted = ExtractedData(
            litigation=LitigationLandscape(
                securities_class_actions=[
                    CaseDetail(
                        case_name=_sv("In re Full Test Corp"),
                        status=_sv("ACTIVE"),
                    )
                ]
            ),
            market=MarketSignals(
                stock=StockPerformance(
                    decline_from_high_pct=_sv(45.0),
                ),
            ),
        )

        stage = ScoreStage()
        stage.run(state)

        # Core fields (from 06-02)
        assert state.scoring is not None
        assert len(state.scoring.factor_scores) == 10
        assert len(state.scoring.red_flags) == 17  # CRF-1 through CRF-17
        assert state.scoring.tier is not None
        assert state.scoring.claim_probability is not None

        # New fields (from 06-03/06-04)
        assert state.scoring.patterns_detected is not None
        assert isinstance(state.scoring.patterns_detected, list)
        assert state.scoring.risk_type is not None
        assert state.scoring.allegation_mapping is not None
        assert state.scoring.red_flag_summary is not None
        assert state.scoring.tower_recommendation is not None
        # severity_scenarios may be None if no market_cap, that's fine

        # Calibration notes must be non-empty
        assert len(state.scoring.calibration_notes) > 0
        assert "calibration" in state.scoring.calibration_notes[0].lower()

        # Stage completed
        assert state.stages["score"].status == StageStatus.COMPLETED

    def test_pattern_modifiers_applied_and_capped(self) -> None:
        """Pattern modifiers are applied to factor scores and capped."""
        from do_uw.stages.score import _apply_pattern_modifiers

        factor_scores = [
            FactorScore(
                factor_name="Stock Decline",
                factor_id="F2",
                max_points=15,
                points_deducted=12.0,
            ),
            FactorScore(
                factor_name="Governance",
                factor_id="F9",
                max_points=6,
                points_deducted=2.0,
            ),
        ]
        patterns = [
            PatternMatch(
                pattern_id="TEST_PATTERN",
                detected=True,
                score_impact={"F2": 5.0, "F9": 2.0},
            ),
        ]

        _apply_pattern_modifiers(factor_scores, patterns, {})

        # F2: 12 + 5 = 17, capped at 15
        f2 = next(f for f in factor_scores if f.factor_id == "F2")
        assert f2.points_deducted == 15.0
        assert f2.sub_components.get("pattern_modifier") == 5.0

        # F9: 2 + 2 = 4, within cap of 6
        f9 = next(f for f in factor_scores if f.factor_id == "F9")
        assert f9.points_deducted == 4.0
        assert f9.sub_components.get("pattern_modifier") == 2.0

    def test_pattern_modifiers_no_detected_patterns(self) -> None:
        """Pattern modifiers do nothing when no patterns detected."""
        from do_uw.stages.score import _apply_pattern_modifiers

        factor_scores = [
            FactorScore(
                factor_name="Test",
                factor_id="F1",
                max_points=20,
                points_deducted=10.0,
            ),
        ]
        patterns = [
            PatternMatch(
                pattern_id="TEST",
                detected=False,
                score_impact={"F1": 5.0},
            ),
        ]

        _apply_pattern_modifiers(factor_scores, patterns, {})
        assert factor_scores[0].points_deducted == 10.0
