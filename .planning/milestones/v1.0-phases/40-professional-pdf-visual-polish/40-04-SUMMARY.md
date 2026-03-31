---
phase: 40-professional-pdf-visual-polish
plan: 04
subsystem: render
tags: [charts, matplotlib, jinja2, pdf, figure-captions, color-theme, enum-humanization, markdown-stripping]

# Dependency graph
requires:
  - phase: 40-01
    provides: Pre-compiled Tailwind CSS with zero-CDN PDF rendering pipeline
provides:
  - CREDIT_REPORT_LIGHT color palette for white-background PDF charts
  - Figure caption system with numbered captions for all 5 charts
  - Parameterized chart color API across all 4 chart generators
  - Ownership and timeline chart generation wired into render pipeline
  - humanize and strip_md Jinja2 filters for clean enum/narrative display
affects: [40-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Chart color parameterization: all chart generators accept optional colors dict, defaulting to BLOOMBERG_DARK"
    - "embed_chart macro reads chart_images from Jinja2 context (with context import)"
    - "humanize_enum filter on all template enum values"
    - "strip_md filter on narrative text to remove markdown artifacts"

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/design_system.py
    - src/do_uw/stages/render/__init__.py
    - src/do_uw/stages/render/charts/stock_charts.py
    - src/do_uw/stages/render/charts/radar_chart.py
    - src/do_uw/stages/render/charts/ownership_chart.py
    - src/do_uw/stages/render/charts/timeline_chart.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/components/charts.html.j2
    - src/do_uw/templates/html/components/narratives.html.j2
    - src/do_uw/templates/html/sections/market.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/html/sections/litigation.html.j2
    - src/do_uw/templates/html/sections/executive.html.j2
    - src/do_uw/templates/html/sections/company.html.j2
    - tests/stages/render/test_html_components.py

key-decisions:
  - "Chart generators accept colors dict parameter defaulting to BLOOMBERG_DARK; CREDIT_REPORT_LIGHT passed for PDF"
  - "embed_chart macro uses 'with context' import to access chart_images from template context rather than positional parameter"
  - "Radar chart uses brand navy/gold colors on both themes (work on white and dark backgrounds); only text/grid colors adapt"
  - "Ownership and timeline chart generation added to _generate_chart_images pipeline (were expected by loader but not generated)"
  - "narratives macro also imported 'with context' to enable strip_md filter access"

patterns-established:
  - "Color parameterization: chart_func(state, ds, colors=None) pattern for theme switching"
  - "Figure numbering: embed_chart(name, caption, figure_num=N) with sequential numbering across sections"

requirements-completed: []

# Metrics
duration: 12min
completed: 2026-02-22
---

# Phase 40 Plan 04: Charts, Badges, and Display Polish Summary

**Light-themed chart colors for PDF, figure captions on all 5 charts, parameterized chart color API, enum humanization, and markdown stripping across all templates**

## Performance

- **Duration:** 12 min
- **Started:** 2026-02-22T02:43:21Z
- **Completed:** 2026-02-22T02:55:11Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments
- Added CREDIT_REPORT_LIGHT color palette and parameterized all 4 chart generators (stock, radar, ownership, timeline) to accept colors dict
- Implemented figure caption system with "Figure N: caption" numbering across all 5 chart embeds (stock 1Y, stock 5Y, ownership, radar, timeline)
- Wired ownership and timeline chart generation into the render pipeline (were expected by chart loader but never generated)
- Registered humanize and strip_md Jinja2 filters; applied humanize to risk_type, market_cap_tier, severity, risk_level, do_relevance across 5 templates
- Applied strip_md to narrative macro to automatically strip bold/italic/header markdown artifacts from LLM-generated text

## Task Commits

Each task was committed atomically:

1. **Task 1: Add light-themed chart colors and figure caption system** - `a8d94d0` (feat)
2. **Task 2: Risk indicator pills, enum humanization, and markdown stripping** - `709b3fd` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/design_system.py` - Added CREDIT_REPORT_LIGHT color palette dict
- `src/do_uw/stages/render/__init__.py` - Added light_theme param, ownership/timeline chart generation
- `src/do_uw/stages/render/charts/stock_charts.py` - Parameterized all ~30 BLOOMBERG_DARK refs to colors dict
- `src/do_uw/stages/render/charts/radar_chart.py` - Added colors param, parameterized text/grid colors
- `src/do_uw/stages/render/charts/ownership_chart.py` - Added colors param for text/bg/grid theming
- `src/do_uw/stages/render/charts/timeline_chart.py` - Added colors param for text/grid/spine theming
- `src/do_uw/stages/render/html_renderer.py` - Added strip_markdown function, registered humanize/strip_md filters
- `src/do_uw/templates/html/base.html.j2` - Added 'with context' to embed_chart and narratives imports
- `src/do_uw/templates/html/components/charts.html.j2` - New embed_chart macro with figure caption system
- `src/do_uw/templates/html/components/narratives.html.j2` - Applied strip_md filter to narrative text output
- `src/do_uw/templates/html/sections/market.html.j2` - Updated embed_chart calls with figure_num 1-3
- `src/do_uw/templates/html/sections/scoring.html.j2` - Updated embed_chart + humanize on risk_type/severity
- `src/do_uw/templates/html/sections/litigation.html.j2` - Updated embed_chart with figure_num=5
- `src/do_uw/templates/html/sections/executive.html.j2` - Humanize on market_cap_tier
- `src/do_uw/templates/html/sections/company.html.j2` - Humanize on market_cap_tier, severity, do_relevance
- `tests/stages/render/test_html_components.py` - Updated embed_chart tests for new macro signature, added filter registrations

## Decisions Made
- Chart generators accept `colors` dict parameter, defaulting to BLOOMBERG_DARK for HTML dashboard and CREDIT_REPORT_LIGHT for PDF -- this keeps dark charts in the browser dashboard while producing white-background charts for PDF
- The embed_chart macro uses Jinja2 `with context` import to read chart_images from template context rather than receiving it as a positional parameter, matching how other context variables (densities, narratives) are accessed
- The radar chart keeps brand navy (#1A1446) and gold (#FFD000) on both light and dark themes since these work on white backgrounds; only text, grid, and background colors adapt to the theme
- Ownership and timeline chart generation were added to _generate_chart_images because the chart loader already expected ownership.png and timeline.png but they were never actually generated
- The narrative macro import was also changed to `with context` to enable strip_md filter access

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test fixture for new embed_chart signature**
- **Found during:** Task 1 (embed_chart macro update)
- **Issue:** test_html_components.py test_embed_chart_with_data used old macro signature (charts_dict positional arg, alt_text kwarg)
- **Fix:** Updated tests to use new signature and added chart_images via render() context
- **Files modified:** tests/stages/render/test_html_components.py
- **Committed in:** a8d94d0 (Task 1 commit)

**2. [Rule 3 - Blocking] Added 'with context' to Jinja2 macro imports**
- **Found during:** Task 1 (embed_chart macro update)
- **Issue:** Jinja2 macros imported via `from ... import` don't have access to template variables by default; chart_images context variable was not accessible in the macro
- **Fix:** Added `with context` to both embed_chart and narratives macro imports in base.html.j2
- **Committed in:** a8d94d0 (Task 1) and 709b3fd (Task 2)

**3. [Rule 3 - Blocking] Registered custom filters in test fixture**
- **Found during:** Task 2 (strip_md filter in narratives macro)
- **Issue:** test_html_components.py created its own jinja2.Environment without custom filters; narratives macro using strip_md filter caused TemplateRuntimeError
- **Fix:** Added strip_md, humanize, and format_na filter registrations to test fixture
- **Files modified:** tests/stages/render/test_html_components.py
- **Committed in:** 709b3fd (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (3 blocking issues)
**Impact on plan:** All auto-fixes necessary for correct template rendering and test passing. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 charts now generate with light-themed colors for PDF output
- Chart figure captions provide professional numbered references (Figure 1-5)
- Enum values display as title case throughout all templates
- Markdown artifacts stripped from LLM narrative text
- 186 render tests pass; ready for Plan 40-05

## Self-Check: PASSED

All 16 modified files verified present. Both task commits (a8d94d0, 709b3fd) verified in git log.

---
*Phase: 40-professional-pdf-visual-polish*
*Completed: 2026-02-22*
