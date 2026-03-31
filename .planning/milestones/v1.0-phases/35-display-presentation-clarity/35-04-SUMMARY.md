---
phase: 35-display-presentation-clarity
plan: 04
subsystem: render, templates
tags: [html, jinja2, tailwind, bloomberg, css, component-macros, design-system]

# Dependency graph
requires:
  - phase: 35-display-presentation-clarity
    provides: "DensityLevel enum and SectionDensity model for conditional rendering"
provides:
  - "base.html.j2 with Tailwind CSS v4 CDN, Bloomberg color config, header/footer, print styles"
  - "5 component macro files: badges, tables, callouts, charts, narratives"
  - "Bloomberg-quality CSS with Navy #0B1D3A / Gold #D4A843 palette"
  - "html_* color constants on DesignSystem for single source of truth"
  - "33 tests validating all component macros via Jinja2 rendering"
affects: [35-05, 35-06, 35-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Jinja2 macro component library: import macros in base template, use in section templates"
    - "Tailwind CSS v4 CDN with custom config for Bloomberg palette"
    - "CSS variables (--do-*) for consistent theming between Tailwind and custom CSS"
    - "html_* color constants on frozen DesignSystem dataclass for HTML/PDF pipeline"

key-files:
  created:
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/components/badges.html.j2
    - src/do_uw/templates/html/components/tables.html.j2
    - src/do_uw/templates/html/components/callouts.html.j2
    - src/do_uw/templates/html/components/charts.html.j2
    - src/do_uw/templates/html/components/narratives.html.j2
    - src/do_uw/templates/html/styles.css
    - tests/stages/render/test_html_components.py
  modified:
    - src/do_uw/stages/render/design_system.py

key-decisions:
  - "Tailwind CSS v4 CDN via script tag (not build step) -- works in Playwright Chromium for PDF generation"
  - "CSS variables (--do-navy, --do-gold, etc.) supplement Tailwind for custom Bloomberg styling"
  - "Bloomberg palette: Navy #0B1D3A, Gold #D4A843, Risk Red #B91C1C, Positive Blue #1D4ED8 (NO green)"
  - "DesignSystem html_* fields as single source of truth for HTML/PDF colors (separate from python-docx RGBColor fields)"
  - "KV tables get lighter header (slate-100) vs data tables (navy) for visual hierarchy"
  - "Confidence marker only renders for LOW (MEDIUM/HIGH invisible per user decision)"
  - "Discovery boxes use gold border/background (distinct from amber warning boxes)"

patterns-established:
  - "Component macro pattern: {% from 'components/X.html.j2' import macro_name %} in base.html.j2"
  - "Badge macro pattern: status string -> CSS class mapping via Jinja2 conditionals"
  - "Conditional cell formatting: direction + threshold_pct drives risk coloring"
  - "Test pattern: Jinja2 Environment renders macros directly, assert on CSS classes in output"

requirements-completed: [VIS-04, VIS-05, SECT1-01]

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 35 Plan 04: Bloomberg HTML Template Foundation Summary

**Jinja2 component library with base layout, 5 macro files (badges/tables/callouts/charts/narratives), Bloomberg CSS, and DesignSystem HTML color palette**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T14:56:26Z
- **Completed:** 2026-02-21T15:01:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Created base.html.j2 with Tailwind CSS v4 CDN, custom Bloomberg color config, header/footer layout, and print styles
- Built 5 reusable Jinja2 component macro files: badges (traffic_light, density_indicator, confidence_marker, tier_badge), tables (data_table, kv_table, multi_column_grid, conditional_cell, financial_row), callouts (discovery_box, warning_box, do_context, gap_notice), charts (embed_chart), narratives (section_narrative, evidence_chain)
- Created 243-line Bloomberg CSS with color variables, financial table styling, risk coloring classes, and print media queries
- Extended DesignSystem with 7 html_* color constants matching CSS variables
- 33 tests covering all macro components via Jinja2 rendering plus DesignSystem/CSS consistency checks

## Task Commits

Each task was committed atomically:

1. **Task 1: Create base HTML template and component macros** - `5ecf403` (feat)
2. **Task 2: Create Bloomberg CSS and extend design system** - `d0210e7` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/base.html.j2` - Base layout with Tailwind CDN, header, footer, print styles, macro imports
- `src/do_uw/templates/html/components/badges.html.j2` - Traffic light, density, confidence, tier badge macros (86 lines)
- `src/do_uw/templates/html/components/tables.html.j2` - Data table, KV table, grid, conditional cell, financial row macros (155 lines)
- `src/do_uw/templates/html/components/callouts.html.j2` - Discovery box, warning box, D&O context, gap notice macros (58 lines)
- `src/do_uw/templates/html/components/charts.html.j2` - Chart embedding with base64 PNG and fallback (30 lines)
- `src/do_uw/templates/html/components/narratives.html.j2` - Section narrative with AI label, evidence chain macros (44 lines)
- `src/do_uw/templates/html/styles.css` - Bloomberg CSS with color variables, financial tables, risk coloring, print styles (243 lines)
- `src/do_uw/stages/render/design_system.py` - Added html_navy, html_gold, html_risk_red, html_caution_amber, html_positive_blue, html_neutral_gray, html_bg_alt
- `tests/stages/render/test_html_components.py` - 33 tests across 12 test classes

## Decisions Made
- Tailwind CSS v4 CDN via script tag (not build step) -- works in Playwright Chromium for PDF generation per research
- CSS custom properties (--do-*) used alongside Tailwind utility classes for consistent theming
- Bloomberg palette: Navy #0B1D3A (primary), Gold #D4A843 (accent), Risk Red #B91C1C, Positive Blue #1D4ED8 (NOT green per existing design system convention)
- DesignSystem html_* fields provide single source of truth for HTML/PDF colors; do not affect python-docx Word rendering which uses RGBColor
- KV tables use lighter header background (slate-100) vs data tables (navy) for visual hierarchy differentiation
- Confidence markers only visible for LOW confidence per user decision -- MEDIUM/HIGH render nothing
- Discovery boxes styled with gold border/background to visually distinguish from amber warning boxes
- Print styles use letter page size with 0.75in/0.65in margins matching existing PDF styles.css

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Complete HTML component library ready for Plan 05 (section-specific templates)
- All macros importable via standard Jinja2 `{% from %}` pattern
- Base template provides content block for section injection
- DesignSystem html_* colors available for any Python-side color references
- 33 tests provide regression coverage for all components

## Self-Check: PASSED

All 9 created/modified files verified on disk. Both task commits (5ecf403, d0210e7) verified in git log.

---
*Phase: 35-display-presentation-clarity*
*Completed: 2026-02-21*
