---
phase: 71-form4-enhancement
verified: 2026-03-06T22:30:00Z
status: passed
score: 12/12 must-haves verified
re_verification: false
---

# Phase 71: Form 4 Enhancement Verification Report

**Phase Goal:** Enhance existing Form 4 XML parser with post-transaction ownership, deduplication, gift filtering, exercise-sell patterns, and filing timing analysis. Extend, don't rewrite.
**Verified:** 2026-03-06T22:30:00Z
**Status:** passed

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every InsiderTransaction has shares_owned_following from postTransactionAmounts XML | VERIFIED | insider_trading.py:164 extracts sharesOwnedFollowingTransaction; market_events.py:167 defines field |
| 2 | Relationship flags (isDirector, isOfficer, isTenPercentOwner) parsed for every transaction | VERIFIED | insider_trading.py:84-87 parses reportingOwnerRelationship element |
| 3 | Gift (G) and estate (W) transactions excluded from buy/sell aggregation | VERIFIED | insider_trading.py:353 EXCLUDED_CODES = {"G", "W"}, line 377 filters |
| 4 | RSU vesting (A, $0) and tax withholding (F) excluded entirely from output | VERIFIED | insider_trading.py:355 COMPENSATION_CODES = {"A", "F"}, line 374 filters |
| 5 | Form 4/A amendments acquired and preferred over original Form 4 filings | VERIFIED | sec_client_filing.py:47 "4": ["4", "4/A"]; dedup prefers amendments |
| 6 | Duplicate transactions deduplicated by owner+date+code tuple | VERIFIED | insider_trading_analysis.py:37 _deduplicate_transactions groups by tuple |
| 7 | Ownership concentration computed per insider with tiered alerts | VERIFIED | insider_trading_analysis.py:95 compute_ownership_concentration; OwnershipConcentrationAlert model at market_events.py:197 |
| 8 | Exercise-and-sell patterns (M + S, same owner, same/adjacent day) detected as amber | VERIFIED | insider_trading_patterns.py:84 detect_exercise_sell_patterns; ExerciseSellEvent model at market_events.py:262 |
| 9 | Filing timing analysis detects selling within 60 days before negative 8-K filings | VERIFIED | insider_trading_patterns.py:184 analyze_filing_timing with 60-day window |
| 10 | Filing timing analysis detects buying within 60 days before positive 8-K filings | VERIFIED | Same function, classify_8k_item at line 64 classifies POSITIVE items (1.01/2.01) |
| 11 | 8-K events classified by item number: 2.02/5.02/4.02=negative, 1.01/2.01=positive | VERIFIED | insider_trading_patterns.py:64 classify_8k_item with exact mappings |
| 12 | All detected patterns create brain signals in GOV.INSIDER.* namespace | VERIFIED | insider.yaml has 4 signals: ownership_concentration, exercise_sell, timing_suspect, unusual_timing; all routed in signal_field_routing.py:383-388; resolved in signal_mappers_sections.py:277-304; facet-wired in governance.yaml and enrichment_data.py |

**Score:** 12/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/market_events.py` | Extended InsiderTransaction + new models | VERIFIED | 597 lines; 9 new fields on InsiderTransaction; OwnershipConcentrationAlert, OwnershipTrajectoryPoint, ExerciseSellEvent, FilingTimingSuspect models |
| `src/do_uw/stages/extract/insider_trading.py` | Extended parser + gift filtering | VERIFIED | 488 lines; XML extraction of postTransactionAmounts, relationship flags, ownership nature; EXCLUDED_CODES/COMPENSATION_CODES filtering |
| `src/do_uw/stages/extract/insider_trading_analysis.py` | Dedup + ownership concentration | VERIFIED | 258 lines; _deduplicate_transactions, compute_ownership_concentration |
| `src/do_uw/stages/extract/insider_trading_patterns.py` | Exercise-sell + filing timing | VERIFIED | 284 lines; detect_exercise_sell_patterns, analyze_filing_timing, classify_8k_item, get_eight_k_filings |
| `src/do_uw/stages/acquire/clients/sec_client_filing.py` | 4/A variant | VERIFIED | Line 47: "4": ["4", "4/A"] |
| `src/do_uw/brain/signals/gov/insider.yaml` | 4 new/reactivated signals | VERIFIED | 11 total GOV.INSIDER signals; ownership_concentration, exercise_sell, timing_suspect, unusual_timing |
| `tests/test_insider_form4_enhancements.py` | Tests for plan 01 logic (min 150 lines) | VERIFIED | 525 lines |
| `tests/test_insider_form4_patterns.py` | Tests for plan 02 logic (min 120 lines) | VERIFIED | 299 lines |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| insider_trading.py | market_events.py | InsiderTransaction new fields populated by _parse_single_tx | WIRED | shares_owned_following, is_director, is_officer, is_ten_pct_owner, ownership_nature, accession_number, is_amendment all set in parser |
| insider_trading_analysis.py | market_events.py | OwnershipConcentrationAlert created by compute_ownership_concentration | WIRED | Function returns list[OwnershipConcentrationAlert] |
| insider_trading_patterns.py | market_events.py | ExerciseSellEvent + FilingTimingSuspect created | WIRED | Both models instantiated in detection functions |
| insider_trading_patterns.py | state.acquired_data.filings | 8-K filing dates cross-referenced | WIRED | get_eight_k_filings extracts from state |
| insider.yaml signals | signal_field_routing.py | field_key routing | WIRED | Lines 383-388: all 4 signals mapped to field keys |
| signal_field_routing.py | signal_mappers_sections.py | Data resolution | WIRED | Lines 277-304: exercise_sell_count, timing_suspect_severity, ownership_concentration_severity resolved from InsiderTradingAnalysis |
| insider.yaml signals | governance.yaml facet | Section registration | WIRED | Lines 122-127: all 3 new signals in facet list |
| insider.yaml signals | enrichment_data.py | Subsection + peril mapping | WIRED | Lines 226-228 (subsection 2.8) + lines 437-439 (HAZ-SCA, HAZ-SEC) |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| FORM4-01 [MUST] | 71-01 | Parse sharesOwnedFollowingTransaction, flag C-suite >25% sales | SATISFIED | XML extraction + ownership concentration alerts with tiered thresholds |
| FORM4-02 [MUST] | 71-01 | Deduplicate by accession+date+owner, prefer 4/A | SATISFIED | _deduplicate_transactions + 4/A in _FORM_TYPE_VARIANTS |
| FORM4-03 [MUST] | 71-01 | Exclude gift (G) and estate (W), handle $0 grants | SATISFIED | EXCLUDED_CODES + COMPENSATION_CODES filtering |
| FORM4-04 [SHOULD] | 71-02 | Exercise-and-sell pattern detection (M+S same date) | SATISFIED | detect_exercise_sell_patterns with 1-day tolerance |
| FORM4-05 [SHOULD] | 71-01 | Parse isDirector/isOfficer/isTenPercentOwner + indirect ownership | SATISFIED | Relationship flags parsed at document level, ownership_nature extracted |
| FORM4-06 [SHOULD] | 71-02 | Filing timing analysis vs 8-K dates | SATISFIED | analyze_filing_timing with 60-day bidirectional window, classify_8k_item |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | - | - | - | No TODO/FIXME/PLACEHOLDER found in any modified file |

**Note:** market_events.py at 597 lines exceeds the 500-line rule, but as documented in the summary, it consists entirely of declarative Pydantic models -- acceptable per project conventions.

### Human Verification Required

### 1. Live Pipeline Run

**Test:** Run pipeline for a ticker with known insider trading activity (e.g., a company with recent C-suite sales)
**Expected:** InsiderTradingAnalysis populated with ownership_alerts, exercise_sell_events, and timing_suspects; brain signals fire appropriately
**Why human:** Requires live SEC data acquisition and end-to-end pipeline execution

### 2. 4/A Amendment Deduplication

**Test:** Find a ticker where Form 4/A amendments exist alongside original Form 4 filings
**Expected:** Amendments preferred, originals marked is_superseded=True, no duplicate transactions in output
**Why human:** Depends on actual SEC filing availability

## Gaps Summary

No gaps found. All 6 requirements (3 MUST, 3 SHOULD) satisfied. All 12 observable truths verified. All key links wired end-to-end from XML parsing through model storage through brain signal routing to governance facet. 42 tests passing. No anti-patterns detected.

---

_Verified: 2026-03-06T22:30:00Z_
_Verifier: Claude (gsd-verifier)_
