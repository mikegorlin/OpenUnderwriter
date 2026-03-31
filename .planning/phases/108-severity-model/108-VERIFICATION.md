---
phase: 108-severity-model
verified: 2026-03-16T02:10:00Z
status: passed
score: 5/5 must-haves verified
re_verification: false
---

# Phase 108: Severity Model Verification Report

**Phase Goal:** Implement damages estimation and settlement prediction so the worksheet shows probability and severity independently with expected loss computation
**Verified:** 2026-03-16T02:10:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Damages estimation computed from market cap, class period return, and shares traded | VERIFIED | `damages_estimation.py:99` — `return market_cap * abs(class_period_return) * min(turnover_rate, 1.0)` |
| 2 | Settlement percentile regression produces estimate from SCAC/Cornerstone filing features (sector, market cap, allegation type, jurisdiction, lead plaintiff) | VERIFIED | `settlement_regression.py` — 12-feature log-linear model with published Cornerstone/NERA coefficients; `build_feature_vector()` extracts all required features from AnalysisState |
| 3 | Severity amplifiers defined in YAML with epistemology (media notoriety, jurisdiction, fraud type, government investigation) — each amplifier has a documented basis | VERIFIED | `severity_model_design.yaml` has 11 amplifiers in `severity_amplifiers.catalog`; `severity_amplifiers.py` loads, evaluates signal-driven firing, combines multiplicatively with 3.0 cap |
| 4 | Probability displayed independently from severity — expected loss P x S available as a computed field | VERIFIED | `SeverityResult` (models/severity.py:226-234) has independent `probability: float`, `severity: float`, `expected_loss: float` fields; P from `hae_result.product_score`, S from primary settlement estimate |
| 5 | P x S matrix visualization renders as a chart showing risk positioning | VERIFIED | `pxs_matrix_chart.py` renders matplotlib chart with log-scale Y ($100K-$10B), linear X (0-1), 4 colored zone Rectangle patches, primary dot + scenario range bar, optional Liberty attachment line |

**Score: 5/5 truths verified**

---

### Required Artifacts

#### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|---------|--------|---------|
| `src/do_uw/models/severity.py` | SeverityResult, AmplifierResult, LayerErosionResult, ScenarioSeverity Pydantic models | VERIFIED | 245 lines; exports all 6 required classes; zone_for() classmethod on SeverityZone |
| `src/do_uw/stages/score/severity_lens.py` | SeverityLens Protocol + SeverityLensResult | VERIFIED | 39 lines; @runtime_checkable Protocol with evaluate() signature |
| `src/do_uw/stages/score/damages_estimation.py` | Base damages formula + allegation modifiers + scenario grid | VERIFIED | 242 lines; exports compute_base_damages, compute_scenario_grid, apply_allegation_modifier, compute_defense_costs, estimate_turnover_rate |
| `src/do_uw/stages/score/settlement_regression.py` | 12-feature log-linear regression with published coefficients | VERIFIED | 376 lines; exports predict_settlement_regression, build_feature_vector, predict_all_allegation_types, infer_primary_allegation_type |
| `src/do_uw/stages/score/severity_amplifiers.py` | Amplifier loading from YAML, signal-driven firing, combination | VERIFIED | 220 lines; exports load_amplifiers, evaluate_amplifiers, combine_amplifiers; loads from severity_model_design.yaml |
| `src/do_uw/stages/score/layer_erosion.py` | Log-normal layer penetration + ABC/Side A + DIC | VERIFIED | 288 lines; exports compute_layer_erosion, compute_side_a_erosion, compute_dic_probability; uses math.erfc (no scipy) |
| `src/do_uw/stages/score/legacy_severity_lens.py` | Legacy DDL wrapped as SeverityLens adapter | VERIFIED | 154 lines; LegacySeverityLens post-hoc adapter pattern |
| `src/do_uw/stages/score/_severity_runner.py` | Pipeline orchestrator for ScoreStage | VERIFIED | Present (not in original PLAN artifacts list but documented in SUMMARY); wires all severity modules into run_severity_model() |
| `tests/stages/score/test_severity_lens.py` | Tests for severity computation pipeline | VERIFIED | 535 lines; 35 tests; all pass |

#### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|---------|--------|---------|
| `src/do_uw/stages/score/severity_scoring.py` | SeverityScoringLens full orchestrator | VERIFIED | 432 lines; implements SeverityLens Protocol; exports SeverityScoringLens, compute_p_x_s, classify_zone, build_severity_result |
| `src/do_uw/stages/score/severity_calibration.py` | 20-case calibration report | VERIFIED | 280 lines; 20 landmark cases (Enron through Activision); generate_severity_calibration_report() produces HTML with MAE/bias/MSE error metrics |
| `src/do_uw/stages/render/charts/pxs_matrix_chart.py` | P x S matrix chart renderer | VERIFIED | 371 lines; render_pxs_matrix() exports PNG bytes; log-scale Y, 4 zone Rectangle patches, primary dot, range bar, annotation boxes |
| `src/do_uw/stages/render/context_builders/severity_context.py` | Severity context builder for worksheet | VERIFIED | 181 lines; build_severity_context() returns all required keys including dual amplifier views (fired-only + all-11-appendix) |
| `tests/stages/score/test_pxs_computation.py` | P x S computation tests | VERIFIED | 294 lines; 16 tests; all pass |
| `tests/stages/render/test_pxs_chart.py` | P x S chart + context builder tests | VERIFIED | 314 lines; 10 tests; all pass |

---

### Key Link Verification

| From | To | Via | Status | Detail |
|------|----|-----|--------|--------|
| `severity_amplifiers.py` | `severity_model_design.yaml` | YAML load of amplifier catalog | WIRED | Line 42: `/ "severity_model_design.yaml"` + line 69: `design.get("severity_amplifiers", {}).get("catalog", [])` |
| `severity_amplifiers.py` | signal_results dict | `_is_signal_triggered()` lookup | WIRED | Lines 102-129: checks status, triggered, fired fields; mirrors case_characteristics pattern |
| `settlement_regression.py` | `severity_model_design.yaml` | Published coefficient loading | WIRED | Line 40: `/ "severity_model_design.yaml"` + `_load_regression_coefficients()` |
| `layer_erosion.py` | damages_estimation.py (settlement distribution) | Log-normal CDF on median_settlement | WIRED | `compute_layer_erosion(median_settlement, sigma, attachment, ...)` — takes settlement distribution params directly |
| `severity_scoring.py` | `damages_estimation.py` | `compute_base_damages` call | WIRED | Lines 36, 192: direct import and call |
| `severity_scoring.py` | `settlement_regression.py` | `predict_settlement_regression` call | WIRED | Lines 48, 203: direct import and call |
| `severity_scoring.py` | `severity_amplifiers.py` | `evaluate_amplifiers` + `combine_amplifiers` | WIRED | Lines 51-52, 210-211: direct imports and calls |
| `severity_scoring.py` | `layer_erosion.py` | `compute_layer_erosion` call | WIRED | Lines 42, 409: direct import and call |
| `pxs_matrix_chart.py` | `chart_styles.yaml` | resolve_colors / chart_styles param | PARTIAL | chart_styles accepted as optional parameter; `chart_styles.yaml` has `pxs_matrix` entry added but chart does not call resolve_colors() — uses hardcoded zone colors. Functional, not blocking. |
| `severity_context.py` | `models/severity.py` | SeverityResult consumption | WIRED | Lines 54-174: accesses severity_result.primary, .probability, .severity, .expected_loss, .zone, .scenario_table |
| `ScoreStage.__init__.py` | `_severity_runner.run_severity_model` | Step 15.5 integration | WIRED | Lines 514-533: try/except import and call; graceful degradation on failure |
| `cli.py` | `--attachment` / `--product` | typer.Option → pipeline_config | WIRED | Lines 274-282: options defined; lines 380-381: passed to pipeline_config dict |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| SEV-01 | 108-01 | Damages estimation computed: market cap x class period return x shares traded | SATISFIED | `compute_base_damages()` in damages_estimation.py:99 |
| SEV-02 | 108-01 | Settlement percentile regression from SCAC/Cornerstone filing features | SATISFIED | `predict_settlement_regression()` with 12 features, published coefficients |
| SEV-03 | 108-01 | Severity amplifiers defined in YAML with epistemology | SATISFIED | 11 amplifiers in severity_model_design.yaml; signal-driven auto-fire |
| SEV-04 | 108-02 | Probability displayed independently from severity — P x S expected loss available | SATISFIED | SeverityResult.probability, .severity, .expected_loss as independent fields |
| SEV-05 | 108-02 | P x S matrix visualization (chart template) | SATISFIED | pxs_matrix_chart.py; chart_registry.yaml entry with section: risk_summary |

All 5 SEV requirements satisfied. No orphaned requirements found.

---

### Test Results

```
tests/stages/score/test_severity_lens.py   — 35 tests PASS
tests/stages/score/test_pxs_computation.py — 16 tests PASS
tests/stages/render/test_pxs_chart.py      — 10 tests PASS
Total: 61 severity-specific tests, 0 failures
```

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `settlement_regression.py` | 295 | `pass` inside if-branch for `auditor_change` feature | Info | Not a stub — a no-op placeholder comment inside a function that already sets `features["auditor_change"] = 0.0`. Auditor change always defaults to 0.0. Non-blocking. |
| `pxs_matrix_chart.py` | — | Does not call `resolve_colors()` despite chart_styles.yaml having pxs_matrix entry | Warning | Zone colors hardcoded in module constants (correct values). chart_styles.yaml `pxs_matrix` entry added but not consumed by resolve_colors pattern. Cosmetic inconsistency — chart works correctly. |

No blockers. No stubs. No empty implementations.

---

### File Size Compliance

All new source files under 500-line limit:

| File | Lines |
|------|-------|
| severity.py | 245 |
| severity_lens.py | 39 |
| damages_estimation.py | 242 |
| settlement_regression.py | 376 |
| severity_amplifiers.py | 220 |
| layer_erosion.py | 288 |
| legacy_severity_lens.py | 154 |
| severity_scoring.py | 432 |
| severity_calibration.py | 280 |
| pxs_matrix_chart.py | 371 |
| severity_context.py | 181 |

All within limit. (severity_calibration.py extracted from severity_scoring.py per anti-context-rot rule.)

---

### Commit Verification

All 8 SUMMARY-documented commits verified in git history:

| Commit | Description |
|--------|-------------|
| `1ee5312` | test(108-01): failing tests for severity models, damages, regression |
| `6a62c16` | feat(108-01): severity models, damages estimation, settlement regression |
| `cf965ee` | test(108-01): failing tests for amplifiers, erosion, legacy lens, integration |
| `72da079` | feat(108-01): severity amplifiers, layer erosion, legacy lens, pipeline integration |
| `3353bfa` | test(108-02): failing tests for P x S computation and severity scoring lens |
| `46b8e59` | feat(108-02): SeverityScoringLens orchestrator, P x S computation, CLI --attachment, calibration |
| `3bdb611` | test(108-02): failing tests for P x S chart and severity context builder |
| `4c6592f` | feat(108-02): P x S matrix chart, severity context builder, chart registry |

TDD discipline maintained throughout: each RED commit followed by GREEN commit.

---

### Human Verification Required

The following items cannot be verified programmatically:

#### 1. P x S Chart Visual Rendering

**Test:** Run `uv run python -c "from do_uw.stages.render.charts.pxs_matrix_chart import render_pxs_matrix_html; ..."` with a mock SeverityResult and open the output HTML.
**Expected:** 4 distinct colored zone backgrounds visible (green lower-left, red upper-right), primary scenario dot plotted, log scale Y-axis readable with $100K-$10B range.
**Why human:** Visual appearance and log-scale rendering quality cannot be verified by grep.

#### 2. Calibration Report Accuracy Assessment

**Test:** Run `generate_severity_calibration_report()` and review model estimates vs actual settlements for landmark cases.
**Expected:** Enron ($7.2B actual) and WorldCom ($6.2B actual) should show large-cap restatement estimates within plausible log-scale error. MAE-log metric visible.
**Why human:** Whether the calibration error metrics indicate acceptable model accuracy requires domain judgment.

#### 3. CLI --attachment End-to-End Flow

**Test:** Run `uv run python -m do_uw.cli analyze AAPL --attachment 25000000 --product ABC` (or similar).
**Expected:** ScoreStage receives liberty_attachment=25000000.0, layer erosion computed, `layer_erosion` populated in severity context output.
**Why human:** Full pipeline integration with real data requires live execution.

---

### Summary

Phase 108 goal is fully achieved. All five SEV requirements are satisfied with substantive, wired implementations — no stubs, no orphans, no missing artifacts. The damages-estimation, settlement-regression, and amplifier engines (Plan 01) plus the SeverityScoringLens orchestrator, P x S visualization chart, severity context builder, and CLI parameters (Plan 02) are all present, tested (61 tests passing), and integrated into ScoreStage as Step 15.5 with graceful degradation. P and S are structurally independent fields on SeverityResult, and expected loss P x S is a computed field accessible throughout the pipeline.

---

_Verified: 2026-03-16T02:10:00Z_
_Verifier: Claude (gsd-verifier)_
