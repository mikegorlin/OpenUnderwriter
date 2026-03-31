# Phase 147: Golden Manifest Wiring - Research

**Researched:** 2026-03-28
**Domain:** Jinja2 template wiring, manifest-driven rendering, context builder pipeline
**Confidence:** HIGH

## Summary

The output manifest (`output_manifest.yaml`) declares 166 groups across 14 sections. Of these, 103 are `display_only` (62%), 21 have explicit `requires` clauses, and 42 are regular groups with neither flag. The primary problem is that 70 `display_only` templates lack top-level `{% if %}` suppression guards, meaning they may render empty cards, headers with no content, or whitespace when data is absent.

Three templates are outright stubs (comment-only, zero rendering): `subsidiary_structure`, `workforce_distribution`, `operational_resilience`. These currently get `{% include %}`d without guards in the report template and produce no visible output -- but they still exist in the DOM path and could produce empty space.

The context builder pipeline is well-structured: 5 assembly modules register via `@register_builder` decorator, each populating context keys that templates consume. Alt-data builders (ESG, tariff, AI-washing, peer SCA) already exist and produce data for AAPL. The wiring gap is between these context keys and the template guards -- many templates read from context dicts but don't suppress when the dict is empty or contains only fallback values.

**Primary recommendation:** Systematically audit each of the 166 groups, classify them into three tiers (renders/wired/suppressed), add `{% if %}` guards to all 70 unguarded display_only templates, convert the 3 stubs to empty files, and create an automated completeness test that loads a real state.json and verifies the classification.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Three-tier classification: "renders" (has data, shows content), "wired" (has data path but may be empty for some tickers), "suppressed" (no data path, hidden via `{% if %}` guard). Every template gets exactly one classification.
- **D-02:** Suppressed templates produce ZERO DOM elements -- not hidden divs, not empty cards, not whitespace. Use `{% if data %}...{% endif %}` at the template root level, not CSS display:none.
- **D-03:** Wiring audit is automated -- a test reads the manifest, renders each template with a real state.json, and classifies output as renders/wired/suppressed.
- **D-04:** Wire data through existing context builders in `assembly_registry.py` -- no new builder files. Add keys to existing builder functions where data already exists in state.
- **D-05:** For templates where pipeline data doesn't exist yet (adverse events, tariff risk, ESG), add suppression guards now. Don't fake data or create placeholder text. These templates activate when future pipeline stages produce the data.
- **D-06:** Templates that render analytical content from signals (display_only=true in manifest) should check if any signals fired for their group. If zero signals -> suppress entirely.
- **D-07:** Create `test_manifest_wiring_completeness.py` that loads real state.json, renders each manifest group template, and asserts: (a) renders produce non-empty content, (b) suppressed produce empty string, (c) no template crashes with TypeError/AttributeError.
- **D-08:** Audit log written to render context as `manifest_audit` dict -- available in audit trail section.

### Claude's Discretion
- Order of template wiring within each section
- Whether to merge small related templates into parent sections
- Specific Jinja2 guard expressions for each template
- Whether display-only templates with zero fired signals should show "No concerns identified" vs suppress entirely (recommend: suppress)

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| WIRE-01 | Audit all 27 recently-added manifest templates -- categorize as renders/needs wiring/suppress | Full manifest inventory of 166 groups completed; 3 stubs identified, 70 display_only templates lack guards, actual count is broader than "27" |
| WIRE-02 | For each "needs wiring" template, identify state path and context builder that should populate it | Context builder registry documented; 5 assembly modules identified; alt_data builders already wired |
| WIRE-03 | For each "structurally empty" template, add `{% if %}` guard so it produces zero output | 70 unguarded display_only templates identified; guard patterns documented from existing templates |
| WIRE-04 | Add missing manifest groups: adverse_events, tariff risk, ESG indicators | Alt data context builders already exist (`alt_data_context.py`); data present in AAPL state.json; templates need wiring to these builders |
| WIRE-05 | Manifest completeness test -- automated check that every group renders or is suppressed | Test pattern documented from `test_manifest_coverage.py`; state.json available for AAPL, ORCL, META, HNGE, RPM |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Jinja2 | 3.1+ | Template rendering with conditional guards | Already the template engine; no alternative needed |
| PyYAML | 6.0+ | Manifest YAML parsing | Already used for manifest_schema |
| Pydantic v2 | 2.10+ | ManifestGroup schema with display_only field | Already defined in manifest_schema.py |
| pytest | 9.0+ | Automated wiring completeness tests | Project standard test framework |

No new dependencies required. This phase is entirely about wiring existing infrastructure.

## Architecture Patterns

### Manifest-to-Template Data Flow
```
output_manifest.yaml
  -> ManifestGroup (id, template, display_only, requires)
  -> section_renderer.py build_section_context()
  -> assembly_registry.py build_html_context()
     -> 5 registered builders populate context dict
  -> report/*.html.j2 (parent templates)
     -> {% include "sections/X/Y.html.j2" %}
        -> Template reads context[key], renders or suppresses
```

### Three-Tier Classification Pattern
```
RENDERS:   Template has data path, data exists for target ticker -> produces content
WIRED:     Template has data path, data MAY be empty for some tickers -> conditional guard
SUPPRESSED: Template has no data path or is structurally empty -> zero DOM output
```

### Suppression Guard Pattern (established in codebase)
```jinja2
{# GOOD: Top-level guard, zero output when empty #}
{% set data = context_key | default({}) %}
{% if data and data.get('has_content') %}
<h3>Section Title</h3>
<div>{{ data.value }}</div>
{% endif %}

{# BAD: No guard, renders empty card #}
<h3>Section Title</h3>
{% set data = context_key | default({}) %}
{% if data %}<div>{{ data.value }}</div>{% endif %}
{# ^^ Still emits <h3> even when data is empty #}
```

### Report Template Include Pattern
```jinja2
{# Report templates include sub-templates in two styles: #}

{# Style 1: ignore missing (safe -- produces nothing if file missing) #}
{% include "sections/company/subsidiary_structure.html.j2" ignore missing %}

{# Style 2: direct include (crashes if file missing) #}
{% include "sections/company/business_model.html.j2" %}
```

### Context Builder Registration Pattern
```python
# In assembly_dossier.py (or any builder file)
@register_builder
def _build_my_context(
    state: AnalysisState,
    context: dict[str, Any],
    chart_dir: Path | None,
) -> None:
    context["my_key"] = extract_data(state)
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Template existence checks | Custom file walker | `test_manifest_coverage.py` parametrized tests | Already validates all 166 groups |
| Context key population | New builder files | Existing 5 assembly modules + `@register_builder` | D-04 explicitly requires no new builder files |
| Signal-to-group mapping | Manual mapping dict | `collect_signals_by_group()` in `manifest_schema.py` | Already maps signals to manifest groups |
| Template rendering for tests | Custom Jinja2 env setup | Load real state.json + `build_html_context()` | Matches production rendering path |

## Common Pitfalls

### Pitfall 1: Guard Inside Template Body Instead of Wrapping It
**What goes wrong:** Template emits `<h3>` or `<div>` headers before the data guard, producing empty cards with headers but no content.
**Why it happens:** Developer adds `{% if data %}` around the data rows but forgets the header is outside the guard.
**How to avoid:** Every template's FIRST non-comment line must be the `{% if %}` guard. The guard must wrap the ENTIRE template output including heading tags.
**Warning signs:** `<h3>` tags with no sibling content divs in rendered HTML.

### Pitfall 2: Jinja2 `| default({})` Creates Truthy Empty Dict
**What goes wrong:** `{% if data %}` passes because `{}` is truthy in Jinja2, so an empty fallback dict still triggers rendering.
**Why it happens:** Python/Jinja2 treats empty dict as falsy in Python but the Jinja2 `if` test considers `{}` as truthy.
**How to avoid:** Use `{% if data and data.keys() | list | length > 0 %}` or check a specific sentinel key like `data.get('available', false)` or `data.get('has_content', false)`.
**Warning signs:** Empty cards rendering for tickers where data is absent.

### Pitfall 3: Stub Templates Producing Whitespace
**What goes wrong:** Comment-only stubs (`{# Stub #}`) produce zero DOM elements but may produce whitespace that creates gaps in layout.
**Why it happens:** Jinja2 preserves whitespace around block tags by default.
**How to avoid:** Convert stubs to completely empty files (0 bytes), or add a suppression guard that produces empty string.
**Warning signs:** Unexplained spacing between sections.

### Pitfall 4: Testing with Wrong State
**What goes wrong:** Test uses `AnalysisState(ticker="TEST")` which has no data in any field, so ALL templates would be "suppressed" -- test doesn't catch actual wiring issues.
**Why it happens:** Creating minimal test state is easier than loading real state.
**How to avoid:** D-03 mandates using real state.json. Load from `output/AAPL/state.json` (most complete).
**Warning signs:** All templates classified as "suppressed" in test.

### Pitfall 5: Report Templates vs Manifest Templates Mismatch
**What goes wrong:** The report-level templates (`report/company.html.j2`) include sub-templates directly via `{% include %}`. The manifest declares groups with template paths. These are independent systems -- adding a guard to the sub-template file doesn't help if the report template also emits HTML around the include.
**Why it happens:** Dual rendering path: manifest-driven section context AND hardcoded report templates.
**How to avoid:** Guards must be in the sub-template file itself (the one referenced by manifest group), not in the report template. The report template's `{% include %}` will then get zero output from the sub-template.
**Warning signs:** Empty cards visible despite sub-template having a guard.

## Code Examples

### Adding a Suppression Guard to an Existing Template
```jinja2
{# BEFORE: No guard, may render empty #}
{% set eg = mkt.get('earnings_guidance', {}) %}
{# ... content ... #}

{# AFTER: Guard wraps entire output #}
{% set eg = mkt.get('earnings_guidance', {}) %}
{% if eg and eg.get('provides_guidance') %}
<h3>Earnings Guidance Track Record</h3>
{{ kv_table([...]) }}
{% endif %}
```

### Converting a Stub to Suppressed
```jinja2
{# BEFORE (stub): #}
{# Subsidiary Structure -- stub template, Phase 100 will expand #}

{# AFTER (empty -- produces zero output): #}
{# Suppressed: no data path. Phase 147 audit classification: suppressed. #}
```

### Manifest Audit Dict for Render Context
```python
# In assembly_dossier.py or a new section of an existing builder
manifest_audit: dict[str, str] = {}
manifest = load_manifest()
for section in manifest.sections:
    for group in section.groups:
        # Classification logic based on rendered output
        rendered = render_group_template(group, context)
        if rendered.strip():
            manifest_audit[group.id] = "renders"
        elif group_has_data_path(group, state):
            manifest_audit[group.id] = "wired"
        else:
            manifest_audit[group.id] = "suppressed"
context["manifest_audit"] = manifest_audit
```

### Completeness Test Pattern
```python
# test_manifest_wiring_completeness.py
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

STATE_PATH = Path("output/AAPL/state.json")

def test_no_empty_rendered_groups():
    """Every manifest group either renders content or is explicitly suppressed."""
    state_data = json.loads(STATE_PATH.read_text())
    context = build_html_context_from_state(state_data)
    manifest = load_manifest()

    empty_groups = []
    for section in manifest.sections:
        for group in section.groups:
            rendered = env.get_template(group.template).render(**context)
            if rendered.strip() == "" and group.id not in EXPECTED_SUPPRESSED:
                empty_groups.append(f"{section.id}/{group.id}")

    assert not empty_groups, f"Groups render empty but not suppressed: {empty_groups}"
```

## Inventory: Current State of 166 Manifest Groups

### By Classification (pre-phase-147)

| Category | Count | Description |
|----------|-------|-------------|
| Stub templates (comment-only) | 3 | subsidiary_structure, workforce_distribution, operational_resilience |
| display_only, no guard | 70 | Need `{% if %}` guards added |
| display_only, has guard | 33 | Already properly guarded |
| Non-display, has requires | 21 | Have data dependency declarations |
| Non-display, no requires | 42 | Regular templates, may need guards |

### Section-by-Section Group Counts

| Section | Total | display_only | Needs Guards |
|---------|-------|-------------|-------------|
| executive_summary | 7 | 4 | ~3 |
| red_flags | 1 | 1 | 1 |
| company_operations | 35 | 21 | ~15 |
| market_activity | 23 | 18 | ~14 |
| financial_health | 25 | 12 | ~8 |
| governance | 19 | 8 | ~5 |
| litigation | 13 | 3 | ~2 |
| sector_industry | 5 | 4 | ~4 |
| forward_looking | 4 | 4 | ~3 |
| scoring | 34 | 28 | ~15 |

### Alt-Data Templates (WIRE-04 targets)

These context builders exist in `alt_data_context.py` and produce data for AAPL:
- ESG indicators: `build_esg_context()` -> context keys `esg_*`, `has_esg_data`
- Tariff risk: `build_tariff_context()` -> context keys `tariff_*`, `has_tariff_data`
- AI washing: `build_ai_washing_context()` -> context keys `ai_washing_*`
- Peer SCA: `build_peer_sca_context()` -> context keys `peer_sca_*`

Templates that consume this data need to be identified or created. Currently `peer_sca_contagion.html.j2` exists in company section. Need to verify if ESG, tariff, and adverse_events templates exist as standalone or need manifest group additions.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/brain/test_manifest_coverage.py tests/stages/render/test_manifest_rendering.py -x` |
| Full suite command | `uv run pytest tests/ -x --timeout=120` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WIRE-01 | Audit classifies all groups | integration | `uv run pytest tests/stages/render/test_manifest_wiring_completeness.py::test_audit_classifies_all_groups -x` | Wave 0 |
| WIRE-02 | Wired templates have context paths | unit | `uv run pytest tests/stages/render/test_manifest_wiring_completeness.py::test_wired_templates_have_context -x` | Wave 0 |
| WIRE-03 | Suppressed templates produce empty output | integration | `uv run pytest tests/stages/render/test_manifest_wiring_completeness.py::test_suppressed_produce_empty -x` | Wave 0 |
| WIRE-04 | Alt-data manifest groups exist | unit | `uv run pytest tests/stages/render/test_manifest_wiring_completeness.py::test_alt_data_groups_exist -x` | Wave 0 |
| WIRE-05 | No unclassified groups remain | integration | `uv run pytest tests/stages/render/test_manifest_wiring_completeness.py::test_manifest_completeness -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/brain/test_manifest_coverage.py tests/stages/render/test_manifest_rendering.py tests/stages/render/test_manifest_wiring_completeness.py -x`
- **Per wave merge:** `uv run pytest tests/ -x --timeout=120`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/stages/render/test_manifest_wiring_completeness.py` -- covers WIRE-01 through WIRE-05
- [ ] Test fixture: script to load AAPL state.json and build full HTML context

## Project Constraints (from CLAUDE.md)

- **Brain YAML is source of truth** -- manifest groups reference brain signals; display_only templates show brain-evaluated data
- **Renderers are dumb consumers** -- zero business logic in templates; guards check data presence only
- **No bare float()** -- use `safe_float()` from formatters.py
- **NEVER truncate analytical content** -- no `| truncate()` on evidence/findings
- **Self-verification** -- re-render and verify output before claiming done
- **Root-cause problem solving** -- if a template renders empty, fix the data path, not just the template
- **Anti-context-rot** -- no file over 500 lines; this phase should not bloat any single file
- **Preserve before improve** -- never remove existing analytical capabilities

## Sources

### Primary (HIGH confidence)
- `src/do_uw/brain/output_manifest.yaml` -- full manifest with 166 groups, 14 sections
- `src/do_uw/brain/manifest_schema.py` -- ManifestGroup schema (display_only field)
- `src/do_uw/stages/render/context_builders/assembly_registry.py` -- builder pipeline (5 modules)
- `src/do_uw/stages/render/context_builders/assembly_dossier.py` -- 20+ context builders
- `src/do_uw/stages/render/context_builders/alt_data_context.py` -- ESG, tariff, AI-washing, peer SCA
- `src/do_uw/templates/html/sections/report/company.html.j2` -- 34 includes, report template pattern
- `output/AAPL/state.json` -- real pipeline output confirming data availability
- `tests/brain/test_manifest_coverage.py` -- existing template existence tests

### Secondary (MEDIUM confidence)
- Template-by-template guard audit (70 unguarded display_only templates) -- based on automated scan of first non-comment line

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all existing infrastructure
- Architecture: HIGH -- manifest/builder/template pattern well-documented in codebase
- Pitfalls: HIGH -- based on direct codebase inspection of actual templates and guard patterns
- Inventory: HIGH -- automated count from manifest YAML + template file sizes

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- internal codebase, no external dependency changes)
