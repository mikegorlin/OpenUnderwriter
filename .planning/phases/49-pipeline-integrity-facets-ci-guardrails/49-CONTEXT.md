# Phase 49: Pipeline Integrity, Facets & CI Guardrails - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the brain fully self-describing: every signal declares its data needs, display format, and facet membership. Add traceable data routes, verified rendering completeness, and CI tests that enforce the contract. Rename "check" to "signal" throughout.

</domain>

<decisions>
## Implementation Decisions

### Trace Command Output
- `brain trace <SIGNAL_ID>` shows the **full pipeline journey**: YAML definition → extraction source → mapping → evaluation result → rendered output location
- Step-by-step vertical flow format with clear stage markers (e.g., ✅ YAML → ✅ Extract → ❌ Evaluate (SKIPPED))
- Show **actual data values + status** at each stage — extracted values, thresholds, scores alongside pass/fail/skip
- **Two modes**: default shows results from last completed analysis run; `--blueprint` flag shows the theoretical route from YAML without needing a run
- Errors if no run exists and --blueprint not specified

### Facet Organization
- **Signals own their display spec** — each signal YAML defines data, acquisition strategy, processing, evaluation, AND how that signal renders in output
- **A grouping/section level exists above signals** that defines what needs to be in a rendered section from a display standpoint: non-signal display elements (charts, tables, narrative), ordering, layout requirements
- Some grouping-level components wrap a single signal, some combine multiple data points with enrichment (e.g., stock drops table needs price data + event attribution + industry comparison), some are purely display (charts)
- **Facets are a metadata layer for now** — keep existing rendering sections, add facet as parallel classification. Renderer can optionally use facets. Full migration happens in a future phase.
- **Claude proposes the exact organizational model** during research/planning — hierarchy, naming, and boundaries between concepts must be defined with precise, non-overlapping nomenclature (no confusion between "facet," "section," "group," etc.)

### Skipped Signal Triage
- **Fix all DEF14A Population B signals** that have a viable extraction path
- Signals with no reliable extraction path → mark as **INACTIVE** in YAML (explicitly off, doesn't count as SKIPPED)
- **Hard CI gate** on maximum SKIPPED count — CI fails if SKIPPED exceeds threshold (target: ~34, down from ~68)
- New evaluations go **live immediately** — once a signal evaluates, it appears in the next run's output with no staging gate

### Rename Migration (check → signal)
- **Total rename** — Python classes, function names, CLI commands, YAML field names, file/directory names, config keys, log messages, test names
- `brain/checks/` directory renames to `brain/signals/`
- **Big bang single commit** — one atomic commit, clean break, no backward-compatible aliases
- **CI lint guard** — a CI test greps for "check" in signal-related contexts and fails if found, preventing drift back to old terminology

### Claude's Discretion
- Exact organizational model/hierarchy for facet system (proposed during research, with clear naming)
- CI lint implementation approach (avoiding false positives on generic "check" usage)
- Trace command formatting details (colors, indentation, truncation)
- Order of operations (rename first vs facets first vs parallel)

</decisions>

<specifics>
## Specific Ideas

- Stock Performance example as test case for facet model: stock charts (1yr/5yr), significant drops table with event attribution, short interest evaluation, insider activity, analysis narrative — shows range from display-only to enriched multi-data components
- User envisions facets as rich section definitions that describe display requirements beyond just signal grouping — "for the stock facet, I want a one-year stock chart, five-year chart, comparison to industry, all 5%+ drops with event context, insider position, short interest, and an analysis paragraph"
- Trace command should feel like following a single signal's complete story through the system

</specifics>

<deferred>
## Deferred Ideas

- Full renderer migration to facet-driven layout (this phase adds facets as metadata; future phase makes them the primary organizer)
- Non-DEF14A skipped signal remediation
- Facet-level narrative generation (AI-written analysis paragraphs per section)

</deferred>

---

*Phase: 49-pipeline-integrity-facets-ci-guardrails*
*Context gathered: 2026-02-26*
