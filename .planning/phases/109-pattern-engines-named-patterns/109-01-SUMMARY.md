---
phase: 109-pattern-engines-named-patterns
plan: 01
subsystem: scoring
tags: [pattern-engine, conjunction-scan, peer-outlier, z-score, mad, protocol, pydantic, yaml]

# Dependency graph
requires:
  - phase: 107-scoring-model
    provides: "ScoringLens Protocol pattern, HAETier, ScoringResult, TYPE_CHECKING + model_rebuild pattern"
  - phase: 108-severity-model
    provides: "SeverityLens Protocol pattern, SeverityResult, _rebuild_scoring_models"
  - phase: 106-research
    provides: "pattern_engine_design.yaml algorithm specifications"
provides:
  - "PatternEngine Protocol (runtime_checkable) with engine_id, engine_name, evaluate()"
  - "EngineResult and ArchetypeResult Pydantic models"
  - "PatternEngineResult state model with any_fired computed property"
  - "CaseLibraryEntry Pydantic model for case library YAML"
  - "ConjunctionScanEngine detecting cross-domain co-firing CLEAR signals"
  - "PeerOutlierEngine detecting multi-dimensional statistical outliers via MAD z-scores"
  - "seed_correlations.yaml with 20 curated D&O co-fire pairs"
  - "ScoringResult.pattern_engine_result field via TYPE_CHECKING + model_rebuild"
affects: [109-02, 109-03, 110-signal-rules, 112-rendering]

# Tech tracking
tech-stack:
  added: []
  patterns: [PatternEngine Protocol, seed + enrich data model, MAD-based z-scores, peer_data_override for testability]

key-files:
  created:
    - src/do_uw/stages/score/pattern_engine.py
    - src/do_uw/stages/score/conjunction_scan.py
    - src/do_uw/stages/score/peer_outlier.py
    - src/do_uw/brain/framework/seed_correlations.yaml
    - tests/stages/score/test_conjunction_scan.py
    - tests/stages/score/test_peer_outlier.py
  modified:
    - src/do_uw/models/patterns.py
    - src/do_uw/models/scoring.py

key-decisions:
  - "PatternEngine Protocol mirrors ScoringLens/SeverityLens with evaluate() returning EngineResult"
  - "Conjunction Scan uses correlations_override constructor param for testability and DuckDB supplement"
  - "Peer Outlier uses peer_data_override constructor param since real SEC Frames peer arrays not yet available at engine level"
  - "MAD (median absolute deviation) with 1.4826 consistency constant for robust z-scores"
  - "Seed correlations as alphabetically-sorted tuple keys for consistent lookup"

patterns-established:
  - "PatternEngine Protocol: engine_id property + engine_name property + evaluate(signal_results, *, state) -> EngineResult"
  - "correlations_override / peer_data_override constructor params for testing without YAML/DuckDB dependencies"
  - "Seed + enrich model: curated YAML data supplemented by DuckDB empirical data when available"

requirements-completed: [PAT-01, PAT-02]

# Metrics
duration: 6min
completed: 2026-03-16
---

# Phase 109 Plan 01: PatternEngine Protocol + Conjunction Scan + Peer Outlier Summary

**PatternEngine Protocol with two engine implementations: Conjunction Scan (cross-domain co-firing CLEAR signals from 20 seed correlations) and Peer Outlier (MAD-based z-score multi-dimensional outlier detection from SEC Frames data), 24 tests passing**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-16T03:12:28Z
- **Completed:** 2026-03-16T03:18:30Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- PatternEngine Protocol defined with runtime_checkable, mirroring ScoringLens/SeverityLens pattern
- ConjunctionScanEngine detects 3+ cross-domain co-firing CLEAR signals using seed correlation data (20 curated D&O pairs)
- PeerOutlierEngine detects multi-dimensional statistical outliers using MAD-based z-scores from SEC Frames data
- PatternEngineResult and CaseLibraryEntry Pydantic models for state integration
- ScoringResult extended with pattern_engine_result field via TYPE_CHECKING + model_rebuild pattern
- All thresholds configurable via constructor kwargs, no hardcoded values
- 24 tests across both engines covering protocol compliance, fire/no-fire scenarios, YAML loading, edge cases

## Task Commits

Each task was committed atomically (TDD: tests + implementation in single commit):

1. **Task 1: PatternEngine Protocol + Pydantic models + Conjunction Scan engine** - `1318a76` (feat)
2. **Task 2: Peer Outlier engine with SEC Frames z-score detection** - `20db8df` (feat)

## Files Created/Modified
- `src/do_uw/stages/score/pattern_engine.py` - PatternEngine Protocol + EngineResult + ArchetypeResult models (~100 lines)
- `src/do_uw/stages/score/conjunction_scan.py` - ConjunctionScanEngine implementation with seed YAML loading (~230 lines)
- `src/do_uw/stages/score/peer_outlier.py` - PeerOutlierEngine implementation with MAD z-scores (~230 lines)
- `src/do_uw/models/patterns.py` - PatternEngineResult + CaseLibraryEntry Pydantic models (~90 lines)
- `src/do_uw/models/scoring.py` - Added pattern_engine_result field to ScoringResult + updated model_rebuild
- `src/do_uw/brain/framework/seed_correlations.yaml` - 20 curated D&O co-fire pairs spanning all 3 RAP domains
- `tests/stages/score/test_conjunction_scan.py` - 12 tests for conjunction scan engine
- `tests/stages/score/test_peer_outlier.py` - 12 tests for peer outlier engine

## Decisions Made
- PatternEngine Protocol uses `evaluate(signal_results, *, state=None) -> EngineResult` rather than ScoringLens signature because pattern engines need full AnalysisState (for benchmarks access) not just company/liberty params
- Both engines use constructor injection for test overrides (correlations_override, peer_data_override) rather than test monkeypatching -- cleaner separation of concerns
- Peer Outlier synthesizes peer data from override in tests; real SEC Frames peer arrays will need extraction in the runner (109-02) when integrating with ScoreStage
- seed_correlations.yaml uses 20 entries (exceeding 15 minimum from plan) to cover all cross-domain combinations: host x agent, host x environment, agent x environment

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- PatternEngine Protocol ready for Migration Drift and Precedent Match engines (109-02)
- ScoringResult.pattern_engine_result field ready for ScoreStage integration (109-02)
- CaseLibraryEntry model ready for case library YAML seeding (109-02)
- All 280 score stage tests pass (256 existing + 24 new)

## Self-Check: PASSED

- All 7 created files exist on disk
- Commit 1318a76 (Task 1) verified in git log
- Commit 20db8df (Task 2) verified in git log
- 24 tests pass across both test files
- 280 total score stage tests pass (no regressions)

---
*Phase: 109-pattern-engines-named-patterns*
*Completed: 2026-03-16*
