---
phase: 48-output-quality-hardening
plan: "03"
subsystem: render/brain
tags: [QA-04, threshold_context, red_flags, deprecation_note, population_a, brain_yaml]
dependency_graph:
  requires: [48-01]
  provides: [QA-04-threshold-context, population-a-deprecation-markers]
  affects: [red_flags_section, md_renderer_helpers_scoring, brain_check_schema]
tech_stack:
  added: []
  patterns:
    - _load_crf_conditions() module-level helper reads red_flags.json at call time (non-fatal on failure)
    - display.deprecation_note field on BrainCheckEntry marks permanently unanswerable Population A checks
    - threshold_context key added to extract_scoring() red_flags list dicts (QA-04 pattern)
key_files:
  created: []
  modified:
    - src/do_uw/stages/render/md_renderer_helpers_scoring.py
    - src/do_uw/templates/html/sections/red_flags.html.j2
    - src/do_uw/brain/checks/fwrd/warn_ops.yaml
    - src/do_uw/brain/checks/fwrd/warn_sentiment.yaml
    - src/do_uw/brain/checks/exec/profile.yaml
    - src/do_uw/brain/checks/nlp/nlp.yaml
    - src/do_uw/brain/checks/gov/effect.yaml
    - tests/stages/render/test_red_flags_template.py
decisions:
  - "[48-03]: _load_crf_conditions() is module-level (not inline) so it can be tested independently"
  - "[48-03]: threshold_context key added to all triggered flag dicts — empty string for unknown CRF IDs (not KeyError)"
  - "[48-03]: FWRD.WARN checks split across 3 files (warn_ops/warn_sentiment/warn_tech) — plan frontmatter had single warn.yaml which does not exist"
  - "[48-03]: deprecation_note placed before gap_bucket in YAML entries — display: block is additive, brain build unaffected"
  - "[48-03]: Test mock fixed to use state.scoring (not state.analysis.scoring) — extract_scoring() accesses state.scoring per AnalysisState model"
  - "[48-03]: 2 additional test cases added (test_load_crf_conditions_returns_dict, test_load_crf_conditions_crf01_has_condition)"
metrics:
  duration: 370s
  completed: 2026-02-25
  tasks: 2
  files: 8
---

# Phase 48 Plan 03: QA-04 Threshold Context Display + Population A Deprecation Notes Summary

CRF condition text now displays as muted italic secondary line below each triggered red flag in the HTML worksheet; 19 Population A brain YAML checks marked with display.deprecation_note for future retirement.

## What Was Built

### Task 1: threshold_context in extract_scoring() and red_flags.html.j2

Added `_load_crf_conditions()` helper to `md_renderer_helpers_scoring.py` that reads `brain/red_flags.json` at call time and returns a `dict[str, str]` mapping CRF IDs to condition text (e.g., `"CRF-01"` → `"Company has pending securities class action lawsuit"`). Returns an empty dict on any failure — non-fatal by design.

Updated `extract_scoring()` to call `_load_crf_conditions()` and inject `threshold_context` into each entry in the `red_flags` list. Unknown CRF IDs get an empty string (no KeyError).

Updated `red_flags.html.j2` to render `threshold_context` as a `<br><span class="text-gray-400 text-xs italic">` secondary line below the flag description cell, visible only when non-empty. Style is muted (gray, italic) per QA-04 spec.

Fixed Wave 0 test mock: The scaffold used `state.analysis.scoring.red_flags` but `extract_scoring()` accesses `state.scoring`. Updated mock to configure `state.scoring` directly with proper numeric values to avoid MagicMock format errors.

Added 2 additional test cases:
- `test_load_crf_conditions_returns_dict` — verifies >= 10 CRF entries loaded
- `test_load_crf_conditions_crf01_has_condition` — verifies CRF-01 has non-empty condition

### Task 2: Population A deprecation_note backfill

Added `display:` blocks with `deprecation_note` to all 19 Population A brain YAML checks:

| File | Checks | Count | Reason |
|------|--------|-------|--------|
| fwrd/warn_ops.yaml | cfpb_complaints, fda_medwatch, nhtsa_complaints | 3 | Requires regulatory complaint databases (CFPB, FDA, NHTSA) |
| fwrd/warn_sentiment.yaml | glassdoor, indeed, blind, linkedin_headcount/departures, g2, trustpilot, app_ratings, social_sentiment, journalism_activity | 10 | Requires third-party sentiment/review platform data |
| exec/profile.yaml | EXEC.CEO.risk_score, EXEC.CFO.risk_score | 2 | Requires proprietary executive risk scoring (Kroll-style) |
| nlp/nlp.yaml | NLP.FILING.late_filing, NLP.FILING.filing_timing_change | 2 | Requires NLP pipeline not implemented |
| gov/effect.yaml | GOV.EFFECT.iss_score, GOV.EFFECT.proxy_advisory | 2 | Already had deprecation_note; updated to match plan spec |

Note: Plan frontmatter referenced `fwrd/warn.yaml` (single file) and `nlp/filing.yaml` which do not exist. Actual files are `fwrd/warn_ops.yaml`, `fwrd/warn_sentiment.yaml`, `fwrd/warn_tech.yaml`, and `nlp/nlp.yaml`. Applied deprecation_note to all checks with `gap_bucket: intentionally-unmapped` in FWRD.WARN domain = 13 checks (matching plan's "all 13 are Population A").

## Verification Results

1. `test_red_flags_template.py` — 4/4 tests PASS (GREEN)
2. Full render test suite: 280/280 PASS, no regressions
3. `_load_crf_conditions()`: 17 CRF conditions loaded (>= 10 required)
4. YAML syntax: all 6 files valid, brain build exits 0
5. `md_renderer_helpers_scoring.py`: 410 lines (under 500 limit)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test mock targeted wrong state attribute path**
- **Found during:** Task 1 test execution
- **Issue:** Wave 0 test scaffold used `state.analysis.scoring.red_flags` but `extract_scoring()` accesses `state.scoring` (top-level field per AnalysisState model)
- **Fix:** Updated mock helper `_make_mock_state_with_red_flag()` to configure `state.scoring` with proper numeric attrs; MagicMock auto-format errors resolved
- **Files modified:** `tests/stages/render/test_red_flags_template.py`
- **Commit:** 04b3439

**2. [Rule 2 - Missing functionality] Additional _load_crf_conditions() test cases**
- **Found during:** Task 1 implementation
- **Issue:** Wave 0 tests only tested extract_scoring() behavior, not _load_crf_conditions() directly
- **Fix:** Added 2 additional test cases to verify the helper loads correctly and CRF-01 has non-empty condition
- **Files modified:** `tests/stages/render/test_red_flags_template.py`
- **Commit:** 04b3439

**3. [Rule 3 - Blocking] Plan referenced non-existent YAML files**
- **Found during:** Task 2 file lookup
- **Issue:** Plan frontmatter listed `fwrd/warn.yaml` and `nlp/filing.yaml` which do not exist; actual files are warn_ops/warn_sentiment/warn_tech and nlp/nlp.yaml
- **Fix:** Applied deprecation_note to the correct actual files, covering all 13 intentionally-unmapped FWRD.WARN checks as intended
- **Commit:** 4259305

## Self-Check: PASSED

| Item | Status |
|------|--------|
| md_renderer_helpers_scoring.py exists | FOUND |
| red_flags.html.j2 exists | FOUND |
| 48-03-SUMMARY.md exists | FOUND |
| Commit 04b3439 (Task 1) | FOUND |
| Commit 4259305 (Task 2) | FOUND |
| _load_crf_conditions in source | FOUND |
| threshold_context in template | FOUND |
| deprecation_note in warn_ops.yaml | FOUND |
