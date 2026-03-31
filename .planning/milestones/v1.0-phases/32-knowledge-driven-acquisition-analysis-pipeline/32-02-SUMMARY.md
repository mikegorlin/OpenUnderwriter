---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
plan: 02
subsystem: brain
tags: [duckdb, enrichment, risk-questions, hazards, risk-framework]

# Dependency graph
requires:
  - phase: 32-01
    provides: brain_schema.py and brain_migrate.py (DuckDB schema + initial migration)
provides:
  - enrichment_data.py with 5 mapping tables (prefix->section, check->questions, check->hazards, check->framework-layer, check->characteristic)
  - brain_enrich.py applier that creates version 2 rows with enriched metadata
  - 23 validation tests covering completeness, changelog, spot-checks, distribution
affects: [32-03, 32-04, 32-05, 32-06, 32-07]

# Tech tracking
tech-stack:
  added: []
  patterns: [append-only-versioning, prefix-based-defaults-with-explicit-overrides]

key-files:
  created:
    - src/do_uw/brain/enrichment_data.py
    - src/do_uw/brain/brain_enrich.py
    - tests/brain/test_brain_enrich.py
    - src/do_uw/brain/__init__.py
    - src/do_uw/brain/brain_migrate.py
  modified: []

key-decisions:
  - "Enrichment uses prefix.subdomain defaults (53 patterns) plus explicit per-check overrides (84 checks) for risk question mapping"
  - "All 388 checks get risk_questions (not just evaluative), since MANAGEMENT_DISPLAY checks also belong to risk question scopes"
  - "Framework layer distribution: 37 inherent_risk (BIZ.*), 78 hazard (LIT.*, FWRD.EVENT.*), 273 risk_characteristic (rest)"
  - "Characteristic direction/strength mapped for 95 key signal checks from BRAIN-DESIGN.md risk characteristics table"

patterns-established:
  - "Prefix-based defaults with explicit overrides: SUBDOMAIN_TO_RISK_QUESTIONS provides defaults, CHECK_TO_RISK_QUESTIONS overrides for multi-question checks"
  - "Append-only versioning: enrichment creates version 2 rows (never modifies version 1), with changelog entries"

# Metrics
duration: 10min
completed: 2026-02-15
---

# Phase 32 Plan 02: Brain Check Enrichment Summary

**All 388 checks enriched with risk_questions (Q1-Q25), hazards (HAZ-*), report_section, risk_framework_layer, and characteristic direction/strength via append-only version 2 rows**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-16T01:30:07Z
- **Completed:** 2026-02-16T01:40:41Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created enrichment_data.py with 5 comprehensive mapping tables covering all 388 checks
- All 388 checks have report_section (across 7 sections) and risk_questions (Q1-Q25)
- 83 checks mapped to specific hazard codes (HAZ-SCA through HAZ-PRODUCT)
- 95 checks have characteristic direction (amplifier/mitigator/context) and strength
- Framework layer: 37 inherent_risk, 78 hazard, 273 risk_characteristic
- 23 validation tests (completeness, changelog, 5 spot-checks, distributions, hazard mapping)
- 388 brain_changelog entries documenting all enrichment changes

## Task Commits

Each task was committed atomically:

1. **Task 1: Enrichment data module** - `50e0d53` (feat)
2. **Task 2: Brain enrichment applier and tests** - `f68b4d1` (feat)

## Files Created/Modified
- `src/do_uw/brain/enrichment_data.py` - Static mapping tables: PREFIX_TO_REPORT_SECTION (8), SUBDOMAIN_TO_RISK_QUESTIONS (53), CHECK_TO_RISK_QUESTIONS (84), CHECK_TO_HAZARDS (83), CHECK_TO_RISK_FRAMEWORK_LAYER (115), CHECK_TO_CHARACTERISTIC (95)
- `src/do_uw/brain/brain_enrich.py` - enrich_brain_checks() creates version 2 rows with enriched metadata
- `tests/brain/test_brain_enrich.py` - 23 tests across 6 test classes
- `src/do_uw/brain/__init__.py` - Package init for brain module
- `src/do_uw/brain/brain_migrate.py` - Migration script (Rule 3 prerequisite)

## Decisions Made
- Used two-tier resolution: subdomain-based defaults (covers ~90% of checks) with explicit per-check overrides for multi-question mapping
- All 388 checks get risk_questions, not just the 324 evaluative ones -- MANAGEMENT_DISPLAY checks also belong to risk question scopes for dual-lens queries
- Characteristic direction/strength limited to 95 well-established signal checks from BRAIN-DESIGN.md; remaining checks can be refined in later iterations

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created brain_migrate.py prerequisite**
- **Found during:** Task 2 (test setup requires migration)
- **Issue:** Plan 01's brain_migrate.py was not yet committed (only brain_schema.py from Plan 01 Task 1 existed)
- **Fix:** Created brain_migrate.py with full migration logic (388 checks, 57 taxonomy entities, 7 backlog items)
- **Files modified:** src/do_uw/brain/brain_migrate.py
- **Verification:** migrate_checks_to_brain() returns correct counts, all tests pass
- **Committed in:** 50e0d53 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** brain_migrate.py was needed for test setup. Created minimal but complete implementation. No scope creep.

## Issues Encountered
- enrichment_data.py is 446 lines (data-only module with static mapping tables); this exceeds the 500-line anti-context-rot guideline but is acceptable since it contains only static data structures with no logic

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Brain checks fully enriched with dual-organization metadata (report sections + risk questions)
- Ready for Plan 03: pipeline integration to read check definitions from brain.duckdb at runtime
- All mapping tables available for query-based views (by section, by question, by hazard)

## Self-Check: PASSED

All files verified present. All commit hashes verified in git log.

---
*Phase: 32-knowledge-driven-acquisition-analysis-pipeline*
*Completed: 2026-02-15*
