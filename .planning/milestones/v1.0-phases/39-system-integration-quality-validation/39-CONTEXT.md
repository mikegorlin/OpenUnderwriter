# Phase 39: System Integration & Quality Validation - Context

**Gathered:** 2026-02-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Run end-to-end pipeline on real tickers (AAPL, TSLA), verify all 3 output formats produce solid worksheets, validate the knowledge feedback/learning loop works end-to-end, fix ALL false triggers in check evaluation, clean up architectural debt (directory moves, file splits, dead code), add LLM token tracking, and confirm the system is ready for continuous improvement.

</domain>

<decisions>
## Implementation Decisions

### False Trigger Triage
- **Zero tolerance** for false triggers — every triggered check must be genuinely relevant to the data it evaluates
- **Full audit** of both AAPL and TSLA — review every TRIGGERED check result for accuracy
- **Audit SKIPPED checks too** — a skipped check that should have fired is equally bad; both undermine underwriter trust
- **Fix the check logic itself** — improve field routing, threshold parsing, or mapper logic so checks evaluate against the correct data. No exclusion rules or workarounds.
- Discovery method: run full backtest on both tickers, audit every TRIGGERED and SKIPPED result

### Worksheet Quality Bar
- **Single source of truth** — completeness, accuracy, AND actionability all matter equally. An underwriter must be able to make decisions based solely on this worksheet.
- **Clarity and transparency are paramount** — every data point sourced, every risk signal visible, every narrative tells a clear story
- **Deal-breakers (any of these = reject):**
  - Wrong company data (data integrity failures like TSLA showing Tim Cook)
  - Missing known public risk signals (active lawsuits, SEC investigations not appearing)
  - Unsourced claims presented as fact
  - Stale data presented as current
  - Misleading narrative that downplays real risks
- **Reusable quality checklist** — create a standard per-section verification checklist that becomes part of the system for every run, not a one-time review
- **All 3 formats (Word, PDF, Markdown) must meet the same quality bar** — underwriters may use any of them

### Architecture Cleanup Scope
- **Broader sweep** beyond named items — use this as an opportunity to clean up anything violating anti-context-rot rules
- Named items: classify/ and hazard/ directories → analyze/layers/, checks.json sync from DuckDB, calibrate.py split
- **Pragmatic 500-line enforcement** — split files that are genuinely hard to navigate; well-organized cohesive files slightly over 500 lines are acceptable
- **Reusable dead code detection tool** — build a script/command that can be re-run after any phase, not a one-time vulture scan
- **Full import cleanup** on directory moves — update every import across the codebase, no backwards-compat shims or re-exports

### Knowledge Loop Validation
- **Full round-trip testing** — submit feedback → verify persistence in DuckDB → re-run calibration → confirm score actually changed → verify learning persists
- **Three feedback scenarios to test:**
  1. Score overrides — "This company should be HIGH risk, not MEDIUM" → verify future scoring adjusts
  2. False trigger reports — "This check fired incorrectly" → verify check gets suppressed or adjusted
  3. Data corrections — "Revenue was wrong, here's the real number" → verify correction persists
- **Real SEC filings** for document ingestion tests — prove the pipeline works with real-world data, not synthetic test documents

### LLM Token Tracking
- **Worksheet footer** — include data freshness date and estimated API cost in the final worksheet output for transparency
- Per-stage token count and cost in pipeline logs

### Claude's Discretion
- Exact approach to backtest automation (script vs. test harness)
- Which dead code detection tool to use or build
- Organization of the reusable quality checklist (config file vs. code vs. test suite)
- Order of operations within the phase (cleanup first vs. fixes first vs. parallel)

</decisions>

<specifics>
## Specific Ideas

- The worksheet is the product — it must be a document an underwriter can trust completely and base real decisions on
- False triggers are credibility-destroying — if the system flags something wrong, underwriters will stop trusting all flags
- The quality checklist should be part of the permanent system, not a document that gets forgotten
- Token cost in the worksheet footer adds transparency about what the analysis cost to produce

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 39-system-integration-quality-validation*
*Context gathered: 2026-02-21*
