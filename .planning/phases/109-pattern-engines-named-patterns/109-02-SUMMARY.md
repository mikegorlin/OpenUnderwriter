---
phase: 109-pattern-engines-named-patterns
plan: 02
subsystem: scoring
tags: [jaccard, xbrl, pattern-engine, case-library, archetypes, precedent-match, migration-drift]

# Dependency graph
requires:
  - phase: 106-scoring-severity-design
    provides: "Pattern engine design, case library design, archetype design documents"
  - phase: 107-hae-scoring
    provides: "HAETier enum, ScoringLens Protocol, CRF veto catalog"
provides:
  - "case_library.yaml: 20 canonical D&O cases with signal profiles"
  - "named_archetypes.yaml: 6 named risk archetypes with real signal IDs"
  - "MigrationDriftEngine: cross-domain deterioration detection from XBRL"
  - "PrecedentMatchEngine: weighted Jaccard similarity against case library"
affects: [109-03-pattern-engines-named-patterns, 110-mechanism-evaluation, 112-render-v7]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Weighted Jaccard similarity for binary signal fingerprints"
    - "Standardized OLS slope for quarterly XBRL trend detection"
    - "Module-level lru_cache singleton for case library loading"

key-files:
  created:
    - src/do_uw/brain/framework/case_library.yaml
    - src/do_uw/brain/framework/named_archetypes.yaml
    - src/do_uw/stages/score/migration_drift.py
    - src/do_uw/stages/score/precedent_match.py
    - tests/stages/score/test_case_library.py
    - tests/stages/score/test_archetypes.py
    - tests/stages/score/test_migration_drift.py
    - tests/stages/score/test_precedent_match.py
  modified: []

key-decisions:
  - "CRF signal weighting uses 12 signal IDs from scoring_model_design.yaml CRF veto catalog (3x weight)"
  - "Case library trimmed to exactly 20 cases matching design doc spec (6 HIGH, 14 MEDIUM)"
  - "Migration drift uses standardized OLS slope / std(values) for cross-metric comparison"
  - "Precedent match confidence is adjusted similarity (raw * confidence_weight) not match_score"

patterns-established:
  - "Pattern engine data files: YAML in brain/framework/, loaded via lru_cache singleton"
  - "Weighted Jaccard: sum(w*min)/sum(w*max) with CRF 3x, confidence tier adjustment"

requirements-completed: [PAT-03, PAT-04, PAT-05, PAT-06]

# Metrics
duration: 15min
completed: 2026-03-16
---

# Phase 109 Plan 02: Case Library + Migration Drift + Precedent Match Summary

**20-case D&O precedent library with weighted Jaccard similarity engine and XBRL quarterly drift detection across host/agent/environment RAP categories**

## Performance

- **Duration:** 15 min
- **Started:** 2026-03-16T03:13:16Z
- **Completed:** 2026-03-16T03:28:00Z
- **Tasks:** 3
- **Files created:** 8

## Accomplishments
- 20 canonical D&O cases (Enron through SVB) with reconstructed signal profiles validated against CaseLibraryEntry schema
- 6 named archetypes (desperate_growth_trap, governance_vacuum, post_spac_hangover, accounting_time_bomb, regulatory_reckoning, ai_mirage) validated against PatternDefinition schema
- MigrationDriftEngine detects cross-domain deterioration from 4-8 quarters of XBRL data across host/agent/environment categories
- PrecedentMatchEngine computes weighted Jaccard similarity with CRF 3x weighting, confidence tier adjustment, and dismissed case 0.5x severity
- 50 tests passing across 4 test files

## Task Commits

Each task was committed atomically:

1. **Task 1: Case library + archetypes YAML + validation tests** - `563d57e` (feat)
2. **Task 2: MigrationDriftEngine (TDD)** - `86fe9b1` (test RED), `2056e12` (feat GREEN)
3. **Task 3: PrecedentMatchEngine (TDD)** - `c51d6f0` (test RED), `f5422d7` (feat GREEN)

## Files Created/Modified
- `src/do_uw/brain/framework/case_library.yaml` - 20 canonical D&O cases with signal profiles and outcomes
- `src/do_uw/brain/framework/named_archetypes.yaml` - 6 named archetypes conforming to PatternDefinition
- `src/do_uw/stages/score/migration_drift.py` - MigrationDriftEngine with XBRL quarterly trend detection
- `src/do_uw/stages/score/precedent_match.py` - PrecedentMatchEngine with weighted Jaccard similarity
- `tests/stages/score/test_case_library.py` - 12 tests for case library YAML validation
- `tests/stages/score/test_archetypes.py` - 12 tests for archetypes YAML validation
- `tests/stages/score/test_migration_drift.py` - 9 tests for migration drift engine
- `tests/stages/score/test_precedent_match.py` - 17 tests for precedent match engine

## Decisions Made
- CRF signal IDs for 3x weighting sourced directly from scoring_model_design.yaml CRF veto catalog (12 signal IDs across 5 CRF categories)
- Migration drift uses standardized slope (slope / std) rather than raw slope for cross-metric comparability
- Precedent match confidence = raw_similarity * confidence_tier_weight (HIGH=1.0, MEDIUM=0.8, LOW=0.6)
- Case library trimmed to exactly 20 cases: removed GE, PGE, Purdue to match plan spec of 6 HIGH + 14 MEDIUM

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 109-01 dependency files already created by parallel execution**
- **Found during:** Task 1 start
- **Issue:** pattern_engine.py and models/patterns.py already existed from 109-01 parallel execution
- **Fix:** Used existing files rather than creating new ones; restored models/patterns.py after accidental overwrite
- **Files affected:** src/do_uw/models/patterns.py, src/do_uw/stages/score/pattern_engine.py
- **Verification:** All imports resolve correctly, 50 tests pass

**2. [Rule 1 - Bug] SourcedValue requires as_of field in test helper**
- **Found during:** Task 2 (MigrationDriftEngine tests)
- **Issue:** Test helper creating SourcedValue without required as_of datetime field
- **Fix:** Added as_of=datetime.now(tz=UTC) to test helper _make_quarterly_period
- **Files modified:** tests/stages/score/test_migration_drift.py
- **Verification:** All 9 migration drift tests pass

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both engines implement PatternEngine Protocol, ready for 109-03 engine orchestrator integration
- Case library and archetypes YAML ready for consumption by 109-03 archetype evaluator
- All 4 pattern engines now exist (Conjunction Scan + Peer Outlier from 109-01, Migration Drift + Precedent Match from 109-02)

## Self-Check: PASSED

All 9 created files verified on disk. All 5 commits verified in git log.

---
*Phase: 109-pattern-engines-named-patterns*
*Completed: 2026-03-16*
