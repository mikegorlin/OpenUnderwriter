---
phase: 45-codebase-cleanup-architecture-hardening
plan: "05"
subsystem: render, extract
tags: [file-splitting, 500-line-rule, refactoring, architecture]
dependency_graph:
  requires: []
  provides:
    - md_renderer_helpers_narrative.py
    - md_renderer_helpers_tables.py
    - md_renderer_helpers_financial_income.py
    - md_renderer_helpers_financial_balance.py
    - company_profile_items.py
    - earnings_guidance_classify.py
    - regulatory_extract_patterns.py
  affects:
    - src/do_uw/stages/render/
    - src/do_uw/stages/extract/
tech_stack:
  added: []
  patterns:
    - Vertical split by concern: prose helpers vs table/structural helpers
    - Income statement orchestrator calls balance sheet row builder via import
    - Extract item-level helpers (resolve codes, validate counts) separated from orchestrators
    - Classification logic (beat/miss/philosophy) isolated from data extraction
key_files:
  created:
    - src/do_uw/stages/render/md_renderer_helpers_narrative.py
    - src/do_uw/stages/render/md_renderer_helpers_tables.py
    - src/do_uw/stages/render/md_renderer_helpers_financial_income.py
    - src/do_uw/stages/render/md_renderer_helpers_financial_balance.py
    - src/do_uw/stages/extract/company_profile_items.py
    - src/do_uw/stages/extract/earnings_guidance_classify.py
    - src/do_uw/stages/extract/regulatory_extract_patterns.py
  modified:
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/stages/render/pdf_renderer.py
    - src/do_uw/stages/extract/company_profile.py
    - src/do_uw/stages/extract/earnings_guidance.py
    - src/do_uw/stages/extract/regulatory_extract.py
    - tests/test_earnings_capital_adverse.py
    - tests/stages/extract/test_market_easy_wins.py
    - tests/test_company_profile.py
    - tests/test_regulatory_extract.py
  deleted:
    - src/do_uw/stages/render/md_renderer_helpers.py
    - src/do_uw/stages/render/md_renderer_helpers_financial.py
decisions:
  - "Narrative split: extract_exec_summary + extract_company → _narrative; extract_market + dim_display_name → _tables"
  - "Financial split: extract_financials + income helpers → _income; _build_statement_rows + _format_line_value → _balance"
  - "Extract split: resolve helpers moved to company_profile_items; classification logic moved to earnings_guidance_classify"
  - "No re-export shims anywhere — all callers import directly from split modules"
metrics:
  duration: "21m 29s"
  completed: "2026-02-25"
  tasks: 4
  files: 17
---

# Phase 45 Plan 05: File Splits (Render + Extract 500-Line Rule) Summary

Split 4 oversized files into 7 focused modules using clean boundary cuts with no re-export shims; deleted 2 originals, trimmed 2 in-place, fixed 1 bonus violation found during compliance scan.

## What Was Built

All files in the render and extract subsystems now comply with CLAUDE.md's 500-line rule. Six new purpose-named files were created, two original render files were deleted (no shims), and two extract files were trimmed in-place.

### Render Subsystem

**`md_renderer_helpers.py` (590 lines) → DELETED**

Split into:
- `md_renderer_helpers_narrative.py` (324 lines): `extract_exec_summary`, `extract_company`, `_lookup_gics_name` — prose/data extraction for executive summary and company profile sections
- `md_renderer_helpers_tables.py` (273 lines): `extract_market`, `dim_display_name`, `_build_insider_summary` — market data tables and Jinja2 filter utilities

Callers updated: `md_renderer.py`, `html_renderer.py`, `pdf_renderer.py` — all now import directly from split modules.

**`md_renderer_helpers_financial.py` (528 lines) → DELETED**

Split into:
- `md_renderer_helpers_financial_income.py` (419 lines): `extract_financials`, `find_line_item_value`, `_margin_change`, `_build_quarterly_context` — the main financial context builder and income statement helpers
- `md_renderer_helpers_financial_balance.py` (126 lines): `_build_statement_rows`, `_format_line_value` — full statement row builders for income/balance/cash flow tables

`extract_financials` calls `_build_statement_rows` via direct import from `_balance`.

### Extract Subsystem

**`company_profile.py` (583 lines) → trimmed to 386 lines**

New file: `company_profile_items.py` (229 lines): `_resolve_gics_code`, `_resolve_naics_code`, `_validate_employee_count`, `_extract_business_description` — item-level data resolution helpers

`company_profile.py` retains the orchestrator (`extract_company_profile`), LLM enrichment (`_enrich_from_llm`), and identity enrichment functions.

**`earnings_guidance.py` (533 lines) → trimmed to 465 lines**

New file: `earnings_guidance_classify.py` (99 lines): `classify_result`, `compute_consecutive_misses`, `compute_philosophy`, `_consensus_from_mean` — all classification/scoring logic isolated from data parsing.

### Compliance Scan Bonus Fix

The Task 4 compliance scan found `regulatory_extract.py` at 521 lines (pre-existing violation).

New file: `regulatory_extract_patterns.py` (309 lines): agency regex patterns, classification helpers (`_classify_proceeding_type`, `_extract_penalty_amount`, `_agency_to_report_field`), and `_scan_text_for_agencies` — all detection logic

`regulatory_extract.py` trimmed to 248 lines (text extraction helpers + orchestrator only).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Compliance] Split regulatory_extract.py (521 lines)**

- **Found during:** Task 4 compliance scan
- **Issue:** `regulatory_extract.py` was 521 lines, violating 500-line rule. This is a pre-existing violation predating Phase 45.
- **Fix:** Split patterns/detection helpers into `regulatory_extract_patterns.py` (309 lines); trimmed `regulatory_extract.py` to 248 lines. Updated `test_regulatory_extract.py` to import from `regulatory_extract_patterns` directly.
- **Files modified:** `src/do_uw/stages/extract/regulatory_extract.py`, `src/do_uw/stages/extract/regulatory_extract_patterns.py`, `tests/test_regulatory_extract.py`
- **Commit:** 7717a90

### Pre-existing Failure (not caused by this plan)

`tests/test_render_coverage.py::TestMultiFormatCoverage::test_html_coverage_exceeds_90_percent` was already failing at 89.1% before this plan's changes. Verified via `git stash` test run. This is an HTML template coverage gap unrelated to file splits.

## Verification Results

- All 3939 tests pass (0 regressions)
- No 500-line violations in render or extract directories
- AAPL pipeline completes and produces output at `output/AAPL/AAPL_worksheet.html`
- No `from ... import *` re-export stubs in any split file

## Self-Check: PASSED

Checking created files exist:
- [x] `src/do_uw/stages/render/md_renderer_helpers_narrative.py` (324 lines)
- [x] `src/do_uw/stages/render/md_renderer_helpers_tables.py` (273 lines)
- [x] `src/do_uw/stages/render/md_renderer_helpers_financial_income.py` (419 lines)
- [x] `src/do_uw/stages/render/md_renderer_helpers_financial_balance.py` (126 lines)
- [x] `src/do_uw/stages/extract/company_profile_items.py` (229 lines)
- [x] `src/do_uw/stages/extract/earnings_guidance_classify.py` (99 lines)
- [x] `src/do_uw/stages/extract/regulatory_extract_patterns.py` (309 lines)

Checking deleted files do not exist:
- [x] `md_renderer_helpers.py` — DELETED
- [x] `md_renderer_helpers_financial.py` — DELETED

Checking commits exist:
- [x] a717719 — Task 1: md_renderer_helpers.py split
- [x] 5746ee0 — Task 2: md_renderer_helpers_financial.py split
- [x] 90c156a — Task 3: company_profile.py + earnings_guidance.py splits
- [x] 7717a90 — Task 4: compliance scan + regulatory_extract.py fix
