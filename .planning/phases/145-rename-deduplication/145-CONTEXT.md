# Phase 145: Rename & Deduplication - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Rename all `beta_report` references to `uw_analysis` (code, files, templates, tests). Deduplicate cross-section metrics so each has one "home section" with full provenance — other sections remove redundant displays. Header bar keeps MCap/Revenue/Price/Employees as only allowed duplicates.

</domain>

<decisions>
## Implementation Decisions

### Rename Scope
- **D-01:** Rename `beta_report` → `uw_analysis` everywhere. User chose "Underwriting Analysis" as the conceptual name, `uw_analysis` as the code abbreviation.
- **D-02:** Rename ALL filenames too — `beta_report.py` → `uw_analysis.py`, `_beta_report_helpers.py` → `_uw_analysis_helpers.py`, `beta_report.html.j2` → `uw_analysis.html.j2`, etc. Full clean break.
- **D-03:** Template context variable changes: `beta_report` → `uw_analysis`. Templates use `b = uw_analysis` instead of `b = beta_report`.
- **D-04:** 10+ source files with `beta_report` in filename, 7 Python source files with references, 3 templates, 6 test files — all must be updated.

### Deduplication Strategy
- **D-05:** Home + header bar only. Revenue shows full context in Financial section ONLY. Market cap in Decision Dashboard ONLY. Stock price in Stock & Market ONLY. Board size in Governance ONLY.
- **D-06:** Header bar keeps MCap/Revenue/Price/Employees as persistent compact reference — these are the ONLY allowed cross-section duplicates (per DEDUP-03).
- **D-07:** All other mentions of these metrics in non-home sections are removed or replaced with layout space for section-specific content. No "See X section" cross-references — just remove.
- **D-08:** Revenue appears in 29 templates currently — significant reduction expected.

### Migration Safety
- **D-09:** Two-commit structure: Commit 1 = pure rename (git mv files + update all imports/references, no logic changes). Commit 2 = dedup pass (remove redundant metric displays from non-home sections).
- **D-10:** Separating rename from dedup makes it safe to bisect if something breaks.

### Claude's Discretion
- Order of file renames within the rename commit
- Whether to create temporary compatibility aliases during rename (probably not needed if done atomically)
- Which specific template blocks to remove vs keep during dedup (within home section rules above)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Files to Rename
- `src/do_uw/stages/render/context_builders/beta_report.py` — main context builder
- `src/do_uw/stages/render/context_builders/assembly_beta_report.py` — assembly module
- `src/do_uw/stages/render/context_builders/_beta_report_helpers.py` — helper functions
- `src/do_uw/stages/render/context_builders/_beta_report_investigative.py` — investigative helpers
- `src/do_uw/stages/render/context_builders/_beta_report_findings.py` — findings helpers
- `src/do_uw/stages/render/context_builders/_beta_report_uw_metrics.py` — UW metrics
- `src/do_uw/stages/render/context_builders/beta_report_sections.py` — section builders
- `src/do_uw/stages/render/context_builders/beta_report_charts.py` — chart builders
- `src/do_uw/stages/render/context_builders/beta_report_infographics.py` — infographics
- `src/do_uw/templates/html/sections/beta_report.html.j2` — main section template

### Assembly & Integration
- `src/do_uw/stages/render/context_builders/assembly_registry.py` — registers all context builders, references beta_report
- `src/do_uw/stages/render/__init__.py` — render stage entry point

### Requirements
- `.planning/REQUIREMENTS.md` — NAME-01, NAME-02, DEDUP-01 through DEDUP-04

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `CanonicalMetricsRegistry` (Phase 137) — already computes each metric once. Dedup aligns with this.
- `SectionCompletenessGate` (Phase 142) — can detect sections that become empty after dedup removal.

### Established Patterns
- Templates use `b = beta_report` at top then reference `b.fin`, `b.gov`, etc. — renaming the top-level key cascades naturally.
- Assembly registry calls builders in sequence — rename the function names and imports.

### Integration Points
- `assembly_registry.py` — central hub that calls all context builders
- `build_html_context()` in `__init__.py` — sets up the context dict with `beta_report` key
- All section templates that include `{% set b = beta_report %}`

</code_context>

<specifics>
## Specific Ideas

- User chose "Underwriting Analysis" as the product-facing name — this is what the report represents
- `uw_analysis` as the code abbreviation — professional, domain-appropriate, compact
- Revenue in 29 templates is the biggest dedup challenge — most will be removals

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 145-rename-deduplication*
*Context gathered: 2026-03-28*
