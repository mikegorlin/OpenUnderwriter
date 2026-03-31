---
phase: 140-litigation-classification-consolidation
verified: 2026-03-28T03:19:18Z
status: gaps_found
score: 8/12 must-haves verified
re_verification: false
gaps:
  - truth: "The litigation section in the rendered worksheet shows case type labels derived from legal theories, not data source names"
    status: partial
    reason: "Word renderer (primary output) fully shows legal-theory-based labels via direct CaseDetail reads. HTML and Markdown templates do not consume legal_theories_display from context dict — they omit the column entirely."
    artifacts:
      - path: "src/do_uw/templates/html/sections/litigation.html.j2"
        issue: "Does not render legal_theories_display or legal_theories keys from context"
      - path: "src/do_uw/templates/markdown/sections/litigation.md.j2"
        issue: "Markdown table renders case.name, case.allegations, etc. — no legal theory column"
    missing:
      - "Add legal theory display to HTML litigation template case rows (use litigation.cases[n].legal_theories_display or .legal_theories)"
      - "Add legal theory column to markdown litigation table"
  - truth: "Each case shows its D&O coverage side classification"
    status: partial
    reason: "Word renderer includes Coverage column in SCA table via _format_sca_row. HTML and Markdown templates do not render coverage_display or coverage keys."
    artifacts:
      - path: "src/do_uw/templates/html/sections/litigation.html.j2"
        issue: "Does not render coverage_display key from enriched case dict"
      - path: "src/do_uw/templates/markdown/sections/litigation.md.j2"
        issue: "No coverage column in case table"
    missing:
      - "Surface coverage_display in HTML case rendering"
      - "Add coverage column to markdown SCA table"
  - truth: "Cases with missing critical fields show a data quality warning in the output"
    status: partial
    reason: "context builder populates data_quality_flags per case dict, but no HTML or Markdown template renders this key. Warning is silently dropped for both output formats."
    artifacts:
      - path: "src/do_uw/templates/html/sections/litigation.html.j2"
        issue: "data_quality_flags key not referenced in any litigation template"
      - path: "src/do_uw/templates/markdown/sections/litigation.md.j2"
        issue: "No data quality warning rendering"
    missing:
      - "Add data quality warning rendering in HTML template when data_quality_flags is non-empty"
      - "Add data quality note in markdown template"
  - truth: "Unclassified reserves appear in a separate subsection, not mixed with classified cases"
    status: partial
    reason: "Word renderer has _render_unclassified_reserves() in sect6_litigation.py. Context builder populates unclassified_reserves in context dict. HTML and Markdown templates do not render this bucket."
    artifacts:
      - path: "src/do_uw/templates/html/sections/litigation.html.j2"
        issue: "unclassified_reserves key not referenced anywhere in HTML templates"
      - path: "src/do_uw/templates/markdown/sections/litigation.md.j2"
        issue: "No unclassified reserves section"
    missing:
      - "Add unclassified reserves subsection to HTML litigation template"
      - "Add unclassified reserves table to markdown litigation section"
human_verification:
  - test: "Run underwrite AAPL --fresh, open HTML output, inspect Litigation section"
    expected: "Each SCA row shows legal theory (Rule 10b-5 etc.), coverage side (Side A/B/C), year suffix on case name, data quality flags where applicable, and separate unclassified reserves subsection"
    why_human: "HTML templates verified programmatically as NOT rendering these keys — human check needed once HTML templates are updated to confirm correct visual output"
  - test: "Run underwrite META --fresh, open Word output (.docx), inspect Litigation section"
    expected: "SCA table has Legal Theory and Coverage columns populated from classifier, case names have year suffixes, unclassified reserves subsection present if boilerplate found"
    why_human: "Word renderer verified as wired but visual confirmation needed for live data"
---

# Phase 140: Litigation Classification Consolidation Verification Report

**Phase Goal:** Every litigation entry in the worksheet is classified by legal theory (not data source), deduplicated across sources, disambiguated by year, and tagged with D&O coverage side
**Verified:** 2026-03-28T03:19:18Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

#### Plan 01 Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Every CaseDetail in securities_class_actions and derivative_suits has legal_theories set by the unified classifier | VERIFIED | `classify_all_cases()` iterates both lists, detects theories via EXTENDED_THEORY_PATTERNS, overwrites with confidence-preserving logic. 23/23 classifier unit tests pass. |
| 2 | Duplicate cases across SCA and derivative lists consolidated into single entry with merged source references | VERIFIED | `deduplicate_all_cases()` collects both lists, clusters at 70% word overlap + <=1 year gap, merges via `_enrich_case_confidence`. `TestUniversalDedup` tests cross-list dedup with 5/5 passing. |
| 3 | Every case name ends with a year suffix like (2020) | VERIFIED | `disambiguate_by_year()` appends `(YYYY)` unless already present; skips if no date available. Tests: already-suffixed not doubled, no-date gets no suffix. Both pass. |
| 4 | Each case has a coverage_type derived from legal theories + named defendants | VERIFIED | `_infer_coverage_type()` maps 12 LegalTheory values to CoverageType enum. `TestCoverageSideClassification` 4/4 pass. |
| 5 | Cases with missing critical fields queued in cases_needing_recovery | VERIFIED | `flag_missing_fields()` checks case_number, court, class_period_start, class_period_end, named_defendants. Populates `landscape.cases_needing_recovery`. `TestMissingFieldRecovery` 2/2 pass. |
| 6 | Boilerplate 10-K reserves separated into unclassified bucket | VERIFIED | `_is_boilerplate()` filters generic labels + patterns with Pitfall-5 guard. `TestBoilerplateFilter` 2/2 pass. `landscape.unclassified_reserves` model field confirmed present at runtime. |

#### Plan 02 Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 7 | Litigation section in rendered worksheet shows case type labels from legal theories | PARTIAL | Word renderer (`_format_sca_row`) calls `format_legal_theories(sca)` from CaseDetail directly — verified. HTML templates (`litigation.html.j2`, `litigation_dashboard.html.j2`) do not render `legal_theories_display` or `legal_theories` key. Markdown template omits legal theory column. |
| 8 | Consolidated cases display primary case name with all source references | VERIFIED | `extract_source_references()` in `_litigation_helpers.py` exists and is populated in context dict. Word renderer uses `format_citation(sca.case_name)` for source column. Context builder wires source_references key. |
| 9 | Every case name in the worksheet includes a year suffix | VERIFIED | Year suffix appended at extraction time by classifier. Flows through to all render paths via `case.case_name.value`. HTML gets it via `_sv_str(case.case_name)`. |
| 10 | Each case shows its D&O coverage side classification | PARTIAL | Word renderer: VERIFIED — includes Coverage column in SCA table. HTML templates: NOT wired — `coverage_display` key populated in context dict but not rendered. Markdown: NOT wired. |
| 11 | Cases with missing critical fields show a data quality warning | PARTIAL | `extract_data_quality_flags()` helper implemented and called in context builder. Returns "Missing: court, case_number" etc. No HTML or Markdown template renders `data_quality_flags` key. Word renderer does not have a per-case data quality warning either. |
| 12 | Unclassified reserves appear in a separate subsection | PARTIAL | Word renderer: VERIFIED — `_render_unclassified_reserves()` in sect6_litigation.py wired. HTML templates: NOT wired — `unclassified_reserves` key in context dict but no template renders it. Markdown: NOT wired. |

**Score:** 8/12 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/extract/litigation_classifier.py` | Unified classifier, universal dedup, year disambiguation, missing field flagger | VERIFIED | 649 lines, 4 public functions, EXTENDED_THEORY_PATTERNS covering all 12 LegalTheory values, DEDUP_THRESHOLD=0.70, confirmed callable at runtime |
| `tests/stages/extract/test_litigation_classifier.py` | Unit tests for all 5 LIT requirements, min 150 lines | VERIFIED | 495 lines, 6 test classes (TestUnifiedClassification, TestUniversalDedup, TestYearDisambiguation, TestCoverageSideClassification, TestMissingFieldRecovery, TestBoilerplateFilter), 23/23 passing |
| `src/do_uw/stages/render/context_builders/litigation.py` | Updated context builder surfacing classifier output | VERIFIED | Imports 3 helpers from `_litigation_helpers`, enriches SCA + derivative case dicts with 4 new keys, adds `unclassified_reserves` bucket to result dict |
| `src/do_uw/stages/render/context_builders/_litigation_helpers.py` | Display helpers for source references and data quality flags | VERIFIED | `extract_source_references`, `extract_data_quality_flags`, `format_legal_theories` all present and callable; `LEGAL_THEORY_DISPLAY` covers 12 values, `COVERAGE_DISPLAY` covers 20 |

### Key Link Verification

#### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `extract_litigation.py` | `litigation_classifier.py` | `from do_uw.stages.extract.litigation_classifier import classify_all_cases, ...` | WIRED | Import at line 239, all 4 functions called at lines 247, 250, 253, 256 in correct order |
| `litigation_classifier.py` | `models/litigation.py` | imports CaseDetail, CoverageType, LegalTheory, LitigationLandscape | WIRED | Line 22-27 confirmed; both `unclassified_reserves` and `cases_needing_recovery` fields present in LitigationLandscape model |

#### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `litigation.py` (context builder) | `models/litigation.py` | reads `landscape.unclassified_reserves` | WIRED | Line 142: `if hasattr(lit, "unclassified_reserves") and lit.unclassified_reserves` |
| `_litigation_helpers.py` | `litigation.py` | imported by context builder | WIRED | Line 17-28 of litigation.py imports `extract_data_quality_flags`, `extract_source_references`, `format_legal_theories` |
| HTML templates | context dict keys | render `legal_theories_display`, `coverage_display`, `data_quality_flags`, `unclassified_reserves` | NOT WIRED | None of the 4 HTML/Markdown templates reference these keys. `litigation.html.j2` uses only `active_summary`, `historical_summary`, `open_sol_count`. Markdown template renders `case.name`, `case.allegations`, `case.court` — none of the classifier-derived keys. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `_format_sca_row()` in sect6_litigation.py | `legal_theories` from CaseDetail | `classify_all_cases()` sets `case.legal_theories` during extraction | Yes — classifier runs on real extracted cases | FLOWING (Word renderer) |
| HTML litigation template | `legal_theories_display` context key | `extract_litigation()` populates from `format_legal_theories(sca_obj)` | Yes — key is populated | HOLLOW (not consumed by template) |
| HTML litigation template | `unclassified_reserves` context key | `extract_litigation()` populates from `lit.unclassified_reserves` | Yes — key is populated | HOLLOW (not consumed by template) |
| HTML litigation template | `data_quality_flags` per case dict | `extract_data_quality_flags()` cross-refs `cases_needing_recovery` | Yes — key is populated | HOLLOW (not consumed by template) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Classifier exports 4 public functions | `uv run python -c "from do_uw.stages.extract.litigation_classifier import classify_all_cases, deduplicate_all_cases, disambiguate_by_year, flag_missing_fields; print(callable(classify_all_cases))"` | True | PASS |
| LEGAL_THEORY_DISPLAY covers all 12 theories | `uv run python -c "from do_uw.stages.render.context_builders._litigation_helpers import LEGAL_THEORY_DISPLAY; print(len(LEGAL_THEORY_DISPLAY))"` | 12 | PASS |
| LitigationLandscape has new fields | `uv run python -c "from do_uw.models.litigation import LitigationLandscape; print('unclassified_reserves' in LitigationLandscape.model_fields)"` | True | PASS |
| 23 unit tests pass | `uv run pytest tests/stages/extract/test_litigation_classifier.py -q` | 23 passed | PASS |
| HTML template renders legal_theories_display | Grep for key in all HTML templates | No match in any .html.j2 file | FAIL |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| LIT-01 | 140-01, 140-02 | Case type classified from legal theories, not source category | SATISFIED (partial in HTML/MD) | `classify_all_cases()` sets legal_theories on CaseDetail; Word renderer shows it; HTML/MD templates do not |
| LIT-02 | 140-01 | Substantially similar cases consolidated | SATISFIED | `deduplicate_all_cases()` with 70% threshold + year gap check; `TestUniversalDedup` 5/5 pass |
| LIT-03 | 140-01 | Same-name cases disambiguated by year | SATISFIED | `disambiguate_by_year()` appends `(YYYY)`; year suffix flows through all render paths via case_name.value |
| LIT-04 | 140-01, 140-02 | Coverage side classification (A/B/C) derived from case type + defendants | SATISFIED (partial in HTML/MD) | `_infer_coverage_type()` complete; Word renderer shows Coverage column; HTML/MD templates missing coverage display |
| LIT-05 | 140-01 | Missing critical fields flagged | PARTIALLY SATISFIED | `flag_missing_fields()` populates `cases_needing_recovery`; `extract_data_quality_flags()` helper exists; but no HTML/MD template renders the warning |

All 5 LIT requirements appear as "Complete" in REQUIREMENTS.md. The underlying pipeline logic (extraction + classification) satisfies all 5. The display gap in HTML/Markdown is a rendering concern, not a data model concern. REQUIREMENTS.md does not specify which output format must display these — the requirement is about classification existing, not about which render path surfaces it.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `_litigation_helpers.py` | 110, 113, 122 | `return None` in `extract_data_quality_flags` | Info | Correct logic (returns None when no recovery entry) — not a stub |
| `litigation.py` context builder | SUMMARY notes | Pre-existing unused imports (`safe_get_result`, `safe_get_signals_by_prefix`) | Warning | Pre-existing lint debt, not introduced by Phase 140 |
| Multiple HTML templates | — | `legal_theories_display`, `coverage_display`, `data_quality_flags`, `unclassified_reserves` keys built but not consumed | Warning | Context enrichment is hollow for HTML/Markdown output paths |

### Human Verification Required

#### 1. Word/PDF Output — Litigation Classification Display

**Test:** Run `underwrite AAPL --fresh` (or META for richer litigation), open the generated Word document, navigate to Section 6 Litigation.
**Expected:**
- SCA table has "Legal Theory" column showing "Rule 10b-5", "Section 11", etc. (not "SCA" or source names)
- SCA table has "Coverage" column showing "Side A (D&O)", "Side C (Entity)", etc.
- Every case name includes a year suffix like "(2020)"
- Unclassified reserves subsection appears if any boilerplate was filtered
**Why human:** Word/PDF rendering cannot be verified programmatically without running the full pipeline with real data.

#### 2. HTML Output — Post-Template-Fix Verification

**Test:** After HTML template updates (see gaps), run `underwrite AAPL --fresh`, open HTML output, navigate to Litigation section.
**Expected:**
- Legal theory labels visible per case
- Coverage side badges per case
- Data quality warnings for cases with missing fields
- Separate unclassified reserves subsection if applicable
**Why human:** HTML template changes required first; then visual confirmation needed.

### Gaps Summary

Phase 140 fully achieves its extraction-layer goals: all 5 LIT requirements are implemented in the classification pipeline (`litigation_classifier.py`), wired into `extract_litigation.py`, and the data model has the new `unclassified_reserves` and `cases_needing_recovery` fields. The **Word renderer (primary output)** correctly surfaces legal theories, coverage side, and year suffixes via direct `CaseDetail` reads.

The gap is in the **HTML and Markdown rendering paths**. Plan 02 enriched the context dict with 4 new keys (`legal_theories_display`, `coverage_display`, `data_quality_flags`, `unclassified_reserves`) and noted in its own SUMMARY that "HTML template updates may be needed." None of the HTML Jinja2 templates (`litigation.html.j2`, `litigation_dashboard.html.j2`, `litigation_checks.html.j2`) or the Markdown template (`litigation.md.j2`) consume these keys. The data is computed and silently dropped.

Since CLAUDE.md states "PDF is the final output — HTML is intermediate" and the primary worksheet format is Word/PDF, this is a medium-severity gap rather than a critical blocker. The phase goal is partially achieved: classification exists in the data model and Word output; it is not visible in HTML/Markdown output.

The Plan 02 human-verify checkpoint (Task 2) was not executed — the SUMMARY marks it as "NOT EXECUTED (checkpoint for orchestrator)." This gate was intended to confirm visual display of all 5 LIT requirements, which would have caught the HTML template omission.

---

_Verified: 2026-03-28T03:19:18Z_
_Verifier: Claude (gsd-verifier)_
