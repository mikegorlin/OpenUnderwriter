"""Tests for executive summary overhaul (Phase 130-02).

Verifies:
- SCA theory/defense mappings in extract_exec_summary()
- No factor codes (F1-F10) in any theory text
- No "AI Assessment" in key_findings or narratives templates
- Executive brief template has narrative BEFORE recommendation
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from do_uw.stages.render.context_builders.company_exec_summary import (
    _SCA_DEFENSE_MAP,
    _SCA_THEORY_MAP,
    extract_exec_summary,
)


# ---------------------------------------------------------------------------
# SCA Theory/Defense map content tests
# ---------------------------------------------------------------------------


class TestSCATheoryMaps:
    """Verify SCA theory and defense maps contain named legal theories."""

    def test_theory_map_has_entries(self) -> None:
        assert len(_SCA_THEORY_MAP) >= 5

    def test_defense_map_has_entries(self) -> None:
        assert len(_SCA_DEFENSE_MAP) >= 5

    def test_theory_map_contains_section_10b(self) -> None:
        all_theories = " ".join(_SCA_THEORY_MAP.values())
        assert "Section 10(b)" in all_theories

    def test_theory_map_contains_caremark(self) -> None:
        all_theories = " ".join(_SCA_THEORY_MAP.values())
        assert "Caremark" in all_theories

    def test_theory_map_contains_tellabs(self) -> None:
        all_theories = " ".join(_SCA_THEORY_MAP.values())
        assert "Tellabs" in all_theories

    def test_theory_map_contains_scienter(self) -> None:
        all_theories = " ".join(_SCA_THEORY_MAP.values())
        assert "scienter" in all_theories

    def test_defense_map_contains_loss_causation(self) -> None:
        all_defenses = " ".join(_SCA_DEFENSE_MAP.values())
        assert "loss causation" in all_defenses

    def test_defense_map_contains_dura(self) -> None:
        all_theories = " ".join(_SCA_DEFENSE_MAP.values())
        assert "Dura" in all_theories

    def test_no_factor_codes_in_theory_map(self) -> None:
        """No F1-F10 factor codes in any theory text."""
        factor_re = re.compile(r"\bF\d{1,2}\b")
        for key, text in _SCA_THEORY_MAP.items():
            assert not factor_re.search(text), (
                f"Factor code found in theory '{key}': {text}"
            )

    def test_no_factor_codes_in_defense_map(self) -> None:
        """No F1-F10 factor codes in any defense text."""
        factor_re = re.compile(r"\bF\d{1,2}\b")
        for key, text in _SCA_DEFENSE_MAP.items():
            assert not factor_re.search(text), (
                f"Factor code found in defense '{key}': {text}"
            )


# ---------------------------------------------------------------------------
# extract_exec_summary SCA enrichment tests
# ---------------------------------------------------------------------------


def _mock_state_with_findings() -> Any:
    """Build a mock AnalysisState with key findings that have theory_mapping."""
    state = MagicMock()

    # Mock key findings
    neg = MagicMock()
    neg.evidence_narrative = "Stock declined 30% in 90 days"
    neg.section_origin = "SECT4"
    neg.scoring_impact = "High impact"
    neg.theory_mapping = "stock_drop"

    pos = MagicMock()
    pos.evidence_narrative = "No prior SCA filings"
    pos.section_origin = "SECT6"
    pos.scoring_impact = "Positive"
    pos.theory_mapping = "no_sca_history"

    key_findings = MagicMock()
    key_findings.negatives = [neg]
    key_findings.positives = [pos]

    es = MagicMock()
    es.key_findings = key_findings
    es.thesis = MagicMock()
    es.thesis.narrative = "Test thesis"
    es.snapshot = None
    es.inherent_risk = None

    state.executive_summary = es
    state.scoring = MagicMock()
    state.scoring.quality_score = 85.0
    state.scoring.composite_score = 12.0
    state.scoring.tier = MagicMock()
    state.scoring.tier.tier = "WIN"
    state.scoring.tier.action = "Write primary"
    state.scoring.claim_probability = None
    state.scoring.tower_recommendation = None
    state.company = None

    return state


class TestExtractExecSummarySCA:
    """Verify extract_exec_summary adds SCA theory/defense."""

    def test_negatives_have_sca_theory_key(self) -> None:
        state = _mock_state_with_findings()
        result = extract_exec_summary(state)
        neg_detail = result.get("key_findings_detail", [])
        assert len(neg_detail) >= 1
        assert "sca_theory" in neg_detail[0]

    def test_negative_sca_theory_is_populated(self) -> None:
        state = _mock_state_with_findings()
        result = extract_exec_summary(state)
        neg_detail = result["key_findings_detail"]
        theory = neg_detail[0]["sca_theory"]
        assert "Section 10(b)" in theory

    def test_positives_have_sca_defense_key(self) -> None:
        state = _mock_state_with_findings()
        result = extract_exec_summary(state)
        pos_detail = result.get("positive_detail", [])
        assert len(pos_detail) >= 1
        assert "sca_defense" in pos_detail[0]

    def test_positive_sca_defense_is_populated(self) -> None:
        state = _mock_state_with_findings()
        result = extract_exec_summary(state)
        pos_detail = result["positive_detail"]
        defense = pos_detail[0]["sca_defense"]
        assert "recurrence probability" in defense


# ---------------------------------------------------------------------------
# Template content tests
# ---------------------------------------------------------------------------


class TestTemplateContent:
    """Verify template files have correct structure."""

    def test_no_ai_assessment_in_key_findings(self) -> None:
        """key_findings.html.j2 must not contain AI Assessment."""
        path = Path("src/do_uw/templates/html/sections/executive/key_findings.html.j2")
        content = path.read_text()
        assert "AI Assessment" not in content

    def test_no_ai_assessment_in_narratives(self) -> None:
        """narratives.html.j2 must not contain AI Assessment."""
        path = Path("src/do_uw/templates/html/components/narratives.html.j2")
        content = path.read_text()
        assert "AI Assessment" not in content

    def test_key_findings_uses_numbered_list(self) -> None:
        """key_findings.html.j2 uses <ol> not <ul> for findings."""
        path = Path("src/do_uw/templates/html/sections/executive/key_findings.html.j2")
        content = path.read_text()
        assert "<ol" in content
        assert "<ul" not in content

    def test_key_findings_shows_sca_theory(self) -> None:
        """key_findings.html.j2 includes sca_theory span."""
        path = Path("src/do_uw/templates/html/sections/executive/key_findings.html.j2")
        content = path.read_text()
        assert "sca_theory" in content

    def test_key_findings_shows_sca_defense(self) -> None:
        """key_findings.html.j2 includes sca_defense span."""
        path = Path("src/do_uw/templates/html/sections/executive/key_findings.html.j2")
        content = path.read_text()
        assert "sca_defense" in content

    def test_exec_brief_narrative_before_recommendation(self) -> None:
        """executive_brief.html.j2 has narrative section BEFORE recommendation."""
        path = Path("src/do_uw/templates/html/sections/executive_brief.html.j2")
        content = path.read_text()
        narr_pos = content.find("eb-risk-narrative")
        rec_pos = content.find("eb-recommendation")
        assert narr_pos > 0, "Narrative section not found"
        assert rec_pos > 0, "Recommendation section not found"
        assert narr_pos < rec_pos, (
            f"Narrative (pos={narr_pos}) must come before "
            f"recommendation (pos={rec_pos})"
        )

    def test_exec_brief_findings_before_recommendation(self) -> None:
        """executive_brief.html.j2 has findings BEFORE recommendation."""
        path = Path("src/do_uw/templates/html/sections/executive_brief.html.j2")
        content = path.read_text()
        findings_pos = content.find("eb-findings-grid")
        rec_pos = content.find("eb-recommendation")
        assert findings_pos > 0, "Findings section not found"
        assert rec_pos > 0, "Recommendation section not found"
        assert findings_pos < rec_pos, (
            f"Findings (pos={findings_pos}) must come before "
            f"recommendation (pos={rec_pos})"
        )


# ---------------------------------------------------------------------------
# Narrative prompts content tests
# ---------------------------------------------------------------------------


class TestNarrativePrompts:
    """Verify narrative prompts have no system internals."""

    def test_no_factor_codes_in_prompts(self) -> None:
        """No F1-F10 references in narrative prompts."""
        path = Path("src/do_uw/stages/benchmark/narrative_prompts.py")
        content = path.read_text()
        # Should not have scoring factor references like 'F3 = 5/8'
        assert "Scoring factor F" not in content
        assert "'F3 = X/Y points'" not in content
        assert "F2 and F7 deductions" not in content

    def test_no_deduction_points_in_thesis(self) -> None:
        """thesis_templates.py has no deduction points."""
        path = Path("src/do_uw/stages/benchmark/thesis_templates.py")
        content = path.read_text()
        assert "deduction points" not in content

    def test_no_factor_id_in_thesis_narrative(self) -> None:
        """thesis_templates _top_factor_narrative has no factor_id."""
        path = Path("src/do_uw/stages/benchmark/thesis_templates.py")
        content = path.read_text()
        # Find the function and check it doesn't reference factor_id
        func_start = content.find("def _top_factor_narrative")
        func_end = content.find("\ndef ", func_start + 1)
        func_body = content[func_start:func_end]
        assert "factor_id" not in func_body
