"""Tests for AI Transformation Risk scoring engine.

Covers:
- score_ai_risk with minimal state (no extraction data)
- score_ai_risk with populated disclosure data
- Individual sub-dimension scorers with HIGH/MEDIUM/LOW threat levels
- Weights load correctly from config
- get_ai_impact_model selects correct model
- overall_score in 0-100 range
- Narrative is non-empty
"""

from __future__ import annotations

from do_uw.knowledge.ai_impact_models import (
    AI_IMPACT_MODELS,
    get_ai_impact_model,
)
from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
)
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.score.ai_risk_scoring import (
    generate_ai_risk_narrative,
    score_ai_risk,
    score_competitive_moat,
    score_cost_structure,
    score_regulatory_ip,
    score_revenue_displacement,
    score_workforce_automation,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_state() -> AnalysisState:
    """Create a minimal AnalysisState with no extraction data."""
    return AnalysisState(ticker="TEST")


def _state_with_disclosure(
    mention_count: int = 25,
    threat_mentions: int = 15,
    opportunity_mentions: int = 10,
    sentiment: str = "THREAT",
    yoy_trend: str = "INCREASING",
    risk_factors: list[str] | None = None,
) -> AnalysisState:
    """Create state with populated AI disclosure data."""
    disclosure = AIDisclosureData(
        mention_count=mention_count,
        risk_factors=risk_factors or ["AI competition risk"],
        opportunity_mentions=opportunity_mentions,
        threat_mentions=threat_mentions,
        sentiment=sentiment,
        yoy_trend=yoy_trend,
    )
    assessment = AIRiskAssessment(disclosure_data=disclosure)
    extracted = ExtractedData(ai_risk=assessment)
    state = AnalysisState(ticker="TEST", extracted=extracted)
    return state


def _impact_model_with_threat(
    dimension: str, threat_level: str
) -> dict[str, object]:
    """Build a minimal impact model stub for a given dimension."""
    return {
        "exposure_areas": {
            dimension: {
                "threat_level": threat_level,
                "activities": ["Test activity"],
            }
        }
    }


# ---------------------------------------------------------------------------
# score_ai_risk integration tests
# ---------------------------------------------------------------------------


class TestScoreAIRiskMinimal:
    """Test score_ai_risk with minimal/empty state."""

    def test_returns_valid_assessment(self) -> None:
        """Minimal state returns a valid AIRiskAssessment."""
        state = _minimal_state()
        result = score_ai_risk(state)
        assert isinstance(result, AIRiskAssessment)
        assert 0.0 <= result.overall_score <= 100.0

    def test_has_5_sub_dimensions(self) -> None:
        """Result always has 5 sub-dimensions."""
        state = _minimal_state()
        result = score_ai_risk(state)
        assert len(result.sub_dimensions) == 5
        dim_names = {d.dimension for d in result.sub_dimensions}
        expected = {
            "revenue_displacement",
            "cost_structure",
            "competitive_moat",
            "workforce_automation",
            "regulatory_ip",
        }
        assert dim_names == expected

    def test_default_industry_model(self) -> None:
        """Minimal state uses GENERIC industry model."""
        state = _minimal_state()
        result = score_ai_risk(state)
        assert result.industry_model_id == "GENERIC"

    def test_narrative_not_empty(self) -> None:
        """Narrative is always non-empty."""
        state = _minimal_state()
        result = score_ai_risk(state)
        assert result.narrative != ""
        assert len(result.narrative) > 20

    def test_insufficient_data_evidence(self) -> None:
        """Empty state produces insufficient data evidence."""
        state = _minimal_state()
        result = score_ai_risk(state)
        all_evidence: list[str] = []
        for dim in result.sub_dimensions:
            all_evidence.extend(dim.evidence)
        assert any("Insufficient" in e for e in all_evidence)


class TestScoreAIRiskPopulated:
    """Test score_ai_risk with populated disclosure data."""

    def test_adjusts_scores(self) -> None:
        """Populated disclosure data changes scores from baseline."""
        minimal = score_ai_risk(_minimal_state())
        populated = score_ai_risk(_state_with_disclosure())

        # Scores should differ because extraction evidence adjusts them
        assert minimal.overall_score != populated.overall_score

    def test_threat_sentiment_increases_score(self) -> None:
        """THREAT sentiment should produce higher scores than OPPORTUNITY."""
        threat_state = _state_with_disclosure(
            sentiment="THREAT",
            threat_mentions=20,
            opportunity_mentions=5,
        )
        opp_state = _state_with_disclosure(
            sentiment="OPPORTUNITY",
            threat_mentions=5,
            opportunity_mentions=20,
        )
        threat_result = score_ai_risk(threat_state)
        opp_result = score_ai_risk(opp_state)
        assert threat_result.overall_score > opp_result.overall_score

    def test_data_sources_populated(self) -> None:
        """Populated state has non-empty data_sources."""
        result = score_ai_risk(_state_with_disclosure())
        assert len(result.data_sources) > 0
        assert any("SEC" in s for s in result.data_sources)

    def test_disclosure_trend_propagated(self) -> None:
        """Disclosure trend propagates to assessment."""
        result = score_ai_risk(
            _state_with_disclosure(yoy_trend="INCREASING")
        )
        assert result.disclosure_trend == "INCREASING"


# ---------------------------------------------------------------------------
# Individual sub-dimension scorer tests
# ---------------------------------------------------------------------------


class TestRevenueDisplacement:
    """Test score_revenue_displacement with different threat levels."""

    def test_high_threat_baseline(self) -> None:
        """HIGH threat level starts at 7.0."""
        model = _impact_model_with_threat("revenue_displacement", "HIGH")
        disclosure = AIDisclosureData()
        score, evidence = score_revenue_displacement(disclosure, model)
        assert score == 7.0
        assert any("Insufficient" in e for e in evidence)

    def test_low_threat_baseline(self) -> None:
        """LOW threat level starts at 3.0."""
        model = _impact_model_with_threat("revenue_displacement", "LOW")
        disclosure = AIDisclosureData()
        score, _ = score_revenue_displacement(disclosure, model)
        assert score == 3.0

    def test_threat_ratio_adjusts(self) -> None:
        """High threat ratio increases score."""
        model = _impact_model_with_threat("revenue_displacement", "MEDIUM")
        disclosure = AIDisclosureData(
            mention_count=20,
            threat_mentions=18,
            opportunity_mentions=2,
        )
        score, evidence = score_revenue_displacement(disclosure, model)
        assert score > 5.0  # Above MEDIUM baseline
        assert any("ratio" in e.lower() for e in evidence)


class TestCostStructure:
    """Test score_cost_structure with different threat levels."""

    def test_high_threat_baseline(self) -> None:
        """HIGH threat level starts at 7.0."""
        model = _impact_model_with_threat("cost_structure", "HIGH")
        disclosure = AIDisclosureData()
        score, _ = score_cost_structure(disclosure, model)
        assert score == 7.0

    def test_high_mention_count_increases(self) -> None:
        """High mention count increases score."""
        model = _impact_model_with_threat("cost_structure", "MEDIUM")
        disclosure = AIDisclosureData(mention_count=25)
        score, evidence = score_cost_structure(disclosure, model)
        assert score > 5.0
        assert any("High AI mention" in e for e in evidence)


class TestCompetitiveMoat:
    """Test score_competitive_moat with different inputs."""

    def test_no_data_returns_baseline(self) -> None:
        """No patent/competitive data returns baseline."""
        model = _impact_model_with_threat("competitive_moat", "HIGH")
        patents = AIPatentActivity()
        competitive = AICompetitivePosition()
        score, evidence = score_competitive_moat(patents, competitive, model)
        assert score == 7.0
        assert any("Insufficient" in e for e in evidence)

    def test_strong_patents_reduces_risk(self) -> None:
        """Strong patent portfolio reduces moat erosion risk."""
        model = _impact_model_with_threat("competitive_moat", "HIGH")
        patents = AIPatentActivity(ai_patent_count=60)
        competitive = AICompetitivePosition(adoption_stance="LEADING")
        score, _ = score_competitive_moat(patents, competitive, model)
        assert score < 7.0  # Below HIGH baseline due to patents + leading

    def test_lagging_increases_risk(self) -> None:
        """Lagging adoption increases moat erosion risk."""
        model = _impact_model_with_threat("competitive_moat", "MEDIUM")
        patents = AIPatentActivity(ai_patent_count=1)
        competitive = AICompetitivePosition(adoption_stance="LAGGING")
        score, evidence = score_competitive_moat(patents, competitive, model)
        assert score > 5.0  # Above MEDIUM baseline
        assert any("Lagging" in e for e in evidence)


class TestWorkforceAutomation:
    """Test score_workforce_automation."""

    def test_medium_threat_baseline(self) -> None:
        """MEDIUM threat level starts at 5.0."""
        model = _impact_model_with_threat("workforce_automation", "MEDIUM")
        disclosure = AIDisclosureData()
        score, _ = score_workforce_automation(disclosure, model)
        assert score == 5.0

    def test_extensive_disclosure_increases(self) -> None:
        """Extensive AI disclosure increases workforce risk."""
        model = _impact_model_with_threat("workforce_automation", "MEDIUM")
        disclosure = AIDisclosureData(
            mention_count=35,
            risk_factors=["AI job displacement", "Automation impact", "Skills gap"],
        )
        score, _ = score_workforce_automation(disclosure, model)
        assert score > 5.0


class TestRegulatoryIP:
    """Test score_regulatory_ip."""

    def test_high_threat_baseline(self) -> None:
        """HIGH threat level starts at 7.0."""
        model = _impact_model_with_threat("regulatory_ip", "HIGH")
        disclosure = AIDisclosureData()
        patents = AIPatentActivity()
        score, _ = score_regulatory_ip(disclosure, patents, model)
        assert score == 7.0

    def test_patents_increase_complexity(self) -> None:
        """More patents increase regulatory/IP complexity."""
        model = _impact_model_with_threat("regulatory_ip", "MEDIUM")
        disclosure = AIDisclosureData(mention_count=5)
        patents = AIPatentActivity(
            ai_patent_count=25,
            filing_trend="INCREASING",
        )
        score, evidence = score_regulatory_ip(disclosure, patents, model)
        assert score > 5.0
        assert any("patent" in e.lower() for e in evidence)


# ---------------------------------------------------------------------------
# Config and model selection tests
# ---------------------------------------------------------------------------


class TestWeightsConfig:
    """Test weights load correctly from config."""

    def test_weights_loaded(self) -> None:
        """Scoring uses weights from JSON config."""
        state = _minimal_state()
        result = score_ai_risk(state)
        # Weights should sum to ~1.0 across dimensions
        total_weight = sum(d.weight for d in result.sub_dimensions)
        assert abs(total_weight - 1.0) < 0.01

    def test_industry_weights_affect_output(self) -> None:
        """Different industries produce different composite scores."""
        state_tech = _minimal_state()
        state_tech.active_playbook_id = "TECH_SAAS"

        state_energy = _minimal_state()
        state_energy.active_playbook_id = "ENERGY_UTILITIES"

        tech_result = score_ai_risk(state_tech)
        energy_result = score_ai_risk(state_energy)

        # Different industries have different threat levels per dimension,
        # so composite scores should differ
        assert tech_result.overall_score != energy_result.overall_score
        assert tech_result.industry_model_id == "TECH_SAAS"
        assert energy_result.industry_model_id == "ENERGY_UTILITIES"


class TestGetAIImpactModel:
    """Test get_ai_impact_model selection logic."""

    def test_select_by_playbook_id(self) -> None:
        """Playbook ID exact match selects correct model."""
        model = get_ai_impact_model(None, "TECH_SAAS")
        assert model["id"] == "TECH_SAAS"

    def test_select_by_sic_code(self) -> None:
        """SIC code range match selects correct model."""
        model = get_ai_impact_model(7372, None)  # SaaS SIC range
        assert model["id"] == "TECH_SAAS"

    def test_sic_code_financial(self) -> None:
        """Financial services SIC code selects correct model."""
        model = get_ai_impact_model(6020, None)
        assert model["id"] == "FINANCIAL_SERVICES"

    def test_sic_code_biotech(self) -> None:
        """Biotech SIC code selects correct model."""
        model = get_ai_impact_model(2834, None)
        assert model["id"] == "BIOTECH_PHARMA"

    def test_sic_code_energy(self) -> None:
        """Energy SIC code selects correct model."""
        model = get_ai_impact_model(1311, None)
        assert model["id"] == "ENERGY_UTILITIES"

    def test_sic_code_healthcare(self) -> None:
        """Healthcare SIC code selects correct model."""
        model = get_ai_impact_model(8050, None)
        assert model["id"] == "HEALTHCARE"

    def test_fallback_to_generic(self) -> None:
        """Unknown SIC and no playbook returns GENERIC."""
        model = get_ai_impact_model(9999, None)
        assert model["id"] == "GENERIC"

    def test_playbook_id_takes_precedence(self) -> None:
        """Playbook ID overrides SIC code match."""
        # SIC 7372 = TECH_SAAS, but playbook says HEALTHCARE
        model = get_ai_impact_model(7372, "HEALTHCARE")
        assert model["id"] == "HEALTHCARE"

    def test_none_inputs_return_generic(self) -> None:
        """Both None returns GENERIC."""
        model = get_ai_impact_model(None, None)
        assert model["id"] == "GENERIC"


class TestOverallScoreRange:
    """Test that overall_score stays in 0-100 range."""

    def test_minimal_state_in_range(self) -> None:
        """Minimal state score is in valid range."""
        result = score_ai_risk(_minimal_state())
        assert 0.0 <= result.overall_score <= 100.0

    def test_high_threat_state_in_range(self) -> None:
        """High-threat state score stays in range."""
        state = _state_with_disclosure(
            mention_count=100,
            threat_mentions=90,
            opportunity_mentions=10,
            sentiment="THREAT",
            yoy_trend="INCREASING",
            risk_factors=["AI risk 1", "AI risk 2", "AI risk 3", "AI risk 4"],
        )
        state.active_playbook_id = "TECH_SAAS"
        result = score_ai_risk(state)
        assert 0.0 <= result.overall_score <= 100.0


class TestNarrative:
    """Test narrative generation."""

    def test_narrative_not_empty(self) -> None:
        """Narrative is always non-empty."""
        result = score_ai_risk(_minimal_state())
        assert result.narrative != ""

    def test_narrative_contains_industry(self) -> None:
        """Narrative references the industry."""
        state = _minimal_state()
        state.active_playbook_id = "TECH_SAAS"
        result = score_ai_risk(state)
        assert "Technology" in result.narrative or "SaaS" in result.narrative

    def test_narrative_contains_score(self) -> None:
        """Narrative contains the overall score."""
        result = score_ai_risk(_minimal_state())
        assert "/100" in result.narrative

    def test_generate_narrative_high_risk(self) -> None:
        """High risk narrative contains 'significant'."""
        from do_uw.models.ai_risk import AISubDimension

        assessment = AIRiskAssessment(
            overall_score=75.0,
            sub_dimensions=[
                AISubDimension(
                    dimension="revenue_displacement",
                    score=8.0,
                    weight=0.25,
                    threat_level="HIGH",
                )
            ],
        )
        narrative = generate_ai_risk_narrative(assessment, "Technology / SaaS")
        assert "significant" in narrative

    def test_generate_narrative_low_risk(self) -> None:
        """Low risk narrative contains 'limited'."""
        assessment = AIRiskAssessment(overall_score=25.0)
        narrative = generate_ai_risk_narrative(assessment, "Energy / Utilities")
        assert "limited" in narrative


class TestAIImpactModelsStructure:
    """Test AI_IMPACT_MODELS structural validity."""

    def test_six_models_defined(self) -> None:
        """All 6 impact models are defined."""
        assert len(AI_IMPACT_MODELS) == 6

    def test_all_have_required_keys(self) -> None:
        """Every model has id, industry, sic_ranges, exposure_areas."""
        for model in AI_IMPACT_MODELS:
            assert "id" in model
            assert "industry" in model
            assert "sic_ranges" in model
            assert "exposure_areas" in model

    def test_all_have_5_dimensions(self) -> None:
        """Every model defines all 5 exposure dimensions."""
        expected_dims = {
            "revenue_displacement",
            "cost_structure",
            "competitive_moat",
            "workforce_automation",
            "regulatory_ip",
        }
        for model in AI_IMPACT_MODELS:
            areas = set(model["exposure_areas"].keys())
            assert areas == expected_dims, f"Model {model['id']} missing dims"

    def test_threat_levels_valid(self) -> None:
        """All threat levels are valid enum values."""
        valid = {"HIGH", "MEDIUM", "LOW"}
        for model in AI_IMPACT_MODELS:
            for dim_name, area in model["exposure_areas"].items():
                assert area["threat_level"] in valid, (
                    f"Model {model['id']}.{dim_name} has invalid "
                    f"threat_level: {area['threat_level']}"
                )
