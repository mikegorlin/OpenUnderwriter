# Phase 24: Check Calibration & Knowledge Enrichment - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Calibrate the 359+ checks against real company output from 10-12 diverse tickers. Validate that checks fire correctly, produce quality evidence, and differentiate between risk profiles. Enrich the knowledge store with observations, new risk patterns, and industry-specific checks derived from claims research. Validate industry playbooks produce genuinely differentiated, claims-driven analysis — not generic boilerplate applied to every company.

This phase does NOT add new pipeline stages or change the rendering system. It improves the intelligence layer: checks, scoring weights, knowledge store, and playbooks.

</domain>

<decisions>
## Implementation Decisions

### Calibration methodology
- **Dual approach**: Ground truth for top 20 highest-impact checks (auto-ranked by scoring weight x fire rate x severity contribution), reasonableness testing for the remaining 339+
- **10-12 diverse tickers**: AAPL (clean mega), SMCI (distressed tech), XOM (energy stable), MRNA (biotech volatile), NFLX (entertainment growth), plus JPM (financial), PLUG (pre-revenue), HON (industrial conglomerate), COIN (crypto), DIS (media), and 1-2 more for coverage
- **Fix workflow**: Auto-fix obvious bugs (wrong threshold, missing data mapping, check logic errors). Report complex judgment-call issues for manual review. Both happen within this phase.
- **Top 20 checks selected automatically** by impact scoring — system ranks by (weight x fire rate x severity contribution), not manual selection

### Validation output format
- **CLI command + snapshot**: `do-uw calibrate` as a permanent repeatable CLI command. Phase 24 also commits a baseline snapshot to .planning/
- **Problem-centric summary**: Default view shows only anomalies — checks with 0% or 100% fire rate, LOW evidence quality, tier mismatches vs expectations, contradictions between sections
- **Per-ticker detail in Markdown**: Detailed per-ticker reports in output/calibration/ for drill-down. Summary in .planning/ for project tracking
- **MD-first**: Calibration results validated in Markdown before any visual work — separating "is the data right?" from "does it look good?"

### Knowledge enrichment scope
- **Auto-capture + review gate**: System captures all observations as INCUBATING. Surfaces the most interesting for review. Auto-promotes clear patterns after N confirmations across tickers
- **Discover new risk stories**: Validate the existing 17 composite patterns AND discover new ones from co-firing analysis. New patterns go to INCUBATING
- **Redundancy flagged for review**: When checks are identified as redundant (always co-fire), flag for human review — don't auto-deprecate
- **Scoring weight auto-adjustment within ±10%**: System can nudge weights within bounds based on calibration evidence. Larger changes require approval

### Industry playbook depth
- **Playbooks are CHECK FACTORIES**: Not just display layers — they generate industry-specific checks that trace back to real claim drivers
- **Claims-driven approach**: Research why claims actually happen in each vertical → identify metric precursors → create checks that extract those metrics from filings → compare to peers → flag anomalies
- **Industry-specific KPIs extracted from filings**: LLM extraction pulls industry KPIs (same-store sales for retail, book-to-bill for semiconductors, etc.) from 10-K. These become check data points compared to peer benchmarks
- **Deep validation for 4 verticals**: Tech, Healthcare, Energy, Biotech get deep validation (2-3 tickers each, claims research, KPI verification, new check creation)
- **Light validation for remaining 6**: Financial, CPG, Industrials, Media, REITs, Transportation get 1 ticker each with differentiation check. Review needed before deep treatment
- **Always be learning**: Validate existing claim intelligence AND actively research new patterns, theories, regulatory developments. Knowledge store never "complete"
- **Tied to checks**: Every industry insight must trace back to a check. "I found that energy companies get sued for X" → create check that looks for precursors of X in filings

### Claude's Discretion
- Which specific 10-12 tickers beyond the named ones
- Auto-ranking algorithm for top 20 checks
- Threshold for auto-promoting INCUBATING observations
- N value for "confirmed across N tickers" pattern promotion
- Format of CLI `calibrate` command flags and output structure

</decisions>

<specifics>
## Specific Ideas

- "Same-store sales is not a metric you would apply to a semiconductor company. You would be looking at a book-to-bill." — Playbooks must surface the RIGHT metrics for each industry, not generic financial ratios
- "If you go back to thinking and feeding the knowledge model through claims and then understanding how claims happen, that'll naturally happen." — Claims data drives everything: what to look for, what metrics matter, what checks to create
- "We should be finding the reasons why something gave rise to claims in the energy space. And maybe there's specific metrics that come into play and we ask questions about it." — Claims research → metric identification → check creation → filing extraction → peer comparison
- "This has to be essentially tied back to checks. And we should be continuing improving the checks." — Every playbook insight becomes a check. Playbooks are the mechanism for growing the check library with industry intelligence
- MD-first validation: verify all content correctness in Markdown output before separately working on visual presentation

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 24-check-calibration-knowledge-enrichment*
*Context gathered: 2026-02-11*
