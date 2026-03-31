---
phase: 65-narrative-depth
plan: "02"
subsystem: render
tags: [jinja2, css, narrative, bull-bear, confidence-verbs, context-builders]

# Dependency graph
requires:
  - phase: 65-narrative-depth/65-01
    provides: "5-layer narrative architecture, section_narratives context, narrative macros"
provides:
  - "Bull/bear case framing in executive summary and scoring sections"
  - "Confidence-calibrated verb mapping (HIGH=confirms, MEDIUM=indicates, LOW=suggests)"
  - "extract_bull_bear_cases() context builder for template consumption"
  - "calibrate_verb() and derive_section_confidence() for thesis generation"
  - "bull_bear_framing Jinja2 macro for two-column risk framing"
affects: [render, templates, html-output, pdf-output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Private helper module pattern (_bull_bear.py) for context builder extraction"
    - "Confidence tier -> verb mapping driven by source data, not density levels"
    - "Jinja2 dict field named 'entries' to avoid collision with dict.items() method"

key-files:
  created:
    - src/do_uw/stages/render/context_builders/_bull_bear.py
    - tests/stages/render/test_bull_bear.py
  modified:
    - src/do_uw/stages/render/context_builders/__init__.py
    - src/do_uw/stages/render/context_builders/narrative.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/components/narratives.html.j2
    - src/do_uw/templates/html/sections/executive.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/components.css

key-decisions:
  - "Renamed 'items' to 'entries' in bull/bear data dicts to avoid Jinja2 dict.items() collision"
  - "Confidence verb selection driven by signal_results source confidence tiers (mode of section signals), not density levels"
  - "Lazy import of calibrate_verb/derive_section_confidence inside _build_thesis to avoid circular imports"

patterns-established:
  - "Bull/bear dict uses 'entries' key (not 'items') for Jinja2 compatibility"
  - "Context builder returns None for bull/bear case when no items available (template guards with {% if data.bull_case %})"

requirements-completed: [NARR-02, NARR-03]

# Metrics
duration: 9min
completed: 2026-03-03
---

# Phase 65 Plan 02: Bull/Bear Framing + Confidence-Calibrated Language Summary

**Bull/bear case framing in executive/scoring sections with confidence-calibrated verbs (HIGH=confirms, MEDIUM=indicates, LOW=suggests) driven by source data tiers**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-03T18:52:08Z
- **Completed:** 2026-03-03T19:01:27Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- Created _bull_bear.py context builder (199 lines) with confidence verb mapping and bull/bear case extraction
- Added bull_bear_framing Jinja2 macro with two-column green/red grid layout in executive and scoring templates
- Integrated confidence-calibrated verbs into thesis generation (narrative.py _build_thesis() now uses calibrate_verb())
- 24 new tests all passing; 471 render tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Bull/Bear context builder + confidence verb mapping** - `1eb0078` (feat)
2. **Task 2: Bull/Bear framing macro + template integration + CSS + tests** - `43fd5e9` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/_bull_bear.py` - Bull/bear extraction + confidence verb mapping (199 lines)
- `src/do_uw/stages/render/context_builders/__init__.py` - Added extract_bull_bear_cases to exports
- `src/do_uw/stages/render/context_builders/narrative.py` - Integrated calibrate_verb into _build_thesis()
- `src/do_uw/stages/render/html_renderer.py` - Wired bull_bear_data into build_html_context()
- `src/do_uw/templates/html/components/narratives.html.j2` - Added bull_bear_framing macro
- `src/do_uw/templates/html/sections/executive.html.j2` - Added bull/bear framing call
- `src/do_uw/templates/html/sections/scoring.html.j2` - Added bull/bear framing call
- `src/do_uw/templates/html/base.html.j2` - Added bull_bear_framing to macro imports
- `src/do_uw/templates/html/components.css` - Added bull/bear grid CSS (8 rules)
- `tests/stages/render/test_bull_bear.py` - 24 tests covering verbs, extraction, and templates

## Decisions Made
- **Renamed 'items' to 'entries':** Jinja2 treats `data.bull_case.items` as the dict `.items()` method. Using `entries` key avoids this collision while keeping the template readable.
- **Confidence from signal_results:** derive_section_confidence() counts signal result confidence annotations per section and returns the mode (most common) tier. This ensures verb selection is driven by actual source data quality, not density levels.
- **Lazy imports in _build_thesis:** calibrate_verb and derive_section_confidence are imported inside the function to avoid circular imports between narrative.py and _bull_bear.py.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Jinja2 'items' key collision with dict.items()**
- **Found during:** Task 2 (Template macro testing)
- **Issue:** `data.bull_case.items` in Jinja2 resolves to the built-in dict method, not the dict value. Test failed with "builtin_function_or_method is not iterable."
- **Fix:** Renamed all occurrences of `"items"` key to `"entries"` in _bull_bear.py output dicts and narratives.html.j2 macro
- **Files modified:** _bull_bear.py, narratives.html.j2, test_bull_bear.py
- **Verification:** All 24 tests pass including template rendering tests
- **Committed in:** 43fd5e9 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Essential fix for Jinja2 compatibility. No scope creep.

## Issues Encountered
- Pre-existing test failures in tests/brain/test_brain_framework.py (missing module) and tests/brain/test_brain_enrich.py (count mismatch 98 vs 99) are not related to this plan. Logged as pre-existing, not addressed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- NARR-02 and NARR-03 gaps from 65-VERIFICATION.md are now closed
- Bull/bear framing and confidence-calibrated language ready for visual verification in HTML output
- All file limits respected: narrative.py (467), _bull_bear.py (199), components.css (500)
- Ready for Phase 65-03 or final verification pass

## Self-Check: PASSED

- FOUND: src/do_uw/stages/render/context_builders/_bull_bear.py
- FOUND: tests/stages/render/test_bull_bear.py
- FOUND: .planning/phases/65-narrative-depth/65-02-SUMMARY.md
- FOUND: commit 1eb0078
- FOUND: commit 43fd5e9

---
*Phase: 65-narrative-depth*
*Plan: 02*
*Completed: 2026-03-03*
