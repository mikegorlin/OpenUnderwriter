---
phase: 21-multi-ticker-validation
plan: 01
subsystem: validation
tags: [validation, cli, runner, checkpointing, batch-execution]
depends_on:
  requires: [phase-20]
  provides: [validation-runner, validation-config, validation-report, validate-cli]
  affects: [21-02, 21-03, 21-04, 21-05, 21-06]
tech-stack:
  added: []
  patterns: [checkpoint-resume, continue-on-failure, rich-reporting]
key-files:
  created:
    - src/do_uw/validation/__init__.py
    - src/do_uw/validation/config.py
    - src/do_uw/validation/runner.py
    - src/do_uw/validation/report.py
    - src/do_uw/cli_validate.py
    - tests/test_validation_runner.py
  modified:
    - src/do_uw/cli.py
    - ruff.toml
decisions:
  - id: ticker-count-24
    decision: "24 tickers (18 standard + 5 known-outcome + 1 FPI edge case)"
    reason: "Covers 9 industry verticals with 2 each, plus companies with known D&O events and a Foreign Private Issuer"
  - id: conservative-rate-temp
    decision: "Temporary rate limiter hack via module attribute override"
    reason: "Plan 02 will add proper set_max_rps() function; temporary solution unblocks validation runs"
metrics:
  duration: 6m 24s
  completed: 2026-02-11
  tests-added: 21
  tests-total: 2366
---

# Phase 21 Plan 01: Multi-Ticker Validation Infrastructure Summary

ValidationRunner with checkpointing, continue-on-failure, and Rich+JSON reporting for 24 tickers across 9 industry verticals.

## What Was Built

### Validation Package (`src/do_uw/validation/`)

**config.py** -- 24 canonical validation tickers:
- 18 standard tickers across 9 industry playbooks (TECH_SAAS, BIOTECH_PHARMA, ENERGY_UTILITIES, HEALTHCARE, CPG_CONSUMER, MEDIA_ENTERTAINMENT, INDUSTRIALS, REITS, TRANSPORTATION)
- 5 known-outcome companies with historical D&O events (SMCI, RIDE, COIN, LCID, PLUG)
- 1 Foreign Private Issuer edge case (TSM: files 20-F, CIK 1046179, SIC 3674)
- `get_tickers(category)` filter function

**runner.py** -- ValidationRunner class:
- Sequential pipeline execution across tickers
- Checkpoint to `.validation_checkpoint.json` after each ticker
- Skip completed/failed tickers on restart
- Continue-on-failure: PipelineError for one ticker does not halt the batch
- Fresh mode: clears ticker output before running
- Per-ticker timing via `time.monotonic()`

**report.py** -- Report generation:
- `TickerResult` and `ReportSummary` dataclasses
- `ValidationReport` with run_date, per-ticker results, and summary
- Rich table display with color-coded PASS/FAIL
- JSON serialization/deserialization round-trip

### CLI Command (`src/do_uw/cli_validate.py`)

`angry-dolphin validate run` with options:
- `--output` / `-o`: Output directory (default: `output`)
- `--fresh / --no-fresh`: Clear cache before each ticker
- `--conservative-rate / --no-conservative-rate`: 5 req/sec SEC rate
- `--no-llm`: Disable LLM extraction
- `--tickers-file`: Override ticker list from text file
- `--category`: Filter by standard/known_outcome/edge_case

### Tests (21 new)

- 9 ticker configuration tests (count, industries, known outcomes, edge cases, uniqueness)
- 5 runner tests (all tickers run, checkpoint skip, continue-on-failure, fresh clear, checkpoint write)
- 4 report tests (compute summary, JSON round-trip, Rich display, empty results)
- 3 utility tests (extract failed stage patterns)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Adjusted ticker count from 25 to 24**
- **Found during:** Task 1
- **Issue:** Plan referenced both 24 and 25 ticker counts. Actual math: 18 + 5 + 1 = 24.
- **Fix:** Used consistent 24 count across all code and tests.

**2. [Rule 3 - Blocking] Pyright strict mode fixes**
- **Found during:** Task 1
- **Issue:** `dict` default_factory returned `dict[Unknown, Unknown]`; unused `ReportSummary` import; private module attribute access on rate_limiter.
- **Fix:** Used `dict[str, TickerResult]()` constructor; removed unused import; added `type: ignore[attr-defined]` for temporary rate limiter hack.

## Verification Results

| Check | Result |
|-------|--------|
| `pytest tests/test_validation_runner.py` | 21 passed |
| `pyright src/do_uw/validation/ src/do_uw/cli_validate.py` | 0 errors |
| `ruff check src/do_uw/validation/ src/do_uw/cli_validate.py` | All checks passed |
| Ticker count assertion | 24 (correct) |
| No file over 500 lines | Largest: tests/test_validation_runner.py at 326 lines |

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | 0a4e9de | feat(21-01): add validation package with runner, config, and report |
| 2 | 6817d17 | feat(21-01): add CLI validate command and validation runner tests |
