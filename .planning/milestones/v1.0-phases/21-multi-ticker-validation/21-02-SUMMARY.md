---
phase: 21-multi-ticker-validation
plan: 02
subsystem: infrastructure
tags: [rate-limiting, retry, error-handling, resilience, bulk-runs]
depends_on:
  requires: []
  provides: [sec-retry-backoff, anthropic-retry, budget-warning]
  affects: [21-04, 21-05, 21-06]
tech-stack:
  added: []
  patterns: [exponential-backoff, retry-with-jitter, budget-monitoring]
key-files:
  created:
    - tests/test_rate_limiter.py
  modified:
    - src/do_uw/stages/acquire/rate_limiter.py
    - src/do_uw/stages/extract/llm/extractor.py
    - src/do_uw/stages/extract/llm/cost_tracker.py
    - tests/test_llm_extractor.py
decisions:
  - id: 21-02-01
    description: "Renamed _SEC_MAX_RPS/_SEC_INTERVAL to lowercase for pyright strict compatibility with reassignment"
  - id: 21-02-02
    description: "Switched from instructor.from_provider to instructor.from_anthropic for explicit Anthropic client control"
  - id: 21-02-03
    description: "Added budget_usd property to CostTracker for pyright-clean external access"
metrics:
  duration: 6m 00s
  completed: 2026-02-11
---

# Phase 21 Plan 02: Error Resilience for Bulk Runs Summary

**One-liner:** SEC rate limiter with configurable RPS + retry/backoff on 403/5xx, Anthropic client with max_retries=3, budget warning at 80%

## What Was Done

### Task 1: Configurable SEC rate limiter with retry (5a0ce14)

Enhanced `rate_limiter.py` (113 -> 184 lines) with:

1. **Configurable RPS** via `set_max_rps(rps)` / `get_max_rps()`:
   - Thread-safe, clamps input to [1, 10]
   - Updates both `_sec_max_rps` and `_sec_interval` atomically under lock

2. **Retry with exponential backoff** on `sec_get()` and `sec_get_text()`:
   - 403 (rate-limited): 10s fixed wait
   - 5xx (server error): 2s * 2^attempt exponential backoff
   - Connection errors (httpx.RequestError): same backoff as 5xx
   - Other 4xx: raise immediately, no retry
   - Default `max_retries=5` (keyword-only parameter)

3. **Refactored** shared retry logic into `_sec_request()` helper to avoid duplication.

7 new tests in `tests/test_rate_limiter.py` covering all paths.

### Task 2: Anthropic API retry configuration (4f9030d)

Enhanced `extractor.py` (242 -> 259 lines) with:

1. **Explicit Anthropic client** with `max_retries=3`:
   - Changed from `instructor.from_provider(model)` to `instructor.from_anthropic(Anthropic(max_retries=3))`
   - Model name stripped of `anthropic/` prefix for direct client usage

2. **Enhanced error logging** includes exception type name:
   - `"LLM extraction failed for %s (%s): %s"` with accession, type(exc).__name__, exc

3. **Budget warning at 80%** consumption:
   - After each extraction, checks if usage exceeds 80% of budget limit
   - Logs warning with percentage, used amount, and budget total
   - Added `budget_usd` property to CostTracker for clean external access

2 new tests added to existing `test_llm_extractor.py` (14 -> 16 tests).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pyright strict: uppercase globals treated as constants**
- **Found during:** Task 1
- **Issue:** Pyright strict mode reports `reportConstantRedefinition` when reassigning `_SEC_MAX_RPS` / `_SEC_INTERVAL` in `set_max_rps()`
- **Fix:** Renamed to lowercase `_sec_max_rps` / `_sec_interval`
- **Files modified:** rate_limiter.py, test_rate_limiter.py
- **Commit:** 5a0ce14

**2. [Rule 3 - Blocking] Pyright strict: protected member access across classes**
- **Found during:** Task 2
- **Issue:** Accessing `_budget_usd` on CostTracker from LLMExtractor triggers `reportPrivateUsage`
- **Fix:** Added public `budget_usd` property to CostTracker
- **Files modified:** cost_tracker.py, extractor.py
- **Commit:** 4f9030d

**3. [Rule 2 - Missing Critical] Test mocks needed updating for API change**
- **Found during:** Task 2
- **Issue:** Existing tests mocked `instructor.from_provider` and `client.chat.completions.create` but new code uses `instructor.from_anthropic` and `client.messages.create`
- **Fix:** Updated all 6 mock-based tests to match new API pattern, including system prompt handling (separate `system` kwarg instead of messages array)
- **Files modified:** test_llm_extractor.py
- **Commit:** 4f9030d

## Verification Results

- rate_limiter.py: 0 pyright errors, ruff clean, 7/7 tests pass
- extractor.py: 0 pyright errors, ruff clean, 16/16 tests pass
- cost_tracker.py: 0 pyright errors
- Total: 23 new/updated tests passing

## Next Phase Readiness

No blockers. The pipeline is now robust for bulk validation runs with:
- Automatic retry on SEC EDGAR transient errors (403, 5xx, connection)
- Anthropic API retries (3 attempts) for transient LLM errors
- Early warning when approaching cost budget limits
