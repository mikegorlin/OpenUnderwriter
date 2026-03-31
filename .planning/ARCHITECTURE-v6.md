# v6.0 Architectural Constraint: Brain-First Portability

## Principle (NON-NEGOTIABLE)

The brain and rendering layer must be **portable to another system**. That means:

1. **Everything starts in the brain YAML** — a signal definition IS the specification
2. **The manifest IS the contract** between brain and rendering
3. **Renderers are dumb consumers** — they read signal results and display them, zero business logic
4. **Any system that reads our YAML signals + manifest can produce the same worksheet**

## Signal-First Data Flow

```
Brain Signal YAML (declaration)
  → Acquisition (what data to pull, from where)
  → Extraction (how to parse it into structured fields)
  → Evaluation (thresholds: red/amber/green, when to fire)
  → Presentation (facet, display format, callout text)
  → Manifest (where in the worksheet it appears)
  → Renderer (reads manifest + signal results → HTML/Word/PDF)
```

NO data enters the worksheet that isn't declared as a brain signal first.

## What "Portable" Means Concretely

If you took `brain/signals/*.yaml` + `brain/output_manifest.yaml` + signal evaluation results (JSON), a completely separate rendering system should be able to produce an equivalent worksheet. This means:

### Brain YAML signals must be self-contained:
- `acquisition.source`: where the data comes from (XBRL concept, 10-K section, web search, etc.)
- `acquisition.field_key`: what field in state holds the raw data
- `evaluation.thresholds`: red/amber/green conditions with human-readable criteria
- `evaluation.method`: AUTO (numeric compare), LLM (qualitative), COMPOSITE (aggregation)
- `presentation.facet`: which facet group this belongs to
- `presentation.display_format`: kv_pair, data_table, metric_card, narrative, timeline, etc.
- `presentation.callout_template`: what to say when the signal fires

### Output manifest must be the ONLY layout specification:
- Section ordering
- Group ordering within sections
- Which signals appear in which groups
- Display position (main vs sidebar vs collapsed)

### Renderers must NEVER:
- Contain threshold values (those live in signal YAML)
- Contain evaluation logic (that's the check engine's job)
- Hardcode which signals to display (manifest decides)
- Compute derived values (signals or extraction do that)
- Have conditional logic based on data content (signal evaluation handles that)

## Centralization Rules for v6.0

1. **New dimension → new signal YAML file(s)** in `brain/signals/`
2. **Signal declares everything** — acquisition source, evaluation thresholds, presentation format
3. **Manifest updated** with new groups/facets for the dimension
4. **Context builder reads signal results** from state, formats for template
5. **Template renders what manifest says** using standard macros (kv_table, data_table, metric_card)
6. **No dimension-specific rendering code** — use existing generic rendering patterns

## v6.0 Signal Inventory (target)

| Category | Signal Prefix | Approximate Count | Source |
|----------|--------------|-------------------|--------|
| Business Model | BIZ.MODEL.* | 6+ | 10-K Item 1, XBRL |
| Operational | BIZ.OPS.* | 5+ | Exhibit 21, 10-K, XBRL |
| Corporate Events | BIZ.EVENT.* | 5+ | 10-K, S-1/S-3, 8-K |
| Structural | BIZ.STRUC.* | 5+ | 10-K notes, CORRESP |
| Environment | ENVR.* | 5+ | 10-K Item 1A, web search |
| Sector | SECT.* | 4+ | SCAC data, config reference |

All ~30+ new signals follow identical schema to existing 400+ signals. Same loader, same evaluator, same renderer.
