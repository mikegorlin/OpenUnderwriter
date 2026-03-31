---
phase: 35-display-presentation-clarity
plan: 03
subsystem: benchmark, models
tags: [llm, narrative-generation, anthropic, caching, density-tiered, fallback]

# Dependency graph
requires:
  - phase: 35-display-presentation-clarity
    provides: "DensityLevel enum, SectionDensity, PreComputedNarratives model (Plan 01); benchmark/narrative_helpers.py (Plan 02)"
provides:
  - "LLM narrative generation in BENCHMARK stage via generate_all_narratives()"
  - "Density-tiered narrative length: CLEAN 2-3, ELEVATED 4-5, CRITICAL 6-8 sentences"
  - "In-memory SHA-256 cache for narrative deduplication within a run"
  - "Fallback to rule-based narratives when anthropic unavailable"
  - "AI Assessment labeling on all LLM-generated content per DATA-14"
  - "Meeting prep questions tied to specific findings"
  - "Executive thesis with tiered length (CLEAN 3-4, ELEVATED/CRITICAL 6-8 sentences)"
affects: [35-04, 35-05, 35-06, 35-07, render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "LLM narrative generation with density-tiered max_tokens (400/600/800)"
    - "In-memory per-run SHA-256 cache for LLM output deduplication"
    - "Lazy import anthropic inside functions matching LLMExtractor pattern"
    - "Fallback to existing rule-based narratives on ImportError"
    - "Extracted enrichments into benchmark_enrichments.py for 500-line compliance"

key-files:
  created:
    - src/do_uw/stages/benchmark/narrative_generator.py
    - src/do_uw/stages/benchmark/narrative_data.py
    - src/do_uw/stages/benchmark/benchmark_enrichments.py
    - tests/stages/benchmark/test_narrative_generator.py
  modified:
    - src/do_uw/stages/benchmark/__init__.py

key-decisions:
  - "Split narrative_generator.py (451L) + narrative_data.py (292L) for 500-line compliance"
  - "Extracted enrich_market_intelligence and enrich_actuarial_pricing to benchmark_enrichments.py to make room for narrative integration in __init__.py"
  - "AI Assessment prefix on all LLM narratives per DATA-14; rule-based fallbacks get no prefix"
  - "claude-sonnet-4-20250514 model for cost-effective narrative generation per research guidance"
  - "In-memory per-run cache only (not persisted) per research recommendation"
  - "Meeting prep questions parsed from JSON array with newline-split fallback"

patterns-established:
  - "Density-tiered LLM prompting: section_data + density -> length-controlled narrative"
  - "Section data extraction: _extract_section_data pulls primitive-typed dicts from typed state"
  - "generate_all_narratives as single entry point for BenchmarkStage with per-section try/except"

requirements-completed: [OUT-03, DATA-14]

# Metrics
duration: 10min
completed: 2026-02-21
---

# Phase 35 Plan 03: LLM Narrative Generation Summary

**LLM-powered narrative generation in BENCHMARK with density-tiered length control (CLEAN/ELEVATED/CRITICAL), SHA-256 caching, fallback to rule-based narratives, and AI Assessment labeling**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-21T14:56:24Z
- **Completed:** 2026-02-21T15:06:35Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Created narrative_generator.py with generate_section_narrative, generate_executive_thesis, and generate_meeting_prep_questions -- all with density-tiered max_tokens (400/600/800) and in-memory SHA-256 caching
- Created narrative_data.py with section data extraction helpers pulling primitive-typed dicts from AnalysisState for LLM prompting
- Integrated generate_all_narratives into BenchmarkStage._precompute_narratives with non-breaking try/except
- Extracted enrich_market_intelligence and enrich_actuarial_pricing into benchmark_enrichments.py to bring __init__.py from 499 to 358 lines
- 27 new tests covering cache determinism, density tiers, fallback, partial failure, structure validation

## Task Commits

Each task was committed atomically:

1. **Task 1: Create LLM narrative generator with caching** - `a120ae4` (feat)
2. **Task 2: Integrate narrative generator into BenchmarkStage** - `d75fbad` (feat)

## Files Created/Modified
- `src/do_uw/stages/benchmark/narrative_generator.py` - LLM narrative generation with caching, density-tiered length, fallback (451 lines)
- `src/do_uw/stages/benchmark/narrative_data.py` - Section data extraction from AnalysisState for prompts (292 lines)
- `src/do_uw/stages/benchmark/benchmark_enrichments.py` - Extracted market intelligence and actuarial pricing enrichments (237 lines)
- `tests/stages/benchmark/test_narrative_generator.py` - 27 tests across 7 test classes
- `src/do_uw/stages/benchmark/__init__.py` - Integrated generate_all_narratives, refactored to delegate enrichments (358 lines)

## Decisions Made
- Split narrative_generator.py into narrative_generator.py (451L) + narrative_data.py (292L) because original 636-line file exceeded 500-line limit
- Extracted enrich_market_intelligence and enrich_actuarial_pricing into benchmark_enrichments.py because adding narrative integration would push __init__.py past 500 lines (was 499)
- Used claude-sonnet-4-20250514 (not opus) per research cost guidance -- sufficient quality at lower cost
- In-memory per-run cache only (not persisted to DuckDB) per research recommendation -- LLM outputs are non-deterministic so cross-run caching adds complexity without clear benefit
- Meeting prep questions use JSON array parsing with newline-split fallback for robustness against LLM formatting variations
- All LLM narratives prefixed with "AI Assessment: " per DATA-14 requirement; rule-based fallback narratives explicitly omit this prefix

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Split narrative_generator.py for 500-line compliance**
- **Found during:** Task 1 (narrative generator creation)
- **Issue:** Original narrative_generator.py was 636 lines, exceeding 500-line project limit
- **Fix:** Extracted _extract_section_data, _extract_state_summary, _extract_findings into narrative_data.py (292 lines)
- **Files modified:** narrative_generator.py, narrative_data.py
- **Verification:** Both files under 500 lines, all 27 tests pass
- **Committed in:** a120ae4

**2. [Rule 3 - Blocking] Extracted enrichment methods from __init__.py**
- **Found during:** Task 2 (BenchmarkStage integration)
- **Issue:** __init__.py was 499 lines; adding narrative integration would exceed 500
- **Fix:** Extracted _enrich_market_intelligence and _enrich_actuarial_pricing to benchmark_enrichments.py with public API
- **Files modified:** __init__.py, benchmark_enrichments.py
- **Verification:** __init__.py at 358 lines, all 82 benchmark tests pass
- **Committed in:** d75fbad

---

**Total deviations:** 2 auto-fixed (2 blocking -- 500-line compliance)
**Impact on plan:** Both splits were necessary to comply with project 500-line limit. No scope creep. All functionality preserved.

## Issues Encountered
None -- all tests passed on first run after each task.

## User Setup Required
None -- anthropic is already a project dependency. Narrative generation falls back gracefully to rule-based when ANTHROPIC_API_KEY is not set.

## Next Phase Readiness
- PreComputedNarratives populated on state.analysis after BENCHMARK stage runs
- RENDER can read narratives directly from state.analysis.pre_computed_narratives
- Plan 04+ can use density-tiered narratives for conditional HTML/PDF rendering
- Fallback ensures pipeline never breaks when LLM is unavailable

## Self-Check: PASSED

All 5 created/modified files verified on disk. Both task commits (a120ae4, d75fbad) verified in git log. 82 benchmark tests pass, 207 targeted tests (benchmark + render + section assessments) pass.

---
*Phase: 35-display-presentation-clarity*
*Completed: 2026-02-21*
