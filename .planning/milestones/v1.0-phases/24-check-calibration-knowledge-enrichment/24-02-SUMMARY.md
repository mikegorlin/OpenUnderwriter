---
phase: 24-check-calibration-knowledge-enrichment
plan: 02
subsystem: calibration
tags: [pydantic, scoring, fire-rate, impact-ranking, evidence-quality]

requires:
  - phase: 24-01
    provides: CalibrationRunner, CalibrationReport, CalibrationTickerResult, CheckResultSummary
provides:
  - CheckAnalyzer computing fire rate, skip rate, evidence quality per check
  - ImpactRanker auto-ranking top N checks by weight x fire_rate x severity
  - Dead check, always-fire, high-skip, and low-evidence detection
  - Factor distribution analysis for mapping imbalance detection
affects: [24-03 anomaly-detection, 24-04 enrichment, 24-05 playbook-validation]

tech-stack:
  added: []
  patterns: [impact scoring formula, evidence quality heuristic, factor weight normalization F.1->F1]

key-files:
  created:
    - src/do_uw/calibration/analyzer.py
    - src/do_uw/calibration/impact_ranker.py
    - tests/test_calibration_analyzer.py
  modified: []

key-decisions:
  - "Factor ID normalization: scoring.json uses F.1 (dotted), checks.json uses F1 (undotted) -- ImpactRanker normalizes via replace('.', '')"
  - "Evidence quality heuristic: regex patterns detect generic evidence strings (Qualitative check:, Check value:, N/A, etc.); >50 chars + not-generic = specific"
  - "Dead check definition: fire_rate == 0.0 AND skip_rate < 0.5 (excludes checks that are merely data-unavailable)"
  - "Impact score formula: max(factor_weights) x fire_rate x avg_severity where red=3.0, yellow=2.0, clear=0.0"

patterns-established:
  - "CheckAnalyzer analyze-then-query pattern: call analyze() once, then use getter methods for filtered views"
  - "SimpleNamespace mock fixtures for parallel plan testing: tests work regardless of whether Plan 01 Pydantic models exist"
  - "Severity map for threshold levels: red=3.0, yellow=2.0, clear=0.0 as standard calibration severity weights"

duration: 5m 36s
completed: 2026-02-11
---

# Phase 24 Plan 02: Check Analyzer & Impact Ranker Summary

**CheckAnalyzer and ImpactRanker for cross-ticker check metrics with auto-ranking by weight x fire_rate x severity**

## Performance

- **Duration:** 5m 36s
- **Started:** 2026-02-12T00:14:12Z
- **Completed:** 2026-02-12T00:19:48Z
- **Tasks:** 2
- **Files created:** 3

## Accomplishments
- CheckAnalyzer computes fire rate, skip rate, and evidence quality for every check across all calibration tickers
- ImpactRanker automatically identifies top 20 highest-impact checks using the weight x fire_rate x severity formula with scoring.json factor weights
- Dead checks (0% fire rate), always-fire checks (100%), high-skip checks (>50%), and low-evidence checks are all identifiable via dedicated getter methods
- Factor distribution analysis can reveal the F10=102 mapping anomaly documented in RESEARCH.md
- 21 comprehensive unit tests covering both analyzer and ranker with synthetic 3-ticker, 5-check calibration data

## Task Commits

Each task was committed atomically:

1. **Task 1: Build CheckAnalyzer for cross-ticker check metrics** - `2c4b47e` (feat)
2. **Task 2: Build ImpactRanker and unit tests** - `2de481f` (feat)

## Files Created/Modified
- `src/do_uw/calibration/analyzer.py` (337 lines) - CheckAnalyzer class with fire rate, skip rate, evidence quality computation and getter methods for dead/always-fire/high-skip/low-evidence checks
- `src/do_uw/calibration/impact_ranker.py` (224 lines) - ImpactRanker class auto-ranking checks by impact score with factor distribution analysis and unmapped check detection
- `tests/test_calibration_analyzer.py` (581 lines) - 21 unit tests: 13 for CheckAnalyzer, 8 for ImpactRanker including integration test with analyzer output

## Decisions Made
- Factor ID normalization (F.1 -> F1) handles mismatch between scoring.json and checks.json formats
- Evidence quality uses regex heuristics rather than LLM evaluation (fast, deterministic, no API cost)
- SimpleNamespace mocks allow tests to run independently of Plan 01's Pydantic models (parallel execution safe)
- getattr-based attribute access in analyzer makes it compatible with any object providing the expected interface (duck typing for parallel plan safety)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pyright strict flagged unknown types when iterating dict[str, Any] from JSON -- resolved with cast() for type narrowing (standard pattern for this codebase)
- Plan 01 completed during execution (commit 86df7e9 appeared between Task 1 and Task 2 commits) -- no conflicts, parallel execution worked cleanly

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- CheckAnalyzer and ImpactRanker are ready for Plans 03-04 (anomaly detection and enrichment)
- The analyzer accepts any CalibrationReport-like object (duck-typed), so it works with Plan 01's actual Pydantic models
- Factor distribution analysis is ready to identify and quantify the F10=102 mapping anomaly
- Evidence quality detection is ready to flag generic/boilerplate evidence strings

## Self-Check: PASSED

- FOUND: src/do_uw/calibration/analyzer.py
- FOUND: src/do_uw/calibration/impact_ranker.py
- FOUND: tests/test_calibration_analyzer.py
- FOUND commit: 2c4b47e
- FOUND commit: 2de481f

---
*Phase: 24-check-calibration-knowledge-enrichment*
*Completed: 2026-02-11*
