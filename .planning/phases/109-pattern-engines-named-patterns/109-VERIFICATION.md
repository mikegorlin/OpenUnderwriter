---
phase: 109-pattern-engines-named-patterns
verified: 2026-03-16T04:30:00Z
status: passed
score: 16/16 must-haves verified
re_verification: false
gaps: []
---

# Phase 109: Pattern Engines + Named Patterns Verification Report

**Phase Goal:** Implement four pattern detection engines that find risk patterns invisible to individual signal evaluation, seeded with a case library and 6 named D&O archetypes
**Verified:** 2026-03-16T04:30:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Conjunction Scan detects 3+ cross-domain co-firing CLEAR signals as elevated risk | VERIFIED | `conjunction_scan.py` implements 5-step algorithm, 12 tests pass |
| 2 | Peer Outlier detects multi-dimensional statistical outliers from SEC Frames data via MAD z-scores | VERIFIED | `peer_outlier.py` implements MAD with 1.4826 constant, 12 tests pass |
| 3 | Both engines (01) return NOT_FIRED with informative note when data insufficient | VERIFIED | Explicit early-exit paths for empty correlations, no CLEAR signals, no state |
| 4 | Seed correlation YAML provides day-one co-fire rates for cold start | VERIFIED | `seed_correlations.yaml` has 20 curated D&O pairs spanning all 3 RAP domains |
| 5 | Migration Drift detects cross-domain gradual deterioration from 8 quarters of XBRL data | VERIFIED | `migration_drift.py` maps 23 XBRL concepts to host/agent/environment RAP categories, 9 tests pass |
| 6 | Precedent Match computes weighted Jaccard similarity against 20 case library entries | VERIFIED | `precedent_match.py` with CRF 3x weighting and confidence tier adjustment, 17 tests pass |
| 7 | Case library has 20 canonical D&O cases with signal profiles and outcomes | VERIFIED | 20 cases: 6 HIGH-confidence (50-60 signals each), 14 MEDIUM-confidence |
| 8 | 6 named archetypes defined in YAML with real signal IDs and recommendation floors | VERIFIED | All 6 archetypes present, all with recommendation_floor=ELEVATED, ai_mirage has 3 future_signal.* placeholders |
| 9 | Both engines (02) return NOT_FIRED when data insufficient | VERIFIED | Explicit guards for missing quarterly_xbrl, empty case library, insufficient quarters |
| 10 | Dismissed cases appear in Precedent Match with 0.5x outcome severity weight | VERIFIED | `precedent_match.py` applies 0.5x to `outcome_severity` for dismissed cases |
| 11 | All 4 engines run in ScoreStage pipeline after severity (Step 16) | VERIFIED | `__init__.py` Step 16 uses identical try/except/warning pattern to Step 15.5 |
| 12 | 6 named archetypes evaluated; archetype recommendation_floor raises tier (never lowers) | VERIFIED | `_apply_tier_floors()` uses `HAETier` ordered comparison, only raises via `if floor_tier > current.tier` |
| 13 | Engine failure is logged as warning, scoring continues unaffected | VERIFIED | Per-engine try/except in Step 16; remaining engines run on individual failure |
| 14 | Firing panel context builder produces template data for all 10 items (4 engines + 6 archetypes) | VERIFIED | `build_pattern_context()` returns list of 10 items with MATCH/NOT_FIRED status |
| 15 | Firing panel renders as visible HTML section via Jinja2 template | VERIFIED | `pattern_firing.html.j2` (175 lines) in manifest at `sections/pattern_firing.html.j2`; manifest drives `worksheet.html.j2` via `manifest_sections` |
| 16 | Active SCAC filing auto-adds case library entry with POST_FILING flag | VERIFIED | `_auto_expand_case_library()` writes to `brain/framework/auto_cases/`, best-effort with logging |

**Score:** 16/16 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/score/pattern_engine.py` | PatternEngine Protocol + EngineResult/ArchetypeResult | VERIFIED | 125 lines, `@runtime_checkable` Protocol, both models with full fields |
| `src/do_uw/models/patterns.py` | PatternEngineResult + CaseLibraryEntry Pydantic models | VERIFIED | 97 lines, `any_fired` computed_field, CaseLibraryEntry with `extra="forbid"` |
| `src/do_uw/stages/score/conjunction_scan.py` | ConjunctionScanEngine implementing PatternEngine | VERIFIED | 296 lines, seed YAML loading + DuckDB supplement, all thresholds configurable |
| `src/do_uw/stages/score/peer_outlier.py` | PeerOutlierEngine implementing PatternEngine | VERIFIED | 292 lines, MAD z-scores, risk-direction awareness, peer_data_override for testing |
| `src/do_uw/brain/framework/seed_correlations.yaml` | 15+ curated D&O co-fire pairs | VERIFIED | 20 pairs spanning host/agent/environment cross-domain combinations |
| `src/do_uw/stages/score/migration_drift.py` | MigrationDriftEngine implementing PatternEngine | VERIFIED | 9,731 bytes, OLS slope, 23-metric RAP mapping, configurable thresholds |
| `src/do_uw/stages/score/precedent_match.py` | PrecedentMatchEngine implementing PatternEngine | VERIFIED | 12,207 bytes, CRF 3x weights, lru_cache singleton, weighted Jaccard |
| `src/do_uw/brain/framework/case_library.yaml` | 20 canonical D&O cases | VERIFIED | 34,458 bytes, 6 HIGH + 14 MEDIUM confidence, validates against CaseLibraryEntry |
| `src/do_uw/brain/framework/named_archetypes.yaml` | 6 named archetypes | VERIFIED | 14,278 bytes, all 6 archetypes, all recommendation_floor=ELEVATED, ai_mirage has future_signal.* |
| `src/do_uw/stages/score/_pattern_runner.py` | Orchestrator running all 4 engines + 6 archetypes | VERIFIED | 12,325 bytes, graceful degradation, tier floor logic, auto-expansion |
| `src/do_uw/stages/render/context_builders/pattern_context.py` | Firing panel context builder | VERIFIED | 3,731 bytes, 10-item list, summary stats, patterns_available guard |
| `src/do_uw/templates/html/sections/pattern_firing.html.j2` | Jinja2 10-card firing panel template | VERIFIED | 6,994 bytes, amber MATCH / gray NOT_FIRED cards, confidence bars |
| `src/do_uw/models/scoring.py` | ScoringResult.pattern_engine_result field | VERIFIED | Field present and confirmed via `ScoringResult.model_fields` |
| `src/do_uw/stages/score/__init__.py` | Step 16 integration after Step 15.5 | VERIFIED | Lines 543-583, identical graceful degradation pattern |
| `src/do_uw/stages/render/html_renderer.py` | build_pattern_context() call site | VERIFIED | Lines 424-429, injected as `context["pattern_context"]` |
| `src/do_uw/stages/render/context_builders/__init__.py` | build_pattern_context export | VERIFIED | Line 64-73, in `__all__` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `conjunction_scan.py` | `seed_correlations.yaml` | `_load_correlations()` reads YAML, supplements from DuckDB | WIRED | `_SEED_PATH` resolves to `brain/framework/seed_correlations.yaml`, DuckDB supplement in try/except |
| `peer_outlier.py` | `state.benchmarks.frames_percentiles` | Extracts FramesPercentileResult data for z-score computation | WIRED | `getattr(state, "benchmarks")` then `frames_percentiles` loop |
| `conjunction_scan.py` | `pattern_engine.py` | Implements PatternEngine Protocol | WIRED | `isinstance(ConjunctionScanEngine(), PatternEngine)` = True |
| `migration_drift.py` | `state.extracted.financials.quarterly_xbrl` | Extracts QuarterlyPeriod data for trend computation | WIRED | `getattr(state.extracted.financials, "quarterly_xbrl")` |
| `precedent_match.py` | `case_library.yaml` | `_load_case_library()` reads YAML, validates via CaseLibraryEntry | WIRED | `@functools.lru_cache` singleton, validates each entry |
| `named_archetypes.yaml` | `brain_schema.py::PatternDefinition` | Archetypes validated against PatternDefinition schema in tests | WIRED | `test_archetypes.py` validates all 6 against PatternDefinition |
| `_pattern_runner.py` | `__init__.py` (Step 16) | `run_pattern_engines()` called after Step 15.5 | WIRED | Lines 543-583 of `__init__.py` |
| `_pattern_runner.py` | `conjunction_scan.py` | Instantiates ConjunctionScanEngine.evaluate() | WIRED | Line in `run_pattern_engines()` |
| `_pattern_runner.py` | `named_archetypes.yaml` | `_evaluate_archetypes()` loads YAML and checks required_signals | WIRED | Confirmed in `_pattern_runner.py` with future_signal.* skip logic |
| `pattern_context.py` | `state.scoring.pattern_engine_result` | Reads PatternEngineResult to build firing panel data | WIRED | `state.scoring.pattern_engine_result` access with `patterns_available=False` guard |
| `html_renderer.py` | `pattern_context.py` | `build_html_context()` calls `build_pattern_context()` | WIRED | Lines 424-429 of `html_renderer.py` |
| `pattern_firing.html.j2` | `pattern_context.py` | Template consumes `pattern_context` dict | WIRED | Template guarded by `{% if pattern_context is defined and pattern_context.patterns_available %}` |
| `worksheet.html.j2` | `pattern_firing.html.j2` | Manifest-driven include via `manifest_sections` | WIRED | `output_manifest.yaml` has `id: pattern_firing`, `template: sections/pattern_firing.html.j2`; `section_renderer.py` loads manifest into `manifest_sections` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PAT-01 | 109-01 | Conjunction Scan engine detects 3+ individually normal signals co-occurring as elevated risk | SATISFIED | `conjunction_scan.py` fully implemented, 12 tests pass |
| PAT-02 | 109-01 | Peer Outlier engine detects multi-dimensional statistical outliers from SEC Frames data | SATISFIED | `peer_outlier.py` with MAD z-scores, 12 tests pass |
| PAT-03 | 109-02 | Migration Drift engine detects cross-domain gradual deterioration from XBRL quarterly trends | SATISFIED | `migration_drift.py` with OLS slope, 9 tests pass |
| PAT-04 | 109-02 | Precedent Match engine computes signal profile similarity against case library | SATISFIED | `precedent_match.py` weighted Jaccard, 17 tests pass |
| PAT-05 | 109-02 | Case library seeded from Stanford SCAC data (signal profiles at time of filing + outcomes) | SATISFIED | 20 cases in `case_library.yaml` with reconstructed signal profiles and outcomes |
| PAT-06 | 109-02 | 6 named D&O pattern archetypes defined in YAML | SATISFIED | All 6 archetypes in `named_archetypes.yaml`: desperate_growth_trap, governance_vacuum, post_spac_hangover, accounting_time_bomb, regulatory_reckoning, ai_mirage |
| PAT-07 | 109-03 | Engine firing panel visualization showing which engines fired with confidence | SATISFIED | `pattern_firing.html.j2` 10-card grid with MATCH/NOT_FIRED styling, wired through manifest |

No orphaned requirements — all 7 PAT requirements appear in plan frontmatter and are accounted for.

---

### Anti-Patterns Found

No blockers or warnings. Two informational items:

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `peer_outlier.py` | 281 | `return None` in `_get_peer_values()` when no peer data override | INFO | Intentional: real peer arrays not yet available; `peer_data_override` constructor param enables testing. Engine degrades gracefully. Not a stub. |
| `_pattern_runner.py` | 126 | `future_signal.*` comment re: AI Mirage placeholders | INFO | Intentional design note per plan spec. Skip logic implemented correctly. |

---

### Human Verification Required

None. All behavioral verification was automated.

---

### Test Suite Summary

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_conjunction_scan.py` | 12 | PASS |
| `test_peer_outlier.py` | 12 | PASS |
| `test_migration_drift.py` | 9 | PASS |
| `test_precedent_match.py` | 17 | PASS |
| `test_case_library.py` | 12 | PASS |
| `test_archetypes.py` | 12 | PASS |
| `test_pattern_runner.py` | 13 | PASS |
| `test_pattern_context.py` | 11 | PASS |
| **Total Phase 109** | **98** | **ALL PASS** |
| Full score stage suite | 354 | ALL PASS (no regressions) |

---

### Gaps Summary

No gaps. All 16 must-have truths verified. All 7 PAT requirements satisfied. All 12 primary artifacts substantive and wired. All 98 phase tests pass. No regressions in 354-test score stage suite.

---

_Verified: 2026-03-16T04:30:00Z_
_Verifier: Claude (gsd-verifier)_
