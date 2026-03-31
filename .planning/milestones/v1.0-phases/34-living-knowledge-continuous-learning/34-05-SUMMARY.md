---
phase: 34-living-knowledge-continuous-learning
plan: 05
subsystem: knowledge, render
tags: [discovery, calibration, blind-spot, ingestion, worksheet, duckdb]

# Dependency graph
requires:
  - phase: 34-02
    provides: LLM ingestion pipeline (extract_document_intelligence, store_proposals)
  - phase: 34-03
    provides: Underwriter feedback system (brain_feedback table, feedback CLI)
provides:
  - Automatic blind spot discovery hook in ACQUIRE stage
  - Calibration Notes worksheet section showing system intelligence status
  - Integration tests for discovery + calibration rendering
affects: [render, acquire, knowledge]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Non-blocking discovery hook pattern (try/except in orchestrator)"
    - "Lazy import for brain DuckDB in renderers (graceful degradation)"
    - "Keyword-based relevance scoring for search result filtering"

key-files:
  created:
    - src/do_uw/knowledge/discovery.py
    - src/do_uw/stages/render/md_renderer_helpers_calibration.py
    - src/do_uw/stages/render/sections/sect_calibration.py
    - tests/knowledge/test_discovery_integration.py
  modified:
    - src/do_uw/stages/acquire/orchestrator.py
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/stages/render/word_renderer.py
    - src/do_uw/templates/markdown/worksheet.md.j2

key-decisions:
  - "Discovery hook wired into orchestrator (not web_search.py) because orchestrator controls blind_spot_results lifecycle"
  - "Calibration notes in separate file md_renderer_helpers_calibration.py (md_renderer_helpers_ext.py at 453 lines would exceed 500-line limit)"
  - "sect_calibration.py renders markdown-to-Word by parsing simple markdown syntax (headings, bullets, tables)"

patterns-established:
  - "Non-blocking discovery: try/except wrapping ensures pipeline never breaks from discovery failures"
  - "Calibration notes section renders only when data exists (empty string = section omitted)"

requirements-completed: [ARCH-09, ARCH-10, SECT7-11]

# Metrics
duration: 8min
completed: 2026-02-21
---

# Phase 34 Plan 05: Automatic Discovery & Calibration Notes Summary

**Blind spot discovery hook auto-feeds high-relevance search results through LLM ingestion pipeline; Calibration Notes section in worksheet shows system intelligence status, recent changes, and pending feedback**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-21T05:23:50Z
- **Completed:** 2026-02-21T05:31:59Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- ACQUIRE stage automatically feeds high-relevance blind spot results through LLM ingestion for proposal generation
- Calibration Notes worksheet section renders system intelligence status (active/incubating checks, pending feedback, recent changes, discovery findings)
- 19 tests covering relevance scoring, blind spot processing, failure handling, calibration notes rendering, and hook integration

## Task Commits

Each task was committed atomically:

1. **Task 1: Build discovery hook and wire into ACQUIRE stage** - `3a914c1` (feat)
2. **Task 2: Add Calibration Notes worksheet section and tests** - `d9e20e0` (feat)

## Files Created/Modified
- `src/do_uw/knowledge/discovery.py` - Blind spot discovery hook with keyword relevance scoring, URL fetch, LLM extraction, proposal storage
- `src/do_uw/stages/render/md_renderer_helpers_calibration.py` - Calibration notes section renderer querying brain DuckDB
- `src/do_uw/stages/render/sections/sect_calibration.py` - Word document renderer for calibration notes (markdown-to-docx)
- `tests/knowledge/test_discovery_integration.py` - 19 tests for discovery and calibration notes
- `src/do_uw/stages/acquire/orchestrator.py` - Added _run_discovery_hook after blind spot sweeps
- `src/do_uw/stages/render/md_renderer.py` - Added calibration_notes to build_template_context
- `src/do_uw/stages/render/word_renderer.py` - Registered calibration section before meeting prep
- `src/do_uw/templates/markdown/worksheet.md.j2` - Added calibration_notes template block

## Decisions Made
- Discovery hook placed in orchestrator.py (not web_search.py) because the orchestrator controls the blind_spot_results dict lifecycle and has access to both pre- and post-structured sweep results
- Created md_renderer_helpers_calibration.py as a new file rather than extending md_renderer_helpers_ext.py which was at 453 lines (would exceed 500-line limit with the new section)
- Word renderer for calibration notes parses simple markdown syntax rather than duplicating the rendering logic, keeping the section consistent across Markdown/Word/PDF outputs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Discovery hook location change**
- **Found during:** Task 1
- **Issue:** Plan specified wiring hook in web_search.py, but web_search.py's blind_spot_sweep returns results to the orchestrator which populates blind_spot_results. The hook needs access to the full blind_spot_results dict.
- **Fix:** Wired hook in orchestrator.py as _run_discovery_hook function, called after all blind spot sweeps complete
- **Files modified:** src/do_uw/stages/acquire/orchestrator.py
- **Verification:** Tests pass, hook correctly accesses pre_structured and post_structured results

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Hook placement in orchestrator is architecturally correct -- web_search.py doesn't have access to the blind_spot_results dict. No scope creep.

## Issues Encountered
- Mock patching for lazy imports required patching at source module (do_uw.brain.brain_schema) rather than consumer module since functions are imported inside try blocks

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 34 Plan 05 is the final plan in Phase 34
- All 5 plans complete: brain feedback schema, LLM ingestion pipeline, underwriter feedback system, calibration workflow, automatic discovery + calibration notes
- The living knowledge loop is complete: discovery feeds proposals, underwriters provide feedback, calibration changes flow through, and the worksheet transparently shows what changed

## Self-Check: PASSED

All 5 created files exist. Both task commits (3a914c1, d9e20e0) verified in git log. 19/19 tests pass. Pyright clean on all new files.

---
*Phase: 34-living-knowledge-continuous-learning*
*Completed: 2026-02-21*
