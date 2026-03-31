"""Tests for dashboard state_api extraction functions.

Unit tests for section detail, finding detail, meeting questions,
and peer metrics extraction from AnalysisState.
Split from test_dashboard.py for 500-line compliance.
"""

from __future__ import annotations

from do_uw.dashboard.state_api import (
    build_dashboard_context,
    extract_finding_detail,
    extract_meeting_questions,
    extract_peer_metrics,
    extract_section_detail,
)
from do_uw.models.financials import (
    DistressIndicators,
    DistressResult,
    DistressZone,
    ExtractedFinancials,
)
from do_uw.models.scoring import (
    BenchmarkResult,
    FactorScore,
    MetricBenchmark,
    RedFlagResult,
    ScoringResult,
    Tier,
    TierClassification,
)
from do_uw.models.state import AnalysisState, ExtractedData


def _make_rich_state() -> AnalysisState:
    """Create a state with scoring, financials, benchmark for tests."""
    factors = [
        FactorScore(
            factor_name=f"Factor {i}",
            factor_id=f"F{i}",
            max_points=10,
            points_deducted=float(i),
            evidence=[f"Evidence for F{i}"],
            rules_triggered=[f"F{i}-001"],
        )
        for i in range(1, 4)
    ]
    red_flags = [
        RedFlagResult(
            flag_id="CRF-1",
            flag_name="Active SEC Investigation",
            triggered=True,
            ceiling_applied=30,
            evidence=["SEC Wells notice"],
        ),
    ]
    scoring = ScoringResult(
        quality_score=45.0,
        composite_score=55.0,
        total_risk_points=45.0,
        factor_scores=factors,
        red_flags=red_flags,
        tier=TierClassification(
            tier=Tier.WATCH,
            score_range_low=26,
            score_range_high=50,
        ),
    )
    distress = DistressIndicators(
        altman_z_score=DistressResult(
            score=1.5, zone=DistressZone.DISTRESS,
        ),
    )
    financials = ExtractedFinancials(distress=distress)
    extracted = ExtractedData(financials=financials)
    benchmark = BenchmarkResult(
        peer_group_tickers=["PEER1", "PEER2"],
        peer_quality_scores={"PEER1": 60.0, "PEER2": 75.0},
        metric_details={
            "market_cap": MetricBenchmark(
                metric_name="Market Cap",
                company_value=5.0,
                baseline_value=10.0,
            ),
        },
    )
    return AnalysisState(
        ticker="RICH",
        scoring=scoring,
        extracted=extracted,
        benchmark=benchmark,
    )


# ---- build_dashboard_context tests ----


def test_state_api_build_context() -> None:
    """build_dashboard_context returns expected keys."""
    state = AnalysisState(ticker="AAPL")
    ctx = build_dashboard_context(state)
    assert ctx["ticker"] == "AAPL"
    assert "sections" in ctx
    assert isinstance(ctx["sections"], list)
    assert len(ctx["sections"]) == 7
    assert "risk_level_class" in ctx
    assert "company_name" in ctx


def test_state_api_section_ids() -> None:
    """build_dashboard_context sections have correct IDs."""
    state = AnalysisState(ticker="TEST")
    ctx = build_dashboard_context(state)
    section_ids = [s["id"] for s in ctx["sections"]]
    assert section_ids == [
        "company",
        "financials",
        "market",
        "governance",
        "litigation",
        "scoring",
        "ai_risk",
    ]


def test_state_api_empty_state_sections() -> None:
    """Sections show 'No data' status for empty state."""
    state = AnalysisState(ticker="EMPTY")
    ctx = build_dashboard_context(state)
    for section in ctx["sections"]:
        assert section["status"] == "No data"
        assert section["status_class"] == "badge-ghost"


# ---- extract_section_detail tests ----


def test_extract_section_detail_scoring() -> None:
    """extract_section_detail returns factor data for scoring."""
    state = _make_rich_state()
    detail = extract_section_detail(state, "scoring")
    assert detail["title"] == "Risk Scoring"
    assert detail["section_id"] == "scoring"
    assert len(detail["findings"]) > 0
    assert len(detail["charts"]) > 0


def test_extract_section_detail_empty() -> None:
    """extract_section_detail returns empty findings for empty state."""
    state = AnalysisState(ticker="EMPTY")
    detail = extract_section_detail(state, "company")
    assert detail["title"] == "Company Profile"
    assert len(detail["findings"]) == 0


def test_extract_section_detail_financials() -> None:
    """extract_section_detail for financials includes charts."""
    state = _make_rich_state()
    detail = extract_section_detail(state, "financials")
    assert detail["title"] == "Financial Health"
    assert len(detail["charts"]) == 4  # 4 distress gauges


def test_extract_section_detail_unknown() -> None:
    """extract_section_detail for unknown section returns title."""
    state = _make_rich_state()
    detail = extract_section_detail(state, "unknown_section")
    assert detail["title"] == "Unknown_Section"
    assert len(detail["findings"]) == 0


# ---- extract_finding_detail tests ----


def test_extract_finding_detail_valid() -> None:
    """extract_finding_detail returns detail for valid index."""
    state = _make_rich_state()
    finding = extract_finding_detail(state, "scoring", 0)
    assert finding["label"] != "Not Found"
    assert "confidence" in finding
    assert "source" in finding
    assert "do_context" in finding


def test_extract_finding_detail_invalid() -> None:
    """extract_finding_detail returns 'Not Found' for invalid idx."""
    state = _make_rich_state()
    finding = extract_finding_detail(state, "scoring", 999)
    assert finding["label"] == "Not Found"


def test_extract_finding_detail_negative_idx() -> None:
    """extract_finding_detail returns 'Not Found' for negative idx."""
    state = _make_rich_state()
    finding = extract_finding_detail(state, "scoring", -1)
    assert finding["label"] == "Not Found"


# ---- extract_meeting_questions tests ----


def test_extract_meeting_questions_all() -> None:
    """extract_meeting_questions returns questions for rich state."""
    state = _make_rich_state()
    questions = extract_meeting_questions(state)
    assert isinstance(questions, list)
    assert len(questions) > 0


def test_extract_meeting_questions_filtered() -> None:
    """extract_meeting_questions filters by category."""
    state = _make_rich_state()
    all_q = extract_meeting_questions(state)
    fwd_q = extract_meeting_questions(state, "FORWARD_INDICATOR")
    assert len(fwd_q) <= len(all_q)
    for q in fwd_q:
        assert q["category"] == "FORWARD_INDICATOR"


def test_extract_meeting_questions_empty() -> None:
    """extract_meeting_questions returns empty for empty state."""
    state = AnalysisState(ticker="EMPTY")
    questions = extract_meeting_questions(state)
    assert isinstance(questions, list)


def test_extract_meeting_questions_invalid_category() -> None:
    """extract_meeting_questions returns empty for invalid category."""
    state = _make_rich_state()
    questions = extract_meeting_questions(state, "NONEXISTENT")
    assert len(questions) == 0


# ---- extract_peer_metrics tests ----


def test_extract_peer_metrics() -> None:
    """extract_peer_metrics returns available metrics."""
    state = _make_rich_state()
    metrics = extract_peer_metrics(state)
    assert metrics["ticker"] == "RICH"
    assert len(metrics["available_metrics"]) >= 2
    assert metrics["default_metric"] == "quality_score"


def test_extract_peer_metrics_empty_state() -> None:
    """extract_peer_metrics returns quality_score for empty state."""
    state = AnalysisState(ticker="EMPTY")
    metrics = extract_peer_metrics(state)
    assert len(metrics["available_metrics"]) == 1
    assert metrics["available_metrics"][0]["key"] == "quality_score"


def test_extract_peer_metrics_keys() -> None:
    """extract_peer_metrics includes both quality_score and benchmark metrics."""
    state = _make_rich_state()
    metrics = extract_peer_metrics(state)
    keys = [m["key"] for m in metrics["available_metrics"]]
    assert "quality_score" in keys
    assert "market_cap" in keys
