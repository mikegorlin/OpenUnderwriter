---
phase: 46-brain-driven-gap-search
plan: "03"
subsystem: acquire
tags: [acquire, brain, gap-search, web-search, phase-e, orchestrator]

# Dependency graph
requires:
  - phase: 46-01
    provides: gap_bucket/gap_keywords fields on 68 SKIPPED check YAMLs (2 non-L1 routing-gap checks)
  - phase: 46-02
    provides: AcquiredData.brain_targeted_search write target
provides:
  - gap_searcher.py module with run_gap_search() entry point
  - gap_query_generator.py with LLM + template query generation
  - Phase E wired into AcquisitionOrchestrator.run() as final non-blocking step
affects:
  - "46-04 (re-evaluator reads acquired.brain_targeted_search to update CheckResult status)"
  - "46-05+ (downstream stages benefit from gap search evidence)"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Phase E follows non-blocking try/except pattern (same as _run_discovery_hook)"
    - "Lazy import of run_gap_search inside try block prevents import-time failures"
    - "Batch LLM query generation (one prompt for N checks) reduces API calls when >3 checks"
    - "Cache-first pattern: gap_search:{ticker}:{check_id} key, WEB_SEARCH_TTL TTL"
    - "Evidence gate: keyword in snippet/title/description -> TRIGGERED; results but no match -> CLEAR; empty keywords -> skip"

key-files:
  created:
    - src/do_uw/stages/acquire/gap_searcher.py
    - src/do_uw/stages/acquire/gap_query_generator.py
  modified:
    - src/do_uw/stages/acquire/orchestrator.py

key-decisions:
  - "Eligible checks are those with non-empty gap_keywords AND non-L1 acquisition_tier; empty-keyword checks are skipped (unevaluable, not CLEAR) per RESEARCH.md pitfall 3"
  - "Budget cap: min(web_search.budget_remaining, GAP_SEARCH_MAX=15) so Phase E never starves Phases A-D"
  - "Cache hits do NOT decrement searched counter — only live searches count against budget"
  - "Orchestrator line count (624) pre-existed before this plan; deferred to a future file-split plan"

# Metrics
duration: 8min
completed: 2026-02-25
---

# Phase 46 Plan 03: Gap Searcher Module and Phase E Wiring Summary

**gap_searcher.py and gap_query_generator.py built and wired into AcquisitionOrchestrator as Phase E — brain-driven targeted web search for non-L1 SKIPPED checks within shared budget**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-25T23:15:14Z
- **Completed:** 2026-02-25T23:23:18Z
- **Tasks:** 2
- **Files created/modified:** 3

## Accomplishments

- Built `gap_searcher.py`: `_load_gap_eligible_checks()` walks brain YAML and returns 2 non-L1 routing-gap checks (FIN.ACCT.restatement_stock_window, LIT.PATTERN.peer_contagion)
- Built evidence quality gate `_evaluate_evidence()`: keyword match → TRIGGERED; results but no match → CLEAR; empty keywords or no results → (False, "")
- Built `run_gap_search()`: budget gating at `min(budget_remaining, 15)`, cache-first lookup, batch query generation, result storage in `acquired.brain_targeted_search`
- Built `gap_query_generator.py`: `generate_gap_query()` with claude-haiku-3-5 LLM + template fallback; `generate_gap_queries_batch()` for efficient multi-check generation
- Wired Phase E into `AcquisitionOrchestrator.run()` as non-blocking step after discovery hook, before `return acquired`
- All 3384 existing tests pass (1 pre-existing failure in test_word_coverage_exceeds_90_percent, confirmed unrelated)

## Task Commits

1. **Task 1: Build gap_searcher.py and gap_query_generator.py** - `644d5c4` (feat)
2. **Task 2: Wire Phase E into AcquisitionOrchestrator** - `7c54442` (feat)

## Files Created/Modified

- `src/do_uw/stages/acquire/gap_searcher.py` (305 lines) - Core gap search orchestrator: eligible check loading, evidence gate, run_gap_search entry point
- `src/do_uw/stages/acquire/gap_query_generator.py` (254 lines) - LLM + template query generation with batch support
- `src/do_uw/stages/acquire/orchestrator.py` - Phase E block added after discovery hook, before return acquired

## Decisions Made

- **Empty-keyword checks skipped (not CLEAR)**: Checks with empty `gap_keywords` are unevaluable — marking them CLEAR would be a false signal. They are logged at DEBUG and skipped. This follows RESEARCH.md pitfall 3 explicitly.
- **Cache does not decrement budget counter**: Cache hits are free — only live web_search.search() calls count against the 15-search cap. This maximizes search quality on repeat runs.
- **Batch query generation for efficiency**: When >3 checks are eligible, a single LLM prompt lists all checks and parses numbered responses. Falls back to per-check template if batch parsing fails. Per RESEARCH.md pitfall 5.
- **Lazy import in orchestrator**: `from do_uw.stages.acquire.gap_searcher import run_gap_search` inside the try block prevents import-time failures from breaking the pipeline.

## Deviations from Plan

None - plan executed exactly as written.

## Deferred Items

- **orchestrator.py line count (624)**: Exceeds 500-line limit. Pre-existed before this plan (608 lines before Task 2's +18 lines). Only 18 lines added by this plan. Flagged for a future file-split plan. Added to deferred-items.md.

## Self-Check: PASSED

- FOUND: `src/do_uw/stages/acquire/gap_searcher.py` — contains `run_gap_search`, `_load_gap_eligible_checks`, `_evaluate_evidence`, `GAP_SEARCH_MAX`
- FOUND: `src/do_uw/stages/acquire/gap_query_generator.py` — contains `generate_gap_query`, `_generate_via_template`, `_generate_via_llm`
- FOUND: `src/do_uw/stages/acquire/orchestrator.py` — contains "Phase E" and "run_gap_search"
- FOUND: Commit `644d5c4` — feat(46-03): build gap_searcher.py and gap_query_generator.py
- FOUND: Commit `7c54442` — feat(46-03): wire Phase E brain-driven gap search into AcquisitionOrchestrator

---
*Phase: 46-brain-driven-gap-search*
*Completed: 2026-02-25*
