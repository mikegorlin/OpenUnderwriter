---
phase: "03"
plan: "07"
subsystem: "extract"
tags: ["extract-stage", "orchestrator", "financial-narrative", "peer-override", "integration-tests"]
dependency_graph:
  requires: ["03-02", "03-03", "03-04", "03-05", "03-06"]
  provides: ["extract-stage-orchestrator", "financial-health-narrative", "peers-cli-flag"]
  affects: ["phase-4", "phase-5", "phase-6", "phase-7"]
tech_stack:
  added: []
  patterns: ["orchestrator-pattern", "validation-summary", "exit-stack-mock-management"]
file_tracking:
  key_files:
    created:
      - tests/test_extract_stage.py
    modified:
      - src/do_uw/stages/extract/__init__.py
      - src/do_uw/models/financials.py
      - src/do_uw/cli.py
      - src/do_uw/pipeline.py
      - tests/test_pipeline.py
      - tests/test_cli.py
decisions:
  - id: "03-07-01"
    description: "ExitStack for CLI test mock management instead of tuple unpacking"
    rationale: "8 patches exceeded readable inline with-statement length"
  - id: "03-07-02"
    description: "Financial narrative as SourcedValue[str] with LOW/DERIVED confidence"
    rationale: "Synthesized data must be clearly marked as derived per CLAUDE.md data integrity rules"
  - id: "03-07-03"
    description: "_find_line_item uses list[Any] to avoid FinancialLineItem import cycle"
    rationale: "Keeps orchestrator loosely coupled to statement internals"
metrics:
  duration: "8m 59s"
  completed: "2026-02-08"
  tests_added: 11
  tests_total: 264
  lines_added: ~1050
---

# Phase 3 Plan 7: ExtractStage Orchestrator Summary

ExtractStage orchestrator wiring all 8 extractors in dependency order with financial health narrative, --peers CLI flag, and integration tests.

## What Was Done

### Task 1: ExtractStage Orchestrator + Financial Narrative + --peers CLI

**ExtractStage orchestrator** (`src/do_uw/stages/extract/__init__.py`, 373 lines):
- Rewrote from 39-line stub to 373-line full orchestrator
- Calls 8 extractors in dependency order: company profile -> statements -> distress -> earnings quality -> debt analysis -> audit risk -> tax indicators -> peer group -> narrative
- Collects ExtractionReports from all extractors
- Produces consolidated validation summary (total fields expected vs found, coverage %)
- Logs low-coverage extractors as warnings
- Marks stage FAILED on exception with error message preserved

**Financial health narrative** (SECT3-01):
- `_generate_financial_narrative()` synthesizes 3-5 sentence paragraph
- Revenue trend (growing/declining/stable with YoY %)
- Profitability (net income positive/negative)
- Liquidity position (current ratio assessment: strong/adequate/concerning)
- Leverage position (debt/EBITDA: conservative/moderate/elevated)
- Key concerns (distress zones, going concern, material weaknesses)
- Marked DERIVED/LOW confidence per data integrity rules

**--peers CLI flag** (`src/do_uw/cli.py`):
- `--peers MSFT,GOOG,AMZN` comma-separated override
- Parsed to `list[str]` and passed through `pipeline_config`
- Pipeline wires `peers` from config to `ExtractStage(peers=...)`
- ExtractStage passes to `construct_peer_group(override_peers=...)`

**Model updates** (`src/do_uw/models/financials.py`):
- Added `financial_health_narrative: SourcedValue[str] | None` to `ExtractedFinancials`

### Task 2: Integration Tests + Pipeline/CLI Test Updates

**`tests/test_extract_stage.py`** (10 integration tests):
1. `test_extract_stage_populates_company_profile` -- enriched company profile after run
2. `test_extract_stage_populates_financials` -- statements, distress, audit populated
3. `test_extract_stage_validation_summary` -- validation summary logged with coverage
4. `test_extract_stage_marks_complete` -- stage status COMPLETED with timing
5. `test_extract_stage_fails_without_acquire` -- ValueError on missing acquire
6. `test_extract_stage_fails_without_acquired_data` -- ValueError on None acquired_data
7. `test_extract_stage_peers_override` -- override tickers appear in peer group
8. `test_extract_stage_financial_narrative` -- narrative generated with LOW confidence
9. `test_extract_stage_no_imputation` -- spot check values have sources
10. `test_extract_stage_marks_failed_on_error` -- stage marks FAILED on exception

**Pipeline test updates** (`tests/test_pipeline.py`):
- Added peer group mock patches to 4 full-pipeline test methods
- Prevents flakiness from real financedatabase/yfinance imports

**CLI test updates** (`tests/test_cli.py`):
- Refactored from tuple unpacking to `ExitStack` for 8 mock patches
- Added `_apply_network_patches()` helper for clean reuse
- New test: `test_analyze_peers_flag` verifies --peers acceptance

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- `uv run pytest tests/ -v`: 264 passed, 0 failed
- `uv run pyright src/do_uw/`: 0 errors
- `uv run ruff check src/do_uw/`: All checks passed
- All files under 500 lines (max: 499 distress_formulas.py)
- ExtractStage calls all 8 extractors + narrative generator
- --peers flag passes through CLI -> Pipeline -> ExtractStage -> construct_peer_group

## Phase 3 Completion

This plan completes Phase 3 (Company Profile & Financial Extraction). All 7 plans are done:

| Plan | Description | Tests |
|------|-------------|-------|
| 03-01 | Extraction validation framework + XBRL mapping | 25 |
| 03-02 | Company profile extraction (SECT2) | 31 |
| 03-03 | Financial statement extraction (SECT3-02/03/04) | 45 |
| 03-04 | Distress models + earnings quality (SECT3-06/07) | 64 |
| 03-05 | Debt analysis (SECT3-08/09/10/11) | 36 |
| 03-06 | Audit risk, tax indicators, peer group (SECT3-12/13, SECT2-09) | 52 |
| 03-07 | ExtractStage orchestrator + integration tests | 11 |
| **Total** | | **264** |

All 24 SECT2/SECT3 requirements have corresponding extraction logic:
- SECT2-01 through SECT2-11: Company profile extraction
- SECT3-01: Financial health narrative
- SECT3-02 through SECT3-04: Financial statements
- SECT3-05: Peer group foundation
- SECT3-06: Earnings quality
- SECT3-07: Distress indicators
- SECT3-08 through SECT3-11: Debt analysis
- SECT3-12: Audit risk
- SECT3-13: Tax indicators

## Next Phase Readiness

Phase 4 (Market Analysis & Governance) can proceed immediately. The extract stage provides:
- Complete financial statements with typed models
- Distress indicator scores with zone classifications
- Audit risk profile with opinion parsing
- Peer group for benchmarking
- Financial health narrative for report rendering
