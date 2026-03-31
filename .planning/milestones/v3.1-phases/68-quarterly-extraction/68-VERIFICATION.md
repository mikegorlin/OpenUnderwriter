---
phase: 68-quarterly-extraction
verified: 2026-03-06T15:30:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 68: Quarterly XBRL Extraction Verification Report

**Phase Goal:** Extract 8 quarters of XBRL financial data with proper YTD disambiguation, fiscal period alignment, trend computation, and XBRL/LLM reconciliation.
**Verified:** 2026-03-06T15:30:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `state.extracted.financials.quarterly_xbrl` populated with 8 quarters for test tickers | VERIFIED | `QuarterlyStatements` model exists on `ExtractedFinancials.quarterly_xbrl`, `extract_quarterly_xbrl()` builds up to 8 quarters, 22 tests confirm population |
| 2 | Duration concepts correctly disambiguated (YTD subtraction verified) | VERIFIED | Frame-based filtering (`CY####Q#` regex) selects standalone quarters; fallback uses 70-105 day span; `test_ytd_excluded` confirms YTD=219000 never appears; `test_duration_filters_by_frame_pattern` and `test_fallback_duration_filter` pass |
| 3 | QoQ and YoY trends computed with acceleration/deceleration detection | VERIFIED | `xbrl_trends.py` (260 lines): `compute_qoq`, `compute_yoy`, `compute_acceleration`, `detect_sequential_pattern`, `compute_trends`, `compute_all_trends`. YoY matches by `fiscal_quarter` field (Q1-to-Q1). 14 tests pass. |
| 4 | XBRL values take precedence over LLM; divergences logged | VERIFIED | `xbrl_llm_reconciler.py` (290 lines): `reconcile_value()` returns XBRL when both present, LLM at MEDIUM confidence as fallback. Divergences >1% logged with concept, period, both values, %. 9 tests pass. |
| 5 | All quarterly values have HIGH confidence SourcedValue with XBRL provenance | VERIFIED | `_make_quarterly_sourced_value()` sets `confidence=Confidence.HIGH`, source=`XBRL:10-Q:{end}:CIK{cik}:accn:{accn}`. `test_sourced_value_provenance` verifies format on every SourcedValue across all quarters. |

**Score:** 5/5 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/financials.py` | QuarterlyPeriod + QuarterlyStatements models | VERIFIED | `QuarterlyPeriod` at line 296, `QuarterlyStatements` at line 334, `quarterly_xbrl` field at line 432 |
| `src/do_uw/stages/extract/xbrl_quarterly.py` | extract_quarterly_xbrl() with frame-based filtering | VERIFIED | 390 lines. Exports `extract_quarterly_xbrl`, `select_standalone_quarters`. Frame regex, dedup, fiscal alignment all substantive. |
| `src/do_uw/stages/extract/xbrl_trends.py` | TrendResult + compute_trends + compute_all_trends | VERIFIED | 260 lines. Exports `TrendResult`, `compute_qoq`, `compute_yoy`, `compute_acceleration`, `detect_sequential_pattern`, `compute_trends`, `compute_all_trends`. |
| `src/do_uw/stages/extract/xbrl_llm_reconciler.py` | reconcile_quarterly + cross_validate_yfinance + ReconciliationReport | VERIFIED | 290 lines. Exports `reconcile_value`, `reconcile_quarterly`, `cross_validate_yfinance`, `ReconciliationReport`. |
| `tests/test_xbrl_quarterly.py` | Tests for models, frame filtering, fiscal alignment | VERIFIED | 431 lines, 22 tests (all pass) |
| `tests/test_xbrl_trends.py` | Tests for QoQ, YoY, acceleration, patterns | VERIFIED | 270 lines, 14 tests (all pass) |
| `tests/test_xbrl_reconciler.py` | Tests for reconciliation and cross-validation | VERIFIED | 199 lines, 9 tests (all pass) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| xbrl_quarterly.py | xbrl_mapping.py | `resolve_concept(facts, mapping, concept_name, form_type="10-Q")` | WIRED | Import at line 28, usage at line 268. Also imports `load_xbrl_mapping`, `normalize_sign`, `XBRLConcept`. |
| xbrl_quarterly.py | financials.py | `QuarterlyStatements` + `QuarterlyPeriod` | WIRED | Import at line 23, constructs both models throughout the module. |
| xbrl_quarterly.py | financial_statements.py | `_make_sourced_value` provenance pattern | WIRED (pattern reused) | Does not import `_make_sourced_value` directly but replicates the pattern via `_make_quarterly_sourced_value` with 10-Q provenance format. Deliberate to keep modules independent. |
| xbrl_trends.py | financials.py | `QuarterlyStatements` + `QuarterlyPeriod` | WIRED | Import at line 16, used throughout. |
| xbrl_llm_reconciler.py | financials.py | `QuarterlyStatements`, `QuarterlyUpdate` | WIRED | Import at line 20, consumes both types in `reconcile_quarterly` and `cross_validate_yfinance`. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| QTRLY-01 [MUST] | 68-01 | Extract 8 quarters from Company Facts API | SATISFIED | `extract_quarterly_xbrl()` filters by `form_type="10-Q"`, stores in `QuarterlyStatements` on `quarterly_xbrl` field |
| QTRLY-02 [MUST] | 68-01 | YTD-to-quarterly disambiguation for duration concepts | SATISFIED | Frame-based filtering (`CY####Q#` regex) selects standalone only; duration fallback for frameless entries (70-105 day span). No subtraction math needed. |
| QTRLY-03 [MUST] | 68-01 | Fiscal period alignment using fy+fp fields | SATISFIED | `QuarterlyPeriod` stores both `fiscal_label` ("Q1 FY2025") and `calendar_period` ("CY2024Q4"). AAPL fiscal alignment tested explicitly. |
| QTRLY-04 [MUST] | 68-02 | QoQ and YoY trends with acceleration/deceleration | SATISFIED | `compute_qoq`, `compute_yoy` (matches by `fiscal_quarter`), `compute_acceleration`. All tested with 14 tests. |
| QTRLY-05 [MUST] | 68-02 | Sequential pattern detection (4+ quarters) | SATISFIED | `detect_sequential_pattern` flags compression/deceleration/deterioration at 4+ consecutive negative QoQ. 4 pattern-specific tests pass. |
| QTRLY-06 [MUST] | 68-03 | XBRL/LLM reconciler: XBRL always wins | SATISFIED | `reconcile_value` returns XBRL when both present. Divergences >1% logged. LLM fallback at MEDIUM confidence. 5 reconciliation tests pass. |
| QTRLY-07 [SHOULD] | 68-03 | Validation against yfinance quarterly data | SATISFIED | `cross_validate_yfinance` matches by date proximity (7-day tolerance), logs discrepancies >1%. 3 cross-validation tests pass. |
| QTRLY-08 [MUST] | 68-01 | SourcedValue with XBRL provenance at HIGH confidence | SATISFIED | `_make_quarterly_sourced_value` sets source=`XBRL:10-Q:{end}:CIK{cik}:accn:{accn}`, confidence=HIGH. Test verifies on every SourcedValue. |

No orphaned requirements -- all 8 QTRLY requirements are claimed and satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| xbrl_quarterly.py | 124 | `return []` | Info | Legitimate empty return when no instant fallback possible -- not a stub |

No TODOs, FIXMEs, placeholders, or stub implementations found in any Phase 68 file.

### Pipeline Integration Note

The three new modules (xbrl_quarterly.py, xbrl_trends.py, xbrl_llm_reconciler.py) are not imported from anywhere in the pipeline (`src/do_uw/`). This is BY DESIGN per the ROADMAP: Phase 70 (Signal Integration & Validation) is the wiring phase that depends on Phase 68. The modules are self-contained, tested, and ready for integration.

### Human Verification Required

### 1. Live ticker extraction test

**Test:** Run `extract_quarterly_xbrl(facts, cik)` with real Company Facts for AAPL, RPM, SHW
**Expected:** 8 quarters of data with correct fiscal/calendar alignment, no YTD contamination
**Why human:** Requires live SEC API data and visual inspection of period alignment correctness

### 2. Non-calendar fiscal year edge cases

**Test:** Verify AAPL (Sep FY), SHW (Dec FY), and companies with Jan/Feb FY-end
**Expected:** Fiscal Q1 maps to correct calendar quarter in all cases
**Why human:** Calendar arithmetic edge cases best verified with real data

### Gaps Summary

No gaps found. All 5 observable truths verified. All 8 requirements satisfied. All 7 artifacts exist and are substantive. All 5 key links wired. No anti-patterns. 45 tests pass (22 + 14 + 9).

---

_Verified: 2026-03-06T15:30:00Z_
_Verifier: Claude (gsd-verifier)_
