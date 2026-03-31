# Domain Pitfalls: v3.1 XBRL-First Data Integrity

**Domain:** Adding comprehensive XBRL extraction to existing D&O underwriting system
**Researched:** 2026-03-05
**Overall confidence:** HIGH (based on codebase analysis + SEC documentation + XBRL.org guidance)

---

## Critical Pitfalls

Mistakes that cause wrong numbers in the worksheet, broken forensic models, or silent data corruption.

### Pitfall 1: XBRL Tag Fragmentation -- Same Concept, Different Tags

**What goes wrong:** Companies use different US-GAAP tags for the same financial concept. Revenue alone has 5+ valid tags (`Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, etc.). When expanding from 40 to 120+ concepts, the tag-miss rate increases dramatically. A concept mapped to `Liabilities` misses companies that only report `LiabilitiesAndStockholdersEquity` (which the system already hit -- see `financial_models.py` lines 137-153 where `total_liabilities` is derived from `Assets - StockholdersEquity` as a workaround).

**Why it happens:** The US-GAAP taxonomy has 20,000+ tags. FASB periodically renames/deprecates tags across taxonomy versions. Companies may use a 2020 tag in filings through 2026 if they haven't updated. Custom extensions (used by 10-15% of filings for at least some concepts) are invisible to the Company Facts API.

**Consequences:** Missing financial data for specific companies. Forensic models (Beneish, Altman) get `NOT_APPLICABLE` instead of a score. Silent bias: companies with unusual tags appear "no data" rather than "high risk."

**Prevention:**
- The existing `xbrl_concepts.json` multi-tag approach is correct. For every new concept added beyond the current 40, research the actual tag distribution across 50+ real filings before choosing tags.
- Add a coverage validation step after extraction: for each concept, log which tag resolved and which companies had zero-resolution. Track resolution rates per concept across tickers.
- Build a "tag discovery" utility that scans Company Facts for a CIK and dumps all concepts with values, so you can audit what tags a specific company actually uses.
- The existing `resolve_concept()` function picks the tag with the most recent `max_end` date. This is correct -- keep this behavior.

**Detection:** Extraction coverage below 60% for any statement type. New ticker producing significantly fewer resolved concepts than existing tickers. `DistressResult.is_partial=True` with many `missing_inputs`.

**Phase impact:** Must be addressed in the XBRL Foundation phase (first). Build the tag registry with coverage testing before building forensic models on top.

**Confidence:** HIGH -- directly observed in codebase. The `total_liabilities` derivation workaround is proof this already bites.

### Pitfall 2: Quarterly Period Confusion -- YTD vs Discrete Quarters

**What goes wrong:** The Company Facts API returns both YTD cumulative values and discrete quarterly values for income statement / cash flow items. A Q3 10-Q filing reports revenue for Q3 alone AND cumulative Q1+Q2+Q3. If you naively take the `fp=Q3` entry, you might get the 9-month cumulative instead of the 3-month quarter. Subtracting to get discrete quarterly data introduces errors when companies restate prior quarters.

**Why it happens:** SEC XBRL reporting requires cumulative YTD figures for income statements. The Company Facts API stores both the discrete quarter and the YTD filing. The `fp` field (fiscal period) is `Q1`, `Q2`, `Q3`, or `FY` -- but `Q2` means "YTD through Q2" for duration concepts, not "Q2 alone." The `start` and `end` dates disambiguate, but require date arithmetic.

**Consequences:** Revenue, net income, and cash flow could be 2-3x overstated for Q2/Q3 if you mistake YTD for quarterly. Forensic models that compute quarter-over-quarter trends will produce nonsensical ratios. Seasonal pattern detection becomes impossible.

**Prevention:**
- For duration concepts (income statement, cash flow): Filter by `start` and `end` dates, not just `fp`. A discrete quarter has `end - start` of approximately 90 days. A YTD period has `end - start` of 180+ days.
- Compute discrete Q2 = YTD_Q2 - YTD_Q1 (and Q3 = YTD_Q3 - YTD_Q2). This is how professional data providers do it.
- For instant concepts (balance sheet): No YTD issue -- each period is a point-in-time snapshot. Just filter by `fp` and `end` date.
- Store both raw (as-filed) and computed (discrete quarterly) values. Flag computed values with a different confidence or source annotation.
- The existing `period_type` field in `xbrl_concepts.json` (`"instant"` vs `"duration"`) is the key discriminator. Use it to route different handling logic.

**Detection:** Revenue for Q2 or Q3 that is 2x+ the Q1 figure for the same fiscal year. Quarter-over-quarter growth rates exceeding 100% on a mature company.

**Phase impact:** Must be solved in the XBRL Foundation phase before any quarterly data is consumed by forensic models. Getting this wrong poisons everything downstream.

**Confidence:** HIGH -- confirmed via SEC EDGAR API documentation and Company Facts API behavior.

### Pitfall 3: XBRL Sign Convention Errors -- Companies Report Wrong Signs

**What goes wrong:** XBRL requires values to be reported per the element's "balance type" (debit or credit), regardless of how the number appears in the HTML/PDF filing. But approximately 12% of all XBRL errors are sign errors (second most common error type per XBRL US DQC). Companies report expenses as negative because they show in parentheses in the filing, even though the XBRL element definition says they should be positive.

**Why it happens:** Filing preparers confuse presentation formatting (parentheses = subtraction) with XBRL semantics (element balance type determines sign). Treasury stock, tax benefits/expenses, and cash flow items are the worst offenders.

**Consequences:** Capital expenditures might be reported as positive in one company and negative in another. This makes free cash flow calculations wrong. Debt-to-equity ratios can flip sign. Beneish M-Score and Altman Z-Score produce wrong zone classifications.

**Prevention:**
- Build a sign normalization layer that applies AFTER extraction, BEFORE any ratio computation:
  - `capital_expenditures`: Should be positive (cash outflow). If negative, take `abs()`.
  - `dividends_paid`: Should be positive (cash outflow). If negative, take `abs()`.
  - `share_repurchases`: Should be positive (cash outflow). If negative, take `abs()`.
  - `depreciation_amortization`: Should be positive. If negative, take `abs()`.
  - `treasury_stock`: Should be positive (equity reduction). If negative, take `abs()`.
  - `interest_expense`: Should be positive. If negative, take `abs()`.
  - `income_tax_expense`: Can legitimately be negative (tax benefit). Do NOT blindly abs().
  - `net_income`: Can legitimately be negative (net loss). Do NOT abs().
  - `operating_cash_flow`: Can legitimately be negative. Do NOT abs().
- Log every sign normalization for audit trail.
- Cross-validate: if OCF is negative and net income is positive AND capex is large, double-check signs before computing accruals ratios.

**Detection:** Any financial ratio producing a value outside its theoretical range (e.g., negative current ratio, debt-to-equity below -10). Altman Z-Score below -5 or above +15 on a real company.

**Phase impact:** Must be built into the XBRL extraction layer itself, not bolted on later. Every concept in `xbrl_concepts.json` needs an `expected_sign` field.

**Confidence:** HIGH -- XBRL US DQC Rule 0015 documents this extensively. The rule lists 900+ elements that commonly have sign errors.

### Pitfall 4: Fiscal Year Misalignment Across Companies and Periods

**What goes wrong:** Apple's fiscal year ends September 30. Walmart's ends January 31. When comparing Apple's "FY2024" (ending Sep 2024) to Walmart's "FY2024" (ending Jan 2024), you're comparing periods 8 months apart. Worse, the Company Facts API's `fy` field reflects the company's fiscal year, not the calendar year -- so Apple's FY2024 Q1 is October-December 2023.

**Why it happens:** The system currently uses `fiscal_year_label()` which generates `FY{fy}` directly from the Company Facts API's `fy` field. This works for single-company analysis but breaks for peer benchmarking.

**Consequences:** Peer comparison ratios are meaningless when comparing different economic periods. A company reporting in a recession quarter gets compared to peers reporting in a growth quarter. The Frames API mitigates this for cross-company comparison (it calendar-aligns), but Company Facts for single-company deep-dive does not.

**Prevention:**
- For single-company time series: Use `fy` + `fp` as-is. The company's own periods are internally consistent.
- For peer benchmarking: Use the Frames API (which calendar-aligns) rather than Company Facts. The Frames API's `CY2024Q1` means calendar Q1 2024 for ALL companies.
- Store both the company's fiscal period labels AND the calendar-aligned period for each data point.
- When computing QoQ or YoY trends on a single company, always compare `fp=Q1` to prior year `fp=Q1`, not across different fiscal periods.
- The `end` date field is the ground truth for temporal alignment.

**Detection:** Peer comparison showing implausible divergence (e.g., all peers down 20% but target up 30% -- might be period misalignment, not outperformance).

**Phase impact:** Affects peer benchmarking phase. Single-company extraction can proceed with fiscal year labels, but peer comparison requires calendar alignment.

**Confidence:** HIGH -- observed in existing `fiscal_year_label()` implementation.

---

## Moderate Pitfalls

### Pitfall 5: Company Facts API Blind Spots

**What goes wrong:** The Company Facts API only contains data from standard taxonomies (`us-gaap`, `ifrs-full`, `dei`, `srt`). It does NOT include:
- Company extension elements (custom tags created by filers)
- Dimensional/segment-level data (revenue by geography, product line)
- Text blocks (MD&A, risk factors)
- Filing-level calculations and hierarchy
- Inline XBRL rendering hints

**Prevention:**
- Company Facts for flat concept resolution (current approach -- correct).
- Filing-level XBRL (via edgartools or direct iXBRL parsing) for segment data, dimensional breakdowns, and custom extensions.
- Keep LLM extraction as Tier 2 for qualitative data that has no XBRL equivalent (risk factor narratives, MD&A commentary, litigation descriptions).
- The existing two-tier approach in `financial_statements.py` (Company Facts primary, edgartools fallback) is architecturally correct but the edgartools fallback currently returns `None` always (line 326: `return None, report`). This must be implemented.

**Detection:** Coverage metrics per concept. Companies with >30% of financial data in custom extensions will show low XBRL coverage.

**Phase impact:** Core XBRL phase for flat concepts. Segment/dimensional extraction is a separate sub-phase that requires filing-level parsing.

**Confidence:** HIGH -- confirmed via SEC EDGAR API documentation. Company Facts response structure verified in codebase.

### Pitfall 6: Form 4 XML Parsing Edge Cases

**What goes wrong:** The existing `insider_trading.py` Form 4 parser handles basic non-derivative and derivative transactions but misses several edge cases:

1. **Indirect ownership:** Transactions through trusts, LLCs, family members. The same shares may appear under multiple owners. Current parser extracts `rptOwnerName` but doesn't handle `ownershipNature/directOrIndirectOwnership`.
2. **Filing amendments (Form 4/A):** Amendments restate prior transactions. Without deduplication by `accn` (accession number), amended transactions get double-counted.
3. **Gift transactions (code "G"):** Currently mapped but not excluded from buy/sell aggregation. A gift of $50M in shares is not a bearish signal.
4. **Derivative conversions (code "C"):** Option exercises followed by same-day sales. Currently treated as two separate transactions but should be analyzed as a single exercise-and-sell pattern.
5. **Multiple owners per filing:** Form 4 can report for joint owners. Current parser takes the first `rptOwnerName` only.
6. **Price per share = $0:** Stock grants, RSU vesting. These inflate transaction counts without economic significance.

**Prevention:**
- Add `directOrIndirectOwnership` field to `InsiderTransaction` model. Filter or annotate indirect holdings.
- Deduplicate by accession number + transaction date + owner. Prefer amendments (Form 4/A) over originals.
- Exclude gift transactions (code "G") and estate transfers (code "W") from buy/sell aggregation.
- Detect exercise-and-sell patterns: same owner, same date, code "M" followed by code "S".
- Handle `$0` price transactions separately in aggregate metrics.
- The existing `TX_CODE_MAP` is comprehensive (12 codes). The gap is in how aggregates treat each code.

**Detection:** Insider selling totals that seem implausibly high (gift transactions inflating sell volume). Cluster detection firing on gift transactions.

**Phase impact:** Form 4 extraction sub-phase. Can be done in parallel with XBRL financial foundation.

**Confidence:** HIGH -- reviewed `insider_trading.py` in detail. Edge cases identified from SEC Form 4 technical specification.

### Pitfall 7: Beneish M-Score False Positives on High-Growth and One-Time Items

**What goes wrong:** The Beneish M-Score's SGI (Sales Growth Index) component inherently flags high-growth companies. A company growing revenue 40% YoY gets a high SGI, pushing the M-Score toward "manipulation likely" regardless of actual manipulation. Similarly, one-time items (restructuring charges, impairment losses, acquisition-related costs) corrupt the DSRI, GMI, and TATA components because they distort the year-over-year comparison.

**Why it happens:** The Beneish model was calibrated on 1982-1992 data. High-growth companies were rare in that sample. The model's 17.5% false positive rate is well-documented. SOX-era improvements help but the structural growth bias remains.

**Consequences:** The system flags high-growth tech companies (which are often large D&O risks for OTHER reasons) with "earnings manipulation" when the signal is actually "fast growth." This undermines credibility of the forensic scoring with experienced underwriters who know the company is simply growing fast.

**Prevention:**
- Contextualize M-Score results with growth rate. If revenue growth > 25% and M-Score is in distress zone, add a caveat: "M-Score elevated, likely driven by high revenue growth (SGI={value}) rather than manipulation indicators."
- Report individual M-Score components (DSRI, GMI, AQI, SGI, DEPI, SGAI, TATA, LVGI) alongside the aggregate score. The current `compute_m_score()` function computes all 8 but only stores the final score.
- Flag one-time items: if `restructuring_charges` or `impairment_charges` are non-zero in current or prior period, note that M-Score may be distorted.
- Consider adding industry-adjusted thresholds: tech/biotech companies have structurally different M-Score distributions than industrials. The current `-1.78` threshold is one-size-fits-all.
- Do NOT remove or suppress the M-Score for high-growth companies -- it still catches real manipulation. Just add context.

**Detection:** M-Score in distress zone with SGI > 1.25 and other components near baseline. High-growth company with no other red flags triggering on M-Score alone.

**Phase impact:** Forensic models phase. Component-level reporting should be built when implementing expanded forensic analysis.

**Confidence:** HIGH -- Beneish's original paper documents the 17.5% false positive rate. Confirmed by multiple academic sources.

### Pitfall 8: XBRL-to-LLM Handoff -- Breaking the Anti-Hallucination Guarantee

**What goes wrong:** The system's core promise is "zero hallucination for quantitative data." When XBRL extraction fails (tag not found, company uses custom extension, data quality issue), falling back to LLM extraction reintroduces hallucination risk. The LLM might confidently extract a number that doesn't exist in the filing, or misread a footnote table.

**Why it happens:** The current system uses LLM extraction for everything. Switching to "XBRL primary, LLM fallback" creates a hybrid where the confidence level of any given number depends on which path produced it, but downstream consumers (forensic models, signal evaluation, rendering) don't distinguish.

**Consequences:** A Beneish M-Score computed from 6 XBRL values and 2 LLM-extracted values has mixed confidence. If one LLM value is hallucinated, the entire model output is wrong but marked as HIGH confidence because the XBRL values are HIGH.

**Prevention:**
- **Confidence tagging per value, not per statement.** The existing `SourcedValue` model already has `confidence` (HIGH/MEDIUM/LOW) and `source` fields. Use them rigorously:
  - XBRL Company Facts = HIGH confidence
  - XBRL filing-level = HIGH confidence
  - LLM extraction from filing text = MEDIUM confidence
  - yfinance/web data = LOW confidence
- **Composite confidence for derived metrics:** A Beneish M-Score should inherit the LOWEST confidence of its input values. If any input is MEDIUM (LLM-extracted), the M-Score is MEDIUM.
- **Never mix in the same computation without flagging.** If 7/8 Beneish inputs are XBRL and 1 is LLM, log which input was LLM and note it in `missing_inputs` or a new `fallback_inputs` field.
- **LLM extraction guardrails stay in place:** Instructor schemas, validation ranges, cross-field consistency checks. Don't weaken these just because XBRL is "primary."
- **Prefer "N/A" over LLM fallback for forensic models.** For M-Score/Z-Score, a partial computation (5/8 XBRL inputs) is more trustworthy than a full computation (8/8 with 3 LLM guesses). The existing `is_partial` flag already supports this.

**Detection:** Confidence distribution per extraction run. If >20% of financial values are LLM-sourced, the XBRL extraction layer has gaps that need tag expansion.

**Phase impact:** Must be designed into the extraction architecture from day one. Retrofitting confidence tracking is much harder than building it in.

**Confidence:** HIGH -- directly relevant to system's core anti-hallucination principle documented in CLAUDE.md.

### Pitfall 9: Breaking Existing Signal Evaluation When Data Sources Change

**What goes wrong:** The system has 400 brain signals with `field_key` routing that maps signals to specific data fields. Signals like `fin_revenue_growth_yoy` expect `float | None` at a specific path. When XBRL extraction replaces LLM extraction, the data values may differ slightly (XBRL reports exact GAAP numbers; LLM might have extracted rounded figures or different line items). Thresholds calibrated on LLM-extracted data may not work correctly on XBRL data.

**Why it happens:** LLM extraction introduces systematic biases: rounding, choosing different line items for "revenue," occasionally missing values that XBRL captures. Signals and their thresholds were tuned against these biased values. Switching to "correct" XBRL data changes the distribution.

**Consequences:**
- Signals that were TRIGGERED at a threshold of `< 1.0` for current ratio might stop triggering because XBRL reports `1.02` while LLM was extracting `0.98`.
- More values resolve (fewer `None`/`N/A`), which means more signals fire. Previously-SKIPPED signals now evaluate, potentially changing overall scores.
- Composite scores (Altman Z, Beneish M) may shift by 0.1-0.5 points due to more precise inputs.
- Cross-ticker validation baselines (AAPL, RPM, SNA, V, WWD) become invalid and need recalibration.

**Prevention:**
- **Shadow evaluation during transition.** Run both LLM and XBRL extraction for at least one full validation cycle. Compare outputs field-by-field.
- **Log data source for every field.** The existing `SourcedValue.source` field should clearly indicate "XBRL:company_facts:Revenues" vs "LLM:10-K:revenue_extraction."
- **Recalibrate cross-ticker baselines AFTER switching.** Re-run AAPL, RPM, SNA, V, WWD with XBRL extraction and update golden baselines.
- **Threshold review:** For signals with numeric thresholds (e.g., `current_ratio < 1.0`), verify that the threshold is still appropriate with XBRL precision. Some thresholds may need 5-10% adjustment.
- **SKIPPED signal audit:** After XBRL expansion, re-run the SKIPPED signal audit. Expect the SKIPPED count to drop from ~60 to ~30-40 as more data resolves.
- **DO NOT change thresholds preemptively.** Run the shadow evaluation first, identify actual divergences, then adjust case by case with evidence.

**Detection:** Score delta report: run same tickers through old and new extraction, compare per-signal results. Any signal flipping from TRIGGERED to NOT_TRIGGERED (or vice versa) needs investigation.

**Phase impact:** This is a cross-cutting concern that spans all phases. Each phase that adds new XBRL concepts must include a backward-compatibility check. But the heaviest impact is in the first phase (XBRL Foundation) when the extraction layer changes.

**Confidence:** HIGH -- the codebase has 400 signals with specific thresholds. Any data source change will affect evaluation.

---

## Minor Pitfalls

### Pitfall 10: IFRS Filers Use Different Namespace and Concepts

**What goes wrong:** Foreign Private Issuers (FPIs) filing under IFRS use `ifrs-full` namespace instead of `us-gaap`. The concept names are completely different (`Revenue` in IFRS vs `Revenues` in US-GAAP). The existing code detects IFRS (line 419-421 of `financial_statements.py`) but doesn't extract from it.

**Prevention:** Build a parallel `ifrs_concepts.json` mapping table with IFRS tag equivalents. The `resolve_concept()` function should check both `us-gaap` and `ifrs-full` namespaces. For the v3.1 milestone, IFRS support can be deferred if scope is limited to US-domiciled companies, but the architecture should not assume `us-gaap` exclusively.

**Phase impact:** Low priority for v3.1 (most D&O targets are US-domiciled). But the extraction architecture should allow namespace parameterization.

**Confidence:** MEDIUM -- IFRS filer handling not tested against real data.

### Pitfall 11: Frames API Data Freshness and Calendar Alignment Quirks

**What goes wrong:** The Frames API calendar-aligns data using +/- 30 day windows. A company with fiscal year ending January 31 gets mapped to CY####Q4 (calendar Q4 = Oct-Dec). If the company's Q4 is actually Nov-Jan, the 30-day tolerance handles it, but edge cases exist (companies with 4-4-5 fiscal calendars, 52/53-week years, or mid-month period ends).

**Prevention:** Always verify Frames API results against Company Facts for the same company. If Frames API returns a value for CY2024 but Company Facts shows the actual fiscal year ending in March 2025, flag the discrepancy. Use Frames API for sector-level percentile ranking (where +/- 30 day alignment is acceptable) but Company Facts for company-specific analysis.

**Phase impact:** Peer benchmarking phase only.

**Confidence:** MEDIUM -- Frames API behavior confirmed in documentation but edge cases not tested empirically.

### Pitfall 12: SEC Rate Limiting and Cache Staleness

**What goes wrong:** SEC APIs have a 10 req/sec rate limit. The current system caches Company Facts for 14 months (line 215 of `sec_client.py`). When expanding to Frames API calls for peer benchmarking (one call per concept per period per SIC code), the number of API calls increases dramatically. Hitting rate limits silently drops requests.

**Prevention:** Batch Frames API calls with rate limiting (already have `sec_get()` with proper User-Agent). Pre-cache common SIC codes. Consider reducing Company Facts TTL to 90 days for companies with recent filings (fiscal year just ended). The Frames API data updates within minutes of filing, so freshness is good -- but cached data can be 14 months stale.

**Phase impact:** Infrastructure concern for peer benchmarking phase.

**Confidence:** HIGH -- rate limit is documented and enforced.

### Pitfall 13: edgartools Fallback Currently Non-Functional

**What goes wrong:** The Tier 2 fallback via edgartools in `financial_statements.py` (lines 278-335) is scaffolded but always returns `None`. This means when Company Facts coverage is below 50%, the system has no fallback -- it just reports empty data.

**Prevention:** Either implement the edgartools fallback properly (parse XBRL from individual filings) or replace it with a filing-level XBRL parser. The `edgartools` library (v5.14.1 installed) has XBRL parsing capabilities that should be leveraged. This is not a "pitfall to avoid" but a "known gap to close."

**Phase impact:** Should be addressed in the XBRL Foundation phase. Without a working fallback, coverage will remain incomplete for companies with unusual tagging.

**Confidence:** HIGH -- directly observed in code (line 326: `return None, report`).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| XBRL Financial Foundation | Tag fragmentation for 80 new concepts (Pitfall 1) | Research real tag distribution before mapping. Build coverage validator. |
| XBRL Financial Foundation | YTD vs quarterly confusion (Pitfall 2) | Use `start`/`end` date filtering for duration concepts. Build discrete quarter computation. |
| XBRL Financial Foundation | Sign convention errors (Pitfall 3) | Add `expected_sign` to concept config. Build normalization layer. |
| XBRL Financial Foundation | edgartools fallback broken (Pitfall 13) | Implement or replace before expanding concept count. |
| Forensic Calculations | Beneish false positives on growth companies (Pitfall 7) | Report components, add growth-rate context, industry thresholds. |
| Forensic Calculations | Mixed-confidence inputs (Pitfall 8) | Composite confidence = min(input confidences). Flag LLM fallback inputs. |
| Form 4 Extraction | Amendment double-counting (Pitfall 6) | Deduplicate by accession + date + owner. Prefer 4/A over original. |
| Form 4 Extraction | Gift transactions inflating sell volume (Pitfall 6) | Exclude codes G, W from buy/sell aggregation. |
| Peer Benchmarking | Fiscal year misalignment (Pitfall 4) | Use Frames API (calendar-aligned) for cross-company comparison. |
| Peer Benchmarking | Frames API rate limits (Pitfall 12) | Batch calls, pre-cache common SIC codes, rate-limit requests. |
| Signal Integration | Threshold recalibration needed (Pitfall 9) | Shadow evaluation, cross-ticker delta report, recalibrate baselines. |
| Signal Integration | SKIPPED signal count changes (Pitfall 9) | Re-run SKIPPED audit after each extraction expansion. |

---

## Integration-Specific Warnings

These pitfalls are unique to ADDING XBRL extraction to an EXISTING system (not building from scratch).

### The "Better Data, Worse Scores" Problem

When XBRL provides more precise numbers than LLM extraction, some companies will score better and some worse. This is correct behavior but will confuse users comparing old vs new reports for the same company. Mitigation: version reports. Include extraction method and date in output metadata.

### The Partial Migration Trap

During the transition, some financial fields will come from XBRL and others from LLM. The temptation is to migrate one concept at a time ("let's just do revenue from XBRL"). This creates a period where half the data is HIGH confidence and half is MEDIUM, with no way for downstream consumers to tell which is which unless `SourcedValue.source` is properly set. Mitigation: migrate by statement type (all income statement concepts at once, then all balance sheet), not by individual concept.

### The Coverage Regression

Adding XBRL extraction should INCREASE data availability. But if the XBRL tag list is incomplete, switching from LLM (which can extract ANY concept mentioned in text) to XBRL (which only extracts tagged concepts) actually REDUCES coverage for some companies. Mitigation: never remove LLM extraction until XBRL coverage is validated at >= 90% across all test tickers.

---

## Sources

- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) -- Company Facts and Frames API documentation
- [XBRL US DQC Rule 0015 -- Negative Values](https://xbrl.us/data-rule/dqc_0015/) -- Sign convention errors, 900+ element list
- [XBRL.org -- Positive and Negative Values](https://www.xbrl.org/guidance/positive-and-negative-values/) -- Sign convention guidance
- [SEC Custom Tags Trend 2022-2024](https://www.sec.gov/data-research/gaap-xbrl-custom-tags) -- Custom extension usage statistics
- [SEC Form 4 XML Technical Specification](https://www.sec.gov/info/edgar/ownershipxmltechspec-v3.pdf) -- Form 4 parsing reference
- [Beneish M-Score -- Wikipedia](https://en.wikipedia.org/wiki/Beneish_M-score) -- False positive rates, model limitations
- [Portfolio123 -- Beneish M-Score Analysis](https://blog.portfolio123.com/detecting-financial-fraud-a-close-look-at-the-beneish-m-score/) -- Post-SOX performance analysis
- Codebase analysis: `xbrl_mapping.py`, `financial_statements.py`, `financial_models.py`, `financial_formulas.py`, `insider_trading.py`, `xbrl_concepts.json`, `sec_client.py`
