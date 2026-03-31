---
phase: 45-codebase-cleanup-architecture-hardening
plan: "06"
subsystem: score, acquire, analyze, cli, validation, brain
tags: [file-splitting, 500-line-rule, architecture-cleanup]
dependency_graph:
  requires: [45-05]
  provides: [factor_data_market.py, sec_client_filing.py, financial_formulas_distress.py, cli_knowledge_checks.py, qa_report_generator.py, brain_loader_rows.py]
  affects: [factor_data.py, sec_client.py, financial_formulas.py, cli_knowledge.py, qa_report.py, brain_loader.py]
tech_stack:
  added: []
  patterns: [module-split, direct-imports, no-reexport-shims]
key_files:
  created:
    - src/do_uw/stages/score/factor_data_market.py
    - src/do_uw/stages/acquire/clients/sec_client_filing.py
    - src/do_uw/stages/analyze/financial_formulas_distress.py
    - src/do_uw/cli_knowledge_checks.py
    - src/do_uw/validation/qa_report_generator.py
    - src/do_uw/brain/brain_loader_rows.py
  modified:
    - src/do_uw/stages/score/factor_data.py
    - src/do_uw/stages/acquire/clients/sec_client.py
    - src/do_uw/stages/analyze/financial_formulas.py
    - src/do_uw/stages/analyze/financial_models.py
    - src/do_uw/cli_knowledge.py
    - src/do_uw/validation/qa_report.py
    - src/do_uw/cli.py
    - src/do_uw/brain/brain_loader.py
    - tests/test_acquire_clients.py
    - tests/test_extract_foundation.py
    - tests/test_distress_earnings.py
  deleted:
    - src/do_uw/stages/render/md_renderer_helpers.py
    - src/do_uw/stages/render/md_renderer_helpers_financial.py
decisions:
  - "factor_data_market.py: moved get_sector_code alongside _get_f6_data/_get_f7_data to avoid circular import; imported back in factor_data.py"
  - "sec_client_filing.py: moved filing fetch + parse functions; acquire_company_facts stays in sec_client.py (different concern)"
  - "financial_formulas_distress.py: moved O-score + F-score to new module; Beneish + zone classifiers stay in financial_formulas.py"
  - "cli_knowledge_checks.py: moved check_stats + dead_checks; registered via knowledge_app.command() in cli_knowledge.py"
  - "qa_report_generator.py: print_qa_report moves out; _fmt_size/_sv_val stay in qa_report.py (used internally by validation logic)"
  - "brain_loader_rows.py: created to fix pre-existing 510-line violation from Plan 45-03"
  - "Mock patch targets updated: sec_client_filing.sec_get for filing fetches, sec_client.sec_get for company_facts"
metrics:
  duration: "23m 32s"
  completed: "2026-02-25"
  tasks: 3
  files: 14
---

# Phase 45 Plan 06: File Splits (Score, Acquire, Analyze, CLI, Validation) Summary

Split 6 oversized files across score, acquire, analyze, CLI, and validation subsystems into 6 focused new modules. Also fixed one pre-existing 500-line violation (brain_loader.py) discovered during compliance scan.

## Tasks Completed

### Task 1: Split factor_data.py and sec_client.py

**factor_data.py (514 -> 427 lines):**
- Moved `get_sector_code`, `_get_f6_data`, `_get_f7_data` to `factor_data_market.py` (112 lines)
- Imported back in `factor_data.py` for dispatcher use
- Callers (`factor_scoring.py`, `factor_rules.py`) unchanged (they import top-level functions that remain)

**sec_client.py (511 -> 307 lines):**
- Moved `_fetch_from_submissions`, `_fetch_from_efts`, `_filing_cutoff_date`, `_form_type_matches`, `_FORM_TYPE_VARIANTS`, `SEC_SUBMISSIONS_URL`, `SEC_EFTS_URL`, `FILING_LOOKBACK` to `sec_client_filing.py` (221 lines)
- `acquire_company_facts` stays in `sec_client.py` (uses `sec_get` directly)
- `_make_submissions_fn`, `_make_efts_fn`, `_build_filing_chain` stay in `sec_client.py` (call imported functions)

**regulatory_extract.py:** Already at 248 lines (split in Plan 05); no action needed.

### Task 2: Split financial_formulas.py, cli_knowledge.py, qa_report.py

**financial_formulas.py (509 -> 219 lines):**
- Moved `compute_o_score` and `compute_f_score` to `financial_formulas_distress.py` (320 lines)
- Zone classifiers (`altman_zone_*`, `beneish_zone`, `ohlson_zone`, `piotroski_zone`), `safe_ratio`, and `compute_m_score` stay
- Updated `financial_models.py` and `test_distress_earnings.py` to import from new module

**cli_knowledge.py (505 -> 392 lines):**
- Moved `check_stats` and `dead_checks` command functions to `cli_knowledge_checks.py` (139 lines)
- Registered via `knowledge_app.command("check-stats")(check_stats)` pattern in cli_knowledge.py

**qa_report.py (503 -> 460 lines):**
- Moved `print_qa_report` to `qa_report_generator.py` (67 lines)
- `_fmt_size` and `_sv_val` kept in qa_report.py (used by internal validation functions)
- Updated `cli.py` to import `print_qa_report` from `qa_report_generator`

### Task 3: Compliance scan, tests, and AAPL pipeline

**Pre-existing violation fixed:**
- `brain_loader.py` was 510 lines (violated since Plan 45-03, missed in Plan 05)
- Split `_row_to_check_dict`, `_parse_json`, `SECTION_MAP` to `brain_loader_rows.py` (118 lines)
- `brain_loader.py` trimmed to 417 lines

**Plan 05 cleanup:**
- `md_renderer_helpers.py` and `md_renderer_helpers_financial.py` were supposed to be deleted in Plan 05 but weren't committed as deleted. Deleted and committed.

**Test fixes (Rule 1 - Bug):**
- `test_acquire_clients.py`: Updated 3 mock patch targets from `sec_client.sec_get` to `sec_client_filing.sec_get` for filing fetch tests
- `test_extract_foundation.py`: Same fix for 3 company-facts tests; kept company_facts tests pointing to `sec_client.sec_get`

**Results:**
- 3,939 tests pass, 0 new failures
- 1 pre-existing failure: `test_render_coverage.py::test_html_coverage_exceeds_90_percent` (89.1% < 90%, pre-existing since before Plan 06)
- Zero files in `src/do_uw` exceed 500 lines
- AAPL pipeline completes successfully with output files generated

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] brain_loader.py was 510 lines (pre-existing violation)**
- **Found during:** Task 3 compliance scan
- **Issue:** File was 510 lines since Plan 45-03, missed during Plan 05's compliance check
- **Fix:** Created `brain_loader_rows.py` with `row_to_check_dict`, `_parse_json`, `SECTION_MAP`; trimmed `brain_loader.py` to 417 lines
- **Files modified:** `src/do_uw/brain/brain_loader.py`, `src/do_uw/brain/brain_loader_rows.py`
- **Commit:** c26d9d0

**2. [Rule 1 - Bug] Test mock patch targets broke after sec_client split**
- **Found during:** Task 3 test run
- **Issue:** Tests patched `sec_client.sec_get` but after split, filing fetches use `sec_client_filing.sec_get`
- **Fix:** Updated patch targets in `test_acquire_clients.py` and `test_extract_foundation.py`
- **Files modified:** `tests/test_acquire_clients.py`, `tests/test_extract_foundation.py`
- **Commit:** c26d9d0

**3. [Rule 1 - Bug] md_renderer_helpers.py deletion missing from Plan 05 commit**
- **Found during:** Task 3 git status check
- **Issue:** Plan 05 intended to delete these files but didn't stage the deletions
- **Fix:** Staged and committed the deletions
- **Files deleted:** `src/do_uw/stages/render/md_renderer_helpers.py`, `src/do_uw/stages/render/md_renderer_helpers_financial.py`
- **Commit:** c26d9d0

## Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `src/do_uw/stages/score/factor_data_market.py` | 112 | Market/trading factors (F6, F7) + get_sector_code |
| `src/do_uw/stages/acquire/clients/sec_client_filing.py` | 221 | Filing fetch/parse helpers for SEC EDGAR |
| `src/do_uw/stages/analyze/financial_formulas_distress.py` | 320 | O-Score (Ohlson) + F-Score (Piotroski) |
| `src/do_uw/cli_knowledge_checks.py` | 139 | check-stats + dead-checks CLI commands |
| `src/do_uw/validation/qa_report_generator.py` | 67 | QA report print/format |
| `src/do_uw/brain/brain_loader_rows.py` | 118 | Row-to-dict conversion + _parse_json |

## Files Reduced

| File | Before | After |
|------|--------|-------|
| `src/do_uw/stages/score/factor_data.py` | 514 | 427 |
| `src/do_uw/stages/acquire/clients/sec_client.py` | 511 | 307 |
| `src/do_uw/stages/analyze/financial_formulas.py` | 509 | 219 |
| `src/do_uw/cli_knowledge.py` | 505 | 392 |
| `src/do_uw/validation/qa_report.py` | 503 | 460 |
| `src/do_uw/brain/brain_loader.py` | 510 | 417 |

## Self-Check: PASSED

All 6 created files exist. All 3 task commits exist (20ba3bb, 37d73cc, c26d9d0). Zero 500-line violations. 3,939 tests pass.
