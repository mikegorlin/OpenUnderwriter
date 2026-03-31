---
phase: 68-quarterly-extraction
plan: 03
subsystem: extract
tags: [xbrl, reconciliation, data-integrity, yfinance, anti-hallucination]

# Dependency graph
requires:
  - phase: 68-01
    provides: QuarterlyStatements model with 8-quarter XBRL data
provides:
  - reconcile_value() for single-concept XBRL-vs-LLM reconciliation
  - reconcile_quarterly() for full period-matched reconciliation
  - cross_validate_yfinance() with 7-day date tolerance matching
  - ReconciliationReport dataclass for aggregate statistics
affects: [68-02 trend computation, 70-signal-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [xbrl-wins-precedence, divergence-audit-trail, date-proximity-matching]

key-files:
  created:
    - src/do_uw/stages/extract/xbrl_llm_reconciler.py
    - tests/test_xbrl_reconciler.py
  modified: []

key-decisions:
  - "1% divergence threshold for logging -- values within 1% considered matching"
  - "ReconciliationReport as dataclass (not Pydantic) since it is internal tracking, not pipeline state"
  - "LLM fallback source explicitly labeled 'LLM fallback (no XBRL available)' for audit trail"

patterns-established:
  - "XBRL-wins precedence: XBRL always takes priority over LLM for numeric financial data"
  - "Date proximity matching: _match_period_by_date with configurable tolerance window"
  - "Divergence audit trail: structured messages with concept, period, both values, and percentage"

requirements-completed: [QTRLY-06, QTRLY-07]

# Metrics
duration: 3min
completed: 2026-03-06
---

# Phase 68 Plan 03: XBRL/LLM Reconciler Summary

**XBRL-wins reconciler with divergence logging, LLM fallback at MEDIUM confidence, and yfinance 7-day cross-validation**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-06T14:16:10Z
- **Completed:** 2026-03-06T14:19:20Z
- **Tasks:** 1 (TDD)
- **Files modified:** 2

## Accomplishments
- XBRL always wins for numeric data -- anti-hallucination guarantee enforced
- Divergences logged with concept name, period, both values, and percentage difference
- LLM values used as MEDIUM confidence fallback only when XBRL absent
- yfinance cross-validation matches periods by closest date within 7-day tolerance
- ReconciliationReport tracks total comparisons, divergences, xbrl_wins, llm_fallbacks, and messages
- 9 TDD tests covering all reconciliation and cross-validation behaviors

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement XBRL/LLM reconciler with XBRL-wins precedence** - `c23603b` (feat, TDD)

## Files Created/Modified
- `src/do_uw/stages/extract/xbrl_llm_reconciler.py` - Reconciler with reconcile_value, reconcile_quarterly, cross_validate_yfinance (240 lines)
- `tests/test_xbrl_reconciler.py` - 9 tests covering XBRL precedence, divergence logging, yfinance matching (165 lines)

## Decisions Made
- 1% divergence threshold chosen to avoid noise from rounding differences while catching meaningful discrepancies
- ReconciliationReport uses dataclass (not Pydantic) since it is internal tracking, not persisted pipeline state
- LLM fallback source explicitly labeled for full audit trail traceability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Reconciler ready for integration into quarterly extraction pipeline
- reconcile_quarterly and cross_validate_yfinance can be called after XBRL extraction + LLM extraction complete
- ReconciliationReport messages suitable for inclusion in data quality dashboard

---
*Phase: 68-quarterly-extraction*
*Completed: 2026-03-06*
