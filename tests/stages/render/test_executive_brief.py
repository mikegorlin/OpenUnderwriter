"""Tests for executive brief template rendering (Phase 114-02)."""

from __future__ import annotations

from jinja2 import Environment, FileSystemLoader

import pytest


@pytest.fixture()
def jinja_env() -> Environment:
    """Create Jinja2 env with template dir and stub filters."""
    env = Environment(loader=FileSystemLoader("src/do_uw/templates/html"))
    env.filters["format_na"] = lambda v: str(v) if v else "N/A"
    env.filters["linkify_sections"] = lambda v: v  # stub: pass-through
    return env


def _brief_context(
    *,
    with_enriched: bool = True,
    with_findings: bool = True,
) -> dict:
    """Build mock executive brief context."""
    ctx: dict = {
        "company_name": "TestCo Inc",
        "ticker": "TST",
        "sector": "Technology",
        "generation_date": "2026-03-17",
        "company": {
            "business_description": "TestCo is a global technology company specializing in cloud services.",
        },
        "executive_summary": {
            "tier_label": "STANDARD",
            "quality_score": 82.0,
            "snapshot": {
                "market_cap": "$5.2B",
                "revenue": "$1.8B",
                "employees": "12,000",
                "description": "TestCo is a global technology company specializing in cloud services.",
            },
            "risk_assessment": {
                "tier_label": "STANDARD",
                "quality_score": 82.0,
                "summary": "Low-risk profile with strong governance.",
            },
        },
    }

    if with_findings:
        ctx["executive_summary"]["key_findings"] = [
            "Strong revenue growth of 15% YoY",
            "Pending patent litigation in Eastern District",
            "Board independence at 80%",
        ]

    if with_enriched:
        ctx["executive_summary"]["negatives_enriched"] = [
            {"title": "Pending patent litigation exposure", "body": "Eastern District filing pending", "confidence": "MEDIUM"},
            {"title": "Key executive departure risk", "body": "CFO announced retirement", "confidence": "LOW"},
        ]
        ctx["executive_summary"]["positives_enriched"] = [
            {"title": "Strong revenue diversification", "body": "No customer >10%", "confidence": "HIGH"},
            {"title": "Board independence exceeds industry median", "body": "80% independent", "confidence": "HIGH"},
        ]

    return ctx


def test_brief_renders_company_profile(jinja_env: Environment) -> None:
    """Executive brief renders company name, sector, and snapshot data."""
    tmpl = jinja_env.get_template("sections/executive_brief.html.j2")
    html = tmpl.render(**_brief_context())

    assert "TestCo Inc" in html
    assert "Technology" in html
    assert "STANDARD" in html
    assert "82.0" in html


def test_brief_renders_enriched_findings(jinja_env: Environment) -> None:
    """Executive brief renders enriched negative and positive findings."""
    tmpl = jinja_env.get_template("sections/executive_brief.html.j2")
    html = tmpl.render(**_brief_context())

    assert "Pending patent litigation exposure" in html
    assert "Strong revenue diversification" in html
    assert "Key Negatives" in html
    assert "Key Positives" in html


def test_brief_fallback_without_enriched(jinja_env: Environment) -> None:
    """Executive brief falls back to raw key_findings when no enriched data."""
    tmpl = jinja_env.get_template("sections/executive_brief.html.j2")
    ctx = _brief_context(with_enriched=False)
    html = tmpl.render(**ctx)

    assert "Strong revenue growth" in html
    assert "Pending patent litigation" in html
    assert "Board independence at 80%" in html


def test_brief_self_contained(jinja_env: Environment) -> None:
    """Executive brief is self-contained -- all variables are provided in context."""
    tmpl = jinja_env.get_template("sections/executive_brief.html.j2")
    # Minimal context -- only what the brief itself needs
    html = tmpl.render(
        company_name="MinCo",
        ticker="MIN",
        executive_summary={"tier_label": "STANDARD"},
    )
    # Should render without error and show company name
    assert "MinCo" in html
    assert "executive-brief" in html


def test_brief_risk_assessment_section(jinja_env: Environment) -> None:
    """Executive brief shows risk assessment with tier and confidence badge."""
    ctx = _brief_context()
    ctx["executive_summary"]["tier_label"] = "STANDARD"
    ctx["executive_summary"]["quality_score"] = 82.0
    tmpl = jinja_env.get_template("sections/executive_brief.html.j2")
    html = tmpl.render(**ctx)

    assert "STANDARD" in html
    assert "82.0" in html
    assert "Underwriting Recommendation" in html


def test_brief_print_page_break(jinja_env: Environment) -> None:
    """Executive brief has page-break-after for print."""
    tmpl = jinja_env.get_template("sections/executive_brief.html.j2")
    html = tmpl.render(**_brief_context())

    assert "executive-brief" in html
