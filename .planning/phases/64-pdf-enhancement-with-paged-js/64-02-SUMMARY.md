---
phase: 64-pdf-enhancement-with-paged-js
plan: 02
subsystem: render
tags: [pdf, toc, details-expansion, image-optimization, playwright]

# Dependency graph
requires:
  - phase: 64-pdf-enhancement-with-paged-js
    provides: "CSS running headers/footers, pdf_mode context flag, _build_pdf_html()"
provides:
  - "Automatic PDF table of contents with leader-dot entries and clickable links"
  - "Details expansion for PDF (template script + Playwright evaluate)"
  - "_optimize_chart_images_for_pdf() for smaller PDF file size"
  - "TOC CSS with page-break-after for proper pagination"
affects: [66-mcp-final-qa, render, pdf]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Conditional TOC via pdf_mode Jinja2 block", "Belt-and-suspenders details expansion (template + Playwright)", "Pillow-based chart image optimization with graceful degradation"]

key-files:
  created:
    - tests/stages/render/test_pdf_toc.py
  modified:
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/components.css
    - src/do_uw/stages/render/html_renderer.py

key-decisions:
  - "TOC built via JavaScript in template (not server-side) -- section headings discovered dynamically at render time"
  - "Details expansion via both template script AND Playwright evaluate() for belt-and-suspenders reliability"
  - "Chart image optimization uses Pillow with graceful degradation (skip if unavailable)"
  - "TOC page numbers are structural placeholders -- actual page numbers require Paged.js JS polyfill which we deliberately avoided"
  - "TOC div only exists in HTML when pdf_mode=True, so browser HTML is completely unaffected"

patterns-established:
  - "PDF TOC generation via JavaScript scanning section[id] > h2 headings"
  - "Chart image size reduction pattern: resize > 800px width, re-encode with PNG optimize flag"
  - "Graceful degradation: optional dependency (Pillow) wrapped in try/except ImportError"

requirements-completed: [PDF-03, PDF-06, PDF-07]

# Metrics
duration: 6min
completed: 2026-03-03
---

# Phase 64 Plan 02: PDF TOC, Details Expansion, and File Size Optimization Summary

**Automatic PDF table of contents with leader-dot links, universal details expansion, and Pillow-based chart image optimization for sub-5MB PDFs**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-03T04:08:38Z
- **Completed:** 2026-03-03T04:14:27Z
- **Tasks:** 2
- **Files modified:** 4 (+ 1 created)

## Accomplishments
- Added conditional PDF TOC in base.html.j2 that renders only when pdf_mode=True, with leader dots and clickable anchor links to all section headings
- Implemented belt-and-suspenders details expansion: JavaScript in template + Playwright evaluate() ensures all collapsible sections are open in PDF
- Created _optimize_chart_images_for_pdf() function that resizes charts >800px and re-encodes with PNG optimize flag, with graceful Pillow degradation
- Added 18 comprehensive tests covering TOC conditional rendering, details expansion, chart optimization, CSS styling, and file size estimation

## Task Commits

Each task was committed atomically:

1. **Task 1: Add TOC generation and details expansion for PDF mode** - `ef90629` (feat)
2. **Task 2: Optimize PDF file size and add comprehensive tests** - `50294ee` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/base.html.j2` - Added conditional TOC div and PDF preparation script (details expansion + TOC building)
- `src/do_uw/templates/html/components.css` - Added TOC CSS (leader dots, page-break-after) and chart-figure print constraint
- `src/do_uw/stages/render/html_renderer.py` - Added _optimize_chart_images_for_pdf(), integrated into _build_pdf_html(), added Playwright details expansion
- `tests/stages/render/test_pdf_toc.py` - 18 tests for TOC, details, optimization, CSS, file size

## Decisions Made
- TOC is built via JavaScript at render time (not server-side in Python) because the template already knows all section IDs and this approach works with any section configuration without code changes.
- Page number placeholders are structural (data-toc-for attributes) but not populated -- actual page numbers would require the Paged.js JavaScript polyfill which was deliberately excluded in 64-01 (CSS-only approach).
- Details expansion uses dual approach: template script runs during initial page load, then Playwright evaluate() runs again before PDF printing, ensuring reliability regardless of script execution timing.
- Chart optimization gracefully degrades when Pillow is unavailable (returns original images unchanged).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Test assertions for "pdf-toc" and "Table of Contents" in browser-mode HTML failed initially because CSS class definitions and comments containing those strings are always present in the inlined stylesheet. Fixed by asserting on actual HTML element markers (id="pdf-toc", h2 tag) instead of generic string presence.
- html_renderer.py reached 522 lines (over 500-line limit) due to the optimization function addition combined with concurrent SVG chart code from Phase 63. Logged to deferred-items.md for future extraction.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 64 (PDF Enhancement) is now complete with all 7 requirements addressed (PDF-01 through PDF-07)
- PDF output has: running headers/footers, TOC with links, page breaks, details expansion, chart optimization
- Ready for Phase 66 final QA validation

## Self-Check: PASSED

- All 4 modified/created files verified on disk
- Commits ef90629 and 50294ee found in git log
- 27 PDF tests pass (9 existing + 18 new)
- 350 total render tests pass (no regressions)

---
*Phase: 64-pdf-enhancement-with-paged-js*
*Completed: 2026-03-03*
