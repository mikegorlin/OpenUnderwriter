---
phase: 124-css-density-overhaul
plan: 02
subsystem: render
tags: [boilerplate, narrative-quality, regression-test, llm-prompts]

requires:
  - phase: 124-01
    provides: CSS density foundation with borderless tables and risk colors
provides:
  - 28 boilerplate detection patterns in BOILERPLATE_PATTERNS catalog
  - find_boilerplate_matches() utility for narrative scanning
  - strip_boilerplate() safety net in formatters.py
  - Anti-boilerplate LLM directives in all narrative prompts
affects: [render, benchmark, extract, brain-narratives]

tech-stack:
  added: []
  patterns: [boilerplate-detection-regex, anti-boilerplate-llm-directive]

key-files:
  created:
    - tests/stages/render/test_boilerplate_elimination.py
  modified:
    - src/do_uw/stages/render/formatters.py
    - src/do_uw/stages/benchmark/narrative_generator.py
    - src/do_uw/stages/benchmark/narrative_prompts.py
    - src/do_uw/stages/extract/dossier_extraction.py
    - src/do_uw/stages/render/sections/sect1_findings_neg.py
    - src/do_uw/templates/html/sections/market/stock_charts.html.j2
    - src/do_uw/templates/html/sections/scoring/ten_factor_scoring.html.j2
    - src/do_uw/brain/narratives/red_flags.yaml

key-decisions:
  - "strip_boilerplate() logs warnings but does not mutate text -- safety net not a filter"
  - "Source code scanner tests exclude pattern definitions and anti-boilerplate directives via skip markers"
  - "Brain YAML narratives updated alongside Python source -- boilerplate in YAML templates is equally harmful"

patterns-established:
  - "Boilerplate regression test: new narrative code must pass find_boilerplate_matches() scan"
  - "Anti-boilerplate LLM directive: every narrative prompt includes explicit forbidden phrase list"

requirements-completed: [FIX-03]

duration: 6min
completed: 2026-03-21
---

# Phase 124 Plan 02: Boilerplate Elimination Summary

**28 boilerplate detection patterns with regression tests, safety-net strip_boilerplate(), and anti-boilerplate LLM directives across all narrative generators**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-21T21:45:07Z
- **Completed:** 2026-03-21T21:51:07Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Cataloged 28 boilerplate patterns covering generic hedging, filler, and D&O-specific boilerplate
- Eliminated all boilerplate from sect1_findings_neg.py (2 occurrences: "warrants underwriting attention", "creates structural complexity that elevates D&O exposure")
- Added strip_boilerplate() safety net to formatters.py with 24 compiled regex patterns and warning logging
- Added anti-boilerplate directives to 4 LLM prompt locations (narrative_generator executive thesis, meeting prep, narrative_prompts COMMON_RULES, dossier_extraction emerging risks)
- Fixed boilerplate in 3 template/YAML files (stock_charts, ten_factor_scoring, red_flags)

## Task Commits

Each task was committed atomically:

1. **Task 1: Catalog boilerplate patterns and create regression test** - `996996f6` (test) + `b1d637a0` (feat) -- TDD RED then GREEN
2. **Task 2: Eliminate boilerplate from narrative generators and formatters** - `c9397190` (feat)

## Files Created/Modified
- `tests/stages/render/test_boilerplate_elimination.py` - 28 boilerplate patterns, find_boilerplate_matches(), source code scanner tests
- `src/do_uw/stages/render/formatters.py` - strip_boilerplate() safety net with warning logging
- `src/do_uw/stages/render/sections/sect1_findings_neg.py` - Replaced 2 boilerplate phrases with data-specific text
- `src/do_uw/stages/benchmark/narrative_generator.py` - Anti-boilerplate directives in executive thesis and meeting prep prompts
- `src/do_uw/stages/benchmark/narrative_prompts.py` - Anti-boilerplate directive in COMMON_RULES
- `src/do_uw/stages/extract/dossier_extraction.py` - Anti-boilerplate directive in emerging risk prompt
- `src/do_uw/templates/html/sections/market/stock_charts.html.j2` - Replaced "warrant further investigation" with 8-K filing review instruction
- `src/do_uw/templates/html/sections/scoring/ten_factor_scoring.html.j2` - Replaced "warrant individual attention" with signal detail reference
- `src/do_uw/brain/narratives/red_flags.yaml` - Replaced generic "warrant focused attention" with data-specific flag count reference

## Decisions Made
- strip_boilerplate() is a logging-only safety net, not a text mutator -- upstream generators must be fixed at source
- Source code scanner tests use skip markers to exclude pattern definitions and anti-boilerplate directives from false-positive detection
- Extended scope to templates and brain YAML (Deviation Rule 2) since they also emit boilerplate into rendered output

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Extended boilerplate elimination to templates and brain YAML**
- **Found during:** Task 2
- **Issue:** Plan listed only Python source files but templates and brain YAML also contained boilerplate phrases
- **Fix:** Updated 3 additional files: stock_charts.html.j2, ten_factor_scoring.html.j2, red_flags.yaml
- **Files modified:** See above
- **Verification:** Grep for boilerplate patterns returns 0 matches in all modified files
- **Committed in:** c9397190

---

**Total deviations:** 1 auto-fixed (1 missing critical)
**Impact on plan:** Necessary for completeness -- boilerplate in templates reaches rendered output the same as Python source. No scope creep.

## Issues Encountered
- Pre-existing test failures in test_section_renderer.py and test_5layer_narrative.py due to manifest schema validation error (render_as 'data_table' not permitted) -- unrelated to this plan, not caused by our changes

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Boilerplate regression tests in place to catch future regressions
- Anti-boilerplate LLM directives will improve narrative quality on next pipeline run
- Phase 124 is now fully complete (both plans done)

---
*Phase: 124-css-density-overhaul*
*Completed: 2026-03-21*
