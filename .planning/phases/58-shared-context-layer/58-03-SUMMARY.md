---
phase: 58-shared-context-layer
plan: 03
subsystem: render
tags: [context-builders, shim, refactor, backward-compat, import-rewiring]

# Dependency graph
requires:
  - phase: 58-01
    provides: context_builders/ package with company, financials, market modules
  - phase: 58-02
    provides: context_builders/ governance, litigation, scoring, analysis, calibration modules
provides:
  - 9 thin re-export shims replacing original md_renderer_helpers_*.py files
  - All primary consumers rewired to import from context_builders/
  - Backward compatibility preserved for test and external imports
affects: [60-word-adapter, 61-surface-hidden-data, 62-facet-completion]

# Tech tracking
tech-stack:
  added: []
  patterns: [shim-reexport-pattern, single-import-block, format-agnostic-context]

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/md_renderer_helpers_narrative.py
    - src/do_uw/stages/render/md_renderer_helpers_financial_income.py
    - src/do_uw/stages/render/md_renderer_helpers_financial_balance.py
    - src/do_uw/stages/render/md_renderer_helpers_tables.py
    - src/do_uw/stages/render/md_renderer_helpers_governance.py
    - src/do_uw/stages/render/md_renderer_helpers_ext.py
    - src/do_uw/stages/render/md_renderer_helpers_scoring.py
    - src/do_uw/stages/render/md_renderer_helpers_analysis.py
    - src/do_uw/stages/render/md_renderer_helpers_calibration.py
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/stages/render/pdf_renderer.py
    - src/do_uw/stages/render/sections/sect2_company_hazard.py
    - src/do_uw/stages/render/sections/sect_calibration.py

key-decisions:
  - "Added _score_to_exposure to analysis shim (sect2_company_hazard.py imports it)"
  - "Test files NOT rewired -- backward compat through shims is sufficient for CTX-03"
  - "Private function imports (like _score_to_exposure, _load_crf_conditions) preserved in shims"

patterns-established:
  - "Shim re-export pattern: old module becomes <30 line file re-exporting from context_builders/"
  - "Single import block: md_renderer.py uses one import from context_builders instead of 6 separate helper imports"

requirements-completed: [CTX-03, CTX-04, CTX-05]

# Metrics
duration: 11min
completed: 2026-03-02
---

# Phase 58 Plan 03: Shim Conversion & Consumer Rewiring Summary

**9 md_renderer_helpers_*.py files converted to thin re-export shims (max 27 lines), all consumers rewired to context_builders/, SNA HTML output byte-identical**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-02T18:00:35Z
- **Completed:** 2026-03-02T18:11:57Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments

- Converted all 9 md_renderer_helpers_*.py files from 3,057 lines of implementation to 65 lines of re-export shims
- Rewired 5 primary consumers (md_renderer, html_renderer, pdf_renderer, sect2_company_hazard, sect_calibration) to import directly from context_builders/
- Verified SNA HTML output is byte-identical before and after the rewiring
- All 319 render tests pass; 4,288 total tests pass (19 pre-existing failures unrelated to changes)

## Task Commits

Each task was committed atomically:

1. **Task 1: Convert all 9 md_renderer_helpers_*.py to thin re-export shims** - `afa6d9c` (refactor)
2. **Task 2: Rewire consumers to import from context_builders/ and verify SNA output** - `12048d7` (feat)

**Plan metadata:** [pending] (docs: complete plan)

## Files Created/Modified

- `src/do_uw/stages/render/md_renderer_helpers_narrative.py` - Shim re-exporting extract_company, extract_exec_summary
- `src/do_uw/stages/render/md_renderer_helpers_financial_income.py` - Shim re-exporting extract_financials, find_line_item_value
- `src/do_uw/stages/render/md_renderer_helpers_financial_balance.py` - Shim re-exporting _build_statement_rows, _format_line_value
- `src/do_uw/stages/render/md_renderer_helpers_tables.py` - Shim re-exporting dim_display_name, extract_market
- `src/do_uw/stages/render/md_renderer_helpers_governance.py` - Shim re-exporting extract_governance
- `src/do_uw/stages/render/md_renderer_helpers_ext.py` - Shim re-exporting extract_governance, extract_litigation
- `src/do_uw/stages/render/md_renderer_helpers_scoring.py` - Shim re-exporting extract_scoring, extract_ai_risk, extract_meeting_questions, _load_crf_conditions
- `src/do_uw/stages/render/md_renderer_helpers_analysis.py` - Shim re-exporting 8 extract_* functions + _score_to_exposure
- `src/do_uw/stages/render/md_renderer_helpers_calibration.py` - Shim re-exporting render_calibration_notes
- `src/do_uw/stages/render/md_renderer.py` - Single import block from context_builders, updated docstring
- `src/do_uw/stages/render/html_renderer.py` - dim_display_name from context_builders
- `src/do_uw/stages/render/pdf_renderer.py` - dim_display_name from context_builders
- `src/do_uw/stages/render/sections/sect2_company_hazard.py` - _score_to_exposure from context_builders.analysis
- `src/do_uw/stages/render/sections/sect_calibration.py` - render_calibration_notes from context_builders

## Decisions Made

- **Added _score_to_exposure to analysis shim:** The plan specified `extract_classification` and `extract_hazard_profile` for sect2_company_hazard.py, but the actual import was `_score_to_exposure` (a private function). Added it to the analysis shim for backward compat and rewired the consumer to context_builders.analysis directly.
- **Test files NOT rewired:** Per plan guidance, test files continue importing through the shims. This is sufficient for CTX-03 (which requires shims be <30 lines, not that all consumers switch). Rewiring tests can happen in a later cleanup.
- **Private function re-exports preserved:** `_load_crf_conditions` (scoring), `_build_statement_rows`/`_format_line_value` (balance), and `_score_to_exposure` (analysis) are all private but imported by consumers -- shims preserve these imports.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added _score_to_exposure to analysis shim**
- **Found during:** Task 2 (consumer rewiring)
- **Issue:** Plan listed `extract_classification` and `extract_hazard_profile` as the imports from sect2_company_hazard.py, but actual import was `_score_to_exposure` (private function)
- **Fix:** Added `_score_to_exposure` to the analysis shim's re-exports, and rewired sect2_company_hazard.py to import from context_builders.analysis directly
- **Files modified:** md_renderer_helpers_analysis.py, sections/sect2_company_hazard.py
- **Verification:** Full render test suite passes (319/319)
- **Committed in:** 12048d7 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Minor -- plan had incorrect interface spec for one file. Auto-fixed with correct import. No scope creep.

## Issues Encountered

- Pre-existing test failures (19 tests) related to brain data count mismatches (99 vs 98 MANAGEMENT_DISPLAY checks) and deleted facet_schema module. These are unrelated to the Phase 58 changes and were confirmed to fail on the pre-change codebase as well.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Phase 58 complete:** context_builders/ is the canonical location for all extract_* functions. Old helpers are thin shims.
- **Phase 59 (HTML Visual Polish):** Can proceed independently -- no dependency on Phase 58.
- **Phase 60 (Word Adapter):** Ready -- context_builders/ provides format-agnostic context that Word renderer can consume.
- **Phases 61-62:** Ready -- shared context layer is fully established.

## Self-Check: PASSED

All 15 files verified present. Both commit hashes (afa6d9c, 12048d7) verified in git log.

---
*Phase: 58-shared-context-layer*
*Completed: 2026-03-02*
