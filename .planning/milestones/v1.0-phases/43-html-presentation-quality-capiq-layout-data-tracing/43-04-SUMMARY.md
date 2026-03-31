---
phase: 43-html-presentation-quality-capiq-layout-data-tracing
plan: "04"
subsystem: render
tags: [footnotes, data-tracing, sources-appendix, html-renderer, split]
dependency_graph:
  requires: [43-03]
  provides: [footnote-registry, sources-appendix, data-tracing-infrastructure]
  affects: [html_renderer, financial-template, market-template]
tech_stack:
  added: [html_footnotes.py, html_narrative.py, html_checks.py]
  patterns: [FootnoteRegistry, build_footnote_registry, footnote_num template wiring]
key_files:
  created:
    - src/do_uw/stages/render/html_footnotes.py
    - src/do_uw/stages/render/html_narrative.py
    - src/do_uw/stages/render/html_checks.py
  modified:
    - src/do_uw/stages/render/html_renderer.py
    - src/do_uw/templates/html/appendices/sources.html.j2
    - src/do_uw/templates/html/sections/financial.html.j2
    - src/do_uw/templates/html/sections/market.html.j2
    - src/do_uw/templates/html/styles.css
decisions:
  - "Split html_renderer.py (707 lines) into three focused modules: html_footnotes.py (FootnoteRegistry), html_narrative.py (markdown/narrative processing), html_checks.py (check result processing) — renderer now 395 lines"
  - "FootnoteRegistry.register() returns 0 for empty/None source text — safe default, no superscript rendered"
  - "_format_trace_source (footnotes) replaces _format_filing_ref (renderer) — single definition in html_footnotes.py"
  - "Footnote numbers sourced via footnote_registry.get(source_key) in templates — returns 0 silently if source not registered"
metrics:
  duration: "6m 9s"
  completed_date: "2026-02-25"
  tasks: 2
  files: 7
---

# Phase 43 Plan 04: Footnote / Sources Data Tracing Infrastructure Summary

FootnoteRegistry class pre-collects all data source citations from AnalysisState before rendering, assigns sequential 1-based footnote numbers with deduplication, wired to Sources appendix (id="sources") and inline superscripts in financial/market data rows.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | FootnoteRegistry + build_html_context() wiring | 1942162 | html_footnotes.py, html_narrative.py, html_checks.py, html_renderer.py |
| 2 | sources.html.j2 numbered appendix + data_row wiring | 7ec9564 | sources.html.j2, styles.css, financial.html.j2, market.html.j2 |

## What Was Built

**FootnoteRegistry** (`html_footnotes.py`):
- `register(source_text) -> int`: Idempotent registration, returns 1-based number (0 for empty/None)
- `get(source_text) -> int`: Look up number for already-registered source
- `all_sources: list[tuple[int, str]]`: All sources as (number, text) pairs for appendix
- `__len__`: Count of registered unique sources

**build_footnote_registry(state)**: Walks `state.acquired_data.filing_documents` (form_type + filing_date) and `state.analysis.check_results` (trace_data_source), registers all unique sources.

**Template wiring in build_html_context()**:
```python
footnote_reg = build_footnote_registry(state)
context["footnote_registry"] = footnote_reg
context["all_sources"] = footnote_reg.all_sources
```

**sources.html.j2**: Renders numbered list with `<li id="fn-N">` anchors inside `<section id="sources">`. Guards with `{% if all_sources %}` — renders nothing when empty.

**financial.html.j2 / market.html.j2**: Wired `footnote_num=fin_fn` / `footnote_num=mkt_fn` to all `data_row` calls in the key metrics grids. Source key resolution uses `get()` (returns 0 if not found — no superscript).

## 500-Line Rule Enforcement

The plan required html_renderer.py to be under 500 lines (it was 707 lines). Split into:

| File | Lines | Content |
|------|-------|---------|
| `html_renderer.py` | 395 | Core renderer, build_html_context, Playwright/WeasyPrint |
| `html_footnotes.py` | 168 | FootnoteRegistry class, build_footnote_registry |
| `html_narrative.py` | 173 | _strip_markdown, _narratize, _extract_lead_phrase |
| `html_checks.py` | 155 | _group_checks_by_section, _compute_coverage_stats |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] _format_filing_ref duplicated between renderer and footnotes**
- **Found during:** Task 1
- **Issue:** Plan said to call `_format_filing_ref` from html_renderer in `build_footnote_registry`, but that function was being removed from the renderer as part of the split
- **Fix:** Renamed to `_format_trace_source` in html_footnotes.py (single definition), imported back into html_renderer.py for backward compatibility with _group_checks_by_section
- **Files modified:** html_footnotes.py, html_renderer.py, html_checks.py
- **Commit:** 1942162

**2. [Rule 2 - 500-line rule] html_renderer.py still 684 lines after first split**
- **Found during:** Task 1 verification
- **Issue:** After moving FootnoteRegistry to html_footnotes.py, renderer was still 684 lines (well above 500)
- **Fix:** Created html_narrative.py (narrative processing) and html_checks.py (check result processing) to bring renderer to 395 lines
- **Files modified:** html_narrative.py, html_checks.py, html_renderer.py
- **Commit:** 1942162

## Self-Check: PASSED

All created files verified:
- FOUND: src/do_uw/stages/render/html_footnotes.py
- FOUND: src/do_uw/stages/render/html_narrative.py
- FOUND: src/do_uw/stages/render/html_checks.py
- FOUND: src/do_uw/templates/html/appendices/sources.html.j2
- FOUND commit: 1942162 (Task 1)
- FOUND commit: 7ec9564 (Task 2)
