---
phase: 4
plan: 6
subsystem: extract-market
tags: [earnings, guidance, capital-markets, section-11, adverse-events, scoring]
depends_on:
  requires: [04-01, 04-02, 04-03]
  provides: [SECT4-06, SECT4-07, SECT4-08, SECT4-09]
  affects: [04-09, 04-10, 04-11]
tech_stack:
  added: []
  patterns: [config-driven-scoring, severity-weight-aggregation, section-11-window]
key_files:
  created:
    - src/do_uw/stages/extract/earnings_guidance.py
    - src/do_uw/stages/extract/capital_markets.py
    - src/do_uw/stages/extract/adverse_events.py
    - src/do_uw/config/adverse_events.json
    - tests/test_earnings_capital_adverse.py
  modified: []
decisions:
  - Made classify_result, compute_consecutive_misses, compute_philosophy, compute_section_11_end, is_window_active public for testability
  - Used cast() pattern for yfinance dict-of-dicts data (earnings_dates, upgrades_downgrades) to satisfy pyright strict
  - Config-driven severity weights in adverse_events.json with 14 event types
  - Leap year handling for Section 11 window: Feb 29 filing rolls to March 1
metrics:
  duration: 7m 47s
  tests_added: 29
  completed: 2026-02-08
---

# Phase 4 Plan 6: Earnings Guidance, Capital Markets, Adverse Events Summary

Config-driven SECT4 extractors for earnings beat/miss (SECT4-06), analyst sentiment (SECT4-07), capital markets Section 11 windows (SECT4-08), and composite adverse event scoring (SECT4-09) with 14 severity weights.

## Tasks Completed

### Task 1: earnings_guidance.py and capital_markets.py

**earnings_guidance.py (496 lines):**
- `extract_earnings_guidance()`: Parses yfinance earnings_dates into EarningsQuarterRecord list, classifies BEAT/MISS/MEET with 1% tolerance, computes beat_rate, consecutive_miss_count, and philosophy (CONSERVATIVE/AGGRESSIVE/MIXED/NO_GUIDANCE)
- `extract_analyst_sentiment()`: Reads yfinance info/recommendations/upgrades_downgrades, extracts coverage count, consensus, recommendation mean, target prices, recent upgrades/downgrades (90-day window)
- Helper functions: `classify_result`, `compute_consecutive_misses`, `compute_philosophy` -- all public for testability

**capital_markets.py (309 lines):**
- `extract_capital_markets()`: Reads SEC filing metadata (S-1/S-3/424B forms), builds CapitalMarketsOffering records, computes Section 11 window (filing_date + 3 years), counts active windows
- Searches multiple filing storage locations: recent submissions format, filing_list, filing_documents
- ATM program detection from S-3ASR/F-3ASR/424B5 forms

### Task 2: adverse_events.py, config, and tests

**adverse_events.py (368 lines):**
- `compute_adverse_event_score()`: Aggregates all SECT4 results -- stock drops, insider clusters, earnings misses, analyst downgrades, Section 11 windows
- Loads severity weights from config/adverse_events.json via standard Path-based config loading
- Produces total_score, event_count, severity_breakdown (LOW/MEDIUM/HIGH/CRITICAL)
- Consecutive miss bonus: 3+ consecutive misses adds a separate penalty

**config/adverse_events.json:**
- 14 severity weights ranging from 0.5 (analyst_downgrade) to 4.0 (single_day_drop_20pct)
- Weights reflect D&O claim correlation from underwriting research

**tests/test_earnings_capital_adverse.py (407 lines, 29 tests):**
- 6 beat/miss classification tests (BEAT, MISS, MEET, magnitude, None handling)
- 3 consecutive miss tests (3 in a row, no streak, empty)
- 4 philosophy tests (CONSERVATIVE, AGGRESSIVE, MIXED, NO_GUIDANCE)
- 2 earnings integration tests (with data, no data)
- 5 Section 11 tests (window computation, leap year, invalid date, active/expired)
- 3 capital markets integration tests (with offerings, active count, no offerings)
- 6 adverse event scoring tests (full scoring, consecutive bonus, breakdown, empty, config loading, missing config)

## Decisions Made

1. **Public helper functions**: Made classify_result, compute_consecutive_misses, compute_philosophy, compute_section_11_end, is_window_active public (not underscore-prefixed) for direct testability, matching the pattern used in other extractors like distress_formulas.py
2. **cast() for yfinance data**: yfinance returns dict-of-dicts where pyright cannot infer inner types. Used cast(dict[str, Any], ...) after isinstance checks, consistent with project pattern.
3. **Section 11 leap year**: Filing date of Feb 29 in a leap year rolls to March 1 when adding 3 years to a non-leap year target.
4. **Config-driven scoring**: 14 event types with float severity weights in JSON, loadable with optional path override for testing.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

- ruff check: 0 errors
- pyright strict: 0 errors, 0 warnings
- pytest: 29/29 passed in 0.11s
- All files under 500 lines (max: 496 lines)

## Commits

| Hash | Message |
|------|---------|
| 896c45a | feat(04-06): earnings guidance, capital markets, adverse events extractors |
