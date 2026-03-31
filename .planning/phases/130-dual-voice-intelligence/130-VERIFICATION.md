---
phase: 130-dual-voice-intelligence
verified: 2026-03-23T22:15:00Z
status: gaps_found
score: 3/5 success criteria verified
re_verification: false
gaps:
  - truth: "Commentary prompts are free of factor codes and system internals"
    status: failed
    reason: "commentary_prompts.py COMMENTARY_RULES lines 27 and 53 explicitly instruct LLM to cite factor codes ('F.7 = 5/8' and 'F1-F10'). This contradicts D-13 (factor codes banned from main body). LLM output in FUN state.json contains factor codes: F8, F3, F10, F1, F5, F2, F.3, F.1 across governance, scoring, meeting_prep sections."
    artifacts:
      - path: "src/do_uw/stages/benchmark/commentary_prompts.py"
        issue: "Line 27: 'Cite scoring factor references (e.g., F.7 = 5/8)'. Line 53: 'Reference scoring factors where relevant (F1-F10)'. Must be replaced with NEVER-reference rule matching narrative_prompts.py line 22."
    missing:
      - "Replace lines 27 and 53 in commentary_prompts.py with explicit ban on factor codes, matching the pattern already in narrative_prompts.py COMMON_RULES"
      - "Regenerate FUN commentary after prompt fix to verify factor codes are absent from LLM output"
  - truth: "All 8 sections produce non-empty dual-voice commentary"
    status: partial
    reason: "Market and Litigation sections produced empty commentary (0 chars for both what_was_said and underwriting_commentary) in FUN pipeline run. 6/8 sections have real content. The macro gracefully degrades (no crash), but 2 important sections show no dual-voice blocks."
    artifacts:
      - path: "src/do_uw/stages/benchmark/commentary_generator.py"
        issue: "Market and Litigation sections returned empty SectionCommentary. May be data extraction issue (empty section data) or LLM response parsing failure."
    missing:
      - "Investigate why market and litigation commentary is empty for FUN -- check if extract_section_data returns empty dict, if LLM call failed silently, or if parse returned empty strings"
      - "Add logging or warning when a section produces empty commentary despite having state data available"
human_verification:
  - test: "Open FUN HTML worksheet and verify dual-voice blocks are visible with correct styling"
    expected: "Gray factual block and navy commentary block side-by-side in 6+ sections, confidence badges visible"
    why_human: "Visual layout verification -- CSS rendering, color contrast, responsive grid behavior cannot be verified programmatically"
  - test: "Read commentary text and confirm it reads like a senior underwriter's research report"
    expected: "Formal D&O tone, company-specific data in every sentence, no boilerplate or generic phrasing"
    why_human: "Prose quality and professional tone assessment requires human judgment"
---

# Phase 130: Dual-Voice Intelligence Verification Report

**Phase Goal:** Every analytical section reads as underwriting intelligence -- factual data summary ("What Was Said") visually separated from D&O risk interpretation ("Underwriting Commentary"), with the executive summary connecting every finding to specific SCA litigation theories
**Verified:** 2026-03-23T22:15:00Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Opening any analytical section shows two visually distinct blocks: factual summary and underwriting commentary with different styling | VERIFIED | 8 templates contain `dual_voice_block` macro call. CSS: factual=#f8f9fa (gray), commentary=#1a2744 (navy). Macro in `macros/dual_voice.html.j2`. CSS in `components.css` lines 529-597. |
| 2 | Re-rendering without re-running pipeline produces identical commentary from cached state (no additional LLM calls) | VERIFIED | Commentary stored on `state.analysis.pre_computed_commentary` (Pydantic PreComputedCommentary). Cache guard in `_precompute_commentary()` checks `state.analysis.pre_computed_commentary is not None`. FUN state.json confirms 6/8 sections persisted. |
| 3 | Executive summary key negatives each cite finding + magnitude + SCA litigation theory (no factor codes) | VERIFIED | Template uses `<ol>` lists. `_SCA_THEORY_MAP` (10 entries) provides named theories (Section 10(b), Caremark, Tellabs, etc.). `sca_theory` field wired through `assembly_html_extras.py` to `executive_brief.html.j2` line 44-46. |
| 4 | Executive summary key positives cite evidence + quantification + SCA defense theory | VERIFIED | `_SCA_DEFENSE_MAP` (7 entries) with named defenses (PSLRA safe harbor, loss causation defense, etc.). `sca_defense` field rendered at template line 64-66. |
| 5 | Any dollar amount in LLM-generated commentary not matching state data within 2x tolerance is flagged with cross-validation warning | VERIFIED | `validate_narrative_amounts()` called on both `what_was_said` and `underwriting_commentary` in `commentary_generator.py` lines 265-266. Warnings stored in `hallucination_warnings` field. |

**Score:** 5/5 ROADMAP success criteria verified

### Additional Truths (from PLAN must_haves)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| A1 | Commentary generated in BENCHMARK stage via LLM, not in RENDER | VERIFIED | `_precompute_commentary()` at Step 8.5 in `benchmark/__init__.py` line 278-279 |
| A2 | Commentary cached on state and survives serialization | VERIFIED | FUN state.json contains `pre_computed_commentary` with 8 section entries |
| A3 | No "AI Assessment" label in rendered worksheet (HTML, Word, Markdown) | VERIFIED | Removed from narratives.html.j2, word_renderer.py, worksheet.md.j2. Grep confirms zero matches in templates (only CSS class name and MANIFEST.md docs remain). |
| A4 | No factor codes in main body prose | FAILED | commentary_prompts.py lines 27,53 instruct LLM to cite F-codes. FUN output contains F8, F3, F10, F1, F5, F2, F.3, F.1 in generated commentary text. narrative_prompts.py was correctly cleaned (line 22 bans F1-F10) but commentary_prompts.py was not. |
| A5 | Exec summary leads with risk narrative, recommendation comes after | VERIFIED | executive_brief.html.j2: dual-voice block (line 14) -> risk narrative (line 16-28) -> findings (line 30-76) -> recommendation (line 78+) |
| A6 | Recommendation block shows tier + probability + severity + defense cost | VERIFIED | Template lines 83-99 render tier badge, tier_action, claim probability, inherent risk |
| A7 | Every analytical section shows dual-voice blocks when commentary exists | PARTIAL | 8 templates wired. But FUN pipeline produced empty commentary for market and litigation (0 chars). 6/8 sections will show blocks. |

**Score (combined):** 9/12 truths verified, 1 failed, 2 partial

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/models/density.py` | SectionCommentary + PreComputedCommentary models | VERIFIED | Lines 79-110, both classes present with all fields |
| `src/do_uw/stages/benchmark/commentary_generator.py` | generate_all_commentary() | VERIFIED | 310 lines, full implementation with cache, cross-validation, 8 sections |
| `src/do_uw/stages/benchmark/commentary_prompts.py` | build_commentary_prompt() + SECTION_PREFIX_MAP | VERIFIED (with defect) | Present and functional, but COMMENTARY_RULES contains factor code refs |
| `src/do_uw/templates/html/macros/dual_voice.html.j2` | Dual-voice Jinja2 macro | VERIFIED | 25 lines, factual + commentary blocks with confidence badge |
| `src/do_uw/stages/render/context_builders/assembly_commentary.py` | Commentary context builder | VERIFIED | @register_builder decorated, reads PreComputedCommentary, serializes to template dict |
| `src/do_uw/stages/render/context_builders/company_exec_summary.py` | SCA theory/defense maps | VERIFIED | _SCA_THEORY_MAP (10 entries), _SCA_DEFENSE_MAP (7 entries) |
| `tests/models/test_commentary_model.py` | Model serialization tests | VERIFIED | 6 tests passing |
| `tests/stages/benchmark/test_commentary_generator.py` | Generator tests | VERIFIED | 8 tests passing |
| `tests/stages/render/test_exec_summary_overhaul.py` | Exec summary tests | VERIFIED | 24 tests passing |
| `tests/stages/render/test_dual_voice_templates.py` | Template tests | VERIFIED | 39 tests passing |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| benchmark/__init__.py | commentary_generator.py | Step 8.5 _precompute_commentary() | WIRED | Line 279 calls, line 427 imports generate_all_commentary |
| commentary_generator.py | density.py | PreComputedCommentary model | WIRED | Line 24 imports, line 293 instantiates |
| commentary_generator.py | narrative_generator.py | validate_narrative_amounts() | WIRED | Line 33 imports, lines 265-266 call |
| assembly_commentary.py | state.pre_computed_commentary | reads and serializes | WIRED | Line 39 reads pcc, lines 44-49 serialize per section |
| assembly_registry.py | assembly_commentary.py | import at line 109 | WIRED | noqa import ensures builder registration |
| 8 section templates | macros/dual_voice.html.j2 | import + call | WIRED | All 8 templates confirmed with grep |
| company_exec_summary.py | _SCA_THEORY_MAP | enrichment of negatives | WIRED | assembly_html_extras.py lines 139-143 |
| key_findings.html.j2 | sca_theory/sca_defense | template rendering | WIRED | Lines 13-14 (theory), 30-31 (defense) |
| narrative_prompts.py | LLM | ban on factor codes | WIRED | Line 22 bans F1-F10 |
| commentary_prompts.py | LLM | should ban factor codes | NOT WIRED | Lines 27,53 ENCOURAGE factor codes -- contradicts D-13 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| assembly_commentary.py | commentary dict | state.analysis.pre_computed_commentary | Yes -- FUN state.json has 6/8 populated sections | FLOWING (6/8) |
| commentary_generator.py | SectionCommentary | Anthropic LLM API | Yes -- real LLM calls producing content | FLOWING |
| executive_brief.html.j2 | negatives_enriched, positives_enriched | assembly_html_extras.py | Yes -- wired with SCA theory enrichment | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Commentary model serializes | pytest test_commentary_model.py | 6 passed | PASS |
| Commentary generator works | pytest test_commentary_generator.py | 8 passed | PASS |
| Exec summary structure correct | pytest test_exec_summary_overhaul.py | 24 passed | PASS |
| Dual-voice templates wired | pytest test_dual_voice_templates.py | 39 passed | PASS |
| FUN state has commentary | Check state.json pre_computed_commentary | 6/8 sections populated | PARTIAL -- market,litigation empty |
| Factor codes absent from commentary output | Regex scan of FUN state.json commentary | F8,F3,F10,F1,F5,F2,F.3,F.1 found | FAIL |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| VOICE-01 | 130-03 | Every section displays dual-voice blocks | VERIFIED | 8 templates wired with dual_voice_block macro |
| VOICE-02 | 130-01 | Commentary generated via batched LLM in BENCHMARK | VERIFIED | generate_all_commentary() in benchmark Step 8.5 |
| VOICE-03 | 130-01 | Commentary cached in state for deterministic re-render | VERIFIED | PreComputedCommentary on state.analysis, cache guard present |
| VOICE-04 | 130-01 | Cross-validates against XBRL/state data, flags hallucinated amounts | VERIFIED | validate_narrative_amounts() called on both voice blocks |
| EXEC-01 | 130-02 | Executive narrative reads like senior underwriter assessment with SCA theories | VERIFIED | narrative_prompts.py cleaned, SCA theory maps enriching findings |
| EXEC-02 | 130-02 | Key negatives: finding + magnitude + scoring factor ref + litigation theory | VERIFIED (adapted) | Factor codes banned per user override D-13. Negatives show finding + magnitude + SCA theory name instead. |
| EXEC-03 | 130-02 | Key positives: evidence + quantification + SCA defense theory | VERIFIED | sca_defense field from _SCA_DEFENSE_MAP rendered in template |
| EXEC-04 | 130-02 | Recommendation block: tier + probability + severity + defense cost | VERIFIED | executive_brief.html.j2 lines 78-99 render all four elements |

All 8 requirements accounted for. No orphaned requirements.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/do_uw/stages/benchmark/commentary_prompts.py | 27 | `"Cite scoring factor references (e.g., 'F.7 = 5/8')"` -- instructs LLM to emit banned factor codes | BLOCKER | Directly contradicts D-13. Causes factor codes in rendered output. |
| src/do_uw/stages/benchmark/commentary_prompts.py | 53 | `"Reference scoring factors where relevant (F1-F10)"` -- instructs LLM to emit banned factor codes | BLOCKER | Same as above. Must be replaced with NEVER-reference ban. |
| FUN state.json | market section | Empty commentary (0 chars what_was_said + underwriting_commentary) | WARNING | Dual-voice block will not render for market section |
| FUN state.json | litigation section | Empty commentary (0 chars what_was_said + underwriting_commentary) | WARNING | Dual-voice block will not render for litigation section |

### Human Verification Required

### 1. Visual Dual-Voice Block Layout

**Test:** Open FUN HTML worksheet. Scroll through Financial, Governance, Scoring, Company, Executive Brief, Meeting Prep sections.
**Expected:** Each shows side-by-side gray (factual) and navy (commentary) blocks with "What Was Said" / "Underwriting Commentary" headers and confidence badge.
**Why human:** CSS grid rendering, color contrast, and responsive layout require visual confirmation.

### 2. Commentary Prose Quality

**Test:** Read the Financial and Governance commentary text in the rendered worksheet.
**Expected:** Formal D&O underwriting tone. Company-specific data in every sentence. SCA theory references (Section 10(b), Caremark, etc.). No boilerplate.
**Why human:** Prose quality and professional tone assessment.

### 3. Executive Summary Structure

**Test:** Scroll to Executive Brief section in rendered worksheet.
**Expected:** Risk narrative paragraphs FIRST, then numbered key negatives with SCA theories, numbered key positives with SCA defenses, then recommendation block (tier badge + probability + severity).
**Why human:** Layout ordering and visual hierarchy assessment.

## Gaps Summary

Two gaps found, one blocking:

**1. BLOCKER: commentary_prompts.py instructs LLM to emit factor codes.**
The COMMENTARY_RULES in `commentary_prompts.py` (lines 27, 53) explicitly tell the LLM to "Cite scoring factor references (e.g., 'F.7 = 5/8')" and "Reference scoring factors where relevant (F1-F10)". This is the opposite of what D-13 requires. The narrative_prompts.py was correctly cleaned (line 22 bans F1-F10), but the new commentary_prompts.py was created with factor code instructions. As a result, the FUN pipeline output contains factor codes (F8, F3, F10, F1, F5, F2, F.3, F.1) in generated commentary. Fix: replace lines 27 and 53 with the same NEVER-reference ban used in narrative_prompts.py.

**2. WARNING: 2/8 sections produce empty commentary.**
Market and Litigation sections in FUN state.json have zero-length what_was_said and underwriting_commentary. The macro handles this gracefully (no crash), but these sections will show no dual-voice blocks. Root cause unknown -- may be empty section data, LLM failure, or parsing issue. Investigation needed.

---

_Verified: 2026-03-23T22:15:00Z_
_Verifier: Claude (gsd-verifier)_
