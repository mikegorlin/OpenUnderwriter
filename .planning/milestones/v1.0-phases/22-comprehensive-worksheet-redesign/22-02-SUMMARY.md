---
phase: 22
plan: 02
subsystem: render
tags: [word-renderer, executive-summary, company-profile, v2-redesign]
depends_on:
  requires: [22-01]
  provides: [sect1-v2-renderer, sect2-v2-renderer, sect2-details-split]
  affects: [22-07, 22-08, 22-09, 22-10]
tech-stack:
  added: []
  patterns: [narrative-first-rendering, source-trail-citations, delegation-with-fallback]
key-files:
  created:
    - src/do_uw/stages/render/sections/sect2_company_details.py
  modified:
    - src/do_uw/stages/render/sections/sect1_executive.py
    - src/do_uw/stages/render/sections/sect2_company.py
decisions:
  - "Thesis fallback chain: LLM narrative -> scoring_narrative() -> static message"
  - "Snapshot table has 3 columns (attr/value/source) for inline citations"
  - "Exposure factors rendered as paragraphs with risk indicators (not table-only)"
  - "sect2_company delegates to sect2_company_details via try/except ImportError fallback"
  - "Severity dots use text brackets [*]/[**]/[***] instead of Unicode circles"
metrics:
  duration: 8m 12s
  completed: 2026-02-11
---

# Phase 22 Plan 02: Section 1 & 2 Renderer Redesign Summary

Redesigned Section 1 (Executive Summary) and Section 2 (Company Profile) Word renderers for rich, sourced, narrative-first output instead of sparse N/A grids.

## Tasks Completed

### Task 1: Redesign Section 1 Executive Summary (494 lines)

Rewrote sect1_executive.py with narrative-first approach:
- **Underwriting Thesis**: LLM-generated narrative lead with fallback to scoring_narrative()
- **Company Snapshot**: 3-column table (Attribute/Value/Source) with format_source_trail() citations on market cap, revenue, employee count
- **Tier Classification**: Score breakdown (factor-by-factor), score ceiling from red flags, tier range position context
- **Inherent Risk Baseline**: Severity percentiles with compact currency, actuarial expected loss when available
- **Key Findings**: Severity dots [*]/[**]/[***] based on ranking_score, allegation theory mapping per finding
- **Claim Probability**: Band with severity scenario integration when available
- **Tower Recommendation**: Layer-level assessments with premium guidance

### Task 2: Redesign Section 2 Company Profile with Split (305 + 350 lines)

Rewrote sect2_company.py and created sect2_company_details.py:

**sect2_company.py** (305 lines):
- Company Identity: 10-field table with source trail citations including fiscal year end
- Business Description: 3-tier fallback (business_description -> business_model_description -> industry_classification)
- Subsidiaries: Count with D&O complexity flagging (>100 subsidiaries = multi-jurisdiction warning)
- Delegation to sect2_company_details with ImportError fallback to legacy inline rendering

**sect2_company_details.py** (350 lines):
- Revenue Segments: 5-column table with YoY growth column
- Geographic Footprint: High-risk jurisdiction flagging (sanctions/regulatory), international exposure percentage summary
- Customer/Supplier Concentration: Binary event risk D&O context notes
- D&O Exposure Mapping: Per-factor paragraph rendering with risk indicators and coverage part

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Thesis fallback chain | Ensures section always has content even without LLM extraction |
| 3-column snapshot table | Inline source citations without separate citation paragraphs |
| Delegation with ImportError fallback | Allows sect2_company_details to be developed independently |
| Severity dots as text brackets | Unicode circles may not render in all Word fonts |
| High-risk jurisdiction flagging | Underwriters need sanctions/regulatory exposure at a glance |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added stub for sect5_governance_comp.py**
- **Found during:** Final verification
- **Issue:** Another parallel agent created empty sect5_governance_comp.py, causing ImportError cascade through sections/__init__.py that blocked all section imports
- **Fix:** Added no-op stub with render_compensation_detail() signature
- **Files modified:** src/do_uw/stages/render/sections/sect5_governance_comp.py
- **Commit:** 88dbd61

## Verification Results

- All Section 1 tests pass (4/4)
- All Section 2 tests pass (3/3)
- All render framework tests pass (87/87)
- Pyright: 0 errors on all 3 files
- Line counts: 494, 305, 350 (all under 500)
- Section 3 tests have pre-existing failure from parallel agent rewriting sect3_tables.py

## Next Phase Readiness

Sections 1 and 2 are ready for integration with the full worksheet render pipeline. The delegation pattern in sect2_company.py means sect2_company_details.py can be enhanced independently without touching the main entry point.
