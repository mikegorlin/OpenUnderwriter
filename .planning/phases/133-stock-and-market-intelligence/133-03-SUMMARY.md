---
phase: 133-stock-and-market-intelligence
plan: "03"
subsystem: render/context_builders
tags: [earnings-reactions, correlation, gap-closure, tech-debt]
dependency_graph:
  requires: [133-01, 133-02]
  provides: [STOCK-04-complete]
  affects: [market-section-rendering]
tech_stack:
  added: []
  patterns: [computed-fallback-with-model-priority]
key_files:
  created: []
  modified:
    - src/do_uw/stages/render/context_builders/_market_acquired_data.py
    - src/do_uw/stages/render/context_builders/_market_correlation.py
    - tests/stages/render/test_market_context_phase133.py
decisions:
  - Quarter dates from model preferred over yfinance earnings_dates for reaction lookup
  - Multi-window returns use model fields first, computed reactions as fallback
metrics:
  duration: 195s
  completed: "2026-03-27T05:02:48Z"
  tasks: 2
  files: 3
---

# Phase 133 Plan 03: STOCK-04 Gap Closure Summary

Wire orphaned compute_earnings_reactions() into build_earnings_trust() so earnings reaction table renders real multi-window returns instead of N/A, plus deduplicate correlation functions.

## What Was Done

### Task 1: Wire compute_earnings_reactions() into build_earnings_trust()
- Imported `compute_earnings_reactions` from `stages/extract/earnings_reactions.py`
- Added computation block before the quarter loop that builds a `reaction_lookup` dict from price history
- Replaced the old getattr-based next_day/week_ret logic with model-field-first, computed-fallback pattern
- Added day_of_return fallback from computed reactions when model field is None
- Removed outdated "Plan 01 dep" comment
- Added test `test_build_earnings_trust_populates_multi_window_returns` verifying non-N/A returns
- **Commit:** a478b8f7

### Task 2: Deduplicate correlation functions in _market_correlation.py
- Removed local `_compute_correlation()` (26 lines) and `_compute_r_squared()` (6 lines)
- Imported canonical `compute_correlation` and `compute_r_squared` from `chart_computations.py`
- Updated all call sites within `build_correlation_metrics()`
- **Commit:** 6abfcbb4

## Verification Results

- `tests/stages/render/test_market_context_phase133.py`: 12 passed
- `tests/stages/extract/test_earnings_reactions.py`: 11 passed
- `tests/stages/render/test_chart_computations_correlation.py`: 8 passed
- `tests/stages/render/test_market_templates.py`: 16 passed
- `tests/stages/render/test_market_context_drops.py`: 13 passed
- Total: 60 tests passed, 0 failures

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all data paths are wired end-to-end.

## Self-Check: PASSED
