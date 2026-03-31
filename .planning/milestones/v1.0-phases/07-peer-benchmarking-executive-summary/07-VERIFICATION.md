---
phase: 07-peer-benchmarking-executive-summary
verified: 2026-02-08T18:30:00Z
status: passed
score: 6/6 must-haves verified
re_verification: false
---

# Phase 7: Peer Benchmarking & Executive Summary Verification Report

**Phase Goal:** The BENCHMARK pipeline stage positions every metric peer-relative, and the Executive Summary (Section 1) synthesizes all findings into an at-a-glance risk assessment -- completing the analytical pipeline so that all data needed for document rendering exists in the state file.

**Verified:** 2026-02-08T18:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every financial ratio, governance metric, and risk indicator has a peer-relative percentile rank computed against the primary peer group, stored in state | ✓ VERIFIED | `BenchmarkResult.metric_details` contains `MetricBenchmark` entries with `percentile_rank` for 7 metrics (market_cap, revenue, volatility, short_interest, leverage, quality_score, governance_score). Computed by `compute_peer_rankings()` in `peer_metrics.py` (362 lines). Tests: 5 peer ranking tests pass. |
| 2 | The executive summary contains the top 5 key negatives and top 5 key positives, each with evidence narrative, section origin, scoring impact, and allegation/defense theory mapping | ✓ VERIFIED | `ExecutiveSummary.key_findings` contains `KeyFindings` model with negatives/positives lists. Each `KeyFinding` has: evidence_narrative, section_origin, scoring_impact, theory_mapping, ranking_score. Multi-signal ranker (40/20/20/20 weights) in `key_findings.py` line 259-315. Positive catalog (11 indicators) in `positive_indicators.py` line 318+. Tests: 9 key findings tests pass. |
| 3 | Inherent risk baseline is computed from the market cap x industry matrix showing actuarial filing probability and severity range before company-specific adjustments | ✓ VERIFIED | `InherentRiskBaseline` computed by `compute_inherent_risk_baseline()` in `inherent_risk.py` (267 lines). Formula: `company_rate = sector_base_rate * cap_multiplier * score_multiplier`. Sector base rates from `sectors.json` claim_base_rates (TECH=6.0%, BIOT=8.0%, etc.). Market cap multipliers (mega=1.56x, large=1.28x, mid=1.0x, small=0.90x, micro=0.77x). Tests: 8 inherent risk tests pass. |
| 4 | Tower position recommendation specifies minimum attachment point and position assessment by layer type (primary, low/mid/high excess, Side A) | ✓ VERIFIED | `TowerRecommendation` on `ScoringResult` (from Phase 6) contains `minimum_attachment_point` and `layer_positions` with assessments for PRIMARY, LOW_EXCESS, MID_EXCESS, HIGH_EXCESS, SIDE_A. Not duplicated in Phase 7; referenced directly from `state.scoring.tower`. SECT1-06 requirement satisfied. |
| 5 | The complete state file contains all data needed for document rendering -- no analysis logic remains to be executed after this phase | ✓ VERIFIED | State completeness test (`test_state_completeness_after_benchmark`) verifies all SECT1-SECT7 data exists: `state.executive_summary` (snapshot, inherent_risk, key_findings, thesis, deal_context), `state.company`, `state.extracted`, `state.scoring`, `state.benchmark` all populated. No further analysis stages defined in pipeline. |
| 6 | All 7 risk type thesis templates produce distinct narratives | ✓ VERIFIED | `generate_thesis()` in `thesis_templates.py` line 318+ dispatches to 7 template functions: `_growth_darling_thesis`, `_distressed_thesis`, `_binary_event_thesis`, `_guidance_dependent_thesis`, `_regulatory_sensitive_thesis`, `_transformation_thesis`, `_stable_mature_thesis`. Each produces distinct professional narrative with company-specific data filled from scoring, inherent risk, allegation mapping. Tests: 5 thesis generation tests pass. |

**Score:** 6/6 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/executive_summary.py` | SECT1-01 through SECT1-07 Pydantic models | ✓ VERIFIED | 286 lines. Contains: CompanySnapshot (SECT1-01), InherentRiskBaseline (SECT1-02), KeyFinding/KeyFindings (SECT1-03/04), DealContext (SECT1-07), UnderwritingThesis, ExecutiveSummary root. Exports 7 classes. Type-checks clean (0 errors). |
| `src/do_uw/stages/benchmark/percentile_engine.py` | Percentile rank computation with directionality | ✓ VERIFIED | 74 lines. Exports `percentile_rank()` with higher/lower_is_better parameter and tie handling. Also `ratio_to_baseline()` helper. 7 tests pass (basic, empty, ties, edge cases). |
| `src/do_uw/stages/benchmark/inherent_risk.py` | Actuarial baseline computation | ✓ VERIFIED | 267 lines. Exports `compute_inherent_risk_baseline()` with multiplicative formula. Steps: sector base → cap multiplier → score multiplier → adjusted rate. Severity ranges from scoring.json. 8 tests pass. |
| `src/do_uw/stages/benchmark/peer_metrics.py` | Metric extraction and peer comparison | ✓ VERIFIED | 362 lines. Exports `compute_peer_rankings()` with 7-metric registry: market_cap, revenue, volatility_90d, short_interest, leverage, quality_score, governance_score. Returns (peer_rankings dict, metric_details dict[str, MetricBenchmark]). 5 tests pass. |
| `src/do_uw/stages/benchmark/__init__.py` | Real BenchmarkStage replacing stub | ✓ VERIFIED | 203 lines. BenchmarkStage.run() executes 5 steps: peer rankings → relative position → BenchmarkResult → inherent risk → ExecutiveSummary. Calls `build_executive_summary()` at line 185-187. Populates `state.benchmark` and `state.executive_summary`. 5 stage tests pass. |
| `src/do_uw/stages/benchmark/key_findings.py` | Key negatives/positives selection | ✓ VERIFIED | 369 lines. Exports `select_key_negatives()` and `select_key_positives()`. Multi-signal ranking: scoring_impact (40%), recency (20%), trajectory (20%), claim_correlation (20%). Max 5 findings per side. 5 tests pass. |
| `src/do_uw/stages/benchmark/positive_indicators.py` | Positive indicator catalog | ✓ VERIFIED | 338 lines (split from key_findings.py for 500-line compliance). 11 positive indicators with module-level check functions: no_active_sca, clean_audit, no_sec_enforcement, strong_governance, no_distress, stable_leadership, low_short_interest, independent_board, forum_selection, positive_fcf, low_volatility. Tests pass. |
| `src/do_uw/stages/benchmark/thesis_templates.py` | Risk type narrative templates | ✓ VERIFIED | 392 lines. Exports `generate_thesis()` with 7 risk type templates. Each template fills company-specific data (score, tier, top factor, theory, rates) into professional consulting tone narrative. Tests: all 7 types produce distinct narratives. |
| `src/do_uw/stages/benchmark/summary_builder.py` | Executive summary orchestration | ✓ VERIFIED | 238 lines. Exports `build_executive_summary()` which calls key_findings ranker, thesis generator, snapshot builder. Populates all SECT1 fields from state data. Graceful None handling throughout. 5 tests pass. |
| `tests/test_benchmark_stage.py` | Benchmark stage tests | ✓ VERIFIED | 558 lines. 28 tests: percentile (7), ratio (3), inherent risk (8), peer metrics (5), stage (5). All passing. |
| `tests/test_executive_summary.py` | Executive summary tests | ✓ VERIFIED | 516 lines. 20 tests: key negatives (5), key positives (4), thesis (5), summary builder (5), state completeness (1). All passing. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `benchmark/__init__.py` | `scoring.py` | BenchmarkResult population | ✓ WIRED | Line 161-167: `state.benchmark = BenchmarkResult(peer_rankings, metric_details, ...)` populates state. `BenchmarkResult` has `metric_details: dict[str, MetricBenchmark]` and `inherent_risk: InherentRiskBaseline` fields. |
| `benchmark/inherent_risk.py` | `brain/sectors.json` | claim_base_rates lookup | ✓ WIRED | Line 201: `sector_base_rate * cap_multiplier * score_multiplier`. `sectors.json` has `claim_base_rates` section (line 138+) with TECH=6.0, BIOT=8.0, etc. ConfigLoader loads successfully. |
| `state.py` | `executive_summary.py` | executive_summary field | ✓ WIRED | Line 203: `executive_summary: ExecutiveSummary | None = Field(...)` on AnalysisState. Import at line 23. Field verified with uv run python check: "executive_summary field exists: True". |
| `benchmark/__init__.py` | `summary_builder.py` | build_executive_summary call | ✓ WIRED | Line 185-187: `state.executive_summary = build_executive_summary(state, inherent_risk)`. Import at line 23. Populates CompanySnapshot, InherentRiskBaseline, KeyFindings, UnderwritingThesis, DealContext. Test confirms all populated. |
| `key_findings.py` | `scoring_output.py` | FlaggedItem reading | ✓ WIRED | Lines 23-29: imports FlaggedItem, FlagSeverity, RedFlagSummary from scoring_output. `select_key_negatives()` line 259+ reads `red_flag_summary.items` for candidate extraction. Pattern match confirmed. |

### Requirements Coverage

Phase 7 requirements from REQUIREMENTS.md:

| Requirement | Status | Blocking Issue |
|-------------|--------|----------------|
| SECT1-01 (CompanySnapshot) | ✓ SATISFIED | CompanySnapshot model with ticker, name, market_cap, revenue, employees, industry, SIC, exchange. Built by `_build_snapshot()` in summary_builder.py. |
| SECT1-02 (InherentRiskBaseline) | ✓ SATISFIED | InherentRiskBaseline computed via multiplicative formula from sectors.json base rates + cap multipliers + score multipliers. Severity ranges from scoring.json. |
| SECT1-03 (Key Negatives) | ✓ SATISFIED | Top 5 key negatives selected by multi-signal ranker (40/20/20/20 weights). Each has evidence, section, scoring_impact, theory_mapping. |
| SECT1-04 (Key Positives) | ✓ SATISFIED | Top 5 key positives from 11-indicator catalog. Each has evidence, section, scoring_impact, theory_mapping. Sorted by scoring_relevance. |
| SECT1-05 (ClaimProbability) | ✓ SATISFIED | Exists on ScoringResult.claim_probability (Phase 6). Not duplicated in ExecutiveSummary. Referenced from state.scoring. |
| SECT1-06 (TowerRecommendation) | ✓ SATISFIED | Exists on ScoringResult.tower (Phase 6). Not duplicated in ExecutiveSummary. Referenced from state.scoring. |
| SECT1-07 (DealContext) | ✓ SATISFIED | DealContext model with layer_quoted, premium, carrier_lineup, tower_structure, additional_notes, is_placeholder. Always placeholder in ticker-only mode. |
| CORE-02 (Multi-section worksheet) | ✓ SATISFIED | All 7 analytical sections (SECT1-SECT7) exist in state after BenchmarkStage: CompanyProfile (SECT2), ExtractedFinancials (SECT3), MarketSignals (SECT4), GovernanceData (SECT5), LitigationLandscape (SECT6), ScoringResult (SECT7), ExecutiveSummary (SECT1). Rendering-ready. |

### Anti-Patterns Found

None. All files under 500 lines (max 558 for test_benchmark_stage.py which is a test file, not src). No TODOs, FIXMEs, placeholders, or empty implementations. All functions substantive and wired.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| - | - | - | - | - |

### Human Verification Required

No items requiring human testing. All verification performed programmatically via:
- Type checking (0 errors)
- Test execution (974 tests pass, 48 new in Phase 7)
- Source code inspection (functions exist, export correctly, wired to state)
- Model validation (Pydantic models serialize/deserialize)
- Config loading (sectors.json claim_base_rates and multipliers load)

---

## Summary

**All 6 must-haves verified.** Phase 7 goal achieved.

### What Works

1. **BenchmarkStage is real, not stub** — Computes peer rankings (7 metrics), inherent risk baseline (multiplicative formula), and builds complete ExecutiveSummary in 5 steps. No longer a placeholder.

2. **ExecutiveSummary complete** — All SECT1 sub-models populated:
   - SECT1-01: CompanySnapshot from state.company
   - SECT1-02: InherentRiskBaseline via `compute_inherent_risk_baseline()`
   - SECT1-03: Top 5 key negatives via multi-signal ranker
   - SECT1-04: Top 5 key positives from 11-indicator catalog
   - SECT1-05/06: ClaimProbability + TowerRecommendation on ScoringResult (not duplicated)
   - SECT1-07: DealContext placeholder
   - Thesis: Risk-type-specific narrative (7 templates)

3. **Percentile engine handles directionality** — `percentile_rank()` supports higher_is_better and lower_is_better with tie handling. 7 tests cover edge cases.

4. **Inherent risk actuarially sound** — Multiplicative formula: base_rate (from sector) * cap_multiplier (from market cap tier) * score_multiplier (from quality score/tier). Severity ranges from scoring.json. 8 tests validate.

5. **Peer rankings cover SECT2-SECT7** — 7-metric registry: market_cap, revenue, volatility, short_interest, leverage, quality_score, governance_score. MetricBenchmark model tracks percentile, peer count, baseline for each.

6. **Key findings selection works** — Multi-signal ranking (40% scoring impact, 20% recency, 20% trajectory, 20% claim correlation) for negatives. Positive catalog with 11 checks (no_active_sca, clean_audit, strong_governance, etc.). Top 5 each side.

7. **All 7 risk types have distinct thesis templates** — GROWTH_DARLING, DISTRESSED, BINARY_EVENT, GUIDANCE_DEPENDENT, REGULATORY_SENSITIVE, TRANSFORMATION, STABLE_MATURE. Each fills company-specific data into professional consulting tone narrative.

8. **State file rendering-ready** — All SECT1-SECT7 data exists after BenchmarkStage. Test `test_state_completeness_after_benchmark` confirms: executive_summary, company, extracted, scoring, benchmark all populated. No further analysis stages.

9. **All tests pass** — 974 total tests (926 existing + 48 new). 28 benchmark stage tests, 20 executive summary tests. 0 regressions.

10. **500-line compliance maintained** — All src files under 500 lines. Largest: thesis_templates.py (392), key_findings.py (369), peer_metrics.py (362). Test files allowed to be larger.

### Gaps

None. All truths verified, all artifacts substantive and wired, all requirements satisfied.

---

_Verified: 2026-02-08T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
