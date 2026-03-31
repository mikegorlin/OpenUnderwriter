---
phase: 57-closed-learning-loop
plan: 02
subsystem: brain
tags: [duckdb, co-occurrence, correlation, pydantic, mining]

# Dependency graph
requires:
  - phase: 54-signal-contract-v2
    provides: BrainSignalEntry Pydantic schema with V2 fields
provides:
  - Co-occurrence mining engine (brain_correlation.py)
  - brain_correlations DuckDB table DDL
  - correlated_signals field on BrainSignalEntry
  - CORRELATION_ANNOTATION proposal generation
  - Configurable learning thresholds (learning_config.json)
affects: [57-closed-learning-loop]

# Tech tracking
tech-stack:
  added: []
  patterns: [co-occurrence mining via DuckDB cross-join, prefix-based redundancy detection]

key-files:
  created:
    - src/do_uw/brain/brain_correlation.py
    - src/do_uw/brain/config/learning_config.json
    - tests/brain/test_brain_correlation.py
  modified:
    - src/do_uw/brain/brain_schema.py
    - src/do_uw/brain/brain_signal_schema.py
    - tests/brain/test_brain_schema.py

key-decisions:
  - "Co-fire rate formula uses LEAST(a_total, b_total) denominator -- asymmetric but conservative"
  - "mine_cooccurrences returns tuple of (above, below) threshold pairs for full storage"
  - "Redundancy clusters require ALL pairwise combinations above threshold, not just any 3 signals"
  - "Proposals generated per-signal (not per-pair) with aggregated correlated_signals list"

patterns-established:
  - "DuckDB cross-join with CTE for co-occurrence analysis pattern"
  - "Prefix extraction via first 2 dot-segments for same-prefix classification"
  - "learning_config.json as single source for all learning loop thresholds"

requirements-completed: [LEARN-02]

# Metrics
duration: 29min
completed: 2026-03-02
---

# Phase 57 Plan 02: Co-Occurrence Mining Engine Summary

**DuckDB cross-join co-occurrence mining engine with same-prefix redundancy detection, configurable thresholds, and CORRELATION_ANNOTATION proposal generation**

## Performance

- **Duration:** 29 min
- **Started:** 2026-03-02T14:41:31Z
- **Completed:** 2026-03-02T15:10:40Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Co-occurrence mining engine that discovers correlated signal pairs from brain_signal_runs via DuckDB cross-join
- Same-prefix pairs labeled "potential_redundancy", cross-prefix labeled "risk_correlation"
- Redundancy cluster detection: 3+ same-prefix signals all co-firing >70% triggers consolidation warning
- High fire rate signals (>80%) excluded from mining to avoid spurious correlations (Pitfall 4)
- CORRELATION_ANNOTATION proposals generated for YAML write-back approval
- Configurable thresholds via learning_config.json
- 16 tests covering all mining, labeling, clustering, exclusion, and proposal behaviors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create brain_correlation.py with Pydantic models, co-occurrence mining engine, and schema extensions**
   - `f71b309` (test: TDD RED - failing tests for co-occurrence mining)
   - `59fc27e` (feat: TDD GREEN - implement mining engine with schema extensions)
2. **Task 2: Create learning_config.json with configurable thresholds** - `0a69ac4` (chore)

_Note: TDD task had test commit followed by implementation commit._

## Files Created/Modified
- `src/do_uw/brain/brain_correlation.py` - Co-occurrence mining engine (463 lines): mine_cooccurrences, detect_redundancy_clusters, generate_correlation_proposals, compute_correlation_report
- `src/do_uw/brain/config/learning_config.json` - Learning loop thresholds (co_fire=0.70, high_fire_rate=0.80, min_runs=5, confidence levels)
- `tests/brain/test_brain_correlation.py` - 16 test cases (416 lines)
- `src/do_uw/brain/brain_schema.py` - Added brain_correlations table DDL and idx_correlations_rate index
- `src/do_uw/brain/brain_signal_schema.py` - Added correlated_signals field to BrainSignalEntry
- `tests/brain/test_brain_schema.py` - Updated expected table count from 20 to 21

## Decisions Made
- Co-fire rate formula uses LEAST(a_total, b_total) as denominator -- conservative approach that captures asymmetric correlation (if A fires 100x and B fires 5x, and they co-fire all 5 times, rate = 5/5 = 1.0)
- mine_cooccurrences returns tuple of (above_threshold, below_threshold) pairs so both can be stored in brain_correlations for analysis
- Redundancy clusters require ALL pairwise combinations to appear above threshold, not just any 3 signals appearing in pairs -- this prevents false positives from partial overlap
- Proposals generated per-signal (not per-pair) with aggregated correlated_signals list to avoid duplicate proposals

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated test_brain_schema.py table count**
- **Found during:** Task 1 (schema extension)
- **Issue:** test_all_tables_exist expected 20 tables, new brain_correlations table makes it 21
- **Fix:** Updated expected table list and idempotent count assertion
- **Files modified:** tests/brain/test_brain_schema.py
- **Verification:** Full test suite passes (1369 passed, 3 pre-existing failures unrelated)
- **Committed in:** 59fc27e (part of Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary schema test update. No scope creep.

## Issues Encountered
- 3 pre-existing test failures in test_brain_enrich.py, test_enriched_roundtrip.py, and test_enrichment.py (content type count assertions stale from prior changes) -- confirmed pre-existing via git stash verification, not caused by this plan

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- brain_correlation.py ready for CLI wiring into `brain audit --calibrate` in Plan 03
- compute_correlation_report() returns structured CorrelationReport for CLI display formatting
- learning_config.json provides shared thresholds for both calibration (Plan 01) and correlation (this plan)

## Self-Check: PASSED

All 3 created files verified on disk. All 3 commit hashes verified in git log.

---
*Phase: 57-closed-learning-loop*
*Completed: 2026-03-02*
