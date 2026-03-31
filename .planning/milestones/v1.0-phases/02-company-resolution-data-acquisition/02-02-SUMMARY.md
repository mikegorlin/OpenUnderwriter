---
phase: 02-company-resolution-data-acquisition
plan: 02
subsystem: acquire-clients
tags: [acquire, sec, market, litigation, news, web-search, fallback, gates]
dependency-graph:
  requires: [01-03]
  provides: [data-clients, fallback-chain, acquisition-gates]
  affects: [02-03]
tech-stack:
  added: []
  patterns: [data-client-protocol, fallback-chain, acquisition-gate, pluggable-search]
key-files:
  created:
    - src/do_uw/stages/acquire/fallback.py
    - src/do_uw/stages/acquire/gates.py
    - src/do_uw/stages/acquire/clients/__init__.py
    - src/do_uw/stages/acquire/clients/sec_client.py
    - src/do_uw/stages/acquire/clients/market_client.py
    - src/do_uw/stages/acquire/clients/litigation_client.py
    - src/do_uw/stages/acquire/clients/news_client.py
    - src/do_uw/stages/acquire/clients/web_search.py
    - tests/test_acquire_clients.py
  modified: []
decisions:
  - id: RATE_LIMITER_REUSE
    decision: "Used rate_limiter.py from Plan 02-01 directly instead of creating placeholder"
    rationale: "02-01 completed in parallel and created rate_limiter.py with exact API needed (sec_get, sec_get_text, SEC_USER_AGENT)"
  - id: CLOSURE_OVER_LAMBDA
    decision: "Used closure functions instead of lambdas for FallbackTier acquire_fn in SECFilingClient"
    rationale: "Pyright strict mode rejects lambda default parameters as Unknown type; closures provide explicit type signatures"
  - id: GETATTR_FOR_FPI
    decision: "Used getattr(identity, 'is_fpi', False) for FPI detection"
    rationale: "is_fpi field may not exist on CompanyIdentity yet (added by resolve stage); safe fallback to False"
  - id: YFINANCE_LOCAL_IMPORT
    decision: "yfinance imported locally inside functions, not at module level"
    rationale: "Avoids import failure if yfinance has issues; enables easier mocking via yfinance.Ticker patch"
metrics:
  duration: 10m 40s
  completed: 2026-02-07
---

# Phase 2 Plan 02: Data Acquisition Clients Summary

**One-liner:** Five data clients (SEC, market, litigation, news, web search) with fallback chain framework, 6 acquisition gates (4 HARD / 2 SOFT), and 22 mocked tests.

## What Was Built

### Infrastructure (Task 1)
- **FallbackChain/FallbackTier** (`fallback.py`, 104 lines): Generic tier-ordered execution with confidence tracking. Each tier attempts acquisition, logs success/failure, falls through on None return or exception. `DataAcquisitionError` carries source name and per-tier error list.
- **Acquisition Gates** (`gates.py`, 161 lines): 6 gates per user's locked decisions. 4 HARD gates (annual_report, quarterly_report, proxy_statement, market_data) halt pipeline on failure. 2 SOFT gates (litigation, news_sentiment) warn but continue. `check_gates()` evaluates all gates and returns `GateResult` list.
- **DataClient Protocol** (`clients/__init__.py`, 45 lines): Protocol class requiring `name` property and `acquire(state, cache)` method. All clients structurally implement this.

### SEC Filing Client (Task 1)
- **SECFilingClient** (`sec_client.py`, 353 lines): Fetches filing METADATA only (accession number, date, form type, URL). Two-tier fallback: SEC Submissions API (HIGH confidence) -> EFTS full-text search (MEDIUM). Handles FPI mapping: domestic 10-K/10-Q -> FPI 20-F/6-K. Per-type cache TTLs (14mo for annual/proxy, 5mo for quarterly, 30d for 8-K, 7d for Form 4). Filing lookback: 3 annual reports, 12 quarterly, 3 proxy statements.

### Market Data Client (Task 1)
- **MarketDataClient** (`market_client.py`, 187 lines): Wraps yfinance with per-category try/except. Collects: info dict, 1y/5y price history, insider transactions, institutional holders, recommendations, news. Every yfinance call individually protected -- partial data returned on failure, never crashes. DataFrame-to-dict conversion for JSON serialization. 7-day cache TTL.

### Litigation Client (Task 2)
- **LitigationClient** (`litigation_client.py`, 221 lines): Web search fires FIRST per user decision (4 search templates: securities class action, SEC investigation, derivative lawsuit, settlement). Then EFTS search for 10-K/20-F legal proceedings. Results tagged: web=LOW confidence, SEC=HIGH. 10-year lookback. 7-day cache TTL.

### News/Sentiment Client (Task 2)
- **NewsClient** (`news_client.py`, 157 lines): Web search for company+news and company+CEO (when available). yfinance news as secondary source. 30-day cache TTL.

### Web Search Orchestrator (Task 2)
- **WebSearchClient** (`web_search.py`, 236 lines): Pluggable search_fn (default no-op with warning). Per-analysis budget tracking with configurable limit (default 50). Monthly usage tracking in cache (warns at 80% of 2,000 Brave limit). `blind_spot_sweep()` runs 5 priority-ordered searches: litigation > regulatory > short_seller > whistleblower > industry_regulatory. Stops when budget exhausted.

## Tests Written

22 tests in `tests/test_acquire_clients.py` (311 lines):

| Test Class | Count | Coverage |
|---|---|---|
| TestFallbackChain | 4 | First succeeds, fallback to second, all fail, exception+recovery |
| TestAcquisitionGates | 6 | Count (4H+2S), all pass, missing annual, FPI 20-F, soft fail, DEF14A variant |
| TestSECFilingClient | 3 | Domestic types, FPI types, metadata structure |
| TestMarketDataClient | 2 | All categories, partial data on failure |
| TestLitigationClient | 2 | Web search first with correct terms, SEC refs tagged HIGH |
| TestWebSearchClient | 4 | Budget tracking, priority order, budget exhaustion, default no-op |
| TestNewsClient | 1 | Web + yfinance news collection |

All tests use `unittest.mock.patch` -- zero real network calls.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Pyright strict mode lambda type inference**
- **Found during:** Task 1
- **Issue:** Lambda default parameters in FallbackTier acquire_fn were inferred as Unknown type by Pyright strict mode.
- **Fix:** Replaced lambdas with closure factory functions (`_make_submissions_fn`, `_make_efts_fn`) that have explicit type signatures.
- **Files modified:** `sec_client.py`
- **Commit:** 2077532

**2. [Rule 3 - Blocking] yfinance untyped import in Pyright strict**
- **Found during:** Task 1
- **Issue:** yfinance has no type stubs; Pyright strict mode reports `reportMissingTypeStubs`.
- **Fix:** Added `# type: ignore[import-untyped]` on yfinance import; used `cast()` for return types from yfinance objects.
- **Files modified:** `market_client.py`, `news_client.py`
- **Commit:** 2077532, fb935c4

**3. [Rule 1 - Bug] Test mock target for local imports**
- **Found during:** Task 2
- **Issue:** Tests patched `market_client.yf` but yfinance is imported locally inside `_collect_yfinance_data()`, not at module level. AttributeError: module does not have attribute 'yf'.
- **Fix:** Changed mock target to `yfinance.Ticker` (the actual import point).
- **Files modified:** `tests/test_acquire_clients.py`
- **Commit:** fb935c4

## Decisions Made

| ID | Decision | Rationale |
|---|---|---|
| RATE_LIMITER_REUSE | Used 02-01's rate_limiter.py directly | API matched exactly; no placeholder needed |
| CLOSURE_OVER_LAMBDA | Closures instead of lambdas for acquire_fn | Pyright strict requires explicit types |
| GETATTR_FOR_FPI | getattr for is_fpi with False default | Field may not exist on model yet |
| YFINANCE_LOCAL_IMPORT | Local yfinance import in functions | Isolates import failures, simplifies mocking |

## Next Phase Readiness

Plan 02-03 (ACQUIRE orchestrator) can now:
- Wire all 5 clients into the orchestrator
- Inject real MCP search function into WebSearchClient
- Run check_gates() after acquisition to validate completeness
- Use FallbackChain for any additional multi-source acquisitions

**No blockers for 02-03.**
