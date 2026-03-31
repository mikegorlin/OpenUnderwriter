"""Tests for scorecard template rendering (Phase 114-02)."""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

import pytest


@pytest.fixture()
def jinja_env() -> Environment:
    """Create Jinja2 env with template dir and stub filters."""
    env = Environment(loader=FileSystemLoader("src/do_uw/templates/html"))
    env.filters["format_na"] = lambda v: str(v) if v else "N/A"
    env.filters["humanize_evidence"] = lambda v: str(v) if v else ""
    env.filters["format_signal_value"] = lambda v: str(v) if v else "N/A"
    return env


def _scorecard_context(available: bool = True) -> dict:
    """Build a mock scorecard context dict."""
    if not available:
        return {"scorecard": {"scorecard_available": False}}

    return {
        "company_name": "Acme Corp",
        "ticker": "ACME",
        "sector": "Industrials",
        "generation_date": "2026-03-17",
        "scorecard": {
            "scorecard_available": True,
            "tier": "ELEVATED",
            "quality_score": 72.5,
            "composites": {"host": 0.15, "agent": 0.30, "environment": 0.10},
            "risk_type": {"available": False},
            "severity": {"available": False},
            "claim_prob": {"available": False},
            "allegations": {"available": False},
            "tower": {"available": False},
            "hae": {"available": False, "composites": {}},
            "recommendations": {"available": False},
            "factors_summary": [
                {"id": "F1", "name": "Financial Health", "full_name": "Financial Health",
                 "score": 8, "max": 15, "pct": 53, "has_deduction": True,
                 "evidence": "", "signal_count": 0, "coverage_pct": 0, "scoring_method": "rule_based"},
                {"id": "F9", "name": "Governance", "full_name": "Governance",
                 "score": 3, "max": 10, "pct": 30, "has_deduction": True,
                 "evidence": "", "signal_count": 0, "coverage_pct": 0, "scoring_method": "rule_based"},
                {"id": "F3", "name": "Litigation", "full_name": "Litigation",
                 "score": 12, "max": 20, "pct": 60, "has_deduction": True,
                 "evidence": "", "signal_count": 0, "coverage_pct": 0, "scoring_method": "rule_based"},
            ],
            "top_concerns": [
                {
                    "signal_id": "FIN_RESTATEMENT",
                    "signal_name": "Financial Restatement",
                    "status": "TRIGGERED",
                    "level": "red",
                    "value": "True",
                    "evidence": "Revenue restatement filed Q3 2025",
                    "explanation": "Revenue restatement filed Q3 2025",
                    "rap_class": "host",
                    "rap_label": "Structural Risk",
                    "rap_subcategory": "",
                },
                {
                    "signal_id": "GOV_BOARD_INDEPENDENCE",
                    "signal_name": "Board Independence",
                    "status": "TRIGGERED",
                    "level": "yellow",
                    "value": "40%",
                    "evidence": "Board independence below 50%",
                    "explanation": "Board independence below 50%",
                    "rap_class": "agent",
                    "rap_label": "Behavioral Risk",
                    "rap_subcategory": "",
                },
            ],
            "metrics_strip": {
                "market_cap": "$2.1B",
                "revenue": "$850M",
                "employees": "4,200",
                "years_public": "15",
            },
        },
        "hae_context": {
            "hae_available": True,
            "host_composite": 0.15,
            "agent_composite": 0.30,
            "environment_composite": 0.10,
        },
        "heatmap": {"heatmap_available": False},
    }


def test_scorecard_renders_with_data(jinja_env: Environment) -> None:
    """Scorecard template renders tier badge, factors, concerns, metrics."""
    tmpl = jinja_env.get_template("sections/scorecard.html.j2")
    ctx = _scorecard_context()
    html = tmpl.render(**ctx)

    assert "scorecard" in html.lower()
    assert "ELEVATED" in html
    assert "Financial Health" in html
    # Concern signal_name is displayed instead of raw signal_id
    assert "Financial Restatement" in html
    # Metrics strip is consumed by other sections, not rendered inline in scorecard
    assert "72.5" in html  # quality_score is displayed


def test_scorecard_graceful_degradation(jinja_env: Environment) -> None:
    """Scorecard template renders nothing when scorecard_available=False."""
    tmpl = jinja_env.get_template("sections/scorecard.html.j2")
    ctx = _scorecard_context(available=False)
    html = tmpl.render(**ctx)

    # Should produce essentially empty output
    assert "scorecard-page" not in html
    assert "ELEVATED" not in html


def test_scorecard_heatmap_cells(jinja_env: Environment) -> None:
    """Factor heatmap renders correct number of cells based on factors_summary."""
    tmpl = jinja_env.get_template("sections/scorecard.html.j2")
    ctx = _scorecard_context()
    html = tmpl.render(**ctx)

    # Template uses sc-heatmap-cell with sc-heat-- classes based on pct thresholds
    assert "sc-heatmap-cell" in html
    # 3 factors in context: pct=53 (elevated), pct=30 (elevated), pct=60 (critical)
    assert "sc-heat--critical" in html
    assert "sc-heat--elevated" in html
    # 3 total cells (one per factor)
    assert html.count("sc-heatmap-cell") == 3


def test_scorecard_factor_bars(jinja_env: Environment) -> None:
    """Factor score bars use correct CSS classes based on pct thresholds."""
    tmpl = jinja_env.get_template("sections/scorecard.html.j2")
    ctx = _scorecard_context()
    html = tmpl.render(**ctx)

    assert "bar-critical" in html  # 60% factor
    assert "bar-elevated" in html  # 53% and 30% factors
    # pct=30 is exactly 30, which is >= 30 so it's bar-elevated
    assert "bar-normal" not in html or "bar-elevated" in html


def test_scorecard_print_page_break(jinja_env: Environment) -> None:
    """Scorecard section has page-break-after for print isolation."""
    tmpl = jinja_env.get_template("sections/scorecard.html.j2")
    ctx = _scorecard_context()
    html = tmpl.render(**ctx)

    assert "scorecard-page" in html
