---
status: complete
phase: 43-html-presentation-quality-capiq-layout-data-tracing
source: [43-01-SUMMARY.md, 43-02-SUMMARY.md, 43-03-SUMMARY.md, 43-04-SUMMARY.md, 43-05-SUMMARY.md]
started: 2026-02-25T03:51:28Z
updated: 2026-02-25T03:51:28Z
---

## Current Test
<!-- OVERWRITE each test - shows where we are -->

[testing complete]

## Tests

### 1. Two-column layout visible
expected: Open AAPL worksheet HTML in browser. Page shows two-column layout — narrow sidebar on the left (~180px) with section navigation links, main document content on the right.
result: issue
reported: "nothat looks bad"
severity: major

### 2. Sticky topbar — identity only, no scores
expected: The sticky bar at the top shows company name, ticker, sector, market cap, and date only. No tier badge (e.g. "Standard"), no score numbers, no action text.
result: pass

### 3. Sidebar TOC links + active highlight
expected: Sidebar has 9 links (Identity, Exec Summary, Red Flags, Scoring, Financial, Market, Governance, Litigation, Sources). Scrolling through the document highlights the current section's link in the sidebar.
result: issue
reported: "left bar should not scrolling into the top bar.. section disappears"
severity: major

### 4. Print layout — sidebar hidden
expected: Open browser print preview (Cmd+P on Mac). The sidebar is gone — layout collapses to a single column. Content is readable with no overlapping elements.
result: pass

### 5. Document starts with company identity block
expected: At the top of the content area (below the topbar), a company identity block shows: company name + ticker as a heading, sector/exchange/analyzed-date as metadata, business description, and a metrics table (market cap, revenue, employees, years public).
result: skipped
reason: stopped early to diagnose and plan fixes

### 6. Red Flags section immediately after Executive Summary
expected: Scrolling down, the section order is: Identity → Executive Summary → Red Flags. The Red Flags section appears before Scoring. If AAPL has triggered/elevated flags, they show in a table with Severity | Flag | Finding | Source columns.
result: skipped
reason: stopped early to diagnose and plan fixes

### 7. Section order throughout the document
expected: Scrolling through the full document, sections appear in this order: Identity → Executive Summary → Red Flags → Scoring → Financial → Market → Governance → Litigation → Sources. No section appears out of order.
result: skipped
reason: stopped early to diagnose and plan fixes

### 8. Financial key metrics — 3-column grid
expected: In the Financial section, key metrics (Revenue, Gross Margin, Operating Margin, Net Margin, Total Debt, Cash) appear in a 3-column layout: bold label on the left, value in the center, peer context or benchmark in the right column.
result: skipped
reason: stopped early to diagnose and plan fixes

### 9. Market section stock performance — 3-column grid
expected: In the Market section, stock performance metrics (YTD Return, 1-Year Return, Beta, Short Interest) appear in the same 3-column grid (label | value | context).
result: skipped
reason: stopped early to diagnose and plan fixes

### 10. Sources appendix with numbered citations
expected: At the bottom of the document, a "Sources" section appears with a numbered list of data citations (e.g. "1. 10-K (SEC EDGAR), filed 2024-11-01"). Each entry has a number matching superscript references in the financial/market sections.
result: skipped
reason: stopped early to diagnose and plan fixes

## Summary

total: 10
passed: 2
issues: 7
pending: 0
skipped: 6

## Gaps

- truth: "Page shows two-column layout with sidebar on the left and main content on the right"
  status: failed
  reason: "User reported: nothat looks bad"
  severity: major
  test: 1
  root_cause: ""
  artifacts: []
  missing: []
  debug_session: ""

- truth: "Sidebar has 9 section links and scrolling highlights the active section"
  status: failed
  reason: "User reported: left bar should not scrolling into the top bar.. section disappears — sidebar top: 0 causes it to slide under sticky topbar when scrolling; needs top: [topbar height]px"
  severity: major
  test: 3
  root_cause: ".sidebar-toc has position: sticky; top: 0 — should be top: [topbar height] so sidebar sticks below the topbar, not under it"
  artifacts:
    - path: "src/do_uw/templates/html/sidebar.css"
      issue: ".sidebar-toc top: 0 needs to match sticky topbar height"
  missing:
    - "Set .sidebar-toc top to topbar height (measure actual px from rendered topbar)"
    - "Set .worksheet-layout padding-top or margin-top to topbar height so content doesn't start under topbar"
  debug_session: ""

- truth: "Sidebar TOC includes an Appendix group listing appendix items (Meeting Prep, Sources, Coverage) rather than a flat Sources link"
  status: failed
  reason: "User reported: there should also be Appendix — and any things that go there should be listed under Appendix"
  severity: minor
  test: 3
  root_cause: "Sidebar TOC in base.html.j2 has a single 'Sources' link; should have an 'Appendix' header with sub-items (Meeting Prep, Sources, Coverage)"
  artifacts:
    - path: "src/do_uw/templates/html/base.html.j2"
      issue: "Sidebar TOC missing Appendix grouping"
  missing:
    - "Replace flat 'Sources' sidebar link with Appendix header + sub-links for meeting_prep, sources, coverage"
  debug_session: ""

- truth: "Identity block shows IPO date (or major spinoff/listing date) instead of years public"
  status: failed
  reason: "User reported: don't want years public — want to see IPO date or major spinoff/spin-off date"
  severity: minor
  test: 5
  root_cause: "identity.html.j2 shows cl.get('years_public') — should show IPO date or listing event date from classification data"
  artifacts:
    - path: "src/do_uw/templates/html/sections/identity.html.j2"
      issue: "years_public row should be replaced with IPO date / major listing event date"
  missing:
    - "Replace 'Years Public' row with 'IPO Date' (or 'Listed' / 'Spinoff Date') using cl.get('ipo_date') or equivalent field from AnalysisState"
    - "Verify AnalysisState/classification model has IPO date field; if not, add it to ACQUIRE stage"
  debug_session: ""

- truth: "Scoring section appears last before appendices (after financial, market, governance, litigation)"
  status: failed
  reason: "User reported: section 7 appearing after section 1 — scoring should be the last section before appendices, not 4th in the order"
  severity: major
  test: 5
  root_cause: "worksheet.html.j2 include order puts scoring 4th (after red_flags); user wants scoring at the end — identity → executive → red_flags → financial → market → governance → litigation → ai_risk → scoring → appendices"
  artifacts:
    - path: "src/do_uw/templates/html/worksheet.html.j2"
      issue: "scoring.html.j2 included too early — should be last before appendices"
  missing:
    - "Move {% include 'sections/scoring.html.j2' %} to after litigation and ai_risk in worksheet.html.j2"
    - "Update sidebar TOC link order to match"
  debug_session: ""

- truth: "Appendix includes a QA/audit section for each data section listing what was checked, how it was verified, and source/confidence level for each data point"
  status: failed
  reason: "User reported: for each section in the appendix you need to list specifically what was checked and verified and how — like a QA section"
  severity: major
  test: 5
  root_cause: "No per-section QA audit trail exists in the appendix — sources appendix only lists citations, does not map them to individual checks or show verification method/confidence"
  artifacts:
    - path: "src/do_uw/templates/html/appendices/sources.html.j2"
      issue: "Only renders a numbered source list — no check-level audit trail"
  missing:
    - "New appendix template (e.g. appendices/qa_audit.html.j2) that for each section lists: check name, what was verified, source used, confidence level (HIGH/MEDIUM/LOW)"
    - "Wire check_results from AnalysisState into the QA audit template"
    - "Add sidebar TOC link for QA/Audit section"
  debug_session: ""

- truth: "Main content area is fully visible without horizontal clipping"
  status: failed
  reason: "Screenshots show right-side content truncated — table text clipped at viewport edge"
  severity: major
  test: 1
  root_cause: "Likely .worksheet-main overflow or table column widths expanding beyond available space"
  artifacts:
    - path: "src/do_uw/templates/html/sidebar.css"
      issue: ".worksheet-main may need overflow-x: auto or table column constraints"
  missing:
    - "Add overflow-x: auto to .worksheet-main or constrain table widths"
  debug_session: ""
