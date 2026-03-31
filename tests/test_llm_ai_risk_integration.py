"""Integration tests for LLM AI risk factor supplementation.

Tests that LLM-extracted risk factors categorized as 'AI' supplement the
keyword-based AIDisclosureData.risk_factors list. Non-AI factors are
ignored, and existing factors are not duplicated.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
)
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.llm.schemas.common import ExtractedRiskFactor
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction
from do_uw.stages.extract.validation import ExtractionReport


def _ten_k_dict(
    risk_factors: list[dict[str, Any]] | None = None,
) -> dict[str, object]:
    """Build a TenKExtraction dict with risk factors."""
    factors = [ExtractedRiskFactor(**rf) for rf in (risk_factors or [])]
    extraction = TenKExtraction(risk_factors=factors)
    return extraction.model_dump()


def _make_state(
    with_llm: bool = True,
    risk_factors: list[dict[str, Any]] | None = None,
) -> AnalysisState:
    """Create state with optional LLM 10-K extraction."""
    state = AnalysisState(ticker="TEST")
    llm_extractions: dict[str, object] = {}
    if with_llm:
        llm_extractions["10-K:0001-24-000001"] = _ten_k_dict(risk_factors)
    state.acquired_data = AcquiredData(llm_extractions=llm_extractions)
    return state


def _run_ai_risk(
    state: AnalysisState,
    disclosure: AIDisclosureData | None = None,
) -> tuple[AIRiskAssessment, list[ExtractionReport]]:
    """Run AI risk extractors with individual extractors mocked."""
    reports: list[ExtractionReport] = []
    disc = disclosure or AIDisclosureData(mention_count=5)
    with (
        patch(
            "do_uw.stages.extract.extract_ai_risk._run_disclosure",
            return_value=disc,
        ),
        patch(
            "do_uw.stages.extract.extract_ai_risk._run_patent",
            return_value=AIPatentActivity(ai_patent_count=0),
        ),
        patch(
            "do_uw.stages.extract.extract_ai_risk._run_competitive",
            return_value=AICompetitivePosition(adoption_stance="UNKNOWN"),
        ),
    ):
        from do_uw.stages.extract.extract_ai_risk import run_ai_risk_extractors

        assessment = run_ai_risk_extractors(state, reports)
    return assessment, reports


class TestAIRiskWithLLMFactors:
    """AI-categorized risk factors supplement disclosure."""

    def test_ai_factors_added(self) -> None:
        """LLM risk factors with AI category added to disclosure."""
        state = _make_state(
            with_llm=True,
            risk_factors=[
                {
                    "title": "AI model bias may cause discrimination lawsuits",
                    "category": "AI",
                    "severity": "HIGH",
                },
                {
                    "title": "AI training data privacy regulations evolving",
                    "category": "AI",
                    "severity": "MEDIUM",
                },
            ],
        )
        disclosure = AIDisclosureData(
            mention_count=5,
            risk_factors=["Existing keyword-based AI risk"],
        )
        assessment, _reports = _run_ai_risk(state, disclosure)

        # Original + 2 new AI factors
        ai_risks = assessment.disclosure_data.risk_factors
        assert len(ai_risks) == 3
        assert "Existing keyword-based AI risk" in ai_risks
        assert "AI model bias may cause discrimination lawsuits" in ai_risks
        assert "AI training data privacy regulations evolving" in ai_risks


class TestAIRiskWithoutLLM:
    """Falls back to keyword analysis when LLM absent."""

    def test_no_llm_unchanged(self) -> None:
        """Disclosure risk_factors unchanged when no LLM data."""
        state = _make_state(with_llm=False)
        disclosure = AIDisclosureData(
            mention_count=3,
            risk_factors=["Only keyword-based risk"],
        )
        assessment, _reports = _run_ai_risk(state, disclosure)

        assert len(assessment.disclosure_data.risk_factors) == 1
        assert assessment.disclosure_data.risk_factors[0] == "Only keyword-based risk"


class TestAIRiskNonAIFactorsIgnored:
    """Non-AI risk factors not added to AI disclosure."""

    def test_non_ai_ignored(self) -> None:
        """Risk factors categorized as LITIGATION, CYBER etc. are skipped."""
        state = _make_state(
            with_llm=True,
            risk_factors=[
                {
                    "title": "Securities class action pending",
                    "category": "LITIGATION",
                    "severity": "HIGH",
                },
                {
                    "title": "Data breach risk from third-party vendors",
                    "category": "CYBER",
                    "severity": "MEDIUM",
                },
                {
                    "title": "AI cost optimization may reduce workforce",
                    "category": "AI",
                    "severity": "MEDIUM",
                },
            ],
        )
        disclosure = AIDisclosureData(mention_count=2, risk_factors=[])
        assessment, _reports = _run_ai_risk(state, disclosure)

        # Only the AI-categorized factor should be added
        ai_risks = assessment.disclosure_data.risk_factors
        assert len(ai_risks) == 1
        assert ai_risks[0] == "AI cost optimization may reduce workforce"

    def test_duplicate_ai_factors_not_added(self) -> None:
        """AI factors already in disclosure are not duplicated."""
        state = _make_state(
            with_llm=True,
            risk_factors=[
                {
                    "title": "AI model governance risk",
                    "category": "AI",
                    "severity": "HIGH",
                },
            ],
        )
        disclosure = AIDisclosureData(
            mention_count=3,
            risk_factors=["AI model governance risk"],
        )
        assessment, _reports = _run_ai_risk(state, disclosure)

        # Should not be duplicated
        assert len(assessment.disclosure_data.risk_factors) == 1
