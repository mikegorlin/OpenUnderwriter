---
phase: 23-end-to-end-output-quality
plan: 04
subsystem: render
tags: [blind-spot-detection, data-quality, web-search, serper, executive-summary]

# Dependency graph
requires:
  - phase: 02-company-resolution-data-acquisition
    provides: "WebSearchClient with pluggable search_fn, blind_spot_results in AcquiredData"
  - phase: 08-worksheet-rendering
    provides: "sect1_executive.py executive summary renderer"
provides:
  - "Data quality notice in executive summary when blind spot detection is skipped"
  - "is_search_configured property on WebSearchClient for search availability tracking"
  - "search_configured flag propagated to blind_spot_results in state"
  - "CLI WARNING log when SERPER_API_KEY is missing"
affects: [23-end-to-end-output-quality, render, acquire]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Data quality notice pattern: render warning when upstream data acquisition is incomplete"
    - "search_configured flag in blind_spot_results dict for downstream render awareness"

key-files:
  created: []
  modified:
    - src/do_uw/stages/acquire/clients/web_search.py
    - src/do_uw/stages/acquire/orchestrator.py
    - src/do_uw/stages/render/sections/sect1_executive.py
    - src/do_uw/cli.py
    - tests/test_render_sections_1_4.py

key-decisions:
  - "Data quality notice placed at top of executive summary (after heading, before thesis) for maximum visibility"
  - "Notice renders in dark red bold text (RGBColor 0xB71C1C) to ensure it cannot be missed"
  - "is_search_configured checks function identity (not _default_search_fn) rather than None check for accuracy"
  - "search_configured flag stored in blind_spot_results dict (existing dict[str, Any] field) rather than new model field"
  - "Checkpoint for SERPER_API_KEY configuration deferred to user"

patterns-established:
  - "Data quality notice: render upstream acquisition status in downstream output sections"
  - "Search status propagation: orchestrator writes flags, renderer reads flags from state"

# Metrics
duration: 2m 25s
completed: 2026-02-11
---

# Phase 23 Plan 04: Blind Spot Detection Visibility Summary

**Red-text data quality notice in executive summary when web search API is not configured, preventing silent incomplete risk assessments**

## Performance

- **Duration:** 2m 25s
- **Started:** 2026-02-11T22:34:48Z
- **Completed:** 2026-02-11T22:37:13Z
- **Tasks:** 1
- **Files modified:** 5

## Accomplishments
- `is_search_configured` property on WebSearchClient tracks whether real search function was injected vs no-op default
- Orchestrator propagates `search_configured` and `search_budget_used` flags to `blind_spot_results` in state
- Executive summary renders prominent "Data Quality Notice" in dark red bold text when blind spot detection was not performed
- CLI logs a visible WARNING about missing SERPER_API_KEY (upgraded from yellow info to bold red + logger warning)
- 2 new tests verify notice appears when unconfigured and is hidden when configured

## Task Commits

Each task was committed atomically:

1. **Task 1: Add blind spot detection status to state and render notice** - `2c25880` (feat)

**Plan metadata:** pending

## Files Created/Modified
- `src/do_uw/stages/acquire/clients/web_search.py` - Added `is_search_configured` property to WebSearchClient
- `src/do_uw/stages/acquire/orchestrator.py` - Propagate search_configured and search_budget_used flags to blind_spot_results
- `src/do_uw/stages/render/sections/sect1_executive.py` - Added `_render_data_quality_notice()` function called from render_section_1
- `src/do_uw/cli.py` - CLI logs WARNING about missing SERPER_API_KEY, upgraded console output to bold red
- `tests/test_render_sections_1_4.py` - 2 new tests for data quality notice visibility

## Decisions Made
- Data quality notice placed at TOP of executive summary (after heading, before thesis) -- most visible position for the reader
- Notice text explicitly names what may be missing: short seller reports, state AG actions, SCAs not in filings, news, social media
- Used function identity check (`is not _default_search_fn`) rather than None check since search_fn can be non-None but still no-op
- Stored flags in existing `blind_spot_results` dict rather than adding new Pydantic model fields (backward compatible)
- SERPER_API_KEY configuration checkpoint deferred per execution instructions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Handle None acquired_data in data quality notice**
- **Found during:** Task 1
- **Issue:** `_render_data_quality_notice` accessed `state.acquired_data.blind_spot_results` without checking if `acquired_data` is None (happens with empty AnalysisState in tests)
- **Fix:** Added explicit None check for `state.acquired_data` before accessing blind_spot_results
- **Files modified:** src/do_uw/stages/render/sections/sect1_executive.py
- **Verification:** test_render_with_none_executive_summary passes
- **Committed in:** 2c25880 (Task 1 commit)

**2. [Rule 1 - Bug] Removed unnecessary isinstance check for pyright strict**
- **Found during:** Task 1
- **Issue:** pyright strict flagged `isinstance(blind_spots, dict)` as unnecessary since the type is already `dict[str, Any]`
- **Fix:** Removed the isinstance guard, accessing dict directly
- **Files modified:** src/do_uw/stages/render/sections/sect1_executive.py
- **Verification:** pyright reports 0 errors
- **Committed in:** 2c25880 (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Both fixes necessary for correctness and strict type checking. No scope creep.

## Issues Encountered
None

## User Setup Required
**Optional:** To enable full blind spot detection, set SERPER_API_KEY:
- Sign up at https://serper.dev/ (free tier: 2,500 queries)
- `export SERPER_API_KEY=your_key_here`
- Re-run pipeline to verify blind spot detection finds results
- The data quality notice will automatically be suppressed when search is configured

## Next Phase Readiness
- Data quality notice system is complete and tested
- Pipeline never silently claims completeness when search was not performed
- Ready for remaining Phase 23 plans (scoring calibration, rendering improvements)

---
*Phase: 23-end-to-end-output-quality*
*Completed: 2026-02-11*
