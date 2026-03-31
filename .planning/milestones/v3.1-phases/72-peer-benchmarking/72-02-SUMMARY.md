---
phase: 72-peer-benchmarking
plan: 02
subsystem: benchmark
tags: [percentile-ranking, xbrl, frames-api, peer-benchmarking, sic-mapping, derived-metrics]

requires:
  - phase: 72-peer-benchmarking
    provides: SEC Frames API acquisition client (acquire_frames, acquire_sic_mapping)
provides:
  - True percentile computation from SEC Frames data (compute_frames_percentiles)
  - FramesPercentileResult model for per-metric overall + sector percentiles
  - 5 derived financial ratios (current_ratio, D/E, operating_margin, net_margin, ROE)
  - 6 peer-relative brain signals firing on percentile thresholds
  - Frames percentiles merged into BenchmarkResult.metric_details for rendering
affects: [73-rendering, benchmark-stage, financial-health-section]

tech-stack:
  added: []
  patterns: [derived-metric-join-by-cik, sic-prefix-sector-filter, additive-benchmark-wiring]

key-files:
  created:
    - src/do_uw/stages/benchmark/frames_benchmarker.py
    - tests/test_frames_benchmarker.py
    - src/do_uw/brain/signals/fin/peer_xbrl.yaml
  modified:
    - src/do_uw/models/scoring.py
    - src/do_uw/stages/benchmark/__init__.py
    - src/do_uw/brain/sections/financial_health.yaml

key-decisions:
  - "DerivedMetricDef frozen dataclass for 5 derived ratio definitions (current_ratio, D/E, op_margin, net_margin, ROE)"
  - "Inner join by CIK for derived metrics (only entities with both numerator and denominator)"
  - "2-digit SIC prefix for sector filtering (groups 36xx semiconductors, 73xx software etc.)"
  - "Frames percentiles merged INTO existing metric_details dict (additive, not replacing)"
  - "AcquiredData.filings is Pydantic attribute access, not dict.get() (bug found + fixed)"

patterns-established:
  - "Additive benchmark wiring: Frames data enhances existing metrics without replacing yfinance data"
  - "DerivedMetricDef registry pattern for ratio metrics computed from two Frames datasets"
  - "Peer-relative signal naming: FIN.PEER.{metric_description} convention"

requirements-completed: [PEER-02, PEER-04, PEER-05, PEER-06]

duration: 31min
completed: 2026-03-07
---

# Phase 72 Plan 02: Frames Benchmarker + Peer Signals Summary

**True percentile computation engine ranking companies against ~8,000 SEC filers across 15 metrics (10 direct + 5 derived), with 6 peer-relative brain signals and BenchmarkStage integration**

## Performance

- **Duration:** 31 min
- **Started:** 2026-03-07T01:51:02Z
- **Completed:** 2026-03-07T02:22:25Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Built frames_benchmarker.py with true cross-filer percentile ranking (replaces ratio-to-baseline proxy)
- 5 derived financial ratios computed by inner-joining two Frames datasets by CIK
- Sector-relative percentile filtering via 2-digit SIC code prefix
- 6 peer-relative brain signals (revenue, leverage, margin, ROE, size, cash flow) registered in peer_matrix facet
- 13 unit tests covering direct, derived, missing company, empty SIC, division by zero

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for frames benchmarker** - `0deb972` (test)
2. **Task 1 (GREEN): Implement frames benchmarker** - `a196ac9` (feat)
3. **Task 2: Wire into BenchmarkStage + peer signals** - `09c9e2e` (feat)

_TDD pattern: Task 1 has RED + GREEN commits_

## Files Created/Modified
- `src/do_uw/stages/benchmark/frames_benchmarker.py` - True percentile engine with direct + derived metric computation
- `tests/test_frames_benchmarker.py` - 13 tests covering all percentile computation paths
- `src/do_uw/models/scoring.py` - FramesPercentileResult model + frames_percentiles field on BenchmarkResult
- `src/do_uw/stages/benchmark/__init__.py` - BenchmarkStage.run() integration + metric_details merge
- `src/do_uw/brain/signals/fin/peer_xbrl.yaml` - 6 peer-relative threshold signals
- `src/do_uw/brain/sections/financial_health.yaml` - Added peer signals to peer_matrix facet

## Decisions Made
- Used DerivedMetricDef frozen dataclass for 5 derived ratio definitions (consistent with FramesMetricDef pattern from Plan 01)
- Inner join by CIK for derived metrics ensures only entities with both values are ranked
- 2-digit SIC prefix grouping balances specificity vs. peer count (4-digit too narrow, 1-digit too broad)
- Frames percentiles merged INTO metric_details dict so existing rendering shows them without new templates
- Company missing from Frames data returns None percentile (not 50th) -- absence of data is not average

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed AcquiredData attribute access**
- **Found during:** Task 2 (BenchmarkStage wiring)
- **Issue:** Code used `state.acquired_data.get("filings", {})` but AcquiredData is a Pydantic model, not a dict
- **Fix:** Changed to `state.acquired_data.filings` (Pydantic attribute access)
- **Files modified:** src/do_uw/stages/benchmark/__init__.py
- **Verification:** Pipeline tests pass (9/9)
- **Committed in:** 09c9e2e (Task 2 commit)

**2. [Rule 3 - Blocking] Registered signals in financial_health.yaml facet**
- **Found during:** Task 2 (peer signals YAML creation)
- **Issue:** brain contract test requires every active signal to be in exactly one facet
- **Fix:** Added 6 FIN.PEER signals to peer_matrix facet in financial_health.yaml
- **Files modified:** src/do_uw/brain/sections/financial_health.yaml
- **Verification:** test_brain_contract.py passes
- **Committed in:** 09c9e2e (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- Pre-existing test failures in tests/knowledge/ (test_enriched_roundtrip, test_enrichment, test_migrate), tests/render/test_peril_scoring_html, tests/stages/acquire/test_orchestrator_brain, tests/stages/analyze/test_regression_baseline -- all confirmed unrelated to this plan's changes by running against pre-change codebase

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 72 (Peer Benchmarking) is now complete (both plans done)
- Frames percentiles available in BenchmarkResult.frames_percentiles for Phase 73 rendering
- 6 peer signals will fire during ANALYZE stage for companies with Frames data
- Phase 73 can build dedicated percentile display templates

---
*Phase: 72-peer-benchmarking*
*Completed: 2026-03-07*
