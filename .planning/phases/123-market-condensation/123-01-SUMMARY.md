---
phase: 123-market-condensation
plan: 01
subsystem: render
tags: [context-builders, condensation, overflow, market, governance, charts]

requires:
  - phase: 122-manifest-reorder-audit-layer
    provides: layer-aware template rendering with audit/decision/analysis tiers
provides:
  - condensed market context with top-10 insiders, top-5 drop events (1Y), top-10 holders
  - overflow keys (transactions_overflow, drop_events_overflow, top_holders_overflow) for audit appendix
  - chart classification (main_charts vs audit_charts) for template consumption
affects: [123-02, templates, audit-appendix]

tech-stack:
  added: []
  patterns:
    - "condensed + overflow pattern: main body gets top-N, overflow key gets remainder"
    - "build_drop_events returns tuple (condensed, all_events) instead of flat list"

key-files:
  created:
    - tests/stages/render/test_market_condensation.py
  modified:
    - src/do_uw/stages/render/context_builders/_market_display.py
    - src/do_uw/stages/render/context_builders/market.py
    - src/do_uw/stages/render/context_builders/governance.py

key-decisions:
  - "Removed 40-transaction cap in _build_transaction_rows -- overflow needs full dataset"
  - "build_drop_events now returns tuple instead of list -- breaking change handled in market.py caller"
  - "Date filtering uses date.fromisoformat() with fallback for non-parseable dates"

patterns-established:
  - "Condensation pattern: context builders produce {key} (limited) + {key}_overflow (remainder)"
  - "Total counts always reflect full dataset, never truncated counts"

requirements-completed: [MARKET-01, MARKET-02, MARKET-03, MARKET-04, MARKET-05]

duration: 7min
completed: 2026-03-21
---

# Phase 123 Plan 01: Market Context Condensation Summary

**Context builders now produce top-N limited main-body data with full overflow preservation in separate keys for audit appendix consumption**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-21T21:34:45Z
- **Completed:** 2026-03-21T21:41:18Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Insider transactions capped at 10 sales + 5 other in main body, overflow preserves all remaining
- Stock drop events filtered to 1Y lookback and limited to top 5 by severity; full sorted list in overflow
- Institutional holders expanded from 5 to 10 in main body, overflow for entries 11+
- Chart classification separates 1Y main charts from 5Y/analysis audit charts
- 20 new condensation tests covering all limits and overflow completeness

## Task Commits

Each task was committed atomically:

1. **Task 1: Condensation limits with overflow (TDD RED)** - `aa33775e` (test)
2. **Task 1: Condensation limits with overflow (TDD GREEN)** - `9421c501` (feat)
3. **Task 2: Verify existing tests pass** - `ec370bda` (chore)

## Files Created/Modified
- `tests/stages/render/test_market_condensation.py` - 20 tests for all condensation limits and overflow preservation
- `src/do_uw/stages/render/context_builders/_market_display.py` - 10-sale/5-other limits with overflow, build_drop_events returns tuple with 1Y filtering
- `src/do_uw/stages/render/context_builders/market.py` - Unpacks drop tuple, adds drop_events_overflow and chart classification keys
- `src/do_uw/stages/render/context_builders/governance.py` - Top 10 holders (was 5) with overflow for audit

## Decisions Made
- Removed the [:40] cap in _build_transaction_rows since overflow needs ALL transactions processed
- build_drop_events signature changed from returning list to tuple -- the only caller (market.py) was updated in the same commit
- Holders expanded from 5 to 10 per plan (adding granularity, not taking it away)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- MagicMock in chart classification tests leaked through to format_percentage() calls -- resolved by explicitly nullifying all optional stock/short-interest attributes in the mock helper
- 2 pre-existing test failures found (financials_evaluative.py line limit, html_signals key set) -- documented in deferred-items.md, not caused by this phase

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All overflow keys ready for template consumption in Plan 02
- Chart classification keys (main_charts, audit_charts) ready for template conditional rendering
- Templates will need to render condensed main body + collapsed audit overflow sections

---
*Phase: 123-market-condensation*
*Completed: 2026-03-21*
