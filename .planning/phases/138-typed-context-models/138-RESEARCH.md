# Phase 138: Typed Context Models - Research

**Researched:** 2026-03-27
**Domain:** Pydantic typed output contracts for context builder functions
**Confidence:** HIGH (direct codebase analysis of all 5 target builders, templates, assembly pipeline, and Phase 137 canonical metrics)

## Summary

Phase 138 wraps the 5 highest-leakage context builders with Pydantic models to catch type errors at the builder boundary rather than at render time (or by the underwriter). The 5 targets -- `extract_exec_summary`, `extract_financials`, `extract_market`, `extract_governance`, `extract_litigation` -- collectively return ~340 dict keys across deeply nested structures (sub-dicts, lists-of-dicts, optional computed fields).

The key architectural insight is that templates access builder output via Jinja2 dict operations (`gov.get('key', default)`, `litigation.cases`, `financials.revenue`). Since `model_dump()` produces a regular dict, typed models are a drop-in replacement with zero template changes. The validation wrapper pattern (try typed, fall back to untyped) makes this fully non-breaking.

**Primary recommendation:** Define one Pydantic model per builder with nested sub-models for structured sub-dicts (snapshot, dashboard, board, etc.). Use `Optional[T] = None` for every field. Validate via `model_validate()` on the existing builder output. Wrap in try/except at the call site in `md_renderer.py::build_template_context()`. Byte-identical output guaranteed by `model_dump()` producing the same dict keys.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TYPE-01 | Pydantic BaseModel defined for each section context (exec brief, financial, market, governance, litigation) | Builder return key audit complete; ~340 total keys across 5 builders identified |
| TYPE-02 | All fields use `Optional[T] = None` defaults -- no required fields for data that can be missing | All 5 builders return `{}` on missing data; every key is conditionally set |
| TYPE-03 | Validation wrapper: try typed path, fall back to untyped dict on failure | Call site identified: `md_renderer.py` lines 182-191; wrapper pattern documented |
| TYPE-04 | `model_dump()` produces identical dict keys templates expect -- zero template changes | Templates use `gov.get()`, `litigation.cases`, `financials.revenue` -- all dict-compatible |
| TYPE-05 | Priority migration: 5 highest-leakage builders first | All 5 builders analyzed with key counts and nesting structure |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.x (already in project) | Typed model definitions, validation | Project standard (CLAUDE.md: "Pydantic v2 for all data models") |

### No New Dependencies

All work uses existing Pydantic v2 already in the project. No new packages required.

## Architecture Patterns

### Recommended Project Structure

```
src/do_uw/stages/render/
  context_models/           # NEW package
    __init__.py
    exec_summary.py         # ExecSummaryContext model
    financial.py            # FinancialContext model
    market.py               # MarketContext model
    governance.py           # GovernanceContext model
    litigation.py           # LitigationContext model
```

### Builder Return Key Audit (Critical Research Finding)

Each builder was analyzed for the complete set of keys it returns. This is the foundation for model field definitions.

#### 1. `extract_exec_summary` (~12 top-level keys)

```python
{
    "tier_label": str | None,
    "tier_action": str | None,
    "quality_score": str | None,        # e.g., "72.3"
    "composite_score": str | None,
    "thesis": str | None,
    "key_findings": list[str],          # just narratives
    "key_findings_detail": list[dict],  # {narrative, section, impact, theory, sca_theory}
    "positive_indicators": list[str],
    "positive_detail": list[dict],      # {narrative, section, impact, theory, sca_defense}
    "snapshot": dict | None,            # {company_name, ticker, exchange, industry, market_cap, revenue, employees}
    "claim_probability": dict | None,   # {band, range, industry_base}
    "tower_recommendation": dict | None, # {position, min_attachment, side_a}
    "inherent_risk": dict | None,       # {sector, market_cap_tier, sector_base_rate, adjusted_rate}
}
```

**Nesting:** 4 sub-dicts (snapshot, claim_probability, tower_recommendation, inherent_risk) + 2 list-of-dicts (key_findings_detail, positive_detail). Sub-models recommended for each.

#### 2. `extract_financials` (~65+ top-level keys)

Largest builder. Keys added by `_build_income_context`, `_build_balance_sheet`, `_build_cash_flow`, `build_*_computed` helpers, `_extract_*_signals` evaluative helpers, and sub-context builders (quarterly, forensics, peer percentiles).

Key groups:
- **Income statement:** `revenue`, `net_income`, `prior_revenue`, `prior_net_income`, `revenue_yoy`, `net_income_yoy`, `gross_profit`, `gross_margin`, `operating_income`, `operating_margin`, `diluted_eps`, etc.
- **Balance sheet:** `total_assets`, `total_equity`, `cash`, `total_liabilities`, etc.
- **Cash flow:** `operating_cf`, `capex`, `buybacks`, `dividends`
- **Computed:** goodwill_equity, capital_allocation, debt_service, refinancing, bankruptcy composite
- **Evaluative (from signals):** `z_score`, `z_zone`, `o_score`, `o_zone`, `beneish_score`, `beneish_zone`, `piotroski_score`, `piotroski_zone`, debt/leverage/earnings/tax/liquidity context strings
- **Audit:** `auditor_name`, `is_big4`, `auditor_tenure`, `material_weaknesses`, `going_concern`
- **Sub-contexts:** `peers` (list), `quarterly_updates`, `yfinance_quarterly`, `quarterly_trends`, `forensics` (dict), `peer_percentiles`, `debt_structure` (dict), `liquidity_detail` (dict), `health_narrative`
- **Sparklines:** `revenue_sparkline`, `net_income_sparkline`, `total_assets_sparkline`

**Nesting:** Deep. `debt_structure` has `instruments` (list-of-dicts) and `maturity_schedule`. `liquidity_detail` has `metrics` (list-of-dicts). `forensics` is itself a complex dict. Recommend 3-4 sub-models.

#### 3. `extract_market` (~50+ top-level keys)

Key groups:
- **Price/valuation:** `current_price`, `high_52w`, `low_52w`, `pct_off_high`, `valuation` (sub-dict), `growth` (sub-dict), `profitability` (sub-dict)
- **Short interest:** `short_pct`, `days_to_cover`
- **Insider:** `insider_summary`, `insider_data` (complex dict)
- **Evaluative (from signals):** volatility, short interest, insider, returns, guidance context strings
- **Stock events:** `worst_drop_pct`, `worst_drop_date`, `worst_drop_trigger`, `drop_events` (list), `drop_events_overflow`
- **DDL/MDL:** `ddl_exposure`, `mdl_exposure`, `ddl_settlement_estimate`
- **Capital markets:** `capital_markets` (sub-dict with offerings, shelf_registrations)
- **Charts:** `main_charts` (list), `audit_charts` (list)
- **Earnings:** `earnings_guidance` (sub-dict), `analyst_consensus`, `eight_k_events` (complex dict)
- **Additional:** `capital_returns` (dict), `stock_sparkline`, `next_earnings`
- **Phase 133 additions:** EPS revision trends, analyst targets, earnings trust, volume anomalies, correlation metrics

**Nesting:** Very deep. `eight_k_events` has `filings` (list-of-dicts) and `item_frequency`. `capital_markets` has `offerings` and `shelf_registrations` (lists-of-dicts). Recommend 5+ sub-models.

#### 4. `extract_governance` (~75+ top-level keys)

Key groups:
- **Board:** `board_size`, `independence_ratio`, `ceo_duality`, `avg_tenure`, `classified_board`, `dual_class`, `overboarded_count` + `board` (nested summary dict)
- **Compensation:** `ceo_comp`, `say_on_pay`, `ceo_pay_ratio`, `has_clawback`, `clawback_scope` + `compensation` (nested dict) + `compensation_analysis` (complex nested dict with ECD sub-dict)
- **Ownership:** `institutional_pct`, `insider_pct`, `top_holders` (list-of-dicts), `known_activists`, `filings_13d_24mo`, `conversions_13g_to_13d`, `proxy_contests_3yr`
- **Leadership:** `executives` (list-of-dicts), `departures_18mo` (list-of-dicts), `leadership_red_flags`, `stability_score`
- **Sentiment:** `has_sentiment_data`, `management_tone`, `hedging_language`, `qa_evasion`
- **Structural:** `anti_takeover`, `bylaws_provisions` (list-of-dicts)
- **Board forensics:** `board_members` (list-of-dicts with ~15 fields each), column visibility flags
- **Narrative coherence:** `narrative_coherence` (dict), `coherence_flags`
- **Visual:** `score_breakdown` (list-of-dicts), `tenure_distribution` (list-of-dicts), `skills_matrix`, `committee_detail`
- **Evaluative (from signals):** board quality flags, compensation flags, structural governance
- **Intelligence:** officer backgrounds, shareholder rights, per-insider activity

**Nesting:** Most deeply nested of all 5. The `compensation_analysis` dict contains ECD data which itself has badges and TSR comparisons. Recommend 6+ sub-models.

#### 5. `extract_litigation` (~35+ top-level keys)

Key groups:
- **Summary:** `active_summary`, `historical_summary`, `active_matters` (alias)
- **Cases:** `cases` (list-of-dicts), `historical_cases` (list-of-dicts)
- **SOL:** `sol_windows` (list-of-dicts), `open_sol_count`, `sol_analysis` (dict)
- **SEC:** `sec_enforcement_stage`, `comment_letters`, `sec_enforcement` (nested dict), `comment_letter_topics`
- **Derivative/regulatory:** `derivative_suits`, `derivative_count`, `regulatory_proceedings` (list-of-dicts)
- **Defense:** `defense` (dict with ~8 keys), `defense_strength`
- **Reserve:** `litigation_reserve`
- **Timeline:** `timeline_events` (list-of-dicts)
- **Contingent/other:** `contingent_liabilities`, `workforce_product_env`, `whistleblower_indicators`
- **Deal:** `deal_litigation` (list-of-dicts), `ma_activity_notes`
- **Settlements:** `settlements` (list-of-dicts)
- **Dashboard:** `dashboard` (dict with ~11 keys)
- **Industry:** `industry_patterns` (list[str])
- **Evaluative:** from litigation_evaluative signals

**Nesting:** Moderate. `dashboard` and `sec_enforcement` are key sub-dicts. Recommend 3-4 sub-models.

### Pattern 1: Validation Wrapper (Non-Breaking Migration)

**What:** Wrap each builder call in `md_renderer.py::build_template_context()` with typed validation that falls back to the existing untyped dict on any error.

**Call site (md_renderer.py lines 182-191):**
```python
# CURRENT:
if state.executive_summary is not None:
    context["executive_summary"] = extract_exec_summary(state, signal_results=signal_results)

# AFTER:
if state.executive_summary is not None:
    raw = extract_exec_summary(state, signal_results=signal_results)
    context["executive_summary"] = _validate_context(
        ExecSummaryContext, raw, "executive_summary"
    )

# Wrapper function:
def _validate_context(
    model_cls: type[BaseModel],
    raw: dict[str, Any],
    section_name: str,
) -> dict[str, Any]:
    """Validate raw dict against typed model. Fall back on error."""
    try:
        typed = model_cls.model_validate(raw)
        return typed.model_dump()
    except ValidationError as e:
        logger.warning(
            "Typed validation failed for %s (%d errors), using untyped fallback",
            section_name, e.error_count(),
        )
        return raw
```

**Why this works:** `model_dump()` produces a regular dict with identical keys. Templates see no difference. If validation fails, the original dict passes through unchanged.

### Pattern 2: Model Design Rules

**All fields Optional with None default:**
```python
class ExecSummaryContext(BaseModel):
    model_config = ConfigDict(extra="allow")  # NOT "forbid" during migration

    tier_label: str | None = None
    tier_action: str | None = None
    quality_score: str | None = None
    # ...
```

**Why `extra="allow"` not `extra="forbid"`:** During migration, sub-helpers like evaluative extractors add keys that may not be in the model yet. Using `"forbid"` would reject valid data. Use `"allow"` initially, tighten to `"forbid"` after full key coverage is verified.

**Sub-models for nested dicts:**
```python
class SnapshotContext(BaseModel):
    company_name: str = "N/A"
    ticker: str = ""
    exchange: str = "N/A"
    industry: str = "N/A"
    market_cap: str = "N/A"
    revenue: str = "N/A"
    employees: str = "N/A"

class ExecSummaryContext(BaseModel):
    snapshot: SnapshotContext | None = None
    # ...
```

### Pattern 3: Template Access Compatibility

Templates access context values via:
1. **Dot notation on dicts:** `financials.revenue` -- Jinja2 treats this as `financials["revenue"]` for dicts
2. **`.get()` calls:** `gov.get('institutional_pct', 'N/A')` -- works only on dicts, NOT on Pydantic model objects
3. **Set-and-use:** `{% set gov = governance or {} %}` -- creates local dict alias

Since we always call `model_dump()` before passing to templates, the dict interface is preserved. No aliases needed. No template changes needed.

### Pattern 4: Where to Insert -- Single Validation Point

The 5 builder calls all happen in `md_renderer.py::build_template_context()` (lines 182-191). The assembly registry's `build_html_context()` (lines 78-132) calls `build_template_context()` first, then runs registered builders. Phase 138 modifies only `build_template_context()`, not the assembly registry.

### Anti-Patterns to Avoid

- **Big-bang:** Don't type all ~90 builders at once. Only the 5 specified in TYPE-05.
- **`extra="forbid"` too early:** Evaluative helpers add keys via `result.update()`. Many keys come from sub-modules not yet audited. Start with `extra="allow"`.
- **Changing dict keys:** Never rename a key. Templates use exact key names. Use `Field(alias=...)` only if model field names must differ (unlikely given keys are already snake_case).
- **Passing model objects to templates:** Always `model_dump()`. Templates use `.get()` which fails on Pydantic models.
- **Required fields:** Every field must have a default. All 5 builders return `{}` when data is missing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dict-to-model conversion | Custom parsing per field | `model_validate(raw_dict)` | Pydantic v2 handles coercion, nested models, extra keys |
| Model-to-dict for templates | Custom serializer | `model_dump()` | Produces exact dict with same key names |
| Fallback on validation error | Per-field try/except | Single wrapper with ValidationError catch | Cleaner, logs all errors at once |

## Common Pitfalls

### Pitfall 1: Pydantic Rigidity on Real Data

**What goes wrong:** Model defines `revenue: str` but builder sometimes produces `revenue: None` when XBRL data is missing. ValidationError crashes for one company but not another.
**Why:** Different tickers have different data availability. AAPL has everything; a recent-IPO micro-cap may have almost nothing.
**How to avoid:** Every single field is `Optional[T] = None` or has a concrete default (`str = "N/A"`, `list = Field(default_factory=list)`). Never `float` without `| None`.
**Warning signs:** ValidationError count > 0 on any cached state.json.

### Pitfall 2: Evaluative Helpers Add Unknown Keys

**What goes wrong:** `result.update(_extract_distress_signals(...))` adds keys like `z_score`, `z_zone`, `debt_summary`, etc. If the model uses `extra="forbid"`, these keys cause validation failure.
**Why:** Each evaluative helper returns its own dict of keys. The full key set is spread across 5+ helper files per builder.
**How to avoid:** Use `extra="allow"` during initial migration. After all keys are documented and in the model, tighten to `extra="forbid"`. Create a ratchet test that tracks which builders have full key coverage.

### Pitfall 3: Nested Dict Types Vary

**What goes wrong:** `governance["compensation_analysis"]` is a dict with an `ecd` sub-dict that has an `ecd_badges` list-of-dicts. Defining this as `dict[str, Any]` preserves the status quo but provides no type safety at the nested level. Defining specific sub-models is correct but requires auditing every nested structure.
**Why:** The 5 builders collectively produce ~25 nested sub-dicts with varying schemas.
**How to avoid:** Start with `dict[str, Any]` for complex nested values. Replace with sub-models incrementally in later phases. Document which fields are "typed pass-through" vs "fully typed".

### Pitfall 4: Byte-Identical Output Assumption

**What goes wrong:** `model_dump()` may serialize differently than the raw dict in edge cases -- `None` vs key-absent, `0` vs `"0"`, nested model dicts vs nested raw dicts.
**Why:** The raw builder dict may omit keys entirely when data is missing. `model_dump()` includes all fields (with None defaults). Templates use `financials.revenue or "N/A"` which treats None the same as missing in Jinja2, but `{% if financials.debt_structure %}` would be True for an empty dict `{}` but False for None.
**How to avoid:** For sub-dicts that are conditionally set (only added when data exists), use `None` default, not `dict = Field(default_factory=dict)`. Then `model_dump(exclude_none=True)` can omit them. Or test with `model_dump()` and verify template behavior.

### Pitfall 5: safe_float Call Sites in Builders

**What goes wrong:** 26 `safe_float()` calls across the 5 builders (0 in exec_summary, 6 in financials, 7 in market, 11 in governance, 2 in litigation). These are NOT replaced by Pydantic typing -- they handle LLM/API garbage strings like "N/A", "13.2%", concatenated junk. The typed model operates AFTER the builder runs.
**Why:** Pydantic validators could replace `safe_float` but that changes builder logic. Phase 138 scope is wrapping builders, not rewriting them.
**How to avoid:** Don't touch `safe_float()` calls. The typed model validates the ALREADY-FORMATTED output dict, not the raw state data.

## Code Examples

### Minimal Exec Summary Model

```python
# context_models/exec_summary.py
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field


class FindingDetail(BaseModel):
    narrative: str = ""
    section: str = ""
    impact: str = ""
    theory: str | None = None
    sca_theory: str | None = None
    sca_defense: str | None = None


class SnapshotContext(BaseModel):
    company_name: str = "N/A"
    ticker: str = ""
    exchange: str = "N/A"
    industry: str = "N/A"
    market_cap: str = "N/A"
    revenue: str = "N/A"
    employees: str = "N/A"


class ClaimProbability(BaseModel):
    band: str = ""
    range: str = ""
    industry_base: str = ""


class TowerRecommendation(BaseModel):
    position: str = ""
    min_attachment: str = "N/A"
    side_a: str = "N/A"


class InherentRisk(BaseModel):
    sector: str = "N/A"
    market_cap_tier: str = "N/A"
    sector_base_rate: str = "N/A"
    adjusted_rate: str = "N/A"


class ExecSummaryContext(BaseModel):
    """Typed context for executive summary section."""
    model_config = ConfigDict(extra="allow")

    tier_label: str | None = None
    tier_action: str | None = None
    quality_score: str | None = None
    composite_score: str | None = None
    thesis: str | None = None
    key_findings: list[str] = Field(default_factory=list)
    key_findings_detail: list[FindingDetail] = Field(default_factory=list)
    positive_indicators: list[str] = Field(default_factory=list)
    positive_detail: list[FindingDetail] = Field(default_factory=list)
    snapshot: SnapshotContext | None = None
    claim_probability: ClaimProbability | None = None
    tower_recommendation: TowerRecommendation | None = None
    inherent_risk: InherentRisk | None = None
```

### Validation Wrapper Function

```python
# In md_renderer.py
from pydantic import ValidationError

def _validate_context(
    model_cls: type[BaseModel],
    raw: dict[str, Any],
    section_name: str,
) -> dict[str, Any]:
    """Validate raw context dict against typed model.

    Returns model_dump() on success, raw dict on failure.
    Never breaks the pipeline.
    """
    if not raw:
        return raw
    try:
        typed = model_cls.model_validate(raw)
        return typed.model_dump()
    except ValidationError as e:
        logger.warning(
            "Typed validation failed for %s (%d errors), using untyped fallback",
            section_name,
            e.error_count(),
        )
        return raw
```

### Integration Test Pattern

```python
# tests/stages/render/test_context_models.py
import json
import pytest
from do_uw.models.state import AnalysisState
from do_uw.stages.render.context_builders.company_exec_summary import extract_exec_summary
from do_uw.stages.render.context_models.exec_summary import ExecSummaryContext

STATE_FILES = [
    "output/AAPL/state.json",
    "output/RPM - RPM INTERNATIONAL/2026-03-18/state.json",
    "output/ULS - UL Solutions/2026-03-25/state.json",
]

@pytest.mark.parametrize("state_path", STATE_FILES)
def test_exec_summary_model_validates_real_state(state_path):
    """Typed model must accept real pipeline output without error."""
    with open(state_path) as f:
        state = AnalysisState.model_validate_json(f.read())
    raw = extract_exec_summary(state)
    typed = ExecSummaryContext.model_validate(raw)
    dumped = typed.model_dump()
    # Every key in raw must be in dumped
    for key in raw:
        assert key in dumped, f"Key '{key}' lost in model_dump()"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `dict[str, Any]` returns from builders | Pydantic-validated typed models with fallback | Phase 138 | Type errors caught at builder boundary, not render time |
| Independent metric computation per builder | CanonicalMetrics registry (Phase 137) | Phase 137 | Cross-section consistency for shared metrics |
| No validation of builder output | `model_validate()` on builder return | Phase 138 | Structured error logging, field coverage tracking |

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/stages/render/test_context_models.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TYPE-01 | Pydantic model defined per section | unit | `uv run pytest tests/stages/render/test_context_models.py -x -k "model_fields"` | Wave 0 |
| TYPE-02 | All fields Optional with None defaults | unit | `uv run pytest tests/stages/render/test_context_models.py -x -k "empty_dict"` | Wave 0 |
| TYPE-03 | Fallback wrapper catches errors | unit | `uv run pytest tests/stages/render/test_context_models.py -x -k "fallback"` | Wave 0 |
| TYPE-04 | model_dump produces template-compatible keys | integration | `uv run pytest tests/stages/render/test_context_models.py -x -k "real_state"` | Wave 0 |
| TYPE-05 | All 5 builders migrated | integration | `uv run pytest tests/stages/render/test_context_models.py -x -k "all_builders"` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/stages/render/test_context_models.py -x`
- **Per wave merge:** `uv run pytest tests/ -x`
- **Phase gate:** Full suite green before verify

### Wave 0 Gaps
- [ ] `tests/stages/render/test_context_models.py` -- all TYPE-01 through TYPE-05 tests
- [ ] `src/do_uw/stages/render/context_models/__init__.py` -- new package
- [ ] `src/do_uw/stages/render/context_models/exec_summary.py` -- model definition
- [ ] `src/do_uw/stages/render/context_models/financial.py`
- [ ] `src/do_uw/stages/render/context_models/market.py`
- [ ] `src/do_uw/stages/render/context_models/governance.py`
- [ ] `src/do_uw/stages/render/context_models/litigation.py`

## Open Questions

1. **Evaluative helper key coverage**
   - What we know: Each builder calls 3-6 evaluative helpers that add keys via `result.update()`. These keys are not in the main builder file.
   - What's unclear: Exact full key set per builder including all helpers.
   - Recommendation: Start with `extra="allow"` and log extra keys. Use logged extras to incrementally expand models.

2. **`model_dump()` None vs key-absent behavior**
   - What we know: Raw dicts omit keys when data is missing. `model_dump()` includes all fields with None defaults.
   - What's unclear: Whether any template uses `{% if 'key' in dict %}` vs `{% if dict.key %}` -- the former would break.
   - Recommendation: Test with real state.json and compare template output byte-for-byte. Use `model_dump(exclude_none=True)` if needed.

3. **Assembly registry overlay**
   - What we know: `assembly_registry.py` overlays canonical values onto `context["executive_summary"]` and `context["company"]` AFTER `build_template_context()` runs (line 108-117).
   - What's unclear: Whether the typed model should be applied before or after this overlay.
   - Recommendation: Apply typed validation in `build_template_context()` (before overlay). The overlay mutates the dict, which works on `model_dump()` output identically.

## Sources

### Primary (HIGH confidence)
- Direct analysis of `company_exec_summary.py` (314 lines, 12 top-level keys, 4 sub-dicts)
- Direct analysis of `financials.py` (477 lines, ~65 keys, deep nesting)
- Direct analysis of `market.py` (490 lines, ~50 keys, 5+ sub-dicts)
- Direct analysis of `governance.py` (523 lines, ~75 keys, 6+ sub-dicts)
- Direct analysis of `litigation.py` (305 lines, ~35 keys, 3 sub-dicts)
- Direct analysis of `assembly_registry.py` (165 lines, canonical overlay logic)
- Direct analysis of `md_renderer.py` lines 170-209 (builder call site)
- Direct analysis of `canonical_metrics.py` (Phase 137 implementation)
- Template access patterns verified across `templates/html/sections/governance/*.html.j2` and `templates/pdf/worksheet.html.j2`

### Secondary (MEDIUM confidence)
- `.planning/research/ARCHITECTURE.md` -- v12.0 typed context model design
- `.planning/research/PITFALLS.md` -- migration pitfall analysis

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Pydantic v2 already in project, no new deps
- Architecture: HIGH -- direct code analysis of all 5 builders and call sites
- Pitfalls: HIGH -- pitfalls doc covers all known risks, verified against codebase
- Key counts: MEDIUM -- approximate (~340 total), evaluative helper keys not fully enumerated

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (stable; codebase patterns unlikely to change significantly)
