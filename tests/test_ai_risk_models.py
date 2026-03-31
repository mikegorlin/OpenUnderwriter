"""Tests for AI Transformation Risk Factor Pydantic models.

Covers:
- AIRiskAssessment JSON round-trip serialization
- Default value validity
- AISubDimension with all fields populated
- AICompetitivePosition optional percentile_rank
- ExtractedData.ai_risk field acceptance
"""

from __future__ import annotations

from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
    AISubDimension,
)
from do_uw.models.state import ExtractedData


class TestAIRiskAssessmentRoundTrip:
    """Test JSON serialization round-trip."""

    def test_round_trip_default(self) -> None:
        """Default AIRiskAssessment round-trips to JSON and back."""
        original = AIRiskAssessment()
        json_str = original.model_dump_json()
        restored = AIRiskAssessment.model_validate_json(json_str)
        assert restored.overall_score == original.overall_score
        assert restored.industry_model_id == "GENERIC"
        assert restored.narrative == ""
        assert restored.data_sources == []
        assert restored.sub_dimensions == []

    def test_round_trip_populated(self) -> None:
        """Fully populated AIRiskAssessment round-trips correctly."""
        sub_dim = AISubDimension(
            dimension="revenue_displacement",
            score=7.5,
            weight=0.25,
            evidence=["High AI threat mentions in 10-K"],
            threat_level="HIGH",
        )
        disclosure = AIDisclosureData(
            mention_count=42,
            risk_factors=["AI competition", "Automation risk"],
            opportunity_mentions=10,
            threat_mentions=32,
            sentiment="THREAT",
            yoy_trend="INCREASING",
        )
        patent = AIPatentActivity(
            ai_patent_count=15,
            recent_filings=[
                {
                    "patent_number": "US12345",
                    "filing_date": "2025-06-01",
                    "title": "AI Method",
                }
            ],
            filing_trend="INCREASING",
        )
        competitive = AICompetitivePosition(
            company_ai_mentions=42,
            peer_avg_mentions=25.0,
            peer_mention_counts={"MSFT": 80, "GOOG": 95},
            percentile_rank=65.0,
            adoption_stance="INLINE",
        )
        assessment = AIRiskAssessment(
            overall_score=72.5,
            sub_dimensions=[sub_dim],
            disclosure_data=disclosure,
            patent_activity=patent,
            competitive_position=competitive,
            industry_model_id="TECH_SAAS",
            disclosure_trend="INCREASING",
            narrative="Significant AI disruption risk in core SaaS market.",
            narrative_source="AI impact model TECH_SAAS",
            narrative_confidence="MEDIUM",
            peer_comparison_available=True,
            forward_indicators=["Competitor AI product launch"],
            data_sources=["SEC 10-K", "Patent DB"],
        )

        json_str = assessment.model_dump_json()
        restored = AIRiskAssessment.model_validate_json(json_str)

        assert restored.overall_score == 72.5
        assert len(restored.sub_dimensions) == 1
        assert restored.sub_dimensions[0].dimension == "revenue_displacement"
        assert restored.sub_dimensions[0].score == 7.5
        assert restored.disclosure_data.mention_count == 42
        assert restored.patent_activity.ai_patent_count == 15
        assert restored.competitive_position.percentile_rank == 65.0
        assert restored.industry_model_id == "TECH_SAAS"
        assert restored.peer_comparison_available is True
        assert len(restored.data_sources) == 2


class TestAIRiskDefaults:
    """Test that default values are valid."""

    def test_disclosure_defaults(self) -> None:
        """AIDisclosureData defaults are valid."""
        d = AIDisclosureData()
        assert d.mention_count == 0
        assert d.risk_factors == []
        assert d.opportunity_mentions == 0
        assert d.threat_mentions == 0
        assert d.sentiment == "UNKNOWN"
        assert d.yoy_trend == "UNKNOWN"

    def test_patent_defaults(self) -> None:
        """AIPatentActivity defaults are valid."""
        p = AIPatentActivity()
        assert p.ai_patent_count == 0
        assert p.recent_filings == []
        assert p.filing_trend == "UNKNOWN"

    def test_competitive_defaults(self) -> None:
        """AICompetitivePosition defaults are valid."""
        c = AICompetitivePosition()
        assert c.company_ai_mentions == 0
        assert c.peer_avg_mentions == 0.0
        assert c.peer_mention_counts == {}
        assert c.percentile_rank is None
        assert c.adoption_stance == "UNKNOWN"

    def test_assessment_defaults(self) -> None:
        """AIRiskAssessment defaults are valid."""
        a = AIRiskAssessment()
        assert a.overall_score == 0.0
        assert a.sub_dimensions == []
        assert a.industry_model_id == "GENERIC"
        assert a.disclosure_trend == "UNKNOWN"
        assert a.narrative == ""
        assert a.narrative_confidence == "LOW"
        assert a.peer_comparison_available is False
        assert a.forward_indicators == []
        assert a.data_sources == []


class TestAISubDimension:
    """Test AISubDimension with all fields populated."""

    def test_all_fields_populated(self) -> None:
        """AISubDimension with full data validates correctly."""
        dim = AISubDimension(
            dimension="workforce_automation",
            score=8.0,
            weight=0.20,
            evidence=["40% workforce in automatable roles", "No retraining program"],
            threat_level="HIGH",
        )
        assert dim.dimension == "workforce_automation"
        assert dim.score == 8.0
        assert dim.weight == 0.20
        assert len(dim.evidence) == 2
        assert dim.threat_level == "HIGH"

    def test_round_trip(self) -> None:
        """AISubDimension round-trips through JSON."""
        dim = AISubDimension(
            dimension="competitive_moat",
            score=3.5,
            weight=0.30,
            evidence=["Strong patent portfolio"],
            threat_level="LOW",
        )
        json_str = dim.model_dump_json()
        restored = AISubDimension.model_validate_json(json_str)
        assert restored.dimension == "competitive_moat"
        assert restored.score == 3.5
        assert restored.weight == 0.30


class TestAICompetitivePositionOptional:
    """Test AICompetitivePosition percentile_rank optional handling."""

    def test_percentile_rank_none(self) -> None:
        """Percentile rank is None by default."""
        c = AICompetitivePosition()
        assert c.percentile_rank is None

    def test_percentile_rank_populated(self) -> None:
        """Percentile rank accepts float value."""
        c = AICompetitivePosition(percentile_rank=85.0)
        assert c.percentile_rank == 85.0

    def test_round_trip_with_none(self) -> None:
        """Round-trip preserves None percentile_rank."""
        c = AICompetitivePosition()
        json_str = c.model_dump_json()
        restored = AICompetitivePosition.model_validate_json(json_str)
        assert restored.percentile_rank is None

    def test_round_trip_with_value(self) -> None:
        """Round-trip preserves non-None percentile_rank."""
        c = AICompetitivePosition(percentile_rank=42.0)
        json_str = c.model_dump_json()
        restored = AICompetitivePosition.model_validate_json(json_str)
        assert restored.percentile_rank == 42.0


class TestExtractedDataAIRisk:
    """Test ExtractedData.ai_risk field."""

    def test_accepts_ai_risk_assessment(self) -> None:
        """ExtractedData.ai_risk accepts AIRiskAssessment."""
        assessment = AIRiskAssessment(
            overall_score=55.0,
            industry_model_id="BIOTECH_PHARMA",
        )
        extracted = ExtractedData(ai_risk=assessment)
        assert extracted.ai_risk is not None
        assert extracted.ai_risk.overall_score == 55.0
        assert extracted.ai_risk.industry_model_id == "BIOTECH_PHARMA"

    def test_ai_risk_default_none(self) -> None:
        """ExtractedData.ai_risk defaults to None."""
        extracted = ExtractedData()
        assert extracted.ai_risk is None

    def test_round_trip_with_ai_risk(self) -> None:
        """ExtractedData with ai_risk round-trips through JSON."""
        assessment = AIRiskAssessment(overall_score=80.0)
        extracted = ExtractedData(ai_risk=assessment)
        json_str = extracted.model_dump_json()
        restored = ExtractedData.model_validate_json(json_str)
        assert restored.ai_risk is not None
        assert restored.ai_risk.overall_score == 80.0
