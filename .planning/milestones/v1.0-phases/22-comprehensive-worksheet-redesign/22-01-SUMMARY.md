---
phase: 22-comprehensive-worksheet-redesign
plan: 01
subsystem: render
tags: [narrative, formatters, prose-generation, d&o-underwriting]
completed: 2026-02-11
duration: ~12m
dependency_graph:
  requires: [phase-20-llm-extraction, phase-17-data-quality]
  provides: [analyst-quality-narratives, v2-formatters]
  affects: [22-02, 22-03, 22-04, 22-05, 22-06, 22-07, 22-08, 22-09, 22-10]
tech_stack:
  added: []
  patterns: [dual-dispatch-isinstance, helper-file-split, typed-state-narratives]
key_files:
  created:
    - src/do_uw/stages/render/md_narrative_sections.py
    - src/do_uw/stages/render/md_narrative_helpers.py
  modified:
    - src/do_uw/stages/render/md_narrative.py
    - src/do_uw/stages/render/formatters.py
    - tests/test_render_framework.py
decisions:
  - "3-file narrative split: md_narrative.py (368L) + md_narrative_sections.py (486L) + md_narrative_helpers.py (279L)"
  - "Dual-dispatch pattern: isinstance(state_or_dict, dict) routes to legacy wrapper or typed implementation"
  - "Re-exports in md_narrative.py for backward compatibility (governance, litigation, scoring, company narratives)"
  - "TypeVar _T for generic sv_val() SourcedValue extraction"
  - "format_source_trail extracts filing section from source string via marker matching"
metrics:
  tests_added: 8
  tests_total: 87
  lines_added: ~1130
  pyright_errors: 0
  ruff_errors: 0
---

# Phase 22 Plan 01: Narrative Engine + V2 Formatters Summary

**One-liner:** Analyst-quality D&O narrative engine with typed AnalysisState dispatch, 8 narrative functions across 3 files, plus 6 v2 formatter utilities for section renderers.

## What Was Done

### Task 1: Rewrite narrative engine for analyst-quality prose (d08fbb3)

Rewrote the narrative engine from 442-line template-fill code into 1133 lines of analyst-quality prose generation across 3 files:

**md_narrative.py (368 lines)** -- Core engine with:
- `financial_narrative(state)`: Revenue trajectory with YoY comparison, net margin analysis, distress model interpretation (Altman Z + Ohlson O + Piotroski F), leverage/debt context, earnings quality (OCF/NI ratio, accruals), audit risk (material weaknesses, going concern, auditor tenure), D&O underwriting conclusion
- `market_narrative(state)`: Stock performance vs 52-week high with SCA viability thresholds (15%/30%/50%), sector-relative performance, worst single-day drop with trigger attribution, short interest with trend, analyst consensus, stock-drop litigation risk conclusion
- `insider_narrative(state)`: Net buying/selling direction, 10b5-1 plan coverage percentage, cluster selling events with names/values/dates, unplanned executive departures context

**md_narrative_sections.py (486 lines)** -- Section narratives:
- `governance_narrative(state)`: Governance score interpretation (4 tiers), board independence vs NYSE minimum, CEO/Chair duality, overboarding, anti-takeover provisions (classified board, dual-class), say-on-pay alignment, CEO compensation, risk factor summary
- `litigation_narrative(state)`: Active SCA summary with class period, lead counsel tier, SEC enforcement pipeline, derivative suits, industry claim patterns, SOL windows, defense quality, litigation reserve
- `scoring_narrative(state)`: Tier classification with action/probability, top risk factor contributors, active composite patterns, red flag gate activations with ceiling, claim probability band
- `company_narrative(state)`: Business description, revenue concentration segments, geographic risk (international exposure), FPI status/implications, market cap/filer category, D&O exposure factors, risk classification

**md_narrative_helpers.py (279 lines)** -- Private helpers:
- `distress_narrative(fin)`: Z-Score/O-Score combination with zone interpretation
- `leverage_narrative(fin)`: D/E ratio, interest coverage, near-term maturities
- `earnings_quality_narrative(fin)`: OCF/NI ratio, accruals ratio, effective tax rate
- `audit_narrative(fin)`: Material weaknesses, going concern, auditor tenure
- `financial_do_conclusion(fin)`: D&O-specific risk signal aggregation
- Legacy dict wrappers: `financial_narrative_from_dict`, `market_narrative_from_dict`, `insider_narrative_from_dict`

All functions accept `AnalysisState | dict[str, Any]` via isinstance dispatch for backward compatibility. Re-exports in md_narrative.py maintain existing import paths.

### Task 2: Enhance formatters with v2 utilities (6dd5e74)

Added 6 new utility functions to formatters.py (313 lines total):

1. **format_source_trail(sv)**: Full attribution `[SEC 10-K, filed 2024-02-15, Item 7, HIGH confidence]` with section extraction from source string
2. **format_risk_level(level)**: Standardized uppercase risk labels (CRITICAL, HIGH, ELEVATED, MODERATE, LOW, NEUTRAL)
3. **format_date_range(start, end)**: ISO dates to `Jan 2023 - Mar 2024` format with edge cases (present, through)
4. **format_compact_table_value(value, is_currency, is_pct)**: Single function for table cells handling None, currency compact, percentage, integer/float
5. **sv_val(sv, default)**: Generic `SourcedValue[T] | None -> T | str` extraction with TypeVar for type preservation
6. **format_change_indicator(current, prior)**: YoY change `+12.3%` / `-5.7%` / `0.0%` with zero-division guard

Added 8 new test cases in test_render_framework.py covering all 6 functions with edge cases (None inputs, negative values, zero prior, filing section extraction). Total: 87 tests passing.

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| 3-file narrative split | md_narrative.py would exceed 500 lines without split; helpers extracted for financial sub-narratives and legacy wrappers |
| Dual-dispatch isinstance pattern | Maintains backward compatibility with existing dict-based callers while enabling typed state path |
| Re-exports for backward compat | `from md_narrative import governance_narrative` still works even though function lives in sections file |
| TypeVar _T for sv_val | Preserves generic type information (`sv_val(sv_float)` returns `float`, not `Any`) |
| Filing section marker matching | Extracts Item 7, Item 8, DEF 14A from source strings via simple string matching rather than regex |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] md_narrative_sections.py exceeded 500 lines**
- **Found during:** Task 1
- **Issue:** Initial implementation of md_narrative_sections.py was 510 lines
- **Fix:** Removed separator comment blocks and excess blank lines, trimmed to 486 lines
- **Files modified:** md_narrative_sections.py

**2. [Rule 3 - Blocking] md_narrative.py exceeded 500 lines**
- **Found during:** Task 1
- **Issue:** Initial implementation was 689 lines with all financial sub-narratives inline
- **Fix:** Created md_narrative_helpers.py with distress, leverage, earnings quality, audit, conclusion, and legacy dict wrappers
- **Files modified:** md_narrative.py, md_narrative_helpers.py (new)

**3. [Rule 1 - Bug] Multiple pyright type errors from model field mismatches**
- **Found during:** Task 1
- **Issue:** 34 pyright errors including: ClaimProbability has no `base_rate` (uses `band`/`range_low_pct`/`range_high_pct`), IndustryClaimPattern has no `pattern_name` (uses `legal_theory`/`description`), SOLWindow uses `window_open` not `is_open`, DefenseAssessment uses `overall_defense_strength` not `overall_assessment`, SourcedValue[float].value is never None (redundant checks)
- **Fix:** Corrected all field references to match actual model definitions, removed redundant None checks on non-optional SourcedValue fields
- **Files modified:** md_narrative_sections.py

## Verification Results

- Tests: 87 passed (test_render_framework.py)
- Pyright: 0 errors across all 4 files
- Ruff: All checks passed
- Line counts: 313 + 368 + 486 + 279 = 1446 total (all under 500 individually)

## Commits

| Hash | Message |
|------|---------|
| d08fbb3 | feat(22-01): rewrite narrative engine for analyst-quality prose |
| 6dd5e74 | feat(22-01): enhance formatters with v2 table/risk/change utilities |

## Next Phase Readiness

This plan provides the narrative engine and formatter utilities required by all subsequent plans in Phase 22:
- Plan 02 (section renderers) imports narrative functions
- Plans 03-09 (individual section rewrites) use formatters for table cells, risk labels, source trails
- Plan 10 (integration) validates narratives render correctly end-to-end
