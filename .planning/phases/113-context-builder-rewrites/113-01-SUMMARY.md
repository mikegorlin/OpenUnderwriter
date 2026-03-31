---
phase: 113-context-builder-rewrites
plan: 01
subsystem: render
tags: [context-builders, signal-results, refactor, module-split]

requires:
  - phase: 112-signal-driven-scoring
    provides: signal_results on AnalysisState.analysis
  - phase: 104-signal-consumer-layer
    provides: _signal_consumer.py and _signal_fallback.py typed accessors
provides:
  - 6 focused company_*.py modules each under 300 lines
  - signal_results plumbing in md_renderer and html_renderer for all builders
  - signal_results parameter on all 14 builder functions
  - Wave 0 test scaffolds for BUILD-07 (line limits, signal consumption)
  - Wave 0 test scaffold for BUILD-08 (H/A/E radar chart context)
affects: [113-02, 113-03, 113-04]

tech-stack:
  added: []
  patterns: ["signal_results kwarg pass-through to all context builders", "re-export shim for backward compatibility after module split"]

key-files:
  created:
    - src/do_uw/stages/render/context_builders/company_profile.py
    - src/do_uw/stages/render/context_builders/company_exec_summary.py
    - src/do_uw/stages/render/context_builders/company_business_model.py
    - src/do_uw/stages/render/context_builders/company_environment.py
    - src/do_uw/stages/render/context_builders/company_operations.py
    - src/do_uw/stages/render/context_builders/company_events.py
    - tests/stages/render/test_builder_line_limits.py
    - tests/stages/render/test_signal_consumption.py
    - tests/stages/render/test_hae_context.py
  modified:
    - src/do_uw/stages/render/context_builders/company.py
    - src/do_uw/stages/render/context_builders/__init__.py
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/stages/render/context_builders/financials.py
    - src/do_uw/stages/render/context_builders/market.py
    - src/do_uw/stages/render/context_builders/governance.py
    - src/do_uw/stages/render/context_builders/litigation.py
    - src/do_uw/stages/render/context_builders/scoring.py
    - src/do_uw/stages/render/context_builders/analysis.py

key-decisions:
  - "company_profile.py gets extract_company and helper functions; other builders imported lazily to avoid circular deps"
  - "html_renderer delegates to md_renderer build_template_context for signal_results pass-through; only import path updated directly"
  - "All non-company builders get signal_results parameter as no-op until Plans 02-04 add consumption"

patterns-established:
  - "signal_results kwarg: all builder functions accept signal_results: dict[str, Any] | None = None as keyword-only argument"
  - "Re-export shim: company.py imports from 6 sub-modules and re-exports for backward compatibility"

requirements-completed: [BUILD-01, BUILD-07]

duration: 12min
completed: 2026-03-17
---

# Phase 113 Plan 01: Company Builder Split + Signal Plumbing Summary

**Split company.py (1,178 lines) into 6 focused modules under 300 lines each, wired signal_results pass-through to all 14 builder functions via md_renderer.py**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-17T11:57:55Z
- **Completed:** 2026-03-17T12:09:41Z
- **Tasks:** 3
- **Files modified:** 19

## Accomplishments
- Eliminated largest anti-context-rot violation: company.py split from 1,178 lines to 6 modules (135-280 lines each) + 45-line re-export shim
- All 6 sub-builders import and use _signal_fallback safe accessors for evaluative content
- md_renderer.py now extracts signal_results from state.analysis and passes to every builder call
- html_renderer.py import updated to new module path; delegates to md_renderer for builder plumbing
- All 14 builder functions accept signal_results parameter (company builders consume; others no-op until Plans 02-04)
- Wave 0 test scaffolds: line limits, signal consumption, H/A/E context (xfail)
- All 747 render tests pass unchanged

## Task Commits

1. **Task 0: Create Wave 0 test scaffolds** - `f1d3036` (test)
2. **Task 1: Split company.py into 6 focused modules** - `b862482` (feat)
3. **Task 2: Wire signal_results plumbing in callers** - `f75f150` (feat)

## Files Created/Modified
- `company_profile.py` (280 lines) - extract_company, _get_yfinance_sector, _lookup_gics_name
- `company_exec_summary.py` (135 lines) - extract_exec_summary with signal enrichment
- `company_business_model.py` (165 lines) - extract_business_model with BIZ.CONCENTRATION signals
- `company_environment.py` (240 lines) - _build_environment_assessment, _build_sector_risk with ENVR signals
- `company_operations.py` (269 lines) - _build_operational_complexity, _build_structural_complexity with BIZ.OPS signals
- `company_events.py` (249 lines) - _build_corporate_events, extract_ten_k_yoy with BIZ.EVENT/EXEC signals
- `company.py` (45 lines) - thin re-export shim
- `md_renderer.py` - signal_results extraction and pass-through to all 14 builders
- `html_renderer.py` - import path update from company to company_profile
- `analysis.py`, `financials.py`, `governance.py`, `litigation.py`, `market.py`, `scoring.py` - signal_results parameter stubs

## Decisions Made
- company_profile.py uses lazy imports for sub-builder calls to avoid circular dependencies
- html_renderer.py signal_results pass-through handled via md_renderer delegation (no direct builder calls)
- extract_peer_matrix excluded from signal_results pass-through (pure data extraction, no evaluative content)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- company_profile.py initially at 316 lines; trimmed docstrings and consolidated config path to get under 300
- Pre-existing test_5layer_narrative.py failure (PydanticUserError for model_rebuild) unrelated to this plan

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Signal plumbing established for all builders; Plans 02-04 can now add signal consumption to financials, market, governance, litigation, scoring, and analysis builders
- Wave 0 tests ready to validate each plan's work

---
*Phase: 113-context-builder-rewrites*
*Completed: 2026-03-17*
