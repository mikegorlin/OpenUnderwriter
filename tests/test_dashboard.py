"""Tests for the interactive dashboard.

Tests the FastAPI dashboard app factory, state API context building,
drill-down routes, meeting prep, peer comparison, and CLI dashboard
command using TestClient.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from do_uw.dashboard.app import create_app
from do_uw.dashboard.design import (
    risk_level_to_css_class,
    tier_to_css_class,
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

runner = CliRunner()


def _write_test_state(tmp_path: Path) -> Path:
    """Create a minimal AnalysisState JSON file for testing."""
    state = AnalysisState(ticker="TEST")
    state_path = tmp_path / "TEST" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    return state_path


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


def _write_rich_state(tmp_path: Path) -> Path:
    """Write a rich state file for drill-down tests."""
    state = _make_rich_state()
    state_path = tmp_path / "RICH" / "state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )
    return state_path


def _create_test_client(tmp_path: Path) -> TestClient:
    """Create a TestClient with a minimal test state."""
    state_path = _write_test_state(tmp_path)
    app = create_app(state_path)
    return TestClient(app)


def _create_rich_client(tmp_path: Path) -> TestClient:
    """Create a TestClient with a rich test state."""
    state_path = _write_rich_state(tmp_path)
    app = create_app(state_path)
    return TestClient(app)


# ---- Dashboard index tests ----


def test_dashboard_index_returns_200(tmp_path: Path) -> None:
    """GET / returns 200 with dashboard content."""
    client = _create_test_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert "Angry Dolphin" in response.text


def test_dashboard_index_shows_ticker(tmp_path: Path) -> None:
    """GET / includes the ticker symbol in the response."""
    client = _create_test_client(tmp_path)
    response = client.get("/")
    assert "TEST" in response.text


def test_dashboard_index_shows_section_cards(tmp_path: Path) -> None:
    """GET / includes all 7 analytical section cards."""
    client = _create_test_client(tmp_path)
    response = client.get("/")
    text = response.text
    assert "Company Profile" in text
    assert "Financial Health" in text
    assert "Market" in text
    assert "Governance" in text
    assert "Litigation" in text
    assert "Risk Scoring" in text
    assert "AI Transformation Risk" in text


def test_dashboard_index_has_meeting_prep_card(
    tmp_path: Path,
) -> None:
    """GET / includes a Meeting Prep card."""
    client = _create_test_client(tmp_path)
    response = client.get("/")
    assert "Meeting Prep" in response.text


def test_dashboard_index_has_peer_comparison(
    tmp_path: Path,
) -> None:
    """GET / includes peer comparison section."""
    client = _create_test_client(tmp_path)
    response = client.get("/")
    assert "Peer Comparison" in response.text


# ---- Static file tests ----


def test_static_css_served(tmp_path: Path) -> None:
    """GET /static/css/dashboard.css returns 200."""
    client = _create_test_client(tmp_path)
    response = client.get("/static/css/dashboard.css")
    assert response.status_code == 200
    assert "text/css" in response.headers.get("content-type", "")


def test_static_js_served(tmp_path: Path) -> None:
    """GET /static/js/dashboard.js returns 200."""
    client = _create_test_client(tmp_path)
    response = client.get("/static/js/dashboard.js")
    assert response.status_code == 200
    assert "javascript" in response.headers.get("content-type", "")


def test_css_has_finding_styles(tmp_path: Path) -> None:
    """CSS includes finding-negative and finding-positive styles."""
    client = _create_test_client(tmp_path)
    response = client.get("/static/css/dashboard.css")
    assert ".finding-negative" in response.text
    assert ".finding-positive" in response.text


def test_css_has_print_styles(tmp_path: Path) -> None:
    """CSS includes print media query."""
    client = _create_test_client(tmp_path)
    response = client.get("/static/css/dashboard.css")
    assert "@media print" in response.text


# ---- Section drill-down tests ----


def test_section_drill_down_financials(tmp_path: Path) -> None:
    """GET /section/financials returns 200 with content."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/financials")
    assert response.status_code == 200
    assert "Financial Health" in response.text


def test_section_drill_down_scoring(tmp_path: Path) -> None:
    """GET /section/scoring returns 200 with factor content."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/scoring")
    assert response.status_code == 200
    assert "Risk Scoring" in response.text


def test_section_drill_down_governance(tmp_path: Path) -> None:
    """GET /section/governance returns 200."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/governance")
    assert response.status_code == 200
    assert "Governance" in response.text


def test_section_drill_down_litigation(tmp_path: Path) -> None:
    """GET /section/litigation returns 200."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/litigation")
    assert response.status_code == 200
    assert "Litigation" in response.text


def test_section_drill_down_market(tmp_path: Path) -> None:
    """GET /section/market returns 200."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/market")
    assert response.status_code == 200


def test_section_drill_down_company(tmp_path: Path) -> None:
    """GET /section/company returns 200."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/company")
    assert response.status_code == 200
    assert "Company Profile" in response.text


def test_section_drill_down_unknown(tmp_path: Path) -> None:
    """GET /section/nonexistent returns 200 with no findings."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/nonexistent")
    assert response.status_code == 200
    assert "No findings" in response.text


# ---- Finding detail tests ----


def test_finding_detail(tmp_path: Path) -> None:
    """GET /section/scoring/finding/0 returns 200 with detail."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/scoring/finding/0")
    assert response.status_code == 200


def test_finding_detail_out_of_range(tmp_path: Path) -> None:
    """GET /section/scoring/finding/999 returns 200 with not found."""
    client = _create_rich_client(tmp_path)
    response = client.get("/section/scoring/finding/999")
    assert response.status_code == 200
    assert "Not Found" in response.text


# ---- Meeting prep tests ----


def test_meeting_prep_all(tmp_path: Path) -> None:
    """GET /meeting-prep returns 200 with questions panel."""
    client = _create_rich_client(tmp_path)
    response = client.get("/meeting-prep")
    assert response.status_code == 200
    assert "Meeting Prep" in response.text


def test_meeting_prep_filtered(tmp_path: Path) -> None:
    """GET /meeting-prep?category=CLARIFICATION returns 200."""
    client = _create_rich_client(tmp_path)
    response = client.get("/meeting-prep?category=CLARIFICATION")
    assert response.status_code == 200
    assert "Meeting Prep" in response.text


def test_meeting_prep_invalid_category(tmp_path: Path) -> None:
    """GET /meeting-prep?category=INVALID returns 200 (empty)."""
    client = _create_rich_client(tmp_path)
    response = client.get("/meeting-prep?category=INVALID")
    assert response.status_code == 200


# ---- Peer comparison tests ----


def test_peer_comparison_endpoint(tmp_path: Path) -> None:
    """GET /api/peer-comparison returns 200."""
    client = _create_rich_client(tmp_path)
    response = client.get("/api/peer-comparison")
    assert response.status_code == 200
    assert "Peer Comparison" in response.text


def test_peer_comparison_with_metric(tmp_path: Path) -> None:
    """GET /api/peer-comparison?metric=market_cap returns 200."""
    client = _create_rich_client(tmp_path)
    response = client.get("/api/peer-comparison?metric=market_cap")
    assert response.status_code == 200


# ---- State reload test ----


def test_state_reload_on_mtime_change(tmp_path: Path) -> None:
    """Dashboard reloads state when file mtime changes."""
    state_path = _write_test_state(tmp_path)
    app = create_app(state_path)
    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == 200
    assert "TEST" in response.text

    raw = json.loads(state_path.read_text(encoding="utf-8"))
    raw["ticker"] = "RELOADED"
    state_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")

    response = client.get("/")
    assert response.status_code == 200
    assert "RELOADED" in response.text


# ---- Design module tests ----


def test_tier_to_css_class_win() -> None:
    """WIN tier maps to badge-info."""
    assert tier_to_css_class("WIN") == "badge-info"


def test_tier_to_css_class_walk() -> None:
    """WALK tier maps to badge-error."""
    assert tier_to_css_class("WALK") == "badge-error"


def test_tier_to_css_class_none() -> None:
    """None tier maps to badge-ghost."""
    assert tier_to_css_class(None) == "badge-ghost"


def test_risk_level_to_css_class_critical() -> None:
    """CRITICAL risk level maps to badge-error."""
    assert risk_level_to_css_class("CRITICAL") == "badge-error"


def test_risk_level_to_css_class_moderate() -> None:
    """MODERATE risk level maps to badge-info."""
    assert risk_level_to_css_class("MODERATE") == "badge-info"


# ---- Missing state path test ----


def test_create_app_missing_state(tmp_path: Path) -> None:
    """create_app raises when state file does not exist."""
    bad_path = tmp_path / "nonexistent" / "state.json"
    with pytest.raises((FileNotFoundError, ValueError)):
        create_app(bad_path)


# ---- CLI dashboard serve test ----


def test_cli_serve_missing_ticker(tmp_path: Path) -> None:
    """do-uw dashboard serve with missing state exits with code 1."""
    from do_uw.cli_dashboard import dashboard_app

    result = runner.invoke(
        dashboard_app,
        ["serve", "NOEXIST", "--output", str(tmp_path)],
    )
    assert result.exit_code != 0
    assert "Error" in result.output or "No analysis found" in result.output
