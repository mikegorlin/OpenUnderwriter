---
phase: 17-system-assessment
plan: 01
subsystem: data-pipeline
tags: [sec-filings, xbrl, state-serialization, filing-documents, pydantic]

# Dependency graph
requires:
  - phase: 04-governance-market-analysis
    provides: Filing document fetcher and filing_documents TypedDict
  - phase: 03-financial-extraction
    provides: Company Facts XBRL extraction via sourced.py helpers
provides:
  - Filing documents correctly routed to acquired.filing_documents
  - State serialization strips company_facts (~4MB) for lean state.json
  - Backward-compat fallback for legacy state files
affects:
  - 17-02 (name extraction quality depends on filing text access)
  - 17-03 (SCA extraction needs filing documents for 10-K Item 3)
  - 17-04 (all extraction improvements depend on data reaching extractors)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Strip-before-serialize pattern: _strip_filings_blobs / _restore_filings_blobs"
    - "_promote_filing_fields pattern: pop nested keys to dedicated Pydantic fields"

key-files:
  created:
    - tests/test_filing_documents.py
  modified:
    - src/do_uw/stages/acquire/orchestrator.py
    - src/do_uw/pipeline.py

key-decisions:
  - "Pop-and-promote pattern for filing_documents instead of second setattr call"
  - "Strip-before-serialize with try/finally restore instead of model_dump exclude"
  - "Strip exhibit_21 along with company_facts and filing_texts (all cached in SQLite)"
  - "cast() for pyright strict on dict popped from Any-typed SEC client result"

patterns-established:
  - "_promote_filing_fields: pop nested keys from client result dict to dedicated state fields"
  - "_strip_filings_blobs/_restore_filings_blobs: temporarily remove large blobs for serialization"

# Metrics
duration: 8min
completed: 2026-02-10
---

# Phase 17 Plan 01: Filing Documents Data Flow & State Size Summary

**Fixed filing_documents not reaching extractors by promoting from nested filings dict to dedicated field; stripped Company Facts XBRL blob from state.json serialization reducing size from ~16MB to <2MB**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-10T16:10:42Z
- **Completed:** 2026-02-10T16:18:42Z
- **Tasks:** 2
- **Files modified:** 3 (orchestrator.py, pipeline.py, test_filing_documents.py)

## Accomplishments
- Filing documents (DEF 14A, 8-K, 10-K, etc.) now correctly routed to `acquired.filing_documents` dedicated Pydantic field
- Company Facts XBRL blob (~4MB) stripped from state.json serialization while remaining available in-memory for extractors
- Legacy filing_texts and exhibit_21 also stripped from serialized state
- 19 tests covering promotion, orchestrator integration, fallback compatibility, and serialization behavior
- All 1940+ tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix filing_documents data flow** - `5e6dfcb` (fix)
2. **Task 2: Strip Company Facts from serialization** - `479dfa3` (perf)

## Files Created/Modified
- `src/do_uw/stages/acquire/orchestrator.py` - Added `_promote_filing_fields()` to extract filing_documents from SEC result to dedicated state field
- `src/do_uw/pipeline.py` - Added `_strip_filings_blobs()` and `_restore_filings_blobs()` for lean state serialization
- `tests/test_filing_documents.py` - 19 tests: promotion, orchestrator flow, fallback compat, serialization stripping

## Decisions Made
- **Pop-and-promote pattern**: Pop filing_documents from SEC client dict and set on `acquired.filing_documents` directly, preventing double-storage. Cleanest approach since it keeps the orchestrator's generic `setattr` pattern intact.
- **Strip-before-serialize with try/finally restore**: Rather than using Pydantic's `model_dump(exclude=...)` (which requires complex path specifications), we pop keys before serialization and restore them in a finally block. This is simpler and guarantees in-memory state integrity even if serialization fails.
- **Three keys stripped**: company_facts (~4MB), filing_texts (legacy), and exhibit_21 are all stripped. All three are cached in SQLite by the SEC client and re-fetched on pipeline resume.
- **cast() for pyright strict**: Used `cast(dict[str, Any], data)` for the dict from `client.acquire()` which returns `Any`, and `cast(dict[str, list[dict[str, str]]], filing_docs)` for the popped filing_documents value.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pyright strict type errors from Any-typed client result**
- **Found during:** Task 1 (orchestrator fix)
- **Issue:** `client.acquire()` returns `Any`, so `isinstance(data, dict)` narrows to `dict[Unknown, Unknown]` -- pyright reports `reportUnknownArgumentType`
- **Fix:** Added `cast(dict[str, Any], data)` before passing to `_promote_filing_fields()`
- **Files modified:** src/do_uw/stages/acquire/orchestrator.py
- **Verification:** `pyright src/do_uw/` returns 0 errors
- **Committed in:** 479dfa3 (Task 2 commit, combined with serialization fix)

**2. [Rule 1 - Bug] Removed unused pytest import**
- **Found during:** Task 2 (ruff lint check)
- **Issue:** pytest was imported but not used in test_filing_documents.py
- **Fix:** Removed the import
- **Files modified:** tests/test_filing_documents.py
- **Committed in:** 479dfa3

---

**Total deviations:** 2 auto-fixed (2 bugs: type errors, lint)
**Impact on plan:** Both auto-fixes necessary for code quality. No scope creep.

## Issues Encountered
- Pre-existing test failure in `test_sca_extractor.py::TestTwoLayerClassification::test_10b5_maps_to_sca_side_a` from uncommitted working directory changes from a prior session. Not caused by this plan's changes. All 1940+ committed tests pass.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Filing documents now reach extractors at the correct state path
- State.json serialization is lean (<2MB vs ~16MB)
- Ready for Phase 17 Plan 02 (name extraction quality) and Plans 03-04 (extraction improvements)
- Extractors accessing `get_filing_documents(state)` and `get_company_facts(state)` work correctly with both new and legacy state files

---
*Phase: 17-system-assessment*
*Completed: 2026-02-10*
