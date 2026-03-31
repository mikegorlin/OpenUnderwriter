---
phase: 19
plan: 01
subsystem: extract-llm-schemas
tags: [pydantic, llm-extraction, schemas, deserialization]
dependency-graph:
  requires: [18]
  provides: [expanded-llm-schemas, llm-deserialization-helpers]
  affects: [19-02, 19-03, 19-04]
tech-stack:
  added: []
  patterns: [shared-deserialization-pattern, typed-extraction-models]
key-files:
  created:
    - src/do_uw/stages/extract/llm_helpers.py
  modified:
    - src/do_uw/stages/extract/llm/schemas/common.py
    - src/do_uw/stages/extract/llm/schemas/def14a.py
    - src/do_uw/stages/extract/llm/schemas/ten_k.py
    - src/do_uw/stages/extract/llm/schemas/__init__.py
decisions:
  - ExtractedContingency as structured model replacing bare strings for ASC 450 contingencies
  - get_llm_ten_k falls back to 20-F key prefix for foreign private issuers
metrics:
  duration: 3m 29s
  completed: 2026-02-10
---

# Phase 19 Plan 01: Schema Expansion and LLM Helpers Summary

Expanded Phase 18 LLM extraction schemas with structured contingency model, legal proceeding enrichment, and clawback fields; created shared deserialization helpers for typed access to LLM extraction results.

## Completed Tasks

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Expand LLM extraction schemas | 0fe02b0 | ExtractedContingency model, 3 new ExtractedLegalProceeding fields, 2 new DEF14AExtraction fields, TenKExtraction type change |
| 2 | Create shared LLM deserialization helpers | ef22cf0 | get_llm_def14a(), get_llm_ten_k(), _get_llm_extraction() |

## Decisions Made

1. **ExtractedContingency as structured model** -- Replaced `list[str]` with `list[ExtractedContingency]` on `TenKExtraction.contingent_liabilities`. The structured model has 6 fields (description, classification, accrued_amount, range_low, range_high, source_passage) enabling proper ASC 450 analysis downstream.

2. **20-F fallback in get_llm_ten_k** -- Foreign private issuers file 20-F instead of 10-K. The helper tries `"10-K:"` prefix first, then falls back to `"20-F:"`, since both use `TenKExtraction` schema.

## Verification Results

- pyright: 0 errors across all modified files
- ruff: all checks passed
- pytest: 2146 passed, 14 skipped, 3 xfailed, 1 xpassed (all existing tests pass)
- All files under 500 lines (llm_helpers.py: 75 lines)

## Deviations from Plan

None -- plan executed exactly as written.

## Next Phase Readiness

Plans 19-02 through 19-04 can now import:
- `ExtractedContingency` from `do_uw.stages.extract.llm.schemas`
- `get_llm_def14a()` and `get_llm_ten_k()` from `do_uw.stages.extract.llm_helpers`

All converter modules in subsequent plans will use these shared helpers for typed deserialization.
