# Phase 27: Peril Mapping & Bear Case Framework - Context

**Gathered:** 2026-02-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement Layer 4 of the five-layer analysis architecture. Build the "who's suing" assessment that maps every company to plaintiff exposure across 7 lenses. Construct company-specific bear cases from actual analysis. Implement settlement prediction (replacing Phase 12's severity model), frequency/severity modeling, tower positioning intelligence, and plaintiff firm intelligence.

**Critical addition from user**: This phase MUST include a full data pipeline audit and wiring — every active check (~333) must have a verified ACQUIRE → EXTRACT → ANALYZE data path before Phase 28 begins. Three-state data_status (EVALUATED / DATA_UNAVAILABLE / NOT_APPLICABLE) on all CheckResults. Coverage Gaps section in the worksheet for the small number of checks where public data genuinely doesn't exist.

</domain>

<decisions>
## Implementation Decisions

### Bear Case Construction
- Claude's discretion on narrative style (structured templates vs complaint-style prose) — pick what the data supports
- Evidence-gated only: only construct bear cases where analysis found supporting signals. Clean company = 1-2 bear cases, troubled company = 5-6. Silence means clean.
- Tiered audience: summary for committee (2-3 sentences per bear case), detail drill-down for line underwriter (full narrative with evidence chain)
- Defense theory included ONLY when company-specific measures exist (actual forum selection clause, documented PSLRA safe harbor usage, etc.) — not generic defenses that every company could claim

### Data Pipeline Audit & Wiring
- Three-state data_status applies to ALL ~333 active checks, not just decision-driving
- The goal is to CLOSE gaps, not just label them. Audit identifies unwired checks, then this phase wires the data paths
- Validation: both end-to-end code trace (ACQUIRE → EXTRACT → ANALYZE chain verified in code) AND empirical test-ticker validation (run on AAPL, TSLA, XOM, SMCI, JPM — any check returning empty/default for ALL tickers is unwired)
- DATA_UNAVAILABLE is the rare exception for genuinely unobtainable public data (private settlement terms, internal board dynamics). Should be a SHORT list (5-10 items). These appear in a Coverage Gaps section in the worksheet.
- Checks that cannot be wired to any public data source get deactivated with reason — but the priority is wiring, not deactivating
- Always do deep web search as part of data acquisition — not a fallback, a first-class method

### Settlement Prediction Calibration
- REPLACES Phase 12's severity model — Phase 27 builds a better severity model, Phase 12's output recalculated using Phase 27 inputs. One model, not two.
- Uncertainty communicated as BOTH percentile ranges (25th-75th) for actuarial view AND named scenarios (Base/Adverse/Catastrophic) for narrative view
- When company-specific settlement comparables are thin, fall back to industry averages. Always produce a number, note the basis.
- Tower positioning: characterize risk by layer, don't prescribe specific attachment points. "Primary layer carries X% of expected loss exposure" — analytical, lets the underwriter decide.

### Plaintiff Lens Granularity
- Securities-first: shareholders + regulators get full probabilistic modeling. Other 5 lenses (customers, competitors, employees, creditors, government) get proportional treatment (present/absent + severity estimate)
- Data sources: SEC filings (Item 3, Item 1A, 8-K) + web search for all lenses. Use what we already acquire.
- Plaintiff firm intelligence: static config-driven tier list (top 10-15 firms classified elite/major/regional with severity multiplier). Dynamic tracking deferred to Phase 30.
- Display format: heat map style — 7x2 grid with probability band (Very Low/Low/Moderate/Elevated/High) and severity band (Nuisance/Minor/Moderate/Significant/Severe). Visual, scannable.

### Claude's Discretion
- Bear case narrative style (complaint-like prose vs structured analytical templates) — based on data richness
- Technical integration between the new severity model and Phase 12's actuarial pricing
- Exact methodology for frequency/severity model internals
- How to organize the data pipeline audit (by check category, by data source, by pipeline stage)

</decisions>

<specifics>
## Specific Ideas

- "Our goal is to ensure the data is available — that's the win. Putting out a report saying 'here it is, we have no info' would be a disaster." The data pipeline audit is not about transparency of gaps — it's about closing them.
- "All data mapping has to be done before we move on to 28." Phase 27 is the last phase before user-driven iteration. Everything must work.
- "Always do a deep search" — web search is first-class acquisition, not fallback. Every analysis run should include proactive discovery.
- Phase 27 requirements from earlier discussions: data coverage audit, three-state data_status, Coverage Gaps section, peril mapping + bear case construction, fold in presentation improvements from Phase 24 unified framework research.

</specifics>

<deferred>
## Deferred Ideas

- Dynamic plaintiff firm tracking from case outcome data — Phase 30 (Intelligence Augmentation & Feedback Loops)
- Converting unwirable checks to meeting prep questions — potential Phase 28 enhancement
- Company-specific defense theory database — could be a knowledge store enrichment in Phase 30

</deferred>

---

*Phase: 27-peril-mapping-bear-case-framework*
*Context gathered: 2026-02-12*
