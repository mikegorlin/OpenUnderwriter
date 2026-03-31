# Phase 25: Classification Engine & Hazard Profile - Context

**Gathered:** 2026-02-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the classification engine (3 objective variables → base filing rate) and hazard profile engine (7 categories, 47 dimensions → Inherent Exposure Score 0-100). These implement Layers 1-2 of the five-layer analysis architecture defined in the Phase 24 unified framework. The engines produce the "starting point" for every company analysis — structural risk assessment before any behavioral signals are considered.

This phase does NOT reorganize existing checks (Phase 26), build bear case/peril mapping (Phase 27), or change the presentation layer (Phase 28).

</domain>

<decisions>
## Implementation Decisions

### Classification variables
- **Exactly 3 variables**: market cap tier, industry sector (SIC/NAICS), IPO age (years since listing)
- Exchange/index membership dropped — redundant with market cap + industry
- FPI status, dual-class, analyst coverage considered and rejected for classification (may appear as hazard dimensions instead)
- **5 market cap tiers**: Mega (>$200B, 6-8%), Large ($10-200B, 4-6%), Mid ($2-10B, 3-4%), Small ($300M-2B, 2-3%), Micro (<$300M, 1-2%)
- **IPO age decay**: 3-year cliff model. Full 2.8x multiplier for years 0-3, drops to 1.5x for years 3-5, then 1.0x after 5 years
- **Output**: Single base filing rate + severity band (not a range with confidence interval). Example: "6.2% annual filing rate, $45-120M severity band"

### Hazard dimension selection
- **Keep all 47 dimensions** from the research taxonomy — do not trim
- **Rebalanced weights**: Business Model UP to 30-35% (from 25%), Governance DOWN to 5-10% (from 15%). Per Kim & Skinner (2012), governance adds relatively little predictive value beyond structural characteristics
- Proposed weights: Business 30-35%, People 15%, Financial 15%, Governance 5-10%, Maturity 10%, Environment 10%, Emerging 10%
- **Non-automatable dimensions** (Baker & Griffith "deep governance" — tone at top, management character): Use proxy signals for scoring, AND flag for underwriter attention with specific meeting prep questions. System never claims to assess "character" — it provides indicators and says "ask about this in the meeting"
- **Worksheet visibility**: IES score + hazard highlights in executive summary. Full 47-dimension breakdown available in appendix/drill-down section

### IES scoring & interactions
- **Named interaction effects in config + dynamic detection**: Hardcode 4-6 named patterns (Rookie Rocket, Black Box, Imperial Founder, Acquisition Machine) in JSON config with multiplier ranges. ALSO detect novel combinations dynamically and flag as "elevated co-occurrence"
- **IES-to-tier mapping**: Claude's discretion to determine the best relationship between IES bands and tier assignment
- **Combination model**: Multiplicative. Filing rate = base_rate × IES_multiplier. IES=50 (neutral) = 1.0x. Higher IES = higher multiplier
- **Transparency**: Full 47-dimension breakdown shown with individual scores, weights, and contribution to IES. All computation visible

### Output & integration
- **Replaces old inherent risk baseline** but keeps old as silent validation. New classification + IES replaces the market-cap-x-industry baseline. Old baseline computed silently as sanity check; if they diverge significantly, system flags it
- **Pipeline position**: After EXTRACT, before ANALYZE. Classification needs market cap + industry (from RESOLVE). Hazard profile needs governance, financial structure data (from EXTRACT). Both complete before ANALYZE runs checks
- **IES as Factor 0 (pre-factor)**: IES becomes the baseline BEFORE the 10-factor (F1-F10) scoring adjustments. Factors modify the IES-adjusted rate. IES = "where you start", factors = "what the signals say"
- **Caching**: Claude's discretion based on computational cost

### Claude's Discretion
- IES-to-tier band mapping (what IES score maps to which underwriting action)
- Caching strategy (recompute vs. cache in state.json)
- Exact multiplier values for IES-to-filing-rate conversion
- Dynamic interaction detection algorithm
- Hazard dimension data source mapping (which EXTRACT outputs feed which dimensions)

</decisions>

<specifics>
## Specific Ideas

- The 5-layer architecture is defined in `24-UNIFIED-FRAMEWORK.md` — this phase implements Layers 1-2
- Full hazard taxonomy with 7 categories and 47 dimensions is in `research/HAZARD_DIMENSIONS_RESEARCH.md`
- Industry validation and weight recommendations in `research/HAZARD_MODEL_VALIDATION.md`
- The user explicitly wanted classification to be ONLY 3-4 objective variables — no subjective judgment at classification stage. Subjectivity lives in the hazard profile
- "Initial inherent risk should be only 3 or 4 top objective variables, this will go under classifications and then we'll have subjective adjustments"
- Classification = automated, deterministic. Hazard profile = where judgment lives
- Named interaction effects should be branded/memorable ("Rookie Rocket" not "Interaction Pattern 1")

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 25-classification-engine-hazard-profile*
*Context gathered: 2026-02-11*
