---
phase: 114-worksheet-restructure
plan: 01
subsystem: render
tags: [context-builders, html-renderer, heatmap, scorecard, epistemology, decision-record]

requires:
  - phase: 113-context-builder-rewrites
    provides: signal-backed context builders, _signal_consumer API
provides:
  - html_context_assembly.py with extracted build_html_context
  - 5 new context builders (scorecard, heatmap, crf_bar, epistemological_trace, decision)
  - html_renderer.py under 500 lines
affects: [114-02-templates, 114-03-styling]

tech-stack:
  added: []
  patterns: [context builder extraction, try/except graceful degradation for new builders]

key-files:
  created:
    - src/do_uw/stages/render/html_context_assembly.py
    - src/do_uw/stages/render/context_builders/scorecard_context.py
    - src/do_uw/stages/render/context_builders/heatmap_context.py
    - src/do_uw/stages/render/context_builders/crf_bar_context.py
    - src/do_uw/stages/render/context_builders/epistemological_trace.py
    - src/do_uw/stages/render/context_builders/decision_context.py
    - tests/stages/render/test_scorecard_context.py
    - tests/stages/render/test_heatmap_context.py
    - tests/stages/render/test_crf_bar_context.py
    - tests/stages/render/test_epistemological_trace.py
    - tests/stages/render/test_decision_context.py
  modified:
    - src/do_uw/stages/render/html_renderer.py

key-decisions:
  - "build_html_context re-exported from html_renderer.py for full backward compatibility"
  - "_risk_class and zone map moved to html_context_assembly since they are context-building helpers"
  - "Each new builder wrapped in try/except with graceful degradation defaults"

patterns-established:
  - "Context builder extraction: heavy context assembly in separate module, renderer keeps only template rendering + PDF generation"
  - "New context builders keyed under top-level context keys (scorecard, heatmap, crf_bar, etc.) to avoid namespace collision"

requirements-completed: [WS-01, WS-03, WS-07]

duration: 11min
completed: 2026-03-17
---

# Phase 114 Plan 01: Context Assembly Split and New Worksheet Builders Summary

**Split html_renderer.py (697 to 303 lines) and created 5 context builders for scorecard, heatmap, CRF bar, epistemological trace, and decision record**

## Performance

- **Duration:** 11 min
- **Started:** 2026-03-17T14:24:00Z
- **Completed:** 2026-03-17T14:35:00Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- html_renderer.py reduced from 697 to 303 lines (57% reduction) by extracting build_html_context to html_context_assembly.py
- 5 new context builders produce typed dicts for worksheet restructure components
- 24 new unit tests covering all builder behaviors, 811 total render tests passing
- Full backward compatibility maintained -- all imports from html_renderer still work

## Task Commits

Each task was committed atomically:

1. **Task 1: Split html_renderer.py** - `f53f6ad2` (refactor)
2. **Task 2 RED: Add failing tests** - `c4cc7ba8` (test)
3. **Task 2 GREEN: Implement 5 context builders** - `9e0cf864` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/html_context_assembly.py` - Extracted build_html_context + helpers (468 lines)
- `src/do_uw/stages/render/html_renderer.py` - Slim renderer with PDF/template functions only (303 lines)
- `src/do_uw/stages/render/context_builders/scorecard_context.py` - Tier, factors, top concerns, metrics strip (131 lines)
- `src/do_uw/stages/render/context_builders/heatmap_context.py` - H/A/E signal grid (71 lines)
- `src/do_uw/stages/render/context_builders/crf_bar_context.py` - CRF vetoes + red flags with section links (75 lines)
- `src/do_uw/stages/render/context_builders/epistemological_trace.py` - Full signal provenance table (101 lines)
- `src/do_uw/stages/render/context_builders/decision_context.py` - Tier distribution + posture fields (48 lines)
- `tests/stages/render/test_scorecard_context.py` - 5 tests
- `tests/stages/render/test_heatmap_context.py` - 5 tests
- `tests/stages/render/test_crf_bar_context.py` - 4 tests
- `tests/stages/render/test_epistemological_trace.py` - 6 tests
- `tests/stages/render/test_decision_context.py` - 4 tests

## Decisions Made
- build_html_context re-exported from html_renderer.py so all existing imports continue to work without changes
- _risk_class and _ZONE_STATUS_MAP moved to html_context_assembly since they are context-building helpers used by Jinja2 filters
- Each new builder wrapped in try/except with graceful degradation defaults in html_context_assembly.py
- New builder results stored under top-level context keys (context["scorecard"], context["heatmap"], etc.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added re-exports for _compute_coverage_stats and _group_signals_by_section**
- **Found during:** Task 1 (html_renderer split)
- **Issue:** test_html_renderer.py imports _compute_coverage_stats and _group_signals_by_section from html_renderer, but these lived in html_signals.py and were only incidentally available
- **Fix:** Added explicit re-export imports in html_renderer.py for backward compatibility
- **Files modified:** src/do_uw/stages/render/html_renderer.py
- **Verification:** All 782 existing tests pass
- **Committed in:** f53f6ad2 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential for backward compatibility. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_5layer_narrative.py (PydanticUserError for ScoringLensResult model_rebuild) -- not related to this plan's changes, excluded from test runs

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 context builders are wired into build_html_context and ready for template consumption
- Templates in 114-02 can consume context["scorecard"], context["heatmap"], context["crf_bar"], context["epistemological_trace"], and context["decision"]
- Each returns *_available flag for conditional rendering

---
*Phase: 114-worksheet-restructure*
*Completed: 2026-03-17*
