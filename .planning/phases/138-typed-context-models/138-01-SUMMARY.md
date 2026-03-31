---
phase: 138-typed-context-models
plan: 01
subsystem: render
tags: [pydantic, context-models, type-safety, validation]

# Dependency graph
requires:
  - phase: 137-canonical-metrics-registry
    provides: MetricValue/CanonicalMetrics models referenced by context builders
provides:
  - 5 Pydantic BaseModel classes for exec_summary, financial, market, governance, litigation context builders
  - _validate_context wrapper function with fallback to untyped dicts
  - Real-state integration tests against 3 tickers (AAPL, RPM, ULS)
affects: [138-02, 142-quality-gates]

# Tech tracking
tech-stack:
  added: []
  patterns: [typed-context-models, validation-wrapper-fallback, extra-allow-migration]

key-files:
  created:
    - src/do_uw/stages/render/context_models/__init__.py
    - src/do_uw/stages/render/context_models/exec_summary.py
    - src/do_uw/stages/render/context_models/financial.py
    - src/do_uw/stages/render/context_models/market.py
    - src/do_uw/stages/render/context_models/governance.py
    - src/do_uw/stages/render/context_models/litigation.py
    - src/do_uw/stages/render/context_models/validation.py
    - tests/stages/render/test_context_models.py
  modified: []

key-decisions:
  - "All models use extra='allow' (not 'forbid') during migration -- evaluative helpers add unknown keys"
  - "Union types (dict|str, list|dict) used where builders return varying types across tickers"
  - "_validate_context returns raw dict unchanged on empty input (same object, no copy)"

patterns-established:
  - "Typed context model pattern: one Pydantic BaseModel per builder, all fields Optional with defaults"
  - "Validation wrapper pattern: try model_validate/model_dump, catch ValidationError, return raw"
  - "extra='allow' migration pattern: start permissive, tighten to 'forbid' after full key coverage"

requirements-completed: [TYPE-01, TYPE-02, TYPE-03, TYPE-04]

# Metrics
duration: 4min
completed: 2026-03-27
---

# Phase 138 Plan 01: Typed Context Models Summary

**5 Pydantic context models (250+ typed fields) with validation wrapper and real-state tests against AAPL, RPM, and ULS**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-27T23:22:30Z
- **Completed:** 2026-03-27T23:26:30Z
- **Tasks:** 1
- **Files created:** 8

## Accomplishments
- Defined Pydantic BaseModel for all 5 highest-leakage context builders with 250+ total typed fields
- Created _validate_context wrapper with try/except fallback that never breaks the render pipeline
- All 34 tests pass including real state.json round-trips for 3 tickers

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests** - `30263869` (test)
2. **Task 1 (GREEN): Implement models + validation** - `08d4fa51` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/context_models/__init__.py` - Package re-exporting all 5 models + _validate_context
- `src/do_uw/stages/render/context_models/exec_summary.py` - ExecSummaryContext with 14 fields + 4 sub-models
- `src/do_uw/stages/render/context_models/financial.py` - FinancialContext with 80+ fields
- `src/do_uw/stages/render/context_models/market.py` - MarketContext with 60+ fields
- `src/do_uw/stages/render/context_models/governance.py` - GovernanceContext with 60+ fields
- `src/do_uw/stages/render/context_models/litigation.py` - LitigationContext with 40+ fields + 3 sub-models
- `src/do_uw/stages/render/context_models/validation.py` - _validate_context wrapper function
- `tests/stages/render/test_context_models.py` - 34 tests (empty dict, extra allow, field counts, fallback, real state)

## Decisions Made
- Used `extra="allow"` on all models (not `"forbid"`) because evaluative helpers add keys via `result.update()` that are not yet fully enumerated in models
- Used union types (`dict[str, Any] | str | None`) for 5 fields where builder output varies by ticker (debt_service_coverage, z_trajectory, piotroski_components, earnings_quality_detail, tax_risk, committee_detail, workforce_product_env)
- Sub-models created for well-defined nested structures (SnapshotContext, ClaimProbability, TowerRecommendation, InherentRisk, FindingDetail, LitigationDashboard, SecEnforcement, SolAnalysis)
- Derivative suits typed as `list[dict[str, Any]]` (not `list[dict[str, str]]`) because settlement field can be None

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed 5 type mismatches in FinancialContext discovered during real-state testing**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** debt_service_coverage is actually a dict (not str), z_trajectory is a list (not dict), piotroski_components is a list (not dict), earnings_quality_detail can be dict or str, tax_risk can be dict or str
- **Fix:** Changed to union types that accept both possible shapes
- **Files modified:** src/do_uw/stages/render/context_models/financial.py
- **Verification:** All 34 tests pass including 3 real state files

**2. [Rule 1 - Bug] Fixed committee_detail type in GovernanceContext**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** committee_detail is a dict (not list) in real builder output
- **Fix:** Changed to `dict[str, Any] | list[dict[str, Any]] | None`
- **Files modified:** src/do_uw/stages/render/context_models/governance.py

**3. [Rule 1 - Bug] Fixed derivative_suits and workforce_product_env types in LitigationContext**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** derivative_suits has None values (not just str), workforce_product_env is a dict (not list)
- **Fix:** Changed to `list[dict[str, Any]]` and `dict[str, Any] | list[dict[str, str]]`
- **Files modified:** src/do_uw/stages/render/context_models/litigation.py

---

**Total deviations:** 3 auto-fixed (all Rule 1 - type mismatch bugs)
**Impact on plan:** All fixes necessary for correctness. Real state data revealed type variations not documented in research. No scope creep.

## Issues Encountered
None beyond the type mismatches documented above.

## Known Stubs
None - all models are fully defined with real field types validated against production data.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All 5 context models ready for Plan 02 to wire _validate_context into md_renderer.py
- Models validated against real pipeline output for 3 tickers
- _validate_context wrapper provides safe fallback during integration

## Self-Check: PASSED

- All 8 created files verified present on disk
- Both commit hashes (30263869, 08d4fa51) found in git log

---
*Phase: 138-typed-context-models*
*Completed: 2026-03-27*
