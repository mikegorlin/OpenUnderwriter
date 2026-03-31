"""Tests for Key Stats Overview — locks down consistent rendering.

Verifies the key_stats context builder produces correct data and
the template renders all required sections for different company types.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader


@pytest.fixture()
def jinja_env() -> Environment:
    """Jinja2 env with required filters."""
    env = Environment(
        loader=FileSystemLoader("src/do_uw/templates/html"),
        finalize=lambda x: "\u2014" if x is None else x,
    )
    env.filters["format_na"] = lambda v: str(v) if v else "N/A"
    env.filters["humanize_evidence"] = lambda v: v
    return env


def _base_key_stats(**overrides: Any) -> dict[str, Any]:
    """Build a complete key_stats context dict for testing."""
    ks: dict[str, Any] = {
        "available": True,
        "legal_name": "TEST CORP",
        "ticker": "TST",
        "exchange": "NYSE",
        "cik": "123456",
        "sic_code": "2851",
        "sic_description": "Paints & Coatings",
        "naics_code": "325510",
        "state_of_inc": "DE",
        "fy_end": "12-31",
        "is_fpi": False,
        "sector": "INDU",
        "industry": "Specialty Chemicals",
        "filer_category": "Large Accelerated Filer",
        "market_cap_fmt": "$10.0B",
        "revenue_fmt": "$5.0B",
        "employees_fmt": "15,000",
        "years_public": 30,
        "subsidiary_count": 80,
        "jurisdiction_count": 20,
        "high_reg_jurisdictions": 5,
        "size_tier": "Large",
        "maturity_label": "Legacy",
        "stock_price": 100.0,
        "high_52w": 120.0,
        "low_52w": 80.0,
        "pct_off_high": 17,
        "price_pct_in_range": 50,
        "chart_1y": "<svg>1y</svg>",
        "chart_5y": "<svg>5y</svg>",
        "chart_1y_label": "1-Year",
        "chart_5y_label": "5-Year",
        "is_recent_ipo": False,
        "ipo_months": 0,
        "scale_metrics": [
            {"label": "Market Cap", "value": "$10.0B", "tier": "Large", "pct": 70},
            {"label": "Revenue", "value": "$5.0B", "tier": "Large", "pct": 65},
            {"label": "Employees", "value": "15,000", "tier": "Large", "pct": 75},
            {"label": "Years Public", "value": "30", "tier": "Legacy", "pct": 80, "inverted": True},
        ],
        "revenue_model": "Hybrid \u2014 manufacturing + distribution",
        "comparison_sector": "Specialty Chemicals (ETF: XLB)",
        "competitors": ["SHW (Sherwin-Williams)", "PPG (PPG Industries)"],
        "geo_mix": "US 70% | International 30%",
        "geo_breakdown": [
            {"region": "United States", "pct": "70%"},
            {"region": "Europe", "pct": "20%", "revenue": "$1.0B"},
        ],
        "customer_list": [
            {"name": "Home Depot", "detail": "23% of Consumer segment"},
        ],
        "segment_list": [
            {"name": "CPG", "stage": "Growth", "growth": "4.9%"},
        ],
        "entity_type": "Operating",
        "analysis_date": "2026-03-17",
        "tier": "WIN",
        "quality_score": 91.3,
        "business_description": "Test Corp makes things.",
        "governing_insight": "Test Corp is a large-cap, legacy specialty chemicals company.",
        "litigation_summary": {
            "sca_status": "None on record",
            "derivative_status": "None confirmed",
            "derivative_note": "",
            "sec_enforcement": "None",
            "regulatory_items": [],
            "contingent_total": 0,
            "contingent_fmt": "\u2014",
        },
        "regulatory_oversight": [
            {"agency": "SEC", "scope": "Securities regulation", "active": False},
            {"agency": "EPA", "scope": "Environmental", "active": True},
        ],
    }
    ks.update(overrides)
    return ks


class TestKeyStatsTemplate:
    """Template renders all required sections."""

    def test_renders_company_header(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "TEST CORP" in html
        assert "(TST)" in html
        assert "NYSE" in html
        assert "WIN" in html
        assert "91.3" in html

    def test_renders_business_profile(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "Business Profile" in html
        assert "Test Corp makes things" in html
        assert "manufacturing + distribution" in html
        assert "Specialty Chemicals (ETF: XLB)" in html

    def test_renders_geographic_with_revenue(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "United States" in html
        assert "70%" in html
        assert "Europe" in html
        assert "$1.0B" in html

    def test_renders_competitors(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "SHW (Sherwin-Williams)" in html
        assert "PPG (PPG Industries)" in html
        assert "ks-competitor-tag" in html

    def test_renders_customers(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "Home Depot" in html
        assert "23% of Consumer segment" in html

    def test_renders_segments(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "CPG" in html
        assert "Growth" in html
        assert "4.9%" in html

    def test_renders_scale_sliders(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "Scale" in html and "Complexity" in html
        assert "$10.0B" in html
        assert "Large" in html
        assert "ks-spectrum-marker" in html

    def test_renders_identity(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "2851" in html
        assert "325510" in html
        assert "DE" in html
        assert "12-31" in html

    def test_renders_litigation_box(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "Litigation" in html and "Enforcement" in html
        assert "None on record" in html

    def test_renders_regulatory_with_active_badge(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=_base_key_stats())
        assert "Regulatory Oversight" in html
        assert "SEC" in html
        assert "EPA" in html
        assert "ACTIVE" in html

    def test_no_data_renders_gracefully(self, jinja_env: Environment) -> None:
        """Minimal context should not crash."""
        ks = _base_key_stats(
            competitors=[],
            customer_list=[],
            segment_list=[],
            geo_breakdown=[],
            business_description="",
            litigation_summary=None,
            regulatory_oversight=[],
        )
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats=ks)
        assert "TEST CORP" in html
        assert "key-stats" in html

    def test_not_available_renders_nothing(self, jinja_env: Environment) -> None:
        tmpl = jinja_env.get_template("sections/key_stats.html.j2")
        html = tmpl.render(key_stats={"available": False})
        assert "key-stats" not in html
