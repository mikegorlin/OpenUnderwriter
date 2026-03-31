---
phase: 71-form4-enhancement
plan: 02
subsystem: insider-trading-patterns
tags: [form4, exercise-sell, filing-timing, brain-signal, 8-K]
dependency_graph:
  requires: [InsiderTransaction-v2, OwnershipConcentrationAlert]
  provides: [ExerciseSellEvent, FilingTimingSuspect, exercise-sell-detection, filing-timing-analysis]
  affects: [insider_trading.py, market_events.py, signal_field_routing.py, governance-facet]
tech_stack:
  added: []
  patterns: [file-split-for-500-line-compliance, 8k-item-classification, bidirectional-timing-window]
key_files:
  created:
    - src/do_uw/stages/extract/insider_trading_patterns.py
    - tests/test_insider_form4_patterns.py
  modified:
    - src/do_uw/models/market_events.py
    - src/do_uw/stages/extract/insider_trading.py
    - src/do_uw/brain/signals/gov/insider.yaml
    - src/do_uw/stages/analyze/signal_field_routing.py
    - src/do_uw/stages/analyze/signal_mappers_sections.py
    - src/do_uw/brain/enrichment_data.py
    - src/do_uw/brain/sections/governance.yaml
decisions:
  - Moved get_eight_k_filings to insider_trading_patterns.py for 500-line compliance
  - 8-K item classification is deterministic (no LLM) per user decision
  - Exercise-sell severity always AMBER per user decision
  - Ownership concentration severity routing added to mapper alongside new fields
metrics:
  duration_seconds: 399
  completed: "2026-03-06T22:12:13Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 17
  tests_total: 65
  files_created: 2
  files_modified: 7
---

# Phase 71 Plan 02: Pattern Detection + Filing Timing Summary

Exercise-sell pattern detection (M+S same owner, 1-day tolerance) and bidirectional filing timing analysis (60-day window before material 8-K events) with 3 brain signals wired to governance facet.

## Tasks Completed

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | Exercise-sell pattern detection + filing timing analysis | 2fd2cd7 | ExerciseSellEvent/FilingTimingSuspect models, detect_exercise_sell_patterns, analyze_filing_timing, classify_8k_item, 17 TDD tests |
| 2 | Brain signals for exercise-sell and timing patterns | 785717f | 2 new signals + 1 reactivated, field routing, mapper data resolution, enrichment+facet wiring |

## What Was Built

### Models (market_events.py)
- **ExerciseSellEvent**: owner, date, exercised/sold shares+value, severity=AMBER, is_10b5_1
- **FilingTimingSuspect**: insider_name, transaction/filing dates, 8-K item, sentiment, days_before, severity (RED_FLAG/AMBER)
- **InsiderTradingAnalysis**: New fields exercise_sell_events and timing_suspects

### Pattern Detection (insider_trading_patterns.py - 284 lines)
- **detect_exercise_sell_patterns**: Groups by owner, finds M+S on T+0 or T+1, aggregates totals, always AMBER
- **classify_8k_item**: NEGATIVE (2.02/5.02/4.02), POSITIVE (1.01/2.01), NEUTRAL (everything else)
- **analyze_filing_timing**: 60-day window before 8-K filings, SELL-before-negative=RED_FLAG, BUY-before-positive=AMBER
- **get_eight_k_filings**: Extracts 8-K metadata from state.acquired_data.filings

### Brain Signals (gov/insider.yaml - now 11 signals)
- **GOV.INSIDER.exercise_sell**: exercise_sell_count field_key, AMBER threshold
- **GOV.INSIDER.timing_suspect**: timing_suspect_severity field_key, RED/AMBER tiers, weight 0.25
- **GOV.INSIDER.unusual_timing**: Reactivated with timing_suspect_count (was INACTIVE)

### Signal Routing
- exercise_sell_count -> len(insider_analysis.exercise_sell_events)
- timing_suspect_severity -> max severity across timing_suspects
- timing_suspect_count -> len(insider_analysis.timing_suspects)
- ownership_concentration_severity -> max severity across ownership_alerts

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] get_eight_k_filings moved to patterns module**
- **Found during:** Task 1
- **Issue:** Adding _get_eight_k_filings to insider_trading.py pushed it to 509 lines (over 500 limit)
- **Fix:** Moved function to insider_trading_patterns.py as get_eight_k_filings (public), imported in insider_trading.py
- **Files modified:** insider_trading.py (488 lines), insider_trading_patterns.py (284 lines)

**2. [Rule 2 - Missing functionality] Ownership concentration severity routing**
- **Found during:** Task 2
- **Issue:** Plan 01 added ownership_concentration_severity to signal_field_routing.py but never resolved it in the mapper
- **Fix:** Added ownership_concentration_severity resolution in signal_mappers_sections.py (max severity from alerts)
- **Files modified:** signal_mappers_sections.py

## Verification

- 17 new tests + 48 existing insider tests = 65 passing
- Full test suite: 594 passed, 1 pre-existing failure (test_enriched_roundtrip -- unrelated)
- GOV.INSIDER signal count: 11 (8 original + 2 new + 1 reactivated)
- All modified files under 500 lines

## Self-Check: PASSED
