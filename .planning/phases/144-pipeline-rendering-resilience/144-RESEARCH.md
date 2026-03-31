# Phase 144: Pipeline & Rendering Resilience - Research

**Researched:** 2026-03-28
**Domain:** Pipeline error handling, defensive rendering, partial-output resilience
**Confidence:** HIGH

## Summary

Phase 144 converts the pipeline from fail-fast (raise PipelineError on first stage failure) to continue-on-error (catch failures, mark stage FAILED, continue to RENDER). The pipeline currently has 7 stages with strict sequential validation gates -- each stage's `validate_input()` checks that the previous stage is COMPLETED. This gate chain must be relaxed so RENDER runs even when upstream stages fail.

The rendering layer already has partial resilience patterns: chart generation catches individual chart failures, context builders are wrapped in try/except in the assembly registry, and `SectionCompletenessGate` suppresses >50% N/A sections with banners. This phase extends those patterns systematically to all chart builders (None guards) and all section templates (amber "Incomplete" banners).

**Primary recommendation:** Modify `Pipeline.run()` to catch-and-continue on both validation and execution failures, relax `validate_input()` gates to allow FAILED predecessor stages, add a systematic `@null_safe_chart` decorator for all chart builders, and extend `SectionCompletenessGate` with stage-failure-aware banners.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Pipeline continues through ALL remaining stages after a failure. Failed stage is logged and marked in state, but pipeline does not raise PipelineError -- it continues to RENDER. Currently `pipeline.py:181-194` raises on failure; this must change to catch-and-continue.
- D-02: CLI exits 0 with warnings when HTML is produced, even if stages failed. Producing output = success. Failed stages are logged as warnings.
- D-03: `state.mark_stage_failed()` already exists -- use it. Stage status (pending/running/complete/failed) + duration + error message all tracked per stage.
- D-04: Sections with missing data render with an amber "Incomplete -- [Stage] did not complete" banner at top, then show whatever partial data IS available below. Partial info > no info.
- D-05: Chart builders that receive None data render a gray placeholder box (same dimensions as chart) with centered "No data available" text. Maintains layout flow, no broken whitespace or AttributeError crashes.
- D-06: Every chart builder must guard against None input systematically -- not ad-hoc per builder.
- D-07: Pipeline stage status displayed in the audit section of the worksheet, not a separate footer. Full traceability: each stage shows status (complete/failed/skipped), duration, and error message if failed.
- D-08: Guiding principle: "single source of truth" -- the worksheet must show what the pipeline did, what data it has, and what's missing. No hiding failures.
- D-09: Dual-path render -- risk card context builder pulls from `acquired_data` directly, never from `extracted` data. Two completely separate data paths. Even if EXTRACT/ANALYZE/SCORE all fail, Supabase SCA data renders independently.

### Claude's Discretion
- Chart placeholder styling (exact gray shade, font size, border treatment)
- Whether to add a `@contextmanager` for stage execution or keep inline try/except
- How to structure the audit section template (table vs cards vs list)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RES-01 | Pipeline completes all 7 stages or logs clear error with stage name and traceback; state.json includes stage status for each stage | Pipeline.run() catch-and-continue pattern; StageResult model already tracks status/duration/error |
| RES-02 | Every chart builder guards against None data -- no AttributeError crashes; empty chart renders placeholder | Decorator pattern on 11 chart builder functions; gray placeholder SVG/PNG generation |
| RES-03 | Every section template guards against missing context -- show banners for missing stages | Extend SectionCompletenessGate with stage-failure awareness; amber banner pattern |
| RES-04 | Risk card renders from acquired_data even when extraction is incomplete | _hydrate_risk_card() already reads from acquired_data.litigation_data; needs isolation from extracted path |
| RES-05 | CLI always produces HTML output even on partial pipeline completion | CLI catch block change from Exit(1) to Exit(0) with warnings when HTML exists |
| RES-06 | Pipeline stage status tracked in state.json -- each stage records status, duration, error | StageResult model already has these fields; need audit section template to display them |
</phase_requirements>

## Architecture Patterns

### Pattern 1: Pipeline Catch-and-Continue

**What:** Replace the raise-on-failure pattern in `Pipeline.run()` with catch-and-continue.

**Current code (pipeline.py:170-194):**
```python
# Validation -- currently raises PipelineError
try:
    stage.validate_input(state)
except ValueError as exc:
    state.mark_stage_failed(stage.name, error_msg)
    self._save_state(state)
    raise PipelineError(error_msg) from exc

# Execution -- currently raises PipelineError
try:
    stage.run(state)
except Exception as exc:
    state.mark_stage_failed(stage.name, str(exc))
    self._save_state(state)
    raise PipelineError(error_msg) from exc
```

**New pattern:**
```python
# Validation -- catch and continue
try:
    stage.validate_input(state)
except ValueError as exc:
    error_msg = f"Validation failed for {stage.name}: {exc}"
    state.mark_stage_failed(stage.name, error_msg)
    self._callbacks.on_stage_fail(stage.name, index, total, error_msg)
    self._save_state(state)
    logger.warning("Stage %s skipped: %s", stage.name, error_msg)
    continue  # <-- KEY CHANGE: continue instead of raise

# Execution -- catch and continue
try:
    stage.run(state)
except Exception as exc:
    error_msg = f"Stage {stage.name} failed: {exc}"
    state.mark_stage_failed(stage.name, str(exc))
    self._callbacks.on_stage_fail(stage.name, index, total, error_msg)
    self._save_state(state)
    logger.warning("Stage %s failed: %s", stage.name, error_msg)
    continue  # <-- KEY CHANGE: continue instead of raise
```

**Critical detail:** The `run()` method must return a boolean or summary indicating whether any stages failed, so the CLI can decide exit code. A new `pipeline_had_failures` flag on state or a return value works.

**When to use:** Always -- this is the only pipeline execution pattern going forward.

### Pattern 2: Relaxed Validation Gates

**What:** Each stage's `validate_input()` currently requires the previous stage to be COMPLETED. With catch-and-continue, predecessor stages may be FAILED. Validation must be relaxed to allow running with degraded input.

**Current gates (all raise ValueError if predecessor != COMPLETED):**
| Stage | Requires |
|-------|----------|
| resolve | ticker present (no predecessor) |
| acquire | resolve COMPLETED + company exists |
| extract | acquire COMPLETED + acquired_data exists |
| analyze | extract COMPLETED |
| score | analyze COMPLETED |
| benchmark | score COMPLETED |
| render | benchmark COMPLETED |

**New approach:** Two options:
1. **Option A (recommended): Skip validation on failed predecessors.** If the predecessor is FAILED, log a warning and proceed. The stage itself will encounter None data and handle gracefully or fail fast with a clear error. This is simpler and the stage's own error handling captures the actual problem.
2. **Option B:** Rewrite each validate_input to accept FAILED predecessors. More defensive but more code.

**Recommendation:** Option A -- move the validation relaxation to `Pipeline.run()` itself. If the predecessor stage is FAILED, skip the validation call entirely and let the stage try to run (it will fail if it can't work with the data, and that failure gets caught by catch-and-continue).

**Special case -- RESOLVE:** If resolve fails, the entire pipeline is useless (no ticker identity). Pipeline should still continue to attempt remaining stages, but they'll all fail validation immediately. The important thing is that state.json is saved with clear status for each stage.

### Pattern 3: Null-Safe Chart Decorator

**What:** A decorator that wraps chart builder functions to catch None/missing data and return a placeholder instead of crashing.

**Chart builders that need guarding (11 functions across 9 modules):**
| Module | Function | Data Source |
|--------|----------|-------------|
| `charts/stock_charts.py` | `create_stock_chart` | `state.acquired_data.market_data` |
| `charts/stock_charts.py` | `create_stock_performance_chart` | same |
| `charts/stock_charts.py` | `create_stock_performance_chart_5y` | same |
| `charts/drawdown_chart.py` | `create_drawdown_chart` | `state.acquired_data.market_data` |
| `charts/drop_analysis_chart.py` | `create_drop_analysis_chart` | `state.extracted.market.stock_drops` |
| `charts/drop_analysis_chart.py` | `create_drop_scatter_chart` | same |
| `charts/volatility_chart.py` | `create_volatility_chart` | `state.acquired_data.market_data` |
| `charts/relative_performance_chart.py` | `create_relative_performance_chart` | `state.acquired_data.market_data` |
| `charts/ownership_chart.py` | `create_ownership_chart` | `state.extracted.governance.ownership` |
| `charts/radar_chart.py` | `create_radar_chart` | `state.scoring.factor_scores` |
| `charts/timeline_chart.py` | `create_litigation_timeline` | `state.extracted.litigation` |
| `charts/waterfall_chart.py` | `render_waterfall_chart` | scoring data |
| `charts/tornado_chart.py` | `render_tornado_chart` | scoring data |
| `context_builders/_stock_chart_mpl.py` | `render_stock_chart_png` | market data |
| `context_builders/beta_report_charts.py` | `build_stock_chart_svg` | market data |

**Implementation:**
```python
# In chart_helpers.py or a new chart_guards.py
import functools
import io
from typing import Any, Callable

def null_safe_chart(fn: Callable[..., io.BytesIO | str | None]) -> Callable[..., io.BytesIO | str | None]:
    """Decorator: return None (or placeholder) if chart data is missing."""
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> io.BytesIO | str | None:
        try:
            return fn(*args, **kwargs)
        except (AttributeError, TypeError, KeyError, IndexError) as exc:
            logger.warning("Chart %s skipped (missing data): %s", fn.__name__, exc)
            return None  # Caller renders placeholder
    return wrapper
```

**Gray placeholder generation (for callers in `_generate_chart_images`):**
```python
def create_chart_placeholder(width: int = 800, height: int = 400, label: str = "No data available") -> io.BytesIO:
    """Create a gray placeholder PNG with centered text."""
    fig, ax = plt.subplots(figsize=(width/100, height/100))
    ax.set_facecolor("#E5E7EB")  # gray-200
    ax.text(0.5, 0.5, label, ha="center", va="center",
            fontsize=14, color="#6B7280", transform=ax.transAxes)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="#E5E7EB")
    plt.close(fig)
    buf.seek(0)
    return buf
```

### Pattern 4: Stage-Failure-Aware Section Banners

**What:** Extend the existing `SectionCompletenessGate` pattern to detect stage failures and inject amber banners into template context.

**Existing pattern (from Phase 142):**
- `SectionCompletenessGate.apply_banners(context)` scans context sections for >50% N/A values and replaces with `{"_suppressed": True, "_banner": "..."}` dicts
- Templates use `{% if section_var and not section_var._suppressed %}` guards

**Extension for stage failures:**
- After `build_html_context()` runs, check `state.stages` for FAILED stages
- Map failed stages to affected sections:
  - extract FAILED -> financial, governance, market, litigation sections incomplete
  - analyze FAILED -> signal results, check results missing
  - score FAILED -> scoring, risk tier, factor scores missing
  - benchmark FAILED -> peer comparisons missing
- Inject `_stage_banner` into affected section contexts: `"Incomplete -- Extract stage did not complete"`

**Template pattern:**
```html
{% if section._stage_banner %}
<div class="stage-failure-banner" style="background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 8px 12px; margin-bottom: 12px; font-size: 12px; color: #92400E;">
  {{ section._stage_banner }}
</div>
{% endif %}
```

### Pattern 5: CLI Exit Code Logic

**Current (cli.py:447-498):**
```python
try:
    state = pipeline.run(state)
    # ... post-pipeline QA, health summary, etc.
    console.print("[bold green]Analysis complete![/bold green]")
except PipelineError as exc:
    console.print(f"[bold red]Pipeline failed:[/bold red] {exc}")
    raise typer.Exit(code=1) from exc
```

**New pattern:**
```python
state = pipeline.run(state)  # Never raises PipelineError anymore

# Check if HTML was produced
html_files = list(output_dir.glob("*.html"))
failed_stages = [s for s, r in state.stages.items() if r.status == StageStatus.FAILED]

if failed_stages:
    for s in failed_stages:
        result = state.stages[s]
        console.print(f"[yellow]WARNING: Stage {s} failed: {result.error}[/yellow]")

if html_files:
    console.print("[bold green]Analysis complete (with warnings)![/bold green]")
    # Exit 0 -- HTML was produced
else:
    console.print("[bold red]Pipeline failed -- no output produced[/bold red]")
    raise typer.Exit(code=1)
```

### Pattern 6: Audit Section Stage Status Display (D-07)

**What:** Add a pipeline execution summary to the audit section of the HTML worksheet.

**Stage-to-display mapping (from state.stages):**
```python
def build_pipeline_status_context(state: AnalysisState) -> list[dict[str, Any]]:
    """Build pipeline stage status for audit section template."""
    rows = []
    for stage_name in PIPELINE_STAGES:
        result = state.stages.get(stage_name)
        if result is None:
            continue
        rows.append({
            "stage": stage_name.upper(),
            "status": result.status.value,
            "duration": f"{result.duration_seconds:.1f}s" if result.duration_seconds else "---",
            "error": result.error or "",
            "status_class": {
                "completed": "status-ok",
                "failed": "status-fail",
                "skipped": "status-skip",
                "pending": "status-pending",
            }.get(result.status.value, ""),
        })
    return rows
```

**Template (table in audit section):**
```html
<table class="pipeline-status">
  <thead><tr><th>Stage</th><th>Status</th><th>Duration</th><th>Error</th></tr></thead>
  <tbody>
  {% for row in pipeline_status %}
  <tr class="{{ row.status_class }}">
    <td>{{ row.stage }}</td>
    <td>{{ row.status }}</td>
    <td>{{ row.duration }}</td>
    <td>{{ row.error }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
```

### Anti-Patterns to Avoid
- **Swallowing errors silently:** Every caught exception MUST be logged with stage name, error message, and traceback at WARNING level. The worksheet audit section must show failures.
- **Removing validate_input():** Keep validation -- just catch the ValueError instead of propagating it. Validation messages are useful diagnostic info recorded in stage error.
- **Ad-hoc None checks in each chart:** Use the decorator pattern for consistency. Individual chart builders should NOT have their own try/except wrappers -- the decorator handles it.
- **Hiding failures from the user:** The CLI must print warnings for failed stages. The worksheet must show banners. State.json must have the full picture.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Placeholder chart images | Custom per-chart empty state rendering | Centralized `create_chart_placeholder()` function | One function, consistent styling, DRY |
| Stage failure to section mapping | Hardcoded if/else chains | Data-driven dict mapping `failed_stage -> [affected_sections]` | Easy to maintain as sections change |
| N/A detection for banners | New N/A scanning logic | Extend existing `SectionCompletenessGate` | Already tested, handles edge cases |

## Common Pitfalls

### Pitfall 1: Render Stage Validation Gate Blocks Everything
**What goes wrong:** The RenderStage.validate_input() requires benchmark COMPLETED. If any upstream stage fails, render never runs -- defeating the entire purpose.
**Why it happens:** Current architecture has strict sequential gates.
**How to avoid:** Pipeline.run() must skip validation when predecessor failed, OR RenderStage.validate_input() must accept degraded state.
**Warning signs:** Pipeline completes but no HTML file is produced.

### Pitfall 2: Context Builders Crash on None State Fields
**What goes wrong:** `build_html_context()` calls ~100 builder functions. Many assume `state.extracted` or `state.scoring` exists. If EXTRACT failed, `state.extracted` is None and builders crash with AttributeError.
**Why it happens:** Builders were written assuming all stages complete.
**How to avoid:** Each builder is already wrapped in try/except in the assembly registry (line 119-127). This existing pattern catches builder failures. The key is that the template also needs to handle missing context keys gracefully (via `{% if %}` guards and `| default()` filters).
**Warning signs:** Empty sections with no banner explanation.

### Pitfall 3: Chart Placeholder Breaks Layout
**What goes wrong:** A PNG placeholder has different dimensions than the expected chart, causing layout shifts in the HTML.
**Why it happens:** Each chart type has different dimensions.
**How to avoid:** The placeholder generator must accept width/height parameters matching the chart's expected dimensions. Or use CSS to constrain chart containers to fixed dimensions.
**Warning signs:** Visual layout jumps when comparing complete vs partial worksheets.

### Pitfall 4: Resume Skips Failed Stages Instead of Retrying
**What goes wrong:** Current resume logic skips COMPLETED stages. If we also skip FAILED stages, a re-run after fixing the underlying issue won't retry.
**Why it happens:** Adding FAILED to skip conditions.
**How to avoid:** ONLY skip COMPLETED stages on resume. FAILED stages should be retried (they go back to RUNNING). This is the current behavior and should be preserved.
**Warning signs:** User runs `underwrite TICKER` again after fixing an API key, but failed stages are still FAILED.

### Pitfall 5: PipelineError Removal Breaks Tests
**What goes wrong:** Existing tests likely assert `raises(PipelineError)` for failure cases.
**Why it happens:** Test expectations match old raise-on-failure behavior.
**How to avoid:** Update tests to assert stage status is FAILED in state rather than catching PipelineError. Keep PipelineError class for backward compat but pipeline.run() no longer raises it.
**Warning signs:** Test failures after pipeline changes.

## Code Examples

### Example 1: Pipeline.run() with catch-and-continue
```python
def run(self, state: AnalysisState) -> AnalysisState:
    total = len(self._stages)
    for index, stage in enumerate(self._stages):
        stage_result = state.stages.get(stage.name)
        if stage_result is not None and stage_result.status == StageStatus.COMPLETED:
            self._callbacks.on_stage_skip(stage.name, index, total)
            continue

        # Validate -- catch failures, continue pipeline
        try:
            stage.validate_input(state)
        except ValueError as exc:
            error_msg = f"Validation failed for {stage.name}: {exc}"
            state.mark_stage_failed(stage.name, error_msg)
            self._callbacks.on_stage_fail(stage.name, index, total, error_msg)
            self._save_state(state)
            logger.warning(error_msg)
            continue

        # Execute -- catch failures, continue pipeline
        self._callbacks.on_stage_start(stage.name, index, total)
        try:
            stage.run(state)
        except Exception as exc:
            error_msg = f"Stage {stage.name} failed: {exc}"
            state.mark_stage_failed(stage.name, str(exc))
            self._callbacks.on_stage_fail(stage.name, index, total, error_msg)
            self._save_state(state)
            logger.warning(error_msg)
            continue

        duration = state.stages[stage.name].duration_seconds
        self._callbacks.on_stage_complete(stage.name, index, total, duration)
        self._save_state(state)

    # Post-pipeline hooks (render audit, learning) unchanged
    ...
    return state
```

### Example 2: Stage failure to section mapping
```python
# In a new module or in html_context_assembly.py
STAGE_SECTION_MAP: dict[str, list[str]] = {
    "extract": ["financials", "governance", "market", "litigation", "company"],
    "analyze": ["signal_results", "check_results", "analysis"],
    "score": ["scoring", "factor_scores", "risk_tier", "red_flags"],
    "benchmark": ["peer_comparison", "benchmark"],
}

def inject_stage_failure_banners(
    state: AnalysisState, context: dict[str, Any]
) -> None:
    """Add amber banners to sections affected by failed stages."""
    for stage_name, result in state.stages.items():
        if result.status != StageStatus.FAILED:
            continue
        affected = STAGE_SECTION_MAP.get(stage_name, [])
        for section_key in affected:
            if section_key in context and isinstance(context[section_key], dict):
                context[section_key]["_stage_banner"] = (
                    f"Incomplete -- {stage_name.upper()} stage did not complete: "
                    f"{result.error or 'unknown error'}"
                )
```

### Example 3: Risk card dual-path (D-09)
```python
# In litigation context builder -- _hydrate_risk_card already reads from acquired_data
# The key insight: this function already works correctly!
# It reads from state.acquired_data.litigation_data["risk_card"]
# This is populated in ACQUIRE, not EXTRACT.
# If EXTRACT fails, acquired_data is still intact.
# No code change needed -- just verify with a test.
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/ -x --timeout=30 -q` |
| Full suite command | `uv run pytest tests/ --timeout=60` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RES-01 | Pipeline continues after stage failure, state.json has all stage statuses | unit | `uv run pytest tests/test_pipeline_resilience.py::test_continue_on_failure -x` | Wave 0 |
| RES-02 | Chart builders return None (not crash) on missing data | unit | `uv run pytest tests/stages/render/test_chart_null_safety.py -x` | Wave 0 |
| RES-03 | Section templates show banner when stage failed | unit | `uv run pytest tests/stages/render/test_stage_failure_banners.py -x` | Wave 0 |
| RES-04 | Risk card renders from acquired_data when extract fails | unit | `uv run pytest tests/stages/render/test_risk_card_isolation.py -x` | Wave 0 |
| RES-05 | CLI exits 0 when HTML produced despite stage failures | unit | `uv run pytest tests/test_cli_resilience.py -x` | Wave 0 |
| RES-06 | Pipeline status visible in audit section context | unit | `uv run pytest tests/stages/render/test_pipeline_status_context.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x --timeout=30 -q -k "resilience or null_safety or banner or isolation"`
- **Per wave merge:** `uv run pytest tests/ --timeout=60`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_pipeline_resilience.py` -- covers RES-01 (pipeline catch-and-continue)
- [ ] `tests/stages/render/test_chart_null_safety.py` -- covers RES-02 (all chart builders with None input)
- [ ] `tests/stages/render/test_stage_failure_banners.py` -- covers RES-03 (section banners)
- [ ] `tests/stages/render/test_risk_card_isolation.py` -- covers RES-04 (risk card from acquired_data)
- [ ] `tests/test_cli_resilience.py` -- covers RES-05 (CLI exit codes)
- [ ] `tests/stages/render/test_pipeline_status_context.py` -- covers RES-06 (audit section)

## Open Questions

1. **Post-pipeline hooks when render fails**
   - What we know: `_inject_render_audit()` and `run_post_pipeline_learning()` run after all stages. If render itself fails (partial or complete), these may fail too.
   - What's unclear: Should post-pipeline hooks also be catch-and-continue?
   - Recommendation: Yes -- wrap them in try/except (render_audit already is). This is low risk since they're already partially guarded.

2. **Word/PDF output when data is partial**
   - What we know: HTML is the primary output. Word and PDF are generated in the render stage.
   - What's unclear: Should Word/PDF also attempt partial rendering?
   - Recommendation: Focus on HTML. Word/PDF secondary renderers already have try/except wrappers in `_render_secondary()`. Let them fail gracefully -- HTML is the success criterion per D-02.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/pipeline.py` -- Current pipeline orchestration, lines 141-263
- `src/do_uw/models/common.py` -- StageStatus enum, StageResult model
- `src/do_uw/models/state.py` -- AnalysisState.mark_stage_failed(), PIPELINE_STAGES
- `src/do_uw/stages/render/__init__.py` -- RenderStage.validate_input() gate, _generate_chart_images() existing error handling
- `src/do_uw/stages/render/context_builders/assembly_registry.py` -- Builder try/except pattern (lines 119-127)
- `src/do_uw/validation/section_completeness.py` -- SectionCompletenessGate pattern
- `src/do_uw/stages/render/context_builders/litigation.py` -- _hydrate_risk_card() reads from acquired_data
- `src/do_uw/cli.py` -- Current PipelineError catch block (lines 447-498)

### Secondary (MEDIUM confidence)
- `.planning/milestones/v13.0-worksheet-excellence/MILESTONE.md` -- Known combo chart crash on stock_drops None

## Metadata

**Confidence breakdown:**
- Pipeline catch-and-continue: HIGH -- the change is mechanical (raise -> continue), existing infrastructure supports it
- Chart null safety: HIGH -- chart builders already return None for missing data, decorator pattern is standard Python
- Section banners: HIGH -- SectionCompletenessGate pattern already exists and is tested
- Risk card isolation: HIGH -- _hydrate_risk_card already reads from acquired_data, no change needed, just verification
- CLI exit code: HIGH -- straightforward control flow change

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable domain -- internal Python patterns, no external dependencies)
