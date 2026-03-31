"""Tests for Phase 125: Grid Layouts + Section Templates.

VIS-04: Multi-column grid layouts for KV data (2-col and 3-col).
FIX-04: Governance narrative not truncated for complex companies.
"""

from __future__ import annotations

import pytest

from do_uw.stages.render.context_builders.narrative_evaluative import (
    collect_deep_context,
)


# ---------------------------------------------------------------------------
# VIS-04: Grid CSS classes present in component stylesheet
# ---------------------------------------------------------------------------

class TestGridCSSClasses:
    """Verify kv-grid-2 and kv-grid-3 classes exist in components.css."""

    @pytest.fixture()
    def components_css(self) -> str:
        from pathlib import Path
        css_path = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html" / "components.css"
        return css_path.read_text()

    def test_kv_grid_2_class_exists(self, components_css: str) -> None:
        assert ".kv-grid-2" in components_css

    def test_kv_grid_3_class_exists(self, components_css: str) -> None:
        assert ".kv-grid-3" in components_css

    def test_kv_grid_2_is_two_column(self, components_css: str) -> None:
        # Should have grid-template-columns: 1fr 1fr
        idx = components_css.index(".kv-grid-2")
        block = components_css[idx:idx + 300]
        assert "1fr 1fr" in block

    def test_kv_grid_3_is_three_column(self, components_css: str) -> None:
        idx = components_css.index(".kv-grid-3")
        block = components_css[idx:idx + 300]
        assert "1fr 1fr 1fr" in block

    def test_kv_grid_prevents_blowout(self, components_css: str) -> None:
        assert "min-width: 0" in components_css

    def test_kv_grid_print_styles(self, components_css: str) -> None:
        # Print styles should be defined
        assert ".kv-grid-2" in components_css
        assert "@media print" in components_css


# ---------------------------------------------------------------------------
# VIS-04: Grid classes used in governance templates
# ---------------------------------------------------------------------------

class TestGovernanceGridTemplates:
    """Verify governance templates use kv-grid-2 for multi-column layout."""

    @pytest.fixture()
    def structural_gov_template(self) -> str:
        from pathlib import Path
        t = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html" / "sections" / "governance" / "structural_governance.html.j2"
        return t.read_text()

    @pytest.fixture()
    def transparency_template(self) -> str:
        from pathlib import Path
        t = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html" / "sections" / "governance" / "transparency_disclosure.html.j2"
        return t.read_text()

    def test_structural_governance_uses_grid(self, structural_gov_template: str) -> None:
        assert "kv-grid-2" in structural_gov_template

    def test_transparency_uses_grid(self, transparency_template: str) -> None:
        assert "kv-grid-2" in transparency_template


# ---------------------------------------------------------------------------
# VIS-04: Grid classes used in financial key_metrics template
# ---------------------------------------------------------------------------

class TestFinancialGridTemplates:
    """Verify financial key_metrics template uses kv-grid-2."""

    @pytest.fixture()
    def key_metrics_template(self) -> str:
        from pathlib import Path
        t = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html" / "sections" / "financial" / "key_metrics.html.j2"
        return t.read_text()

    def test_key_metrics_uses_grid(self, key_metrics_template: str) -> None:
        assert "kv-grid-2" in key_metrics_template


# ---------------------------------------------------------------------------
# VIS-04: kv_grid macro exists in tables.html.j2
# ---------------------------------------------------------------------------

class TestKvGridMacro:
    """Verify kv_grid macro exists in the tables component."""

    @pytest.fixture()
    def tables_template(self) -> str:
        from pathlib import Path
        t = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html" / "components" / "tables.html.j2"
        return t.read_text()

    def test_kv_grid_macro_defined(self, tables_template: str) -> None:
        assert "macro kv_grid" in tables_template

    def test_kv_grid_macro_uses_css_class(self, tables_template: str) -> None:
        assert 'kv-grid-{{ cols }}' in tables_template


# ---------------------------------------------------------------------------
# FIX-04: Governance narrative NOT truncated
# ---------------------------------------------------------------------------

class TestGovernanceNarrativeNotTruncated:
    """Verify collect_deep_context does not truncate narrative content."""

    def test_long_narrative_preserved(self) -> None:
        """A 2000-char governance narrative must not be truncated."""
        from unittest.mock import MagicMock, patch

        # Create a long narrative (realistic for complex governance)
        long_narrative = (
            "The board comprises 14 directors with 78.6% independence. "
            "CEO Tim Cook does not serve as board chair, providing separation "
            "of powers. Average board tenure is 8.3 years, within the healthy "
            "5-12 year range. Gender diversity stands at 35.7%, exceeding "
            "NASDAQ requirements. The audit committee is fully independent. "
            "Say-on-Pay approval was 94.2%, indicating strong shareholder "
            "confidence in the compensation structure. CEO total compensation "
            "was $63.2M with a pay ratio of 1,447:1. The clawback policy "
            "exceeds Dodd-Frank minimums, covering cash bonuses and equity "
            "awards. No related-party transactions were disclosed. "
            "Institutional ownership stands at 60.3% with insider ownership "
            "at 0.07%. Narrative coherence analysis shows strategy aligned "
            "with results and tone aligned with financials. No activists "
            "detected. Board forensic profiles show no prior litigation for "
            "any director. Overboarding count is zero. "
        ) * 3  # ~2400 chars

        mock_state = MagicMock()
        mock_state.analysis = MagicMock()

        with patch(
            "do_uw.stages.render.context_builders.narrative_evaluative."
            "collect_deep_context.__module__"
        ):
            pass

        # Directly test the truncation removal by calling with mocked imports
        with (
            patch(
                "do_uw.stages.render.context_builders.narrative._get_narrative_text",
                return_value=long_narrative,
            ),
            patch(
                "do_uw.stages.render.context_builders.narrative._build_scr_for_section",
                return_value=None,
            ),
            patch(
                "do_uw.stages.render.context_builders.narrative._strip_md",
                side_effect=lambda x: x,
            ),
        ):
            items = collect_deep_context(mock_state, "governance")

        assert len(items) == 1
        assert items[0]["label"] == "Full Assessment"
        # Key assertion: content is NOT truncated
        assert len(items[0]["content"]) == len(long_narrative)
        assert "..." not in items[0]["content"]

    def test_short_narrative_unchanged(self) -> None:
        """Short narratives should also pass through unmodified."""
        from unittest.mock import MagicMock, patch

        short_narrative = "Board is well governed with 80% independence."
        mock_state = MagicMock()

        with (
            patch(
                "do_uw.stages.render.context_builders.narrative._get_narrative_text",
                return_value=short_narrative,
            ),
            patch(
                "do_uw.stages.render.context_builders.narrative._build_scr_for_section",
                return_value=None,
            ),
            patch(
                "do_uw.stages.render.context_builders.narrative._strip_md",
                side_effect=lambda x: x,
            ),
        ):
            items = collect_deep_context(mock_state, "governance")

        assert len(items) == 1
        assert items[0]["content"] == short_narrative
