---
phase: 20
plan: 01
subsystem: extract-llm
tags: [schema, pydantic, 8-K, audit, llm-helpers, budget]
depends_on:
  requires: [19]
  provides: ["EightKExtraction.departing_officer_title", "AuditProfile.significant_deficiencies", "AuditProfile.remediation_status", "get_llm_eight_k()", "LLMExtractor budget $2.00"]
  affects: [20-02, 20-03, 20-04, 20-05, 20-06]
tech_stack:
  added: []
  patterns: ["multi-instance LLM extraction helper (list return vs single)"]
key_files:
  created:
    - tests/test_llm_helpers.py
  modified:
    - src/do_uw/stages/extract/llm/schemas/eight_k.py
    - src/do_uw/models/financials.py
    - src/do_uw/stages/extract/llm_helpers.py
    - src/do_uw/stages/extract/llm/extractor.py
decisions:
  - id: "20-01-D1"
    decision: "get_llm_eight_k returns list (not single) because companies file multiple 8-Ks per year"
    rationale: "Unlike 10-K and DEF 14A which are one-per-year, 8-Ks are event-driven and multi-instance"
metrics:
  duration: "3m 22s"
  tests_added: 6
  tests_total: 2227
  completed: "2026-02-10"
---

# Phase 20 Plan 01: Schema and Infrastructure Foundation Summary

**Batched schema/model changes and LLM helper additions to prevent multiple cache invalidation cycles.**

## What Was Done

### Task 1: Schema and Domain Model Expansions
- Added `departing_officer_title` field to `EightKExtraction` for officer severity classification (C-suite departures are higher risk than VP departures)
- Added `significant_deficiencies` (list) and `remediation_status` (optional) fields to `AuditProfile` for internal control tracking beyond material weaknesses
- All new fields have defaults so no existing code breaks

### Task 2: LLM Helpers and Budget Update
- Added `get_llm_eight_k()` to `llm_helpers.py` -- returns `list[EightKExtraction]` (multi-instance pattern, unlike single-result 10-K/DEF 14A helpers)
- Updated `LLMExtractor` default `budget_usd` from `$1.00` to `$2.00` per CONTEXT.md decision to accommodate expanded extraction coverage
- Created 6 comprehensive tests covering: multiple 8-Ks, no 8-Ks, invalid data, no acquired_data, title field preservation, malformed dicts

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 20-01-D1 | get_llm_eight_k returns list | 8-Ks are event-driven (multi-instance per company), unlike annual 10-K/DEF 14A |

## Verification

- pyright: 0 errors on all modified files
- ruff: All checks passed
- pytest: 2227 passed, 14 skipped, 3 xfailed, 1 xpassed (6 new tests)

## Next Phase Readiness

All schema changes are batched in this plan. Subsequent plans (20-02 through 20-06) can build converters and integrations without re-invalidating LLM caches.
