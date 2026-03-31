---
phase: 113-context-builder-rewrites
plan: 03
subsystem: render
tags: [context-builders, signal-results, governance, litigation, refactor]

requires:
  - phase: 113-context-builder-rewrites
    provides: signal_results plumbing in md_renderer for all builders (Plan 01)
  - phase: 104-signal-consumer-layer
    provides: _signal_consumer.py and _signal_fallback.py typed accessors
provides:
  - governance_evaluative.py with 7 GOV.* signal extraction functions
  - litigation_evaluative.py with 6 LIT.* signal extraction functions
  - governance.py rewritten to 212 lines (from 464) with signal-backed evaluative content
  - litigation.py rewritten to 166 lines (from 500) with signal-backed evaluative content
  - _litigation_helpers.py display data extraction functions
  - Extended _governance_helpers.py with display data builders
affects: [113-04]

tech-stack:
  added: []
  patterns: ["evaluative module extraction: _extract_{category}_signals functions with safe_get_signals_by_prefix", "display helper extraction to _{module}_helpers.py for line count reduction"]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/governance_evaluative.py
    - src/do_uw/stages/render/context_builders/litigation_evaluative.py
    - src/do_uw/stages/render/context_builders/_litigation_helpers.py
  modified:
    - src/do_uw/stages/render/context_builders/governance.py
    - src/do_uw/stages/render/context_builders/_governance_helpers.py
    - src/do_uw/stages/render/context_builders/litigation.py
    - tests/stages/render/test_signal_consumption.py

key-decisions:
  - "Display helper functions (_build_executive_detail, _build_board_member_detail, _build_leaders) moved to _governance_helpers.py rather than governance_evaluative.py since they extract display data not evaluative judgments"
  - "Created _litigation_helpers.py (260 lines) for SCA case, SOL window, derivative, contingent liability extraction -- same pattern as _governance_helpers.py"
  - "GOV signal prefixes mapped to actual brain signal taxonomy: GOV.BOARD, GOV.PAY, GOV.RIGHTS, GOV.EFFECT, GOV.INSIDER, GOV.EXEC, GOV.ACTIVIST (not GOV.COMP/GOV.STRUCTURE as plan suggested)"
  - "LIT signal prefixes mapped to actual taxonomy: LIT.DEFENSE, LIT.REG, LIT.PATTERN, LIT.SCA, LIT.OTHER, LIT.SECTOR (not LIT.SEC/LIT.SOL/LIT.RESERVE as plan suggested)"

patterns-established:
  - "Evaluative extraction pattern: safe_get_signals_by_prefix -> filter TRIGGERED -> _view_to_flag -> list[dict]"
  - "Helper module convention: _{builder}_helpers.py for display-data functions extracted to keep primary builder under 300 lines"

requirements-completed: [BUILD-04, BUILD-05]

duration: 8min
completed: 2026-03-17
---

# Phase 113 Plan 03: Governance + Litigation Evaluative Split Summary

**Governance and litigation builders rewritten with signal-backed evaluative content from GOV.*/LIT.* brain signals, display helpers extracted to keep all modules under 300 lines**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-17T12:13:43Z
- **Completed:** 2026-03-17T12:21:43Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- governance.py reduced from 464 to 212 lines; governance_evaluative.py (193 lines) extracts board quality, compensation, structural, effectiveness, insider, executive, and activist signal flags
- litigation.py reduced from 500 to 166 lines; litigation_evaluative.py (184 lines) extracts defense, SEC/regulatory, SOL/pattern, SCA, other litigation, and sector signal flags
- Both primary builders now import from _signal_fallback and consume signal results via evaluative modules
- Display data (director lists, case details, settlements, holders) preserved as direct state reads
- All render tests pass unchanged (706 passed excluding pre-existing market.py import issues)

## Task Commits

1. **Task 1: Rewrite governance.py + governance_evaluative.py** - `ccab6d0` (feat)
2. **Task 2: Rewrite litigation.py + litigation_evaluative.py** - `978f4a6` (feat)

## Files Created/Modified
- `governance_evaluative.py` (193 lines) - 7 signal extraction functions for GOV.BOARD/PAY/RIGHTS/EFFECT/INSIDER/EXEC/ACTIVIST
- `litigation_evaluative.py` (184 lines) - 6 signal extraction functions for LIT.DEFENSE/REG/PATTERN/SCA/OTHER/SECTOR
- `_litigation_helpers.py` (260 lines) - Display data extractors for SCA cases, SOL windows, derivatives, contingencies, WPE, whistleblower
- `governance.py` (212 lines) - Rewritten to import evaluative + helper functions
- `_governance_helpers.py` (251 lines) - Extended with _build_executive_detail, _build_board_member_detail, _build_leaders
- `litigation.py` (166 lines) - Rewritten to import evaluative + helper functions
- `test_signal_consumption.py` - Added governance.py, governance_evaluative.py, litigation.py, litigation_evaluative.py to SIGNAL_CONSUMING_BUILDERS

## Decisions Made
- Mapped GOV signal prefixes to actual brain taxonomy (GOV.BOARD, GOV.PAY, GOV.RIGHTS, GOV.EFFECT, GOV.INSIDER, GOV.EXEC, GOV.ACTIVIST) rather than plan's simplified GOV.COMP/GOV.STRUCTURE
- Mapped LIT signal prefixes to actual taxonomy (LIT.DEFENSE, LIT.REG, LIT.PATTERN, LIT.SCA, LIT.OTHER, LIT.SECTOR) rather than plan's LIT.SEC/LIT.SOL/LIT.RESERVE
- Created _litigation_helpers.py for display data extraction (same pattern as existing _governance_helpers.py)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Mapped to actual signal ID prefixes instead of plan's suggested prefixes**
- **Found during:** Tasks 1 and 2
- **Issue:** Plan referenced GOV.COMP.*, GOV.STRUCTURE.*, GOV.NARRATIVE.*, LIT.SEC.*, LIT.SOL.*, LIT.RESERVE.* but actual brain signal IDs use GOV.PAY.*, GOV.RIGHTS.*, GOV.EFFECT.*, LIT.REG.*, LIT.PATTERN.*, LIT.SCA.* etc.
- **Fix:** Grepped brain/signals/ for actual IDs and mapped all 7 GOV and 6 LIT prefix groups correctly
- **Verification:** Signal consumption test passes; all render tests pass

**2. [Rule 3 - Blocking] Created _litigation_helpers.py for display data extraction**
- **Found during:** Task 2
- **Issue:** litigation.py at 500 lines could not fit under 300 even after extracting evaluative content
- **Fix:** Created _litigation_helpers.py with display data extraction functions (SCA cases, SOL windows, derivatives, contingencies, WPE, whistleblower)
- **Files modified:** _litigation_helpers.py (new), litigation.py
- **Verification:** litigation.py at 166 lines, all tests pass

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both necessary for correctness. Signal prefix mapping is essential for actual signal consumption. Helper extraction needed for line count requirement.

## Issues Encountered
- Pre-existing market.py import issues (from concurrent 113-02/04 plan execution) caused collection errors in some test files -- excluded from test run, not related to governance/litigation changes
- Pre-existing PydanticUserError in test_compensation_peer_matrix.py and test_narrative_context.py -- excluded, known issue

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Governance and litigation builders now signal-consuming; Plan 04 (scoring + analysis) can proceed
- Pattern established: evaluative module + display helper module + rewritten primary builder

---
*Phase: 113-context-builder-rewrites*
*Completed: 2026-03-17*
