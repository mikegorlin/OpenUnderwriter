---
phase: 135-governance-intelligence
plan: 02
subsystem: render, templates
tags: [context-builders, governance, officer-backgrounds, shareholder-rights, insider-activity, serial-defendant, 10b5-1]

requires:
  - phase: 135-governance-intelligence
    plan: 01
    provides: "Pydantic models + extraction functions for officer backgrounds, shareholder rights, per-insider activity"
provides:
  - "build_officer_backgrounds context builder with serial defendant flagging"
  - "build_shareholder_rights context builder with 8-provision checklist and Strong/Moderate/Weak defense posture"
  - "build_per_insider_activity context builder with 10b5-1 badge classification"
  - "3 Jinja2 template fragments wired into beta_report governance section"
affects: [beta-report-governance, governance-context-builders]

tech-stack:
  added: []
  patterns:
    - "Governance intelligence context builder following Phase 134 _company_intelligence.py pattern"
    - "8-provision shareholder rights inventory with protective/shareholder-friendly classification"
    - "Per-insider sell aggregation with formatted currency and 10b5-1 badge"

key-files:
  created:
    - src/do_uw/stages/render/context_builders/_governance_intelligence.py
    - src/do_uw/templates/html/sections/governance/officer_backgrounds.html.j2
    - src/do_uw/templates/html/sections/governance/shareholder_rights.html.j2
    - src/do_uw/templates/html/sections/governance/per_insider_activity.html.j2
    - tests/render/test_governance_intelligence_ctx.py
  modified:
    - src/do_uw/stages/render/context_builders/governance.py
    - src/do_uw/templates/html/sections/beta_report.html.j2

key-decisions:
  - "Defense posture thresholds: Strong >= 5 protective, Moderate 3-4, Weak <= 2 (per D-09)"
  - "Provision status color coding: green for protective matches, red for shareholder-friendly, gray for N/A"
  - "String-valued board fields (proxy_access_threshold, special_meeting_threshold, forum_selection_clause) treated as Yes when non-empty"
  - "Per-insider %O/S uses company.shares_outstanding with XBRL fallback; shows N/A if unavailable"

patterns-established:
  - "Governance intelligence context builders: pure formatters, no evaluative logic"
  - "Template placement: officer_backgrounds after board_forensics, per_insider after ownership, shareholder_rights after structural_governance"

requirements-completed: [GOV-01, GOV-02, GOV-03, GOV-04, GOV-05]

duration: 7min
completed: 2026-03-27
---

# Phase 135 Plan 02: Governance Intelligence Context Builders & Templates Summary

**Context builders and Jinja2 templates for officer background investigation cards with serial defendant badges, shareholder rights 8-provision checklist with defense posture assessment, and per-insider trading detail with 10b5-1 classification**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-27T07:33:29Z
- **Completed:** 2026-03-27T07:40:18Z
- **Tasks:** 2
- **Files created:** 5
- **Files modified:** 2

## Accomplishments
- 3 context builder functions in _governance_intelligence.py following Phase 134 pattern: build_officer_backgrounds, build_shareholder_rights, build_per_insider_activity
- Officer backgrounds: reads leadership profiles, extracts prior companies from bios, batch Supabase SCA cross-reference, serial defendant detection, suitability assessment
- Shareholder rights: 8-provision checklist (classified board, poison pill, supermajority, proxy access, cumulative voting, written consent, special meeting, forum selection) with Strong/Moderate/Weak defense posture
- Per-insider activity: aggregates Form 4 transactions by insider, formats currency, calculates %O/S, classifies 10b5-1 vs Discretionary
- 3 template fragments with governance-consistent styling: officer cards, provision checklist table, insider detail table
- All 3 templates wired into beta_report.html.j2 governance section at appropriate positions
- 16 unit tests covering all builders, edge cases, defense strength thresholds, and 10b5-1 badge logic
- governance.py updated with 3 import + 3 update calls (stays under 520 lines)

## Task Commits

Each task was committed atomically:

1. **Task 1: Context builder helper and unit tests** - `92241ae8` (feat)
2. **Task 2: Template fragments and beta_report wiring** - `612f88bd` (feat)

## Files Created/Modified
- `src/do_uw/stages/render/context_builders/_governance_intelligence.py` - 3 context builder functions (296 lines)
- `src/do_uw/templates/html/sections/governance/officer_backgrounds.html.j2` - Per-officer investigation cards with serial defendant badges
- `src/do_uw/templates/html/sections/governance/shareholder_rights.html.j2` - 8-provision checklist with color-coded defense posture
- `src/do_uw/templates/html/sections/governance/per_insider_activity.html.j2` - Per-insider table with 10b5-1 badges
- `tests/render/test_governance_intelligence_ctx.py` - 16 unit tests
- `src/do_uw/stages/render/context_builders/governance.py` - Added import + 3 builder calls
- `src/do_uw/templates/html/sections/beta_report.html.j2` - Added 3 include directives

## Decisions Made
- Defense posture thresholds: Strong >= 5, Moderate 3-4, Weak <= 2 protective provisions (per D-09 from CONTEXT.md)
- String board fields (proxy_access_threshold, special_meeting_threshold, forum_selection_clause) treated as "Yes" when non-empty, mapping to their respective defense strengths
- Shares outstanding fallback: company.shares_outstanding -> XBRL financials dict -> None (N/A display)
- Template placement follows natural governance flow: officer investigation after board forensics, insider detail after ownership, shareholder rights after structural governance

## Deviations from Plan
None - plan executed exactly as written.

## Known Stubs
None - all context builders are fully implemented with real data wiring.

## Issues Encountered
- Pre-existing test failure in test_peril_scoring_html.py (ceiling_details AttributeError on SimpleNamespace mock) -- unrelated to governance intelligence, not introduced by this plan.

## User Setup Required
None.

## Next Phase Readiness
- All governance intelligence features now render in the beta report
- Officer backgrounds will populate on next --fresh pipeline run with DEF 14A data
- Shareholder rights will display for any company with BoardProfile governance data
- Per-insider detail will show for any company with Form 4 insider trading data

---
*Phase: 135-governance-intelligence*
*Completed: 2026-03-27*
