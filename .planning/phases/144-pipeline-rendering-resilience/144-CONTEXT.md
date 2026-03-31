# Phase 144: Pipeline & Rendering Resilience - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the pipeline survive any stage failure and always produce an HTML worksheet. No crashes on missing data. Every section renders what it has or shows an explicit banner about what's missing. Full traceability of pipeline execution in the audit section.

</domain>

<decisions>
## Implementation Decisions

### Failure Strategy
- **D-01:** Pipeline continues through ALL remaining stages after a failure. Failed stage is logged and marked in state, but pipeline does not raise PipelineError — it continues to RENDER. Currently `pipeline.py:181-194` raises on failure; this must change to catch-and-continue.
- **D-02:** CLI exits 0 with warnings when HTML is produced, even if stages failed. Producing output = success. Failed stages are logged as warnings.
- **D-03:** `state.mark_stage_failed()` already exists — use it. Stage status (pending/running/complete/failed) + duration + error message all tracked per stage.

### Missing Data Display
- **D-04:** Sections with missing data render with an amber "Incomplete — [Stage] did not complete" banner at top, then show whatever partial data IS available below. Partial info > no info.
- **D-05:** Chart builders that receive None data render a gray placeholder box (same dimensions as chart) with centered "No data available" text. Maintains layout flow, no broken whitespace or AttributeError crashes.
- **D-06:** Every chart builder must guard against None input systematically — not ad-hoc per builder.

### Stage Status Tracking
- **D-07:** Pipeline stage status displayed in the **audit section** of the worksheet, not a separate footer. Full traceability: each stage shows status (complete/failed/skipped), duration, and error message if failed.
- **D-08:** Guiding principle: "single source of truth" — the worksheet must show what the pipeline did, what data it has, and what's missing. No hiding failures.

### Supabase Independence
- **D-09:** Dual-path render — risk card context builder pulls from `acquired_data` directly, never from `extracted` data. Two completely separate data paths. Even if EXTRACT/ANALYZE/SCORE all fail, Supabase SCA data renders independently.

### Claude's Discretion
- Chart placeholder styling (exact gray shade, font size, border treatment)
- Whether to add a `@contextmanager` for stage execution or keep inline try/except
- How to structure the audit section template (table vs cards vs list)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pipeline Architecture
- `src/do_uw/pipeline.py` — Current pipeline orchestrator (PipelineError stops on failure, needs continue-on-error)
- `src/do_uw/models/common.py` — StageStatus enum (COMPLETED, FAILED, etc.)
- `src/do_uw/models/state.py` — AnalysisState with stages dict and mark_stage_failed()

### Rendering
- `src/do_uw/stages/render/` — All render code; chart builders need None guards
- `src/do_uw/stages/render/qd_report.py` — Risk card / Supabase rendering
- `src/do_uw/stages/render/chart_registry.py` — Chart builder dispatch

### Requirements
- `.planning/REQUIREMENTS.md` — RES-01 through RES-06

### Milestone Context
- `.planning/milestones/v13.0-worksheet-excellence/MILESTONE.md` — Issues catalog, known bugs (combo chart crash on stock_drops None)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StageCallbacks` protocol with `on_stage_fail` — already handles failure notification, just needs pipeline to not crash
- `state.mark_stage_failed(stage_name, error_msg)` — already records failures in state
- `StageStatus` enum — already has COMPLETED, FAILED, PENDING states
- `SectionCompletenessGate` (v12.0 Phase 142) — suppresses >50% N/A sections with banners; pattern can be extended for stage failures

### Established Patterns
- Pipeline saves state after each stage via `_save_state()` — incremental persistence already works
- Resume support exists (skip COMPLETED stages) — extend to also skip FAILED stages on re-run
- Context builders use `safe_float()` for None-safe numeric operations — extend this defensive pattern to all chart builders

### Integration Points
- `pipeline.py:run()` — main loop that needs catch-and-continue instead of raise
- Every chart builder function — needs systematic None guard
- Audit section template — needs new stage status block
- Risk card context builder — needs to pull from acquired_data path directly

</code_context>

<specifics>
## Specific Ideas

- User explicitly stated: "this is the single source of truth" — full traceability is paramount. The audit section must show everything about what the pipeline did.
- Combo chart crash on `stock_drops` being None was a specific bug from the v13.0 session — example of what this phase prevents.
- ORCL was the ticker that exposed pipeline failures — didn't complete SCORE/ANALYZE/RENDER, CLI silently produced partial state with no HTML.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 144-pipeline-rendering-resilience*
*Context gathered: 2026-03-28*
