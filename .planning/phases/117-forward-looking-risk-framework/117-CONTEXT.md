# Phase 117: Forward-Looking Risk Framework - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Surface every forward-looking claim the company has made, assess miss probability and SCA relevance, build management credibility scoring from historical guidance vs actuals, create company-specific monitoring triggers for post-bind surveillance, generate an algorithmic underwriting posture recommendation, and build a quick screen trigger matrix aggregating all RED/YELLOW flags with deep-dive routing and nuclear trigger verification.

</domain>

<decisions>
## Implementation Decisions

### Forward Statement Extraction
- **LLM extraction from 10-K + 8-K** — Extract forward-looking statements from 10-K (risk factors, MD&A) and 8-K (earnings releases, guidance updates) using LLM in EXTRACT stage. Map each to: metric guided, current value, guidance/target, miss risk assessment, SCA theory if missed
- **Miss risk algorithm** — Compare current trajectory to guidance midpoint. >10% gap = HIGH, 5-10% = MEDIUM, <5% = LOW. Adjust by management credibility score (track record <50% beat → +1 level, >80% beat → -1 level)
- **SCA relevance mapping** — HIGH miss risk + material metric → "10b-5: misleading forward guidance". MED miss risk + financial metric → "Potential earnings fraud theory". Deterministic mapping, not LLM-generated

### Management Credibility Scoring
- **yfinance earnings + LLM from 8-K** — yfinance provides historical EPS estimates vs actuals. LLM extracts company-specific revenue/margin guidance from 8-K earnings releases. Combine for credibility score
- **Track record**: % of quarters where management beat their own guidance
- **Credibility score**: HIGH (>80% beat), MEDIUM (50-80%), LOW (<50%)
- **Quarter-by-quarter table**: Quarter | Metric | Guided | Actual | Beat/Miss | Magnitude

### Monitoring Triggers
- **Company-specific thresholds** — Each trigger has a threshold derived from the company's actual data:
  - Stock below support level (from stock analysis)
  - Insider selling pace >2x current quarterly rate
  - EPS miss >10% (from credibility analysis)
  - CEO/C-suite departure (any)
  - SCA filing (any SCAC match)
  - Peer SCA (same SIC code)
- **Table format**: Trigger | Action | Threshold — all thresholds specific to THIS company, not generic industry standards

### Suggested Underwriting Posture
- **Algorithmic from scoring tier** — Decision matrix in brain YAML config mapping tier to underwriting posture:
  - WIN → full terms, standard retention, full tower, at-model pricing, standard exclusions, annual review
  - WANT → full terms with monitoring, standard retention, full tower, slight adjustment, standard exclusions, semi-annual review
  - WRITE → conditional terms, elevated retention, sublimit consideration, +10-20% pricing, targeted exclusions, quarterly review
  - WATCH → restricted terms, high retention, sublimit required, +25-50% pricing, broad exclusions, continuous monitoring
  - WALK → decline consideration, maximum retention, minimum limit, +50%+ pricing, extensive exclusions, monthly review
  - NO TOUCH → decline
- **Specific factor overrides** — Active SCA (F.1>0) → add litigation exclusion. Heavy insider selling (F.7>5) → add insider monitoring. Restatement (F.3>0) → add financial reporting exclusion
- **Table format**: Element | Recommendation | Rationale — all with company-specific reasoning

### Quick Screen / Trigger Matrix
- **Signal results aggregation** — Scan all signal results for TRIGGERED status with red/yellow threshold_level. Group by section. Each flag links to section anchor in HTML worksheet
- **Prospective checks** — Forward-looking checks with traffic light status (earnings expectations, regulatory decisions, competitive disruption, macro headwinds, major contracts)
- **5 nuclear triggers** — Verified explicitly with positive evidence:
  1. Active SCA (Stanford SCAC match)
  2. SEC investigation/enforcement (AAER match)
  3. Financial restatement (10-K disclosure)
  4. CEO/CFO departure under pressure (8-K Item 5.02)
  5. Going concern opinion (audit opinion)
- **Display**: "0/5 nuclear triggers fired ✓" — clean verification prominently displayed

### Claude's Discretion
- Exact LLM prompt design for forward statement extraction from 10-K/8-K
- How to handle companies that don't provide numeric guidance (qualitative-only)
- Prospective check data sources and assessment methodology
- Whether growth estimates table (FORWARD-05) uses yfinance consensus or extracted guidance
- Exact section placement in the HTML worksheet (new section or subsection of existing)
- Alternative forward-looking signals implementation (FORWARD-06: short interest trend, analyst sentiment, buyback support)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 115-116 Infrastructure (consume, don't rebuild)
- `src/do_uw/stages/analyze/do_context_engine.py` — Template evaluation engine
- `src/do_uw/stages/render/context_builders/_signal_consumer.py` — Signal result consumer pattern
- `src/do_uw/stages/benchmark/narrative_generator.py` — LLM narrative generation pattern (Phase 116)
- `src/do_uw/stages/benchmark/narrative_prompts.py` — Section-specific prompt builders

### Existing Forward-Looking Signals
- `src/do_uw/brain/signals/fwrd/` — 79 FWRD signals across 6 YAML files (guidance, M&A, transform, warnings)

### Scoring Model (for underwriting posture)
- `src/do_uw/models/scoring.py` — ScoringResult, tier boundaries, factor scores
- `src/do_uw/brain/config/` — Scoring weights and thresholds
- `src/do_uw/stages/render/context_builders/tier_explanation.py` — Tier boundary analysis (Phase 116)

### Data Sources (for extraction)
- `src/do_uw/stages/acquire/` — 8-K and 10-K acquisition
- `src/do_uw/stages/extract/` — LLM extraction patterns
- yfinance market_data (earnings_dates, analyst_price_targets, recommendations)

### Requirements
- `.planning/REQUIREMENTS.md` — FORWARD-01 through FORWARD-06, SCORE-02, SCORE-03, SCORE-05, TRIGGER-01 through TRIGGER-03

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `narrative_generator.py` + `narrative_prompts.py` — LLM narrative generation pattern from Phase 116
- `tier_explanation.py` — Algorithmic tier analysis with counterfactual (reuse for posture derivation)
- `_signal_consumer.py` — Signal result aggregation (reuse for quick screen flag collection)
- `safe_get_result()` / `get_signal_do_context()` — Established consumer pattern
- 79 FWRD signals already in brain YAML — some may already cover guidance/credibility checks

### Established Patterns
- LLM extraction in EXTRACT stage → structured data on state → context builders consume
- Algorithmic analysis in ANALYZE/BENCHMARK → stored on state → dumb renderers consume
- do_context on all signals → D&O columns on evaluative tables
- Collapsible sections with chevrons (CIQ pattern)

### Integration Points
- New extraction in EXTRACT: forward statements, guidance vs actuals
- New analysis in ANALYZE/BENCHMARK: miss risk, credibility score, monitoring thresholds, underwriting posture
- New rendering section(s): Forward Risk Map, Credibility, Triggers, Posture, Quick Screen
- Existing sections enhanced: scoring (ZER-001 verification, watch items)

</code_context>

<specifics>
## Specific Ideas

- The Quick Screen should be one of the FIRST things an underwriter sees — possibly in Section 1 (Executive Summary) or as a standalone section near the top
- Nuclear trigger verification should feel like a checklist — clean, prominent, unambiguous
- Monitoring triggers should be copy-paste ready for an underwriter's post-bind surveillance system
- The underwriting posture decision matrix should live in brain YAML config, not hardcoded Python — matching the brain portability principle

</specifics>

<deferred>
## Deferred Ideas

- Real-time monitoring dashboard (different product — worksheet is point-in-time)
- Automated bind/decline decisions (system augments judgment, doesn't replace it)
- Earnings call transcript analysis (paid API, out of scope for public-data-only constraint)

</deferred>

---

*Phase: 117-forward-looking-risk-framework*
*Context gathered: 2026-03-19*
