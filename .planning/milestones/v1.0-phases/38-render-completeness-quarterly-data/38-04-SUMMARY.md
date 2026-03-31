---
phase: 38-render-completeness-quarterly-data
plan: 04
subsystem: render
tags: [jinja2, markdown, html, docx, quarterly, financial-statements, templates]

# Dependency graph
requires:
  - phase: 38-01
    provides: "Split MD template with section includes and FileSystemLoader"
  - phase: 38-03
    provides: "QuarterlyUpdate model on ExtractedFinancials with aggregate_quarterly_updates()"
provides:
  - "Full income/balance sheet/cash flow tables with all line items in MD and HTML"
  - "Quarterly update subsection rendering in MD, Word, and HTML"
  - "Quarterly context extraction from QuarterlyUpdate models"
affects: [38-05 data freshness, 38-06 governance rendering, 38-07 final polish]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Full statement row extraction with period-keyed values and YoY change", "Quarterly context builder pattern for renderer consumption"]

key-files:
  created:
    - src/do_uw/stages/render/sections/sect3_quarterly.py
  modified:
    - src/do_uw/stages/render/md_renderer_helpers_financial.py
    - src/do_uw/templates/markdown/sections/financial.md.j2
    - src/do_uw/stages/render/sections/sect3_financial.py
    - src/do_uw/templates/html/sections/financial.html.j2

key-decisions:
  - "Full statement tables are ADDITIONS to existing summary snapshot, not replacements -- backward compatibility preserved"
  - "Statement periods derived from income statement first, falling back to balance sheet then cash flow"
  - "YoY change in full tables computed from first two SourcedValue entries rather than stored yoy_change field for consistency"
  - "Quarterly update uses only the most recent quarter (index 0) for the subsection heading and details"

patterns-established:
  - "_build_statement_rows() pattern: iterate all line items, format per-period values, skip all-N/A rows"
  - "_build_quarterly_context() pattern: extract QuarterlyUpdate into renderer-friendly dict with formatted currency/EPS"

requirements-completed: [SC-2, SC-3, SC-6]

# Metrics
duration: 5min
completed: 2026-02-21
---

# Phase 38 Plan 04: Full Financial Statement Tables & Quarterly Update Rendering Summary

**Full income/balance sheet/cash flow tables with all line items in MD/HTML, quarterly update subsection with YTD comparison in all three output formats (MD, Word, HTML)**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-21T20:33:30Z
- **Completed:** 2026-02-21T20:38:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Full financial statement tables (income, balance sheet, cash flow) with all line items and YoY change column render in both Markdown and HTML templates
- Quarterly update subsection renders in all three formats (MD, Word, HTML) when post-annual 10-Q data is present, omitted when absent
- YTD comparison table with current vs prior year revenue, net income, and EPS
- Material changes, legal proceedings, going concern, material weaknesses, and subsequent events render in quarterly update section
- All existing financial rendering preserved for backward compatibility

## Task Commits

Each task was committed atomically:

1. **Task 1: Full financial statement tables in MD + quarterly update context extraction** - `b1ea50d` (feat)
2. **Task 2: Quarterly update in Word renderer + HTML template alignment** - `e0a6408` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/md_renderer_helpers_financial.py` - Added _build_statement_rows() and _build_quarterly_context() for full statement + quarterly data extraction (386 lines)
- `src/do_uw/templates/markdown/sections/financial.md.j2` - Added full statement tables and quarterly update subsection (172 lines)
- `src/do_uw/stages/render/sections/sect3_quarterly.py` - New Word renderer for quarterly update subsection (122 lines)
- `src/do_uw/stages/render/sections/sect3_financial.py` - Wired quarterly update rendering after financial tables (469 lines)
- `src/do_uw/templates/html/sections/financial.html.j2` - Added full statement tables and quarterly update to HTML template (327 lines)

## Decisions Made
- **Full tables are additions, not replacements**: The existing Key Financial Metrics summary snapshot at the top of Section 3 is preserved. Full statement tables appear below it, giving underwriters both a quick glance and full detail.
- **Period source priority**: Statement periods are derived from income statement first, then balance sheet, then cash flow. This matches the natural document order.
- **Most recent quarter only for subsection**: Only index 0 of quarterly_updates is rendered as the "Recent Quarterly Update" subsection heading. If multiple quarters exist, only the most recent is shown in detail.
- **Same context for all formats**: MD and HTML use the same `extract_financials()` context dict from `build_template_context()`. Word renderer reads directly from state model. All three produce identical content.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Two pre-existing test failures (PDF/WeasyPrint library loading) are unrelated to this plan and were not fixed (out of scope, same as noted in 38-01-SUMMARY).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Full financial statement tables available in MD and HTML for plans 05-07
- Quarterly update rendering established in all three formats
- sect3_quarterly.py can be extended in future for multi-quarter comparison
- All files well under 500 lines (largest: sect3_financial.py at 469 lines)

## Self-Check: PASSED

- All 5 files verified present on disk
- Commit b1ea50d verified in git history
- Commit e0a6408 verified in git history
- All 15 Markdown/meeting prep tests pass
- All 15 quarterly integration tests pass

---
*Phase: 38-render-completeness-quarterly-data*
*Completed: 2026-02-21*
