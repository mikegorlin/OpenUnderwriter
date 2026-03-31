---
phase: 127-self-review-loop
plan: "01"
subsystem: validation
tags: [html-audit, json-report, cli, quality-assurance, boilerplate-detection]

requires:
  - phase: 124-css-density-overhaul
    provides: boilerplate patterns, borderless table CSS conventions
provides:
  - Self-review HTML audit module (run_self_review)
  - Structured JSON quality report with per-section scores
  - --review CLI flag for post-pipeline audit
  - Detection of LLM refusals, double-encoding, empty red flags, DDL discrepancies
affects: [render, cli, validation]

tech-stack:
  added: []
  patterns: [self-review audit pattern, per-section scoring, finding categorization]

key-files:
  created:
    - src/do_uw/stages/render/self_review.py
    - tests/test_self_review.py
    - .planning/phases/127-self-review-loop/127-01-PLAN.md
  modified:
    - src/do_uw/cli.py

key-decisions:
  - "Self-review module placed in stages/render/ alongside existing render infrastructure"
  - "Boilerplate patterns mirrored from formatters.py (not imported) to keep module self-contained"
  - "DDL check uses bidirectional pattern matching (dollar before/after DDL keyword)"
  - "Visual compliance scored by absence of legacy border/cellpadding attributes"

patterns-established:
  - "SelfReviewReport dataclass with to_json() for structured output"
  - "Per-section scoring: data_population, narrative_quality, visual_compliance"
  - "Finding categorization: refusal, encoding, red_flag, ddl, consistency"

requirements-completed: [REVIEW-01, REVIEW-02, REVIEW-03, REVIEW-04]

duration: 8min
completed: 2026-03-22
---

# Phase 127 Plan 01: Self-Review Loop Summary

**Automated HTML quality audit with per-section JSON scoring, CLI --review flag, and detection of LLM refusals, double-encoding, empty red flags, and DDL discrepancies**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-22T03:56:44Z
- **Completed:** 2026-03-22T04:05:00Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Self-review module reads HTML output and produces structured audit report with section counts, N/A tallies, empty section detection, boilerplate phrase matching, and data consistency checks (REVIEW-01)
- JSON report includes per-section scores for data_population, narrative_quality, and visual_compliance (REVIEW-02)
- --review CLI flag wired through both `analyze` command and `_app_init` shortcut (REVIEW-03)
- Specific detectors for LLM refusal messages (8 patterns), HTML double-encoding (12 patterns), empty red flags, and DDL discrepancies with 5x threshold (REVIEW-04)
- 48 tests covering all requirement areas

## Task Commits

1. **Tasks 1-3: Self-review module + CLI + tests** - `edff5532` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/self_review.py` - Self-review audit engine with run_self_review(), JSON report, console printer
- `src/do_uw/cli.py` - Added --review flag to analyze command and _app_init shortcut
- `tests/test_self_review.py` - 48 tests covering REVIEW-01 through REVIEW-04
- `.planning/phases/127-self-review-loop/127-01-PLAN.md` - Phase plan

## Decisions Made
- Placed self_review.py in stages/render/ (not validation/) since it reads rendered HTML output and is a render-stage concern
- Mirrored boilerplate patterns from formatters.py rather than importing to keep the module self-contained and testable
- Used bidirectional DDL pattern matching: "$X DDL" and "DDL ... $X" to catch both narrative orderings
- Visual compliance scored by detecting legacy HTML attributes (border=, cellpadding=) not CSS classes

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] DDL regex direction**
- **Found during:** Task 3 (test execution)
- **Issue:** DDL pattern only matched "$X DDL" but real worksheets often say "DDL estimate of $X"
- **Fix:** Added bidirectional pattern matching with 60-char lookahead
- **Files modified:** src/do_uw/stages/render/self_review.py
- **Verification:** DDL discrepancy tests pass

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor regex fix for correctness. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Self-review module ready for use with `underwrite TICKER --review`
- Future phases can extend SelfReviewReport with additional checks
- Module is independent of pipeline state (reads HTML file directly)

---
*Phase: 127-self-review-loop*
*Completed: 2026-03-22*
