---
phase: 55-declarative-mapping-structured-evaluation
verified: 2026-03-01T20:16:21Z
status: gaps_found
score: 7/9 requirements verified
gaps:
  - truth: "EVAL-02: Formula evaluation supports arithmetic expressions and built-in functions count_within, years_since, pct_change"
    status: failed
    reason: "REQUIREMENTS.md explicitly names count_within, years_since, pct_change as required built-in functions. None of these are implemented in COMPUTED_FUNCTIONS or anywhere in the V2 evaluation path. The implementation supports COMPUTED function dispatch (8 functions) but not the three named built-ins. The Research doc narrowed scope to 'field reference + COMPUTED dispatch' but REQUIREMENTS.md is the contract."
    artifacts:
      - path: "src/do_uw/brain/field_registry_functions.py"
        issue: "COMPUTED_FUNCTIONS dict has count_items, count_active_scas, etc. but NOT count_within, years_since, pct_change"
      - path: "src/do_uw/stages/analyze/declarative_mapper.py"
        issue: "map_v2_signal() treats formula as a single field_key reference only; no arithmetic expression evaluation"
    missing:
      - "count_within function in COMPUTED_FUNCTIONS (count items within a date window)"
      - "years_since function in COMPUTED_FUNCTIONS (years elapsed from a date)"
      - "pct_change function in COMPUTED_FUNCTIONS (percentage change between two values)"
      - "Multi-field arithmetic formula support in declarative_mapper.py (or explicit deferral documented in REQUIREMENTS.md)"

  - truth: "EVAL-05: Shadow evaluation switches signal to V2 primary when discrepancy count is zero across last 3 ticker runs"
    status: partial
    reason: "Shadow evaluation infrastructure IS implemented: both V2 and legacy paths run, discrepancies log to DuckDB brain_shadow_evaluations, mismatches warn to console. However, the automatic V2-switch trigger based on 'zero discrepancies across last 3 ticker runs' is not implemented. _evaluate_v2_signal always returns the legacy result; no code reads accumulated shadow data to promote a signal to V2-primary. REQUIREMENTS.md states 'Signal only switches to V2 when discrepancy count is zero across last 3 ticker runs' — the switching mechanism is missing."
    artifacts:
      - path: "src/do_uw/stages/analyze/signal_engine.py"
        issue: "_evaluate_v2_signal always returns legacy_result (line 254). No code checks DuckDB shadow history to auto-promote to V2 primary. Comment on line 253 says 'Plan 03 will switch to V2 for fully-migrated prefixes' but Plan 03 did not implement this."
    missing:
      - "Automatic V2 promotion logic: query brain_shadow_evaluations for signal's last N runs, check is_match rate, switch to V2 primary when zero discrepancies"
      - "OR: explicit REQUIREMENTS.md update or deferral doc acknowledging this is a Phase 56/57 concern"
human_verification:
  - test: "Run a real ticker through the pipeline and check shadow evaluation DuckDB table"
    expected: "brain_shadow_evaluations table populated with FIN.LIQ signal comparisons; is_match=TRUE for all 5 FIN.LIQ signals"
    why_human: "Requires an actual pipeline run with a real ticker and real SEC data to verify shadow evaluation fires correctly end-to-end"
---

# Phase 55: Declarative Mapping + Structured Evaluation Verification Report

**Phase Goal:** Signals with V2 paths resolve data declaratively via field registry. Signals with V2 thresholds evaluate via structured operators. Shadow evaluation proves parity. At least one full prefix migrated end-to-end.
**Verified:** 2026-03-01T20:16:21Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | V2 signals resolve data via field registry paths (DIRECT_LOOKUP + COMPUTED) | VERIFIED | declarative_mapper.py: resolve_field() dispatches to DIRECT_LOOKUP (dotted-path + key) or COMPUTED (function dispatch). 14 mapper tests pass. |
| 2 | SourcedValue auto-unwrap via duck-typing at each traversal step | VERIFIED | resolve_path() checks hasattr(obj, "value/source/confidence") at each segment. Propagates source/confidence metadata. Tests confirm. |
| 3 | V2 evaluator handles operator-based {op, value, label} thresholds | VERIFIED | structured_evaluator.py: evaluate_v2() with all 8 operators. 28 evaluator tests pass. |
| 4 | Edge cases: None->SKIPPED, N/A->SKIPPED, empty list->0, qualitative clear | VERIFIED | _MISSING_VALUES frozenset handles N/A variants. clear_conditions via ClearCondition Pydantic model (added Plan 03). Tests confirm all cases. |
| 5 | Shadow evaluation runs both V2 and legacy paths for V2 signals | VERIFIED | _evaluate_v2_signal() runs map_v2_signal+evaluate_v2 AND evaluate_signal, compares status+level. 11 shadow eval tests pass. DuckDB logging fire-and-forget. |
| 6 | V1 signals and V2 signals without evaluation section use legacy path unchanged | VERIFIED | Guard in _evaluate_v2_signal: returns None if no evaluation section. V1 check: sig.get("schema_version", 1) < 2. Tests confirm V1 bypass. |
| 7 | At least one full prefix (FIN.LIQ) migrated with FIELD_FOR_CHECK entries removed | VERIFIED | All 5 FIN.LIQ signals have schema_version: 2 with acquisition/evaluation/presentation. FIELD_FOR_CHECK shows tombstone comment only. 10 regression tests pass. |
| 8 | Formula evaluation supports arithmetic expressions and built-in functions (count_within, years_since, pct_change) | FAILED | Formula is treated as a field_key reference to a single field. count_within, years_since, pct_change are not in COMPUTED_FUNCTIONS. EVAL-02 requirement partially met. |
| 9 | Shadow evaluation switches signal to V2 primary when zero discrepancies across last 3 runs | PARTIAL | Shadow infrastructure exists (DuckDB logging, discrepancy detection). Auto-switch trigger not implemented — always returns legacy result. EVAL-05 requirement partially met. |

**Score:** 7/9 truths verified (plus 2 partial)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/analyze/declarative_mapper.py` | resolve_field, map_v2_signal for V2 signal data resolution | VERIFIED | 259 lines. Exports resolve_field, resolve_path, map_v2_signal. Fully substantive. |
| `src/do_uw/stages/analyze/structured_evaluator.py` | evaluate_v2() with 8 operators | VERIFIED | 226 lines. All 8 operators, clear_conditions, edge cases. |
| `src/do_uw/brain/field_registry_functions.py` | COMPUTED_FUNCTIONS dict | VERIFIED | 199 lines. 8 functions: count_items, count_active_scas, compute_board_independence_pct, compute_cash_burn_months, etc. Missing count_within/years_since/pct_change per EVAL-02. |
| `src/do_uw/brain/field_registry.yaml` | 17+ entries including cash_ratio and cash_burn_months | VERIFIED | 17 fields confirmed via load_field_registry(). cash_ratio (DIRECT_LOOKUP) and cash_burn_months (COMPUTED) both present. |
| `src/do_uw/stages/analyze/signal_engine.py` | _evaluate_v2_signal with V2 dispatch + shadow eval | VERIFIED | 579 lines. _evaluate_v2_signal replaces stub. shadow comparison + DuckDB logging. NOTE: over 500-line limit per CLAUDE.md. |
| `src/do_uw/brain/brain_schema.py` | brain_shadow_evaluations DDL | VERIFIED | CREATE TABLE IF NOT EXISTS brain_shadow_evaluations at line 362. Two indexes added. |
| `tests/stages/analyze/test_shadow_evaluation.py` | Shadow evaluation unit + integration tests | VERIFIED | 18,185 bytes. 11 tests: shadow comparison, V2 dispatch integration, DuckDB logging, classification metadata. |
| `src/do_uw/brain/signals/fin/balance.yaml` | V2 YAML for all 5 FIN.LIQ signals | VERIFIED | All 5 FIN.LIQ signals have schema_version: 2, acquisition, evaluation (with thresholds), presentation. Confirmed via runtime check. |
| `src/do_uw/stages/analyze/signal_field_routing.py` | FIELD_FOR_CHECK with FIN.LIQ entries removed | VERIFIED | Only tombstone comment: "# FIN.LIQ — migrated to V2 declarative mapping (Phase 55)". 258 remaining entries, 0 FIN.LIQ. |
| `src/do_uw/cli_brain.py` | brain status with shadow eval summary | VERIFIED | Queries brain_shadow_evaluations table, shows total/match/mismatch counts, top 5 discrepant signals. Wrapped in try/except. |
| `tests/brain/test_v2_migration.py` | FIN.LIQ migration regression tests | VERIFIED | TestFINLIQMigration class with 10 tests: position RED/YELLOW/CLEAR, efficiency RED, cash_burn qualitative clear, cash_burn RED, rollback to V1, V2 count. All pass. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| declarative_mapper.py | brain/field_registry.py | get_field_entry() lookup | WIRED | Import at line 24: `from do_uw.brain.field_registry import ... get_field_entry` |
| declarative_mapper.py | brain/field_registry_functions.py | COMPUTED_FUNCTIONS dispatch via get_computed_function | WIRED | get_computed_function() in field_registry.py lazy-imports COMPUTED_FUNCTIONS |
| structured_evaluator.py | stages/analyze/signal_helpers.py | coerce_value, extract_factors, make_skipped | WIRED | Import at line 22-26: `from do_uw.stages.analyze.signal_helpers import ...` |
| signal_engine.py | declarative_mapper.py | map_v2_signal() in V2 dispatch path | WIRED | Import at line 16. Used at line 205 in _evaluate_v2_signal. |
| signal_engine.py | structured_evaluator.py | evaluate_v2() in V2 dispatch path | WIRED | Import at line 32. Used at line 208 in _evaluate_v2_signal. |
| signal_engine.py | brain_schema.py | DuckDB shadow evaluation logging | WIRED | INSERT INTO brain_shadow_evaluations at line 282. DDL confirmed in brain_schema.py line 362. |
| balance.yaml | declarative_mapper.py | V2 evaluation.formula references field_registry entries | WIRED | All 5 FIN.LIQ formulas (current_ratio, cash_ratio, cash_burn_months) confirmed in field_registry.yaml. |
| signal_field_routing.py | balance.yaml | FIELD_FOR_CHECK entries removed for FIN.LIQ | WIRED | Tombstone comment only. Runtime check: 0 FIN.LIQ entries remain. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| MAP-01 | 55-01 | Declarative mapper resolves DIRECT_LOOKUP and COMPUTED fields | SATISFIED | resolve_field() dispatches both types. 14 mapper tests pass. |
| MAP-02 | 55-01 | SourcedValue-aware path resolver with dual roots | SATISFIED | resolve_path() unwraps SourcedValue at each step via duck-typing. Dual roots (extracted.*, company.*) confirmed in code and tests. |
| MAP-03 | 55-02 | Legacy fallback for signals without V2 acquisition | SATISFIED | guard in _evaluate_v2_signal returns None if no evaluation section. V1 signals skip V2 dispatch entirely. Tests confirm. |
| MAP-04 | 55-03 | FIN.LIQ prefix migrated, FIELD_FOR_CHECK entries removed | PARTIALLY SATISFIED | All 5 FIN.LIQ signals have V2 YAML. FIELD_FOR_CHECK entries removed. BUT: _evaluate_v2_signal still returns legacy result during shadow phase — V2 is not the exclusive evaluator for final results. Word "exclusively" in requirement is not fully achieved. |
| EVAL-01 | 55-01 | Structured evaluator with {op, value} operators (8 operators) | SATISFIED | All 8 operators implemented: <, >, <=, >=, ==, !=, between, contains. 28 evaluator tests pass. |
| EVAL-02 | 55-01 | Formula evaluation for single-field, multi-field, and built-in functions count_within/years_since/pct_change | BLOCKED | Formula is treated as a single field_key reference only. count_within, years_since, pct_change not in COMPUTED_FUNCTIONS. Multi-field arithmetic formulas not supported. REQUIREMENTS.md explicitly names these three functions. |
| EVAL-03 | 55-01 | Edge cases: None->SKIPPED, empty list->0, N/A->missing | SATISFIED | _MISSING_VALUES frozenset, make_skipped() on None/empty, count_items returns 0 for None/empty. Tests confirm. |
| EVAL-04 | 55-02 | Legacy fallback for signals without V2 evaluation section | SATISFIED | V2 signals without evaluation section return None from _evaluate_v2_signal, falling through to legacy. Tests confirm. |
| EVAL-05 | 55-02 | Shadow evaluation mode: both evaluators run, discrepancies logged, signal switches to V2 at zero discrepancies | PARTIALLY SATISFIED | Shadow evaluation runs both paths and logs to DuckDB. Discrepancy warnings via logger.warning. BUT: auto-switch mechanism (based on last 3 ticker runs with zero discrepancies) is not implemented. Always returns legacy result. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `signal_engine.py` | — | 579 lines (over 500-line limit per CLAUDE.md) | Warning | Deferred item per 55-02 SUMMARY. Shadow eval adds ~138 lines. No functional impact, but violates Anti-Context-Rot rule. |

### Human Verification Required

#### 1. End-to-End Pipeline Shadow Evaluation

**Test:** Run `uv run python -m do_uw.cli analyze AAPL` and then query `brain_shadow_evaluations` table in brain.duckdb for FIN.LIQ signals.
**Expected:** All 5 FIN.LIQ signals appear in brain_shadow_evaluations with is_match=TRUE (zero discrepancies between V2 and legacy paths).
**Why human:** Requires a real pipeline run with real SEC data. Automated tests use mocked ExtractedData. Real data path differences could cause discrepancies not visible in unit tests.

---

## Gaps Summary

### Gap 1: EVAL-02 — Missing built-in functions (BLOCKER for requirement)

REQUIREMENTS.md for EVAL-02 explicitly states: "built-in functions (`count_within`, `years_since`, `pct_change`)". These three functions are named requirements, not examples. None appear in `field_registry_functions.py`, `declarative_mapper.py`, or anywhere in the V2 evaluation path.

The implementation does provide COMPUTED function dispatch (8 functions), which covers many real needs, but the three named functions are missing. The Research doc re-scoped EVAL-02 as "field reference + COMPUTED dispatch" — but the Research doc does not override REQUIREMENTS.md.

**Root cause:** The plan's task spec for `field_registry_functions.py` focused on functions needed for FIN.LIQ migration (count_items, compute_cash_burn_months, etc.) and did not implement the three EVAL-02-named built-ins.

**Fix:** Add `count_within`, `years_since`, and `pct_change` to COMPUTED_FUNCTIONS — or formally update REQUIREMENTS.md to document that these three built-ins are deferred to Phase 56/57.

### Gap 2: EVAL-05 — Auto-switch mechanism missing (PARTIAL)

REQUIREMENTS.md for EVAL-05 says signals switch to V2 primary "when discrepancy count is zero across last 3 ticker runs." The shadow evaluation infrastructure is fully in place (DuckDB logging, discrepancy detection, console warnings). What's missing is the auto-switch trigger: code that reads accumulated shadow data and promotes a signal from shadow-phase (returns legacy) to V2-primary (returns V2 result).

The current design always returns legacy. No code reads `brain_shadow_evaluations` to promote signals. The comment at signal_engine.py line 253 says "Plan 03 will switch to V2 for fully-migrated prefixes" — but Plan 03 did not implement this.

**Root cause:** The Plan 02/03 design decision was deliberate: "shadow phase returns LEGACY result." The promotion mechanism was expected to be a separate future step, not implemented in Phase 55.

**Fix:** Either implement the auto-promotion logic (read DuckDB shadow history, switch to V2 when zero discrepancies across 3+ runs), or formally document in REQUIREMENTS.md that auto-switch is a Phase 56/57 milestone.

### Note on MAP-04 Interpretation

MAP-04 says "use declarative mapping exclusively." The V2 path does run for FIN.LIQ signals, but the result returned is from the legacy evaluator (shadow phase). This means FIN.LIQ does NOT use declarative mapping "exclusively" for its output — the legacy path still determines the result.

However, this interpretation may be too strict. The shadow evaluation architecture was designed so that:
1. V2 declarative path runs and is validated
2. Legacy result is returned only until zero discrepancies are confirmed
3. At that point the signal "switches to V2" (EVAL-05)

So MAP-04 and EVAL-05 are interdependent — MAP-04 cannot be fully satisfied until EVAL-05's switch mechanism fires. This makes Gap 2 (EVAL-05) the root cause of MAP-04's "exclusively" gap.

---

_Verified: 2026-03-01T20:16:21Z_
_Verifier: Claude (gsd-verifier)_
