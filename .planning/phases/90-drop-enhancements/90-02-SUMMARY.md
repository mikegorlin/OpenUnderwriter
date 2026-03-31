---
phase: 90-drop-enhancements
plan: 02
subsystem: extract, score, render
tags: [time-decay, return-decomposition, corrective-disclosure, f2-scoring, html-template, word-renderer]

# Dependency graph
requires:
  - phase: 90-drop-enhancements
    plan: 01
    provides: "stock_drop_decay, stock_drop_decomposition, stock_drop_enrichment modules"
  - phase: 89-statistical-analysis
    provides: "abnormal return fields, DDL exposure on StockDropEvent"
provides:
  - "Pipeline wiring: decay, decomposition, reverse lookup integrated into extraction"
  - "F2 scoring: compound drop-level modifier (decay * company_pct * disclosure)"
  - "HTML/Word: Recency, Market, Sector, Company, Disclosure columns on drops table"
  - "drop_contributions data key in factor_data for F2"
affects: [91-display-centralization, 92-rendering-completeness]

# Tech tracking
tech-stack:
  added: []
  patterns: [compound-scoring-modifier, conditional-column-display, decay-weighted-sort]

key-files:
  created:
    - tests/stages/score/test_factor_scoring_f2_decay.py
    - tests/stages/render/test_market_context_drops.py
  modified:
    - src/do_uw/stages/extract/stock_performance.py
    - src/do_uw/stages/score/factor_data.py
    - src/do_uw/stages/score/factor_scoring.py
    - src/do_uw/stages/render/context_builders/market.py
    - src/do_uw/templates/html/sections/market/stock_drops.html.j2
    - src/do_uw/stages/render/sections/sect4_drop_tables.py

key-decisions:
  - "Compound modifier applied AFTER insider amplifier and market cap multiplier in F2 scoring chain"
  - "Decomposition/disclosure columns conditionally displayed (only when data exists)"
  - "Sort by decay_weighted_severity with fallback to raw magnitude for backward compat"

patterns-established:
  - "Conditional column display: check data availability in template with selectattr filter"
  - "Compound scoring modifier: weighted_sum/raw_sum ratio applied as multiplier"

requirements-completed: [STOCK-06, STOCK-08, STOCK-09]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 90 Plan 02: Pipeline Wiring + F2 Scoring + Rendering Summary

**Full pipeline integration of decay/decomposition/disclosure into extraction, F2 compound scoring modifier, and HTML/Word drops table with 5 new columns**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T13:29:13Z
- **Completed:** 2026-03-09T13:34:00Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Wired decompose_drops, apply_decay_weights, and enrich_drops_with_reverse_lookup into extraction pipeline (steps 8a-8c)
- Added compound F2 scoring modifier: contribution = magnitude * decay_weight * company_pct_ratio * disclosure_mult
- Extended HTML drops table with Recency, Market, Sector, Company, Disclosure columns (conditionally displayed)
- Extended Word renderer with same columns plus Market-Driven badge
- Drops table now sorted by decay-weighted severity (recent severe drops rank first)
- 21 new tests (9 F2 scoring + 12 rendering)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire computations into extraction pipeline and add F2 scoring modifiers** - `1e91c86` (feat, TDD)
2. **Task 2: Extend HTML template and context builder with new drop columns** - `33f0bbd` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/stock_performance.py` - Steps 8a-8c: decomposition, decay, reverse lookup in pipeline
- `src/do_uw/stages/score/factor_data.py` - drop_contributions list in _get_f2_data
- `src/do_uw/stages/score/factor_scoring.py` - _apply_drop_contribution_modifier function
- `src/do_uw/stages/render/context_builders/market.py` - 7 new fields per drop + _format_disclosure_badge + decay-sorted
- `src/do_uw/templates/html/sections/market/stock_drops.html.j2` - Recency/Market/Sector/Company/Disclosure columns
- `src/do_uw/stages/render/sections/sect4_drop_tables.py` - Word table with same new columns
- `tests/stages/score/test_factor_scoring_f2_decay.py` - 9 TDD tests for compound modifier
- `tests/stages/render/test_market_context_drops.py` - 12 tests for badge formatting, fields, sort order

## Decisions Made
- Compound modifier placed after insider amplifier and market cap multiplier in F2 scoring chain (follows existing pattern, modifiers compound multiplicatively)
- Decomposition columns only shown when at least one drop has market_pct data (avoids N/A clutter)
- Disclosure column only shown when at least one drop has corrective disclosure (same conditional pattern)
- Sort order uses decay_weighted_severity with fallback to raw magnitude for drops without decay data

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 90 (Drop Enhancements) is now complete
- All 9 new StockDropEvent fields are populated during extraction, used in scoring, and displayed in rendering
- Ready for Phase 91 (Display Centralization) and Phase 92 (Rendering Completeness)

## Self-Check: PASSED

- All 8 files verified present
- Both commits (1e91c86, 33f0bbd) verified in git log
- 176 related tests pass (9 F2 decay + 12 render drops + 114 score + 11 stock perf + 15 decay + 9 decomp + 15 enrichment)

---
*Phase: 90-drop-enhancements*
*Completed: 2026-03-09*
