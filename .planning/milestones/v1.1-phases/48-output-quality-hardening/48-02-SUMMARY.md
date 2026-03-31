---
phase: 48-output-quality-hardening
plan: "02"
subsystem: render
tags: [check_helpers, html_checks, html_renderer, bool_coercion, source_column, qa_audit]

# Dependency graph
requires:
  - phase: 48-01
    provides: "Wave 0 RED tests for QA-01 and QA-02; DisplaySpec/FacetSpec schemas"
provides:
  - "coerce_value() with bool-before-int guard: True->'True', False->'False', 1.0->1.0"
  - "_format_check_source() in html_checks.py: '10-K 2024-09-28' or 'WEB (domain...)' format"
  - "_build_filing_date_lookup() in html_renderer.py: {form_label: filing_date} lookup dict"
  - "_group_checks_by_section() updated to accept filing_date_lookup parameter"
affects: [48-03, 48-04, render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "bool-before-int isinstance ordering: always check bool before int/float in Python"
    - "source column formatting via dedicated _format_check_source() with 3-tier priority"
    - "filing date lookup built at render time from acquired_data.filing_documents"

key-files:
  created: []
  modified:
    - src/do_uw/stages/analyze/check_helpers.py
    - src/do_uw/stages/render/html_checks.py
    - src/do_uw/stages/render/html_renderer.py

key-decisions:
  - "_format_check_source() uses 3-tier priority: WEB raw_source > trace_data_source lookup > fallback dash"
  - "_build_filing_date_lookup() builds labels using _SOURCE_LABELS (lazy import from html_footnotes) so form type keys map to display labels matching the QA audit table"
  - "_group_checks_by_section() accepts filing_date_lookup as optional param (default None) for backward compatibility with any test callers that don't pass it"
  - "WEB source truncation: netloc+path up to 35 chars, then '...' — wraps in 'WEB (...)' envelope"
  - "Pre-existing 2 test failures (test_red_flags_template.py::threshold_context) confirmed unchanged — introduced in Phase 47, not a regression"

patterns-established:
  - "QA audit source column formatting: _format_check_source() canonical location for all filing ref display"
  - "Filing date lookup: built once in build_html_context(), passed down to grouping functions"

requirements-completed: [QA-01, QA-02]

# Metrics
duration: 3min
completed: 2026-02-26
---

# Phase 48 Plan 02: QA-01 Source Column + QA-02 Bool Coercion Summary

**Fixed two independent QA audit table bugs: booleans now show "True"/"False" (not "1.00"/"0.00") and source column now shows "10-K 2024-09-28" format with filing dates from acquired data.**

## Performance

- **Duration:** 3 min 8s
- **Started:** 2026-02-26T04:30:53Z
- **Completed:** 2026-02-26T04:34:01Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Fixed `coerce_value()` bool-before-int guard: Python `bool` is a subclass of `int`, so `True` was hitting the `int` branch and Pydantic was coercing it to `1.0`, then `format_adaptive(1.0)` -> `"1.00"`. Now `True` -> `"True"`, `False` -> `"False"`, `1.0` -> `1.0` (unchanged).
- Added `_format_check_source()` to `html_checks.py`: formats QA audit source column with 3-tier priority — WEB sources show truncated domain, trace_data_source lookups show "10-K 2024-09-28" format, fallback is "—".
- Added `_build_filing_date_lookup()` to `html_renderer.py`: reads `acquired_data.filing_documents` at render time to build `{label: date}` dict; wired into `build_html_context()` -> `_group_checks_by_section()`.
- All 12 Wave 0 tests (6 QA-01, 6 QA-02) pass GREEN. 500 combined tests pass.

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix coerce_value() bool-before-int guard (QA-02)** - `f761bce` (fix)
2. **Task 2: Add _build_filing_date_lookup() and _format_check_source() (QA-01)** - `5fc3d8f` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `src/do_uw/stages/analyze/check_helpers.py` - Added `isinstance(data_value, bool)` guard before `(str, int, float)` branch in `coerce_value()`
- `src/do_uw/stages/render/html_checks.py` - Added `_format_check_source()` helper; updated `_group_checks_by_section()` to accept `filing_date_lookup`; imported `_SOURCE_LABELS` from `html_footnotes`
- `src/do_uw/stages/render/html_renderer.py` - Added `_build_filing_date_lookup()` helper; wired into `build_html_context()`

## Decisions Made

- `_format_check_source()` uses 3-tier priority: WEB raw_source > trace_data_source lookup > fallback dash
- `_build_filing_date_lookup()` builds labels using `_SOURCE_LABELS` (lazy import from html_footnotes) so form type keys map to display labels matching the QA audit table
- `_group_checks_by_section()` accepts `filing_date_lookup` as optional param (default `None`) for backward compatibility
- WEB source truncation: netloc+path up to 35 chars, then "..." — wraps in "WEB (...)" envelope
- Pre-existing 2 test failures (`test_red_flags_template.py::threshold_context`) confirmed unchanged — introduced in Phase 47, not a regression from this plan

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The stash verification check (confirming the 2 test failures were pre-existing) required a `git stash pop` to restore changes, but this was routine.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- QA-01 and QA-02 bugs fixed; QA audit table source column and boolean values now display correctly
- Wave 0 tests for QA-01/02 are GREEN
- Plan 03 can address QA-03 (threshold_context rendering) and QA-04 (CRF condition display)
- Pre-existing test failures in `test_red_flags_template.py::threshold_context` remain — these are Phase 47 test stubs awaiting Plan 03

---
*Phase: 48-output-quality-hardening*
*Completed: 2026-02-26*
