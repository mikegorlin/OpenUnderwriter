# Phase 27: Peril Mapping & Bear Case Framework - Research

**Researched:** 2026-02-12
**Domain:** D&O underwriting peril assessment, settlement prediction, data pipeline audit
**Confidence:** HIGH (internal codebase research, well-documented predecessor phases)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Bear Case Construction:**
- Claude's discretion on narrative style (structured templates vs complaint-style prose) -- pick what the data supports
- Evidence-gated only: only construct bear cases where analysis found supporting signals. Clean company = 1-2 bear cases, troubled company = 5-6. Silence means clean.
- Tiered audience: summary for committee (2-3 sentences per bear case), detail drill-down for line underwriter (full narrative with evidence chain)
- Defense theory included ONLY when company-specific measures exist (actual forum selection clause, documented PSLRA safe harbor usage, etc.) -- not generic defenses that every company could claim

**Data Pipeline Audit & Wiring:**
- Three-state data_status applies to ALL ~333 active checks, not just decision-driving
- The goal is to CLOSE gaps, not just label them. Audit identifies unwired checks, then this phase wires the data paths
- Validation: both end-to-end code trace (ACQUIRE->EXTRACT->ANALYZE chain verified in code) AND empirical test-ticker validation (run on AAPL, TSLA, XOM, SMCI, JPM -- any check returning empty/default for ALL tickers is unwired)
- DATA_UNAVAILABLE is the rare exception for genuinely unobtainable public data (private settlement terms, internal board dynamics). Should be a SHORT list (5-10 items). These appear in a Coverage Gaps section in the worksheet.
- Checks that cannot be wired to any public data source get deactivated with reason -- but the priority is wiring, not deactivating
- Always do deep web search as part of data acquisition -- not a fallback, a first-class method

**Settlement Prediction Calibration:**
- REPLACES Phase 12's severity model -- Phase 27 builds a better severity model, Phase 12's output recalculated using Phase 27 inputs. One model, not two.
- Uncertainty communicated as BOTH percentile ranges (25th-75th) for actuarial view AND named scenarios (Base/Adverse/Catastrophic) for narrative view
- When company-specific settlement comparables are thin, fall back to industry averages. Always produce a number, note the basis.
- Tower positioning: characterize risk by layer, don't prescribe specific attachment points. "Primary layer carries X% of expected loss exposure" -- analytical, lets the underwriter decide.

**Plaintiff Lens Granularity:**
- Securities-first: shareholders + regulators get full probabilistic modeling. Other 5 lenses (customers, competitors, employees, creditors, government) get proportional treatment (present/absent + severity estimate)
- Data sources: SEC filings (Item 3, Item 1A, 8-K) + web search for all lenses. Use what we already acquire.
- Plaintiff firm intelligence: static config-driven tier list (top 10-15 firms classified elite/major/regional with severity multiplier). Dynamic tracking deferred to Phase 30.
- Display format: heat map style -- 7x2 grid with probability band (Very Low/Low/Moderate/Elevated/High) and severity band (Nuisance/Minor/Moderate/Significant/Severe). Visual, scannable.

### Claude's Discretion
- Bear case narrative style (complaint-like prose vs structured analytical templates) -- based on data richness
- Technical integration between the new severity model and Phase 12's actuarial pricing
- Exact methodology for frequency/severity model internals
- How to organize the data pipeline audit (by check category, by data source, by pipeline stage)

### Deferred Ideas (OUT OF SCOPE)
- Dynamic plaintiff firm tracking (deferred to Phase 30)
- Prescriptive attachment point recommendations (Phase 27 characterizes risk by layer only)
</user_constraints>

## Summary

Phase 27 is the system's Layer 4 implementation: "Peril Mapping (Who Sues, How Bad)." It transforms the system from "here are the red flags" to "here's how this company gets sued and how bad it would be." There are four major workstreams: (1) 7-plaintiff-lens assessment with probability and severity per lens, (2) bear case construction from actual analysis findings, (3) settlement prediction replacing Phase 12's severity model with a better one calibrated from DDL + case characteristics, and (4) a full data pipeline audit ensuring all ~374 AUTO checks have verified ACQUIRE-to-EXTRACT-to-ANALYZE data paths, with three-state data_status on every CheckResult.

The codebase is well-positioned for this work. Phase 26 established the check classification infrastructure with `PlaintiffLens` enum (7 values matching the 7 lenses), `CheckCategory` (DECISION_DRIVING / CONTEXT_DISPLAY / FUTURE_RESEARCH), and `check_classification.json` mapping every check prefix to default lenses. The existing severity model (`severity_model.py`), actuarial model (`actuarial_model.py`), and allegation mapping (`allegation_mapping.py`) provide the foundation that Phase 27 replaces and enhances. Engine outputs are stored as `dict[str, Any]` on AnalysisResults (per Phase 26 decision), which means the new peril mapping outputs should follow the same pattern.

**Primary recommendation:** Organize into 5-6 plans: (1) data pipeline audit tooling + three-state data_status, (2) pipeline gap wiring, (3) peril mapping models + 7-lens assessment, (4) settlement prediction model replacing Phase 12 severity, (5) bear case construction + plaintiff firm intelligence, (6) render integration + coverage gaps section.

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pydantic v2 | 2.x | All data models (peril maps, bear cases, settlement predictions) | Project standard per CLAUDE.md |
| python-docx | 1.x | Word document rendering (heat map tables, bear case sections) | Already used for RENDER stage |
| matplotlib | 3.x | Heat map visualization for plaintiff lens grid | Already used for charts |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| textstat | 0.x | NLP readability metrics (already used in Phase 26 NLP engine) | If bear case narrative complexity metrics needed |
| httpx | 0.x | HTTP client for any new data acquisition paths | ACQUIRE stage only |

### No New Dependencies Required
Phase 27 builds entirely on existing infrastructure. No new external libraries are needed. The settlement prediction model, peril mapping, and bear case construction are all computational logic operating on existing extracted data.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
├── models/
│   └── peril.py                    # New: PerilMap, PlaintiffAssessment, BearCase, SettlementPrediction
├── config/
│   ├── plaintiff_firms.json        # New: Static tier list (elite/major/regional + severity multiplier)
│   └── settlement_calibration.json # New: DDL-to-settlement regression parameters, case multipliers
├── stages/
│   ├── analyze/
│   │   └── pipeline_audit.py       # New: Data pipeline audit tooling
│   ├── score/
│   │   ├── peril_mapping.py        # New: 7-lens assessment engine
│   │   ├── bear_case.py            # New: Bear case construction from findings
│   │   ├── settlement_prediction.py # New: Replaces severity_model.py settlement logic
│   │   └── severity_model.py       # Modified: Tower positioning refactored, settlement delegation
│   └── render/
│       └── sections/
│           ├── sect7_peril_map.py   # New: Heat map grid + bear case rendering
│           └── sect7_coverage_gaps.py # New: Coverage Gaps section
```

### Pattern 1: Engine Output as Dict (Phase 26 Convention)
**What:** Phase 26 established that analytical engine outputs are stored as `dict[str, Any]` on `AnalysisResults` to avoid coupling `AnalysisState` to engine-specific Pydantic models.
**When to use:** For all new Phase 27 outputs stored on state.
**Example:**
```python
# In AnalysisResults (state.py):
peril_map: dict[str, Any] | None = Field(
    default=None,
    description="Phase 27 peril map serialized from PerilMap model",
)

# In the engine:
peril = build_peril_map(state)
state.analysis.peril_map = peril.model_dump()  # Store as dict
```

### Pattern 2: Severity Model Replacement
**What:** Phase 27's settlement prediction REPLACES Phase 12's severity model. The existing `severity_model.py` has `model_severity()` which computes percentile scenarios from market cap + tier. Phase 27 builds a better model using DDL + case characteristics.
**When to use:** The new model produces the same output types (`SeverityScenarios`, `SeverityScenario`) so downstream consumers (tower recommendation, actuarial pricing, render) continue working unchanged.
**Integration approach:**
1. New `settlement_prediction.py` produces `SeverityScenarios` (same Pydantic model)
2. `severity_model.py::model_severity()` is replaced by `settlement_prediction.py::predict_settlement()`
3. The `ScoreStage.__init__.py` changes Step 11 to call the new function
4. Actuarial pricing (Phase 12) uses the new severity scenarios -- no changes to `actuarial_model.py` needed

### Pattern 3: Three-State Data Status on CheckResult
**What:** Every CheckResult gets a `data_status` field distinguishing EVALUATED / DATA_UNAVAILABLE / NOT_APPLICABLE.
**Current state:** CheckResult has `status: CheckStatus` with values TRIGGERED/CLEAR/SKIPPED/INFO. The SKIPPED status covers what should be two distinct cases: data not acquired vs. check not applicable.
**Implementation:**
```python
class DataStatus(StrEnum):
    """Three-state data availability classification."""
    EVALUATED = "EVALUATED"           # Data acquired, check ran
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"  # Check exists but data not acquired
    NOT_APPLICABLE = "NOT_APPLICABLE"      # Check doesn't apply to this company type

class CheckResult(BaseModel):
    # ... existing fields ...
    data_status: str = Field(
        default="EVALUATED",
        description="Data pipeline status: EVALUATED, DATA_UNAVAILABLE, NOT_APPLICABLE",
    )
    data_status_reason: str = Field(
        default="",
        description="Why data is unavailable or not applicable",
    )
```

### Pattern 4: Bear Case as Evidence-Gated Narrative
**What:** Bear cases are constructed ONLY from actual analysis findings, not generic templates. Each bear case has a committee summary (2-3 sentences) and a detail drill-down (full narrative with evidence chain).
**Design decision (Claude's discretion):** Use **structured analytical templates** rather than complaint-like prose. Rationale:
- The system has structured data (check results, factor scores, allegation mappings) -- structured templates map directly to this
- Complaint-style prose requires natural language generation that would need LLM calls in the SCORE stage (violates MCP boundary -- no LLM in post-ACQUIRE stages)
- Structured templates are reproducible, testable, and auditable
- The underwriter can read a structured template faster than prose
- When data is rich enough (many triggered checks in one area), the template naturally expands; when data is thin, it stays concise

**Template structure per bear case:**
```python
class BearCase(BaseModel):
    theory: AllegationTheory          # Which of the 5 allegation theories
    plaintiff_type: PlaintiffLens     # Primary plaintiff
    committee_summary: str            # 2-3 sentences for committee
    evidence_chain: list[EvidenceItem] # Ordered evidence supporting the case
    severity_estimate: str            # Severity band
    defense_assessment: str | None    # ONLY if company-specific defense exists
    probability_band: str             # Very Low through High
```

### Anti-Patterns to Avoid
- **Two severity models:** Phase 27 REPLACES Phase 12's severity model. Do not create a parallel model -- refactor the existing one.
- **Generic bear cases:** Never construct a bear case without at least 2 triggered checks supporting it. Clean companies get few/no bear cases.
- **N/A masquerading as clean:** DATA_UNAVAILABLE must never be displayed as "N/A" or "No issues found." The Coverage Gaps section must explicitly list what was not checked.
- **Scoring logic outside stages/score/:** Per CLAUDE.md, all scoring (including peril mapping) lives in `stages/score/`. Bear case construction is a scoring output, not an analysis output.
- **Data acquisition outside stages/acquire/:** The pipeline audit may identify needed data paths, but any new acquisition logic goes in ACQUIRE. The audit itself is analysis tooling.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DDL calculation | Custom market cap loss math | Reuse existing `SeverityScenarios.decline_scenarios` | Already computed in `severity_model.py`, proven tested |
| Plaintiff lens mapping | New mapping from checks to lenses | `check_classification.json::plaintiff_lens_defaults` | Phase 26 already mapped all 374 checks to plaintiff lenses |
| Tier-to-probability conversion | New probability estimation | `tier_classification.py::compute_claim_probability()` | Existing function, calibrated in Phase 25 |
| Config loading | New JSON loaders | `BackwardCompatLoader` from `knowledge/compat_loader.py` | Standard pattern for all brain configs |
| Chart rendering | Custom heat map drawing | `matplotlib` + existing `chart_helpers.py` patterns | Established chart infrastructure |

**Key insight:** Phase 27 builds ON TOP of a large existing infrastructure. The temptation will be to rebuild components that already exist. The primary risk is duplication, not missing capability.

## Common Pitfalls

### Pitfall 1: Scope Creep from Pipeline Audit
**What goes wrong:** The pipeline audit discovers dozens of unwired checks and the phase balloons trying to wire them all.
**Why it happens:** 374 AUTO checks, many with complex data paths. The audit will find that many checks return SKIPPED because the data mapper returns `{}`.
**How to avoid:**
1. Audit FIRST (Plan 1), quantify the gap
2. Prioritize wiring by check category: DECISION_DRIVING first, CONTEXT_DISPLAY second
3. Checks that need new ACQUIRE paths are a bigger lift than checks that need new mapper entries
4. Set a threshold: if >50% of checks are unwired, something is fundamentally wrong (investigate before mass-wiring)
**Warning signs:** More than 2 plans spent on wiring alone.

### Pitfall 2: Settlement Model Over-Engineering
**What goes wrong:** Building a complex settlement prediction model with insufficient calibration data.
**Why it happens:** The Cornerstone Research regression model uses ~20 variables. We don't have access to most of them (private settlement data, discovery records).
**How to avoid:** Build a simplified 5-step model per the framework:
1. DDL from stock drops (already have this)
2. Settlement percentage by case type (config-driven, ~1% of DDL for standard SCA)
3. Case characteristic multipliers (accounting fraud: 2x, institutional lead plaintiff: 1.5x, top-tier counsel: 1.3x)
4. Insurance cap consideration (available limits as settlement ceiling)
5. Expected loss = probability * adjusted_settlement
All parameters in config JSON, flagged NEEDS CALIBRATION.
**Warning signs:** Model has >10 input variables that aren't populated from actual data.

### Pitfall 3: Bear Case Without Evidence Gate
**What goes wrong:** System generates bear cases for clean companies, producing noise that undermines credibility.
**Why it happens:** Template approach that fills in every allegation theory regardless of findings.
**How to avoid:** Hard evidence gate: a bear case is ONLY constructed when its allegation theory has exposure_level of MODERATE or HIGH in the existing `AllegationMapping`. This is already computed by `allegation_mapping.py::map_allegations()`.
**Warning signs:** Bear cases appearing for companies with quality_score > 85.

### Pitfall 4: 500-Line Rule Violations
**What goes wrong:** New files exceed the 500-line limit per CLAUDE.md.
**Why it happens:** Peril mapping + bear cases + settlement prediction + pipeline audit is a lot of logic.
**How to avoid:** Pre-split files by responsibility:
- `peril_mapping.py`: 7-lens assessment (one function per lens)
- `bear_case_builder.py`: Bear case construction
- `bear_case_templates.py`: Template strings and evidence formatting
- `settlement_prediction.py`: DDL-to-settlement model
- `settlement_calibration.py`: Calibration data helpers
- `pipeline_audit.py`: Audit tooling
**Warning signs:** Any file approaching 400 lines during implementation.

### Pitfall 5: CheckResult Schema Change Breaking Tests
**What goes wrong:** Adding `data_status` field to CheckResult breaks 3020 existing tests.
**Why it happens:** CheckResult is used everywhere -- check engine, check mappers, factor scoring, pattern detection, render.
**How to avoid:** Add `data_status` as an optional field with a backward-compatible default of `"EVALUATED"`. The check engine sets it based on evaluation outcome:
- `status == SKIPPED` -> `data_status = "DATA_UNAVAILABLE"` (default for SKIPPED)
- `status == TRIGGERED/CLEAR/INFO` -> `data_status = "EVALUATED"`
- NOT_APPLICABLE requires explicit tagging (from check metadata or company type)
**Warning signs:** Test failures in test files not modified by Phase 27.

## Code Examples

### Example 1: Peril Map Assessment (One Lens)
```python
# Source: Internal architecture based on check_classification.json + allegation_mapping.py
def assess_shareholder_lens(
    check_results: dict[str, Any],
    allegation_mapping: AllegationMapping,
    claim_probability: ClaimProbability,
    severity_scenarios: SeverityScenarios | None,
) -> PlaintiffAssessment:
    """Full probabilistic assessment for shareholder lens."""
    # Count triggered checks mapping to SHAREHOLDERS
    shareholder_checks = [
        cr for cr in check_results.values()
        if "SHAREHOLDERS" in cr.get("plaintiff_lenses", [])
    ]
    triggered = sum(
        1 for cr in shareholder_checks
        if cr.get("status") == "TRIGGERED"
    )
    # Map allegation exposure to probability band
    theory_a = next(
        (t for t in allegation_mapping.theories
         if t.theory == AllegationTheory.A_DISCLOSURE), None
    )
    prob_band = _map_to_probability_band(
        claim_probability, triggered, theory_a
    )
    sev_band = _map_to_severity_band(severity_scenarios)
    return PlaintiffAssessment(
        plaintiff_type=PlaintiffLens.SHAREHOLDERS,
        probability_band=prob_band,
        severity_band=sev_band,
        triggered_check_count=triggered,
        total_check_count=len(shareholder_checks),
        key_findings=[...],
    )
```

### Example 2: Settlement Prediction (DDL-Based)
```python
# Source: Internal design from Phase 24 game theory research
def predict_settlement(
    market_cap: float | None,
    stock_drops: list[dict[str, Any]],
    case_characteristics: dict[str, bool],
    calibration_config: dict[str, Any],
) -> SeverityScenarios:
    """Predict settlement from DDL + case characteristics.

    Replaces severity_model.model_severity().
    """
    ddl = compute_ddl(market_cap, stock_drops)
    base_settlement_pct = calibration_config.get("base_settlement_pct", 0.01)  # ~1% of DDL

    # Apply case characteristic multipliers
    multiplier = 1.0
    for char_key, present in case_characteristics.items():
        if present:
            mult = calibration_config.get("multipliers", {}).get(char_key, 1.0)
            multiplier *= mult

    base_settlement = ddl * base_settlement_pct * multiplier
    # Build percentile scenarios around base
    scenarios = [
        SeverityScenario(percentile=25, label="favorable", settlement_estimate=base_settlement * 0.5, ...),
        SeverityScenario(percentile=50, label="median", settlement_estimate=base_settlement, ...),
        SeverityScenario(percentile=75, label="adverse", settlement_estimate=base_settlement * 2.0, ...),
        SeverityScenario(percentile=95, label="catastrophic", settlement_estimate=base_settlement * 4.0, ...),
    ]
    return SeverityScenarios(market_cap=market_cap or 0, scenarios=scenarios)
```

### Example 3: Pipeline Audit Check
```python
# Source: Internal design for pipeline audit tooling
def audit_check_pipeline(
    check_id: str,
    check_config: dict[str, Any],
    extracted: ExtractedData,
    company: CompanyProfile | None,
) -> dict[str, Any]:
    """Audit a single check's data pipeline."""
    from do_uw.stages.analyze.check_mappers import map_check_data

    data = map_check_data(check_id, check_config, extracted, company)
    all_none = all(v is None for v in data.values())

    return {
        "check_id": check_id,
        "has_mapper": bool(data),  # Empty dict = no mapper
        "all_values_none": all_none,
        "mapped_fields": list(data.keys()),
        "non_none_fields": [k for k, v in data.items() if v is not None],
        "data_status": (
            "NO_MAPPER" if not data
            else "ALL_NONE" if all_none
            else "HAS_DATA"
        ),
    }
```

## State of the Art

### Current System State vs Phase 27 Target

| Area | Current (Phase 26) | Phase 27 Target | Impact |
|------|-------------------|-----------------|--------|
| Severity model | Market cap tier-based ranges (severity_model.py) | DDL-based with case characteristic multipliers | More accurate, evidence-based predictions |
| Allegation mapping | 5 theories with HIGH/MODERATE/LOW | 7 plaintiff lenses with probability + severity bands | Broader coverage beyond securities fraud |
| Bear cases | Not implemented | Evidence-gated narrative per allegation theory | Concrete "how they get sued" stories |
| Check data_status | SKIPPED (one meaning) | EVALUATED / DATA_UNAVAILABLE / NOT_APPLICABLE | Honest data coverage reporting |
| Tower positioning | Tier-to-position lookup table | Risk-by-layer characterization with expected loss % | Analytical, not prescriptive |
| Pipeline coverage | Unknown -- no audit mechanism | Full audit with empirical validation | Close gaps before Phase 28 |

### Existing Infrastructure to Build On

| Component | Location | Phase 27 Uses It For |
|-----------|----------|---------------------|
| `PlaintiffLens` enum | `check_results.py` | 7 lens values already defined |
| `check_classification.json` | `config/` | All 374 checks already mapped to plaintiff lenses |
| `AllegationMapping` | `scoring_output.py` + `allegation_mapping.py` | Theory exposure levels drive bear case gating |
| `SeverityScenarios` | `scoring_output.py` | Output type preserved -- new model produces same shape |
| `lead_counsel_tiers.json` | `config/` | Plaintiff firm tier list (5 tier-1, 9 tier-2) |
| `claim_types.json` | `config/` | 9 claim types with SOL/repose/coverage |
| `actuarial.json` | `config/` | Defense cost factors, ILF parameters, loss ratio targets |
| `stock_drops.py` | `stages/extract/` | DDL computation from stock price declines |
| `check_mappers.py` + `check_mappers_phase26.py` | `stages/analyze/` | Data pipeline for all 374 checks |
| `BackwardCompatLoader` | `knowledge/` | Config loading pattern |

## Codebase Findings

### Finding 1: Check Inventory and Coverage (HIGH confidence)
- **381 total checks** in brain/checks.json (version 8.0.0)
- **374 AUTO checks** (0 MANUAL, 0 DEFERRED -- all executable)
- **312 with factors** (DECISION_DRIVING), **62 without** (CONTEXT_DISPLAY)
- **By section:** Sect 1: 40, Sect 2: 34, Sect 3: 65, Sect 4: 53, Sect 5: 101, Sect 6: 81
- **By plaintiff lens:** SHAREHOLDERS: 348, REGULATORS: 148, EMPLOYEES: 85, CREDITORS: 62, COMPETITORS: 25, CUSTOMERS: 17, GOVERNMENT: 11
- **Observation:** Shareholder coverage is deep (348 checks). Other lenses are proportionally covered but much thinner. This aligns with the user's "securities-first" decision.

### Finding 2: Current Severity Model Architecture (HIGH confidence)
- `severity_model.py::model_severity()` takes market_cap + tier + scoring_config
- Returns `SeverityScenarios` with 4 scenarios (25th/50th/75th/95th)
- Uses market-cap-tier base ranges from `scoring.json::severity_ranges.by_market_cap`
- Tier multipliers from `scoring.json::severity_ranges.tier_multipliers`
- Defense costs: fixed percentages per scenario (15%/20%/25%/30%)
- The 95th percentile is simply 2x the 75th -- no actual case data backing it
- `actuarial_model.py::compute_expected_loss()` consumes the severity scenarios
- `actuarial_layer_pricing.py` builds layer pricing from expected loss
- **Key point:** Replacing `model_severity()` with a DDL-based model preserves all downstream consumers because they only care about `SeverityScenarios`.

### Finding 3: Actuarial Pricing Integration Path (HIGH confidence)
- Phase 12's actuarial model (`actuarial_model.py`) reads `SeverityScenarios` from the SCORE stage
- The pricing chain: `model_severity() -> SeverityScenarios -> compute_expected_loss() -> layer_pricing -> calibrated_pricing`
- Phase 27's replacement model just needs to produce the same `SeverityScenarios` shape
- The `actuarial_pricing_builder.py::build_actuarial_pricing()` orchestrates the full chain
- Integration is in `ScoreStage.run()` at Step 11 (`model_severity`)
- **Risk:** If we change SeverityScenario fields (e.g., add `ddl_amount` population), we need to verify actuarial model still works

### Finding 4: CheckResult and Three-State Status (HIGH confidence)
- `CheckResult` in `check_results.py` has `status: CheckStatus` (TRIGGERED/CLEAR/SKIPPED/INFO)
- Adding `data_status: str` with default `"EVALUATED"` is backward-compatible
- 3020 tests exist -- all create CheckResults; default value prevents breakage
- The check engine (`check_engine.py`) already distinguishes SKIPPED (data missing) from other states
- `_make_skipped()` helper creates SKIPPED results -- easy to set `data_status = "DATA_UNAVAILABLE"` here
- NOT_APPLICABLE needs company-type context: e.g., `FIN.SECTOR.biotech` checks on a tech company

### Finding 5: Render Infrastructure (HIGH confidence)
- Current render sections: sect1 through sect8 (8 sections)
- `sect7_scoring.py` and `sect7_scoring_detail.py` render the scoring section
- A new `sect7_peril_map.py` section can be added following the same pattern
- Word renderer uses `docx_helpers.py` for tables -- the 7x2 heat map grid can use existing table helpers
- Markdown renderer has `md_renderer_helpers.py` -- same pattern
- Coverage Gaps section can be a new subsection of sect7 or a standalone section

### Finding 6: PlaintiffLens Already Defined (HIGH confidence)
- `PlaintiffLens` enum in `check_results.py` has all 7 values: SHAREHOLDERS, REGULATORS, CUSTOMERS, COMPETITORS, EMPLOYEES, CREDITORS, GOVERNMENT
- `check_classification.json::plaintiff_lens_defaults` maps every check prefix to default lenses
- The check engine copies `plaintiff_lenses` to each CheckResult via `_apply_classification_metadata()`
- **This means the data for the 7-lens assessment already exists on every CheckResult.** Phase 27 aggregates it.

### Finding 7: Stock Drop Data for DDL (HIGH confidence)
- `stock_drops.py` extracts `StockDropEvent` objects from market data
- Each drop has `magnitude_pct`, `date`, `sector_relative_pct`, `triggering_event`
- Market cap is on `state.company.market_cap`
- DDL = market_cap * drop_magnitude -- straightforward computation from existing data
- Multiple drops can compound DDL -- the model should sum or take the maximum

### Finding 8: Existing Plaintiff Firm Configuration (HIGH confidence)
- `lead_counsel_tiers.json` already has 5 tier-1 and 9 tier-2 firms
- Match strategy is "substring" -- already handles name variations
- **Gap:** No severity multiplier per tier. Phase 27 needs to add multipliers:
  - Tier 1 (elite): 2.0x severity multiplier (Bernstein Litowitz, Robbins Geller, etc.)
  - Tier 2 (major): 1.5x
  - Tier 3 (regional/default): 1.0x
- This is a config enhancement, not a code change to the matching logic

## Open Questions

1. **Pipeline audit scope -- full run or sampled?**
   - What we know: 374 AUTO checks. Running the full pipeline on 5 tickers (AAPL, TSLA, XOM, SMCI, JPM) will identify which checks are empirically unwired.
   - What's unclear: Does the pipeline currently complete end-to-end for any ticker? If not, the audit may be blocked by upstream errors.
   - Recommendation: Run pipeline first on one ticker (AAPL) to establish baseline, then audit results programmatically. If pipeline doesn't complete, fix blockers first.

2. **NOT_APPLICABLE classification source**
   - What we know: Checks like `FIN.SECTOR.biotech` are only applicable to biotech companies. The `check_classification.json::deprecated_check_ids` list removed sector-specific stubs, but there may be active checks that are company-type-conditional.
   - What's unclear: How many checks have industry-conditional applicability? Is it driven by SIC code, or by playbook activation?
   - Recommendation: Start with a simple heuristic: if `active_playbook_id` is set and the check's section/prefix doesn't match the playbook's industry, mark NOT_APPLICABLE. Refine in Phase 28 iteration.

3. **Defense theory data availability**
   - What we know: User wants defense theories ONLY when company-specific measures exist. Forum selection clauses are in proxy/10-K. PSLRA safe harbor usage is in earnings call disclaimers.
   - What's unclear: Do we currently extract forum selection clause data? PSLRA safe harbor language?
   - Recommendation: Check the litigation extraction pipeline (`defense_assessment.py`). If these aren't extracted, add extraction before bear case construction.

4. **Tower positioning "risk by layer" vs "attachment points"**
   - What we know: User explicitly wants risk characterized by layer, not specific attachment point recommendations. Current `recommend_tower()` does position-based recommendation.
   - What's unclear: What does "primary layer carries X% of expected loss exposure" look like technically? Is it the ILF curve split across layers?
   - Recommendation: Use the existing ILF (Increased Limit Factor) from `actuarial_layer_pricing.py` to compute expected loss share per layer. This is already computed -- just surface it as a percentage.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: All Python source files in `src/do_uw/` (direct code reading)
- `check_classification.json`: Phase 26 classification metadata
- `brain/checks.json`: Check inventory (381 checks, version 8.0.0)
- Phase 24 Unified Framework: `24-UNIFIED-FRAMEWORK.md` (5-layer architecture, plaintiff lens definitions)
- Phase 24 Non-SCA Claims Research: `research/NON_SCA_CLAIMS_RESEARCH.md`
- Phase 24 Recent Claims Analysis: `research/RECENT_CLAIMS_ANALYSIS.md`

### Secondary (MEDIUM confidence)
- Phase 24 Game Theory Research: `research/GAME_THEORY_PRICING.md` (settlement prediction methodology)
- Phase 26 decisions: State.md accumulated decisions (engine output patterns)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, building on existing infrastructure
- Architecture: HIGH -- clear patterns from Phase 26, well-defined integration points
- Pitfalls: HIGH -- identified from 3020 existing tests and 129 test files
- Settlement model internals: MEDIUM -- methodology is sound but calibration data is limited (public data only)
- Pipeline audit scope: MEDIUM -- uncertain how many checks are actually unwired until audit runs

**Research date:** 2026-02-12
**Valid until:** 2026-03-12 (stable internal architecture, no external dependency changes expected)
