---
phase: 06-scoring-patterns-risk-synthesis
plan: 02
subsystem: scoring
tags: [scoring-engine, factor-scoring, red-flags, tier-classification, pydantic, crf-gates]

# Dependency graph
requires:
  - phase: 01-project-setup
    provides: scoring.json, red_flags.json, sectors.json brain config, ConfigLoader
  - phase: 03-financial-data-extraction
    provides: ExtractedFinancials, AuditProfile models
  - phase: 04-market-trading-governance-analysis
    provides: MarketSignals, StockPerformance, GovernanceData models
  - phase: 05-litigation-regulatory-analysis
    provides: LitigationLandscape, SECEnforcementPipeline models
  - phase: 06-01
    provides: AnalyzeStage, CheckEngine (must complete before SCORE)
provides:
  - 10-factor scoring engine (F1-F10) computing risk points from scoring.json rules
  - 11 CRF red flag gate evaluators with ceiling application
  - Tier classification (WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH)
  - Claim probability computation with industry base rates
  - Expanded scoring Pydantic models (SECT7-04 through SECT7-10)
  - Partial ScoreStage orchestrator (factor + CRF + tier pipeline)
affects: [06-03 pattern detection, 06-04 scoring calibration, 07 benchmark, 08 render]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "3-way file split for complex engines (factor_scoring + factor_data + factor_rules)"
    - "CRF ID normalization via regex for cross-config consistency"
    - "Ceiling application pattern: min(composite, lowest_triggered_ceiling)"
    - "Per-factor data extraction functions returning typed dicts"

key-files:
  created:
    - src/do_uw/stages/score/factor_scoring.py
    - src/do_uw/stages/score/factor_data.py
    - src/do_uw/stages/score/factor_rules.py
    - src/do_uw/stages/score/red_flag_gates.py
    - src/do_uw/stages/score/tier_classification.py
    - src/do_uw/models/scoring_output.py
  modified:
    - src/do_uw/models/scoring.py
    - src/do_uw/stages/score/__init__.py
    - tests/test_score_stage.py

key-decisions:
  - "3-way split of factor scoring engine (factor_scoring 497L + factor_data 453L + factor_rules 271L) to stay under 500-line limit"
  - "CRF-2 (Wells Notice) checks highest_confirmed_stage and pipeline_position since no direct wells_notice field exists on model"
  - "CRF-3 (DOJ Investigation) checks pipeline_signals and regulatory_proceedings since no direct doj_investigation field exists"
  - "Scoring models split into scoring.py (303L) + scoring_output.py (313L) with re-exports for backward compat"
  - "Backward-compat aliases (_get_sector_code, _min_settlement_years) for internal function renames"
  - "CRF ID normalization strips leading zeros: CRF-001 and CRF-01 both become CRF-1"

patterns-established:
  - "Factor data extraction: _get_fN_data functions return typed dicts for rule matching"
  - "Rule matching dispatch: rule_matches(rule, data, factor_key) routes to per-factor matchers"
  - "CRF gate evaluation: per-trigger evaluators return (triggered, evidence) tuples"
  - "Tier classification from config: iterate tier_config ranges, fallback to NO_TOUCH"
  - "Claim probability: parse probability_range string to band + numeric range"

# Metrics
duration: 15min
completed: 2026-02-08
---

# Phase 6 Plan 02: SCORE Stage Core Summary

**10-factor scoring engine with 11 CRF red flag gates, tier classification (WIN through NO_TOUCH), and claim probability computation from scoring.json rules**

## Performance

- **Duration:** 15 min (across 2 context windows)
- **Started:** 2026-02-08T19:24:10Z
- **Completed:** 2026-02-08T19:39:50Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Built complete 10-factor scoring engine (F1-F10) computing risk deductions from scoring.json rules with sub-component breakdowns, bonuses, and multipliers
- Implemented 11 CRF red flag gate evaluators with CRF ID normalization and quality score ceiling application
- Created tier classification mapping quality scores to WIN/WANT/WRITE/WATCH/WALK/NO_TOUCH tiers
- Wired ScoreStage orchestrator: CRF gates -> factor scoring -> composite -> ceiling -> tier -> probability
- Expanded scoring Pydantic models with SECT7-04 through SECT7-10 output models (RiskType, AllegationMapping, SeverityScenarios, TowerRecommendation, RedFlagSummary)

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand scoring models and build factor scoring engine** - `43b218e` (feat)
2. **Task 2: CRF red flag gates, tier classification, and ScoreStage orchestrator** - `7c05660` (feat)

## Files Created/Modified
- `src/do_uw/models/scoring.py` - Core scoring models (Tier, FactorScore, RedFlagResult, ScoringResult) with re-exports from scoring_output.py
- `src/do_uw/models/scoring_output.py` - SECT7-04 through SECT7-10 output models (RiskType, AllegationMapping, ClaimProbability, SeverityScenarios, TowerRecommendation, RedFlagSummary)
- `src/do_uw/stages/score/factor_scoring.py` - 10-factor scoring engine with rule matching, bonuses, multipliers
- `src/do_uw/stages/score/factor_data.py` - Per-factor data extraction from ExtractedData models
- `src/do_uw/stages/score/factor_rules.py` - Per-factor rule matchers (F1-F10 condition evaluation)
- `src/do_uw/stages/score/red_flag_gates.py` - 11 CRF gate evaluators with ceiling application and CRF ID normalization
- `src/do_uw/stages/score/tier_classification.py` - Tier classification, claim probability, probability band parsing
- `src/do_uw/stages/score/__init__.py` - ScoreStage orchestrator (replaces stub) with full pipeline
- `tests/test_score_stage.py` - 45 tests covering models, factor scoring, CRF gates, tier classification, integration

## Decisions Made
- **3-way factor scoring split**: factor_scoring.py was 1196 lines after initial implementation. Split into factor_scoring.py (engine, 497L) + factor_data.py (data extraction, 453L) + factor_rules.py (rule matchers, 271L) to comply with 500-line limit.
- **CRF model adaptation**: CRF-2 (Wells Notice) and CRF-3 (DOJ Investigation) required adapting to actual model fields rather than assumed convenience fields. Wells Notice checks `highest_confirmed_stage` and `pipeline_position`; DOJ checks `pipeline_signals` and `regulatory_proceedings`.
- **Scoring model split**: scoring.py approaching 500L split into scoring.py (303L) + scoring_output.py (313L) with re-exports maintaining backward compatibility.
- **CRF ID normalization**: Both CRF-01 (red_flags.json) and CRF-001 (scoring.json) formats normalized to CRF-1 via regex for cross-config lookups.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Factor scoring file too large (1196 lines)**
- **Found during:** Task 1
- **Issue:** factor_scoring.py exceeded 500-line limit after implementing all 10 factor data extractors and rule matchers
- **Fix:** Created factor_data.py (data extraction helpers) and factor_rules.py (rule matcher dispatch), reducing factor_scoring.py to 497 lines
- **Files modified:** factor_scoring.py, factor_data.py (new), factor_rules.py (new)
- **Committed in:** 43b218e (Task 1 commit)

**2. [Rule 1 - Bug] CRF-2/CRF-3 referenced non-existent model fields**
- **Found during:** Task 2
- **Issue:** Plan specified checking `wells_notice` and `doj_investigation` fields that do not exist on LitigationLandscape or SECEnforcementPipeline models
- **Fix:** CRF-2 adapted to check `highest_confirmed_stage` for WELLS_NOTICE/ENFORCEMENT_ACTION and `pipeline_position` for WELLS. CRF-3 adapted to check `pipeline_signals` for DOJ/CRIMINAL and `regulatory_proceedings` for DOJ agency.
- **Files modified:** red_flag_gates.py
- **Committed in:** 7c05660 (Task 2 commit)

**3. [Rule 1 - Bug] AnalysisState requires ticker field**
- **Found during:** Task 2
- **Issue:** TestScoreStageRun used `AnalysisState()` but AnalysisState has required `ticker` field
- **Fix:** Changed to `AnalysisState(ticker="TEST")`
- **Files modified:** tests/test_score_stage.py
- **Committed in:** 7c05660 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and 500-line compliance. No scope creep.

## Issues Encountered
- Context window exhausted during Task 1 implementation, requiring continuation in a new session. All work was preserved and continued seamlessly.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ScoreStage pipeline complete: CRF gates -> factor scoring -> composite -> ceiling -> tier -> probability
- Patterns, allegation mapping, severity scenarios, and tower recommendation fields are None -- populated by 06-03 (pattern detection) and 06-04 (scoring calibration)
- 834 tests passing, 0 pyright errors, 0 ruff errors
- All files under 500 lines

---
*Phase: 06-scoring-patterns-risk-synthesis*
*Completed: 2026-02-08*
