"""Tests for reading path navigation structure.

Validates navigation paths through the worksheet:
1. UW path: Scorecard -> CRF alerts -> section of concern -> trace
2. Secondary path: Executive brief -> Decision record

Updated for uw analysis layout: navigation is in uw_analysis.html.j2
header bar, not the old sidebar in base.html.j2.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_TEMPLATE_DIR = Path(__file__).resolve().parents[3] / "src" / "do_uw" / "templates" / "html"
_BASE_TEMPLATE = _TEMPLATE_DIR / "base.html.j2"
_BETA_TEMPLATE = _TEMPLATE_DIR / "sections" / "uw_analysis.html.j2"
_SIDEBAR_CSS = _TEMPLATE_DIR / "sidebar.css"


@pytest.fixture()
def base_html() -> str:
    return _BASE_TEMPLATE.read_text()


@pytest.fixture()
def beta_html() -> str:
    return _BETA_TEMPLATE.read_text()


@pytest.fixture()
def all_html(base_html: str, beta_html: str) -> str:
    """Combined template text for navigation checks."""
    return base_html + beta_html


class TestBetaNavLinks:
    """UW analysis header nav must link to all major sections.

    Nav links are Jinja2 tuples: ('#section-id', 'Label') rendered
    into href attributes at template execution time.
    """

    @pytest.mark.parametrize(
        "section_id",
        [
            "scorecard",
            "executive-brief",
            "company-operations",
            "stock-market",
            "financial-health",
            "governance",
            "litigation",
            "scoring",
        ],
    )
    def test_nav_links_to_section(self, beta_html: str, section_id: str) -> None:
        # In raw template, links appear as Jinja2 tuples: ('#section-id', 'Label')
        assert f"'#{section_id}'" in beta_html, (
            f"Beta nav must contain ('#{section_id}', ...) tuple"
        )


class TestBetaNavStructure:
    """Beta header nav must be a fixed bar with no-print class."""

    def test_fixed_position(self, beta_html: str) -> None:
        assert "position:fixed" in beta_html

    def test_no_print(self, beta_html: str) -> None:
        assert 'class="no-print"' in beta_html

    def test_z_index(self, beta_html: str) -> None:
        assert "z-index:100" in beta_html


class TestSidebarHidden:
    """Old sidebar must be hidden when uw analysis is active."""

    def test_sidebar_hidden_when_beta(self, base_html: str) -> None:
        assert "display:none" in base_html or "display: none" in base_html


class TestSidebarAlertStyle:
    """Sidebar alert link for CRF should have amber styling."""

    def test_sidebar_alert_class(self) -> None:
        css = _SIDEBAR_CSS.read_text()
        assert "sidebar-alert" in css
        assert "#D97706" in css


class TestIntersectionObserverTracking:
    """IntersectionObserver must track all section[id] elements."""

    def test_observer_queries_sections(self, base_html: str) -> None:
        assert "section[id]" in base_html

    def test_observer_present(self, base_html: str) -> None:
        assert "IntersectionObserver" in base_html

    def test_toc_links_query(self, base_html: str) -> None:
        assert ".sidebar-toc a[href" in base_html


class TestPrimaryReadingPath:
    """UW reading path: scorecard -> analysis sections -> scoring.

    In beta layout, nav button order defines the reading path.
    """

    def test_scorecard_before_company(self, beta_html: str) -> None:
        sc_pos = beta_html.index("'#scorecard'")
        co_pos = beta_html.index("'#company-operations'")
        assert sc_pos < co_pos, "Scorecard must appear before Company in nav"

    def test_company_before_market(self, beta_html: str) -> None:
        co_pos = beta_html.index("'#company-operations'")
        mkt_pos = beta_html.index("'#stock-market'")
        assert co_pos < mkt_pos, "Company must appear before Market in nav"

    def test_market_before_financial(self, beta_html: str) -> None:
        mkt_pos = beta_html.index("'#stock-market'")
        fin_pos = beta_html.index("'#financial-health'")
        assert mkt_pos < fin_pos, "Market must appear before Financial in nav"

    def test_financial_before_governance(self, beta_html: str) -> None:
        fin_pos = beta_html.index("'#financial-health'")
        gov_pos = beta_html.index("'#governance'")
        assert fin_pos < gov_pos, "Financial must appear before Governance in nav"

    def test_governance_before_litigation(self, beta_html: str) -> None:
        gov_pos = beta_html.index("'#governance'")
        lit_pos = beta_html.index("'#litigation'")
        assert gov_pos < lit_pos, "Governance must appear before Litigation in nav"

    def test_litigation_before_scoring(self, beta_html: str) -> None:
        lit_pos = beta_html.index("'#litigation'")
        sc_pos = beta_html.index("'#scoring'")
        assert lit_pos < sc_pos, "Litigation must appear before Scoring in nav"


class TestPdfModeDetailsExclusion:
    """pdf_mode details expansion must exclude signal-drilldown."""

    def test_signal_drilldown_excluded(self, base_html: str) -> None:
        assert "details:not(.signal-drilldown)" in base_html
