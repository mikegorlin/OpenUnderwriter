---
phase: 128-infrastructure-foundation
plan: 03
subsystem: infra
tags: [xbrl, reconciliation, hallucination-detection, regression-testing, snapshot]

# Dependency graph
requires:
  - phase: 128-01
    provides: assembly_registry pattern and build_html_context entry point
  - phase: 128-02
    provides: source_link.json and inventory completeness heuristic
provides:
  - DiscrepancyWarning dataclass for >2x XBRL/LLM divergence flagging
  - state.extracted.financials.reconciliation_warnings persistence path
  - build_reconciliation_audit_context for audit appendix rendering
  - Reference snapshot capture/compare scripts for regression detection
affects: [render, audit-appendix, data-quality, regression-testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [hallucination-threshold-ratio, reference-snapshot-hashing]

key-files:
  created:
    - scripts/capture_reference_snapshots.py
    - scripts/compare_reference_snapshots.py
    - tests/extract/test_xbrl_cross_validation.py
    - tests/test_reference_snapshots.py
    - .planning/baselines/.gitkeep
  modified:
    - src/do_uw/stages/extract/xbrl_llm_reconciler.py
    - src/do_uw/stages/extract/__init__.py
    - src/do_uw/models/financials.py
    - src/do_uw/stages/render/context_builders/audit.py
    - src/do_uw/stages/render/context_builders/assembly_signals.py
    - .gitignore

key-decisions:
  - "reconcile_value returns 3-tuple (result, messages, warnings) to carry DiscrepancyWarning objects alongside string messages"
  - "Hallucination threshold ratio set at 2.0x, separate from the 1% divergence threshold for XBRL-wins logic"
  - "XBRL=0 with LLM!=0 always flags as inf divergence (cannot compute ratio)"
  - "Reference baselines stored as JSON in .planning/baselines/ and gitignored (machine-specific)"

patterns-established:
  - "Hallucination detection: separate threshold constant (_HALLUCINATION_THRESHOLD_RATIO) from divergence threshold (_DIVERGENCE_THRESHOLD_PCT)"
  - "Reference snapshots: SHA256 section hashing for regression detection across tickers"

requirements-completed: [INFRA-05, INFRA-02]

# Metrics
duration: 12min
completed: 2026-03-22
---

# Phase 128 Plan 03: XBRL/LLM Discrepancy Flagging + Reference Snapshot Tooling Summary

**>2x XBRL/LLM hallucination flagging with DiscrepancyWarning dataclass, state persistence, audit appendix wiring, plus SHA256-based reference snapshot capture/compare scripts for regression detection**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-22T22:38:34Z
- **Completed:** 2026-03-22T22:50:34Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- XBRL/LLM reconciler now flags any divergence >2x as hallucination-level with structured DiscrepancyWarning
- Warnings persist at state.extracted.financials.reconciliation_warnings and surface in audit appendix
- Reference snapshot scripts enable regression detection by comparing HTML section hashes across AAPL, RPM, V
- 15 tests covering discrepancy flagging, audit context, snapshot structure, and comparison logic

## Task Commits

Each task was committed atomically:

1. **Task 1: Add >2x discrepancy flagging (TDD RED)** - `f3925b56` (test)
2. **Task 1: Add >2x discrepancy flagging (TDD GREEN)** - `827a4533` (feat)
3. **Task 2: Create reference snapshot scripts** - `5a5b6267` (feat)

_Note: Task 1 used TDD with RED (failing tests) then GREEN (implementation) commits._

## Files Created/Modified
- `src/do_uw/stages/extract/xbrl_llm_reconciler.py` - Added DiscrepancyWarning, _HALLUCINATION_THRESHOLD_RATIO, 3-tuple return
- `src/do_uw/models/financials.py` - Added reconciliation_warnings field to ExtractedFinancials
- `src/do_uw/stages/extract/__init__.py` - Wires discrepancy warnings to state via dataclasses.asdict
- `src/do_uw/stages/render/context_builders/audit.py` - Added build_reconciliation_audit_context
- `src/do_uw/stages/render/context_builders/assembly_signals.py` - Wires reconciliation audit into HTML context
- `scripts/capture_reference_snapshots.py` - CLI for capturing JSON context + HTML section hashes
- `scripts/compare_reference_snapshots.py` - CLI for comparing current vs baseline snapshots
- `tests/extract/test_xbrl_cross_validation.py` - 8 tests for discrepancy flagging
- `tests/test_reference_snapshots.py` - 7 tests for snapshot capture/comparison
- `.planning/baselines/.gitkeep` - Empty baseline directory
- `.gitignore` - Exclude machine-specific baseline JSONs

## Decisions Made
- reconcile_value returns 3-tuple to carry DiscrepancyWarning objects alongside string messages (minimal API change, all callers are internal)
- Fixed pre-existing bug reference: extract/__init__.py had `recon.llm_wins` but ReconciliationReport field is `llm_fallbacks` -- corrected to `llm_fallbacks` in the pipeline_metadata dict
- XBRL=0 + LLM nonzero uses float("inf") ratio since division by zero is undefined

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed recon.llm_wins reference in extract/__init__.py**
- **Found during:** Task 1 (wiring extract stage)
- **Issue:** `state.pipeline_metadata["xbrl_reconciliation"]` referenced `recon.llm_wins` but the field is `llm_fallbacks`
- **Fix:** Changed to `recon.llm_fallbacks` in the metadata dict
- **Files modified:** src/do_uw/stages/extract/__init__.py
- **Committed in:** 827a4533 (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Bug fix was necessary for correct pipeline metadata. No scope creep.

## Issues Encountered
- Pre-existing test failure in tests/brain/test_brain_contract.py (ohlson_o_score threshold_provenance.source 'academic' not in valid sources) -- unrelated to this plan, not fixed.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 128 infrastructure foundation is now complete (all 3 plans done)
- Discrepancy flagging ready for production pipeline runs
- Reference snapshot tooling ready for use -- run `uv run python scripts/capture_reference_snapshots.py` after next full pipeline run to establish baselines
- Baselines directory empty until snapshots are captured post-Phase 128

---
*Phase: 128-infrastructure-foundation*
*Completed: 2026-03-22*
