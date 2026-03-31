---
phase: 43-html-presentation-quality-capiq-layout-data-tracing
plan: "01"
subsystem: render/html-templates
tags: [layout, css-grid, sidebar, navigation, topbar, capiq, jinja2]

dependency_graph:
  requires: []
  provides:
    - Two-column CapIQ layout shell in base.html.j2
    - Sticky sidebar TOC with 9 section anchor links
    - Identity-only sticky topbar (name/ticker/sector/market cap/date)
    - IntersectionObserver active-section tracking
    - sidebar.css with grid + sidebar CSS
  affects:
    - All HTML section templates (rendered inside .worksheet-main)
    - PDF output (sidebar hidden via @media print)

tech_stack:
  added:
    - sidebar.css (new file — CSS Grid + sidebar TOC, split from styles.css per 500-line rule)
  patterns:
    - CSS Grid two-column layout (180px sidebar + 1fr main)
    - IntersectionObserver for active-section tracking (vanilla JS, no dependencies)
    - @media print sidebar suppression

key_files:
  modified:
    - src/do_uw/templates/html/base.html.j2
  created:
    - src/do_uw/templates/html/sidebar.css

decisions:
  - sidebar.css created as separate file because styles.css was at 491 lines — adding 60+ lines of sidebar CSS would exceed 500-line limit from CLAUDE.md anti-context-rot rule

metrics:
  duration: "~12 minutes"
  completed: "2026-02-25"
  tasks_completed: 2
  files_modified: 2
  files_created: 1
  tests_passing: 217
---

# Phase 43 Plan 01: CapIQ Two-Column Layout Shell Summary

**One-liner:** Two-column CSS Grid layout (180px sticky sidebar TOC + main content) with identity-only topbar (name/ticker/sector/market cap), IntersectionObserver active-section tracking, and @media print sidebar suppression.

## What Was Built

### Task 1: Strip Sticky Topbar to Identity-Only

Modified the `<nav class="sticky-topbar">` block in `base.html.j2` to remove:
- `.sticky-topbar-center` div (tier badge, quality score, composite score)
- `.sticky-topbar-right` tier action text
- The `<header class="bg-navy">` block (company name duplication)
- The `.sticky-topbar-details` row (employees, industry — redundant)

The topbar now shows only: company name | ticker | sector | market cap | date.
The `sector` and `market_cap` fields appear inline in `.sticky-topbar-left` using new `.sticky-topbar-sep` and `.sticky-topbar-meta` CSS classes in sidebar.css.

### Task 2: Two-Column Layout + Sidebar TOC + IntersectionObserver

**sidebar.css** (new file, 81 lines): Contains all sidebar and grid CSS:
- `.worksheet-layout { display: grid; grid-template-columns: 180px 1fr; }`
- `.sidebar-toc` sticky positioning, height 100vh, background #f8fafc
- `.sidebar-toc a` and `.sidebar-toc a.active` styling with border-left highlight
- `.worksheet-main { min-width: 0; }` prevents grid blowout on wide tables
- `@media print` rules: hides sidebar, reverts layout to `display: block`
- `.sticky-topbar-sep` and `.sticky-topbar-meta` classes for topbar identity row

**base.html.j2** changes:
- Added `<style>{% include "sidebar.css" %}</style>` in `<head>`
- Replaced `<main class="px-8 max-w-none">` with two-column `.worksheet-layout` grid
- Added `<nav class="sidebar-toc">` with 9 section anchor links (identity → sources)
- Wrapped `{% block content %}` in `<main class="worksheet-main">`
- Added IntersectionObserver `<script>` before `</body>` for active-section tracking

**IntersectionObserver:** Vanilla JS, no dependencies, placed at end of body (no DOMContentLoaded needed). Uses `rootMargin: '-10% 0px -80% 0px'` to trigger highlight when section enters the top 20% of viewport. Adds/removes `.active` class on `.sidebar-toc a[href="#section-id"]` elements.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written with one implementation decision:

**Implementation decision: sidebar.css as separate file**

The plan stated: "If styles.css would exceed 500 lines, create `sidebar.css` and include it separately." `styles.css` was at 491 lines before this plan, so the sidebar CSS (81 lines) would push it to 572 lines — violating CLAUDE.md's 500-line rule. `sidebar.css` was created and included via `{% include "sidebar.css" %}` in a new `<style>` block in `base.html.j2`.

## Self-Check

### Created files exist:
- `src/do_uw/templates/html/sidebar.css` — FOUND (81 lines)
- `src/do_uw/templates/html/base.html.j2` — FOUND (modified)

### Commits exist:
- `8c681b8` — feat(43-01): strip sticky topbar to identity-only
- `27c87e4` — feat(43-01): add two-column CapIQ layout, sidebar TOC, IntersectionObserver

### Tests:
- `uv run pytest tests/stages/render/ -x -q` — 217 passed

## Self-Check: PASSED
