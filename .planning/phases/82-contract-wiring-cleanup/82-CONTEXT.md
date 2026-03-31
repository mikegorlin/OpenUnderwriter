# Phase 82: Signal Schema v3 - Context

**Gathered:** 2026-03-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Extend every brain signal YAML to be self-contained — adding `group`, `depends_on`, `field_path`, and `signal_class` fields — with backward-compatible loading and migration tooling that populates all 476 signals from existing sources. Existing `type` and `facet` fields are removed and replaced by their v3 equivalents. Output is identical before and after migration.

</domain>

<decisions>
## Implementation Decisions

### V3 Field Semantics
- **Two-level grouping**: `group` is fine-grained (matches manifest group objects, e.g. `distress_indicators`, `key_metrics`). `facet` (coarse section-level, e.g. `financial_health`) is being REMOVED — replaced by the section association derivable from manifest group membership
- **`field_path` hybrid resolution**: Can be either a direct dotted path (`extracted.financials.liquidity`) OR a registry key (`current_ratio`). Resolver tries direct path first, falls back to field_registry.yaml. Gradually absorb registry entries into direct paths over time
- **`signal_class` three-tier**: `foundational | evaluative | inference`. Maps execution order, not rendering intent. Display-only signals are still `evaluative` with display intent captured in presentation spec
- **`depends_on` with signal + field**: Each dependency declares both the signal ID and the specific field needed: `[{signal: BASE.XBRL.balance_sheet, field: total_assets}]`. Enables precise validation and graph construction. Foundational signals have empty depends_on

### Migration Strategy
- **`group` auto-populated** from existing `facet` field + section YAML mapping. Ambiguous assignments flagged for manual review
- **`depends_on` auto-populated** for evaluative signals by tracing `data_strategy.field_key` through field_registry.yaml to find producing foundational signal. Inference signals (COMP.*, FORENSIC.*) populated manually since they reference other evaluative signals
- **`field_path` population**: Claude's discretion — minimize risk while making progress toward inline paths
- **`signal_class` inferred** from existing `type` field: `foundational` stays, `evaluate` becomes `evaluative`, COMP.*/FORENSIC.* patterns become `inference`
- **In-place YAML modification with git safety**: Commit pre-migration state, then modify YAML files in-place using ruamel.yaml to preserve comments/formatting. Git revert if migration is wrong

### Backward Compatibility
- **Clean break on `type` and `facet`**: Remove old fields in this phase, replace with `signal_class` and `group`. All consumers updated as part of migration
- **V3 fields have backward-compatible defaults** so any un-migrated signal still loads: `group: ''`, `depends_on: []`, `field_path: ''`, `signal_class: 'evaluative'` (default inferred from `type` if present)
- **BrainLoader warns on missing v3 fields in Phase 82**, enforcement deferred to Phase 84 (manifest/section elimination)
- **CI contract test (test_brain_contract.py)**: Structural + cross-reference validation — every `group` must exist in manifest, every `depends_on` signal ID must exist, every `field_path` must resolve

### Audit Trail (SCHEMA-08)
- **Expanded `provenance` block**: Merge all audit metadata into single block — origin fields + `formula` (evaluation logic), `threshold_provenance` (source + rationale), `render_target` (output location), `data_source` (where input data comes from)
- **Threshold provenance requires source + rationale**: E.g., "NERA 2024: 3.8% annual filing rate — most comprehensive multi-year study". Aligns with brain-changes-driven-by-evidence principle
- **Auto-categorize unknown thresholds**: Migration categorizes into `calibrated` (from learning loop), `standard` (common industry thresholds), `unattributed` (legacy, needs attribution). Not blocked on full attribution
- **`brain audit` produces HTML report**: Institutional-quality HTML showing all signals with provenance, grouped by section. Filterable, searchable. Beautiful and clear presentation

### Claude's Discretion
- `field_path` population strategy (registry key vs resolved direct path) — pick approach that minimizes risk
- V3 field default computation logic (whether to auto-infer `signal_class` from `type` during loading)
- Exact ruamel.yaml formatting/comment preservation approach
- HTML audit report template design

</decisions>

<specifics>
## Specific Ideas

- Audit trail presentation must be "very clear and visually beautiful" — match the institutional quality of the worksheet output
- Brain-changes-driven-by-evidence principle: every threshold attribution should explain WHY that value, not just WHERE it came from
- `depends_on` precision: signal + field tuple enables future dependency graph visualization (Phase 83) to show exactly what data flows where

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BrainSignalEntry` (brain_signal_schema.py:234): Already has `extra: "allow"`, V2 fields (`acquisition`, `evaluation`, `presentation`), `schema_version`. Adding v3 fields follows same additive pattern
- `field_registry.yaml`: 100+ field definitions mapping logical names to data paths. Can be queried during migration to populate `field_path` and trace dependencies
- `BrainLoader` (brain_loader.py): 482 lines, handles YAML loading. Must be extended to validate v3 fields and warn on missing
- `test_brain_contract.py`: Existing CI contract test. Extend with v3 field validation assertions
- `brain_migrate.py` + `brain_migrate_scoring.py`: Existing migration tooling patterns. New migration script follows same conventions

### Established Patterns
- **`extra: "allow"` on Pydantic models**: BrainSignalEntry accepts unknown fields — ensures forward compatibility
- **V2 Signal Contract additive pattern** (Phase 54): All V2 fields optional with defaults so 400 signals loaded unchanged. V3 follows same pattern initially, then removes old fields
- **ruamel.yaml for round-trip YAML**: Used in brain feedback system for signal YAML write-back with comment preservation
- **Migration scripts commit before modifying**: Established in prior brain migrations

### Integration Points
- **Output manifest** (v4.0): Defines group objects that `group` field values must reference
- **Section YAML** (brain/sections/*.yaml): Source of facet-to-section mapping for migration. Will be deleted in Phase 84
- **check_field_routing.py**: Consumes `data_strategy.field_key` — may need update if `field_path` replaces it
- **signal_engine/check_engine**: Currently uses `type` field — must update to `signal_class`
- **All renderers**: Currently use `facet` field for signal grouping — must update to `group`

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 82-contract-wiring-cleanup*
*Context gathered: 2026-03-07*
