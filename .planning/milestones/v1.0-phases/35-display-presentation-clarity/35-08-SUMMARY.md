---
phase: 35-display-presentation-clarity
plan: 08
subsystem: render
tags: [html, jinja2, yoy-change, financial-table, conditional-formatting]

# Dependency graph
requires:
  - phase: 35-display-presentation-clarity
    provides: "financial_row macro with yoy_change parameter and conditional coloring in tables.html.j2"
provides:
  - "YoY change percentages (revenue_yoy, net_income_yoy) computed in extract_financials()"
  - "Financial summary HTML table with 4-column layout including YoY Change column"
  - "Conditional red/blue/gray coloring on YoY changes via financial_row macro"
affects: [render, html-output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "format_change_indicator(current, prior) for YoY percentage strings"

key-files:
  created: []
  modified:
    - "src/do_uw/stages/render/md_renderer_helpers.py"
    - "src/do_uw/templates/html/sections/financial.html.j2"

key-decisions:
  - "Computed YoY from already-extracted rev_val/prior_rev rather than re-searching line items for yoy_change attribute -- avoids redundant iteration"

patterns-established:
  - "YoY percentages passed as formatted strings to Jinja2 macros, coloring logic stays in template layer"

requirements-completed: [VIS-04]

# Metrics
duration: 2min
completed: 2026-02-21
---

# Phase 35 Plan 08: VIS-04 YoY Change Column Summary

**Wired YoY change percentages from extract_financials() into HTML financial summary table with conditional red/blue coloring via financial_row macro**

## Performance

- **Duration:** 1m 48s
- **Started:** 2026-02-21T15:55:46Z
- **Completed:** 2026-02-21T15:57:34Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Added `format_change_indicator` import and YoY computation in `extract_financials()` producing `revenue_yoy` and `net_income_yoy` keys
- Added 4th column header "YoY Change" to financial summary table in `financial.html.j2`
- Wired `yoy_change` parameter to Revenue and Net Income `financial_row` calls with `direction="lower_is_worse"` for conditional coloring
- Non-numeric rows (Leverage, Liquidity, etc.) gracefully render "--" via existing macro default behavior

## Task Commits

Each task was committed atomically:

1. **Task 1: Compute YoY change percentages and wire to template** - `c252847` (feat)

**Plan metadata:** `c0a6c55` (docs: complete plan)

## Files Created/Modified
- `src/do_uw/stages/render/md_renderer_helpers.py` - Added format_change_indicator import; compute revenue_yoy and net_income_yoy in extract_financials()
- `src/do_uw/templates/html/sections/financial.html.j2` - Added YoY Change column header; pass yoy_change to financial_row macro calls

## Decisions Made
- Used `format_change_indicator(current, prior)` from formatters.py rather than reading `FinancialLineItem.yoy_change` directly -- the current/prior values are already extracted, avoiding redundant line item iteration

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- VIS-04 gap fully closed: financial summary table now shows computed YoY percentages with conditional formatting
- All 147 render tests pass; 58 financial-related tests pass (39 skipped as expected)
- Ready for plan 09

## Self-Check: PASSED

All files exist, all commits verified.

---
*Phase: 35-display-presentation-clarity*
*Completed: 2026-02-21*
