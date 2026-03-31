---
phase: 08-document-rendering-visualization
plan: 01
subsystem: render
tags: [python-docx, matplotlib, word-generation, design-system, charts, branding]

# Dependency graph
requires:
  - phase: 07-peer-benchmarking-executive-summary
    provides: "Complete AnalysisState with SECT1-SECT7 data for rendering"
provides:
  - "DesignSystem with Liberty Mutual branding (navy/gold, no green risk spectrum)"
  - "docx_helpers for styled tables, cell shading, page numbers, TOC, borders"
  - "chart_helpers for matplotlib-to-BytesIO pipeline and radar charts"
  - "word_renderer document assembly with section renderer dispatch"
  - "formatters for currency, percentage, compact numbers, citations"
  - "RenderStage with output_dir passthrough from Pipeline"
affects:
  - "08-02 (section renderers use design_system, docx_helpers, chart_helpers, formatters)"
  - "08-03 (section renderers use same shared utilities)"
  - "08-04 (output formats build on word_renderer)"

# Tech tracking
tech-stack:
  added: ["python-docx>=1.1.0", "matplotlib>=3.9.0", "jinja2>=3.1.0", "weasyprint>=60.0 (optional pdf group)"]
  patterns:
    - "Any-typed python-docx API access (untyped library with pyright strict)"
    - "_oxml() helper wrapping OxmlElement with cast(Any) for type safety"
    - "Frozen dataclass DesignSystem with RUF009 per-file ignore"
    - "Section renderer dispatch with try/except ImportError fallback"
    - "matplotlib Agg backend for headless chart generation"

key-files:
  created:
    - "src/do_uw/stages/render/design_system.py"
    - "src/do_uw/stages/render/formatters.py"
    - "src/do_uw/stages/render/docx_helpers.py"
    - "src/do_uw/stages/render/chart_helpers.py"
    - "src/do_uw/stages/render/word_renderer.py"
    - "src/do_uw/stages/render/sections/__init__.py"
    - "tests/test_render_framework.py"
  modified:
    - "pyproject.toml"
    - "ruff.toml"
    - "src/do_uw/stages/render/__init__.py"
    - "src/do_uw/pipeline.py"

key-decisions:
  - "Any-typed python-docx API: doc, styles, paragraphs all typed as Any for pyright strict"
  - "_oxml() helper: cast(Any, OxmlElement(tag)) to wrap untyped xml element creation"
  - "RUF009 per-file ignore for design_system.py: frozen dataclass with immutable Pt/Inches/RGBColor defaults"
  - "Section renderer dispatch via importlib with None fallback for not-yet-implemented sections"
  - "pyright: ignore[reportUnknownMemberType] for matplotlib.pyplot partially-unknown overloads"
  - "legal_name field (not name) on CompanyIdentity for company name resolution"

patterns-established:
  - "_oxml() pattern: all OxmlElement creation goes through cast(Any) helper"
  - "Section renderer protocol: render_section_N(doc, state, ds) -> None"
  - "Design system singleton: DesignSystem() frozen dataclass for all visual constants"
  - "Chart pipeline: create_figure -> plot -> save_chart_to_bytes -> embed_chart"

# Metrics
duration: 10min
completed: 2026-02-09
---

# Phase 8 Plan 01: Render Stage Framework Summary

**RENDER stage framework with Liberty Mutual design system, python-docx/matplotlib helpers, Word document assembly, and 59 tests**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-09T00:43:21Z
- **Completed:** 2026-02-09T00:53:22Z
- **Tasks:** 2/2
- **Tests added:** 59 (total: 1033)
- **Files created/modified:** 11

## Accomplishments
- Design system with Liberty Mutual branding (#1A1446 navy, #FFD000 gold), risk heat spectrum (no green), Georgia/Calibri typography
- Full docx helper suite: styled tables, cell shading, page numbers, TOC field, sourced paragraphs, risk indicators, border control
- Chart pipeline: matplotlib-to-BytesIO with radar/spider chart for 10-factor scoring visualization
- Word document assembly orchestrator with section renderer dispatch and graceful fallback for unimplemented sections
- RenderStage wired into Pipeline with output_dir passthrough
- Formatters for currency ($1.2B compact), percentages, dates, SourcedValue citations

## Task Commits

Each task was committed atomically:

1. **Task 1: Install dependencies and create design system + formatters** - `a0ae9f2` (feat)
2. **Task 2: Create docx helpers, chart helpers, word renderer, and RenderStage** - `0a4e871` (feat)

## Files Created/Modified
- `pyproject.toml` - Added python-docx, matplotlib, jinja2 deps; WeasyPrint optional pdf group
- `ruff.toml` - RUF009 per-file ignore for design_system.py frozen dataclass defaults
- `src/do_uw/stages/render/design_system.py` - Visual constants, custom styles, risk colors, matplotlib config
- `src/do_uw/stages/render/formatters.py` - Currency, percentage, compact number, date, citation formatters
- `src/do_uw/stages/render/docx_helpers.py` - Table creation, cell shading, page numbers, TOC, borders
- `src/do_uw/stages/render/chart_helpers.py` - Figure creation, BytesIO pipeline, radar chart, chart styling
- `src/do_uw/stages/render/word_renderer.py` - Document assembly, section dispatch, header/footer, margins
- `src/do_uw/stages/render/__init__.py` - RenderStage with output_dir, replaces Phase 1 stub
- `src/do_uw/stages/render/sections/__init__.py` - Empty package for section renderers (Plans 02-03)
- `src/do_uw/pipeline.py` - Pass output_dir to RenderStage in _build_default_stages
- `tests/test_render_framework.py` - 59 tests covering all render framework components

## Decisions Made
- **Any-typed python-docx API**: python-docx is fully untyped; all doc/style/paragraph variables typed as `Any` for pyright strict compliance
- **_oxml() helper**: Wraps `OxmlElement(tag)` with `cast(Any, ...)` to avoid `BaseOxmlElement | Unknown` type propagation
- **RUF009 per-file ignore**: DesignSystem uses `Pt()`, `Inches()`, `RGBColor()` in frozen dataclass defaults -- immutable and safe
- **Section renderer dispatch via importlib**: `_try_import_renderer()` returns None for not-yet-implemented sections, which get placeholder paragraphs
- **matplotlib pyright ignores**: `plt.subplots()` and `plt.figure()` have `**kwargs: Unknown` in stubs, requiring targeted `pyright: ignore` comments
- **CompanyIdentity.legal_name**: Field is `legal_name` not `name` -- resolved during implementation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed CompanyIdentity field name**
- **Found during:** Task 2 (word_renderer.py)
- **Issue:** Plan referenced `state.company.identity.name` but field is `legal_name` on CompanyIdentity model
- **Fix:** Changed to `state.company.identity.legal_name`
- **Files modified:** src/do_uw/stages/render/word_renderer.py
- **Verification:** pyright passes, tests pass
- **Committed in:** 0a4e871 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Trivial field name correction. No scope creep.

## Issues Encountered
- python-docx and matplotlib are untyped libraries requiring extensive `Any` annotations and `type: ignore[import-untyped]` for pyright strict mode. Established `_oxml()` pattern to keep OxmlElement usage clean.
- ruff RUF009 flags function calls in dataclass defaults (Pt, Inches, RGBColor) -- resolved with per-file ignore since these are immutable value types.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- All shared render utilities ready for section renderers (Plans 02-03)
- Design system, docx_helpers, chart_helpers, formatters all tested and pyright-clean
- Section renderer protocol established: `render_section_N(doc, state, ds) -> None`
- word_renderer dispatches to sections via importlib with placeholder fallback
- No blockers for Plans 02-04

---
*Phase: 08-document-rendering-visualization*
*Completed: 2026-02-09*
