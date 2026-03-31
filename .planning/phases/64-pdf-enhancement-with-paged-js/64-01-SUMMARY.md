---
phase: 64-pdf-enhancement-with-paged-js
plan: 01
subsystem: render
tags: [paged-js, css-paged-media, pdf, playwright, running-headers, page-breaks]

# Dependency graph
requires:
  - phase: 59-html-visual-polish
    provides: "HTML template structure and CSS framework for PDF rendering"
provides:
  - "CSS-driven running headers/footers for PDF output"
  - "pdf_mode context flag for conditional PDF rendering"
  - "_build_pdf_html() function for PDF-specific HTML generation"
  - "Table break-inside:avoid rules for PDF page breaks"
  - "Chart interactive/static CSS toggle for print mode"
affects: [64-02-PLAN, render, pdf]

# Tech tracking
tech-stack:
  added: []
  patterns: ["CSS position:fixed for print headers/footers", "pdf_mode context flag for conditional rendering", "@page CSS rules with first-page override"]

key-files:
  created:
    - tests/stages/render/test_pdf_paged.py
  modified:
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/styles.css
    - src/do_uw/templates/html/components.css
    - src/do_uw/stages/render/html_renderer.py

key-decisions:
  - "CSS-only approach (no Paged.js JS library) -- uses position:fixed elements that Chromium prints on every page"
  - "Playwright footer_template retained for Page N of M (CSS page counters unreliable without JS polyfill)"
  - "pdf_mode=False default in build_html_context, set True only by _build_pdf_html for PDF rendering"
  - "Browser HTML saved separately (pdf_mode=False) alongside PDF HTML (pdf_mode=True) for debugging"

patterns-established:
  - "pdf_mode context flag: Templates can conditionally render PDF-specific elements"
  - "CSS print header/footer: position:fixed elements with display:none default, shown only in @media print"
  - "Chart static/interactive toggle: .chart-interactive hidden, .chart-static shown in @media print"

requirements-completed: [PDF-01, PDF-02, PDF-04, PDF-05]

# Metrics
duration: 5min
completed: 2026-03-03
---

# Phase 64 Plan 01: Paged.js CSS Integration Summary

**CSS-driven running headers/footers, table page-break controls, and chart static mode for professional PDF output via Playwright**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-03T02:55:36Z
- **Completed:** 2026-03-03T03:00:36Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- Added CSS running header (company name + date) and footer (confidential notice) that appear on every printed page via position:fixed
- Enhanced @page rules with expanded margins for header/footer space and first-page override for cover
- Added table break-inside:avoid rules preventing tables from splitting across PDF pages
- Added chart-interactive/chart-static CSS toggle hiding JS charts and showing static PNGs in print
- Created _build_pdf_html() function with pdf_mode context flag for PDF-specific HTML generation
- Updated Playwright PDF path with simplified header_template and retained footer for page numbers
- 9 unit tests covering all PDF CSS integration points

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Paged.js CSS and running header/footer definitions** - `d607d2f` (feat)
2. **Task 2: Update html_renderer.py Playwright PDF path** - `d062ed6` (feat)
3. **Task 3: Add tests for PDF Paged.js integration** - `13772eb` (test)

## Files Created/Modified
- `src/do_uw/templates/html/base.html.j2` - Added pdf-running-header and pdf-running-footer HTML elements
- `src/do_uw/templates/html/styles.css` - Enhanced @page rules, added running header/footer CSS
- `src/do_uw/templates/html/components.css` - Table break-avoidance, chart toggle rules in print
- `src/do_uw/stages/render/html_renderer.py` - pdf_mode flag, _build_pdf_html(), updated Playwright options
- `tests/stages/render/test_pdf_paged.py` - 9 tests for PDF CSS integration

## Decisions Made
- CSS-only approach: No Paged.js JavaScript library (500KB+). Instead, CSS position:fixed elements that Chromium renders on every printed page provide the same visual result without the dependency.
- Retained Playwright footer_template for Page N of M numbering since CSS page counters require the Paged.js JS polyfill to work reliably.
- pdf_mode defaults to False in build_html_context so browser HTML is completely unaffected. Only _build_pdf_html sets it True.
- Browser-view HTML and PDF-specific HTML both saved for debugging: the .html review file uses pdf_mode=False while Playwright renders with pdf_mode=True.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing test failures discovered in test_render_integration.py and test_section_renderer.py (DensityLevel attribute error in sect6_litigation.py, missing readability attribute in scoring.md.j2). Confirmed these exist before this plan's changes. Logged to deferred-items.md.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- PDF running headers/footers active via CSS -- Plan 64-02 can build on this for section-aware headers
- pdf_mode flag available for any future PDF-specific template conditionals
- Chart static mode CSS ready -- Plan 64-02 can implement actual chart PNG generation pipeline

---
*Phase: 64-pdf-enhancement-with-paged-js*
*Completed: 2026-03-03*
