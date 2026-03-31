---
phase: 136-forward-looking-and-integration
plan: 02
subsystem: render
tags: [templates, forward-looking, beta-report, qa-validation, integration]

requires:
  - phase: 136-forward-looking-and-integration
    plan: 01
    provides: build_forward_scenarios, build_forward_calendar, build_forward_credibility, build_short_seller_alerts, derive_short_conviction

provides:
  - Four Jinja2 templates for forward-looking sections (scenarios, key dates, credibility, short-seller)
  - beta_report.py wiring with try/except fallback guards
  - Forward-Looking Analysis mega-section in beta_report.html.j2
  - qa_compare.py extended with 16 Phase 133-136 section checks

affects: [beta-report-html, qa-compare]

tech-stack:
  added: []
  patterns: [inline-styles-beta-report, try-except-fallback-guard, section-content-detection-regex]

key-files:
  created:
    - src/do_uw/templates/html/sections/forward_looking/scenarios.html.j2
    - src/do_uw/templates/html/sections/forward_looking/key_dates.html.j2
    - src/do_uw/templates/html/sections/forward_looking/credibility_enhanced.html.j2
    - src/do_uw/templates/html/sections/forward_looking/short_seller_alerts.html.j2
  modified:
    - src/do_uw/stages/render/context_builders/beta_report.py
    - src/do_uw/templates/html/sections/beta_report.html.j2
    - scripts/qa_compare.py

key-decisions:
  - "Forward-Looking Analysis mega-section placed between Litigation (section 6) and Sector (section 7) in beta_report"
  - "All five forward-looking context builders wired with try/except guards returning *_available=False on failure"
  - "Templates use inline styles matching existing beta_report pattern (no external CSS classes)"
  - "qa_compare.py uses regex-based content detection for soft v10.0 section parity checks (data-dependent)"

requirements-completed: [FWD-01, FWD-02, FWD-03, FWD-04, FWD-05]

duration: 30min
completed: 2026-03-27
---

# Phase 136 Plan 02: Forward-Looking Templates & Integration Summary

**Four Jinja2 templates rendering scenario cards with probability badges, key dates timeline with urgency colors, credibility quarter-by-quarter table with pattern classification, and short-seller alert cards with conviction badges -- all wired into beta_report with fallback guards and validated with extended cross-ticker QA**

## Performance

- **Duration:** 30 min
- **Started:** 2026-03-27T13:04:37Z
- **Completed:** 2026-03-27T13:35:00Z
- **Tasks:** 3 (2 auto + 1 auto-approved checkpoint)
- **Files created:** 4
- **Files modified:** 3

## Accomplishments

- Scenario cards template with flex-wrap layout (2-3 per row), left border colored by probability, severity estimate, score delta with tier change badge, and company-specific catalyst text
- Key dates calendar template with urgency dots (red/amber/gray), chronological sort, source labels, D&O relevance text, and re-underwriting trigger callout
- Credibility enhanced template with pattern badge (Consistent Beater/Sandbagging/Unreliable/Deteriorating), cumulative B/M/I colored blocks, borderless quarter-by-quarter table with row highlighting
- Short-seller monitor template with named firm alert cards (red left border), conviction direction badge (Bears Rising/Stable/Declining), short interest stats panel, and firms-checked disclosure
- beta_report.py imports and calls all 5 forward-looking builders with try/except guards setting fallback dicts on failure
- Forward-Looking Analysis mega-section added to beta_report.html.j2 between litigation and sector sections
- qa_compare.py extended with 16 Phase 133-136 section detection fields and soft parity comparison

## Task Commits

1. **Task 1: Templates + beta_report wiring** - `c78ea66f` (feat)
2. **Task 2: Cross-ticker QA validation** - `b43f7eb8` (feat)
3. **Task 3: Visual checkpoint** - auto-approved (no commit needed)

## Files Created/Modified

- `src/do_uw/templates/html/sections/forward_looking/scenarios.html.j2` - Scenario cards with probability badges, severity, catalyst
- `src/do_uw/templates/html/sections/forward_looking/key_dates.html.j2` - Key dates timeline with urgency color coding
- `src/do_uw/templates/html/sections/forward_looking/credibility_enhanced.html.j2` - Pattern classification + quarter table
- `src/do_uw/templates/html/sections/forward_looking/short_seller_alerts.html.j2` - Alert cards + conviction badge + SI stats
- `src/do_uw/stages/render/context_builders/beta_report.py` - Wired 5 forward-looking builders with try/except guards
- `src/do_uw/templates/html/sections/beta_report.html.j2` - Added Forward-Looking Analysis mega-section with 4 includes
- `scripts/qa_compare.py` - 16 new Phase 133-136 section detection fields + v10.0 parity checks

## Decisions Made

- Mega-section placed between litigation (section 6) and sector (section 7) to maintain narrative flow: what has gone wrong -> what could go wrong -> industry context
- All inline styles (no external CSS classes) matching existing beta_report pattern for consistency
- Soft section parity checks in qa_compare.py: missing sections logged but many are data-dependent (not all tickers have analyst coverage, short-seller reports, etc.)
- Templates use `| default('N/A')` for None handling; no `| truncate()` on analytical content per CLAUDE.md

## Deviations from Plan

None - plan executed exactly as written.

## Pre-existing Test Failures

Three pre-existing test failures found (all confirmed by running against the pre-merge commit):
1. `test_threshold_provenance_categorized` - FIN.ACCT.ohlson_o_score has `source: 'academic'` instead of `'academic_research'`
2. `test_real_manifest_template_agreement` - Templates from Phase 133-135 not yet declared in manifest
3. `test_all_signals_have_do_context` - 5 signals missing do_context

These are NOT caused by Phase 136-02 changes. Logged to deferred items.

## Known Stubs

None -- all templates render real data from context builders that read from state paths.

## User Setup Required

None -- no external service configuration required.

## Next Phase Readiness

- All v10.0 forward-looking features are wired end-to-end: context builders (Plan 01) -> templates (Plan 02) -> beta_report rendering
- Cross-ticker QA script covers all Phase 133-136 sections
- Visual verification deferred (auto-approved in auto mode) -- should be manually verified on next pipeline run

---
*Phase: 136-forward-looking-and-integration*
*Completed: 2026-03-27*
