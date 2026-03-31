---
phase: 39-system-integration-quality-validation
plan: 03
subsystem: analyze
tags: [classify, hazard, directory-restructure, imports]

requires:
  - phase: 29-architectural-cleanup
    provides: conceptual absorption of classify/hazard into ANALYZE
provides:
  - Physical directory move completing Phase 29 architectural intent
  - Clean import paths under analyze/layers/
affects: [analyze, classify, hazard, scoring]

key-files:
  created:
    - src/do_uw/stages/analyze/layers/__init__.py
    - src/do_uw/stages/analyze/layers/classify/__init__.py
    - src/do_uw/stages/analyze/layers/hazard/__init__.py
  modified:
    - src/do_uw/stages/analyze/__init__.py
    - tests/test_classification.py
    - tests/test_classification_integration.py
    - tests/test_hazard_engine.py
    - tests/test_hazard_dimensions.py

key-decisions:
  - "No backwards-compat shims — all imports updated directly"
  - "Old directories completely deleted"

requirements-completed: []

duration: 15min
completed: 2026-02-21
---

# Plan 39-03: Move classify/ and hazard/ into analyze/layers/ Summary

**17 files moved to analyze/layers/, 50+ imports updated, old directories deleted, zero shims**

## Performance

- **Duration:** 15 min
- **Tasks:** 1
- **Files modified:** 23

## Accomplishments
- Moved classify/ (3 files) and hazard/ (14 files) into analyze/layers/
- Updated all 50+ import paths across source and test files
- Deleted old directories completely
- 117 tests pass, 6 skipped, zero old-path imports remain

## Task Commits

1. **Task 1: Move and update all imports** - `5cf31bc` (refactor)

## Deviations from Plan
None — plan executed as written.

---
*Phase: 39-system-integration-quality-validation*
*Completed: 2026-02-21*
