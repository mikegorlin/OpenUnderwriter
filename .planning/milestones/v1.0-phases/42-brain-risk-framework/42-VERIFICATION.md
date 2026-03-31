---
phase: 42-brain-risk-framework
verified: 2026-02-24T12:00:00Z
status: passed
score: 4/4 must-haves verified
re_verification: false
---

# Phase 42: Brain Risk Framework Verification Report

**Phase Goal:** Restructure brain risk framework — add peril-organized scoring data extraction from brain framework (perils + causal chains), wire into Word/HTML/Markdown renderers with summary tables and per-peril deep dives, verify brain build works end-to-end with integration smoke test.
**Verified:** 2026-02-24
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | BrainDBLoader can load perils and causal chains from brain.duckdb | VERIFIED | `load_perils()` and `load_causal_chains()` exist at lines 427-456 of brain_loader.py; integration smoke test returns 8 perils and 16 chains |
| 2 | `extract_peril_scoring()` cross-references check_results and produces risk-organized dict | VERIFIED | Full implementation in scoring_peril_data.py (242 lines); returns `{perils, all_perils, active_count, highest_peril}` with chain activation and risk level logic |
| 3 | Word renderer renders peril summary table and per-peril deep dives in Section 7 | VERIFIED | sect7_scoring_perils.py (313 lines) with `render_peril_summary()` and `render_peril_deep_dives()`; wired into sect7_scoring.py at lines 411-413 and 434-450 |
| 4 | HTML template renders peril summary table and per-peril chain narratives | VERIFIED | scoring.html.j2 lines 53-115 render full summary table and per-peril deep dives with trigger/amplifier/mitigator sections |
| 5 | Markdown template renders peril summary table | VERIFIED | scoring.md.j2 lines 15-24 render peril summary with conditional guard |
| 6 | extract_scoring() in md_renderer_helpers_scoring.py populates peril_scoring key | VERIFIED | Lines 218-225 of md_renderer_helpers_scoring.py call extract_peril_scoring and add result to dict |
| 7 | brain build works end-to-end without error | VERIFIED | `do-uw brain build` outputs: Perils migrated: 8, Causal chains: 16, Framework entries: 19, Checks tagged (peril): 88, Checks tagged (chain): 117 |
| 8 | All plan 42-01 tests pass (chain activation, peril computation) | VERIFIED | 25/25 tests pass in tests/render/test_scoring_peril_data.py |
| 9 | Brain framework tests pass (YAML loading, migration, coverage matrix) | VERIFIED | 23/23 tests pass in tests/brain/test_brain_framework.py |
| 10 | Full test suite passes (no Phase 42 regressions) | VERIFIED with caveat | 2079 passed, 13 skipped, 1 pre-existing failure unrelated to Phase 42 (see Anti-Patterns section) |

**Score:** 10/10 truths verified (1 with pre-existing caveat)

---

## Required Artifacts

### Plan 42-01: Peril Scoring Data Extraction

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/brain_loader.py` | Add `load_perils()` and `load_causal_chains()` methods | VERIFIED | Both methods present at lines 427-456; correctly query brain_perils and brain_causal_chains tables; 497 lines (under 500 limit) |
| `src/do_uw/stages/render/scoring_peril_data.py` | `extract_peril_scoring(state)` with chain activation logic | VERIFIED | 242 lines; contains `_check_fired()`, `_evaluate_chain()`, `_aggregate_peril()`, `extract_peril_scoring()`; graceful fallback returns `{}` on exception |
| `tests/render/test_scoring_peril_data.py` | Tests for chain activation, peril computation, fallback | VERIFIED | 25 tests covering all required scenarios; all pass |

### Plan 42-02: Word Renderer

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/sections/sect7_scoring_perils.py` | `render_peril_summary()` and `render_peril_deep_dives()` | VERIFIED | 313 lines; full color-coded table with cell shading; per-peril deep dives with chain narratives; only active perils get deep dives |
| `src/do_uw/stages/render/sections/sect7_scoring.py` | Calls peril renderers after tier box | VERIFIED | `_render_peril_scoring()` added at lines 434-450; called from `render_section_7()` at line 412; graceful `ImportError` fallback; 473 lines (under 500 limit) |

### Plan 42-03: HTML + Markdown Templates

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/md_renderer_helpers_scoring.py` | `extract_scoring()` populates `peril_scoring` key | VERIFIED | Lines 218-225 add peril_scoring to result dict; graceful ImportError fallback; 366 lines (under 500 limit) |
| `src/do_uw/templates/html/sections/scoring.html.j2` | Peril summary table + per-peril chain deep dives | VERIFIED | Lines 53-115 render full peril section with conditional guard; includes summary table, per-peril divs with triggers/amplifiers/mitigators |
| `src/do_uw/templates/markdown/sections/scoring.md.j2` | Peril summary table after tier classification | VERIFIED | Lines 15-24 render markdown table with conditional guard |

### Plan 42-04: Brain Build + Integration

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/brain/brain_migrate_framework.py` | `build_framework()` with `create_schema(conn)` call | VERIFIED | 341 lines; `build_framework()` calls `create_schema(conn)` at line 330 before migrations |
| `src/do_uw/brain/framework/perils.yaml` | 8 perils with required fields | VERIFIED | Confirmed: 8 perils, all have `id`, `name`, `haz_codes` |
| `src/do_uw/brain/framework/causal_chains.yaml` | 16 causal chains | VERIFIED | 16 chains (note: Plan 42-04 and some test docstrings say "18" but actual count is 16 — tests assert 16 and pass) |
| `tests/brain/test_brain_framework.py` | Framework YAML, migration, coverage matrix, CLI smoke tests | VERIFIED | 23 tests, all pass |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `sect7_scoring.py` | `scoring_peril_data.py` | `extract_peril_scoring()` inside `_render_peril_scoring()` | WIRED | Lines 439-449; lazy import with ImportError fallback |
| `sect7_scoring.py` | `sect7_scoring_perils.py` | `render_peril_summary()` and `render_peril_deep_dives()` | WIRED | Lines 440-448; both functions imported and called |
| `md_renderer_helpers_scoring.py` | `scoring_peril_data.py` | `extract_peril_scoring()` | WIRED | Lines 220-225; result added to `result["peril_scoring"]` |
| `scoring.html.j2` | `peril_scoring` key | Jinja2 `sc.get('peril_scoring', {})` | WIRED | Line 54; conditional guard at line 55 |
| `scoring.md.j2` | `peril_scoring` key | Jinja2 `scoring.peril_scoring is defined` | WIRED | Line 15; conditional guard |
| `brain_loader.py` | `brain_perils` table | DuckDB SELECT | WIRED | `load_perils()` queries `brain_perils` directly |
| `brain_loader.py` | `brain_causal_chains` table | DuckDB SELECT | WIRED | `load_causal_chains()` queries `brain_causal_chains` directly |
| `brain_migrate_framework.py` | `brain_schema.create_schema()` | `build_framework()` calls `create_schema(conn)` | WIRED | Line 330; ensures Phase 42 tables exist before migration |
| `cli_brain.py` | `brain_migrate_framework.build_framework()` | `brain build` CLI command | WIRED | Lines 364-379; `brain build` invokes `build_framework(conn)` |

---

## Requirements Coverage

No requirements IDs were declared for Phase 42 (standalone phase per task specification). N/A.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/test_cli_brain.py` | 82 | Pre-existing test failure: `test_status_missing_db` asserts `exit_code == 1` but gets `0` | Info | Pre-existing before Phase 42 (test was added in commit 7d11773, identical before/after Phase 42 commits); caused by brain.duckdb existing on disk so `db_path.exists()` check in `status()` fails to see the mocked path. The mock patches `do_uw.brain.brain_schema.get_brain_db_path` but the function uses a local import in `cli_brain.py`, so the patch reaches the right module but brain.duckdb at the default path already exists. Not introduced by Phase 42. |
| `tests/brain/test_brain_framework.py` | 6, 61, 156 | Docstring/comment inconsistency: says "18 chains" but YAML has 16 and assertions use `== 16` | Info | Documentation staleness only; all assertions correct and pass. No functional impact. |

No blocker or warning anti-patterns in Phase 42 code. All new files are clean.

---

## Human Verification Required

### 1. Word Document Visual Rendering

**Test:** Run a full pipeline against a ticker with triggered checks (e.g., a company with stock drop and governance issues). Open the resulting Word document and navigate to Section 7.
**Expected:** The "D&O Claim Peril Assessment" table appears after the Tier Classification, showing 8 perils with color-coded risk levels (red for HIGH, amber for ELEVATED, light amber for MODERATE, blue for LOW). Active perils also have "Active Peril Analysis" deep dive sections with trigger/amplifier/mitigator bullet lists.
**Why human:** Cell shading colors, font sizing, and visual layout cannot be verified programmatically. Also depends on having check_results data that actually triggers chains.

### 2. HTML Report Peril Section

**Test:** Run the pipeline and open the generated HTML report, scroll to the Scoring section.
**Expected:** The Peril Assessment section renders between Tier Classification and 10-Factor Scoring. The peril table uses traffic light badges for risk level. Active perils have colored left-border divs with chain detail text.
**Why human:** Tailwind CSS class application and traffic_light() macro rendering requires visual inspection.

### 3. Graceful Fallback When brain.duckdb Missing

**Test:** Temporarily rename brain.duckdb, run a full pipeline render, verify Word/HTML/Markdown output has no peril section but renders all other scoring sections normally.
**Expected:** Render completes without error; peril section simply absent; all other scoring content intact.
**Why human:** Can verify import path programmatically but not the full render-without-crash guarantee in a real pipeline run without brain.duckdb.

---

## Gaps Summary

No gaps. All 4 wave plans have their must-haves fully implemented, tested, and wired.

**One pre-existing test failure** (`test_status_missing_db`) exists that predates Phase 42. It is caused by brain.duckdb now existing on disk, causing the mock patch to behave differently than when the test was written (when brain.duckdb did not yet exist). This should be tracked as a follow-up fix but does not block Phase 42 goal achievement.

---

## Chain Count Discrepancy Note

Plan 42-04 mentions "16 chains" and "some test docstrings say 18 chains." The actual causal_chains.yaml contains 16 chains. The plan text originally said "~18 chains." All tests correctly assert `== 16`. The brain build CLI output shows "Causal chains: 16." This is a documentation inconsistency, not a functional issue.

---

_Verified: 2026-02-24_
_Verifier: Claude (gsd-verifier)_
