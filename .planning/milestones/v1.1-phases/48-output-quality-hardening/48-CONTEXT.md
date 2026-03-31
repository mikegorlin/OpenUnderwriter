# Phase 48: Output Quality Hardening - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Introduce the **Signal + Section** architectural foundation for brain-driven rendering, and deliver the three QA output quality fixes as the first expression of that architecture.

**Architectural scope (new):**
- Brain `checks/**/*.yaml` files are formally named **Signals** — self-contained, atomic knowledge units
- Extend the Signal YAML schema with a `display:` block: `value_format`, `source_type`, `threshold_context`, `deprecation_note`
- Introduce `brain/facets/*.yaml` — **Facets** are composed display units that declare which Signals they aggregate and how to render them together
- Rewrite the rendering layer to be brain-driven: formatters and templates read Facet schemas and Signal display specs instead of hard-coding grouping and format logic

**Output quality fixes (must ship as part of this architecture):**
1. QA audit table source column — filing type + date (e.g., `10-K 2024-09-28`) or `WEB (domain...)` — no more `—`
2. QA audit table value column — `result.value` populated by all evaluator types, `True`/`False` for booleans
3. Red flags section — threshold criterion rendered as muted secondary line below each TRIGGERED finding

**Out of scope:** New checks, new data sources, new report sections, full UI redesign.

</domain>

<decisions>
## Implementation Decisions

### Source column format
- Filing sources: "filing type + date" format — e.g., `10-K 2024-09-28` — plain text, no hyperlinks
- Web sources: "WEB + truncated URL" format — e.g., `WEB (reuters.com/...)` — shows domain for traceability
- SKIPPED rows: leave as "—" (dash) — don't disguise missing data; goal is to reduce SKIPPED, not relabel it
- Always plain text — no hyperlinks in the source cell regardless of URL availability

### Value column content
- Numeric checks: raw number, 2 decimal places — e.g., `1.23` for ratios, `12.50` for percentages; units implied by check name
- Boolean/qualitative checks: `True` / `False` — unambiguous, consistent
- Show value even for PASSED checks — reviewers need to verify thresholds weren't just barely missed
- Fix at the evaluator layer — each threshold evaluator type sets `result.value` before returning; not a QA-table-level workaround

### Threshold criterion display
- Position: below the finding description as a secondary line
- Style: smaller, muted text — visually secondary, not invisible
- Scope: TRIGGERED findings in the red flags HTML section only — not in the QA audit table
- Backfill required: most checks do not yet have `threshold_context` in brain YAML — this phase must write it for all relevant checks

### SKIPPED reduction strategy
- Root cause is unknown — researcher must audit the actual SKIPPED checks on AAPL to categorize (data path gaps vs. brain YAML config gaps vs. legitimately unanswerable)
- Goal: maximize reduction — fix everything that has a fix available, no minimum floor
- Fixes must be general (pipeline-level), not AAPL-specific — improvements apply to all tickers
- Legitimately unanswerable checks stay SKIPPED — never force-pass a check with no data
- Permanently unanswerable checks (e.g., checks that require data the company type can never provide): flag for deprecation review — add a `deprecation_note` field (or equivalent) to brain YAML and surface the flag in output so future reviews can act on it

### Architecture — Signal + Facet schema
- Brain YAML files in `checks/**/*.yaml` are now formally called **Signals** — self-contained, atomic knowledge units
- Each Signal YAML gets a `display:` block — at minimum: `value_format`, `source_type`, `threshold_context`, `deprecation_note`
- New `brain/facets/*.yaml` files — **Facets** are composed display units that declare which Signals they aggregate and how to render them together (e.g., "Governance Facet" = 12 Signals → table view; "Red Flags Facet" = all TRIGGERED Signals → flag list)
- Rendering layer (formatters + templates) reads Signal display specs and Facet schemas — no more hard-coded grouping or format logic
- The three QA fixes (source date, bool coercion, threshold_context) are implemented *through* the new Signal/Facet schema, not as standalone patches

### Claude's Discretion
- Exact field names in the Signal `display:` block (beyond `threshold_context` and `deprecation_note` which are locked)
- Section schema structure (YAML format, required fields, inheritance rules)
- Phasing: whether all Signals get `display:` backfilled this phase, or just those touched by the three fixes
- Exact format for truncating web URLs in the source column (character limit, ellipsis style)

</decisions>

<specifics>
## Specific Ideas

- The deprecation flag on unanswerable checks should be visible in output — not just internal metadata. The idea: over time, unanswerable checks should be deprecated or reformulated (e.g., convert "does X exist" to "is X disclosed" — a disclosure check can always be answered)
- The researcher should run AAPL through the current pipeline and inspect the actual SKIPPED list to understand root causes before planning fix strategies

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 48-output-quality-hardening*
*Context gathered: 2026-02-25*
