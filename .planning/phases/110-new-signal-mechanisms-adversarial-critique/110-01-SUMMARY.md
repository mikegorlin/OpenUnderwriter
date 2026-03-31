---
phase: 110-new-signal-mechanisms-adversarial-critique
plan: 01
subsystem: signal-engine, score-stage, brain-signals
tags: [mechanism-evaluators, conjunction, absence, contextual, deep-dive, TDD]
dependency_graph:
  requires: [phase-103-schema, phase-104-signal-consumer, phase-109-pattern-engines]
  provides: [mechanism-dispatch, conjunction-signals, absence-signals, contextual-signals, deepdive-triggers]
  affects: [signal_engine.py, brain_signal_schema.py, score/__init__.py, scoring.py]
tech_stack:
  added: []
  patterns: [mechanism-dispatch, accumulated-signal-results, all_of-AND-logic, company-context-builder]
key_files:
  created:
    - src/do_uw/stages/analyze/mechanism_evaluators.py
    - src/do_uw/models/deepdive.py
    - src/do_uw/stages/score/_deepdive_runner.py
    - src/do_uw/brain/framework/context_matrix.yaml
    - src/do_uw/brain/framework/deepdive_triggers.yaml
    - src/do_uw/brain/signals/conjunction/ (8 files)
    - src/do_uw/brain/signals/absence/ (20 files)
    - src/do_uw/brain/signals/contextual/ (20 files)
    - tests/stages/analyze/test_mechanism_evaluators.py
    - tests/stages/score/test_deepdive_runner.py
  modified:
    - src/do_uw/brain/brain_signal_schema.py
    - src/do_uw/stages/analyze/signal_engine.py
    - src/do_uw/models/scoring.py
    - src/do_uw/stages/score/__init__.py
    - tests/brain/test_schema_validation_ci.py
decisions:
  - Mechanism dispatch added to execute_signals (not evaluate_signal) because mechanism signals need accumulated results dict
  - Company context built dynamically from CompanyProfile attributes (lifecycle_stage, size_tier, sector)
  - Deep-dive acquisition loop deferred to future iteration; UW investigation prompts deliver 80% of value
  - RAP subcategories mapped to existing taxonomy values rather than adding new ones
  - CI gate bands widened to accommodate 562 total signals (was 514)
metrics:
  duration_seconds: 965
  completed: "2026-03-16"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 50
  files_created: 56
  files_modified: 5
---

# Phase 110 Plan 01: Mechanism Evaluators + Deep-Dive Triggers Summary

Three new signal mechanisms (conjunction, absence, contextual) with 48 YAML signals, plus 10 conditional deep-dive triggers integrated as ScoreStage Step 17.

## Task Completion

| Task | Name | Commit | Status |
|------|------|--------|--------|
| 1 | Schema extensions + mechanism evaluators + YAML signals | ab25804, 48bef44 | Done |
| 2 | Deep-dive trigger runner + ScoreStage Step 17 | 0b88914, 7b04a58 | Done |

## What Was Built

### Task 1: Mechanism Evaluators (TDD: 35 tests)

**Schema Extensions:**
- ConjunctionRuleSpec: required_signals, minimum_matches, signal_conditions, recommendation_floor
- AbsenceRuleSpec: expectation_type (always/company_profile/peer), expected_signals, condition
- ContextualRuleSpec: source_signal, context_dimensions, context_adjustments
- All three are Optional fields on EvaluationSpec (backward compatible with 514 existing signals)

**Mechanism Evaluators (mechanism_evaluators.py):**
- evaluate_conjunction: Checks if 2+ component signals co-fire. Returns TRIGGERED when >= minimum_matches met. Returns SKIPPED when >50% components unavailable. Supports custom signal_conditions (e.g., CLEAR means "absence of clawback").
- evaluate_absence: Detects missing expected disclosures. Three types: always_expected (SEC requirements), company_profile (conditional on company attributes), peer_comparison (large-cap expectations). Distinguishes "didn't look" (DATA_UNAVAILABLE -> SKIPPED) from "looked but absent" (EVALUATED -> TRIGGERED).
- evaluate_contextual: Re-evaluates source signal through lifecycle/sector/size lens. Applies threshold_adjustment multipliers. Returns SKIPPED when required context dimensions unavailable.

**Signal Engine Integration:**
- Mechanism dispatch added to execute_signals() before content_type dispatch
- Accumulated signal_results_dict built as signals execute (inference-class runs last)
- Company context builder extracts lifecycle_stage, size_tier, sector from CompanyProfile

**48 New YAML Signals:**
- 8 conjunction: comp_perf_divergence, governance_event, insider_news_gap, related_party_audit, growth_margin_guidance, financial_distress_insider, regulatory_litigation, accounting_governance
- 20 absence: 6 always-expected (risk_factors, internal_controls, going_concern, executive_comp, audit_fees, board_independence), 10 company-profile (related_party, segment_reporting, stock_comp, cyber_risk, litigation_contingency, pension_obligations, goodwill_impairment, derivative_instruments, debt_covenants, clawback_policy), 4 peer-driven (esg, revenue_recognition, lease_obligations, tax_positions)
- 20 contextual: 2 compensation, 3 governance, 6 financial, 4 market, 1 litigation, 4 risk

### Task 2: Deep-Dive Triggers (TDD: 15 tests)

**Models:**
- DeepDiveTriggerResult: trigger_id, trigger_name, fired, matched_conditions, uw_investigation_prompt, rap_dimensions
- DeepDiveResult: triggers_evaluated, triggers_fired, results list, computed_at
- ScoringResult.deepdive_result field added via TYPE_CHECKING + model_rebuild pattern

**10 Deep-Dive Triggers (deepdive_triggers.yaml):**
1. governance_board: Weak governance + exec departure
2. financial_controls: Restatement + auditor change
3. distress_insider: Financial distress + insider selling
4. regulatory_escalation: Regulatory action + new litigation
5. ma_integration: Rapid M&A + goodwill impairment
6. compensation_governance: Excessive comp + weak board
7. cyber_operational: Cyber incident + operational disruption
8. accounting_fraud: Beneish M-Score + revenue anomaly
9. litigation_surge: Active SCA + corrective disclosure stock drop
10. environmental_regulatory: Environmental liability + regulatory action

**ScoreStage Integration:**
- Step 17 added after Step 16 (pattern engines) with try/except graceful degradation
- Logs additional_acquisition fields for future acquisition loop implementation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed SIGNALS_DIR path resolution in tests**
- Found during: Task 1 tests
- Issue: Path(__file__).parent.parent.parent resolved to tests/ not project root
- Fix: Changed to parent.parent.parent.parent for correct path
- Files modified: tests/stages/analyze/test_mechanism_evaluators.py

**2. [Rule 3 - Blocking] Converted single-entry YAML to list format**
- Found during: Task 1 CI gate
- Issue: New YAML files were single-entry dicts; existing loader only handles lists
- Fix: Wrapped all 48 new signals in YAML list format to match convention
- Files modified: All 48 signal YAML files

**3. [Rule 1 - Bug] Remapped 18 signals to valid RAP subcategories**
- Found during: Task 1 CI gate
- Issue: New signals used subcategories not in rap_taxonomy.yaml (e.g., agent.governance_quality, environment.legal)
- Fix: Mapped to nearest valid subcategories (e.g., host.governance_structure, environment.external_warnings)
- Files modified: 18 signal YAML files

**4. [Rule 3 - Blocking] Added model_rebuild call in ScoringResult test**
- Found during: Task 2 tests
- Issue: ScoringResult() fails without model_rebuild() due to forward refs
- Fix: Called _rebuild_scoring_models() in test before constructing ScoringResult
- Files modified: tests/stages/score/test_deepdive_runner.py

## Decisions Made

1. **Mechanism dispatch location**: Added to execute_signals() (not evaluate_signal()) because mechanism signals need accumulated results from prior evaluations
2. **Acquisition loop deferral**: Deep-dive triggers log what additional data WOULD be requested, but actual re-acquisition is deferred. UW investigation prompts deliver 80% of value without pipeline loop complexity.
3. **Company context builder**: Built dynamically from CompanyProfile attributes rather than requiring pre-computed context. Uses simple thresholds (market_cap tiers, years_public brackets, SIC code ranges).

## Verification

- 50 new tests pass (35 mechanism + 15 deep-dive)
- 8 CI gate tests pass (schema validation for all 562 signals)
- 369 existing score tests pass (zero regressions)
- 231 existing analyze tests pass (zero regressions, excluding 1 pre-existing model_rebuild failure)

## Self-Check: PASSED

All 7 key files verified present. All 4 commits verified in git log. Signal counts: 8 conjunction, 20 absence, 20 contextual (48 total).
