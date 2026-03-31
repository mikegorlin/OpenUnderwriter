"""Tests for dashboard chart builders and chart API endpoints.

Tests Plotly chart generation functions and the /api/chart/* endpoints
that return Plotly JSON specs for client-side rendering.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from do_uw.dashboard.app import create_app
from do_uw.dashboard.charts import (
    build_factor_bar_chart,
    build_risk_heatmap,
    build_risk_radar,
    build_score_gauge,
    build_tier_gauge,
)
from do_uw.dashboard.charts_financial import (
    build_distress_gauges,
    build_peer_comparison_bars,
    build_red_flag_summary,
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

# -- Test helpers --


def _make_scored_state() -> AnalysisState:
    """Create an AnalysisState with mock scoring data for chart tests."""
    factors = [
        FactorScore(
            factor_name=f"Factor {i}",
            factor_id=f"F{i}",
            max_points=max_pts,
            points_deducted=deducted,
        )
        for i, (max_pts, deducted) in enumerate(
            [
                (20, 15),  # F0: 75%
                (15, 10),  # F1: 67%
                (10, 2),   # F2: 20%
                (10, 8),   # F3: 80%
                (10, 5),   # F4: 50%
                (5, 1),    # F5: 20%
                (5, 3),    # F6: 60%
                (10, 7),   # F7: 70%
                (10, 4),   # F8: 40%
                (5, 0),    # F9: 0%
            ],
            start=1,
        )
    ]
    red_flags = [
        RedFlagResult(
            flag_id="CRF-1",
            flag_name="Active SEC Investigation",
            triggered=True,
            ceiling_applied=30,
        ),
        RedFlagResult(
            flag_id="CRF-2",
            flag_name="Restatement Pending",
            triggered=True,
            ceiling_applied=50,
        ),
        RedFlagResult(
            flag_id="CRF-3",
            flag_name="Low Short Interest",
            triggered=False,
        ),
    ]
    scoring = ScoringResult(
        quality_score=30.0,
        composite_score=45.0,
        total_risk_points=55.0,
        factor_scores=factors,
        red_flags=red_flags,
        tier=TierClassification(
            tier=Tier.WATCH,
            score_range_low=26,
            score_range_high=50,
        ),
    )
    return AnalysisState(ticker="TEST", scoring=scoring)


def _make_financial_state() -> AnalysisState:
    """Create an AnalysisState with mock distress scores for chart tests."""
    distress = DistressIndicators(
        altman_z_score=DistressResult(score=2.5, zone=DistressZone.GREY),
        ohlson_o_score=DistressResult(score=0.3, zone=DistressZone.SAFE),
        beneish_m_score=DistressResult(score=-2.1, zone=DistressZone.SAFE),
        piotroski_f_score=DistressResult(score=6.0, zone=DistressZone.GREY),
    )
    financials = ExtractedFinancials(distress=distress)
    extracted = ExtractedData(financials=financials)
    return AnalysisState(ticker="FINTEST", extracted=extracted)


def _write_scored_state(tmp_path: Path) -> Path:
    """Write a scored state file and return its path."""
    state = _make_scored_state()
    state_path = tmp_path / "TEST" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    return state_path


def _write_financial_state(tmp_path: Path) -> Path:
    """Write a financial state file and return its path."""
    state = _make_financial_state()
    # Merge scoring so chart endpoints work end-to-end
    scored = _make_scored_state()
    state.scoring = scored.scoring
    state_path = tmp_path / "FINTEST" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    return state_path


# -- Direct chart builder tests --


def test_build_risk_radar() -> None:
    """Risk radar returns a valid Plotly figure with data and layout."""
    state = _make_scored_state()
    fig: Any = build_risk_radar(state)
    d = fig.to_dict()
    assert "data" in d
    assert "layout" in d
    assert len(d["data"]) > 0


def test_build_risk_radar_empty_state() -> None:
    """Risk radar returns a valid empty figure for state without scoring."""
    state = AnalysisState(ticker="EMPTY")
    fig: Any = build_risk_radar(state)
    d = fig.to_dict()
    assert "data" in d
    assert "layout" in d


def test_build_risk_heatmap() -> None:
    """Risk heatmap returns valid Plotly figure with heatmap data."""
    state = _make_scored_state()
    fig: Any = build_risk_heatmap(state)
    d = fig.to_dict()
    assert "data" in d
    assert len(d["data"]) > 0
    assert d["data"][0]["type"] == "heatmap"


def test_build_factor_bar_chart() -> None:
    """Factor bar chart returns valid horizontal bar chart data."""
    state = _make_scored_state()
    fig: Any = build_factor_bar_chart(state)
    d = fig.to_dict()
    assert "data" in d
    assert len(d["data"]) > 0
    assert d["data"][0]["type"] == "bar"
    assert d["data"][0]["orientation"] == "h"


def test_build_score_gauge() -> None:
    """Score gauge returns valid indicator figure."""
    fig: Any = build_score_gauge(65.0, 100.0, "Test Gauge")
    d = fig.to_dict()
    assert "data" in d
    assert d["data"][0]["type"] == "indicator"
    assert d["data"][0]["value"] == 65.0


def test_build_tier_gauge() -> None:
    """Tier gauge returns valid indicator figure for quality score."""
    fig: Any = build_tier_gauge(75.0)
    d = fig.to_dict()
    assert "data" in d
    assert d["data"][0]["type"] == "indicator"
    assert d["data"][0]["value"] == 75.0


def test_build_distress_gauges() -> None:
    """Distress gauges return dict with 4 model keys."""
    state = _make_financial_state()
    gauges = build_distress_gauges(state)
    assert set(gauges.keys()) == {"z_score", "o_score", "m_score", "f_score"}
    for key, fig in gauges.items():
        d: Any = fig.to_dict()
        assert "data" in d, f"Missing data for {key}"


def test_build_distress_gauges_empty() -> None:
    """Distress gauges return empty figures for state without financials."""
    state = AnalysisState(ticker="EMPTY")
    gauges = build_distress_gauges(state)
    assert len(gauges) == 4


def test_build_red_flag_summary() -> None:
    """Red flag summary shows triggered flags only."""
    state = _make_scored_state()
    fig: Any = build_red_flag_summary(state)
    d = fig.to_dict()
    assert "data" in d
    # Should have 2 triggered flags (CRF-1 and CRF-2, not CRF-3)
    if d["data"]:
        bar_data = d["data"][0]
        assert len(bar_data.get("y", [])) == 2


def test_build_red_flag_summary_no_flags() -> None:
    """Red flag summary returns empty figure when no flags triggered."""
    state = AnalysisState(ticker="CLEAN")
    fig: Any = build_red_flag_summary(state)
    d = fig.to_dict()
    assert "data" in d


def test_build_peer_comparison_no_benchmark() -> None:
    """Peer comparison returns empty figure without benchmark data."""
    state = AnalysisState(ticker="NOBENCH")
    fig: Any = build_peer_comparison_bars(state, "quality_score")
    d = fig.to_dict()
    assert "data" in d


def test_build_peer_comparison_with_peers() -> None:
    """Peer comparison bars include company and peer values."""
    scored = _make_scored_state()
    scored.benchmark = BenchmarkResult(
        peer_group_tickers=["PEER1", "PEER2"],
        peer_quality_scores={"PEER1": 60.0, "PEER2": 80.0},
    )
    fig: Any = build_peer_comparison_bars(scored, "quality_score")
    d = fig.to_dict()
    assert "data" in d
    assert len(d["data"]) > 0
    bar_data = d["data"][0]
    # Should have company + 2 peers = 3 bars
    assert len(bar_data.get("y", [])) == 3


def test_build_peer_comparison_generic_metric() -> None:
    """Peer comparison bars work with generic metric."""
    scored = _make_scored_state()
    scored.benchmark = BenchmarkResult(
        metric_details={
            "market_cap": MetricBenchmark(
                metric_name="Market Cap",
                company_value=5.0,
                baseline_value=10.0,
            ),
        },
    )
    fig: Any = build_peer_comparison_bars(scored, "market_cap")
    d = fig.to_dict()
    assert "data" in d
    bar_data = d["data"][0]
    # Company + Sector Avg = 2 bars
    assert len(bar_data.get("y", [])) == 2


# -- Chart API endpoint tests --


def test_chart_api_risk_radar(tmp_path: Path) -> None:
    """GET /api/chart/risk-radar returns 200 with valid Plotly JSON."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/risk-radar")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "layout" in data


def test_chart_api_risk_heatmap(tmp_path: Path) -> None:
    """GET /api/chart/risk-heatmap returns 200."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/risk-heatmap")
    assert response.status_code == 200
    assert "data" in response.json()


def test_chart_api_factor_bars(tmp_path: Path) -> None:
    """GET /api/chart/factor-bars returns 200."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/factor-bars")
    assert response.status_code == 200
    assert "data" in response.json()


def test_chart_api_quality_gauge(tmp_path: Path) -> None:
    """GET /api/chart/quality-gauge returns 200 with indicator data."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/quality-gauge")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_chart_api_distress_model(tmp_path: Path) -> None:
    """GET /api/chart/distress/z_score returns 200."""
    state_path = _write_financial_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/distress/z_score")
    assert response.status_code == 200
    assert "data" in response.json()


def test_chart_api_distress_unknown_model(tmp_path: Path) -> None:
    """GET /api/chart/distress/unknown returns 200 with empty figure."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/distress/unknown_model")
    assert response.status_code == 200
    assert "data" in response.json()


def test_chart_api_red_flags(tmp_path: Path) -> None:
    """GET /api/chart/red-flags returns 200."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/red-flags")
    assert response.status_code == 200
    assert "data" in response.json()


def test_chart_api_peer_comparison(tmp_path: Path) -> None:
    """GET /api/chart/peer-comparison/quality_score returns 200."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/peer-comparison/quality_score")
    assert response.status_code == 200
    assert "data" in response.json()


def test_chart_api_peer_comparison_market_cap(
    tmp_path: Path,
) -> None:
    """GET /api/chart/peer-comparison/market_cap returns 200."""
    state = _make_scored_state()
    state.benchmark = BenchmarkResult(
        metric_details={
            "market_cap": MetricBenchmark(
                metric_name="Market Cap",
                company_value=5.0,
                baseline_value=10.0,
            ),
        },
    )
    state_path = tmp_path / "PEER" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        state.model_dump_json(indent=2), encoding="utf-8",
    )
    client = TestClient(create_app(state_path))
    response = client.get("/api/chart/peer-comparison/market_cap")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data


def test_index_has_chart_containers(tmp_path: Path) -> None:
    """GET / includes chart containers with data-chart-url attributes."""
    state_path = _write_scored_state(tmp_path)
    client = TestClient(create_app(state_path))
    response = client.get("/")
    assert response.status_code == 200
    text = response.text
    assert 'data-chart-url="/api/chart/risk-radar"' in text
    assert 'data-chart-url="/api/chart/quality-gauge"' in text
    assert 'data-chart-url="/api/chart/factor-bars"' in text
    assert 'data-chart-url="/api/chart/risk-heatmap"' in text
    assert 'data-chart-url="/api/chart/distress/z_score"' in text
    assert 'data-chart-url="/api/chart/red-flags"' in text
