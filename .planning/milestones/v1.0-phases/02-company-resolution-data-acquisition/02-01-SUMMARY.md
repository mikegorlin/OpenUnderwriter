---
phase: 02-company-resolution-data-acquisition
plan: 01
subsystem: resolve
tags: [resolve, sec-edgar, ticker, cik, identity, rate-limiter, fuzzy-match, fpi-detection]
dependency-graph:
  requires: [01-03]
  provides: [resolve-stage, rate-limiter, company-identity, sic-sector-mapping]
  affects: [02-02, 02-03]
tech-stack:
  added: [yfinance, rapidfuzz, aiolimiter]
  patterns: [synchronous-rate-limiting, fuzzy-matching, sourced-value-wrapping, sic-to-sector-mapping]
key-files:
  created:
    - src/do_uw/stages/acquire/rate_limiter.py
    - src/do_uw/stages/resolve/ticker_resolver.py
    - src/do_uw/stages/resolve/sec_identity.py
    - tests/test_resolve.py
  modified:
    - pyproject.toml
    - uv.lock
    - src/do_uw/models/company.py
    - src/do_uw/stages/resolve/__init__.py
    - tests/test_pipeline.py
    - tests/test_cli.py
decisions:
  - id: SYNC_RATE_LIMITER
    decision: "Synchronous rate limiter using time.sleep() and monotonic timestamp tracking"
    rationale: "yfinance is sync-only, pipeline is sync, aiolimiter requires asyncio. Thread-safe via threading.Lock."
  - id: SIC_SECTOR_MAP_INLINE
    decision: "SIC-to-sector mapping defined as inline dict in sec_identity.py"
    rationale: "sectors.json has sector baselines but no SIC mapping. Small static mapping (23 ranges) fits cleanly in the module."
  - id: PUBLIC_SIC_TO_SECTOR
    decision: "sic_to_sector() is public (not underscore-prefixed)"
    rationale: "Needed by tests and potentially by other modules for sector classification."
  - id: SEC_API_PRIMARY
    decision: "SEC EDGAR REST API as primary implementation, MCP integration deferred"
    rationale: "Per plan: MCP tool invocation pattern not established yet. Direct httpx calls work, MCP can wrap later."
metrics:
  duration: 9m 35s
  completed: 2026-02-07
---

# Phase 2 Plan 1: Ticker Resolution and SEC Identity Summary

SEC EDGAR ticker resolution with fuzzy matching, SIC-to-sector mapping, FPI detection, and synchronous rate limiter shared by all SEC API calls.

## What Was Built

### Rate Limiter (`src/do_uw/stages/acquire/rate_limiter.py`)
- Module-level singleton rate limiter using `time.sleep()` with monotonic timestamp tracking
- Thread-safe via `threading.Lock` for shared module-level state
- `sec_get(url)` returns parsed JSON, `sec_get_text(url)` returns raw text
- Reusable httpx.Client with proper User-Agent header and 30s timeout
- Target: max 10 requests/second to comply with SEC EDGAR rate limits

### Ticker Resolver (`src/do_uw/stages/resolve/ticker_resolver.py`)
- `resolve_ticker(input_str, cache)` detects ticker vs company name input
- Ticker input: exact match against SEC `company_tickers.json` (~13,000 entries)
- Company name input: rapidfuzz `WRatio` scorer with 80 threshold for match, 90 for auto-proceed
- Parent entity resolution: groups entries by CIK (e.g., GOOG/GOOGL both map to CIK 1652044)
- Returns `ResolvedTicker` dataclass with ticker, cik, company_name, confidence, all_tickers
- Caches company_tickers.json with 30-day TTL

### SEC Identity Resolution (`src/do_uw/stages/resolve/sec_identity.py`)
- `resolve_company_identity(cik, ticker, cache)` fetches full identity from SEC submissions API
- Parses: name, SIC, SIC description, state of incorporation, fiscal year end, entity type, exchange, tickers
- FPI detection: checks `entityType` field for "foreign-private-issuer" AND filing history for 20-F
- SIC-to-sector mapping: 23-range mapping covering all SIC divisions (01-99) to sector codes (TECH, HLTH, FINS, ENGY, INDU, UTIL, CONS, REIT, DEFAULT)
- Every field wrapped in `SourcedValue[str]` with HIGH confidence and SEC EDGAR source
- Caches submissions response with 30-day TTL

### ResolveStage (`src/do_uw/stages/resolve/__init__.py`)
- Replaces stub with real implementation calling ticker_resolver and sec_identity
- Enriches CompanyProfile with market_cap and employee_count from yfinance (MEDIUM confidence)
- yfinance enrichment is non-critical: logs warning on failure, does not halt pipeline
- Proper error handling: marks stage failed on exception, always closes cache

### CompanyIdentity Model Extensions (`src/do_uw/models/company.py`)
- Added `is_fpi: bool` - foreign private issuer flag
- Added `entity_type: SourcedValue[str] | None` - SEC entity type
- Added `sic_description: SourcedValue[str] | None` - SIC code description
- Added `all_tickers: list[str]` - all ticker symbols sharing the same CIK

## Tests Written

17 new tests in `tests/test_resolve.py`:

| Test Class | Tests | What's Covered |
|---|---|---|
| TestResolveTickerByTicker | 4 | Exact ticker match, parent entity (GOOG/GOOGL), unknown ticker, empty input |
| TestResolveTickerByName | 2 | Fuzzy match for "Apple" and "Alphabet" |
| TestResolveCompanyIdentity | 3 | Full Apple identity, FPI via entityType, FPI via filing history |
| TestSicToSector | 5 | TECH, HLTH, FINS, ENGY, DEFAULT mapping |
| TestResolveStage | 3 | Empty ticker validation, valid ticker, full run with mocked deps |

All tests use `unittest.mock.patch` -- no real network requests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed existing test regressions from stub replacement**
- **Found during:** Task 2 verification
- **Issue:** Replacing the ResolveStage stub caused `test_pipeline.py` (test_pipeline_callbacks_fire, test_pipeline_runs_all_stages, test_resume_skips_completed_stages, test_state_saved_after_each_stage) and `test_cli.py` (all 4 tests) to fail because they ran the pipeline which now makes real SEC API calls.
- **Fix:** Added `@patch` decorators to mock `sec_get`, `_enrich_from_yfinance`, and `AnalysisCache` in test_pipeline.py and test_cli.py. This prevents network access and cache side effects.
- **Files modified:** tests/test_pipeline.py, tests/test_cli.py
- **Commit:** 6e696c7

**2. [Rule 1 - Bug] Pre-existing broken tests in test_acquire_clients.py**
- **Found during:** Task 2 verification
- **Issue:** 3 tests in pre-existing `tests/test_acquire_clients.py` fail because they try to patch `yf` as a module-level import but the actual client code uses inline imports. File also exceeds 500-line limit.
- **Status:** NOT FIXED -- this is pre-existing code not part of this plan. Filed as known issue for plan 02-02.

### Implementation Adjustments

- **aiolimiter installed but not used**: Plan specified `uv add aiolimiter` and the research recommended it. However, per the plan's explicit note ("rate limiter must be SYNCHRONOUS"), the actual implementation uses `time.sleep()` + `threading.Lock`. aiolimiter is installed for future async usage but is not imported.
- **sic_to_sector made public**: Plan used underscore prefix `_sic_to_sector`. Changed to public `sic_to_sector` for testability and potential reuse by other modules.

## Decisions Made

| ID | Decision | Rationale |
|---|---|---|
| SYNC_RATE_LIMITER | Sync rate limiter with time.sleep() | Pipeline is sync, yfinance is sync, aiolimiter requires asyncio |
| SIC_SECTOR_MAP_INLINE | SIC mapping in sec_identity.py | sectors.json has baselines but no SIC mapping; 23-range static dict is small |
| PUBLIC_SIC_TO_SECTOR | Public function name | Tests need it, other modules may reuse it |
| SEC_API_PRIMARY | Direct SEC REST API, no MCP | MCP tool invocation pattern not established; direct httpx works |

## Next Phase Readiness

### Ready for Plan 02-02 (Data Acquisition)
- Rate limiter in place for all SEC EDGAR calls
- CompanyIdentity fully populated with CIK, SIC, sector, FPI status
- Cache infrastructure working with proper TTLs
- All 74 tests pass (excluding 3 pre-existing broken tests in test_acquire_clients.py)

### Known Issues for Next Plan
- `tests/test_acquire_clients.py` has 3 broken tests (pre-existing, not from this plan) and exceeds 500-line limit
- aiolimiter installed but unused (sync implementation used instead)
