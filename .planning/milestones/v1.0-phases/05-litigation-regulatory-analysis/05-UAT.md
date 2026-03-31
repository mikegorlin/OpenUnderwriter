---
status: passed
phase: 05-litigation-regulatory-analysis
source: [05-01-SUMMARY.md, 05-02-SUMMARY.md, 05-03-SUMMARY.md, 05-04-SUMMARY.md, 05-05-SUMMARY.md]
started: 2026-02-08T19:00:00Z
updated: 2026-02-08T21:00:00Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

number: done
name: All tests complete
awaiting: none

## Tests

### 1. Litigation models serialize and deserialize
expected: LitigationLandscape() serializes to JSON and deserializes cleanly. All StrEnums importable.
result: PASS — Serialized 1187 chars, deserialized back. CoverageType (10 values), LegalTheory (5+ values), EnforcementStage (6 values), CaseStatus (5 values) all importable.

### 2. Filing section parsing extracts Item 3 and Item 1A
expected: extract_section() with "item3" key finds Legal Proceedings section from a 10-K. extract_section() with "item1a" key finds Risk Factors.
result: PASS — extract_10k_sections() extracted item3 (1439 chars) and item1a (2459 chars) with correct content.

### 3. Config files load via ConfigLoader
expected: lead_counsel_tiers.json, claim_types.json, and industry_theories.json all load without error and contain expected structure.
result: PASS — lead_counsel_tiers: 5 tier-1, 9 tier-2. claim_types: 9 types. industry_theories: 8 industries.

### 4. SCA extractor processes EFTS data with two-layer classification
expected: extract_securities_class_actions() on a state with EFTS sec_references containing SCA keywords returns CaseDetail objects with coverage_type and legal_theories populated.
result: PASS — 29/29 tests passed (sca_extractor.py). Two-layer classification, lead counsel tier, dedup all verified.

### 5. SEC enforcement pipeline maps to correct stages
expected: extract_sec_enforcement() on state with 10-K text containing "Wells notice" returns SECEnforcementPipeline with highest_confirmed_stage = WELLS_NOTICE.
result: PASS — 17/17 tests passed (sec_enforcement.py). Pipeline stage detection, highest-stage-wins logic verified.

### 6. Derivative suits detects Section 220 demands
expected: extract_derivative_suits() on state with Item 3 text mentioning "Section 220 books and records demand" returns cases with appropriate key_rulings.
result: PASS — 16/16 tests passed (derivative_suits.py). Section 220, Caremark, fiduciary duty all detected.

### 7. Regulatory proceedings detects multiple agencies
expected: extract_regulatory_proceedings() on state with 10-K text mentioning DOJ, FTC, and EPA actions returns RegulatoryProceeding objects for each agency.
result: PASS — 36/36 tests passed (regulatory_extract.py). All 10 agency patterns (DOJ, FTC, FDA, EPA, CFPB, OCC, OSHA, EEOC, STATE_AG, FCPA) verified.

### 8. Defense assessment evaluates forum provisions and PSLRA
expected: extract_defense_assessment() on state with DEF 14A containing federal forum provision and 10-K with PSLRA safe harbor language returns DefenseAssessment with forum provisions and pslra_safe_harbor_usage populated.
result: PASS — 18/18 tests passed (defense_assessment.py). Forum provision parsing, PSLRA safe harbor classification verified.

### 9. SOL mapper computes windows from config
expected: compute_sol_map() returns SOLWindow objects with computed sol_expiry and repose_expiry dates. Windows with past expiry dates show window_open=False.
result: PASS — 13/13 tests passed (sol_mapper.py). Dual SOL/repose window computation from claim_types.json verified.

### 10. Contingent liabilities extracts ASC 450 classifications
expected: extract_contingent_liabilities() on state with 10-K footnote text containing "probable loss" and "$50 million" returns ContingentLiability with asc_450_classification and accrued_amount.
result: PASS — 22/22 tests passed (contingent_liab.py). ASC 450 classification, accrued amounts, 3-tuple return verified.

### 11. Litigation sub-orchestrator calls all 10 extractors
expected: run_litigation_extractors() with mocked individual extractors calls all 10 wrapper functions and returns populated LitigationLandscape.
result: PASS — 12/12 tests passed (extract_litigation.py). All 10 wrappers called with try/except isolation.

### 12. ExtractStage includes litigation as Phase 12
expected: ExtractStage.run() calls run_litigation_extractors and populates state.extracted.litigation.
result: PASS — 19/19 tests passed (extract_stage.py). Phase 12 litigation wired into ExtractStage pipeline.

### 13. Full test suite passes
expected: `uv run python -m pytest tests/ -q` shows 752+ tests passing, 0 failures.
result: PASS — 752 passed, 0 failures in 6.43s.

### 14. Zero lint and type errors
expected: `uv run ruff check src/ tests/` and `uv run pyright src/` both clean.
result: PASS — ruff: "All checks passed!" pyright: "0 errors, 0 warnings, 0 informations"

### 15. All source files under 500 lines
expected: No .py file in src/do_uw/ exceeds 500 lines.
result: PASS — Largest file: distress_formulas.py at 499 lines. All under 500.

## Summary

total: 15
passed: 15
issues: 0
pending: 0
skipped: 0

## Gaps

[none]
