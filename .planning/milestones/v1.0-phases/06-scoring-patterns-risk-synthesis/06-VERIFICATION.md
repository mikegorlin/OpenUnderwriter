---
phase: 06-scoring-patterns-risk-synthesis
verified: 2026-02-08T20:21:40Z
status: passed
score: 6/6 must-haves verified
---

# Phase 6: Scoring, Patterns & Risk Synthesis Verification Report

**Phase Goal:** The ANALYZE and SCORE pipeline stages are complete -- the 359-check execution engine runs against all structured facts, the 10-factor scoring model produces a composite score, 17 composite patterns are detected, 11 critical red flag gates apply score ceilings, and the company receives a tier classification (WIN/WANT/WRITE/WATCH/WALK/NO TOUCH).

**Verified:** 2026-02-08T20:21:40Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #   | Truth                                                                                           | Status     | Evidence                                                                                                  |
| --- | ----------------------------------------------------------------------------------------------- | ---------- | --------------------------------------------------------------------------------------------------------- |
| 1   | 359 checks execute against structured facts in chunked batches                                 | ✓ VERIFIED | check_engine.py executes_checks() with CHUNK_SIZE=50, 351 AUTO checks run, produces CheckResult per check |
| 2   | 10-factor composite score computed with transparent sub-component breakdowns                   | ✓ VERIFIED | factor_scoring.py scores all F1-F10, FactorScore.sub_components shows breakdown, test confirms 10 factors |
| 3   | 17+ composite patterns detected with evidence                                                  | ✓ VERIFIED | pattern_detection.py detects 19 patterns (17 original + AI_WASHING + EARNINGS_QUALITY), PatternMatch model |
| 4   | 11 critical red flag gates apply score ceilings when triggered                                 | ✓ VERIFIED | red_flag_gates.py evaluates 11 CRF gates (CRF-01 through CRF-11), apply_crf_ceilings() finds lowest ceiling |
| 5   | Company receives tier classification and claim probability band                                | ✓ VERIFIED | tier_classification.py maps to 6 tiers (WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH), compute_claim_probability() |
| 6   | Loss severity scenarios at 4 percentiles (25/50/75/95)                                         | ✓ VERIFIED | severity_model.py model_severity() produces 4 SeverityScenario objects with DDL + settlement + defense cost |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact                                          | Expected                                        | Status     | Details                                                                                    |
| ------------------------------------------------- | ----------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------ |
| `src/do_uw/stages/analyze/check_engine.py`       | Check execution engine                          | ✓ VERIFIED | 455 lines, executes 10 threshold types, chunked batch processing                          |
| `src/do_uw/stages/analyze/check_mappers.py`      | Data mappers for sections 2-6                   | ✓ VERIFIED | 493 lines, section-routed mapping to 5 domains (company, financial, market, gov, lit)     |
| `src/do_uw/stages/analyze/check_results.py`      | CheckResult model and aggregation               | ✓ VERIFIED | 107 lines, CheckStatus enum, aggregate_results helper                                     |
| `src/do_uw/stages/analyze/__init__.py`           | AnalyzeStage orchestrator                       | ✓ VERIFIED | 110 lines, loads checks, executes engine, populates state.analysis                        |
| `src/do_uw/stages/score/factor_scoring.py`       | 10-factor scoring engine                        | ✓ VERIFIED | 497 lines, scores F1-F10 from scoring.json rules with sub-components                      |
| `src/do_uw/stages/score/factor_data.py`          | Per-factor data extraction                      | ✓ VERIFIED | 453 lines, get_factor_data for F1-F10                                                     |
| `src/do_uw/stages/score/factor_rules.py`         | Per-factor rule matching                        | ✓ VERIFIED | 271 lines, rule_matches dispatcher                                                        |
| `src/do_uw/stages/score/red_flag_gates.py`       | 11 CRF gate evaluators                          | ✓ VERIFIED | 396 lines, evaluates all 11 CRF gates with ceiling application                            |
| `src/do_uw/stages/score/tier_classification.py`  | Tier classification and claim probability       | ✓ VERIFIED | 253 lines, classify_tier + compute_claim_probability                                      |
| `src/do_uw/stages/score/pattern_detection.py`    | 19-pattern detection engine                     | ✓ VERIFIED | 324 lines, detect_all_patterns from patterns.json                                         |
| `src/do_uw/stages/score/pattern_fields.py`       | Pattern field value mapping                     | ✓ VERIFIED | 480 lines, maps ~50 pattern fields to ExtractedData paths                                 |
| `src/do_uw/stages/score/allegation_mapping.py`   | 5-theory allegation mapping + 7-archetype risk  | ✓ VERIFIED | 407 lines, map_allegations + classify_risk_type                                           |
| `src/do_uw/stages/score/severity_model.py`       | Severity scenarios, tower position, red flags   | ✓ VERIFIED | 380 lines, model_severity + recommend_tower + compile_red_flag_summary                    |
| `src/do_uw/stages/score/__init__.py`             | Complete ScoreStage orchestrator                | ✓ VERIFIED | 206 lines, 16-step pipeline from CRF gates through red flag summary                       |
| `src/do_uw/brain/checks.json`                    | 359 check definitions                           | ✓ VERIFIED | 359 checks total, 351 AUTO-mode checks                                                    |
| `src/do_uw/brain/patterns.json`                  | 19 pattern definitions (17+2 new)               | ✓ VERIFIED | total_patterns=19, includes AI_WASHING_RISK + EARNINGS_QUALITY_DETERIORATION              |
| `src/do_uw/brain/red_flags.json`                 | 11 CRF gate definitions                         | ✓ VERIFIED | 11 escalation_triggers (CRF-01 through CRF-11)                                            |
| `src/do_uw/brain/scoring.json`                   | 10 factors, 6 tiers, severity ranges, tower map | ✓ VERIFIED | 10 factors (F1-F10), 6 tiers (WIN-NO_TOUCH), ceiling config, severity/tower config        |
| `src/do_uw/models/scoring.py`                    | Expanded scoring models (SECT7-04 thru -10)     | ✓ VERIFIED | ScoringResult has all fields: risk_type, allegation_mapping, claim_probability, severity, tower, rf_summary |
| `tests/test_analyze_stage.py`                    | AnalyzeStage tests                              | ✓ VERIFIED | 37 tests covering engine, mappers, orchestration                                          |
| `tests/test_score_stage.py`                      | ScoreStage tests                                | ✓ VERIFIED | 48 tests covering models, factors, CRF, tier, patterns, allegation, full pipeline         |
| `tests/test_pattern_detection.py`                | Pattern detection + allegation tests            | ✓ VERIFIED | 64 tests for pattern engine, field mapping, allegation, risk type                         |
| `tests/test_severity_tower.py`                   | Severity + tower + red flag tests               | ✓ VERIFIED | 25 tests for severity model, tower recommendation, red flag summary                       |

### Key Link Verification

| From                         | To                          | Via                      | Status     | Details                                                              |
| ---------------------------- | --------------------------- | ------------------------ | ---------- | -------------------------------------------------------------------- |
| AnalyzeStage.__init__        | check_engine.py             | execute_checks()         | ✓ WIRED    | Line 78: `results = execute_checks(checks, state.extracted, state.company)` |
| check_engine.py              | check_mappers.py            | map_check_data()         | ✓ WIRED    | Line 80-81: `data = map_check_data(...); result = evaluate_check(...)` |
| check_engine.py              | check_results.py            | CheckResult model        | ✓ WIRED    | Lines throughout: `CheckResult(...)` constructor calls               |
| AnalyzeStage.__init__        | state.analysis              | AnalysisResults          | ✓ WIRED    | Lines 84-92: Populates `state.analysis = AnalysisResults(...)`      |
| ScoreStage.__init__          | factor_scoring.py           | score_all_factors()      | ✓ WIRED    | Line 115-117: `factor_scores = score_all_factors(...)`              |
| ScoreStage.__init__          | pattern_detection.py        | detect_all_patterns()    | ✓ WIRED    | Line 120-122: `patterns = detect_all_patterns(...)`                 |
| ScoreStage.__init__          | red_flag_gates.py           | evaluate_red_flag_gates()| ✓ WIRED    | Line 110-112: `red_flag_results = evaluate_red_flag_gates(...)`     |
| ScoreStage.__init__          | tier_classification.py      | classify_tier()          | ✓ WIRED    | Line 138: `tier = classify_tier(quality_score, tiers_config)`       |
| ScoreStage.__init__          | allegation_mapping.py       | map_allegations()        | ✓ WIRED    | Line 146-148: `allegation_map = map_allegations(...)`               |
| ScoreStage.__init__          | severity_model.py           | model_severity()         | ✓ WIRED    | Line 157: `severity = model_severity(market_cap, tier, ...)`        |
| ScoreStage.__init__          | severity_model.py           | recommend_tower()        | ✓ WIRED    | Line 160-162: `tower = recommend_tower(...)`                        |
| ScoreStage.__init__          | severity_model.py           | compile_red_flag_summary()| ✓ WIRED   | Line 165-167: `rf_summary = compile_red_flag_summary(...)`          |
| ScoreStage.__init__          | state.scoring               | ScoringResult            | ✓ WIRED    | Lines 174-193: Populates `state.scoring = ScoringResult(...)`       |
| Pipeline                     | AnalyzeStage                | stages list              | ✓ WIRED    | pipeline.py line 98: `AnalyzeStage()` in default stages list        |
| Pipeline                     | ScoreStage                  | stages list              | ✓ WIRED    | pipeline.py line 99: `ScoreStage()` in default stages list          |

### Requirements Coverage

All SECT7 requirements from REQUIREMENTS.md mapped to implementation:

| Requirement | Status     | Supporting Evidence                                                                                   |
| ----------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| SECT7-01    | ✓ SATISFIED | 10-factor scoring in factor_scoring.py, all F1-F10 with max_points, sub_components transparency      |
| SECT7-02    | ✓ SATISFIED | 19 patterns (17 original + 2 new) in patterns.json detected by pattern_detection.py                  |
| SECT7-03    | ✓ SATISFIED | 11 CRF gates (CRF-01 through CRF-11) in red_flag_gates.py with configurable ceilings                 |
| SECT7-04    | ✓ SATISFIED | 7 risk archetypes in allegation_mapping.py classify_risk_type() with secondary overlay support       |
| SECT7-05    | ✓ SATISFIED | 5 allegation theories (A-E) mapped in allegation_mapping.py map_allegations() with exposure levels   |
| SECT7-06    | ✓ SATISFIED | Claims correlation integrated via historical_lift weights in scoring.json factor rules (flagged for calibration) |
| SECT7-07    | ✓ SATISFIED | Claim probability bands (LOW/MODERATE/ELEVATED/HIGH/VERY_HIGH) in tier_classification.py             |
| SECT7-08    | ✓ SATISFIED | Loss severity at 4 percentiles (25/50/75/95) with DDL scenarios in severity_model.py                 |
| SECT7-09    | ✓ SATISFIED | Tower position recommendation with Side A assessment in severity_model.py recommend_tower()           |
| SECT7-10    | ✓ SATISFIED | Red flag summary with 4 severity tiers in severity_model.py compile_red_flag_summary()               |
| SECT7-11    | ✓ SATISFIED | Calibration notes in ScoringResult.calibration_notes, needs_calibration=True on all output models    |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| None | N/A  | N/A     | N/A      | No anti-patterns detected |

**Anti-pattern scan results:**
- 0 TODO/FIXME/placeholder comments found in analyze/ and score/ stages
- 0 empty return patterns (only valid None returns for missing data)
- 0 console.log-only implementations
- All files under 500-line limit (largest: factor_scoring.py at 497 lines)

### Test Coverage Summary

**Phase 6 test suites:**
- `test_analyze_stage.py`: 37 tests (check engine, mappers, orchestration)
- `test_score_stage.py`: 48 tests (models, factors, CRF, tier, full pipeline)
- `test_pattern_detection.py`: 64 tests (patterns, allegation, risk type)
- `test_severity_tower.py`: 25 tests (severity, tower, red flags)

**Total:** 174 Phase 6 tests
**Full suite:** 926 tests passing (up from ~750 at Phase 5 end)
**Type checking:** 0 pyright errors (strict mode)
**Linting:** 0 ruff violations
**Duration:** Full suite runs in 7.04s

**Integration test evidence:**
- `test_score_stage_full_pipeline_all_fields` verifies complete ScoringResult population with all SECT7-04 through SECT7-10 fields
- `test_pattern_modifiers_applied_and_capped` verifies pattern score impacts are applied to factors and capped at max_points
- `test_pipeline_runs_all_stages` verifies both AnalyzeStage and ScoreStage execute in full pipeline
- `test_resume_skips_completed_stages` verifies state persistence works with both stages

### Human Verification Required

None. All verification criteria can be checked programmatically against the codebase.

---

## Verification Details

### Truth 1: 359 checks execute in chunked batches

**Files verified:**
- `src/do_uw/brain/checks.json` contains 359 checks (351 AUTO-mode)
- `src/do_uw/stages/analyze/check_engine.py` implements `execute_checks()` with `CHUNK_SIZE = 50`
- `src/do_uw/stages/analyze/check_results.py` defines `CheckResult` model with status/value/evidence/source/factors fields
- `src/do_uw/stages/analyze/__init__.py` loads checks from ConfigLoader and calls `execute_checks()`

**Wiring verified:**
- AnalyzeStage.run() line 78: `results = execute_checks(checks, state.extracted, state.company)`
- check_engine.py lines 80-81: Maps data via `map_check_data()`, evaluates via `evaluate_check()`
- Results stored in state.analysis.check_results as dict[check_id, CheckResult]

**Test evidence:**
- `test_batch_execution` verifies chunked processing
- `test_run_populates_state_analysis` verifies state.analysis populated with counts and results

**Substantive check:**
- 455 lines of real threshold evaluation logic covering 10 threshold types
- Handles tiered (309), info (19), percentage (10), boolean (2), count (2), value (4), pattern (6), search (1), multi_period (1), classification (5)
- Missing data produces SKIPPED status (not false CLEAR)

### Truth 2: 10-factor composite score with transparent breakdowns

**Files verified:**
- `src/do_uw/stages/score/factor_scoring.py` implements `score_all_factors()` for F1-F10
- `src/do_uw/stages/score/factor_data.py` extracts data for each factor
- `src/do_uw/stages/score/factor_rules.py` matches rules per factor
- `src/do_uw/brain/scoring.json` defines 10 factors with max_points (F1=20, F2=15, F3=12, F4=10, F5=10, F6=8, F7=9, F8=8, F9=6, F10=2)

**Wiring verified:**
- ScoreStage.run() line 115-117: `factor_scores = score_all_factors(...)`
- FactorScore model includes `sub_components: dict[str, float]` for transparency
- Pattern modifiers applied via `_apply_pattern_modifiers()` (line 125)
- Composite computed as `100.0 - sum(f.points_deducted for f in factor_scores)` (line 128-129)

**Test evidence:**
- `test_f1_active_sca_scores_20` verifies F1 scoring
- `test_f2_45pct_decline_scores_9` verifies F2 scoring
- `test_f2_insider_amplifier_cluster_selling` verifies multipliers
- `test_f2_max_points_cap` verifies capping at max_points
- `test_all_none_produces_10_zero_scores` verifies all 10 factors always score

**Substantive check:**
- 497 lines in factor_scoring.py (under 500 limit)
- Factor data extraction covers all ExtractedData domains
- Sub-components show: base rule points, bonuses, multipliers, pattern modifiers

### Truth 3: 17+ composite patterns detected

**Files verified:**
- `src/do_uw/brain/patterns.json` defines 19 patterns (total_patterns=19)
- `src/do_uw/stages/score/pattern_detection.py` implements `detect_all_patterns()`
- `src/do_uw/stages/score/pattern_fields.py` maps ~50 pattern field names to ExtractedData paths
- Patterns include: 17 original + AI_WASHING_RISK + EARNINGS_QUALITY_DETERIORATION

**Wiring verified:**
- ScoreStage.run() line 120-122: `patterns = detect_all_patterns(...)`
- PatternMatch model includes: detected, severity, matched_triggers, score_impact
- Pattern modifiers applied to factor scores (line 125)
- Detected patterns stored in state.scoring.patterns_detected (line 181)

**Test evidence:**
- `test_detect_all_patterns` returns 19 PatternMatch objects
- `test_ai_washing_risk_new_pattern_loads_from_config` verifies new pattern
- `test_earnings_quality_deterioration_new_pattern_loads_from_config` verifies new pattern
- `test_death_spiral_pattern_detection` verifies multi-trigger pattern

**Substantive check:**
- 324 lines in pattern_detection.py (trigger evaluation, severity computation, score impact)
- Trigger operators: gt, lt, gte, lte, eq, ne, in, not_in
- Severity levels: BASELINE, ELEVATED, HIGH, SEVERE
- Majority (>50%) of triggers must match for pattern detection

### Truth 4: 11 critical red flag gates apply ceilings

**Files verified:**
- `src/do_uw/brain/red_flags.json` defines 11 escalation_triggers (CRF-01 through CRF-11)
- `src/do_uw/brain/scoring.json` defines critical_red_flag_ceilings with ceiling values per CRF
- `src/do_uw/stages/score/red_flag_gates.py` implements `evaluate_red_flag_gates()` and `apply_crf_ceilings()`

**Wiring verified:**
- ScoreStage.run() line 110-112: CRF gates evaluated FIRST (per processing_rules)
- CRF ceilings applied AFTER composite calculation (line 132-134)
- Binding ceiling ID stored in state.scoring.binding_ceiling_id (line 188)
- CRF normalization handles both CRF-01 and CRF-001 formats

**Test evidence:**
- `test_active_sca_triggers_crf1` verifies CRF-01 evaluation
- `test_going_concern_triggers_crf4` verifies CRF-04 evaluation
- `test_two_triggers_lowest_wins` verifies lowest ceiling is binding
- `test_ceiling_below_composite` verifies ceiling application

**Substantive check:**
- 396 lines in red_flag_gates.py covering all 11 CRF conditions
- CRF conditions check: active SCA, Wells notice, DOJ investigation, going concern, restatement, material weakness, etc.
- Ceiling application: `quality_score = min(composite, lowest_ceiling)`
- Missing data evaluates as not-triggered (safe default)

### Truth 5: Tier classification and claim probability band

**Files verified:**
- `src/do_uw/brain/scoring.json` defines 6 tiers (WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH) with score ranges
- `src/do_uw/stages/score/tier_classification.py` implements `classify_tier()` and `compute_claim_probability()`
- `src/do_uw/models/scoring_output.py` defines ProbabilityBand enum (LOW/MODERATE/ELEVATED/HIGH/VERY_HIGH)

**Wiring verified:**
- ScoreStage.run() line 138: `tier = classify_tier(quality_score, tiers_config)`
- ScoreStage.run() line 151-153: `claim_prob = compute_claim_probability(tier, state.company, brain.sectors)`
- Both stored in state.scoring (lines 180, 184)

**Test evidence:**
- `test_score_90_is_win` through `test_score_20_is_walk` verify all 6 tier classifications
- `test_win_tier_low_band` and `test_watch_tier_high_band` verify probability band assignment
- `test_score_stage_populates_state` verifies tier and claim_probability in ScoringResult

**Substantive check:**
- 253 lines in tier_classification.py
- Tier score ranges defined in config (not hardcoded)
- Claim probability includes: band, range_low_pct, range_high_pct, industry_base_rate_pct, adjustment_narrative
- Industry base rate looked up from sectors.json by SIC code

### Truth 6: Loss severity scenarios at 4 percentiles

**Files verified:**
- `src/do_uw/stages/score/severity_model.py` implements `model_severity()`
- `src/do_uw/brain/scoring.json` defines severity_ranges with base_range by market_cap and tier_multipliers
- `src/do_uw/models/scoring_output.py` defines SeverityScenario and SeverityScenarios models

**Wiring verified:**
- ScoreStage.run() line 157: `severity = model_severity(market_cap, tier, brain.scoring)`
- Stored in state.scoring.severity_scenarios (line 185)
- Helper `_get_market_cap()` extracts market cap from SourcedValue

**Test evidence:**
- `test_model_severity_with_10b_market_cap` verifies scenario computation
- `test_ddl_scenarios_10_20_30_pct` verifies DDL decline scenarios
- `test_four_percentile_scenarios_ascending` verifies ordering
- `test_defense_cost_proportions` verifies 15%/20%/25%/30% defense costs

**Substantive check:**
- 380 lines in severity_model.py
- 4 scenarios: 25th (favorable), 50th (median), 75th (adverse), 95th (catastrophic)
- Each scenario includes: ddl_amount, settlement_estimate, defense_cost_estimate, total_exposure
- Decline scenarios: 10%, 20%, 30% of market cap
- Settlement = base_range * tier_multiplier (config-driven)
- Defense costs = percentage of settlement (config-driven)

---

## Overall Assessment

**Status: PASSED**

All 6 observable truths are verified. All required artifacts exist, are substantive (no stubs), and are wired correctly. The ANALYZE and SCORE pipeline stages are complete and functional.

**Evidence summary:**
- 359 checks defined, 351 AUTO checks execute
- 10 factors score with transparent sub-components
- 19 patterns detect (17 + 2 new)
- 11 CRF gates apply ceilings
- 6 tiers classify companies
- 4 severity scenarios model loss
- 926 tests pass (174 Phase 6-specific)
- 0 pyright errors, 0 ruff violations
- All files under 500 lines (largest: 497)
- No anti-patterns detected

**Phase 6 goal achieved:** The ANALYZE and SCORE pipeline stages run end-to-end, producing a complete ScoringResult with all SECT7-01 through SECT7-11 outputs.

---

_Verified: 2026-02-08T20:21:40Z_
_Verifier: Claude Code (gsd-verifier)_
