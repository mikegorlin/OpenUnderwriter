---
phase: 22-comprehensive-worksheet-redesign
plan: "06"
subsystem: render
tags: [ai-risk, meeting-prep, section-8, questions, word-renderer]
dependency_graph:
  requires: ["22-01"]
  provides: ["Company-specific AI risk Section 8 renderer", "Data-driven meeting prep question system"]
  affects: ["22-07", "22-08", "22-09", "22-10"]
tech_stack:
  added: []
  patterns: ["Helper constructors for compact question creation", "Category-organized question rendering"]
key_files:
  created: []
  modified:
    - src/do_uw/stages/render/sections/sect8_ai_risk.py
    - src/do_uw/stages/render/sections/meeting_prep.py
    - src/do_uw/stages/render/sections/meeting_questions.py
    - src/do_uw/stages/render/sections/meeting_questions_gap.py
    - tests/test_ai_risk_render.py
decisions:
  - id: "22-06-01"
    description: "Helper constructors _gap() and _cred() for compact question creation in meeting_questions_gap.py"
    rationale: "Reduces boilerplate from 573 to 378 lines while maintaining readability"
  - id: "22-06-02"
    description: "Category display order: CREDIBILITY_TEST first, then FORWARD_INDICATOR, GAP_FILLER, CLARIFICATION"
    rationale: "Most critical questions (credibility tests) presented first for meeting prioritization"
  - id: "22-06-03"
    description: "AI disclosure mismatch credibility tests check sentiment vs patent investment and adoption stance vs disclosure emphasis"
    rationale: "Detects misleading AI disclosure patterns relevant to Theory A securities claims"
metrics:
  duration: "~13m"
  completed: "2026-02-11"
---

# Phase 22 Plan 06: Section 8 AI Risk + Meeting Prep Redesign Summary

Company-specific AI risk section with sub-dimension scoring, peer comparison, and patent/disclosure data from LLM extraction; meeting prep generates data-driven questions citing actual extracted findings with source references.

## Tasks Completed

### Task 1: Redesign Section 8 AI Risk renderer
**Commit:** `204a57e`

Rewrote `sect8_ai_risk.py` from 258 to 465 lines for company-specific AI risk data.

**Changes:**
- Overview panel: composite score with threat level badge, industry model, disclosure trend
- Sub-dimension scoring table: 5 dimensions with score/weight/threat/evidence, D&O context for high-scoring dimensions
- AI Disclosures section: mention count, opportunity/threat split, sentiment, YoY trend, specific risk factors from filings
- Patent & Innovation section: patent count, filing trend, recent patent listings
- Peer comparison: summary metrics (company mentions, peer average, adoption stance, percentile rank) plus detailed peer mention breakdown with vs. Company delta column
- D&O context paragraphs for: high overall scores (>=70), high sub-dimensions (>=7), THREAT sentiment, LAGGING adoption
- Industry-specific narrative assessment with confidence attribution
- Forward indicators with D&O context for multiple signals
- Data source attribution footer
- Tests expanded from 12 to 17 (disclosure, patent, peer delta, no-disclosures, no-patents, overview panel)

### Task 2: Redesign Meeting Prep for data-driven questions
**Commit:** `e6ae776`

Rewrote all three meeting prep files (meeting_questions.py 400L, meeting_questions_gap.py 378L, meeting_prep.py 296L).

**meeting_questions.py changes:**
- MeetingQuestion dataclass retains `source_finding` and `expected_answer_range` fields
- All questions reference actual extracted data (Z-Score values, short interest percentages, SOL window dates)
- Added `_check_ai_forward` for AI risk forward indicators (score >= 70)
- Fixed model attribute references: SOLWindow.claim_type/trigger_date/sol_expiry, FactorScore.points_deducted/factor_id

**meeting_questions_gap.py changes:**
- Helper constructors `_gap()` and `_cred()` reduce boilerplate (573 -> 378 lines)
- Added `_check_ai_risk_gaps` for missing AI sub-dimension data
- Added `_check_single_source_data` for MEDIUM confidence non-proxy data
- Added `_check_ai_disclosure_mismatch` for OPPORTUNITY sentiment with zero patents, LAGGING adoption with optimistic disclosures
- Fixed model references: CompensationFlags.ceo_pay_ratio/say_on_pay_support_pct, PatternMatch.triggers_matched, RedFlagResult.evidence[0]

**meeting_prep.py changes:**
- Summary statistics table with total questions, high-priority count, per-category breakdown
- Category-organized rendering (CREDIBILITY_TEST -> FORWARD_INDICATOR -> GAP_FILLER -> CLARIFICATION)
- Color-coded category tags (red, orange, amber, blue)
- Source finding display for each question
- Priority indicator "(HIGH)" for priority >= 8.0
- Expected answer range display
- Footer with generation date

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created stub files for parallel agent imports**
- **Found during:** Task 1
- **Issue:** Parallel agents (22-04, 22-05) modified sect4_market.py and sect6_litigation.py to import from sect4_market_events.py and sect6_defense.py which didn't exist yet
- **Fix:** Created stub files with placeholder functions to unblock import chain
- **Files modified:** sect4_market_events.py, sect6_defense.py (later replaced by real implementations from parallel agents)

**2. [Rule 1 - Bug] Fixed model attribute references across meeting prep files**
- **Found during:** Task 2
- **Issue:** Multiple incorrect model attribute references: SOLWindow.trigger_event (should be claim_type), FactorScore.score (should be points_deducted), CompensationFlags.ceo_total_comp (doesn't exist), PatternMatch.contributing_factors (should be triggers_matched), RedFlagResult.evidence as string (is list[str])
- **Fix:** Updated all references to match actual Pydantic model field names
- **Files modified:** meeting_questions.py, meeting_questions_gap.py

**3. [Rule 1 - Bug] Fixed meeting_questions_gap.py over 500-line limit**
- **Found during:** Task 2
- **Issue:** Initial rewrite was 573 lines, exceeding 500-line limit
- **Fix:** Introduced _gap() and _cred() helper constructors to reduce boilerplate
- **Files modified:** meeting_questions_gap.py (573 -> 378 lines)

## Verification Results

- Pyright: 0 errors across all 4 modified files
- Tests: 123 passed (17 AI risk + 106 render framework/outputs)
- Line counts: sect8_ai_risk.py (465), meeting_prep.py (296), meeting_questions.py (400), meeting_questions_gap.py (378) -- all under 500
- Signatures preserved: render_section_8(doc, state, ds) and render_meeting_prep(doc, state, ds)

## Next Phase Readiness

All must-haves satisfied:
- AI Risk section shows company-specific AI scoring from actual filing data
- Industry-specific AI impact model classification rendered
- Peer comparison table with vs. Company delta column
- Meeting prep questions reference actual extracted data with source findings
- Questions categorized as CLARIFICATION, FORWARD_INDICATOR, GAP_FILLER, CREDIBILITY_TEST
