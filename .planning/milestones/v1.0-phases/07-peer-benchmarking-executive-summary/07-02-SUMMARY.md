# Phase 7 Plan 2: Executive Summary Synthesis -- Key Findings, Thesis, Pipeline Integration

---
phase: 07
plan: 02
subsystem: benchmark
tags: [executive-summary, key-findings, thesis, ranking, synthesis]
depends_on:
  requires: [07-01]
  provides: [executive-summary-complete, key-findings-ranker, thesis-templates]
  affects: [phase-08]
tech-stack:
  added: []
  patterns: [multi-signal-ranking, risk-type-templates, positive-indicator-catalog]
key-files:
  created:
    - src/do_uw/stages/benchmark/key_findings.py
    - src/do_uw/stages/benchmark/positive_indicators.py
    - src/do_uw/stages/benchmark/thesis_templates.py
    - src/do_uw/stages/benchmark/summary_builder.py
    - tests/test_executive_summary.py
  modified:
    - src/do_uw/stages/benchmark/__init__.py
decisions:
  - id: "07-02-01"
    decision: "Split key_findings.py + positive_indicators.py for 500-line compliance"
    context: "Original key_findings.py was 669 lines; check functions + catalog separated"
  - id: "07-02-02"
    decision: "Module-level check functions (not lambdas) for PositiveIndicator.check_fn"
    context: "Pyright strict compliance -- lambdas in dataclass fields get Unknown type"
  - id: "07-02-03"
    decision: "No BenchmarkStage mock needed in CLI tests"
    context: "BenchmarkStage handles None/empty scoring gracefully; CLI tests pass as-is"
  - id: "07-02-04"
    decision: "Separate test file (test_executive_summary.py) instead of adding to test_benchmark_stage.py"
    context: "test_benchmark_stage.py already 558 lines; new tests would exceed 500-line limit"
  - id: "07-02-05"
    decision: "Tuple-based matched list for positives selection avoids storing PositiveIndicator reference"
    context: "Extracting fields into tuple avoids carrying Callable reference through sort"
metrics:
  duration: "9m 8s"
  completed: "2026-02-08"
  tests_added: 20
  tests_total: 974
  type_errors: 0
  lint_errors: 0
---

## One-liner

Multi-signal key findings ranker (40/20/20/20 weights), 7 risk-type thesis templates, and summary builder populating all SECT1 fields from pipeline state.

## What Was Built

### Key Findings Ranker (`key_findings.py` -- 369 lines)

**Key negatives selection (SECT1-03):**
- Multi-signal ranking with 4-factor composite score
- Scoring impact (40%): points deducted normalized to 0-1
- Recency (20%): trajectory-based proxy (NEW=1.0, WORSENING=0.8)
- Trajectory (20%): WORSENING > NEW > STABLE > IMPROVING
- Claim correlation (20%): allegation theory exposure from AllegationMapping
- Three candidate sources: FlaggedItems, high-deduction FactorScores (>=3 pts), PatternMatches above BASELINE
- Returns top 5 sorted by composite ranking score

**Key positives selection (SECT1-04):**
- 11 positive indicators covering SECT2-SECT7 domains
- Each indicator has a module-level check function (pyright strict)
- Conditions: no_active_sca, clean_audit, no_sec_enforcement, strong_governance, no_distress, stable_leadership, low_short_interest, independent_board, forum_selection, positive_fcf, low_volatility
- Sorted by scoring_relevance (10.0 for no_active_sca down to 5.0 for low_volatility)
- Returns top 5 matched indicators

### Positive Indicators (`positive_indicators.py` -- 338 lines)

- `PositiveIndicator` dataclass with `Callable[[AnalysisState], bool]` check_fn
- 11 public check functions with defensive None handling
- `build_positive_indicators()` factory returns catalog
- Split from key_findings.py for 500-line compliance

### Thesis Templates (`thesis_templates.py` -- 392 lines)

- 7 risk-type-specific template functions
- Professional consulting report tone
- Company-specific data filled from scoring, inherent risk, allegation mapping
- Each template includes: risk descriptor, quality score, tier label, top factor narrative, primary theory, base rate, adjusted rate
- Distinct narratives for: GROWTH_DARLING (high-growth disclosure risk), DISTRESSED (fiduciary/Side A), BINARY_EVENT (concentrated event), GUIDANCE_DEPENDENT (earnings miss-and-drop), REGULATORY_SENSITIVE (enforcement/compliance), TRANSFORMATION (transition risk), STABLE_MATURE (monitor deterioration)

### Summary Builder (`summary_builder.py` -- 238 lines)

- `build_executive_summary(state, inherent_risk) -> ExecutiveSummary`
- Orchestrates all SECT1 population:
  - SECT1-01: CompanySnapshot from state.company
  - SECT1-02: InherentRiskBaseline (passed in)
  - SECT1-03: Key negatives via select_key_negatives
  - SECT1-04: Key positives via select_key_positives
  - Thesis: Via generate_thesis with risk type dispatch
  - SECT1-07: DealContext (placeholder in ticker-only mode)
- Graceful handling of None scoring data throughout

### BenchmarkStage Update (`__init__.py` -- 203 lines)

- Replaced Steps 5+6 (partial snapshot + partial ExecutiveSummary init) with single `build_executive_summary` call
- Removed `_build_company_snapshot` (moved to summary_builder.py)
- BenchmarkStage now produces complete ExecutiveSummary in one step

### Tests (`test_executive_summary.py` -- 20 tests)

- 5 key negatives tests: flagged items, factor scores, fewer than 5, empty, ranking order
- 4 key positives tests: clean company, problematic company, sorted by relevance, max 5
- 5 thesis tests: GROWTH_DARLING, DISTRESSED, all 7 types distinct, no top factor, no inherent risk
- 5 summary builder tests: complete summary, serialization round-trip, deal context placeholder, no scoring data, key findings counts
- 1 state completeness test: BenchmarkStage with mocked config, all SECT1 + SECT2-7 populated

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Split key_findings.py + positive_indicators.py**
- **Found during:** Task 1
- **Issue:** key_findings.py was 669 lines, exceeding 500-line limit
- **Fix:** Extracted PositiveIndicator dataclass, 11 check functions, and catalog builder into positive_indicators.py (338 lines)
- **Files created:** positive_indicators.py
- **Commit:** e9a3d13

**2. [Rule 1 - Bug] Fixed CompanyIdentity.name -> .legal_name**
- **Found during:** Task 1 type checking
- **Issue:** Plan referenced `state.company.identity.name` but CompanyIdentity has `legal_name` not `name`
- **Fix:** Changed to `state.company.identity.legal_name`
- **Files modified:** summary_builder.py
- **Commit:** e9a3d13

**3. [Rule 1 - Bug] Fixed PatternMatch import from scoring.py not scoring_output.py**
- **Found during:** Task 1 type checking
- **Issue:** PatternMatch is defined in scoring.py, not scoring_output.py
- **Fix:** Import from `do_uw.models.scoring` instead of `do_uw.models.scoring_output`
- **Files modified:** key_findings.py
- **Commit:** e9a3d13

## Decisions Made

| ID | Decision | Rationale |
|---|---|---|
| 07-02-01 | Split key_findings.py + positive_indicators.py | 500-line compliance (669 -> 369 + 338) |
| 07-02-02 | Module-level check functions for PositiveIndicator | Pyright strict: lambdas in dataclass get Unknown type |
| 07-02-03 | No BenchmarkStage mock in CLI tests | Graceful None handling; less mocking is better |
| 07-02-04 | Separate test_executive_summary.py | test_benchmark_stage.py already 558 lines |
| 07-02-05 | Tuple-based positives sorting | Avoids carrying Callable reference through sort |

## Commits

| Hash | Message |
|---|---|
| e9a3d13 | feat(07-02): key findings ranker, thesis templates, summary builder |
| 413b968 | feat(07-02): wire summary builder into BenchmarkStage, add tests |

## Next Phase Readiness

Phase 7 is now complete. All SECT1-SECT7 data exists in the state file:

- **SECT1**: ExecutiveSummary (snapshot, inherent_risk, key_findings, thesis, deal_context)
- **SECT2**: CompanyProfile (identity, financials, market data)
- **SECT3**: ExtractedFinancials (statements, distress, audit, peers)
- **SECT4**: MarketSignals (stock, short interest, insider trading, earnings, adverse events)
- **SECT5**: GovernanceData (leadership, board, comp, ownership, sentiment, quality score)
- **SECT6**: LitigationLandscape (SCAs, SEC enforcement, derivatives, defense, industry patterns, SOL)
- **SECT7**: ScoringResult (10 factors, red flags, patterns, risk type, allegations, claim probability, severity, tower)

Phase 8 (Document Rendering) can now read all data from `state` to generate Word/PDF/Markdown output.
No blockers. No pending concerns.
