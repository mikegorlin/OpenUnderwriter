# SECTION G: PRIOR ACTS & PROSPECTIVE RISK
## 85 Checks | MANDATORY when: Active claim exists, Runoff transaction, OR elevated forward risk

---

## G.1: STOCK DROP ANALYSIS - DETAILED (19 checks)

### G.1.1: 52-Week Decline from High â­ HIGH PREDICTIVE VALUE
- **What**: Total decline magnitude
- **Source**: Yahoo Finance
- **Calculate**: (52-week high - Current) / 52-week high Ã— 100
- **Threshold**:
  - ðŸ”´ NUCLEAR: >70% (auto HIGH tier floor)
  - ðŸ”´ CRITICAL: >60% (feeds F.2: 15 pts)
  - ðŸ”´ HIGH: 50-60% (feeds F.2: 12 pts)
  - âš ï¸ MODERATE-HIGH: 40-50% (feeds F.2: 9 pts)
  - âš ï¸ MODERATE: 30-40% (feeds F.2: 6 pts)
  - âš ï¸ LOW-MOD: 20-30% (feeds F.2: 3 pts)
  - âœ… LOW: <20% (feeds F.2: 0 pts)
- **Score Impact**: Feeds F.2 Stock Decline Score

### G.1.2: Attribution Analysis - Sector Comparison
- **What**: Company vs sector performance
- **Source**: Sector ETF (see ETF table)
- **Calculate**: Company return - Sector ETF return
- **Threshold**:
  - ðŸ”´ CRITICAL: Underperformed sector by >30 pts (company-specific)
  - ðŸ”´ HIGH: Underperformed by 20-30 pts (+3 to F.2)
  - âš ï¸ MODERATE: Underperformed by 10-20 pts
  - âœ… LOW: Within 10 pts of sector (sector-driven)
- **Score Impact**: +3 to F.2 if company-specific >20 pts

### G.1.3: Attribution Analysis - Peer Comparison
- **What**: Company vs direct peers
- **Source**: 3-5 direct competitors
- **Calculate**: Company return vs average peer return
- **Document**: Each peer with ticker and return

### G.1.4: Single-Day Drops >10% Count
- **What**: Number of major drops
- **Source**: Yahoo Finance historical
- **Threshold**:
  - ðŸ”´ CRITICAL: 3+ drops >10% in 12 months
  - ðŸ”´ HIGH: 2 drops >10%
  - âš ï¸ MODERATE: 1 drop >10%
  - âœ… LOW: No drops >10%

### G.1.4a: EVENT-WINDOW ANALYSIS â­ CRITICAL FOR LITIGATION ASSESSMENT

**Why This Matters**: Securities litigation is based on **cumulative declines over event windows**, not just single-day drops. Plaintiffs measure damages using 5-10+ day windows following corrective disclosures.

**For EACH material disclosure event in past 24 months:**

| Event Window | Company Return | Sector ETF Return | Sector-Adjusted Return | Peers Avg Return |
|--------------|----------------|-------------------|------------------------|------------------|
| Day 0 (event day) | [X]% | [X]% | [X]% | [X]% |
| Day 0-1 (2-day) | [X]% | [X]% | [X]% | [X]% |
| Day 0-5 (1-week) | [X]% | [X]% | [X]% | [X]% |
| Day 0-10 (2-week) | [X]% | [X]% | [X]% | [X]% |

**Calculation Method**:
```
Event Day = Day of 8-K filing or earnings release
Return = (Price at end of window - Price at close before event) / Price at close before event
Sector-Adjusted = Company return - Sector ETF return over same window
```

**Event Window Severity**:
| Sector-Adjusted Cumulative Decline | Severity | Litigation Risk |
|-----------------------------------|----------|-----------------|
| >30% over 10 days | ðŸ”´ CRITICAL | Very High - strong plaintiff case |
| 20-30% over 10 days | ðŸ”´ HIGH | High - likely actionable |
| 15-20% over 10 days | âš ï¸ MODERATE-HIGH | Moderate - depends on disclosure facts |
| 10-15% over 10 days | âš ï¸ MODERATE | Lower - may not attract plaintiffs |
| <10% over 10 days | âœ… LOW | Low - likely not actionable alone |

**Key Events to Analyze** (past 24 months):
1. Earnings misses vs guidance
2. Guidance reductions
3. Restatement announcements
4. FDA/regulatory news (if applicable)
5. Executive departures
6. Material contract losses
7. Cybersecurity incidents
8. Product recalls/failures

**Document Each Event**:
```
EVENT #1:
- Event Date: [Date]
- Event Type: [Earnings miss / Guidance cut / etc.]
- 8-K Filed: [Date, if applicable]
- Disclosure Summary: [What was announced]

Price Action:
- Pre-event close (T-1): $[X]
- Event day close (T+0): $[X] â†’ Day 0 return: [X]%
- T+5 close: $[X] â†’ 5-day return: [X]%
- T+10 close: $[X] â†’ 10-day return: [X]%

Sector Comparison (same windows):
- Sector ETF (T-1 to T+10): [X]%
- Company-specific decline: [X]% - [X]% = [X]%

Peer Comparison:
- Peer 1 ([Ticker]): [X]%
- Peer 2 ([Ticker]): [X]%
- Peer 3 ([Ticker]): [X]%

Attribution: [COMPANY-SPECIFIC / SECTOR-WIDE / MACRO]
Disclosure Adequacy: [Prior warnings? / Surprise? / Contradicted prior statements?]
Statute of Limitations: [Open until DATE / Expired / Litigation filed]
Assessment: [HIGH / MODERATE / LOW litigation risk]
```

**Pattern Analysis**:
- Multiple events with sector-adjusted declines >15%? â†’ ðŸ”´ CRITICAL (pattern of disclosure failures)
- Events cluster around earnings? â†’ Check guidance practices
- Events follow insider selling? â†’ ðŸ”´ CRITICAL (scienter indicator)

### G.1.4b: CUMULATIVE LOSS CALCULATION
- **What**: Total investor losses from all event windows
- **Calculate**: Sum of market cap losses across all material events
- **Document**:
  - Event 1 market cap loss: $[X]M
  - Event 2 market cap loss: $[X]M
  - Event 3 market cap loss: $[X]M
  - **Total potential damages**: $[X]M
- **Note**: Overlapping windows should not double-count losses

### G.1.4c: RECOVERY ANALYSIS
- **What**: Did stock recover after event windows?
- **Why It Matters**: Plaintiffs prefer no recovery (higher damages)
- **Calculate**: Current price vs post-event low
- **Threshold**:
  - ðŸ”´ HIGH: No meaningful recovery (within 10% of event low)
  - âš ï¸ MODERATE: Partial recovery (10-50% of decline recovered)
  - âœ… LOW: Full recovery (>50% of decline recovered)
- **What**: First major drop detailed analysis
- **Source**: Yahoo Finance, 8-K, news
- **Document**:
  - Date: [Date]
  - Magnitude: [X]% ($[A] â†’ $[B])
  - Market Cap Loss: $[X]M
  - Trigger Event: [Specific event]
  - Attribution: [Company-specific / Sector / Macro]
  - Disclosure Quality: [Adequate / Inadequate]
  - Prior Warning: [Y/N]
  - Litigation Filed: [Y/N] - If Y: [Case details]
  - Statute Open Until: [Date if no litigation]
- **Assessment**: [HIGH / MODERATE / LOW litigation risk]

### G.1.6: Drop #2 Analysis
- **Same format as G.1.5**

### G.1.7: Drop #3 Analysis
- **Same format as G.1.5**

### G.1.8: Drop #4 Analysis (if applicable)
- **Same format as G.1.5**

### G.1.9: Total Actionable Drops
- **What**: Drops >10% not covered by existing litigation
- **Calculate**: Sum of material drops with open statutes
- **Document**: Number and total market cap loss

### G.1.10: Volatility 90-Day â­ HIGH PREDICTIVE VALUE
- **What**: Stock price volatility
- **Source**: Yahoo Finance historical (90 trading days)
- **Calculate**: STDEV of daily returns
- **Threshold**:
  - ðŸ”´ HIGH: >8% std dev (feeds F.8: 7 pts)
  - âš ï¸ MODERATE-HIGH: 6-8% (feeds F.8: 5 pts)
  - âš ï¸ MODERATE: 4-6% (feeds F.8: 3 pts)
  - âš ï¸ LOW-MOD: 2-4% (feeds F.8: 1 pt)
  - âœ… LOW: <2% (feeds F.8: 0 pts)
- **Score Impact**: Feeds F.8 Volatility Score

### G.1.11: Volatility vs Sector
- **What**: Relative volatility
- **Source**: Same calculation for sector ETF
- **Calculate**: Company vol / Sector vol
- **Threshold**:
  - ðŸ”´ HIGH: >2x sector volatility
  - âš ï¸ MODERATE: 1.5-2x sector
  - âœ… LOW: <1.5x sector

### G.1.12: Beta Analysis â­
- **What**: Market sensitivity
- **Source**: Yahoo Finance (5-year monthly)
- **Threshold**:
  - ðŸ”´ HIGH: >2.5 (feeds F.8: +2 pts)
  - âš ï¸ MODERATE: 1.5-2.5
  - âœ… LOW: <1.5
- **Score Impact**: +2 to F.8 if beta >2.5

### G.1.13: Max Drawdown (12 months)
- **What**: Largest peak-to-trough decline
- **Source**: Yahoo Finance historical
- **Calculate**: Maximum decline from any high to subsequent low
- **Threshold**:
  - ðŸ”´ CRITICAL: >60%
  - ðŸ”´ HIGH: 40-60%
  - âš ï¸ MODERATE: 20-40%
  - âœ… LOW: <20%

### G.1.14: Recovery Analysis
- **What**: Has stock recovered from major drops?
- **Source**: Yahoo Finance
- **Threshold**:
  - ðŸ”´ HIGH: No recovery (still near lows)
  - âš ï¸ MODERATE: Partial recovery
  - âœ… LOW: Full recovery

### G.1.15: Volume During Drops
- **What**: Trading volume during major declines
- **Source**: Yahoo Finance volume data
- **Threshold**:
  - ðŸ”´ HIGH: Volume spike >5x average (panic selling)
  - âš ï¸ MODERATE: 2-5x average
  - âœ… LOW: Normal volume

### G.1.16: Drop Timing vs Disclosures
- **What**: Were drops before or after company disclosures?
- **Source**: 8-K filing dates vs stock drops
- **Threshold**:
  - ðŸ”´ CRITICAL: Major drop before 8-K (insider knowledge concern)
  - ðŸ”´ HIGH: Drop after guidance without warning
  - âš ï¸ MODERATE: Drop with 8-K disclosure
  - âœ… LOW: Normal market reaction

---

## G.2: EXISTING LITIGATION ANALYSIS (12 checks)

### G.2.1: Active Securities Class Actions
- **What**: Current SCA cases
- **Source**: Stanford SCAC, PACER
- **Document each case**:
  - Case Name
  - Court
  - Filing Date
  - Class Period Start
  - Class Period End
  - Lead Plaintiff
  - Allegations
  - Current Status
  - Motion to Dismiss outcome
  - Settlement if any
- **Assessment**: Coverage overlap with current policy

### G.2.2: Prior Securities Settlements â­ HIGH PREDICTIVE VALUE
- **What**: Historical settlement record
- **Source**: Stanford SCAC
- **Threshold**:
  - ðŸ”´ CRITICAL: Settlement <3 years (feeds F.1: 18 pts)
  - ðŸ”´ HIGH: Settlement 3-5 years (feeds F.1: 15 pts)
  - âš ï¸ MODERATE: Settlement 5-10 years (feeds F.1: 10 pts)
  - âœ… LOW: >10 years or none (feeds F.1: 0 pts)
- **Score Impact**: Feeds F.1 Prior Litigation Score

### G.2.3: Derivative Litigation
- **What**: Shareholder derivative suits
- **Source**: PACER, Delaware Chancery
- **Document each case**:
  - Case Name
  - Court
  - Filing Date
  - Allegations
  - Demand status
  - Current Status
- **Score Impact**: Feeds F.1 (6 pts if <5 years)

### G.2.4: SEC Enforcement History â­
- **What**: SEC actions
- **Source**: SEC.gov Litigation Releases
- **Threshold**:
  - ðŸ”´ CRITICAL: Active investigation/Wells Notice (NUCLEAR)
  - ðŸ”´ HIGH: Settlement <5 years (feeds F.1: 12 pts)
  - âš ï¸ MODERATE: Settlement 5-10 years
  - âœ… LOW: None
- **Score Impact**: Feeds F.1

### G.2.5: DOJ/Criminal History
- **What**: Criminal investigations/indictments
- **Source**: DOJ.gov, news
- **Threshold**:
  - ðŸ”´ NUCLEAR: Active criminal investigation
  - ðŸ”´ CRITICAL: Deferred prosecution <5 years
  - ðŸ”´ HIGH: Resolved criminal matter <5 years
  - âœ… LOW: None

### G.2.6: State AG Actions
- **What**: State attorney general investigations
- **Source**: State AG press releases
- **Document**: State, allegations, status, settlement

### G.2.7: Industry-Specific Regulatory History
- **What**: FDA, FTC, banking regulators, etc.
- **Source**: Respective agency databases
- **Document**: Agency, matter, status, penalty

### G.2.8: Class Period Coverage Analysis
- **What**: Are existing class periods covered by prior policy?
- **Source**: Litigation timeline vs policy periods
- **Document**: 
  - Existing class period: [Start] - [End]
  - Prior policy period: [Start] - [End]
  - Coverage determination: [Covered / Gap / Unclear]

### G.2.9: Settlement Adequacy Analysis
- **What**: Were prior settlements adequate?
- **Source**: Settlement amounts vs damages claimed
- **Threshold**:
  - ðŸ”´ HIGH: Settlement <10% of claimed damages
  - âš ï¸ MODERATE: 10-30% of claimed damages
  - âœ… LOW: >30% or adequate

### G.2.10: Related Party Litigation
- **What**: Suits involving insiders
- **Source**: Court records, 10-K
- **Document**: Party, allegations, status

### G.2.11: Books & Records Demands
- **What**: Section 220 demands
- **Source**: 10-K, court records
- **Threshold**:
  - ðŸ”´ HIGH: Active demand with broad scope
  - âš ï¸ MODERATE: Resolved demand
  - âœ… LOW: None

### G.2.12: Appraisal Litigation
- **What**: M&A appraisal proceedings
- **Source**: Delaware Chancery
- **Threshold**:
  - ðŸ”´ HIGH: Active appraisal <2 years
  - âš ï¸ MODERATE: Resolved appraisal
  - âœ… LOW: None

---

## G.3: PROSPECTIVE TRIGGERS (18 checks)

### G.3.1: Upcoming Earnings
- **What**: Next earnings date and expectations
- **Source**: Earnings calendar, analyst estimates
- **Document**:
  - Date: [Date]
  - Consensus EPS: $[X]
  - Consensus Revenue: $[X]
  - Whisper number: $[X]
  - Potential miss magnitude: [Assessment]
  - Stock impact if miss: [Estimate]
- **Risk**: [HIGH / MODERATE / LOW]

### G.3.2: Guidance Changes Expected
- **What**: Upcoming guidance revisions
- **Source**: Prior guidance, analyst commentary
- **Threshold**:
  - ðŸ”´ HIGH: Guidance cut likely
  - âš ï¸ MODERATE: Guidance uncertain
  - âœ… LOW: Guidance likely maintained/raised

### G.3.3: Pending FDA Decisions (Life Sciences)
- **What**: Regulatory decisions expected
- **Source**: ClinicalTrials.gov, company disclosures
- **Document each**:
  - Product/indication
  - Decision type (NDA, BLA, 510(k))
  - Expected date (PDUFA date)
  - Historical approval rate for indication
  - Stock impact if rejected: [Estimate]
- **Risk**: [HIGH / MODERATE / LOW]

### G.3.4: Clinical Trial Readouts
- **What**: Upcoming data releases
- **Source**: ClinicalTrials.gov, investor presentations
- **Document each**:
  - Trial name
  - Phase
  - Indication
  - Expected readout
  - Binary vs continuous outcome
  - Stock impact if failed: [Estimate]

### G.3.5: Patent Expirations
- **What**: Key patent cliff dates
- **Source**: Patent filings, 10-K
- **Document**:
  - Patent/product
  - Expiration date
  - Revenue at risk: $[X]M ([X]% of total)
  - Generic competition expected: [Y/N]

### G.3.6: Contract Renewals
- **What**: Major customer/supplier contracts expiring
- **Source**: 10-K, 8-K
- **Document**:
  - Customer/supplier
  - Current revenue/cost: $[X]M
  - Expiration date
  - Renewal risk: [HIGH / MODERATE / LOW]

### G.3.7: Debt Maturities
- **What**: Upcoming refinancing needs
- **Source**: 10-K debt footnotes
- **Document**:
  - Amount: $[X]M
  - Maturity date
  - Refinancing plan: [Y/N]
  - Risk if unable to refinance

### G.3.8: Regulatory Deadlines
- **What**: Compliance deadlines
- **Source**: Regulatory filings
- **Document**: Deadline, requirement, penalty for non-compliance

### G.3.9: Legal Proceedings Timeline
- **What**: Upcoming court dates
- **Source**: Court dockets
- **Document**:
  - Case
  - Event (motion hearing, trial, etc.)
  - Date
  - Potential outcome and impact

### G.3.10: Activist Campaign Milestones
- **What**: Proxy season, board elections
- **Source**: Proxy filings, activist communications
- **Document**: Dates, demands, expected outcomes

### G.3.11: Product Launch Dates
- **What**: Scheduled product introductions
- **Source**: Company announcements
- **Document**:
  - Product
  - Launch date
  - Revenue expectation: $[X]M
  - Delay risk and impact

### G.3.12: Restructuring Milestones
- **What**: Scheduled cost savings realization
- **Source**: 8-K, earnings calls
- **Document**:
  - Program
  - Expected completion
  - Savings target: $[X]M
  - Risk of miss

### G.3.13: Acquisition Closing Dates
- **What**: Pending M&A completion
- **Source**: 8-K, merger agreements
- **Document**:
  - Target/transaction
  - Expected close
  - Regulatory approvals needed
  - Break fee if failed

### G.3.14: Divestiture Dates
- **What**: Scheduled asset sales
- **Source**: 8-K, company announcements
- **Document**:
  - Asset/business
  - Expected close
  - Expected proceeds: $[X]M
  - Risk of failed sale

### G.3.15: Credit Rating Reviews
- **What**: Scheduled rating actions
- **Source**: Rating agency announcements
- **Document**:
  - Agency
  - Review date
  - Current rating
  - Expected direction

### G.3.16: Index Inclusion/Exclusion
- **What**: Potential index changes
- **Source**: Index methodology, market cap changes
- **Threshold**:
  - ðŸ”´ HIGH: Likely exclusion (forced selling)
  - âš ï¸ MODERATE: On bubble
  - âœ… LOW: Stable inclusion

### G.3.17: Lock-Up Expirations
- **What**: Insider selling restrictions ending
- **Source**: S-1, prospectus
- **Document**:
  - Expiration date
  - Shares released: [X]M
  - % of float
  - Expected selling pressure

### G.3.18: Warrant/Convert Exercises
- **What**: Dilution events
- **Source**: 10-K, warrant terms
- **Document**:
  - Exercise price
  - Shares if exercised: [X]M
  - In-the-money: [Y/N]
  - Dilution %

---

## G.4: DISCLOSURE GAP ANALYSIS (12 checks)

### G.4.1: Earnings Quality vs Disclosure
- **What**: Are earnings quality issues adequately disclosed?
- **Source**: Compare financials to MD&A
- **Threshold**:
  - ðŸ”´ HIGH: Material issues not discussed
  - âš ï¸ MODERATE: Vague disclosure
  - âœ… LOW: Adequate disclosure

### G.4.2: Risk Factor Currency
- **What**: Are risk factors updated for current issues?
- **Source**: Compare 10-K risk factors to actual events
- **Threshold**:
  - ðŸ”´ HIGH: Known issues not in risk factors
  - âš ï¸ MODERATE: Boilerplate risk factors
  - âœ… LOW: Tailored, current risk factors

### G.4.3: Forward-Looking Statement Support
- **What**: Are projections adequately cautioned?
- **Source**: Safe harbor language, guidance disclosures
- **Threshold**:
  - ðŸ”´ HIGH: Aggressive guidance without caveats
  - âš ï¸ MODERATE: Standard cautionary language
  - âœ… LOW: Robust cautionary disclosure

### G.4.4: Material Contract Disclosure
- **What**: Are key contracts properly filed?
- **Source**: Exhibit list vs. referenced agreements
- **Threshold**:
  - ðŸ”´ HIGH: Material contracts not filed
  - âš ï¸ MODERATE: Heavy redaction
  - âœ… LOW: Complete disclosure

### G.4.5: Related Party Transparency
- **What**: Full disclosure of insider transactions?
- **Source**: 10-K footnotes, proxy statement
- **Threshold**:
  - ðŸ”´ HIGH: Undisclosed material relationships
  - âš ï¸ MODERATE: Limited disclosure
  - âœ… LOW: Full transparency

### G.4.6: Segment Reporting Quality
- **What**: Sufficient operating segment detail?
- **Source**: 10-K segment disclosures
- **Threshold**:
  - ðŸ”´ HIGH: Aggregation obscures performance
  - âš ï¸ MODERATE: Limited segment detail
  - âœ… LOW: Clear segment breakdown

### G.4.7: Goodwill Impairment Testing Disclosure
- **What**: Adequate impairment testing transparency?
- **Source**: 10-K goodwill footnote
- **Threshold**:
  - ðŸ”´ HIGH: No cushion disclosure, assumptions unclear
  - âš ï¸ MODERATE: Limited sensitivity analysis
  - âœ… LOW: Full testing disclosure

### G.4.8: Off-Balance Sheet Disclosure
- **What**: Are OBS obligations clear?
- **Source**: 10-K contractual obligations table
- **Threshold**:
  - ðŸ”´ HIGH: Material OBS items not quantified
  - âš ï¸ MODERATE: Some disclosure gaps
  - âœ… LOW: Complete OBS disclosure

### G.4.9: Litigation Disclosure Completeness
- **What**: Are all material legal matters disclosed?
- **Source**: Compare 10-K to court records
- **Threshold**:
  - ðŸ”´ HIGH: Material litigation not disclosed
  - âš ï¸ MODERATE: Vague disclosure
  - âœ… LOW: Complete legal disclosure

### G.4.10: Revenue Recognition Policy Clarity
- **What**: Is revenue policy understandable?
- **Source**: 10-K Note 2
- **Threshold**:
  - ðŸ”´ HIGH: Complex/unclear policy
  - âš ï¸ MODERATE: Some complexity
  - âœ… LOW: Clear policy

### G.4.11: Cybersecurity Incident Disclosure
- **What**: Proper disclosure of cyber events?
- **Source**: 8-K Item 1.05, 10-K
- **Threshold**:
  - ðŸ”´ HIGH: Known incident not disclosed
  - âš ï¸ MODERATE: Delayed disclosure
  - âœ… LOW: Timely disclosure or N/A

### G.4.12: Management Discussion Quality
- **What**: Does MD&A provide real insight?
- **Source**: 10-K MD&A section
- **Threshold**:
  - ðŸ”´ HIGH: Boilerplate, no real analysis
  - âš ï¸ MODERATE: Limited insight
  - âœ… LOW: Candid, insightful discussion

---

## G.5: INSIDER TRADING DEEP DIVE (12 checks)

### G.5.1: Net Insider Position (6 months) â­ HIGH PREDICTIVE VALUE
- **What**: Total insider buying vs selling
- **Source**: Form 4 filings (cite accession #)
- **Calculate**: Sum of all purchases - Sum of all sales
- **Threshold**:
  - ðŸ”´ CRITICAL: >$50M net selling (feeds F.7: 8 pts)
  - ðŸ”´ HIGH: $25-50M net selling (feeds F.7: 6 pts)
  - âš ï¸ MODERATE: $10-25M net selling (feeds F.7: 4 pts)
  - âš ï¸ LOW-MOD: $5-10M net selling (feeds F.7: 2 pts)
  - âœ… LOW: <$5M selling or net buying (feeds F.7: 0 pts)
- **Score Impact**: Feeds F.7 Insider Trading Score

### G.5.2: CEO Trading Activity
- **What**: CEO specific trading
- **Source**: Form 4 filings
- **Document**:
  - Transactions: [Buy/Sell], [Shares], $[Value], [Date]
  - 10b5-1 plan: [Y/N]
  - % of holdings sold: [X]%
- **Threshold**:
  - ðŸ”´ CRITICAL: CEO sold >50% holdings (+3 to F.7)
  - ðŸ”´ HIGH: CEO heavy selling outside 10b5-1
  - âš ï¸ MODERATE: Normal plan sales
  - âœ… LOW: Holding or buying

### G.5.3: CFO Trading Activity
- **What**: CFO specific trading
- **Source**: Form 4 filings
- **Document**: Same as G.5.2
- **Threshold**: Same as G.5.2

### G.5.4: 10b5-1 Plan Analysis
- **What**: Are sales via pre-arranged plans?
- **Source**: Form 4 footnotes
- **Calculate**: % of sales via 10b5-1
- **Threshold**:
  - ðŸ”´ HIGH: <50% via 10b5-1 (+2 to F.7)
  - âš ï¸ MODERATE: 50-80% via 10b5-1
  - âœ… LOW: >80% via 10b5-1
- **Score Impact**: +2 to F.7 if significant sales outside plans

### G.5.5: Timing Analysis
- **What**: Sales timing vs disclosures
- **Source**: Form 4 dates vs 8-K dates
- **Threshold**:
  - ðŸ”´ CRITICAL: Heavy sales before negative news
  - ðŸ”´ HIGH: Sales pattern suggests knowledge
  - âš ï¸ MODERATE: Normal timing
  - âœ… LOW: No concerning patterns

### G.5.6: Director Trading
- **What**: Board member trading patterns
- **Source**: Form 4 filings
- **Document**: Material transactions by directors

### G.5.7: Section 16 Late Filings
- **What**: Late Form 4 filings
- **Source**: SEC EDGAR filing dates
- **Threshold**:
  - ðŸ”´ HIGH: Pattern of late filings
  - âš ï¸ MODERATE: Occasional late filing
  - âœ… LOW: Timely filings

### G.5.8: Derivative Transactions
- **What**: Options, RSU exercises
- **Source**: Form 4 Table II
- **Document**: Material derivative transactions

### G.5.9: Gift Transactions
- **What**: Insider gifts of stock
- **Source**: Form 4 gift codes
- **Threshold**:
  - ðŸ”´ HIGH: Large gifts before stock decline (tax strategy)
  - âš ï¸ MODERATE: Normal charitable giving
  - âœ… LOW: No material gifts

### G.5.10: Rule 144 Sales
- **What**: Unregistered share sales
- **Source**: Form 144 filings
- **Document**: Material Rule 144 sales

### G.5.11: Insider Pledging
- **What**: Shares pledged as collateral
- **Source**: DEF 14A beneficial ownership
- **Threshold**:
  - ðŸ”´ HIGH: Material shares pledged
  - âš ï¸ MODERATE: Some pledging
  - âœ… LOW: No pledging

### G.5.12: Insider Hedging
- **What**: Executive hedging activity
- **Source**: DEF 14A hedging policy
- **Threshold**:
  - ðŸ”´ HIGH: Hedging permitted, used by executives
  - âš ï¸ MODERATE: Hedging permitted, not used
  - âœ… LOW: Hedging prohibited

---

## G.6: RUNOFF-SPECIFIC ANALYSIS (12 checks)

*Use this section only for RUNOFF transactions*

### G.6.1: Transaction Structure
- **What**: M&A deal mechanics
- **Source**: Merger agreement (8-K exhibit)
- **Document**:
  - Buyer
  - Deal value
  - Structure (cash/stock/mix)
  - Premium to unaffected price
  - Expected close date

### G.6.2: Rep & Warranty Survival
- **What**: How long do R&W survive closing?
- **Source**: Merger agreement
- **Document**:
  - General reps: [X] months
  - Fundamental reps: [X] months / Indefinite
  - Financial statement reps: [X] months
  - Tax reps: [X] months

### G.6.3: Indemnification Cap
- **What**: Maximum indemnification obligation
- **Source**: Merger agreement
- **Document**:
  - General cap: $[X]M ([X]% of deal)
  - Fundamental rep cap: [Amount or uncapped]
  - Per-claim deductible: $[X]

### G.6.4: Escrow/Holdback
- **What**: Funds held for indemnification
- **Source**: Merger agreement
- **Document**:
  - Escrow amount: $[X]M
  - Release schedule
  - Claim process

### G.6.5: R&W Insurance
- **What**: Is buyer obtaining RWI?
- **Source**: Deal announcements, merger agreement
- **Document**:
  - RWI obtained: [Y/N]
  - Policy limit: $[X]M
  - Retention: $[X]
  - Exclusions

### G.6.6: Known Issues Analysis
- **What**: Issues that may be excluded from coverage
- **Source**: Disclosure schedules, 10-K
- **Document**: Issues requiring exclusion

### G.6.7: Material Adverse Change Definition
- **What**: MAC definition scope
- **Source**: Merger agreement
- **Document**: MAC carve-outs, buyer's out

### G.6.8: Management Transition
- **What**: Key executives leaving/staying?
- **Source**: 8-K, deal announcements
- **Document**: Who's staying, employment agreements

### G.6.9: Post-Close Discovery Risk
- **What**: What buyer may discover post-close
- **Source**: Due diligence analysis
- **Assess**:
  - Financial statement issues likely to surface
  - Contract issues
  - Compliance gaps
  - Customer concentration surprises
  - Employee issues

### G.6.10: Appraisal Rights
- **What**: Shareholder appraisal availability
- **Source**: State law, merger agreement
- **Document**: Appraisal available: [Y/N], exercise threshold

### G.6.11: Shareholder Litigation Risk
- **What**: Deal-related litigation probability
- **Source**: Deal premium, process
- **Assess**:
  - Premium adequacy challenge
  - Process challenge (conflicts)
  - Disclosure challenge

### G.6.12: Tail Policy Needs
- **What**: Coverage continuation requirements
- **Source**: D&O program analysis
- **Document**:
  - Required tail period
  - Who purchases
  - Limit requirements

---

## SECTION G CHECKPOINT

**Complete this checkpoint before proceeding:**

```
SECTION G: PRIOR ACTS & PROSPECTIVE CHECKPOINT
==============================================
Company: [Name]
Completed: [Date/Time]
Transaction Type: [STANDARD / RUNOFF]

STOCK DROP ANALYSIS (G.1):
â–¡ G.1.1 52-Week Decline: [X]% â†’ F.2: [X] pts
â–¡ G.1.2 Attribution: [Company-Specific / Sector / Macro]
â–¡ G.1.3 Company-Specific Component: [X]%
â–¡ G.1.4 Single-Day Drops >10%: [Count]
â–¡ G.1.10 90-Day Volatility: [X]% â†’ F.8: [X] pts
â–¡ G.1.12 Beta: [X.XX]

DROP ANALYSIS SUMMARY:
| Drop | Date | Magnitude | Trigger | Attribution | Litigation |
|------|------|-----------|---------|-------------|------------|
| #1   |      |           |         |             |            |
| #2   |      |           |         |             |            |
| #3   |      |           |         |             |            |

EXISTING LITIGATION (G.2):
â–¡ G.2.1 Active SCAs: [Count]
â–¡ G.2.2 Prior Settlements: $[X]M, [X] years ago â†’ F.1: [X] pts
â–¡ G.2.4 SEC Enforcement: [Y/N]
â–¡ G.2.5 DOJ/Criminal: [Y/N]

PROSPECTIVE TRIGGERS (G.3):
â–¡ G.3.1 Next Earnings: [Date], Risk: [Assessment]
â–¡ G.3.3 FDA Decisions: [List or N/A]
â–¡ G.3.7 Debt Maturities: $[X]M by [Date]

DISCLOSURE QUALITY (G.4):
â–¡ G.4.1 Earnings Quality Disclosure: [Assessment]
â–¡ G.4.9 Litigation Disclosure: [Complete / Gaps]

INSIDER TRADING (G.5):
â–¡ G.5.1 Net Position (6mo): $[X]M [selling/buying] â†’ F.7: [X] pts
â–¡ G.5.2 CEO Activity: [Assessment]
â–¡ G.5.4 10b5-1 Usage: [X]%

[IF RUNOFF - SECTION G.6]:
â–¡ G.6.2 R&W Survival: [X] months
â–¡ G.6.3 Indemnification Cap: $[X]M
â–¡ G.6.5 R&W Insurance: [Y/N]
â–¡ G.6.9 Post-Close Discovery Risk: [Assessment]

SCORE IMPACTS:
- F.1 Prior Litigation: [X]/20 pts
- F.2 Stock Decline: [X]/15 pts
- F.7 Insider Trading: [X]/8 pts
- F.8 Volatility: [X]/7 pts
- Nuclear Triggers: [List or None]

RED FLAGS IDENTIFIED:
[List any ðŸ”´ findings]

PROCEED TO: [10_SCORING.md for final score calculation]
```

---

**END OF SECTION G**
