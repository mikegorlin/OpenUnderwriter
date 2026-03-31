---
phase: 20
plan: 02
subsystem: extract
tags: [llm, 10-K, converters, sourced-values, items-1-7-8-9A]
depends_on:
  requires: [20-01]
  provides: ["10-K converter functions for Items 1, 7, 8, 9A"]
  affects: [20-04, 20-05]
tech_stack:
  added: []
  patterns: ["colon-pair parsing for segment/region strings", "dict-of-SourcedValue return pattern for multi-field converters"]
key_files:
  created:
    - src/do_uw/stages/extract/ten_k_converters.py
    - tests/test_ten_k_converters.py
  modified: []
decisions:
  - id: "20-02-01"
    description: "key_financial_concerns treated as list[SourcedValue[str]] (matches schema list[str] type, not scalar string)"
  - id: "20-02-02"
    description: "has_material_weakness always wrapped as SourcedValue (non-optional bool on schema, still useful as SourcedValue for downstream)"
  - id: "20-02-03"
    description: "sourced_str_dict reused from sourced.py for segment/region dicts (avoids new factory function)"
metrics:
  duration: "3m 49s"
  completed: "2026-02-11"
  tests_added: 32
  tests_total: 2276
---

# Phase 20 Plan 02: 10-K Converter Functions Summary

10-K converter module with 13 functions mapping TenKExtraction fields to typed SourcedValues across Items 1 (Business), 7 (MD&A), 8 (Footnotes), and 9A (Controls), plus 32 unit tests.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create ten_k_converters.py with all conversion functions | f723bb3 | src/do_uw/stages/extract/ten_k_converters.py |
| 2 | Unit tests for all 10-K converter functions | 1b6990f | tests/test_ten_k_converters.py |

## What Was Built

### ten_k_converters.py (380 lines)

13 public converter functions organized by 10-K Item:

**Item 1 (Business) -- 9 converters:**
- `convert_business_description` -> SourcedValue[str] | None
- `convert_revenue_segments` -> list[SourcedValue[dict[str, str]]] (parses "Name: Pct" format)
- `convert_geographic_footprint` -> list[SourcedValue[dict[str, str]]] (parses "Region: Pct" format)
- `convert_customer_concentration` -> list[SourcedValue[str]]
- `convert_supplier_concentration` -> list[SourcedValue[str]]
- `convert_operational_complexity_flags` -> dict[str, SourcedValue[bool]] (dual-class, VIE)
- `convert_employee_count` -> SourcedValue[int] | None
- `convert_competitive_position` -> SourcedValue[str] | None
- `convert_regulatory_environment` -> SourcedValue[str] | None

**Item 7 (MD&A) -- 1 converter:**
- `convert_mda_qualitative` -> dict with revenue_trend, margin_trend, guidance_language (scalar SourcedValue[str] | None), plus key_financial_concerns, critical_accounting_estimates, non_gaap_measures (list[SourcedValue[str]])

**Item 8 (Footnotes) -- 2 converters:**
- `convert_debt_enrichment` -> dict with debt_instruments (list), credit_facility_detail, covenant_status, tax_rate_notes (qualitative context, NEVER overrides XBRL)
- `convert_stock_comp_detail` -> SourcedValue[str] | None

**Item 9A (Controls) -- 1 converter:**
- `convert_controls_assessment` -> dict with has_material_weakness (bool), material_weakness_detail/significant_deficiencies (lists), remediation_status, auditor_attestation, auditor_name, auditor_tenure_years

All converters return None/empty when input is None/empty. All SourcedValues use source="10-K (LLM)" and Confidence.HIGH.

### Test Coverage (32 tests)

- 15 test classes covering all 13 converters
- Edge cases: None inputs, empty strings, empty lists, partial data, no-colon fallback parsing
- Material weakness scenario with populated detail lists and remediation status
- Every test verifies .value, .source, and .confidence

## Decisions Made

1. **key_financial_concerns as list**: The TenKExtraction schema defines this as list[str], not str. The converter returns list[SourcedValue[str]] matching the actual schema type.
2. **has_material_weakness always wrapped**: Even though it defaults to False (not optional), wrapping as SourcedValue[bool] provides source attribution for downstream consumers.
3. **Reuse sourced_str_dict**: Used existing `sourced_str_dict` from sourced.py for segment/region dict wrapping instead of creating a new factory.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

```
pyright: 0 errors, 0 warnings, 0 informations
ruff: All checks passed!
pytest: 32 passed (ten_k_converters), 2276 passed (full suite)
Line count: 380 (under 500 limit)
```

## Next Phase Readiness

Plan 02 converters are ready for integration by Plans 04 and 05, which will wire these into the sub-orchestrators (extract_governance.py, extract_litigation.py, and the new business/financial extraction flow).
