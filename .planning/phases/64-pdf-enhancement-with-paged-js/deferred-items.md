# Deferred Items - Phase 64

## Pre-existing Test Failures (Out of Scope)

### test_render_integration.py::TestAllFormatsRender::test_all_formats_render

- **Discovered during:** 64-01 Task 3 regression check
- **Root cause 1:** sect6_litigation.py line 86 -- `_read_density_clean()` receives a `DensityLevel` enum but calls `.level` on it (attribute doesn't exist on enum member)
- **Root cause 2:** scoring.md.j2 line 124 -- Deprecated Markdown template references `nlp_signals.readability` which doesn't exist in the dict
- **Impact:** Word renderer litigation section and Markdown scoring section fail for test fixture data
- **Verdict:** Pre-existing, unrelated to PDF CSS changes. Confirmed by running test against pre-change code.

### html_renderer.py line count at 522 (over 500-line limit)

- **Discovered during:** 64-02 Task 2
- **Root cause:** The file was at ~476 lines before 64-02. Addition of _optimize_chart_images_for_pdf (+34 lines) and concurrent SVG chart additions from Phase 63 (+6 lines) pushed it to 522.
- **Impact:** Minor violation of the 500-line anti-context-rot rule.
- **Recommended fix:** Extract `_optimize_chart_images_for_pdf` and `_fallback_weasyprint` into a pdf_helpers module, or extract the Playwright PDF path into its own module. Either approach would bring html_renderer.py well under 500 lines.
- **Verdict:** Deferred -- extracting functions now would be architectural scope creep for a PDF TOC plan.
