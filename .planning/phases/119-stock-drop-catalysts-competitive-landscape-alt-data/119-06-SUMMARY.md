---
phase: 119-stock-drop-catalysts-competitive-landscape-alt-data
plan: 06
subsystem: pipeline
tags: [pipeline-wiring, extract, benchmark, render, manifest, context-builders, integration-tests]

# Dependency graph
requires:
  - phase: 119-01
    provides: "AnalysisState explicit fields (stock_patterns, multi_horizon_returns, analyst_consensus, drop_narrative)"
  - phase: 119-02
    provides: "Stock catalyst enrichment + performance summary modules"
  - phase: 119-03
    provides: "Competitive landscape extraction + alt data extraction modules"
  - phase: 119-04
    provides: "D&O assessment + competitive/alt data enrichment modules"
  - phase: 119-05
    provides: "Context builders + Jinja2 templates for all Phase 119 sections"
provides:
  - "EXTRACT pipeline: Phases 15-17 (stock catalyst, alt data, competitive landscape)"
  - "BENCHMARK pipeline: Steps 11-13 (drop D&O assessment, competitive enrichment, alt data enrichment)"
  - "7 context builders wired into html_context_assembly.py"
  - "Manifest: competitive landscape activated (was deferred), alternative_data section with 4 groups"
  - "45 integration tests covering complete data flow"
affects: [render, pipeline, worksheet-output]

# Tech tracking
tech-stack:
  added: []
  patterns: ["asyncio.run() for calling async functions from sync pipeline context"]

key-files:
  created:
    - "src/do_uw/templates/html/sections/alt_data.html.j2"
    - "tests/stages/render/test_119_integration.py"
  modified:
    - "src/do_uw/stages/extract/__init__.py"
    - "src/do_uw/stages/benchmark/__init__.py"
    - "src/do_uw/stages/render/html_context_assembly.py"
    - "src/do_uw/brain/output_manifest.yaml"
    - "src/do_uw/templates/html/sections/dossier.html.j2"
    - "tests/stages/render/test_manifest_rendering.py"
    - "tests/stages/render/test_dossier_integration.py"
    - "tests/stages/render/test_section_renderer.py"

key-decisions:
  - "Used asyncio.run() to call async extract_competitive_landscape from sync ExtractStage.run()"
  - "All inter-stage data stored on explicit AnalysisState fields (not underscore-prefixed attrs)"
  - "alternative_data section placed after intelligence_dossier, before financial_health in manifest"
  - "Stock performance summary + drop catalyst templates added before market_checks in market section"

patterns-established:
  - "Phase 119 pipeline wiring: try/except with logger.warning for non-breaking step failures"
  - "Context builders read from explicit AnalysisState fields passed as keyword args"

requirements-completed: [STOCK-01, STOCK-02, STOCK-03, STOCK-04, STOCK-05, STOCK-06, DOSSIER-07, ALTDATA-01, ALTDATA-02, ALTDATA-03, ALTDATA-04]

# Metrics
duration: 30min
completed: 2026-03-20
---

# Phase 119 Plan 06: Pipeline Integration Summary

**Full pipeline wiring for stock drop catalysts, competitive landscape, and alternative data: 3 EXTRACT phases, 3 BENCHMARK steps, 7 context builders, manifest activation, and 45 integration tests**

## Performance

- **Duration:** 30 min
- **Started:** 2026-03-20T17:19:22Z
- **Completed:** 2026-03-20T17:50:06Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- EXTRACT pipeline extended with Phases 15-17: stock catalyst enrichment, alt data extraction, competitive landscape extraction (async via asyncio.run)
- BENCHMARK pipeline extended with Steps 11-13: drop D&O assessment, competitive enrichment, alt data enrichment
- All 7 Phase 119 context builders wired into html_context_assembly with try/except for graceful degradation
- Manifest updated: competitive landscape activated from deferred, alternative_data section with 4 groups (ESG, AI-washing, tariff, peer SCA), stock templates in market section
- 45 integration tests covering source wiring, context builder wiring, empty/populated state, explicit field usage, analyst narrative flow, manifest structure, and template existence

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire EXTRACT + BENCHMARK pipeline steps** - `c588349b` (feat)
2. **Task 2: Wire context builders + update manifest + delete deferred placeholder** - `ce2f2b8d` (feat)
3. **Task 3: Integration tests for end-to-end data flow** - `ba8bd86a` (test)
4. **Test fixes for manifest changes** - `02ed0ff7` (fix)

## Files Created/Modified
- `src/do_uw/stages/extract/__init__.py` - Added Phases 15-17 (stock catalyst, alt data, competitive landscape)
- `src/do_uw/stages/benchmark/__init__.py` - Added Steps 11-13 (drop D&O, competitive, alt data enrichment)
- `src/do_uw/stages/render/html_context_assembly.py` - Wired 7 context builders with explicit state field reads
- `src/do_uw/brain/output_manifest.yaml` - Activated competitive landscape, added alternative_data section + stock templates
- `src/do_uw/templates/html/sections/alt_data.html.j2` - Section wrapper for 4 alt data subsections
- `src/do_uw/templates/html/sections/dossier.html.j2` - Added competitive_landscape include
- `tests/stages/render/test_119_integration.py` - 45 integration tests
- `tests/stages/render/test_manifest_rendering.py` - Updated section count 17->18, added alternative_data
- `tests/stages/render/test_dossier_integration.py` - Updated competitive landscape: deferred -> active
- `tests/stages/render/test_section_renderer.py` - Updated market fragment count 11->13

## Decisions Made
- Used `asyncio.run()` to call async `extract_competitive_landscape` from sync pipeline -- the function is declared async but contains no actual await calls, so this is safe
- All inter-stage data stored on explicit AnalysisState fields (stock_patterns, multi_horizon_returns, analyst_consensus, drop_narrative) per Plan 01 design -- NOT underscore-prefixed attrs which Pydantic v2 silently ignores

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing tests broken by manifest changes**
- **Found during:** Task 2 verification
- **Issue:** test_dossier_integration expected competitive_landscape render_as=deferred; test_section_renderer expected 11 market fragments
- **Fix:** Updated test assertions to match new manifest state (active competitive landscape, 13 market fragments)
- **Files modified:** tests/stages/render/test_dossier_integration.py, tests/stages/render/test_section_renderer.py
- **Committed in:** 02ed0ff7

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary test update to reflect intended manifest changes. No scope creep.

## Issues Encountered
- `AIWashingRisk.indicators` and `PeerSCACheck.peer_scas` are `list[dict[str, str]]` not `list[str]` -- fixed test fixture during Task 3 development
- Pre-existing test failure in `test_brain_contract.py::test_threshold_provenance_categorized` and `test_html_signals.py::test_grouped_entry_has_required_keys` -- not caused by our changes, not fixed

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All Phase 119 code is now wired into the pipeline and will execute during `underwrite TICKER`
- Pipeline runs will produce stock catalyst, competitive landscape, and alt data sections in HTML output
- Phase 120 (integration testing) can now validate end-to-end output quality

---
*Phase: 119-stock-drop-catalysts-competitive-landscape-alt-data*
*Completed: 2026-03-20*
