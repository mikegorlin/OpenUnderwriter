---
phase: 27-peril-mapping-bear-case-framework
plan: 04
subsystem: scoring
tags: [bear-case, peril-mapping, allegation-theory, evidence-gate, pipeline-gaps]

# Dependency graph
requires:
  - phase: 27-01
    provides: DataStatus enum, pipeline audit tooling, check classification
  - phase: 27-02
    provides: PerilMap models, 7-lens assessment engine, plaintiff firm config
provides:
  - Evidence-gated bear case builder producing litigation narratives from findings
  - ScoreStage Step 14 integrating peril mapping and bear cases
  - FWRD check prefix wired to existing earnings, debt, litigation data
affects: [27-05-render-integration, worksheet-output, peril-map-display]

# Tech tracking
tech-stack:
  added: []
  patterns: [evidence-gated-construction, structured-committee-summary, theory-to-plaintiff-mapping]

key-files:
  created:
    - src/do_uw/stages/score/bear_case_builder.py
    - tests/stages/score/test_bear_case_builder.py
  modified:
    - src/do_uw/stages/score/__init__.py
    - src/do_uw/stages/analyze/check_mappers.py
    - src/do_uw/stages/analyze/check_mappers_phase26.py

key-decisions:
  - "Bear cases gated on MODERATE/HIGH exposure only -- clean companies get zero bear cases"
  - "Committee summary uses structured templates (2-3 sentences) for reproducibility"
  - "Defense assessment returns None unless company-specific provisions found"
  - "FWRD checks wired through Phase 26 mapper to reuse existing data paths"
  - "Peril map construction wrapped in try/except to not block scoring on failure"

patterns-established:
  - "Evidence gate: only MODERATE/HIGH exposure theories produce bear cases"
  - "Theory-to-plaintiff mapping: A_DISCLOSURE->SHAREHOLDERS, C_PRODUCT_OPS->REGULATORS"

# Metrics
duration: 10min
completed: 2026-02-12
---

# Phase 27 Plan 04: Bear Case Builder and ScoreStage Integration Summary

**Evidence-gated bear case construction with 2-3 sentence committee summaries, ScoreStage Step 14 peril mapping integration, and FWRD check prefix pipeline gap closure**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-12T21:06:13Z
- **Completed:** 2026-02-12T21:16:04Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Bear case builder produces litigation narratives ONLY where MODERATE/HIGH exposure exists -- clean companies get zero bear cases
- ScoreStage now runs 17 steps with Step 14 building peril map + bear cases after red flag summary
- FWRD checks (forward-looking indicators) now wired to existing earnings guidance, debt structure, and litigation data
- 89 score tests pass (26 new bear case tests + 63 existing), 2865 total tests pass with 0 regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement evidence-gated bear case builder** - `acf904d` (feat)
2. **Task 2: Wire peril mapping + bear cases into ScoreStage, close pipeline gaps** - `bb284b1` (feat)

## Files Created/Modified
- `src/do_uw/stages/score/bear_case_builder.py` - Evidence-gated bear case construction with committee summaries and defense assessment
- `tests/stages/score/test_bear_case_builder.py` - 26 tests covering gate logic, summary structure, defense, evidence chain ordering
- `src/do_uw/stages/score/__init__.py` - Step 14 added: build_peril_map + build_bear_cases, store on AnalysisResults
- `src/do_uw/stages/analyze/check_mappers_phase26.py` - FWRD.EVENT and FWRD.NARRATIVE checks wired to existing data
- `src/do_uw/stages/analyze/check_mappers.py` - FWRD routing comment updated

## Decisions Made
- Evidence gate uses exposure_level from AllegationMapping (MODERATE/HIGH only) -- same threshold used by the scoring pipeline
- Committee summary structured as exactly 2-3 sentences: company+exposure, key evidence, severity context (3rd only if >= MODERATE)
- Defense assessment checks market data (Section 11 windows) and governance data (governance score, CEO-Chair duality) -- no generic defenses
- FWRD.WARN checks (Glassdoor, LinkedIn, etc.) left as DATA_UNAVAILABLE since they need web scraping not yet in ACQUIRE
- Peril map construction wrapped in try/except to prevent scoring stage failure if peril map has issues

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed str vs SourcedValue type on EarningsGuidance.philosophy**
- **Found during:** Task 2 (FWRD mapper wiring)
- **Issue:** `_safe_sv(eg.philosophy)` called `.value` on a plain `str` field, causing AttributeError
- **Fix:** Changed to direct access `eg.philosophy` instead of unwrapping
- **Files modified:** src/do_uw/stages/analyze/check_mappers_phase26.py
- **Verification:** Phase 26 integration test passes
- **Committed in:** bb284b1 (Task 2 commit)

**2. [Rule 1 - Bug] Section 11 defense check incorrectly nested under litigation gate**
- **Found during:** Task 1 (bear case builder tests)
- **Issue:** Section 11 window defense checked `extracted.market` but was gated behind `if lit is not None:`
- **Fix:** Moved Section 11 check to its own block reading from `extracted.market` directly
- **Files modified:** src/do_uw/stages/score/bear_case_builder.py
- **Verification:** Defense assessment tests pass
- **Committed in:** acf904d (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes were necessary for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Peril map and bear cases fully integrated into scoring pipeline
- Plan 05 (render integration) can now consume state.analysis.peril_map for worksheet output
- All scoring outputs (factors, patterns, CRF, allegations, probability, severity, tower, peril map) are available for rendering

## Self-Check: PASSED

- All 5 key files verified present on disk
- Commit acf904d (Task 1) verified in git log
- Commit bb284b1 (Task 2) verified in git log
- 89 score tests pass, 2865 total tests pass

---
*Phase: 27-peril-mapping-bear-case-framework*
*Completed: 2026-02-12*
