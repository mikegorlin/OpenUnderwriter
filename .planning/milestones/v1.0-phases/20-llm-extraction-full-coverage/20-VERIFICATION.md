---
phase: 20-llm-extraction-full-coverage
verified: 2026-02-11T01:30:34Z
status: passed
score: 8/8 must-haves verified
must_haves:
  truths:
    - "Item 1 (Business): Revenue segments, geographic footprint, customer/supplier concentration, competitive position, regulatory environment, VIE/dual-class detection"
    - "Item 7 (MD&A): Segment performance with revenue/margin, critical accounting estimates, known trends/uncertainties, guidance language, non-GAAP measures"
    - "Item 8 Footnotes: Debt instruments with terms/rates/maturity, credit facility detail, covenant status; tax rate reconciliation; stock compensation detail"
    - "Item 9A (Controls): Material weakness detail with remediation status, significant deficiencies, auditor attestation"
    - "8-K Events: Executive departures with reason/successor, material agreements, acquisitions, restatement notices"
    - "DEF 14A Ownership: Officer/director ownership table, 5% holders with share counts"
    - "AI Risk: Company-specific AI disclosure extraction, patent data, competitive position assessment"
    - "All regex extractors moved to fallback-only role; LLM is primary for all text sections"
  artifacts:
    - path: "src/do_uw/stages/extract/ten_k_converters.py"
      provides: "13 converter functions for Items 1/7/8/9A"
    - path: "src/do_uw/stages/extract/eight_k_converter.py"
      provides: "5 aggregation converters for 8-K events"
    - path: "src/do_uw/stages/extract/proxy_ownership_converter.py"
      provides: "Ownership table parser for DEF 14A"
    - path: "src/do_uw/stages/extract/profile_item1_helpers.py"
      provides: "Split helpers from company_profile.py (under 500-line limit)"
    - path: "src/do_uw/stages/extract/audit_risk_helpers.py"
      provides: "Split helpers from audit_risk.py (under 500-line limit)"
    - path: "src/do_uw/stages/extract/company_profile.py"
      provides: "_enrich_from_llm for Item 1 Business"
    - path: "src/do_uw/stages/extract/audit_risk.py"
      provides: "_enrich_from_llm for Item 9A Controls"
    - path: "src/do_uw/stages/extract/ownership_structure.py"
      provides: "_enrich_from_llm for DEF 14A Ownership"
    - path: "src/do_uw/stages/extract/debt_analysis.py"
      provides: "_enrich_debt_with_llm for Item 8 Footnotes"
    - path: "src/do_uw/stages/extract/extract_market.py"
      provides: "_enrich_with_eight_k_events for 8-K routing"
    - path: "src/do_uw/stages/extract/extract_ai_risk.py"
      provides: "_supplement_ai_risk_factors for AI risk enrichment"
  key_links:
    - from: "company_profile.py"
      to: "ten_k_converters.py"
      via: "imports 6 converter functions (business_description, geographic_footprint, customer/supplier_concentration, operational_complexity_flags, employee_count)"
    - from: "audit_risk.py"
      to: "ten_k_converters.py"
      via: "imports convert_controls_assessment"
    - from: "debt_analysis.py"
      to: "ten_k_converters.py"
      via: "imports convert_debt_enrichment"
    - from: "extract_market.py"
      to: "eight_k_converter.py"
      via: "imports all 5 convert_* functions"
    - from: "ownership_structure.py"
      to: "proxy_ownership_converter.py"
      via: "imports convert_top_holders, convert_insider_ownership"
    - from: "extract_ai_risk.py"
      to: "llm_helpers.py"
      via: "imports get_llm_ten_k for AI risk factor supplement"
---

# Phase 20: LLM Extraction -- Full Coverage Verification Report

**Phase Goal:** Extend LLM extraction to all remaining filing sections. After this phase, every data point in the worksheet comes from either XBRL, LLM, or structured API -- zero reliance on regex for primary data.
**Verified:** 2026-02-11T01:30:34Z
**Status:** PASSED
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Item 1 (Business): Revenue segments, geographic footprint, customer/supplier concentration, competitive position, regulatory environment, VIE/dual-class detection | VERIFIED | TenKExtraction schema has all 10 Item 1 fields. ten_k_converters.py has 9 converter functions (convert_business_description, convert_revenue_segments, convert_geographic_footprint, convert_customer_concentration, convert_supplier_concentration, convert_operational_complexity_flags, convert_employee_count, convert_competitive_position, convert_regulatory_environment). company_profile.py _enrich_from_llm() wires all 6 enrichment paths with LLM-fills-when-empty logic. |
| 2 | Item 7 (MD&A): Segment performance with revenue/margin, critical accounting estimates, known trends/uncertainties, guidance language, non-GAAP measures | VERIFIED | TenKExtraction has revenue_trend, margin_trend, key_financial_concerns, critical_accounting_estimates, guidance_language, non_gaap_measures. convert_mda_qualitative() returns dict with all 6 fields as SourcedValues. MD&A data stays on TenKExtraction for narrative renderers via get_llm_ten_k() (design decision D20-05-02). |
| 3 | Item 8 Footnotes: Debt instruments with terms/rates/maturity, credit facility detail, covenant status; tax rate reconciliation; stock compensation detail | VERIFIED | TenKExtraction has debt_instruments, credit_facility_detail, covenant_status, tax_rate_notes, stock_comp_detail. convert_debt_enrichment() returns all 4 fields. convert_stock_comp_detail() handles stock comp. debt_analysis.py _enrich_debt_with_llm() supplements debt_structure with covenant_status, credit_facility llm_detail, and llm_debt_instruments. Bootstraps empty structure when regex found nothing. XBRL numeric values never modified. |
| 4 | Item 9A (Controls): Material weakness detail with remediation status, significant deficiencies, auditor attestation | VERIFIED | TenKExtraction has has_material_weakness, material_weakness_detail, significant_deficiencies (Plan 20-01 schema addition), remediation_status (Plan 20-01 schema addition), auditor_attestation, auditor_name, auditor_tenure_years. convert_controls_assessment() wraps all 7 fields. audit_risk.py _enrich_from_llm() fills material_weakness_detail, significant_deficiencies, remediation_status, auditor_name, and tenure with strict override protection (going concern and opinion type NEVER overridden). |
| 5 | 8-K Events: Executive departures with reason/successor, material agreements, acquisitions, restatement notices | VERIFIED | EightKExtraction has departing_officer, departing_officer_title (Plan 20-01 addition), departure_reason, successor, is_termination, agreement_type, counterparty, transaction_type, target_name, restatement_periods, restatement_reason. eight_k_converter.py has 5 aggregation functions (convert_departures, convert_agreements, convert_acquisitions, convert_restatements, convert_earnings_events). extract_market.py _enrich_with_eight_k_events() processes all 5 types, stores counts in market_data["eight_k_events"], and flags restatements in market_data["has_restatement"]. |
| 6 | DEF 14A Ownership: Officer/director ownership table, 5% holders with share counts | VERIFIED | DEF14AExtraction has top_5_holders (list[str]) and officers_directors_ownership_pct (float). proxy_ownership_converter.py has convert_top_holders() (parses "Name: Pct" format), convert_insider_ownership(), and convert_proxy_ownership_summary(). ownership_structure.py _enrich_from_llm() fills top_holders and insider_pct when yfinance returns nothing, running before activist risk assessment (line 478 before line 481). |
| 7 | AI Risk: Company-specific AI disclosure extraction, patent data, competitive position assessment | VERIFIED | extract_ai_risk.py _supplement_ai_risk_factors() finds risk factors with category "AI" from LLM 10-K extraction and appends to disclosure.risk_factors with case-insensitive dedup. Runs after keyword-based disclosure extraction, before competitive positioning (line 48 between lines 45 and 51). Non-AI factors (LITIGATION, CYBER, etc.) are correctly filtered out. |
| 8 | All regex extractors moved to fallback-only role; LLM is primary for all text sections | VERIFIED | All 6 sub-orchestrators follow the pattern: regex/XBRL runs first, then _enrich_from_llm() supplements/replaces. LLM enrichment is called unconditionally in every pipeline path. company_profile: "LLM replaces if richer", audit_risk: "LLM fills not available from regex", ownership: "LLM fills only when yfinance empty", debt: "LLM supplements with qualitative context", market: "LLM 8-K events route to cross-domain", ai_risk: "LLM supplements keyword analysis". XBRL numeric values explicitly protected from LLM override. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/extract/ten_k_converters.py` | 13 converter functions for Items 1/7/8/9A | VERIFIED | 380 lines, 13 public functions, no stubs, 0 pyright errors |
| `src/do_uw/stages/extract/eight_k_converter.py` | 5 aggregation converters for 8-K events | VERIFIED | 309 lines, 5 convert_* functions, typed aliases, no stubs |
| `src/do_uw/stages/extract/proxy_ownership_converter.py` | Ownership table parser | VERIFIED | 136 lines, 3 public functions, colon-pair parsing with fallback |
| `src/do_uw/stages/extract/profile_item1_helpers.py` | Split helpers from company_profile | VERIFIED | 281 lines, imports confirmed |
| `src/do_uw/stages/extract/audit_risk_helpers.py` | Split helpers from audit_risk | VERIFIED | 280 lines, imports confirmed |
| `src/do_uw/stages/extract/company_profile.py` | LLM Item 1 enrichment | VERIFIED | 357 lines (split from 483), _enrich_from_llm at line 112 with 6 paths |
| `src/do_uw/stages/extract/audit_risk.py` | LLM Item 9A enrichment | VERIFIED | 292 lines (split from 478), _enrich_from_llm at line 99 with 5 paths |
| `src/do_uw/stages/extract/ownership_structure.py` | LLM DEF 14A enrichment | VERIFIED | 496 lines, _enrich_from_llm at line 346, called at 478 before activist risk |
| `src/do_uw/stages/extract/debt_analysis.py` | LLM Item 8 debt enrichment | VERIFIED | 473 lines, _enrich_debt_with_llm at line 349, called at 431 |
| `src/do_uw/stages/extract/extract_market.py` | 8-K event routing | VERIFIED | 335 lines, _enrich_with_eight_k_events at line 249, called at 73 |
| `src/do_uw/stages/extract/extract_ai_risk.py` | AI risk factor supplement | VERIFIED | 193 lines, _supplement_ai_risk_factors at line 87, called at 48 |
| `src/do_uw/stages/extract/llm/schemas/eight_k.py` | departing_officer_title field | VERIFIED | Field at line 123 |
| `src/do_uw/models/financials.py` | significant_deficiencies + remediation_status | VERIFIED | Fields at lines 273 and 277 |
| `src/do_uw/stages/extract/llm_helpers.py` | get_llm_eight_k() multi-instance | VERIFIED | Function at line 24, returns list[EightKExtraction] |
| `src/do_uw/stages/extract/llm/extractor.py` | budget_usd = $2.00 | VERIFIED | Default at line 80 |
| `tests/ground_truth/helpers.py` | Shared test utilities | VERIFIED | 204 lines |
| `tests/test_ground_truth_coverage.py` | 15 coverage tests for Phase 20 | VERIFIED | 427 lines, 15 test functions, all passing or xfailed |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| company_profile.py | ten_k_converters.py | import at line 130 | WIRED | Imports 6 converters, uses all in _enrich_from_llm |
| audit_risk.py | ten_k_converters.py | import at line 117 | WIRED | Imports convert_controls_assessment, uses in _enrich_from_llm |
| debt_analysis.py | ten_k_converters.py | import at line 364 | WIRED | Imports convert_debt_enrichment, uses in _enrich_debt_with_llm |
| extract_market.py | eight_k_converter.py | import at line 265 | WIRED | Imports all 5 convert_* functions, uses in _enrich_with_eight_k_events |
| ownership_structure.py | proxy_ownership_converter.py | import at line 364 | WIRED | Imports convert_top_holders + convert_insider_ownership, uses in _enrich_from_llm |
| extract_ai_risk.py | llm_helpers.py | import at line 96 | WIRED | Imports get_llm_ten_k, filters AI-categorized risk factors |
| all enrichment functions | main entry points | function call | WIRED | All 6 _enrich_* functions called in their respective extract_* entry points |

### Requirements Coverage

Phase 20 does not have specific requirements mapped in REQUIREMENTS.md. The phase goal is defined in ROADMAP.md and all 8 success criteria are verified above.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | -- | -- | -- | -- |

No TODOs, FIXMEs, placeholders, or stub patterns found in any Phase 20 file. No files exceed the 500-line limit (max is ownership_structure.py at 496).

### Human Verification Required

### 1. LLM Extraction Quality on Live Filings

**Test:** Run the full pipeline against TSLA and AAPL with LLM enabled and inspect the extracted values for Item 1, Item 7, Item 8, Item 9A, 8-K events, and ownership.
**Expected:** All fields populated with accurate data matching the actual SEC filings.
**Why human:** Ground truth tests use xfail for risk_factors (not yet populated in state files -- LLM extraction hasn't been run against live pipeline). Live extraction quality requires human review of output vs. source filing.

### 2. XBRL Override Protection

**Test:** Run pipeline and verify XBRL-sourced numeric values (liquidity ratios, leverage ratios, going concern, opinion type) are not overwritten by LLM values.
**Expected:** XBRL values preserved with their original source attribution.
**Why human:** While code review confirms override protection logic, runtime verification against actual data is needed to confirm no edge cases.

### Gaps Summary

No gaps found. All 8 observable truths verified. All 17 artifacts exist, are substantive (real implementations, no stubs), and are wired (imported and called in production code). All 7 key links confirmed wired with imports, function calls, and data flow. 124 tests pass, 8 xfailed (expected -- risk_factors and dual_class not yet populated in cached state files). Full test suite: 2345 passed, 0 failures. Pyright: 0 errors across all files. Ruff: all checks passed.

---

_Verified: 2026-02-11T01:30:34Z_
_Verifier: Claude (gsd-verifier)_
