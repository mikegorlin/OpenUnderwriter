---
phase: "65"
plan: "03"
subsystem: render
tags: [narrative, scr, d-and-o, templates, html]
dependency_graph:
  requires: [Phase 61, Phase 62]
  provides: [SCR framework, D&O implications callout]
  affects: [html_renderer, section templates, context_builders]
tech_stack:
  added: []
  patterns: [SCR narrative framework, D&O implications mapping]
key_files:
  created:
    - src/do_uw/stages/render/context_builders/narrative.py
    - tests/stages/render/test_narrative_context.py
  modified:
    - src/do_uw/templates/html/components/callouts.html.j2
    - src/do_uw/templates/html/base.html.j2
    - src/do_uw/templates/html/components.css
    - src/do_uw/stages/render/context_builders/__init__.py
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/sections/executive.html.j2
    - src/do_uw/templates/html/sections/company.html.j2
    - src/do_uw/templates/html/sections/financial.html.j2
    - src/do_uw/templates/html/sections/governance.html.j2
    - src/do_uw/templates/html/sections/litigation.html.j2
    - src/do_uw/templates/html/sections/market.html.j2
    - src/do_uw/templates/html/sections/scoring.html.j2
    - src/do_uw/templates/html/sections/ai_risk.html.j2
decisions:
  - SCR framework uses density levels + pre-computed narratives to auto-derive situation/complication/resolution per section
  - D&O implications use signal condition checks mapping to coverage-relevant observations with severity levels
  - Template context variable named do_implications_data to avoid collision with do_implications macro name
  - Template keys mapped from brain IDs (business_profile->company, financial_health->financial, market_activity->market)
metrics:
  duration: 563s
  completed: "2026-03-03T04:38:00Z"
  tasks_completed: 4
  tasks_total: 4
  files_created: 2
  files_modified: 13
  tests_added: 13
---

# Phase 65 Plan 03: SCR Framework + D&O Implications Callout Boxes Summary

SCR (Situation-Complication-Resolution) analytical framework and D&O-specific implications callout boxes added to all 8 HTML section templates with auto-derived context from density/signal analysis.

## Tasks Completed

### Task 1: SCR + D&O Implications Jinja2 Macros
- Added `scr_narrative(scr)` macro: 3-segment block with color-coded left borders (gray/amber/green) for S/C/R
- Added `do_implications(impl)` macro: navy-bordered callout with severity-colored items (HIGH=red, MEDIUM=amber, LOW=default)
- CSS in components.css (`.scr-block`, `.scr-segment`, `.do-implications`) with print-safe `break-inside: avoid`
- Both macros imported in base.html.j2

### Task 2: Narrative Context Builder
- Created `context_builders/narrative.py` (309 lines) with `extract_scr_narratives()` and `extract_do_implications()`
- SCR derives from density levels and pre-computed narrative text: Situation=baseline, Complication=risk level, Resolution=first 2 sentences of narrative (capped at 300 chars)
- D&O implications use 28 condition checks across 8 sections mapping signals to coverage-relevant observations
- Per-section coverage notes for underwriting guidance
- Integrated into `build_html_context()` via top-level imports

### Task 3: Section Template Updates
- All 8 section templates (executive, company, financial, governance, litigation, market, scoring, ai_risk) updated
- SCR block appears after section heading, before pre-computed narrative
- D&O implications appears after narrative, before facet content
- All guarded by `is defined` checks for graceful degradation

### Task 4: Tests
- 13 tests: 6 for SCR narratives, 7 for D&O implications
- Tests cover empty state, elevated/critical density, template key mapping, resolution cap, signal triggers, coverage notes
- All 381 render tests pass (no regressions)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Template key mapping mismatch**
- **Found during:** Task 3
- **Issue:** Brain section IDs (business_profile, financial_health, market_activity) don't match template narrative attribute names (company, financial, market)
- **Fix:** Added `_TEMPLATE_KEYS` mapping dict, used by both extract functions and `_get_narrative_text()`
- **Files modified:** narrative.py
- **Commit:** d92ca4f

**2. [Rule 1 - Bug] Macro/variable name collision**
- **Found during:** Task 3
- **Issue:** Context variable `do_implications` would shadow the Jinja2 macro of the same name
- **Fix:** Renamed context variable to `do_implications_data`
- **Files modified:** html_renderer.py, all 8 section templates
- **Commit:** 5350bfb

## Out of Scope

- html_renderer.py was already 521 lines (over 500-line limit) before this plan. This plan added 8 net lines (to 529). Pre-existing condition not addressed per scope rules.
