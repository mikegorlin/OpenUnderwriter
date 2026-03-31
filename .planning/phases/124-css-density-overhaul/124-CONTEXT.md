# Phase 124: CSS Density Overhaul - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary
Remove all table borders, use subtle lines. Minimal margins, compact spacing. Modern typography. Infographic-density presentation.
</domain>

<decisions>
## Implementation Decisions

### Table Design (NON-NEGOTIABLE per user)
- Remove ALL cell borders — no grid lines
- Navy header row (#0B1D3A), white text
- Subtle 1px bottom border on rows only (gray-200)
- Alternating row backgrounds: white / #F8FAFC
- Compact padding: p-1 on cells (was p-2/p-3)

### Typography
- Section headers: normal case (not uppercase), 1.125rem, weight 600
- Tabular-nums on ALL numeric columns
- Monospace for financial data

### Spacing
- Minimal margins: 0.5rem sides
- Compact section gaps
- Maximize data-ink ratio — every pixel earns its place

### Risk Colors
- Critical: #DC2626 (brighter red)
- Elevated: #EA580C (brighter amber)
- Watch: #EAB308 (warning yellow)
- Positive: #2563EB (blue, no green per design rule)

### Boilerplate Elimination (FIX-03)
- grep for all known boilerplate patterns, eliminate remaining ones

### Claude's Discretion
- Exact spacing values for optimal density
- Which sections benefit from multi-column grid (Phase 125)
</decisions>

<canonical_refs>
## Canonical References
- `src/do_uw/templates/html/input.css` — Tailwind v4 theme
- `src/do_uw/stages/render/design_system.py` — Color/font/spacing config
- `src/do_uw/templates/html/styles.css` — Main stylesheet
</canonical_refs>

<deferred>
None
</deferred>

---
*Phase: 124-css-density-overhaul*
*Context gathered: 2026-03-21*
