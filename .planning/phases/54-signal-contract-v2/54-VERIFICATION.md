---
phase: 54-signal-contract-v2
verified: 2026-03-01T17:30:00Z
status: passed
score: 6/6 success criteria verified
re_verification: false
gaps: []
---

# Phase 54: Signal Contract V2 Verification Report

**Phase Goal:** Extend signal YAML with machine-readable acquisition, evaluation, and presentation sections. Add `schema_version` for dual-path dispatch and field registry for declarative resolution. Schema is additive — old signals keep working unchanged. 10-15 signals migrated as proof of concept.

**Verified:** 2026-03-01T17:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | BrainSignalEntry accepts optional `acquisition`, `evaluation`, and `presentation` V2 sections | VERIFIED | 6 Pydantic sub-models (AcquisitionSource, AcquisitionSpec, EvaluationThreshold, EvaluationSpec, PresentationDetailLevel, PresentationSpec) defined with `extra='forbid'`. 4 optional fields on BrainSignalEntry. 42 schema tests pass. |
| 2 | `schema_version` field on BrainSignalEntry (default: 1) — signal engine dispatches based on this field | VERIFIED | `schema_version: int = Field(default=1)` in brain_signal_schema.py:271. Dispatch in execute_signals() at line 107. `_evaluate_v2_stub()` returns None (legacy fallthrough). 9 dispatch tests pass. |
| 3 | `brain/field_registry.yaml` maps logical field names to ExtractedData/CompanyProfile dotted paths with DIRECT_LOOKUP or COMPUTED classification | VERIFIED | 15-field registry at src/do_uw/brain/field_registry.yaml. 7 DIRECT_LOOKUP, 8 COMPUTED entries. Pydantic-validated loader (field_registry.py, 131 lines). 22 field registry tests pass. |
| 4 | Existing 400 signals load without modification — V2 fields are optional with sensible defaults | VERIFIED | `load_signals()["total_signals"] == 400` confirmed programmatically. All V1 fields Optional with defaults. `test_400_signals_still_load` passes. |
| 5 | 10-15 signals across FIN, GOV, LIT, STOCK, BIZ prefixes have V2 fields populated and `schema_version: 2` — Pydantic-validated at load time | VERIFIED | 15 V2 signals confirmed (5 prefixes, 3 each). `test_v2_signal_count_in_range` and `test_v2_signals_span_all_five_prefixes` pass. All 15 pass `BrainSignalEntry.model_validate()`. |
| 6 | V2 fields are stored but NOT consumed by pipeline yet — evaluation results identical before/after | VERIFIED | `_evaluate_v2_stub()` always returns None. `test_v2_identical_to_v1_with_same_data` confirms V1 and V2 signals produce identical SignalResult status, threshold_level, and value. |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/brain_signal_schema.py` | V2 Pydantic sub-models + 4 new fields on BrainSignalEntry | VERIFIED | 286 lines (under 500 limit). 6 V2 sub-models + schema_version, acquisition, evaluation, presentation fields. |
| `src/do_uw/stages/analyze/signal_engine.py` | Schema version dispatch stub before content_type dispatch | VERIFIED | `_evaluate_v2_stub()` defined at line 156. Dispatch at line 107 in execute_signals(). |
| `src/do_uw/brain/field_registry.yaml` | 15 field mappings with DIRECT_LOOKUP/COMPUTED classification | VERIFIED | 15 fields: 7 DIRECT_LOOKUP, 8 COMPUTED. Paths verified against actual Pydantic model attributes. |
| `src/do_uw/brain/field_registry.py` | Pydantic-validated loader with lazy caching | VERIFIED | 131 lines (under 150 limit). FieldRegistry + FieldRegistryEntry with `extra='forbid'`. load_field_registry(), get_field_entry(), _reset_cache(). |
| `tests/brain/test_v2_schema.py` | 42 tests covering V2 sub-model validation | VERIFIED | 42 tests across 8 test classes. All pass. |
| `tests/brain/test_v2_dispatch.py` | 9 tests covering dispatch stub and legacy fallthrough | VERIFIED | 9 tests in 2 classes. All pass. |
| `tests/brain/test_field_registry.py` | 22 tests for field registry loading and validation | VERIFIED | 22 tests across 5 test classes. All pass. |
| `tests/brain/test_v2_migration.py` | 14 regression tests for V2 signal migration | VERIFIED | 14 tests covering count, coverage, threshold ordering, field registry references, Pydantic validation, and threshold consistency. All pass. |
| Signal YAML files (13 files) | V2 fields added in-place to 15 signals | VERIFIED | fin/balance.yaml, fin/accounting.yaml, gov/board.yaml, gov/pay.yaml, gov/activist.yaml, lit/sca.yaml, lit/defense.yaml, lit/other.yaml, stock/price.yaml, stock/short.yaml, stock/ownership.yaml, biz/dependencies.yaml, biz/core.yaml — all modified with V2 additions. |
| `src/do_uw/cli_brain.py` | V2 signal count and field registry count in brain status; V2 validation in brain build | VERIFIED | V2 count computed at line 85. Field registry loaded at line 94-96. brain build V2 count reported at line 389-391. |
| `src/do_uw/brain/brain_build_signals.py` | Step 5 V2 section validation; v2_signals return key | VERIFIED | V2 validation at lines 226-255. `"v2_signals": v2_count` returned in result dict. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| BrainSignalEntry | AcquisitionSpec / EvaluationSpec / PresentationSpec | Optional fields with V2 sub-models | WIRED | brain_signal_schema.py lines 275-286. Sub-models use extra='forbid'; BrainSignalEntry stays extra='allow'. |
| execute_signals() | _evaluate_v2_stub() | schema_version >= 2 check | WIRED | signal_engine.py lines 107-118. Checked after map_signal_data(), before content_type dispatch. |
| _evaluate_v2_stub() | Legacy evaluate_signal() | returns None | WIRED | Stub always returns None in Phase 54, triggering fallthrough to legacy path. Identical results confirmed by test. |
| cli_brain.py status() | load_field_registry() | Import + field count display | WIRED | cli_brain.py lines 84-100. Exception-safe (try/except wraps registry load). |
| cli_brain.py build() | brain_build_signals.py v2_signals key | results.get("v2_signals", 0) | WIRED | cli_brain.py line 389. brain_build_signals.py line 255 returns the key. |
| V2 signal evaluation.formula | field_registry.yaml field keys | test_v2_evaluation_formula_exists_in_field_registry | WIRED | All 15 V2 signals' evaluation.formula values exist in the field registry. Test passes. |
| load_field_registry() | field_registry.yaml | CSafeLoader + Pydantic validation | WIRED | field_registry.py lines 101-107. Cached after first load. |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| SCHEMA-01 | 54-01 | BrainSignalEntry extended with optional `acquisition` section | SATISFIED | AcquisitionSpec + AcquisitionSource defined. `acquisition: AcquisitionSpec | None = None` on BrainSignalEntry. 15 V2 signals have populated acquisition sections. |
| SCHEMA-02 | 54-01 | BrainSignalEntry extended with optional `evaluation` section | SATISFIED | EvaluationSpec + EvaluationThreshold defined. `evaluation: EvaluationSpec | None = None` on BrainSignalEntry. Structured thresholds with op/value/label. |
| SCHEMA-03 | 54-01 | BrainSignalEntry extended with optional `presentation` section | SATISFIED | PresentationSpec + PresentationDetailLevel defined. `presentation: PresentationSpec | None = None` on BrainSignalEntry. glance/standard/deep levels. |
| SCHEMA-04 | 54-01 | `schema_version` field on BrainSignalEntry; signal engine dispatches based on this field | SATISFIED | `schema_version: int = Field(default=1)`. Dispatch stub in execute_signals() before content_type dispatch. V2 stub returns None for legacy fallthrough. |
| SCHEMA-05 | 54-02 | Field registry YAML — maps logical field names to ExtractedData/CompanyProfile paths; DIRECT_LOOKUP or COMPUTED | SATISFIED | brain/field_registry.yaml with 15 fields. field_registry.py with Pydantic validation. FIELD_FOR_CHECK untouched. |
| SCHEMA-06 | 54-03 | 10-15 representative signals migrated to V2; at least 2 from each of FIN, GOV, LIT, STOCK, BIZ | SATISFIED | 15 signals migrated (3 per prefix). All pass Pydantic validation at load time. 400 total signals unchanged. |

All 6 requirements fully satisfied. No orphaned requirements found.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| signal_engine.py | 156-169 | `_evaluate_v2_stub()` returns None | INFO (intentional) | Not an anti-pattern — this is the intended Phase 54 design. Docstring explicitly documents it as a stub for Phase 55. The None return is the signal for "use legacy path." |

No blockers. No unintentional stubs, TODOs, or placeholder returns found in any modified file.

---

### Human Verification Required

None. All success criteria are programmatically verifiable:
- Signal counts: verified via load_signals()
- Pydantic validation: verified via test suite (87 tests)
- Pipeline behavior: verified via dispatch tests (V1 == V2 results)
- Commit existence: all 9 task commits verified in git history

---

### Plan-Level Must-Have Coverage

**54-01 must_haves (6/6 verified):**
1. V2 sub-models defined with extra='forbid' — VERIFIED (6 models)
2. BrainSignalEntry extended with 4 Optional fields — VERIFIED
3. 400 signals still load — VERIFIED (programmatic + test)
4. Dispatch stub added to signal_engine.py — VERIFIED (lines 107-118, 156-169)
5. Pipeline behavior identical — VERIFIED (9 dispatch tests)
6. brain_signal_schema.py under 500 lines — VERIFIED (286 lines)

**54-02 must_haves (7/7 verified):**
1. brain/field_registry.yaml exists — VERIFIED
2. Fields classified as DIRECT_LOOKUP or COMPUTED — VERIFIED (7+8=15)
3. COMPUTED fields use named function dispatch — VERIFIED (function + args pattern)
4. Dual roots supported — VERIFIED (all paths start with extracted. or company.)
5. Pydantic-validated at load time — VERIFIED (FieldRegistry + FieldRegistryEntry)
6. FIELD_FOR_CHECK untouched — VERIFIED (signal_field_routing.py unchanged)
7. All V2-migrated signal field_keys present — VERIFIED (test_v2_evaluation_formula_exists_in_field_registry passes)

**54-03 must_haves (7/7 verified):**
1. 12-15 signals migrated to V2 — VERIFIED (15 signals)
2. All 5 prefixes covered — VERIFIED (FIN/GOV/LIT/STOCK/BIZ, 3 each)
3. V2 fields validated by Pydantic at load time — VERIFIED (test_v2_signals_pass_pydantic_validation)
4. 400 signals still load — VERIFIED
5. CLI shows V2 progress — VERIFIED (brain status + brain build)
6. Pipeline behavior identical — VERIFIED (dispatch stub falls through)
7. V1 fields preserved alongside V2 — VERIFIED (test_v1_threshold_text_preserved_on_v2_signals)

---

### Deviations from Plan That Were Auto-Fixed

The following deviations were documented in SUMMARYs and verified as correct in the codebase:

1. **Path corrections** (54-02): Research-estimated paths like `extracted.financials.coverage.interest_coverage` were corrected to match actual Pydantic model attributes (e.g., `extracted.financials.leverage` with `key: interest_coverage`). Correct behavior.

2. **`key` field added to FieldRegistryEntry** (54-02): Plan's FieldRegistryEntry schema only had `path` for DIRECT_LOOKUP, but financial fields use SourcedValue[dict] pattern requiring both path AND key. Added `key: str | None` field. Correct — required for dict-valued SourcedValues.

3. **test_v2_schema.py updated** (54-03): Plan 54-01 test `test_all_signals_have_schema_version_1_by_default` was renamed to `test_signals_have_valid_schema_version` to accept both V1 and V2 signals after migration. Correct — the old test was a pre-migration placeholder.

---

### Test Suite Summary

| Test File | Tests | Status |
|-----------|-------|--------|
| tests/brain/test_v2_schema.py | 42 | All pass |
| tests/brain/test_v2_dispatch.py | 9 | All pass |
| tests/brain/test_field_registry.py | 22 | All pass |
| tests/brain/test_v2_migration.py | 14 | All pass |
| **Total V2-specific** | **87** | **All pass** |

Pre-existing test failures noted in SUMMARYs (test_brain_enrich.py MANAGEMENT_DISPLAY count, test_enriched_roundtrip.py) are unrelated to Phase 54 work and were present before this phase began.

---

_Verified: 2026-03-01T17:30:00Z_
_Verifier: Claude (gsd-verifier)_
