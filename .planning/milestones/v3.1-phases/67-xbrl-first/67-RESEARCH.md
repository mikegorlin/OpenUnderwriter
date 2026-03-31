# Phase 67: XBRL Foundation -- Concept Expansion & Infrastructure - Research

**Researched:** 2026-03-05
**Domain:** XBRL concept mapping, sign normalization, derived computation, coverage validation
**Confidence:** HIGH

## Summary

Phase 67 expands the XBRL extraction foundation from 40 mapped concepts to 120+ concepts, adds sign normalization, builds a derived computation module, and creates coverage validation tooling. This is pure config + computation work with zero API changes -- the Company Facts API already returns all the data; the system just needs to extract more concepts from it and compute derived metrics.

The existing `xbrl_concepts.json` has 40 concepts (38 with XBRL tags, 2 derived: `working_capital` and `ebitda`). The `xbrl_mapping.py` module's `resolve_concept()` function tries priority-ordered tags and picks the tag with the most recent data -- this pattern is correct and just needs more entries. The `financial_statements.py` module extracts 3 annual periods from 10-K filings and builds `FinancialStatement` objects with `FinancialLineItem` entries. The total liabilities derivation (Assets - Equity) already exists in `financial_models.py` but needs hardening for minority interest and preferred stock edge cases.

**Primary recommendation:** Expand `xbrl_concepts.json` with ~70 new entries (adding `expected_sign` to ALL entries), create `xbrl_derived.py` for computed ratios/margins, add `xbrl_coverage.py` for tag resolution validation, and harden the total liabilities derivation. No new dependencies, no API changes, no model changes beyond adding fields to the config schema.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| XBRL-01 | Expand xbrl_concepts.json from 50 to 120+ concepts | Current file has 40 concepts (582 lines). ~70 new entries needed across income (~15), balance sheet (~20), cash flow (~15), plus ~20 derived. Tag lists researched from SEC API patterns and prior research. |
| XBRL-02 | expected_sign field + sign normalization layer | DQC 0015 documents 900+ elements with sign errors (~12% of filings). Each concept needs debit/credit expected_sign. Normalization runs after extraction, before ratios. |
| XBRL-03 | Derived concept computation module (xbrl_derived.py) | ~20 derived concepts: margins (gross, operating, net, EBITDA), ratios (current, quick, D/E, D/EBITDA, interest coverage), per-share (BV/share, FCF/share). All from XBRL primitives. |
| XBRL-04 | Coverage validator: log tag resolution, alert <60% | `resolve_concept()` already logs which tag matched. Need structured tracking per concept per ticker with coverage report. |
| XBRL-05 | Tag discovery utility: scan Company Facts for a CIK | Simple utility: load company_facts, iterate all concepts, dump names+values. For research when adding new concepts. |
| XBRL-06 | Total liabilities derivation hardened | Current code derives TL = TA - SE. Edge cases: minority interest (should be subtracted from SE before deriving TL), preferred stock equity component, companies with LiabilitiesAndStockholdersEquity but no atomic Liabilities. |
</phase_requirements>

## Standard Stack

### Core (Already Installed -- No Changes)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Runtime | Project standard |
| Pydantic | 2.10+ | Config validation, new models | Already used everywhere |
| httpx | 0.28+ | SEC API (no new calls for this phase) | Project standard |

### Supporting (Already in Codebase)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `xbrl_mapping.py` | existing | Concept resolution from Company Facts | Extend with new concepts |
| `financial_statements.py` | existing | Statement extraction | Modify to use sign normalization |
| `financial_models.py` | existing | Distress model inputs | Fix total_liabilities derivation |

### No New Dependencies
This phase requires zero new packages. Everything is config expansion + pure Python computation.

## Architecture Patterns

### Recommended File Structure
```
src/do_uw/
  brain/config/
    xbrl_concepts.json       # MODIFY: 40 -> 120+ concepts, add expected_sign
  stages/extract/
    xbrl_mapping.py           # MODIFY: add sign normalization, coverage tracking
    xbrl_derived.py           # NEW: derived concept computation (~200 lines)
    xbrl_coverage.py          # NEW: coverage validator + tag discovery (~150 lines)
    financial_statements.py   # MODIFY: call sign normalization after extraction
  stages/analyze/
    financial_models.py       # MODIFY: harden total_liabilities derivation
```

### Pattern 1: Config-Driven Concept Mapping (EXISTING -- extend)
**What:** XBRL tags -> canonical names in JSON config; code resolves via priority-ordered tag list
**When to use:** Every new financial concept
**Example:**
```json
{
  "stock_based_compensation": {
    "canonical_name": "stock_based_compensation",
    "xbrl_tags": [
      "ShareBasedCompensation",
      "AllocatedShareBasedCompensationExpense",
      "ShareBasedCompensationIncludingDiscontinuedOperations"
    ],
    "unit": "USD",
    "period_type": "duration",
    "statement": "income",
    "description": "Stock-based compensation expense",
    "expected_sign": "positive"
  }
}
```

### Pattern 2: Sign Normalization Layer (NEW -- establish)
**What:** After `resolve_concept()` returns raw values, normalize signs based on `expected_sign` config
**When to use:** Before ANY ratio computation or downstream consumption
**Example:**
```python
def normalize_sign(
    value: float,
    expected_sign: str,
    concept_name: str,
) -> tuple[float, bool]:
    """Normalize sign based on expected_sign config.

    Returns (normalized_value, was_normalized).
    """
    if expected_sign == "positive" and value < 0:
        logger.info("Sign normalization: %s was negative (%.2f), taking abs", concept_name, value)
        return abs(value), True
    if expected_sign == "negative" and value > 0:
        logger.info("Sign normalization: %s was positive (%.2f), negating", concept_name, value)
        return -abs(value), True
    # "any" or matching sign -- no normalization
    return value, False
```

### Pattern 3: Derived Computation (NEW -- establish)
**What:** Compute margins, ratios, per-share metrics from XBRL primitives
**When to use:** After all primitive concepts are extracted
**Example:**
```python
def compute_derived_concepts(
    line_items: dict[str, float | None],
) -> dict[str, float | None]:
    """Compute all derived concepts from XBRL primitives."""
    derived: dict[str, float | None] = {}

    # Gross margin
    revenue = line_items.get("revenue")
    cogs = line_items.get("cost_of_revenue")
    if revenue and cogs and revenue != 0:
        derived["gross_margin_pct"] = (revenue - cogs) / revenue * 100

    # Current ratio
    ca = line_items.get("current_assets")
    cl = line_items.get("current_liabilities")
    if ca is not None and cl and cl != 0:
        derived["current_ratio"] = ca / cl

    return derived
```

### Anti-Patterns to Avoid
- **Computing derived metrics in multiple places:** All derived computation goes in `xbrl_derived.py`, nowhere else
- **Adding `expected_sign` only to new concepts:** ALL 40 existing concepts MUST also get `expected_sign`
- **Hardcoding tag lists in Python code:** Tags belong in `xbrl_concepts.json`, period
- **Normalizing signs that can legitimately be negative:** `net_income`, `operating_cash_flow`, `retained_earnings` use `expected_sign: "any"`
- **Breaking existing tests:** The 15 existing financial statement tests must continue to pass without modification

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tag priority resolution | Custom logic per concept | Existing `resolve_concept()` | Already picks tag with most recent data |
| SourcedValue provenance | Custom tracking | Existing `_make_sourced_value()` | Already sets HIGH confidence + full source |
| Extraction reports | Custom logging | Existing `ExtractionReport` / `create_report()` | Already tracks found/missing/coverage |
| Financial model inputs | Direct state access | Existing `_collect_all_inputs()` / `_extract_input()` | Already handles latest/prior period routing |

## Common Pitfalls

### Pitfall 1: Tag Fragmentation for New Concepts
**What goes wrong:** New concept mapped with only 1-2 tags works for test tickers but misses 30% of real-world companies
**Why it happens:** US-GAAP taxonomy has 20,000+ tags; FASB renames/deprecates across versions; companies use tags from older taxonomy years
**How to avoid:** Every new concept MUST have 3+ tags in priority order. Use the tag discovery utility (XBRL-05) to verify tag resolution across AAPL, RPM, SNA, V, WWD before committing
**Warning signs:** Coverage validator (XBRL-04) reports <60% resolution for any concept

### Pitfall 2: Sign Convention Errors (~12% of Filings)
**What goes wrong:** Capital expenditures reported as negative by one company and positive by another. Free cash flow computation produces wrong sign.
**Why it happens:** Filing preparers confuse presentation formatting (parentheses) with XBRL semantics (balance type)
**How to avoid:** `expected_sign` field on every concept. Normalization layer applies `abs()` where appropriate. Log every normalization.
**Warning signs:** Ratios outside theoretical range (negative current ratio, debt-to-equity < -10)

### Pitfall 3: Total Liabilities Derivation Edge Cases
**What goes wrong:** TL = TA - SE formula produces wrong result when SE includes minority interest or preferred stock equity
**Why it happens:** `StockholdersEquity` sometimes includes noncontrolling interest; some filers use `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest`
**How to avoid:** Derivation cascade: (1) try `Liabilities` tag directly, (2) try `TA - SE`, (3) if minority_interest found, compute `TA - SE - minority_interest`, (4) if `LiabilitiesAndStockholdersEquity` found, try `L&SE - SE`
**Warning signs:** Total liabilities > total assets (impossible unless negative equity, which should be flagged separately)

### Pitfall 4: Derived Concept Division by Zero
**What goes wrong:** Computing ratios with denominator = 0 or None
**Why it happens:** Newly public companies may have zero revenue in early periods; companies with zero debt have undefined D/E
**How to avoid:** Every derived computation must guard against None inputs AND zero denominators. Return None, never raise.
**Warning signs:** Any derived metric producing `inf` or `nan`

### Pitfall 5: Breaking Existing Concept Resolution by Adding expected_sign
**What goes wrong:** Adding `expected_sign` to `xbrl_concepts.json` breaks `load_xbrl_mapping()` if the TypedDict is strict
**Why it happens:** The `XBRLConcept` TypedDict defines exactly 6 fields. Adding `expected_sign` requires updating the TypedDict.
**How to avoid:** Update `XBRLConcept` TypedDict to include `expected_sign: str` with default `"any"`. Make `load_xbrl_mapping()` handle missing `expected_sign` gracefully (default to `"any"`).

## Code Examples

### Current xbrl_concepts.json Structure (40 concepts)
```json
{
  "revenue": {
    "canonical_name": "revenue",
    "xbrl_tags": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", ...],
    "unit": "USD",
    "period_type": "duration",
    "statement": "income",
    "description": "Total revenue / net sales"
  }
}
```

### New xbrl_concepts.json Structure (with expected_sign)
```json
{
  "revenue": {
    "canonical_name": "revenue",
    "xbrl_tags": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", ...],
    "unit": "USD",
    "period_type": "duration",
    "statement": "income",
    "description": "Total revenue / net sales",
    "expected_sign": "positive"
  }
}
```

### Sign Convention Reference (from DQC 0015 + accounting standards)
```
ALWAYS POSITIVE (debit balance, cash outflow):
  capital_expenditures, depreciation_amortization, interest_expense,
  research_development, sga_expense, cost_of_revenue, income_tax_expense,
  dividends_paid, share_repurchases, restructuring_charges, impairment_charges,
  total_assets, current_assets, accounts_receivable, inventory,
  property_plant_equipment, goodwill, intangible_assets

ALWAYS POSITIVE (credit balance):
  revenue, gross_profit, total_liabilities, current_liabilities,
  accounts_payable, deferred_revenue, long_term_debt, short_term_debt,
  total_debt, operating_lease_liabilities, stockholders_equity (usually)

CAN BE NEGATIVE (legitimate):
  net_income (net loss), operating_income (operating loss),
  operating_cash_flow (cash used), investing_cash_flow (usually negative),
  financing_cash_flow (can go either way), retained_earnings (accumulated deficit),
  comprehensive_income, other_income, pretax_income, ebit, ebitda,
  working_capital, minority_interest
```

### Total Liabilities Derivation Cascade
```python
def derive_total_liabilities(
    inputs: dict[str, float | None],
) -> float | None:
    """Derive total liabilities with edge case handling.

    Priority order:
    1. Direct Liabilities tag
    2. TA - SE (basic derivation)
    3. TA - SE - minority_interest (when SE includes NCI)
    4. LiabilitiesAndStockholdersEquity - SE (when only L&SE available)
    """
    tl = inputs.get("total_liabilities")
    if tl is not None:
        return tl

    ta = inputs.get("total_assets")
    se = inputs.get("stockholders_equity")

    if ta is not None and se is not None:
        mi = inputs.get("minority_interest")
        if mi is not None and mi > 0:
            # SE tag includes NCI -- subtract it
            return ta - se + mi
        return ta - se

    # Fallback: LiabilitiesAndStockholdersEquity - SE
    lse = inputs.get("liabilities_and_stockholders_equity")
    if lse is not None and se is not None:
        return lse - se

    return None
```

### Coverage Validator Output Format
```python
@dataclass
class ConceptResolution:
    concept_name: str
    resolved_tag: str | None  # Which XBRL tag matched
    tags_tried: int           # How many tags were attempted
    value_count: int          # How many period values found

@dataclass
class CoverageReport:
    ticker: str
    total_concepts: int
    resolved_concepts: int
    coverage_pct: float
    by_statement: dict[str, float]  # statement_type -> coverage %
    resolutions: list[ConceptResolution]
    alerts: list[str]  # e.g., "balance_sheet coverage 45% < 60% threshold"
```

## New Concepts to Add (Researched Tag Lists)

### Income Statement Additions (~15 new)
| Concept | Primary Tag | Fallback Tags | expected_sign |
|---------|------------|---------------|---------------|
| stock_based_compensation | ShareBasedCompensation | AllocatedShareBasedCompensationExpense | positive |
| income_before_tax | IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest | IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments | any |
| discontinued_operations | IncomeLossFromDiscontinuedOperationsNetOfTax | IncomeLossFromDiscontinuedOperationsNetOfTaxAttributableToReportingEntity | any |
| gain_loss_investments | GainLossOnInvestments | GainLossOnInvestmentsExcludingOtherThanTemporaryImpairments | any |
| gain_loss_sale_assets | GainLossOnSaleOfPropertyPlantEquipment | GainLossOnDispositionOfAssets1 | any |
| other_comprehensive_income | OtherComprehensiveIncomeLossNetOfTax | OtherComprehensiveIncomeLossNetOfTaxPortionAttributableToParent | any |
| operating_expenses_total | OperatingExpenses | CostsAndExpenses | positive |
| total_operating_expenses | CostsAndExpenses | OperatingCostsAndExpenses | positive |

### Balance Sheet Additions (~20 new)
| Concept | Primary Tag | Fallback Tags | expected_sign |
|---------|------------|---------------|---------------|
| short_term_investments | ShortTermInvestments | MarketableSecuritiesCurrent, AvailableForSaleSecuritiesDebtSecuritiesCurrent | positive |
| prepaid_expenses | PrepaidExpenseAndOtherAssetsCurrent | PrepaidExpense | positive |
| other_current_assets | OtherAssetsCurrent | OtherAssetsCurrentAndNoncurrent | positive |
| long_term_investments | LongTermInvestments | InvestmentsInAffiliatesSubsidiariesAssociatesAndJointVentures | positive |
| accrued_liabilities | AccruedLiabilitiesCurrent | AccruedLiabilitiesAndOtherLiabilities | positive |
| deferred_tax_asset | DeferredIncomeTaxAssetsNet | DeferredTaxAssetsLiabilitiesNetNoncurrent | positive |
| deferred_tax_liability | DeferredIncomeTaxLiabilitiesNet | DeferredTaxLiabilitiesNoncurrent | positive |
| pension_liability | DefinedBenefitPlanAmountsRecognizedInBalanceSheet | PensionAndOtherPostretirementDefinedBenefitPlansLiabilitiesNoncurrent | positive |
| accumulated_other_comprehensive_income | AccumulatedOtherComprehensiveIncomeLossNetOfTax | AccumulatedOtherComprehensiveIncomeMember | any |
| treasury_stock | TreasuryStockValue | TreasuryStockValueAcquiredCostMethod | positive |
| common_stock_value | CommonStockValue | CommonStockValueOutstanding | positive |
| additional_paid_in_capital | AdditionalPaidInCapital | AdditionalPaidInCapitalCommonStock | positive |
| liabilities_and_stockholders_equity | LiabilitiesAndStockholdersEquity | LiabilitiesAndStockholdersEquityIncludingPortionAttributableToNoncontrollingInterest | positive |
| preferred_stock_value | PreferredStockValue | PreferredStockValueOutstanding | positive |
| right_of_use_asset | OperatingLeaseRightOfUseAsset | FinanceLeaseRightOfUseAsset | positive |

### Cash Flow Additions (~15 new)
| Concept | Primary Tag | Fallback Tags | expected_sign |
|---------|------------|---------------|---------------|
| acquisitions_net | PaymentsToAcquireBusinessesNetOfCashAcquired | PaymentsToAcquireBusinessesGross | positive |
| debt_issuance | ProceedsFromIssuanceOfLongTermDebt | ProceedsFromIssuanceOfDebt | positive |
| debt_repayment | RepaymentsOfLongTermDebt | RepaymentsOfDebt | positive |
| stock_issuance | ProceedsFromIssuanceOfCommonStock | ProceedsFromStockPlans | positive |
| interest_paid | InterestPaidNet | InterestPaid | positive |
| taxes_paid | IncomeTaxesPaid | IncomeTaxesPaidNet | positive |
| stock_based_comp_cf | ShareBasedCompensation | StockBasedCompensationExpenseIncludingDiscontinuedOperations | positive |
| change_in_working_capital | IncreaseDecreaseInOperatingCapital | IncreaseDecreaseInOperatingLiabilities | any |
| net_change_in_cash | CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect | CashAndCashEquivalentsPeriodIncreaseDecrease | any |

### Derived Concepts (~20, computed from primitives)
| Concept | Formula | Inputs | Statement |
|---------|---------|--------|-----------|
| gross_margin_pct | (revenue - cost_of_revenue) / revenue * 100 | revenue, cost_of_revenue | income |
| operating_margin_pct | operating_income / revenue * 100 | operating_income, revenue | income |
| net_margin_pct | net_income / revenue * 100 | net_income, revenue | income |
| ebitda_margin_pct | ebitda / revenue * 100 | ebitda, revenue | income |
| effective_tax_rate | income_tax_expense / income_before_tax * 100 | income_tax_expense, pretax_income | income |
| interest_coverage_ratio | ebit / interest_expense | ebit, interest_expense | income |
| revenue_growth_yoy | (rev_t - rev_t1) / abs(rev_t1) * 100 | revenue (2 periods) | income |
| current_ratio | current_assets / current_liabilities | current_assets, current_liabilities | balance_sheet |
| quick_ratio | (current_assets - inventory) / current_liabilities | current_assets, inventory, current_liabilities | balance_sheet |
| debt_to_equity | total_debt / stockholders_equity | total_debt, stockholders_equity | balance_sheet |
| debt_to_ebitda | total_debt / ebitda | total_debt, ebitda | balance_sheet |
| tangible_book_value | stockholders_equity - goodwill - intangible_assets | stockholders_equity, goodwill, intangible_assets | balance_sheet |
| net_debt | total_debt - cash_and_equivalents | total_debt, cash_and_equivalents | balance_sheet |
| book_value_per_share | stockholders_equity / shares_outstanding | stockholders_equity, shares_outstanding | balance_sheet |
| free_cash_flow | operating_cash_flow - capital_expenditures | operating_cash_flow, capital_expenditures | cash_flow |
| fcf_to_revenue | free_cash_flow / revenue * 100 | free_cash_flow, revenue | cash_flow |
| capex_to_revenue | capital_expenditures / revenue * 100 | capital_expenditures, revenue | cash_flow |
| capex_to_depreciation | capital_expenditures / depreciation_amortization | capital_expenditures, depreciation_amortization | cash_flow |
| dividend_payout_ratio | dividends_paid / net_income * 100 | dividends_paid, net_income | cash_flow |
| fcf_per_share | free_cash_flow / shares_outstanding | free_cash_flow, shares_outstanding | cash_flow |

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 40 XBRL concepts | 120+ concepts | This phase | 3x coverage of financial line items |
| No sign normalization | expected_sign per concept + normalization layer | This phase | Eliminates ~12% of sign convention errors |
| Derived metrics scattered | Centralized xbrl_derived.py | This phase | Single location for all computed ratios |
| No coverage tracking | Per-concept per-ticker resolution logging | This phase | Visibility into extraction quality |
| TL = TA - SE only | 4-step derivation cascade | This phase | Handles minority interest, preferred stock, L&SE edge cases |

## Open Questions

1. **Tag priority validation against real filings**
   - What we know: Prior research lists recommended tags; existing 40 concepts work on test tickers
   - What's unclear: Whether all ~70 new concept tag lists actually resolve on AAPL, RPM, SNA, V, WWD
   - Recommendation: Build tag discovery utility (XBRL-05) first, use it to validate tag lists before committing concept entries

2. **Derived concepts in xbrl_concepts.json vs separate config**
   - What we know: Current `working_capital` and `ebitda` are in xbrl_concepts.json with empty `xbrl_tags: []`
   - What's unclear: Whether 20 more derived entries clutters the config or if a separate `xbrl_derived_concepts.json` is cleaner
   - Recommendation: Keep all in one file -- the code already handles empty `xbrl_tags`. Derived concepts are still concepts.

3. **Sign normalization audit trail format**
   - What we know: Must log every normalization for audit
   - What's unclear: Whether to log to Python logger only or also store in ExtractionReport
   - Recommendation: Log to Python logger AND add `normalizations: list[str]` field to ExtractionReport for structured tracking

## Sources

### Primary (HIGH confidence)
- `xbrl_concepts.json` -- 40 existing concepts, structure verified (582 lines)
- `xbrl_mapping.py` -- `resolve_concept()`, `extract_concept_value()`, `load_xbrl_mapping()` (212 lines)
- `financial_statements.py` -- `_extract_single_statement()`, `_make_sourced_value()`, `extract_financial_statements()` (486 lines)
- `financial_models.py` -- `_collect_all_inputs()`, total_liabilities derivation (lines 136-153)
- `financials.py` -- `FinancialLineItem`, `FinancialStatement`, `FinancialStatements`, `ExtractedFinancials` models
- `test_financial_statements.py` -- 15 existing tests covering multi-period, YoY, deduplication, coverage, fallback

### Secondary (MEDIUM confidence)
- [XBRL US DQC 0015 -- Negative Values](https://xbrl.us/data-rule/dqc_0015/) -- Sign convention rules, 900+ element list
- [DQC 0015 List of Elements V3](https://xbrl.us/data-rule/dqc_0015-le-v3pr/) -- Specific elements that should not be negative
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) -- Company Facts API structure
- `.planning/research/ARCHITECTURE.md` -- Full v3.1 architecture with concept expansion details
- `.planning/research/xbrl-pitfalls.md` -- 13 pitfalls documented with prevention strategies
- `.planning/research/xbrl-features.md` -- Feature landscape including sign convention details
- `.planning/research/signal-xbrl-audit.md` -- 45 XBRL-replaceable signals, 28 enhanceable

### Tertiary (LOW confidence)
- [2025 US GAAP Taxonomy](https://xbrl.us/xbrl-taxonomy/2025-us-gaap/) -- Taxonomy reference (not directly consulted for tag lists)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, purely extending existing patterns
- Architecture: HIGH -- extending proven `xbrl_concepts.json` + `resolve_concept()` pattern
- Pitfalls: HIGH -- DQC 0015 sign convention well-documented; total liabilities derivation already encountered in codebase
- New concept tag lists: MEDIUM -- researched from prior architecture research + SEC documentation, but not validated against all 5 test tickers yet

**Research date:** 2026-03-05
**Valid until:** 2026-04-05 (stable domain -- XBRL taxonomy changes annually, not monthly)
