---
phase: 140-litigation-classification-consolidation
plan: 03
subsystem: render
tags: [jinja2, html, markdown, litigation, templates]

requires:
  - phase: 140-01
    provides: unified litigation classifier with legal_theories, coverage_type, unclassified_reserves
  - phase: 140-02
    provides: context builder enrichment with legal_theories_display, coverage_display, data_quality_flags keys

provides:
  - HTML templates render legal theory column, coverage badges, data quality warnings, unclassified reserves
  - Markdown templates render legal theory, coverage, data quality flags, unclassified reserves
  - All 3 output formats (Word, HTML, Markdown) now at parity for classifier output

affects: [litigation-rendering, template-completeness]

tech-stack:
  added: []
  patterns:
    - "Classifier output keys flow through context builder to all 3 render paths"

key-files:
  created: []
  modified:
    - src/do_uw/templates/html/sections/litigation/active_matters.html.j2
    - src/do_uw/templates/html/sections/litigation/derivative_suits.html.j2
    - src/do_uw/templates/html/sections/litigation.html.j2
    - src/do_uw/templates/markdown/sections/litigation.md.j2

key-decisions:
  - "coverage_display used as primary badge source with fallback to coverage and coverage_type"
  - "Data quality flags shown in amber color with warning icon for visual prominence"
  - "Unclassified reserves placed after litigation_checks in HTML and after contingent liabilities in Markdown"

patterns-established:
  - "Classifier-derived display keys follow naming convention: {field}_display for human-readable versions"

requirements-completed: [LIT-01, LIT-02, LIT-03, LIT-04, LIT-05]

duration: 5min
completed: 2026-03-28
---

# Phase 140 Plan 03: Template Gap Closure Summary

**HTML and Markdown litigation templates now render all 4 classifier-derived keys: legal theories, coverage side badges, data quality warnings, and unclassified reserves**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-28T04:04:32Z
- **Completed:** 2026-03-28T04:09:46Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- HTML active_matters table now has 7 columns (was 6) with Legal Theory column showing human-readable theory names
- HTML coverage badge updated to prefer coverage_display from classifier over raw coverage_type
- HTML detail rows show amber data quality warnings when classifier flags missing fields
- HTML derivative_suits table has 6 columns (was 4) with Legal Theory and Coverage columns with color-coded badges
- HTML litigation section now includes Unclassified Legal Reserves subsection for boilerplate disclosures
- Markdown active cases table has 8 columns (was 6) with Legal Theory and Coverage
- Markdown derivative suits show Legal Theory and Coverage in detail tables
- Markdown historical cases table includes Legal Theory and Coverage columns
- Markdown includes unclassified reserves table section

## Task Commits

Each task was committed atomically:

1. **Task 1: Add classifier output to HTML litigation templates** - `06a6afca` (feat)
2. **Task 2: Add classifier output to Markdown litigation template** - `22e7de0a` (feat)

## Files Created/Modified
- `src/do_uw/templates/html/sections/litigation/active_matters.html.j2` - Added Legal Theory column, coverage_display badge, data quality flags warning
- `src/do_uw/templates/html/sections/litigation/derivative_suits.html.j2` - Added Legal Theory and Coverage columns with badges, data quality warning rows
- `src/do_uw/templates/html/sections/litigation.html.j2` - Added Unclassified Legal Reserves subsection after litigation_checks
- `src/do_uw/templates/markdown/sections/litigation.md.j2` - Added Legal Theory and Coverage columns to active/historical/derivative tables, data quality flags, unclassified reserves section

## Decisions Made
- Used coverage_display as primary badge source with graceful fallback chain: coverage_display -> coverage -> coverage_type -> em-dash
- Data quality flags rendered in amber (#d97706) with warning character for visual consistency with other warnings in the worksheet
- Unclassified reserves subsection positioned after litigation_checks (HTML) and after contingent liabilities (Markdown) to maintain logical flow

## Deviations from Plan
None - plan executed exactly as written.

## Known Stubs
None - all template references connect to populated context builder keys.

## Issues Encountered
- Worktree was behind main and missing Phase 140-01/02 changes; resolved by merging main before starting work
- Pre-existing test failures in test_119_integration.py (stock_catalyst_context_imported) and test_5layer_narrative.py (humanize_factor filter) unrelated to this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 4 verification gaps from 140-VERIFICATION.md are now closed
- Phase 140 is complete: classification pipeline (Plan 01) + context builder wiring (Plan 02) + template rendering (Plan 03)
- All 3 output formats (Word, HTML, Markdown) now display legal theory, coverage side, data quality warnings, and unclassified reserves

---
*Phase: 140-litigation-classification-consolidation*
*Completed: 2026-03-28*
