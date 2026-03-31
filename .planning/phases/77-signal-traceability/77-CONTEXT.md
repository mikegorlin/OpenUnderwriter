# Phase 77: Signal Traceability - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a CLI audit tool (`brain trace-chain`) and automated validation library that traces every active signal's data chain end-to-end: acquisition source → extraction field → analysis evaluation → rendering facet → output manifest. Gaps are surfaced with granular categorization. No fixing of broken chains — that's Phase 80.

</domain>

<decisions>
## Implementation Decisions

### Chain definition
- Full 4-link chain required for ACTIVE evaluative signals: ACQUIRE (acquisition spec or Tier 1 manifest) → EXTRACT (data_strategy.field_key or field routing) → ANALYZE (evaluation/threshold) → RENDER (facet assignment in section YAML + facet present in output manifest)
- Output manifest is the final render authority — a signal assigned to a facet NOT in the manifest is chain-incomplete
- Foundational (BASE.*) signals get a modified chain: acquire → extract only. Analyze + render links are N/A. Reported as "chain-complete (foundational)" with distinct status
- Validation is purely declarative/static — checks that YAML declarations connect. Whether data actually flows at runtime is Phase 78's disposition tagging concern

### CLI output format
- Single command: `do-uw brain trace-chain`
- No args = full table of ALL signals (400+) with chain status per signal
- With signal ID arg = vertical chain detail view showing each link with checkmark/X status, source details, field keys, facet/manifest references
- `--json` flag writes structured JSON report to file for Phase 79 CI consumption
- Rich tables and panels following existing brain CLI patterns

### Gap categorization
- 6 granular gap types matching specific pipeline locations:
  1. `NO_ACQUISITION` — no acquisition spec or Tier 1 manifest entry
  2. `MISSING_FIELD_KEY` — no data_strategy.field_key declared
  3. `NO_FIELD_ROUTING` — field_key exists but no check_field_routing entry
  4. `NO_EVALUATION` — no threshold or evaluation spec
  5. `NO_FACET` — not assigned to any facet in section YAML
  6. `FACET_NOT_IN_MANIFEST` — assigned to facet but facet not in output manifest
- Show ALL gaps per signal (a signal can have multiple gap types simultaneously)
- Primary grouping by gap type with signal count per type
- INACTIVE signals listed in a separate section with reason; not counted in chain stats

### Report structure
- This phase reports only — no fixing of broken chains (Phase 80)
- Summary stats at top: total signals, chain-complete count, chain-broken count by gap type
- Full table: every signal with its chain status and gap types
- INACTIVE signals section at bottom

### Claude's Discretion
- Exact Rich table column layout and styling
- How to infer acquisition link for signals without explicit acquisition spec (e.g., check if field_key maps to a known Tier 1 manifest entry)
- Internal data model for chain validation results

</decisions>

<specifics>
## Specific Ideas

- Gap types are intentionally granular (6 types, not 4) because Phase 80 remediation needs to know exactly WHERE in the pipeline each fix goes
- JSON export is specifically for Phase 79 CI test consumption — design the schema with that downstream use in mind
- The vertical chain detail view for single-signal lookup should make debugging easy — show the actual values (which acquisition source, which field_key, which facet, which manifest section)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `brain_audit.py` (490 lines): Structural audit (staleness, peril coverage, thresholds, orphans) — pattern to follow but separate module
- `brain_unified_loader.py`: `load_signals()` returns all signal YAML data; `load_perils()` for peril data
- `brain_section_schema.py`: `load_all_sections()` returns SectionSpec with facet→signal mappings
- `manifest_schema.py`: `load_manifest()` returns OutputManifest with section→facet→signals chain
- `brain_signal_schema.py`: BrainSignalEntry has `acquisition` (AcquisitionSpec), `data_strategy`, `acquisition_tier` fields
- `check_field_routing.py` (329 lines): Field routing tables mapping field_keys to check evaluation
- `cli_brain.py` + `cli_brain_health.py`: Existing brain CLI commands with Rich formatting patterns

### Established Patterns
- Brain CLI commands registered as Typer sub-app via `brain_app`
- `compute_*()` function returns Pydantic report model; CLI command formats it with Rich
- Signal definitions always from YAML via `load_signals()`, never DuckDB

### Integration Points
- New `brain_chain_validator.py` module in `src/do_uw/brain/`
- New `cli_brain_trace.py` registered in `cli_brain.py` (same pattern as `cli_brain_health.py`)
- Reads: signal YAML, section YAML, output_manifest.yaml, check_field_routing tables
- Outputs: Rich terminal display + optional JSON file

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 77-signal-traceability*
*Context gathered: 2026-03-07*
