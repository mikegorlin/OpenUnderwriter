---
phase: 40-professional-pdf-visual-polish
plan: 02
subsystem: render
tags: [cover-page, pdf, playwright, header, footer, page-breaks, branding]

# Dependency graph
requires:
  - phase: 40-professional-pdf-visual-polish
    provides: Pre-compiled Tailwind CSS with zero-CDN rendering (Plan 01)
provides:
  - Branded cover page template with company identity, risk tier, and Angry Dolphin branding
  - Playwright PDF header "CONFIDENTIAL -- [Company] D&O Worksheet" on every page
  - Playwright PDF footer "Angry Dolphin Underwriting System | Page X of Y | [Date]" on every page
  - Conditional page breaks preventing blank pages for sparse sections
  - Print CSS heading orphan protection and table break avoidance
affects: [40-03, 40-04, 40-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [cover page break-after pattern, conditional page break on content presence, no-print class for PDF-hidden in-document elements]

key-files:
  created:
    - src/do_uw/templates/html/sections/cover.html.j2
  modified:
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/templates/html/styles.css
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/sections/ai_risk.html.j2
    - src/do_uw/stages/render/html_renderer.py

key-decisions:
  - "Cover page uses flexbox centering with break-after: page for guaranteed page separation"
  - "In-document header/footer hidden via no-print class in PDF (Playwright templates handle PDF header/footer)"
  - "AI risk section gets conditional page break -- only when overall_score or dimensions data present"
  - "Header/footer changes already committed in 40-03; Task 2 focuses on base template and CSS"

patterns-established:
  - "Cover page pattern: full-viewport flex container with break-after for S&P-style branded first page"
  - "Conditional page break pattern: Jinja2 conditional class application based on data presence"

requirements-completed: []

# Metrics
duration: 4min
completed: 2026-02-22
---

# Phase 40 Plan 02: Cover Page & Page Layout Summary

**Branded cover page with company name, risk tier badge, and Angry Dolphin branding; per-page CONFIDENTIAL header and branded footer via Playwright; conditional page breaks to eliminate blank pages**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-22T02:43:11Z
- **Completed:** 2026-02-22T02:47:21Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Created full-page branded cover in S&P/Moody's credit report style with company name, ticker, risk tier badge, quality/composite scores, date, and Angry Dolphin branding
- Updated Playwright PDF rendering with company-specific header ("CONFIDENTIAL -- [Company] D&O Worksheet") and branded footer ("Angry Dolphin Underwriting System | Page X of Y | [Date]")
- Added conditional page break on AI risk section to prevent blank pages when section has no data
- Hidden in-document header/footer from PDF output via no-print class (Playwright templates handle PDF)
- Added print CSS heading orphan protection (h2/h3 break-after: avoid) and table break rules

## Task Commits

Each task was committed atomically:

1. **Task 1: Create branded cover page template** - `3d4c1e1` (feat)
2. **Task 2: Update headers, footers, and conditional page breaks** - `0b6a78e` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/sections/cover.html.j2` - Full-page branded cover with company identity, tier badge, scores, and Angry Dolphin branding
- `src/do_uw/templates/html/worksheet.html.j2` - Added cover.html.j2 as first included section
- `src/do_uw/templates/html/styles.css` - Cover page CSS (flexbox centering, break-after), print heading protection, page-break-inside-avoid
- `src/do_uw/templates/html/base.html.j2` - Added no-print class to header and footer for PDF exclusion
- `src/do_uw/templates/html/sections/ai_risk.html.j2` - Conditional page-break class based on data presence
- `src/do_uw/stages/render/html_renderer.py` - Header/footer with company name and generation date (changes landed in 40-03 commit)

## Decisions Made
- Cover page uses `min-height: 100vh` flexbox with `break-after: page` for guaranteed page separation -- executive summary naturally starts on page 2
- In-document header and footer get `no-print` class rather than being removed, preserving them for the HTML dashboard view while hiding from PDF
- AI risk section uses conditional page break (`{% if ai.get('overall_score') is not none or ai.get('dimensions') %}`) to prevent blank pages when the section has no substantive data
- The `html_renderer.py` header/footer changes (company name in CONFIDENTIAL header, Angry Dolphin in footer) were already committed as part of 40-03; Task 2 focuses on the template and CSS changes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] html_renderer.py changes already in 40-03 commit**
- **Found during:** Task 2 (header/footer update)
- **Issue:** The header_template and footer_template changes to html_renderer.py were already committed in the 40-03 plan commit (a9c2c1f)
- **Fix:** No duplicate commit needed; verified changes present, committed only the remaining base template and CSS changes
- **Files affected:** src/do_uw/stages/render/html_renderer.py (already committed)
- **Verification:** grep confirmed CONFIDENTIAL and Angry Dolphin present in html_renderer.py

---

**Total deviations:** 1 (overlap with prior plan commit -- no code impact)
**Impact on plan:** All intended changes are in the repo. The header/footer logic arrived via 40-03 rather than 40-02.

## Issues Encountered
- 6 pre-existing test failures from Plan 40-03 changes (TestEmbedChart alt_text parameter, stock chart overlay args, backward compat exports) -- not caused by this plan's changes; 178 render tests pass

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Cover page renders as first page of PDF with full branding
- Headers and footers use company name and Angry Dolphin branding per LOCKED decisions
- Conditional page breaks prevent blank pages for sparse sections
- Plans 03-05 can build on the page structure established here

## Self-Check: PASSED

All created files verified present. Both task commits (3d4c1e1, 0b6a78e) verified in git log.

---
*Phase: 40-professional-pdf-visual-polish*
*Completed: 2026-02-22*
