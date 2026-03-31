# Phase 145: Rename & Deduplication - Research

**Researched:** 2026-03-28
**Domain:** Codebase rename (beta_report -> uw_analysis) + template metric deduplication
**Confidence:** HIGH

## Summary

This phase is a pure internal refactor: rename all `beta_report` references to `uw_analysis` across 10 Python source files, 3 templates, 6 test files, 1 QA script, and the assembly registry. Then deduplicate cross-section metric displays so each headline metric (revenue, market cap, stock price, board size, employees) has exactly one "home section" with full provenance, plus the persistent header bar.

The rename is mechanical but broad: 318 total occurrences of `beta_report` across 55 files (most in `.planning/` docs that are out of scope). The active code scope is 16 source files + 6 test files + 1 script = 23 files to modify, plus 10 files to `git mv`. The dedup pass is template-focused: revenue appears in 43 HTML templates (157 occurrences), but most are section-specific analytical content (revenue model, segments, concentration) that should stay. The dedup targets are headline metric *values* repeated outside their home section.

**Primary recommendation:** Execute as two atomic commits per D-09: (1) pure rename via `git mv` + find-and-replace, (2) dedup pass removing redundant headline metrics from non-home templates. Run full test suite between commits.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Rename `beta_report` -> `uw_analysis` everywhere. "Underwriting Analysis" conceptual name, `uw_analysis` code abbreviation.
- **D-02:** Rename ALL filenames too -- full clean break.
- **D-03:** Template context variable: `beta_report` -> `uw_analysis`. Templates use `b = uw_analysis`.
- **D-04:** 10+ source files with `beta_report` in filename, 7 Python source files with references, 3 templates, 6 test files.
- **D-05:** Home + header bar only. Revenue=Financial, Market cap=Decision Dashboard, Stock price=Stock & Market, Board size=Governance.
- **D-06:** Header bar keeps MCap/Revenue/Price/Employees as ONLY allowed cross-section duplicates.
- **D-07:** All other mentions removed or replaced with layout space. No "See X section" cross-references.
- **D-08:** Revenue appears in 29 templates currently -- significant reduction expected.
- **D-09:** Two-commit structure: Commit 1 = pure rename, Commit 2 = dedup pass.
- **D-10:** Separating rename from dedup makes it safe to bisect.

### Claude's Discretion
- Order of file renames within the rename commit
- Whether to create temporary compatibility aliases during rename (probably not needed if done atomically)
- Which specific template blocks to remove vs keep during dedup (within home section rules)

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| NAME-01 | Rename beta_report -> worksheet_report across all Python files (11 files), templates (3 files), context builders, and tests | **NOTE: CONTEXT.md overrides this** -- user chose `uw_analysis` not `worksheet_report`. Full file inventory below (10 Python files to rename, 3 templates, 6 test files, 1 script, 1 registry). |
| NAME-02 | Context variable `beta_report` -> `report` in all templates | **NOTE: CONTEXT.md overrides this** -- user chose `uw_analysis` not `report`. Template sets `b = uw_analysis`. |
| DEDUP-01 | Define "home section" for each major metric | Home assignments per D-05: Revenue=Financial, MCap=Decision Dashboard, Price=Stock & Market, Board size=Governance |
| DEDUP-02 | Revenue home = Financial; MCap home = Decision Dashboard; Stock price home = Stock & Market; Board size home = Governance | Confirmed -- these align with existing template structure |
| DEDUP-03 | Header bar keeps MCap/Revenue/Price/Employees as persistent reference -- ONLY allowed cross-section duplicates | Header bar is in beta_report.html.j2 line 40: `{% for label, val in [("MCap", b.market_cap), ("Revenue", b.revenue), ("Price", b.stock_price), ("Employees", b.employees)] %}` |
| DEDUP-04 | Remove redundant metric displays from non-home sections | Dedup targets identified below; most "revenue" mentions are analytical content (revenue model, segments) that stays |
</phase_requirements>

## REQUIREMENTS.md vs CONTEXT.md Discrepancy

**CRITICAL:** REQUIREMENTS.md says `beta_report -> worksheet_report` (NAME-01) and `beta_report -> report` (NAME-02). CONTEXT.md overrides both -- user decided `uw_analysis` in discussion. **The CONTEXT.md decisions take precedence.** The planner MUST use `uw_analysis`, not `worksheet_report` or `report`.

## Architecture Patterns

### Rename File Map (Commit 1)

**Python source files to `git mv` (9 files):**

| Old Name | New Name | Lines |
|----------|----------|-------|
| `beta_report.py` | `uw_analysis.py` | 380 |
| `assembly_beta_report.py` | `assembly_uw_analysis.py` | 32 |
| `_beta_report_helpers.py` | `_uw_analysis_helpers.py` | 682 |
| `_beta_report_investigative.py` | `_uw_analysis_investigative.py` | 609 |
| `_beta_report_findings.py` | `_uw_analysis_findings.py` | 934 |
| `_beta_report_uw_metrics.py` | `_uw_analysis_uw_metrics.py` | 214 |
| `beta_report_sections.py` | `uw_analysis_sections.py` | 3,751 |
| `beta_report_charts.py` | `uw_analysis_charts.py` | 209 |
| `beta_report_infographics.py` | `uw_analysis_infographics.py` | 305 |

All in `src/do_uw/stages/render/context_builders/`.

**Template file to `git mv` (1 file):**
- `templates/html/sections/beta_report.html.j2` -> `uw_analysis.html.j2`

**CONTEXT.md MISSED ONE FILE:** `beta_report_infographics.py` (305 lines) is NOT in the canonical refs list but DOES contain `beta_report` in its filename and is imported by multiple other beta_report files. It MUST be renamed.

**Files requiring string replacement (not rename):**

| File | Occurrences | What Changes |
|------|-------------|--------------|
| `assembly_registry.py` | 9 | Function name refs, banner propagation, import |
| `templates/html/base.html.j2` | 1 | `{% if beta_report %}` -> `{% if uw_analysis %}` |
| `templates/html/worksheet.html.j2` | 1 | `{% include "sections/beta_report.html.j2" %}` |
| `scripts/qa_beta_report.py` | 10+ | Script name stays (or rename to `qa_uw_analysis.py`), internal refs |

**Test files requiring string replacement (6 files):**

| File | Occurrences | What Changes |
|------|-------------|--------------|
| `tests/stages/render/test_stage_banner_template.py` | 12 | Patch paths, context key refs |
| `tests/stages/render/test_pipeline_status_wiring.py` | 4 | Patch paths |
| `tests/test_canonical_metrics.py` | 4 | Import path, function name |
| `tests/stages/render/test_reading_paths.py` | 2 | Template path constant |
| `tests/brain/test_contract_enforcement.py` | 1 | Template name in allowlist |
| `tests/brain/test_template_facet_audit.py` | 1 | Template name in allowlist |

### Context Variable Flow

```
assembly_beta_report.py:
  context["beta_report"] = build_beta_report_context(state, ...)
  ↓
beta_report.html.j2:
  {% set b = beta_report %}
  ↓
All template refs use: b.market_cap, b.revenue, b.stock_price, etc.
```

After rename:
```
assembly_uw_analysis.py:
  context["uw_analysis"] = build_uw_analysis_context(state, ...)
  ↓
uw_analysis.html.j2:
  {% set b = uw_analysis %}
  ↓
All template refs: b.market_cap, b.revenue, etc. (UNCHANGED — 'b' alias is stable)
```

The `b` alias means most template internals need zero changes. Only the top-level `{% set b = ... %}` line and the `{% if beta_report %}` guard in `base.html.j2` change.

### Dedup Home Section Map (Commit 2)

| Metric | Home Section | Header Bar | Remove From |
|--------|-------------|------------|-------------|
| Revenue ($X.XB) | Financial (`report/financial.html.j2`) | Yes (line 40) | `report/page0_dashboard.html.j2` card 3 shows Revenue prominently -- this is the Decision Dashboard so it STAYS per DEDUP-02 (MCap home = Decision Dashboard, but Revenue card is analytical). `key_stats.html.j2` -- NO revenue headline value there (it's "Revenue Model" text). |
| Market Cap | Decision Dashboard (`report/page0_dashboard.html.j2`) | Yes (line 40) | `report/stock_market.html.j2`, `sections/market.html.j2`, `sections/executive/company_profile.html.j2` |
| Stock Price | Stock & Market (`report/stock_market.html.j2`) | Yes (line 40) | `key_stats.html.j2` (lines 143-161 stock price panel), `sections/scorecard.html.j2` |
| Board Size | Governance (`report/governance.html.j2`) | Yes (NOT in header bar currently -- only MCap/Revenue/Price/Employees) | Limited duplication -- mostly only in governance templates |
| Employees | Header bar reference | Header bar (line 40) | Check `identity.html.j2`, `company_profile.html.j2` |

**Important distinction for dedup:** "Revenue" as a concept (revenue model, revenue segments, revenue growth %) is analytical content that STAYS in its section. Only the headline dollar value ("Revenue: $X.XXB") is the dedup target. The planner must instruct implementers to distinguish between:
1. **Headline metric value** (e.g., "$3.05B") -- dedup target, keep only in home + header
2. **Analytical use of metric** (e.g., "revenue grew 12% YoY", "revenue concentration risk") -- NOT a dedup target, stays wherever contextually relevant

### Anti-Patterns to Avoid
- **Renaming in planning/docs**: `.planning/` files, MILESTONES.md, HANDOFF.json contain `beta_report` references. These are historical records -- do NOT rename them. Only rename active source code, templates, tests, and scripts.
- **Breaking the `b` alias**: Templates use `{% set b = beta_report %}` then reference `b.fin`, `b.gov`, etc. throughout. Only change the set line, NOT every `b.something` reference.
- **Over-deduping analytical content**: "Revenue" appears 157 times in templates. Most are section-specific analysis (revenue model, segments, growth rates). Only the headline value display is a dedup target.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Finding all references | Manual file-by-file search | `grep -r "beta_report" src/ tests/ templates/ scripts/` | Mechanical, complete |
| Verifying rename completeness | Manual checking | `grep -r "beta_report" src/ tests/` should return 0 matches | Per success criteria |
| Dedup verification | Manual template review | Automated check: count occurrences of metric values across rendered HTML sections | Catches regressions |

## Runtime State Inventory

This is a rename/refactor phase, so runtime state inventory is required.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **state.json files in output/** -- contain no `beta_report` keys (context builder output uses metric names like `market_cap`, `revenue`). The key `beta_report` is only in the HTML template context dict, never serialized to state.json. | None -- state.json is unaffected |
| Live service config | None -- no external services reference `beta_report`. Dashboard app (`dashboard/app.py`) does not use this string. | None |
| OS-registered state | None -- CLI entry points are `angry-dolphin` and `do-uw`, unaffected by internal module rename. | None |
| Secrets/env vars | None -- no env vars reference `beta_report`. | None |
| Build artifacts | `.venv/` contains compiled bytecode (`.pyc`) for old module paths. After rename, Python will auto-recompile on next import. Stale `.pyc` files for old paths are harmless (never imported). | None -- `uv sync` or natural execution cleans up |

**The canonical question:** After every file in the repo is updated, what runtime systems still have the old string cached, stored, or registered? **Answer: None.** The `beta_report` name exists only in source code, templates, and tests. No runtime state persists it.

## Common Pitfalls

### Pitfall 1: Import Ordering After git mv
**What goes wrong:** `git mv` renames the file but all imports still point to old module name. If you run tests between `git mv` and import updates, everything breaks.
**Why it happens:** `git mv` is just a filesystem operation, not a refactoring tool.
**How to avoid:** Do ALL `git mv` operations and ALL import/reference updates in a single commit. Never commit a half-renamed state.
**Warning signs:** Any import error mentioning `beta_report` after rename commit.

### Pitfall 2: Circular Import During Rename
**What goes wrong:** The context builder files have many cross-imports (`_beta_report_helpers` imports from `beta_report_infographics`, which imports from `beta_report_charts`, etc.). Renaming one without the others causes ImportError.
**Why it happens:** Tight coupling between the 9 builder files.
**How to avoid:** Rename ALL 9+1 files atomically in the same commit. Use find-and-replace across all files simultaneously.

### Pitfall 3: Template Name in Test Allowlists
**What goes wrong:** `test_contract_enforcement.py` and `test_template_facet_audit.py` have `"sections/beta_report.html.j2"` in hardcoded allowlists. If template is renamed but allowlist is not, tests fail.
**Why it happens:** Template names are strings in test files, not programmatic references.
**How to avoid:** Include test file updates in the rename commit.

### Pitfall 4: Over-Deduping Revenue
**What goes wrong:** Removing revenue mentions from Company section templates destroys revenue model analysis, segment breakdowns, and concentration data.
**Why it happens:** Grepping for "revenue" catches both headline value and analytical content.
**How to avoid:** Dedup pass must distinguish headline metric VALUE from analytical USE. Only remove `$X.XXB` displays, not "revenue model", "revenue segments", "revenue growth %", etc.

### Pitfall 5: qa_beta_report.py Script
**What goes wrong:** Script looks for `id="beta-report"` in HTML output. After template rename, the section ID changes and the QA script finds nothing.
**Why it happens:** QA script hardcodes the HTML element ID.
**How to avoid:** Rename script + update all internal references to match new template IDs.

### Pitfall 6: assembly_registry Banner Propagation
**What goes wrong:** `_propagate_banners_to_beta_report()` in `assembly_registry.py` explicitly references `context.get("beta_report")`. If context key changes but this function doesn't, stage failure banners stop propagating.
**Why it happens:** String key reference to context dict.
**How to avoid:** Update the `_BANNER_MAP` and all `context.get("beta_report")` calls in assembly_registry.py.

## Code Examples

### Rename Pattern: git mv + sed

```bash
# File renames (all in src/do_uw/stages/render/context_builders/)
git mv beta_report.py uw_analysis.py
git mv assembly_beta_report.py assembly_uw_analysis.py
git mv _beta_report_helpers.py _uw_analysis_helpers.py
git mv _beta_report_investigative.py _uw_analysis_investigative.py
git mv _beta_report_findings.py _uw_analysis_findings.py
git mv _beta_report_uw_metrics.py _uw_analysis_uw_metrics.py
git mv beta_report_sections.py uw_analysis_sections.py
git mv beta_report_charts.py uw_analysis_charts.py
git mv beta_report_infographics.py uw_analysis_infographics.py

# Template rename
git mv templates/html/sections/beta_report.html.j2 templates/html/sections/uw_analysis.html.j2
```

### Import Update Pattern

```python
# Before
from do_uw.stages.render.context_builders.beta_report import build_beta_report_context
from do_uw.stages.render.context_builders._beta_report_helpers import badges

# After
from do_uw.stages.render.context_builders.uw_analysis import build_uw_analysis_context
from do_uw.stages.render.context_builders._uw_analysis_helpers import badges
```

### Context Key Update Pattern

```python
# assembly_uw_analysis.py (was assembly_beta_report.py)
context["uw_analysis"] = build_uw_analysis_context(state, canonical=context.get("_canonical_obj"))

# assembly_registry.py banner propagation
br = context.get("uw_analysis")
```

### Template Update Pattern

```jinja2
{# uw_analysis.html.j2 — only this line changes #}
{% set b = uw_analysis %}

{# base.html.j2 #}
<nav ... {% if uw_analysis %}style="display:none"{% endif %}>

{# worksheet.html.j2 #}
{% include "sections/uw_analysis.html.j2" ignore missing %}
```

### Dedup Template Removal Pattern

```jinja2
{# BEFORE: key_stats.html.j2 showing stock price panel (lines 143-170) #}
<div class="ks-panel-title">Stock Price -- {{ ks.ticker }}
  ...
  <span class="ks-stock-current">${{ "%.2f" | format(ks.stock_price) }}</span>
  ...

{# AFTER: Remove entire stock price panel from key_stats (home = Stock & Market) #}
{# Replace with additional section-specific content or nothing #}
```

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2+ with pytest-asyncio |
| Config file | `pyproject.toml` ([tool.pytest.ini_options]) |
| Quick run command | `uv run pytest tests/stages/render/ -x -q --timeout=30` |
| Full suite command | `uv run pytest --timeout=60` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| NAME-01 | No `beta_report` in source | smoke | `grep -r "beta_report" src/ tests/ scripts/ \| wc -l` (expect 0) | Wave 0 |
| NAME-02 | Context variable is `uw_analysis` | unit | `uv run pytest tests/test_canonical_metrics.py -x` (after update) | Exists (needs update) |
| DEDUP-01 | Home sections defined | unit | N/A -- verified by DEDUP-02/03/04 tests | N/A |
| DEDUP-02 | Metric homes correct | smoke | Render HTML, grep for metric values per section | Wave 0 |
| DEDUP-03 | Header bar has MCap/Revenue/Price/Employees | unit | `uv run pytest tests/stages/render/test_reading_paths.py -x` (after update) | Exists (needs update) |
| DEDUP-04 | No redundant displays | smoke | Render HTML, count metric occurrences by section | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/render/ -x -q --timeout=30`
- **Per wave merge:** `uv run pytest --timeout=60`
- **Phase gate:** `grep -r "beta_report" src/ tests/ scripts/` returns 0 + full suite green

### Wave 0 Gaps
- [ ] `grep`-based smoke test for zero `beta_report` matches in src/tests/scripts
- [ ] Rendered HTML dedup assertion (count metric value occurrences per section ID)

## Complete File Inventory

### Files to Rename (git mv) -- 10 files

All paths relative to project root:

1. `src/do_uw/stages/render/context_builders/beta_report.py`
2. `src/do_uw/stages/render/context_builders/assembly_beta_report.py`
3. `src/do_uw/stages/render/context_builders/_beta_report_helpers.py`
4. `src/do_uw/stages/render/context_builders/_beta_report_investigative.py`
5. `src/do_uw/stages/render/context_builders/_beta_report_findings.py`
6. `src/do_uw/stages/render/context_builders/_beta_report_uw_metrics.py`
7. `src/do_uw/stages/render/context_builders/beta_report_sections.py`
8. `src/do_uw/stages/render/context_builders/beta_report_charts.py`
9. `src/do_uw/stages/render/context_builders/beta_report_infographics.py`
10. `src/do_uw/templates/html/sections/beta_report.html.j2`

### Files Needing String Replacement Only -- 13 files

1. `src/do_uw/stages/render/context_builders/assembly_registry.py` (9 occurrences)
2. `src/do_uw/templates/html/base.html.j2` (1 occurrence)
3. `src/do_uw/templates/html/worksheet.html.j2` (1 occurrence)
4. `scripts/qa_beta_report.py` (10+ occurrences -- also rename file to `qa_uw_analysis.py`)
5. `tests/stages/render/test_stage_banner_template.py` (12 occurrences)
6. `tests/stages/render/test_pipeline_status_wiring.py` (4 occurrences)
7. `tests/test_canonical_metrics.py` (4 occurrences)
8. `tests/stages/render/test_reading_paths.py` (2 occurrences)
9. `tests/brain/test_contract_enforcement.py` (1 occurrence)
10. `tests/brain/test_template_facet_audit.py` (1 occurrence)

### Files NOT to Rename (historical docs) -- ~20 files in .planning/

All `.planning/phases/*/` files, `MILESTONES.md`, `HANDOFF.json`, `PROJECT.md`, `ROADMAP.md`, `research/ARCHITECTURE.md` -- these are historical records.

## Open Questions

1. **qa_beta_report.py -- rename file too?**
   - What we know: Script contains `beta_report` in filename and 10+ internal references. HTML looks for `id="beta-report"`.
   - What's unclear: User didn't explicitly mention this script in D-02 (which focused on `src/` files).
   - Recommendation: Rename to `qa_uw_analysis.py` for consistency. Update `id="beta-report"` to `id="uw-analysis"` in template.

2. **key_stats.html.j2 stock price panel -- remove or keep?**
   - What we know: Lines 143-170 show stock price with range visualization. Home = Stock & Market per D-05.
   - What's unclear: Key Stats is a unique overview section -- removing the price panel changes its utility.
   - Recommendation: Remove per D-07 (no cross-references). Stock & Market section has the full treatment.

3. **Page-0 Dashboard revenue card -- remove or keep?**
   - What we know: Card 3 shows Revenue & Growth with sparkline. D-05 says Revenue home = Financial.
   - What's unclear: Page-0 is the Decision Dashboard. D-06 says header bar is the ONLY allowed duplicate. But D-05 says MCap home = Decision Dashboard.
   - Recommendation: Revenue card on Page-0 provides growth context (sparkline, EV/Revenue) beyond the headline number. This is analytical content, not pure duplication. Keep it. The header bar shows the bare number; Page-0 shows the analytical card. If strict interpretation of D-07 requires removal, flag for user confirmation.

## Sources

### Primary (HIGH confidence)
- Direct codebase grep: `beta_report` across all files -- 318 total occurrences, 55 files
- Direct file inspection: assembly_registry.py, assembly_beta_report.py, beta_report.html.j2, worksheet.html.j2, base.html.j2
- Template grep: revenue (157 occurrences/43 files), market_cap (44/22), stock_price (23/15), board_size (13/5)

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions from user discussion session

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, pure rename + template edits
- Architecture: HIGH -- all files identified, import graph traced, context flow mapped
- Pitfalls: HIGH -- based on direct code inspection of cross-imports and string references

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable -- internal codebase refactor, no external dependencies)
