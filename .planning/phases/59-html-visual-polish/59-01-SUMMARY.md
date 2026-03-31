---
phase: 59-html-visual-polish
plan: 01
subsystem: ui
tags: [css, jinja2, html, layout, collapsible, sticky-headers, tabular-nums]

requires:
  - phase: 58-shared-context-layer
    provides: context_builders package for shared extract_* functions

provides:
  - paired_kv_table macro for CIQ-density 4-column KV layouts
  - components.css split file for component-level CSS
  - Collapsible section wrappers with chevron animation
  - Sticky table headers on data_table macro
  - Global tabular-nums on all td elements

affects: [59-02-PLAN, 60-word-adapter, 63-interactive-charts, 64-pdf-enhancement]

tech-stack:
  added: []
  patterns:
    - "CSS file split: components.css loaded via inline <style> include (same as sidebar.css)"
    - "Collapsible sections: <details class='collapsible' open> with .collapsible-content wrapper"
    - "Paired KV table: 4-col layout via paired_kv_table macro (Label|Value|Label|Value)"
    - "Sticky headers: .sticky-header class on data_table, offset 44px for topbar"

key-files:
  created:
    - src/do_uw/templates/html/components.css
  modified:
    - src/do_uw/templates/html/components/tables.html.j2
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/styles.css
    - src/do_uw/templates/html/sections/executive/company_profile.html.j2
    - src/do_uw/templates/html/sections/identity.html.j2
    - src/do_uw/templates/html/sections/company.html.j2
    - src/do_uw/templates/html/sections/financial.html.j2
    - src/do_uw/templates/html/sections/market.html.j2
    - src/do_uw/templates/html/sections/governance.html.j2
    - src/do_uw/templates/html/sections/litigation.html.j2
    - src/do_uw/templates/html/sections/ai_risk.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/html/sections/scoring_hazard.html.j2
    - src/do_uw/templates/html/sections/scoring/hazard_profile.html.j2
    - tests/stages/render/test_html_layout.py
    - tests/stages/render/test_html_components.py

key-decisions:
  - "Moved data-grid and sources-appendix CSS from styles.css to components.css to bring styles.css under 500-line limit (was 568)"
  - "Removed dead Tailwind Supplement comment block from styles.css (zero active rules, migration note)"
  - "Print media query forces collapsible sections open and hides summary elements"
  - "company.html.j2 not tested in collapsible layout tests since it is not rendered in main worksheet (company profile is inside executive section)"

patterns-established:
  - "CSS split pattern: new component CSS goes in components.css, not styles.css"
  - "Collapsible wrapping: h2 + narrative stay visible, facet/legacy content goes in <details class='collapsible' open>"
  - "Sections NOT wrapped: Executive Summary, Red Flags, Identity (always fully visible)"

requirements-completed: [VIS-01, VIS-02, VIS-03, VIS-04]

duration: 11min
completed: 2026-03-02
---

# Phase 59 Plan 01: CIQ Layout Density Summary

**Paired-column KV tables, sticky table headers, global tabular-nums, and collapsible sections with CSS chevron indicators across all major worksheet sections**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-02T18:46:57Z
- **Completed:** 2026-03-02T18:58:00Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Created paired_kv_table macro for CIQ-density 4-column layout; deployed in Company Profile and Identity sections
- Split CSS into components.css (152 lines) with sticky headers, tabular-nums, data-grid, sources-appendix, and collapsible section styles; styles.css reduced from 568 to 487 lines
- Wrapped 7 section templates (company, financial, market, governance, litigation, ai_risk, scoring) in collapsible `<details>` with chevron rotation animation
- Added 7 new tests (3 layout + 4 component); all 283 render tests pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Create paired_kv_table macro, split CSS, sticky headers, tabular-nums** - `257c729` (feat)
2. **Task 2: Add collapsible sections with chevron indicators and tests** - `3301aa8` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/components.css` - New component CSS split (sticky headers, tabular-nums, data-grid, sources, collapsible sections)
- `src/do_uw/templates/html/components/tables.html.j2` - Added paired_kv_table macro and sticky-header class on data_table
- `src/do_uw/templates/html/base.html.j2` - Import paired_kv_table macro and include components.css
- `src/do_uw/templates/html/styles.css` - Removed tabular-nums rule, data-grid, sources-appendix, dead comments (568 -> 487 lines)
- `src/do_uw/templates/html/sections/executive/company_profile.html.j2` - Converted to paired_kv_table macro
- `src/do_uw/templates/html/sections/identity.html.j2` - Converted to paired_kv_table macro
- `src/do_uw/templates/html/sections/{company,financial,market,governance,litigation,ai_risk,scoring}.html.j2` - Collapsible wrappers
- `src/do_uw/templates/html/sections/scoring_hazard.html.j2` - Updated <details> to collapsible class
- `src/do_uw/templates/html/sections/scoring/hazard_profile.html.j2` - Updated <details> to collapsible class
- `tests/stages/render/test_html_layout.py` - 3 new tests: collapsible presence, open-by-default, exec summary excluded
- `tests/stages/render/test_html_components.py` - 4 new tests: paired_kv_table (4-col, odd, title), sticky-header

## Decisions Made
- Moved data-grid and sources-appendix CSS blocks from styles.css to components.css to meet 500-line limit (these are component-level styles that naturally belong in the split file)
- Removed dead Tailwind Supplement comment block from styles.css (zero active CSS rules; migration note superseded by stable compiled.css)
- Print CSS forces all collapsible sections open and hides summary elements so printed output retains full content
- Excluded company.html.j2 from collapsible layout tests since it is not rendered in the main worksheet (company profile is included inside executive.html.j2)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Moved data-grid and sources-appendix CSS to components.css**
- **Found during:** Task 1 (CSS split)
- **Issue:** After removing the tabular-nums rule, styles.css was 562 lines (still over 500-line limit). The plan only moved tabular-nums.
- **Fix:** Additionally moved data-grid CSS (35 lines) and sources-appendix CSS (18 lines) to components.css. Also removed dead Tailwind Supplement comment block (10 lines).
- **Files modified:** src/do_uw/templates/html/styles.css, src/do_uw/templates/html/components.css
- **Verification:** styles.css = 487 lines, components.css = 152 lines
- **Committed in:** 257c729 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — 500-line compliance)
**Impact on plan:** Necessary to comply with CLAUDE.md anti-context-rot rule. All moved CSS rules are component-level styles that belong in the split file. No behavioral change.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CSS component split pattern established for future additions (Phase 59-02, 63, 64)
- Collapsible section pattern ready for deeper subsection nesting in Phase 59-02 (VIS-05 two-column layout)
- Paired KV table macro available for any future section conversions
- All 283 render tests passing provides stable baseline

---
*Phase: 59-html-visual-polish*
*Completed: 2026-03-02*
