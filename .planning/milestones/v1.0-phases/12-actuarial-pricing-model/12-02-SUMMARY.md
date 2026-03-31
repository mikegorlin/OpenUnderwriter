---
phase: 12-actuarial-pricing-model
plan: 02
subsystem: scoring
tags: [ilf, power-curve, layer-pricing, market-calibration, credibility-weighting, actuarial]

# Dependency graph
requires:
  - phase: 12-01
    provides: "compute_expected_loss, ExpectedLoss/LayerSpec/LayerPricing/CalibratedPricing/ActuarialPricing models, actuarial.json config"
provides:
  - "ILF power curve layer pricing (compute_ilf, price_tower_layers)"
  - "Market calibration with credibility weighting (calibrate_against_market)"
  - "Full actuarial pricing orchestrator (build_actuarial_pricing)"
affects: ["12-03", "render-pricing-section", "score-stage-integration"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ILF power curve: (L/B)^alpha for loss allocation across tower layers"
    - "Credibility weighting: z = min(1, sqrt(n/standard)) for model-market blend"
    - "Duck-typed MarketPosition via getattr for runtime decoupling from pricing_analytics"

key-files:
  created:
    - "src/do_uw/stages/score/actuarial_layer_pricing.py"
    - "src/do_uw/stages/score/actuarial_pricing_builder.py"
    - "tests/test_actuarial_layer_pricing.py"
  modified: []

key-decisions:
  - "Split into actuarial_layer_pricing.py (402L) + actuarial_pricing_builder.py (233L) for 500-line compliance"
  - "get_alpha public (not _get_alpha) for cross-module use by builder"
  - "load_tower_structure public (not _load_tower_structure) for builder access"
  - "Named helper functions (_find_primary, _find_excess, _find_side_a) instead of lambdas for pyright strict"
  - "Side A layers priced at primary attachment (factor=1.0) not ILF excess"

patterns-established:
  - "ILF tower pricing: compute_ilf -> _compute_layer_factor -> price_tower_layers pipeline"
  - "Credibility-weighted calibration: z=min(1,sqrt(n/std)), blend = z*market + (1-z)*model"
  - "Duck-typed MarketPosition via getattr for runtime type flexibility"

# Metrics
duration: 7min
completed: 2026-02-10
---

# Phase 12 Plan 02: ILF Layer Pricing and Market Calibration Summary

**ILF power curve allocates expected loss across 5-layer D&O tower with credibility-weighted market calibration**

## Performance

- **Duration:** 7 min
- **Started:** 2026-02-10T05:42:34Z
- **Completed:** 2026-02-10T05:49:21Z
- **Tasks:** 1 (TDD: RED + GREEN phases)
- **Files created:** 3

## Accomplishments
- ILF power curve implementation: ILF(L) = (L/B)^alpha correctly allocates loss across tower
- Primary factor = 1.0, excess factors decrease monotonically up the tower
- Premium = expected_loss / target_loss_ratio with configurable ratios per layer type
- Market calibration blends model ROL with market ROL via credibility weight z = min(1, sqrt(n/standard))
- build_actuarial_pricing orchestrates: expected loss -> tower pricing -> calibration -> ActuarialPricing
- 17 comprehensive TDD tests covering all functions and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Failing tests** - `7b07188` (test)
2. **Task 1 GREEN: Implementation** - `a652456` (feat)

**Plan metadata:** (pending)

_Note: TDD task with RED + GREEN commits._

## Files Created/Modified
- `src/do_uw/stages/score/actuarial_layer_pricing.py` (402L) - ILF computation, layer factors, tower pricing, market calibration, tower structure loader
- `src/do_uw/stages/score/actuarial_pricing_builder.py` (233L) - build_actuarial_pricing orchestrator, tower description, assumptions builder
- `tests/test_actuarial_layer_pricing.py` (452L) - 17 tests: ILF, layer factors, tower pricing, calibration, orchestrator

## Decisions Made
- Split into two files for 500-line compliance (actuarial_layer_pricing 402L + actuarial_pricing_builder 233L)
- Made get_alpha and load_tower_structure public (no underscore) since builder needs them cross-module
- Used named helper functions instead of lambdas in _build_tower_description for pyright strict compatibility
- Side A layers use factor=1.0 (priced at primary attachment), not ILF excess curve
- Duck-typed MarketPosition via getattr() at runtime to avoid import dependency on pricing_analytics

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Split for 500-line compliance**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Initial implementation was 619 lines in one file, exceeding 500-line limit
- **Fix:** Split into actuarial_layer_pricing.py (402L) + actuarial_pricing_builder.py (233L)
- **Files created:** actuarial_pricing_builder.py
- **Verification:** Both files under 500 lines, all tests pass
- **Committed in:** a652456

---

**Total deviations:** 1 auto-fixed (1 missing critical - 500-line compliance)
**Impact on plan:** Essential for code quality rules. No scope creep.

## Issues Encountered
- Pyright strict rejected lambdas passed to a generic `_find_first(predicate: Any)` helper due to Unknown parameter type. Resolved by replacing with named helper functions (_find_primary, _find_excess, _find_side_a) per project pattern.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Expected loss -> layer pricing -> calibration pipeline complete
- Plan 12-03 (score stage integration) can wire build_actuarial_pricing into the ScoreStage pipeline
- 1683 tests passing, 0 lint/type errors
- All files under 500 lines

---
*Phase: 12-actuarial-pricing-model*
*Completed: 2026-02-10*
