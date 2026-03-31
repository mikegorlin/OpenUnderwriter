---
phase: 12-actuarial-pricing-model
verified: 2026-02-10T06:00:02Z
status: passed
score: 14/14 must-haves verified
re_verification: false
---

# Phase 12: Actuarial Pricing Model Verification Report

**Phase Goal:** Build a credible actuarial loss model that predicts what D&O coverage should cost based on risk scoring output, historical claims data, and market pricing — moving from "here's the risk" to "here's what it should cost"

**Verified:** 2026-02-10T06:00:02Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| **Plan 12-01** | | | |
| 1 | Expected loss = filing_probability * median_severity * (1 + defense_cost_pct) | ✓ VERIFIED | Lines 192-194 of actuarial_model.py: `expected_indemnity = filing_probability * median_severity`, `expected_defense = expected_indemnity * defense_cost_pct`, `total_expected = expected_indemnity + expected_defense` |
| 2 | Scenario losses computed at 25th/50th/75th/95th percentiles | ✓ VERIFIED | Lines 106-128 of actuarial_model.py: `_compute_scenario_losses()` iterates `_SCENARIO_PERCENTILES = [25, 50, 75, 95]` |
| 3 | Returns has_data=False gracefully when inputs are missing | ✓ VERIFIED | Lines 169-174, 178-183 of actuarial_model.py: returns `ExpectedLoss(has_data=False)` for missing scenarios or median |
| 4 | All parameters read from actuarial.json config, none hardcoded | ✓ VERIFIED | Lines 59-88 of actuarial_model.py: `_get_defense_cost_pct()` reads from config; Lines 161-165: model_label from config; actuarial.json contains all defense_cost_factors, ilf_parameters, loss_ratio_targets |
| **Plan 12-02** | | | |
| 5 | ILF power curve allocates total expected loss across tower layers | ✓ VERIFIED | Lines 42-57 of actuarial_layer_pricing.py: `compute_ilf()` implements `(limit / basic_limit) ** alpha`; Lines 189-193: `layer_el = layer_factor * total_el` |
| 6 | Primary layer gets factor 1.0, excess layers get decreasing factors via (L/B)^alpha | ✓ VERIFIED | Lines 80-85 of actuarial_layer_pricing.py: `if attachment <= 0: return 1.0` (primary); excess: `ilf_top - ilf_bottom` |
| 7 | Premium = expected_loss / target_loss_ratio for each layer | ✓ VERIFIED | Line 200 of actuarial_layer_pricing.py: `indicated_premium = layer_el / target_lr if target_lr > 0 else 0.0` |
| 8 | Market calibration blends model and market ROL via credibility weight z = min(1, sqrt(n/standard)) | ✓ VERIFIED | Lines 325 of actuarial_layer_pricing.py: `z = min(1.0, sqrt(n / float(standard)))`; Line 328: `calibrated_rol = z * float(market_rol) + (1.0 - z) * model_rol` |
| 9 | Returns empty results gracefully when expected_loss.has_data is False | ✓ VERIFIED | Lines 170-171 of actuarial_layer_pricing.py: `if not expected_loss.has_data or not tower_structure: return []` |
| **Plan 12-03** | | | |
| 10 | Running the pipeline produces actuarial_pricing on state.scoring for any analyzed company | ✓ VERIFIED | Line 365 of benchmark/__init__.py: `scoring.actuarial_pricing = result`; integration tests confirm pipeline produces actuarial_pricing |
| 11 | Actuarial pricing is computed in BENCHMARK stage after inherent risk and severity exist | ✓ VERIFIED | Lines 210-211 of benchmark/__init__.py: Step 7 runs `_enrich_actuarial_pricing()` after inherent risk (Step 4) and uses `scoring.severity_scenarios` from SCORE |
| 12 | Missing scoring data or severity scenarios produces actuarial_pricing=None, not errors | ✓ VERIFIED | Lines 307-314 of benchmark/__init__.py: guards with `if severity is None: return`; Lines 380-384: try/except catches errors; test_no_severity_skips_actuarial verifies this |
| 13 | Market calibration is applied when PricingStore has data for the segment | ✓ VERIFIED | Lines 329-342 of benchmark/__init__.py: builds `_MarketPositionProxy` from `market_intelligence` when available; Lines 99-106 of actuarial_pricing_builder.py: calls `calibrate_against_market()` when `market_position is not None` |
| 14 | All existing tests still pass (non-breaking addition) | ✓ VERIFIED | Full test suite: 1689 passed (33 new tests), 4 warnings, 0 failures |

**Score:** 14/14 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| **Plan 12-01** | | | |
| `src/do_uw/config/actuarial.json` | All actuarial model parameters | ✓ VERIFIED | 47 lines, contains defense_cost_factors, ilf_parameters, loss_ratio_targets, expense_loads, credibility, default_tower, model_label |
| `src/do_uw/models/scoring_output.py` | ActuarialPricing Pydantic model | ✓ VERIFIED | Contains ScenarioLoss (L321), ExpectedLoss (L339), LayerSpec (L374), LayerPricing (L385), CalibratedPricing (L414), ActuarialPricing (L442) |
| `src/do_uw/stages/score/actuarial_model.py` | Expected loss computation | ✓ VERIFIED | 223 lines, exports `compute_expected_loss`, implements frequency-severity model |
| `tests/test_actuarial_model.py` | Tests for expected loss | ✓ VERIFIED | 235 lines (>80 required), 8 test cases all passing |
| **Plan 12-02** | | | |
| `src/do_uw/stages/score/actuarial_layer_pricing.py` | ILF layer pricing and market calibration | ✓ VERIFIED | 402 lines, exports `price_tower_layers`, `calibrate_against_market`, `compute_ilf`, `get_alpha`, `load_tower_structure` |
| `src/do_uw/stages/score/actuarial_pricing_builder.py` | Orchestrator function | ✓ VERIFIED | 233 lines, exports `build_actuarial_pricing` (split for 500-line compliance) |
| `tests/test_actuarial_layer_pricing.py` | Tests for ILF and calibration | ✓ VERIFIED | 452 lines (>100 required), 17 test cases all passing |
| **Plan 12-03** | | | |
| `src/do_uw/stages/benchmark/__init__.py` | Actuarial pricing integration | ✓ VERIFIED | 388 lines, contains `_enrich_actuarial_pricing` method (L285-384) |
| `tests/test_actuarial_integration.py` | Integration tests | ✓ VERIFIED | 375 lines (>60 required), 6 test cases all passing |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| actuarial_model.py | scoring_output.py | imports ActuarialPricing models | ✓ WIRED | Lines 20-24: imports ExpectedLoss, ScenarioLoss, SeverityScenarios |
| actuarial_model.py | actuarial.json | reads defense_cost_factors | ✓ WIRED | Lines 59-88: `_get_defense_cost_pct()` reads from config dict |
| actuarial_layer_pricing.py | actuarial_model.py | imports compute_expected_loss | ✓ WIRED | actuarial_pricing_builder.py L28 imports and calls compute_expected_loss |
| actuarial_layer_pricing.py | actuarial.json | reads ilf_parameters, loss_ratio_targets | ✓ WIRED | Lines 101-122, 196-197, 321: reads from actuarial_config dict |
| actuarial_pricing_builder.py | actuarial_layer_pricing.py | orchestrates pricing pipeline | ✓ WIRED | Lines 22-27: imports; Lines 70-106: calls compute_expected_loss → price_tower_layers → calibrate_against_market |
| benchmark/__init__.py | actuarial_pricing_builder.py | lazy import of build_actuarial_pricing | ✓ WIRED | Lines 303-305: lazy import; Lines 355-363: calls build_actuarial_pricing |
| benchmark/__init__.py | scoring.py | sets state.scoring.actuarial_pricing | ✓ WIRED | Line 365: `scoring.actuarial_pricing = result`; scoring.py L235: actuarial_pricing field exists |

### Anti-Patterns Found

No anti-patterns detected. All files are substantive implementations with:
- No TODO/FIXME/placeholder comments
- No hardcoded values (all config-driven)
- No stub implementations
- Proper error handling and graceful degradation
- Clear logging of model outputs

### Code Quality Checks

| Check | Status | Details |
|-------|--------|---------|
| Line count limits | ✓ PASS | actuarial_model.py: 223L, actuarial_layer_pricing.py: 402L, actuarial_pricing_builder.py: 233L, benchmark/__init__.py: 388L — all under 500L |
| Ruff lint | ✓ PASS | All checks passed on all actuarial files |
| Pyright type check | ✓ PASS | 0 errors, 0 warnings, 0 informations |
| Test coverage | ✓ PASS | 31 actuarial tests: 8 model + 17 layer pricing + 6 integration, all passing |
| Full test suite | ✓ PASS | 1689 passed (baseline 1656 + 33 new), 0 failed |

## Detailed Formula Verification

### Expected Loss Computation (Plan 12-01)

**Formula implemented (actuarial_model.py:192-194):**
```python
expected_indemnity = filing_probability * median_severity
expected_defense = expected_indemnity * defense_cost_pct
total_expected = expected_indemnity + expected_defense
```

**Test verification:**
- Filing prob 7.68%, median $27M, defense 20%
- Expected indemnity = 0.0768 * 27,000,000 = $2,073,600
- Expected defense = $2,073,600 * 0.20 = $414,720
- Total = $2,488,320
- Test passes: `test_expected_loss_basic` ✓

**Scenario computation:**
- 4 scenarios computed: 25th, 50th, 75th, 95th percentiles
- Each scenario: `expected_indemnity = prob * severity_at_percentile`
- Test passes: `test_scenario_losses_computed` ✓

### ILF Power Curve (Plan 12-02)

**ILF formula (actuarial_layer_pricing.py:57):**
```python
return (limit / basic_limit) ** alpha
```

**Layer factor formula (actuarial_layer_pricing.py:83-85):**
```python
ilf_top = compute_ilf(attachment + layer_limit, basic_limit, alpha)
ilf_bottom = compute_ilf(attachment, basic_limit, alpha)
return ilf_top - ilf_bottom
```

**Test verification:**
- ILF(20M, 10M, 0.40) = (20/10)^0.40 = 2^0.40 = 1.3195
- Test passes: `test_compute_ilf_excess` ✓
- First excess (10xs10) factor = ILF(20M) - ILF(10M) = 1.3195 - 1.0 = 0.3195
- Test passes: `test_compute_layer_factor_first_excess` ✓
- Factors decrease monotonically up the tower
- Test passes: `test_compute_layer_factor_decreasing` ✓

### Premium Derivation (Plan 12-02)

**Premium formula (actuarial_layer_pricing.py:200):**
```python
indicated_premium = layer_el / target_lr if target_lr > 0 else 0.0
```

**ROL formula (actuarial_layer_pricing.py:203):**
```python
indicated_rol = indicated_premium / spec.limit if spec.limit > 0 else 0.0
```

**Test verification:**
- Premium = expected_loss / loss_ratio
- Test passes: `test_premium_equals_loss_div_lr` ✓
- ROL = premium / limit
- Test passes: `test_rol_equals_premium_div_limit` ✓

### Market Calibration (Plan 12-02)

**Credibility weight (actuarial_layer_pricing.py:325):**
```python
z = min(1.0, sqrt(n / float(standard)))
```

**Blend formula (actuarial_layer_pricing.py:328):**
```python
calibrated_rol = z * float(market_rol) + (1.0 - z) * model_rol
```

**Test verification:**
- n=25, standard=50 → z=sqrt(0.5)=0.707
- Test passes: `test_calibrate_with_market` ✓
- n=100 >= standard=50 → z=1.0 (full credibility)
- Test passes: `test_calibrate_full_credibility` ✓
- Insufficient market data → returns model-only
- Test passes: `test_calibrate_no_market` ✓

### Pipeline Integration (Plan 12-03)

**Integration flow verified:**
1. BenchmarkStage Step 4 computes `inherent_risk.company_adjusted_rate_pct` (filing probability)
2. SCORE stage already computed `scoring.severity_scenarios` (from Phase 6)
3. BenchmarkStage Step 7 calls `_enrich_actuarial_pricing()`:
   - Loads actuarial.json config
   - Extracts sector, market_cap_tier
   - Builds market_position proxy from market_intelligence (if available)
   - Calls `build_actuarial_pricing()` orchestrator
   - Sets `scoring.actuarial_pricing = result`
4. Non-breaking: try/except wraps all logic, missing severity returns early

**Integration tests pass:**
- `test_produces_actuarial_pricing` ✓ — full pipeline produces actuarial_pricing
- `test_no_severity_skips_actuarial` ✓ — graceful degradation
- `test_graceful_on_error` ✓ — exception handling works
- `test_layer_rols_decrease` ✓ — ROLs decrease from primary → excess (key property)
- `test_assumptions_populated` ✓ — metadata tracked
- `test_tower_structure_described` ✓ — human-readable description

## Requirements Coverage

Phase 12 does not map to any original requirements (this was out-of-scope "Premium pricing calculator" in the original spec, added as a later-stage enhancement per ROADMAP.md note).

No requirements to verify.

## Summary

**Phase goal ACHIEVED:** The system now produces credible actuarial pricing that moves from "here's the risk" to "here's what it should cost."

**All 14 must-haves verified:**
- ✓ Expected loss formula correctly implements frequency × severity + defense costs
- ✓ Scenario losses computed at all 4 percentiles (25/50/75/95)
- ✓ Graceful degradation when inputs missing (has_data=False)
- ✓ All parameters config-driven (actuarial.json), zero hardcoding
- ✓ ILF power curve correctly allocates loss across tower
- ✓ Primary factor = 1.0, excess factors decrease via (L/B)^alpha
- ✓ Premium = expected_loss / loss_ratio for each layer
- ✓ Market calibration via credibility weighting z = min(1, sqrt(n/standard))
- ✓ Pipeline integration in BENCHMARK stage after inherent risk computed
- ✓ Market calibration applied when market intelligence available
- ✓ Missing data produces None, not errors (non-breaking)
- ✓ All 1656 existing tests still pass + 33 new tests

**Code quality:** All files under 500 lines, ruff clean, pyright clean, comprehensive test coverage.

**Formulas verified:** Expected loss, ILF power curve, premium derivation, market calibration all match actuarial specifications and pass numerical tests.

**Non-breaking integration:** Pipeline completes normally when actuarial inputs unavailable, enriches state when data exists.

---

_Verified: 2026-02-10T06:00:02Z_
_Verifier: Claude (gsd-verifier)_
