# Phase 16 Plan 01: Rebrand Liberty Mutual to Angry Dolphin Summary

**One-liner:** Replaced all Liberty Mutual references and --lm- CSS variable prefixes with Angry Dolphin branding and --ad- prefix across 16 source files

## Metadata

- **Phase:** 16 (Program Identity & Polish)
- **Plan:** 01
- **Subsystem:** UI/Branding (design system, dashboard, templates, CSS)
- **Duration:** 3m 30s
- **Completed:** 2026-02-10

## What Was Done

### Task 1: Replace Liberty Mutual references with Angry Dolphin in all source code comments and CSS variables

Executed a comprehensive branding rename across 16 files:

**Part A - Code comments (7 files):**
- `design_system.py`: "Liberty Mutual brand colors" -> "Angry Dolphin brand colors", "Liberty Blue" -> "AD Navy", "Liberty Yellow" -> "AD Gold", "Liberty Mutual branding" -> "Angry Dolphin branding"
- `design.py`: "Liberty Mutual brand colors" -> "Angry Dolphin brand colors", "Liberty Mutual brand" -> "Angry Dolphin brand"
- `charts.py`: "Liberty Mutual brand colors" -> "Angry Dolphin brand colors"
- `charts_financial.py`: "Liberty Mutual brand colors" -> "Angry Dolphin brand colors"
- `docx_helpers.py`: "Liberty Gold" -> "AD Gold"
- `pdf_renderer.py`: "Liberty Mutual branding" -> "Angry Dolphin branding"
- `dashboard.css`: "Liberty Mutual branding" -> "Angry Dolphin branding"

**Part B - CSS variable prefix rename (16 files):**
- `design.py`: CSS_VARIABLES dict keys `--lm-*` -> `--ad-*`
- `base.html`: `:root` declarations and all `var()` references
- `dashboard.css`: `[data-theme="lm"]` -> `[data-theme="ad"]`, all `var()` references
- `index.html`, `section.html`, and 6 partials: all `var(--lm-*)` -> `var(--ad-*)`

**Commit:** 9f4f395

### Task 2: Update test assertions and verify full test suite passes

- Verified no test files reference `--lm-` or Liberty Mutual
- All 1892 tests pass
- Zero ruff errors in src/
- Zero pyright type errors
- No code changes needed in tests (assertions already used "Angry Dolphin")

## Verification Results

| Check | Result |
|-------|--------|
| `grep -rn "Liberty" src/` (text files) | 0 matches |
| `grep -rn "--lm-" src/` | 0 matches |
| `grep -rn 'data-theme="lm"' src/` | 0 matches |
| `grep -rn "Angry Dolphin" src/` | 33 matches |
| `grep -rn "--ad-navy" src/` | 29 matches |
| `pytest tests/ -x -q` | 1892 passed |
| `ruff check src/` | All checks passed |
| `pyright src/` | 0 errors |

## Deviations from Plan

None -- plan executed exactly as written.

## Decisions Made

- Binary file `knowledge.db` contains "Liberty" in stored data but is a SQLite database cache, not source code. Not modified.
- Color values (#1A1446, #FFD000, etc.) intentionally preserved -- only variable names and comments changed.

## Files Modified

### Created
(none)

### Modified
- `src/do_uw/stages/render/design_system.py` - Brand color comments
- `src/do_uw/dashboard/design.py` - CSS_VARIABLES dict keys
- `src/do_uw/dashboard/charts.py` - Brand color comment
- `src/do_uw/dashboard/charts_financial.py` - Brand color comment
- `src/do_uw/stages/render/docx_helpers.py` - Color comment
- `src/do_uw/stages/render/pdf_renderer.py` - Docstring
- `src/do_uw/static/css/dashboard.css` - Theme selector, CSS var references, comments
- `src/do_uw/templates/dashboard/base.html` - data-theme, CSS var declarations and references
- `src/do_uw/templates/dashboard/index.html` - CSS var references
- `src/do_uw/templates/dashboard/section.html` - CSS var references
- `src/do_uw/templates/dashboard/partials/_peer_comparison.html` - CSS var references
- `src/do_uw/templates/dashboard/partials/_meeting_prep.html` - CSS var references
- `src/do_uw/templates/dashboard/partials/_chart_container.html` - CSS var references
- `src/do_uw/templates/dashboard/partials/_summary_card.html` - CSS var references
- `src/do_uw/templates/dashboard/partials/_finding_detail.html` - CSS var references
- `src/do_uw/templates/dashboard/partials/_factor_detail.html` - CSS var references

## Next Phase Readiness

Plan 16-02 can proceed. All branding is now consistent with "Angry Dolphin" identity.
