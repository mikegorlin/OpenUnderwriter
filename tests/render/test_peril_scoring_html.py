"""Integration tests for peril scoring in HTML rendering context.

Tests the data flow from extract_scoring() through to HTML template rendering,
including F/S role badge display and graceful degradation when data is absent.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import jinja2
import pytest


# -- Helpers --


def _make_factor(
    factor_id: str = "F1",
    name: str = "Prior Litigation History",
    points: float = 5.0,
    max_points: int = 15,
    evidence: list[str] | None = None,
) -> SimpleNamespace:
    """Create a mock factor score object."""
    return SimpleNamespace(
        factor_id=factor_id,
        factor_name=name,
        points_deducted=points,
        max_points=max_points,
        evidence=evidence or [],
        sub_components=None,
        rules_triggered=[],
        scoring_method="rule_based",
    )


def _make_scoring(
    factors: list[SimpleNamespace] | None = None,
) -> SimpleNamespace:
    """Create a minimal scoring object for extract_scoring()."""
    return SimpleNamespace(
        quality_score=75.0,
        composite_score=80.0,
        total_risk_points=20.0,
        factor_scores=factors or [
            _make_factor("F1", "Prior Litigation History", 5.0, 15),
            _make_factor("F2", "Stock Price Decline", 3.0, 15),
            _make_factor("F7", "Stock Volatility", 2.0, 10),
            _make_factor("F8", "Financial Distress", 8.0, 15),
            _make_factor("F9", "Governance Quality", 1.0, 10),
        ],
        red_flags=[],
        red_flag_summary=None,
        patterns_detected=[],
        tier=None,
        binding_ceiling_id=None,
        claim_probability=None,
        severity_scenarios=None,
        risk_type=None,
        allegation_mapping=None,
        tower_recommendation=None,
        calibration_notes=None,
    )


def _make_state(
    scoring: SimpleNamespace | None = None,
    signal_results: dict[str, Any] | None = None,
) -> SimpleNamespace:
    """Create a minimal state for testing."""
    analysis = None
    if signal_results is not None:
        analysis = SimpleNamespace(signal_results=signal_results)
    return SimpleNamespace(
        scoring=scoring,
        analysis=analysis,
    )


def _render_scoring_template(context: dict[str, Any]) -> str:
    """Render the scoring.html.j2 template with given context.

    Uses a simplified Jinja2 environment with stub macros.
    """
    template_dir = (
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "do_uw"
        / "templates"
        / "html"
    )
    if not template_dir.exists():
        pytest.skip("HTML templates directory not found")

    # Provide stub macros that the template expects
    stubs = """
{% macro density_indicator(level) %}<!-- density: {{ level }} -->{% endmacro %}
{% macro section_narrative(narr, ai_generated=false) %}{% endmacro %}
{% macro kv_table(items) %}{% for item in items %}<tr><td>{{ item.key }}</td><td>{{ item.value }}</td></tr>{% endfor %}{% endmacro %}
{% macro tier_badge(tier) %}<span class="tier-badge">{{ tier }}</span>{% endmacro %}
{% macro traffic_light(status, label) %}<span class="traffic-light {{ status }}">{{ label }}</span>{% endmacro %}
{% macro gap_notice(title, msg) %}<div class="gap">{{ title }}: {{ msg }}</div>{% endmacro %}
{% macro warning_box(concern, detail) %}<div class="warning">{{ concern }}</div>{% endmacro %}
{% macro evidence_chain(items) %}{% for item in items %}<p>{{ item }}</p>{% endfor %}{% endmacro %}
{% macro check_summary(checks) %}<div class="signals">{{ checks|length }} checks</div>{% endmacro %}
{% macro embed_chart(name, title, figure_num=0, full_width=false) %}<div class="chart">{{ title }}</div>{% endmacro %}
"""

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(template_dir)),
        autoescape=False,
        undefined=jinja2.Undefined,
    )
    env.filters["humanize"] = lambda v: str(v).replace("_", " ").title()
    env.filters["humanize_theory"] = lambda v: str(v).replace("_", " ").title()
    env.filters["humanize_evidence"] = lambda v: str(v)
    env.filters["format_na"] = lambda v: v if v else "N/A"
    env.filters["truncate"] = lambda v, length=50: v[:length] if isinstance(v, str) and len(v) > length else (v if isinstance(v, str) else str(v))
    env.filters["strip_jargon"] = lambda v: str(v) if v else ""

    # Compile template from string that includes stubs + actual template
    stubs_and_template = stubs + "\n{% include 'sections/scoring.html.j2' %}"
    template = env.from_string(stubs_and_template)

    # Build full context with defaults
    full_context: dict[str, Any] = {
        "scoring": context.get("scoring", {}),
        "densities": context.get("densities", {}),
        "narratives": context.get("narratives", None),
        "hazard_profile": context.get("hazard_profile", None),
        "forensic_composites": context.get("forensic_composites", None),
        "executive_risk": context.get("executive_risk", None),
        "temporal_signals": context.get("temporal_signals", None),
        "nlp_signals": context.get("nlp_signals", None),
        "peril_map": context.get("peril_map", None),
        "signal_results_by_section": context.get("signal_results_by_section", {}),
    }

    return template.render(**full_context)


# -- Test: peril_scoring in extract_scoring context --


class TestPerilScoringInExtractScoring:
    """Test that extract_scoring() includes peril_scoring data."""

    def test_peril_scoring_key_present_with_brain_data(self) -> None:
        """extract_scoring includes peril_scoring when brain data available."""
        mock_perils = [
            {"peril_id": "SECURITIES", "name": "Securities Class Action",
             "description": "SCA risk", "frequency": "HIGH",
             "severity": "HIGH", "typical_settlement_range": "$10M-$100M",
             "key_drivers": ["stock_drop"], "haz_codes": ["HAZ-SCA"]},
        ]
        mock_chains = [
            {"chain_id": "stock_drop_to_sca", "name": "Stock Drop to SCA",
             "peril_id": "SECURITIES", "description": "Stock drop triggers SCA",
             "trigger_signals": ["CHK.1"], "amplifier_signals": [],
             "mitigator_signals": [], "evidence_signals": [],
             "red_flags": [], "historical_filing_rate": 0.05,
             "median_severity_usd": 50_000_000},
        ]

        signal_results = {
            "CHK.1": {"status": "TRIGGERED", "threshold_level": "red",
                       "evidence": "Stock dropped"},
        }
        state = _make_state(
            scoring=_make_scoring(),
            signal_results=signal_results,
        )

        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            return_value=mock_perils,
        ), patch(
            "do_uw.brain.brain_unified_loader.load_causal_chains",
            return_value=mock_chains,
        ):
            from do_uw.stages.render.md_renderer_helpers_scoring import extract_scoring
            result = extract_scoring(state)  # type: ignore[arg-type]

        assert "peril_scoring" in result
        ps = result["peril_scoring"]
        assert "all_perils" in ps
        assert "perils" in ps
        assert ps["active_count"] == 1
        assert ps["perils"][0]["peril_id"] == "SECURITIES"

    def test_peril_scoring_empty_when_no_brain(self) -> None:
        """extract_scoring works without peril_scoring when brain unavailable."""
        state = _make_state(scoring=_make_scoring())

        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            side_effect=ImportError("No brain"),
        ):
            from do_uw.stages.render.md_renderer_helpers_scoring import extract_scoring
            result = extract_scoring(state)  # type: ignore[arg-type]

        # peril_scoring should not be in result (empty dict was returned)
        assert "peril_scoring" not in result
        # But other scoring data should be present
        assert "factors" in result
        assert result["quality_score"] == "75.0"


# -- Test: factor role annotation --


class TestFactorRoleAnnotation:
    """Test that factors get annotated with F/S role from risk_model.yaml."""

    def test_each_factor_has_role(self) -> None:
        """All factors should have a role key after extract_scoring."""
        state = _make_state(scoring=_make_scoring())

        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            side_effect=ImportError("No brain"),
        ):
            from do_uw.stages.render.md_renderer_helpers_scoring import extract_scoring
            result = extract_scoring(state)  # type: ignore[arg-type]

        valid_roles = {"FREQUENCY", "SEVERITY", "BOTH", ""}
        for factor in result["factors"]:
            assert "role" in factor, f"Factor {factor['id']} missing 'role' key"
            assert factor["role"] in valid_roles, (
                f"Factor {factor['id']} has invalid role '{factor['role']}'"
            )

    def test_specific_factor_roles(self) -> None:
        """Specific factors should have known roles from risk_model.yaml."""
        state = _make_state(scoring=_make_scoring())

        with patch(
            "do_uw.brain.brain_unified_loader.load_perils",
            side_effect=ImportError("No brain"),
        ):
            from do_uw.stages.render.md_renderer_helpers_scoring import extract_scoring
            result = extract_scoring(state)  # type: ignore[arg-type]

        factor_roles = {f["id"]: f["role"] for f in result["factors"]}
        assert factor_roles["F1"] == "FREQUENCY"
        assert factor_roles["F2"] == "BOTH"
        assert factor_roles["F7"] == "SEVERITY"
        assert factor_roles["F8"] == "BOTH"
        assert factor_roles["F9"] == "FREQUENCY"


# -- Test: template graceful degradation --


class TestTemplateGracefulDegradation:
    """Test template renders without crashing when data is absent."""

    def test_empty_peril_scoring_renders(self) -> None:
        """Template renders without error when peril_scoring is empty."""
        context = {
            "scoring": {
                "quality_score": "75",
                "composite_score": "80",
                "tier": "WRITE",
                "factors": [],
                "red_flags": [],
                "patterns": [],
                "peril_scoring": {},
            },
        }
        html = _render_scoring_template(context)
        assert "Scoring" in html and "Risk Assessment" in html
        # Peril assessment should NOT appear
        assert "D&O Claim Peril Assessment" not in html

    def test_no_scoring_at_all_renders(self) -> None:
        """Template renders without error when scoring is empty."""
        context = {"scoring": {}}
        html = _render_scoring_template(context)
        assert "Scoring" in html and "Risk Assessment" in html

    def test_peril_scoring_with_data_renders(self) -> None:
        """Template renders peril assessment when data is present."""
        context = {
            "scoring": {
                "quality_score": "75",
                "composite_score": "80",
                "tier": "WRITE",
                "factors": [],
                "red_flags": [],
                "patterns": [],
                "peril_scoring": {
                    "active_count": 1,
                    "highest_peril": "SECURITIES",
                    "all_perils": [
                        {
                            "peril_id": "SECURITIES",
                            "name": "Securities Class Action",
                            "risk_level": "HIGH",
                            "active_chain_count": 2,
                            "total_chain_count": 5,
                            "key_evidence": ["Stock dropped 15%"],
                            "chains": [],
                            "frequency": "HIGH",
                            "severity": "HIGH",
                            "typical_settlement_range": "$10M-$100M",
                        },
                    ],
                    "perils": [
                        {
                            "peril_id": "SECURITIES",
                            "name": "Securities Class Action",
                            "risk_level": "HIGH",
                            "active_chain_count": 2,
                            "total_chain_count": 5,
                            "frequency": "HIGH",
                            "severity": "HIGH",
                            "typical_settlement_range": "$10M-$100M",
                            "chains": [
                                {
                                    "chain_id": "chain1",
                                    "name": "Stock Drop Chain",
                                    "active": True,
                                    "risk_level": "HIGH",
                                    "triggered_triggers": ["CHK.1"],
                                    "active_amplifiers": [],
                                    "active_mitigators": [],
                                },
                            ],
                        },
                    ],
                },
            },
        }
        html = _render_scoring_template(context)
        assert "D&O Claim Peril Assessment" in html
        assert "Securities Class Action" in html
        assert "1 of 1" in html


# -- Test: F/S role badge rendering in template --


class TestFactorRoleBadgeInTemplate:
    """Test that F/S role badges appear in rendered HTML."""

    def test_role_badges_rendered(self) -> None:
        """Factors with roles should show role badges in HTML output."""
        context = {
            "scoring": {
                "quality_score": "75",
                "composite_score": "80",
                "tier": "WRITE",
                "factors": [
                    {
                        "id": "F1",
                        "name": "Prior Litigation",
                        "score": "5.0",
                        "max": "15",
                        "pct": 33,
                        "risk_level": "INFO",
                        "weight": "15",
                        "pct_used": "33%",
                        "top_evidence": "",
                        "all_evidence": [],
                        "sub_components": [],
                        "rules_triggered": [],
                        "role": "FREQUENCY",
                    },
                    {
                        "id": "F2",
                        "name": "Stock Decline",
                        "score": "8.0",
                        "max": "15",
                        "pct": 53,
                        "risk_level": "ELEVATED",
                        "weight": "15",
                        "pct_used": "53%",
                        "top_evidence": "",
                        "all_evidence": [],
                        "sub_components": [],
                        "rules_triggered": [],
                        "role": "BOTH",
                    },
                    {
                        "id": "F7",
                        "name": "Volatility",
                        "score": "3.0",
                        "max": "10",
                        "pct": 30,
                        "risk_level": "INFO",
                        "weight": "10",
                        "pct_used": "30%",
                        "top_evidence": "",
                        "all_evidence": [],
                        "sub_components": [],
                        "rules_triggered": [],
                        "role": "SEVERITY",
                    },
                ],
                "red_flags": [],
                "patterns": [],
            },
        }
        html = _render_scoring_template(context)

        # Check FREQUENCY badge (F)
        assert "bg-blue-100 text-blue-700" in html
        assert ">F</span>" in html

        # Check BOTH badge (F+S)
        assert "bg-purple-100 text-purple-700" in html
        assert ">F+S</span>" in html

        # Check SEVERITY badge (S)
        assert "bg-orange-100 text-orange-700" in html
        assert ">S</span>" in html

    def test_no_role_badge_when_empty(self) -> None:
        """Factors without role should NOT show badge in factor name cell."""
        context = {
            "scoring": {
                "quality_score": "75",
                "composite_score": "80",
                "tier": "WRITE",
                "factors": [
                    {
                        "id": "F1",
                        "name": "Prior Litigation",
                        "score": "5.0",
                        "max": "15",
                        "pct": 33,
                        "risk_level": "INFO",
                        "weight": "15",
                        "pct_used": "33%",
                        "top_evidence": "",
                        "all_evidence": [],
                        "sub_components": [],
                        "rules_triggered": [],
                        "role": "",
                    },
                ],
                "red_flags": [],
                "patterns": [],
            },
        }
        html = _render_scoring_template(context)

        # The factor row containing "Prior Litigation" should NOT have >F</span>
        # or >S</span> or >F+S</span> badges (footnote will have them, that's OK)
        # Find the factor name cell line and check no badge class follows it
        import re
        factor_cells = re.findall(
            r"Prior Litigation.*?</td>", html, re.DOTALL,
        )
        assert len(factor_cells) > 0, "Factor name cell not found"
        # The cell should contain just the name, no badge span
        assert ">F</span>" not in factor_cells[0]
        assert ">S</span>" not in factor_cells[0]
        assert ">F+S</span>" not in factor_cells[0]

    def test_role_footnote_present(self) -> None:
        """The factor role footnote should appear in the scoring section."""
        context = {
            "scoring": {
                "quality_score": "75",
                "composite_score": "80",
                "tier": "WRITE",
                "factors": [
                    {
                        "id": "F1",
                        "name": "Prior Litigation",
                        "score": "5.0",
                        "max": "15",
                        "pct": 33,
                        "risk_level": "INFO",
                        "weight": "15",
                        "pct_used": "33%",
                        "top_evidence": "",
                        "all_evidence": [],
                        "sub_components": [],
                        "rules_triggered": [],
                        "role": "FREQUENCY",
                    },
                ],
                "red_flags": [],
                "patterns": [],
            },
        }
        html = _render_scoring_template(context)

        # Footnote should explain the badges
        assert "Factor roles:" in html
        assert "Frequency (drives claim filing probability)" in html
        assert "Severity (drives loss amount)" in html
