# Phase 13 Plan 03: AI Risk Rendering, ScoreStage Integration, Dashboard Summary

Section 8 AI Transformation Risk renders in Word/Markdown/Dashboard with sub-dimension table, peer comparison, narrative, forward indicators; ScoreStage calls score_ai_risk() to populate scoring on extracted AI data; full pipeline EXTRACT->SCORE->RENDER chain verified.

## Frontmatter

- **phase:** 13
- **plan:** 03
- **subsystem:** render, score, dashboard
- **tags:** ai-risk, sect8, word-renderer, markdown, dashboard, score-stage, pipeline-integration
- **requires:** 13-01 (scoring engine), 13-02 (extraction pipeline)
- **provides:** Section 8 in all output formats, ScoreStage AI risk wiring, dashboard AI risk section
- **affects:** None (final plan in Phase 13)
- **tech-stack.added:** None
- **tech-stack.patterns:** importlib section dispatch (sect8), dashboard partial routing
- **key-files.created:**
  - src/do_uw/stages/render/sections/sect8_ai_risk.py
  - src/do_uw/templates/dashboard/partials/_ai_risk_detail.html
  - tests/test_ai_risk_render.py
  - tests/test_ai_risk_pipeline.py
- **key-files.modified:**
  - src/do_uw/stages/render/word_renderer.py
  - src/do_uw/stages/render/md_renderer.py
  - src/do_uw/templates/markdown/worksheet.md.j2
  - src/do_uw/stages/score/__init__.py
  - src/do_uw/dashboard/state_api.py
  - src/do_uw/dashboard/app.py
  - src/do_uw/templates/dashboard/index.html
  - tests/test_dashboard.py
  - tests/test_dashboard_state_api.py
- **decisions:** Section 8 uses same importlib dispatch pattern as Sections 1-7; AI risk dashboard uses custom partial for rich sub-dimension display
- **duration:** 8m 29s
- **completed:** 2026-02-10

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Section 8 renderer, Word/Markdown template, ScoreStage wiring | 24e778e | sect8_ai_risk.py, word_renderer.py, md_renderer.py, worksheet.md.j2, score/__init__.py |
| 2 | Dashboard AI risk section, pipeline integration tests | 9382675 | state_api.py, app.py, _ai_risk_detail.html, test_ai_risk_pipeline.py |

## Decisions Made

1. **Section 8 importlib dispatch:** Registered sect8_ai_risk.py between Section 7 (Scoring) and Meeting Prep appendix using the same _try_import_renderer pattern.
2. **Dashboard AI risk partial:** Instead of generic section.html findings list, AI risk section routes to a custom _ai_risk_detail.html partial that renders sub-dimension table, peer comparison card, and forward indicators with proper formatting.
3. **ScoreStage wiring:** AI risk scoring runs after the main 16-step scoring pipeline but before stage completion, wrapped in try/except for isolation. Uses lazy import for score_ai_risk.
4. **Markdown template:** Added full AI risk section with sub-dimension table, peer comparison conditional, narrative, and forward indicators between Section 7 and Meeting Prep appendix.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Dashboard state_api existing tests expected 6 sections**
- **Found during:** Task 2
- **Issue:** tests/test_dashboard_state_api.py hardcoded len(sections)==6 and explicit section_ids list
- **Fix:** Updated to 7 sections and added "ai_risk" to expected section_ids
- **Files modified:** tests/test_dashboard_state_api.py
- **Commit:** 9382675

**2. [Rule 3 - Blocking] Dashboard index.html needed AI risk card template**
- **Found during:** Task 2
- **Issue:** index.html loop had section-specific card templates for 6 sections but not ai_risk
- **Fix:** Added ai_risk card template showing score, model ID, disclosure trend, dimension count
- **Files modified:** src/do_uw/templates/dashboard/index.html
- **Commit:** 9382675

## Verification Results

- `python -m pytest tests/test_ai_risk_render.py` -- 11 passed
- `python -m pytest tests/test_ai_risk_pipeline.py` -- 13 passed
- `python -m pyright src/do_uw/stages/render/sections/sect8_ai_risk.py src/do_uw/stages/score/__init__.py src/do_uw/dashboard/state_api.py` -- 0 errors
- `python -m ruff check src/do_uw/` -- 0 errors
- `python -m pytest` -- 1790 passed, 0 failed (was 1766)
- No modified file exceeds 500 lines

## Test Summary

- **New tests:** 24 (11 render + 13 pipeline)
- **Total tests:** 1790 (was 1766)
- **Regressions:** 0

## Next Phase Readiness

Phase 13 (AI Transformation Risk Factor) is now complete:
- Plan 01: AI risk models + scoring engine
- Plan 02: AI risk extraction pipeline
- Plan 03: Section 8 rendering, ScoreStage wiring, dashboard integration

The full AI risk pipeline is operational: EXTRACT populates raw disclosure/patent/competitive data, SCORE runs the 5-dimension scoring engine, and RENDER outputs Section 8 in Word documents, Markdown, and the interactive dashboard.
