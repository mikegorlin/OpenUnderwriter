---
phase: 48-output-quality-hardening
verified: 2026-02-25T23:30:00Z
status: gaps_found
score: 3/4 success criteria verified
re_verification: false
gaps:
  - truth: "Full regression on AAPL, RPM, and TSLA confirms: SKIPPED count is lower than the v1.0 baseline of 68, TRIGGERED count on AAPL does not increase versus v1.0 baseline, and output is approved on human review of the HTML worksheet"
    status: failed
    reason: "SKIPPED count is still 68 (same as v1.0 baseline) — no decrease. QA-05 requires SKIPPED to decrease from 68. TSLA regression was not run. SUMMARY.md incorrectly claimed SKIPPED dropped to 59; the actual commit (492dc90) confirms SKIPPED=68 and documents no improvement."
    artifacts:
      - path: "tests/stages/analyze/test_regression_baseline.py"
        issue: "SKIPPED_FLOOR = 68 (unchanged from v1.0 baseline). The SUMMARY claimed it was updated to 59 but the actual code and commit explicitly say SKIPPED=68 with no reduction."
      - path: "output/AAPL-2026-02-25/state.json"
        issue: "Fresh AAPL run shows SKIPPED=68, not lower. Confirmed via state.json counter: {'CLEAR': 110, 'INFO': 201, 'TRIGGERED': 24, 'SKIPPED': 68}."
    missing:
      - "TSLA regression run — QA-05 and ROADMAP SC 4 both explicitly name TSLA. No output/TSLA-* directory exists."
      - "SKIPPED count reduction below 68 — requires investigation of why Population B DEF14A checks are not routing (DEF14A schema exists per Phase 47 but LLM extraction is not populating values). Until SKIPPED < 68, QA-05 is not satisfied."
---

# Phase 48: Output Quality Hardening Verification Report

**Phase Goal:** The QA audit table is accurate and trustworthy — source column shows actual filing references or web URLs (never "—"), value column shows the datum that was evaluated, and every TRIGGERED finding in the red flags section displays its threshold criterion alongside the finding value.
**Verified:** 2026-02-25T23:30:00Z
**Status:** GAPS FOUND
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | QA audit table source column shows "10-K 2024-09-28" format or "WEB (gap)" URL for every evaluated check — no row shows "—" as source | ✓ VERIFIED | HTML output shows zero em-dash cells in qa-audit section; 61 date references found; sample shows "10-K 2025-10-31" format. `_format_check_source()` confirmed wired end-to-end. SKIPPED rows show "—" as per design. |
| 2   | QA audit table value column shows the raw datum evaluated — `result.value` populated by all threshold evaluator types | ✓ VERIFIED | `coerce_value()` bool-before-int guard confirmed in code. Fresh AAPL run: 20 boolean checks store "True"/"False" strings. 0 spurious 1.0/0.0 float values for boolean checks found. 6 QA-02 tests GREEN. |
| 3   | Every TRIGGERED finding in the red flags HTML section displays the human-readable threshold criterion alongside the finding, sourced from `threshold_context` | ✓ VERIFIED (conditional) | `_load_crf_conditions()` loads 17 CRF conditions. `extract_scoring()` injects `threshold_context` key into all triggered flag dicts. `red_flags.html.j2` renders muted gray italic secondary line when non-empty. 4 QA-04 tests GREEN. Cannot visually verify on AAPL (0 triggered flags on clean company). |
| 4   | Full regression on AAPL, RPM, and TSLA confirms: SKIPPED count is lower than v1.0 baseline of 68, TRIGGERED count on AAPL does not increase, output approved on human review | ✗ FAILED | AAPL fresh run: SKIPPED=68 (unchanged from v1.0). TSLA not run. TRIGGERED=24 (no increase — passes). Human review: completed for AAPL. QA-05 requires SKIPPED to decrease from 68. |

**Score:** 3/4 success criteria verified (SC 4 fails on SKIPPED count and missing TSLA run)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/do_uw/brain/brain_check_schema.py` | `DisplaySpec` with value_format, source_type, threshold_context, deprecation_note; `BrainCheckEntry.display: DisplaySpec \| None` | ✓ VERIFIED | 154 lines (under 500). `class DisplaySpec` present with all 4 fields. `BrainCheckEntry.display` present (line 150–153). |
| `src/do_uw/brain/brain_facet_schema.py` | `FacetSpec` Pydantic model with id, name, display_type, signals, display_config | ✓ VERIFIED | 76 lines (under 100). `class FacetSpec` present with all required fields. `load_facet()` and `load_all_facets()` utility functions present. |
| `src/do_uw/brain/facets/governance.yaml` | Loads as FacetSpec with display_type=scorecard_table, ≥3 GOV.* signals | ✓ VERIFIED | Loads successfully. display_type=scorecard_table. 12 GOV.* signals declared. |
| `src/do_uw/brain/facets/red_flags.yaml` | Loads as FacetSpec with display_type=flag_list, signals=[] | ✓ VERIFIED | Loads successfully. display_type=flag_list. signals=[]. |
| `src/do_uw/stages/analyze/check_helpers.py` | `coerce_value()` with `isinstance(data_value, bool)` guard before int check | ✓ VERIFIED | `isinstance(data_value, bool)` present on line 91. Bool-before-int order confirmed. |
| `src/do_uw/stages/render/html_checks.py` | `_format_check_source()` and `_get_facets()` present; `_group_checks_by_section()` passes filing_date_lookup | ✓ VERIFIED | Both functions present. `_group_checks_by_section()` accepts `filing_date_lookup` param. `_SOURCE_LABELS` imported from `html_footnotes`. |
| `src/do_uw/stages/render/html_renderer.py` | `_build_filing_date_lookup()` present, wired into `build_html_context()` | ✓ VERIFIED | `_build_filing_date_lookup()` on lines 80–103. Called in `build_html_context()` on line 141, result passed to `_group_checks_by_section()`. |
| `src/do_uw/stages/render/md_renderer_helpers_scoring.py` | `_load_crf_conditions()` present; `extract_scoring()` includes `threshold_context` key in red_flags list | ✓ VERIFIED | `_load_crf_conditions()` on lines 18–38. `extract_scoring()` calls it on line 136 and injects `threshold_context` via `crf_conditions.get(rf.flag_id, "")` on line 144. |
| `src/do_uw/templates/html/sections/red_flags.html.j2` | Renders `threshold_context` as muted secondary line when non-empty | ✓ VERIFIED | Lines 34–36: `{% if flag.get('threshold_context') %}<br><span class="text-gray-400 text-xs italic">{{ flag.get('threshold_context') }}</span>{% endif %}` |
| `tests/stages/analyze/test_regression_baseline.py` | Updated SKIPPED_FLOOR and TRIGGERED_CEILING constants | ✗ GAP | `SKIPPED_FLOOR = 68` (NOT lowered from v1.0 baseline). `TRIGGERED_CEILING = 24` (correct). SUMMARY claimed floor was set to 59; the actual code and commit message say 68 and explicitly document no improvement. |
| `tests/stages/render/test_qa_audit_source.py` | 6 QA-01 tests GREEN | ✓ VERIFIED | 6/6 pass GREEN. |
| `tests/stages/render/test_red_flags_template.py` | 4 QA-04 tests GREEN | ✓ VERIFIED | 4/4 pass GREEN (2 original + 2 additional added in Plan 03). |
| `tests/stages/analyze/test_coerce_value_boolean.py` | 6 QA-02 tests GREEN | ✓ VERIFIED | 6/6 pass GREEN. |
| `output/AAPL-2026-02-25/` | Fresh AAPL pipeline run with Phase 48 fixes | ✓ VERIFIED | AAPL_worksheet.html exists. TRIGGERED=24 (no increase). SKIPPED=68 (no decrease). |
| `output/RPM-2026-02-25/` | Fresh RPM pipeline run without errors | ✓ VERIFIED | RPM_worksheet.html exists. |
| `output/TSLA-*/` | Fresh TSLA pipeline run | ✗ MISSING | No TSLA output directory exists. QA-05 and ROADMAP SC 4 both name TSLA explicitly. |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `html_renderer.py` | `html_checks.py` | `_build_filing_date_lookup()` result passed to `_group_checks_by_section()` | ✓ WIRED | Line 141–142 of html_renderer.py: `filing_date_lookup = _build_filing_date_lookup(state)` then `_group_checks_by_section(check_results, filing_date_lookup)`. |
| `html_checks.py` | `html_footnotes.py` | `_SOURCE_LABELS` imported for src_key → form_type label translation | ✓ WIRED | Line 21 of html_checks.py: `from do_uw.stages.render.html_footnotes import _SOURCE_LABELS, _format_trace_source`. Used in `_format_check_source()` line 90. |
| `html_checks.py` | `brain/facets/` | `load_all_facets()` imported and called lazily via `_get_facets()` | ✓ WIRED | Line 15: `from do_uw.brain.brain_facet_schema import load_all_facets`. `_get_facets()` function present at lines 29–34. |
| `md_renderer_helpers_scoring.py` | `brain/red_flags.json` | `_load_crf_conditions()` reads JSON at call time | ✓ WIRED | Path: `Path(__file__).parent.parent.parent / "brain" / "red_flags.json"`. Loads 17 CRF conditions. |
| `red_flags.html.j2` | `extract_scoring()` output | `flag.get('threshold_context')` in template | ✓ WIRED | Template line 34 checks `flag.get('threshold_context')` and renders secondary span if non-empty. |
| `check_helpers.py` | `CheckResult.value` | `coerce_value()` called by threshold evaluators | ✓ WIRED | `isinstance(data_value, bool)` guard present. Verified: fresh AAPL run shows 20 checks with string "True"/"False" values. |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ----------- | ----------- | ------ | -------- |
| QA-01 | 48-01, 48-02 | Source column shows actual filing reference or "WEB (gap)" URL for every evaluated check | ✓ SATISFIED | `_format_check_source()` wired. QA audit HTML shows 61 date references, zero em-dashes in evaluated rows. 6 tests GREEN. |
| QA-02 | 48-01, 48-02 | Value column shows raw datum evaluated — `result.value` populated for all threshold evaluator types | ✓ SATISFIED | `coerce_value()` bool guard present. 20 boolean checks show "True"/"False" strings in fresh AAPL run. 6 tests GREEN. |
| QA-04 | 48-01, 48-03 | TRIGGERED findings in red_flags section display human-readable threshold criterion | ✓ SATISFIED (conditional) | `threshold_context` key in all triggered flag dicts. Template renders muted secondary line. Cannot visually verify on AAPL (no triggered flags). Implementation is correct. |
| QA-05 | 48-04 | Full regression on AAPL, RPM, and TSLA: SKIPPED decreases from 68, TRIGGERED unchanged, human-approved | ✗ BLOCKED | SKIPPED=68 (no decrease). TSLA not run. TRIGGERED=24 (no increase — partial pass). Human approval obtained for AAPL only. |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
| ---- | ------- | -------- | ------ |
| `tests/stages/analyze/test_regression_baseline.py` | `SKIPPED_FLOOR = 68` — comment says "no improvement yet, routing infra in place" contradicts SUMMARY claim | ⚠️ Warning | SUMMARY.md claimed SKIPPED dropped to 59; actual code is 68. This could mislead future verification. |
| `48-04-SUMMARY.md` | "SKIPPED reduced from 68 to 59" — factually incorrect per commit 492dc90 | ⚠️ Warning | SUMMARY documents a claimed 59-check floor that does not exist in any code or output. The summary was written incorrectly. |

### Human Verification Required

None of the automated checks pass in a way that requires additional human review. The gaps are fully automated/measurable:

1. **SKIPPED count check**
   - Test: Run `do-uw analyze AAPL --force` and count SKIPPED status in state.json
   - Expected: SKIPPED < 68
   - Why human: Pipeline requires MCP tools (EdgarTools, Brave Search) not available in automated verification

2. **TSLA regression run**
   - Test: Run `do-uw analyze TSLA --force` and confirm pipeline completes without errors
   - Expected: No Python errors, HTML worksheet exists, TRIGGERED count reasonable
   - Why human: Requires MCP tool execution

### Gaps Summary

**Gap 1: SKIPPED count did not decrease (SC 4, QA-05 blocked)**

QA-05 states "SKIPPED count decreases from baseline 68." The fresh AAPL run after all Phase 47+48 changes shows SKIPPED=68 — identical to the v1.0 baseline. The commit message for 492dc90 explicitly documents: "SKIPPED: 68 — Population B DEF14A checks remain SKIPPED because LLM extraction did not populate new board governance fields." The SUMMARY.md inaccurately claimed the floor was set to 59. The 9-check improvement referenced in the SUMMARY did not materialize.

The root cause is that Phase 47's DEF14A extraction schema (DEF14AExtraction, BoardProfile, FIELD_FOR_CHECK) is structurally complete but the LLM extraction step does not actually populate the new fields from AAPL's actual proxy statement during a live run. The infrastructure exists; the data population does not.

**Gap 2: TSLA regression not run**

QA-05 explicitly requires "AAPL, RPM, and TSLA" confirmation. The ROADMAP SC 4 also names TSLA. No TSLA output exists in the `output/` directory. Plan 04 only mentions AAPL and RPM and does not include a TSLA run task. TSLA was either overlooked or scoped out without updating QA-05 to match.

**What is fully working:** QA-01 (source dates), QA-02 (bool coercion), QA-04 (threshold context schema + template wiring), DisplaySpec + FacetSpec infrastructure, Population A deprecation notes, full test suite (3985 pass, 2 pre-existing failures). Three of four success criteria are satisfied.

**What needs to close the phase:** Either (a) run TSLA regression + diagnose/fix SKIPPED count to get below 68, or (b) formally accept that QA-05 cannot be fully satisfied in Phase 48 scope and document it as a known gap for the next planning cycle.

---

_Verified: 2026-02-25T23:30:00Z_
_Verifier: Claude (gsd-verifier)_
