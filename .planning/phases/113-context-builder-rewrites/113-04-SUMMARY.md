---
phase: 113-context-builder-rewrites
plan: 04
subsystem: render
tags: [context-builders, signal-results, refactor, module-split, hae-radar]

requires:
  - phase: 113-context-builder-rewrites
    provides: signal_results plumbing from Plan 01, evaluative split pattern from Plans 02-03
  - phase: 107-hae-scoring
    provides: ScoringLensResult with H/A/E composites on state.scoring.hae_result
  - phase: 104-signal-consumer-layer
    provides: _signal_consumer.py and _signal_fallback.py typed accessors
provides:
  - analysis.py + analysis_evaluative.py split (273 + 298 lines)
  - scoring.py + scoring_evaluative.py split (176 + 206 lines)
  - narrative.py + narrative_evaluative.py split (261 + 194 lines)
  - hae_context.py (51 lines) -- H/A/E radar chart data from ScoringLensResult
  - build_hae_context exported from __init__.py
  - All context builders under 300 lines (BUILD-07 fully satisfied for analysis/scoring/narrative)
affects: [114-template-rewrites]

tech-stack:
  added: []
  patterns: ["evaluative split: primary module re-exports from _evaluative.py companion", "hae_context reads composites dict from ScoringLensResult with getattr fallback for test mocks"]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/analysis_evaluative.py
    - src/do_uw/stages/render/context_builders/scoring_evaluative.py
    - src/do_uw/stages/render/context_builders/narrative_evaluative.py
    - src/do_uw/stages/render/context_builders/hae_context.py
  modified:
    - src/do_uw/stages/render/context_builders/analysis.py
    - src/do_uw/stages/render/context_builders/scoring.py
    - src/do_uw/stages/render/context_builders/narrative.py
    - src/do_uw/stages/render/context_builders/__init__.py
    - tests/stages/render/test_hae_context.py
    - tests/stages/render/test_builder_line_limits.py
    - tests/stages/render/test_signal_consumption.py

key-decisions:
  - "analysis_evaluative.py gets forensic composites, exec risk, NLP, temporal, peril map -- all state.analysis.* readers"
  - "scoring_evaluative.py gets AI risk, meeting questions, and allegation/tower/severity helper functions called by extract_scoring"
  - "narrative_evaluative.py gets condition checking (migrated from raw dict to typed API) and 5-layer architecture functions"
  - "hae_context reads ScoringLensResult.composites dict with getattr fallback for test mock compatibility"

patterns-established:
  - "Evaluative split pattern: all 4 rewritten builders (company, analysis, scoring, narrative) follow same structure -- primary module re-exports from _evaluative.py"

requirements-completed: [BUILD-06, BUILD-07, BUILD-08]

duration: 13min
completed: 2026-03-17
---

# Phase 113 Plan 04: Analysis/Scoring/Narrative Builder Split + H/A/E Context Summary

**Split analysis.py, scoring.py, narrative.py into 7 modules all under 300 lines with signal-backed evaluative content and H/A/E radar chart context builder**

## Performance

- **Duration:** 13 min
- **Started:** 2026-03-17T12:12:47Z
- **Completed:** 2026-03-17T12:25:23Z
- **Tasks:** 3
- **Files modified:** 11

## Accomplishments
- All 3 oversized builders split: analysis.py (583->273), scoring.py (492->176), narrative.py (580->261)
- 3 new evaluative modules created with signal consumer API integration
- hae_context.py provides H/A/E radar chart data from ScoringLensResult composites
- build_hae_context exported and xfail markers removed (4 tests now pass as real assertions)
- analysis.py, scoring.py, narrative.py all removed from EXCLUDED_FILES in line limits test
- 50 BUILD-07 verification tests pass (line limits + signal consumption + HAE context)

## Task Commits

1. **Task 1: Rewrite analysis.py + analysis_evaluative.py** - `88719d1` (feat)
2. **Task 2: Split scoring.py + create hae_context.py** - `1aaaacb` (feat)
3. **Task 3: Split narrative.py + narrative_evaluative.py** - `68ad80a` (feat)

## Files Created/Modified
- `analysis_evaluative.py` (298 lines) - forensic composites, exec risk, NLP, temporal, peril map with EXEC/DISC/NLP signal enrichment
- `scoring_evaluative.py` (206 lines) - AI risk, meeting questions, allegation/tower/severity helpers with signal consumer imports
- `narrative_evaluative.py` (194 lines) - condition checking with typed signal API, 5-layer architecture (verdict, thesis, evidence, deep context)
- `hae_context.py` (51 lines) - H/A/E radar chart data from ScoringLensResult
- `analysis.py` (273 lines) - classification, hazard profile, risk factors + re-exports
- `scoring.py` (176 lines) - extract_scoring with delegated evaluative helpers
- `narrative.py` (261 lines) - SCR, D&O implications, shared helpers
- `__init__.py` - added build_hae_context export

## Decisions Made
- analysis_evaluative.py gets all state.analysis.* readers (forensic, exec, NLP, temporal, peril) since they are evaluative
- scoring_evaluative.py splits extract_scoring helpers (allegation, tower, severity) as callable functions rather than inlining
- narrative_evaluative.py migrates raw signal_results dict access to typed safe_get_signals_by_prefix API
- hae_context reads composites dict from ScoringLensResult with getattr fallback for test mock compatibility

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Pre-existing PydanticUserError failures in test_narrative_context.py and test_bull_bear.py (model_rebuild) -- unrelated to this plan, documented in Plan 01

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All context builder modules under 300 lines (BUILD-07 fully satisfied)
- H/A/E radar chart context ready for template integration in Phase 114
- Signal consumption established across all evaluative modules
- Phase 113 complete -- 4 of 4 plans done

---
*Phase: 113-context-builder-rewrites*
*Completed: 2026-03-17*
