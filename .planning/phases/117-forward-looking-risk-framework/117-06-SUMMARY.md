---
phase: 117-forward-looking-risk-framework
plan: 06
subsystem: render
tags: [pipeline-wiring, context-builders, jinja2, html-templates, integration]

requires:
  - phase: 117-01
    provides: ForwardLookingData model on AnalysisState
  - phase: 117-02
    provides: forward_statements extraction, credibility engine, miss risk
  - phase: 117-03
    provides: underwriting posture, monitoring triggers, quick screen
  - phase: 117-04
    provides: 5 context builders (forward_risk_map, credibility, monitoring, posture, quick_screen)
  - phase: 117-05
    provides: 10 Jinja2 templates (risk_map, credibility, catalysts, etc.)
provides:
  - Full pipeline wiring: EXTRACT -> ANALYZE -> BENCHMARK -> RENDER for forward-looking intelligence
  - Forward statement extraction in EXTRACT stage (Step 9)
  - Credibility/posture/triggers/quick-screen computation in BENCHMARK stage (Step 9)
  - 5 context builder calls in html_context_assembly.py
  - Trigger matrix in worksheet Zone 1.5 (after CRF, before domain sections)
  - Scoring enhancements (posture, zero verification, watch items) in scoring template
  - forward_looking as top-level manifest section with 11 groups
  - 23 integration tests
affects: [render, benchmark, extract, manifest]

tech-stack:
  added: []
  patterns:
    - "try/except graceful degradation for all forward-looking context builders"
    - "forward_looking manifest section with 11 facet groups"

key-files:
  created:
    - src/do_uw/templates/html/sections/forward_looking.html.j2
    - tests/stages/render/test_forward_integration.py
  modified:
    - src/do_uw/stages/extract/extract_market.py
    - src/do_uw/stages/benchmark/__init__.py
    - src/do_uw/stages/render/html_context_assembly.py
    - src/do_uw/templates/html/worksheet.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/brain/output_manifest.yaml
    - tests/stages/render/test_manifest_rendering.py

key-decisions:
  - "forward_looking elevated to top-level manifest section (moved from scoring sub-facets)"
  - "Trigger matrix placed in Zone 1.5 between CRF banner and domain sections for immediate UW visibility"
  - "All 5 context builders wrapped in try/except for graceful degradation"

patterns-established:
  - "Phase 117 integration pattern: try/except per context builder in html_context_assembly.py"

requirements-completed: [FORWARD-01, FORWARD-02, FORWARD-03, FORWARD-04, FORWARD-05, FORWARD-06, SCORE-02, SCORE-03, SCORE-05, TRIGGER-01, TRIGGER-02, TRIGGER-03]

duration: 38min
completed: 2026-03-19
---

# Phase 117 Plan 06: Forward-Looking Integration Wiring Summary

**Pipeline end-to-end wiring: forward statement extraction (EXTRACT) -> credibility/posture/quick-screen (BENCHMARK) -> 5 context builders (RENDER) -> template includes with trigger matrix at worksheet top**

## Performance

- **Duration:** 38 min
- **Started:** 2026-03-20T02:46:51Z
- **Completed:** 2026-03-20T03:24:51Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Forward statement extraction wired into EXTRACT stage as Step 9 (after adverse events)
- Full forward-looking intelligence computation wired into BENCHMARK stage as Step 9 (credibility, miss risk, monitoring triggers, posture, quick screen)
- 5 context builders injected into html_context_assembly.py with graceful degradation
- Quick Screen / Trigger Matrix placed in worksheet Zone 1.5 for immediate underwriter visibility
- forward_looking elevated to standalone manifest section with 11 groups (6 new Phase 117 + 5 existing facets)
- Scoring template enhanced with posture, zero verification, and watch items includes
- 23 integration tests covering wiring verification, empty state fallbacks, and template include ordering

## Task Commits

Each task was committed atomically:

1. **Task 1: Pipeline wiring (EXTRACT + BENCHMARK stages)** - `126431f4` (feat)
2. **Task 2: HTML context assembly + template includes + integration test** - `e39ed369` (feat)

## Files Created/Modified
- `src/do_uw/stages/extract/extract_market.py` - Added _run_forward_statements (Step 9)
- `src/do_uw/stages/benchmark/__init__.py` - Added _compute_forward_looking_intelligence (Step 9)
- `src/do_uw/stages/render/html_context_assembly.py` - Added 5 forward-looking context builder calls
- `src/do_uw/templates/html/worksheet.html.j2` - Added trigger_matrix include in Zone 1.5
- `src/do_uw/templates/html/sections/scoring.html.j2` - Added posture/zero/watch includes
- `src/do_uw/templates/html/sections/forward_looking.html.j2` - New parent section template
- `src/do_uw/brain/output_manifest.yaml` - Added forward_looking section + scoring enhancements
- `tests/stages/render/test_forward_integration.py` - 23 integration tests
- `tests/stages/render/test_manifest_rendering.py` - Updated section count (15->16) and order

## Decisions Made
- Elevated forward_looking from scoring sub-facets to its own top-level manifest section -- cleaner architecture, enables standalone rendering, and fixed several orphan template warnings
- Placed trigger matrix in Zone 1.5 (after CRF banner, before domain sections) per CONTEXT.md requirement for immediate underwriter visibility
- Used try/except per context builder (not a single wrapper) for maximum graceful degradation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Manifest section ordering test failures**
- **Found during:** Task 2 (manifest modification)
- **Issue:** Adding forward_looking section to manifest broke test_manifest_rendering.py (expected 15 sections, got 16)
- **Fix:** Updated _MANIFEST_SECTION_IDS list and section count from 15 to 16
- **Files modified:** tests/stages/render/test_manifest_rendering.py
- **Verification:** All 10 manifest rendering tests pass
- **Committed in:** e39ed369 (Task 2 commit)

**2. [Rule 3 - Blocking] Orphan template detection for forward_looking.html.j2**
- **Found during:** Task 2 (template creation)
- **Issue:** New parent template not declared in manifest, triggering orphan detection
- **Fix:** Created forward_looking as top-level manifest section with all facets moved from scoring
- **Files modified:** src/do_uw/brain/output_manifest.yaml
- **Verification:** forward_looking.html.j2 no longer in orphan list
- **Committed in:** e39ed369 (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for test green. Actually improved architecture by elevating forward_looking to proper manifest section.

## Issues Encountered
- 5 pre-existing test failures in test suite (brain_contract, contract_enforcement, template_facet_audit, template_purity, peril_scoring_html) -- all verified as pre-existing via git stash testing, not caused by Phase 117 changes
- Logged to deferred-items.md

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 117 (Forward-Looking Risk Framework) is COMPLETE -- all 6 plans executed
- Full pipeline runs end-to-end: EXTRACT -> ANALYZE -> BENCHMARK -> RENDER
- 23 new integration tests + 86 total Phase 117 tests pass
- Ready to proceed to next phase

---
*Phase: 117-forward-looking-risk-framework*
*Completed: 2026-03-19*
