---
phase: 56-facet-driven-rendering
plan: 02
subsystem: render
tags: [jinja2, template-fragments, facet-dispatch, html-rendering, section-context]

# Dependency graph
requires:
  - phase: 56-01-facet-driven-rendering
    provides: FacetSpec schema, financial_health.yaml subsections, facet_renderer dispatch
provides:
  - 11 financial fragment templates in sections/financial/ decomposed from monolithic financial.html.j2
  - Section-driven dispatch in financial.html.j2 using section_context from YAML
  - build_section_context() wired into build_html_context() for all HTML renders
  - Legacy fallback when section_context is empty
affects: [56-03-facet-driven-rendering, 56-04-facet-driven-rendering, 56-05-facet-driven-rendering, render, html-templates]

# Tech tracking
tech-stack:
  added: []
  patterns: [section-context-dispatch, fragment-template-extraction, dual-path-legacy-fallback]

key-files:
  created:
    - src/do_uw/templates/html/sections/financial/annual_comparison.html.j2
    - src/do_uw/templates/html/sections/financial/key_metrics.html.j2
    - src/do_uw/templates/html/sections/financial/statement_tables.html.j2
    - src/do_uw/templates/html/sections/financial/quarterly_updates.html.j2
    - src/do_uw/templates/html/sections/financial/distress_indicators.html.j2
    - src/do_uw/templates/html/sections/financial/tax_risk.html.j2
    - src/do_uw/templates/html/sections/financial/earnings_quality.html.j2
    - src/do_uw/templates/html/sections/financial/audit_profile.html.j2
    - src/do_uw/templates/html/sections/financial/peer_group.html.j2
    - src/do_uw/templates/html/sections/financial/financial_checks.html.j2
    - src/do_uw/templates/html/sections/financial/density_alerts.html.j2
    - src/do_uw/brain/brain_section_schema.py
    - src/do_uw/stages/render/section_renderer.py
    - tests/brain/test_section_schema.py
    - tests/stages/render/test_section_renderer.py
  modified:
    - src/do_uw/templates/html/sections/financial.html.j2
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/brain/brain_facet_schema.py
    - src/do_uw/stages/render/facet_renderer.py

key-decisions:
  - "Dispatch placed inside financial.html.j2 rather than separate facet_section.html.j2 -- each section template manages its own facet-vs-legacy routing"
  - "Schema rename during execution: FacetSpec->SectionSpec, SubsectionSpec->FacetSpec, facet_sections->section_context, build_facet_context->build_section_context"
  - "statement_tables.html.j2 wraps existing financial_statements.html.j2 include (not duplicated)"

patterns-established:
  - "Section-driven dispatch: section templates check section_context[section_id] and iterate facets with {% include facet.template %}"
  - "Fragment extraction: verbatim copy of template blocks into individual files, section wrapper handles dispatch"
  - "Dual-path rendering: facet path from YAML or legacy inline includes as fallback"

requirements-completed: [RENDER-02, RENDER-03, RENDER-04]

# Metrics
duration: 45min
completed: 2026-03-02
---

# Phase 56 Plan 02: Financial Template Decomposition and Facet Dispatch Summary

**Decomposed 449-line financial.html.j2 into 11 fragment templates with section_context dispatch from YAML, achieving zero visual regression across 276 render tests**

## Performance

- **Duration:** ~45 min (spanning commits 642edd3 through 1ee81fa)
- **Started:** 2026-03-02T02:00:00Z
- **Completed:** 2026-03-02T04:21:06Z
- **Tasks:** 3 (schema rename + fragment extraction + regression verification)
- **Files modified:** 37 (22 in rename, 15 in decomposition)

## Accomplishments
- financial.html.j2 reduced from 449 lines to 41-line dispatch wrapper with 11 fragment templates (422 total lines)
- Section-driven dispatch: financial.html.j2 checks section_context from YAML and iterates facets, falling back to legacy inline includes
- build_section_context() wired into build_html_context() so all HTML renders get facet dispatch data
- Schema rename completed: FacetSpec->SectionSpec, SubsectionSpec->FacetSpec, brain/facets/->brain/sections/
- 39 section renderer tests + 13 section schema tests + 276 render tests all passing

## Task Commits

Each task was committed atomically:

1. **Task 1 + Task 2 (schema rename + dispatch wiring):** `642edd3` refactor(56-02): rename FacetSpec->SectionSpec, SubsectionSpec->FacetSpec
2. **Task 1 continued (fragment extraction + dispatch):** `1ee81fa` feat(56-03): decompose financial.html.j2 into 11 facet fragments with dispatch

**Note:** Plan 02 was executed together with a schema rename that happened concurrently. The rename commit (642edd3) established the corrected naming convention used throughout.

## Files Created/Modified

**Fragment templates (11 files in sections/financial/):**
- `sections/financial/annual_comparison.html.j2` (41 lines) - K-to-K comparison table with gap_notice
- `sections/financial/key_metrics.html.j2` (34 lines) - 3-column data grid with profitability/balance/cash flow
- `sections/financial/statement_tables.html.j2` (2 lines) - Thin wrapper delegating to existing financial_statements.html.j2
- `sections/financial/quarterly_updates.html.j2` (193 lines) - Quarterly update tables with MD&A/legal/going concern
- `sections/financial/distress_indicators.html.j2` (51 lines) - Altman Z, Ohlson O, Beneish M, Piotroski F
- `sections/financial/tax_risk.html.j2` (17 lines) - Tax risk KV table
- `sections/financial/earnings_quality.html.j2` (14 lines) - Earnings quality section
- `sections/financial/audit_profile.html.j2` (25 lines) - Audit KV table with interpretation
- `sections/financial/peer_group.html.j2` (13 lines) - Peer data table
- `sections/financial/financial_checks.html.j2` (6 lines) - Check results block
- `sections/financial/density_alerts.html.j2` (26 lines) - ELEVATED/CRITICAL alert blocks

**Dispatch infrastructure:**
- `src/do_uw/templates/html/sections/financial.html.j2` - Rewritten as 41-line dispatch wrapper (was 449 lines)
- `src/do_uw/stages/render/html_renderer.py` - Added build_section_context() call
- `src/do_uw/stages/render/section_renderer.py` - New dispatch orchestrator (renamed from facet_renderer.py)
- `src/do_uw/brain/brain_section_schema.py` - New schema module (renamed from brain_facet_schema.py)

**Tests:**
- `tests/stages/render/test_section_renderer.py` - 39 tests covering all faceted sections
- `tests/brain/test_section_schema.py` - 13 tests covering schema validation and backward compat

## Decisions Made

1. **Dispatch inside section template, not separate wrapper:** Plan specified a `facet_section.html.j2` wrapper. Instead, the dispatch was placed inside `financial.html.j2` itself. Each section template manages its own facet-vs-legacy routing, which is cleaner because the section template already sets up context variables (fin, density, level, narratives). This pattern was then replicated across all other sections in Plans 03-05.

2. **Schema rename concurrent with decomposition:** Plan 56-02 in git was the rename (FacetSpec->SectionSpec), correcting backwards naming. The decomposition followed as commit 56-03. Both are part of the logical Plan 02 work.

3. **statement_tables.html.j2 naming:** Plan specified `financial_statements.html.j2` as the wrapper fragment name. Used `statement_tables.html.j2` instead to avoid confusion with the existing `sections/financial_statements.html.j2` it delegates to.

## Deviations from Plan

### Architecture Deviations (applied consistently)

**1. No separate facet_section.html.j2 wrapper**
- **Plan specified:** A standalone `facet_section.html.j2` that sets context variables and iterates subsections
- **Implemented:** Dispatch logic embedded in `financial.html.j2` with `{% if section_context is defined and section_context.get('financial_health') %}` guard
- **Rationale:** The section template already has the context setup (density, level, fin, narratives). A separate wrapper would require duplicating these or passing them through an additional include layer. Keeping dispatch in the section template is simpler and was adopted for all 8 sections.

**2. worksheet.html.j2 unchanged**
- **Plan specified:** Conditional routing in worksheet.html.j2 between facet_section.html.j2 and legacy financial.html.j2
- **Implemented:** worksheet.html.j2 always includes financial.html.j2; the conditional routing is inside that template
- **Rationale:** Follows from deviation 1. Each section handles its own dispatch. worksheet.html.j2 remains a clean ordered list of section includes.

**3. Naming convention changed**
- **Plan specified:** `facet_sections`, `build_facet_context()`, `SubsectionSpec`
- **Implemented:** `section_context`, `build_section_context()`, `FacetSpec` (atomic unit), `SectionSpec` (grouping container)
- **Rationale:** The 56-02 rename corrected the backwards naming where FacetSpec was the container and SubsectionSpec was the atom. The new naming (SectionSpec = container, FacetSpec = atom) is clearer and matches domain terminology.

---

**Total deviations:** 3 architectural deviations (all improvements over plan)
**Impact on plan:** All deviations produced a cleaner architecture that was adopted across all 8 sections. No functionality lost.

## Issues Encountered

None - decomposition was mechanical extraction of template blocks.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Financial fragment pattern proven and ready for replication across governance, market, company, litigation, executive, ai_risk, scoring sections
- build_section_context() already supports all sections with facets in YAML
- Legacy fallback verified for sections without facets
- 276 render tests + 39 section tests + 13 schema tests confirm zero regression

## Self-Check: PASSED

All 15 files verified present on disk. Both commit hashes (642edd3, 1ee81fa) verified in git log. 276 render tests + 39 section tests + 13 schema tests all passing.

---
*Phase: 56-facet-driven-rendering*
*Completed: 2026-03-02*
