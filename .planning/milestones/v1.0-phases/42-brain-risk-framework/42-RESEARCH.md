# Phase 42: Scoring Presentation Redesign — Research

## Research Date: 2026-02-23

## Problem Statement
Current scoring presentation is flat: 10-factor table, red flags, patterns, allegations all rendered sequentially with no organizing principle. User wants scoring restructured around **perils** (8 D&O claim types) with **causal chain narratives** showing how risks connect.

## Current Architecture

### Data Flow
```
ScoringResult (models/scoring.py)
  → extract_scoring() (md_renderer_helpers_scoring.py)
    → scoring.md.j2 / scoring.html.j2 (templates)
  → render_section_7() (sect7_scoring.py, Word renderer)
    → render_scoring_detail() (sect7_scoring_detail.py)
    → render_peril_map() (sect7_peril_map.py)
    → render_coverage_gaps() (sect7_coverage_gaps.py)
```

### Key Files (Current)
| File | Lines | Role |
|------|-------|------|
| `stages/render/sections/sect7_scoring.py` | 484 | Main orchestrator: narrative, tier, breakdown, radar, red flags, risk type, severity, calibration |
| `stages/render/sections/sect7_scoring_detail.py` | 369 | Per-factor detail, patterns, allegations, claim prob, tower |
| `stages/render/sections/sect7_scoring_analysis.py` | 190 | Forensic composites, temporal signals, NLP, exec risk |
| `stages/render/sections/sect7_peril_map.py` | 461 | Plaintiff heat map, bear cases, settlement, tower characterization |
| `stages/render/sections/sect7_coverage_gaps.py` | 297 | DATA_UNAVAILABLE disclosure |
| `stages/render/md_renderer_helpers_scoring.py` | 357 | extract_scoring() for Markdown/HTML templates |
| `templates/html/sections/scoring.html.j2` | 669 | HTML template |
| `templates/markdown/sections/scoring.md.j2` | 146 | Markdown template |

### Brain Framework Data (Phase 42 Waves 1-4, COMPLETE)
- **8 perils** in `brain/framework/perils.yaml` → `brain_perils` table
- **16 causal chains** in `brain/framework/causal_chains.yaml` → `brain_causal_chains` table
- Each chain has: trigger_checks, amplifier_checks, mitigator_checks, evidence_checks
- Each chain has: frequency_factors, severity_factors, patterns, red_flags
- Each chain has: historical_filing_rate, median_severity_usd
- Checks tagged with `peril_id` and `chain_ids` in brain_checks table
- **BrainDBLoader** can query all this data from brain.duckdb

### What Pipeline Already Produces
- `state.scoring.factor_scores` — 10 factors with points_deducted, evidence, rules_triggered
- `state.scoring.red_flags` — CRF results with triggered/ceiling/evidence
- `state.scoring.patterns_detected` — pattern matches with triggers/severity
- `state.scoring.allegation_mapping` — theory exposures
- `state.scoring.claim_probability` — probability band/range
- `state.scoring.severity_scenarios` — settlement estimates
- `state.scoring.tower_recommendation` — position/layers
- `state.analysis.check_results` — all 400 check results with status/evidence
- `state.analysis.peril_map` — PlaintiffAssessment + BearCase (Phase 27)

## Design: Peril-Organized Scoring

### New Presentation Structure
```
Section 7: Risk Scoring & Synthesis
├── Narrative Lead (existing - keep)
├── Tier Classification (existing - keep)
├── D&O Peril Summary (NEW — 8-peril overview table)
│   └── Per-peril: risk level, triggered chains, key evidence
├── Peril Deep Dives (NEW — one per active peril)
│   ├── SECURITIES: causal chain narratives
│   │   ├── "Stock Drop → SCA" chain: trigger/amplifier/mitigator
│   │   ├── "Restatement → SCA" chain: trigger/amplifier/mitigator
│   │   └── Supporting: factors F1,F2,F5,F6 detail
│   ├── FIDUCIARY: governance_to_derivative, activist_to_derivative
│   ├── REGULATORY: enforcement_to_penalty
│   └── ... (only active perils shown)
├── Composite Score Breakdown (existing 10-factor - keep but reorganize)
├── Red Flag Gates (existing - keep)
├── Severity Scenarios (existing - keep)
├── Tower Recommendation (existing - keep)
├── Forensic/Temporal/NLP (existing - keep)
└── Coverage Gaps (existing - keep, always last)
```

### Data Extraction Strategy
New function `extract_peril_scoring()` that:
1. Loads perils + chains from brain.duckdb via BrainDBLoader
2. Cross-references check_results to find which chains are "active" (trigger checks fired)
3. For each active chain, collects triggered/amplified/mitigated checks with evidence
4. Groups by peril, computes per-peril risk level
5. Returns structured dict for templates

### Chain Activation Logic
A causal chain is "active" when:
- At least 1 trigger_check has status RED or YELLOW in check_results
- Activation strength = (triggered_triggers / total_triggers) * weight
- Amplifiers increase concern, mitigators decrease it
- Chain with no triggers fired = INACTIVE (hidden)

### Per-Peril Risk Level
- **HIGH**: Any chain with 2+ triggers fired, OR red flag associated with peril triggered
- **ELEVATED**: 1 trigger fired + amplifiers present
- **MODERATE**: 1 trigger fired, no amplifiers
- **LOW**: No triggers fired but evidence checks show data present
- **INACTIVE**: No relevant data — peril not displayed

## Technical Approach

### Plan 1: Peril Data Extraction (Wave 1)
New file: `stages/render/scoring_peril_data.py` (~300 lines)
- `extract_peril_scoring(state) -> dict[str, Any]`
- Loads brain framework data (perils, chains)
- Crosses with check_results
- Returns peril summary + chain details

### Plan 2: Word Renderer Restructure (Wave 2)
Modify: `sect7_scoring.py` — reorder calls
New file: `sect7_scoring_perils.py` (~400 lines)
- `render_peril_summary()` — overview table
- `render_peril_deep_dives()` — per-peril sections with chain narratives

### Plan 3: HTML Template Restructure (Wave 2, parallel)
Modify: `scoring.html.j2` — add peril sections
Modify: `md_renderer_helpers_scoring.py` — add peril data to template context

### Plan 4: Markdown Template Update (Wave 3)
Modify: `scoring.md.j2` — add peril summary

## Risk Assessment
- **No regression risk**: Existing scoring data unchanged, just reorganized presentation
- **Brain.duckdb dependency**: Must be built first (`brain build`)
- **Graceful fallback**: If brain.duckdb missing, fall back to current flat presentation
