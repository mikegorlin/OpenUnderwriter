---
phase: 133-stock-and-market-intelligence
plan: 02
subsystem: render
tags: [market-intelligence, stock-drops, earnings, correlation, volume, analyst, context-builders, jinja2]

requires:
  - phase: 133-stock-and-market-intelligence/01
    provides: "earnings_reactions compute module, chart_computations correlation/r_squared functions"
provides:
  - "5 new/enhanced context builders for market section stock intelligence"
  - "4 new Jinja2 templates: earnings_reaction, volume_anomalies, analyst_revisions, correlation_metrics"
  - "D&O litigation theory mapping on drop events with attribution visualization"
  - "Earnings trust narrative connecting beat/miss patterns to market reaction"
  - "22 total template includes in market.html.j2 (up from 13)"
affects: [market-section, stock-analysis, worksheet-rendering]

tech-stack:
  added: []
  patterns: ["D&O theory mapping from trigger_category", "attribution split bar visualization", "severity-based card layout"]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/_market_volume.py
    - src/do_uw/stages/render/context_builders/_market_correlation.py
    - src/do_uw/templates/html/sections/market/earnings_reaction.html.j2
    - src/do_uw/templates/html/sections/market/volume_anomalies.html.j2
    - src/do_uw/templates/html/sections/market/analyst_revisions.html.j2
    - src/do_uw/templates/html/sections/market/correlation_metrics.html.j2
    - tests/stages/render/test_market_context_phase133.py
  modified:
    - src/do_uw/stages/render/context_builders/_market_display.py
    - src/do_uw/stages/render/context_builders/_market_acquired_data.py
    - src/do_uw/stages/render/context_builders/market.py
    - src/do_uw/templates/html/sections/market.html.j2
    - src/do_uw/templates/html/sections/market/stock_drops.html.j2

key-decisions:
  - "D&O theory derived from trigger_category mapping with do_assessment override"
  - "Correlation computed inline rather than depending on Plan 01 compute_correlation (not yet merged)"
  - "Attribution bar uses proportional widths of absolute values for visual clarity"
  - "Volume anomaly severity: high = >3x AND <-3%, medium = >2.5x OR abs>3%, low = rest"

patterns-established:
  - "D&O litigation theory mapping: _DO_THEORY_BY_CATEGORY dict in _market_display.py"
  - "Correlation metrics builder: self-contained with local correlation/r_squared computation"
  - "Card-style display for major drops (>=10%) with attribution bar and D&O theory"

requirements-completed: [STOCK-01, STOCK-02, STOCK-03, STOCK-05, STOCK-06, STOCK-07, STOCK-08]

duration: 8min
completed: 2026-03-27
---

# Phase 133 Plan 02: Market Section Stock Intelligence Displays Summary

**D&O theory cards on major drops, earnings trust narrative, volume anomaly table, analyst revision trends, correlation metrics card with loss causation interpretation -- market section expanded from 13 to 22 template includes**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-27T04:19:21Z
- **Completed:** 2026-03-27T04:27:16Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Every >10% drop now shows COMPANY/MARKET/SECTOR attribution bar + D&O litigation theory one-liner
- Earnings trust narrative analyzes beat/miss vs stock reaction patterns for fraud-on-the-market assessment
- Volume anomaly table cross-references spikes with 8-K filings and news within proximity windows
- Analyst revision trends show directional EPS estimate changes (7d/30d) with price target range card
- Correlation metrics card shows SPY/sector correlation, R-squared, idiosyncratic risk % with D&O interpretation
- 5 previously-orphaned templates wired into market.html.j2 (stock_drop_catalyst, earnings_history, forward_estimates, upgrades_downgrades, news_articles)

## Task Commits

1. **Task 1: Drop event card enhancement + earnings trust narrative** - `f815b101` (feat)
2. **Task 2: Volume anomalies + analyst revisions + correlation metrics** - `d3a8699e` (feat)
3. **Task 3: Wire all into extract_market() and market.html.j2** - `21781041` (feat)

## Files Created/Modified
- `_market_volume.py` - Volume anomaly builder with 8-K/news cross-reference
- `_market_correlation.py` - Return correlation metrics with D&O loss causation interpretation
- `_market_acquired_data.py` - Added build_earnings_trust, build_eps_revision_trends, build_analyst_targets
- `_market_display.py` - Enhanced drop events with do_theory, attribution_split, consolidated_days
- `market.py` - Wired 5 new builder calls into extract_market()
- `market.html.j2` - Expanded include list from 13 to 22 templates
- `stock_drops.html.j2` - Added Significant Decline Events card section
- `earnings_reaction.html.j2` - NEW: multi-window earnings reaction table
- `volume_anomalies.html.j2` - NEW: volume spike table with catalyst cross-reference
- `analyst_revisions.html.j2` - NEW: EPS revision trends + price target range
- `correlation_metrics.html.j2` - NEW: 2x2 metric grid with D&O interpretation
- `test_market_context_phase133.py` - 11 tests covering all new builders

## Decisions Made
- D&O theory mapping uses a category-to-theory dict with evt.do_assessment as override
- Correlation computed with local functions rather than waiting for Plan 01's compute_correlation (not yet merged into worktree)
- Attribution bar shows proportional absolute values for visual clarity regardless of sign
- Volume severity uses compound threshold (>3x AND <-3% for high) to reduce noise

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Plan 01 outputs not available in worktree**
- **Found during:** Task 1 (earnings trust builder)
- **Issue:** compute_correlation(), compute_r_squared(), next_day_return_pct, week_return_pct from Plan 01 not merged into this worktree
- **Fix:** Created local _compute_correlation() and _compute_r_squared() in _market_correlation.py; used getattr() for optional fields on EarningsQuarterRecord
- **Files modified:** _market_correlation.py, _market_acquired_data.py
- **Verification:** All 11 tests pass, correlation metrics produce correct values
- **Committed in:** d3a8699e (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minimal -- local computation duplicates Plan 01 functions but will be superseded when Plan 01 merges.

## Issues Encountered
None beyond the Plan 01 dependency noted above.

## Known Stubs
None -- all builders produce real data from state. Templates guard with `{% if %}` for missing data.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Market section now has 22 template includes covering all stock intelligence data
- When Plan 01 merges, _market_correlation.py can optionally import from chart_computations instead of local functions
- EarningsQuarterRecord next_day_return_pct/week_return_pct columns will auto-populate when Plan 01 fields are added

---
*Phase: 133-stock-and-market-intelligence*
*Completed: 2026-03-27*
