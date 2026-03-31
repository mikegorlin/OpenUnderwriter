# Phase 71: Form 4 Insider Trading Enhancement - Research

**Researched:** 2026-03-06
**Domain:** SEC Form 4 XML parsing, insider trading analysis, filing timing correlation
**Confidence:** HIGH

## Summary

Phase 71 enhances an existing, well-structured Form 4 parser (`insider_trading.py`, 499 lines) with five capabilities: post-transaction ownership tracking, deduplication with amendment handling, gift/estate filtering, exercise-and-sell pattern detection, and filing timing analysis against 8-K events. The current parser already handles XML parsing via defusedxml, extracts transaction codes, detects 10b5-1 plans, computes cluster selling, and falls back to yfinance. The enhancement is purely additive -- extending `_parse_single_tx()` to extract additional XML fields, adding new analysis functions, and enriching the `InsiderTransaction` and `InsiderTradingAnalysis` models.

The Form 4 XML schema is well-defined by the SEC (ownershipDocument schema). Critical fields NOT currently extracted: `postTransactionAmounts/sharesOwnedFollowingTransaction/value` (ownership after trade), `ownershipNature/directOrIndirectOwnership/value` (direct vs indirect), and the full `reportingOwnerRelationship` flags (isDirector, isOfficer, isTenPercentOwner, isOther). These fields exist in every Form 4 filing and are straightforward to parse with the existing `_xml_text()` helper.

Filing timing analysis (FORM4-06) requires correlating Form 4 transaction dates with 8-K filing dates. Both are already acquired by the SEC client -- Form 4 filings and 8-K filings are both in `state.acquired_data.filings`. The 8-K filing metadata includes `filing_date`. The implementation cross-references these dates to detect insiders selling before negative announcements.

**Primary recommendation:** Extend the existing parser incrementally. Add 5-7 new fields to InsiderTransaction, 3-4 new analysis functions to insider_trading.py, and new computed fields to InsiderTradingAnalysis. Total change: ~200 lines of new code across 2 files (model + extractor).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FORM4-01 | Parse sharesOwnedFollowingTransaction, track post-transaction ownership, flag C-suite >25% sell in 6mo | XML field at `postTransactionAmounts/sharesOwnedFollowingTransaction/value`; add to `_parse_single_tx()` and new `compute_ownership_concentration()` function |
| FORM4-02 | Deduplicate by accession+date+owner, prefer 4/A over original | Add `accession_number` to InsiderTransaction; add `4/A` to `_FORM_TYPE_VARIANTS` in sec_client_filing.py; dedup in `_extract_from_form4s()` |
| FORM4-03 | Exclude gifts (G) and estate transfers (W) from buy/sell aggregation | Filter in `compute_aggregates()` by transaction_code; handle $0 price separately |
| FORM4-04 | Exercise-and-sell pattern: same owner, same date, code M then S | New `detect_exercise_sell_patterns()` function; group by owner+date |
| FORM4-05 | Parse isDirector, isOfficer, isTenPercentOwner; annotate indirect ownership | Parse from `reportingOwnerRelationship` and `ownershipNature/directOrIndirectOwnership`; add to InsiderTransaction model |
| FORM4-06 | Filing timing analysis: transaction dates vs 8-K dates | Cross-reference Form 4 transaction dates with 8-K `filing_date` from `state.acquired_data.filings["8-K"]` |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| defusedxml | installed | Safe XML parsing (Form 4) | Already used in insider_trading.py; prevents XXE attacks |
| pydantic | v2 | InsiderTransaction model extension | Project standard for all data models |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| xml.etree.ElementTree | stdlib | Type hints for Element type | Already imported alongside defusedxml |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| defusedxml | lxml | lxml is faster but defusedxml is already wired in; no need to change |

**Installation:**
No new dependencies required. Everything needed is already installed.

## Architecture Patterns

### Recommended Project Structure
```
src/do_uw/
  models/
    market_events.py      # MODIFY: Add new fields to InsiderTransaction, InsiderTradingAnalysis
  stages/
    extract/
      insider_trading.py  # MODIFY: Extend _parse_single_tx(), add analysis functions
    acquire/
      clients/
        sec_client_filing.py  # MODIFY: Add "4/A" to _FORM_TYPE_VARIANTS
```

### Pattern 1: Extend _parse_single_tx() for New Fields
**What:** Add extraction of 3 new XML fields to the existing per-transaction parser
**When to use:** FORM4-01, FORM4-05
**Example:**
```python
# In _parse_single_tx(), after existing parsing:
shares_owned_after = _safe_float(
    _xml_text(tx_el, ".//postTransactionAmounts/sharesOwnedFollowingTransaction/value")
)
direct_indirect = _xml_text(tx_el, ".//ownershipNature/directOrIndirectOwnership/value")
```

### Pattern 2: Separate Analysis Functions (Don't Bloat compute_aggregates)
**What:** Each FORM4 requirement gets its own function, called from extract_insider_trading()
**When to use:** FORM4-01 ownership concentration, FORM4-04 exercise-sell, FORM4-06 timing
**Example:**
```python
def compute_ownership_concentration(
    transactions: list[InsiderTransaction],
    lookback_months: int = 6,
) -> list[OwnershipConcentrationAlert]:
    """Flag C-suite selling >25% of holdings in lookback period."""
    # Group by owner, track shares_owned_following_transaction over time
```

### Pattern 3: Deduplication Before Analysis
**What:** Dedup transactions after parsing all Form 4 docs, before any analysis
**When to use:** FORM4-02
**Example:**
```python
def _deduplicate_transactions(
    transactions: list[InsiderTransaction],
) -> list[InsiderTransaction]:
    """Prefer 4/A amendments over original Form 4 filings."""
    # Key: (accession_number, transaction_date, owner_name)
    # If 4/A exists for same key, drop original
```

### Pattern 4: Filter by Transaction Code in Aggregation
**What:** Exclude non-economic transactions from buy/sell totals
**When to use:** FORM4-03
**Example:**
```python
# In compute_aggregates(), change the loop filter:
EXCLUDED_CODES = {"G", "W"}  # Gift, Will/Estate
ZERO_PRICE_CODES = {"A", "M", "F"}  # Grant, Exercise, Tax Withhold

for tx in transactions:
    if tx.transaction_code in EXCLUDED_CODES:
        continue  # Skip gifts and estate transfers
    if tx.transaction_code in ZERO_PRICE_CODES:
        # Track separately (grants, exercises)
        continue
```

### Anti-Patterns to Avoid
- **Rewriting the parser:** The existing parser is well-structured. Extend `_parse_single_tx()`, don't create a parallel parser.
- **Adding fields to InsiderTradingProfile AND InsiderTradingAnalysis:** The newer `InsiderTradingAnalysis` model (on `state.extracted.market.insider_analysis`) is the primary store. `InsiderTradingProfile` (on `state.extracted.market.insider_trading`) is the older summary model. Add new data to `InsiderTradingAnalysis` only.
- **Fetching additional SEC API calls:** All Form 4 data is already acquired. The 20-filing lookback on type "4" provides sufficient data. Just extend extraction from existing documents.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XML parsing | Custom regex-based parser | defusedxml (already used) | XML namespaces, entity attacks, edge cases |
| Date math | Manual string comparison | datetime.strptime + timedelta (already used) | Timezone, leap year, edge cases |
| Transaction code classification | New mapping dict | Existing TX_CODE_MAP + filtering | Already maps all SEC codes |

**Key insight:** The Form 4 XML schema is stable and well-documented by the SEC. The parser already handles the hard parts (defusedxml safety, footnote parsing, 10b5-1 detection). New fields are straightforward XPath extractions.

## Common Pitfalls

### Pitfall 1: Derivative vs Non-Derivative Ownership Tracking
**What goes wrong:** `sharesOwnedFollowingTransaction` appears in BOTH nonDerivativeTransaction AND derivativeTransaction elements. They track different ownership (common stock vs options/warrants).
**Why it happens:** An insider may own 50,000 shares directly but also hold 200,000 in options.
**How to avoid:** Track non-derivative ownership (actual shares) separately from derivative holdings. FORM4-01's "sells >25% of holdings" should use non-derivative shares only for the percentage calculation.
**Warning signs:** Ownership numbers much larger than expected (mixing derivative + non-derivative).

### Pitfall 2: Indirect Ownership Misclassification
**What goes wrong:** An insider's shares held through a trust, LLC, or family member are flagged as "indirect" but still represent economic interest.
**Why it happens:** `directOrIndirectOwnership` value is "D" (direct) or "I" (indirect). Indirect ≠ no interest.
**How to avoid:** Report indirect ownership with nature annotation (`ownershipNature/natureOfOwnership/value` gives "By Trust", "By LLC", etc.). Include indirect in total ownership tracking but annotate clearly.
**Warning signs:** Insider appears to own zero shares when they actually control millions through a trust.

### Pitfall 3: Amendment Deduplication Edge Cases
**What goes wrong:** A Form 4/A may correct only one transaction in a multi-transaction filing. The original filing's other transactions should be kept.
**Why it happens:** Amendments are full-filing replacements, not per-transaction patches.
**How to avoid:** When a 4/A replaces a 4, drop ALL transactions from the original accession number and keep ALL from the 4/A. Key on accession number, not individual transactions.
**Warning signs:** Duplicate transactions in output; missing transactions after dedup.

### Pitfall 4: Exercise-Sell Detection Window
**What goes wrong:** Exercise (M) and sell (S) may not be on the exact same calendar date -- they could be split across adjacent days.
**Why it happens:** Some exercise-and-sell transactions settle across days; Form 4 reports transaction date, not filing date.
**How to avoid:** Use a 1-day window for same-owner M+S pairing, not strict same-date matching.
**Warning signs:** Known exercise-sell patterns missed because transactions span midnight.

### Pitfall 5: 8-K Filing Date vs Event Date
**What goes wrong:** Using 8-K `filing_date` instead of the event date inside the 8-K.
**Why it happens:** Companies have up to 4 business days to file an 8-K after a triggering event. The filing_date is when SEC received it, which may differ from the actual event.
**How to avoid:** Use both dates if available. The LLM-extracted 8-K data (`eight_k_events`) may include event dates. For the initial implementation, use filing_date as a conservative proxy (insider selling BEFORE the filing date is more suspicious, not less).
**Warning signs:** False positives where insider sold after the event but before the 8-K was filed.

### Pitfall 6: Multiple Reporting Owners
**What goes wrong:** A single Form 4 can have multiple `reportingOwner` elements (e.g., joint filing by co-CEOs or a company + an officer).
**Why it happens:** SEC allows joint Form 4 filings.
**How to avoid:** The current parser only reads the first `rptOwnerName`. Need to handle multiple owners correctly -- each transaction belongs to the reporting owner(s).
**Warning signs:** Transactions attributed to wrong person; only one of two joint filers captured.

## Code Examples

### Current XML Parsing (source: insider_trading.py)
```python
# Existing _parse_single_tx extracts:
tx_date_str = _xml_text(tx_el, ".//transactionDate/value")
tx_code = _xml_text(tx_el, ".//transactionCoding/transactionCode")
shares_val = _safe_float(_xml_text(tx_el, ".//transactionAmounts/transactionShares/value"))
price_val = _safe_float(_xml_text(tx_el, ".//transactionAmounts/transactionPricePerShare/value"))
```

### New Fields to Extract (Form 4 XML XPaths)
```python
# FORM4-01: Post-transaction ownership
shares_owned_after = _safe_float(
    _xml_text(tx_el, ".//postTransactionAmounts/sharesOwnedFollowingTransaction/value")
)

# FORM4-05: Ownership nature (direct vs indirect)
direct_indirect = _xml_text(
    tx_el, ".//ownershipNature/directOrIndirectOwnership/value"
)  # "D" = direct, "I" = indirect
nature_of_ownership = _xml_text(
    tx_el, ".//ownershipNature/natureOfOwnership/value"
)  # e.g., "By Trust", "By LLC"

# FORM4-05: Relationship flags (from reportingOwner, NOT transaction)
is_director = _xml_text(root, ".//isDirector") == "1"
is_officer = _xml_text(root, ".//isOfficer") == "1"
is_ten_pct_owner = _xml_text(root, ".//isTenPercentOwner") == "1"
```

### Model Extensions (InsiderTransaction)
```python
# New fields on InsiderTransaction:
shares_owned_following: SourcedValue[float] | None = Field(
    default=None,
    description="Shares owned after this transaction (from postTransactionAmounts)",
)
is_director: bool = Field(default=False)
is_officer: bool = Field(default=False)
is_ten_pct_owner: bool = Field(default=False)
ownership_nature: str = Field(
    default="D",
    description="D=direct, I=indirect",
)
indirect_ownership_explanation: str = Field(
    default="",
    description="Nature of indirect ownership (e.g., By Trust)",
)
accession_number: str = Field(
    default="",
    description="SEC accession number for deduplication",
)
is_amendment: bool = Field(
    default=False,
    description="True if from a Form 4/A filing",
)
```

### Exercise-Sell Pattern Detection
```python
def detect_exercise_sell_patterns(
    transactions: list[InsiderTransaction],
) -> list[ExerciseSellEvent]:
    """Detect same-owner, same-date exercise (M) + sell (S) patterns."""
    events: list[ExerciseSellEvent] = []
    # Group by (owner, date) with 1-day tolerance
    by_owner_date: dict[str, list[InsiderTransaction]] = {}
    for tx in transactions:
        if tx.insider_name and tx.transaction_date:
            key = f"{tx.insider_name.value}|{tx.transaction_date.value}"
            by_owner_date.setdefault(key, []).append(tx)

    for key, txns in by_owner_date.items():
        exercises = [t for t in txns if t.transaction_code == "M"]
        sells = [t for t in txns if t.transaction_code == "S"]
        if exercises and sells:
            events.append(ExerciseSellEvent(
                owner=txns[0].insider_name.value if txns[0].insider_name else "",
                date=txns[0].transaction_date.value if txns[0].transaction_date else "",
                exercised_shares=sum(e.shares.value for e in exercises if e.shares),
                sold_shares=sum(s.shares.value for s in sells if s.shares),
                sold_value=sum(s.total_value.value for s in sells if s.total_value),
            ))
    return events
```

### Filing Timing Analysis
```python
def analyze_filing_timing(
    transactions: list[InsiderTransaction],
    eight_k_filings: list[dict[str, str]],
    window_days: int = 30,
) -> list[TimingSuspect]:
    """Detect insider selling within window_days before 8-K filing."""
    suspects: list[TimingSuspect] = []
    for filing in eight_k_filings:
        filing_date = filing.get("filing_date", "")
        if not filing_date:
            continue
        # Find sells within window before this 8-K
        sells_before = [
            tx for tx in transactions
            if tx.transaction_type == "SELL"
            and tx.transaction_date
            and _days_between(tx.transaction_date.value, filing_date) > 0
            and _days_between(tx.transaction_date.value, filing_date) <= window_days
        ]
        if sells_before:
            suspects.append(TimingSuspect(
                filing_date=filing_date,
                filing_type="8-K",
                insiders_who_sold=[
                    tx.insider_name.value for tx in sells_before
                    if tx.insider_name
                ],
                days_before_filing=min(
                    _days_between(tx.transaction_date.value, filing_date)
                    for tx in sells_before if tx.transaction_date
                ),
                total_sold_value=sum(
                    tx.total_value.value for tx in sells_before if tx.total_value
                ),
            ))
    return suspects
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yfinance-only insider data | Form 4 XML parser + yfinance fallback | v1.0 Phase 4 | HIGH confidence transactions from SEC |
| No ownership tracking | sharesOwnedFollowingTransaction (Phase 71) | This phase | Enables ownership concentration alerts |
| No deduplication | Accession-based dedup with 4/A preference | This phase | Eliminates double-counting |

**Key data flow:**
- Form 4 filings acquired: `state.acquired_data.filings["4"]` contains 20 most recent filings with `full_text` (raw XML)
- 8-K filings acquired: `state.acquired_data.filings["8-K"]` contains 20 most recent with `filing_date`
- Parsed transactions: `state.extracted.market.insider_analysis.transactions`
- Cluster events: `state.extracted.market.insider_analysis.cluster_events`
- Signal routing: 14 existing insider signals in `gov/insider.yaml` + `stock/insider.yaml`, routed via `signal_field_routing.py`

## Critical Implementation Details

### Form 4/A Amendment Handling
The current `_FORM_TYPE_VARIANTS` dict in `sec_client_filing.py` does NOT include "4/A". The `_form_type_matches()` function only matches exact type "4". To support FORM4-02:
1. Add `"4": ["4", "4/A"]` to `_FORM_TYPE_VARIANTS`
2. Mark which transactions came from 4/A vs 4 (store form_type on InsiderTransaction)
3. Dedup: when same accession base exists as both 4 and 4/A, keep 4/A only

### Accession Number Availability
The filing metadata in `state.acquired_data.filings["4"]` includes `accession_number` per filing. However, `_extract_from_form4s()` iterates over filing documents (the XML content), not the metadata. Need to pass accession_number from the filing metadata into `parse_form4_xml()` so it can be stored on InsiderTransaction for deduplication.

### 8-K Data Availability for Timing Analysis
8-K filing metadata is available in `state.acquired_data.filings["8-K"]` with `filing_date` field. The enriched 8-K events (from LLM extraction) are stored in `state.acquired_data.market_data["eight_k_events"]` with departure/restatement/earnings counts. For FORM4-06, the raw filing metadata dates are sufficient.

### Existing Signal Wiring
14 insider-related signals already exist but many are INACTIVE or poorly wired:
- `GOV.INSIDER.unusual_timing` (INACTIVE) -- FORM4-06 data will enable activation
- `GOV.INSIDER.plan_adoption` (INACTIVE) -- Not directly addressed by this phase
- `GOV.INSIDER.executive_sales` -- Currently maps to `insider_pct` field; can be upgraded to use ownership concentration data
- `GOV.INSIDER.ownership_pct` -- Currently maps to `insider_pct`; can be upgraded to use actual post-transaction ownership

### Multiple Reporting Owners
Current parser reads only the FIRST `rptOwnerName` from `root.findall(".//rptOwnerName")`. A Form 4 can have multiple `<reportingOwner>` elements. The current design assigns all transactions to one owner. This is acceptable for most filings (single owner) but should be documented as a known limitation.

## Open Questions

1. **8-K event date extraction accuracy**
   - What we know: 8-K filing metadata has `filing_date`. LLM 8-K extraction may have event dates.
   - What's unclear: How reliably does the LLM extract the actual event date vs filing date?
   - Recommendation: Use `filing_date` as the conservative date for timing analysis. If LLM-extracted event dates are available in `eight_k_events`, use those as a more precise alternative.

2. **Ownership percentage calculation denominator**
   - What we know: `sharesOwnedFollowingTransaction` gives absolute share count.
   - What's unclear: What denominator to use for "sells >25% of holdings"? Use the insider's own prior holdings (shares_owned_before = shares_owned_after + shares_sold), not total shares outstanding.
   - Recommendation: Compute percentage as `shares_sold / (shares_owned_after + shares_sold)` per owner over the 6-month window.

3. **Form 4/A accession number relationship**
   - What we know: 4/A has a different accession number than the original 4.
   - What's unclear: How to link a 4/A to its original 4 filing programmatically.
   - Recommendation: The 4/A XML contains the same owner + same transaction dates as the original. Dedup by (owner_name, transaction_date, shares) tuple rather than trying to link accession numbers. If a transaction matches on all three fields, keep the one from the later filing date (which is the amendment).

## Sources

### Primary (HIGH confidence)
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/extract/insider_trading.py` -- Current Form 4 parser (499 lines, complete review)
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/market_events.py` -- InsiderTransaction and InsiderTradingAnalysis models
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/models/market.py` -- MarketSignals model with insider_analysis field
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/brain/signals/gov/insider.yaml` -- 8 GOV.INSIDER signals
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/brain/signals/stock/insider.yaml` -- 3 STOCK.INSIDER signals
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/analyze/signal_field_routing.py` -- Field key routing for insider signals
- `/Users/gorlin/projects/UW/do-uw/src/do_uw/stages/acquire/clients/sec_client_filing.py` -- Filing acquisition, lookback=20, no 4/A variant
- `/Users/gorlin/projects/UW/do-uw/tests/test_insider_short.py` -- Existing test fixtures with sample Form 4 XML

### Secondary (MEDIUM confidence)
- [SEC EDGAR Ownership XML Technical Specification](https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf) -- Official XML schema documentation
- [SEC Form 4 Data Guide](https://www.sec.gov/files/form4data.pdf) -- Transaction code definitions

### Tertiary (LOW confidence)
- General knowledge of Form 4 XML structure from training data -- verified against sample XML in test fixtures

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new dependencies, extending existing code
- Architecture: HIGH - Current parser is well-structured, clear extension points
- Pitfalls: HIGH - Based on actual codebase review and SEC filing structure analysis
- XML field paths: HIGH - Verified against sample Form 4 XML in test fixtures (isDirector, isOfficer fields present and working)

**Research date:** 2026-03-06
**Valid until:** 2026-04-06 (stable -- SEC Form 4 XML schema rarely changes)
