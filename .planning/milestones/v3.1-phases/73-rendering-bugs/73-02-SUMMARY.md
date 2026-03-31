---
phase: 73-rendering-bugs
plan: "02"
subsystem: render
tags: [percentile-bars, peer-benchmarking, insider-trading, sec-frames, jinja2]

# Dependency graph
requires:
  - phase: 72-peer-benchmarking
    provides: FramesPercentileResult data on state.benchmark.frames_percentiles
  - phase: 71-form4-enhancement
    provides: InsiderTradingAnalysis with ownership_alerts and shares_owned_following
provides:
  - Peer percentile context builder with direction-aware risk coloring (15 metrics)
  - Dual horizontal bar template (navy=all filers, gold=sector peers)
  - Enhanced insider trading table with ownership concentration alerts
  - Transaction detail rows with 10b5-1 badges and post-transaction ownership
affects: [73-03-PLAN, rendering-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [direction-aware-risk-coloring, dual-bar-percentile-display]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/financials_peers.py
    - src/do_uw/templates/html/sections/financial/peer_percentiles.html.j2
    - tests/test_financials_peers_context.py
  modified:
    - src/do_uw/stages/render/context_builders/financials.py
    - src/do_uw/stages/render/context_builders/market.py
    - src/do_uw/brain/sections/financial_health.yaml
    - src/do_uw/templates/html/sections/market/insider_trading.html.j2
    - tests/stages/render/test_section_renderer.py

key-decisions:
  - "Direction-aware coloring: HIGH_IS_GOOD (margin, ROE, coverage) vs HIGH_IS_BAD (leverage) vs NEUTRAL (size metrics)"
  - "Ownership alerts rendered as severity-colored table rows with C-Suite badge"
  - "Transaction detail limited to 30 most recent to avoid table bloat"

patterns-established:
  - "Dual-bar percentile: navy=overall + gold(50% opacity)=sector in same percentile-bar div"
  - "Severity-colored left border pattern for alerts (red=RED_FLAG, amber=WARNING)"

requirements-completed: [RENDER-03, RENDER-04]

# Metrics
duration: 7min
completed: 2026-03-07
---

# Phase 73 Plan 02: Peer Percentile Display & Insider Trading Enhancement Summary

**Dual horizontal bar peer benchmarking template for 15 SEC Frames metrics with direction-aware risk coloring, plus insider trading table enhanced with ownership concentration alerts and 10b5-1 badges**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-07T03:11:33Z
- **Completed:** 2026-03-07T03:19:20Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- New peer percentile context builder (financials_peers.py, 179 lines) transforms Frames API data into direction-aware risk-colored bars
- Dual horizontal bar template shows overall (navy) vs sector (gold) percentile positioning for 15 metrics
- Insider trading template enhanced with ownership concentration alerts table, individual transaction detail, 10b5-1 trading plan badges, and cluster event callout
- 8 new tests covering empty data, coloring logic, formatting, and full metric set

## Task Commits

Each task was committed atomically:

1. **Task 1: Peer percentile context builder and template** - `ffe0819` (feat)
2. **Task 2: Enhanced insider trading table with ownership concentration** - `8848977` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/financials_peers.py` - New context builder: 15-metric direction-aware percentile data
- `src/do_uw/templates/html/sections/financial/peer_percentiles.html.j2` - Dual bar template with print CSS
- `tests/test_financials_peers_context.py` - 8 tests for percentile builder
- `src/do_uw/stages/render/context_builders/financials.py` - Import + call peer percentile builder
- `src/do_uw/stages/render/context_builders/market.py` - Ownership alerts + transaction detail context
- `src/do_uw/brain/sections/financial_health.yaml` - peer_percentiles facet entry
- `src/do_uw/templates/html/sections/market/insider_trading.html.j2` - Ownership alerts, 10b5-1 badges, transaction table
- `tests/stages/render/test_section_renderer.py` - Updated facet count 14->15

## Decisions Made
- Direction-aware coloring uses three categories: FAVORABLE_HIGH (margin, ROE, current_ratio, coverage, operating_income, cash_from_operations), UNFAVORABLE_HIGH (debt_to_equity, total_liabilities), NEUTRAL (all size metrics like revenue, assets)
- Ownership concentration alerts use severity-colored left border (red for RED_FLAG, amber for WARNING) plus C-Suite badge pills
- Individual transactions capped at 30 rows to keep table manageable
- Percentile ordinal suffix simplified (always "th" except 1st/2nd/3rd)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed sic_to_sector import path**
- **Found during:** Task 1
- **Issue:** Plan referenced import from context_builders/company.py but function lives in stages/resolve/sec_identity.py
- **Fix:** Updated import to correct module path
- **Files modified:** financials_peers.py
- **Committed in:** ffe0819

**2. [Rule 3 - Blocking] Updated section renderer tests for new facet count**
- **Found during:** Task 2
- **Issue:** Adding peer_percentiles facet to financial_health.yaml changed facet count from 14 to 15, breaking 4 tests
- **Fix:** Updated _EXPECTED_FINANCIAL_FACETS list and count assertions
- **Files modified:** tests/stages/render/test_section_renderer.py
- **Committed in:** 8848977

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pre-existing test failures in test_peril_scoring_html.py (red_flag_summary attribute), test_pdf_paged.py (CSS page rules), test_render_coverage.py (89.6% coverage < 90% threshold), and test_analyze_stage.py (debt_to_ebitda key error) - all unrelated to this plan's changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Peer percentile template ready for rendering in HTML output
- Insider trading enhancements will display when companies have Form 4 data with ownership tracking
- Ready for 73-03 (remaining rendering/bug fix work)

---
*Phase: 73-rendering-bugs*
*Completed: 2026-03-07*
