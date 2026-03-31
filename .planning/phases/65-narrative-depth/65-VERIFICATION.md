---
phase: 65-narrative-depth
verified: 2026-03-03T19:15:00Z
status: human_needed
score: 4/4 success criteria verified
re_verification: true
  previous_status: gaps_found
  previous_score: 2/4 success criteria (5/7 requirements)
  gaps_closed:
    - "Executive Summary and Scoring sections have Bull Case / Bear Case framing (NARR-02)"
    - "Narratives use confidence-calibrated language: HIGH=confirms, MEDIUM=indicates, LOW=suggests, INFERENCE=pattern may indicate (NARR-03)"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Open output HTML and visually confirm verdict badges appear at the top of each section"
    expected: "Color-coded pill badge (FAVORABLE=emerald, NEUTRAL=blue, CONCERNING=amber, CRITICAL=red) visible before the thesis paragraph in every section"
    why_human: "CSS color rendering and visual badge placement cannot be verified programmatically from template code alone"

  - test: "Open the HTML output and locate the Executive Summary section. Verify the Bull Case / Bear Case two-column grid is present."
    expected: "A green-left-bordered bull case block and red-left-bordered bear case block appear side-by-side below the 5-layer narrative in the Executive Summary section. Each block lists up to 5 items with source tags."
    why_human: "Two-column CSS grid layout and visual color rendering of .bull-case / .bear-case require browser inspection"

  - test: "Open the HTML output and locate the Scoring section. Verify the Bull Case / Bear Case two-column grid is present."
    expected: "Bull/Bear Case framing blocks appear below the 5-layer narrative, above the Scoring Details collapsible, with green/red styling"
    why_human: "Template rendering with real analysis state data requires running a full analysis; layout requires browser inspection"

  - test: "Check that narrative thesis text uses calibrated verbs (not generic 'shows'/'has'/'presents')"
    expected: "Section thesis sentences use 'confirms' (HIGH confidence), 'indicates' (MEDIUM), or 'suggests' (LOW) based on signal_results confidence tiers for that section"
    why_human: "Verb selection depends on real analysis state signal_results data; requires running analysis with known confidence distribution per section"

  - test: "Expand and collapse the Deep Context disclosure in any section"
    expected: "Deep context is hidden by default and expands on click via HTML details/summary element"
    why_human: "Progressive disclosure behavior requires browser interaction to verify"

  - test: "Check SCR block placement in a section where section_narratives is absent (e.g., clear session cache)"
    expected: "When 5-layer data is unavailable, SCR block renders after section heading and D&O implications box renders after narrative"
    why_human: "Fallback rendering requires a state that bypasses the 5-layer path, not testable via static file inspection"
---

# Phase 65: Narrative Depth Verification Report

**Phase Goal:** 5-layer narrative architecture, bull/bear framing, confidence-calibrated language, progressive disclosure.
**Verified:** 2026-03-03T19:15:00Z
**Status:** human_needed
**Re-verification:** Yes — after gap closure (65-02-PLAN.md executed)

## Gap Closure Summary

The previous verification (2026-03-03T12:30:00Z) found two gaps:

| Gap | Previous Status | Current Status |
|-----|----------------|----------------|
| NARR-02: Bull/Bear framing | FAILED — 65-02-PLAN.md never created | CLOSED — 65-02 executed, code verified, 24 tests pass |
| NARR-03: Confidence-calibrated language | FAILED — no verb mapping existed | CLOSED — CONFIDENCE_VERBS dict + calibrate_verb() + _build_thesis() integration verified |

**No regressions.** All 79 previously passing narrative tests still pass.

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Every section starts with color-coded verdict badge | VERIFIED | `verdict_badge` macro in badges.html.j2; imported in base.html.j2 line 10; 9 section templates call `narrative_5layer` which renders verdict badge as Layer 1 |
| 2 | Executive summary has bull/bear cases | VERIFIED | `bull_bear_framing` macro in narratives.html.j2 line 125; executive.html.j2 lines 33-36 call `bull_bear_framing(bull_bear_data.executive_summary)`; `_bull_bear.py:extract_bull_bear_cases()` wired into html_renderer.py line 298 |
| 3 | Narratives use confidence-appropriate verbs | VERIFIED | `CONFIDENCE_VERBS = {HIGH: confirms, MEDIUM: indicates, LOW: suggests, INFERENCE: pattern may indicate}` in _bull_bear.py lines 19-24; `_build_thesis()` in narrative.py line 371 calls `calibrate_verb(derive_section_confidence(state, section_id))`; 24 tests all pass |
| 4 | Deep context hidden by default, expandable | VERIFIED | `narrative_5layer` macro uses HTML `<details>/<summary>` element at line 93; CSS `.narrative-deep` class confirmed present at line 474 of components.css |

**Score:** 4/4 success criteria verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/context_builders/_bull_bear.py` | Bull/bear extraction + confidence verb mapping | VERIFIED | 199 lines (under 200 limit); exports `CONFIDENCE_VERBS`, `calibrate_verb`, `calibrate_narrative_text`, `derive_section_confidence`, `extract_bull_bear_cases` |
| `src/do_uw/templates/html/components/narratives.html.j2` | `bull_bear_framing` macro | VERIFIED | Lines 125-150; renders two-column grid with `.bull-bear-grid`, `.bull-case`, `.bear-case` classes; uses `entries` key (not `items`) for Jinja2 compatibility |
| `tests/stages/render/test_bull_bear.py` | 24 tests for verbs, extraction, templates | VERIFIED | 366 lines; 24 tests; all pass (0.47s); covers TestConfidenceVerbs (10), TestDeriveConfidence (3), TestBullBearExtraction (6), TestBullBearTemplate (4) |
| `src/do_uw/stages/render/context_builders/narrative.py` | confidence-calibrated `_build_thesis()` | VERIFIED | 467 lines (under 500 limit); line 367 lazy-imports `calibrate_verb, derive_section_confidence`; line 371 calls `calibrate_verb(derive_section_confidence(state, section_id))` |
| `src/do_uw/templates/html/sections/executive.html.j2` | Bull/bear call after 5-layer block | VERIFIED | Lines 33-36: `{% if bull_bear_data is defined and bull_bear_data.get('executive_summary') %} {{ bull_bear_framing(bull_bear_data.executive_summary) }}` |
| `src/do_uw/templates/html/sections/scoring.html.j2` | Bull/bear call after 5-layer block | VERIFIED | Lines 34-37: `{% if bull_bear_data is defined and bull_bear_data.get('scoring') %} {{ bull_bear_framing(bull_bear_data.scoring) }}` |
| `src/do_uw/templates/html/components.css` | Bull/bear grid CSS | VERIFIED | 500 lines (at limit); lines 492-500: `.bull-bear-grid`, `.bull-case`, `.bear-case`, `.case-header`, `.bull-header`, `.bear-header`, `.case-items`, severity classes; line 445: print break-inside rule added |
| `src/do_uw/templates/html/base.html.j2` | `bull_bear_framing` imported | VERIFIED | Line 10: `{% from "components/narratives.html.j2" import section_narrative, evidence_chain, narrative_5layer, bull_bear_framing with context %}` |
| `src/do_uw/stages/render/context_builders/__init__.py` | `extract_bull_bear_cases` exported | VERIFIED | Lines 55-57 import from `._bull_bear`; line 67 in `__all__` |

Previously verified artifacts (regression check — all still present and wired):

| Artifact | Previous Status | Regression Check |
|----------|----------------|-----------------|
| `src/do_uw/brain/narratives/__init__.py` | VERIFIED | PASS — unchanged |
| `src/do_uw/brain/narratives/*.yaml` (12 files) | VERIFIED | PASS — unchanged |
| `src/do_uw/templates/html/components/badges.html.j2` | VERIFIED | PASS — unchanged |
| `src/do_uw/stages/render/html_renderer.py` | VERIFIED | PASS — `_extract_bb` import and `bull_bear_data` context line 297-298 added cleanly |
| `tests/stages/render/test_5layer_narrative.py` | VERIFIED (66 tests) | PASS — 66 tests still pass |
| `tests/stages/render/test_narrative_context.py` | VERIFIED (13 tests) | PASS — 13 tests still pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `html_renderer.py` | `_bull_bear.py:extract_bull_bear_cases` | import at line 57 + call at line 298 | WIRED | `context["bull_bear_data"] = _extract_bb(state)` |
| `executive.html.j2` | `bull_bear_data` context variable | `bull_bear_data.get('executive_summary')` at line 34 | WIRED | Template guard + macro call confirmed |
| `scoring.html.j2` | `bull_bear_data` context variable | `bull_bear_data.get('scoring')` at line 35 | WIRED | Template guard + macro call confirmed |
| `narrative.py:_build_thesis` | `_bull_bear.py:calibrate_verb` | lazy import at line 367, call at line 371 | WIRED | `verb = calibrate_verb(derive_section_confidence(state, section_id))` |
| `base.html.j2` | `bull_bear_framing` macro | `{% from "components/narratives.html.j2" import ... bull_bear_framing with context %}` at line 10 | WIRED | Confirmed |
| All previously verified links | (see previous report) | — | WIRED | No regressions detected |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| NARR-01 | 65-01 | 5-layer narrative: Verdict > Thesis > Evidence Grid > Implications > Deep Context | SATISFIED | `narrative_5layer` macro wired in 9 section templates; 66 tests pass |
| NARR-02 | 65-02 | Bull Case / Bear Case framing for Executive Summary and Scoring | SATISFIED | `extract_bull_bear_cases()` in _bull_bear.py; `bull_bear_framing` macro in narratives.html.j2; wired in html_renderer.py:298; present in executive.html.j2:33-36 and scoring.html.j2:34-37; 24 tests pass |
| NARR-03 | 65-02 | Confidence-calibrated language: HIGH=confirms, MEDIUM=indicates, LOW=suggests | SATISFIED | `CONFIDENCE_VERBS` dict in _bull_bear.py:19-24; `calibrate_verb()` at line 34; integrated into `_build_thesis()` in narrative.py:371; 10 verb tests pass |
| NARR-04 | 65-03 | SCR framework (Situation-Complication-Resolution) per section | SATISFIED | `extract_scr_narratives()` in narrative.py; `scr_narrative` macro in callouts.html.j2; wired in html_renderer.py; present in 8 section templates (fallback branch) |
| NARR-05 | 65-01 | Progressive disclosure: Glance (badge+1 line), Standard (thesis+evidence), Deep (collapsible) | SATISFIED | Layer structure in `narrative_5layer` macro; `<details>/<summary>` HTML for collapsible Layer 3 |
| NARR-06 | 65-03 | D&O-specific implications callout box in every section | SATISFIED | `extract_do_implications()` in narrative.py; `do_implications` macro in callouts.html.j2; wired in html_renderer.py; present in 8 section templates (fallback branch) |
| NARR-07 | 65-01 | Narrative templates in `brain/narratives/` YAML, not hardcoded strings | SATISFIED | 12 YAML files in `src/do_uw/brain/narratives/`; `load_narrative_config()` with LRU cache; all 12 validated |

**Note:** REQUIREMENTS.md status tracking table (lines 155-161) still shows NARR-02 and NARR-03 as "Pending" — this is a stale tracking artifact only. The `[x]` checkbox list at lines 85-86 correctly shows both as complete, and code verification confirms both requirements are fully implemented. The status table should be updated to "Complete" for NARR-02 and NARR-03.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/do_uw/stages/render/html_renderer.py` | — | 539 lines (over 500-line anti-context-rot limit) | Warning | Pre-existing condition (521 lines before phase 65; grew to 539 across three plans). Not introduced by this phase. |
| `src/do_uw/templates/html/components.css` | — | Exactly 500 lines (at limit) | Info | At the anti-context-rot limit. Any future additions to this file must refactor or split first. |

No TODO/FIXME/PLACEHOLDER comments found in any phase 65 files. No empty implementations found.

### Human Verification Required

#### 1. Verdict Badge Visual Rendering

**Test:** Run `python -m do_uw analyze AAPL` and open the output HTML. Inspect Section 1 (Executive Summary).
**Expected:** A color-coded pill badge appears at the top of the section before any narrative text. Badge color corresponds to risk tier (emerald for FAVORABLE, amber for CONCERNING, red for CRITICAL).
**Why human:** CSS color rendering and badge visual placement require browser inspection.

#### 2. Bull/Bear Case Grid in Executive Summary

**Test:** Open the HTML output and locate Section 1 (Executive Summary). Look below the 5-layer narrative block.
**Expected:** A two-column grid appears with a green-left-bordered "Bull Case" block on the left and a red-left-bordered "Bear Case" block on the right. Each block lists up to 5 items with source tags in light italic. HIGH severity bear items appear in dark red; MEDIUM in amber.
**Why human:** Two-column CSS grid layout and green/red color rendering require browser inspection.

#### 3. Bull/Bear Case Grid in Scoring Section

**Test:** Open the HTML output and locate Section 7 (Scoring & Risk Assessment). Look below the 5-layer narrative block, above the "Scoring Details" collapsible.
**Expected:** Bull/Bear Case framing blocks appear with the same two-column green/red layout as in the Executive Summary.
**Why human:** Requires running a full analysis with real state data that populates `section_densities` or `peril_map` (empty states return no bull/bear data).

#### 4. Confidence-Calibrated Verb in Thesis Text

**Test:** Open the HTML output. Read the one-line thesis sentence next to the verdict badge in any section (e.g., Governance). Compare the verb used to the expected confidence mapping.
**Expected:** If the governance section has predominantly HIGH-confidence signals, the thesis reads "Governance confirms..." (not "indicates" or "suggests"). Sections with LOW-confidence data read "suggests".
**Why human:** Verb selection depends on `signal_results` confidence annotations from real analysis data; requires a run with known confidence distribution per section.

#### 5. Progressive Disclosure (Deep Context Collapse)

**Test:** Open the HTML output, find any section with a narrative, click the "Deep Context & Implications" collapsible element.
**Expected:** The deep context block is hidden by default (collapsed), and clicking it expands to show the full assessment and SCR framework text.
**Why human:** HTML `details`/`summary` interactive behavior requires browser interaction.

#### 6. SCR Block Fallback Rendering

**Test:** Temporarily set `section_narratives = {}` in context (or clear analysis state) and render the executive section.
**Expected:** The SCR (Situation / Complication / Resolution) block renders after the section heading, before narrative text. The D&O implications callout box renders after the narrative.
**Why human:** The fallback branch only activates when `section_narratives` is empty/undefined; testing requires a controlled state manipulation.

---

## Full Test Suite Results

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/stages/render/test_bull_bear.py` | 24 | PASS (24/24) |
| `tests/stages/render/test_5layer_narrative.py` | 66 | PASS (66/66) |
| `tests/stages/render/test_narrative_context.py` | 13 | PASS (13/13) |
| **Phase 65 total** | **103** | **PASS (103/103)** |

---

_Verified: 2026-03-03T19:15:00Z_
_Verifier: Claude (gsd-verifier)_
_Re-verification after 65-02 gap closure_
