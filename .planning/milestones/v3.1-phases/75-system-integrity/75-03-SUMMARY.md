---
phase: 75-system-integrity
plan: 03
subsystem: testing
tags: [beautifulsoup, semantic-qa, html-validation, pytest]

requires:
  - phase: 73-rendering-bugs
    provides: HTML rendering templates and output format
provides:
  - Semantic QA validation module comparing rendered HTML against state.json source data
  - CI-integrated pytest tests for revenue, board size, score, and tier validation
affects: [render, testing, qa]

tech-stack:
  added: []
  patterns: [semantic-qa-validation, html-state-comparison, multi-strategy-extraction]

key-files:
  created:
    - src/do_uw/stages/render/semantic_qa.py
    - tests/stages/render/test_semantic_qa.py
  modified: []

key-decisions:
  - "Revenue validation uses 5% tolerance and matches against ANY FY period (HTML may show prior year)"
  - "Score extraction uses narrative text as primary strategy (most reliable), signal debug table as fallback"
  - "Board size extraction filters by row cell count (<=4) to avoid signal debug table false matches"
  - "Tier extraction searches badge-tier CSS class first, then narrative text patterns"

patterns-established:
  - "Multi-strategy HTML extraction: try specific structures first, fall back to broader patterns"
  - "Parametrized integration tests over all available output directories with graceful skip"

requirements-completed: [SYS-06, SYS-07]

duration: 9min
completed: 2026-03-07
---

# Phase 75 Plan 03: Semantic QA Summary

**BeautifulSoup-based semantic QA validates HTML revenue, board size, score, and tier against state.json with multi-strategy extraction and 79 CI-integrated tests**

## Performance

- **Duration:** 9 min
- **Started:** 2026-03-07T05:31:37Z
- **Completed:** 2026-03-07T05:40:06Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Financial value parser handles all formatting patterns ($1.2B, $450M, commas, negative parens)
- Multi-strategy HTML extraction: narrative text for scores, KV tables for board/revenue, badge classes for tier
- Validated against 6 real pipeline outputs (RPM, V, AAPL, SHW, SNA, WWD) -- all 24 checks pass
- Integration tests parametrized over all available output directories with graceful skip when unavailable

## Task Commits

Each task was committed atomically:

1. **Task 1: Create semantic QA validation module** - `64d87fd` (feat)
2. **Task 2: Create CI-integrated semantic QA tests** - `de1647f` (test)

## Files Created/Modified
- `src/do_uw/stages/render/semantic_qa.py` - Semantic QA validation functions (418 lines)
- `tests/stages/render/test_semantic_qa.py` - Unit + integration tests (424 lines, 79 tests)

## Decisions Made
- Revenue: 5% tolerance for display rounding ($7.4B vs $7,372,644,000), matches any FY period since HTML may show prior year
- Score: Narrative text extraction ("composite quality score of 83.8") is most reliable; debug table cell is fallback
- Board size: Row cell count filter (<=4) distinguishes display KV tables from signal debug tables (6 cells)
- Tier: Badge CSS class first, narrative text fallback for older outputs

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] State data paths differ from plan assumptions**
- **Found during:** Task 1 (state extraction)
- **Issue:** Plan assumed `extracted.financials.statements[].concept == "revenue"` but actual structure is `statements.income_statement.line_items[].label` with `values.FYXXXX.value` dict
- **Fix:** Rewrote state extraction to follow actual data paths: `label` not `concept`, `scoring.composite_score` not `scored.overall_score`, `scoring.tier.tier` nested dict, `governance.board.size` SourcedValue
- **Files modified:** src/do_uw/stages/render/semantic_qa.py
- **Verification:** All 6 ticker outputs validate correctly

**2. [Rule 1 - Bug] HTML score extraction hitting wrong table**
- **Found during:** Task 1 (HTML extraction debugging)
- **Issue:** Small "Quality Score" KV rows (2 cells, value 1.00) matched before signal debug table with actual composite score (83.80). Board size similarly matched 6-cell debug rows returning "12.0" parsed as 120.
- **Fix:** Score extraction prioritizes narrative text ("composite quality score of X"); board size filters by row cell count (<=4 to exclude debug tables)
- **Files modified:** src/do_uw/stages/render/semantic_qa.py
- **Verification:** All 6 tickers pass score and board size validation

---

**Total deviations:** 2 auto-fixed (2 bugs -- data path and HTML parsing)
**Impact on plan:** Essential corrections for real-world data structures. No scope creep.

## Issues Encountered
- Pre-existing test failure in test_pdf_paged.py (CSS margin assertion) -- unrelated to this plan, not addressed

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Semantic QA ready for CI integration -- 79 tests pass
- Framework extensible: adding new validation checks follows the same pattern (state extractor + HTML extractor + validator)
- Pre-existing test_pdf_paged failure should be tracked separately

---
*Phase: 75-system-integrity*
*Completed: 2026-03-07*
