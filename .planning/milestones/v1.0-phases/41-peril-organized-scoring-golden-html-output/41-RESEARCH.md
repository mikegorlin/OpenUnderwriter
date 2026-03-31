# Phase 41: Peril-Organized Scoring & Golden HTML Output - Research

**Researched:** 2026-02-24
**Domain:** Risk framework visualization, HTML rendering, quarterly financial presentation
**Confidence:** HIGH

## Summary

Phase 41 wires the brain risk framework (8 perils, 16 causal chains, 3-layer risk model) into the scoring stage and HTML rendering to replace the current flat check-list scoring presentation with a peril-organized view. The infrastructure is 90% built: `scoring_peril_data.py` (242 lines) already cross-references brain perils/chains with check results, `scoring.html.j2` (733 lines) already has a complete peril assessment template section (lines 53-115) that checks for `sc.get('peril_scoring', {})`, and both Word and Markdown renderers already call `extract_peril_scoring()`. The gap is that the SCORE stage never populates `peril_scoring` data into the scoring context dict consumed by the HTML template. Additionally, only the first quarterly filing is rendered in HTML, and frequency/severity factor dimensions from `risk_model.yaml` are not surfaced in the output.

**Primary recommendation:** Wire `extract_peril_scoring()` output into the `build_html_context()` scoring dict so the existing HTML template populates. Then extend quarterly rendering to show all available quarters with trend analysis. Make HTML the primary output format with PDF generated from it via Playwright.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.1+ | HTML template engine | Already in use for all HTML/Markdown rendering |
| Playwright | 1.40+ | HTML-to-PDF generation | Already wired as primary PDF engine |
| DuckDB | 0.10+ | Brain framework queries | Already in use for brain_perils/brain_causal_chains |
| python-docx | 0.8+ | Word document generation | Already in use for parallel Word rendering |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyyaml | 6.0+ | YAML framework file parsing | Already added in Phase 42 |
| Pydantic v2 | 2.0+ | State model validation | All data models use this |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jinja2 HTML | React/Vue SPA | Over-engineering; Jinja2 is established, Playwright renders it perfectly |
| Tailwind CSS in HTML | Raw CSS | Tailwind already compiled to static CSS (compiled.css); no build step needed |

## Architecture Patterns

### Current Architecture (What Exists)

```
Brain Framework (YAML source of truth)
├── brain/framework/perils.yaml        (8 perils)
├── brain/framework/causal_chains.yaml (16 chains)
├── brain/framework/risk_model.yaml    (3-layer model + F/S dimensions)
└── brain/framework/taxonomy.yaml      (risk vocabulary)
     │
     ▼ brain build
brain.duckdb (runtime cache)
├── brain_perils (8 rows)
├── brain_causal_chains (16 rows)
├── brain_risk_framework (19 rows)
├── brain_coverage_matrix (view)
└── brain_check_effectiveness (view)
     │
     ▼ BrainDBLoader.load_perils() / .load_causal_chains()
     │
scoring_peril_data.py::extract_peril_scoring(state)
├── Loads perils + chains from brain.duckdb
├── Cross-references with state.analysis.check_results
├── Evaluates each chain: triggers fired? amplifiers? mitigators?
├── Aggregates chains into peril-level risk assessments
└── Returns: {perils, all_perils, active_count, highest_peril}
     │
     ▼ [GAP: this data never reaches the HTML template context]
     │
scoring.html.j2 lines 53-115
├── Checks sc.get('peril_scoring', {}) — always empty
├── Template gracefully degrades (skips peril section)
└── Falls through to flat 10-factor table
```

### Target Architecture (What Phase 41 Builds)

```
SCORE Stage (__init__.py)
├── Existing 16-step scoring pipeline (untouched)
└── NEW Step 14.5: extract_peril_scoring() → populate peril_scoring on scoring context

build_html_context() (html_renderer.py)
├── Calls build_template_context() → gets scoring dict
├── scoring dict now includes peril_scoring key
└── Template renders peril assessment table + deep dives

scoring.html.j2
├── Peril assessment table (8 perils, risk level, active chains, evidence)
├── Per-peril deep dives (causal chains with T/A/M indicators)
├── Frequency vs Severity factor tagging
└── ALL quarterly financial updates (not just first)
```

### Pattern 1: Scoring Context Injection
**What:** The `extract_scoring()` function in `md_renderer_helpers_scoring.py` (line 218-225) already calls `extract_peril_scoring()` and merges the result as `result["peril_scoring"]`. This data flows through `build_template_context()` → `build_html_context()` → `scoring.html.j2`.
**When it works:** When `brain.duckdb` has `brain_perils` and `brain_causal_chains` tables populated and `state.analysis.check_results` contains evaluated checks.
**When it fails:** When `brain build` hasn't been run (tables missing) — `extract_peril_scoring()` returns `{}` and template gracefully skips the section.
**Current status:** This path WORKS for Word renderer (verified: `sect7_scoring.py` calls `extract_peril_scoring()` at line 445 and renders via `sect7_scoring_perils.py`). The HTML path also works — the issue is that the data IS being generated by `extract_scoring()` (line 218-225), so the gap may be smaller than initially assessed. Verification needed: run pipeline on a ticker and inspect whether `peril_scoring` key appears in the rendered HTML context.

### Pattern 2: Template Graceful Degradation
**What:** All HTML templates check for data presence before rendering. `{% if ps and ps.get('all_perils') %}` gates the entire peril section. This means the phase can be implemented incrementally — enhanced data flows in, template renders it, no regression if data is missing.
**Source:** `scoring.html.j2` line 55

### Pattern 3: Quarterly Multi-Update Rendering
**What:** The HTML template currently renders `qu_list[0]` (first/most-recent quarterly update only, line 203). The data model supports multiple `QuarterlyUpdate` objects in `ExtractedFinancials.quarterly_updates` (most-recent-first). The context builder `_build_quarterly_context()` already builds context dicts for ALL quarterly updates but the template only uses the first.
**Source:** `financial.html.j2` line 201-203, `md_renderer_helpers_financial.py` line 464-519

### Anti-Patterns to Avoid
- **Computing in RENDER stage:** Do NOT add scoring logic to the renderer. All peril evaluation happens in `scoring_peril_data.py::extract_peril_scoring()` which reads brain data and check results. The renderer only formats.
- **Duplicating template between formats:** Word renderer has its own peril rendering (`sect7_scoring_perils.py`). HTML has its own in `scoring.html.j2`. Do NOT try to share rendering logic between Word and HTML (per research anti-pattern from Phase 35).
- **Breaking existing scoring display:** The flat 10-factor table must remain. Peril assessment is ADDITIONAL visualization, not a replacement. User wants "all schools of thought" presented.
- **Hardcoding peril count:** Use `ps.all_perils|length` not `8` (Phase 42-03 decision — future-proof for peril additions).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Peril evaluation from checks | New evaluation engine | `scoring_peril_data.py::extract_peril_scoring()` | Already built, tested, handles both dict and Pydantic check results |
| Brain data loading | Direct SQL queries | `BrainDBLoader.load_perils()` / `.load_causal_chains()` | Already built, handles migration, fallbacks |
| HTML template rendering | String concatenation | Jinja2 templates in `templates/html/sections/` | Established pattern, all filters registered |
| Quarterly context building | New extraction logic | `_build_quarterly_context()` in `md_renderer_helpers_financial.py` | Already builds context for ALL quarters |
| PDF from HTML | WeasyPrint | Playwright headless Chromium | Already primary path, `render_html_pdf()` handles everything |

**Key insight:** The infrastructure is almost entirely built. Phase 42 created the brain framework tables and data loaders. `scoring_peril_data.py` already does the cross-referencing. The HTML template already has the rendering markup. The gap is in the data plumbing — ensuring the data actually reaches the template context — and in extending the quarterly rendering.

## Common Pitfalls

### Pitfall 1: brain.duckdb Not Rebuilt After Phase 42
**What goes wrong:** `brain_perils` and `brain_causal_chains` tables may not exist in the database because `brain build` was never run successfully (Phase 42 HANDOFF.md documents this: `build_framework()` fails without `create_schema(conn)` call).
**Why it happens:** Phase 42 code is complete but the `brain build` command has a one-line fix needed.
**How to avoid:** First task MUST be: apply the `create_schema(conn)` fix and run `brain build` to populate tables. Verify with `brain explore framework`.
**Warning signs:** `extract_peril_scoring()` returns `{}`, template skips peril section entirely.

### Pitfall 2: peril_scoring Already in Context but Template Not Receiving It
**What goes wrong:** The `extract_scoring()` function (line 218-225) already calls `extract_peril_scoring()` and adds the result as `result["peril_scoring"]`. But the HTML template accesses it as `sc.get('peril_scoring', {})` where `sc = scoring or {}`. If `scoring` context key has the data nested correctly, it should work.
**Why it happens:** Need to verify the context path: `context["scoring"]` → dict with `peril_scoring` key → template reads `sc.get('peril_scoring')`.
**How to avoid:** Run the pipeline, inspect the rendered HTML context dict, and verify the data path.
**Warning signs:** Word renderer shows perils but HTML does not.

### Pitfall 3: 500-Line Limit on Template
**What goes wrong:** `scoring.html.j2` is already 733 lines. Adding more content could make it unwieldy.
**Why it happens:** Templates are excluded from the 500-line Python source rule, but readability still matters.
**How to avoid:** The peril section (lines 53-115) is already in the template. If significant additions are needed, consider `{% include %}` directives to split into sub-templates.
**Warning signs:** Template becomes hard to reason about during debugging.

### Pitfall 4: Quarterly Data Present But Empty Fields
**What goes wrong:** Multiple `QuarterlyUpdate` objects exist but have `None` for revenue/net_income/eps, rendering as "N/A" rows.
**Why it happens:** 10-Q extraction via LLM may not populate all fields for every quarter.
**How to avoid:** Filter quarterly updates to only render those with at least one non-None financial metric. Add a "data coverage" indicator.
**Warning signs:** HTML shows 3 quarterly sections all showing "N/A" for every metric.

### Pitfall 5: Concurrent DuckDB Access During Rendering
**What goes wrong:** `extract_peril_scoring()` opens a `BrainDBLoader` connection to read perils/chains. If this runs while another process accesses brain.duckdb, contention may occur.
**Why it happens:** DuckDB allows single-writer, multiple-reader, but connection management must be clean.
**How to avoid:** `extract_peril_scoring()` already uses `try/finally` with `loader.close()`. Ensure no long-held connections.
**Warning signs:** "IO Error" or "database locked" during rendering.

## Code Examples

### Example 1: How peril_scoring reaches the HTML template (existing flow)

```python
# md_renderer_helpers_scoring.py line 218-225 (ALREADY EXISTS)
def extract_scoring(state: AnalysisState) -> dict[str, Any]:
    ...
    # Peril-organized scoring (Phase 42)
    try:
        from do_uw.stages.render.scoring_peril_data import extract_peril_scoring
        peril_data = extract_peril_scoring(state)
        if peril_data:
            result["peril_scoring"] = peril_data
    except ImportError:
        pass
    return result

# md_renderer.py line 135-136 (ALREADY EXISTS)
if state.scoring is not None:
    context["scoring"] = extract_scoring(state)

# html_renderer.py line 410 (ALREADY EXISTS)
context = build_template_context(state, chart_dir)  # inherits scoring context

# scoring.html.j2 line 8-9 + 54-55 (ALREADY EXISTS)
# {% set sc = scoring or {} %}
# {% set ps = sc.get('peril_scoring', {}) %}
# {% if ps and ps.get('all_perils') %}
```

### Example 2: How to extend quarterly rendering (template change)

```jinja2
{# CURRENT: Only renders first quarterly update #}
{% set qu_list = fin.get('quarterly_updates', []) %}
{% if qu_list %}
{% set qu = qu_list[0] %}
...

{# TARGET: Render all quarterly updates with trend analysis #}
{% set qu_list = fin.get('quarterly_updates', []) %}
{% if qu_list %}
{% for qu in qu_list %}
<h3>{{ 'Post-Annual Update' if loop.first else 'Prior Quarter' }}: {{ qu.quarter }}</h3>
...
{% endfor %}
{# Trend summary across quarters #}
{% if qu_list|length > 1 %}
<h3>Quarterly Trend Analysis</h3>
...
{% endif %}
{% endif %}
```

### Example 3: Frequency vs Severity factor tagging (from risk_model.yaml)

```yaml
# brain/framework/risk_model.yaml (ALREADY EXISTS)
factor_dimensions:
  F1:
    name: "Prior Litigation History"
    role: FREQUENCY
  F2:
    name: "Stock Price Decline"
    role: BOTH  # Triggers claims AND correlates with settlement size
  F7:
    name: "Stock Volatility"
    role: SEVERITY
```

To surface this in the template, load `factor_dimensions` from `risk_model.yaml` or `brain_risk_framework` table and annotate each factor in the 10-factor table with its F/S role badge.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat check list (400 checks, random order) | Peril-organized view (8 perils, 16 chains) | Phase 42 (brain framework) | Underwriter sees "Securities Risk: HIGH" not "check BIZ.SIZE.public_tenure = TRIGGERED" |
| Word as primary output | HTML as primary output | Phase 35/40 (Bloomberg template) | HTML renders in browser, generates PDF via Playwright, richer interactivity |
| Single quarterly update | Multiple quarterly updates | Phase 38 (quarterly models) | Data model supports multiple; rendering shows only first |
| Factor scores as flat numbers | Factor scores with F/S dimension | Phase 42 (risk_model.yaml) | Each factor tagged as frequency driver, severity driver, or both |

## Key Files (Annotated)

### Brain Framework Data Layer
| File | Lines | Role |
|------|-------|------|
| `brain/framework/perils.yaml` | 108 | Source of truth: 8 D&O claim perils with frequency/severity/settlement ranges |
| `brain/framework/causal_chains.yaml` | 482 | Source of truth: 16 causal chains mapping checks to perils |
| `brain/framework/risk_model.yaml` | 116 | Source of truth: 3-layer model + F/S factor dimensions |
| `brain/brain_loader.py` | 498 | `load_perils()` and `load_causal_chains()` from DuckDB |
| `brain/brain_schema.py` | ~422 | DDL for `brain_perils`, `brain_causal_chains`, `brain_risk_framework` |
| `brain/brain_migrate_framework.py` | ~200 | `brain build` populates tables from YAML |

### Scoring & Peril Evaluation
| File | Lines | Role |
|------|-------|------|
| `stages/score/__init__.py` | 471 | 16-step scoring pipeline orchestrator. Step 14 builds peril map (plaintiff lens), NOT brain peril assessment |
| `stages/score/factor_scoring.py` | 500 | F1-F10 factor scoring engine |
| `stages/score/peril_mapping.py` | 406 | 7-lens plaintiff assessment (SHAREHOLDERS, REGULATORS, etc.) — distinct from brain perils |
| `stages/render/scoring_peril_data.py` | 242 | `extract_peril_scoring()`: cross-references brain perils/chains with check results |

### Rendering Layer
| File | Lines | Role |
|------|-------|------|
| `stages/render/html_renderer.py` | 695 | `build_html_context()` + `render_html_pdf()` — HTML context builder and PDF generator |
| `stages/render/md_renderer.py` | ~170 | `build_template_context()` — shared context builder (base for HTML) |
| `stages/render/md_renderer_helpers_scoring.py` | 366 | `extract_scoring()` — scoring context extraction (calls `extract_peril_scoring()` at line 218) |
| `stages/render/sections/sect7_scoring.py` | 473 | Word renderer: Section 7 orchestrator. Calls `_render_peril_scoring()` at line 412 |
| `stages/render/sections/sect7_scoring_perils.py` | 313 | Word renderer: peril summary table + deep dives |
| `templates/html/sections/scoring.html.j2` | 733 | HTML scoring template. Peril section at lines 53-115 (exists but data-gated) |
| `templates/html/sections/financial.html.j2` | ~350 | HTML financial template. Quarterly section at line 201 (single update only) |
| `stages/render/md_renderer_helpers_financial.py` | ~530 | Financial context extraction. `_build_quarterly_context()` builds ALL quarters |

## Critical Distinctions

### Peril Map vs Peril Scoring
The codebase has TWO different peril-related concepts:

1. **Peril Map** (`peril_mapping.py` / `stages/score/peril_mapping.py`): 7-lens plaintiff assessment (SHAREHOLDERS, REGULATORS, EMPLOYEES, etc.) with probability/severity bands. This is the Phase 27 plaintiff lens model. Stored on `state.analysis.peril_map`. Rendered in the EXISTING "Peril Map" section of scoring template (lines 642-684).

2. **Peril Scoring** (`scoring_peril_data.py`): 8-peril brain framework assessment (SECURITIES, FIDUCIARY, REGULATORY, etc.) using causal chains. This is the Phase 42 brain risk framework. Generated by `extract_peril_scoring()` at render time. Rendered in the "D&O Claim Peril Assessment" section (lines 53-115).

These are COMPLEMENTARY views — both should appear in the output. The peril map shows who might sue; the peril scoring shows what kind of claims are most likely.

### Factor F/S Roles
Each of the 10 scoring factors has a designated role from `risk_model.yaml`:
- **FREQUENCY** factors (F1, F3, F4, F5, F6, F9, F10): Drive claim filing probability
- **SEVERITY** factors (F7): Drive settlement/loss amount
- **BOTH** factors (F2, F8): Drive both frequency and severity

This distinction is defined in YAML but NOT currently surfaced in any output. The 10-factor scoring table should annotate each factor with its F/S role.

## Scope Assessment

### Must Do (Core Phase 41)
1. Fix `brain build` (one-line fix from HANDOFF.md) and verify tables populated
2. Verify peril_scoring data flow from `extract_scoring()` → HTML template
3. If data flow broken, fix the plumbing
4. Extend quarterly rendering to show all available quarters
5. Add quarterly trend analysis (sequential deterioration detection)
6. Annotate 10-factor table with frequency/severity roles
7. Make HTML the golden (primary) output — ensure all scoring content renders

### Should Do (Enhances Quality)
8. Add peril-level settlement range and historical filing rate to template
9. Cross-link factor scores to perils (show which perils each factor drives)
10. Add causal chain activation summary to executive summary

### Could Defer
11. Interactive drill-down from peril to chains (requires JS in HTML)
12. Heat map visualization for peril risk levels
13. Side-by-side frequency vs severity breakdown chart

## Open Questions

1. **Is peril_scoring already populating in HTML output?**
   - What we know: `extract_scoring()` calls `extract_peril_scoring()` and adds it to the scoring dict. `build_template_context()` puts this in `context["scoring"]`. HTML template reads `sc.get('peril_scoring')`.
   - What's unclear: Whether `brain build` has been run successfully and tables are populated.
   - Recommendation: First task = run `brain build`, run pipeline on a ticker, inspect HTML output. This may reveal the phase is partially already working.

2. **How many quarterly updates does the pipeline actually extract?**
   - What we know: The model supports `list[QuarterlyUpdate]` and the acquisition stage fetches multiple 10-Qs.
   - What's unclear: How many typically have non-empty financial data.
   - Recommendation: Inspect a real state.json to count quarterly updates with data.

3. **Should the peril assessment replace or augment the existing plaintiff lens peril map?**
   - What we know: They are different views (claim type vs plaintiff type).
   - Recommendation: Augment — show both. User explicitly wants "all schools of thought."

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run python -m pytest tests/ -x --no-header -q` |
| Full suite command | `uv run python -m pytest tests/ --no-header -q` |
| Estimated runtime | ~30-60 seconds |

### Relevant Existing Tests
| Test File | Coverage | Status |
|-----------|----------|--------|
| `tests/brain/test_brain_framework.py` | Brain perils, chains, framework build | 23 tests, passing |
| `tests/brain/test_brain_schema.py` | Schema DDL, table/view counts | Passing |
| `tests/test_scoring.py` | 10-factor scoring, CRF gates | Passing |
| `tests/test_html_renderer.py` | HTML context building | Passing |
| `tests/render/test_md_renderer.py` | Markdown template rendering | Passing |

### Phase 41 Test Requirements
| Behavior | Test Type | Approach |
|----------|-----------|----------|
| Peril scoring data flows to HTML template | Integration | Render HTML for a mock state with check results, verify peril section appears |
| All quarterly updates rendered in HTML | Unit | Build context with 3 quarterly updates, verify all in output |
| Factor F/S role annotation present | Unit | Verify scoring context dict includes F/S role from risk_model.yaml |
| brain build populates peril tables | Integration | Run brain build, query brain_perils count = 8 |
| Template graceful degradation | Unit | Render with empty peril_scoring, verify no errors |

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `scoring_peril_data.py`, `scoring.html.j2`, `brain_loader.py`, `html_renderer.py`, `md_renderer_helpers_scoring.py`
- Brain framework YAML files: `perils.yaml`, `causal_chains.yaml`, `risk_model.yaml`
- Phase 42 HANDOFF.md: documents current state and known issues

### Secondary (MEDIUM confidence)
- Phase 42 plan documents (42-01 through 42-04): implementation details for brain framework
- User priorities from MEMORY.md: "restructure worksheet scoring presentation around perils/causal chains"

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all libraries already in use, no new dependencies
- Architecture: HIGH - all infrastructure exists, phase is primarily plumbing and template work
- Pitfalls: HIGH - based on direct codebase inspection, known issues documented in HANDOFF.md

**Research date:** 2026-02-24
**Valid until:** 2026-03-24 (stable codebase, no external dependency changes expected)
