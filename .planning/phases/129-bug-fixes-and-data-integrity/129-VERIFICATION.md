---
phase: 129-bug-fixes-and-data-integrity
verified: 2026-03-22T00:00:00Z
status: gaps_found
score: 9/11 must-haves verified
re_verification: false
gaps:
  - truth: "SCA count is identical in executive brief, key stats, monitoring triggers, litigation section, meeting prep, and narrative sections for any given ticker"
    status: failed
    reason: "key_stats_context.py line 264 counts ALL genuine SCAs (including settled/dismissed) using inline _is_regulatory_not_sca, not count_active_genuine_scas(). This will diverge from all other sections when a company has historical settled SCAs."
    artifacts:
      - path: "src/do_uw/stages/render/context_builders/key_stats_context.py"
        issue: "Line 264: r['sca_count'] = str(len([s for s in all_scas if not _is_regulatory_not_sca(s)])) — no status filter; counts settled/dismissed SCAs as active"
    missing:
      - "Replace line 264 in key_stats_context.py with: from do_uw.stages.render.sca_counter import count_active_genuine_scas; r['sca_count'] = str(count_active_genuine_scas(state))"
  - truth: "Plan 02 key link: narrative_data_sections.py passes XBRL-reconciled revenue values (verifiable by pattern 'xbrl|reconcil' in file)"
    status: partial
    reason: "narrative_data_sections.py uses state.extracted.financials.statements.income_statement.line_items which ARE the XBRL-reconciled data path, but no 'xbrl' or 'reconcil' string appears in the file. The plan's key_link pattern check fails literally, though the data path is architecturally correct."
    artifacts:
      - path: "src/do_uw/stages/benchmark/narrative_data_sections.py"
        issue: "No 'xbrl' or 'reconcil' reference; key link pattern fails. FIX-01 origin comment is in narrative_generator.py but not propagated here."
    missing:
      - "Add a comment in narrative_data_sections.py extract_financial() noting that fin.statements values are XBRL-reconciled (Phase 128), so no raw LLM fallback is used"
human_verification:
  - test: "Run underwrite AAPL --fresh and verify no $383B revenue figure appears anywhere in output"
    expected: "Revenue figures match XBRL-reconciled values (~$394B for AAPL FY2024)"
    why_human: "LLM cross-validation logs NARRATIVE_HALLUCINATION_FLAG warnings but does not auto-replace — actual output review required"
  - test: "Run underwrite AAPL --fresh and confirm Jennifer Newstead (not Kate Adams) appears as GC"
    expected: "General Counsel shown as Jennifer Newstead in leadership/governance section"
    why_human: "Prompt fix requires --fresh run to bypass LLM extraction cache; prompt hash not in cache key"
  - test: "Run underwrite AAPL --fresh and confirm board gender diversity percentage is displayed"
    expected: "Board composition section shows percentage of female directors"
    why_human: "DEF 14A prompt enhanced but LLM extraction cache invalidation requires fresh run"
---

# Phase 129: Bug Fixes and Data Integrity — Verification Report

**Phase Goal:** Known data quality bugs are eliminated -- no hallucinated revenue figures, no misclassified enforcement actions, no stale extraction data, no inconsistent SCA counts across sections
**Verified:** 2026-03-22
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | SCA count is identical in executive brief, key stats, monitoring triggers, litigation section, meeting prep, and narrative sections | FAILED | `key_stats_context.py:264` counts ALL genuine SCAs (no status filter) while all other sections use `count_active_genuine_scas()` |
| 2 | CRF insolvency trigger does not fire for companies with healthy balance sheets (Altman Z > 3.0) | VERIFIED | `should_suppress_insolvency()` in `red_flag_gates.py:33` wired to all 3 CRF suppression sites via delegation wrappers |
| 3 | CRF ceiling values displayed in HTML match size-resolved values from apply_crf_ceilings | VERIFIED | `crf_bar_context.py`, `assembly_registry.py`, `scoring.py` all delegate to canonical; 3 ceiling display tests pass |
| 4 | AAPL worksheet shows no $383B services revenue figure anywhere in output (programmatic prevention) | VERIFIED | `validate_narrative_amounts()` in `narrative_generator.py:138` cross-validates all LLM dollar amounts against XBRL state values with 2x threshold |
| 5 | No DOJ_FCPA case appears in the securities class actions section of any worksheet | VERIFIED | `narrative_data_sections.py:11` and `narrative_data.py:23` both import `get_active_genuine_scas`/`count_active_genuine_scas` which call `_is_regulatory_not_sca`; DOJ_FCPA entries are filtered |
| 6 | Board composition includes gender diversity percentage derived from DEF 14A | VERIFIED | `def14a.py:67` has `board_gender_diversity_pct: float | None`; `prompts.py:92` explicitly requests it |
| 7 | Current GC shows Jennifer Newstead (not Kate Adams) for AAPL | VERIFIED (prompt) | `prompts.py:96` asks for CURRENT GC; requires `--fresh` run to bypass extraction cache (noted in SUMMARY) |
| 8 | Meeting prep questions reference company-specific findings (dollar amounts, names, dates) | VERIFIED | `_company_name()` helper in `meeting_questions.py:41` used at 6 injection sites; zero generic "the company" in question templates |
| 9 | Every meeting prep question contains at least one company-specific data point from AnalysisState | VERIFIED | 10 specificity tests pass confirming company name, amounts, factor scores injected |
| 10 | Meeting prep SCA count matches the canonical count from sca_counter.py | VERIFIED | `meeting_questions.py:19` and `meeting_prep.py:43` both import from `sca_counter` |
| 11 | narrative_data_sections.py passes XBRL-reconciled revenue to LLM prompt (verifiable by explicit xbrl/reconcil reference) | PARTIAL | Data path is correct (uses `fin.statements` which holds XBRL-reconciled values) but no explicit 'xbrl'/'reconcil' string in file; key link pattern fails |

**Score:** 9/11 truths verified (1 failed, 1 partial)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/sca_counter.py` | Canonical `get_active_genuine_scas()` and `count_active_genuine_scas()` | VERIFIED | 73 lines; both functions defined at lines 21 and 65 |
| `src/do_uw/stages/score/red_flag_gates.py` | `def should_suppress_insolvency` | VERIFIED | Defined at line 33 |
| `tests/render/test_sca_count_consistency.py` | 12+ SCA consistency tests (min 40 lines) | VERIFIED | 173 lines, 12 tests, all pass |
| `tests/render/test_crf_insolvency_suppression.py` | 7+ insolvency suppression tests (min 30 lines) | VERIFIED | 102 lines, 7 tests, all pass |
| `tests/render/test_crf_ceiling_display.py` | Ceiling display tests (min 20 lines) | VERIFIED | 140 lines, 3 tests, all pass |
| `src/do_uw/stages/benchmark/narrative_generator.py` | `cross_validate` or `validate_narrative_amounts` function | VERIFIED | `validate_narrative_amounts()` defined at line 138 |
| `tests/benchmark/test_narrative_validation.py` | Narrative dollar validation tests (min 30 lines) | VERIFIED | 154 lines, 6 tests, all pass |
| `tests/extract/test_governance_extraction.py` | Gender diversity and GC extraction tests (min 30 lines) | VERIFIED | 100 lines, 8 tests, all pass |
| `src/do_uw/stages/render/sections/meeting_questions.py` | Company-specific question generators | VERIFIED | `_company_name()` helper, `state.company` references, 6 injection sites |
| `tests/render/test_meeting_prep_specificity.py` | Specificity tests (min 40 lines) | VERIFIED | 280 lines, 10 tests, all pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `sect1_findings_data.py` | `sca_counter.py` | `from do_uw.stages.render.sca_counter import count_active_genuine_scas` | WIRED | Line 222 (lazy import) |
| `monitoring_context.py` | `sca_counter.py` | `from do_uw.stages.render.sca_counter import count_active_genuine_scas` | WIRED | Line 36 (lazy import) |
| `crf_bar_context.py` | `red_flag_gates.py` | `from do_uw.stages.score.red_flag_gates import should_suppress_insolvency` | WIRED | Line 55 (lazy import inside condition) |
| `assembly_registry.py` | `red_flag_gates.py` | `from do_uw.stages.score.red_flag_gates import should_suppress_insolvency` | WIRED | Line 66 (lazy import); `_should_suppress_insolvency_crf` delegates to canonical |
| `scoring.py` | `red_flag_gates.py` | `from do_uw.stages.score.red_flag_gates import should_suppress_insolvency` | WIRED | Lines 42 and 62; `_should_suppress_insolvency_crf_flag` delegates to canonical |
| `narrative_generator.py` | `xbrl_llm_reconciler.py` | Uses XBRL-reconciled values for cross-validation | PARTIAL | Comment at line 110 references XBRL reconciler; no direct import. Cross-validation runs against values from `state.extracted.financials.statements` which ARE the reconciled path, but not via direct import |
| `narrative_data_sections.py` | `state.extracted.financials` | Passes XBRL-reconciled revenue to LLM prompt | PARTIAL | Uses `fin.statements.income_statement.line_items` (XBRL-reconciled); no literal 'xbrl'/'reconcil' string |
| `meeting_questions.py` | `state.extracted` | Reads specific risk findings from state | WIRED | `state.company`, `state.scoring`, `state.extracted.governance` all accessed |
| `meeting_prep.py` | `sca_counter.py` | `from do_uw.stages.render.sca_counter import count_active_genuine_scas` | WIRED | Line 43 |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| FIX-01 | 129-02 | Eliminates $383B services revenue hallucination and DOJ_FCPA misclassification | VERIFIED | `validate_narrative_amounts()` in narrative_generator; canonical SCA counter in narrative_data.py and narrative_data_sections.py |
| FIX-02 | 129-02 | Fixes extraction gaps: gender diversity, board profiles, GC succession | VERIFIED (prompt) | `board_gender_diversity_pct` field in def14a.py; prompt enhanced; board completeness check in board_parsing.py |
| FIX-03 | 129-03 | Company-specific meeting prep questions tied to actual risk findings | VERIFIED | `_company_name()` helper; 6 injection sites; zero generic templates; 10 tests |
| FIX-04 | 129-01 | Resolves SCA count inconsistencies across sections | FAILED | `key_stats_context.py:264` still uses inline count-all (no status filter), diverges from canonical active count |
| FIX-05 | 129-01 | Suppresses stale CRF insolvency trigger; correct CRF ceiling display | VERIFIED | `should_suppress_insolvency()` canonical; 3 suppression sites delegate; 10 insolvency+ceiling tests pass |

**Orphaned requirements:** None. All 5 FIX requirements are claimed by plans and present in REQUIREMENTS.md traceability table.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/do_uw/stages/render/context_builders/key_stats_context.py` | 261-264 | `_is_regulatory_not_sca` without status filter — counts ALL genuine SCAs | Blocker | FIX-04 goal not achieved: key_stats `sca_count` includes settled/dismissed SCAs, diverges from canonical active count in all other sections |
| `src/do_uw/stages/render/context_builders/_key_stats_helpers.py` | 285-288 | `_is_regulatory_not_sca` to build "X on record" display — intentionally all-genuine | Info | Legitimately different semantics (shows total on record, not active count); consistent with Plan 01 decision |
| `src/do_uw/stages/render/sections/sect6_litigation.py` | 282-292 | `_is_regulatory_not_sca` with explicit status filter matching canonical | Info | Legitimate: `sect6_litigation` filters separately for active vs. settled display rows |
| `src/do_uw/stages/score/factor_data.py` | 99-109 | `_is_regulatory_not_sca` with manual status criteria matching canonical | Info | Legitimate: uses same status set as sca_counter._ACTIVE_STATUSES (documented in comment at line 107) |
| `src/do_uw/stages/score/pattern_fields.py` | 379-395 | `_is_regulatory_not_sca` with manual status criteria | Info | Legitimate: comment at line 376 says "Uses the same status set and regulatory filter as sca_counter.py" |

### Human Verification Required

#### 1. Revenue Hallucination Prevention — End-to-End

**Test:** Run `underwrite AAPL --fresh` and search the output HTML for any revenue figure containing "383"
**Expected:** No $383B figure; revenue shown as XBRL-reconciled value (~$394B for FY2024)
**Why human:** `validate_narrative_amounts()` logs `NARRATIVE_HALLUCINATION_FLAG` warnings but does NOT auto-replace values (conservative approach per Plan 02 decision). Human must verify the pipeline run to confirm flagging or absence.

#### 2. Jennifer Newstead GC Succession — Cache Invalidation Required

**Test:** Run `underwrite AAPL --fresh` and check the governance/leadership section
**Expected:** General Counsel shown as Jennifer Newstead (not Kate Adams)
**Why human:** The DEF 14A LLM extraction cache is keyed by (accession, form_type, schema_version), NOT by prompt content. Prompt enhancement only takes effect on `--fresh` run. Cannot verify programmatically without an actual pipeline run.

#### 3. Gender Diversity Display

**Test:** Run `underwrite AAPL --fresh` and check board composition section
**Expected:** Female director count and board_gender_diversity_pct displayed
**Why human:** Schema and prompt are enhanced; actual rendering depends on LLM extraction producing non-null `board_gender_diversity_pct` on a fresh run.

### Gaps Summary

**Two gaps found:**

**Gap 1 (Blocker — FIX-04):** `key_stats_context.py` still uses an inline SCA count that lacks the status filter. Line 264 counts ALL genuine SCAs regardless of status (active, pending, settled, dismissed) by only applying `_is_regulatory_not_sca`. This diverges from the canonical `count_active_genuine_scas()` which restricts to ACTIVE/PENDING/N/A/None statuses. Any company with a historical settled SCA will show a higher count in the Key Stats section than in the Executive Brief, Monitoring Triggers, and Meeting Prep sections. This directly contradicts the FIX-04 requirement and the phase goal ("no inconsistent SCA counts across sections").

The fix is a one-line change: replace line 264's inline filter with `count_active_genuine_scas(state)`. The Plan 01 SUMMARY describes "Rewired 5 direct active-count call sites" but `key_stats_context.py` was listed as a required rewire target in the Plan and was not completed.

**Gap 2 (Warning — FIX-01 traceability):** `narrative_data_sections.py` uses the correct XBRL-reconciled data path for financial figures (`fin.statements.income_statement.line_items`) but contains no explicit comment documenting that these are the XBRL-reconciled values. The Plan 02 key link pattern `xbrl|reconcil` fails literally. The functional behavior is correct, but a future developer could accidentally substitute raw LLM-extracted values without knowing this matters. A single comment line would satisfy this traceability requirement.

**Root cause for Gap 1:** The Plan 01 SUMMARY documents a decision that "sites that count all genuine SCAs regardless of status... have legitimately different semantics" — but `key_stats_context.py`'s `sca_count` field is meant to represent the same active-SCA count shown elsewhere, not a "total on record" display. This conflates two semantically distinct use cases.

---

_Verified: 2026-03-22_
_Verifier: Claude (gsd-verifier)_
