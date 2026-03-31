# Brain-Driven Architecture Redesign

## Context

The D&O underwriting system has 90K+ lines of code, 400 signals, and genuinely valuable analytical capabilities (4 distress models, DDL settlement prediction, 7-lens plaintiff assessment, Bloomberg-quality HTML). But the brain YAML — which is supposed to be the single source of truth driving acquisition, evaluation, and rendering — currently only drives ~60% of the pipeline. Acquisition is hardcoded. Rendering is hardcoded. There are 5 different data stores and 4 loaders. The user's vision: "the brain dictates everything we check, where we get the data, how we evaluate it, and how we display it."

This plan makes the brain actually drive the system, evolutionary (not a rewrite).

---

## What We're Preserving (These Work Well)

1. **7-stage pipeline** (RESOLVE → ACQUIRE → EXTRACT → ANALYZE → SCORE → BENCHMARK → RENDER)
2. **Single AnalysisState** as the only data model
3. **4 distress models** (Altman, Beneish, Piotroski, Ohlson)
4. **DDL settlement prediction** with case characteristic multipliers
5. **7-lens plaintiff assessment** (shareholders, regulators, employees, etc.)
6. **10-factor scoring** with CRF gates
7. **18 causal chains** mapping signals → perils → claims
8. **Bloomberg-quality HTML** with CapIQ sidebar, density indicators, risk coloring
9. **Source + confidence discipline** on every data point
10. **Feedback loop infrastructure** (Phase 51)

---

## The 6 Problems We're Solving

### P1: Signals don't contain acquisition instructions
Signals say `required_data: [SEC_10Q]` but the pipeline runs 4 hardcoded clients regardless. Adding a new signal that needs a new source requires writing Python code.

### P2: Signals don't contain evaluation logic
Thresholds are English text (`red: <1.0 current ratio`) that Python must parse. No formulas, no edge case handling. 500+ lines of procedural mappers translate fields manually.

### P3: Facets don't drive rendering
Facets define `display_type`, `signals`, `content`, `render_as` — but renderers are 100% hardcoded. Section order, content, layout: all Python/Jinja2, no brain involvement.

### P4: DuckDB intermediary adds complexity without benefit
YAML → (brain build) → DuckDB → (BrainDBLoader) → Pipeline. Manual sync step. If you edit YAML and forget `brain build`, you run on stale data.

### P5: 5 data stores, 21 duplicate config files, 4 loaders
brain.duckdb, knowledge.db, brain/config/*.json, config/*.json, analysis.db. Most config duplicated across directories. 4 loaders with fallback chains.

### P6: No closed learning loop
Run history is stored but not analyzed. No automatic threshold calibration. No signal effectiveness tracking that feeds back into the brain.

---

## The Redesign: 6 Phases

### Phase 1: Signal Contract V2 (Make signals self-contained)

**Goal**: Extend signal YAML with 3 optional sections: `acquisition`, `evaluation`, `presentation`. Old signals keep working. New format adds machine-readable instructions.

**Current best signal** (FIN.ACCT.restatement):
```yaml
threshold:
  type: tiered
  red: '>1 restatements within 3 years'
  yellow: '>0 restatements within 5 years'
  clear: No restatements
data_strategy:
  field_key: restatements
  primary_source: SEC_8K
```

**V2 signal** (additive — old fields stay, new fields are optional):
```yaml
acquisition:
  sources:
    - type: SEC_8K
      sections: [item_4_01, item_4_02]
      fields:
        restatement_count:
          path: financials.earnings_quality.restatements  # dotted path into ExtractedData
          required: true
    - type: SEC_10K
      sections: [item_9a_controls]
      fields:
        material_weakness:
          path: financials.earnings_quality.material_weakness
  fallback:
    - type: WEB_SEARCH
      keywords: ["{company} restatement", "{company} non-reliance"]

evaluation:
  formula: restatement_count  # field reference or expression
  thresholds:
    red: { op: ">", value: 1, window_years: 3, label: "Multiple restatements" }
    yellow: { op: ">", value: 0, window_years: 5, label: "Recent restatement" }
    clear: { op: "==", value: 0, window_years: 5, label: "Clean record" }

presentation:
  facet: financial_health
  subsection: accounting_quality
  format:
    label: "Restatement History"
    value: numeric
    context: "{value} restatement(s) in past {window_years} years"
  detail_levels:
    glance: "{value} restatement(s)"
    standard: "{value} restatement(s) — {level_label}"
    deep: "{value} restatement event(s) in {window_years}-year lookback. {IF material_weakness}Material weakness also disclosed.{/IF}"
```

**Files to change**:
- `brain_signal_schema.py` — Add optional `acquisition`, `evaluation`, `presentation` fields to BrainSignalEntry
- `brain_build_signals.py` — Accept V2 fields during build
- Migrate 10-15 representative signals across categories as proof of concept

**No pipeline code changes yet** — V2 fields are stored but not consumed until Phase 2-3.

---

### Phase 2: Declarative Data Mapping (Brain drives field resolution)

**Goal**: When a signal has `acquisition.sources[].fields[].path`, resolve data by traversing ExtractedData directly. Eliminate manual mapper code per signal.

**How it works**:
```python
# NEW: declarative_mapper.py (~100 lines)
def map_signal_declarative(signal_def, extracted_data):
    """Resolve signal data from dotted paths in acquisition spec."""
    paths = signal_def["acquisition"]["sources"][0]["fields"]
    result = {}
    for field_name, spec in paths.items():
        result[field_name] = resolve_dotted_path(extracted_data, spec["path"])
    return result
```

**In signal_engine.py**, before calling legacy mapper:
```python
if signal_has_declarative_paths(sig):
    data = map_signal_declarative(sig, extracted)
else:
    data = map_signal_data(sig, extracted, company)  # legacy
```

**Migration**: Convert signals one prefix at a time (FIN.LIQ.*, FIN.DEBT.*, etc.). Each migration removes entries from the 329-line `FIELD_FOR_CHECK` dict in signal_field_routing.py.

**Files to change**:
- NEW: `stages/analyze/declarative_mapper.py` (~100 lines)
- `stages/analyze/signal_engine.py` — Add V2 check before legacy mapper
- `stages/analyze/signal_field_routing.py` — Entries shrink as signals migrate

---

### Phase 3: Structured Threshold Evaluation (Brain drives evaluation)

**Goal**: When a signal has `evaluation.thresholds` with structured operators (`op: ">"`, `value: 1.0`), evaluate directly without parsing English text.

**How it works**:
```python
# NEW: structured_evaluator.py (~80 lines)
def evaluate_structured(signal_def, data):
    """Evaluate signal using structured threshold operators."""
    thresholds = signal_def["evaluation"]["thresholds"]
    value = compute_formula(signal_def["evaluation"]["formula"], data)
    for level in ["red", "yellow", "clear"]:
        spec = thresholds[level]
        if compare(value, spec["op"], spec["value"]):
            return level, spec["label"], value
```

**In signal_engine.py**, before calling legacy evaluator:
```python
if signal_has_structured_thresholds(sig):
    result = evaluate_structured(sig, data)
else:
    result = evaluate_signal(sig, data)  # legacy
```

**Files to change**:
- NEW: `stages/analyze/structured_evaluator.py` (~80 lines)
- `stages/analyze/signal_engine.py` — Add V2 check before legacy evaluator

---

### Phase 4: Facet-Driven Rendering (Brain drives output)

**Goal**: Facets control what appears in each document section. Add `subsections` to facets with layout specs. Renderers iterate over facet structure dynamically.

**Enhanced facet YAML**:
```yaml
id: financial_health
name: Financial Health
subsections:
  - id: kpi
    name: Key Financial Metrics
    render_as: kv_table
    signals: [FIN.LIQ.position, FIN.DEBT.coverage, FIN.PROFIT.margin]
    columns: [label, value, assessment, source]

  - id: distress
    name: Distress Indicators
    render_as: scorecard
    signals: [FIN.DIST.altman_z, FIN.DIST.beneish_m, FIN.DIST.piotroski_f, FIN.DIST.ohlson_o]

  - id: forensics
    name: Forensic Analysis
    render_as: narrative_with_table
    composite: COMP.FIN.forensic_analysis
```

**How the renderer changes**:
```python
# In facet_renderer.py
def render_facet_section(facet, signal_results, state):
    for subsection in facet["subsections"]:
        if subsection["render_as"] == "kv_table":
            render_kv_table(subsection, signal_results)
        elif subsection["render_as"] == "scorecard":
            render_scorecard(subsection, signal_results)
        elif subsection["render_as"] == "narrative_with_table":
            render_narrative_composite(subsection, state)
```

**Fallback**: If a facet has no `subsections` field, use the current hardcoded section renderer. Migration is incremental per section.

**Files to change**:
- NEW: `stages/render/facet_renderer.py` (~200 lines)
- `brain/facets/*.yaml` — Add subsections to each facet
- `stages/render/html_renderer.py` — Check for facet-driven rendering before legacy
- `templates/html/sections/*.html.j2` — Add facet-driven template block alongside hardcoded

---

### Phase 5: Simplify Data Stores (Kill the complexity)

**Goal**: Single source of truth. YAML files → read directly at runtime → no DuckDB intermediary for config/signals.

**Changes**:

1. **Read YAML directly at runtime** — Replace `BrainDBLoader.load_signals()` (DuckDB query) with a `YAMLBrainLoader.load_signals()` that reads YAML files directly. Cache parsed YAML in memory for the duration of a pipeline run (the 45 YAML files are small — <1MB total).

2. **Keep DuckDB for run history only** — brain.duckdb keeps `brain_signal_runs`, `brain_effectiveness`, `brain_changelog`, `brain_feedback`. These are analytics/history tables. But signal definitions, scoring factors, patterns, red flags, sectors — all come from YAML.

3. **Merge config directories** — Delete `config/` directory. Move any config not already in `brain/config/` there. One config directory: `brain/config/`. Load via `load_brain_config()` which reads JSON directly (no DuckDB lookup).

4. **Deprecate knowledge.db** — Anything still read from knowledge.db either moves to brain YAML or brain.duckdb analytics tables. No more dual-database confusion.

5. **Kill loaders** — Replace `BrainDBLoader`, `BrainKnowledgeLoader`, `BackwardCompatLoader`, `KnowledgeStore`, `ConfigLoader` with ONE loader: `BrainLoader` that reads YAML + JSON from the brain/ directory.

**Result**:
```
brain/
  signals/**/*.yaml   — 400 signal definitions (read at runtime)
  facets/*.yaml        — 9 facet display specs (read at runtime)
  composites/*.yaml    — 3+ composite definitions (read at runtime)
  framework/*.yaml     — risk model, perils, chains, taxonomy (read at runtime)
  config/*.json        — 22 config keys (read at runtime)
  brain.duckdb         — run history, effectiveness, feedback, changelog ONLY
```

**Files to change**:
- NEW: `brain/brain_yaml_loader.py` (~200 lines) — Replaces BrainDBLoader
- DEPRECATE: `brain/brain_loader.py`, `knowledge/compat_loader.py`, `knowledge/store.py`, `config/loader.py`
- DELETE: `config/` directory (merge into brain/config/)
- `stages/analyze/__init__.py` — Use new BrainLoader
- `brain_build_signals.py` — Simplified (YAML is already the runtime format)

---

### Phase 6: Closed Learning Loop (Brain improves itself)

**Goal**: Every pipeline run makes the brain smarter. Signal effectiveness is tracked, thresholds drift-checked, correlations discovered.

**A. After every run** — `brain_signal_runs` records what fired, what was skipped, what value was observed. Already implemented.

**B. `brain audit` enhancements**:
- Statistical analysis of threshold calibration (is threshold red=1.0 reasonable given observed values?)
- Co-occurrence mining: which signals fire together? Auto-populate `correlated_signals` field
- Fire rate alerts: signals that fire on >80% or <2% of companies get flagged
- Extraction coverage: signals with >50% SKIPPED rate across runs get flagged for extraction improvement

**C. Signal lifecycle state machine**:
```
INCUBATING → ACTIVE → MONITORING → DEPRECATED → ARCHIVED
```
Transitions proposed by `brain audit`, confirmed by underwriter via `feedback process`.

**D. Underwriter feedback integration** (Phase 51 infra already exists):
- Capture: "This signal is wrong / threshold too sensitive / missing context"
- Process: Aggregate reactions into calibration proposals
- Apply: Write threshold changes back to YAML via ruamel.yaml (already implemented)
- Validate: A/B test old vs new threshold on next N runs before committing

**Files to change**:
- `cli_brain_health.py` — Extend audit with statistical analysis
- `brain/brain_writer.py` — Record calibration proposals in brain.duckdb
- Signal YAML — Add `correlated_signals` field (auto-populated by audit)

---

## Implementation Order & Priorities

| Phase | Effort | Impact | Dependencies |
|-------|--------|--------|-------------|
| **5. Simplify Data Stores** | Medium | HIGH — eliminates complexity | None |
| **1. Signal Contract V2** | Small | FOUNDATION — enables phases 2-4 | None |
| **2. Declarative Mapping** | Medium | HIGH — brain drives field resolution | Phase 1 |
| **3. Structured Evaluation** | Small | MEDIUM — brain drives evaluation | Phase 1 |
| **4. Facet-Driven Rendering** | Large | HIGH — brain drives output | Phase 1 |
| **6. Learning Loop** | Medium | HIGH — brain improves over time | Phases 1-3 |

**Recommended order**: Phase 5 first (clean foundation), then Phase 1 (schema), then Phases 2+3 together (pipeline), then Phase 4 (rendering), then Phase 6 (learning).

---

## Verification Plan

After each phase:

1. **Run pipeline on SNA** — Compare output before/after. No regression in data quality.
2. **Check signal evaluation counts** — Same number of TRIGGERED/CLEAR/SKIPPED signals.
3. **Compare HTML output** — Side-by-side visual diff of worksheet.
4. **Run tests** — All 3,967+ tests pass.
5. **Verify brain reads** — Grep for any remaining DuckDB signal reads (Phase 5), any remaining FIELD_FOR_CHECK entries (Phase 2), any remaining hardcoded section renderers (Phase 4).

---

## What This Achieves

**Before**: Brain is 60% self-contained. Acquisition hardcoded. Rendering hardcoded. 5 data stores. Manual DuckDB sync.

**After**: Brain YAML signals are complete contracts that drive acquisition, evaluation, and rendering. One data store (YAML + JSON for definitions, DuckDB for history only). One loader. Facets control the output. Every run makes the brain smarter.

A human can read any signal YAML and understand: why we check this, where we get the data, how we evaluate it, and how we display it. All in one file.
