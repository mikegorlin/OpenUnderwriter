---
phase: 140-litigation-classification-consolidation
plan: 02
subsystem: render
tags: [litigation, context-builder, display-helpers, classifier-output, coverage-side, legal-theory]

requires:
  - phase: 140-litigation-classification-consolidation
    plan: 01
    provides: "Unified post-extraction classifier with legal theory, coverage side, dedup, year disambiguation, missing field flagging"
provides:
  - "Litigation context builder surfaces all classifier output to templates"
  - "Three new display helpers: extract_source_references, extract_data_quality_flags, format_legal_theories"
  - "LEGAL_THEORY_DISPLAY mapping for all 12 LegalTheory enum values"
  - "Unclassified reserves bucket surfaced as separate context key"
  - "SCA table in Word renderer includes Legal Theory and Coverage columns"
  - "Unclassified reserves subsection in Word renderer"
affects: [rendering-litigation, html-templates]

tech-stack:
  added: []
  patterns: [context-enrichment-post-extraction, display-helper-pattern]

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/context_builders/_litigation_helpers.py
    - src/do_uw/stages/render/context_builders/litigation.py
    - src/do_uw/stages/render/sections/sect6_litigation.py

key-decisions:
  - "LEGAL_THEORY_DISPLAY covers all 12 LegalTheory enum values with human-readable labels"
  - "Enrichment applied post-extraction by iterating parallel case objects and case dicts (index-based matching)"
  - "Unclassified reserves rendered as simple table with explanatory note"
  - "Pre-existing lint errors and test failures left untouched (out of scope per deviation rules)"

requirements-completed: [LIT-01, LIT-02, LIT-03, LIT-04, LIT-05]

duration: 6min
completed: 2026-03-28
---

# Phase 140 Plan 02: Litigation Context Builder + Template Updates Summary

**Context builder enriched with legal theory labels, coverage side badges, source references, data quality flags, and separated unclassified reserves from classifier output**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-28T01:49:01Z
- **Completed:** 2026-03-28T01:55:02Z
- **Tasks:** 1 completed, 1 checkpoint (human-verify)
- **Files modified:** 3

## Accomplishments
- Added LEGAL_THEORY_DISPLAY mapping covering all 12 LegalTheory enum values (Rule 10b-5, Section 11, FCPA, etc.)
- Created extract_source_references helper to format merged source provenance from dedup
- Created extract_data_quality_flags helper that cross-references cases_needing_recovery queue
- Created format_legal_theories helper using LEGAL_THEORY_DISPLAY with CLAIM_TYPE_NAMES fallback
- Enriched both SCA and derivative suit case dicts with legal_theories_display, coverage_display, source_references, data_quality_flags
- Added unclassified_reserves bucket to litigation context dict from LitigationLandscape
- Updated Word renderer SCA table headers to include Legal Theory and Coverage columns
- Added _render_unclassified_reserves subsection to sect6_litigation.py Word renderer

## Task Commits

Each task was committed atomically:

1. **Task 1: Context builder + helpers + template updates** - `d01e91e4` (feat)
2. **Task 2: Human verification checkpoint** - NOT EXECUTED (checkpoint for orchestrator)

## Checkpoint Status

Task 2 is a `checkpoint:human-verify` requiring visual inspection of rendered worksheet.

**What was built:**
- Full litigation classification and consolidation pipeline (Plan 01 + Plan 02)
- Unified post-extraction classifier with legal theory + coverage side
- Universal deduplication across SCA and derivative case lists
- Year disambiguation on all case names
- Missing field flagging with data quality annotations
- Boilerplate reserves separated into unclassified bucket
- Context builder updated to surface all classifier output

**How to verify:**
1. Run `underwrite AAPL --fresh` (or a ticker with known litigation)
2. Open the HTML output and navigate to the Litigation section
3. Verify each case shows legal theory type (Rule 10b-5, Section 11, etc.)
4. Verify no duplicate cases appear
5. Verify every case name includes a year suffix
6. Verify coverage side labels appear (Side A, Side B, Side C, etc.)
7. Check for data quality warnings on cases with missing fields
8. Check for separated unclassified reserves subsection

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/_litigation_helpers.py` - Added LEGAL_THEORY_DISPLAY, extract_source_references, extract_data_quality_flags, format_legal_theories
- `src/do_uw/stages/render/context_builders/litigation.py` - Enriched SCA + derivative case dicts, added unclassified_reserves bucket
- `src/do_uw/stages/render/sections/sect6_litigation.py` - Added Legal Theory + Coverage columns to SCA table, added unclassified reserves subsection

## Decisions Made
- LEGAL_THEORY_DISPLAY maps all 12 enum values with human-readable labels (e.g. RULE_10B5 -> "Rule 10b-5")
- Index-based matching between case objects and case dicts for enrichment (parallel iteration)
- Unclassified reserves rendered as simple 3-column table with italic explanatory note
- Removed unused CLAIM_TYPE_NAMES import from litigation.py (it's used indirectly via helpers)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs
None -- all functions are fully implemented with real logic.

## Issues Encountered
- Pre-existing test failures in test_forward_scenarios.py and test_narrative_generation.py (unrelated to changes)
- Pre-existing lint errors (E501 line length) in unchanged lines of _litigation_helpers.py and litigation.py
- Pre-existing unused imports (safe_get_result, safe_get_signals_by_prefix) in litigation.py

## User Setup Required
None - no external service configuration required.

## Next Steps
- Human verification via `underwrite AAPL --fresh` to confirm visual output
- HTML template updates may be needed to surface the new context keys in the HTML render path

---
*Phase: 140-litigation-classification-consolidation*
*Completed: 2026-03-28*
