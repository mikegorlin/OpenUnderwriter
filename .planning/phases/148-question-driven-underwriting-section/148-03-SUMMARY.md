---
phase: 148-question-driven-underwriting-section
plan: 03
subsystem: render
tags: [jinja2, context-builders, sca, verdict-badges, print-css]

requires:
  - phase: 148-01
    provides: "55 answerers in ANSWERER_REGISTRY + _helpers.py"
  - phase: 148-02
    provides: "generate_sca_questions() + answer_sca_question() in sca_questions.py"
provides:
  - "SCA questions slotted inline into domain groups by domain key"
  - "Domain-level verdict badges (FAVORABLE/UNFAVORABLE/MIXED)"
  - "Section-level verdict badge via section_verdict key"
  - "Context ordering fix: uw_questions built after all analysis contexts"
  - "Print-ready CSS for verdict badges and colored elements"
affects: [render, uw-analysis, worksheet-output]

tech-stack:
  added: []
  patterns: ["domain verdict computed from upgrade/downgrade net count", "SCA questions appended after brain questions per domain"]

key-files:
  created: []
  modified:
    - "src/do_uw/stages/render/context_builders/uw_questions.py"
    - "src/do_uw/stages/render/context_builders/uw_analysis.py"
    - "src/do_uw/templates/html/sections/report/uw_questions.html.j2"

key-decisions:
  - "Context ordering: uw_questions call moved after forensic/settlement/peril/exec_risk/temporal/investigative so answerers access all ctx keys"
  - "SCA questions appended after brain questions within each domain (not interleaved)"
  - "section_verdict uses same FAVORABLE/UNFAVORABLE/MIXED logic as domain verdicts"
  - "SCA source badge uses purple #6366F1 to visually distinguish from brain-derived questions"

patterns-established:
  - "Domain verdict: net = upgrades - downgrades; >0 FAVORABLE, <0 UNFAVORABLE, =0 MIXED"
  - "source field on formatted questions enables template-level source badges"

requirements-completed: [QFW-05, QFW-07]

duration: 2min
completed: 2026-03-28
---

# Phase 148 Plan 03: SCA Integration + Verdict Badges + Context Ordering Summary

**SCA questions slotted inline by domain with source badges, domain/section verdict badges, context ordering fix, and print CSS**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-28T20:52:18Z
- **Completed:** 2026-03-28T20:54:28Z
- **Tasks:** 1 of 2 (Task 2 is human-verify checkpoint)
- **Files modified:** 3

## Accomplishments
- SCA questions from Supabase claims data now appear inline within their matching domain groups (Litigation, Market, Operational)
- Each domain header shows a verdict badge (FAVORABLE/UNFAVORABLE/MIXED) based on net upgrade/downgrade count
- Section header shows overall assessment badge via section_verdict key
- Context ordering fixed: build_uw_questions_context now runs after all analysis context builders
- Print CSS ensures verdict dots, completeness bars, and domain badges render with correct colors in PDF

## Task Commits

Each task was committed atomically:

1. **Task 1: Integrate SCA questions + verdict badges + context ordering** - `b3b24b1a` (feat)

**Plan metadata:** pending (awaiting checkpoint completion)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/uw_questions.py` - Added SCA question integration, domain verdict badges, section_verdict, source field
- `src/do_uw/stages/render/context_builders/uw_analysis.py` - Moved uw_questions call after all analysis contexts
- `src/do_uw/templates/html/sections/report/uw_questions.html.j2` - Domain verdict badge, SCA source badge (purple), print CSS

## Decisions Made
- Context ordering: uw_questions call moved to after forensic/settlement/peril/exec_risk/temporal/investigative contexts so answerers can access all ctx keys
- SCA questions appended after brain questions within each domain (preserving brain question ordering)
- section_verdict uses same logic as domain verdicts (net upgrade/downgrade count)
- SCA source badge uses purple #6366F1 to visually distinguish from brain-derived questions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Known Stubs

None - all data paths are wired to real state data.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Task 2 (human-verify checkpoint) pending: visual verification of rendered worksheet
- All code changes complete and tested (14 tests passing)

---
*Phase: 148-question-driven-underwriting-section*
*Completed: 2026-03-28*
