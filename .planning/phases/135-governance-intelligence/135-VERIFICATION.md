---
phase: 135-governance-intelligence
verified: 2026-03-27T07:44:23Z
status: passed
score: 10/10 must-haves verified
re_verification: false
---

# Phase 135: Governance Intelligence Verification Report

**Phase Goal:** Governance analysis reaches investigative depth -- underwriters see per-officer background investigation with prior SCA/SEC exposure, serial defendant flags, complete shareholder rights inventory, and detailed insider trading activity with 10b5-1 plan classification
**Verified:** 2026-03-27T07:44:23Z
**Status:** passed
**Re-verification:** No -- initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                                   | Status     | Evidence                                                                                                   |
|----|---------------------------------------------------------------------------------------------------------|------------|------------------------------------------------------------------------------------------------------------|
| 1  | OfficerBackground model captures prior companies, SCA exposures, serial defendant flag, and suitability | VERIFIED | `governance_intelligence.py` defines all 6 fields; model validated in 18 tests                           |
| 2  | Serial defendant detection correctly identifies officers at companies during SCA class periods           | VERIFIED | `detect_serial_defendants` + `date_ranges_overlap` with 6 edge-case tests; fuzzy company name matching  |
| 3  | Per-insider aggregation groups InsiderTransaction records by insider name with totals and 10b5-1 status | VERIFIED | `aggregate_per_insider` in `officer_background.py`; excludes comp codes A/F; sorts by total_sold desc   |
| 4  | Shareholder rights provisions cover all 8 required items including cumulative_voting field              | VERIFIED | `_RIGHTS_PROVISIONS` list has 8 entries; `BoardProfile.cumulative_voting` added to `governance.py`       |
| 5  | Defense strength assessment aggregates provisions into Strong/Moderate/Weak                             | VERIFIED | `build_shareholder_rights` computes posture: Strong >= 5, Moderate 3-4, Weak <= 2 protective; 4 tests   |
| 6  | Each named officer shows prior companies, SCA/SEC history, personal litigation, and suitability         | VERIFIED | `build_officer_backgrounds` reads leadership profiles, extracts bios, calls Supabase, returns officer_dicts |
| 7  | Officers flagged as serial defendants display red badge with case references                            | VERIFIED | `officer_backgrounds.html.j2` line 17: red badge rendered when `is_serial_defendant` is True             |
| 8  | Shareholder rights inventory shows 8 provisions as checklist table with defense strength and D&O implication | VERIFIED | `shareholder_rights.html.j2` renders provision table with defense_strength and do_implication columns  |
| 9  | Per-insider table shows name, position, total sales, tx count, 10b5-1 badge, and activity period sorted by sales | VERIFIED | `per_insider_activity.html.j2` table header has all 7 columns; data sorted by context builder |
| 10 | Anti-takeover defense posture shows aggregate Strong/Moderate/Weak assessment                          | VERIFIED | `shareholder_rights.html.j2` lines 8-17 display overall_defense_posture badge with color coding         |

**Score:** 10/10 truths verified

---

## Required Artifacts

| Artifact                                                                         | Expected                                                           | Status    | Details                                                |
|----------------------------------------------------------------------------------|--------------------------------------------------------------------|-----------|--------------------------------------------------------|
| `src/do_uw/models/governance_intelligence.py`                                    | 6 Pydantic models for governance intelligence data layer           | VERIFIED  | 122 lines, all 6 classes present, fully implemented    |
| `src/do_uw/stages/extract/officer_background.py`                                 | 6 extraction functions: bio parsing, SCA query, serial defendants  | VERIFIED  | 465 lines, all 6 functions present and substantive     |
| `src/do_uw/stages/render/context_builders/_governance_intelligence.py`           | 3 context builder functions                                        | VERIFIED  | 417 lines, all 3 builders wired to extraction layer    |
| `src/do_uw/templates/html/sections/governance/officer_backgrounds.html.j2`      | Per-officer investigation cards with serial defendant badges       | VERIFIED  | Guarded with `has_officer_backgrounds`, badges present |
| `src/do_uw/templates/html/sections/governance/shareholder_rights.html.j2`       | 8-provision checklist table with color coding                      | VERIFIED  | Iterates provisions list, posture badge at top         |
| `src/do_uw/templates/html/sections/governance/per_insider_activity.html.j2`     | Per-insider detail table with 10b5-1 badges                        | VERIFIED  | 7-column table, 10b5-1 vs Discretionary badge          |
| `tests/extract/test_officer_background.py`                                       | Unit tests: bio extraction, date overlap, serial defendant         | VERIFIED  | 5 test classes; TestDateRangesOverlap, TestDetectSerialDefendants, TestAggregatePerInsider all present |
| `tests/models/test_governance_intelligence.py`                                   | Model validation tests                                             | VERIFIED  | 18 tests, all pass                                     |
| `tests/render/test_governance_intelligence_ctx.py`                               | Context builder unit tests                                         | VERIFIED  | 3 test classes, 16 tests, all pass                     |

---

## Key Link Verification

| From                                             | To                                          | Via                                              | Status  | Details                                                            |
|--------------------------------------------------|---------------------------------------------|--------------------------------------------------|---------|--------------------------------------------------------------------|
| `officer_background.py`                          | `supabase_litigation.py` (pattern)          | `query_officer_prior_sca` batch ilike query      | VERIFIED | Uses same httpx + Supabase URL pattern; batches of 20              |
| `officer_background.py`                          | `governance_intelligence.py`                | `from do_uw.models.governance_intelligence import` | VERIFIED | Lines 23-28 import all 4 model classes                            |
| `_governance_intelligence.py`                    | `officer_background.py`                     | `from do_uw.stages.extract.officer_background import` | VERIFIED | Lines 23-29 import all 5 extraction functions                 |
| `governance.py`                                  | `_governance_intelligence.py`               | `from do_uw.stages.render.context_builders._governance_intelligence import` | VERIFIED | Lines 39-42; calls at lines 516-518 via `result.update()` |
| `beta_report.html.j2`                            | 3 governance template fragments             | `{% include %}` directives                       | VERIFIED | Lines 1833, 1839, 1842 include all 3 fragments                    |

---

## Data-Flow Trace (Level 4)

| Artifact                           | Data Variable          | Source                                           | Produces Real Data | Status   |
|------------------------------------|------------------------|--------------------------------------------------|--------------------|----------|
| `officer_backgrounds.html.j2`      | `officer_backgrounds`  | `state.extracted.governance.leadership.executives` via `build_officer_backgrounds` | Yes -- reads live LeadershipForensicProfile objects | FLOWING |
| `shareholder_rights.html.j2`       | `shareholder_rights`   | `state.extracted.governance.board` (BoardProfile fields) via `build_shareholder_rights` | Yes -- reads SourcedValue fields from BoardProfile | FLOWING |
| `per_insider_activity.html.j2`     | `per_insider_activity` | `state.extracted.market.insider_trading.transactions` via `aggregate_per_insider` | Yes -- aggregates real InsiderTransaction records | FLOWING |

All three templates depend on real pipeline state data. The context builders have proper empty-state guards (`has_X` flags) that prevent rendering when data is absent, ensuring no phantom sections appear for companies without that data.

---

## Behavioral Spot-Checks

| Behavior                                       | Command                                                                 | Result                          | Status |
|------------------------------------------------|-------------------------------------------------------------------------|---------------------------------|--------|
| All 55 Phase 135 tests pass                    | `uv run pytest tests/models/test_governance_intelligence.py tests/extract/test_officer_background.py tests/render/test_governance_intelligence_ctx.py -q` | `55 passed in 2.04s`           | PASS   |
| Jinja2 template syntax valid for all 3 fragments | `python -c "env.get_template(...)"` for all 3 templates               | `All templates parse OK`        | PASS   |
| Governance render tests pass with no regressions | `uv run pytest tests/render/ -q -k governance`                        | `19 passed, 167 deselected`    | PASS   |
| date_ranges_overlap edge cases                  | TestDateRangesOverlap: overlap, no-overlap-before, no-overlap-after, edge-same-year, single-year, empty-dates | All 6 pass | PASS |

---

## Requirements Coverage

| Requirement | Source Plan  | Description                                                                                    | Status    | Evidence                                                                          |
|-------------|-------------|-----------------------------------------------------------------------------------------------|-----------|-----------------------------------------------------------------------------------|
| GOV-01      | 135-01, 135-02 | Per-officer background: prior companies, SCA/SEC history, personal litigation, suitability  | SATISFIED | OfficerBackground model + extract_prior_companies_from_bio + officer_backgrounds.html.j2 |
| GOV-02      | 135-01, 135-02 | Serial defendant detection: flag executives present at companies during prior SCAs           | SATISFIED | detect_serial_defendants + date_ranges_overlap + Supabase query + red badge in template |
| GOV-03      | 135-01, 135-02 | Shareholder rights inventory: 8 provisions including cumulative voting                      | SATISFIED | ShareholderRightsInventory model, 8 items in _RIGHTS_PROVISIONS, cumulative_voting in BoardProfile |
| GOV-04      | 135-01, 135-02 | Anti-takeover protections inventory with defense strength assessment                        | SATISFIED | build_shareholder_rights computes Strong/Moderate/Weak; displayed with color-coded badge |
| GOV-05      | 135-01, 135-02 | Per-insider activity detail: name, position, sales ($, %O/S), tx count, 10b5-1, period     | SATISFIED | aggregate_per_insider + build_per_insider_activity + per_insider_activity.html.j2 with all 7 columns |

No orphaned requirements -- all 5 GOV requirements are claimed by both plans, implemented, and have REQUIREMENTS.md entries marked complete.

---

## Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `governance.py` | 523 lines (3.4% over 500-line CLAUDE.md limit) | Info | File is slightly over the project soft limit. The 23 extra lines are the 3 import + 3 `result.update()` calls added by this phase. Not a functional issue; note for next refactor. |

No TODO/FIXME/placeholder comments, no return stubs, no hardcoded empty arrays masquerading as real data.

---

## Human Verification Required

### 1. Officer Background Cards -- Live Pipeline Rendering

**Test:** Run `underwrite TICKER --fresh` for a company with a DEF 14A with multiple executive bios. Open the governance section.
**Expected:** Officer background cards appear with prior companies listed (if bios have recognizable role+company patterns), suitability badges shown, and if any officer matches a Supabase SCA record, "Serial Defendant" badge appears.
**Why human:** Requires a live pipeline run + visual inspection. Regex bio extraction depends on actual DEF 14A text formats; cannot verify without real filing data.

### 2. Shareholder Rights -- Real BoardProfile Data

**Test:** Run `underwrite TICKER --fresh` for a company with a full DEF 14A. Open governance section, check Shareholder Rights Inventory.
**Expected:** 8 rows in the checklist table, defense posture badge shows Strong/Moderate/Weak based on actual provisions, D&O implication column shows specific text per provision.
**Why human:** BoardProfile fields are populated by the board_governance extraction stage. Cannot verify the display without a live run that populates `classified_board`, `poison_pill`, etc.

### 3. Per-Insider Activity -- Sorting and %O/S Column

**Test:** Run `underwrite TICKER --fresh` for a company with multiple Form 4 filers. Open governance section.
**Expected:** Per-insider table shows sellers sorted by total sales descending, %O/S column shows either a percentage or "N/A", 10b5-1 badges are colored green (plan trades) vs amber (discretionary).
**Why human:** Requires real Form 4 data flowing through the pipeline. The %O/S calculation depends on the shares_outstanding fallback chain being correctly populated.

---

## Gaps Summary

No gaps. All plan artifacts are substantive, wired, and have data flowing from real pipeline state. All 55 unit tests pass. All 3 Jinja2 templates are syntactically valid and wired into `beta_report.html.j2`. All 5 GOV requirements are implemented end-to-end from data model through extraction through context builder through template.

The only advisory item is `governance.py` at 523 lines (23 over the 500-line soft limit) -- not a functional gap.

---

_Verified: 2026-03-27T07:44:23Z_
_Verifier: Claude (gsd-verifier)_
