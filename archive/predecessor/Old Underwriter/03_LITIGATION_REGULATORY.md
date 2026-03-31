# SECTION A: LITIGATION & REGULATORY RISK
## 37 Checks

---

## A.1: COMPANY EVENT RISK (Checks A.1.1 - A.1.4)

### A.1.1: IPO Timing Risk
**Check ID**: A.1.1
**What**: Companies <3 years post-IPO have elevated litigation rates (~16%)
**Source**: S-1 filing date, 8-K IPO completion
**Data to Collect**:
- IPO date: [Date]
- Time since IPO: [X] months/years
- IPO price: $[X]
- Current price vs. IPO: [+/-X%]

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| IPO <18 months + stock down >40% | ðŸ”´ HIGH | F.4: 8 pts |
| IPO <18 months, stock stable | ðŸŸ¡ MODERATE | F.4: 5 pts |
| IPO 18-36 months | ðŸŸ¡ MODERATE | F.4: 3 pts |
| IPO >36 months | ðŸŸ¢ LOW | F.4: 0 pts |

---

### A.1.2: Recent Capital Raises
**Check ID**: A.1.2
**What**: Secondary offerings, debt issuances create disclosure liability
**Source**: 8-K, S-3 filings
**Data to Collect**:
| Date | Type | Amount | Stock Performance Since |
|------|------|--------|------------------------|
| [Date] | [Type] | $[X]M | [+/-X%] |

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Multiple offerings <12mo + stock down >20% | ðŸ”´ HIGH |
| Offerings <24mo, stock stable | ðŸŸ¡ MODERATE |
| No recent capital raises | ðŸŸ¢ LOW |

---

### A.1.3: SPAC Status â­ HIGH PREDICTIVE
**Check ID**: A.1.3
**What**: De-SPAC companies have ~60% litigation rate in first 3 years
**Source**: 8-K merger completion, S-4, original SPAC documents
**Data to Collect**:
- De-SPAC date: [Date]
- Original SPAC sponsor: [Name]
- SPAC projections at merger: [Revenue/EBITDA targets]
- Actual vs. projections: [Variance %]
- Stock at merger: $[X]
- Current stock: $[X] ([+/-X%])

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| SPAC <18mo + stock <$5 | ðŸ”´ NUCLEAR | F.4: 10 pts |
| SPAC <18mo + stock down >50% | ðŸ”´ HIGH | F.4: 10 pts |
| SPAC 18-36 months | ðŸŸ¡ MODERATE | F.4: 7 pts |
| SPAC >36 months, stable | ðŸŸ¢ LOW | F.4: 0 pts |
| Not a SPAC | ðŸŸ¢ LOW | F.4: 0 pts |

---

### A.1.4: Secondary Offering Timing
**Check ID**: A.1.4
**What**: Recent equity offerings create 10b-5 exposure
**Source**: S-3, 424B prospectus supplements
**Data to Collect**:
- Most recent offering date: [Date]
- Offering price: $[X]
- Current price: $[X] ([+/-X%])
- Insider participation: [Yes/No]

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Offering <12mo + stock down >30% | ðŸ”´ HIGH |
| Offering <12mo, stock down 10-30% | ðŸŸ¡ MODERATE |
| Offering >12mo or stock stable | ðŸŸ¢ LOW |

---

## A.2: SECURITIES LITIGATION HISTORY (Checks A.2.1 - A.2.5)

### A.2.1: Securities Class Actions â­ HIGH PREDICTIVE
**Check ID**: A.2.1
**What**: Prior securities litigation history
**Source**: Stanford SCAC (securities.stanford.edu), 10-K Item 3 Legal Proceedings
**Search Method**: 
1. Go to securities.stanford.edu
2. Search by ticker AND company name
3. Note all cases, class periods, status, settlements

**Data to Collect**:
| Case | Class Period | Status | Settlement | Lead Plaintiff |
|------|-------------|--------|------------|----------------|
| [Name] | [Start-End] | [Active/Settled/Dismissed] | $[X]M | [Name] |

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Active securities class action | ðŸ”´ NUCLEAR | F.1: 20 pts |
| Settled <3 years | ðŸ”´ HIGH | F.1: 18 pts |
| Settled 3-5 years | ðŸŸ¡ MODERATE | F.1: 15 pts |
| Settled 5-10 years | ðŸŸ¡ MODERATE | F.1: 10 pts |
| None (verified via Stanford SCAC) | ðŸŸ¢ LOW | F.1: 0 pts |

---

### A.2.2: Derivative Litigation
**Check ID**: A.2.2
**What**: Shareholder derivative suits indicate governance failures
**Source**: 10-K Legal Proceedings, PACER, Delaware Chancery Court
**Data to Collect**:
| Case | Filed | Status | Allegations |
|------|-------|--------|-------------|
| [Name] | [Date] | [Status] | [Brief] |

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Active derivative suit | ðŸ”´ HIGH | F.1: 6 pts |
| Demand refused <2 years | ðŸŸ¡ MODERATE | F.1: 4 pts |
| Settled <5 years | ðŸŸ¡ MODERATE | F.1: 3 pts |
| None | ðŸŸ¢ LOW | F.1: 0 pts |

---

### A.2.3: Employment/ERISA Class Actions
**Check ID**: A.2.3
**What**: Employment class actions (wage/hour, discrimination, ERISA)
**Source**: 10-K Legal Proceedings, PACER
**Data to Collect**:
- Active cases: [X]
- Class size: [X] employees
- Alleged damages: $[X]M

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active class action with material damages | ðŸ”´ HIGH |
| Settled <3 years, >$10M | ðŸŸ¡ MODERATE |
| None significant | ðŸŸ¢ LOW |

---

### A.2.4: Product Liability/Mass Tort
**Check ID**: A.2.4
**What**: Product liability or mass tort exposure
**Source**: 10-K Legal Proceedings, news
**Data to Collect**:
- MDL status: [Yes/No]
- Bellwether trial results: [If applicable]
- Settlement reserve: $[X]M
- Number of claims: [X]

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active MDL or mass tort | ðŸ”´ HIGH |
| Isolated product claims | ðŸŸ¡ MODERATE |
| None | ðŸŸ¢ LOW |

---

### A.2.5: Patent/IP Litigation
**Check ID**: A.2.5
**What**: Intellectual property disputes
**Source**: 10-K Legal Proceedings, USPTO, PACER
**Data to Collect**:
- Active patent cases: [X]
- Key patent expiration: [Date]
- Infringement allegations: [Plaintiff/Defendant]

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Defendant in significant IP suit | ðŸŸ¡ MODERATE |
| Plaintiff in IP suit | ðŸŸ¢ LOW |
| None | ðŸŸ¢ LOW |

---

## A.3: REGULATORY ENFORCEMENT (Checks A.3.1 - A.3.8)

### A.3.1: SEC Enforcement â­ HIGH PREDICTIVE
**Check ID**: A.3.1
**What**: SEC actions indicate securities violations
**Source**: SEC.gov Litigation Releases, 10-K
**Search Method**: sec.gov/litigation â†’ Litigation Releases â†’ Search company name

**Data to Collect**:
| Date | Action | Allegations | Resolution | Amount |
|------|--------|-------------|------------|--------|
| [Date] | [Type] | [Brief] | [Status] | $[X]M |

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Active investigation or Wells Notice | ðŸ”´ NUCLEAR | F.1: 20 pts |
| Settlement <3 years | ðŸ”´ HIGH | F.1: 12 pts |
| Settlement 3-5 years | ðŸŸ¡ MODERATE | F.1: 8 pts |
| None | ðŸŸ¢ LOW | F.1: 0 pts |

---

### A.3.2: DOJ/Criminal
**Check ID**: A.3.2
**What**: Criminal investigations create extreme exposure
**Source**: DOJ.gov press releases, 10-K Legal Proceedings
**Data to Collect**:
- Investigation status: [Active/Resolved/None]
- DPA/NPA status: [If applicable]
- Individual indictments: [Names]

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active investigation or indictment | ðŸ”´ NUCLEAR |
| DPA active | ðŸ”´ HIGH |
| Resolved <5 years | ðŸŸ¡ MODERATE |
| None | ðŸŸ¢ LOW |

---

### A.3.3: FCPA/International Corruption
**Check ID**: A.3.3
**What**: Foreign Corrupt Practices Act exposure
**Source**: DOJ FCPA database (justice.gov/criminal-fraud/fcpa), SEC releases
**Data to Collect**:
- High-risk country revenue: [X]% of total
- Third-party intermediaries: [Yes/No]
- Compliance program maturity: [Assessment]

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active FCPA investigation | ðŸ”´ NUCLEAR |
| Settlement <5 years | ðŸ”´ HIGH |
| High-risk operations without robust compliance | ðŸŸ¡ MODERATE |
| Minimal international exposure | ðŸŸ¢ LOW |

---

### A.3.4: FTC Enforcement
**Check ID**: A.3.4
**What**: Consumer protection violations
**Source**: FTC.gov press releases
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active FTC action | ðŸ”´ HIGH |
| Consent decree active | ðŸŸ¡ MODERATE |
| None | ðŸŸ¢ LOW |

---

### A.3.5: FDA Enforcement (Healthcare)
**Check ID**: A.3.5
**What**: FDA warning letters, consent decrees
**Source**: FDA.gov Warning Letters, 483 Observations
**Applies to**: Pharma, Biotech, Medical Device, Food companies

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active consent decree | ðŸ”´ NUCLEAR |
| Warning letter <2 years | ðŸ”´ HIGH |
| 483 observations | ðŸŸ¡ MODERATE |
| Clean record | ðŸŸ¢ LOW |

---

### A.3.6: EPA Enforcement (Environmental)
**Check ID**: A.3.6
**What**: Environmental violations
**Source**: EPA.gov ECHO database
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Significant violations + enforcement | ðŸ”´ HIGH |
| Minor violations | ðŸŸ¡ MODERATE |
| Clean | ðŸŸ¢ LOW |

---

### A.3.7: State AG Actions
**Check ID**: A.3.7
**What**: Multi-state attorney general investigations
**Source**: News, state AG press releases
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Multi-state AG action active | ðŸ”´ HIGH |
| Single state action | ðŸŸ¡ MODERATE |
| None | ðŸŸ¢ LOW |

---

### A.3.8: Industry-Specific Regulators
**Check ID**: A.3.8
**What**: FINRA, OCC, CFPB, FERC, etc.
**Source**: Varies by industry
**Data to Collect**:
| Regulator | Action | Status | Amount |
|-----------|--------|--------|--------|

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active enforcement | ðŸ”´ HIGH |
| Recent settlement | ðŸŸ¡ MODERATE |
| Clean | ðŸŸ¢ LOW |

---

## A.4: FINANCIAL REPORTING ISSUES (Checks A.4.1 - A.4.6)

### A.4.1: Restatements â­ HIGH PREDICTIVE
**Check ID**: A.4.1
**What**: Financial restatements have 70-80% correlation with litigation
**Source**: 8-K Item 4.02 (Non-Reliance on Previously Issued Financials)
**Search Method**: SEC EDGAR â†’ 8-K filings â†’ Search for Item 4.02

**Data to Collect**:
- Restatement date: [Date]
- Periods affected: [List]
- Nature: [Error type]
- Magnitude: [$ impact, % of revenue/income]
- Fraud vs. error: [Assessment]

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Restatement <12 months | ðŸ”´ NUCLEAR | F.3: 12 pts |
| Restatement 12-24 months | ðŸ”´ HIGH | F.3: 10 pts |
| Restatement 2-5 years | ðŸŸ¡ MODERATE | F.3: 6 pts |
| None >5 years | ðŸŸ¢ LOW | F.3: 0 pts |

---

### A.4.2: Auditor Changes â­ HIGH PREDICTIVE
**Check ID**: A.4.2
**What**: Auditor dismissal or resignation with disagreements
**Source**: 8-K Item 4.01 (Changes in Registrant's Certifying Accountant)
**Search Method**: SEC EDGAR â†’ 8-K filings â†’ Search for Item 4.01

**Data to Collect**:
- Change date: [Date]
- Former auditor: [Name]
- New auditor: [Name]
- Reason: [Dismissed/Resigned/Rotation]
- Disagreements: [Yes/No - describe if Yes]
- Reportable events: [List]

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Resigned with disagreements | ðŸ”´ NUCLEAR | F.3: 10 pts |
| Dismissed by company with disagreements | ðŸ”´ HIGH | F.3: 10 pts |
| Dismissed, no disagreements | ðŸŸ¡ MODERATE | F.3: 4 pts |
| Routine rotation | ðŸŸ¡ MODERATE | F.3: 2 pts |
| Same auditor >5 years | ðŸŸ¢ LOW | F.3: 0 pts |

---

### A.4.3: Material Weaknesses (SOX 404)
**Check ID**: A.4.3
**What**: Internal control deficiencies
**Source**: 10-K Item 9A (Controls and Procedures)
**Data to Collect**:
- Material weakness: [Yes/No]
- Description: [Control area]
- Remediation status: [Complete/In Progress/Not Started]
- Timeframe: [Expected completion]

**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Material weakness, not remediated | ðŸ”´ HIGH | F.3: 5 pts |
| Material weakness, remediation in progress | ðŸŸ¡ MODERATE | F.3: 3 pts |
| Significant deficiency | ðŸŸ¡ MODERATE | F.3: 2 pts |
| Effective controls | ðŸŸ¢ LOW | F.3: 0 pts |

---

### A.4.4: SEC Comment Letters
**Check ID**: A.4.4
**What**: SEC review comments on disclosures
**Source**: SEC EDGAR â†’ Correspondence
**Data to Collect**:
- Open letters: [X]
- Topics: [List]
- Resolution status: [Open/Closed]

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Open, unresolved on material issues | ðŸ”´ HIGH |
| Recent, resolved | ðŸŸ¡ MODERATE |
| None or routine | ðŸŸ¢ LOW |

---

### A.4.5: Late Filings
**Check ID**: A.4.5
**What**: NT filings indicate reporting problems
**Source**: SEC EDGAR NT 10-K, NT 10-Q filings
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| NT filing <12 months | ðŸ”´ HIGH |
| NT filing 12-24 months | ðŸŸ¡ MODERATE |
| Timely filer | ðŸŸ¢ LOW |

---

### A.4.6: Non-GAAP Adjustments
**Check ID**: A.4.6
**What**: Aggressive non-GAAP reporting
**Source**: Earnings releases, 10-Q MD&A
**Calculate**: Non-GAAP Net Income / GAAP Net Income

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Non-GAAP >2x GAAP + increasing gap | ðŸ”´ HIGH |
| Significant adjustments, stable | ðŸŸ¡ MODERATE |
| Minimal adjustments | ðŸŸ¢ LOW |

---

## A.5: WHISTLEBLOWER & INTERNAL (Checks A.5.1 - A.5.4)

### A.5.1: Whistleblower Complaints
**Check ID**: A.5.1
**What**: Internal complaints often precede enforcement
**Source**: 10-K Legal Proceedings, news, court filings
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active investigation from whistleblower | ðŸ”´ NUCLEAR |
| Settlement <3 years | ðŸ”´ HIGH |
| Historical, resolved | ðŸŸ¡ MODERATE |
| None | ðŸŸ¢ LOW |

---

### A.5.2: Internal Investigations
**Check ID**: A.5.2
**What**: Board-level investigations
**Source**: 8-K, 10-K, news
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Active investigation into fraud | ðŸ”´ NUCLEAR |
| Recent with material findings | ðŸ”´ HIGH |
| Completed, no material findings | ðŸŸ¡ MODERATE |
| None | ðŸŸ¢ LOW |

---

### A.5.3: Employee Hotline Activity
**Check ID**: A.5.3
**What**: Elevated complaint activity
**Source**: 10-K Risk Factors, ESG reports
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Material increase in hotline activity disclosed | ðŸŸ¡ MODERATE |
| Normal levels | ðŸŸ¢ LOW |

---

### A.5.4: Books & Records Demands
**Check ID**: A.5.4
**What**: Shareholder 220 demands indicate activism
**Source**: 10-K Legal Proceedings, Delaware Chancery
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Multiple 220 demands <12 months | ðŸŸ¡ MODERATE |
| Single demand | ðŸŸ¢ LOW |
| None | ðŸŸ¢ LOW |

---

## A.6: GOING CONCERN & DISTRESS (Checks A.6.1 - A.6.4)

### A.6.1: Going Concern Opinion â­ NUCLEAR
**Check ID**: A.6.1
**What**: Auditor questions ability to continue
**Source**: 10-K auditor's report (immediately after financial statements)
**Thresholds**:
| Condition | Severity | Score Impact |
|-----------|----------|--------------|
| Going concern opinion | ðŸ”´ NUCLEAR | F.9: 6 pts |
| Substantial doubt in MD&A | ðŸ”´ HIGH | F.9: 4 pts |
| Liquidity concerns discussed | ðŸŸ¡ MODERATE | F.9: 2 pts |
| Clean | ðŸŸ¢ LOW | F.9: 0 pts |

---

### A.6.2: Bankruptcy Risk Indicators
**Check ID**: A.6.2
**What**: Bankruptcy filing indicators
**Source**: 10-K MD&A, news, Altman Z-score
**Calculate**: Altman Z-Score for manufacturing companies

**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Bankruptcy filed/imminent | ðŸ”´ NUCLEAR |
| Z-score <1.8 (distress zone) | ðŸ”´ HIGH |
| Z-score 1.8-3.0 (grey zone) | ðŸŸ¡ MODERATE |
| Z-score >3.0 | ðŸŸ¢ LOW |

---

### A.6.3: Restructuring Activity
**Check ID**: A.6.3
**What**: Active restructuring indicates stress
**Source**: 8-K, 10-K
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Debt restructuring active | ðŸ”´ HIGH |
| Operational restructuring | ðŸŸ¡ MODERATE |
| Normal course | ðŸŸ¢ LOW |

---

### A.6.4: Credit Rating Downgrades
**Check ID**: A.6.4
**What**: Rating agency actions
**Source**: Moody's, S&P, Fitch
**Thresholds**:
| Condition | Severity |
|-----------|----------|
| Downgrade to junk + negative outlook | ðŸ”´ HIGH |
| Recent downgrade | ðŸŸ¡ MODERATE |
| Stable ratings | ðŸŸ¢ LOW |

---

## SECTION A CHECKPOINT OUTPUT

```
## SECTION A RESULTS - [COMPANY NAME]

| Check | Description | Finding | Severity | Source |
|-------|-------------|---------|----------|--------|
| A.1.1 | IPO Timing | [Result] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | [Source] |
| A.1.2 | Capital Raises | [Result] | ðŸŸ¢/ðŸŸ¡/ðŸ”´ | [Source] |
...

### SUMMARY
- **RED FLAGS**: X/37
- **YELLOW FLAGS**: X/37
- **LITIGATION SCORE IMPACT**: F.1 = [X]/20 points
- **RESTATEMENT SCORE IMPACT**: F.3 = [X]/12 points
- **EVENT SCORE IMPACT**: F.4 = [X]/10 points
```

---

**END OF SECTION A**
