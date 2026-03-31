"""Tests for decision record page template (Phase 114-03).

Renders decision_record.html.j2 with mock context and verifies
structural correctness: tier distribution, posture options,
no system recommendation, graceful degradation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader

TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html"


def _env() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )


def _make_decision_context(
    *,
    current_tier: str = "ELEVATED",
    decision_available: bool = True,
) -> dict:
    return {
        "decision": {
            "decision_available": decision_available,
            "current_tier": current_tier,
            "tier_distribution": {
                "PREFERRED": 15.0,
                "STANDARD": 40.0,
                "ELEVATED": 25.0,
                "HIGH_RISK": 15.0,
                "PROHIBITED": 5.0,
            },
            "posture_fields": {},
            "source": "Industry Reference",
        },
        "company_name": "Acme Corp",
        "ticker": "ACME",
    }


class TestDecisionRecordTemplate:
    def test_renders_with_decision_context(self) -> None:
        """Template renders with full decision context."""
        ctx = _make_decision_context(current_tier="ELEVATED")
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render(**ctx)

        assert 'id="decision-record"' in html
        assert "Underwriting Decision Record" in html
        assert "Acme Corp" in html
        assert "ACME" in html

    def test_tier_distribution_shows_all_five_tiers(self) -> None:
        """All 5 tier segments render with percentage labels."""
        ctx = _make_decision_context()
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render(**ctx)

        assert "Preferred" in html
        assert "Standard" in html
        assert "Elevated" in html
        assert "High Risk" in html
        assert "Prohibited" in html
        # Check percentage values are present
        assert "15%" in html
        assert "40%" in html
        assert "25%" in html
        assert "5%" in html

    def test_current_tier_highlighted(self) -> None:
        """Current tier gets the tier-highlight CSS class."""
        ctx = _make_decision_context(current_tier="ELEVATED")
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render(**ctx)

        assert "tier-highlight" in html
        # The ELEVATED segment should have the highlight class
        assert 'tier-segment--elevated tier-highlight' in html

    def test_posture_options_present(self) -> None:
        """All four posture options (BIND/DECLINE/REFER/TERMS) are present."""
        ctx = _make_decision_context()
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render(**ctx)

        assert "Bind" in html
        assert "Decline" in html
        assert "Refer" in html
        assert "Terms" in html

    def test_no_system_recommendation(self) -> None:
        """Template explicitly states no system recommendation."""
        ctx = _make_decision_context()
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render(**ctx)

        assert "No system recommendation provided" in html
        assert "independent assessment" in html

    def test_graceful_degradation(self) -> None:
        """Template renders gracefully when decision_available=False."""
        ctx = {"decision": {"decision_available": False}}
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render(**ctx)

        assert 'id="decision-record"' in html
        assert "Scoring data unavailable" in html
        # Should NOT have posture grid
        assert "posture-grid" not in html

    def test_industry_reference_label(self) -> None:
        """Template labels tier distribution as 'Industry Reference', not 'Recommendation'."""
        ctx = _make_decision_context()
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render(**ctx)

        assert "Industry Reference" in html
        # The tier distribution heading should say "Industry Reference", not "Recommendation"
        assert "D&amp;O Tier Distribution" in html
        # There should be no "Recommended" or "Recommendation" as a heading/label
        # near the tier bar. "No system recommendation" is fine as an explicit disclaimer.
        assert "Recommended Tier" not in html
        assert "System Recommendation:" not in html

    def test_no_context_key_graceful(self) -> None:
        """Template renders safely when decision key is missing entirely."""
        env = _env()
        html = env.get_template("sections/decision_record.html.j2").render()

        assert 'id="decision-record"' in html
        assert "Scoring data unavailable" in html
