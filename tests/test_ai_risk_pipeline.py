"""Integration tests for the AI risk pipeline flow.

Tests end-to-end wiring: EXTRACT -> SCORE -> RENDER for AI risk.
Tests ScoreStage integration, ExtractStage wiring, Word renderer
registration, and dashboard state_api support.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from do_uw.dashboard.app import create_app
from do_uw.dashboard.state_api import (
    SECTION_TITLES,
    extract_ai_risk_detail,
    extract_section_detail,
)
from do_uw.models.ai_risk import (
    AICompetitivePosition,
    AIDisclosureData,
    AIPatentActivity,
    AIRiskAssessment,
    AISubDimension,
)
from do_uw.models.state import AnalysisState, ExtractedData
from do_uw.stages.render.word_renderer import _get_section_renderers


def _make_ai_risk_raw() -> AIRiskAssessment:
    """Create raw AI risk data as EXTRACT stage would produce.

    Contains disclosure/patent/competitive data but no scoring
    (overall_score=0, empty sub_dimensions).
    """
    return AIRiskAssessment(
        disclosure_data=AIDisclosureData(
            mention_count=20,
            risk_factors=["AI competition", "Automation risk"],
            opportunity_mentions=8,
            threat_mentions=12,
            sentiment="THREAT",
            yoy_trend="INCREASING",
        ),
        patent_activity=AIPatentActivity(
            ai_patent_count=15,
            filing_trend="STABLE",
        ),
        competitive_position=AICompetitivePosition(
            company_ai_mentions=20,
            peer_avg_mentions=15.0,
            adoption_stance="INLINE",
        ),
        disclosure_trend="INCREASING",
        peer_comparison_available=False,
        data_sources=["10-K Item 1A AI disclosures", "USPTO patent filings"],
    )


def _make_scored_ai_risk() -> AIRiskAssessment:
    """Create fully scored AI risk data (post SCORE stage)."""
    return AIRiskAssessment(
        overall_score=55.0,
        sub_dimensions=[
            AISubDimension(
                dimension="revenue_displacement",
                score=6.5,
                weight=0.25,
                evidence=["Threat ratio: 60%"],
                threat_level="HIGH",
            ),
            AISubDimension(
                dimension="cost_structure",
                score=5.5,
                weight=0.20,
                evidence=["Moderate mentions"],
                threat_level="MEDIUM",
            ),
            AISubDimension(
                dimension="competitive_moat",
                score=4.0,
                weight=0.25,
                evidence=["Moderate patent portfolio"],
                threat_level="MEDIUM",
            ),
            AISubDimension(
                dimension="workforce_automation",
                score=5.5,
                weight=0.20,
                evidence=["Notable disclosure"],
                threat_level="MEDIUM",
            ),
            AISubDimension(
                dimension="regulatory_ip",
                score=5.0,
                weight=0.10,
                evidence=["AI patents add complexity"],
                threat_level="MEDIUM",
            ),
        ],
        disclosure_data=AIDisclosureData(
            mention_count=20,
            sentiment="THREAT",
            yoy_trend="INCREASING",
        ),
        patent_activity=AIPatentActivity(
            ai_patent_count=15,
            filing_trend="STABLE",
        ),
        competitive_position=AICompetitivePosition(
            company_ai_mentions=20,
            peer_avg_mentions=15.0,
            adoption_stance="INLINE",
        ),
        industry_model_id="GENERIC",
        disclosure_trend="INCREASING",
        narrative="This General company faces moderate AI transformation risk.",
        narrative_source="AI impact model GENERIC",
        narrative_confidence="MEDIUM",
        peer_comparison_available=False,
        data_sources=["SEC filings (AI disclosure analysis)", "Patent database"],
    )


# ---- Word renderer registration tests ----


def test_word_renderer_has_scoring_section() -> None:
    """_get_section_renderers includes Section 8: Scoring & Risk Assessment."""
    renderers = _get_section_renderers()
    section_names = [name for name, _fn in renderers]
    assert "Section 8: Scoring & Risk Assessment" in section_names


def test_word_renderer_scoring_not_none() -> None:
    """Scoring section renderer function is not None (module loads)."""
    renderers = _get_section_renderers()
    renderer_map = dict(renderers)
    assert renderer_map["Section 8: Scoring & Risk Assessment"] is not None


def test_word_renderer_scoring_after_litigation() -> None:
    """Scoring appears after Litigation in renderer list."""
    renderers = _get_section_renderers()
    section_names = [name for name, _fn in renderers]
    lit_idx = section_names.index("Section 6: Litigation & Regulatory")
    scoring_idx = section_names.index("Section 8: Scoring & Risk Assessment")
    assert lit_idx < scoring_idx


# ---- Dashboard state_api tests ----


def test_section_titles_includes_ai_risk() -> None:
    """SECTION_TITLES contains ai_risk key."""
    assert "ai_risk" in SECTION_TITLES
    assert SECTION_TITLES["ai_risk"] == "AI Transformation Risk"


def testextract_ai_risk_detail_with_data() -> None:
    """extract_ai_risk_detail returns populated dict when AI risk exists."""
    state = AnalysisState(
        ticker="TEST",
        extracted=ExtractedData(ai_risk=_make_scored_ai_risk()),
    )
    detail = extract_ai_risk_detail(state)
    assert detail is not None
    assert detail["section_id"] == "ai_risk"
    assert detail["title"] == "AI Transformation Risk"
    # Data is nested under "data" key
    data = detail["data"]
    assert data["overall_score"] == 55.0
    assert data["industry_model_id"] == "GENERIC"
    assert len(data["sub_dimensions"]) == 5
    assert data["disclosure_data"]["mention_count"] == 20
    assert data["patent_activity"]["ai_patent_count"] == 15
    assert data["competitive_position"]["adoption_stance"] == "INLINE"
    assert data["narrative"] != ""
    # Findings list populated from score + sub-dimensions
    assert len(detail["findings"]) >= 1


def testextract_ai_risk_detail_without_data() -> None:
    """extract_ai_risk_detail returns empty data when no AI risk data."""
    state = AnalysisState(ticker="TEST")
    detail = extract_ai_risk_detail(state)
    # Always returns a dict (never None), but data is empty
    assert detail is not None
    assert detail["section_id"] == "ai_risk"
    assert detail["data"] == {}
    assert detail["findings"] == []


def test_extract_section_detail_ai_risk() -> None:
    """extract_section_detail for ai_risk returns enriched data."""
    state = AnalysisState(
        ticker="TEST",
        extracted=ExtractedData(ai_risk=_make_scored_ai_risk()),
    )
    detail = extract_section_detail(state, "ai_risk")
    assert detail["title"] == "AI Transformation Risk"
    assert detail["section_id"] == "ai_risk"
    # The data dict should be the enriched AI risk detail
    assert detail["data"]["overall_score"] == 55.0


def test_extract_section_detail_ai_risk_no_data() -> None:
    """extract_section_detail for ai_risk with no data returns empty."""
    state = AnalysisState(ticker="TEST")
    detail = extract_section_detail(state, "ai_risk")
    assert detail["title"] == "AI Transformation Risk"
    # No enriched data, falls through to generic extraction
    assert (
        detail["data"] == {}
        or detail["data"] is None
        or detail["data"].get("overall_score") is None
    )


# ---- Dashboard route tests ----


def _write_ai_risk_state(tmp_path: Path) -> Path:
    """Write a state file with AI risk data for dashboard tests."""
    state = AnalysisState(
        ticker="AITEST",
        extracted=ExtractedData(ai_risk=_make_scored_ai_risk()),
    )
    state_path = tmp_path / "AITEST" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    return state_path


def test_dashboard_ai_risk_section_route(tmp_path: Path) -> None:
    """GET /section/ai_risk returns 200 with AI risk content."""
    state_path = _write_ai_risk_state(tmp_path)
    app = create_app(state_path)
    client = TestClient(app)

    response = client.get("/section/ai_risk")
    assert response.status_code == 200
    text = response.text
    assert "AI Risk Score" in text
    assert "55" in text  # overall_score
    assert "GENERIC" in text  # industry_model_id


def test_dashboard_ai_risk_card_on_index(tmp_path: Path) -> None:
    """GET / shows AI Transformation Risk in section cards."""
    state_path = _write_ai_risk_state(tmp_path)
    app = create_app(state_path)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "AI Transformation Risk" in response.text


def test_dashboard_ai_risk_no_data(tmp_path: Path) -> None:
    """GET /section/ai_risk with no AI data returns 200 with no findings."""
    state = AnalysisState(ticker="EMPTY")
    state_path = tmp_path / "EMPTY" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    app = create_app(state_path)
    client = TestClient(app)

    response = client.get("/section/ai_risk")
    assert response.status_code == 200


# ---- ScoreStage AI risk integration test ----


@patch("do_uw.stages.score.ai_risk_scoring.score_ai_risk")
def test_score_stage_calls_score_ai_risk(
    mock_score_ai: MagicMock,
) -> None:
    """ScoreStage.run() calls score_ai_risk when AI risk data exists."""
    from do_uw.models.common import StageStatus
    from do_uw.stages.score import ScoreStage

    # Create a minimal state that has completed analyze stage
    state = AnalysisState(ticker="TEST")
    state.stages["analyze"].status = StageStatus.COMPLETED
    state.extracted = ExtractedData(ai_risk=_make_ai_risk_raw())

    # Mock the scoring pipeline dependencies
    scored = _make_scored_ai_risk()
    mock_score_ai.return_value = scored

    with (
        patch("do_uw.stages.score.BrainLoader") as mock_loader,
        patch("do_uw.stages.score.score_all_factors") as mock_factors,
        patch("do_uw.stages.score.detect_all_patterns") as mock_patterns,
        patch("do_uw.stages.score.evaluate_red_flag_gates") as mock_gates,
        patch("do_uw.stages.score.classify_risk_type") as mock_risk_type,
        patch("do_uw.stages.score.map_allegations") as mock_allegations,
        patch("do_uw.stages.score.compute_claim_probability") as mock_prob,
        patch("do_uw.stages.score.model_severity") as mock_severity,
        patch("do_uw.stages.score.recommend_tower") as mock_tower,
        patch("do_uw.stages.score.compile_red_flag_summary") as mock_rf_summary,
        patch("do_uw.stages.score.classify_tier") as mock_tier,
    ):
        # Set up the mocked brain
        brain_mock = MagicMock()
        brain_mock.red_flags = {}
        brain_mock.scoring = {"tiers": []}
        brain_mock.patterns = {}
        brain_mock.sectors = {}
        mock_loader.return_value.load_all.return_value = brain_mock

        # Set up factor scoring returns
        mock_gates.return_value = []
        mock_factors.return_value = []
        mock_patterns.return_value = []
        mock_risk_type.return_value = None
        mock_allegations.return_value = None
        mock_prob.return_value = None
        mock_severity.return_value = None
        mock_tower.return_value = None
        mock_rf_summary.return_value = None

        from do_uw.models.scoring import Tier, TierClassification

        mock_tier.return_value = TierClassification(
            tier=Tier.WATCH, score_range_low=26, score_range_high=50
        )

        stage = ScoreStage()
        stage.run(state)

        # Verify score_ai_risk was called
        mock_score_ai.assert_called_once_with(state)
        # Verify the scored result was assigned back
        assert state.extracted is not None
        assert state.extracted.ai_risk is not None
        assert state.extracted.ai_risk.overall_score == 55.0


# ---- ExtractStage AI risk wiring test ----


@patch("do_uw.stages.extract.run_ai_risk_extractors")
@patch("do_uw.stages.extract.run_litigation_extractors")
@patch("do_uw.stages.extract.run_governance_extractors")
@patch("do_uw.stages.extract.run_market_extractors")
def test_extract_stage_calls_ai_risk_extractors(
    mock_market: MagicMock,
    mock_governance: MagicMock,
    mock_litigation: MagicMock,
    mock_ai_risk: MagicMock,
) -> None:
    """ExtractStage.run() calls run_ai_risk_extractors."""
    from do_uw.models.common import StageStatus
    from do_uw.stages.extract import ExtractStage

    # Create a state with completed acquire stage
    state = AnalysisState(ticker="TEST")
    state.stages["acquire"].status = StageStatus.COMPLETED
    state.acquired_data = MagicMock()  # type: ignore[assignment]

    # Mock all sub-orchestrators
    mock_market.return_value = MagicMock()
    mock_governance.return_value = MagicMock()
    mock_litigation.return_value = MagicMock()
    ai_risk_result = _make_ai_risk_raw()
    mock_ai_risk.return_value = ai_risk_result

    # Mock the extractors that run before sub-orchestrators
    with (
        patch("do_uw.stages.extract.extract_company_profile") as mock_profile,
        patch("do_uw.stages.extract.extract_financial_statements") as mock_fin,
        patch("do_uw.stages.analyze.financial_models.compute_distress_indicators") as mock_distress,
        patch("do_uw.stages.analyze.earnings_quality.compute_earnings_quality") as mock_eq,
        patch("do_uw.stages.extract.extract_debt_analysis") as mock_debt,
        patch("do_uw.stages.extract.extract_audit_risk") as mock_audit,
        patch("do_uw.stages.extract.extract_tax_indicators") as mock_tax,
        patch("do_uw.stages.extract.construct_peer_group") as mock_peers,
    ):
        # Set up return values for each extractor
        from do_uw.models.common import Confidence
        from do_uw.models.financials import (
            AuditProfile,
            DistressIndicators,
            FinancialStatements,
        )
        from do_uw.stages.extract.validation import ExtractionReport

        def _report(name: str) -> ExtractionReport:
            return ExtractionReport(
                extractor_name=name,
                expected_fields=["f1"],
                found_fields=["f1"],
                missing_fields=[],
                unexpected_fields=[],
                coverage_pct=100.0,
                confidence=Confidence.HIGH,
                source_filing="mock",
            )

        mock_profile.return_value = (MagicMock(), _report("profile"))
        mock_fin.return_value = (FinancialStatements(), [_report("fin")])
        mock_distress.return_value = (DistressIndicators(), [_report("distress")])
        mock_eq.return_value = (MagicMock(), _report("eq"))
        # Debt analysis returns (liquidity, leverage, debt_struct, refi, reports)
        mock_debt.return_value = (None, None, None, None, [_report("debt")])
        mock_audit.return_value = (AuditProfile(), _report("audit"))
        mock_tax.return_value = (MagicMock(), _report("tax"))
        mock_peers.return_value = (MagicMock(), _report("peers"))

        stage = ExtractStage()
        stage.run(state)

    # Verify AI risk extractors were called
    mock_ai_risk.assert_called_once()
    # Verify result was assigned
    assert state.extracted is not None
    assert state.extracted.ai_risk is ai_risk_result
