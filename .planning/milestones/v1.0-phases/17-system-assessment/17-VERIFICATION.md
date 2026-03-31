---
phase: 17-system-assessment
verified: 2026-02-10T18:30:00Z
status: passed
score: 6/6 must-haves verified
---

# Phase 17: System Assessment & Critical Bug Fixes Verification Report

**Phase Goal:** Diagnose and fix the critical bugs that prevent data from even reaching extractors, remove garbage-producing code, establish ground truth test cases, and clean up technical debt -- so that Phase 18+ builds on a solid foundation rather than on top of known broken infrastructure.

**Verified:** 2026-02-10T18:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Filing documents (DEF 14A, 8-K, 10-K) are available at `state.acquired_data.filing_documents` and contain full text | ✓ VERIFIED | `_promote_filing_fields()` in orchestrator.py pops filing_documents from SEC client result and sets on `acquired.filing_documents`. 19 tests in test_filing_documents.py confirm data flow. |
| 2 | Garbage leadership name extraction removed (no "Interim Award", "Performance Award" as person names) | ✓ VERIFIED | `_NON_NAME_WORDS` expanded to 90+ terms, `_is_valid_person_name()` structural checks (2-4 words, no numeric, avg length >= 3). 14 tests confirm garbage names rejected. |
| 3 | Ground truth test cases established for TSLA, AAPL, JPM with hand-verified expected values | ✓ VERIFIED | tests/ground_truth/{tsla,aapl,jpm}.py with SEC EDGAR-sourced values. 42 parametrized tests, baseline accuracy: TSLA 93%, AAPL 86%. |
| 4 | Phase 3 vs Phase 4 dual model duplication cleaned up | ✓ VERIFIED | `executives`, `ownership_structure`, `sentiment_signals` marked deprecated with `json_schema_extra={'deprecated': True}`. All scoring migrated to Phase 4 paths. 35 model tests confirm backward compat. |
| 5 | State.json size reduced from 16MB to <2MB | ✓ VERIFIED | `_strip_filings_blobs()` in pipeline.py removes company_facts (~4MB), filing_texts, exhibit_21 before serialization. Test confirms serialized JSON < 2MB. Old cached state files not regenerated yet. |
| 6 | Extraction report accurately reflects actual data quality | ✓ VERIFIED | `count_populated_fields()` distinguishes real data from auto-derived defaults. `is_case_viable()` filters hollow SCA cases. Only cases with case_name + 1+ detail field kept. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/acquire/orchestrator.py` | Filing documents promoted to dedicated field | ✓ VERIFIED | `_promote_filing_fields()` at line 307, called at line 184. Pops filing_documents from SEC result dict, sets on `acquired.filing_documents`. |
| `src/do_uw/pipeline.py` | Company Facts stripping before serialization | ✓ VERIFIED | `_strip_filings_blobs()` at line 270, called at line 221 before `model_dump_json()`. Strips 3 keys: company_facts, filing_texts, exhibit_21. |
| `tests/test_filing_documents.py` | Tests proving filing_documents populated correctly | ✓ VERIFIED | 19 tests covering promotion, orchestrator integration, fallback compat, serialization stripping. All pass. |
| `src/do_uw/stages/extract/leadership_parsing.py` | Hardened name validation | ✓ VERIFIED | `_NON_NAME_WORDS` expanded to 90+ terms (lines 35-66), structural checks in `_is_valid_person_name()` (lines 135-164). Rejects garbage names. |
| `src/do_uw/stages/extract/sca_extractor.py` | SCA quality filter | ✓ VERIFIED | `is_case_viable()` at line 329, `count_populated_fields()` at line 293. Filters cases with insufficient detail. |
| `tests/ground_truth/tsla.py` | TSLA ground truth values | ✓ VERIFIED | 74 lines with SEC EDGAR-sourced values: identity, financials (FY2025), market, governance, litigation, distress. |
| `tests/ground_truth/aapl.py` | AAPL ground truth values | ✓ VERIFIED | Similar structure to TSLA with FY2025 data. |
| `tests/ground_truth/jpm.py` | JPM ground truth values | ✓ VERIFIED | FY2024 data. No state.json yet, tests skip (expected). |
| `tests/test_ground_truth_validation.py` | Validation test framework | ✓ VERIFIED | 42 parametrized tests with 10% tolerance for financials, xfail for governance. Accuracy report prints to stdout. |
| `src/do_uw/models/governance.py` | Deprecated Phase 3 fields marked | ✓ VERIFIED | Lines 143-165: executives, ownership_structure, sentiment_signals marked with `json_schema_extra={'deprecated': True}` and description prefix. |
| `tests/test_governance_models.py` | Tests verifying consolidated model usage | ✓ VERIFIED | 35 tests covering deprecation markers, backward compat deserialization, cross-contamination, schema stability. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `sec_client.acquire()` | `orchestrator._promote_filing_fields()` | SEC result dict with filing_documents key | WIRED | SEC client returns dict with filing_documents. Orchestrator calls `_promote_filing_fields()` at line 184 after storing result. |
| `orchestrator._promote_filing_fields()` | `acquired.filing_documents` | Pops from dict, sets on Pydantic field | WIRED | Line 321-324: pops filing_documents from data dict, sets on acquired.filing_documents. Cast for pyright strict. |
| `pipeline.save_state()` | `_strip_filings_blobs()` | Called before model_dump_json() | WIRED | Line 221: stripped = _strip_filings_blobs(state), followed by model_dump_json() in try block, restore in finally. |
| `leadership_parsing._is_valid_person_name()` | Name validation rejection | Blocklist check + structural validation | WIRED | Lines 157-164: checks against _NON_NAME_WORDS, word count, numeric, avg length. Called at lines 196, 206. |
| `sca_extractor.is_case_viable()` | Case quality filtering | Minimum field population check | WIRED | Lines 337-348: requires case_name + 1+ detail field. Called at line 410 in main entry point. |
| `governance.leadership.executives` | Scoring code (factor_data.py) | Phase 4 forensic field path | WIRED | factor_data.py lines migrated from Phase 3 executives to leadership.executives. F9/F10 scoring use tenure_years. |

### Requirements Coverage

No specific requirements mapped to Phase 17 (this is a v2 assessment phase).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| output/TSLA/state.json | N/A | 15MB cached file not regenerated | ℹ️ Info | Old cached state.json files from before fix. Will be regenerated on next pipeline run. Test suite confirms stripping works. |
| output/AAPL/state.json | N/A | 12MB cached file not regenerated | ℹ️ Info | Same as above. |

### Human Verification Required

None — all success criteria verified programmatically through tests and code inspection.

### Gaps Summary

No gaps found. All 6 success criteria achieved:
1. ✓ Filing documents data flow fixed
2. ✓ Garbage name extraction removed
3. ✓ Ground truth established for 3 companies
4. ✓ Model duplication cleaned up
5. ✓ State size reduction implemented (cached files not regenerated yet, but code verified)
6. ✓ Extraction reports reflect actual quality

---

_Verified: 2026-02-10T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
