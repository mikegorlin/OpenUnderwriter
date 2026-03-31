---
phase: 116-d-o-commentary-layer
plan: 03
subsystem: render
tags: [jinja2, do-context, signal-results, evaluative-tables, context-builders]

requires:
  - phase: 116-01
    provides: "563 brain signals with do_context templates"
  - phase: 116-02
    provides: "Migrated D&O commentary from Python/Jinja2 to brain YAML"
provides:
  - "D&O Risk columns on all evaluative tables via context builders + template markup"
  - "do_context extraction pattern for every signal domain (FIN, GOV, LIT, STOCK)"
  - "check_summary macro D&O Risk column (covers 3 check templates)"
  - "Forensic dashboard per-finding D&O context via signal mapping"
affects: [116-04, 116-05, render, scoring]

tech-stack:
  added: []
  patterns:
    - "Signal-to-finding do_context mapping via _FORENSIC_FIELD_TO_SIGNAL dict"
    - "do_context_map pattern: prefix-scanned signal do_context lookup for template consumption"
    - "check_summary macro D&O column: automatic for any template using the macro"

key-files:
  created: []
  modified:
    - src/do_uw/stages/render/context_builders/financials_evaluative.py
    - src/do_uw/stages/render/context_builders/financials.py
    - src/do_uw/stages/render/context_builders/financials_forensic.py
    - src/do_uw/stages/render/context_builders/governance_evaluative.py
    - src/do_uw/stages/render/context_builders/litigation_evaluative.py
    - src/do_uw/stages/render/context_builders/market_evaluative.py
    - src/do_uw/stages/render/context_builders/scoring_evaluative.py
    - src/do_uw/stages/render/context_builders/scoring.py
    - src/do_uw/stages/render/html_signals.py
    - src/do_uw/templates/html/components/badges.html.j2
    - src/do_uw/templates/html/sections/financial/forensic_dashboard.html.j2
    - src/do_uw/templates/html/sections/financial/earnings_quality.html.j2
    - src/do_uw/templates/html/sections/governance/board_composition.html.j2
    - src/do_uw/templates/html/sections/litigation/litigation_dashboard.html.j2
    - src/do_uw/templates/html/sections/litigation/sec_enforcement.html.j2
    - src/do_uw/templates/html/sections/market/insider_trading.html.j2
    - src/do_uw/templates/html/sections/scoring/ten_factor_scoring.html.j2
    - src/do_uw/templates/html/sections/scoring/pattern_detection.html.j2
    - src/do_uw/templates/html/sections/scoring/allegation_mapping.html.j2

key-decisions:
  - "Used do_context_map pattern (prefix-scanned dict) for governance/litigation rather than per-signal keys"
  - "Updated check_summary macro centrally rather than modifying 3 individual check templates"
  - "Forensic dashboard findings get do_context via _FORENSIC_FIELD_TO_SIGNAL mapping"
  - "Plan referenced forensic_composites.html.j2 which does not exist -- mapped to forensic_dashboard.html.j2"

patterns-established:
  - "do_context_map: Build dict of signal_id->do_context from prefix scan, pass to template for flexible lookup"
  - "Signal-to-finding mapping: _FORENSIC_FIELD_TO_SIGNAL maps ForensicMetric field names to brain signal IDs"

requirements-completed: [COMMENT-01, COMMENT-03]

duration: 8min
completed: 2026-03-19
---

# Phase 116 Plan 03: D&O Column Wiring Summary

**D&O Risk columns wired into all evaluative tables across 5 context builders and 13 Jinja2 templates via signal do_context extraction**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-19T05:08:53Z
- **Completed:** 2026-03-19T05:17:00Z
- **Tasks:** 2
- **Files modified:** 20

## Accomplishments
- Every evaluative context builder (financials, governance, litigation, market, scoring) now extracts do_context from signal results
- 62 do_context references across context builders; 24 across templates
- check_summary macro (used by financial/governance/market checks) automatically renders D&O Risk column
- Forensic dashboard findings carry per-indicator D&O context via signal ID mapping
- All 63 render tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire D&O columns into all evaluative table context builders** - `56081dbe` (feat)
2. **Task 2: Add D&O column markup to Jinja2 evaluative templates** - `3c0e3101` (feat)

## Files Created/Modified

### Context Builders (Task 1)
- `src/do_uw/stages/render/context_builders/financials_evaluative.py` - 12 forensic + 5 earnings + 2 leverage + 1 tax + 2 liquidity do_context keys
- `src/do_uw/stages/render/context_builders/financials.py` - 3 audit risk do_context keys
- `src/do_uw/stages/render/context_builders/governance_evaluative.py` - do_context in flags + do_context_map
- `src/do_uw/stages/render/context_builders/litigation_evaluative.py` - do_context in flags + SCA/SEC aggregate
- `src/do_uw/stages/render/context_builders/market_evaluative.py` - volatility/short/insider/guidance/beta/returns do_context
- `src/do_uw/stages/render/context_builders/scoring_evaluative.py` - scoring_do_context_map from all signal prefixes
- `src/do_uw/stages/render/context_builders/scoring.py` - wired extract_scoring_do_context
- `src/do_uw/stages/render/html_signals.py` - do_context in grouped signal results

### Templates (Task 2)
- `src/do_uw/templates/html/components/badges.html.j2` - D&O Risk column in check_summary macro
- `src/do_uw/templates/html/sections/financial/forensic_dashboard.html.j2` - D&O Risk column per finding
- `src/do_uw/templates/html/sections/financial/earnings_quality.html.j2` - D&O context block
- `src/do_uw/templates/html/sections/governance/board_composition.html.j2` - Board D&O context block
- `src/do_uw/templates/html/sections/litigation/litigation_dashboard.html.j2` - SCA/SEC D&O callouts
- `src/do_uw/templates/html/sections/litigation/sec_enforcement.html.j2` - D&O context block
- `src/do_uw/templates/html/sections/market/insider_trading.html.j2` - Insider D&O context
- `src/do_uw/templates/html/sections/scoring/ten_factor_scoring.html.j2` - D&O Risk column per factor
- `src/do_uw/templates/html/sections/scoring/pattern_detection.html.j2` - D&O context per pattern
- `src/do_uw/templates/html/sections/scoring/allegation_mapping.html.j2` - D&O context per theory
- `src/do_uw/stages/render/context_builders/financials_forensic.py` - signal_results passthrough + field-to-signal mapping

## Decisions Made
- Used `do_context_map` pattern (prefix-scanned dict) for governance/litigation rather than dozens of per-signal named keys -- more maintainable as signals are added
- Updated `check_summary` macro centrally rather than duplicating D&O column logic in 3 separate check templates
- Forensic dashboard findings get do_context via `_FORENSIC_FIELD_TO_SIGNAL` mapping dict (22 field-to-signal mappings)
- Plan referenced `forensic_composites.html.j2` which does not exist; correctly mapped to `forensic_dashboard.html.j2`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] forensic_composites.html.j2 does not exist**
- **Found during:** Task 2 (template updates)
- **Issue:** Plan referenced `forensic_composites.html.j2` but actual file is `forensic_dashboard.html.j2`
- **Fix:** Updated `forensic_dashboard.html.j2` instead, also added signal-to-finding D&O context mapping in `financials_forensic.py`
- **Files modified:** `forensic_dashboard.html.j2`, `financials_forensic.py`
- **Verification:** Template renders correctly, 63 tests pass
- **Committed in:** 3c0e3101

---

**Total deviations:** 1 auto-fixed (1 blocking -- nonexistent file)
**Impact on plan:** Minimal -- correct file was identified and updated with equivalent functionality.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All evaluative tables now have D&O Risk columns wired from signal do_context
- Ready for 116-04 (verification/testing of D&O commentary end-to-end)
- Pattern established for any future evaluative tables: extract do_context from signal, pass to template

---
*Phase: 116-d-o-commentary-layer*
*Completed: 2026-03-19*
