"""Tests for severity model, tower recommendation, and red flag summary.

SECT7-08: Loss severity scenarios at 4 percentile levels.
SECT7-09: Tower position recommendation with Side A assessment.
SECT7-10: Red flag summary consolidation by severity tier.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.financials import (
    AuditProfile,
    DistressIndicators,
    DistressResult,
    ExtractedFinancials,
)
from do_uw.models.scoring import (
    FactorScore,
    FlaggedItem,
    FlagSeverity,
    PatternMatch,
    RedFlagResult,
    Tier,
    TierClassification,
)
from do_uw.models.scoring_output import (
    AllegationMapping,
    AllegationTheory,
    TheoryExposure,
    TowerPosition,
)
from do_uw.models.state import ExtractedData
from do_uw.stages.score.severity_model import (
    compile_red_flag_summary,
    model_severity,
    recommend_tower,
)

NOW = datetime.now(tz=UTC)


def _sv(value: object, source: str = "test", conf: Confidence = Confidence.HIGH) -> SourcedValue:  # type: ignore[type-arg]
    """Shorthand to create a SourcedValue for testing."""
    return SourcedValue(value=value, source=source, confidence=conf, as_of=NOW)


def _load_scoring_config() -> dict:  # type: ignore[type-arg]
    """Load the real scoring.json for testing."""
    brain_dir = Path(__file__).parent.parent / "src" / "do_uw" / "brain" / "config"
    with (brain_dir / "scoring.json").open() as f:
        return json.load(f)  # type: ignore[no-any-return]


def _make_tier(tier: Tier) -> TierClassification:
    """Create a TierClassification for a given tier."""
    ranges = {
        Tier.WIN: (86, 100),
        Tier.WANT: (71, 85),
        Tier.WRITE: (51, 70),
        Tier.WATCH: (31, 50),
        Tier.WALK: (11, 30),
        Tier.NO_TOUCH: (0, 10),
    }
    low, high = ranges[tier]
    return TierClassification(
        tier=tier,
        score_range_low=low,
        score_range_high=high,
        probability_range="5-10%",
    )


# -----------------------------------------------------------------------
# SECT7-08: model_severity tests
# -----------------------------------------------------------------------


class TestModelSeverity:
    """Test loss severity scenario modeling."""

    def test_none_market_cap_returns_none(self) -> None:
        """model_severity returns None when market_cap is None."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = model_severity(None, tier, config)
        assert result is None

    def test_10b_write_tier_produces_scenarios(self) -> None:
        """$10B market cap, WRITE tier -> 4 reasonable scenarios."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = model_severity(10e9, tier, config)

        assert result is not None
        assert result.market_cap == 10e9
        assert len(result.scenarios) == 4
        assert result.needs_calibration is True

    def test_500m_walk_tier_higher_multipliers(self) -> None:
        """$500M market cap, WALK tier -> higher multiplied scenarios."""
        config = _load_scoring_config()
        tier_walk = _make_tier(Tier.WALK)
        tier_write = _make_tier(Tier.WRITE)

        result_walk = model_severity(500e6, tier_walk, config)
        result_write = model_severity(500e6, tier_write, config)

        assert result_walk is not None
        assert result_write is not None

        # WALK multiplier [1.5, 2.0] vs WRITE [1.0, 1.0]
        # 75th percentile (high base * high mult) should be higher for WALK
        walk_75 = result_walk.scenarios[2].settlement_estimate
        write_75 = result_write.scenarios[2].settlement_estimate
        assert walk_75 > write_75

    def test_ddl_scenarios_correct(self) -> None:
        """DDL scenarios are 10%/20%/30% of market cap."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = model_severity(10e9, tier, config)

        assert result is not None
        assert result.decline_scenarios["10%"] == 10e9 * 0.10
        assert result.decline_scenarios["20%"] == 10e9 * 0.20
        assert result.decline_scenarios["30%"] == 10e9 * 0.30

    def test_scenarios_ascending_order(self) -> None:
        """4 percentile scenarios are in ascending total exposure order."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WATCH)
        result = model_severity(5e9, tier, config)

        assert result is not None
        exposures = [s.total_exposure for s in result.scenarios]
        assert exposures == sorted(exposures)

    def test_defense_cost_proportions(self) -> None:
        """Defense costs are 15%/20%/25%/30% of settlement estimates."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = model_severity(10e9, tier, config)

        assert result is not None
        expected_pcts = [0.15, 0.20, 0.25, 0.30]
        for scenario, pct in zip(result.scenarios, expected_pcts, strict=True):
            if scenario.settlement_estimate > 0:
                actual_pct = scenario.defense_cost_estimate / scenario.settlement_estimate
                assert abs(actual_pct - pct) < 0.001, (
                    f"Scenario {scenario.label}: expected {pct}, got {actual_pct}"
                )

    def test_percentile_labels(self) -> None:
        """Scenarios have correct percentile and label assignments."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = model_severity(10e9, tier, config)

        assert result is not None
        assert result.scenarios[0].percentile == 25
        assert result.scenarios[0].label == "favorable"
        assert result.scenarios[1].percentile == 50
        assert result.scenarios[1].label == "median"
        assert result.scenarios[2].percentile == 75
        assert result.scenarios[2].label == "adverse"
        assert result.scenarios[3].percentile == 95
        assert result.scenarios[3].label == "catastrophic"

    def test_total_exposure_equals_settlement_plus_defense(self) -> None:
        """total_exposure = settlement_estimate + defense_cost_estimate."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = model_severity(10e9, tier, config)

        assert result is not None
        for scenario in result.scenarios:
            expected = scenario.settlement_estimate + scenario.defense_cost_estimate
            assert abs(scenario.total_exposure - expected) < 0.01


# -----------------------------------------------------------------------
# SECT7-09: recommend_tower tests
# -----------------------------------------------------------------------


class TestRecommendTower:
    """Test tower position recommendation."""

    def test_win_tier_primary_position(self) -> None:
        """WIN tier -> PRIMARY position."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WIN)
        result = recommend_tower(tier, None, ExtractedData(), config)

        assert result.recommended_position == TowerPosition.PRIMARY
        assert result.needs_calibration is True

    def test_walk_tier_high_excess_position(self) -> None:
        """WALK tier -> HIGH_EXCESS position."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WALK)
        result = recommend_tower(tier, None, ExtractedData(), config)

        assert result.recommended_position == TowerPosition.HIGH_EXCESS

    def test_no_touch_tier_decline_position(self) -> None:
        """NO_TOUCH tier -> DECLINE position."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.NO_TOUCH)
        result = recommend_tower(tier, None, ExtractedData(), config)

        assert result.recommended_position == TowerPosition.DECLINE

    def test_layers_from_config(self) -> None:
        """Layer assessments are built from config tower_positions."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = recommend_tower(tier, None, ExtractedData(), config)

        # Should have layers for PRIMARY through DECLINE
        assert len(result.layers) >= 4
        positions = [layer.position for layer in result.layers]
        assert TowerPosition.PRIMARY in positions
        assert TowerPosition.MID_EXCESS in positions

    def test_minimum_attachment_with_severity(self) -> None:
        """Minimum attachment computed from 50th percentile severity."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        severity = model_severity(10e9, tier, config)
        result = recommend_tower(tier, severity, ExtractedData(), config)

        assert "50th percentile" in result.minimum_attachment

    def test_minimum_attachment_without_severity(self) -> None:
        """Without severity data, attachment has insufficient data message."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = recommend_tower(tier, None, ExtractedData(), config)

        assert "Insufficient data" in result.minimum_attachment

    def test_side_a_going_concern(self) -> None:
        """Going concern -> HIGH Side A value."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WALK)
        extracted = ExtractedData(
            financials=ExtractedFinancials(
                audit=AuditProfile(going_concern=_sv(True))
            )
        )
        result = recommend_tower(tier, None, extracted, config)

        assert "HIGH Side A value" in result.side_a_assessment
        assert "going concern" in result.side_a_assessment.lower()

    def test_side_a_altman_z_distress(self) -> None:
        """Altman Z distress zone -> HIGH Side A value."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WALK)
        extracted = ExtractedData(
            financials=ExtractedFinancials(
                distress=DistressIndicators(
                    altman_z_score=DistressResult(
                        score=1.2,
                        zone="distress",
                        data_quality="complete",
                    )
                )
            )
        )
        result = recommend_tower(tier, None, extracted, config)

        assert "HIGH Side A value" in result.side_a_assessment
        assert "Altman Z" in result.side_a_assessment

    def test_side_a_standard(self) -> None:
        """No distress indicators -> Standard Side A considerations."""
        config = _load_scoring_config()
        tier = _make_tier(Tier.WRITE)
        result = recommend_tower(tier, None, ExtractedData(), config)

        assert "Standard Side A" in result.side_a_assessment


# -----------------------------------------------------------------------
# SECT7-10: compile_red_flag_summary tests
# -----------------------------------------------------------------------


class TestCompileRedFlagSummary:
    """Test red flag summary consolidation."""

    def test_two_crf_triggers_two_critical(self) -> None:
        """2 triggered CRFs -> 2 CRITICAL items."""
        red_flags = [
            RedFlagResult(
                flag_id="CRF-1",
                flag_name="Active SCA",
                triggered=True,
                ceiling_applied=30,
                evidence=["Active class action found"],
            ),
            RedFlagResult(
                flag_id="CRF-4",
                flag_name="Going Concern",
                triggered=True,
                ceiling_applied=50,
                evidence=["Going concern opinion"],
            ),
            RedFlagResult(flag_id="CRF-5", triggered=False),
        ]

        result = compile_red_flag_summary([], red_flags, [], None)
        assert result.critical_count == 2
        critical_items = [i for i in result.items if i.severity == FlagSeverity.CRITICAL]
        assert len(critical_items) == 2

    def test_factor_scores_severity_mapping(self) -> None:
        """Factor scores map to correct severity tiers."""
        factor_scores = [
            FactorScore(
                factor_name="Prior Litigation",
                factor_id="F1",
                max_points=20,
                points_deducted=18.0,
                evidence=["Active SCA"],
            ),
            FactorScore(
                factor_name="Stock Decline",
                factor_id="F2",
                max_points=15,
                points_deducted=9.0,
                evidence=["45% decline"],
            ),
            FactorScore(
                factor_name="Governance",
                factor_id="F9",
                max_points=6,
                points_deducted=1.0,
                evidence=["Minor issue"],
            ),
            FactorScore(
                factor_name="No Issue",
                factor_id="F10",
                max_points=2,
                points_deducted=0.0,
            ),
        ]

        result = compile_red_flag_summary(factor_scores, [], [], None)

        # F1: 18/20 = 90% -> HIGH
        # F2: 9/15 = 60% -> MODERATE
        # F9: 1/6 = 16.7% -> LOW
        # F10: 0 -> not included
        assert result.high_count == 1
        assert result.moderate_count == 1
        assert result.low_count == 1
        assert len(result.items) == 3

    def test_empty_inputs_empty_summary(self) -> None:
        """All empty inputs -> empty summary."""
        result = compile_red_flag_summary([], [], [], None)

        assert result.critical_count == 0
        assert result.high_count == 0
        assert result.moderate_count == 0
        assert result.low_count == 0
        assert len(result.items) == 0

    def test_pattern_severity_mapping(self) -> None:
        """Detected patterns map severity correctly."""
        patterns = [
            PatternMatch(
                pattern_id="PATTERN.STOCK.EVENT_COLLAPSE",
                pattern_name="Event Collapse",
                detected=True,
                severity="SEVERE",
                triggers_matched=["Stock drop >25%", "Earnings trigger"],
                score_impact={"F2": 3.0},
            ),
            PatternMatch(
                pattern_id="PATTERN.GOV.TURNOVER_STRESS",
                pattern_name="Turnover Stress",
                detected=True,
                severity="ELEVATED",
                triggers_matched=["CEO <2yr"],
            ),
            PatternMatch(
                pattern_id="PATTERN.STOCK.CASCADE",
                pattern_name="Not Detected",
                detected=False,
            ),
        ]

        result = compile_red_flag_summary([], [], patterns, None)

        # SEVERE -> HIGH, ELEVATED -> MODERATE
        assert result.high_count == 1
        assert result.moderate_count == 1
        assert len(result.items) == 2

    def test_items_sorted_by_severity(self) -> None:
        """Items are sorted CRITICAL > HIGH > MODERATE > LOW."""
        red_flags = [
            RedFlagResult(
                flag_id="CRF-1", flag_name="SCA", triggered=True,
                ceiling_applied=30, evidence=["SCA"],
            ),
        ]
        factor_scores = [
            FactorScore(
                factor_name="Test", factor_id="F1",
                max_points=20, points_deducted=5.0, evidence=["test"],
            ),
        ]

        result = compile_red_flag_summary(factor_scores, red_flags, [], None)

        assert len(result.items) >= 2
        # First item should be CRITICAL (CRF trigger)
        assert result.items[0].severity == FlagSeverity.CRITICAL
        # Last item should be LOW (F1: 5/20 = 25%)
        assert result.items[-1].severity == FlagSeverity.LOW

    def test_allegation_theory_in_factor_flags(self) -> None:
        """Factor flags include allegation theory when mapping available."""
        factor_scores = [
            FactorScore(
                factor_name="Prior Litigation",
                factor_id="F1",
                max_points=20,
                points_deducted=15.0,
                evidence=["Active SCA"],
            ),
        ]
        allegation_mapping = AllegationMapping(
            theories=[
                TheoryExposure(
                    theory=AllegationTheory.A_DISCLOSURE,
                    exposure_level="HIGH",
                    factor_sources=["F1", "F3"],
                ),
            ],
            primary_exposure=AllegationTheory.A_DISCLOSURE,
        )

        result = compile_red_flag_summary(factor_scores, [], [], allegation_mapping)

        assert len(result.items) == 1
        assert result.items[0].allegation_theory == "A_DISCLOSURE"

    def test_flagged_item_serialization(self) -> None:
        """FlaggedItem serializes and deserializes correctly."""
        item = FlaggedItem(
            description="Test flag",
            source="Test source",
            severity=FlagSeverity.HIGH,
            scoring_impact="F1: 15 pts",
            allegation_theory="A_DISCLOSURE",
            trajectory="NEW",
        )
        data = item.model_dump()
        restored = FlaggedItem.model_validate(data)

        assert restored.description == "Test flag"
        assert restored.severity == FlagSeverity.HIGH
        assert restored.trajectory == "NEW"


class TestSeverityModelLineCount:
    """Verify file stays under 500-line limit."""

    def test_severity_model_under_500_lines(self) -> None:
        """severity_model.py must be under 500 lines."""
        path = (
            Path(__file__).parent.parent
            / "src"
            / "do_uw"
            / "stages"
            / "score"
            / "severity_model.py"
        )
        line_count = len(path.read_text().splitlines())
        assert line_count < 500, f"severity_model.py has {line_count} lines (max 500)"
