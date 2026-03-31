---
phase: 19
plan: 02
subsystem: extract-governance-converter
tags: [governance, converter, def14a, sourced-values, board-forensics, compensation]
dependency-graph:
  requires: [19-01]
  provides: [governance-converter-functions, board-forensic-profiles, compensation-analysis]
  affects: [19-04]
tech-stack:
  added: []
  patterns: [llm-extraction-converter, sourced-value-wrapping, title-based-ceo-identification]
key-files:
  created:
    - src/do_uw/stages/extract/llm_governance.py
    - tests/test_llm_governance_converter.py
  modified: []
decisions:
  - CEO identification uses title-based matching (contains "CEO" or "Chief Executive")
  - Overboarding threshold is 4+ total public board seats (other_boards + 1)
  - Pay ratio parsing supports three formats: "123:1", "123 to 1", bare "123"
metrics:
  duration: 3m 13s
  completed: 2026-02-10
---

# Phase 19 Plan 02: Governance Converter Summary

Built governance converter mapping DEF14AExtraction flat fields to rich domain models (BoardForensicProfile, CompensationAnalysis, BoardProfile, CompensationFlags, OwnershipAnalysis, LeadershipForensicProfile) with HIGH confidence and 'DEF 14A (LLM)' source attribution.

## Completed Tasks

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Create governance converter module | 8e1ae3f | 6 public converters + _parse_pay_ratio helper, 339 lines |
| 2 | Unit tests for governance converter | 2779b58 | 13 test functions covering all converters + edge cases |

## Decisions Made

1. **CEO identification by title** -- Searches NEO titles for "CEO" or "Chief Executive" (case-insensitive). Takes first match and breaks. This handles "Chairman and CEO", "Chief Executive Officer", etc.

2. **Overboarding threshold** -- Uses 4+ total public board seats (other_boards count + 1 for the current board). This matches ISS proxy advisory standards.

3. **Pay ratio parsing** -- Supports three common formats: "275:1" (colon), "275 to 1" (text), and bare "275" (number only). Handles comma-separated numbers. Returns None on parse failure.

4. **Sourced bool helper** -- Created `_sourced_bool()` private helper since no `sourced_bool` exists in sourced.py. Constructs `SourcedValue[bool]` with explicit `as_of=now()`.

## Verification Results

- pyright: 0 errors on llm_governance.py
- ruff: all checks passed
- pytest: 13/13 new tests pass
- Full suite: 2159 passed, 14 skipped, 3 xfailed, 1 xpassed
- llm_governance.py: 339 lines (under 500)

## Deviations from Plan

None -- plan executed exactly as written.

## Next Phase Readiness

Plan 19-04 (integration) can now import all 6 converter functions to wire into the governance extraction sub-orchestrator. The converters are stateless -- they take a DEF14AExtraction and return domain model instances, making integration straightforward.
