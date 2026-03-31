---
phase: 47-check-data-mapping-completeness
plan: "04"
subsystem: extract/governance
tags: [def14a-expansion, board-profile, governance-data, population-b, map-02, map-03]

# Dependency graph
requires:
  - phase: 47-check-data-mapping-completeness
    plan: "01"
    provides: Wave 0 RED test scaffolds for DEF14A schema (test_def14a_schema.py)
provides:
  - DEF14AExtraction schema with 5 new board governance fields
  - BoardProfile with 5 corresponding SourcedValue fields
  - convert_board_profile() populating all 5 new fields with sanity checks
  - map_governance_fields() board_attendance, board_meeting_count, board_diversity fields populated from GovernanceData
affects:
  - GOV.BOARD.attendance — board_attendance field now populated from DEF 14A
  - GOV.BOARD.meetings — board_meeting_count field now populated from DEF 14A
  - GOV.BOARD.diversity — board_diversity field now populated from DEF 14A
  - Population B checks that route through board_attendance_pct/board_gender_diversity_pct

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Sanity-gated SourcedValue population: validate range (0-100%) before wrapping in SourcedValue
    - Optional company_name parameter for backward-compat callsite flexibility
    - None-placeholder replacement pattern: replace `None  # Not yet on BoardProfile` comments with real field reads

key-files:
  created: []
  modified:
    - src/do_uw/stages/extract/llm/schemas/def14a.py
    - src/do_uw/models/governance.py
    - src/do_uw/stages/extract/llm_governance.py
    - src/do_uw/stages/analyze/check_mappers_sections.py

key-decisions:
  - "convert_board_profile() accepts optional company_name arg for test callsite compat — not used internally"
  - "All 5 new DEF14AExtraction fields default to None — no downstream breakage from schema expansion"
  - "Sanity checks on diversity/attendance pcts (0.0-100.0 range) before wrapping in SourcedValue"
  - "board_diversity key in map_governance_fields() maps to board_gender_diversity_pct (most commonly disclosed)"
  - "board_racial_diversity added as separate key for completeness (not in original plan spec)"
  - "directors_below_75_pct_attendance added as separate key in mapper for completeness"

requirements-completed: [MAP-02, MAP-03]

# Metrics
duration: 435s
completed: 2026-02-26
---

# Phase 47 Plan 04: DEF14A Schema Expansion and Governance Field Wiring Summary

**5 new DEF14A extraction fields (board attendance + diversity + meeting count) added to schema, wired through convert_board_profile() into BoardProfile SourcedValue fields, and mapper None placeholders replaced with real GovernanceData reads**

## Performance

- **Duration:** 7m 15s
- **Started:** 2026-02-26T01:21:32Z
- **Completed:** 2026-02-26T01:28:47Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added 5 new fields to `DEF14AExtraction`: `board_gender_diversity_pct`, `board_racial_diversity_pct`, `board_meetings_held`, `board_attendance_pct`, `directors_below_75_pct_attendance` — all default None
- Added 5 corresponding `SourcedValue` fields to `BoardProfile` (diversity + meeting attendance sections)
- Updated `convert_board_profile()` to populate all 5 new fields with range sanity checks; added optional `company_name` parameter for test callsite compatibility
- Replaced 3 `None  # Not yet on BoardProfile` placeholders in `map_governance_fields()` with real reads from `gov.board.*`; added 3 additional new fields (`board_diversity`, `board_racial_diversity`, `directors_below_75_pct_attendance`)
- All 7 `test_def14a_schema.py` tests GREEN (previously all 7 were RED)
- Full test suite: 3967 pass, 2 pre-existing failures (render coverage) — no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand DEF14AExtraction schema + BoardProfile model** - `e5b63c6` (feat)
2. **Task 2: Wire convert_board_profile() + update mapper None placeholders** - `b332b7c` (feat)

## Files Modified

- `src/do_uw/stages/extract/llm/schemas/def14a.py` — 5 new fields added in Board of Directors section (252 lines, well under 500)
- `src/do_uw/models/governance.py` — 5 new SourcedValue fields added to BoardProfile (142 lines, well under 500)
- `src/do_uw/stages/extract/llm_governance.py` — convert_board_profile() updated with optional company_name arg + 5 new field population blocks (450 lines, under 500)
- `src/do_uw/stages/analyze/check_mappers_sections.py` — map_governance_fields() updated: 3 None placeholders replaced, 3 new fields added (457 lines, under 500)

## Decisions Made

- **Optional company_name parameter:** Test scaffold called `convert_board_profile(extraction, "AAPL")` with 2 args but function only accepted 1. Added optional `company_name: str | None = None` — accepted but not used internally. This is the right fix: test expectation was part of Wave 0 scaffold design.

- **board_diversity key maps to board_gender_diversity_pct:** The mapper key `board_diversity` maps to `board_gender_diversity_pct` because gender diversity is the most commonly disclosed metric in proxy statements. Racial/ethnic diversity added as separate `board_racial_diversity` key.

- **directors_below_75_pct_attendance in mapper:** Plan spec only mentioned `board_attendance` and `board_diversity`, but `directors_below_75_pct_attendance` is a natural complement (same DEF 14A section, already on BoardProfile) — added per Rule 2 (completeness).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing functionality] Added 3 additional mapper fields beyond plan spec**
- **Found during:** Task 2 (reviewing map_governance_fields() None placeholders)
- **Issue:** Plan spec only mentioned replacing `board_attendance` and `board_expertise` placeholders, but `board_meeting_count` was also a None placeholder and the new `board_racial_diversity` / `directors_below_75_pct_attendance` fields were already on BoardProfile
- **Fix:** Also replaced `board_meeting_count` placeholder; added `board_diversity`, `board_racial_diversity`, `directors_below_75_pct_attendance` as new mapper keys using the same `_safe_sourced(gov.board.*)` pattern
- **Files modified:** `src/do_uw/stages/analyze/check_mappers_sections.py`
- **Committed in:** `b332b7c` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 completeness)
**Impact on plan:** Completes the Population B field wiring more thoroughly. No scope creep — all fields were already on BoardProfile from Task 1.

## Verification Results

```
$ uv run python3 -c "from do_uw.stages.extract.llm.schemas.def14a import DEF14AExtraction; e = DEF14AExtraction(board_attendance_pct=98.5, board_meetings_held=9); print(e.board_attendance_pct, e.board_meetings_held)"
98.5 9

$ uv run pytest tests/stages/extract/test_def14a_schema.py -v
7 passed

$ uv run pytest tests/stages/analyze/ tests/stages/extract/ -q
258 passed

$ uv run pytest tests/ -q | tail -5
2 failed, 3967 passed (pre-existing render coverage failures only)

Line counts:
- def14a.py: 252 lines
- llm_governance.py: 450 lines
- governance.py: 142 lines
- check_mappers_sections.py: 457 lines
```

---
*Phase: 47-check-data-mapping-completeness*
*Completed: 2026-02-26*
