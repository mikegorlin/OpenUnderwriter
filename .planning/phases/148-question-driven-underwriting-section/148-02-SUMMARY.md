---
phase: 148-question-driven-underwriting-section
plan: 02
subsystem: render/context_builders/answerers
tags: [sca, questions, supabase, litigation, underwriting]
dependency_graph:
  requires: []
  provides: [generate_sca_questions, answer_sca_question]
  affects: [uw_questions.py]
tech_stack:
  added: []
  patterns: [domain-slotted-questions, source-badge-tagging]
key_files:
  created:
    - src/do_uw/stages/render/context_builders/answerers/__init__.py
    - src/do_uw/stages/render/context_builders/answerers/sca_questions.py
    - tests/render/test_sca_questions.py
  modified: []
decisions:
  - "SCA questions use safe_float for all numeric conversion (no bare float())"
  - "Scenario tag truncated to 8 chars uppercase for question_id suffix"
  - "DOWNGRADE threshold for trigger patterns: any multiplier > 5x"
  - "Peer comparison DOWNGRADE threshold: > 500 total filings across scenarios"
metrics:
  duration: 184s
  completed: "2026-03-28T20:40:43Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 3
  files_modified: 0
  tests_added: 7
  tests_passing: 7
---

# Phase 148 Plan 02: SCA Question Generator Summary

Dynamic SCA question generator producing Supabase-derived underwriting questions from risk card data, slotted into matching domains with "SCA Data" source badges.

## What Was Built

### `sca_questions.py` -- SCA Question Generator

**Exports:** `generate_sca_questions(state, ctx)`, `answer_sca_question(q, state, ctx)`

Generates questions from 4 SCA scenario types per D-05:

1. **Filing frequency & recidivism** (SCA-LIT-01) -> `litigation_claims` domain. Always generated. Clean-record companies get UPGRADE verdict. Repeat/chronic filers get DOWNGRADE with filing count, settlement rate, and total exposure.

2. **Settlement severity** (SCA-LIT-{SCENARIO}) -> `litigation_claims` domain. One per scenario in benchmarks. Includes median, P25, P75, P90 dollar amounts. DOWNGRADE if company has this scenario in its filing history.

3. **Peer SCA comparison** (SCA-MKT-01) -> `stock_market` domain. Aggregates total filings and average stock drop across scenario types. DOWNGRADE if > 500 total filings.

4. **Trigger patterns** (SCA-OPS-01) -> `operational_emerging` domain. Reports SEC investigation and restatement severity multipliers. DOWNGRADE if any multiplier > 5x.

**Data access:** Reads from `ctx["litigation"]` keys first (`risk_card_filing_history`, `risk_card_repeat_filer`, `risk_card_scenario_benchmarks`), falls back to `state.acquired_data.litigation_data.risk_card`.

**`answer_sca_question`:** Re-answers a pre-generated SCA question from current data (for refresh scenarios).

### `answerers/__init__.py` -- Package Init

Minimal package init for the answerers subpackage.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 2e423d41 | SCA question generator with 4 scenario types |
| 2 | 5529f520 | 7 tests covering all scenario types and edge cases |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created answerers/ package directory**
- **Found during:** Task 1
- **Issue:** The `answerers/` subdirectory did not exist
- **Fix:** Created directory with `__init__.py`
- **Files created:** `answerers/__init__.py`

**2. [Rule 3 - Blocking] Reverted linter auto-expansion of __init__.py**
- **Found during:** Tasks 1 and 2
- **Issue:** A linter/formatter automatically expanded the minimal `__init__.py` to import non-existent domain modules (company, decision, financial, etc.), which would cause ImportErrors
- **Fix:** Reverted to minimal package init each time
- **Files modified:** `answerers/__init__.py`

## Known Stubs

None -- all question types are fully wired to risk card data.

## Self-Check: PASSED
