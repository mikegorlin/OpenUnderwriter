---
phase: 130-dual-voice-intelligence
plan: 01
subsystem: benchmark
tags: [pydantic, anthropic, llm, commentary, dual-voice, sca-theory]

# Dependency graph
requires:
  - phase: 129-bug-fixes-and-data-integrity
    provides: validate_narrative_amounts() cross-validation, narrative_generator.py patterns
provides:
  - SectionCommentary and PreComputedCommentary Pydantic models
  - commentary_generator.py with generate_all_commentary() for 8 sections
  - commentary_prompts.py with SCA litigation theory framework
  - BENCHMARK pipeline hook (_precompute_commentary after Step 8)
  - Cross-validation of commentary dollar amounts via validate_narrative_amounts()
affects: [130-02-PLAN, 130-03-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns: [dual-voice-commentary-generation, section-prefix-signal-mapping, commentary-cache-guard]

key-files:
  created:
    - src/do_uw/stages/benchmark/commentary_generator.py
    - src/do_uw/stages/benchmark/commentary_prompts.py
    - tests/models/test_commentary_model.py
    - tests/stages/benchmark/test_commentary_generator.py
  modified:
    - src/do_uw/models/density.py
    - src/do_uw/models/state.py
    - src/do_uw/stages/benchmark/__init__.py

key-decisions:
  - "Commentary generator is a separate module from narrative_generator (parallel path, not modification)"
  - "Cache guard pattern: skip commentary generation when pre_computed_commentary already exists on state"
  - "SECTION_PREFIX_MAP maps each section to signal prefixes for context enrichment"

patterns-established:
  - "Dual-voice parse: split LLM response on WHAT WAS SAID / UNDERWRITING COMMENTARY markers with graceful fallback"
  - "Commentary context enrichment: base extract_section_data + triggered signals + do_context refs + confidence"

requirements-completed: [VOICE-02, VOICE-03, VOICE-04]

# Metrics
duration: 12min
completed: 2026-03-23
---

# Phase 130 Plan 01: Commentary Engine Summary

**Dual-voice commentary generation engine with SectionCommentary/PreComputedCommentary models, 8-section LLM generation, SCA litigation theory prompts, and XBRL cross-validation**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-23T18:49:31Z
- **Completed:** 2026-03-23T19:01:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- SectionCommentary and PreComputedCommentary Pydantic models with JSON round-trip serialization
- commentary_generator.py: generate_all_commentary() making 8 per-section LLM calls with signal context enrichment
- commentary_prompts.py: full SCA litigation theory framework (10 plaintiff + 7 defense theories) in COMMENTARY_RULES
- BENCHMARK pipeline integration: _precompute_commentary() called as Step 8.5 with cache guard
- Cross-validation catches hallucinated dollar amounts >2x from known XBRL/state values
- 14 tests covering models, generation, parsing, fallback, and VOICE-04 hallucination detection

## Task Commits

Each task was committed atomically:

1. **Task 1: Pydantic models + commentary generator + prompts** - `9919f79e` (feat)
2. **Task 2: Hook commentary generation into BENCHMARK pipeline** - `7c6d52b3` (feat)

## Files Created/Modified
- `src/do_uw/models/density.py` - Added SectionCommentary and PreComputedCommentary models
- `src/do_uw/models/state.py` - Added pre_computed_commentary field to AnalysisResults
- `src/do_uw/stages/benchmark/commentary_generator.py` - Commentary generation engine (8 sections, LLM + cross-validation)
- `src/do_uw/stages/benchmark/commentary_prompts.py` - Dual-voice prompt builder with SCA theory framework
- `src/do_uw/stages/benchmark/__init__.py` - _precompute_commentary() hook at Step 8.5
- `tests/models/test_commentary_model.py` - 6 model serialization tests
- `tests/stages/benchmark/test_commentary_generator.py` - 8 generation/validation tests

## Decisions Made
- Commentary generator is a separate module (commentary_generator.py) parallel to narrative_generator.py, not a modification of it
- Cache guard checks `pre_computed_commentary is not None` to skip regeneration on re-render
- SECTION_PREFIX_MAP centralizes section-to-signal-prefix mapping for context enrichment
- LLM response parsed by splitting on WHAT WAS SAID / UNDERWRITING COMMENTARY markers with graceful half-split fallback

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None - all functions are fully implemented with real logic.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Commentary engine ready for Plans 02 (template integration) and 03 (executive summary overhaul)
- PreComputedCommentary cached on state.analysis, accessible by RENDER context builders
- 323 tests pass across benchmark + model suites (183 benchmark + 140 model)

---
*Phase: 130-dual-voice-intelligence*
*Completed: 2026-03-23*
