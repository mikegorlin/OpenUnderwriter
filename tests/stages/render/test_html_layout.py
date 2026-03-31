"""Automated layout structure tests for the HTML worksheet (Phase 43).

Validates:
- Two-column CapIQ layout (worksheet-layout + sidebar-toc)
- Sidebar TOC links match all 9 required sections
- Sticky topbar is identity-only (no score/tier fields)
- Section order: identity → executive-summary → red-flags → scoring →
  financial-health → market → governance → litigation
- Red Flags as a dedicated section (with and without active flags)
- FootnoteRegistry deduplication (unit test, no HTML rendering)
- Sources appendix renders with footnote anchors when sources exist
- Print CSS hides sidebar
- data_row macro CSS classes appear in rendered HTML

All tests are independent — no shared state between tests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from do_uw.models.state import AnalysisState
from do_uw.stages.render.html_footnotes import FootnoteRegistry
from do_uw.stages.render.html_renderer import build_html_context

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_minimal_state(**overrides: Any) -> AnalysisState:
    """Create a minimal AnalysisState for layout structure tests."""
    from do_uw.models.common import SourcedValue
    from do_uw.models.company import CompanyIdentity, CompanyProfile
    from do_uw.models.state import AnalysisResults

    _now = datetime.now(tz=UTC)
    state = AnalysisState(ticker="TEST")
    state.company = CompanyProfile(
        identity=CompanyIdentity(
            ticker="TEST",
            legal_name=SourcedValue[str](
                value="Test Company Inc.",
                source="test",
                confidence="HIGH",
                as_of=_now,
            ),
        ),
    )
    state.analysis = AnalysisResults()

    for key, val in overrides.items():
        setattr(state, key, val)

    return state


def _render_html_string(state: AnalysisState) -> str:
    """Render the HTML worksheet template to a string without writing to disk."""
    from do_uw.stages.render.html_renderer import _render_html_template

    context = build_html_context(state, chart_dir=None)
    return _render_html_template(context)


# ---------------------------------------------------------------------------
# Test 1: Two-column layout
# ---------------------------------------------------------------------------


def test_two_column_layout() -> None:
    """Rendered HTML must contain the two-column layout container and sidebar."""
    state = _make_minimal_state()
    html = _render_html_string(state)

    assert "worksheet-layout" in html, (
        "Expected 'worksheet-layout' class in rendered HTML — Phase 43 two-column grid"
    )
    assert "sidebar-toc" in html, (
        "Expected 'sidebar-toc' class in rendered HTML — Phase 43 sidebar TOC"
    )


# ---------------------------------------------------------------------------
# Test 2: Sidebar TOC links
# ---------------------------------------------------------------------------


def test_sidebar_toc_links() -> None:
    """All required section anchor hrefs must be present in the sidebar TOC."""
    state = _make_minimal_state()
    html = _render_html_string(state)

    required_anchors = [
        "#key-stats",
        "#scorecard",
        "#executive-brief",
        "#red-flags",
        "#scoring",
        "#financial-health",
        "#market",
        "#governance",
        "#litigation",
        "#sources",
    ]
    for anchor in required_anchors:
        assert f'href="{anchor}"' in html, f"Expected sidebar TOC href '{anchor}' in rendered HTML"


# ---------------------------------------------------------------------------
# Test 3: Sticky topbar — identity only, no score/tier fields
# ---------------------------------------------------------------------------


def test_topbar_identity_only() -> None:
    """Sticky topbar must show company name only — no tier badge or score metrics.

    The CSS file defines sticky-topbar-tier and sticky-topbar-metric classes for
    legacy support, but the <nav class="sticky-topbar"> element itself must not
    use those classes in its rendered HTML structure.
    """
    state = _make_minimal_state()
    html = _render_html_string(state)

    # Topbar must be present
    assert "sticky-topbar" in html, "Expected 'sticky-topbar' in rendered HTML"

    # Company identifier must be present
    assert "sticky-topbar-company" in html, (
        "Expected 'sticky-topbar-company' class — company name in topbar"
    )

    # Extract just the topbar nav element HTML (not the full document with CSS)
    # CSS defines these class names but the <nav> element must not use them.
    topbar_start = html.find('<nav class="sticky-topbar')
    assert topbar_start >= 0, 'Could not locate <nav class="sticky-topbar"> element'
    topbar_end = html.find("</nav>", topbar_start)
    assert topbar_end >= 0, "Could not find closing </nav> for topbar"
    topbar_html = html[topbar_start : topbar_end + 6]

    # Score/tier classes must not appear in the topbar element itself
    assert "sticky-topbar-tier" not in topbar_html, (
        "Topbar nav element must NOT use 'sticky-topbar-tier' — scores removed from topbar"
    )
    assert "sticky-topbar-metric" not in topbar_html, (
        "Topbar nav element must NOT use 'sticky-topbar-metric' — metric chips removed from topbar"
    )


# ---------------------------------------------------------------------------
# Test 4: Section order
# ---------------------------------------------------------------------------


def test_section_order() -> None:
    """Sections must appear in correct document order per Phase 43 spec."""
    state = _make_minimal_state()
    html = _render_html_string(state)

    # Use '<section id=' to match actual HTML elements, not CSS selectors
    # Note: identity and executive-summary are no longer standalone sections;
    # they are replaced by key-stats and executive-brief in Phase 114.
    # Scorecard is conditional (only renders when scorecard_available=True).
    # Phase 122-02: Updated to narrative story order (governance before market)
    required_ids = [
        '<section id="key-stats"',
        '<section id="executive-brief"',
        '<section id="red-flags"',
        '<section id="company-operations"',
        '<section id="financial-health"',
        '<section id="litigation"',
        '<section id="governance"',
        '<section id="market"',
        '<section id="scoring"',
    ]

    positions = []
    for section_id in required_ids:
        pos = html.find(section_id)
        assert pos >= 0, f"Section '{section_id}' not found in rendered HTML"
        positions.append(pos)

    # Positions must be strictly ascending (correct document flow)
    for i in range(len(positions) - 1):
        assert positions[i] < positions[i + 1], (
            f"Section order violation: '{required_ids[i]}' at {positions[i]} "
            f"must come before '{required_ids[i + 1]}' at {positions[i + 1]}"
        )

    # The old 'market-trading' anchor must not appear (renamed to 'market' in Plan 03)
    assert '<section id="market-trading"' not in html, (
        "Old anchor 'market-trading' must not appear — renamed to 'market' in Plan 43-03"
    )


# ---------------------------------------------------------------------------
# Test 5: Red Flags section — with triggered flags
# ---------------------------------------------------------------------------


def test_red_flags_section_standalone() -> None:
    """Red Flags section must appear as a dedicated section before Scoring."""
    from do_uw.models.state import AnalysisResults

    state = _make_minimal_state()
    # Add a triggered flag via scoring context
    state.analysis = AnalysisResults()
    state.analysis.signal_results = {
        "FIN.LIQ.ratio": {
            "signal_name": "Liquidity Position",
            "status": "TRIGGERED",
            "value": 0.8,
            "evidence": "Current ratio below 1.0",
            "content_type": "EVALUATIVE_CHECK",
            "data_status": "EVALUATED",
        },
    }

    html = _render_html_string(state)

    assert '<section id="red-flags"' in html, 'Expected <section id="red-flags"> in rendered HTML'

    red_flags_pos = html.find('<section id="red-flags"')
    scoring_pos = html.find('<section id="scoring"')

    assert red_flags_pos >= 0, "Red Flags section not found"
    assert scoring_pos >= 0, "Scoring section not found"
    assert red_flags_pos < scoring_pos, "Red Flags section must appear BEFORE Scoring section"


# ---------------------------------------------------------------------------
# Test 6: Red Flags section — no flags state
# ---------------------------------------------------------------------------


def test_red_flags_empty_state() -> None:
    """Red Flags section must still render when no triggered/elevated flags exist."""
    state = _make_minimal_state()
    html = _render_html_string(state)

    assert '<section id="red-flags"' in html, (
        "Red Flags section must always render, even when no flags are triggered"
    )

    # Empty state should show "no critical red flags" indicator
    # Template: "No Critical Red Flags Identified"
    assert "No Critical Red Flags" in html, "Expected 'No Critical Red Flags' text when Red Flags section is empty"


# ---------------------------------------------------------------------------
# Test 7: FootnoteRegistry deduplication (unit test)
# ---------------------------------------------------------------------------


def test_footnote_registry_deduplication() -> None:
    """FootnoteRegistry must deduplicate identical source strings and assign stable numbers."""
    registry = FootnoteRegistry()

    # Register same source twice — should return same number
    first = registry.register("10-K 2024")
    second = registry.register("10-K 2024")
    assert first == second, "Registering the same source twice must return the same number"
    assert first == 1, "First registered source must receive number 1"

    # Register a new source — should receive next sequential number
    third = registry.register("DEF 14A 2024")
    assert third == 2, "Second unique source must receive number 2"

    # Registry must have exactly 2 unique entries
    assert len(registry) == 2, (
        "Registry must contain exactly 2 unique sources after registering 3 calls with 1 duplicate"
    )

    # all_sources must return ordered pairs
    sources = registry.all_sources
    assert sources == [(1, "10-K 2024"), (2, "DEF 14A 2024")], (
        f"all_sources must return [(1, '10-K 2024'), (2, 'DEF 14A 2024')], got {sources}"
    )


# ---------------------------------------------------------------------------
# Test 8: Sources appendix renders with at least 1 footnote anchor
# ---------------------------------------------------------------------------


def test_sources_appendix_renders() -> None:
    """Sources appendix must render with numbered anchors when filing documents exist."""
    from do_uw.models.state import AcquiredData

    state = _make_minimal_state()

    # Add filing documents so FootnoteRegistry gets populated
    state.acquired_data = AcquiredData()
    state.acquired_data.filing_documents = {
        "SEC_10K": [
            {"filing_date": "2024-02-23", "accession_number": "0000320193-24-000006"},
        ]
    }

    html = _render_html_string(state)

    assert '<section id="sources"' in html, (
        'Expected <section id="sources"> in rendered HTML when filing documents exist'
    )
    assert '<li id="fn-' in html, 'Expected at least one <li id="fn-N"> anchor in Sources appendix'


# ---------------------------------------------------------------------------
# Test 9: Print CSS hides sidebar
# ---------------------------------------------------------------------------


def test_sidebar_print_css() -> None:
    """sidebar.css @media print block must hide the sidebar-toc."""
    css_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "do_uw"
        / "templates"
        / "html"
        / "sidebar.css"
    )
    assert css_path.exists(), f"sidebar.css not found at {css_path}"
    css_content = css_path.read_text(encoding="utf-8")

    # @media print block must be present
    assert "@media print" in css_content, "Expected '@media print' block in sidebar.css"

    # sidebar-toc must be hidden inside @media print
    media_print_start = css_content.find("@media print")
    assert media_print_start >= 0

    media_print_block = css_content[media_print_start:]
    assert "sidebar-toc" in media_print_block, (
        "Expected 'sidebar-toc' inside @media print block in sidebar.css"
    )
    assert "display: none" in media_print_block, (
        "Expected 'display: none' inside @media print block for sidebar-toc"
    )


# ---------------------------------------------------------------------------
# Test 10: data_row macro CSS classes appear in rendered HTML
# ---------------------------------------------------------------------------


def test_data_row_macro_in_render() -> None:
    """HTML output must include dr-label, dr-value, and dr-context CSS classes.

    Confirms the data_row macro (3-column CapIQ data grid) is wired
    into the rendered output.
    """
    state = _make_minimal_state()
    html = _render_html_string(state)

    assert "dr-label" in html, (
        "Expected 'dr-label' CSS class in rendered HTML — data_row macro 3-column grid"
    )
    assert "dr-value" in html, (
        "Expected 'dr-value' CSS class in rendered HTML — data_row macro 3-column grid"
    )
    assert "dr-context" in html, (
        "Expected 'dr-context' CSS class in rendered HTML — data_row macro 3-column grid"
    )


# ---------------------------------------------------------------------------
# Test 11: Collapsible sections present (Phase 59-01)
# ---------------------------------------------------------------------------


def test_collapsible_sections_present() -> None:
    """Each major section rendered in the worksheet must contain a collapsible details element.

    Note: Phase 122-02 renamed company-profile to company-operations and it is now
    rendered as part of the manifest-driven analysis layer.
    """
    state = _make_minimal_state()
    html = _render_html_string(state)

    # Phase 122-02: ai-risk absorbed into scoring, company-operations added
    collapsible_section_ids = [
        "company-operations",
        "financial-health",
        "market",
        "governance",
        "litigation",
        "scoring",
    ]
    for section_id in collapsible_section_ids:
        # Use '<section id=' to match actual HTML elements, not CSS selectors
        section_start = html.find(f'<section id="{section_id}"')
        assert section_start >= 0, f"Section '{section_id}' not found in rendered HTML"

        # Find the next section boundary or end of document
        next_section = len(html)
        for other_id in collapsible_section_ids:
            if other_id == section_id:
                continue
            pos = html.find(f'<section id="{other_id}"', section_start + 1)
            if pos > section_start and pos < next_section:
                next_section = pos

        section_html = html[section_start:next_section]
        assert '<details class="collapsible"' in section_html, (
            f"Section '{section_id}' must contain a <details class=\"collapsible\"> element"
        )


# ---------------------------------------------------------------------------
# Test 12: Collapsible sections open by default (Phase 59-01)
# ---------------------------------------------------------------------------


def test_collapsible_sections_open_by_default() -> None:
    """Each major section's collapsible details must have the 'open' attribute."""
    state = _make_minimal_state()
    html = _render_html_string(state)

    # Phase 122-02: ai-risk absorbed into scoring, company-operations added
    collapsible_section_ids = [
        "company-operations",
        "financial-health",
        "market",
        "governance",
        "litigation",
        "scoring",
    ]
    for section_id in collapsible_section_ids:
        # Use '<section id=' to match actual HTML elements, not CSS selectors
        section_start = html.find(f'<section id="{section_id}"')
        assert section_start >= 0, f"Section '{section_id}' not found"

        next_section = len(html)
        for other_id in collapsible_section_ids:
            if other_id == section_id:
                continue
            pos = html.find(f'<section id="{other_id}"', section_start + 1)
            if pos > section_start and pos < next_section:
                next_section = pos

        section_html = html[section_start:next_section]
        assert '<details class="collapsible" open>' in section_html, (
            f"Section '{section_id}' collapsible details must have 'open' attribute"
        )


# ---------------------------------------------------------------------------
# Test 13: Executive summary NOT collapsible (Phase 59-01)
# ---------------------------------------------------------------------------


def test_executive_summary_not_collapsible() -> None:
    """Executive summary section must NOT contain a collapsible details element."""
    state = _make_minimal_state()
    html = _render_html_string(state)

    exec_start = html.find('id="executive-summary"')
    assert exec_start >= 0, "Executive summary section not found"

    # Find the next section after executive-summary
    next_sections = [
        html.find('id="red-flags"', exec_start),
        html.find('id="company-operations"', exec_start),
        html.find('id="financial-health"', exec_start),
    ]
    next_section = min(p for p in next_sections if p > exec_start)

    exec_html = html[exec_start:next_section]
    assert '<details class="collapsible"' not in exec_html, (
        "Executive summary must NOT contain a collapsible details element"
    )


# ---------------------------------------------------------------------------
# Test 14: Print CSS expands collapsible details (Phase 59-02)
# ---------------------------------------------------------------------------


def test_print_css_expands_details() -> None:
    """Print CSS must force collapsible details open and hide summary elements."""
    css_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "do_uw"
        / "templates"
        / "html"
        / "components.css"
    )
    assert css_path.exists(), f"components.css not found at {css_path}"
    css_content = css_path.read_text(encoding="utf-8")

    # Must contain @media print block
    assert "@media print" in css_content, "Expected '@media print' block in components.css"

    # Find the print block content
    media_print_start = css_content.find("@media print")
    media_print_block = css_content[media_print_start:]

    # Summary must be hidden in print
    assert "details.collapsible > summary" in media_print_block, (
        "Expected 'details.collapsible > summary' rule in @media print block"
    )
    assert "display: none" in media_print_block, (
        "Expected 'display: none' for summary in print"
    )


# ---------------------------------------------------------------------------
# Test 15: Section page breaks in print (Phase 59-02)
# ---------------------------------------------------------------------------


def test_section_page_breaks() -> None:
    """Print CSS must include page break rules for major sections using both modern and legacy properties."""
    css_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "src"
        / "do_uw"
        / "templates"
        / "html"
        / "components.css"
    )
    css_content = css_path.read_text(encoding="utf-8")

    media_print_start = css_content.find("@media print")
    media_print_block = css_content[media_print_start:]

    # Both modern and legacy page break properties must be present
    assert "break-before: page" in media_print_block, (
        "Expected 'break-before: page' (CSS Fragmentation L3) in print block"
    )
    assert "page-break-before: always" in media_print_block, (
        "Expected 'page-break-before: always' (CSS 2.1 legacy) in print block for Playwright compat"
    )

    # Key section IDs must have page break rules
    for section_id in ["financial-health", "governance", "litigation", "scoring"]:
        assert f'section[id="{section_id}"]' in media_print_block, (
            f"Expected page break rule for section[id=\"{section_id}\"] in print block"
        )


# ---------------------------------------------------------------------------
# Test 16: Two-column profile layout in rendered HTML (Phase 59-02)
# ---------------------------------------------------------------------------


def test_two_column_profile_layout() -> None:
    """Rendered HTML for a state with company data must contain two-col-profile class."""
    state = _make_minimal_state()
    html = _render_html_string(state)

    assert "two-col-profile" in html, (
        "Expected 'two-col-profile' CSS class in rendered HTML for company profile two-column layout"
    )
    assert "profile-col" in html, (
        "Expected 'profile-col' class for grid children in two-column layout"
    )
