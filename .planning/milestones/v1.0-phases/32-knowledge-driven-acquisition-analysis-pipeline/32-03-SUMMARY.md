---
phase: 32-knowledge-driven-acquisition-analysis-pipeline
plan: 03
subsystem: documentation
tags: [taxonomy, questions, review, v6, knowledge-framework]

# Dependency graph
requires:
  - phase: 32-01
    provides: brain DuckDB schema with 388 checks and 57 taxonomy entities
  - phase: 32-02
    provides: enrichment data mapping 388 checks to risk questions, hazards, framework layers
provides:
  - QUESTIONS-FINAL.md — canonical v6 question framework (231 questions, 5 sections, 45 subsections) approved by user
  - Review Decisions documenting 11 user decisions from section-by-section review
  - Structural Relocation Map (v4->v5->v6) for traceability
  - Mapping Audit Results (1,097 checks mapped, 0 unaccounted)
affects: [32-04, 32-05, 32-06, 32-07]

# Tech tracking
tech-stack:
  added: []
  patterns: [question-numbering-drives-check-mapping]

key-files:
  created:
    - .planning/phases/32-knowledge-driven-acquisition-analysis-pipeline/QUESTIONS-FINAL.md
  modified:
    - .planning/phases/32-knowledge-driven-acquisition-analysis-pipeline/QUESTIONS-REVIEW.md

key-decisions:
  - "v6 has 231 questions (up from v5.1's 225 after count correction, down from raw v5.1 after removing 9 aspirational questions)"
  - "Insider trading (7 questions) relocated from GOVERNANCE to MARKET section 2.8 — market signal data, not governance structure"
  - "9 aspirational questions requiring internal/policy access moved to DEFERRED table instead of deleted"
  - "Governance questions reframed to prioritize experience > litigation history > turnover > negative publicity"
  - "Stock drop thresholds lowered (5% single-day, 10% multi-day) and window extended to 18 months"
  - "Data Feasibility and Granularity Rule added as cross-cutting principles"
  - "Runoff/tail coverage (Section 5.10) deferred to future version"

patterns-established:
  - "Section.Subsection.Question numbering (X.Y.Z) as stable identifiers for downstream mapping"
  - "DEFERRED table for aspirational items with reasons — nothing deleted, everything tracked"

# Metrics
duration: 2min
completed: 2026-02-20
---

# Phase 32 Plan 03: Interactive User Review Summary

**Finalized v6 question framework (231 questions, 5 sections, 45 subsections) after section-by-section user review with 11 documented decisions**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-20T15:50:35Z
- **Completed:** 2026-02-20T15:53:17Z
- **Tasks:** 3 (2 checkpoint:decision + 1 auto)
- **Files modified:** 2

## Accomplishments
- User reviewed all 5 sections of v5.1 framework and provided decisions on structure, boundaries, additions, and removals
- Produced QUESTIONS-FINAL.md as the canonical reference — no color codes, all decisions finalized
- Documented 11 review decisions (automation filter, insider trading relocation, governance reframing, threshold changes, etc.)
- Preserved Structural Relocation Map (v4->v5->v6) and Mapping Audit Results for full traceability
- Corrected summary table to match actual question counts (231, not 208 as initially stated)

## Task Commits

Each task was committed atomically:

1. **Task 1: Review Sections 1-2** - User checkpoint (no commit — interactive review)
2. **Task 2: Review Sections 3-5** - User checkpoint (no commit — interactive review)
3. **Task 3: Produce finalized QUESTIONS-FINAL.md** - `7f0b8ee` (docs)

## Files Created/Modified
- `.planning/phases/32-knowledge-driven-acquisition-analysis-pipeline/QUESTIONS-FINAL.md` - Canonical v6 question framework: 231 questions, 5 sections, 45 subsections, process insights, deferred items, relocation map, mapping audit
- `.planning/phases/32-knowledge-driven-acquisition-analysis-pipeline/QUESTIONS-REVIEW.md` - v5.1 review draft (base document for the review process)

## Decisions Made
1. Automation feasibility filter — 9 questions requiring internal/policy access moved to DEFERRED (not deleted)
2. Insider trading relocation — 7 questions moved from Section 4 to Section 2.8 (market signal data)
3. Governance reframing — Experience > litigation history > turnover > negative publicity
4. Stock drop thresholds — Lowered to 5% single-day, 10% multi-day; window extended to 18 months
5. Trend analysis required — Short interest and institutional ownership need 6-12 month trends
6. Runoff/tail deferred — Section 5.10 deferred to future version
7. Identity expansion — SIC, NAICS, GICS codes, incorporation state, exchange, FPI status upfront
8. SCORING clarification — Base D&O exposure and size-adjusted risk are SCORING outputs, not identity inputs
9. Data Feasibility principle — Added as cross-cutting principle
10. Granularity Rule — One question = one analytical judgment call
11. Subsection renumbering — Sections 4-5 renumbered after reorganization

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Summary table counts incorrect**
- **Found during:** Task 3 (Producing QUESTIONS-FINAL.md)
- **Issue:** Summary table claimed 208 questions (53+31+39+52+33) but actual count was 231 (59+31+42+62+37)
- **Fix:** Recounted all questions programmatically and corrected summary table
- **Files modified:** QUESTIONS-FINAL.md
- **Verification:** Python script verified all 5 section counts match
- **Committed in:** 7f0b8ee (Task 3 commit)

**2. [Rule 2 - Missing Critical] Structural Relocation Map and Mapping Audit not preserved**
- **Found during:** Task 3 (Producing QUESTIONS-FINAL.md)
- **Issue:** Plan explicitly requires preserving relocation map (v4->v5) and mapping audit from QUESTIONS-REVIEW.md, but QUESTIONS-FINAL.md did not include them
- **Fix:** Added updated Structural Relocation Map (extended to v4->v5->v6) and Mapping Audit Results table from QUESTIONS-REVIEW.md
- **Files modified:** QUESTIONS-FINAL.md
- **Verification:** Both sections present in final file
- **Committed in:** 7f0b8ee (Task 3 commit)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical)
**Impact on plan:** Both fixes ensure QUESTIONS-FINAL.md is complete and accurate. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- QUESTIONS-FINAL.md is the canonical reference for all subsequent plans
- Plan 04 (v6 taxonomy remap) can now remap enrichment data to the finalized v6 question numbering
- Plan 05 (pipeline integration) depends on stable section/question numbering from this plan
- Plan 06 (gap detection) can compare current checks against the finalized 231-question framework
- Plan 07 (Brain CLI + backtesting) can use v6 taxonomy for query interfaces

## Self-Check: PASSED

- QUESTIONS-FINAL.md verified present on disk
- Task 3 commit (7f0b8ee) verified in git log
- All 5 sections present with numbered subsections and questions
- No color codes remaining
- Summary table matches actual question counts (231)
- Review Decisions section documents 11 user decisions
- Structural Relocation Map preserved
- Mapping Audit Results preserved

---
*Phase: 32-knowledge-driven-acquisition-analysis-pipeline*
*Completed: 2026-02-20*
