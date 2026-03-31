---
phase: 40-professional-pdf-visual-polish
plan: 03
subsystem: render
tags: [formatters, jinja2-filters, accounting-style, tables, css, html-templates, pdf]

# Dependency graph
requires:
  - phase: 40-professional-pdf-visual-polish
    provides: Pre-compiled Tailwind CSS with @theme colors including risk-green
provides:
  - Accounting-style currency formatter with red parentheses for negatives
  - Adaptive precision formatter for ratios, percentages, and large numbers
  - YoY change arrows with colored triangles (green up, red down)
  - Consistent gray italic N/A HTML rendering for missing data
  - Navy-header tables with static zebra striping (no hover states)
  - text-risk-green CSS class for YoY positive arrows
affects: [40-04, 40-05]

# Tech tracking
tech-stack:
  added: []
  patterns: [accounting-style HTML formatters as Jinja2 filters, static zebra striping for PDF tables]

key-files:
  created:
    - tests/stages/render/test_formatters.py
  modified:
    - src/do_uw/stages/render/formatters.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/components/tables.html.j2
    - src/do_uw/templates/html/styles.css
    - src/do_uw/templates/html/sections/financial.html.j2
    - src/do_uw/templates/html/sections/executive.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2

key-decisions:
  - "format_currency_accounting separate from format_currency -- HTML rendering uses red span tags, Word/plain text stays as-is"
  - "text-risk-green added for YoY positive arrows per locked decision (triangle-up +12.3% in green)"
  - "hover:bg-slate-100 transition-colors removed from all PDF table rows -- meaningless in print context"
  - "financial_row macro supports yoy_change_pct numeric arg for yoy_arrow filter, and string yoy_change fallback"

patterns-established:
  - "HTML formatters return safe HTML strings with CSS classes for Jinja2 filters"
  - "format_na filter replaces all default('N/A') patterns with gray italic styled HTML"

requirements-completed: []

# Metrics
duration: 5min
completed: 2026-02-22
---

# Phase 40 Plan 03: Financial Number Formatting & Table Polish Summary

**Accounting-style red-parentheses negatives, adaptive precision ($394.3B), colored YoY triangle arrows, and Bloomberg-quality table styling with static zebra striping**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-22T02:43:23Z
- **Completed:** 2026-02-22T02:48:09Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added 4 new Jinja2 filters: format_acct (red parens for negatives), format_adaptive (ratios/pct/currency), yoy_arrow (colored triangle arrows), format_na (gray italic N/A)
- Removed all interactive hover states from PDF table rows across tables macro, financial, and scoring templates
- Applied format_na consistently across financial statement tables, distress indicators, audit profile, quarterly updates, and executive summary
- Added text-risk-green CSS class and --do-risk-green CSS variable for YoY positive arrows
- 22 new formatter tests covering all edge cases (negatives, compacts, None, zero, arrows)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add accounting-style number formatters and Jinja2 filters** - `a9c2c1f` (feat)
2. **Task 2: Polish table components and update financial/scoring templates** - `2cd3440` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/formatters.py` - Added format_currency_accounting, format_adaptive, format_yoy_html, format_na
- `src/do_uw/stages/render/html_renderer.py` - Registered 4 new Jinja2 filters (format_acct, format_adaptive, yoy_arrow, format_na)
- `tests/stages/render/test_formatters.py` - 22 tests for all new formatters
- `src/do_uw/templates/html/components/tables.html.j2` - Static zebra rows, yoy_arrow in financial_row macro
- `src/do_uw/templates/html/styles.css` - Added text-risk-green class, text-right-nums utility, --do-risk-green CSS var
- `src/do_uw/templates/html/sections/financial.html.j2` - format_na on all values, removed hover states
- `src/do_uw/templates/html/sections/executive.html.j2` - format_na on Company Snapshot and Inherent Risk Profile
- `src/do_uw/templates/html/sections/scoring.html.j2` - Removed hover states from 10-factor scoring table

## Decisions Made
- format_currency_accounting is a separate function from format_currency to keep Word/plain text rendering unaffected by HTML span tags
- text-risk-green is added despite the "NO green in risk spectrum" rule because it was explicitly locked for YoY positive arrows only
- financial_row macro accepts both yoy_change_pct (numeric, for yoy_arrow filter) and yoy_change (string, backward compat)
- Hover states removed globally from PDF templates since they add no value in printed/PDF output

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- 3 pre-existing test failures in render suite (embed_chart alt_text kwarg mismatch, md template stock chart references) -- not caused by this plan's changes, not in scope

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All new formatters are registered and available in templates for Plans 04-05
- Templates are ready for further visual polish (spacing, borders, cover page)
- 184 render tests pass (3 pre-existing failures unrelated to this plan)

## Self-Check: PASSED
