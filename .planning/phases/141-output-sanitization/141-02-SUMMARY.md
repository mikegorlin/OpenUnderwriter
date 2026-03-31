---
phase: 141-output-sanitization
plan: 02
subsystem: render
tags: [sanitization, html-renderer, integration, post-render, safety-net]

requires:
  - phase: 141-output-sanitization
    plan: 01
    provides: OutputSanitizer class with from_defaults() and sanitize() methods
provides:
  - OutputSanitizer wired into render_html_pdf at both HTML write points
  - Sanitization log written to output directory when substitutions found
  - Integration tests verifying sanitizer is called during render
affects: [render-pipeline, html-output, pdf-output]

tech-stack:
  added: []
  patterns: [post-render sanitization at write boundary, dual-path sanitization (browser + PDF)]

key-files:
  created:
    - tests/stages/render/test_html_renderer_sanitizer.py
  modified:
    - src/do_uw/stages/render/html_renderer.py

key-decisions:
  - "Sanitizer instantiated once in render_html_pdf and reused for both browser and PDF HTML"
  - "Sanitization log uses output_path.stem + '_sanitization_log.txt' naming convention"
  - "Existing Jinja filters preserved as first-line defense; sanitizer is safety net only"

patterns-established:
  - "Post-render sanitization at the write boundary: sanitize HTML between template render and disk write"

requirements-completed: [SAN-01, SAN-02, SAN-03, SAN-04, SAN-05]

duration: 2min
completed: 2026-03-28
---

# Phase 141 Plan 02: Wire OutputSanitizer into HTML Renderer Summary

**OutputSanitizer integrated into render_html_pdf as post-render safety net, sanitizing both browser and PDF HTML before write with log output**

## What Was Done

### Task 1: Wire OutputSanitizer into render_html_pdf
- Added `OutputSanitizer` import to html_renderer.py
- After `_render_html_template()` call, sanitizer processes browser HTML before disk write
- After `_build_pdf_html()` call, sanitizer processes PDF HTML before Playwright
- Sanitization log written to `{ticker}_worksheet_sanitization_log.txt` when substitutions found
- Existing Jinja filters (strip_md, strip_jargon, clean_narrative) remain unchanged

### Task 2: Integration Tests (TDD)
- 4 integration tests verifying sanitizer wiring:
  - `test_browser_html_is_sanitized` — confirms markdown/jargon removed from written HTML
  - `test_pdf_html_is_sanitized` — confirms sanitize() called twice (browser + PDF)
  - `test_log_file_created_when_dirty` — confirms log file written when substitutions found
  - `test_no_log_file_when_clean` — confirms no log file when HTML is clean

## Verification Results

- All 4 new integration tests pass
- All 37 sanitizer tests (unit + integration) pass together
- 1 pre-existing failure in test_119_integration.py (unrelated: stock_catalyst_context import check)
- Import verification and ruff lint clean (pre-existing I001 import sort issue in file)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | e2d0cc9e | feat(141-02): wire OutputSanitizer into render_html_pdf |
| 2 | 593f0d8f | test(141-02): add integration tests for sanitizer wiring |

## Self-Check: PASSED
