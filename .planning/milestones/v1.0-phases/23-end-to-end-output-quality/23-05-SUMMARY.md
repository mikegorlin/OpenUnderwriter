---
phase: 23-end-to-end-output-quality
plan: 05
subsystem: testing
tags: [python-docx, output-validation, ground-truth, process-validation, docx-reading]

# Dependency graph
requires:
  - phase: 23-01
    provides: ground truth files with per-ticker facts (xom.py, smci.py, helpers.py)
  - phase: 23-02
    provides: sector display fix verifiable in output
  - phase: 23-03
    provides: employee count fix verifiable in output
provides:
  - Process validation harness reading .docx output and asserting per-ticker facts
  - Docx reading utilities (load_docx, read_docx_tables, read_docx_text, find_in_tables, find_text_containing)
  - Ground truth output_facts sections for XOM and SMCI
  - Custom pytest marker output_validation for selective test runs
affects: [23-06, 23-07, 23-08, render-stage, output-quality]

# Tech tracking
tech-stack:
  added: []
  patterns: [docx-output-validation, skip-when-no-output, output_facts-ground-truth]

key-files:
  created:
    - tests/test_output_validation.py
  modified:
    - tests/ground_truth/helpers.py
    - tests/ground_truth/xom.py
    - tests/ground_truth/smci.py
    - pyproject.toml

key-decisions:
  - "Tests skip (not fail) when .docx not present -- requires prior pipeline run"
  - "find_in_tables searches ALL cells in a row, not just first cell -- catches more matches"
  - "2 expected test failures are CORRECT (detect known XOM employee count and shares $ prefix defects)"
  - "Registered output_validation marker in pyproject.toml for selective test runs"

patterns-established:
  - "output_facts section in ground truth: document-level validation facts separate from state-level facts"
  - "Skip-when-no-output pattern: pytest.skip() when .docx files not generated"
  - "Marker-based test selection: @pytest.mark.output_validation for pipeline output tests"

# Metrics
duration: 3m 29s
completed: 2026-02-11
---

# Phase 23 Plan 05: Process Validation Harness Summary

**Python-docx validation harness with 12 tests across XOM and SMCI that read actual .docx worksheets and assert facts against ground truth, detecting 2 known defects (employee count, shares $ prefix)**

## Performance

- **Duration:** 3m 29s
- **Started:** 2026-02-11T22:41:19Z
- **Completed:** 2026-02-11T22:44:48Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- Built process validation harness that reads generated .docx files (not state.json) and validates per-ticker facts
- Added 5 docx reading utility functions to helpers.py (load_docx, read_docx_tables, read_docx_text, find_in_tables, find_text_containing)
- Created TestXOMOutput (6 tests) validating employee count, sector, shares formatting, auditor, company name, financial tables
- Created TestSMCIOutput (6 tests) validating sector, employee count, company name, known outcome signals, blind spot coverage, financial tables
- Expanded ground truth with output_facts sections for document-level validation
- Correctly detects 2 known defects: XOM employee count (62 vs 50K+) and shares $ prefix

## Task Commits

Each task was committed atomically:

1. **Task 1: Add docx reading utilities and expand ground truth** - `d3e0ebb` (feat)
2. **Task 2: Build output validation test suite** - `04e978b` (feat)

## Files Created/Modified
- `tests/test_output_validation.py` - Process validation harness with TestXOMOutput and TestSMCIOutput classes (12 tests)
- `tests/ground_truth/helpers.py` - Added 5 docx reading utility functions
- `tests/ground_truth/xom.py` - Added output_facts section (employee count, sector, auditor, shares formatting)
- `tests/ground_truth/smci.py` - Added output_facts section (sector, employee count, known outcome signals)
- `pyproject.toml` - Registered output_validation marker

## Decisions Made
- Tests skip (not fail) when .docx not present, since these require a prior pipeline run
- find_in_tables searches ALL cells in a row (not just first cell) to catch more matches across different table layouts
- 2 expected test failures are intentional and correct -- they detect known defects (XOM employee count at 62 instead of 62,000, and shares outstanding with $ prefix)
- Registered output_validation custom marker in pyproject.toml to suppress pytest warnings and enable selective test runs with `-m output_validation`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Registered output_validation pytest marker**
- **Found during:** Task 2 (test suite creation)
- **Issue:** Custom marker `output_validation` caused PytestUnknownMarkWarning
- **Fix:** Added marker registration to pyproject.toml [tool.pytest.ini_options]
- **Files modified:** pyproject.toml
- **Verification:** Marker warning gone on re-run
- **Committed in:** 04e978b (Task 2 commit)

**2. [Rule 1 - Bug] Enhanced find_in_tables to search all cells**
- **Found during:** Task 1 (docx utility creation)
- **Issue:** Plan spec searched only first cell (row[0]), but many .docx tables have labels in middle columns
- **Fix:** Changed to search ALL cells in row for label match
- **Files modified:** tests/ground_truth/helpers.py
- **Verification:** Correctly finds employee rows and shares rows in actual XOM/SMCI .docx files
- **Committed in:** d3e0ebb (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 missing critical, 1 bug fix)
**Impact on plan:** Both auto-fixes necessary for correctness. No scope creep.

## Issues Encountered
None - both .docx files were present and readable, all utilities imported correctly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Validation harness operational and detecting real defects
- 10 tests pass, 2 correctly fail on known defects (to be fixed by other plans)
- Ready for plans 23-06 through 23-08 to fix the detected defects
- Run with: `uv run pytest -m output_validation -v`

## Self-Check: PASSED

All artifacts verified:
- tests/test_output_validation.py: FOUND
- tests/ground_truth/helpers.py: FOUND
- tests/ground_truth/xom.py: FOUND
- tests/ground_truth/smci.py: FOUND
- 23-05-SUMMARY.md: FOUND
- Commit d3e0ebb: FOUND
- Commit 04e978b: FOUND

---
*Phase: 23-end-to-end-output-quality*
*Completed: 2026-02-11*
