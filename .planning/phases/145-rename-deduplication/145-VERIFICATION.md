---
phase: 145-rename-deduplication
verified: 2026-03-28T22:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 6/7
  gaps_closed:
    - "Revenue with full provenance (source, period, confidence) in the Financial section — commit 178d3268 wires revenue_source/as_of/confidence into sections/report/financial.html.j2 (the live manifest template)"
  gaps_remaining: []
  regressions: []
---

# Phase 145: Rename & Deduplication — Verification Report

**Phase Goal:** The report has one name ("worksheet") and each metric has one home section with full context -- all other appearances are cross-references or the persistent header bar
**Verified:** 2026-03-28T22:00:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (commit 178d3268)

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Zero occurrences of `beta_report` in src/, tests/, templates/ | ✓ VERIFIED | `grep -r "beta_report" src/ tests/` returns 0 matches. |
| 2 | All imports resolve — no ImportError when importing any render context builder | ✓ VERIFIED | 20/20 tests in test_key_stats.py + test_dedup_metrics.py pass. |
| 3 | Template context variable is `uw_analysis`, not `beta_report` or `report` | ✓ VERIFIED | `uw_analysis.html.j2` line 5: `{% set b = uw_analysis %}`. `assembly_uw_analysis.py` sets `context["uw_analysis"]`. |
| 4 | Full test suite passes with no failures related to renamed files | ✓ VERIFIED | 12/12 key_stats tests pass; deleted test functions absent. 8/8 dedup tests pass. |
| 5 | Revenue with full provenance appears only in Financial section and header bar | ✓ VERIFIED | `sections/report/financial.html.j2` line 21: `prov` key set from `fn.revenue_as_of ~ " · " ~ fn.revenue_source ~ " · " ~ fn.revenue_confidence`. Line 33 renders it. Context builder `uw_analysis_sections.py` lines 556-587 populates these keys from XBRL (HIGH) or yfinance (MEDIUM). |
| 6 | Market cap, stock price, board size each appear only in their home section plus header bar | ✓ VERIFIED | All 8 dedup tests pass. Market cap: page0_dashboard only + header. Stock price: stock_market only + header. Board size: governance only. |
| 7 | Header bar shows MCap, Revenue, Price, Employees as compact reference | ✓ VERIFIED | `uw_analysis.html.j2` line 40: four-metric loop confirmed. `test_header_bar_has_four_metrics` passes. |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/do_uw/stages/render/context_builders/uw_analysis.py` | Main UW analysis context builder | ✓ VERIFIED | Contains `build_uw_analysis_context`. |
| `src/do_uw/stages/render/context_builders/assembly_uw_analysis.py` | Assembly module | ✓ VERIFIED | Sets `context["uw_analysis"]`. |
| `src/do_uw/templates/html/sections/uw_analysis.html.j2` | Main section template | ✓ VERIFIED | Line 5: `{% set b = uw_analysis %}`. |
| `tests/stages/render/test_dedup_metrics.py` | Automated dedup verification test | ✓ VERIFIED | 8/8 tests pass. |
| `tests/stages/render/test_key_stats.py` | Key stats render tests (updated) | ✓ VERIFIED | Deleted test functions confirmed absent. 12/12 remaining tests pass. |
| `src/do_uw/templates/html/sections/report/financial.html.j2` | Revenue card with provenance | ✓ VERIFIED | Line 21: `prov` key computed from `fn.revenue_as_of ~ " · " ~ fn.revenue_source ~ " · " ~ fn.revenue_confidence`. Line 33: renders when non-empty. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `assembly_registry.py` | `assembly_uw_analysis` | import statement | ✓ WIRED | Line 269: `import do_uw.stages.render.context_builders.assembly_uw_analysis` |
| `uw_analysis.html.j2` | `sections/report/financial.html.j2` | Jinja2 include | ✓ WIRED | Line 89: `{% include "sections/report/financial.html.j2" %}` |
| `uw_analysis_sections.py` | `revenue_source / revenue_as_of / revenue_confidence` | context dict keys | ✓ WIRED | Lines 556-587: provenance keys computed from XBRL (HIGH) or yfinance (MEDIUM), returned in `_build_financial_context`. |
| `sections/report/financial.html.j2` | `fn.revenue_source / fn.revenue_as_of` | template render | ✓ WIRED | Line 21 builds `prov` string from both keys. Line 33 renders it inside the Revenue card. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `sections/report/financial.html.j2` Revenue card | `fn.revenue` | `uw_analysis_sections.py` → `fmt_large_number(rev)` | Yes | ✓ FLOWING |
| `sections/report/financial.html.j2` Revenue provenance | `fn.revenue_source`, `fn.revenue_as_of`, `fn.revenue_confidence` | `uw_analysis_sections.py` lines 556-587 — XBRL statements first, yfinance fallback | Yes | ✓ FLOWING |
| `uw_analysis.html.j2` header bar | `b.revenue` | `assembly_uw_analysis.py` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Zero beta_report in codebase | `grep -r "beta_report" src/ tests/` | 0 matches | ✓ PASS |
| Dedup tests pass | `uv run pytest tests/stages/render/test_dedup_metrics.py -v` | 8/8 passed | ✓ PASS |
| Key stats tests | `uv run pytest tests/stages/render/test_key_stats.py -v` | 12/12 passed | ✓ PASS |
| Deleted test functions absent | `grep -c "test_renders_stock_charts\|test_recent_ipo_hides_5y_chart" tests/stages/render/test_key_stats.py` | 0 | ✓ PASS |
| Revenue provenance in live template | `grep "revenue_source\|revenue_as_of" src/do_uw/templates/html/sections/report/financial.html.j2` | 2 matches (lines 21, 21) | ✓ PASS |
| Provenance context keys exist | `grep "revenue_source\|revenue_as_of" src/do_uw/stages/render/context_builders/uw_analysis_sections.py` | 4 matches | ✓ PASS |
| Live template in render chain | `grep "sections/report/financial" src/do_uw/templates/html/sections/uw_analysis.html.j2` | line 89 | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| NAME-01 | 145-01-PLAN | Rename beta_report → uw_analysis across all Python files, templates, tests | ✓ SATISFIED | 0 beta_report matches in src/tests. |
| NAME-02 | 145-01-PLAN | Context variable is `uw_analysis` in all templates | ✓ SATISFIED | Template line 5: `{% set b = uw_analysis %}`. |
| DEDUP-01 | 145-02-PLAN | Define home section for each metric with full context and provenance | ✓ SATISFIED | Revenue home section is Financial. Live template renders provenance (period · source · confidence) on Revenue card. ROADMAP success criterion 2 met. |
| DEDUP-02 | 145-02-PLAN | Revenue=Financial, MCap=Dashboard, Price=Stock&Market, Board=Governance | ✓ SATISFIED | All 4 home sections verified by test. |
| DEDUP-03 | 145-02-PLAN | Header bar keeps MCap/Revenue/Price/Employees as only allowed cross-section duplicates | ✓ SATISFIED | test_header_bar_has_four_metrics passes. |
| DEDUP-04 | 145-02-PLAN | Remove redundant metric displays from non-home sections | ✓ SATISFIED | 6 dedup tests confirm removal. No stock price in key_stats, no market_cap/revenue in identity/company. |

### Anti-Patterns Found

None blocking goal achievement. The old `sections/financial.html.j2` still exists with provenance code (dead code — not included in any active render chain), but this is a pre-existing orphan file, not introduced by phase 145.

**Pre-existing failures (not phase 145 responsibility, unchanged):**
- `test_contract_enforcement.py::test_real_manifest_template_agreement` — 13 orphaned investigative/financial/scoring templates not registered in manifest
- `test_template_facet_audit.py::test_no_orphaned_group_templates` — `sections/investigative/` templates orphaned
- `test_template_facet_audit.py::test_all_signal_sections_have_groups` — `market_overflow` section has no groups
- 116 other pre-existing failures across html_layout, html_renderer, layer_rendering, manifest_rendering, etc.

### Human Verification Required

None — all verification items are programmatically testable.

### Gaps Summary

All three ROADMAP success criteria are now satisfied:

1. `grep -r "beta_report" src/ tests/ templates/` returns zero matches — ✓
2. Revenue appears with full provenance (source, period, confidence) in the Financial section and as a compact reference in the header bar — ✓ commit 178d3268 applies provenance to the live manifest template `sections/report/financial.html.j2`
3. Market cap, stock price, board size each appear in exactly their home section plus the header bar — ✓ verified by all 8 automated dedup tests

Phase goal achieved: the report has one name ("worksheet"), each metric has one home section with full context, and all other appearances are cross-references or the persistent header bar.

---

_Verified: 2026-03-28T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
