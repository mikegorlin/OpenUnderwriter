"""Integration tests for Phase 117 forward-looking pipeline wiring.

Verifies that:
1. html_context_assembly.py contains all 5 forward-looking context builder imports
2. Context builders produce correct keys with empty/populated state
3. Template includes are correctly wired (forward_looking, scoring, worksheet)

Phase 117-06: Forward-Looking Risk Framework Integration
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from do_uw.models.forward_looking import ForwardLookingData
from do_uw.models.state import AnalysisState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_minimal_state() -> AnalysisState:
    """Build minimal AnalysisState with forward_looking initialized."""
    state = AnalysisState(ticker="TEST")
    state.forward_looking = ForwardLookingData()
    return state


def _get_template_dir() -> Path:
    """Get the template directory path."""
    return (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "do_uw"
        / "templates"
        / "html"
    )


def _get_source_file(name: str) -> str:
    """Read a source file and return its contents."""
    base = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "do_uw"
    )
    return (base / name).read_text()


# ---------------------------------------------------------------------------
# Source code wiring verification: html_context_assembly contains all imports
# ---------------------------------------------------------------------------


class TestContextAssemblyWiring:
    """Verify html_context_assembly.py has correct forward-looking context builder wiring."""

    def _get_assembly_source(self) -> str:
        return _get_source_file("stages/render/html_context_assembly.py")

    def test_imports_forward_risk_map(self) -> None:
        """Assembly imports extract_forward_risk_map."""
        src = self._get_assembly_source()
        assert "extract_forward_risk_map" in src

    def test_imports_credibility(self) -> None:
        """Assembly imports extract_credibility."""
        src = self._get_assembly_source()
        assert "extract_credibility" in src

    def test_imports_monitoring(self) -> None:
        """Assembly imports extract_monitoring_triggers."""
        src = self._get_assembly_source()
        assert "extract_monitoring_triggers" in src

    def test_imports_posture(self) -> None:
        """Assembly imports extract_posture."""
        src = self._get_assembly_source()
        assert "extract_posture" in src

    def test_imports_quick_screen(self) -> None:
        """Assembly imports extract_quick_screen."""
        src = self._get_assembly_source()
        assert "extract_quick_screen" in src

    def test_sets_forward_risk_map_key(self) -> None:
        """Assembly assigns context['forward_risk_map']."""
        src = self._get_assembly_source()
        assert 'context["forward_risk_map"]' in src

    def test_sets_credibility_data_key(self) -> None:
        """Assembly assigns context['credibility_data']."""
        src = self._get_assembly_source()
        assert 'context["credibility_data"]' in src

    def test_sets_monitoring_data_key(self) -> None:
        """Assembly assigns context['monitoring_data']."""
        src = self._get_assembly_source()
        assert 'context["monitoring_data"]' in src

    def test_sets_posture_data_key(self) -> None:
        """Assembly assigns context['posture_data']."""
        src = self._get_assembly_source()
        assert 'context["posture_data"]' in src

    def test_sets_quick_screen_data_key(self) -> None:
        """Assembly assigns context['quick_screen_data']."""
        src = self._get_assembly_source()
        assert 'context["quick_screen_data"]' in src


# ---------------------------------------------------------------------------
# Context builder functional tests with empty state
# ---------------------------------------------------------------------------


class TestContextBuildersEmptyState:
    """Verify context builders produce correct fallback keys with empty state."""

    def test_forward_risk_map_empty(self) -> None:
        """extract_forward_risk_map returns has_forward_statements=False with empty state."""
        from do_uw.stages.render.context_builders.forward_risk_map import (
            extract_forward_risk_map,
        )
        state = _make_minimal_state()
        result = extract_forward_risk_map(state, {})
        assert result["forward_available"] is False
        assert result["has_forward_statements"] is False

    def test_credibility_empty(self) -> None:
        """extract_credibility returns credibility_available=False with empty state."""
        from do_uw.stages.render.context_builders.credibility_context import (
            extract_credibility,
        )
        state = _make_minimal_state()
        result = extract_credibility(state, {})
        assert result["credibility_available"] is False

    def test_monitoring_empty(self) -> None:
        """extract_monitoring_triggers returns monitoring_available=False with empty state."""
        from do_uw.stages.render.context_builders.monitoring_context import (
            extract_monitoring_triggers,
        )
        state = _make_minimal_state()
        result = extract_monitoring_triggers(state, {})
        assert result["monitoring_available"] is False

    def test_posture_empty(self) -> None:
        """extract_posture returns posture_available=False with empty state."""
        from do_uw.stages.render.context_builders.posture_context import (
            extract_posture,
        )
        state = _make_minimal_state()
        result = extract_posture(state, {})
        assert result["posture_available"] is False

    def test_quick_screen_empty(self) -> None:
        """extract_quick_screen returns quick_screen_available=False with empty state."""
        from do_uw.stages.render.context_builders.quick_screen_context import (
            extract_quick_screen,
        )
        state = _make_minimal_state()
        result = extract_quick_screen(state, {})
        assert result["quick_screen_available"] is False


# ---------------------------------------------------------------------------
# Template include verification tests
# ---------------------------------------------------------------------------


class TestTemplateIncludes:
    """Verify template files contain the expected includes."""

    def test_forward_looking_includes_risk_map(self) -> None:
        """forward_looking.html.j2 includes risk_map template."""
        tmpl = _get_template_dir() / "sections" / "forward_looking.html.j2"
        assert tmpl.exists(), f"Missing: {tmpl}"
        content = tmpl.read_text()
        assert "sections/forward_looking/risk_map.html.j2" in content

    def test_scoring_includes_underwriting_posture(self) -> None:
        """scoring.html.j2 includes underwriting_posture template."""
        tmpl = _get_template_dir() / "sections" / "scoring.html.j2"
        assert tmpl.exists(), f"Missing: {tmpl}"
        content = tmpl.read_text()
        assert "sections/scoring/underwriting_posture.html.j2" in content

    def test_scoring_includes_zero_verification(self) -> None:
        """scoring.html.j2 includes zero_verification template."""
        tmpl = _get_template_dir() / "sections" / "scoring.html.j2"
        content = tmpl.read_text()
        assert "sections/scoring/zero_verification.html.j2" in content

    def test_scoring_includes_watch_items(self) -> None:
        """scoring.html.j2 includes watch_items template."""
        tmpl = _get_template_dir() / "sections" / "scoring.html.j2"
        content = tmpl.read_text()
        assert "sections/scoring/watch_items.html.j2" in content

    def test_worksheet_includes_trigger_matrix(self) -> None:
        """worksheet.html.j2 includes trigger_matrix template."""
        tmpl = _get_template_dir() / "worksheet.html.j2"
        assert tmpl.exists(), f"Missing: {tmpl}"
        content = tmpl.read_text()
        assert "sections/trigger_matrix.html.j2" in content

    def test_trigger_matrix_after_crf_banner(self) -> None:
        """trigger_matrix include appears after crf_banner and before Zone 2 section loop."""
        tmpl = _get_template_dir() / "worksheet.html.j2"
        content = tmpl.read_text()
        crf_pos = content.find('include "sections/crf_banner.html.j2"')
        trigger_pos = content.find('include "sections/trigger_matrix.html.j2"')
        # Zone 2 marker is the actual include comment, not the header comment
        zone2_pos = content.find("for section in manifest_sections")
        assert crf_pos > 0 and trigger_pos > 0 and zone2_pos > 0, (
            "All three markers must be found in worksheet"
        )
        assert crf_pos < trigger_pos < zone2_pos, (
            "trigger_matrix must appear after crf_banner and before manifest section loop"
        )

    def test_forward_looking_includes_credibility(self) -> None:
        """forward_looking.html.j2 includes credibility template."""
        tmpl = _get_template_dir() / "sections" / "forward_looking.html.j2"
        content = tmpl.read_text()
        assert "sections/forward_looking/credibility.html.j2" in content

    def test_forward_looking_includes_monitoring(self) -> None:
        """forward_looking.html.j2 includes monitoring_triggers template."""
        tmpl = _get_template_dir() / "sections" / "forward_looking.html.j2"
        content = tmpl.read_text()
        assert "sections/forward_looking/monitoring_triggers.html.j2" in content
