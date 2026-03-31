---
phase: 43-html-presentation-quality-capiq-layout-data-tracing
plan: 03
subsystem: render
tags: [jinja2, html, css, formatters, data-grid, capiq, density]

# Dependency graph
requires:
  - phase: 43-html-presentation-quality-capiq-layout-data-tracing
    provides: base.html.j2 macro system, tables.html.j2 component library, styles.css design tokens
provides:
  - data_row Jinja2 macro: 3-column row (label | value | context) in tables.html.j2
  - data_grid Jinja2 macro: bordered table wrapper for data_row calls in tables.html.j2
  - format_em_dash(): returns em dash for None/empty, str(value) otherwise in formatters_numeric.py
  - format_em Jinja2 filter: registered in html_renderer.py env.filters
  - financial.html.j2 Key Financial Metrics block migrated to data_grid (Profitability / Balance Sheet / Cash Flow)
  - financial_statements.html.j2: split file for income statement, balance sheet, cash flow statement tables
  - market.html.j2 Stock Performance block migrated to data_grid with peer context
  - market.html.j2 section id fixed from market-trading to market (matches sidebar TOC)
  - formatters_numeric.py: new file with format_currency, format_percentage, format_currency_accounting, format_adaptive, format_yoy_html, format_em_dash, spectrum data
  - formatters_humanize.py: new file with humanize_*, strip_cyber_tags
affects: [render, templates, html-output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "3-column data_grid macro: label | value | peer-context for all quantitative data tables"
    - "formatters.py split: numeric functions -> formatters_numeric.py, humanize functions -> formatters_humanize.py; backward-compat re-exports preserve all import sites"
    - "Template split pattern: large section templates split via {%% include %%} with child file owning own context access"

key-files:
  created:
    - src/do_uw/stages/render/formatters_numeric.py
    - src/do_uw/stages/render/formatters_humanize.py
    - src/do_uw/templates/html/sections/financial_statements.html.j2
  modified:
    - src/do_uw/stages/render/formatters.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/components/tables.html.j2
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/styles.css
    - src/do_uw/templates/html/sections/financial.html.j2
    - src/do_uw/templates/html/sections/market.html.j2

key-decisions:
  - "formatters.py was 769 lines (over 500 limit) — split to formatters_numeric.py (numeric/spectrum) + formatters_humanize.py (humanize/strip) with backward-compat re-exports; formatters.py now 380 lines"
  - "financial.html.j2 split: income statement, balance sheet, cash flow tables moved to financial_statements.html.j2 (91 lines); financial.html.j2 now 446 lines"
  - "data_grid uses Jinja2 caller() block ({% call %} syntax) — not the loop-based approach; keeps template readable"
  - "context_text for financial rows: uses empty string where no peer benchmark data is available in fin dict; no 'N/A' in context column per spec"
  - "market.html.j2 section id: was market-trading, changed to market to match sidebar TOC href"

patterns-established:
  - "data_row macro: always pass empty string '' for context_text when no peer data — never 'N/A'"
  - "File split pattern: extract content to child file, replace with {%% include %%}, child accesses parent-scope variables directly"

requirements-completed: [VIS-04, VIS-05]

# Metrics
duration: 8min
completed: 2026-02-25
---

# Phase 43 Plan 03: 3-Column Data Grid Macros + Financial/Market Section Migration Summary

**data_row/data_grid Jinja2 macros + format_em_dash formatter enabling CapIQ-grade Label | Value | Context density in financial and market sections**

## Performance

- **Duration:** 8 min 9s
- **Started:** 2026-02-25T03:04:07Z
- **Completed:** 2026-02-25T03:12:16Z
- **Tasks:** 2
- **Files modified:** 9 (including 3 new)

## Accomplishments
- Added `data_row` and `data_grid` Jinja2 macros to `tables.html.j2` — 3-column layout (Label | Value | Peer Context) for CapIQ-grade density
- Added `format_em_dash()` to `formatters_numeric.py` and registered it as `format_em` Jinja2 filter in `html_renderer.py`
- Migrated `financial.html.j2` Key Financial Metrics block from 2-column inline grid to 3-column `data_grid` (Profitability, Balance Sheet, Cash Flow groups)
- Split `financial_statements.html.j2` from `financial.html.j2` — brings financial.html.j2 from 551 to 446 lines (under 500)
- Migrated `market.html.j2` Stock Performance block from `kv_table` to `data_grid` with sector/peer context for 1Y return and Beta
- Fixed `market.html.j2` section `id` mismatch: `market-trading` -> `market` (matches sidebar TOC `href="#market"`)
- Split `formatters.py` from 769 lines to 380 lines via `formatters_numeric.py` and `formatters_humanize.py` with backward-compat re-exports

## Task Commits

Each task was committed atomically:

1. **Task 1: Add data_row/data_grid macros, format_em_dash, register format_em filter** - `a26d1b2` (feat)
2. **Task 2: Migrate financial.html.j2 and market.html.j2 to 3-column data_grid** - `6e9ae2d` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/formatters_numeric.py` - New: format_currency, format_percentage, format_currency_accounting, format_adaptive, format_yoy_html, format_em_dash, spectrum data/computation
- `src/do_uw/stages/render/formatters_humanize.py` - New: humanize_theory, humanize_field_name, humanize_check_evidence, strip_cyber_tags, humanize_impact, humanize_enum
- `src/do_uw/templates/html/sections/financial_statements.html.j2` - New: income statement, balance sheet, cash flow tables split from financial.html.j2
- `src/do_uw/stages/render/formatters.py` - Reduced from 769 to 380 lines; backward-compat re-exports; format_em_dash in __all__
- `src/do_uw/stages/render/html_renderer.py` - Import format_em_dash; register format_em filter
- `src/do_uw/templates/html/components/tables.html.j2` - Added data_row and data_grid macros (47 lines)
- `src/do_uw/templates/html/base.html.j2` - Added data_row, data_grid to macro import line
- `src/do_uw/templates/html/styles.css` - Added CSS rules for .data-grid-table, .dr-label, .dr-value, .dr-context, .dr-missing, .conf-marker, .fn-ref
- `src/do_uw/templates/html/sections/financial.html.j2` - Key Metrics to data_grid; include financial_statements.html.j2; 551->446 lines
- `src/do_uw/templates/html/sections/market.html.j2` - Stock Performance to data_grid; fix section id

## Decisions Made
- `formatters.py` was 769 lines (over 500 limit) — required more extensive split than plan specified. Extracted numeric formatters and spectrum data to `formatters_numeric.py`, humanize functions to `formatters_humanize.py`. Backward-compat re-exports in `formatters.py` preserve all 14+ import sites with zero changes needed at call sites.
- `data_grid` uses Jinja2 `{% call %}` pattern (caller block) for clean template composition — caller() renders the inner row content between the table tags.
- `context_text` for financial metric rows uses empty string where no peer benchmark is available in the `fin` dict — follows spec requirement to show blank (not "N/A") in context column.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] formatters.py was 769 lines, not ~500 as plan estimated**
- **Found during:** Task 1 (checking line count before split)
- **Issue:** Plan said to split formatters_numeric.py with 4 functions if at/above 500 lines. File was already 769 lines, and after moving those 4 functions it would still be ~640 lines.
- **Fix:** Also extracted humanize functions (humanize_theory, humanize_field_name, etc.) to formatters_humanize.py and spectrum data to formatters_numeric.py. Result: formatters.py is 380 lines. Backward-compat re-exports preserve all import sites.
- **Files modified:** formatters.py, formatters_numeric.py (new), formatters_humanize.py (new)
- **Verification:** `uv run pytest tests/stages/render/ -x -q` — 217 passed
- **Committed in:** a26d1b2 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug/scope expansion due to file larger than plan estimated)
**Impact on plan:** Necessary to meet the 500-line requirement. No scope creep — all changes serve the file-size constraint. All import sites preserved via re-exports.

## Issues Encountered
None beyond the formatters.py size deviation documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- data_row/data_grid macros available for all future section templates
- format_em filter available in all HTML templates via env.filters
- financial.html.j2 and market.html.j2 now show 3-column metric grids
- Plan 04 can use data_row/data_grid for remaining sections (company, governance, litigation)

## Self-Check: PASSED

All created files verified present. All task commits verified in git log.

| Check | Result |
|-------|--------|
| formatters_numeric.py exists | FOUND |
| formatters_humanize.py exists | FOUND |
| financial_statements.html.j2 exists | FOUND |
| Commit a26d1b2 (Task 1) | FOUND |
| Commit 6e9ae2d (Task 2) | FOUND |

---
*Phase: 43-html-presentation-quality-capiq-layout-data-tracing*
*Completed: 2026-02-25*
