---
phase: 59-html-visual-polish
plan: 02
subsystem: ui
tags: [css, jinja2, html, grid-layout, print-stylesheet, badges, two-column]

requires:
  - phase: 59-html-visual-polish
    plan: 01
    provides: components.css split file, collapsible sections, paired_kv_table macro

provides:
  - Two-column company profile layout (Size Metrics | Classification)
  - badge-pill and badge-tier CSS classes with hover transitions
  - Comprehensive print stylesheet with section page breaks and collapsible expansion
  - Consolidated print CSS (removed duplicated inline styles from base.html.j2)

affects: [63-interactive-charts, 64-pdf-enhancement, 60-word-adapter]

tech-stack:
  added: []
  patterns:
    - "Two-column grid: .two-col-profile with .profile-col children, responsive stacking at 768px"
    - "Badge CSS classes: .badge-pill for traffic lights, .badge-tier for tier badges (replaces inline Tailwind)"
    - "Print page breaks: both break-before:page (modern) and page-break-before:always (legacy) for Playwright compat"
    - "Print collapsible: details.collapsible forced open, summary hidden via display:none!important"

key-files:
  created: []
  modified:
    - src/do_uw/templates/html/components.css
    - src/do_uw/templates/html/sections/executive/company_profile.html.j2
    - src/do_uw/templates/html/components/badges.html.j2
    - src/do_uw/templates/html/base.html.j2
    - tests/stages/render/test_html_layout.py
    - tests/stages/render/test_html_components.py

key-decisions:
  - "Consolidated all print CSS rules into components.css @media print block (removed duplicated inline block from base.html.j2, kept only 9pt font-size override)"
  - "Used CSS grid .two-col-profile for company profile layout instead of flexbox (better column alignment)"
  - "Classification panel shows SIC/GICS/NAICS/State/FY/FPI details in right column alongside Size Metrics"
  - "Print layout stacks two-column to single-column for readability"

patterns-established:
  - "Badge styling via CSS classes (.badge-pill, .badge-tier) instead of inline Tailwind utilities"
  - "Section page breaks use BOTH break-before and page-break-before for Playwright Chromium compatibility"
  - "Tests use '<section id=' prefix to match HTML elements, avoiding false matches in CSS selectors"

requirements-completed: [VIS-05, VIS-06, VIS-07]

duration: 7min
completed: 2026-03-02
---

# Phase 59 Plan 02: Two-Column Layout, Badge Refinements, and Print Stylesheet Summary

**CIQ-style two-column company profile with Size Metrics | Classification panels, consistent badge-pill/badge-tier hover classes, and professional print stylesheet with section page breaks**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-02T19:00:53Z
- **Completed:** 2026-03-02T19:07:40Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Restructured Company Profile to two-column grid: Size Metrics (spectrum bars) on left, Classification (SIC/GICS/NAICS/State/FY/FPI) on right
- Replaced inline Tailwind styling on all traffic_light (6 variants) and tier_badge (7 variants) macros with CSS classes (.badge-pill, .badge-tier) providing consistent hover states and transitions
- Built comprehensive print stylesheet: collapsible sections forced open, section page breaks with dual modern/legacy properties, hover effects disabled, two-column stacked to single-column
- Removed duplicated print CSS from base.html.j2 inline block (consolidated to components.css + styles.css as single sources of truth)
- Added 8 new tests (3 layout + 5 component); all 291 render tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Two-column company profile layout and refined risk badges** - `1cfebe0` (feat)
2. **Task 2: Print stylesheet enhancements and tests** - `053619b` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/components.css` - Added two-col-profile grid, badge-pill/badge-tier CSS, comprehensive print stylesheet (152 -> 253 lines)
- `src/do_uw/templates/html/sections/executive/company_profile.html.j2` - Restructured to two-column layout with Classification panel
- `src/do_uw/templates/html/components/badges.html.j2` - Replaced inline Tailwind with badge-pill and badge-tier CSS classes
- `src/do_uw/templates/html/base.html.j2` - Simplified inline print block to just 9pt font-size override
- `tests/stages/render/test_html_layout.py` - 3 new tests + fixed 3 fragile tests (section ID matching)
- `tests/stages/render/test_html_components.py` - 5 new tests for badge-pill and badge-tier classes

## Decisions Made
- Consolidated print CSS into components.css rather than leaving duplicated rules in base.html.j2 inline block. The inline block now has only the 9pt override (styles.css uses 10pt).
- Classification panel shows detailed SIC/GICS/NAICS codes plus State of Inc, FY End, and FPI status -- items that were in the paired_kv_table but now have dedicated space.
- Section page breaks use both `break-before: page` (CSS Fragmentation L3) and `page-break-before: always` (CSS 2.1 legacy) because Playwright's Chromium PDF renderer respects the legacy property more reliably.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed fragile section ID matching in 3 existing tests**
- **Found during:** Task 2 (test execution)
- **Issue:** test_section_order, test_collapsible_sections_present, and test_collapsible_sections_open_by_default used `html.find('id="..."')` which matched CSS selectors like `section[id="executive-summary"]` in the new print stylesheet before matching the actual `<section>` elements.
- **Fix:** Changed all three tests to search for `'<section id="..."'` instead of `'id="..."'` to match only HTML elements.
- **Files modified:** tests/stages/render/test_html_layout.py
- **Verification:** All 291 render tests pass
- **Committed in:** 053619b (Task 2 commit)

**2. [Rule 3 - Blocking] Consolidated duplicate sticky-header print rule**
- **Found during:** Task 2 (print CSS consolidation)
- **Issue:** The existing components.css had a standalone `@media print` block for sticky-header at line 25-29, which would duplicate with the new comprehensive print block.
- **Fix:** Removed the standalone block and included the rule in the consolidated `@media print` block at the bottom.
- **Files modified:** src/do_uw/templates/html/components.css
- **Verification:** CSS rule still present in consolidated block, all tests pass
- **Committed in:** 053619b (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for test correctness and CSS organization. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 59 (HTML Visual Polish) is now complete: VIS-01 through VIS-07 all satisfied
- CSS split pattern (components.css) established for Phase 63 (Interactive Charts) and Phase 64 (PDF Enhancement)
- Badge CSS classes available for any future badge additions
- Print stylesheet ready for Phase 64 PDF Enhancement to build upon
- All 291 render tests passing provides stable baseline

---
*Phase: 59-html-visual-polish*
*Completed: 2026-03-02*
