"""Tests for bull/bear case extraction and confidence-calibrated language (Phase 65-02).

Tests cover:
1. CONFIDENCE_VERBS mapping and calibrate_verb()
2. calibrate_narrative_text() verb replacement
3. derive_section_confidence() tier determination
4. extract_bull_bear_cases() data extraction
5. bull_bear_framing Jinja2 macro rendering
"""

from __future__ import annotations

from pathlib import Path

import jinja2
import pytest

from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders._bull_bear import (
    CONFIDENCE_VERBS,
    calibrate_narrative_text,
    calibrate_verb,
    derive_section_confidence,
    extract_bull_bear_cases,
)


def _make_state(**overrides: object) -> AnalysisState:
    """Create minimal AnalysisState for testing."""
    overrides.setdefault("ticker", "TEST")
    return AnalysisState(**overrides)


# ---------------------------------------------------------------------------
# Test 1: Confidence Verb Mapping
# ---------------------------------------------------------------------------


class TestConfidenceVerbs:
    """Tests for calibrate_verb() and CONFIDENCE_VERBS mapping."""

    def test_confidence_verb_high(self) -> None:
        assert calibrate_verb("HIGH") == "confirms"

    def test_confidence_verb_medium(self) -> None:
        assert calibrate_verb("MEDIUM") == "indicates"

    def test_confidence_verb_low(self) -> None:
        assert calibrate_verb("LOW") == "suggests"

    def test_confidence_verb_inference(self) -> None:
        assert calibrate_verb("INFERENCE") == "pattern may indicate"

    def test_confidence_verb_unknown_defaults(self) -> None:
        assert calibrate_verb("UNKNOWN") == "suggests"

    def test_confidence_verb_case_insensitive(self) -> None:
        assert calibrate_verb("high") == "confirms"
        assert calibrate_verb("Medium") == "indicates"

    def test_calibrate_narrative_text_replaces_verb(self) -> None:
        text = "The report shows risk factors. Analysis has concerns."
        result = calibrate_narrative_text(text, "HIGH")
        assert "confirms" in result
        assert "shows" not in result

    def test_calibrate_narrative_text_empty(self) -> None:
        assert calibrate_narrative_text("", "HIGH") == ""

    def test_calibrate_narrative_text_no_matching_verb(self) -> None:
        text = "Risk factors were identified."
        result = calibrate_narrative_text(text, "HIGH")
        # No generic verb to replace, text unchanged
        assert result == text

    def test_confidence_verbs_dict_complete(self) -> None:
        assert set(CONFIDENCE_VERBS.keys()) == {"HIGH", "MEDIUM", "LOW", "INFERENCE"}


# ---------------------------------------------------------------------------
# Test 2: Derive Section Confidence
# ---------------------------------------------------------------------------


class TestDeriveConfidence:
    """Tests for derive_section_confidence()."""

    def test_no_signals_defaults_medium(self) -> None:
        state = _make_state()
        assert derive_section_confidence(state, "scoring") == "MEDIUM"

    def test_with_signal_results(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {},
            "pre_computed_narratives": None,
            "signal_results": {
                "SIG.001": {"section": "governance", "confidence": "HIGH", "status": "TRIGGERED"},
                "SIG.002": {"section": "governance", "confidence": "HIGH", "status": "CLEAR"},
                "SIG.003": {"section": "governance", "confidence": "LOW", "status": "TRIGGERED"},
            },
            "gap_search_summary": {},
        })()
        result = derive_section_confidence(state, "governance")
        assert result == "HIGH"  # 2 HIGH vs 1 LOW

    def test_filters_by_section(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {},
            "pre_computed_narratives": None,
            "signal_results": {
                "SIG.001": {"section": "governance", "confidence": "HIGH"},
                "SIG.002": {"section": "litigation", "confidence": "LOW"},
            },
            "gap_search_summary": {},
        })()
        # Only governance signal counts for governance
        assert derive_section_confidence(state, "governance") == "HIGH"
        # Only litigation signal counts for litigation
        assert derive_section_confidence(state, "litigation") == "LOW"


# ---------------------------------------------------------------------------
# Test 3: Bull/Bear Case Extraction
# ---------------------------------------------------------------------------


class TestBullBearExtraction:
    """Tests for extract_bull_bear_cases()."""

    def test_empty_state_returns_empty(self) -> None:
        state = _make_state()
        result = extract_bull_bear_cases(state)
        assert isinstance(result, dict)
        # Empty state has no key findings or peril data
        assert not result.get("executive_summary")

    def test_executive_bull_from_positives(self) -> None:
        from do_uw.models.executive_summary import (
            ExecutiveSummary,
            KeyFinding,
            KeyFindings,
        )

        kf = KeyFindings(positives=[
            KeyFinding(
                evidence_narrative="Strong governance structure",
                section_origin="Governance",
                scoring_impact="F3: -5 points",
                theory_mapping="Defense: Strong Board",
            ),
        ])
        es = ExecutiveSummary(key_findings=kf)
        state = _make_state()
        state.executive_summary = es

        result = extract_bull_bear_cases(state)
        assert "executive_summary" in result
        bull = result["executive_summary"]["bull_case"]
        assert bull is not None
        assert len(bull["entries"]) == 1
        assert bull["entries"][0]["text"] == "Strong governance structure"

    def test_executive_bear_from_negatives(self) -> None:
        from do_uw.models.executive_summary import (
            ExecutiveSummary,
            KeyFinding,
            KeyFindings,
        )

        kf = KeyFindings(negatives=[
            KeyFinding(
                evidence_narrative="Accounting restatement risk",
                section_origin="Financial",
                scoring_impact="F1: +20 points critical",
                theory_mapping="Theory A: Disclosure",
            ),
        ])
        es = ExecutiveSummary(key_findings=kf)
        state = _make_state()
        state.executive_summary = es

        result = extract_bull_bear_cases(state)
        assert "executive_summary" in result
        bear = result["executive_summary"]["bear_case"]
        assert bear is not None
        assert len(bear["entries"]) == 1
        assert bear["entries"][0]["severity"] == "HIGH"  # "critical" in scoring_impact

    def test_scoring_bear_from_peril(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {"governance": {"level": "CRITICAL"}},
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
            "peril_map": {
                "bear_cases": [
                    {
                        "theory": "A_DISCLOSURE",
                        "plaintiff_type": "SHAREHOLDERS",
                        "committee_summary": "Securities fraud risk from financial restatement",
                        "severity_estimate": "SIGNIFICANT",
                    },
                ],
            },
        })()

        result = extract_bull_bear_cases(state)
        assert "scoring" in result
        bear = result["scoring"]["bear_case"]
        assert bear is not None
        # Should have both density-derived and peril-derived items
        assert len(bear["entries"]) >= 1

    def test_items_capped_at_5(self) -> None:
        from do_uw.models.executive_summary import (
            ExecutiveSummary,
            KeyFinding,
            KeyFindings,
        )

        findings = [
            KeyFinding(
                evidence_narrative=f"Finding {i}",
                section_origin="Test",
                scoring_impact="F1: +5",
                theory_mapping="Theory A",
            )
            for i in range(10)
        ]
        kf = KeyFindings(negatives=findings)
        es = ExecutiveSummary(key_findings=kf)
        state = _make_state()
        state.executive_summary = es

        result = extract_bull_bear_cases(state)
        bear = result["executive_summary"]["bear_case"]
        assert len(bear["entries"]) <= 5

    def test_confidence_tier_included(self) -> None:
        from do_uw.models.executive_summary import (
            ExecutiveSummary,
            KeyFinding,
            KeyFindings,
        )

        kf = KeyFindings(positives=[
            KeyFinding(
                evidence_narrative="Test",
                section_origin="Test",
                scoring_impact="F1: -5",
                theory_mapping="None",
            ),
        ])
        es = ExecutiveSummary(key_findings=kf)
        state = _make_state()
        state.executive_summary = es

        result = extract_bull_bear_cases(state)
        assert "confidence_tier" in result["executive_summary"]

    def test_scoring_bull_from_clean_sections(self) -> None:
        state = _make_state()
        state.analysis = type("Analysis", (), {
            "section_densities": {
                "governance": {"level": "CLEAN"},
                "financial_health": {"level": "CLEAN"},
            },
            "pre_computed_narratives": None,
            "signal_results": {},
            "gap_search_summary": {},
            "peril_map": None,
        })()

        result = extract_bull_bear_cases(state)
        assert "scoring" in result
        bull = result["scoring"]["bull_case"]
        assert bull is not None
        assert len(bull["entries"]) >= 1


# ---------------------------------------------------------------------------
# Test 4: Bull/Bear Template Macro
# ---------------------------------------------------------------------------


class TestBullBearTemplate:
    """Tests for bull_bear_framing Jinja2 macro."""

    @pytest.fixture()
    def env(self) -> jinja2.Environment:
        from do_uw.stages.render.formatters_humanize import humanize_source

        template_dir = Path(__file__).resolve().parent.parent.parent.parent / "src" / "do_uw" / "templates" / "html"
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_dir)),
            autoescape=True,
            undefined=jinja2.Undefined,
        )
        env.filters["humanize_source"] = humanize_source
        return env

    def test_macro_renders_bull_bear_grid(self, env: jinja2.Environment) -> None:
        tpl = env.from_string(
            "{% from 'components/narratives.html.j2' import bull_bear_framing %}"
            "{{ bull_bear_framing(data) }}"
        )
        data = {
            "bull_case": {
                "title": "Bull Case",
                "entries": [{"text": "Strong board", "source": "DEF 14A", "severity": ""}],
            },
            "bear_case": {
                "title": "Bear Case",
                "entries": [{"text": "Litigation risk", "source": "10-K", "severity": "HIGH"}],
            },
        }
        result = tpl.render(data=data)
        assert "bull-case" in result
        assert "bear-case" in result
        assert "bull-bear-grid" in result
        assert "Strong board" in result
        assert "Litigation risk" in result

    def test_macro_handles_empty_data(self, env: jinja2.Environment) -> None:
        tpl = env.from_string(
            "{% from 'components/narratives.html.j2' import bull_bear_framing %}"
            "{{ bull_bear_framing(data) }}"
        )
        # None data should not crash
        result = tpl.render(data=None)
        assert "bull-bear-grid" not in result

    def test_macro_handles_bull_only(self, env: jinja2.Environment) -> None:
        tpl = env.from_string(
            "{% from 'components/narratives.html.j2' import bull_bear_framing %}"
            "{{ bull_bear_framing(data) }}"
        )
        data = {
            "bull_case": {
                "title": "Bull Case",
                "entries": [{"text": "Clean profile", "source": "", "severity": ""}],
            },
            "bear_case": None,
        }
        result = tpl.render(data=data)
        assert "bull-case" in result
        assert "bear-case" not in result

    def test_macro_severity_classes(self, env: jinja2.Environment) -> None:
        tpl = env.from_string(
            "{% from 'components/narratives.html.j2' import bull_bear_framing %}"
            "{{ bull_bear_framing(data) }}"
        )
        data = {
            "bull_case": None,
            "bear_case": {
                "title": "Bear Case",
                "entries": [
                    {"text": "High risk", "source": "", "severity": "HIGH"},
                    {"text": "Medium risk", "source": "", "severity": "MEDIUM"},
                ],
            },
        }
        result = tpl.render(data=data)
        assert "severity-high" in result
        assert "severity-medium" in result
