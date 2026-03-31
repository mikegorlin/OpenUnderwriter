---
phase: 129-bug-fixes-and-data-integrity
plan: 02
subsystem: benchmark, extract
tags: [narrative-validation, cross-validation, xbrl, sca-filtering, governance, gender-diversity, board-parsing]

# Dependency graph
requires:
  - phase: 129-01
    provides: Canonical SCA counter (get_active_genuine_scas)
  - phase: 128-03
    provides: XBRL/LLM reconciler with hallucination threshold
provides:
  - Post-generation narrative cross-validation for dollar amounts (>2x divergence detection)
  - Canonical SCA counter usage in narrative data extraction (DOJ_FCPA excluded)
  - Enhanced DEF 14A prompt for gender diversity and current GC extraction
  - Board completeness check in proxy parsing
affects: [render, scoring, benchmark, extract]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Post-generation LLM cross-validation via regex dollar extraction + known-value comparison"
    - "Board completeness check via proxy text size mentions vs extracted count"

key-files:
  created:
    - tests/benchmark/__init__.py
    - tests/benchmark/test_narrative_validation.py
    - tests/extract/test_governance_extraction.py
  modified:
    - src/do_uw/stages/benchmark/narrative_generator.py
    - src/do_uw/stages/benchmark/narrative_data_sections.py
    - src/do_uw/stages/benchmark/narrative_data.py
    - src/do_uw/stages/extract/llm/prompts.py
    - src/do_uw/stages/extract/board_parsing.py

key-decisions:
  - "Narrative cross-validation logs warnings but does not auto-replace hallucinated values (conservative approach)"
  - "LLM extraction cache keyed by (accession, form_type, schema_version) -- prompt changes do NOT invalidate cache; --fresh required"
  - "Board completeness check uses proxy text regex for expected size, not a separate API call"

patterns-established:
  - "validate_narrative_amounts: reusable cross-validation for any LLM-generated text"

requirements-completed: [FIX-01, FIX-02]

# Metrics
duration: 21min
completed: 2026-03-23
---

# Phase 129 Plan 02: Narrative Cross-Validation and Governance Extraction Gaps Summary

**Post-generation dollar amount cross-validation gate preventing $383B-type hallucinations, canonical SCA counter in narrative data path excluding DOJ_FCPA, and enhanced DEF 14A prompt for gender diversity and current GC extraction**

## Performance

- **Duration:** 21 min
- **Started:** 2026-03-23T00:12:26Z
- **Completed:** 2026-03-23T00:33:28Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added `validate_narrative_amounts()` function that extracts dollar amounts from LLM-generated narratives via regex and flags any that diverge >2x from known XBRL-reconciled state values
- Replaced inline SCA filtering in `narrative_data_sections.py` and `narrative_data.py` with canonical `get_active_genuine_scas()` from Plan 129-01, ensuring DOJ_FCPA cases never appear in narrative SCA data
- Enhanced DEF 14A system prompt to explicitly request board gender diversity percentage, racial diversity percentage, and current General Counsel/CLO name with appointment date
- Added board completeness check that warns when proxy text mentions more directors than the parser extracted

## Task Commits

Each task was committed atomically:

1. **Task 1: Narrative cross-validation gate + DOJ_FCPA data path** - `1f61a7e9` (feat)
2. **Task 2: Governance extraction gaps** - `d03849cd` (feat)

## Files Created/Modified
- `tests/benchmark/__init__.py` - Test package init
- `tests/benchmark/test_narrative_validation.py` - 6 tests for narrative cross-validation and DOJ_FCPA filtering
- `tests/extract/test_governance_extraction.py` - 8 tests for governance schema, prompt content, board parsing
- `src/do_uw/stages/benchmark/narrative_generator.py` - Added validate_narrative_amounts() and integrated into _generate_one()
- `src/do_uw/stages/benchmark/narrative_data_sections.py` - Replaced inline SCA filter with canonical counter
- `src/do_uw/stages/benchmark/narrative_data.py` - Replaced inline SCA filter with canonical counter
- `src/do_uw/stages/extract/llm/prompts.py` - Enhanced DEF14A prompt with diversity and GC extraction guidance
- `src/do_uw/stages/extract/board_parsing.py` - Added _check_board_completeness() and _extract_expected_board_size()

## Decisions Made
- Cross-validation logs `NARRATIVE_HALLUCINATION_FLAG` warnings but does not auto-replace values -- conservative approach avoids incorrect replacements when the LLM's value might be contextually correct (e.g., segment revenue vs total)
- The `_extract_known_values()` helper extracts all numeric values from section_data dict for comparison, keeping the validation generic across all section types
- Board completeness check uses simple regex patterns to find expected board size in proxy text rather than requiring a separate structured extraction

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- 3 pre-existing test failures found (brain contract, manifest agreement, CI gate) -- all confirmed pre-existing by running against prior commits. Not related to plan changes.
- LLM extraction cache does not include prompt content hash in its key -- documented in commit message that `--fresh` is required after prompt changes

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Narrative cross-validation active for all future pipeline runs
- DEF 14A extraction will produce gender diversity and current GC data on next `--fresh` run (cache invalidation needed)
- Board completeness logging provides visibility into extraction gaps without blocking

## Self-Check: PASSED

All 8 created/modified files exist. Both task commits (1f61a7e9, d03849cd) verified in git log. 14 new tests pass. 3 pre-existing test failures confirmed unrelated to changes.

---
*Phase: 129-bug-fixes-and-data-integrity*
*Completed: 2026-03-23*
