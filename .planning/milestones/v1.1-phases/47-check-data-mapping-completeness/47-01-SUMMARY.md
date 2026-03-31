---
phase: 47-check-data-mapping-completeness
plan: "01"
subsystem: testing
tags: [regression-baseline, wave0-scaffolds, check-audit, def14a, threshold-context]

# Dependency graph
requires:
  - phase: 46-brain-driven-gap-search
    provides: gap_bucket classifications in brain YAML for all 68 SKIPPED checks
provides:
  - 47-baseline.json regression snapshot (AAPL 24T/68S, RPM 14T/60S)
  - 47-reaudit-report.md classifying all 68 SKIPPED checks into 4 populations
  - Wave 0 RED test scaffolds for Plans 47-02, 47-03, 47-04
  - Zero-tolerance regression anchor: AAPL triggered=24 must not increase
affects:
  - 47-02 threshold_context routing (test_threshold_context.py must turn GREEN)
  - 47-03 field routing fixes (FIELD_FOR_CHECK entries for population C+D checks)
  - 47-04 DEF 14A schema expansion (test_def14a_schema.py must turn GREEN)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Wave 0 scaffold pattern: write RED tests before implementation plans begin
    - Regression baseline JSON: capture triggered/skipped counts per company before changes
    - Re-audit-then-report: classify SKIPPED population before writing routing code

key-files:
  created:
    - .planning/phases/47-check-data-mapping-completeness/47-baseline.json
    - .planning/phases/47-check-data-mapping-completeness/47-reaudit-report.md
    - tests/stages/analyze/test_threshold_context.py
    - tests/stages/analyze/test_regression_baseline.py
    - tests/stages/extract/test_def14a_schema.py
  modified: []

key-decisions:
  - "68 SKIPPED checks break into 4 populations: 20 truly unmapped (A), 34 fixable via DEF 14A expansion (B), 12 routing gaps (C), 2 explicit routing-gap bucket (D)"
  - "Target SKIPPED floor after Phase 47: ~20-22 checks (Population A only)"
  - "EXEC.CEO/CFO.risk_score are post-analysis artifacts — no routing, ever"
  - "13x FWRD.WARN.* require external APIs — marked intentionally-unmapped, not fixable in Phase 47"
  - "GOV.EFFECT.iss_score and proxy_advisory are ISS proprietary — marked intentionally-unmapped"
  - "NLP.FILING.* require SEC metadata layer not in ExtractedData — marked intentionally-unmapped"
  - "FWRD.NARRATIVE.* require LLM comparison capability not yet built — marked intentionally-unmapped"
  - "Wave 0 test_threshold_context.py fails with AttributeError (no field yet) — correct RED state"
  - "Wave 0 test_def14a_schema.py fails with AttributeError (no new fields yet) — correct RED state"
  - "Wave 0 test_regression_baseline.py passes all 4 tests — baseline artifact confirmed valid"

patterns-established:
  - "Wave 0 scaffold pattern: create failing tests that define expected behavior BEFORE implementation plans run"
  - "Baseline JSON pattern: capture TRIGGERED/SKIPPED counts as JSON artifact before any routing changes"
  - "Re-audit before routing: classify the full SKIPPED population into fixable vs intentionally-unmapped before writing code"

requirements-completed: [MAP-01, MAP-02, MAP-03]

# Metrics
duration: 401s
completed: 2026-02-25
---

# Phase 47 Plan 01: Check Re-Audit and Wave 0 Test Scaffolds Summary

**Regression baseline captured (AAPL: 24T/68S, RPM: 14T/60S), 68 SKIPPED checks classified into 4 populations, and three Wave 0 RED test scaffold files created before any Phase 47 routing changes begin**

## Performance

- **Duration:** 6m 41s
- **Started:** 2026-02-26T00:52:01Z
- **Completed:** 2026-02-26T00:58:42Z
- **Tasks:** 2
- **Files modified:** 5 created, 0 modified

## Accomplishments

- Captured regression baseline: AAPL (24 triggered, 68 skipped, 110 clear, 201 info), RPM (14 triggered, 60 skipped, 122 clear, 197 info) — saved as 47-baseline.json
- Re-audited all 68 SKIPPED checks with brain YAML gap_bucket lookup — classified into 4 actionable populations with intentionally-unmapped decisions documented
- Created 3 Wave 0 RED test scaffolds: threshold_context (5 tests, AttributeError), regression baseline (4 tests, all pass), DEF14A schema (7 tests, AttributeError)
- Zero new regressions: 478 pre-existing tests still pass

## Task Commits

Each task was committed atomically:

1. **Task 1: Re-audit SKIPPED checks and capture regression baseline** - `0d7ed5a` (feat)
2. **Task 2: Create Wave 0 test scaffolds** - `e5a86f7` (test)

## Files Created/Modified

- `.planning/phases/47-check-data-mapping-completeness/47-baseline.json` — Regression snapshot: AAPL/RPM triggered+skipped counts before Phase 47 changes
- `.planning/phases/47-check-data-mapping-completeness/47-reaudit-report.md` — Full 68-check re-audit with 4 populations and intentionally-unmapped rationale
- `tests/stages/analyze/test_threshold_context.py` — Wave 0 scaffold for QA-03: 5 RED tests verifying CheckResult.threshold_context field existence and _apply_traceability() population
- `tests/stages/analyze/test_regression_baseline.py` — Wave 0 scaffold for MAP-01/MAP-02: 4 PASSING tests loading 47-baseline.json and verifying AAPL counts
- `tests/stages/extract/test_def14a_schema.py` — Wave 0 scaffold for MAP-03: 7 RED tests verifying new DEF14AExtraction fields and convert_board_profile() signature

## Decisions Made

- **68 SKIPPED checks → 4 populations:**
  - Population A (20): Truly intentionally unmapped — external APIs (13x FWRD.WARN.*), ISS proprietary (2), LLM comparison not built (2), post-analysis artifacts (2), SEC metadata not in ExtractedData (2). No routing ever.
  - Population B (34): Fixable via DEF 14A extraction expansion (Plan 47-04) — board composition (9), governance rights (10), compensation (7), executive profile (4), governance effectiveness (4)
  - Population C (12): Routing gap — field exists or can be computed, no FIELD_FOR_CHECK entry (Plans 47-02/47-03)
  - Population D (2): Explicit routing-gap bucket from Phase 46 — FIN.ACCT.restatement_stock_window, LIT.PATTERN.peer_contagion

- **Target SKIPPED floor after Phase 47: ~20-22 checks** (Population A only)

- **Wave 0 failure modes confirmed correct:**
  - test_threshold_context.py: AttributeError on `threshold_context` attribute — correct, field doesn't exist yet
  - test_def14a_schema.py: AttributeError on new DEF14A fields — correct, fields don't exist yet
  - test_regression_baseline.py: all 4 pass — correct, baseline JSON was created in Task 1

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed CheckResult constructor calls missing required `check_name` field**
- **Found during:** Task 2 (test scaffold creation)
- **Issue:** Plan's code snippets called `CheckResult(check_id="TEST.CHECK", status=...)` but `check_name` is a required Pydantic field with no default. Tests were failing with ValidationError instead of AttributeError.
- **Fix:** Added `check_name="Test Check"` / `check_name="Board Tenure"` to all CheckResult constructor calls in test_threshold_context.py
- **Files modified:** tests/stages/analyze/test_threshold_context.py
- **Verification:** Tests now fail with AttributeError on `threshold_context` (correct RED state), not ValidationError
- **Committed in:** `e5a86f7` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 bug fix)
**Impact on plan:** Required for tests to fail for the correct reason. No scope creep.

## Issues Encountered

- RPM state.json was found (output/RPM/state.json) — included in baseline as planned. TSLA state.json was not found — omitted per plan instructions.

## Next Phase Readiness

- 47-baseline.json provides unambiguous zero-tolerance regression anchor for all later plans
- 47-reaudit-report.md provides exact task lists for Plans 47-02, 47-03, 47-04
- Wave 0 test scaffolds ensure Nyquist coverage exists before implementation begins
- Plans 47-02, 47-03, 47-04 can proceed in any order within Wave 1

---
*Phase: 47-check-data-mapping-completeness*
*Completed: 2026-02-25*
