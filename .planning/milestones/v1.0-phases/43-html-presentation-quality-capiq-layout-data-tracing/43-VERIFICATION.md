---
phase: 43-html-presentation-quality-capiq-layout-data-tracing
verified: 2026-02-24T23:00:00Z
status: human_needed
score: 25/25 must-haves verified
re_verification:
  previous_status: human_needed
  previous_score: 18/18
  gaps_closed:
    - "Sidebar top offset fixed (top: 44px) — sidebar no longer slides under sticky topbar"
    - "Body padding-top: 44px — first section content visible on load, not hidden behind topbar"
    - "Wide table overflow fixed — .worksheet-main overflow-x: auto prevents content clipping"
    - "Sidebar Appendix group header added with 4 sub-links (Meeting Prep, Sources, QA Audit, Coverage)"
    - "Scoring section moved last before appendices (after AI Risk) per user preference"
    - "Identity block shows IPO / Listed row derived from years_public instead of raw count"
    - "New QA/Audit Trail appendix (qa_audit.html.j2) with per-section check-level audit trail"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Visual review of two-column layout in AAPL HTML output"
    expected: "Sidebar visible on left with 13 links (9 sections + Appendix group with 4 sub-links). Sidebar sticks below topbar (does not slide under it) when scrolling. Active section highlighted on scroll. Topbar shows name/ticker/sector/market cap with no score numbers or tier badge."
    why_human: "CSS Grid rendering, IntersectionObserver behavior, and sticky positioning are browser-dependent and cannot be verified via static grep or test output."
  - test: "Print preview of AAPL HTML worksheet (Cmd+P)"
    expected: "Sidebar hidden, layout is single-column, content is readable and fits standard letter format. No overlapping elements."
    why_human: "@media print rendering requires visual inspection in a browser print context."
  - test: "Sources appendix populated in real AAPL render"
    expected: "At least several numbered sources appear at the bottom (e.g. '1. 10-K (SEC EDGAR), filed 2024-11-01'). Inline superscript numbers visible in financial and market metric rows."
    why_human: "Automated tests use synthetic state with one mocked filing document. Real AAPL data pipeline output requires visual confirmation."
  - test: "QA/Audit appendix populated in real AAPL render"
    expected: "QA / Audit Trail section appears with check-level rows grouped by section. Each row shows Check ID, Check name, Finding, Source, and color-coded confidence badge (HIGH/MED/LOW)."
    why_human: "qa_audit.html.j2 is guarded by if check_results_by_section. Real AAPL state must have check_results to populate it. Automated tests use synthetic state; real output needs visual confirmation."
metadata_gaps:
  - "ROADMAP.md lines 633-634: Plans 43-06 and 43-07 marked '[ ]' (incomplete) despite commits fa25591, 26782b6, and 579b018 confirming full implementation. ROADMAP checkboxes must be updated to '[x]'."
---

# Phase 43: HTML Presentation Quality — CapIQ Layout Re-Verification Report

**Phase Goal:** Transform the existing HTML worksheet into an institutionally-credible underwriting document matching S&P Capital IQ presentation quality. Two-column layout with sticky sidebar TOC, identity-only top bar, risk-first section order (Red Flags immediately after Exec Summary), 3-column data grid (Label | Value | Context/Benchmark) in key sections, footnote/Sources traceability infrastructure, and automated layout tests.

**Verified:** 2026-02-24T23:00:00Z
**Status:** human_needed
**Re-verification:** Yes — after UAT gap closure (Plans 06 and 07)

## Re-Verification Context

The previous verification (2026-02-24T12:00:00Z) returned `human_needed` at 18/18 automated checks. Human UAT (43-UAT.md) revealed 7 issues (2 passed, 7 issues, 6 skipped):

- **Major:** Sidebar slides under sticky topbar (top: 0 bug)
- **Major:** Main content clipped at viewport edge (no overflow protection)
- **Major:** Scoring section appeared in position 4 (should be last before appendices)
- **Major:** No QA/audit trail appendix
- **Minor:** Sidebar missing Appendix group with sub-links
- **Minor:** Identity block showed raw "Years Public" count instead of IPO date

Plans 06 (CSS layout fixes) and 07 (template structure fixes) were executed to close these gaps. This re-verification checks the gap-closure work against the actual codebase.

---

## Goal Achievement

### Observable Truths — Initial 18 (Regression Check)

All 18 truths from the initial verification continue to hold. Spot-checked the 3 most likely to have been disturbed by gap closure work:

| # | Truth | Status | Regression Check |
|---|-------|--------|-----------------|
| 6 | Document starts with identity block (id="identity") | VERIFIED | worksheet.html.j2 line 8: identity.html.j2 still first include |
| 7 | Red Flags immediately after executive summary, before scoring | VERIFIED | Lines 9-10: executive then red_flags — preserved in new order |
| 11 | scoring.html.j2 under 500 lines | VERIFIED | wc -l confirms 484 lines — unchanged |

### Observable Truths — Gap Closure (7 New Truths from UAT)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 19 | Sidebar sticks below the sticky topbar — does not slide under it when scrolling | VERIFIED | `sidebar.css` line 18: `.sidebar-toc { top: 44px; }`. Commit fa25591 confirms change from `top: 0`. |
| 20 | Main content area not clipped at right edge — wide tables scroll horizontally | VERIFIED | `sidebar.css` line 67: `.worksheet-main { overflow-x: auto; }`. Commit fa25591 confirms addition. |
| 21 | First section (Identity) visible on page load — not hidden behind topbar | VERIFIED | `sidebar.css` lines 12-14: `body { padding-top: 44px; }`. Commit fa25591 confirms addition. |
| 22 | Sidebar TOC has Appendix group header with 4 sub-links (Meeting Prep, Sources, QA Audit, Coverage) | VERIFIED | `base.html.j2` lines 82-86: `<li class="sidebar-group-header">Appendix</li>` + 4 `sidebar-sub` sub-links. CSS classes `.sidebar-group-header` and `.sidebar-sub` defined in `sidebar.css` lines 83-97. |
| 23 | Scoring section appears last before appendices — after Litigation and AI Risk | VERIFIED | `worksheet.html.j2` include order: `ai_risk.html.j2` (line 15) then `scoring.html.j2` (line 16), before appendices (lines 17-20). Commit 26782b6 confirms reorder. |
| 24 | Identity block shows IPO date (or derived approximate year) instead of raw years-public count | VERIFIED | `identity.html.j2` lines 51-63: shows `IPO / Listed` row using `ipo_date` context variable, falls back to `years_public` count if `ipo_date` absent. `html_renderer.py` line 149: `context["ipo_date"] = ipo_date_str` derived from `timedelta`. |
| 25 | QA/Audit Trail appendix exists with per-section check-level audit trail | VERIFIED | `appendices/qa_audit.html.j2` (69 lines): `<section id="qa-audit">`, columns Check ID / Check / Finding / Source / Conf. / Status. Guarded by `{% if check_results_by_section %}`. Included in `worksheet.html.j2` line 19. Context wired in `html_renderer.py` line 115: `context["check_results_by_section"] = _group_checks_by_section(check_results)`. |

**Score:** 25/25 truths verified (automated)

---

## Required Artifacts — Gap Closure Plans

| Artifact | Lines | Status | Evidence |
|----------|-------|--------|----------|
| `src/do_uw/templates/html/sidebar.css` | 130 | VERIFIED | Plan 06 fixes: `top: 44px` (line 18), `body padding-top: 44px` (lines 12-14), `overflow-x: auto` (line 67). Plan 07 additions: `.sidebar-group-header` (lines 83-91), `.sidebar-sub` (lines 94-97), `.qa-conf` badge variants (lines 109-118). Under 500 lines. |
| `src/do_uw/templates/html/base.html.j2` | 173 | VERIFIED | Sidebar TOC updated: 9 section links + Appendix group header + 4 sub-links (lines 72-87). Scoring moved after AI Risk in TOC order (line 81 before Appendix). Under 500 lines. |
| `src/do_uw/templates/html/worksheet.html.j2` | 21 | VERIFIED | Section order: identity→executive→red_flags→financial→market→governance→litigation→ai_risk→scoring→appendices. `qa_audit.html.j2` included at line 19. |
| `src/do_uw/templates/html/sections/identity.html.j2` | 66 | VERIFIED | "Years Public" replaced with "IPO / Listed" using `ipo_date` context variable (lines 51-63) with graceful fallback. Under 500 lines. |
| `src/do_uw/templates/html/appendices/qa_audit.html.j2` | 69 | VERIFIED | New file. `<section id="qa-audit">`. Per-section check audit trail with namespace loop pattern for Jinja2-safe total count. Under 500 lines. |
| `src/do_uw/stages/render/html_renderer.py` | 406 | VERIFIED | `ipo_date` context injection at lines 140-149. `timedelta` import at line 16. `check_results_by_section` already wired at line 115. Under 500 lines. |
| `tests/stages/render/test_html_layout.py` | 360 | VERIFIED | `test_section_order` updated to reflect new order (financial before scoring). All 10 layout tests pass. |

---

## Key Link Verification — Gap Closure Plans

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `sidebar.css .sidebar-toc` | sticky-topbar bottom edge | `top: 44px` | WIRED | Line 18 of sidebar.css. Offsets sidebar below 44px topbar. |
| `sidebar.css body` | layout start below topbar | `padding-top: 44px` | WIRED | Lines 12-14 of sidebar.css. Pushes layout start below topbar. |
| `sidebar.css .worksheet-main` | overflow protection | `overflow-x: auto` | WIRED | Line 67 of sidebar.css. |
| `base.html.j2 sidebar-group-header` | `appendices/qa_audit.html.j2` | `href="#qa-audit"` in `.sidebar-sub` | WIRED | Line 85 of base.html.j2. |
| `worksheet.html.j2` | `appendices/qa_audit.html.j2` | `{% include "appendices/qa_audit.html.j2" %}` | WIRED | Line 19 of worksheet.html.j2. |
| `worksheet.html.j2` | scoring after ai_risk | include order lines 15-16 | WIRED | `ai_risk.html.j2` at line 15, `scoring.html.j2` at line 16. |
| `html_renderer.py` | `identity.html.j2 ipo_date` | `context["ipo_date"]` | WIRED | Line 149 of html_renderer.py. Template consumes at lines 51-63 of identity.html.j2. |
| `html_renderer.py _group_checks_by_section()` | `qa_audit.html.j2` | `context["check_results_by_section"]` | WIRED | Line 115 of html_renderer.py. Template iterates at line 15 of qa_audit.html.j2. |
| `sidebar.css .sidebar-group-header` | visual Appendix group | class defined in CSS | WIRED | Lines 83-91 of sidebar.css. Used in base.html.j2 line 82. |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| VIS-05 | 43-01 through 43-07 | Complete visual design system — presentation quality | SATISFIED | Two-column CapIQ layout with corrected sticky sidebar (top: 44px), content overflow protection, identity-only topbar, risk-first ordering (red flags before scoring), scoring last before appendices, 3-column data grid, Appendix navigation group with sub-links. 10 automated layout tests pass. All UAT gaps closed. |
| OUT-03 | 43-02, 43-05, 43-07 | Every section begins with summary paragraph synthesizing findings | PARTIALLY SATISFIED | Phase 43 scope covers structure and layout, not adding new narrative content. Existing section templates carry forward narrative from earlier phases. QA Audit appendix provides per-check traceability. REQUIREMENTS.md mapping table shows OUT-03 as "Phase 8: Complete." No regression observed. |
| OUT-04 | 43-04, 43-05 | Every data point includes source citation (filing type, date, reference) | SATISFIED | FootnoteRegistry pre-collects filing sources. Inline superscript `<sup class="fn-ref">` links to sources appendix. `sources.html.j2` renders numbered list with `id="fn-N"` anchors. `data_row` macro accepts `footnote_num` parameter wired in financial and market sections. |

---

## Anti-Patterns Found

No new anti-patterns introduced in Plans 06 or 07. Spot check of all modified files:

| File | Check | Result |
|------|-------|--------|
| `sidebar.css` | TODO/FIXME/placeholder | None found |
| `base.html.j2` | Stub sidebar links | Not stubs — all hrefs target real section IDs |
| `qa_audit.html.j2` | Empty or stub template | Not a stub — full table structure with real data iteration |
| `identity.html.j2` | Fallback chain safety | VERIFIED — `{% if ipo_date %} ... {% elif cl.get('years_public') %}` graceful degradation |
| `html_renderer.py` | ipo_date type safety | VERIFIED — `hasattr(state.company.years_public, "value")` guards SourcedValue unwrapping |

---

## Test Suite Results

```
tests/stages/render/test_html_layout.py                              10/10 passed
tests/stages/render/ (full suite)                                    227/227 passed
tests/stages/render/ + tests/stages/analyze/ + tests/stages/extract/   493/493 passed
```

All tests pass. No regressions from Plans 06 or 07.

---

## Metadata Gap (Non-Blocking)

ROADMAP.md lines 633-634 show Plans 43-06 and 43-07 as `[ ]` (incomplete) even though:

- Both plans have completed SUMMARY files (43-06-SUMMARY.md, 43-07-SUMMARY.md)
- Git commits are verified: `fa25591` (Plan 06), `26782b6` + `579b018` + `4156daf` (Plan 07)
- Codebase confirms all changes in place

This is a ROADMAP metadata staleness issue only. The implementation is complete. The ROADMAP checkboxes must be updated to `[x]` to match reality.

---

## Human Verification Required

### 1. Two-Column Layout and Sidebar Sticky Behavior

**Test:** Open `output/AAPL/AAPL-2026-02-24/AAPL_worksheet.html` in a browser.
**Expected:** 180px sidebar on left with 13 navigation links (9 sections + Appendix group label + 4 sub-links). Sidebar stays fixed below the dark topbar as you scroll — does not slide under it. The Identity section is visible on page load, not hidden behind the topbar. Active section link highlighted in sidebar on scroll.
**Why human:** CSS sticky positioning with `top: 44px` and browser rendering cannot be verified via static analysis. IntersectionObserver behavior is entirely runtime.

### 2. Content Not Clipped — Wide Tables Scroll Horizontally

**Test:** In the AAPL worksheet, find a wide table (e.g., financial statements or scoring perils table). Scroll right if needed.
**Expected:** Table content is fully visible. If the table is wider than the content column, a horizontal scrollbar appears within the content area — content is not cut off at the right viewport edge.
**Why human:** `overflow-x: auto` on `.worksheet-main` prevents clipping, but visual result depends on actual table widths in rendered AAPL data.

### 3. Print Preview — Sidebar Hidden

**Test:** Open AAPL worksheet in browser, trigger print preview (Cmd+P on Mac).
**Expected:** Sidebar is gone. Layout collapses to single column. Content is readable on standard letter paper. No overlapping elements.
**Why human:** `@media print` CSS behavior is browser-dependent.

### 4. Sources Appendix Populated in Real AAPL Render

**Test:** Scroll to the Sources section at the bottom of the AAPL worksheet.
**Expected:** Numbered list of data citations appears (e.g. "1. 10-K (SEC EDGAR), filed 2024-11-01"). Inline superscript numbers visible in financial and market metric rows linking back to Sources entries.
**Why human:** Automated tests use synthetic state with one mocked filing document. Real AAPL data may differ.

### 5. QA/Audit Trail Appendix Populated in Real AAPL Render

**Test:** Scroll to the QA / Audit Trail section near the bottom of the AAPL worksheet.
**Expected:** Section appears with check rows grouped by section name (e.g. "Financial Health", "Governance"). Each row shows Check ID, check name, what was verified, source, and a color-coded confidence badge (HIGH = green, MED = yellow, LOW = red).
**Why human:** `qa_audit.html.j2` is guarded by `{% if check_results_by_section %}`. Real AAPL analysis state must have populated `check_results`. Visual inspection needed to confirm data flows through correctly.

---

## Summary

All 7 UAT gaps from the initial human review are closed. The 25 automated truths confirm:

1. **CSS layout fixes (Plan 06):** `sidebar.css` has `top: 44px`, `body padding-top: 44px`, and `.worksheet-main overflow-x: auto`. All three UAT-reported visual defects have verified code-level fixes.

2. **Template structure fixes (Plan 07):** Sidebar TOC has Appendix group with 4 sub-links. Scoring appears last before appendices. Identity shows IPO / Listed date derived from `years_public`. New `qa_audit.html.j2` appendix exists with full check-level audit trail wiring.

3. **No regressions:** 493 tests pass across render, analyze, and extract test suites.

The `human_needed` status reflects 5 items requiring browser visual confirmation: CSS sticky rendering, print layout, and real AAPL data populating Sources and QA Audit appendices. No automated gaps remain.

**Outstanding action before phase close:** Update ROADMAP.md lines 633-634 from `[ ]` to `[x]` for Plans 43-06 and 43-07.

---

_Verified: 2026-02-24T23:00:00Z_
_Re-verification: Yes — after UAT gap closure (Plans 06 and 07)_
_Verifier: Claude (gsd-verifier)_
