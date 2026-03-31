---
phase: 21-multi-ticker-validation
plan: 04
subsystem: validation
tags: [batch-api, cost-reporting, anthropic, cli]
depends_on:
  requires: [21-01, 21-02]
  provides: ["BatchExtractor utility", "CostReport module", "--batch CLI flag", "cost-report CLI subcommand"]
  affects: [21-05, 21-06]
tech-stack:
  added: []
  patterns: ["Anthropic Message Batches API", "Rich table cost reporting", "dataclass closures for pyright"]
key-files:
  created:
    - src/do_uw/validation/batch.py
    - src/do_uw/validation/cost_report.py
    - tests/test_batch_api.py
    - tests/test_cost_report.py
  modified:
    - src/do_uw/cli_validate.py
    - src/do_uw/validation/__init__.py
    - src/do_uw/stages/extract/llm/cache.py
decisions:
  - "BatchExtractor is separate from LLMExtractor (not subclass/mixin) per RESEARCH anti-pattern guidance"
  - "Added get_costs_by_filing_type() public method to ExtractionCache instead of accessing _conn directly"
  - "Dataclass field defaults use named closures (not lambdas) for pyright strict compatibility"
  - "Batch mode is post-run optimization for re-runs, not replacement for real-time validation path"
metrics:
  duration: "~7m"
  completed: "2026-02-11"
  tests_added: 20
  tests_total: 2395
---

# Phase 21 Plan 04: Batch API & Cost Reporting Summary

Batch API tool_use request construction with Anthropic Message Batches SDK, and per-company/per-filing-type cost reporting via ExtractionCache queries.

## Completed Tasks

| # | Task | Commit | Key Changes |
|---|------|--------|-------------|
| 1 | Batch API utility and cost reporting | b616f28 | batch.py (BatchExtractor), cost_report.py (CostReport), 20 tests |
| 2 | Wire batch and cost report into CLI | a9c4500 | --batch flag, cost-report subcommand, fix set_max_rps |

## Key Implementation Details

### BatchExtractor (batch.py, 358 lines)
- `prepare_request()`: Constructs tool_use batch requests with custom_id=`{form_type}:{accession}`
- `submit_batch()`: Wraps `anthropic.Anthropic().messages.batches.create()`
- `poll_batch()`: Polls until terminal status (ended/canceled/expired)
- `parse_results()`: Extracts tool_use content, validates against Pydantic schemas
- `_pydantic_to_tool_schema()`: Converts Pydantic model to Anthropic tool definition
- Lazy anthropic import with try/except pattern

### CostReport (cost_report.py, 313 lines)
- `generate_cost_report()`: Scans output dir, queries ExtractionCache per accession
- `print_cost_report()`: Rich table with dynamic filing-type columns and totals footer
- `save_cost_report()`/`load_cost_report()`: JSON round-trip serialization
- Uses `cache.get_costs_by_filing_type()` (new public API) instead of private `_conn`

### CLI Updates (cli_validate.py, 214 lines)
- `--batch/--no-batch` flag on `run` command (default: no-batch)
- `cost-report` subcommand with `--output` option
- Fixed `_apply_conservative_rate()` from `rate_limiter._SEC_MAX_RPS = 5` to `set_max_rps(5)`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added get_costs_by_filing_type() to ExtractionCache**
- **Found during:** Task 1
- **Issue:** Plan called for accessing `cache._conn` directly from cost_report.py, but pyright strict rejects private member access
- **Fix:** Added public `get_costs_by_filing_type()` method to ExtractionCache
- **Files modified:** src/do_uw/stages/extract/llm/cache.py
- **Commit:** b616f28

**2. [Rule 1 - Bug] Fixed dataclass field defaults for pyright strict**
- **Found during:** Task 1
- **Issue:** `field(default_factory=dict)` produces `dict[Unknown, Unknown]` in pyright strict
- **Fix:** Used named closure functions (`_empty_str_float_dict`, `_empty_entry_list`) instead of bare `dict`/`list`
- **Files modified:** src/do_uw/validation/cost_report.py
- **Commit:** b616f28

**3. [Rule 1 - Bug] Added model property to BatchExtractor**
- **Found during:** Task 2
- **Issue:** CLI accessed `extractor._model` which pyright rejects as private
- **Fix:** Added `@property model` to BatchExtractor for public access
- **Files modified:** src/do_uw/validation/batch.py
- **Commit:** a9c4500

## Verification

- 20 new tests: 10 batch API + 10 cost report (all pass)
- 2395 total tests passing, 0 lint errors, 0 type errors
- All files under 500 lines
- CLI `--help` shows both --batch flag and cost-report subcommand

## Next Phase Readiness

Plans 21-05 and 21-06 can proceed. The batch extraction path is wired but lightweight (logs readiness, does not yet collect uncached filings). The cost-report subcommand is fully functional and ready for use after real validation runs.
