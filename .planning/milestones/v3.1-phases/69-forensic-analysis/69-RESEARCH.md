# Phase 69: Forensic Financial Analysis - Research

**Researched:** 2026-03-06
**Domain:** Forensic financial analysis modules -- balance sheet, capital allocation, debt/tax, revenue quality, Beneish decomposition, M&A forensics, earnings quality dashboard
**Confidence:** HIGH

## Summary

Phase 69 adds four new forensic analysis modules plus Beneish component decomposition, multi-period trajectory analysis, M&A forensics, and an earnings quality dashboard. All consume XBRL-sourced `FinancialStatements` data from the EXTRACT stage -- zero LLM dependency. The existing codebase already has strong patterns to follow: `financial_models.py` (distress models) and `earnings_quality.py` both demonstrate the exact `_extract_input()` / `_find_line_item()` / `ExtractionReport` patterns that new forensic modules should replicate.

The critical insight is that the Beneish M-Score already computes all 8 individual indices (DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI) inside `compute_m_score()` in `financial_formulas.py`, but discards them as local variables -- only the composite score survives into `DistressResult`. FRNSC-05 requires exposing these 8 components individually. This means modifying `compute_m_score()` to return component values (or adding a parallel function) and extending `DistressResult` with a `components` field.

The forensic modules should store results on `state.analysis.forensic_composites` (which already exists as a `dict[str, Any]`) or on a new dedicated `state.analysis.forensics` namespace. Given that `forensic_composites` is already taken by the FIS/RQS/CFQS composite scores, a new field `state.analysis.xbrl_forensics` is recommended to avoid collision.

**Primary recommendation:** Build four forensic analysis modules following the `earnings_quality.py` pattern (consume `FinancialStatements`, return Pydantic model + `ExtractionReport`). Extend `compute_m_score` to expose 8 components. Add multi-period trajectory by running forensic functions across available periods. Wire results into the ANALYZE stage orchestrator (`__init__.py`) via a new `_run_xbrl_forensics()` runner in the analytical engines loop.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FRNSC-01 | Balance sheet forensics: goodwill impairment risk, intangible concentration, off-balance-sheet, cash conversion cycle, working capital manipulation | All required XBRL concepts exist in current 50-concept config OR are being added in Phase 67 (goodwill, intangible_assets, operating_lease_liabilities, current_assets, current_liabilities, accounts_receivable, inventory, accounts_payable). `_extract_input()` pattern from financial_models.py provides the extraction approach. |
| FRNSC-02 | Capital allocation forensics: ROIC trend, acquisition effectiveness, buyback timing, dividend sustainability | Requires concepts from Phase 67: `acquisitions_net`, `stock_based_compensation`, `share_repurchases`, `dividends_paid`, `free_cash_flow` (derived). Market cap from `state.extracted.market.stock_data`. ROIC formula = EBIT*(1-ETR) / (equity+debt-cash). |
| FRNSC-03 | Debt/tax forensics: interest coverage trajectory, debt maturity, ETR anomalies, deferred tax liability, pension underfunding | Requires Phase 67 new concepts: `deferred_tax_liability`, `pension_liability`, `interest_paid`. Current concepts cover `interest_expense`, `long_term_debt`, `short_term_debt`, `income_tax_expense`, `pretax_income`. |
| FRNSC-04 | Revenue quality forensics: deferred revenue vs revenue growth, channel stuffing indicator, margin compression, OCF/revenue | All core concepts already exist: `deferred_revenue`, `revenue`, `accounts_receivable`, `gross_profit`, `operating_cash_flow`. Some overlap with existing `earnings_quality.py` (DSO, accruals) -- extend rather than duplicate. |
| FRNSC-05 | Beneish M-Score component decomposition: expose all 8 indices | `compute_m_score()` in `financial_formulas.py` already computes DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI but discards them. Need to return them in `DistressResult` via a new `components: dict[str, float]` field or a parallel decomposition function. |
| FRNSC-06 | All modules return Pydantic models + ExtractionReport. Composite confidence = min(input confidences) | `ExtractionReport` pattern in `validation.py` is well-established. `create_report()` accepts expected/found/source_filing. Confidence from `SourcedValue` objects flows through. |
| FRNSC-07 | Multi-period forensic trajectory: Beneish/Sloan/accruals across periods | `_build_trajectory()` in `financial_models.py` already implements this pattern for Altman Z across periods. Same pattern: iterate `statements.balance_sheet.periods`, collect inputs per period, compute score. For quarterly data (Phase 68), iterate `quarterly_xbrl.quarters`. |
| FRNSC-08 | M&A forensics from XBRL acquisition data | Phase 67 adds `acquisitions_net` concept (PaymentsToAcquireBusinessesNetOfCashAcquired). Serial acquirer = acquisitions in 3+ of last 5 years. Goodwill accumulation = goodwill growth rate vs revenue growth rate. |
| FRNSC-09 | Earnings quality dashboard: Sloan Accruals, cash flow manipulation, SBC/revenue, non-GAAP gap | Sloan Accruals already partially in `earnings_quality.py` (accruals_ratio). SBC/revenue requires Phase 67 `stock_based_compensation` concept. Non-GAAP gap needs EPS basic vs non-GAAP EPS -- latter not in XBRL (non-standard), so this metric may need to be flagged as limited. |
</phase_requirements>

## Standard Stack

### Core (Already Installed -- No Changes)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | Project standard |
| Pydantic | 2.10+ | Forensic result models | Already used for all models |
| dataclasses | stdlib | ExtractionReport | Already used in validation.py |

### Supporting (Already in Codebase)
| Library | Purpose | When to Use |
|---------|---------|-------------|
| `financial_models.py` | `_extract_input()`, `_find_line_item()`, `_collect_all_inputs()` patterns | Reuse extraction helpers in every forensic module |
| `earnings_quality.py` | `_get_val()`, quality scoring pattern | Extend for revenue quality overlap |
| `financial_formulas.py` | `safe_ratio()`, `compute_m_score()` | Reuse arithmetic helpers; extend M-Score for decomposition |
| `validation.py` | `ExtractionReport`, `create_report()`, `merge_reports()` | Every forensic module returns an ExtractionReport |
| `models/forensic.py` | `ForensicZone`, `SubScore` | Reuse zone classification pattern for new forensic results |
| `models/common.py` | `SourcedValue`, `Confidence` | Wrap all output values |

### No New Dependencies
Zero new packages. Pure computation modules consuming existing XBRL-extracted data.

## Architecture Patterns

### Recommended File Structure
```
src/do_uw/
  stages/analyze/
    forensic_balance_sheet.py   # NEW ~250 lines: FRNSC-01
    forensic_capital_alloc.py   # NEW ~200 lines: FRNSC-02
    forensic_debt_tax.py        # NEW ~200 lines: FRNSC-03
    forensic_revenue.py         # NEW ~150 lines: FRNSC-04
    forensic_beneish.py         # NEW ~200 lines: FRNSC-05, FRNSC-07 (Beneish decomposition + trajectory)
    forensic_ma.py              # NEW ~150 lines: FRNSC-08
    forensic_earnings_dashboard.py  # NEW ~200 lines: FRNSC-09
    financial_formulas.py       # MODIFY: expose M-Score components
    __init__.py                 # MODIFY: add _run_xbrl_forensics() to analytical engines
  models/
    xbrl_forensics.py           # NEW ~250 lines: Pydantic models for all forensic results
    financials.py               # MODIFY: add components to DistressResult
  models/
    state.py                    # MODIFY: add xbrl_forensics field to AnalysisResults
```

### Pattern 1: Forensic Module Interface (NEW -- establish for all 4 modules)
**What:** Each forensic module is a pure function consuming `FinancialStatements`, returning a Pydantic result + ExtractionReport
**When to use:** Every forensic computation module
**Why:** Matches existing `compute_distress_indicators()` and `compute_earnings_quality()` patterns
```python
# Source: existing pattern from financial_models.py + earnings_quality.py
def compute_balance_sheet_forensics(
    statements: FinancialStatements,
    quarterly: QuarterlyStatements | None = None,  # Optional Phase 68 enhancement
) -> tuple[BalanceSheetForensics, ExtractionReport]:
    """Compute balance sheet forensic indicators.

    All inputs from XBRL-extracted FinancialStatements.
    Returns Pydantic model + ExtractionReport.
    """
    expected = [
        "goodwill_to_assets", "intangible_concentration",
        "off_balance_sheet", "cash_conversion_cycle",
        "working_capital_volatility",
    ]
    found: list[str] = []
    # ... compute each metric ...
    report = create_report(
        extractor_name="forensic_balance_sheet",
        expected=expected,
        found=found,
        source_filing="Derived from XBRL financial statements",
    )
    return result, report
```

### Pattern 2: Input Extraction via _extract_input() (EXISTING -- reuse)
**What:** Extract financial values by concept name from `FinancialStatements`
**When to use:** Every forensic metric computation
**Why:** Proven pattern, handles all 3 statement types, latest/prior period routing
```python
# Source: financial_models.py lines 82-104
# Import and reuse -- do NOT duplicate this function
from do_uw.stages.analyze.financial_models import _extract_input
# Or better: extract into a shared module to avoid private import
```

### Pattern 3: Composite Confidence = min(inputs) (NEW -- per FRNSC-06)
**What:** When a forensic metric uses multiple input values, its confidence = min of all input confidences
**When to use:** Every forensic result
**Why:** Requirement FRNSC-06 -- composite confidence cannot exceed weakest input
```python
def _composite_confidence(
    statements: FinancialStatements,
    concepts: list[str],
) -> Confidence:
    """Compute composite confidence as min of all input confidences."""
    confidences: list[Confidence] = []
    for concept in concepts:
        for stmt in [statements.income_statement, statements.balance_sheet, statements.cash_flow]:
            if stmt is None:
                continue
            for item in stmt.line_items:
                if item.xbrl_concept == concept:
                    for sv in item.values.values():
                        if sv is not None:
                            confidences.append(sv.confidence)
    if not confidences:
        return Confidence.LOW
    # Confidence enum: HIGH > MEDIUM > LOW -- min gives weakest
    priority = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
    return min(confidences, key=lambda c: priority[c])
```

### Pattern 4: Multi-Period Trajectory (EXISTING -- follow `_build_trajectory()`)
**What:** Run a forensic computation across all available periods
**When to use:** FRNSC-07 (Beneish/Sloan/accruals trajectory)
**Why:** `_build_trajectory()` in financial_models.py already does this for Altman Z
```python
# Source: financial_models.py lines 333-370
def _build_forensic_trajectory(
    statements: FinancialStatements,
    compute_fn: Callable,
) -> list[dict[str, float | str]]:
    """Build forensic score trajectory across available periods."""
    periods = []
    if statements.balance_sheet:
        periods = list(statements.balance_sheet.periods)
    trajectory = []
    for period in periods:
        inputs = _collect_period_inputs(statements, period)
        result = compute_fn(inputs)
        if result is not None:
            trajectory.append({"period": period, **result})
    return trajectory
```

### Pattern 5: Wiring into ANALYZE Orchestrator (EXISTING pattern)
**What:** Add new forensic runner to `_run_analytical_engines()` in `__init__.py`
**When to use:** Once all forensic modules are built
**Why:** Matches existing pattern for temporal, forensic composites, executive, NLP engines
```python
# Source: stages/analyze/__init__.py lines 297-306
for name, runner in [
    ("Temporal analysis", _run_temporal_engine),
    ("Forensic composites", _run_forensic_composites),
    ("Executive forensics", _run_executive_forensics_engine),
    ("NLP signals", _run_nlp_engine),
    ("XBRL forensics", _run_xbrl_forensics),  # NEW
]:
    try:
        runner(state)
    except Exception:
        logger.warning("%s failed; continuing", name, exc_info=True)
```

### Anti-Patterns to Avoid
- **Duplicating `_extract_input()` helpers:** The same `_find_line_item()` / `_get_latest_value()` / `_extract_input()` pattern exists in BOTH `financial_models.py` and `earnings_quality.py` (copy-pasted). Do NOT create a third copy. Either import from `financial_models.py` or extract into a shared `forensic_helpers.py` module.
- **Storing forensic results on `extracted.financials`:** Forensic analysis happens in ANALYZE stage, not EXTRACT. Results go on `state.analysis`, not `state.extracted`. (Note: `earnings_quality` currently stores on `extracted.financials` which is technically wrong -- it's computed in ANALYZE but stored on EXTRACT. Don't repeat this.)
- **Computing ratios inline:** All safe division should use `safe_ratio()` from `financial_formulas.py`.
- **Ignoring None inputs:** Every forensic metric MUST handle None inputs gracefully (return None, not raise). Guard against division by zero.
- **Forensic modules accessing MCP or network:** These are pure computation modules. All data must come from `FinancialStatements` which is XBRL-extracted in EXTRACT stage.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Safe division | Custom div-by-zero guards | `safe_ratio()` from `financial_formulas.py` | Already handles None + zero denominator |
| Extraction reports | Custom logging | `create_report()` from `validation.py` | Computes coverage, confidence, missing fields automatically |
| Line item lookup | Custom statement search | `_find_line_item()` / `_extract_input()` from `financial_models.py` | Already searches all 3 statement types |
| Zone classification | Custom threshold logic | Extend `ForensicZone` pattern from `models/forensic.py` | 5-tier classification already defined |
| Period iteration | Custom period loop | `_build_trajectory()` pattern from `financial_models.py` | Already handles period discovery + per-period collection |
| Merging reports | Custom aggregation | `merge_reports()` from `validation.py` | Combines expected/found/missing across sub-reports |

## Common Pitfalls

### Pitfall 1: Beneish Component Values Lost as Local Variables
**What goes wrong:** `compute_m_score()` computes DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI but only returns composite M-Score. Components are local variables that get garbage collected.
**Why it happens:** Original implementation only needed the composite score.
**How to avoid:** Either modify `compute_m_score()` to populate `DistressResult.trajectory` or `components` field with individual values, or create `decompose_m_score()` that returns them separately. Prefer modifying the existing function to avoid computing twice.
**Warning signs:** If Beneish decomposition requires re-computing M-Score inputs from scratch, the approach is wrong.

### Pitfall 2: Namespace Collision with Existing `forensic_composites`
**What goes wrong:** `state.analysis.forensic_composites` already stores FIS/RQS/CFQS composite scores. New XBRL forensics stored on same field would overwrite existing data.
**Why it happens:** The field name `forensic_composites` is already taken.
**How to avoid:** Use a new field: `state.analysis.xbrl_forensics: dict[str, Any]` for the new XBRL-based forensic results. Keep existing `forensic_composites` for FIS/RQS/CFQS.
**Warning signs:** If test output shows FIS/RQS/CFQS scores missing, namespace collision occurred.

### Pitfall 3: Double-Counting Metrics Already in earnings_quality.py
**What goes wrong:** FRNSC-04 (revenue quality) and FRNSC-09 (earnings dashboard) overlap with existing `earnings_quality.py` metrics (accruals_ratio, ocf_to_ni, DSO).
**Why it happens:** Multiple requirements address similar analytical areas from different angles.
**How to avoid:** New forensic modules should EXTEND existing metrics, not recompute them. Import from `earnings_quality.py` or reference values already stored on `state.extracted.financials.earnings_quality`. Add new metrics (deferred revenue analysis, channel stuffing indicator, margin compression) that don't already exist.
**Warning signs:** Same metric computed in 2+ places with slightly different formulas.

### Pitfall 4: Missing XBRL Concepts for Forensic Inputs
**What goes wrong:** Forensic module tries to extract a concept (e.g., `deferred_tax_liability`) that doesn't exist yet in `xbrl_concepts.json`.
**Why it happens:** Phase 69 depends on Phase 67 adding ~70 new concepts. If Phase 67 is incomplete, some forensic inputs will be None.
**How to avoid:** Every forensic metric must handle None gracefully. Code against the concept names that Phase 67 will add, but return None (not crash) if the concept isn't available. ExtractionReport documents what's missing.
**Warning signs:** ExtractionReport shows <50% coverage on a forensic module.

### Pitfall 5: Quarterly Data Optional But Assumed Present
**What goes wrong:** Forensic modules assume quarterly data exists (Phase 68) and crash on `None.quarters`.
**Why it happens:** Phase 69 depends on Phase 67 (annual), with Phase 68 (quarterly) as optional enhancement.
**How to avoid:** All quarterly-enhanced forensics must check `quarterly is not None` before accessing. Annual-only path must produce valid (if less detailed) results.
**Warning signs:** `AttributeError: 'NoneType' has no attribute 'quarters'`

### Pitfall 6: File Size Explosion
**What goes wrong:** A forensic module exceeds 500 lines because it tries to do too much.
**Why it happens:** Combining computation, model definition, trajectory analysis, and helper functions in one file.
**How to avoid:** Models go in `models/xbrl_forensics.py`. Shared extraction helpers go in a shared module. Each forensic module stays focused on its domain (~200 lines).
**Warning signs:** Any file approaching 400 lines should be reviewed for splitting opportunities.

## Code Examples

### Current Beneish M-Score -- What Needs to Change (FRNSC-05)
```python
# Current: financial_formulas.py compute_m_score() -- components LOST
# Returns: DistressResult(score=m, zone=..., missing_inputs=..., model_variant="beneish_8var")

# NEEDED: Expose 8 individual indices
# Option A: Add components dict to DistressResult
class DistressResult(BaseModel):
    # ... existing fields ...
    components: dict[str, float | None] = Field(
        default_factory=dict,
        description="Individual model components (e.g., Beneish: DSRI, GMI, ...)",
    )

# Option B: Return components from compute_m_score
# Modify compute_m_score() to populate result.components before returning:
result.components = {
    "dsri": dsri, "gmi": gmi, "aqi": aqi, "sgi": sgi,
    "depi": depi, "sgai": sgai, "tata": tata, "lvgi": lvgi,
}
```

### Balance Sheet Forensics (FRNSC-01)
```python
# Source: derived from financial_models.py pattern
def compute_balance_sheet_forensics(
    statements: FinancialStatements,
) -> tuple[BalanceSheetForensics, ExtractionReport]:
    expected = [
        "goodwill_to_assets", "goodwill_to_assets_prior",
        "intangible_concentration", "off_balance_sheet_ratio",
        "cash_conversion_cycle", "working_capital_volatility",
    ]
    found: list[str] = []

    # Goodwill impairment risk: goodwill/TA trend
    gw = _extract_input(statements, "goodwill")
    ta = _extract_input(statements, "total_assets")
    gw_to_ta = safe_ratio(gw, ta)
    if gw_to_ta is not None:
        found.append("goodwill_to_assets")

    gw_p = _extract_input(statements, "goodwill", "prior")
    ta_p = _extract_input(statements, "total_assets", "prior")
    gw_to_ta_prior = safe_ratio(gw_p, ta_p)
    if gw_to_ta_prior is not None:
        found.append("goodwill_to_assets_prior")

    # Intangible concentration: (goodwill + intangibles) / TA
    intang = _extract_input(statements, "intangible_assets")
    intang_conc = safe_ratio((gw or 0) + (intang or 0), ta) if ta else None
    if intang_conc is not None:
        found.append("intangible_concentration")

    # Off-balance-sheet: operating_lease_liabilities / TA
    lease = _extract_input(statements, "operating_lease_liabilities")
    obs_ratio = safe_ratio(lease, ta)
    if obs_ratio is not None:
        found.append("off_balance_sheet_ratio")

    # Cash conversion cycle: inventory_days + DSO - DPO
    inv = _extract_input(statements, "inventory")
    ar = _extract_input(statements, "accounts_receivable")
    ap = _extract_input(statements, "accounts_payable")
    rev = _extract_input(statements, "revenue")
    cogs = _extract_input(statements, "cost_of_revenue")

    inv_days = safe_ratio(inv, cogs) * 365 if safe_ratio(inv, cogs) else None
    dso = safe_ratio(ar, rev) * 365 if safe_ratio(ar, rev) else None
    dpo = safe_ratio(ap, cogs) * 365 if safe_ratio(ap, cogs) else None

    ccc = None
    if inv_days is not None and dso is not None and dpo is not None:
        ccc = round(inv_days + dso - dpo, 1)
        found.append("cash_conversion_cycle")

    # ... assemble result ...
    report = create_report("forensic_balance_sheet", expected, found,
                           "Derived from XBRL financial statements")
    return result, report
```

### Sloan Accruals Ratio with Zones (FRNSC-09)
```python
# Sloan Accruals = (NI - CFO - CFI) / Average Total Assets
# Zones: Safe (-10% to 10%), Warning (10-25% or -25% to -10%), Danger (>25% or <-25%)
def compute_sloan_accruals(
    statements: FinancialStatements,
) -> tuple[float | None, str]:
    """Compute Sloan Accruals Ratio with zone classification.

    Returns (ratio, zone_label).
    """
    ni = _extract_input(statements, "net_income")
    cfo = _extract_input(statements, "operating_cash_flow")
    cfi = _extract_input(statements, "investing_cash_flow")
    ta = _extract_input(statements, "total_assets")
    ta_p = _extract_input(statements, "total_assets", "prior")

    if any(v is None for v in [ni, cfo, ta]):
        return None, "insufficient_data"

    # Use average total assets if prior available
    avg_ta = (ta + ta_p) / 2 if ta_p is not None else ta
    if avg_ta == 0:
        return None, "zero_assets"

    # CFI may be None -- some companies don't separate investing
    accruals = ni - cfo - (cfi or 0)
    ratio = round(accruals / avg_ta, 4)

    if abs(ratio) <= 0.10:
        zone = "safe"
    elif abs(ratio) <= 0.25:
        zone = "warning"
    else:
        zone = "danger"

    return ratio, zone
```

### Forensic Result Pydantic Models (FRNSC-06)
```python
# New file: models/xbrl_forensics.py
class ForensicMetric(BaseModel):
    """Single forensic metric with value, zone, and confidence."""
    value: float | None = None
    zone: str = "insufficient_data"  # safe/warning/danger/critical
    trend: str | None = None  # improving/stable/deteriorating
    confidence: Confidence = Confidence.LOW

class BalanceSheetForensics(BaseModel):
    goodwill_to_assets: ForensicMetric = Field(default_factory=ForensicMetric)
    intangible_concentration: ForensicMetric = Field(default_factory=ForensicMetric)
    off_balance_sheet_ratio: ForensicMetric = Field(default_factory=ForensicMetric)
    cash_conversion_cycle: ForensicMetric = Field(default_factory=ForensicMetric)
    working_capital_volatility: ForensicMetric = Field(default_factory=ForensicMetric)

class CapitalAllocationForensics(BaseModel):
    roic: ForensicMetric = Field(default_factory=ForensicMetric)
    acquisition_effectiveness: ForensicMetric = Field(default_factory=ForensicMetric)
    buyback_timing: ForensicMetric = Field(default_factory=ForensicMetric)
    dividend_sustainability: ForensicMetric = Field(default_factory=ForensicMetric)

class DebtTaxForensics(BaseModel):
    interest_coverage: ForensicMetric = Field(default_factory=ForensicMetric)
    debt_maturity_concentration: ForensicMetric = Field(default_factory=ForensicMetric)
    etr_anomaly: ForensicMetric = Field(default_factory=ForensicMetric)
    deferred_tax_growth: ForensicMetric = Field(default_factory=ForensicMetric)
    pension_underfunding: ForensicMetric = Field(default_factory=ForensicMetric)

class RevenueForensics(BaseModel):
    deferred_revenue_divergence: ForensicMetric = Field(default_factory=ForensicMetric)
    channel_stuffing_indicator: ForensicMetric = Field(default_factory=ForensicMetric)
    margin_compression: ForensicMetric = Field(default_factory=ForensicMetric)
    ocf_revenue_ratio: ForensicMetric = Field(default_factory=ForensicMetric)

class BeneishDecomposition(BaseModel):
    """All 8 Beneish M-Score components exposed individually."""
    composite_score: float | None = None
    dsri: float | None = None  # Days Sales in Receivables Index
    gmi: float | None = None   # Gross Margin Index
    aqi: float | None = None   # Asset Quality Index
    sgi: float | None = None   # Sales Growth Index
    depi: float | None = None  # Depreciation Index
    sgai: float | None = None  # SGA Index
    tata: float | None = None  # Total Accruals to Total Assets
    lvgi: float | None = None  # Leverage Index
    zone: str = "insufficient_data"
    # Contextual note when SGI drives the score
    primary_driver: str | None = None
    trajectory: list[dict[str, float | str]] = Field(default_factory=list)

class EarningsQualityDashboard(BaseModel):
    sloan_accruals: ForensicMetric = Field(default_factory=ForensicMetric)
    cash_flow_manipulation: ForensicMetric = Field(default_factory=ForensicMetric)
    sbc_to_revenue: ForensicMetric = Field(default_factory=ForensicMetric)
    non_gaap_gap: ForensicMetric = Field(default_factory=ForensicMetric)

class MAForensics(BaseModel):
    """M&A forensics from XBRL acquisition data."""
    is_serial_acquirer: bool = False
    acquisition_years: int = 0  # Years with acquisitions in last 5
    total_acquisition_spend: float | None = None
    goodwill_accumulation_rate: float | None = None  # GW growth vs revenue growth
    acquisition_driven_revenue_pct: float | None = None

class XBRLForensics(BaseModel):
    """Top-level container for all XBRL forensic analysis results."""
    balance_sheet: BalanceSheetForensics = Field(default_factory=BalanceSheetForensics)
    capital_allocation: CapitalAllocationForensics = Field(default_factory=CapitalAllocationForensics)
    debt_tax: DebtTaxForensics = Field(default_factory=DebtTaxForensics)
    revenue: RevenueForensics = Field(default_factory=RevenueForensics)
    beneish: BeneishDecomposition = Field(default_factory=BeneishDecomposition)
    earnings_dashboard: EarningsQualityDashboard = Field(default_factory=EarningsQualityDashboard)
    ma_forensics: MAForensics = Field(default_factory=MAForensics)
```

## XBRL Concepts Required Per Forensic Module

### FRNSC-01: Balance Sheet Forensics
| Metric | Required Concepts | Status |
|--------|------------------|--------|
| Goodwill/TA trend | `goodwill`, `total_assets` | EXISTS in current 50 |
| Intangible concentration | `goodwill`, `intangible_assets`, `total_assets` | EXISTS |
| Off-balance-sheet | `operating_lease_liabilities`, `total_assets` | EXISTS |
| Cash conversion cycle | `inventory`, `accounts_receivable`, `accounts_payable`, `revenue`, `cost_of_revenue` | EXISTS |
| Working capital volatility | `current_assets`, `current_liabilities` | EXISTS |

### FRNSC-02: Capital Allocation Forensics
| Metric | Required Concepts | Status |
|--------|------------------|--------|
| ROIC | `ebit`, `income_tax_expense`, `pretax_income`, `stockholders_equity`, `total_debt`, `cash_and_equivalents` | EXISTS |
| Acquisition effectiveness | `goodwill` (trend), `revenue` (trend), `acquisitions_net` | `acquisitions_net` ADDED BY PHASE 67 |
| Buyback timing | `share_repurchases`, market price data | `share_repurchases` EXISTS; market price from `state.extracted.market` |
| Dividend sustainability | `dividends_paid`, `operating_cash_flow`, `capital_expenditures` | EXISTS |

### FRNSC-03: Debt/Tax Forensics
| Metric | Required Concepts | Status |
|--------|------------------|--------|
| Interest coverage | `ebit`, `interest_expense` | EXISTS |
| Debt maturity | `short_term_debt`, `total_debt` | EXISTS |
| ETR anomalies | `income_tax_expense`, `pretax_income` | EXISTS |
| Deferred tax liability | `deferred_tax_liability`, `revenue` | ADDED BY PHASE 67 |
| Pension underfunding | `pension_liability`, `stockholders_equity` | ADDED BY PHASE 67 |

### FRNSC-04: Revenue Quality
| Metric | Required Concepts | Status |
|--------|------------------|--------|
| Deferred revenue divergence | `deferred_revenue`, `revenue` | EXISTS |
| Channel stuffing | `accounts_receivable`, `revenue` | EXISTS |
| Margin compression | `gross_profit`, `revenue` (multi-period) | EXISTS |
| OCF/revenue | `operating_cash_flow`, `revenue` | EXISTS |

### FRNSC-05: Beneish Decomposition
All concepts already required by existing `compute_m_score()` -- no new concepts needed.

### FRNSC-08: M&A Forensics
| Metric | Required Concepts | Status |
|--------|------------------|--------|
| Acquisition spend | `acquisitions_net` | ADDED BY PHASE 67 |
| Goodwill accumulation | `goodwill` (multi-period) | EXISTS |
| Serial acquirer flag | `acquisitions_net` (multi-period) | ADDED BY PHASE 67 |

### FRNSC-09: Earnings Quality Dashboard
| Metric | Required Concepts | Status |
|--------|------------------|--------|
| Sloan Accruals | `net_income`, `operating_cash_flow`, `investing_cash_flow`, `total_assets` | EXISTS |
| Cash flow manipulation | `operating_cash_flow`, `net_income`, `revenue` | EXISTS |
| SBC/revenue | `stock_based_compensation`, `revenue` | `stock_based_compensation` ADDED BY PHASE 67 |
| Non-GAAP gap | `eps_basic` vs non-GAAP EPS | Non-GAAP EPS NOT in XBRL -- LIMITED |

## Key Design Decisions

### 1. Where to Store Forensic Results
**Decision:** New field `state.analysis.xbrl_forensics: dict[str, Any]` on `AnalysisResults`
**Rationale:**
- `state.analysis.forensic_composites` already taken (FIS/RQS/CFQS from Phase 26)
- Forensic analysis happens in ANALYZE stage, not EXTRACT -- so results go on `state.analysis`
- Using `dict[str, Any]` follows existing pattern (forensic_composites, temporal_signals, executive_risk all use `dict[str, Any]`)
- Serialized from `XBRLForensics.model_dump()`

### 2. Shared Extraction Helpers
**Decision:** Extract `_extract_input()`, `_find_line_item()`, `_get_latest_value()`, `_get_prior_value()` into a new `forensic_helpers.py` shared module
**Rationale:**
- Currently duplicated between `financial_models.py` and `earnings_quality.py`
- Adding 4+ more forensic modules would create 4 more copies
- Single shared module keeps helpers DRY
- Backward-compatible: existing files can import from shared module

### 3. Beneish Component Exposure Strategy
**Decision:** Modify `compute_m_score()` to populate `DistressResult.components` dict with all 8 indices
**Rationale:**
- Adding a `components` field to `DistressResult` is backward-compatible (default empty dict)
- Avoids computing M-Score twice
- Same approach can be used for Ohlson/Piotroski component exposure later
- Forensic module (`forensic_beneish.py`) reads components from existing distress result

### 4. Quarterly Enhancement Strategy
**Decision:** All forensic modules accept `quarterly: QuarterlyStatements | None` as optional parameter
**Rationale:**
- Phase 69 depends on Phase 67 (annual), optionally enhanced by Phase 68 (quarterly)
- When quarterly data absent: use annual periods (3 years) for trends
- When quarterly data present: use 8 quarters for finer-grained trend detection
- Same forensic computation, just different period granularity

### 5. Non-GAAP Gap Limitation
**Decision:** Flag FRNSC-09 non-GAAP gap metric as LIMITED -- non-GAAP EPS is not in standard XBRL taxonomy
**Rationale:**
- Companies report non-GAAP metrics in MD&A text and press releases, not in XBRL
- Some use custom extension taxonomy elements, but these are not standardized
- Best available proxy: compare GAAP EPS (from XBRL) against adjusted EPS if available in earnings_quality
- Flag as LOW confidence with explanation

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| M-Score as single number | 8 individual components exposed | This phase | Underwriter sees WHICH factor drives manipulation risk |
| Earnings quality as flat dict | Structured forensic models with zones | This phase | Color-coded severity per metric |
| No balance sheet forensics | Goodwill risk, intangible concentration, CCC tracking | This phase | Early warning on impairment / off-balance-sheet risk |
| No capital allocation analysis | ROIC trend, buyback timing, dividend sustainability | This phase | Identifies management quality issues |
| Annual-only forensic snapshot | Multi-period trajectory | This phase | Trend onset detection -- problems visible quarters earlier |

## Open Questions

1. **Shared extraction helpers -- import path**
   - What we know: `_extract_input()` is duplicated in financial_models.py and earnings_quality.py (private function, underscore prefix)
   - What's unclear: Whether to make it public in financial_models.py or extract to shared module
   - Recommendation: Extract to `forensic_helpers.py` in the analyze directory. Import from there in all forensic modules. Keep backward-compatible aliases in financial_models.py.

2. **Buyback timing quality -- stock price data source**
   - What we know: FRNSC-02 requires comparing average buyback price vs average stock price
   - What's unclear: Average buyback price is NOT in XBRL (requires dividing repurchase $ by shares retired). Average stock price is on `state.extracted.market.stock_data`.
   - Recommendation: Compute implied buyback price = share_repurchases / decrease_in_shares_outstanding. Compare against mean stock price from yfinance data. Flag as MEDIUM confidence since share count changes may include other factors.

3. **How forensic results feed into existing FIS composite**
   - What we know: Existing FIS (FinancialIntegrityScore) in forensic_composites.py already has revenue_quality, cash_flow_quality sub-scores
   - What's unclear: Whether new XBRL forensic modules should feed INTO existing FIS or remain separate
   - Recommendation: Keep separate for Phase 69. Phase 70 (Signal Integration) is the right place to wire new forensic data into the signal/composite system.

## Sources

### Primary (HIGH confidence)
- `stages/analyze/financial_models.py` -- `compute_distress_indicators()`, `_extract_input()`, `_collect_all_inputs()`, `_build_trajectory()` patterns (514 lines)
- `stages/analyze/financial_formulas.py` -- `compute_m_score()` with all 8 Beneish components, `safe_ratio()` (220 lines)
- `stages/analyze/earnings_quality.py` -- `compute_earnings_quality()` pattern, accruals ratio, OCF/NI, DSO (384 lines)
- `stages/extract/validation.py` -- `ExtractionReport`, `create_report()`, `merge_reports()` (239 lines)
- `models/financials.py` -- `FinancialStatements`, `FinancialLineItem`, `DistressResult`, `ExtractedFinancials` (410 lines)
- `models/forensic.py` -- `ForensicZone`, `SubScore`, `FinancialIntegrityScore` (191 lines)
- `models/state.py` -- `AnalysisResults` with `forensic_composites`, `AnalysisState` (349 lines)
- `stages/analyze/__init__.py` -- `_run_analytical_engines()` orchestrator pattern
- `brain/config/xbrl_concepts.json` -- 50 current concepts (581 lines)
- `.planning/phases/67-xbrl-first/67-RESEARCH.md` -- Phase 67 new concepts (income, balance sheet, cash flow additions)
- `.planning/research/ARCHITECTURE.md` -- v3.1 forensic module architecture spec

### Secondary (MEDIUM confidence)
- `.planning/research/xbrl-features.md` -- Beneish component formulas, Sloan Accruals zones, forensic ratio list
- Beneish M-Score (1999 paper) -- 8-variable model formula and coefficients
- Sloan Accruals Ratio -- Balance sheet approach (NI - CFO - CFI) / avg TA

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- zero new dependencies, all patterns established
- Architecture: HIGH -- follows proven financial_models.py + earnings_quality.py patterns exactly
- Pitfalls: HIGH -- identified from actual codebase analysis (Beneish components lost, namespace collision, helper duplication)
- XBRL concept availability: HIGH for FRNSC-01/04/05 (existing concepts), MEDIUM for FRNSC-02/03/08/09 (depends on Phase 67 additions)
- Non-GAAP gap metric: LOW -- not in standard XBRL taxonomy

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable domain -- financial forensic formulas don't change)
