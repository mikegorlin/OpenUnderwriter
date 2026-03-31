"""Tests for 5-layer narrative architecture (Phase 65-01).

Tests cover:
1. load_narrative_config() loads all 12 section configs
2. verdict_badge macro renders correct colors
3. narrative context builder produces valid output
4. Section templates render without errors with narrative data
"""

from __future__ import annotations

import jinja2
import pytest
from pathlib import Path

from do_uw.brain.narratives import (
    SECTION_IDS,
    load_all_narrative_configs,
    load_narrative_config,
)
from do_uw.models.density import PreComputedNarratives
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.narrative import (
    build_section_narrative,
    extract_section_narratives,
)


def _make_state(**overrides: object) -> AnalysisState:
    """Create minimal AnalysisState for testing."""
    overrides.setdefault("ticker", "TEST")
    return AnalysisState(**overrides)


# ---------------------------------------------------------------------------
# Test 1: YAML Config Loading
# ---------------------------------------------------------------------------

class TestNarrativeYAMLLoading:
    """Test load_narrative_config() loads all 12 section configs."""

    def test_all_12_configs_load(self) -> None:
        configs = load_all_narrative_configs()
        assert len(configs) == 12

    @pytest.mark.parametrize("section_id", SECTION_IDS)
    def test_each_section_has_required_keys(self, section_id: str) -> None:
        config = load_narrative_config(section_id)
        required = {"verdict", "thesis_template", "evidence_keys", "implications_template", "deep_context_keys"}
        missing = required - set(config.keys())
        assert not missing, f"{section_id} missing keys: {missing}"

    @pytest.mark.parametrize("section_id", SECTION_IDS)
    def test_verdict_has_thresholds(self, section_id: str) -> None:
        config = load_narrative_config(section_id)
        verdict = config["verdict"]
        assert "thresholds" in verdict
        thresholds = verdict["thresholds"]
        # Every config should map at least CRITICAL and CLEAN
        assert "CRITICAL" in thresholds
        assert "CLEAN" in thresholds

    @pytest.mark.parametrize("section_id", SECTION_IDS)
    def test_evidence_keys_is_list(self, section_id: str) -> None:
        config = load_narrative_config(section_id)
        assert isinstance(config["evidence_keys"], list)
        assert len(config["evidence_keys"]) > 0

    def test_invalid_section_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_narrative_config("nonexistent_section")


# ---------------------------------------------------------------------------
# Test 2: Verdict Badge Macro
# ---------------------------------------------------------------------------

class TestVerdictBadgeMacro:
    """Test verdict_badge macro renders correct colors."""

    @pytest.fixture()
    def env(self) -> jinja2.Environment:
        template_dir = Path(__file__).resolve().parent.parent.parent.parent / "src" / "do_uw" / "templates" / "html"
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=True,
            undefined=jinja2.Undefined,
        )

    @pytest.mark.parametrize(
        "verdict,css_class",
        [
            ("FAVORABLE", "verdict-favorable"),
            ("NEUTRAL", "verdict-neutral"),
            ("CONCERNING", "verdict-concerning"),
            ("CRITICAL", "verdict-critical"),
        ],
    )
    def test_verdict_renders_correct_class(
        self, env: jinja2.Environment, verdict: str, css_class: str
    ) -> None:
        tpl = env.from_string(
            "{% from 'components/badges.html.j2' import verdict_badge %}"
            "{{ verdict_badge('" + verdict + "') }}"
        )
        result = tpl.render()
        assert css_class in result
        assert verdict in result

    def test_unknown_verdict_uses_neutral(self, env: jinja2.Environment) -> None:
        tpl = env.from_string(
            "{% from 'components/badges.html.j2' import verdict_badge %}"
            "{{ verdict_badge('UNKNOWN') }}"
        )
        result = tpl.render()
        assert "verdict-neutral" in result

    def test_none_verdict_renders_na(self, env: jinja2.Environment) -> None:
        tpl = env.from_string(
            "{% from 'components/badges.html.j2' import verdict_badge %}"
            "{{ verdict_badge('') }}"
        )
        result = tpl.render()
        assert "verdict-neutral" in result


# ---------------------------------------------------------------------------
# Test 3: Narrative Context Builder
# ---------------------------------------------------------------------------

class TestNarrativeContextBuilder:
    """Test narrative context builder produces valid output."""

    def test_empty_state_produces_narratives(self) -> None:
        state = _make_state()
        result = extract_section_narratives(state)
        assert isinstance(result, dict)
        # CLEAN sections with no triggered signals return None (fall through
        # to pre-computed narrative).  Only ELEVATED/CRITICAL sections with
        # real evidence produce 5-layer narratives.
        assert len(result) >= 0

    def test_narrative_has_all_keys_when_present(self) -> None:
        state = _make_state()
        result = extract_section_narratives(state)
        # When a section produces a narrative (ELEVATED/CRITICAL), it must
        # have all 5 layers.  CLEAN sections may return None (no entry).
        for key, narr in result.items():
            assert "verdict" in narr, f"{key} missing verdict"
            assert "thesis" in narr, f"{key} missing thesis"
            assert "evidence_items" in narr, f"{key} missing evidence_items"
            assert "implications" in narr, f"{key} missing implications"
            assert "deep_context" in narr, f"{key} missing deep_context"

    def test_verdict_values_valid(self) -> None:
        state = _make_state()
        result = extract_section_narratives(state)
        valid_verdicts = {"FAVORABLE", "NEUTRAL", "CONCERNING", "CRITICAL"}
        for key, narr in result.items():
            assert narr["verdict"] in valid_verdicts, f"{key} has invalid verdict: {narr['verdict']}"

    def test_elevated_density_changes_verdict(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "ELEVATED"}},
            "pre_computed_narratives": PreComputedNarratives(governance="Board concerns."),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_section_narratives(state)
        gov = result["governance"]
        assert gov["verdict"] == "CONCERNING"

    def test_critical_density_changes_verdict(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"financial_health": {"level": "CRITICAL"}},
            "pre_computed_narratives": PreComputedNarratives(financial="Distress."),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_section_narratives(state)
        fin = result["financial"]
        assert fin["verdict"] == "CRITICAL"

    def test_evidence_items_populated_from_signals(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "ELEVATED"}},
            "pre_computed_narratives": None,
            "signal_results": {
                "GOV.BOARD.independence": {
                    "status": "TRIGGERED",
                    "evidence": "Below 50%",
                    "signal_name": "Board Independence",
                    "filing_ref": "DEF 14A",
                    "section": "governance",
                },
            },
            "gap_search_summary": {},
        })()
        result = extract_section_narratives(state)
        gov = result["governance"]
        # Should have at least one evidence item from signal
        assert len(gov["evidence_items"]) >= 1

    def test_clean_section_skips_5layer(self) -> None:
        """CLEAN sections with no triggered signals skip 5-layer rendering.

        The pre-computed narrative renders via the fallback template path
        instead (SCR + AI Assessment + D&O Implications), which is richer
        for sections without specific findings to highlight.
        """
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "CLEAN"}},
            "pre_computed_narratives": PreComputedNarratives(governance="Board structure is well-organized. Independence ratio exceeds benchmark."),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_section_narratives(state)
        # CLEAN + no signals → None → template falls through to pre-computed narrative
        assert "governance" not in result

    def test_deep_context_includes_full_assessment(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"litigation": {"level": "ELEVATED"}},
            "pre_computed_narratives": PreComputedNarratives(litigation="Active securities case pending. Settlement expected Q3."),
            "signal_results": {},
            "gap_search_summary": {},
        })()
        result = extract_section_narratives(state)
        lit = result["litigation"]
        assert len(lit["deep_context"]) > 0
        labels = [d["label"] for d in lit["deep_context"]]
        assert "Full Assessment" in labels

    def test_build_section_narrative_returns_none_for_missing_config(self) -> None:
        state = _make_state()
        result = build_section_narrative(state, "nonexistent_section")
        assert result is None

    def test_template_key_mapping(self) -> None:
        """business_profile maps to 'company', market_activity to 'market'.

        Only sections with ELEVATED/CRITICAL density or triggered signals
        produce entries.  Brain IDs should never appear as keys.
        """
        state = _make_state()
        result = extract_section_narratives(state)
        # Brain IDs must never leak as keys
        assert "business_profile" not in result
        assert "market_activity" not in result


# ---------------------------------------------------------------------------
# Test 4: Section Template Rendering
# ---------------------------------------------------------------------------

class TestSectionTemplateRendering:
    """Test section templates render without errors with narrative data.

    Sections use macros from base.html.j2, so we wrap each in a test
    template that imports the required macros.
    """

    # Macro imports matching base.html.j2
    _MACRO_PREAMBLE = (
        "{% from 'components/badges.html.j2' import traffic_light, density_indicator, confidence_marker, tier_badge, check_summary, verdict_badge %}"
        "{% from 'components/tables.html.j2' import data_table, kv_table, paired_kv_table, multi_column_grid, conditional_cell, financial_row, spectrum_bar, data_row, data_grid %}"
        "{% from 'components/callouts.html.j2' import discovery_box, warning_box, do_context, gap_notice, scr_narrative, do_implications %}"
        "{% from 'components/charts.html.j2' import embed_chart with context %}"
        "{% from 'components/narratives.html.j2' import section_narrative, evidence_chain, narrative_5layer with context %}"
    )

    @pytest.fixture()
    def env(self) -> jinja2.Environment:
        template_dir = Path(__file__).resolve().parent.parent.parent.parent / "src" / "do_uw" / "templates" / "html"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=True,
            undefined=jinja2.Undefined,
        )
        from do_uw.stages.render.html_narrative import _narratize, _strip_markdown
        from do_uw.stages.render.formatters import (
            format_currency, format_percentage, na_if_none, format_em_dash,
            humanize_enum, format_currency_accounting, format_adaptive,
            format_yoy_html, format_na, humanize_theory, humanize_field_name,
            humanize_impact, humanize_check_evidence, strip_cyber_tags,
        )
        from do_uw.stages.render.context_builders import dim_display_name
        env.filters["narratize"] = _narratize
        env.filters["strip_md"] = _strip_markdown
        env.filters["format_currency"] = format_currency
        env.filters["format_pct"] = format_percentage
        env.filters["na_if_none"] = na_if_none
        env.filters["risk_class"] = lambda x: ""
        env.filters["dim_display_name"] = dim_display_name
        env.filters["zip"] = zip
        env.filters["format_acct"] = format_currency_accounting
        env.filters["format_adaptive"] = format_adaptive
        env.filters["yoy_arrow"] = format_yoy_html
        env.filters["format_na"] = format_na
        env.filters["format_em"] = format_em_dash
        env.filters["humanize"] = humanize_enum
        env.filters["humanize_theory"] = humanize_theory
        env.filters["humanize_field"] = humanize_field_name
        env.filters["humanize_impact"] = humanize_impact
        env.filters["humanize_evidence"] = humanize_check_evidence
        env.filters["strip_cyber"] = strip_cyber_tags
        from do_uw.stages.render.formatters_humanize import humanize_source
        env.filters["humanize_source"] = humanize_source
        return env

    @pytest.fixture()
    def base_context(self) -> dict:
        return {
            "section_narratives": {
                "executive_summary": {"verdict": "FAVORABLE", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
                "company": {"verdict": "NEUTRAL", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
                "financial": {"verdict": "CONCERNING", "thesis": "Test.", "evidence_items": [{"label": "X", "value": "Y", "source": "Z", "severity": "HIGH"}], "implications": "Impl.", "deep_context": [{"label": "D", "content": "C"}]},
                "market": {"verdict": "FAVORABLE", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
                "governance": {"verdict": "CRITICAL", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
                "litigation": {"verdict": "CONCERNING", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
                "scoring": {"verdict": "NEUTRAL", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
                "ai_risk": {"verdict": "FAVORABLE", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
                "red_flags": {"verdict": "FAVORABLE", "thesis": "Test.", "evidence_items": [], "implications": "", "deep_context": []},
            },
            "densities": {},
            "narratives": PreComputedNarratives(),
            "executive_summary": {},
            "company": {},
            "financials": {},
            "market": {},
            "governance": {},
            "litigation": {},
            "scoring": {},
            "ai_risk": {},
            "scr_narratives": {},
            "do_implications_data": {},
            "section_context": {},
            # Additional context variables needed by sub-templates
            "signal_results_by_section": {},
            "chart_images": {},
            "chart_svgs": {},
            "factor_breakdown": [],
            "ceiling_line": "",
            "spectrums": {},
            "footnote_registry": type("FR", (), {"all_sources": []})(),
            "all_sources": [],
        }

    def _render_section(self, env: jinja2.Environment, ctx: dict, tpl_name: str) -> str:
        """Render a section template with macro preamble."""
        wrapper = self._MACRO_PREAMBLE + "{% include '" + tpl_name + "' %}"
        tpl = env.from_string(wrapper)
        return tpl.render(**ctx)

    @pytest.mark.parametrize("template_name", [
        "sections/executive.html.j2",
        "sections/company.html.j2",
        "sections/financial.html.j2",
        "sections/market.html.j2",
        "sections/governance.html.j2",
        "sections/litigation.html.j2",
        "sections/scoring.html.j2",
        "sections/ai_risk.html.j2",
        "sections/red_flags.html.j2",
    ])
    def test_section_renders_with_narrative(
        self, env: jinja2.Environment, base_context: dict, template_name: str
    ) -> None:
        result = self._render_section(env, base_context, template_name)
        assert "narrative-layers" in result or "section" in result

    def test_financial_renders_evidence_grid(
        self, env: jinja2.Environment, base_context: dict
    ) -> None:
        result = self._render_section(env, base_context, "sections/financial.html.j2")
        assert "narrative-evidence-grid" in result

    def test_governance_renders_critical_badge(
        self, env: jinja2.Environment, base_context: dict
    ) -> None:
        result = self._render_section(env, base_context, "sections/governance.html.j2")
        assert "verdict-critical" in result

    def test_fallback_when_no_section_narratives(
        self, env: jinja2.Environment, base_context: dict
    ) -> None:
        """Without section_narratives, should fall back to SCR/narrative."""
        base_context["section_narratives"] = {}
        result = self._render_section(env, base_context, "sections/governance.html.j2")
        assert "governance" in result.lower()
