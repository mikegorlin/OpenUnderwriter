---
phase: 137-canonical-metrics-registry
plan: 01
subsystem: render
tags: [pydantic, xbrl, provenance, metrics-registry, frozen-model]

requires:
  - phase: 132-page-0-decision-dashboard
    provides: XBRL data extraction patterns, yfinance info access, fmt_large_number

provides:
  - MetricValue frozen Pydantic model with provenance (raw, formatted, source, confidence, as_of)
  - CanonicalMetrics model with 22 cross-section metrics
  - build_canonical_metrics() function computing all metrics from AnalysisState
  - XBRL-first source priority chain for all financial metrics

affects: [137-02, context-builders, beta-report, key-stats, section-renderers]

tech-stack:
  added: []
  patterns: [frozen-metric-registry, resolver-per-metric, xbrl-first-fallback-chain]

key-files:
  created:
    - src/do_uw/stages/render/canonical_metrics.py
    - src/do_uw/stages/render/_canonical_resolvers.py
    - src/do_uw/stages/render/_canonical_resolvers_fin.py
    - tests/test_canonical_metrics.py
  modified: []

key-decisions:
  - "Split resolvers into 3 files (<500 lines each) per Anti-Context-Rot rule"
  - "MetricValue uses str confidence field instead of Confidence enum for serialization simplicity"
  - "Resolver functions are public (resolve_*) not private (_resolve_*) for testability"

patterns-established:
  - "Resolver pattern: one function per metric returning MetricValue with try/except isolation"
  - "XBRL-first priority: xbrl:10-K > state SourcedValue > yfinance:info > default N/A"
  - "Provenance format: source='xbrl:10-K:FY2024', confidence='HIGH', as_of='FY2024'"

requirements-completed: [METR-01, METR-02, METR-03]

duration: 11min
completed: 2026-03-27
---

# Phase 137 Plan 01: Canonical Metrics Registry Summary

**Frozen MetricValue/CanonicalMetrics registry with 22 metrics, XBRL-first source priority, and full provenance tracking (source, confidence, as_of) validated against real AAPL state**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-27T20:41:39Z
- **Completed:** 2026-03-27T20:52:52Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files created:** 4

## Accomplishments

- MetricValue frozen Pydantic model with raw, formatted, source, confidence, as_of fields
- CanonicalMetrics model with 22 metrics across identity (6), financial (10), market (4), scoring (2)
- build_canonical_metrics() with per-resolver try/except isolation -- one failure never crashes registry
- XBRL-first source priority chain validated against real AAPL state.json (all 8 core metrics populated)
- 14 tests covering XBRL source verification, provenance completeness, empty state graceful degradation

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `e3590df9` (test)
2. **Task 1 GREEN: Implementation** - `25a30142` (feat)

## Files Created/Modified

- `src/do_uw/stages/render/canonical_metrics.py` - Public API: MetricValue, CanonicalMetrics, build_canonical_metrics (194 lines)
- `src/do_uw/stages/render/_canonical_resolvers.py` - Identity, market, scoring resolvers + shared helpers (367 lines)
- `src/do_uw/stages/render/_canonical_resolvers_fin.py` - Financial statement resolvers (income, balance sheet) (228 lines)
- `tests/test_canonical_metrics.py` - 14 tests against real AAPL state + empty state edge cases (233 lines)

## Decisions Made

- **3-file split**: Original single-file implementation was 782 lines. Split into canonical_metrics.py (models + builder), _canonical_resolvers.py (identity/market/scoring), _canonical_resolvers_fin.py (financial) to comply with 500-line Anti-Context-Rot rule.
- **String confidence over Confidence enum**: MetricValue uses `confidence: str = "LOW"` instead of importing the Confidence enum. Simpler serialization, avoids coupling MetricValue to the common models module.
- **Public resolver names**: resolve_revenue() not _resolve_revenue() -- enables direct testing and potential reuse by context builders wanting individual metrics.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Split into 3 files for Anti-Context-Rot compliance**
- **Found during:** Task 1 (implementation)
- **Issue:** Single canonical_metrics.py was 782 lines, exceeding the 500-line limit in CLAUDE.md
- **Fix:** Split resolvers into _canonical_resolvers.py (identity/market/scoring) and _canonical_resolvers_fin.py (financial). Used lazy imports to avoid circular dependency (resolvers import MetricValue from canonical_metrics.py).
- **Files modified:** All 3 source files
- **Verification:** All 14 tests pass, no circular imports, all files under 500 lines
- **Committed in:** 25a30142

---

**Total deviations:** 1 auto-fixed (Rule 2 - structural compliance)
**Impact on plan:** File split was necessary for CLAUDE.md compliance. No scope creep. All plan artifacts delivered.

## Issues Encountered

None.

## Known Stubs

None -- all metrics are wired to real state data paths.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- CanonicalMetrics registry ready for Plan 02 (wiring context builders to use registry)
- All 22 metrics have explicit source priority chains
- Empty state produces safe N/A defaults for all metrics
- Integration validated against real AAPL state.json

## Self-Check: PASSED

All 4 files exist. Both commits (e3590df9, 25a30142) verified in git log.

---
*Phase: 137-canonical-metrics-registry*
*Completed: 2026-03-27*
