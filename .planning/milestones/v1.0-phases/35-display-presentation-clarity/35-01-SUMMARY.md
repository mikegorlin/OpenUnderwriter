---
phase: 35-display-presentation-clarity
plan: 01
subsystem: models, analyze
tags: [density, pydantic, three-tier, section-assessment, backward-compat]

# Dependency graph
requires:
  - phase: 29-architectural-cleanup
    provides: "Boolean *_clean section assessments in ANALYZE stage"
provides:
  - "DensityLevel enum (CLEAN/ELEVATED/CRITICAL)"
  - "SectionDensity model with per-subsection overrides"
  - "PreComputedNarratives model for BENCHMARK-stage LLM narratives"
  - "Three-tier section density computation in section_assessments.py"
  - "section_densities dict on AnalysisResults"
  - "pre_computed_narratives field on AnalysisResults"
affects: [35-02, 35-03, 35-04, 35-05, 35-06, 35-07, render, benchmark]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Three-tier density enum (StrEnum)", "Per-subsection density overrides", "Deprecated field with json_schema_extra marker"]

key-files:
  created:
    - src/do_uw/models/density.py
    - tests/stages/analyze/test_section_assessments.py
  modified:
    - src/do_uw/models/state.py
    - src/do_uw/models/__init__.py
    - src/do_uw/stages/analyze/section_assessments.py

key-decisions:
  - "DensityLevel as StrEnum with CLEAN/ELEVATED/CRITICAL values per user's locked decision"
  - "Boolean *_clean fields deprecated with json_schema_extra but preserved for backward compat"
  - "Governance subsection IDs match v6 framework: 4.1_people_risk, 4.2_structural_governance, 4.3_transparency, 4.4_activist"
  - "Missing data defaults to ELEVATED (unknown risk) for governance/financial/market; CLEAN for litigation (no evidence = no issues)"
  - "Typed closure default factories for list fields per project pattern"

patterns-established:
  - "Three-tier density assessment: _compute_*_density() returns SectionDensity with level, concerns, critical_evidence"
  - "Per-subsection overrides: governance 4.1-4.4, each independently assessed then worst-level aggregated"
  - "_worst_level() helper for escalation from list of DensityLevel values"

requirements-completed: [CORE-04]

# Metrics
duration: 6min
completed: 2026-02-21
---

# Phase 35 Plan 01: Three-Tier Density Model Summary

**DensityLevel enum (CLEAN/ELEVATED/CRITICAL) with SectionDensity per-subsection overrides, PreComputedNarratives model, and upgraded section_assessments.py replacing boolean clean fields**

## Performance

- **Duration:** 6 min
- **Started:** 2026-02-21T14:47:56Z
- **Completed:** 2026-02-21T14:53:36Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created density.py with DensityLevel (3-value StrEnum), SectionDensity (level + subsection_overrides + concerns + critical_evidence), and PreComputedNarratives (8 section fields + meeting prep questions)
- Extended AnalysisResults with section_densities dict and pre_computed_narratives field; deprecated boolean *_clean fields
- Rewrote section_assessments.py with four density helpers computing governance (4 subsections), litigation, financial, and market density levels
- 32 tests covering all density tiers, subsection overrides, backward compat booleans, and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Create density models and extend AnalysisResults** - `9fc92a4` (feat)
2. **Task 2: Upgrade section_assessments.py to three-tier density** - `aaa541c` (feat)

## Files Created/Modified
- `src/do_uw/models/density.py` - DensityLevel enum, SectionDensity model, PreComputedNarratives model
- `src/do_uw/models/state.py` - Added section_densities + pre_computed_narratives fields; deprecated *_clean fields
- `src/do_uw/models/__init__.py` - Export DensityLevel, SectionDensity, PreComputedNarratives
- `src/do_uw/stages/analyze/section_assessments.py` - Rewrote with three-tier density computation (484 lines)
- `tests/stages/analyze/test_section_assessments.py` - 32 tests across 7 test classes

## Decisions Made
- DensityLevel as StrEnum with CLEAN/ELEVATED/CRITICAL -- matches user's locked decision on three tiers
- Boolean *_clean fields deprecated via json_schema_extra={"deprecated": True} per Phase 17-04 project pattern
- Governance subsection IDs (4.1_people_risk, 4.2_structural_governance, 4.3_transparency, 4.4_activist) align with v6 framework section numbering
- Missing governance/financial/market data defaults to ELEVATED (unknown risk); missing litigation defaults to CLEAN (no evidence of issues)
- Activist presence classified as CRITICAL (known activists indicate active campaigns with significant D&O exposure)
- Board independence thresholds: < 50% CRITICAL, 50-75% ELEVATED, >= 75% CLEAN
- Short interest thresholds: >= 10% CRITICAL, 5-10% ELEVATED, < 5% CLEAN
- Stock drop thresholds: >= 10% CRITICAL, 5-10% ELEVATED
- Insider cluster selling: >= 3 events CRITICAL, 1-2 ELEVATED

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- SourcedValue requires as_of field (datetime) -- test helper _sv() initially missing this required parameter; fixed immediately (Rule 1 auto-fix within test writing, not a plan deviation)

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- DensityLevel enum and SectionDensity model are ready for all downstream Phase 35 plans
- Plan 02 (check-type display mapping) can use density levels for conditional rendering
- Plan 03 (LLM narrative generation) can populate PreComputedNarratives model
- All existing pipeline code continues to work via backward-compat boolean *_clean fields

## Self-Check: PASSED

All 5 created/modified files verified on disk. Both task commits (9fc92a4, aaa541c) verified in git log.

---
*Phase: 35-display-presentation-clarity*
*Completed: 2026-02-21*
