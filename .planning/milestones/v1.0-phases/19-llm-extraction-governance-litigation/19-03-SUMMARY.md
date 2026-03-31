---
phase: 19
plan: 03
subsystem: extraction
tags: [llm, litigation, converter, risk-factors, contingencies, forum-provisions]
depends_on:
  requires: [19-01]
  provides: ["llm_litigation.py converter", "RiskFactorProfile model", "litigation converter tests"]
  affects: [19-04]
tech_stack:
  added: []
  patterns: ["LLM extraction converter pattern (TenKExtraction -> domain models)", "Cross-domain converter (DEF14A -> ForumProvisions)"]
key_files:
  created:
    - src/do_uw/stages/extract/llm_litigation.py
    - tests/test_llm_litigation_converter.py
  modified:
    - src/do_uw/models/state.py
decisions: []
metrics:
  duration: "4m"
  completed: "2026-02-10"
  test_count: 38
  test_result: "all pass"
  line_count: 366
---

# Phase 19 Plan 03: Litigation Converter Summary

**One-liner:** TenKExtraction litigation/contingency/risk-factor converter with legal theory inference, coverage type mapping, and cross-domain DEF14A forum provisions.

## What Was Done

### Task 1: RiskFactorProfile Model + Litigation Converter (366 lines)

Added `RiskFactorProfile` model to `state.py` as a cross-domain model on `ExtractedData`. Created `llm_litigation.py` with:

**4 public converter functions:**
- `convert_legal_proceedings(TenKExtraction) -> list[CaseDetail]` -- Maps Item 3 legal proceedings with date parsing, legal theory inference from allegation text, coverage type derivation, named defendants, settlement amounts, and class period dates
- `convert_contingencies(TenKExtraction) -> list[ContingentLiability]` -- Maps ASC 450 contingent liabilities from structured `ExtractedContingency` models with classification, accrued amounts, and loss ranges
- `convert_risk_factors(TenKExtraction) -> list[RiskFactorProfile]` -- Maps Item 1A risk factors with D&O relevance inference from category (LITIGATION/REGULATORY -> HIGH, FINANCIAL/CYBER -> MEDIUM, else LOW)
- `convert_forum_provisions(DEF14AExtraction) -> ForumProvisions` -- Cross-domain: maps DEF 14A proxy forum provisions to litigation defense model

**3 private helpers:**
- `_parse_date(str | None) -> date | None` -- YYYY-MM-DD parsing with graceful None fallback
- `_infer_legal_theories(str) -> list[str]` -- Keyword matching against 12 legal theory categories (10b-5, Section 11, ERISA, FCPA, etc.)
- `_infer_coverage_type(list[str]) -> str` -- Priority-based coverage type derivation from legal theories

### Task 2: Unit Tests (38 tests, all pass)

Comprehensive test coverage across all public and private functions:
- 10 tests for legal proceedings (count, skip empty, sourced values, dates, theories, coverage, defendants, settlement, class period, employment coverage)
- 5 tests for contingencies (count, skip empty, amounts, classification, source note)
- 6 tests for risk factors (count, relevance inference, skip empty, source, new_this_year, regulatory)
- 2 tests for forum provisions (basic mapping, None values)
- 4 tests for date parsing (valid, invalid, None, empty)
- 5 tests for legal theory inference (single, multiple, case-insensitive, empty, no match)
- 6 tests for coverage type inference (securities, derivative, ERISA, product, default, priority)

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

- pyright strict: 0 errors
- ruff: 0 errors
- Line count: 366 (under 500 limit)
- Full test suite: 2197 passed, 14 skipped, 3 xfailed

## Next Phase Readiness

Plan 19-04 (integration orchestrator) can now wire both `llm_governance.py` (from 19-02) and `llm_litigation.py` (from 19-03) into the extract pipeline.
