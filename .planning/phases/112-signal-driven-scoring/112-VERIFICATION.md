---
phase: 112-signal-driven-scoring
verified: 2026-03-16T00:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
---

# Phase 112: Signal-Driven Scoring Verification Report

**Phase Goal:** Signal-driven scoring — refactor the 10-factor scoring engine to consume signal results instead of ExtractedData, build signal aggregation, extend FactorScore with attribution, add shadow calibration signal-vs-rule comparison, and provide underwriter-facing factor contribution transparency.
**Verified:** 2026-03-16
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | Each factor score is computed from signal results when signal coverage >= 50% | VERIFIED | `factor_scoring.py:111-125` — `aggregate_factor_from_signals` called when `signal_results is not None`; `scoring_method = "signal_driven"` when `use_signal_path is True` |
| 2  | Factors with <50% signal coverage fall back to existing rule-based scoring | VERIFIED | `factor_data_signals.py:231` — `use_signal_path = coverage >= COVERAGE_THRESHOLD` (0.50); `factor_scoring.py:127+` falls back when False |
| 3  | TRIGGERED signals with red threshold contribute more than yellow; CLEAR contributes 0 | VERIFIED | `factor_data_signals.py:48-58` — `_threshold_to_severity`: red=1.0, yellow=0.5, clear=0.0 |
| 4  | DEFERRED and SKIPPED signals excluded from factor score denominator | VERIFIED | `factor_data_signals.py:199` — `if status in ("DEFERRED", "SKIPPED"): continue` (skips evaluable_count increment) |
| 5  | Composite score changes measurably when signals TRIGGER vs all CLEAR | VERIFIED | `test_signal_scoring_influence.py` — 2 integration tests prove score difference; 46 new tests all pass |
| 6  | All existing tests pass (backward compatibility) | VERIFIED | 449 score tests pass; `signal_results=None` default preserves existing behavior in `score_all_factors` |
| 7  | Factor breakdown shows which signals contributed with severity and weight | VERIFIED | `context_builders/scoring.py:140-160` — `signal_attribution` dict with `top_3_signals`, `confidence_pct`, `evaluated_count`, `full_signal_count` |
| 8  | Top 3 contributing signals per factor surfaced for worksheet display | VERIFIED | `context_builders/scoring.py:146-156` — `top_3 = sorted(fs.signal_contributions, key=..., reverse=True)[:3]` |
| 9  | Per-factor confidence bar shows evaluated/total signals ratio | VERIFIED | `context_builders/scoring.py:153-160` — `confidence_pct = f"{round(fs.signal_coverage * 100)}%"` in `signal_attribution` |
| 10 | Shadow calibration compares rule-based vs signal-driven per factor | VERIFIED | `shadow_calibration.py:219-235` — `factor_scores_signal`, `factor_scores_rule`, `signal_composite`, `signal_coverage_avg`, `scoring_methods`; `_calibration_report.py:286-340` factor comparison HTML section |
| 11 | Factor weights visible in factor table output | VERIFIED | `context_builders/scoring.py:140` — `"factor_weight_pct": f"{fs.max_points}%"` added to every factor dict |

**Score:** 11/11 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/score/factor_data_signals.py` | Signal-to-factor aggregation engine with `aggregate_factor_from_signals` | VERIFIED | 243 lines (under 300 limit); `aggregate_factor_from_signals`, `get_signals_for_factor`, `_threshold_to_severity`, `FACTOR_SHORT_TO_LONG` all present |
| `src/do_uw/models/scoring.py` | Extended FactorScore with `signal_contributions`, `signal_coverage`, `scoring_method` | VERIFIED | All three fields present at lines 99-110 with correct types and defaults |
| `src/do_uw/brain/brain_signal_schema.py` | Optional `ScoringSpec` on `BrainSignalEntry` | VERIFIED | `ScoringContribution` (line 405), `ScoringSpec` (line 420), `scoring: ScoringSpec | None` (line 591) |
| `tests/stages/score/test_factor_data_signals.py` | Unit tests for signal aggregation (min 100 lines) | VERIFIED | 362 lines; 18 unit tests covering all aggregation behaviors |
| `tests/stages/score/test_signal_scoring_influence.py` | Integration tests proving score changes (min 50 lines) | VERIFIED | 120 lines; 2 integration tests demonstrating FSCORE-02 |
| `tests/stages/score/test_factor_score_contributions.py` | Tests for factor contribution display (min 50 lines) | VERIFIED | 291 lines; 10 tests covering signal attribution, top-3, confidence bar, factor weights, backward compat |
| `tests/stages/score/test_shadow_signal_calibration.py` | Tests for shadow calibration old vs new (min 50 lines) | VERIFIED | 228 lines; 16 tests for CalibrationRow/Metrics extensions and report generation |
| `src/do_uw/stages/render/context_builders/scoring.py` | Signal attribution in scoring context with `signal_contributions` | VERIFIED | `signal_attribution` dict with top_3, confidence_pct, evaluated_count; `factor_weight_pct` per factor |
| `src/do_uw/stages/score/shadow_calibration.py` | Extended CalibrationRow with signal-driven vs rule-based comparison | VERIFIED | `factor_scores_signal`, `factor_scores_rule`, `signal_composite`, `signal_coverage_avg`, `scoring_methods` on CalibrationRow |
| `src/do_uw/stages/score/_calibration_report.py` | Factor comparison section in calibration HTML | VERIFIED | `_build_factor_comparison_section` at line 286; factor table with Rule-Based/Signal-Driven/Delta/Coverage/Method columns |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `factor_data_signals.py` | `brain/signals/*.yaml` | `brain_unified_loader.load_signals()` | VERIFIED | Line 16: `from do_uw.brain.brain_unified_loader import load_signals`; line 119: `data = load_signals()` |
| `factor_scoring.py` | `factor_data_signals.py` | `signal_results` passed through `score_all_factors` -> `_score_factor` | VERIFIED | Lines 40, 87, 111-125 — `signal_results` param flows through; `aggregate_factor_from_signals` imported and called when signal_results provided |
| `stages/score/__init__.py` | `factor_scoring.py` | `ScoreStage` passes `signal_results` from `state.analysis` | VERIFIED | Lines 255, 268-274 — `signal_results` extracted from `analysis_dict` and passed to `score_all_factors` |
| `context_builders/scoring.py` | `models/scoring.py` | `FactorScore.signal_contributions` consumed by context builder | VERIFIED | Lines 146-160 — iterates `fs.signal_contributions`, reads `fs.signal_coverage`, `fs.scoring_method` |
| `shadow_calibration.py` | `factor_data_signals.py` | Calibration compares scoring methods per factor | VERIFIED | Lines 620-635 — reads `fs.scoring_method` to route into `factor_scores_signal` vs `factor_scores_rule` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| FSCORE-01 | 112-01 | `factor_data.py` reads signal results (not ExtractedData) for all 10 factors — each factor is a weighted aggregation of constituent signals | SATISFIED | Signal-driven primary path in `_score_factor`; `factor_data.py` accepts `signal_results` param (backward-compat); aggregation in `factor_data_signals.py` |
| FSCORE-02 | 112-01 | Composite score demonstrably changes when signals TRIGGER vs when they don't | SATISFIED | `test_signal_scoring_influence.py` — 2 integration tests prove score difference; 46 Phase 112 tests all pass |
| FSCORE-03 | 112-02 | Factor breakdown shows which signals contributed to each factor score with weights | SATISFIED | `signal_attribution` dict in scoring context with top_3_signals, weights, severity, contribution per signal |
| FSCORE-04 | 112-02 | Shadow calibration comparing old direct-data scoring vs new signal-driven scoring on 3 test tickers (RPM, HNGE, V) | PARTIAL (infrastructure only) | CalibrationRow extended and report HTML built; actual RPM/HNGE/V comparison runs are manual post-phase (noted in SUMMARY as deliberate) |

**Note on FSCORE-04:** The requirement specifies a comparison on 3 test tickers. The SUMMARY documents that the infrastructure is in place and "actual run is manual post-phase." The code is wired; live calibration output on RPM/HNGE/V is a human step needing a full pipeline run. This is a human verification item, not a code gap.

### Anti-Patterns Found

No blockers or stubs found. The two `return {}` in `context_builders/scoring.py` (lines 42 and 94) are proper error-guard early exits in exception handlers, not empty implementations.

### Human Verification Required

**1. Live signal-driven scoring on real ticker**

- **Test:** Run `underwrite RPM --fresh` and inspect the scoring section
- **Expected:** At least one factor shows `scoring_method = "signal_driven"` when signal coverage >= 50% for that factor; the factor table shows `signal_attribution` data if Phase 114 template changes are already present
- **Why human:** Requires live pipeline run; actual signal coverage depends on real YAML-tagged signals vs current brain state

**2. FSCORE-04 calibration comparison output (RPM, HNGE, V)**

- **Test:** Run `underwrite RPM --fresh`, `underwrite HNGE --fresh`, `underwrite V --fresh`; inspect `.cache/calibration/` for factor_calibration.json files; optionally invoke the shadow calibration report
- **Expected:** Each run produces a calibration JSON with `factor_scores_signal` and `factor_scores_rule` dicts; calibration HTML report shows Factor-Level Comparison table
- **Why human:** Requires live pipeline runs on 3 tickers; calibration output is runtime-only

## Commits

All 5 commits documented in SUMMARY verified in git history:

| Commit | Description |
|--------|-------------|
| `d35f849` | test(112-01): add failing tests for signal-to-factor aggregation (TDD RED) |
| `a057346` | feat(112-01): signal aggregation engine with schema extensions |
| `5d37b4c` | feat(112-01): wire signal-driven scoring into pipeline |
| `69f6a5b` | feat(112-02): add signal attribution and factor weights to scoring context |
| `0f9ece9` | feat(112-02): extend shadow calibration with signal-driven comparison |

## Test Results

- New Phase 112 tests: **46/46 passed** (0.71s)
- Full score test suite: **449/449 passed** (2.55s)
- Zero regressions

---

_Verified: 2026-03-16_
_Verifier: Claude (gsd-verifier)_
