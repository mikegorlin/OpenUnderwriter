"""Tests for dual-voice template integration (Phase 130-02).

Verifies:
- Jinja2 macro renders dual-voice blocks with commentary data
- Empty/None commentary hides dual-voice blocks (graceful degradation)
- Confidence badge renders with correct CSS class
- All 8 section templates include the macro import
- Meeting prep template renders dual-voice block
"""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import DictLoader, Environment

# Template directories
TEMPLATE_DIR = Path("src/do_uw/templates/html")
SECTIONS_DIR = TEMPLATE_DIR / "sections"
APPENDICES_DIR = TEMPLATE_DIR / "appendices"
MACROS_DIR = TEMPLATE_DIR / "macros"

# The 8 section templates that must include dual-voice
SECTION_TEMPLATES = [
    SECTIONS_DIR / "financial.html.j2",
    SECTIONS_DIR / "market.html.j2",
    SECTIONS_DIR / "governance.html.j2",
    SECTIONS_DIR / "litigation.html.j2",
    SECTIONS_DIR / "scoring.html.j2",
    SECTIONS_DIR / "company.html.j2",
    SECTIONS_DIR / "executive_brief.html.j2",
    APPENDICES_DIR / "meeting_prep.html.j2",
]


# Read the actual macro source for Jinja2 rendering tests
MACRO_SOURCE = (MACROS_DIR / "dual_voice.html.j2").read_text()


def _make_env() -> Environment:
    """Create a Jinja2 env with the dual-voice macro available."""
    loader = DictLoader({
        "macros/dual_voice.html.j2": MACRO_SOURCE,
        "test_template.html.j2": (
            '{% from "macros/dual_voice.html.j2" import dual_voice_block %}'
            "{{ dual_voice_block(commentary, 'Test Section') }}"
        ),
    })
    return Environment(loader=loader, autoescape=False)


class TestDualVoiceMacroFile:
    """Verify the macro file exists and contains expected content."""

    def test_macro_file_exists(self) -> None:
        path = MACROS_DIR / "dual_voice.html.j2"
        assert path.exists(), f"Missing: {path}"

    def test_macro_contains_definition(self) -> None:
        content = (MACROS_DIR / "dual_voice.html.j2").read_text()
        assert "macro dual_voice_block" in content

    def test_macro_contains_factual_div(self) -> None:
        content = (MACROS_DIR / "dual_voice.html.j2").read_text()
        assert "dual-voice__factual" in content

    def test_macro_contains_commentary_div(self) -> None:
        content = (MACROS_DIR / "dual_voice.html.j2").read_text()
        assert "dual-voice__commentary" in content

    def test_macro_contains_confidence_badge(self) -> None:
        content = (MACROS_DIR / "dual_voice.html.j2").read_text()
        assert "confidence-badge" in content


class TestDualVoiceRendering:
    """Test macro rendering with Jinja2 Environment."""

    def test_renders_with_commentary(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary={
            "what_was_said": "Revenue grew 15%.",
            "underwriting_commentary": "Growth masks margin compression risk.",
            "confidence": "HIGH",
            "hallucination_warnings": [],
        })
        assert "dual-voice__factual" in html
        assert "dual-voice__commentary" in html
        assert "Revenue grew 15%." in html
        assert "Growth masks margin compression risk." in html

    def test_renders_confidence_badge_high(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary={
            "what_was_said": "Test",
            "underwriting_commentary": "Test",
            "confidence": "HIGH",
        })
        assert "confidence-badge--high" in html

    def test_renders_confidence_badge_medium(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary={
            "what_was_said": "Test",
            "underwriting_commentary": "Test",
            "confidence": "MEDIUM",
        })
        assert "confidence-badge--medium" in html

    def test_renders_confidence_badge_low(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary={
            "what_was_said": "Test",
            "underwriting_commentary": "Test",
            "confidence": "LOW",
        })
        assert "confidence-badge--low" in html

    def test_hidden_when_none(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary=None)
        assert "dual-voice" not in html

    def test_hidden_when_empty_strings(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary={
            "what_was_said": "",
            "underwriting_commentary": "",
            "confidence": "MEDIUM",
        })
        assert "dual-voice__factual" not in html

    def test_renders_with_only_what_was_said(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary={
            "what_was_said": "Company disclosed risk factors.",
            "underwriting_commentary": "",
            "confidence": "LOW",
        })
        assert "dual-voice__factual" in html

    def test_renders_header_text(self) -> None:
        env = _make_env()
        tpl = env.get_template("test_template.html.j2")
        html = tpl.render(commentary={
            "what_was_said": "Test",
            "underwriting_commentary": "Test",
            "confidence": "HIGH",
        })
        assert "What Was Said" in html
        assert "Underwriting Commentary" in html


class TestSectionTemplateImports:
    """Verify all 8 section templates import and use the dual-voice macro."""

    @pytest.mark.parametrize("template_path", SECTION_TEMPLATES, ids=[
        p.stem for p in SECTION_TEMPLATES
    ])
    def test_template_imports_macro(self, template_path: Path) -> None:
        content = template_path.read_text()
        assert 'from "macros/dual_voice.html.j2" import dual_voice_block' in content, (
            f"{template_path.name} missing dual_voice_block import"
        )

    @pytest.mark.parametrize("template_path", SECTION_TEMPLATES, ids=[
        p.stem for p in SECTION_TEMPLATES
    ])
    def test_template_calls_macro(self, template_path: Path) -> None:
        content = template_path.read_text()
        assert "dual_voice_block(" in content, (
            f"{template_path.name} missing dual_voice_block() call"
        )


class TestMeetingPrepDualVoice:
    """Specific tests for meeting prep template dual-voice integration."""

    def test_meeting_prep_template_exists(self) -> None:
        path = APPENDICES_DIR / "meeting_prep.html.j2"
        assert path.exists(), f"Missing: {path}"

    def test_meeting_prep_imports_macro(self) -> None:
        content = (APPENDICES_DIR / "meeting_prep.html.j2").read_text()
        assert 'from "macros/dual_voice.html.j2" import dual_voice_block' in content

    def test_meeting_prep_uses_correct_key(self) -> None:
        content = (APPENDICES_DIR / "meeting_prep.html.j2").read_text()
        assert "commentary.get('meeting_prep')" in content


class TestCSSStyles:
    """Verify CSS for dual-voice blocks exists in components.css."""

    def test_css_file_has_dual_voice_styles(self) -> None:
        css = (TEMPLATE_DIR / "components.css").read_text()
        assert ".dual-voice" in css

    def test_css_has_factual_style(self) -> None:
        css = (TEMPLATE_DIR / "components.css").read_text()
        assert ".dual-voice__factual" in css

    def test_css_has_commentary_style(self) -> None:
        css = (TEMPLATE_DIR / "components.css").read_text()
        assert ".dual-voice__commentary" in css

    def test_css_has_confidence_badge_high(self) -> None:
        css = (TEMPLATE_DIR / "components.css").read_text()
        assert ".confidence-badge--high" in css

    def test_css_has_confidence_badge_medium(self) -> None:
        css = (TEMPLATE_DIR / "components.css").read_text()
        assert ".confidence-badge--medium" in css

    def test_css_has_confidence_badge_low(self) -> None:
        css = (TEMPLATE_DIR / "components.css").read_text()
        assert ".confidence-badge--low" in css

    def test_css_has_print_media_query(self) -> None:
        css = (TEMPLATE_DIR / "components.css").read_text()
        # Check that dual-voice has print stacking
        assert "dual-voice" in css
        # The print rule stacks columns to 1fr
        assert "grid-template-columns: 1fr" in css
