---
phase: 19
plan: 04
subsystem: extraction
tags: [llm, governance, litigation, sub-orchestrator, integration]
depends_on:
  requires: ["19-01", "19-02", "19-03"]
  provides: ["LLM-first governance extraction", "LLM-first litigation extraction", "end-to-end LLM pipeline wiring"]
  affects: ["20-extraction-quality"]
tech_stack:
  added: []
  patterns: ["LLM-first-regex-fallback", "field-level-supplementation", "cross-domain-extraction"]
key_files:
  created:
    - src/do_uw/stages/extract/governance_narrative.py
    - tests/test_llm_governance_integration.py
    - tests/test_llm_litigation_integration.py
  modified:
    - src/do_uw/stages/extract/extract_governance.py
    - src/do_uw/stages/extract/extract_litigation.py
    - tests/test_extract_stage.py
decisions:
  - id: "19-04-01"
    title: "Narrative helpers extracted to governance_narrative.py"
    rationale: "LLM integration logic pushed extract_governance.py over 500-line limit"
  - id: "19-04-02"
    title: "LLM NEOs supplement leadership, not replace"
    rationale: "Leadership extractor handles departures, stability, 8-K parsing that LLM cannot"
  - id: "19-04-03"
    title: "LLM legal proceedings supplement SCA, not replace"
    rationale: "SCA extractor uses SCAC database which has richer case data; LLM fills gaps from 10-K Item 3"
  - id: "19-04-04"
    title: "LLM contingencies replace regex when available"
    rationale: "LLM extracts structured ASC 450 data (classification, amounts, ranges) better than regex"
  - id: "19-04-05"
    title: "Forum provisions only fill when regex has nothing"
    rationale: "DEF 14A forum data should not overwrite 10-K regex findings that may have more detail"
metrics:
  duration: "8m 02s"
  completed: "2026-02-10"
  tests_added: 24
  total_tests: 2221
---

# Phase 19 Plan 04: Sub-Orchestrator LLM Integration Summary

LLM-first, regex-fallback wiring for governance and litigation sub-orchestrators with 24 integration tests and cross-domain DEF 14A forum provision mapping.

## What Was Done

### Task 1: Governance Sub-Orchestrator LLM Integration
Modified `extract_governance.py` to use LLM DEF14A data as primary source with regex fallback:

- **Board profiles**: LLM directors become `board_forensics` and `board` (BoardProfile) when available; regex skipped
- **Compensation**: LLM NEO data populates `comp_analysis` with salary, bonus, equity, pay ratio, say-on-pay
- **Compensation flags**: LLM populates `say_on_pay_support_pct`, `ceo_pay_ratio`, `golden_parachute_value`
- **Leadership supplement**: LLM NEOs added to `leadership.executives` if not already found by regex (dedup by name)
- **Ownership supplement**: LLM `officers_directors_ownership_pct` fills `insider_pct` if regex left it empty
- **Governance scoring**: `compute_governance_score` called on LLM board profiles with config-driven weights
- **ExtractionReports**: LLM-populated models generate proper reports with "DEF 14A (LLM)" source
- **500-line split**: Narrative helpers (`_add_leadership_summary`, `_add_board_summary`, etc.) extracted to `governance_narrative.py` (203 lines)

Result: `extract_governance.py` at 348 lines (was 427).

### Task 2: Litigation Sub-Orchestrator LLM Integration
Modified `extract_litigation.py` to use LLM 10-K and DEF14A data:

- **Legal proceedings**: LLM Item 3 cases supplement SCA list (dedup by case name, case-insensitive)
- **Contingent liabilities**: LLM replaces regex when available; total reserve computed from accrued amounts
- **Forum provisions**: DEF14A exclusive forum provision populates `defense.forum_provisions` (cross-domain)
- **Risk factors**: LLM risk factors stored on `state.extracted.risk_factors` with D&O relevance inferred from category
- **Regex fallback**: All regex extractors still called when LLM data absent

Result: `extract_litigation.py` at 474 lines (was 400).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Existing test patching `_generate_governance_summary`**
- **Found during:** Task 1 verification
- **Issue:** `test_extract_stage.py` patched `_generate_governance_summary` which was moved to `governance_narrative.py`
- **Fix:** Updated patch target to `generate_governance_summary` (public, imported)
- **Files modified:** `tests/test_extract_stage.py`
- **Commit:** 53f4fc5

## Decisions Made

| ID | Decision | Rationale |
|----|----------|-----------|
| 19-04-01 | Narrative helpers extracted to governance_narrative.py | LLM logic pushed extract_governance.py over 500 lines |
| 19-04-02 | LLM NEOs supplement leadership, not replace | Leadership extractor handles departure/stability/8-K analysis |
| 19-04-03 | LLM legal proceedings supplement SCA, not replace | SCAC database has richer case metadata |
| 19-04-04 | LLM contingencies replace regex when available | LLM provides structured ASC 450 classification + amounts |
| 19-04-05 | Forum provisions only fill when regex has nothing | Avoid overwriting potentially richer regex data |

## Test Results

- 24 new integration tests added (12 governance + 12 litigation)
- All 2221 tests pass, 0 lint errors, 0 type errors
- Both modified files under 500 lines

## Next Phase Readiness

Phase 19 is now complete. All 4 plans delivered:
1. **19-01**: LLM helpers + schema infrastructure
2. **19-02**: Governance converter functions
3. **19-03**: Litigation converter functions + RiskFactorProfile model
4. **19-04**: Sub-orchestrator wiring (this plan)

The LLM extraction pipeline is end-to-end functional: LLM data flows from `state.acquired_data.llm_extractions` through helpers, converters, and sub-orchestrators to populate governance and litigation domain models with HIGH confidence source attribution.
