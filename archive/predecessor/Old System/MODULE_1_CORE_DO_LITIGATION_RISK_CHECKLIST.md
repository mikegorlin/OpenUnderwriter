
### Check 1.1: Basic Company Information
**What to Check**:
- Company legal name
- Ticker symbol and exchange
- Industry classification (primary and secondary)
- Headquarters location
- Year founded / years in operation

**Data Sources**:
- SEC EDGAR (10-K, 10-Q)
- Company website
- Yahoo Finance / Bloomberg

**Pass/Fail Criteria**: N/A (informational)

**Purpose**: Establish baseline company profile for risk assessment

---

### Check 1.2: Market Capitalization Classification
**What to Check**:
- Current market capitalization
- Classification: Mega-cap (>$200B), Large-cap ($10B-$200B), Mid-cap ($2B-$10B), Small-cap ($300M-$2B), Micro-cap (<$300M)

**Data Sources**:
- Yahoo Finance / Bloomberg (real-time data)
- SEC filings (shares outstanding × stock price)

**Pass/Fail Criteria**:
- ✅ PASS: Market cap >$300M (sufficient liquidity for securities litigation)
- ⚠️ CAUTION: Market cap $100M-$300M (marginal)
- 🔴 HIGH RISK: Market cap <$100M (high litigation risk relative to size)

**Purpose**: Market cap correlates with litigation frequency and severity. Smaller companies face disproportionate risk.

**Settlement Benchmarks by Market Cap**:
- Mega-cap: $100M-$7.2B
- Large-cap: $50M-$1B
- Mid-cap: $20M-$200M
- Small-cap: $5M-$50M
- Micro-cap: $1M-$20M

---

### Check 1.3: Company Life Stage
**What to Check**:
- Years since IPO
- Years since founding
- Stage: Pre-revenue, Early-stage, Growth, Mature, Declining

**Data Sources**:
- SEC EDGAR (S-1, 10-K)
- Company website
- Crunchbase / PitchBook

**Pass/Fail Criteria**:
- ✅ PASS: >5 years since IPO, established business model
- ⚠️ CAUTION: 1-5 years since IPO (elevated risk period)
- 🔴 HIGH RISK: <1 year since IPO (highest litigation risk period)
- 🔴 HIGH RISK: Pre-revenue or early-stage (high volatility, unproven business model)

**Purpose**: Newly public companies face 3-5x higher litigation risk in first 3 years post-IPO.

**Case Frequency**: 
- IPO-related litigation: 47 cases out of 500 (9.4%)
- Median time to filing: 18 months post-IPO

---

### Check 1.4: SPAC Status
**What to Check**:
- Did company go public via SPAC (Special Purpose Acquisition Company)?
- If yes, date of de-SPAC transaction
- Sponsor identity and track record

**Data Sources**:
- SEC EDGAR (S-4, 8-K)
- SPAC Research database
- Company press releases

**Pass/Fail Criteria**:
- ✅ PASS: Traditional IPO or >3 years post-de-SPAC
- 🔴 HIGH RISK: SPAC within last 3 years (elevated litigation risk)

**Purpose**: SPAC transactions face significantly higher litigation risk than traditional IPOs.

**Case Frequency**:
- SPAC-related litigation: 117 filings identified by Stanford (2020-2024)
- Median settlement: $20-35M
- Key risks: Misleading projections, breach of fiduciary duty in de-SPAC transaction

---

## CATEGORY 2: ACTIVE LITIGATION & REGULATORY ENFORCEMENT

### Check 2.1: Active Securities Class Action Lawsuits
**What to Check**:
- Are there any active securities class action lawsuits against the company?
- Class period dates
- Lead plaintiff and law firm
- Court and case number
- Status (motion to dismiss pending, discovery, trial, settlement negotiations)
- Alleged violations (Section 10(b), Section 11/12, etc.)

**Data Sources**:
- SEC EDGAR (8-K disclosures)
- Stanford Securities Class Action Clearinghouse
- Law firm websites (Rosen, Bernstein Litowitz, Robbins Geller, etc.)
- PACER (federal court dockets)
- Company 10-K/10-Q (Legal Proceedings section)

**Pass/Fail Criteria**:
- ✅ PASS: No active securities litigation
- 🔴 CRITICAL FAIL: Active securities class action lawsuit

**Purpose**: Active securities litigation is a known loss and indicates material D&O exposure.

**Action if FAIL**:
- Document case details (class period, allegations, status)
- Estimate potential settlement amount based on market cap loss and comparable cases
- Check if company has recorded loss contingency in financials
- Assess probability of additional claims (derivative suits)

**Settlement Estimation Formula**:
- Median settlement = 2.0% of estimated investor losses
- Investor losses ≈ Market cap decline during class period × trading volume
- Adjust for case strength, dismissal probability, and company financial condition

---

### Check 2.2: Active Derivative Lawsuits
**What to Check**:
- Are there any active derivative lawsuits (shareholder suits against directors/officers)?
- Allegations (breach of fiduciary duty, Caremark claims, waste of corporate assets, etc.)
- Demand status (demand made, demand refused, demand excused)
- Court and case number
- Status

**Data Sources**:
- SEC EDGAR (8-K disclosures)
- Company 10-K/10-Q (Legal Proceedings section)
- Delaware Court of Chancery dockets (for Delaware corporations)
- PACER (federal court dockets)

**Pass/Fail Criteria**:
- ✅ PASS: No active derivative litigation
- 🔴 CRITICAL FAIL: Active derivative lawsuit

**Purpose**: Derivative suits often follow securities class actions and can result in substantial settlements.

**Case Frequency**:
- Derivative suits filed in parallel with securities class actions: ~40% of cases
- Median derivative settlement: $9.2M (2024 data)
- Largest derivative settlements: $900M+ (Tesla board compensation)

**Action if FAIL**:
- Document case details
- Assess if parallel to securities class action (increases settlement probability)
- Check for Caremark claims (duty of oversight) - these have high settlement rates
- Estimate potential settlement (typically lower than securities class actions but still material)

---

### Check 2.3: SEC Enforcement Actions
**What to Check**:
- Are there any active or recent SEC enforcement actions?
- Type (civil, administrative, criminal referral)
- Charges (antifraud, reporting violations, FCPA, etc.)
- Status (investigation, settlement, litigation)
- Penalties assessed (disgorgement, civil penalties, officer-and-director bars)

**Data Sources**:
- SEC.gov Litigation Releases
- SEC.gov Administrative Proceedings
- Company 8-K disclosures
- Company 10-K/10-Q (Legal Proceedings section)

**Pass/Fail Criteria**:
- ✅ PASS: No SEC enforcement actions in last 5 years
- ⚠️ CAUTION: SEC investigation disclosed but no charges filed
- 🔴 CRITICAL FAIL: Active SEC enforcement action or settlement in last 3 years

**Purpose**: SEC enforcement actions often precede or run parallel to securities class actions. They provide detailed fact patterns that strengthen plaintiff cases.

**Case Frequency**:
- SEC enforcement actions that trigger securities class actions: ~35% of cases
- Average SEC penalty: $10M-$100M (varies widely)
- Officer-and-director bars: Indicates serious misconduct

**Action if FAIL**:
- Document charges and findings
- Check if settlement included officer-and-director bars (red flag for future D&O coverage)
- Assess if SEC findings will be used in private securities litigation
- Estimate total exposure (SEC penalty + likely shareholder settlement)

---

### Check 2.4: DOJ Criminal Investigations / Prosecutions
**What to Check**:
- Are there any active DOJ criminal investigations or prosecutions?
- Targets (company, executives, both)
- Charges (securities fraud, wire fraud, conspiracy, FCPA, etc.)
- Status (investigation, indictment, trial, plea agreement)

**Data Sources**:
- DOJ press releases
- Company 8-K disclosures
- Company 10-K/10-Q (Legal Proceedings section)
- News reports

**Pass/Fail Criteria**:
- ✅ PASS: No criminal investigations or prosecutions
- 🔴 CRITICAL FAIL: Active DOJ criminal investigation or prosecution

**Purpose**: Criminal prosecutions indicate the most serious forms of misconduct and virtually guarantee massive civil litigation.

**Case Frequency**:
- Criminal prosecutions in parallel with securities class actions: ~5% of cases
- But when present, settlements are typically in top decile ($100M+)
- Examples: Enron, WorldCom, Theranos, FTX

**Action if FAIL**:
- Document charges and status
- Assess if executives are personally charged (indicates intentional fraud)
- Check if company has entered into deferred prosecution agreement (DPA) or non-prosecution agreement (NPA)
- Estimate civil litigation exposure (typically 5-10x criminal penalties)

---

### Check 2.5: Other Regulatory Actions
**What to Check**:
- FDA warning letters, consent decrees, or enforcement actions (for life sciences companies)
- FTC enforcement actions (for consumer-facing companies)
- EPA enforcement actions (for industrial/energy companies)
- FINRA/SEC enforcement (for financial services - excluded from our scope)
- State attorney general actions
- Foreign regulatory actions (if material)

**Data Sources**:
- FDA.gov (Warning Letters, Enforcement Actions)
- FTC.gov (Press Releases)
- EPA.gov (Enforcement Actions)
- Company 8-K disclosures
- Company 10-K/10-Q (Legal Proceedings section)

**Pass/Fail Criteria**:
- ✅ PASS: No material regulatory enforcement actions in last 3 years
- ⚠️ CAUTION: Minor regulatory actions (warning letters) that were resolved
- 🔴 HIGH RISK: Material regulatory enforcement actions (consent decrees, major fines)

**Purpose**: Regulatory enforcement actions can trigger securities litigation if they reveal previously undisclosed problems.

**Case Frequency**:
- FDA enforcement actions that trigger securities litigation: ~15% of life sciences cases
- FTC enforcement actions that trigger securities litigation: ~5% of consumer cases

**Action if FAIL**:
- Document regulatory action and company's response
- Assess if action reveals material misstatements or omissions in prior disclosures
- Check stock price reaction (material drop = higher litigation risk)

---

### Check 2.6: FCPA Investigation or Enforcement Action
**What to Check**:
- Are there any active or recent Foreign Corrupt Practices Act (FCPA) investigations or enforcement actions?
- DOJ or SEC FCPA investigation status
- Charges or allegations (bribery of foreign officials, inadequate internal controls)
- Geographic regions involved
- Penalties assessed or potential exposure

**Data Sources**:
- DOJ FCPA enforcement actions database
- SEC.gov Litigation Releases
- Company 8-K disclosures
- Company 10-K/10-Q (Legal Proceedings section)
- News reports

**Pass/Fail Criteria**:
- ✅ PASS: No FCPA investigations or enforcement actions in last 5 years
- ⚠️ CAUTION: FCPA investigation disclosed but no charges filed
- 🔴 CRITICAL FAIL: Active FCPA enforcement action or settlement in last 3 years

**Purpose**: FCPA violations indicate serious governance failures and often trigger securities litigation and derivative suits.

**Case Frequency**:
- FCPA enforcement actions that trigger securities class actions: ~25% of cases
- Average FCPA penalty: $25M-$500M (varies widely by severity)
- Often accompanied by monitor requirements and compliance obligations

**Action if FAIL**:
- Document charges, geographic regions, and penalties
- Assess if company has operations in high-corruption jurisdictions
- Check if settlement included compliance monitor (indicates serious issues)
- Estimate total exposure (FCPA penalty + likely shareholder settlement)

---

### Check 2.7: Antitrust Investigation
**What to Check**:
- Are there any active DOJ or FTC antitrust investigations?
- Type of investigation (price-fixing, monopolization, merger review, etc.)
- Status (investigation, consent decree, litigation)
- Potential remedies or penalties

**Data Sources**:
- DOJ Antitrust Division press releases
- FTC.gov enforcement actions
- Company 8-K disclosures
- Company 10-K/10-Q (Legal Proceedings section)

**Pass/Fail Criteria**:
- ✅ PASS: No antitrust investigations in last 3 years
- ⚠️ CAUTION: Antitrust investigation disclosed but no charges
- 🔴 HIGH RISK: Active antitrust enforcement action or consent decree

**Purpose**: Antitrust enforcement actions can trigger securities litigation and indicate anticompetitive business practices.

**Case Frequency**:
- Antitrust enforcement that triggers securities litigation: ~10% of cases
- Defense costs can be substantial even if claims dismissed

**Action if FAIL**:
- Document investigation scope and potential penalties
- Assess company's market position and competitive practices
- Check for product bundling, tying arrangements, or exclusionary conduct

---

### Check 2.8: ESG Regulatory Scrutiny
**What to Check**:
- Are there any SEC or state AG investigations of ESG disclosures?
- Greenwashing allegations
- Climate disclosure compliance
- ESG reporting accuracy

**Data Sources**:
- SEC.gov enforcement actions
- State AG press releases
- Company 8-K disclosures
- News reports

**Pass/Fail Criteria**:
- ✅ PASS: No ESG regulatory scrutiny
- ⚠️ CAUTION: ESG disclosure questions from regulators
- 🔴 HIGH RISK: Active investigation of greenwashing or ESG misrepresentation

**Purpose**: ESG-related enforcement is increasing and can trigger securities litigation.

**Action if FAIL**:
- Document specific ESG claims being investigated
- Assess company's ESG disclosure practices
- Check for material gaps between ESG claims and actual performance

---

## CATEGORY 3: FINANCIAL HEALTH & STABILITY

### Check 3.1: Current Ratio (Liquidity Test)
**What to Check**:
- Current Ratio = Current Assets ÷ Current Liabilities
- Trend over last 4 quarters

**Data Sources**:
- Company 10-Q/10-K (Balance Sheet)
- Yahoo Finance / Bloomberg

**Pass/Fail Criteria**:
- ✅ PASS: Current Ratio ≥ 1.5 (healthy liquidity)
- ⚠️ CAUTION: Current Ratio 1.0-1.5 (adequate but tight)
- 🔴 FAIL: Current Ratio < 1.0 (liquidity crisis)

**Purpose**: Companies with liquidity problems are more likely to engage in accounting fraud to hide financial distress.

**Case Frequency**: