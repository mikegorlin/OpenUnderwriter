# Phase 7 Plan 1: BenchmarkStage, Percentile Engine, Inherent Risk Summary

---
phase: 07
plan: 01
subsystem: benchmark
tags: [benchmark, percentile, inherent-risk, executive-summary, pydantic]
depends_on:
  requires: [phase-06]
  provides: [benchmark-stage, executive-summary-models, inherent-risk-baseline]
  affects: [07-02, phase-08]
tech-stack:
  added: []
  patterns: [multiplicative-risk-adjustment, percentile-ranking, metric-registry]
key-files:
  created:
    - src/do_uw/models/executive_summary.py
    - src/do_uw/stages/benchmark/percentile_engine.py
    - src/do_uw/stages/benchmark/peer_metrics.py
    - src/do_uw/stages/benchmark/inherent_risk.py
    - tests/test_benchmark_stage.py
  modified:
    - src/do_uw/models/scoring.py
    - src/do_uw/models/state.py
    - src/do_uw/models/__init__.py
    - src/do_uw/brain/sectors.json
    - src/do_uw/stages/benchmark/__init__.py
decisions:
  - id: "07-01-01"
    decision: "Multiplicative inherent risk: base_rate * cap_multiplier * score_multiplier"
    rationale: "Actuarially sound -- each factor independent, easily calibrated"
  - id: "07-01-02"
    decision: "Closure default_factory for KeyFindings lists (not lambda)"
    rationale: "Pyright strict mode Unknown type avoidance per MEMORY.md"
  - id: "07-01-03"
    decision: "7-metric registry: market_cap, revenue, volatility, short_interest, leverage, quality_score, governance_score"
    rationale: "Covers SECT2-7 sections; peer data and sector baselines both supported"
  - id: "07-01-04"
    decision: "Ratio-to-baseline as percentile proxy when no peer distribution"
    rationale: "Sector baseline metrics lack peer values; ratio comparison is meaningful"
  - id: "07-01-05"
    decision: "SECT1-05 (ClaimProbability) and SECT1-06 (TowerRecommendation) not duplicated"
    rationale: "Already exist on ScoringResult; referenced from state.scoring directly"
metrics:
  duration: "9m 08s"
  completed: "2026-02-08"
  tests_added: 28
  tests_total: 954
  files_created: 5
  files_modified: 5
---

## One-liner

BenchmarkStage with multiplicative inherent risk baseline, 7-metric percentile engine, and ExecutiveSummary SECT1 Pydantic models.

## What Was Done

### Task 1: Executive Summary Models + BenchmarkResult Extension + sectors.json

Created `executive_summary.py` with SECT1-01 through SECT1-07 Pydantic models:
- **CompanySnapshot** (SECT1-01): ticker, name, market_cap, revenue, employees, industry, SIC, exchange
- **InherentRiskBaseline** (SECT1-02): multiplicative risk calculation with severity ranges
- **KeyFinding/KeyFindings** (SECT1-03/04): negative/positive findings with ranking
- **DealContext** (SECT1-07): placeholder for layer, premium, carrier info
- **UnderwritingThesis**: narrative synthesis of risk profile
- **ExecutiveSummary**: root container for all SECT1 sub-models

Extended `BenchmarkResult` with:
- `MetricBenchmark` model: per-metric benchmark details (value, percentile, peer count, baseline)
- `metric_details: dict[str, MetricBenchmark]` field
- `inherent_risk: InherentRiskBaseline | None` field

Extended `AnalysisState` with `executive_summary: ExecutiveSummary | None`.

Extended `sectors.json` with:
- `claim_base_rates`: per-sector SCA filing probability (BIOT 8.0%, TECH 6.0%, ... DEFAULT 3.9%)
- `market_cap_filing_multipliers`: mega 1.56x through micro 0.77x

### Task 2: Percentile Engine + Inherent Risk + Peer Metrics + BenchmarkStage + Tests

**percentile_engine.py** (74 lines):
- `percentile_rank()`: standard formula with higher/lower-is-better and tie handling
- `ratio_to_baseline()`: company-to-sector ratio computation

**inherent_risk.py** (267 lines):
- `compute_inherent_risk_baseline()`: 5-step multiplicative calculation
- Step 1: Sector base rate from claim_base_rates
- Step 2: Market cap multiplier from filing_multipliers (mega/large/mid/small/micro)
- Step 3: Score multiplier from tier (WIN 0.3-0.5x through NO_TOUCH 3.5x)
- Step 4: company_rate = base * cap_mult * score_mult
- Step 5: Severity ranges from scoring.json by_market_cap

**peer_metrics.py** (362 lines):
- 7-metric registry covering SECT2-SECT7
- Category 1 (peer data): market_cap, revenue from PeerCompany.peers
- Category 2 (sector baselines): volatility_90d, short_interest, leverage
- Category 3 (risk scores): quality_score, governance_score
- `compute_peer_rankings()`: extracts values, computes percentile ranks

**BenchmarkStage** (267 lines):
- Replaced stub with full 6-step implementation
- Step 1-3: Peer rankings and BenchmarkResult population
- Step 4: Inherent risk baseline computation
- Step 5-6: CompanySnapshot + ExecutiveSummary initialization

**Tests** (28 tests):
- 7 percentile rank tests (basic, empty, lower-is-better, ties, edge cases)
- 3 ratio-to-baseline tests
- 8 inherent risk tests (sectors, cap tiers, tier multipliers, severity, defaults)
- 5 peer metric tests (with peers, no peers, quality/governance/volatility)
- 5 BenchmarkStage tests (run, executive summary, validation, completion, details)

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

1. **Multiplicative inherent risk** -- base_rate * cap_multiplier * score_multiplier. Each factor independent, easily calibrated individually.

2. **Closure default_factory** for KeyFindings lists (`_default_findings_list()` function) instead of lambdas, per pyright strict compliance pattern from MEMORY.md.

3. **7-metric registry** covers all relevant sections (SECT2-7). Expandable by adding MetricDef entries.

4. **Ratio-to-baseline as percentile proxy** for sector baseline metrics where no peer distribution exists. Ratio > 1.0 = above baseline, converted to percentile scale.

5. **No SECT1-05/SECT1-06 duplication** -- ClaimProbability and TowerRecommendation already on ScoringResult, referenced directly.

## Test Results

- 28 new tests added (all passing)
- 954 total tests passing (0 regressions)
- 0 pyright errors, 0 ruff errors
- All files under 500 lines

## File Size Report

| File | Lines |
|------|-------|
| executive_summary.py | 286 |
| benchmark/__init__.py | 267 |
| benchmark/inherent_risk.py | 267 |
| benchmark/peer_metrics.py | 362 |
| benchmark/percentile_engine.py | 74 |
| test_benchmark_stage.py | 416 |

## Next Phase Readiness

Plan 07-02 can proceed immediately. It needs:
- `ExecutiveSummary` model (created, on state)
- `InherentRiskBaseline` (computed in BENCHMARK stage)
- `CompanySnapshot` (built in BENCHMARK stage)
- Remaining: key_findings, thesis, and summary_builder to be populated
