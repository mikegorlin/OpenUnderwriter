# Phase 136: Forward-Looking and Integration - Research

**Researched:** 2026-03-26
**Domain:** Forward-looking D&O risk sections + cross-ticker integration validation
**Confidence:** HIGH

## Summary

Phase 136 builds four new forward-looking analytical sections and validates all v10.0 features across the test portfolio. The critical finding is that **substantial infrastructure already exists** for every requirement -- existing models, context builders, templates, and data pipelines cover 70-80% of the work. The phase is primarily about extending existing code (not building from scratch) and wiring new displays into the beta_report template.

The scenario generator (`scenario_generator.py`) already produces 5-7 score-impact scenarios with tier change analysis. Credibility assessment infrastructure exists (`credibility_context.py`, `CredibilityScore` model) but needs enhancement with the Phase 133 `build_earnings_trust()` data. Short interest data is already extracted and displayed in two places (market section + beta_report). Calendar data is already acquired via yfinance and partially rendered via `build_key_dates()`. The main work is: (1) enhancing scenarios with probability/severity/catalyst, (2) building a proper key dates calendar section, (3) extending credibility with pattern classification, (4) adding short-seller report detection, and (5) cross-ticker validation.

**Primary recommendation:** Follow the Phase 134/135 pattern -- models (extend existing) -> context builders (new functions in existing modules) -> templates (new .html.j2 files) -> beta_report wiring. All five FWD requirements can reuse existing data paths. No new acquisition or extraction is needed.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Reuse existing `scenario_generator.py`; extend with probability, severity, catalyst linkage
- D-02: Each scenario: Name | Probability | Severity ($) | Score Impact | Catalyst. Derived from scoring factors + signals, not hardcoded
- D-03: Display as cards with color-coded probability badges, not flat table. Progressive disclosure
- D-04: Calendar data from yfinance calendar, DEF 14A, SEC filings, 10-K risk factors. All already in acquired_data or extracted state
- D-05: Timeline/list sorted by date. Color code by urgency (30d red, 30-90d amber, >90d gray)
- D-06: Include monitoring triggers -- dates that should trigger re-underwriting
- D-07: Reuse earnings guidance data from Phase 133 (`build_earnings_trust()`). Quarter-by-quarter table
- D-08: Credibility patterns: "Consistent Beater" (>75% beat, small magnitude), "Sandbagging" (always beats large), "Unreliable" (>25% miss), "Deteriorating" (recent misses after beats)
- D-09: Check for short-seller reports from Citron, Hindenburg, Spruce Point, Muddy Waters, Kerrisdale via existing web search results
- D-10: Short interest trend from `state.extracted.market.stock`. Conviction labels: Rising/Stable/Declining
- D-11: Named firm reports as alert cards, short interest trend as mini-chart/sparkline with conviction badge
- D-12: Run pipeline on AAPL, RPM, V. Compare against golden baselines. No regressions
- D-13: Use existing `scripts/qa_compare.py`, extend for Phase 133-135 sections
- D-14: Validation is test/verification, not new feature -- execute after all forward-looking features

### Claude's Discretion
- Template layout for forward scenarios (cards vs table vs mixed)
- Key dates calendar visual format (timeline vs list)
- Short interest trend visualization approach
- Cross-ticker QA script enhancements

### Deferred Ideas (OUT OF SCOPE)
- Phase 132 (Page-0 Decision Dashboard) -- separate from this phase
- Real-time monitoring/alerting (would need a separate service, not pipeline)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FWD-01 | Named forward scenarios with probability, severity, score impact linked to company-specific catalysts | Existing `scenario_generator.py` already generates scenarios with score deltas and tier changes. Extend `_SCENARIO_TEMPLATES` with probability/severity fields and add catalyst derivation from signal results |
| FWD-02 | Key dates calendar: earnings, annual meeting, IPO milestones, regulatory deadlines, contract expirations | `build_key_dates()` in `_beta_report_uw_metrics.py` already extracts next earnings + dividend dates from yfinance calendar. Extend with DEF 14A annual meeting date, IPO milestones from filing dates, filing schedule dates |
| FWD-03 | Management credibility: quarter-by-quarter guidance vs actual with beat/miss magnitude and pattern | `build_earnings_trust()` already computes beat/miss patterns with reaction data. `CredibilityScore` model and `credibility_context.py` builder exist. Need pattern classification ("Consistent Beater", "Sandbagging", etc.) |
| FWD-04 | Short-seller report check from named firms (Citron, Hindenburg, etc.) | Web search results already in acquired_data (blind spot detection searches for company + risk terms). Need to scan search results for named firm mentions |
| FWD-05 | Short interest trend analysis with conviction direction | `ShortInterestProfile` model has `trend_6m`, `shares_short`, `shares_short_prior`, `short_pct_float`. Already displayed in both market section and beta_report. Need conviction label derivation + enhanced display |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | Data models (ForwardLookingData, etc.) | Project standard -- all models are Pydantic |
| Jinja2 | 3.x | HTML templates | Project standard -- all templates are Jinja2 |
| safe_float() | N/A | Numeric formatting | Project mandate -- never bare float() |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yfinance | (already installed) | Calendar data, earnings history | Already acquired in market_client.py |
| datetime | stdlib | Date parsing, urgency classification | Key dates calendar urgency |

No new dependencies needed. All features build on existing stack.

## Architecture Patterns

### Established Phase 134/135 Pattern (USE THIS)
```
1. Models:       Extend existing Pydantic models (forward_looking.py)
2. Context:      New builder functions in existing modules
3. Templates:    New .html.j2 files in sections/forward_looking/
4. Wiring:       Include in beta_report.html.j2
```

### Recommended New Files
```
src/do_uw/
  stages/render/context_builders/
    _forward_scenarios.py     # Enhanced scenario builder (extends scenario_generator.py)
    _forward_calendar.py      # Key dates calendar builder
    _forward_credibility.py   # Enhanced credibility with pattern classification
    _forward_short_sellers.py # Short-seller report detection + conviction
  templates/html/sections/
    forward_looking/
      scenarios.html.j2       # FWD-01: Scenario cards with probability badges
      key_dates.html.j2       # FWD-02: Calendar timeline
      credibility_enhanced.html.j2  # FWD-03: Enhanced credibility table
      short_seller_alerts.html.j2   # FWD-04: Named firm alert cards
      short_conviction.html.j2      # FWD-05: Short interest trend + conviction
```

### Context Builder Pattern (from Phase 134/135)
```python
def build_forward_scenarios(state: AnalysisState) -> dict[str, Any]:
    """Pure data formatter -- no evaluative logic.

    Reads existing scenario_generator output + signal results.
    Returns template-ready dict with scenarios, probability badges,
    severity estimates, and catalyst linkage.
    """
    # 1. Call existing generate_scenarios(state)
    # 2. Enhance each with probability/severity/catalyst from signal results
    # 3. Return template-ready dict
```

### Anti-Patterns to Avoid
- **Don't rebuild scenario generation** -- extend existing `generate_scenarios()` output
- **Don't add new data acquisition** -- all data already in acquired_data/extracted state
- **Don't put evaluative logic in templates** -- conviction labels, credibility patterns computed in Python
- **Don't duplicate short interest display** -- wire existing data through new builder, don't re-extract

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Scenario scoring | Custom score calculation | `generate_scenarios()` from scenario_generator.py | Already handles factor deltas, tier reclassification, 5-7 scenario trimming |
| Earnings beat/miss | Custom earnings parser | `build_earnings_trust()` from _market_acquired_data.py | Already computes beat rate, sell-off detection, consecutive miss count |
| Short interest data | Custom yfinance calls | `state.extracted.market.short_interest` (ShortInterestProfile) | Already extracted with trend_6m, shares_short, short_pct_float |
| Calendar data | Custom API calls | `state.acquired_data.market_data["calendar"]` | Already acquired via yfinance with next earnings, dividend dates |
| Date urgency classification | Complex date math | Simple `(target - today).days` comparison | 30/90 day thresholds are trivial |

## Common Pitfalls

### Pitfall 1: Scenarios Becoming Generic
**What goes wrong:** Scenarios like "SCA Filed" apply to any company. User CONTEXT says scenarios must link to company-specific catalysts.
**Why it happens:** Template approach without injecting actual signal/factor data.
**How to avoid:** Each scenario must reference the specific signal results or factor scores that make it relevant to THIS company. E.g., "Earnings Miss + 30% Drop" should reference the company's actual earnings beat rate and recent stock volatility.
**Warning signs:** Scenario descriptions that could apply to any company by changing the name.

### Pitfall 2: Key Dates Calendar Empty for Most Companies
**What goes wrong:** Calendar only has next earnings + dividend. Very sparse.
**Why it happens:** yfinance calendar is limited. DEF 14A annual meeting dates require extraction. Filing schedule dates are generic.
**How to avoid:** Supplement with: (1) quarterly earnings cycle from historical dates, (2) annual meeting from DEF 14A extraction (already in governance data), (3) IPO milestones for recent IPOs (already in extracted data), (4) filing deadlines from SEC schedule. Accept that some dates are estimates based on historical patterns.
**Warning signs:** Calendar with fewer than 3 entries.

### Pitfall 3: Credibility Pattern Misclassification
**What goes wrong:** "Sandbagging" vs "Consistent Beater" boundary is subjective. What counts as "large" magnitude?
**Why it happens:** No standard thresholds for beat magnitude.
**How to avoid:** Use industry-standard definitions: "Sandbagging" = beat rate >80% AND average beat magnitude >10%. "Deteriorating" = most recent 2+ quarters are misses after 4+ consecutive beats. These should be in config, not hardcoded.
**Warning signs:** Every company classified as "Consistent Beater" regardless of context.

### Pitfall 4: Short-Seller Report False Positives
**What goes wrong:** Web search mentions "Hindenburg" in unrelated context (the disaster, not the research firm).
**Why it happens:** Naive string matching on search results.
**How to avoid:** Match firm name + company name/ticker in same search result. Require both to be present. Also check for "report" or "short" in proximity.
**Warning signs:** Alert cards for companies that no short seller has actually targeted.

### Pitfall 5: Cross-Ticker Validation Scope Creep
**What goes wrong:** QA validation becomes a multi-hour pipeline run exercise, blocking phase completion.
**Why it happens:** Running full --fresh pipeline for 3 tickers with all stages.
**How to avoid:** Re-render from existing state.json (no pipeline re-run needed unless extraction changed). Use `qa_compare.py` to validate section presence. Focus on: new sections render without crash, existing sections unchanged.
**Warning signs:** Spending >50% of phase time on validation instead of feature building.

### Pitfall 6: N/A Flooding in Templates
**What goes wrong:** Forward-looking sections show mostly "N/A" values when data isn't available.
**Why it happens:** Not all companies have rich forward-looking data (e.g., no analyst estimates, no guidance history).
**How to avoid:** Every template section must have `{% if data %}` guards. Show "Data not available" message for empty sections rather than rendering N/A-filled tables. Test with RPM (mid-cap, less analyst coverage) not just AAPL.
**Warning signs:** Templates rendering with 50%+ N/A values.

## Code Examples

### Existing Scenario Generation (extend this)
```python
# Source: src/do_uw/stages/render/context_builders/scenario_generator.py
# Already returns: id, name, description, factor_deltas,
# current_score, scenario_score, current_tier, scenario_tier,
# score_delta, probability_impact

# Need to add: severity_estimate ($), catalyst (company-specific)
```

### Existing Earnings Trust (reuse for FWD-03)
```python
# Source: src/do_uw/stages/render/context_builders/_market_acquired_data.py
# build_earnings_trust() already returns:
# - earnings_reaction: per-quarter rows with day_of/next_day/week returns
# - earnings_trust_narrative: text assessment
# - earnings_trust_summary: beat_rate, beat_count, miss_count, etc.
```

### Existing Key Dates (extend this)
```python
# Source: src/do_uw/stages/render/context_builders/_beta_report_uw_metrics.py
# build_key_dates() already extracts: Next Earnings, Ex-Dividend, Dividend Payment
# from state.acquired_data.market_data["calendar"]
```

### Existing Short Interest Model
```python
# Source: src/do_uw/models/market.py (ShortInterestProfile)
# Fields: short_pct_float, trend_6m, shares_short, shares_short_prior,
#          short_pct_shares_out, days_to_cover
```

### Conviction Label Derivation Pattern
```python
# Derive from existing data:
def derive_conviction(si: ShortInterestProfile) -> str:
    """Rising/Stable/Declining from prior vs current shares short."""
    current = si.shares_short.value if si.shares_short else None
    prior = si.shares_short_prior.value if si.shares_short_prior else None
    if current is None or prior is None:
        trend = (si.trend_6m.value if si.trend_6m else "").upper()
        if "UP" in trend or "INCREAS" in trend:
            return "Rising"
        if "DOWN" in trend or "DECREAS" in trend:
            return "Declining"
        return "Stable"
    pct_change = (current - prior) / prior if prior > 0 else 0
    if pct_change > 0.10:
        return "Rising"
    elif pct_change < -0.10:
        return "Declining"
    return "Stable"
```

### Short-Seller Report Detection Pattern
```python
# Scan existing web search results in acquired_data
SHORT_SELLER_FIRMS = [
    "Citron Research", "Hindenburg Research", "Spruce Point Capital",
    "Muddy Waters Research", "Kerrisdale Capital",
]

def detect_short_seller_reports(state: AnalysisState) -> list[dict[str, Any]]:
    """Scan acquired web search results for named short-seller reports."""
    reports = []
    # Check state.acquired_data for web search results
    # Match firm name + company name/ticker in same result
    # Return: firm, title, date, url, summary
    return reports
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Generic scenario templates | Score-impact scenarios with factor deltas | Phase 131 | Scenarios now company-specific via scoring |
| Single credibility score | Beat/miss pattern with reaction analysis | Phase 133 | `build_earnings_trust()` already has the data |
| Simple short interest display | Short interest + trend + D&O interpretation | Phase 132 beta report | Already in beta_report lines 1158-1183 |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/render/ -x -q --tb=short` |
| Full suite command | `uv run pytest -x -q --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FWD-01 | Scenarios have probability, severity, catalyst fields | unit | `uv run pytest tests/render/test_scenario_generator.py -x` | Exists (extend) |
| FWD-02 | Key dates calendar with urgency classification | unit | `uv run pytest tests/render/test_forward_calendar.py -x` | Wave 0 |
| FWD-03 | Credibility pattern classification | unit | `uv run pytest tests/render/test_credibility_patterns.py -x` | Wave 0 |
| FWD-04 | Short-seller report detection | unit | `uv run pytest tests/render/test_short_seller_detection.py -x` | Wave 0 |
| FWD-05 | Short interest conviction labels | unit | `uv run pytest tests/render/test_short_conviction.py -x` | Wave 0 |
| Cross-ticker | QA validation across AAPL, RPM, V | integration | `uv run python scripts/qa_compare.py` | Exists (extend) |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/render/ -x -q --tb=short`
- **Per wave merge:** `uv run pytest -x -q --tb=short`
- **Phase gate:** Full suite green + cross-ticker QA green

### Wave 0 Gaps
- [ ] `tests/render/test_forward_calendar.py` -- covers FWD-02 key dates calendar
- [ ] `tests/render/test_credibility_patterns.py` -- covers FWD-03 pattern classification
- [ ] `tests/render/test_short_seller_detection.py` -- covers FWD-04 short-seller report detection
- [ ] `tests/render/test_short_conviction.py` -- covers FWD-05 conviction label derivation

## Open Questions

1. **Where do web search results live in state?**
   - What we know: Blind spot detection runs web searches for company + risk terms during ACQUIRE. Results are stored somewhere in acquired_data.
   - What's unclear: Exact path in state for web search results (need to verify for FWD-04 short-seller report scanning).
   - Recommendation: Check `state.acquired_data` for web search result paths during implementation. If not easily accessible, fall back to re-running a targeted search for known short-seller firms (within acquire boundary rules).

2. **DEF 14A annual meeting date extraction**
   - What we know: DEF 14A is already acquired and extracted for governance data.
   - What's unclear: Whether annual meeting date is currently extracted as a structured field.
   - Recommendation: Check extracted governance data for meeting date. If not present, add to LLM extraction schema as a simple date field.

3. **Severity estimation methodology**
   - What we know: Scenarios need a severity ($) estimate per D-02.
   - What's unclear: What methodology to use (market cap percentage? NERA settlement data? Simple formula?).
   - Recommendation: Use existing severity scenario data from scoring (already has settlement estimates by percentile). Map scenario probability to severity percentile. E.g., "SCA Filed" at 25th percentile settlement, "Restatement" at 75th percentile.

## Sources

### Primary (HIGH confidence)
- `src/do_uw/stages/render/context_builders/scenario_generator.py` -- existing scenario generation code
- `src/do_uw/stages/render/context_builders/credibility_context.py` -- existing credibility builder
- `src/do_uw/stages/render/context_builders/_market_acquired_data.py` -- earnings trust builder
- `src/do_uw/stages/render/context_builders/_beta_report_uw_metrics.py` -- existing key dates builder
- `src/do_uw/models/forward_looking.py` -- complete ForwardLookingData model
- `src/do_uw/models/market.py` -- ShortInterestProfile model
- `src/do_uw/templates/html/sections/beta_report.html.j2` -- current rendering integration points

### Secondary (MEDIUM confidence)
- `scripts/qa_compare.py` -- cross-ticker QA script (needs extension for new sections)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all patterns well-established in Phases 131-135
- Architecture: HIGH -- follows exact same pattern as Phases 134/135, all extension points identified
- Pitfalls: HIGH -- directly observed from existing code and CLAUDE.md rules
- Data availability: MEDIUM -- web search result paths for FWD-04 need verification during implementation

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable -- all dependencies are internal to the project)
