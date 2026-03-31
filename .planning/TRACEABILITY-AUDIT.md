# Full Chain Traceability Audit

**Date**: 2026-03-16
**Reference Run**: RPM-2026-03-10 (state.json, pipeline completed 2026-03-11T04:11:37)
**Code Base**: HEAD as of 2026-03-16 (post-Phase 110)

---

## Summary Statistics

| Metric | Count | % of Total |
|--------|-------|-----------|
| Total signals in YAML | 562 | 100% |
| Signals loaded by brain_unified_loader | 562 | 100% |
| Signals with execution_mode=AUTO | 555 | 98.8% |
| Foundational (skipped by design) | 28 | 5.0% |
| **Evaluable signals (AUTO, non-foundational)** | **527** | **93.8%** |
| Evaluated on RPM run | 473 | 84.2% |
| Not evaluated (post-RPM additions) | 54 | 9.6% |
| Non-AUTO (MANUAL/FALLBACK/SECTOR) | 7 | 1.2% |

### RPM Run Results (473 evaluated)

| Status | Count | % |
|--------|-------|---|
| INFO (data present, informational) | 218 | 46.1% |
| CLEAR (evaluated, no risk) | 146 | 30.9% |
| TRIGGERED (risk detected) | 45 | 9.5% |
| SKIPPED (data unavailable) | 64 | 13.5% |

### Rendering Chain

| Metric | Count |
|--------|-------|
| Manifest sections | 13 |
| Manifest sub-groups | 112 |
| Signal groups (unique) | 61 |
| Signal groups with manifest target | 61 (100%) |
| Manifest groups with NO signal source | 51 (45.5%) |
| Context builders | 18 |
| Context builders consuming signal_results | 3 (16.7%) |
| Context builders reading state directly | 15 (83.3%) |
| Section templates (.j2) | 127 |
| Templates consuming signal_results | 15 (11.8%) |
| Templates bypassing signals entirely | 112 (88.2%) |

### Acquisition Field Coverage

| Metric | Count |
|--------|-------|
| Unique acquisition fields declared in YAML | 142 |
| Fields with data in RPM run | 40 (28.2%) |
| Fields missing data | 102 (71.8%) |

---

## Chain Break Categories

### Category 1: No Data Acquisition (102 fields missing)

Signals declare data needs via `acquisition.sources[].fields` but the acquisition stage does not fetch or store data at those paths. Organized by domain:

**xbrl_forensics (35 fields)** -- DATA EXISTS but path mismatch. Data lives in `analysis.xbrl_forensics.*` (computed during ANALYZE), but signals declare paths like `analysis.xbrl_forensics.beneish.composite_score`. The signal mapper resolves these via the Phase 26 analytical mapper (`signal_mappers_analytical.py`), so these 35 signals DO evaluate. The acquisition field declarations are aspirational documentation, not functional wiring.

**LLM-extracted fields (8 fields)** -- Signals reference `llm.critical_accounting_estimates`, `llm.currency_risk`, `llm.geographic_regions`, `llm.has_vie`, `llm.interest_rate_risk`, `llm.non_gaap_measures`, `llm.regulatory_environment`. No LLM extraction pipeline populates these paths. These represent the "brain_fields dynamic extraction" concept from v2.0 that was never implemented.

**Company profile fields (12 fields)** -- Signals reference `company.business_changes`, `company.customer_concentration`, `company.disruption_risk`, `company.event_timeline`, `company.geographic_footprint`, `company.key_person_risk`, `company.market_cap`, `company.operational_resilience`, `company.revenue_model_type`, `company.revenue_segments`, `company.segment_lifecycle`, `company.segment_margins`, `company.subsidiary_count`, `company.subsidiary_structure`, `company.workforce_distribution`. Some of these exist in different state paths (e.g., market_cap is on `state.company.market_cap`); the declared acquisition paths don't match actual state structure.

**Litigation fields (5 fields)** -- `extracted.litigation.federal_dockets`, `extracted.litigation.other_legal_matters`, `extracted.litigation.sca_summary`, `extracted.litigation.securities_class_actions`, `extracted.litigation.workforce_product_environmental.product_recalls`. The actual litigation data lives in `extracted.litigation.active_cases` and similar paths; the signal field declarations don't match the state model.

**Market fields (4 fields)** -- `extracted.market.capital_markets.offerings_3yr`, `extracted.market.insider_analysis.cluster_events`, `extracted.market.ownership.institutional_pct`, `extracted.market.ownership.top_holders`. Some data exists but at different paths or structures.

**Governance fields (3 fields)** -- `extracted.governance.ownership.filings_13d_24mo`, `governance.comp_analysis.related_party_transactions`, `governance.esg_disclosures`, `governance.dual_class`. The data exists partially but path names diverge.

**Acquired data fields (7 fields)** -- `acquired_data.filings.8-K`, `acquired_data.filings.annual`, `acquired_data.filings.current_reports`, `acquired_data.filings.quarterly`, `acquired_data.news.blind_spot_post`, `acquired_data.news.blind_spot_pre`, `acquired_data.news.general`. These are raw acquisition artifacts that signals declare as inputs but the signal mapper doesn't resolve against `acquired_data`.

**Sector config files (4 fields)** -- `brain/config/sector_claim_patterns.yaml`, `brain/config/sector_hazard_tiers.yaml`, `brain/config/sector_peer_benchmarks.yaml`, `brain/config/sector_regulatory_overlay.yaml`. These config files don't exist. They're referenced by `SECT.claim_patterns` and `SECT.regulatory_overlay` foundational signals.

**Benchmark/other (8 fields)** -- `analyzed.benchmarks.frames_percentiles`, `analyzed.benchmarks.sector_percentiles`, `extracted.financials.audit.material_weaknesses`, `extracted.financials.audit.restatements`, `extracted.financials.profitability`, `extracted.financials.quarterly_periods`, `extracted.risk_factors[category=*]`, `extracted.sentiment`, `score_result.total_score`, `breach_history`, `cybersecurity_incidents`, `regulatory_actions`, `sanctions_violations`.

**Root Cause**: The `acquisition.sources[].fields` declarations in YAML are aspirational metadata documenting what data SHOULD flow to each signal. They are NOT functionally consumed by the signal engine. The actual data wiring happens through the signal mapper functions (`signal_mappers.py` + `signal_mappers_*.py`, ~4,000 lines) which use hardcoded prefix-based routing, not the YAML field declarations.

### Category 2: Data Acquired but Not Extracted (64 SKIPPED signals)

64 signals SKIPPED on the RPM run with one of two reasons:
- **39 signals**: "Required data not available from filings" -- extraction ran but didn't populate the specific field the signal mapper looks for
- **25 signals**: "Data mapping not configured for this check" -- no mapper function exists for the signal's prefix/ID pattern

These represent signals where the brain YAML defines data needs, the signal mapper can route them, but the extraction stage doesn't produce the expected fields. Examples include peer comparison data (`FIN.PEER.*`), some market data fields, and governance detail fields.

### Category 3: Signal Evaluates but Result Orphaned

**All 473 evaluated signals have at least one render path** via the `signal_results_by_section` grouping in `html_renderer.py` (line 252). This groups signals into section-level lists that are rendered in the 5 per-section `*_checks.html.j2` templates:
- `company_checks.html.j2` (section 1)
- `financial_checks.html.j2` (section 2)
- `governance_checks.html.j2` (section 3)
- `market_checks.html.j2` (section 4)
- `scoring_checks.html.j2` (section 5)

However, these check summary templates are **supplementary displays** (collapsed tables of signal names, statuses, evidence). They are NOT the primary rendered content. The primary section content (financial tables, governance profiles, litigation details, charts) comes entirely from context builders that read state directly.

**De facto orphaned from primary rendering**: All 473 signals. Their results appear in check summary panels but do not drive any primary section content. The primary content bypasses the signal engine entirely.

**Exception**: The `narrative.py` context builder (22 signal references) uses signal results to build narrative text for some sections. The `adversarial_context.py` builder (3 signal references) uses signals for the Devil's Advocate section. The `company.py` context builder (3 signal references) uses signals for a few company profile fields.

### Category 4: Renderer Bypasses Signal Engine (Critical Finding)

**15 of 18 context builders (83%) read ExtractedData/state directly without consulting signal results.** This is the primary architectural gap.

| Context Builder | Render Sections | Signal Refs | State Refs | Bypass? |
|----------------|----------------|-------------|------------|---------|
| `analysis.py` | Classification, hazard, risk type | 0 | 16 | YES |
| `audit.py` | QA audit, disposition | 0 | 2 | YES |
| `calibration.py` | Calibration notes | 0 | 4 | YES |
| `chart_thresholds.py` | Chart callout thresholds | 0 | 0 | YES (reads YAML) |
| `company.py` | Business profile, all sub-groups | 3 | 48 | PARTIAL (3 signal, 48 state) |
| `financials.py` | Income, balance sheet, key metrics | 0 | 2 | YES |
| `financials_balance.py` | Balance sheet details | 0 | 0 | YES (formatters) |
| `financials_forensic.py` | Forensic dashboard | 0 | 3 | YES |
| `financials_peers.py` | Peer percentiles, matrix | 0 | 3 | YES |
| `financials_quarterly.py` | Quarterly trends | 0 | 1 | YES |
| `governance.py` | Board, ownership, comp | 0 | 1 | YES |
| `litigation.py` | Active matters, settlement, SOL | 0 | 1 | YES |
| `market.py` | Stock, insider, short interest | 0 | 3 | YES |
| `pattern_context.py` | Pattern firing panel | 0 | 3 | YES |
| `scoring.py` | 10-factor, tier, claims | 0 | 8 | YES |
| `severity_context.py` | Severity scenarios | 0 | 3 | YES |
| `narrative.py` | Section narratives | 22 | 39 | PARTIAL |
| `adversarial_context.py` | Devil's Advocate | 3 | 3 | PARTIAL |

**What this means**: The rendered worksheet shows financial tables, governance profiles, litigation timelines, and market data pulled directly from `state.extracted.*` and `state.analysis.*`. Signal results only appear in collapsed check panels and narrative annotations. A signal could be TRIGGERED with CRITICAL severity, but the primary section it relates to would render identically whether that signal existed or not.

**51 manifest groups have zero signal coverage**, including critical sections:
- `allegation_mapping` -- allegation theory rendering (data from scoring stage, not signals)
- `claim_probability` -- claim probability display (data from scoring)
- `distress_indicators` -- Beneish/Altman display (data from analysis.xbrl_forensics)
- `earnings_quality` -- earnings quality metrics (data from analysis.xbrl_forensics)
- `exposure_factors` -- D&O exposure factors (data from extracted)
- `stock_performance` -- stock data display (data from extracted.market)
- `ten_factor_scoring` -- factor scores display (data from scoring.factor_scores)
- `tier_classification` -- tier display (data from scoring.tier)
- And 43 more.

### Category 5: Scoring Stage Bypasses Signal Engine (Critical Finding)

The 10-factor scoring engine (`stages/score/factor_data.py`) reads directly from `ExtractedData` and `CompanyProfile`, NOT from signal results:

```
F1_prior_litigation -> extracted.litigation (direct)
F2_stock_decline -> extracted.market.stock (direct)
F3_restatement_audit -> extracted.financials (direct)
F4_ipo_spac_ma -> extracted.financials (direct)
F5_guidance_misses -> extracted.market (direct)
F6_short_interest -> extracted.market (direct)
F7_volatility -> extracted.market (direct)
F8_financial_distress -> extracted.financials (direct)
F9_governance -> extracted.governance (direct)
F10_officer_stability -> extracted.governance (direct)
```

The only component that consumes signal results for scoring is:
- `hae_scoring.py` (H/A/E multiplicative scoring) -- reads signal results to compute H/A/E dimension scores
- `red_flag_gates_enhanced.py` -- reads signal results for DOJ, whistleblower, and executive aggregate CRF gates

The composite 10-factor score (81.3 for RPM) is computed entirely from extracted data. Signals do not influence it.

### Category 6: New Phase 110 Signals -- Wiring Status

**48 new signals** added in Phase 110 (mechanism evaluators + adversarial critique):

| Type | Count | Mechanism Dispatch | Data Available | Render Path | Group |
|------|-------|--------------------|----------------|-------------|-------|
| Absence (ABS.DISC.*) | 20 | YES (mechanism_evaluators.py) | Reads other signals | Check panels only | NONE |
| Conjunction (CONJ.*) | 8 | YES (mechanism_evaluators.py) | Reads other signals | Check panels only | NONE |
| Contextual (CTX.*) | 20 | YES (mechanism_evaluators.py) | Reads other signals + company | Check panels only | NONE |

**Will they fire on a real run?** YES -- mechanism dispatch code exists in `signal_engine.py` lines 125-141. They were not in the RPM-2026-03-10 run because the code was committed March 14-15 (after the run).

**Data availability**: These signals consume OTHER signal results (not extracted data), so they will fire whenever their required component signals have results. Conjunction signals need 2+ required signals to be TRIGGERED. Absence signals look for missing disclosures. Contextual signals adjust thresholds based on company size/sector/lifecycle.

**Render path**: ALL 48 have `group: ""` (empty). They will appear in the per-section check summary panels (via `signal_results_by_section` grouping on their `section` field), but they have no dedicated rendering target. No manifest group maps to them. No context builder consumes them.

**Additional Phase 110 additions**:
- `adversarial_engine.py` + `adversarial_context.py` -- Devil's Advocate section that DOES consume signals (one of 3 context builders with signal refs)
- `_adversarial_runner.py` + deep-dive trigger runner -- consume signal results to detect patterns

### Category 7: Trend Mechanism Signals (6 signals, no dispatch)

6 DISC.YOY signals declare `evaluation.mechanism: trend` but there is **no trend dispatch** in the signal engine. The engine dispatches `conjunction`, `absence`, and `contextual` (lines 127, 222-226), then falls through to the standard threshold evaluation path for all other mechanisms. For trend signals, this means they'd be evaluated as threshold signals if they have data, or SKIPPED if not.

These signals were added March 14-15 (post-RPM run) and would need either:
- A dedicated trend evaluator (comparing current vs prior period)
- Reclassification to threshold with appropriate field_key

Similarly, 9 `peer_comparison` mechanism signals exist -- they fall through to threshold evaluation and mostly SKIP due to missing peer data.

---

## Critical Path Gaps (Priority Order)

### 1. Scoring Engine Does Not Consume Signals (ARCHITECTURAL)
The 10-factor scoring engine reads ExtractedData directly. 473 signal evaluations are computed but do not influence the composite score (81.3), tier classification (WIN), or factor breakdowns. Only the HAE lens and CRF gates read signals, and these produce supplementary scores, not the primary composite.

**Impact**: Signals can detect severe risks (45 TRIGGERED on RPM) that have zero effect on the score an underwriter sees. The score is determined by a parallel, independent data path.

### 2. Context Builders Bypass Signals (ARCHITECTURAL)
83% of context builders read state directly. All primary rendered content (financial tables, governance profiles, litigation details, market data) comes from ExtractedData, not signal results. Signals appear only in collapsed check panels.

**Impact**: A signal could fire as CRITICAL but the section it relates to would render identically. The underwriter sees the same financial table whether a forensic signal detected manipulation or not.

### 3. Acquisition Field Declarations Are Non-Functional (DOCUMENTATION GAP)
142 acquisition fields declared in signal YAML. Only 40 (28%) have actual data. The declarations are aspirational metadata, not functional wiring. The actual data routing is in 4,000+ lines of hardcoded mapper functions.

**Impact**: The brain portability principle (YAML as the single source of truth) is violated. Signal YAML says what data it needs, but the system ignores those declarations and uses hardcoded mappers instead.

### 4. 48 Phase 110 Signals Have No Render Target (WIRING GAP)
All absence/conjunction/contextual signals have empty `group` fields. They'll fire but won't appear in any dedicated section.

**Impact**: New analytical capabilities (conjunction detection, disclosure gaps, contextual risk adjustment) compute results that are buried in check panels, not surfaced prominently.

### 5. 51 Manifest Groups Have No Signal Source (COVERAGE GAP)
45.5% of manifest groups render content without any signal governance. These include critical sections like allegation mapping, claim probability, tier classification, and 10-factor scoring.

**Impact**: Nearly half the worksheet's sections have no brain-signal traceability. Their content comes from scoring/analysis stages that operate independently of the signal framework.

### 6. Trend Mechanism Not Implemented (CODE GAP)
6 DISC.YOY trend signals and 9 peer_comparison signals have declared mechanisms with no evaluator dispatch. They fall through to threshold evaluation or skip.

**Impact**: Year-over-year disclosure changes (material weakness, new risk factors, legal proceedings delta) and peer comparisons cannot be properly evaluated.

### 7. 64 Signals SKIPPED Due to Data Gaps (DATA GAP)
13.5% of evaluated signals SKIPPED. 39 due to missing extraction data, 25 due to unconfigured mappers.

**Impact**: Known risk dimensions go unassessed. Includes peer comparisons, some market data, and governance details.

---

## Recommendations

### To achieve 100% traceability (full chain: acquire -> signal -> score -> render):

1. **Signal-Driven Scoring** (Gap #1): Refactor `factor_data.py` to read from signal results instead of ExtractedData. Each factor should be a weighted aggregation of its constituent signals. This is the v7.0 brain-centric architecture's core promise.

2. **Signal-Driven Context Builders** (Gap #2): Each context builder should consume signal results as its primary data source, with ExtractedData as the substrate that signals already evaluated. Signal status/severity should influence what gets highlighted, not just what appears in check panels.

3. **Functional Acquisition Wiring** (Gap #3): Either make the signal mapper resolve YAML `acquisition.sources[].fields` declarations at runtime (replacing 4,000 lines of hardcoded mappers), or accept that the mappers ARE the wiring and remove the aspirational field declarations from YAML.

4. **Render Target Assignment for Phase 110** (Gap #4): Assign `group` values to all 48 mechanism signals. Map conjunction signals to their most relevant manifest group (e.g., `CONJ.ACCT.governance` -> `audit_profile` or `forensic_dashboard`).

5. **Signal Coverage for Ungoverned Sections** (Gap #5): For each of the 51 unattached manifest groups, either create signals that govern their content or accept that they are "display-only" sections (and mark them as such in the manifest).

6. **Trend Evaluator** (Gap #6): Implement `evaluate_trend()` in `mechanism_evaluators.py` that compares current vs prior period values. Wire it into the signal engine dispatch alongside conjunction/absence/contextual.

7. **Data Wiring Sprint** (Gap #7): For the 64 SKIPPED signals, trace each to its required data source and either (a) add extraction logic, (b) add mapper routing, or (c) mark the signal as `execution_mode: DEFERRED` with a rationale.

### Priority ordering:
- Gaps #1 and #2 are **architectural** -- they represent the fundamental disconnect between the signal framework and the scoring/rendering chains. v7.0 was supposed to close this gap.
- Gaps #3-#7 are **wiring** gaps that can be addressed incrementally.
- The system currently has TWO parallel evaluation paths: (1) signal engine -> check panels, and (2) ExtractedData -> factor scoring -> rendering. The v7.0 vision is to collapse these into one: data -> signals -> everything else. That collapse has not happened.
