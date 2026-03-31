---
phase: 43-html-presentation-quality-capiq-layout-data-tracing
plan: "07"
subsystem: ui
tags: [jinja2, html, sidebar, toc, appendix, qa-audit, ipo-date, template, capiq]

# Dependency graph
requires:
  - phase: 43-html-presentation-quality-capiq-layout-data-tracing
    provides: Two-column CapIQ sidebar layout, section templates, html_renderer context builder

provides:
  - Sidebar TOC with Appendix group header and 4 sub-links (Meeting Prep, Sources, QA Audit, Coverage)
  - Scoring section moved to last-before-appendices position (after AI Risk)
  - Identity block shows "IPO / Listed" with year derived from years_public, not raw count
  - QA / Audit Trail appendix (qa_audit.html.j2) with per-section check-level audit trail
  - sidebar.css styles for .sidebar-group-header, .sidebar-sub, and .qa-conf badge variants

affects: [html-rendering, worksheet-layout, appendices, sidebar-navigation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Jinja2 namespace loop for safe variable accumulation across for-loops"
    - "Sidebar group headers as non-anchor <li> elements with CSS styling"
    - "Template context injection for derived identity fields (ipo_date from years_public)"

key-files:
  created:
    - src/do_uw/templates/html/appendices/qa_audit.html.j2
  modified:
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/templates/html/sections/identity.html.j2
    - src/do_uw/templates/html/sidebar.css
    - src/do_uw/stages/render/html_renderer.py
    - tests/stages/render/test_html_layout.py

key-decisions:
  - "Scoring section placed last before appendices (after AI Risk) — underwriters read narrative before seeing score"
  - "IPO year approximated from years_public count (exact firstTradeDateMilliseconds not persisted in state)"
  - "Sidebar Appendix group as plain <li class='sidebar-group-header'> (not a link) — visual-only separator"
  - "QA audit total uses namespace loop (not sum filter) for Jinja2 loop variable safety"

patterns-established:
  - "Appendix sub-links: sidebar-sub class with 20px left padding and 10px font-size"
  - "QA confidence badges: inline-block spans with color-coded HIGH/MED/LOW variants"

requirements-completed:
  - VIS-05
  - OUT-03

# Metrics
duration: 2min
completed: 2026-02-25
---

# Phase 43 Plan 07: UAT Gap Closure — Sidebar, Section Order, IPO Date, QA Audit Summary

**Sidebar TOC with Appendix group + 4 sub-links, scoring moved last before appendices, IPO date in identity block, and new QA/Audit Trail appendix with per-section check-level audit trail**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-25T04:28:55Z
- **Completed:** 2026-02-25T04:31:00Z
- **Tasks:** 2
- **Files modified:** 7 (6 modified + 1 created)

## Accomplishments

- Sidebar TOC reorganized: Scoring link moved after AI Risk; "Appendix" group header added with 4 sub-links (Meeting Prep, Sources, QA Audit, Coverage)
- Worksheet section order corrected: scoring now appears after AI Risk, immediately before appendices — underwriters read narrative before score
- Identity block "Years Public" replaced with "IPO / Listed" row; shows approximate IPO year derived from years_public count, falls back gracefully
- New `qa_audit.html.j2` appendix created: check-level audit trail grouped by section, columns Check ID / Check / Finding / Source / Conf. / Status with color-coded confidence badges
- All 227 render tests pass; both new/modified CSS files well under 500 lines

## Task Commits

1. **Task 1: Fix sidebar TOC, section order, IPO date, and ipo_date context** - `26782b6` (feat)
2. **Task 2: Create qa_audit.html.j2 appendix** - `579b018` (feat)

## Files Created/Modified

- `src/do_uw/templates/html/base.html.j2` - Sidebar TOC: Scoring link repositioned, Appendix group header + 4 sub-links added
- `src/do_uw/templates/html/worksheet.html.j2` - Section include order corrected; qa_audit.html.j2 include added
- `src/do_uw/templates/html/sections/identity.html.j2` - "Years Public" replaced with "IPO / Listed" using ipo_date context variable
- `src/do_uw/stages/render/html_renderer.py` - Injects ipo_date (year derived from years_public) into template context; adds timedelta import
- `src/do_uw/templates/html/sidebar.css` - Adds .sidebar-group-header, .sidebar-sub, and all .qa-conf/* styles
- `src/do_uw/templates/html/appendices/qa_audit.html.j2` - New: QA/Audit Trail appendix, id="qa-audit", check-level table grouped by section
- `tests/stages/render/test_html_layout.py` - Updated test_section_order to reflect new correct section order

## Decisions Made

- Scoring placed last before appendices (after AI Risk): underwriters should read the narrative analysis before the numerical score, matching how CapIQ-style reports sequence summary content
- IPO year approximated from years_public count since exact `firstTradeDateMilliseconds` from yfinance is not persisted in state; showing year is more informative than raw count
- Sidebar Appendix group uses a plain `<li class="sidebar-group-header">` (no anchor href) as a visual-only group separator; sub-links use `.sidebar-sub` class with indented padding
- QA audit check total uses `{% set ns = namespace(total=0) %}` Jinja2 namespace loop pattern instead of `sum(attribute='__len__')` filter, which is not valid for list-of-dicts

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated test_section_order to reflect new correct section order**
- **Found during:** Task 1 (after moving scoring in worksheet.html.j2)
- **Issue:** `test_section_order` in test_html_layout.py still asserted old order (scoring before financial) — test was correct for the old plan but wrong for the new spec
- **Fix:** Updated `required_ids` list in test to match new order: financial before scoring
- **Files modified:** tests/stages/render/test_html_layout.py
- **Verification:** All 227 tests pass
- **Committed in:** 26782b6 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - test assertion corrected for new spec)
**Impact on plan:** Test was testing the OLD incorrect order; fix aligns test with plan spec. No scope creep.

## Issues Encountered

None beyond the test order fix above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All four UAT gaps from phase 43 are now closed
- Sidebar navigation is complete with proper Appendix grouping
- QA Audit appendix provides transparency for underwriters
- HTML worksheet is fully polished for UAT re-verification

---
*Phase: 43-html-presentation-quality-capiq-layout-data-tracing*
*Completed: 2026-02-25*
