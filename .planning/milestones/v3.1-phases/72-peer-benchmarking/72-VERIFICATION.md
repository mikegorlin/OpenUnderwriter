---
phase: 72-peer-benchmarking
verified: 2026-03-07T03:15:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 72: SEC Frames API Peer Benchmarking Verification Report

**Phase Goal:** True percentile ranking across all SEC filers via Frames API. Replace ratio-to-baseline proxy with real cross-filer data. SIC-code sector filtering.
**Verified:** 2026-03-07T03:15:00Z
**Status:** passed
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Frames API client fetches cross-filer data for 10-15 XBRL concepts | VERIFIED | `sec_client_frames.py` has 10-entry `FRAMES_METRICS` registry, `acquire_frames()` iterates all metrics, 22 unit tests pass |
| 2 | Frames responses cached at system level: 180d completed, 1d current | VERIFIED | `FRAMES_TTL_COMPLETED = 180 * 24 * 3600`, `FRAMES_TTL_CURRENT = 1 * 24 * 3600`, cache key pattern `sec:frames:{tag}:{unit}:{period}`, test `test_caches_with_180_day_ttl_for_completed_period` passes |
| 3 | CIK-to-SIC mapping built incrementally with 90-day TTL | VERIFIED | `SIC_TTL = 90 * 24 * 3600`, `SIC_BATCH_LIMIT = 500`, `acquire_sic_mapping()` checks cache first then batch-fetches, tests `test_skips_cached_ciks` and `test_limits_batch_to_500_ciks` pass |
| 4 | Frames acquisition integrates into ACQUIRE stage via orchestrator | VERIFIED | `orchestrator.py:132` calls `self._acquire_frames_data()`, stores on `acquired.filings["frames"]` and `acquired.filings["sic_mapping"]`, wrapped in try/except (non-blocking) |
| 5 | Company percentile computed against ALL SEC filers for each metric | VERIFIED | `_compute_direct_percentile()` ranks against `all_values` list from all Frames entities, test `test_company_found_overall_percentile` confirms 50th percentile for median company |
| 6 | Sector-relative percentile computed using SIC-code filtering | VERIFIED | `_compute_direct_percentile()` filters by 2-digit SIC prefix, test `test_sector_percentile_filters_by_2digit_sic` confirms sector count=3 and percentile=83.33 |
| 7 | Derived metrics (D/E, current ratio, operating margin, net margin, ROE) computed by CIK join | VERIFIED | `DERIVED_METRICS` has 5 entries, `_compute_derived_percentile()` inner-joins by CIK, tests cover join, division-by-zero, missing entity |
| 8 | Existing yfinance peer metrics continue unchanged | VERIFIED | `peer_metrics.py` not modified per summary; benchmark `__init__.py` adds Frames as additive step after `compute_peer_rankings()` |
| 9 | Frames percentiles replace ratio-to-baseline proxy for financial metrics | VERIFIED | `__init__.py:209-228` merges Frames percentiles into `metric_details`, updating existing MetricBenchmark with real percentile_rank from Frames |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/acquire/clients/sec_client_frames.py` | Frames API client + SIC mapping + caching (min 150 lines) | VERIFIED | 339 lines, acquire_frames() + acquire_sic_mapping() + FRAMES_METRICS registry |
| `tests/test_sec_client_frames.py` | Unit tests for Frames client (min 80 lines) | VERIFIED | 397 lines, 22 tests, all pass |
| `src/do_uw/stages/benchmark/frames_benchmarker.py` | True percentile computation (min 150 lines) | VERIFIED | 270 lines, direct + derived percentile, 5 derived metrics |
| `tests/test_frames_benchmarker.py` | Unit tests for percentile computation (min 100 lines) | VERIFIED | 318 lines, 13 tests, all pass |
| `src/do_uw/models/scoring.py` | FramesPercentileResult model + frames_percentiles field | VERIFIED | FramesPercentileResult at line 257, frames_percentiles field at line 355 |
| `src/do_uw/brain/signals/fin/peer_xbrl.yaml` | 6 peer-relative brain signals | VERIFIED | 6 signals: revenue_bottom_quartile, leverage_top_decile, margin_compression, profitability_laggard, size_outlier_small, cash_flow_weak |
| `src/do_uw/brain/sections/financial_health.yaml` | Signals registered in peer_matrix facet | VERIFIED | 7 FIN.PEER references (6 signals + header) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| sec_client_frames.py | rate_limiter.py | `from do_uw.stages.acquire.rate_limiter import sec_get` | WIRED | Import at line 21, used in acquire_frames() and acquire_sic_mapping() |
| sec_client_frames.py | sqlite_cache.py | `AnalysisCache` | WIRED | Import at line 20, used for cache.get/set in both functions |
| orchestrator.py | sec_client_frames.py | `acquire_frames` call | WIRED | Lazy import at line 306, called at line 326 |
| frames_benchmarker.py | percentile_engine.py | `percentile_rank()` | WIRED | Import at line 19, used in both direct and derived percentile functions |
| benchmark/__init__.py | frames_benchmarker.py | `compute_frames_percentiles()` | WIRED | Lazy import at line 172, called at line 183 |
| frames_benchmarker.py | scoring.py | `FramesPercentileResult` | WIRED | Import at line 17, used as return type for all percentile functions |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PEER-01 | 72-01 | Frames API client fetches cross-filer data | SATISFIED | sec_client_frames.py with 10 XBRL metrics, system-level caching |
| PEER-02 | 72-02 | Company percentile computed against all filers and sector | SATISFIED | frames_benchmarker.py with overall + sector percentile |
| PEER-03 | 72-01 | SIC-to-CIK mapping cached for sector filtering | SATISFIED | acquire_sic_mapping() with 90-day TTL, 500-CIK batch limit |
| PEER-04 | 72-02 | Benchmarking results replace ratio-to-baseline proxy | SATISFIED | Frames percentiles merged into metric_details in BenchmarkStage |
| PEER-05 | 72-02 | Peer-relative brain signals | SATISFIED | 6 signals in peer_xbrl.yaml, registered in financial_health facet |
| PEER-06 | 72-02 | Existing yfinance metrics preserved | SATISFIED | peer_metrics.py unchanged, Frames additive only |

**Note:** PEER-01 through PEER-06 are referenced in ROADMAP.md but not formally defined in REQUIREMENTS.md. Verification is against the success criteria and plan must_haves.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| frames_benchmarker.py | 225 | `return {}` | Info | Valid early-return guard for empty input, not a stub |

No TODOs, FIXMEs, placeholders, or stub implementations found in any phase 72 files.

### Human Verification Required

### 1. Live Frames API Integration

**Test:** Run full pipeline for a ticker (e.g., `uv run do-uw AAPL`) and verify Frames data appears in output
**Expected:** state.benchmark.frames_percentiles populated with 10-15 metrics showing real percentile values; metric_details updated with peer_count > 1000
**Why human:** Requires live SEC API access and end-to-end pipeline run

### 2. Sector Percentile Accuracy

**Test:** Compare sector percentile for a known company against manual SEC Frames API query
**Expected:** 2-digit SIC prefix filtering produces reasonable peer counts (50-500 for major sectors)
**Why human:** Requires real data to validate SIC grouping produces meaningful peer sets

### Gaps Summary

No gaps found. All 9 observable truths verified. All 7 required artifacts exist, are substantive (well above min_lines), and are fully wired. All 6 key links confirmed. All 6 requirements (PEER-01 through PEER-06) satisfied. 35/35 unit tests pass. No anti-patterns detected.

The implementation is clean, additive (no existing behavior broken), and non-blocking (pipeline works without Frames data via try/except wrapping). The two auto-fixed deviations documented in the summary (AcquiredData attribute access and facet registration) were both legitimate corrections.

---

_Verified: 2026-03-07T03:15:00Z_
_Verifier: Claude (gsd-verifier)_
