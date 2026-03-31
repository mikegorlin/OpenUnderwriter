---
phase: 50-automated-qa-anomaly-detection
plan: 04
subsystem: brain
tags: [composites, pydantic, yaml, signal-grouping, three-layer-architecture]

# Dependency graph
requires:
  - phase: 50-01
    provides: "SignalResult.details field for composites to read structured evaluation data"
provides:
  - "CompositeDefinition YAML schema + CompositeResult Pydantic model"
  - "evaluate_composites() engine with named evaluator dispatch"
  - "3 stock composites: drop_analysis, short_analysis, insider_analysis"
  - "FacetSpec.content field for referencing composites (backward compatible)"
  - "Composite evaluation wired into AnalyzeStage.run() pipeline"
affects: [50-03, rendering, facet-driven-display]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Three-layer architecture: Signals -> Composites -> Facets", "Named evaluator dispatch registry", "Graceful fallback to default evaluator when details empty"]

key-files:
  created:
    - src/do_uw/brain/brain_composite_schema.py
    - src/do_uw/brain/brain_composite_engine.py
    - src/do_uw/brain/composites/stock_drop_analysis.yaml
    - src/do_uw/brain/composites/stock_short_analysis.yaml
    - src/do_uw/brain/composites/stock_insider_analysis.yaml
    - tests/brain/test_brain_composites.py
  modified:
    - src/do_uw/brain/brain_facet_schema.py
    - src/do_uw/brain/facets/market_activity.yaml
    - src/do_uw/stages/analyze/__init__.py
    - src/do_uw/models/state.py

key-decisions:
  - "Composites are BRAIN analysis (not display); Facets are DISPLAY presentation -- architecture enforced throughout"
  - "Named evaluator dispatch registry (_EVALUATORS dict) for domain-specific composite logic"
  - "Evaluators fall back to default when structured details not populated (graceful degradation)"
  - "FacetSpec evolved with additive content field; signals list preserved for backward compatibility"

patterns-established:
  - "Composite YAML schema: id, name, member_signals, conclusion_schema, evaluator, severity_rules"
  - "Evaluator pattern: domain-specific functions registered by name, read SignalResult.details"
  - "FacetContentRef pattern: ref + render_as for mixing composites and standalone signals"

requirements-completed: [QA-02]

# Metrics
duration: 23min
completed: 2026-02-27
---

# Phase 50 Plan 04: Signal Composites Foundation

**Three-layer signal architecture (Signals -> Composites -> Facets) with CompositeDefinition YAML schema, named evaluator dispatch engine, 3 stock composites, and FacetSpec evolution for composite references**

## Performance

- **Duration:** 23 min
- **Started:** 2026-02-27T03:19:04Z
- **Completed:** 2026-02-27T03:42:18Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- Established three-layer brain architecture: Signals (atomic) -> Composites (brain analysis) -> Facets (display)
- Created CompositeDefinition schema (YAML) and CompositeResult model (Pydantic) with full type safety
- Built evaluate_composites() engine with named evaluator dispatch for domain-specific analysis
- Implemented 3 domain evaluators: stock_drop_analysis, stock_short_analysis, stock_insider_analysis
- Evolved FacetSpec with FacetContentRef model and content list (backward compatible with signals list)
- Wired composite evaluation into AnalyzeStage.run() pipeline (non-fatal, after gap re-eval, before engines)
- Created 9 CI tests validating composite YAML integrity, facet content refs, and engine graceful handling

## Task Commits

Each task was committed atomically:

1. **Task 1: Create CompositeDefinition schema, CompositeResult model, and evaluation engine** - `c50de05` (feat)
2. **Task 2: Create composite YAML definitions, evolve facet schema, and add CI tests** - `6876362` (feat)
3. **Task 3: Wire evaluate_composites() into the analyze pipeline** - `d6e9046` (feat)

## Files Created/Modified
- `src/do_uw/brain/brain_composite_schema.py` - NEW: CompositeDefinition + CompositeResult Pydantic models, load_all_composites()
- `src/do_uw/brain/brain_composite_engine.py` - NEW: evaluate_composites() with 4 evaluators (default + 3 stock domain)
- `src/do_uw/brain/composites/stock_drop_analysis.yaml` - NEW: COMP.STOCK.drop_analysis (6 member signals)
- `src/do_uw/brain/composites/stock_short_analysis.yaml` - NEW: COMP.STOCK.short_analysis (4 member signals)
- `src/do_uw/brain/composites/stock_insider_analysis.yaml` - NEW: COMP.STOCK.insider_analysis (3 member signals)
- `src/do_uw/brain/brain_facet_schema.py` - Added FacetContentRef model + content field to FacetSpec
- `src/do_uw/brain/facets/market_activity.yaml` - Added content list referencing 3 composites + 23 standalone signals
- `src/do_uw/stages/analyze/__init__.py` - Added _run_composites() and wired into pipeline
- `src/do_uw/models/state.py` - Added composite_results field to AnalysisResults
- `tests/brain/test_brain_composites.py` - NEW: 9 CI tests for composite integrity and engine

## Decisions Made
- **Three-layer separation enforced**: Composites contain ONLY analysis logic (grouping, attribution, correlation). Facets contain ONLY display logic (render_as, layout). These are architecturally separate.
- **Named evaluator dispatch**: Each composite declares its evaluator name in YAML; the engine dispatches to registered functions. This allows domain-specific analysis without modifying the engine core.
- **Graceful fallback**: Domain evaluators check if structured details are populated. If not (signals haven't been enriched yet), they fall back to the default aggregation evaluator. Composites work at every stage of enrichment.
- **Additive facet evolution**: FacetSpec gains a `content` list with FacetContentRef entries. The existing `signals` list is unchanged. Both coexist -- content is the new path, signals is the legacy path. No breaking changes.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- 1 pre-existing test failure (test_orchestrator_brain.py::test_brain_requirements_logged) confirmed by running against pre-Plan-04 code. Not related to this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Composite evaluation runs at pipeline time (after signal execution, before analytical engines)
- 3 stock composites produce CompositeResults with structured conclusions
- FacetSpec content list ready for future rendering migration (facet-driven rendering reads content instead of signals)
- CI tests enforce composite integrity (member signals exist, IDs valid, evaluators registered)
- Pattern established for adding more composites (governance, financial, litigation domains)

## Self-Check: PASSED

All files exist, all commits verified:
- c50de05: feat(50-04): add CompositeDefinition schema, CompositeResult model, and evaluation engine
- 6876362: feat(50-04): add composite YAML definitions, evolve facet schema, CI tests
- d6e9046: feat(50-04): wire evaluate_composites() into analyze pipeline

---
*Phase: 50-automated-qa-anomaly-detection*
*Completed: 2026-02-27*
