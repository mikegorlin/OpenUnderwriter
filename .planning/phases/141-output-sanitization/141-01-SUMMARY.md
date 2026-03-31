---
phase: 141-output-sanitization
plan: 01
subsystem: render
tags: [sanitization, html, regex, post-render, safety-net]

requires:
  - phase: 130-human-readability
    provides: pre-render jargon stripping in formatters.py
provides:
  - OutputSanitizer class for post-render HTML cleanup
  - SanitizationLog for upstream leak evidence
affects: [141-02, render-pipeline, html-output]

tech-stack:
  added: []
  patterns: [regex-based text extraction, pre-pass for tag-like debug patterns, category-ordered sanitization]

key-files:
  created:
    - src/do_uw/stages/render/output_sanitizer.py
    - tests/stages/render/test_output_sanitizer.py
  modified: []

key-decisions:
  - "Regex-based text extraction instead of HTMLParser/BeautifulSoup for robustness with malformed HTML and HTML entities"
  - "Pre-pass for debug patterns that resemble HTML tags (e.g., <class '...'>)"
  - "Independent re-implementation of patterns rather than importing existing pre-render filters"

patterns-established:
  - "Post-render sanitization: regex finds text between HTML tags, applies category-ordered substitutions"
  - "SanitizationLog as evidence trail: every substitution logged with category, pattern, match, and context"

requirements-completed: [SAN-01, SAN-02, SAN-03, SAN-04, SAN-05]

duration: 4min
completed: 2026-03-28
---

# Phase 141 Plan 01: Output Sanitizer Summary

**Post-render OutputSanitizer with 4-category HTML cleanup (markdown, Python serial, jargon, debug) and substitution logging for upstream fix evidence**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-28T04:19:37Z
- **Completed:** 2026-03-28T04:24:22Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Created OutputSanitizer class with sanitize() returning (cleaned_html, SanitizationLog) tuple
- 4 pattern categories: markdown (bold/italic/heading/hr/backtick), python_serial (list/dict repr, None/True/False), jargon (factor codes, threshold context, signal counts, known codes), debug (class/module repr, tracebacks)
- Regex-based text extraction skips script/style/code/pre tags and data-raw="true" elements
- 33 tests covering all categories, preservation rules, edge cases, and performance (500KB in < 2s)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create OutputSanitizer class with all pattern categories** - `8c62081f` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/output_sanitizer.py` - OutputSanitizer class with sanitize() method, SanitizationEntry/Log dataclasses, 4 pattern categories
- `tests/stages/render/test_output_sanitizer.py` - 33 tests across 6 test classes

## Decisions Made
- Used regex-based text node extraction (`_find_text_spans`) instead of HTMLParser because HTMLParser decodes `&lt;` to `<` which breaks tag detection in threshold patterns like `(threshold: Cash Ratio < 0.5)`
- Debug patterns that look like HTML tags (`<class '...'>`, `<module '...'>`) handled in a pre-pass before text extraction since the HTML tag regex consumes them
- Each pattern category is a separate method (`_apply_debug`, `_apply_python_serial`, `_apply_jargon`, `_apply_markdown`) for maintainability
- Categories applied in order: debug > python_serial > jargon > markdown (most specific first)
- Does NOT import existing strip_jargon/clean_narrative_text -- independent post-render implementation avoids coupling

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched from HTMLParser to regex-based text extraction**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** HTMLParser decodes HTML entities (e.g., `&lt;` to `<`) which then splits text nodes at unexpected points, causing threshold patterns to not match
- **Fix:** Replaced `_TextNodeExtractor(HTMLParser)` with `_find_text_spans()` using `_HTML_TAG_RE` regex to identify text between tags
- **Files modified:** src/do_uw/stages/render/output_sanitizer.py
- **Verification:** All 33 tests pass including threshold context test
- **Committed in:** 8c62081f

**2. [Rule 3 - Blocking] Pre-pass for debug patterns resembling HTML tags**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** `<class 'module.Class'>` consumed by HTML tag regex, never appears as text node
- **Fix:** Added `_pre_pass_debug_tags()` method to strip class/module repr before text extraction
- **Files modified:** src/do_uw/stages/render/output_sanitizer.py
- **Verification:** test_strips_class_repr passes
- **Committed in:** 8c62081f

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed items above.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all functionality is fully implemented.

## Next Phase Readiness
- OutputSanitizer ready to be wired into the render pipeline (141-02)
- SanitizationLog provides evidence for upstream template fixes

---
*Phase: 141-output-sanitization*
*Completed: 2026-03-28*
