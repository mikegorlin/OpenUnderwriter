# Phase 29: Architectural Cleanup & Stage Boundary Enforcement

## Status: COMPLETE (2026-02-15)

## Commits
- `27adc2f` — refactor(phase-29): enforce stage boundaries, rebalance brain checks, delete dead code
- `b192758` — fix: BoardForensicProfile.director_name -> name.value in sect5 render
- `9a6809d` — feat: parallel LLM extraction, filing prioritization, real-time progress

## What Was Done

### Plan 29-01: Dead Code Deletion
- Deleted `knowledge/pricing_inference.py` (rate decay engine, zero callers)
- Deleted `knowledge/traceability.py` (never invoked)
- ~~Deleted `knowledge/ai_impact_models.py`~~ — **correction (Phase 45 audit)**: this file was NOT deleted. It was replaced/updated and remains live at `src/do_uw/knowledge/ai_impact_models.py` (335 lines). `get_ai_impact_model()` is actively called by `src/do_uw/stages/score/ai_risk_scoring.py:76`. The "1,188 lines removed" count in this summary overcounts by 335 lines.
- Removed deprecated fields from governance/market models
- Fixed model exports in `models/__init__.py`
- **1,188 lines removed**

### Plan 29-02: Move Analysis Out of EXTRACT
Moved 9 files (~6,700 lines) from `stages/extract/` to `stages/analyze/`:
- distress_models.py, distress_formulas.py (financial distress scoring)
- adverse_events.py (composite adverse event scoring)
- defense_assessment.py (defense strength judgment)
- industry_claims.py (SIC -> legal theory mapping)
- earnings_quality.py (accruals/OCF quality scoring)
- text_signals.py (keyword verdict logic)
- sentiment_analysis.py (L-M tone scoring)
- narrative_coherence.py (strategy/results alignment)

**Result**: EXTRACT now only parses facts. ANALYZE evaluates them.

### Plan 29-03: Move Computation Out of RENDER
- Pre-computed clean/elevated flags in ANALYZE stage
- Density mode decisions moved upstream
- Render reads pre-computed values instead of computing thresholds

### Plan 29-04: Consolidate to 7 Pipeline Stages
- Absorbed `stages/classify/` (334 lines) as sub-step of `stages/analyze/`
- Absorbed `stages/hazard/` (3,756 lines) as sub-step of `stages/analyze/`
- PIPELINE_STAGES = 7: RESOLVE, ACQUIRE, EXTRACT, ANALYZE, SCORE, BENCHMARK, RENDER

### Plan 29-05: Brain Priority Fix
- **Governance rationalization**: 81 -> 25 decision-driving checks (56 reclassified to CONTEXT_DISPLAY)
- **Restatement expansion**: 1 -> 8 checks (magnitude, pattern, auditor_link, material_weakness, auditor_disagreement, attestation_fail, stock_window)
- **AI risk right-sizing**: 11 -> 4 checks (removed 7 unvalidated speculative checks)

### Plan 29-06: Parallel LLM Extraction
- ThreadPoolExecutor with 3 concurrent workers
- Filing prioritization: 10-K(100) > DEF 14A(90) > 8-K(70) > 10-Q(50) > SC 13D/G(30-40)
- Redundancy filter: skip 10-Qs filed before latest 10-K (superseded data)
- Max 15 filings per company (was 30)
- Thread-safe: CostTracker, ExtractionCache, rate limiter all use threading.Lock
- TSLA extraction: 30 filings -> 15 filings after filter

### Plan 29-07: Real-Time Progress Display
- Added `on_substage_progress()` to RichCallbacks
- Shows `LLM Extract [N/M]: filing_type (accession)` below pipeline table
- progress_fn plumbed through pipeline_config to ExtractStage

## Impact
| Metric | Before | After |
|--------|--------|-------|
| Dead code | 1,188 lines | 0 |
| Pipeline stages | 9 | 7 |
| Governance decision-driving checks | 81 | 25 |
| Restatement checks | 1 | 8 |
| AI risk checks | 11 | 4 |
| TSLA filings extracted | 30 (sequential) | 15 (parallel, 3 workers) |
| Extraction progress | Hidden | Real-time display |

## Tests
- 2,862 tests pass (1 pre-existing xfail deselected: test_item9a_material_weakness[TSLA])
- Ruff lint clean

## Post-Phase Corrections

**Phase 45 audit (2026-02-25):** `knowledge/ai_impact_models.py` was incorrectly reported as deleted in Plan 29-01. The file exists at `src/do_uw/knowledge/ai_impact_models.py` and is actively imported by `ai_risk_scoring.py`. The line-count deletion total was overstated by ~335 lines. No functional impact — the code works correctly; only the historical record was wrong.
