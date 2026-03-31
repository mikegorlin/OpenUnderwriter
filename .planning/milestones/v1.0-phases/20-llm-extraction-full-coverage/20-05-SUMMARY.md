---
phase: 20
plan: 05
subsystem: extract
tags: [llm, debt, market, 8-K, ai-risk, integration, cross-domain]
depends_on: [20-02, 20-03]
provides: ["LLM-enriched debt analysis", "8-K event routing", "AI risk factor supplement"]
affects: ["render (narrative generators access LLM data)", "score (restatement flags)", "analyze (cross-domain signals)"]
tech_stack:
  patterns: ["LLM-first qualitative enrichment", "cross-domain event routing", "dedup supplementation"]
key_files:
  modified:
    - src/do_uw/stages/extract/debt_analysis.py
    - src/do_uw/stages/extract/extract_market.py
    - src/do_uw/stages/extract/extract_ai_risk.py
  created:
    - tests/test_llm_debt_integration.py
    - tests/test_llm_market_integration.py
    - tests/test_llm_ai_risk_integration.py
decisions:
  - id: D20-05-01
    decision: "Store 8-K event counts and restatement flags in state.acquired_data.market_data"
    rationale: "MarketSignals model lacks typed fields for 8-K events; market_data dict is the appropriate cross-domain store"
  - id: D20-05-02
    decision: "MD&A qualitative data stays on TenKExtraction, not forced into domain models"
    rationale: "revenue_trend, margin_trend, guidance_language have no natural home in ExtractedFinancials; narrative renderers access via get_llm_ten_k()"
  - id: D20-05-03
    decision: "LLM debt enrichment bootstraps empty debt_structure if regex found nothing"
    rationale: "Companies without parseable debt text may still have LLM covenant/facility context from Item 8 footnotes"
metrics:
  duration: "8m 18s"
  completed: "2026-02-11"
  tests_added: 15
  tests_total: 2323
---

# Phase 20 Plan 05: Debt/Market/AI Risk LLM Integration Summary

**One-liner:** LLM Item 8 footnotes enrich debt with covenant/facility context; 8-K events route to cross-domain signals; AI risk factors supplement keyword analysis.

## Completed Tasks

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | LLM debt enrichment | 0565c5d | _enrich_debt_with_llm() adds covenant status, credit facility detail, debt instruments to debt_structure |
| 2 | 8-K events + AI risk | 5d8134f | _enrich_with_eight_k_events() routes 5 event types; _supplement_ai_risk_factors() adds AI-categorized factors |

## What Was Built

### debt_analysis.py (473 lines)
- `_enrich_debt_with_llm()`: After regex debt_structure extraction, supplements with LLM Item 8 footnote context
- Covenant status stored in `debt_structure.value["covenants"]["covenant_status"]` as SourcedValue[str]
- Credit facility detail stored in `debt_structure.value["credit_facility"]["llm_detail"]` as SourcedValue[str]
- Debt instrument descriptions stored in `debt_structure.value["llm_debt_instruments"]` as list[SourcedValue[str]]
- Bootstraps empty debt_structure when regex found nothing but LLM has context
- XBRL numeric values (liquidity ratios, leverage ratios) never modified

### extract_market.py (335 lines)
- `_enrich_with_eight_k_events()`: Processes all 5 8-K event types from LLM extractions
- Departure count, agreement count, acquisition count, restatement count, earnings count stored in `state.acquired_data.market_data["eight_k_events"]`
- Restatement flag: `market_data["has_restatement"]` = True with `market_data["restatement_details"]` list
- All events logged with counts for pipeline observability

### extract_ai_risk.py (193 lines)
- `_supplement_ai_risk_factors()`: Finds risk factors with category "AI" from LLM 10-K extraction
- Appends factor titles to `AIDisclosureData.risk_factors` with case-insensitive dedup
- Non-AI factors (LITIGATION, CYBER, REGULATORY, etc.) ignored
- Runs after keyword-based disclosure extraction, before competitive positioning

## Key Design Decisions

1. **Cross-domain storage via market_data dict**: 8-K events span multiple domains (departures -> governance, restatements -> audit). Rather than modifying typed models not in this plan's scope, events are stored in the flexible `market_data` dict for downstream access.

2. **MD&A qualitative data left on TenKExtraction**: revenue_trend, margin_trend, guidance_language don't map to existing domain model fields. They remain accessible via `get_llm_ten_k(state)` for narrative generators in the RENDER stage.

3. **Bootstrap empty debt_structure**: When regex finds no filing text but LLM has covenant or facility context, the enricher creates a minimal debt_structure to hold the qualitative data.

## Deviations from Plan

None -- plan executed exactly as written.

## Verification Results

- `uv run pyright` on all 3 modified files: 0 errors
- `uv run ruff check src/do_uw/stages/extract/`: All checks passed
- All files under 500 lines (473, 335, 193)
- 15 new integration tests, all passing
- Full test suite: 2323 passed, 0 failures

## Next Phase Readiness

Plan 05 completes Wave 3 integration. The three sub-orchestrators (debt, market, AI risk) now leverage LLM converters from Plans 02/03 alongside Plans 04's company profile, audit risk, and ownership integration. Plan 06 (final wave) can proceed with full end-to-end integration testing.
