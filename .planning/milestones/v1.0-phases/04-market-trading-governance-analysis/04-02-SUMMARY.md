---
phase: 04
plan: 02
subsystem: models
tags: [pydantic, market-data, SECT4, stock-drops, insider-trading, earnings, analyst, capital-markets]
dependency-graph:
  requires: [01-02, 03-01]
  provides: [market_events.py, extended MarketSignals]
  affects: [04-04, 04-05, 04-06, 04-07, 04-08, 04-09]
tech-stack:
  added: []
  patterns: [SourcedValue sub-model containers, model file splitting for 500-line limit]
key-files:
  created:
    - src/do_uw/models/market_events.py
    - tests/test_market_models.py
  modified:
    - src/do_uw/models/market.py
    - src/do_uw/models/__init__.py
decisions:
  - "StrEnum types (DropType, EarningsResult, GuidancePhilosophy, SeverityLevel) for categorical fields"
  - "Legacy MarketSignals fields (guidance_record, analyst_sentiment) kept for backward compat"
  - "Typed test helpers (_sv_str, _sv_float, _sv_int, _sv_bool) for pyright strict invariant generics"
metrics:
  duration: "5m 54s"
  completed: "2026-02-08"
  tests_added: 30
  tests_total_after: 294
---

# Phase 4 Plan 2: Market Event Sub-Models Summary

**One-liner:** 11 typed Pydantic sub-models for SECT4 market event extraction with full SourcedValue provenance and 30 tests.

## What Was Done

### Task 1: Create market_events.py (450 lines)
Created new model file with 11 typed Pydantic models covering all SECT4 extraction output:

- **SECT4-03 (Stock Drops):** StockDropEvent, StockDropAnalysis -- captures single-day and multi-day decline events with sector comparison, trigger identification, and company-specific flagging
- **SECT4-04 (Insider Trading):** InsiderTransaction, InsiderClusterEvent, InsiderTradingAnalysis -- individual Form 4 transactions, cluster selling detection, 10b5-1 plan tracking
- **SECT4-06 (Earnings Guidance):** EarningsQuarterRecord, EarningsGuidanceAnalysis -- per-quarter guidance vs actual, beat rate, consecutive miss streaks, guidance philosophy
- **SECT4-07 (Analyst Sentiment):** AnalystSentimentProfile -- coverage count, consensus, target prices, upgrade/downgrade counts
- **SECT4-08 (Capital Markets):** CapitalMarketsOffering, CapitalMarketsActivity -- shelf registrations, offerings, ATM programs, Section 11 windows
- **SECT4-09 (Adverse Events):** AdverseEventScore -- composite scoring with severity breakdown and peer ranking

All models use `SourcedValue[T]` for data fields, `ConfigDict(frozen=False)`, and `default_factory=lambda: []` for list fields.

Supporting StrEnum types: DropType, EarningsResult, GuidancePhilosophy, SeverityLevel.

### Task 2: Extend market.py and add tests
- **StockPerformance:** Added `returns_5y`, `returns_ytd`, `max_drawdown_1y` fields
- **MarketSignals:** Added 6 typed sub-model fields linking to market_events.py: `stock_drops`, `insider_analysis`, `earnings_guidance`, `analyst`, `capital_markets`, `adverse_events`
- **__init__.py:** Exported all 11 new models in public API
- **Tests:** 30 tests covering model instantiation, SourcedValue field creation, JSON round-trip serialization, and list field isolation

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| StrEnum types for categorical fields | Consistent with project pattern (Python 3.12+, enforced by ruff) |
| Keep legacy MarketSignals fields | Backward compatibility with existing code referencing guidance_record, analyst_sentiment |
| Typed test helpers (_sv_str, _sv_float, etc.) | SourcedValue[T] is invariant -- generic _sv(object) fails pyright strict |
| 450/190 line split | market_events.py (450) holds all sub-models, market.py (190) holds top-level aggregators |

## Deviations from Plan

None -- plan executed exactly as written.

## Verification

- ruff check: 0 errors on all files
- pyright: 0 errors, 0 warnings on all files
- pytest tests/test_market_models.py: 30/30 passed
- Full suite (excluding 04-01's concurrent filing_text changes): 336/337 passed, 1 unrelated failure
- market.py: 190 lines, market_events.py: 450 lines (both under 500)

## Commits

| Hash | Message |
|------|---------|
| 9ac5760 | feat(04-02): create market_events.py with SECT4 typed sub-models |
| 3a6d14b | feat(04-02): extend MarketSignals with SECT4 sub-models and add tests |
