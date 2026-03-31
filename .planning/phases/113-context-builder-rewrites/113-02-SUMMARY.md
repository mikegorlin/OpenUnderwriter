---
phase: 113-context-builder-rewrites
plan: 02
subsystem: render
tags: [context-builders, signal-results, refactor, financials, market]

requires:
  - phase: 113-context-builder-rewrites
    provides: signal_results plumbing in md_renderer for all 14 builder functions (Plan 01)
  - phase: 104-signal-consumer-layer
    provides: _signal_consumer.py and _signal_fallback.py typed accessors
provides:
  - Signal-backed financials evaluative module (distress, earnings quality, leverage, tax, liquidity)
  - Signal-backed market evaluative module (volatility, short interest, insider, guidance, returns)
  - financials.py under 300 lines (was 631)
  - market.py under 300 lines (was 500)
affects: [113-03, 113-04]

tech-stack:
  added: []
  patterns: ["evaluative module extraction pattern: primary builder delegates to *_evaluative.py for signal consumption", "display helper extraction: large display-only helpers into _*_display.py private modules"]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/financials_evaluative.py
    - src/do_uw/stages/render/context_builders/market_evaluative.py
    - src/do_uw/stages/render/context_builders/_financials_display.py
    - src/do_uw/stages/render/context_builders/_market_display.py
  modified:
    - src/do_uw/stages/render/context_builders/financials.py
    - src/do_uw/stages/render/context_builders/market.py
    - tests/stages/render/test_signal_consumption.py
    - tests/stages/render/test_builder_line_limits.py

key-decisions:
  - "Evaluative modules (financials_evaluative.py, market_evaluative.py) own signal consumption; primary builders delegate rather than importing _signal_fallback directly"
  - "Display-only helpers (_financials_display.py, _market_display.py) extracted for quarterly, peer matrix, insider data, stock drops to keep primary builders under 300 lines"
  - "Signal IDs mapped to actual brain YAML: FIN.FORENSIC.m_score_composite (Beneish), FIN.QUALITY.* (earnings), FIN.DEBT.* (leverage), FIN.LIQ.* (liquidity), STOCK.PRICE/SHORT/INSIDER.* (market)"
  - "_format_disclosure_badge re-exported from market.py for backward compatibility with existing tests"

patterns-established:
  - "Evaluative extraction pattern: _extract_*_signals(signal_results, state_obj) returns dict merged into context"
  - "Signal fallback pattern: try signal first, fall back to direct state read if unavailable"

requirements-completed: [BUILD-02, BUILD-03]

duration: 12min
completed: 2026-03-17
---

# Phase 113 Plan 02: Financials + Market Signal-Backed Evaluative Extraction Summary

**Rewrote financials.py (631->280 lines) and market.py (500->228 lines) to consume FIN/STOCK/FWRD signal results for all evaluative content via dedicated evaluative modules**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-17T12:13:53Z
- **Completed:** 2026-03-17T12:25:43Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- financials_evaluative.py (292 lines) consumes 14 signal access calls across FIN.FORENSIC, FIN.QUALITY, FIN.DEBT, FIN.LIQ prefixes for distress, earnings quality, leverage, tax, and liquidity evaluations
- market_evaluative.py (193 lines) consumes 15 signal access calls across STOCK.PRICE, STOCK.SHORT, STOCK.INSIDER, FIN.GUIDE prefixes for volatility, short interest, insider, guidance, and return assessments
- Both primary builders under 300 lines with clean separation of display data (direct state) vs evaluative content (signal-backed)
- All 731 render tests pass unchanged (pre-existing PydanticUserError failures excluded)
- financials.py and market.py removed from EXCLUDED_FILES in line limit test

## Task Commits

1. **Task 1: Rewrite financials.py -- extract evaluative to financials_evaluative.py** - `5c5ba87` (feat)
2. **Task 2: Rewrite market.py -- extract evaluative to market_evaluative.py** - `954c3a6` (feat)

## Files Created/Modified
- `financials_evaluative.py` (292 lines) - Signal-backed distress, earnings quality, leverage, tax, liquidity evaluations
- `market_evaluative.py` (193 lines) - Signal-backed volatility, short interest, insider, guidance, return evaluations
- `_financials_display.py` (178 lines) - Quarterly context, yfinance quarterly, peer matrix display helpers
- `_market_display.py` (246 lines) - Insider data, stock drop events, earnings guidance display helpers
- `financials.py` (280 lines) - Rewritten primary builder, delegates evaluative to financials_evaluative
- `market.py` (228 lines) - Rewritten primary builder, delegates evaluative to market_evaluative
- `test_signal_consumption.py` - Added financials_evaluative.py and market_evaluative.py to signal consumption list
- `test_builder_line_limits.py` - Removed financials.py, market.py, governance.py from EXCLUDED_FILES

## Decisions Made
- Signal consumption lives in dedicated evaluative modules rather than in primary builders, keeping the delegation clean and the signal dependency explicit
- Display-only code (quarterly tables, peer matrix, insider transactions, stock drops) extracted to private `_*_display.py` modules since they have no signal dependency
- Actual brain signal IDs used (not plan-hypothesized ones): FIN.FORENSIC.m_score_composite instead of FIN.DISTRESS.beneish_m_score, etc.
- _format_disclosure_badge re-exported from market.py to maintain backward compatibility with test imports

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed f-string syntax error in valuation formatting**
- **Found during:** Task 2 (market.py rewrite)
- **Issue:** Attempted nested f-string format spec `f"{v.value{fmt}}"` which is invalid Python syntax
- **Fix:** Reverted to explicit per-field formatting matching original code
- **Files modified:** market.py
- **Verification:** Syntax check passes, all market tests pass

**2. [Rule 3 - Blocking] Fixed missing _format_disclosure_badge import**
- **Found during:** Task 2 (market.py rewrite)
- **Issue:** Test file imports `_format_disclosure_badge` from market.py, but function moved to _market_display.py
- **Fix:** Re-exported _format_disclosure_badge from market.py via import from _market_display
- **Files modified:** market.py
- **Verification:** All market tests pass including test_market_context_drops.py

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
- Plan referenced signal IDs that don't exist (FIN.DISTRESS.altman_z_score, STOCK.VOLATILITY.*, FWRD.GUIDANCE.*). Mapped to actual brain YAML signal IDs by grepping brain/signals/ directory.
- financials.py initially at 474 lines after first rewrite; required additional extraction of quarterly and peer matrix functions to _financials_display.py to meet 300-line limit.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Financial and market evaluative content now signal-backed; Plans 03-04 can address remaining builders (analysis, scoring, litigation, governance)
- Established evaluative extraction pattern reusable for remaining builders

---
*Phase: 113-context-builder-rewrites*
*Completed: 2026-03-17*
