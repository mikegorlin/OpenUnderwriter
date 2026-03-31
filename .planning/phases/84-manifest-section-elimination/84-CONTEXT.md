---
phase: 84
name: Manifest & Section Elimination
created: 2026-03-08
source: auto-approved (user away, --auto mode)
---

# Phase 84 Context: Manifest & Section Elimination

## Phase Goal

The manifest uses group objects (not facets-with-signal-lists) where signals self-select via their group field, all 5 section YAML consumers are migrated to read from manifest and signal data, and all 12 brain/sections/*.yaml files are deleted with zero rendering regression.

## Requirements

- MANIF-01: 5-field group objects (id, name, template, render_as, requires) replace facets with signal lists
- MANIF-02: Signals self-select into manifest groups via `group` field
- MANIF-03: HTML renderer consumes manifest group ordering + signal self-selection
- MANIF-04: Word renderer consumes manifest group ordering + signal self-selection
- MANIF-05: PDF renderer correct from manifest-driven HTML
- SECT-01: section_renderer.py migrated from section YAML to manifest + signal data
- SECT-02: html_signals.py migrated from section YAML to manifest + signal data
- SECT-03: cli_brain_trace.py migrated from section YAML to manifest + signal data
- SECT-04: brain_audit.py and brain_health.py migrated from section YAML to manifest + signal data
- SECT-05: All 12 brain/sections/*.yaml files deleted with zero rendering regression

## Decisions

### 1. Migration Strategy: Expand-and-contract (not big-bang)

**Decision:** Add manifest group support alongside section YAML first, verify output parity, then cut over consumers one at a time, then delete section YAML files last.

**Rationale:** STATE.md explicitly states "expand-and-contract migration — never big-bang all 476 signals." This is the highest-risk phase in v5.0 (noted in blockers). Each consumer migration is independently testable.

**Constraint:** Zero rendering regression — output must be visually identical before and after.

### 2. Manifest Group Object Design

**Decision:** Add `ManifestGroup` to manifest_schema.py with 5 fields: `id`, `name`, `template`, `render_as`, `requires`. Manifest sections reference groups (ordered list of group IDs). Signals self-select by declaring `group: "<group_id>"` in their YAML.

**Rationale:** This matches MANIF-01 spec exactly. Group IDs match the existing facet IDs in output_manifest.yaml for smooth migration. No signal lists in the manifest — group membership is derived at runtime from signal.group field.

### 3. Consumer Migration Order

**Decision:** Migrate consumers in risk order (lowest risk first):
1. brain_health.py (simplest — just iterates signal IDs for coverage)
2. brain_audit.py (similar to health — orphan detection)
3. cli_brain_trace.py (group name lookup — simple map)
4. html_signals.py (signal-to-section mapping for QA table)
5. section_renderer.py (highest risk — drives actual facet rendering)

**Rationale:** Each consumer can be migrated and tested independently. Start with validation tools (health, audit) which are easiest to verify, end with the renderer which produces user-visible output.

### 4. Output Parity Verification

**Decision:** Before deleting section YAML, run the pipeline on RPM and V, compare HTML/Word/PDF output byte-for-byte (or visual regression). Only proceed with deletion if output is identical.

**Rationale:** MANIF-05 requires zero visual regression. Running both tickers covers different sector/industry combinations. Visual regression tests already exist in the test suite.

### 5. Section YAML Deletion: Clean delete after all consumers pass

**Decision:** Delete all 12 brain/sections/*.yaml files and brain_section_schema.py in a single commit after verifying all 5 consumers work without them. Remove the sections/ directory entirely.

**Rationale:** Once no code references section YAML, they're dead weight. Clean delete, not gradual deprecation.

## Code Context

### Reusable Assets
- `manifest_schema.py:186 lines` — ManifestFacet, ManifestSection, OutputManifest models; extend with ManifestGroup
- `output_manifest.yaml:1,226 lines` — Already facet-based with 12 sections; evolve to group-based
- `brain_signal_schema.py:363-365` — `group` field already on BrainSignalEntry (populated on all 476 signals in Phase 82)
- `brain_unified_loader.py` — load_signals() returns all signals with group field

### 5 Consumers to Migrate
1. `stages/render/section_renderer.py:110 lines` — build_section_context() reads load_all_sections()
2. `stages/render/html_signals.py:200+ lines` — _get_sections(), _build_signal_section_map(), _group_signals_by_section()
3. `cli_brain_trace.py:700+ lines` — _get_trace_sections() lookup
4. `brain/brain_audit.py:300+ lines` — orphan detection via facet iteration
5. `brain/brain_health.py:200+ lines` — coverage computation via section.signals

### Files to Delete
- 12 files in `brain/sections/`: ai_risk, business_profile, executive_risk, executive_summary, filing_analysis, financial_health, forward_looking, governance, litigation, market_activity, red_flags, scoring
- `brain/brain_section_schema.py:182 lines` — SectionSpec, FacetSpec, load_all_sections()

### Integration Points
- section_renderer.py → called from html_renderer.py and word_renderer.py during render stage
- html_signals.py → called from html_renderer.py for QA audit table
- All consumers import `load_all_sections` from brain_section_schema.py

## Deferred Ideas

- Sector manifest overlays (MANIF-06) — Phase 86-87 scope
- Dynamic group creation at runtime — explicitly out of scope (REQUIREMENTS.md)

## Prior Phase Context

Phase 82: All 476 signals have `group` field populated (135 explicit + 341 prefix-inferred).
Phase 83: Dependency graph and visualization complete — signals execute in tier order.
STATE.md blocker: "Phase 84 (Section Elimination) is highest-risk: 5 consumers across 4 modules"
