---
phase: 142-quality-gates
plan: 01
subsystem: validation
tags: [consistency-checker, completeness-gate, qa, beautifulsoup, html-validation]

# Dependency graph
requires:
  - phase: 92-rendering-completeness
    provides: semantic_qa.py with financial value parsing and HTML validation patterns
provides:
  - ConsistencyChecker for cross-section fact contradiction detection
  - SectionCompletenessGate for N/A section suppression with banners
  - Integration into html_renderer pre-render pipeline
affects: [142-02-quality-gates, render-pipeline, qa-pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns: [report-only-default-gates, leaf-value-counting, known-section-whitelist]

key-files:
  created:
    - src/do_uw/validation/consistency_checker.py
    - src/do_uw/validation/section_completeness.py
    - tests/validation/test_consistency_checker.py
    - tests/validation/test_section_completeness.py
  modified:
    - src/do_uw/stages/render/html_renderer.py

key-decisions:
  - "Adapted plan to work without canonical_metrics.py (does not exist); extract canonical values from state dict directly, following semantic_qa.py patterns"
  - "Added section_keys whitelist to SectionCompletenessGate to prevent false positives on auxiliary context data (chart_images, spectrums, crf_bar, beta_report)"

patterns-established:
  - "Report-only gates: validation gates default to report_only=True (log warnings), promotable to blocking via flag"
  - "Known section whitelist: completeness gate only checks known worksheet section keys, not all dicts in context"

requirements-completed: [GATE-01, GATE-02, GATE-05]

# Metrics
duration: 8min
completed: 2026-03-28
---

# Phase 142 Plan 01: Cross-Section Consistency Checker and Section Completeness Gate Summary

**ConsistencyChecker detects fact contradictions across HTML sections; SectionCompletenessGate suppresses >50% N/A sections with banners pre-render**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-28T04:43:38Z
- **Completed:** 2026-03-28T04:51:51Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- ConsistencyChecker compares revenue/CEO/exchange/market_cap across all HTML sections with 1% financial tolerance and case-insensitive string matching
- SectionCompletenessGate recursively counts leaf N/A values and replaces broken sections with _insufficient_data banner dicts
- Both gates wired into the render pipeline: completeness runs pre-render in _render_html_template, consistency available as post-render check
- 18 passing tests covering inconsistency detection, tolerance, report-only modes, banner content, configurable thresholds, and nested dict handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Cross-section consistency checker with report-only mode** - `19497e73` (feat)
2. **Task 2: Section completeness gate with Insufficient Data banner** - `2fa56e25` (feat)

## Files Created/Modified
- `src/do_uw/validation/consistency_checker.py` - ConsistencyChecker, ConsistencyReport, ConsistencyError, check_cross_section_consistency
- `src/do_uw/validation/section_completeness.py` - SectionCompletenessGate, SectionCompleteness, check_section_completeness
- `tests/validation/test_consistency_checker.py` - 10 tests for consistency checker
- `tests/validation/test_section_completeness.py` - 8 tests for completeness gate
- `src/do_uw/stages/render/html_renderer.py` - Wired SectionCompletenessGate into _render_html_template

## Decisions Made
- canonical_metrics.py referenced in plan does not exist; adapted to extract canonical values from state dict directly, following the semantic_qa.py pattern already in the codebase
- Added _KNOWN_SECTION_KEYS whitelist to prevent the completeness gate from suppressing auxiliary context dicts (chart_images, spectrums, crf_bar, beta_report) that have N/A values in test mocks but are not user-facing sections

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Adapted canonical_metrics.py interface**
- **Found during:** Task 1 (ConsistencyChecker implementation)
- **Issue:** Plan references src/do_uw/stages/render/canonical_metrics.py with CanonicalMetrics model, but this file does not exist
- **Fix:** Built canonical value extraction from state dict directly, reusing _parse_financial_value pattern from semantic_qa.py. ConsistencyChecker takes dict[str, str] of canonical values instead of CanonicalMetrics model.
- **Files modified:** src/do_uw/validation/consistency_checker.py
- **Verification:** All 10 tests pass including state-dict convenience function test

**2. [Rule 1 - Bug] Added section_keys whitelist to completeness gate**
- **Found during:** Task 2 (render test regression check)
- **Issue:** SectionCompletenessGate checked ALL dict-valued context keys, causing it to suppress auxiliary data dicts (spectrums, crf_bar, beta_report) that have N/A values in test mocks
- **Fix:** Added _KNOWN_SECTION_KEYS whitelist and section_keys parameter to SectionCompletenessGate; html_renderer passes known section keys
- **Files modified:** src/do_uw/validation/section_completeness.py, src/do_uw/stages/render/html_renderer.py
- **Verification:** 0 new render test failures; all 18 validation tests pass

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both necessary for correctness. No scope creep.

## Issues Encountered
None.

## Known Stubs
None - all functionality is fully wired.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Consistency checker ready for post-render QA pipeline integration
- Section completeness gate active in html_renderer pre-render pipeline
- Ready for 142-02 plan (additional quality gates)

---
*Phase: 142-quality-gates*
*Completed: 2026-03-28*
