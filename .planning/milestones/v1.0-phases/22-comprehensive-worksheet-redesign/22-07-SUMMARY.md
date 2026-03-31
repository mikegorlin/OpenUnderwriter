---
phase: 22-comprehensive-worksheet-redesign
plan: "07"
subsystem: render
tags: [markdown, jinja2, template, helpers, context-builders]
depends_on:
  requires: ["22-01", "22-02", "22-03", "22-04", "22-05", "22-06"]
  provides: ["Rich Markdown context builders", "Redesigned Jinja2 template"]
  affects: ["22-10"]
tech_stack:
  added: []
  patterns: ["3-module helper split", "typed state narrative with dict fallback", "compact Jinja2 single-row tables"]
key_files:
  created:
    - src/do_uw/stages/render/md_renderer_helpers_scoring.py
  modified:
    - src/do_uw/stages/render/md_renderer_helpers.py
    - src/do_uw/stages/render/md_renderer_helpers_ext.py
    - src/do_uw/stages/render/md_renderer.py
    - src/do_uw/templates/markdown/worksheet.md.j2
decisions:
  - id: "22-07-01"
    decision: "Split scoring/AI risk/meeting prep into new md_renderer_helpers_scoring.py for 500-line compliance"
  - id: "22-07-02"
    decision: "Compact Jinja2 tables (single-row horizontal layout) to keep template under 500 lines while preserving all data"
  - id: "22-07-03"
    decision: "Narratives sourced from typed AnalysisState (primary) with dict fallback for backward compat"
  - id: "22-07-04"
    decision: "Re-exports maintained in md_renderer_helpers.py for backward compatibility (pdf_renderer, dashboard imports)"
metrics:
  duration: "~12 min"
  completed: "2026-02-11"
---

# Phase 22 Plan 07: Markdown Renderer Helpers + Template Redesign Summary

**One-liner:** Rich typed context builders for all 8 sections + compact Jinja2 template with tables, narratives, and D&O context

## What Was Built

### Task 1: Rewrite Markdown template context builders (629d687)

Rewrote 4 Python files to extract rich structured data from AnalysisState for Jinja2 template rendering.

**md_renderer_helpers.py (497 lines)** -- Sections 1-4:
- `extract_exec_summary()`: snapshot table, inherent risk baseline, claim probability dict, tower recommendation dict, key_findings with impact detail
- `extract_company()`: CIK, exchange, FPI, SIC description, revenue_segments list, geographic_footprint list, subsidiary_count, exposure_factors list
- `extract_financials()`: Beneish M-Score/zone, Piotroski F-Score/zone, auditor details (name, is_big4, tenure), material_weaknesses, going_concern, peers list with typed structure
- `extract_market()`: return_1y, max_drawdown_1y, volatility_90d, beta, short_trend_6m, worst_drop events, earnings_guidance dict, analyst_consensus
- Re-exports from _ext and _scoring modules for backward compatibility

**md_renderer_helpers_ext.py (398 lines)** -- Sections 5-6:
- `extract_governance()`: full leadership stability table data (tenure/status/prior_litigation), board quality metrics, top_holders list, known_activists, anti_takeover provisions with implications, sentiment signals, departures_18mo
- `extract_litigation()`: enriched case table (court, lead_counsel, filing_date), SEC enforcement pipeline, derivative count, industry patterns, defense strength, litigation reserve

**md_renderer_helpers_scoring.py (243 lines, NEW)** -- Sections 7-8 + Meeting Prep:
- `extract_scoring()`: factor breakdown with ID/pct_used/top_evidence, red flag gates with ceiling/max_tier, tier detail (action, probability_range, score_range), binding_ceiling, claim_probability, severity_scenarios, allegation_mapping (from TheoryExposure), risk_type, calibration_notes
- `extract_ai_risk()`: unchanged from original (already well-structured)
- `extract_meeting_questions()`: unchanged from original

**md_renderer.py (177 lines):**
- Updated `build_template_context()` to generate narratives from typed AnalysisState (primary) with dict fallback
- Added `company_narrative` and `scoring_narrative` context variables
- Signature unchanged for pdf_renderer and dashboard consumers

### Task 2: Redesign Markdown Jinja2 template (9fcdb1e)

Redesigned worksheet.md.j2 from 374 lines to 479 lines with all 8 sections showing rich data.

Key template improvements by section:
- **Section 1**: Company snapshot table, inherent risk baseline, claim probability (horizontal 3-col table), tower recommendation
- **Section 2**: Merged ticker/CIK and state/FPI rows, revenue segments table, geographic footprint table, exposure factors
- **Section 3**: 4-model distress table with benchmarks, horizontal audit risk table, peer comparison table
- **Section 4**: Merged stock performance + short interest table, earnings guidance table, analyst consensus (horizontal), worst drop event, claims-made context
- **Section 5**: Leadership stability table, full board metrics, horizontal comp/ownership table, top holders list, anti-takeover provisions, horizontal sentiment table
- **Section 6**: Merged SEC enforcement + defense + reserve into single horizontal table, enriched case table with court/counsel
- **Section 7**: Horizontal tier classification table, factor breakdown, red flag gates, claim probability, severity scenarios, allegation mapping, risk type, calibration notes
- **Section 8**: Compact peer comparison, all sub-dimensions
- **Appendix**: Compact meeting prep format with inline reassuring/concerning responses

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] allegation_map field name mismatch**
- **Found during:** Task 1
- **Issue:** Plan referenced `sc.allegation_map` but the actual field on ScoringResult is `sc.allegation_mapping` with `.theories` list of `TheoryExposure`
- **Fix:** Used correct field path `sc.allegation_mapping.theories` with proper TheoryExposure attribute access
- **Files modified:** md_renderer_helpers_scoring.py

**2. [Rule 3 - Blocking] 500-line limit for md_renderer_helpers.py**
- **Found during:** Task 1
- **Issue:** Initial rewrite was 567 lines, exceeding 500-line limit
- **Fix:** Compacted docstrings, removed section separator comments, condensed dict literals to 497 lines
- **Files modified:** md_renderer_helpers.py

**3. [Rule 3 - Blocking] 500-line limit for worksheet.md.j2**
- **Found during:** Task 2
- **Issue:** Initial template was 668 lines (from original 374), far exceeding 500-line limit
- **Fix:** Compacted horizontal single-row tables (audit, compensation, sentiment, enforcement), merged stock+short tables, inline meeting prep format, removed verbose D&O blockquotes -- achieved 479 lines
- **Files modified:** worksheet.md.j2

## Verification

- 106 render tests pass (test_render_outputs.py + test_render_framework.py)
- 0 pyright errors across all 4 Python files
- All files under 500 lines (497, 398, 243, 177, 479)
- build_template_context() and render_markdown() signatures unchanged
- Backward-compatible re-exports maintained

## Next Phase Readiness

Plan 22-10 (final integration) can now verify Markdown output matches Word content richness. The context builders and template are fully redesigned.
