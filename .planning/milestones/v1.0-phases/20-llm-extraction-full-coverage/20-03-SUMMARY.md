---
phase: 20
plan: 03
subsystem: extract-llm
tags: [8-K, DEF-14A, converter, aggregation, ownership, SourcedValue]
depends_on:
  requires: [20-01]
  provides: ["eight_k_converter.py (5 aggregation converters)", "proxy_ownership_converter.py (ownership table parser)"]
  affects: [20-04, 20-05, 20-06]
tech_stack:
  added: []
  patterns: ["multi-instance aggregation (list[EightKExtraction] -> list[record])"]
key_files:
  created:
    - src/do_uw/stages/extract/eight_k_converter.py
    - src/do_uw/stages/extract/proxy_ownership_converter.py
    - tests/test_eight_k_converter.py
    - tests/test_proxy_ownership_converter.py
  modified: []
decisions:
  - id: "20-03-D1"
    decision: "Type aliases (DepartureRecord, AgreementRecord, etc.) for converter return types"
    rationale: "Keeps function signatures readable while maintaining pyright strict compliance"
metrics:
  duration: "3m 56s"
  tests_added: 26
  tests_total: 2285
  completed: "2026-02-10"
---

# Phase 20 Plan 03: 8-K Event Converter and Proxy Ownership Converter Summary

**8-K multi-instance aggregation across 5 event types plus DEF 14A ownership table parser with "Name: Percentage" format parsing.**

## What Was Done

### Task 1: eight_k_converter.py with Multi-Event Aggregation (309 lines)
- Created `convert_departures()` -- aggregates officer departure events across all 8-K extractions (name, title, reason, successor, is_termination, event_date)
- Created `convert_agreements()` -- aggregates material agreement events (type, counterparty, summary, event_date)
- Created `convert_acquisitions()` -- aggregates acquisition/disposition events (type, target, value as float, event_date)
- Created `convert_restatements()` -- aggregates restatement/non-reliance events (periods as list, reason, event_date)
- Created `convert_earnings_events()` -- aggregates revenue/EPS/guidance events (revenue, eps, guidance_update, event_date)
- All 5 converters take `list[EightKExtraction]` and filter by event-specific fields (departing_officer, agreement_type, etc.)
- Events without relevant fields silently skipped -- each 8-K typically covers one event type
- 17 unit tests: multi-instance aggregation, skip logic, empty input, optional field handling, mixed event types

### Task 2: proxy_ownership_converter.py with Ownership Table Parsing (136 lines)
- Created `convert_top_holders()` -- parses "Vanguard Group: 8.2%" format into `SourcedValue[dict[str, str]]` with name/percentage keys
- Created `convert_insider_ownership()` -- maps `officers_directors_ownership_pct` to `SourcedValue[float]`
- Created `convert_proxy_ownership_summary()` -- convenience combining both fields
- Edge cases: no colon separator (full string as name, "N/A" percentage), empty lists, None values, multiple colons
- 9 unit tests: holder parsing, empty list, no colon fallback, multiple colons, insider None, combined summary, partial data

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 20-03-D1 | Type aliases for converter return types | DepartureRecord, AgreementRecord, etc. keep signatures readable under pyright strict |

## Verification

- pyright: 0 errors on both converter files
- ruff: All checks passed
- pytest: 2285 passed, 14 skipped, 3 xfailed, 1 xpassed (26 new tests)
- Line counts: eight_k_converter.py 309, proxy_ownership_converter.py 136

## Next Phase Readiness

Both converter modules are ready for integration into sub-orchestrators (Plans 04-06). The 8-K converter consumes `get_llm_eight_k()` from Plan 01, and the proxy ownership converter consumes `get_llm_def14a()` from Phase 19. No blockers.
