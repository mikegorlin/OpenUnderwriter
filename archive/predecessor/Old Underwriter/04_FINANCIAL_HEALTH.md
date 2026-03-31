# SECTION B: FINANCIAL HEALTH
## 112 Checks

---

## B.1: LIQUIDITY (Checks B.1.1 - B.1.8)

### B.1.1: Cash Position & Runway â­ CRITICAL
**Check ID**: B.1.1
**What**: Insufficient cash creates immediate risk
**Source**: 10-Q Balance Sheet, Cash Flow Statement
**Calculate**: Cash & Equivalents / Quarterly Cash Burn

**Data to Collect**:
| Metric | Current | Prior Quarter |
|--------|---------|---------------|
| Cash & Equivalents | $[X]M | $[X]M |
| Marketable Securities | $[X]M | $[X]M |
| **Total Liquid Assets** | $[X]M | $[X]M |
| Quarterly Cash Burn | $[X]M | $[X]M |
| **Cash Runway** | [X] months | [X] months |

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| <6 months runway | ðŸ”´ CRITICAL | F.9: 6 pts |
| 6-12 months | ðŸ”´ HIGH | F.9: 4 pts |
| 12-18 months | ðŸŸ¡ MODERATE | F.9: 2 pts |
| >18 months | ðŸŸ¢ LOW | F.9: 0 pts |

---

### B.1.2: Working Capital
**Check ID**: B.1.2
**What**: Negative working capital = liquidity stress
**Source**: 10-Q Balance Sheet
**Calculate**: Current Assets - Current Liabilities

**Data to Collect**:
| Metric | Amount |
|--------|--------|
| Current Assets | $[X]M |
| Current Liabilities | $[X]M |
| **Working Capital** | $[X]M |
| **Current Ratio** | [X.X]x |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Current ratio <1.0 | ðŸ”´ HIGH |
| Current ratio 1.0-1.5 | ðŸŸ¡ MODERATE |
| Current ratio >1.5 | ðŸŸ¢ LOW |

---

### B.1.3: Quick Ratio
**Check ID**: B.1.3
**What**: Immediate liquidity (excludes inventory)
**Calculate**: (Current Assets - Inventory) / Current Liabilities

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Quick ratio <0.5 | ðŸ”´ HIGH |
| Quick ratio 0.5-1.0 | ðŸŸ¡ MODERATE |
| Quick ratio >1.0 | ðŸŸ¢ LOW |

---

### B.1.4: Credit Facility Availability
**Check ID**: B.1.4
**What**: Undrawn credit = liquidity buffer
**Source**: 10-K/Q debt footnotes
**Data to Collect**:
| Facility | Commitment | Drawn | Available |
|----------|------------|-------|-----------|
| Revolver | $[X]M | $[X]M | $[X]M |
| Term Loan | $[X]M | $[X]M | N/A |
| **Total Availability** | | | $[X]M |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| No facility or fully drawn | ðŸ”´ HIGH |
| <50% available | ðŸŸ¡ MODERATE |
| >50% available | ðŸŸ¢ LOW |

---

### B.1.5: Revolver Utilization Trend
**Check ID**: B.1.5
**What**: Increasing reliance on credit facility
**Source**: Compare last 4 quarters
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Utilization increasing >50% over 4 quarters | ðŸ”´ HIGH |
| Stable utilization | ðŸŸ¡ MODERATE |
| Decreasing | ðŸŸ¢ LOW |

---

### B.1.6: Cash Concentration Risk
**Check ID**: B.1.6
**What**: Cash trapped in foreign jurisdictions
**Source**: 10-K geographic footnote
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| >50% cash offshore with repatriation issues | ðŸŸ¡ MODERATE |
| Diversified or easily accessible | ðŸŸ¢ LOW |

---

### B.1.7: Restricted Cash
**Check ID**: B.1.7
**What**: Cash not available for operations
**Source**: Balance sheet, footnotes
**Calculate**: Restricted Cash / Total Cash

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| >30% of cash restricted | ðŸŸ¡ MODERATE |
| Minimal restricted | ðŸŸ¢ LOW |

---

### B.1.8: ATM/Shelf Registration Status
**Check ID**: B.1.8
**What**: Ability to raise capital quickly
**Source**: S-3 shelf registration
**Data to Collect**:
- Active shelf: [Yes/No]
- Capacity: $[X]M
- Utilized: $[X]M

---

## B.2: LEVERAGE & DEBT (Checks B.2.1 - B.2.20)

### B.2.1: Debt Structure Summary
**Check ID**: B.2.1
**What**: Comprehensive debt picture
**Source**: 10-Q/10-K debt footnote, balance sheet
**Data to Collect**:
| Debt Type | Amount | Rate | Maturity |
|-----------|--------|------|----------|
| Term Loan A | $[X]M | [X]% | [Date] |
| Term Loan B | $[X]M | [X]% | [Date] |
| Senior Notes | $[X]M | [X]% | [Date] |
| Revolver | $[X]M | [X]% | [Date] |
| Convertible | $[X]M | [X]% | [Date] |
| Other | $[X]M | | |
| **Total Debt** | $[X]M | | |

---

### B.2.2: Debt/EBITDA Ratio â­ CRITICAL
**Check ID**: B.2.2
**What**: Primary leverage measure
**Source**: Balance Sheet, Income Statement
**Calculate**: Total Debt / TTM EBITDA (or Adjusted EBITDA per credit agreement)

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| >6x | ðŸ”´ CRITICAL | F.9: 3 pts |
| 5-6x | ðŸ”´ HIGH | F.9: 2 pts |
| 4-5x | ðŸŸ¡ MODERATE | F.9: 1 pt |
| <4x | ðŸŸ¢ LOW | F.9: 0 pts |

---

### B.2.3: Debt/Equity Ratio
**Check ID**: B.2.3
**What**: Capital structure
**Source**: Balance Sheet
**Calculate**: Total Debt / Total Stockholders' Equity

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| >3x or negative equity | ðŸ”´ HIGH |
| 2-3x | ðŸŸ¡ MODERATE |
| <2x | ðŸŸ¢ LOW |

---

### B.2.4: Net Debt
**Check ID**: B.2.4
**What**: Debt net of cash
**Source**: Balance Sheet
**Calculate**: Total Debt - Cash - Marketable Securities

**Data to Collect**:
| Metric | Amount |
|--------|--------|
| Total Debt | $[X]M |
| Less: Cash | ($[X]M) |
| Less: Securities | ($[X]M) |
| **Net Debt** | $[X]M |
| Net Debt/EBITDA | [X.X]x |

---

### B.2.5: Interest Coverage Ratio
**Check ID**: B.2.5
**What**: Ability to service debt
**Source**: Income Statement
**Calculate**: EBIT / Interest Expense (or EBITDA / Interest for cash coverage)

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| <1.5x | ðŸ”´ CRITICAL |
| 1.5-2.5x | ðŸ”´ HIGH |
| 2.5-4x | ðŸŸ¡ MODERATE |
| >4x | ðŸŸ¢ LOW |

---

### B.2.6: Fixed Charge Coverage (DSCR)
**Check ID**: B.2.6
**What**: Broader debt service coverage including leases
**Source**: Income Statement, Lease footnote
**Calculate**: (EBITDA - CapEx) / (Interest + Principal Payments + Lease Payments)

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| <1.0x | ðŸ”´ CRITICAL |
| 1.0-1.5x | ðŸ”´ HIGH |
| 1.5-2.0x | ðŸŸ¡ MODERATE |
| >2.0x | ðŸŸ¢ LOW |

---

### B.2.7: Debt Maturity Schedule
**Check ID**: B.2.7
**What**: Refinancing risk
**Source**: Debt footnote (maturity table)
**Data to Collect**:
| Year | Principal Due | % of Total |
|------|--------------|------------|
| 2025 | $[X]M | [X]% |
| 2026 | $[X]M | [X]% |
| 2027 | $[X]M | [X]% |
| 2028+ | $[X]M | [X]% |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| >30% due <18 months with limited liquidity | ðŸ”´ CRITICAL |
| >20% due <18 months | ðŸ”´ HIGH |
| Significant due 18-36 months | ðŸŸ¡ MODERATE |
| Well-laddered | ðŸŸ¢ LOW |

---

### B.2.8: Floating Rate Exposure
**Check ID**: B.2.8
**What**: Interest rate risk
**Source**: Debt footnote
**Calculate**: Floating Rate Debt / Total Debt

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| >75% floating AND no hedges | ðŸ”´ HIGH |
| >50% floating, limited hedges | ðŸŸ¡ MODERATE |
| Hedged or mostly fixed | ðŸŸ¢ LOW |

---

### B.2.9: Covenant Identification (75A)
**Check ID**: B.2.9
**What**: Identify all financial covenants
**Source**: 10-K Debt footnote, Credit Agreement (8-K exhibit)
**Data to Collect**:
| Covenant | Test Level | Current | Cushion |
|----------|------------|---------|---------|
| Max Debt/EBITDA | [X.X]x | [X.X]x | [X]% |
| Min Interest Coverage | [X.X]x | [X.X]x | [X]% |
| Min Liquidity | $[X]M | $[X]M | [X]% |
| Max CapEx | $[X]M | $[X]M | [X]% |

---

### B.2.10: Covenant Cushion Analysis (75B) â­ CRITICAL
**Check ID**: B.2.10
**What**: How close to breach?
**Calculate**: (Current Level - Covenant Level) / Covenant Level Ã— 100

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Currently in breach | ðŸ”´ CRITICAL | F.9: 4 pts |
| Cushion <10% | ðŸ”´ HIGH | F.9: 3 pts |
| Cushion 10-25% | ðŸŸ¡ MODERATE | F.9: 1 pt |
| Cushion >25% | ðŸŸ¢ LOW | F.9: 0 pts |

---

### B.2.11: Covenant Trajectory (75C)
**Check ID**: B.2.11
**What**: Is cushion improving or deteriorating?
**Source**: Compare 4 quarters of covenant compliance
**Data to Collect**:
| Quarter | Debt/EBITDA | Cushion | Trend |
|---------|-------------|---------|-------|
| Q4 | [X.X]x | [X]% | |
| Q3 | [X.X]x | [X]% | |
| Q2 | [X.X]x | [X]% | |
| Q1 | [X.X]x | [X]% | |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Cushion deteriorating >10% per quarter | ðŸ”´ HIGH |
| Cushion stable | ðŸŸ¡ MODERATE |
| Cushion improving | ðŸŸ¢ LOW |

---

### B.2.12: EBITDA Quality Check (75D)
**Check ID**: B.2.12
**What**: Is covenant EBITDA artificially inflated?
**Source**: Credit Agreement EBITDA definition, 10-Q adjustments
**Calculate**: Credit Agreement EBITDA / GAAP Net Income

**Common Addbacks to Flag**:
- Stock compensation
- One-time costs (verify truly one-time)
- Pro forma synergies
- Normalized adjustments

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Adjusted EBITDA >2x GAAP Net Income | ðŸ”´ HIGH |
| Unusual addbacks >30% of EBITDA | ðŸ”´ HIGH |
| Moderate adjustments | ðŸŸ¡ MODERATE |
| Minimal adjustments | ðŸŸ¢ LOW |

---

### B.2.13: Covenant Holiday/Amendment History (75E)
**Check ID**: B.2.13
**What**: Prior amendments signal stress
**Source**: 8-K filings, Credit Agreement amendments
**Data to Collect**:
| Date | Amendment | Impact |
|------|-----------|--------|
| [Date] | [Type] | [Covenant change] |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Covenant waiver <12 months | ðŸ”´ HIGH |
| Amendment loosening covenants <24 months | ðŸŸ¡ MODERATE |
| No amendments needed | ðŸŸ¢ LOW |

---

### B.2.14: Liquidity vs. Maturity Analysis (75F)
**Check ID**: B.2.14
**What**: Can they fund near-term maturities?
**Calculate**: (Cash + Revolver Availability + Expected OCF) vs. (Maturities <24 months)

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Available < 100% of maturities | ðŸ”´ CRITICAL |
| Available 100-150% | ðŸ”´ HIGH |
| Available 150-200% | ðŸŸ¡ MODERATE |
| Available >200% | ðŸŸ¢ LOW |

---

### B.2.15: Secured vs. Unsecured
**Check ID**: B.2.15
**What**: Security interest priority
**Source**: Debt footnote
**Calculate**: Secured Debt / Total Debt

---

### B.2.16: Subordination Structure
**Check ID**: B.2.16
**What**: Priority waterfall
**Source**: Credit Agreement
**Data to Collect**:
- First lien amount: $[X]M
- Second lien amount: $[X]M
- Unsecured amount: $[X]M
- Sub debt amount: $[X]M

---

### B.2.17: Cross-Default Provisions
**Check ID**: B.2.17
**What**: Does breach in one facility trigger others?
**Source**: Credit Agreement
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Extensive cross-defaults + tight covenants | ðŸ”´ HIGH |
| Standard cross-defaults | ðŸŸ¡ MODERATE |

---

### B.2.18: Change of Control Provisions
**Check ID**: B.2.18
**What**: M&A could trigger debt acceleration
**Source**: Credit Agreement, Indentures

---

### B.2.19: Pension/OPEB Obligations
**Check ID**: B.2.19
**What**: Unfunded retirement obligations
**Source**: 10-K Pension footnote
**Calculate**: Funded Status = Plan Assets - PBO
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Unfunded >25% of market cap | ðŸ”´ HIGH |
| Unfunded 10-25% | ðŸŸ¡ MODERATE |
| Fully funded or minimal | ðŸŸ¢ LOW |

---

### B.2.20: Operating Lease Obligations
**Check ID**: B.2.20
**What**: Lease liability burden
**Source**: Lease footnote
**Calculate**: Lease Liability / EBITDA
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Lease obligations >3x EBITDA | ðŸ”´ HIGH |
| 1-3x EBITDA | ðŸŸ¡ MODERATE |
| <1x | ðŸŸ¢ LOW |

---

## B.3: PROFITABILITY (Checks B.3.1 - B.3.14)

### B.3.1: Revenue Trend
**Check ID**: B.3.1
**What**: Top-line growth/decline
**Source**: Income Statement
**Data to Collect**:
| Period | Revenue | YoY Change |
|--------|---------|------------|
| TTM | $[X]M | [X]% |
| Prior Year | $[X]M | [X]% |
| 2 Years Ago | $[X]M | [X]% |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Declining >20% YoY | ðŸ”´ HIGH |
| Declining 10-20% | ðŸŸ¡ MODERATE |
| Flat to declining <10% | ðŸŸ¡ MODERATE |
| Growing | ðŸŸ¢ LOW |

---

### B.3.2: Revenue Quality
**Check ID**: B.3.2
**What**: Recurring vs. one-time revenue
**Source**: Revenue footnote, MD&A
**Data to Collect**:
| Type | Amount | % of Total |
|------|--------|------------|
| Recurring/Subscription | $[X]M | [X]% |
| License/One-time | $[X]M | [X]% |
| Services | $[X]M | [X]% |

---

### B.3.3: Gross Margin
**Check ID**: B.3.3
**What**: Unit economics
**Source**: Income Statement
**Calculate**: (Revenue - COGS) / Revenue
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Gross margin compression >500 bps YoY | ðŸ”´ HIGH |
| Compression 200-500 bps | ðŸŸ¡ MODERATE |
| Stable or expanding | ðŸŸ¢ LOW |

---

### B.3.4: Operating Margin
**Check ID**: B.3.4
**What**: Core business profitability
**Source**: Income Statement
**Calculate**: Operating Income / Revenue

---

### B.3.5: Net Margin
**Check ID**: B.3.5
**What**: Bottom-line profitability
**Source**: Income Statement
**Calculate**: Net Income / Revenue

---

### B.3.6: EBITDA Margin
**Check ID**: B.3.6
**What**: Cash generation proxy
**Calculate**: EBITDA / Revenue

---

### B.3.7: Revenue Volatility â­ HIGH PREDICTIVE
**Check ID**: B.3.7
**What**: Predictability of revenue
**Source**: Past 12 quarters
**Calculate**: Standard deviation of quarterly revenue growth rates

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Std dev >15% + negative trend | ðŸ”´ CRITICAL |
| Std dev 10-15% | ðŸ”´ HIGH |
| Std dev 5-10% | ðŸŸ¡ MODERATE |
| Std dev <5% | ðŸŸ¢ LOW |

---

### B.3.8: Path to Profitability
**Check ID**: B.3.8
**What**: For unprofitable companies, when will they be profitable?
**Source**: Management guidance, analyst estimates
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| No clear path, increasing losses | ðŸ”´ HIGH |
| Losses narrowing, path visible | ðŸŸ¡ MODERATE |
| Already profitable | ðŸŸ¢ LOW |

---

### B.3.9-B.3.14: Margin Trend Analysis
Track gross, operating, and net margin trends over 8 quarters to identify deterioration patterns.

---

## B.4: CASH FLOW (Checks B.4.1 - B.4.8)

### B.4.1: Operating Cash Flow â­ CRITICAL
**Check ID**: B.4.1
**What**: Core business cash generation
**Source**: Cash Flow Statement
**Data to Collect**:
| Period | OCF | Net Income | Quality (OCF/NI) |
|--------|-----|------------|------------------|
| TTM | $[X]M | $[X]M | [X.X]x |
| Prior | $[X]M | $[X]M | [X.X]x |

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Negative OCF 4+ consecutive quarters | ðŸ”´ HIGH | F.9: 3 pts |
| Negative OCF <4 quarters | ðŸŸ¡ MODERATE | F.9: 1 pt |
| Positive, declining | ðŸŸ¡ MODERATE | |
| Positive, growing | ðŸŸ¢ LOW | F.9: 0 pts |

---

### B.4.2: Free Cash Flow
**Check ID**: B.4.2
**What**: Cash available after maintenance
**Calculate**: OCF - CapEx
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Persistent negative FCF | ðŸ”´ HIGH |
| Negative but improving | ðŸŸ¡ MODERATE |
| Positive | ðŸŸ¢ LOW |

---

### B.4.3: Cash vs Earnings Quality
**Check ID**: B.4.3
**What**: Divergence indicates manipulation
**Calculate**: Compare Net Income to OCF over 8 quarters
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| OCF << Net Income multiple periods | ðŸ”´ HIGH |
| Temporary divergence explained | ðŸŸ¡ MODERATE |
| OCF tracks Net Income | ðŸŸ¢ LOW |

---

### B.4.4: CapEx Intensity
**Check ID**: B.4.4
**What**: Capital requirements
**Calculate**: CapEx / Revenue

---

### B.4.5: Working Capital Changes
**Check ID**: B.4.5
**What**: Cash trapped in working capital
**Source**: Cash Flow Statement - Changes in WC section

---

### B.4.6: Dividend/Buyback Sustainability
**Check ID**: B.4.6
**What**: Are shareholder returns sustainable?
**Calculate**: (Dividends + Buybacks) / FCF
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| >120% of FCF funded by debt | ðŸ”´ HIGH |
| 80-120% | ðŸŸ¡ MODERATE |
| <80% | ðŸŸ¢ LOW |

---

### B.4.7-B.4.8: Cash Conversion Cycle
Analyze DSO, DIO, DPO for working capital efficiency.

---

## B.5: STOCK PERFORMANCE (Checks B.5.1 - B.5.12) â­ CRITICAL SECTION

### B.5.1: Stock Price Analysis â­ HIGH PREDICTIVE
**Check ID**: B.5.1
**What**: Decline severity
**Source**: Yahoo Finance
**Data to Collect**:
| Metric | Value | Date |
|--------|-------|------|
| Current Price | $[X] | [Date] |
| 52-Week High | $[X] | [Date] |
| 52-Week Low | $[X] | [Date] |
| **Decline from High** | [X]% | Calculated |
| Market Cap | $[X]M | |

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| >60% decline | ðŸ”´ CRITICAL | F.2: 15 pts |
| 50-60% | ðŸ”´ HIGH | F.2: 12 pts |
| 40-50% | ðŸŸ¡ HIGH | F.2: 9 pts |
| 30-40% | ðŸŸ¡ MODERATE | F.2: 6 pts |
| 20-30% | ðŸŸ¡ MODERATE | F.2: 3 pts |
| <20% | ðŸŸ¢ LOW | F.2: 0 pts |

---

### B.5.2: Attribution Analysis â­ REQUIRED IF DECLINE >10%
**Check ID**: B.5.2
**What**: Company-specific vs. sector-wide decline
**Source**: Yahoo Finance - compare to sector ETF
**Calculate**: Company decline - Sector ETF decline

**Data to Collect**:
| Metric | Company | Sector ETF | Difference |
|--------|---------|------------|------------|
| 12-Month Return | [X]% | [X]% | [X]% |
| 6-Month Return | [X]% | [X]% | [X]% |
| 3-Month Return | [X]% | [X]% | [X]% |
| **Company-Specific** | | | [X]% |

**Classification**:
- **Company-Specific**: Underperformed sector by >20 percentage points â†’ +3 F.2 bonus
- **Sector-Wide**: Tracked sector within 10 percentage points
- **Macro-Driven**: All markets down similarly

---

### B.5.3: Peer Comparison
**Check ID**: B.5.3
**What**: Performance vs. direct competitors
**Source**: Yahoo Finance
**Data to Collect**:
| Company | 12-Month | 6-Month | Assessment |
|---------|----------|---------|------------|
| [Company] | [X]% | [X]% | Target |
| [Peer 1] | [X]% | [X]% | |
| [Peer 2] | [X]% | [X]% | |
| [Peer 3] | [X]% | [X]% | |
| **Sector ETF** | [X]% | [X]% | Benchmark |

---

### B.5.4: Volatility (90-Day) â­ HIGH PREDICTIVE
**Check ID**: B.5.4
**What**: Stock price variability
**Source**: Yahoo Finance historical data
**Calculate**: Standard deviation of 90 daily returns

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| >8% | ðŸ”´ HIGH | F.8: 7 pts |
| 6-8% | ðŸŸ¡ MODERATE | F.8: 5 pts |
| 4-6% | ðŸŸ¡ MODERATE | F.8: 3 pts |
| 2-4% | ðŸŸ¢ LOW | F.8: 1 pt |
| <2% | ðŸŸ¢ LOW | F.8: 0 pts |

---

### B.5.5: Beta
**Check ID**: B.5.5
**What**: Market sensitivity
**Source**: Yahoo Finance (5-year monthly)
**Thresholds**:
| Condition | Score Impact |
|-----------|--------------|
| Beta >2.5 | F.8: +2 pts bonus |
| Beta <2.5 | No bonus |

---

### B.5.6: Single-Day Drop Analysis
**Check ID**: B.5.6
**What**: Significant one-day declines
**Source**: Yahoo Finance historical
**Data to Collect**:
| Date | Drop | Trigger | Company-Specific? |
|------|------|---------|-------------------|
| [Date] | -[X]% | [Event] | [Yes/No] |

**Count drops >5% and >10% in past 12 months**

---

### B.5.7-B.5.12: Detailed Attribution for Each Major Drop
For each drop >10% in past 24 months, complete full attribution analysis including:
- Trigger event
- Sector performance same day
- Peer performance same day
- Disclosure quality assessment
- Litigation status (filed or statute open)

---

## B.6: ACCOUNTING QUALITY (Checks B.6.1 - B.6.12)

### B.6.1: Revenue Recognition
**Check ID**: B.6.1
**What**: Revenue recognition complexity and changes
**Source**: 10-K Note 2 (Summary of Significant Accounting Policies)
**Red Flags**:
- Multiple element arrangements
- Percentage of completion
- Variable consideration estimates
- Recent policy changes
- ASC 606 transition issues

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Complex + changes + increasing DSO | ðŸ”´ HIGH |
| Some complexity | ðŸŸ¡ MODERATE |
| Straightforward | ðŸŸ¢ LOW |

---

### B.6.2: Receivables Quality (DSO)
**Check ID**: B.6.2
**What**: Rising A/R relative to sales
**Source**: Balance Sheet
**Calculate**: (Accounts Receivable / Revenue) Ã— 365

**Track 4 quarters**:
| Quarter | DSO | Trend |
|---------|-----|-------|
| Current | [X] days | |
| Q-1 | [X] days | |
| Q-2 | [X] days | |
| Q-3 | [X] days | |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| DSO increasing >20% YoY | ðŸ”´ HIGH |
| DSO increasing 10-20% | ðŸŸ¡ MODERATE |
| Stable or improving | ðŸŸ¢ LOW |

---

### B.6.3: Allowance for Doubtful Accounts
**Check ID**: B.6.3
**What**: Adequacy of reserve
**Source**: A/R footnote
**Calculate**: Allowance / Gross A/R

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Allowance decreasing + DSO increasing | ðŸ”´ HIGH |
| Low allowance <2% + customer concentration | ðŸ”´ HIGH |
| Normal allowance | ðŸŸ¢ LOW |

---

### B.6.4: Inventory Quality
**Check ID**: B.6.4
**What**: Inventory buildup indicates demand problems
**Source**: Balance Sheet, Inventory footnote
**Calculate**: Days Inventory Outstanding = (Inventory / COGS) Ã— 365

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| DIO growing faster than sales + write-downs | ðŸ”´ HIGH |
| Growth with explanation | ðŸŸ¡ MODERATE |
| Stable | ðŸŸ¢ LOW |

---

### B.6.5: Goodwill Impairment Risk
**Check ID**: B.6.5
**What**: Failed acquisitions
**Source**: 10-K goodwill footnote
**Calculate**: Goodwill / Total Equity

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| High % + stock below deal value + impairment risk | ðŸ”´ HIGH |
| High but healthy headroom | ðŸŸ¡ MODERATE |
| Modest or robust headroom | ðŸŸ¢ LOW |

---

### B.6.6: Deferred Revenue Changes
**Check ID**: B.6.6
**What**: Pulling forward revenue
**Source**: Balance Sheet
**Red Flag**: Deferred revenue declining while recognized revenue grows

---

### B.6.7: Accrual vs. Cash Accounting
**Check ID**: B.6.7
**What**: Earnings quality assessment
**Calculate**: Accruals = Net Income - OCF

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Persistent high accruals (>10% of assets) | ðŸ”´ HIGH |
| Moderate accruals | ðŸŸ¡ MODERATE |
| Cash-based earnings | ðŸŸ¢ LOW |

---

### B.6.8: Related Party Transactions
**Check ID**: B.6.8
**What**: Potential conflicts
**Source**: 10-K Related Party footnote, DEF 14A
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Material without clear business purpose | ðŸ”´ HIGH |
| Properly disclosed and approved | ðŸŸ¡ MODERATE |
| None material | ðŸŸ¢ LOW |

---

### B.6.9: Auditor Assessment
**Check ID**: B.6.9
**What**: Auditor quality and continuity
**Source**: 10-K auditor's report
**Data to Collect**:
- Auditor name: [Name]
- Big 4: [Yes/No]
- Tenure: [X] years
- Opinion type: [Unqualified/Qualified/Adverse]

---

### B.6.10-B.6.12: Additional Accounting Quality Checks
- Off-balance sheet arrangements
- Special purpose entities
- Segment reporting changes

---

## B.7: INDUSTRY-SPECIFIC KPIs (Checks B.7.1 - B.7.24)

### B.7.1: SaaS/Software Metrics (6 checks)

**B.7.1.1: Annual Recurring Revenue (ARR)**
**Calculate**: MRR Ã— 12
**Growth rate**: [X]% YoY

**B.7.1.2: Net Revenue Retention (NRR)**
**What**: Expansion - Churn
**Target**: >120% excellent, >100% good

**B.7.1.3: Gross Revenue Retention**
**What**: Before expansion
**Target**: >90%

**B.7.1.4: Customer Churn Rate**
**Calculate**: Churned customers / Starting customers

**B.7.1.5: CAC Payback Period**
**Calculate**: S&M / New ARR
**Target**: <18 months

**B.7.1.6: Rule of 40**
**Calculate**: Revenue growth % + EBITDA margin %
**Target**: >40%

---

### B.7.2: Life Sciences Metrics (6 checks)

**B.7.2.1: Pipeline Stage Analysis**
| Drug | Phase | Indication | FDA Date | Probability |
|------|-------|------------|----------|-------------|

**B.7.2.2: Cash Runway to Data**
**Calculate**: Can they fund to next catalyst?

**B.7.2.3: FDA Status**
- Pending decisions: [List]
- Recent CRLs: [List]
- Inspection status: [Clean/483s]

**B.7.2.4: Patent Cliff**
- Key patents expiring: [Dates]
- Revenue at risk: $[X]M

**B.7.2.5: Partner Milestones**
- Upcoming milestones: [List]

**B.7.2.6: Clinical Trial Risk**
- Enrollment status: [On track/Delayed]
- Site issues: [Any]

---

### B.7.3: Financial Services Metrics (6 checks)

**B.7.3.1: Capital Ratios**
- CET1: [X]% (min [X]%)
- Total Capital: [X]%
- Leverage: [X]%

**B.7.3.2: Non-Performing Loans (NPL)**
**Calculate**: NPLs / Total Loans
**Trend**: [Improving/Stable/Deteriorating]

**B.7.3.3: Net Interest Margin (NIM)**
**Trend over 8 quarters**

**B.7.3.4: Loan Loss Reserves**
**Calculate**: Reserves / NPLs

**B.7.3.5: Regulatory Exam Status**
- Last exam: [Date]
- MRAs/MRIAs: [Count]

**B.7.3.6: Credit Quality Trends**
- 30-day delinquencies
- Charge-off rate

---

### B.7.4: Retail Metrics (6 checks)

**B.7.4.1: Comparable Store Sales**
| Quarter | Comp Sales | Traffic | Ticket |
|---------|------------|---------|--------|

**B.7.4.2: Inventory Turn**
**Calculate**: COGS / Average Inventory

**B.7.4.3: E-commerce Mix**
- Online % of sales: [X]%
- Digital growth: [X]%

**B.7.4.4: Store Count Trends**
- Opens: [X]
- Closes: [X]
- Net: [X]

**B.7.4.5: Customer Metrics**
- Traffic trends
- Loyalty program stats

**B.7.4.6: Gross Margin by Channel**

---

## B.8: GUIDANCE TRACK RECORD (Checks B.8.1 - B.8.6) â­ HIGH PREDICTIVE

### B.8.1: Guidance Miss Count
**Check ID**: B.8.1
**What**: Frequency of missed guidance
**Source**: Past 8 quarters 8-K earnings releases vs. prior guidance
**Data to Collect**:
| Quarter | Guided Revenue | Actual | Miss % | Guided EPS | Actual | Miss % |
|---------|----------------|--------|--------|------------|--------|--------|

**Calculate**: Misses / 8 quarters

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| 4+ misses | ðŸ”´ HIGH | F.5: 8 pts |
| 3 misses | ðŸŸ¡ HIGH | F.5: 6 pts |
| 2 misses | ðŸŸ¡ MODERATE | F.5: 4 pts |
| 1 miss | ðŸŸ¢ LOW | F.5: 2 pts |
| 0 misses | ðŸŸ¢ LOW | F.5: 0 pts |

---

### B.8.2: Average Miss Magnitude
**Check ID**: B.8.2
**Calculate**: Average % miss across missed quarters
**Bonus**: Any miss >15% â†’ F.5: +2 pts

---

### B.8.3: Stock Impact of Misses
**Check ID**: B.8.3
**What**: Market reaction to each miss
**Calculate**: 5-day stock return after each miss

---

### B.8.4: Guidance Credibility Pattern
**Check ID**: B.8.4
**What**: Systematic over-promising?
**Assess**: Are misses getting larger? Multiple consecutive?

---

### B.8.5: Guidance Changes
**Check ID**: B.8.5
**What**: Withdrawn or lowered guidance
**Red Flag**: Guidance pulled entirely

---

### B.8.6: Guidance vs. Street
**Check ID**: B.8.6
**What**: How does guidance compare to analyst consensus?
**Assess**: Sandbagging vs. aggressive guidance

---

## SECTION B CHECKPOINT OUTPUT

```
## SECTION B RESULTS - [COMPANY NAME]

| Check | Description | Finding | Severity | Source |
|-------|-------------|---------|----------|--------|
| B.1.1 | Cash Runway | [X] months | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | [10-Q p.X] |
| B.2.2 | Debt/EBITDA | [X.X]x | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | [Calculated] |
| B.5.1 | Stock Decline | [X]% | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | [Yahoo Finance] |
...

### SUMMARY
- **RED FLAGS**: X/112
- **YELLOW FLAGS**: X/112

### SCORE IMPACTS
- **F.2 Stock Decline**: [X]/15 points
- **F.5 Guidance Miss**: [X]/8 points
- **F.8 Volatility**: [X]/7 points
- **F.9 Financial Distress**: [X]/6 points
```

---

**END OF SECTION B**
