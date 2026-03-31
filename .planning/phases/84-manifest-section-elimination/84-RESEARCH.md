# Phase 84: Manifest & Section Elimination - Research

**Researched:** 2026-03-08
**Domain:** Brain architecture migration -- manifest group objects, section YAML elimination
**Confidence:** HIGH

## Summary

Phase 84 replaces the dual manifest+section-YAML architecture with a single manifest-driven system where signals self-select into groups via their `group` field. The current system has two overlapping data sources: `brain/sections/*.yaml` (12 files with signal lists and facet definitions) and `brain/output_manifest.yaml` (1,226 lines with facet-based sections). Both declare which signals belong where, creating redundancy.

Phase 82 already populated `group` fields on all 476 signals (135 explicit + 341 prefix-inferred), mapping to 54 distinct group IDs. These group IDs already match manifest facet IDs perfectly -- all 54 signal group values exist as facet IDs in the manifest. 43 manifest facets have no signals (infrastructure facets: density alerts, checks, charts, etc.).

**Primary recommendation:** Evolve the manifest to use group objects instead of facets-with-signal-lists, build a runtime function that collects signals per group from YAML `group` fields, migrate each consumer to use manifest + signal data, then delete section YAML files.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
1. **Migration Strategy: Expand-and-contract (not big-bang)** -- Add manifest group support alongside section YAML first, verify output parity, then cut over consumers one at a time, then delete section YAML files last.
2. **Manifest Group Object Design** -- ManifestGroup with 5 fields: `id`, `name`, `template`, `render_as`, `requires`. Signals self-select by declaring `group: "<group_id>"` in their YAML.
3. **Consumer Migration Order** -- brain_health.py (simplest), brain_audit.py, cli_brain_trace.py, html_signals.py, section_renderer.py (highest risk).
4. **Output Parity Verification** -- Before deleting section YAML, run pipeline on RPM and V, compare output. Only proceed with deletion if output is identical.
5. **Section YAML Deletion: Clean delete** -- Delete all 12 brain/sections/*.yaml files and brain_section_schema.py in a single commit after verifying all 5 consumers work without them.

### Claude's Discretion
None specified -- all decisions locked.

### Deferred Ideas (OUT OF SCOPE)
- Sector manifest overlays (MANIF-06) -- Phase 86-87 scope
- Dynamic group creation at runtime -- explicitly out of scope (REQUIREMENTS.md)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| MANIF-01 | Manifest uses 5-field group objects (id, name, template, render_as, requires) instead of facets with signal lists | ManifestGroup model added to manifest_schema.py; manifest YAML restructured from facets to groups |
| MANIF-02 | Signals self-select into manifest groups via `group` field matching manifest group IDs | Runtime function collects signals by group from BrainLoader; 54 group IDs already match facet IDs |
| MANIF-03 | HTML renderer consumes manifest group ordering and signal self-selection | section_renderer.py migrated to read from manifest groups + signal.group lookup |
| MANIF-04 | Word renderer consumes manifest group ordering and signal self-selection | Word renderer already uses manifest for ordering; no brain_section_schema dependency to remove |
| MANIF-05 | PDF renderer produces correct output from manifest-driven HTML (no visual regression) | PDF is generated from HTML; HTML correctness implies PDF correctness |
| SECT-01 | section_renderer.py migrated from section YAML to manifest + signal data | Replace load_all_sections() with manifest groups + signal self-selection |
| SECT-02 | html_signals.py migrated from section YAML to manifest + signal data | Replace _get_sections() with manifest-based signal-to-group mapping |
| SECT-03 | cli_brain_trace.py migrated from section YAML to manifest + signal data | 3 usage sites (lines 29-31, 454-461, 513-529) need migration |
| SECT-04 | brain_audit.py and brain_health.py migrated from section YAML to manifest + signal data | brain_audit.py already uses manifest for orphan detection; brain_health.py uses section.signals for coverage |
| SECT-05 | All 12 brain/sections/*.yaml files deleted with zero rendering regression | 12 YAML files + brain_section_schema.py (182 lines) deleted |
</phase_requirements>

## Architecture Patterns

### Current Architecture (Before Migration)

```
brain/sections/*.yaml (12 files)     brain/output_manifest.yaml
  ├── SectionSpec.signals: [list]       ├── ManifestSection.facets: [list]
  ├── SectionSpec.facets: [FacetSpec]   │   ├── ManifestFacet.signals: [list]
  └── SectionSpec.display_type          │   ├── ManifestFacet.render_as
                                        │   └── ManifestFacet.template
                                        └── ManifestSection.template

5 consumers read from section YAML:
  1. section_renderer.py → section.facets (facet metadata for HTML dispatch)
  2. html_signals.py → section.signals (signal-to-section grouping for QA table)
  3. cli_brain_trace.py → sections[group_id].name (group name lookup)
  4. brain_audit.py → section.signals via import (import only, doesn't use)
  5. brain_health.py → section.signals (facet coverage computation)
```

### Target Architecture (After Migration)

```
brain/output_manifest.yaml (evolved)
  ├── ManifestSection
  │   └── groups: [ManifestGroup]      ← NEW: replaces facets
  │       ├── id, name, template, render_as, requires
  │       └── NO signal lists — signals self-select

brain/signals/**/*.yaml (unchanged)
  └── each signal has group: "<group_id>"  ← matches ManifestGroup.id

Runtime resolution:
  load_signals() → group all by signal.group → marry with manifest group ordering
```

### Key Data Flow for Signal-to-Group Resolution

```python
# Runtime: collect signals per group
def get_signals_by_group(signals: list[dict]) -> dict[str, list[dict]]:
    """Group loaded signals by their 'group' field."""
    groups: dict[str, list[dict]] = {}
    for sig in signals:
        gid = sig.get("group", "")
        if gid:
            groups.setdefault(gid, []).append(sig)
    return groups
```

This replaces the section YAML `signals:` lists. The manifest provides ordering; signals provide membership.

### Consumer Migration Details

#### 1. brain_health.py (SIMPLEST)
**Current:** Loads `load_all_sections()`, iterates `section.signals` to compute facet coverage.
**Migration:** Use signal `group` field directly. A signal is "in a group" if its `group` field is non-empty AND matches a manifest group ID. Coverage = signals with valid group / total active.
**Risk:** LOW -- pure metric computation.

#### 2. brain_audit.py (LOW RISK)
**Current:** `_check_orphaned_signals()` already uses manifest facets (not section YAML) for orphan detection. The top-level import of `load_all_sections` on line 22 is UNUSED in any function.
**Migration:** Remove unused import. Orphan detection already works via manifest. Update orphan logic to use signal `group` field: orphan = signal with empty/unknown group.
**Risk:** LOW -- already mostly migrated.

#### 3. cli_brain_trace.py (MEDIUM RISK)
**Current:** 3 usage sites:
- `_get_trace_sections()` (line 25-32): lazy-loads all sections for group name lookup
- `brain_trace_chain()` (line 454-461): looks up `sections[group_id].name` for group name display
- `brain_render_audit()` (line 513-529): loads sections for per-section declared vs rendered audit
**Migration:**
- Group name lookup: use manifest section/group metadata instead. Build `{group_id: group_name}` from manifest groups.
- Render audit: iterate manifest groups instead of section facets.
**Risk:** MEDIUM -- 3 separate code paths to update.

#### 4. html_signals.py (MEDIUM-HIGH RISK)
**Current:**
- `_get_sections()`: lazy-loads section YAML
- `_build_signal_section_map()`: maps signal IDs to section prefixes via section.signals lists
- `_lookup_facet_metadata()`: finds section_id/section_name for a signal
- `_group_signals_by_section()`: groups signal results by prefix for QA audit table
- `_compute_coverage_stats()`: per-section coverage stats
**Migration:** Replace section-based prefix mapping with signal `group` field + manifest group metadata. Signal `group` field IS the group ID. Map group IDs to section IDs via manifest hierarchy.
**Risk:** MEDIUM-HIGH -- 5 functions need updating, QA audit table display depends on correct grouping.

#### 5. section_renderer.py (HIGHEST RISK)
**Current:** `build_section_context()` does TWO things:
1. Loads section YAML → builds `section_context` dict (facet data per section)
2. Loads manifest → builds `manifest_sections` list (already manifest-driven)
**Migration:** Eliminate step 1. The `manifest_sections` output already provides all facet/group data needed for HTML templates. The `section_context` dict provided redundant data.
**Key risk:** HTML templates may reference `section_context` keys. Must verify all template references.
**Risk:** HIGH -- drives user-visible rendering output.

### Anti-Patterns to Avoid

- **Do NOT remove `ManifestFacet` entirely in this phase.** The manifest currently has 97 facets. The new ManifestGroup is a simplified replacement, but the migration must be clean. Rename or evolve, not fork.
- **Do NOT change the manifest section hierarchy.** Sections (identity, executive_summary, business_profile, etc.) remain as is. Only facets within sections become groups.
- **Do NOT reorder signals within groups.** The current ordering comes from section YAML `signals:` lists. After migration, ordering comes from signal load order (filesystem sort). Verify this doesn't cause visible differences.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Signal-to-group mapping | Custom section-parsing logic | `signal.group` field (already populated on all 476) | Phase 82 already solved this |
| Group metadata (name, template, render_as) | New metadata source | ManifestGroup objects in manifest YAML | Single source of truth |
| Section ordering | Custom ordering logic | Manifest section + group ordering (already exists) | Manifest already drives order |

## Common Pitfalls

### Pitfall 1: Stale Section YAML References in Tests
**What goes wrong:** 454-line test file `test_section_renderer.py` directly imports `load_section`, `load_all_sections` and loads specific section YAML files.
**Why it happens:** Tests written against section YAML infrastructure.
**How to avoid:** Update ALL test imports and assertions in the same wave as the consumer migration. Tests that load `financial_health.yaml` etc. must be rewritten to use manifest groups.
**Warning signs:** Test failures referencing `brain/sections/` paths.

### Pitfall 2: Template Variable Name Mismatch
**What goes wrong:** HTML templates reference `section_context[section_id]` variables that come from section YAML.
**Why it happens:** `build_section_context()` returns both `section_context` (from section YAML) and `manifest_sections` (from manifest). Templates may use either.
**How to avoid:** Search all `.html.j2` templates for `section_context` references before cutting over. The `manifest_sections` path is already wired.
**Warning signs:** Empty sections or missing facet headings in rendered HTML.

### Pitfall 3: Coverage Metric Regression in brain_health
**What goes wrong:** `facet_coverage_pct` changes after migration because section YAML `signals:` lists don't perfectly match signal `group` assignments.
**Why it happens:** Section YAML lists are manually maintained; `group` fields were auto-inferred. Some signals may be in sections but have different/wrong group assignments.
**How to avoid:** Before migration, run a comparison: signals in section YAML vs signals with group fields. Identify any discrepancies. All 54 group IDs already match facet IDs, but section-level `signals:` lists may differ from group-based aggregation.
**Warning signs:** Coverage percentage changing after migration.

### Pitfall 4: Signal Ordering in QA Audit Table
**What goes wrong:** QA audit table groups signals by section prefix (BIZ, FIN, GOV, etc.). After migration, grouping changes to use `group` field (finer-grained: `business_description`, `risk_factors`, etc.).
**Why it happens:** `_group_signals_by_section()` in html_signals.py uses section prefix, not facet-level grouping.
**How to avoid:** Decide whether QA audit table should show section-level or group-level organization. Match current behavior for zero regression, then refine in a later phase.

### Pitfall 5: Backward Compatibility Aliases
**What goes wrong:** `brain_section_schema.py` has backward-compat aliases: `SubsectionSpec = FacetSpec`, `load_facet = load_section`, etc.
**Why it happens:** Phase 56-02 migration left aliases for safety.
**How to avoid:** Search for ALL alias usage before deleting `brain_section_schema.py`. Grep for: `SubsectionSpec`, `FacetContentRef`, `load_facet`, `load_all_facets`.

## Code Examples

### ManifestGroup Model (New)
```python
# In manifest_schema.py
class ManifestGroup(BaseModel):
    """A group within a manifest section.

    Signals self-select into groups via their `group` field.
    No signal lists in the manifest -- membership is runtime-derived.
    """
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique group ID matching signal.group values")
    name: str = Field(..., description="Display heading for this group")
    template: str = Field(..., description="Template path for rendering")
    render_as: str = Field(..., description="Template dispatch type")
    requires: list[str] = Field(
        default_factory=list,
        description="Data field paths required for this group to render",
    )
```

### Signal Self-Selection Helper
```python
# In brain_unified_loader.py or manifest_schema.py
def collect_signals_by_group(
    signals: list[dict[str, Any]],
) -> dict[str, list[str]]:
    """Map group IDs to lists of signal IDs from loaded signals."""
    groups: dict[str, list[str]] = {}
    for sig in signals:
        gid = sig.get("group", "")
        if gid:
            groups.setdefault(gid, []).append(sig["id"])
    return groups
```

### Migrated section_renderer.py Pattern
```python
def build_section_context(state=None) -> dict[str, Any]:
    """Build section dispatch context using manifest groups + signal self-selection."""
    manifest = load_manifest()
    signals_data = load_signals()
    signals_by_group = collect_signals_by_group(signals_data.get("signals", []))

    manifest_sections = []
    for ms in manifest.sections:
        group_list = []
        for group in ms.groups:  # was ms.facets
            group_list.append({
                "id": group.id,
                "name": group.name,
                "template": group.template,
                "render_as": group.render_as,
                "signals": signals_by_group.get(group.id, []),
            })
        manifest_sections.append({
            "id": ms.id,
            "name": ms.name,
            "template": ms.template,
            "render_mode": ms.render_mode,
            "facets": group_list,  # Keep key name for template compat
        })

    return {"section_context": {}, "manifest_sections": manifest_sections}
```

## Existing Asset Inventory

### Files to Modify
| File | Lines | What Changes |
|------|-------|-------------|
| `brain/manifest_schema.py` | 186 | Add ManifestGroup, evolve ManifestSection.facets to .groups |
| `brain/output_manifest.yaml` | 1,226 | Remove `signals:` and `data_type:` from facet objects, becoming group objects |
| `stages/render/section_renderer.py` | 110 | Remove load_all_sections, use manifest groups + signal self-selection |
| `stages/render/html_signals.py` | 261 | Replace all section YAML reads with manifest + signal.group |
| `cli_brain_trace.py` | ~700 | 3 sites: replace section lookup with manifest group lookup |
| `brain/brain_audit.py` | 702 | Remove unused import of load_all_sections (line 22) |
| `brain/brain_health.py` | 219 | Replace section.signals coverage with signal.group coverage |
| `tests/stages/render/test_section_renderer.py` | 454 | Rewrite tests to use manifest groups instead of section YAML |
| `tests/test_cli_brain_trace.py` | varies | Update mocks/fixtures for new data sources |

### Files to Delete
| File | Lines | Safety Check |
|------|-------|-------------|
| `brain/sections/ai_risk.yaml` | ~50 | Verify no other imports |
| `brain/sections/business_profile.yaml` | 106 | Verify no other imports |
| `brain/sections/executive_risk.yaml` | ~80 | Verify no other imports |
| `brain/sections/executive_summary.yaml` | ~40 | Verify no other imports |
| `brain/sections/filing_analysis.yaml` | ~60 | Verify no other imports |
| `brain/sections/financial_health.yaml` | ~130 | Verify no other imports |
| `brain/sections/forward_looking.yaml` | ~80 | Verify no other imports |
| `brain/sections/governance.yaml` | ~120 | Verify no other imports |
| `brain/sections/litigation.yaml` | ~100 | Verify no other imports |
| `brain/sections/market_activity.yaml` | ~100 | Verify no other imports |
| `brain/sections/red_flags.yaml` | ~20 | Verify no other imports |
| `brain/sections/scoring.yaml` | ~80 | Verify no other imports |
| `brain/brain_section_schema.py` | 182 | Verify zero remaining imports |

### Key Numbers
- 476 signals with `group` field populated
- 54 distinct group IDs across signals
- 97 facets in current manifest (54 with signals, 43 infrastructure-only)
- 12 section YAML files to delete
- 5 consumers to migrate
- 1 schema file to delete (`brain_section_schema.py`)

## Word Renderer Note

The Word renderer (`word_renderer.py`) does NOT import `brain_section_schema`. It uses `manifest_schema.load_manifest()` for section ordering and has hardcoded section-to-renderer mappings (`_SECTION_RENDERER_MAP`). No Word renderer migration is needed for section YAML elimination. MANIF-04 is satisfied by ensuring the manifest group structure provides the same section ordering data that `load_manifest()` already provides.

## Manifest YAML Evolution Strategy

The manifest YAML currently has `facets:` with 7 fields per facet (`id`, `name`, `template`, `data_type`, `render_as`, `signals`, `requires`). The target ManifestGroup has 5 fields (`id`, `name`, `template`, `render_as`, `requires`). Removed: `data_type` (unused by consumers), `signals` (now derived from signal.group).

Key decision: whether to rename `facets:` key to `groups:` in YAML and code. Recommendation: YES -- rename to `groups:` for clarity, but keep `"facets"` as a key name in the template context dict for backward compatibility with HTML templates that iterate `manifest_section.facets`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/stages/render/test_section_renderer.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MANIF-01 | ManifestGroup with 5 fields validates | unit | `uv run pytest tests/brain/test_manifest_schema.py -x` | Needs update |
| MANIF-02 | Signals self-select into groups | unit | `uv run pytest tests/brain/test_signal_group_resolution.py -x` | Wave 0 |
| MANIF-03 | HTML render uses manifest groups | integration | `uv run pytest tests/stages/render/test_section_renderer.py -x` | Needs rewrite |
| MANIF-04 | Word render uses manifest groups | integration | `uv run pytest tests/stages/render/test_word_renderer.py -x` | Exists (no change needed) |
| MANIF-05 | PDF/HTML visual parity | manual + visual | `VISUAL_REGRESSION=1 uv run pytest tests/test_visual_regression.py -x` | Exists |
| SECT-01 | section_renderer migrated | unit | `uv run pytest tests/stages/render/test_section_renderer.py -x` | Needs rewrite |
| SECT-02 | html_signals migrated | unit | `uv run pytest tests/stages/render/test_html_signals.py -x` | Wave 0 |
| SECT-03 | cli_brain_trace migrated | unit | `uv run pytest tests/test_cli_brain_trace.py -x` | Exists (needs update) |
| SECT-04 | brain_audit + brain_health migrated | unit | `uv run pytest tests/brain/test_brain_health.py tests/brain/test_brain_audit.py -x` | Wave 0 |
| SECT-05 | Section YAML files deleted | smoke | `python -c "from pathlib import Path; assert not Path('src/do_uw/brain/sections').exists()"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/render/ tests/test_cli_brain_trace.py -x --timeout=30`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green + pipeline run on RPM and V with visual comparison

### Wave 0 Gaps
- [ ] `tests/brain/test_signal_group_resolution.py` -- covers MANIF-02 (signal self-selection)
- [ ] `tests/stages/render/test_html_signals.py` -- covers SECT-02 (does not exist yet)
- [ ] Update `tests/stages/render/test_section_renderer.py` -- 454 lines referencing section YAML

## Open Questions

1. **Template `section_context` Usage**
   - What we know: `build_section_context()` returns both `section_context` and `manifest_sections`. Templates receive both.
   - What's unclear: Do any `.html.j2` templates access `section_context` directly, or only `manifest_sections`? Must grep templates before migration.
   - Recommendation: Grep all templates for `section_context` usage. If only `manifest_sections` is used, the migration is simpler.

2. **Signal Ordering Within Groups**
   - What we know: Section YAML lists signals in explicit order. Signal `group` field provides no ordering.
   - What's unclear: Whether signal ordering within a group affects rendered output.
   - Recommendation: For the QA audit table, sort signals alphabetically by ID (matches current behavior since most section YAMLs sort alphabetically). Verify no visual regression.

## Sources

### Primary (HIGH confidence)
- Direct code reading: `manifest_schema.py` (186 lines), `brain_section_schema.py` (182 lines), `section_renderer.py` (110 lines), `html_signals.py` (261 lines), `brain_audit.py` (702 lines), `brain_health.py` (219 lines), `cli_brain_trace.py` (~700 lines)
- Direct code reading: `output_manifest.yaml` (1,226 lines) -- full facet/signal mapping
- Direct code reading: All signal YAML files -- `group` field analysis (54 distinct groups, 476 signals)
- `grep` analysis: All imports of `brain_section_schema` across codebase (exhaustive)

### Secondary (MEDIUM confidence)
- Phase 82 CONTEXT.md -- group field population decisions and methodology

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries needed, pure internal refactoring
- Architecture: HIGH -- complete code reading of all 5 consumers and both data sources
- Pitfalls: HIGH -- enumerated from actual code analysis, not speculation

**Research date:** 2026-03-08
**Valid until:** 2026-04-08 (stable internal architecture)
