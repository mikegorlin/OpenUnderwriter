# Cutting-Edge Signals for Corporate Fraud, Governance Failure, and D&O Liability Risk

## Research Date: 2026-02-11

This document catalogs novel, unconventional, and cutting-edge signals for detecting corporate fraud, governance failure, and D&O liability risk from PUBLIC data sources. These signals go beyond traditional financial ratio analysis, stock analysis, and litigation history.

---

## 1. NLP / Linguistic Signals

### 1.1 Deception Detection in Corporate Language (Larcker-Zakolyukina Model)

**What it detects:** Active deception by CEO/CFO during earnings conference calls. Based on seminal Stanford research by Larcker & Zakolyukina (2012), validated across thousands of earnings calls.

**Specific linguistic markers of deception:**

| Marker | Direction in Deceptive Speech | Why |
|--------|-------------------------------|-----|
| Self-references ("I", "me", "myself") | DECREASE | Distancing from false statements |
| Third-person plural / impersonal pronouns | INCREASE | Deflecting personal responsibility |
| Extreme positive emotion words | INCREASE (CEOs) | Overcompensation for bad news |
| Non-extreme positive emotion words | DECREASE | Can't maintain nuanced positivity while lying |
| Anxiety words | DECREASE (CEOs) | Suppressing natural anxiety signals |
| Negation words | INCREASE (CFOs) | Language of denial and contradiction |
| Extreme negative emotion | INCREASE (CFOs, strict) | Stress leakage |
| Swear words | INCREASE (CFOs, strict) | Emotional dysregulation under cognitive load |
| References to general knowledge | INCREASE | Vague appeals rather than specific facts |
| References to shareholder value | DECREASE | Avoiding commitment to concrete value |
| Certainty words | DECREASE | Hedging and qualification increase |
| Hesitation words | DECREASE | Over-rehearsed, scripted delivery |

**Data source:** SEC EDGAR filings (earnings call transcripts via 8-K exhibits), or third-party transcript providers (Seeking Alpha, The Motley Fool transcripts are often free).

**Detection approach:**
1. Parse Q&A sections of earnings calls (most deception occurs in unscripted responses)
2. Tokenize and classify using LIWC (Linguistic Inquiry and Word Count) categories
3. Build composite deception score from word category ratios
4. Compare to company's own historical baseline (within-company changes more predictive than absolute levels)

**Performance:** Out-of-sample classification 6-16% better than random; portfolio from highest CFO deception scores produces annualized alpha of -4% to -11%.

**False positive risk:** MEDIUM. Cultural and personality differences affect language patterns. Non-native English speakers may show different pronoun patterns. Best used as a flag for deeper investigation, not standalone.

**Real example:** Would have flagged Enron executive language patterns in earnings calls prior to collapse. Research validated against companies that subsequently restated financials.

**Feasibility: 4/5** - Earnings call transcripts are freely available; LIWC dictionaries are published; FinBERT provides pre-trained financial sentiment analysis.

---

### 1.2 Readability Manipulation (Obfuscation Hypothesis)

**What it detects:** Intentional obfuscation of bad news through increased linguistic complexity in SEC filings, particularly the MD&A section.

**Key research findings:**
- Annual reports of firms with lower earnings are harder to read (higher Fog Index, longer length)
- Firms that manage earnings to beat benchmarks have MORE complex MD&A sections
- Negative narratives have statistically higher Fog Index values
- Year-over-year increases in reading complexity signal management attempting to hide deterioration

**Specific metrics to compute:**
- **Gunning Fog Index**: years of education needed to understand text. Formula: 0.4 * (words/sentences + 100 * complex_words/words)
- **Flesch Reading Ease**: higher = easier to read. Fraudulent 10-Ks have lower FRE scores
- **Average sentence length**: increases when obfuscating
- **Passive voice percentage**: increases when deflecting responsibility
- **MD&A section length**: dramatic increases suggest burying information
- **Year-over-year delta in readability**: MORE IMPORTANT than absolute level

**Data source:** SEC EDGAR full-text search, direct 10-K/10-Q downloads.

**Detection approach:**
1. Extract MD&A section from 10-K filing (Item 7)
2. Compute readability metrics (Fog, Flesch, sentence length, passive voice %)
3. Compare to prior year filing (delta is more predictive than absolute)
4. Compare to industry peers (some industries are inherently more complex)
5. Flag companies with >1 standard deviation increase in complexity

**False positive risk:** MEDIUM. Some genuine business complexity requires complex language. Regulatory changes (e.g., new accounting standards) can increase complexity legitimately. New acquisitions add legitimate complexity. The Loughran-McDonald critique notes that Fog Index is poorly specified for financial documents because "complex words" like "amortization" are well-understood by analysts.

**Real example:** Research by Li (2008) showed firms with lower earnings persistence produce harder-to-read filings. Companies that would later restate had measurably more complex filings in the misleading period.

**Feasibility: 5/5** - All data freely available from EDGAR; readability computation is straightforward; well-established academic backing.

---

### 1.3 Sentiment Divergence Analysis

**What it detects:** Gaps between management's tone and objective reality, or between different communications from the same company.

**Types of divergence to measure:**
1. **CEO letter vs. MD&A tone** - CEO strikes optimistic tone while MD&A is cautious
2. **Prepared remarks vs. Q&A tone** - Management's scripted portion vs. unscripted responses
3. **Management vs. analyst tone** - Prepared remarks are consistently more positive than analyst Q&A
4. **Earnings release vs. 10-K** - Non-GAAP positive spin in release, GAAP reality in 10-K
5. **Within-call tone drift** - Both participants' sentiment moves negative as call progresses (information leakage)
6. **Inter-manager tone distance** - CEO optimistic, CFO cautious = "Tone Distance" (negatively associated with returns)

**Key research (Angelo 2025):** "Tone Distance" - the between-manager variance of tone within an earnings call - is negatively associated with event period returns. Greater Tone Distance predicts higher stock volatility, information uncertainty, and operational risks. Investors interpret Tone Distance as information leakage about future performance.

**Data source:** Earnings call transcripts (free from Seeking Alpha), 10-K/10-Q filings (EDGAR), earnings press releases (8-K exhibits).

**Detection approach:**
1. Apply FinBERT or Loughran-McDonald sentiment dictionary to each section/speaker separately
2. Compute sentiment scores per section (positive word % - negative word %)
3. Calculate divergence metrics: CEO-CFO gap, prepared-vs-Q&A gap, release-vs-filing gap
4. Track over time: widening divergence is a leading indicator

**False positive risk:** LOW-MEDIUM. Legitimate role differences exist (CEO is the optimist, CFO is conservative), so baseline calibration per company is important. The year-over-year change in divergence is more predictive than the level.

**Real example:** Before major fraud revelations, companies typically show widening gap between CEO optimism and CFO caution, as CFO begins hedging while CEO maintains the narrative.

**Feasibility: 4/5** - Requires NLP pipeline but well-established tools exist (FinBERT on HuggingFace, Loughran-McDonald dictionary freely available).

---

### 1.4 Specificity Erosion Detection

**What it detects:** Companies replacing specific quantitative targets with vague language over time, which correlates with deteriorating confidence in future performance.

**Markers to track:**
- Disappearance of specific revenue/earnings guidance numbers
- Replacement of "we expect revenue of $X" with "we expect growth"
- Decrease in numeric values per paragraph in forward-looking sections
- Increase in hedge words: "approximately," "may," "could," "potentially," "subject to"
- Decrease in commitment words: "will," "expect," "target," "commit"

**Data source:** Earnings call transcripts, 10-K MD&A sections, earnings press releases.

**Detection approach:**
1. Count numeric values and specific targets per forward-looking section
2. Track hedge-word to commitment-word ratio over time
3. Flag companies where specificity drops >30% year-over-year
4. Cross-reference with whether company has withdrawn formal guidance

**False positive risk:** MEDIUM. Economic uncertainty (e.g., pandemic) causes industry-wide specificity reduction. Compare to peer group to isolate company-specific effects.

**Real example:** Companies withdrawing guidance ahead of fraud revelations (e.g., Wirecard reduced specificity of subscriber metrics before collapse).

**Feasibility: 4/5** - Straightforward NLP task on freely available text.

---

### 1.5 Boilerplate Detection (Stickiness Analysis)

**What it detects:** Sections of filings that are copy-pasted from prior years without substantive updates, suggesting management disengagement or intentional failure to update risk disclosures.

**Key research findings:**
- Firms reduce text stickiness (boilerplate) during crisis periods, suggesting boilerplate in non-crisis periods = disengagement
- SEC staff specifically targets companies whose risk factors appear unchanged year-over-year
- Failure to update risk factors after known material changes = potential securities law violation
- Companies adding new risk factors have lower variance risk premiums (investors use changes to update beliefs)

**Detection approach:**
1. Extract Item 1A (Risk Factors) from consecutive 10-K filings
2. Compute text similarity (cosine similarity, Jaccard index, or diff-based)
3. Identify unchanged paragraphs vs. additions vs. removals
4. Flag risk factors that SHOULD have changed (based on known events) but didn't
5. Cross-reference: if 8-K disclosed material event but risk factors weren't updated = red flag

**Data source:** EDGAR 10-K filings, consecutive years.

**Detection approach metrics:**
- Cosine similarity >0.95 between consecutive years' risk factors = "sticky"
- Paragraphs with >98% identical text = "boilerplate"
- Zero new risk factors after material 8-K events = "stale disclosure"

**False positive risk:** LOW. Some risk factor stability is normal, but when events have clearly changed the risk landscape and filings don't reflect it, this is a genuine signal.

**Real example:** Companies that failed to update cybersecurity risk factors after known breaches have faced SEC enforcement.

**Feasibility: 5/5** - Simple text comparison on freely available EDGAR data.

---

### 1.6 Topic-Driven Financial Sentiment (FinBERT + LDA)

**What it detects:** Corporate fraud by analyzing sentiment within specific financial topics in the MD&A section, using FinBERT embeddings to capture contextual meaning.

**Methodology (2026 research):**
1. Apply LDA topic modeling to extract financial topics from MD&A text
2. Use FinBERT to compute contextual sentiment within each topic
3. Combine topic-sentiment scores into a fraud prediction model
4. Track topic-sentiment drift over time

**Key topics analyzed:**
- Revenue recognition language
- Asset valuation discussions
- Related party transactions
- Going concern discussions
- Internal controls commentary
- Cash flow characterizations

**Data source:** EDGAR 10-K filings, specifically Item 7 (MD&A sections).

**Performance:** FinBERT achieves F1-score of 93.27% and accuracy of 91.08% on financial sentiment classification tasks, significantly outperforming dictionary-based methods.

**False positive risk:** MEDIUM. Model requires calibration per industry vertical; financial language varies significantly by sector.

**Feasibility: 3/5** - Requires ML infrastructure (FinBERT model, GPU for inference), but models are freely available on HuggingFace.

---

### 1.7 Forward-Looking vs. Backward-Looking Balance

**What it detects:** Companies under stress that shift their narrative from discussing future plans to discussing past performance, indicating loss of confidence in forward trajectory.

**Detection approach:**
1. Classify sentences as forward-looking (future tense, "will," "expect," "plan") or backward-looking (past tense, "achieved," "completed," "delivered")
2. Compute ratio per filing section
3. Track ratio over time - declining forward-looking ratio = stress signal
4. Compare Q&A responses specifically (harder to script than prepared remarks)

**Data source:** Earnings call transcripts, MD&A sections.

**False positive risk:** MEDIUM. Mature companies legitimately have more to discuss about the past. Use year-over-year change within same company.

**Feasibility: 4/5** - Straightforward NLP classification task.

---

## 2. Behavioral / Network Signals

### 2.1 Board Interlock Fraud Contagion

**What it detects:** Companies connected to fraudulent firms through shared board members, which research shows increases the probability of earnings management and audit risk.

**Key research findings:**
- A firm sharing a common director with an earnings manipulator is MORE LIKELY to manage earnings (contagion effect)
- Contagion is STRONGER when the shared director holds an accounting-relevant position (audit committee chair/member)
- Board interlock with a fraud-involved company leads to 12.86% average increase in audit fees at connected firms
- Regulatory sanctions at one firm induce significant stock price drops among firms sharing the same auditor

**Data source:**
- SEC EDGAR DEF 14A (proxy statements) - board member listings
- BoardEx database (paid, but ISS data also available)
- LinkedIn corporate profiles (supplementary)
- SEC enforcement actions database

**Detection approach:**
1. Build director network graph from proxy statements
2. Map all companies where each director serves
3. Cross-reference against SEC enforcement actions, restatements, lawsuits
4. Flag companies with directors connected to >1 problematic firm
5. Weight by director's role (audit committee = higher weight)

**False positive risk:** MEDIUM. Many well-qualified directors serve on multiple boards without issues. The signal is probabilistic - it increases the base rate of problems, not confirms them.

**Real example:** Research shows directors at Enron-connected boards were more likely to have governance issues at their other companies.

**Feasibility: 3/5** - Proxy statements are free; building the network graph is labor-intensive but automatable. BoardEx/ISS data is paid.

---

### 2.2 Auditor Change Patterns

**What it detects:** Companies engaging in "opinion shopping" or experiencing auditor-side risk escalation.

**Critical signals:**
1. **Auditor resignation (vs. dismissal)** - Resignation = auditor walking away = highest risk signal
2. **Big Four to non-Big Four switch** - Opinion shopping for going concern or material weakness
3. **Going concern then auditor change** - Companies that receive GC opinion then switch auditors: more likely managing perception
4. **Material weakness + auditor change** - 2.5% of firms with material weaknesses have future fraud revelations (2.7x the rate of matched firms)
5. **Abnormal audit fee changes** - Large fee increase = auditor discovering issues; large decrease = company shopping for cheaper/less rigorous audit
6. **Mid-year auditor change** - Outside normal rotation cycle = emergency situation

**Data source:** SEC EDGAR 8-K (Item 4.01 - Changes in Registrant's Certifying Accountant), annual reports (auditor opinion letter), Audit Analytics database.

**Detection approach:**
1. Monitor 8-K Item 4.01 filings for auditor changes
2. Cross-reference with prior year audit opinion (clean vs. qualified vs. GC)
3. Compare audit fees year-over-year
4. Check if outgoing auditor resigned vs. was dismissed
5. Check if company disagreed with former auditor (required 8-K disclosure)

**False positive risk:** LOW. Auditor resignation in particular is a very strong signal - auditors rarely walk away from fee-paying clients without serious cause.

**Real example:** Wirecard's auditor EY faced scrutiny after the firm collapsed; Arthur Andersen's client network showed elevated risk signals across connected firms during the Enron era.

**Feasibility: 5/5** - All data available through EDGAR 8-K filings; well-defined trigger event.

---

### 2.3 Law Firm / PR Firm Change Signals

**What it detects:** Companies quietly positioning for anticipated legal or reputational crises by hiring crisis-management firms.

**Signals to track:**
1. **Hiring WilmerHale, Sullivan & Cromwell, Gibson Dunn crisis practice** - These firms' crisis management practices are the most prestigious; their engagement signals serious anticipated trouble
2. **Adding a second law firm** (crisis firm alongside regular securities counsel)
3. **Retaining crisis PR firms** (Sitrick, FTI Consulting, Edelman Crisis, BerlinRosen)
4. **Switching from regional law firm to national firm** - Indicates problems exceeding local expertise
5. **Engaging forensic accountants** (FTI, AlixPartners, Alvarez & Marsal)

**Data source:**
- SEC filings (counsel listed on registration statements, proxy statements)
- News searches (press releases often name counsel)
- DEF 14A proxy statements (legal counsel identification)
- 8-K filings (engagement of advisors for material events)
- OpenSecrets lobbying disclosures (lobbying firm changes)

**Detection approach:**
1. Monitor news feeds for company + crisis firm name co-occurrence
2. Track changes in legal counsel listed on SEC filings
3. Flag sudden engagement of firms known primarily for crisis management
4. Cross-reference with lobbying spend changes (sudden increases = defensive positioning)

**False positive risk:** MEDIUM-HIGH. Companies hire these firms for many legitimate reasons (M&A, regulatory filings). The signal is most useful when combined with OTHER red flags.

**Real example:** Companies facing SEC investigation often retain crisis-specialized counsel months before public disclosure; Nippon Steel increased lobbying from $30K to $4.3M when facing CFIUS review.

**Feasibility: 3/5** - Partial data from EDGAR; news monitoring needed for completeness.

---

### 2.4 Board Meeting Frequency Anomalies

**What it detects:** Boards that meet abnormally often are typically responding to problems, not proactively governing.

**Key research:** Board meeting frequency is inversely related to firm value, driven by increases in board activity FOLLOWING share price declines. High meeting frequency = "fire-fighting device" rather than proactive governance.

**Data source:** DEF 14A proxy statement (required disclosure of total board and committee meetings per fiscal year).

**Detection approach:**
1. Extract board meeting count from proxy statement
2. Compare to prior year (year-over-year increase > 30% = flag)
3. Compare to industry peer median
4. Cross-reference with directors attending <75% of meetings (required disclosure) - may indicate internal disagreement

**False positive risk:** MEDIUM. M&A activity legitimately increases meeting frequency. Compare to 8-K filings to assess whether meetings correlate with known events.

**Feasibility: 4/5** - Data freely available in proxy statements; requires parsing but is structured disclosure.

---

### 2.5 Revolving Door Hires (Former Regulator Signal)

**What it detects:** Companies hiring former SEC/DOJ officials, which research shows correlates with litigation risk and compliance concerns.

**Key research findings:**
- 1 in 3 public firms employ a former regulator
- Firms that recently faced securities class action lawsuits are MORE LIKELY to retain former SEC lawyers
- Firms not using top-tier audit firms are more likely to hire former regulators (substituting personal connections for audit quality)
- Regulatory benefits accrue in the 2-year window BEFORE the regulator's transition (potential capture)

**Data source:**
- SEC EDGAR DEF 14A (proxy statements) - officer/director biographies
- LinkedIn professional profiles
- SEC personnel directories (current and former)
- RevolvingDoorProject.org tracking database

**Detection approach:**
1. Parse proxy statement officer biographies for SEC/DOJ/PCAOB experience
2. Track TIMING of hire relative to known regulatory actions
3. Flag companies that add former regulators to board shortly after SEC inquiry
4. Cross-reference with revolving door project databases

**False positive risk:** MEDIUM-HIGH. Many former regulators bring legitimate expertise. The signal is strongest when the hire coincides with or follows regulatory scrutiny.

**Feasibility: 3/5** - Proxy statement biographical data is available but unstructured; NER extraction needed.

---

### 2.6 Executive Background Network Analysis

**What it detects:** Executives/directors with connections to past frauds, regulatory actions, or failed companies.

**Investigation technique (from Hindenburg playbook):**
1. Multi-jurisdictional court record searches (30% of adverse findings come from onsite searches not available online)
2. Federal criminal records (fraud, embezzlement, tax evasion)
3. State-level civil litigation (breach of fiduciary duty, shareholder suits)
4. Bankruptcy filings (pattern of involvement in failed enterprises)
5. SEC enforcement actions (CIK cross-reference)
6. FINRA BrokerCheck (for financial industry backgrounds)
7. Media coverage analysis (pattern detection across career)

**Data source:**
- PACER (federal court records)
- State court databases (varies by jurisdiction)
- SEC EDGAR enforcement releases
- FINRA BrokerCheck (free public)
- LinkedIn (career timeline)
- State Secretary of State corporate registrations
- SAM.gov (debarment database)

**Detection approach:**
1. Extract all named officers/directors from proxy statement
2. Search PACER and state courts for civil/criminal cases
3. Search SEC enforcement database for prior actions
4. Build career timeline and flag gaps, unexplained transitions
5. Cross-reference companies from their history against SEC enforcement database
6. Flag: "Variations, even if minor but many, may bring into question someone's integrity or character"

**False positive risk:** LOW (for confirmed adverse findings), but HIGH for guilt-by-association signals.

**Real example:** Hindenburg Research has identified executives with histories at multiple failed companies or regulatory violations; their investigations have preceded 65+ SEC fraud charges and 24+ DOJ criminal indictments.

**Feasibility: 3/5** - PACER and state courts are partially online; comprehensive searches require multi-jurisdictional research.

---

## 3. Alternative Data Signals

### 3.1 Job Posting Analysis

**What it detects:** Mass layoffs before announcement, compliance/legal hiring spikes suggesting anticipated problems, or "ghost jobs" masking company distress.

**Specific signals:**
1. **Job posting decline >40%** in 30-day window = potential pre-layoff signal
2. **Compliance/legal hiring spike** (multiple postings for compliance officers, internal investigators, in-house counsel) = anticipated enforcement action
3. **Sudden "Chief Compliance Officer" or "Chief Ethics Officer" posting** = reactive to known or anticipated issue
4. **Job postings removed en masse** = hiring freeze / pre-restructuring
5. **Ghost jobs** - 40% of companies post fake jobs (2024 survey); can inflate "growth" narrative
6. **Senior leadership open positions** = unexpected departures
7. **Glassdoor reviews mentioning "ethics," "compliance," "SEC," "investigation"** = insider knowledge leaking

**Data source:**
- Indeed, LinkedIn, Glassdoor job postings (some require scraping)
- Company careers pages
- Thinknum Alternative Data (paid, tracks job postings)
- Glassdoor employee reviews (free)

**Detection approach:**
1. Monitor company job postings for volume changes
2. NLP classification of job titles for compliance/legal/ethics categories
3. Track Glassdoor employee reviews for risk-related keywords
4. Compare hiring narrative (10-K describes "growth") vs. actual job posting trends

**False positive risk:** MEDIUM. Seasonal hiring patterns, normal compliance buildout for growth. Use year-over-year comparison and peer benchmarking.

**Real example:** Companies facing SEC investigations often hire compliance officers 6-12 months before public disclosure. Research by Campbell and Shang (2022) confirms employee disclosure reveals misconduct risk.

**Feasibility: 3/5** - Job posting data requires monitoring infrastructure; Glassdoor reviews are freely accessible but need scraping.

---

### 3.2 Employee Sentiment (Glassdoor/Indeed Reviews)

**What it detects:** Internal problems leaking through employee reviews, which research shows predict stock price declines and misconduct revelations.

**Key research findings:**
- Glassdoor business outlook ratings predict "bad news" events (credit downgrades, dividend decreases) BETTER than they predict good news
- Statistically and economically significant relation between changes in employee satisfaction and stock returns
- Following revelation of misconduct, employee sentiment decreases sharply and persistently, driven by diminished perceptions of firm culture and senior management
- Employee perceptions provide early warning for financial red flags because pressures from financial distress increase the risk of fraudulent behaviors

**Specific signals:**
1. **Business Outlook rating decline** - Strongest predictive signal
2. **"Senior Leadership" rating decline** - Precedes governance problems
3. **Reviews mentioning specific keywords**: "ethics," "compliance," "investigation," "SEC," "layoff," "toxic," "fraud," "accounting," "audit"
4. **Sudden increase in review volume** - Often precedes or follows major events
5. **CEO approval rating decline** - Leading indicator of leadership problems
6. **"Cons" section keyword analysis** - NLP sentiment on negative aspects

**Data source:** Glassdoor.com (free to read, rate limits apply), Indeed employee reviews, Blind (anonymous employee forum).

**Detection approach:**
1. Scrape or API-access company Glassdoor reviews
2. Apply NLP sentiment analysis to review text
3. Track business outlook, CEO approval, and category ratings over time
4. Flag keyword occurrences related to compliance/ethics/investigation
5. Compare to industry peers

**False positive risk:** MEDIUM. Disgruntled employees can skew results; small companies have low review volume. Best for companies with >50 reviews/year.

**Real example:** Enron and Wells Fargo both showed declining Glassdoor scores before their respective scandals became public.

**Feasibility: 4/5** - Data is free and publicly available; straightforward NLP and trend analysis.

---

### 3.3 Patent Filing Patterns

**What it detects:** Companies claiming innovation growth while patent activity declines, which may indicate fabricated R&D narratives.

**Signals to track:**
1. **Patent application decline** while 10-K touts R&D growth
2. **Patent abandonment increase** - Companies abandoning existing patents = cost-cutting
3. **Patent quality metrics** (citation frequency, claim breadth)
4. **Inventor departure** - Key inventors leaving and filing at new employer
5. **Patent-to-R&D-spend ratio** declining
6. **Division between defensive patents and offensive patents** shifting

**Data source:**
- USPTO full-text database (free, searchable by assignee)
- Google Patents (free, comprehensive search)
- PatentsView API (free, USPTO-maintained)
- WIPO PATENTSCOPE (free, international patents)
- Lens.org (free, combines patents + scholarly works)

**Detection approach:**
1. Query USPTO for all patents assigned to company and subsidiaries
2. Track filing volume by year and compare to R&D expense trajectory
3. Monitor patent abandonments (maintenance fee non-payment is public)
4. Cross-reference named inventors against LinkedIn (did key inventors leave?)
5. Flag: R&D spend increasing + patent filings declining = potential R&D expense manipulation

**False positive risk:** MEDIUM. Companies may shift to trade secrets over patents; industry trends matter (software industry patents less meaningful). Best for pharma, tech hardware, biotech.

**Real example:** Theranos continued to tout technology innovation while its patent portfolio did not reflect credible breakthroughs; Hindenburg checks whether patents match claimed technology capabilities.

**Feasibility: 5/5** - USPTO data is completely free and has APIs; Google Patents provides excellent search.

---

### 3.4 Corporate Registration / Subsidiary Patterns

**What it detects:** Shell entities, unusual jurisdictions, and complex corporate structures designed to obscure related-party transactions or asset hiding.

**Red flags from research:**
1. **Rapid subsidiary creation** in unusual jurisdictions (Delaware, Nevada, Wyoming for domestics; Cayman, BVI, Luxembourg for international)
2. **Multiple LLCs with same registered agent** - Pattern of shell company creation
3. **Administrative dissolution then reinstatement** - Periodic in Secretary of State records
4. **Changes in state of domicile** - Moving corporate registration
5. **Similar names controlled by same person** - Network of interconnected shells
6. **Subsidiaries not disclosed in 10-K Exhibit 21** - Required disclosure of significant subsidiaries
7. **Subsidiary count inconsistent with business complexity** - Too many subsidiaries for business size

**Data source:**
- State Secretary of State databases (most have online search, free)
- SEC EDGAR Exhibit 21 (subsidiary list in 10-K)
- Corporate Transparency Act database (FinCEN, beneficial owners - available to law enforcement, some public access)
- SAM.gov (System for Award Management - debarment records)
- OpenCorporates.com (aggregated corporate registrations)

**Detection approach:**
1. Extract Exhibit 21 subsidiary list from 10-K
2. Search state SOS databases for undisclosed entities with same registered agent
3. Compare subsidiary count year-over-year
4. Flag unusual jurisdictions for company's business type
5. Cross-reference registered agents with other entities
6. Flag: Companies that "may obscure company structure, ownership, and activities" through layered LLCs

**False positive risk:** MEDIUM. International companies legitimately use holding structures. Tax optimization uses Delaware/Ireland structures normally. The signal is in CHANGES and UNDISCLOSED entities.

**Real example:** Hindenburg Research consistently finds undisclosed shell entities in their investigations; Enron had hundreds of special purpose entities designed to hide losses.

**Feasibility: 4/5** - State SOS databases are free but fragmented; OpenCorporates aggregates but may not be complete.

---

### 3.5 Government Contract Data

**What it detects:** Contract cancellations, debarments, and spending pattern changes for companies with government exposure.

**Data source:**
- FPDS.gov (Federal Procurement Data System) - All federal contracts over micro-purchase threshold
- USASpending.gov - Federal spending transparency
- SAM.gov - System for Award Management (debarment/exclusion list)
- GSA Excluded Parties List
- State-level procurement databases

**Detection approach:**
1. Search FPDS.gov for all contracts awarded to company
2. Monitor for contract modifications (reductions, cancellations)
3. Check SAM.gov exclusion list for company, subsidiaries, and officers
4. Track contract award trends (declining = loss of government confidence)
5. Cross-reference with news about contract performance issues

**False positive risk:** LOW for debarments (very definitive signal); MEDIUM for contract volume changes (budget cycles affect awards).

**Real example:** Defense contractors debarred from government contracting have historically faced D&O claims from shareholders.

**Feasibility: 5/5** - FPDS.gov and SAM.gov are completely free with APIs.

---

### 3.6 Supply Chain Cross-Verification

**What it detects:** Fabricated or inflated revenue through cross-referencing customer/supplier SEC filings.

**Technique (from short seller playbook):**
1. SEC requires disclosure of customers representing >10% of revenue
2. Company A says Customer B represents 15% of revenue
3. Check Customer B's filing - do they disclose Company A as a significant supplier?
4. If Company A claims revenue from Customer B but Customer B's filings show no material relationship = revenue fabrication signal

**Data source:**
- SEC EDGAR 10-K filings (Item 1 for customer concentration, Exhibit 21 for subsidiaries)
- EDGAR Full-Text Search for company name mentions in other companies' filings
- SEC supply chain data from Factset/Bloomberg (paid) or manual EDGAR search

**Detection approach:**
1. Extract customer names from target company's 10-K
2. Search each customer's 10-K for mentions of target company
3. Compare disclosed percentages (revenue % vs. supplier spend %)
4. Check if claimed customers are real, operating businesses (SOS database, web presence)
5. For international customers, verify existence through foreign corporate registries

**False positive risk:** LOW when discrepancy is clear; MEDIUM otherwise (thresholds may not trigger both-side disclosure).

**Real example:** Muddy Waters Research exposed Sino-Forest by verifying that claimed timber assets and customer relationships could not be independently confirmed (stock fell 74%). This is a core technique in short seller due diligence.

**Feasibility: 3/5** - Requires manual cross-referencing across multiple EDGAR filings; automatable but labor-intensive.

---

### 3.7 Lobbying Spend Changes

**What it detects:** Companies anticipating regulatory enforcement or seeking to influence upcoming regulatory actions.

**Data source:**
- OpenSecrets.org (comprehensive lobbying data from Senate Office of Public Records)
- LDA filings (Lobbying Disclosure Act quarterly reports)
- House/Senate lobby disclosure databases

**Detection approach:**
1. Track quarterly lobbying spend via OpenSecrets.org API
2. Flag companies with >100% year-over-year increase in lobbying spend
3. Identify specific lobbying issues (topic of lobbying activity is disclosed)
4. Cross-reference lobbying topic with pending regulation/enforcement
5. Example: Nippon Steel went from $30K to $4.3M lobbying when facing CFIUS review

**False positive risk:** MEDIUM. Companies may increase lobbying for legitimate business expansion. Analyze specific lobbying topics for defensive vs. offensive positioning.

**Feasibility: 4/5** - OpenSecrets.org provides free data with API access; quarterly disclosure cycle.

---

## 4. Market Microstructure Signals

### 4.1 Options Market Anomalies

**What it detects:** Informed trading before corporate events - unusual put volume, options open interest changes suggesting someone has non-public information.

**Specific signals:**
1. **Put/call ratio spike** - Sudden increase in put buying relative to calls
2. **Put volume >3x average** - Unusual bearish positioning
3. **Deep out-of-the-money put buying** - Low-cost bets on significant decline
4. **Open interest surge in short-dated options** - New positions timed to specific events
5. **Implied volatility skew changes** - Put implied vol rising faster than call implied vol
6. **Dark pool volume surge** - Unusual institutional flow (FINRA ATS data, 2-4 week delayed)

**Data source:**
- CBOE options data (partially free via market data providers)
- Barchart.com Unusual Activity (free basic access)
- FINRA OTC Transparency data (free, https://otctransparency.finra.org)
- FINRA Short Interest data (free, published bi-monthly)
- InsiderFinance.io, OptionStrat.com (freemium)

**Detection approach:**
1. Monitor daily put/call ratio against 20-day moving average
2. Flag when put volume exceeds 3x 20-day average
3. Analyze open interest changes vs. volume (new positions vs. closing)
4. Check FINRA short interest data (published mid-month and end-of-month)
5. Cross-reference with upcoming corporate events (earnings, filings)

**False positive risk:** MEDIUM-HIGH. Options market is noisy; hedging activity creates false signals. Most useful when combined with fundamental red flags.

**Real example:** Before Enron's collapse, unusual put option activity was observed. Academic research shows abnormal options trading precedes enforcement actions.

**Feasibility: 3/5** - Options data requires subscription for comprehensive access; FINRA data is free but delayed.

---

### 4.2 Short Selling Patterns

**What it detects:** Informed short sellers positioning before bad news.

**Key signals:**
1. **Short interest ratio (days to cover)** >10 days = significant bearish conviction
2. **Short interest increase >30%** between bi-monthly reports
3. **New short positions established within 30 days of bad news** = informed trading
4. **Short squeeze potential** (high short interest + low float) creates volatility risk
5. **Late-filed J-coded Form 4 transactions** - "Highly suspicious," with intense abnormal returns when reported long after transaction

**Data source:**
- FINRA Short Interest Data (free, bi-monthly publication)
- SEC Form 4 (insider sales/purchases with timing data)
- EDGAR insider transaction datasets (free bulk download from SEC)
- Short interest by exchange (NYSE, Nasdaq publish)

**Detection approach:**
1. Track bi-monthly short interest changes via FINRA data
2. Flag companies with short interest >15% of float
3. Monitor Form 4 for insider selling clusters
4. Check for J-coded transactions filed late (strong suspicion signal)
5. Analyze insider Purchase-after-Sales (S->P) patterns vs. Sales-after-Sales (S->S) patterns

**False positive risk:** MEDIUM. Short interest can reflect legitimate hedging or sector-wide positioning. Short squeezes can temporarily inflate prices. Look for CONVERGENCE of insider selling + short interest increase.

**Feasibility: 5/5** - FINRA and SEC data are free; Form 4 data available in bulk from SEC.

---

### 4.3 Credit Market Signals

**What it detects:** Credit market pricing corporate default risk often leads equity market signals.

**Signals:**
1. **CDS spread widening** - Credit default swap market prices fraud/default risk before equity market reacts
2. **Corporate bond spread widening vs. treasury** - Available through TRACE data
3. **CDS-bond basis turning negative** - Arbitrage signal indicating market stress
4. **Bond rating downgrade watchlist** - S&P/Moody's/Fitch watchlist placement

**Data source:**
- FINRA TRACE (corporate bond trading data, free with delay)
- ICE BofA indices (general spread data)
- S&P/Moody's/Fitch websites (rating actions, free)
- Federal Reserve FRED database (corporate spread indices)

**Detection approach:**
1. Monitor company-specific CDS spreads (limited public availability)
2. Track TRACE-reported corporate bond trading and yield spreads
3. Compare to sector peers and treasury benchmarks
4. Flag credit rating outlook changes (negative outlook precedes downgrade)

**False positive risk:** MEDIUM. Credit markets can be illiquid for smaller issuers; spreads affected by general market conditions. Company-specific CDS data has limited free availability.

**Feasibility: 2/5** - CDS data is mostly paid; TRACE data is free but requires processing; bond market data is less accessible than equity data.

---

## 5. Filing Pattern Analysis

### 5.1 Filing Timing Anomalies

**What it detects:** Companies hiding bad news by filing at unusual times.

**Key findings from Hudson Labs research:**
- ~60% of 10-Ks and 10-Qs filed between 4-5:30 PM (normal)
- ~3% of large caps consistently file after 5:30 PM (Apple, Alphabet, Amazon, Meta, PepsiCo - just their schedule)
- <1% of small caps consistently file after hours
- **Deviation from a company's own pattern is the critical signal**
- Friday evening filings ("Friday Night Dump") are deliberate strategy to minimize analyst attention

**Specific examples of bad-news late filings:**
- Citigroup (9:41 PM): Disclosed regulatory investigation, $130M write-down
- Nvidia (8:33 PM): Revealed data hack and terminated acquisition; stock fell 40%
- Southwest Airlines (9:44 PM): Reported declining margins
- Take Two Interactive (8:16 PM): Disclosed declining income during acquisition

**Data source:** EDGAR filing metadata (free, includes accepted timestamp for every filing).

**Detection approach:**
1. Build filing time baseline per company (last 8-12 quarters)
2. Flag any filing accepted >2 hours after company's normal window
3. Extra flag for Friday evening filings (after 5 PM Friday)
4. Extra flag for filings on days before holidays/long weekends
5. Cross-reference with filing content (does late filing contain material news?)

**False positive risk:** LOW for established companies with clear patterns; MEDIUM for companies without filing history.

**Feasibility: 5/5** - EDGAR timestamps are freely available metadata; trivial to compute.

---

### 5.2 NT (Non-Timely) Filing Patterns

**What it detects:** Companies unable to file financial reports on time, which correlates with accounting problems and future restatements.

**Key research findings:**
- Accounting problems are the most frequently cited reason for delays (average 41-day delay vs. 13 days for corporate events)
- NT 10-Q filings cause average stock price drop of ~3%; NT 10-K filings cause ~2% drop
- SEC enforcement initiative discovered companies that filed NT then announced restatements within 4-14 days, despite not disclosing the pending restatement as a reason for the NT
- SEC has charged companies for providing incomplete information on Form NT

**Data source:** EDGAR search for Form NT 10-K and NT 10-Q filings (freely available).

**Detection approach:**
1. Monitor EDGAR for NT filings by tracked companies
2. Extract stated reason from NT filing text
3. Flag NT filings that cite "accounting" or "audit" reasons (highest risk)
4. Track time-to-actual-filing after NT (longer = worse)
5. Check for subsequent restatements within 30 days of NT

**False positive risk:** LOW. Late filing is almost always negative; the only question is severity. Companies experiencing genuine one-time events (acquisitions, system migrations) may file NT legitimately.

**Real example:** Vinco Ventures filed only one quarterly report on schedule as a public company, with 14 non-timely filings.

**Feasibility: 5/5** - EDGAR provides simple search for NT filings; fully automated.

---

### 5.3 Amendment Frequency (10-K/A, 10-Q/A)

**What it detects:** Companies amending previously filed reports, suggesting errors, misstatements, or evolving understanding of problems.

**Data source:** EDGAR search for filing type 10-K/A, 10-Q/A.

**Detection approach:**
1. Track amendment filings per company
2. Companies with >1 amendment in 12 months = elevated risk
3. Parse amendment to identify what changed (financial figures vs. exhibits vs. narrative)
4. Flag financial statement amendments (restated numbers = material problem)

**False positive risk:** LOW for financial restatements; MEDIUM for non-financial amendments (exhibit corrections, typographical fixes).

**Feasibility: 5/5** - EDGAR search for amended filings is straightforward.

---

### 5.4 8-K Filing Patterns

**What it detects:** Unusual patterns in current-event reporting that may indicate brewing problems.

**Signals:**
1. **Multiple 8-Ks in rapid succession** - Cascade of material events
2. **8-K filed Friday evening or holiday weekend** - Burying bad news
3. **Item 4.01 (auditor change)** - Critical governance signal
4. **Item 4.02 (non-reliance on financials)** - Restatement incoming
5. **Item 5.02 (departure of directors/officers)** - Executive flight
6. **Item 2.06 (material impairments)** - Asset write-downs
7. **Item 7.01/8.01 combined with late timing** - Hiding material non-required disclosures

**Data source:** EDGAR 8-K filings (free, searchable by item number and date).

**Detection approach:**
1. Monitor 8-K filing frequency per company (abnormal if >1 per week)
2. Classify by item number and severity
3. Flag specific high-risk items (4.01, 4.02, 5.02)
4. Track timing patterns (day-of-week, time-of-day)
5. Cross-reference with subsequent stock price movement

**Feasibility: 5/5** - All EDGAR data; well-structured for analysis.

---

### 5.5 SEC Comment Letter Escalation

**What it detects:** SEC staff review correspondence that indicates concerns about a company's disclosures, with escalation patterns predicting future restatements.

**Key research findings:**
- Comment letters associated with future restatements can be identified by Naive Bayesian classification
- Revenue recognition comments, number of letters in a conversation, and disclosure-event abnormal returns are useful metrics
- Less readable company responses are associated with longer SEC response times AND higher restatement probability
- Political connections predict more intensive SEC review (number of issues, seniority of staff)

**Data source:** EDGAR CORRESP filing type (comment letter correspondence made public after review completion, typically 60-day delay).

**Detection approach:**
1. Monitor EDGAR for CORRESP filings involving tracked companies
2. Count number of rounds in SEC review (>3 rounds = escalation)
3. Analyze topics raised (revenue recognition = highest risk)
4. Measure readability of company responses (complex/evasive responses = higher risk)
5. Track SEC staff seniority involved in review (senior staff = more serious concern)

**False positive risk:** MEDIUM. All public companies receive comment letters; the majority result in routine disclosure improvements. Escalation signals are what matter.

**Feasibility: 4/5** - EDGAR data is free but parsing correspondence requires NLP; topic classification is moderately complex.

---

### 5.6 EDGAR Download Pattern Analysis

**What it detects:** Unusual interest in a company's filings by specific entities (IRS, Federal Reserve, institutional investors, potential acquirers, short sellers).

**Key findings:**
- EDGAR log files are public and show IP addresses, timestamps, pages visited
- IRS and Federal Reserve systematically access EDGAR for their own investigations
- Auditors access non-client filings for benchmarking
- Spikes in download activity may precede enforcement actions
- Robot downloads (>50 from single IP/day) are filtered but manual access patterns remain informative

**Data source:** SEC EDGAR Log File Data Sets (https://www.sec.gov/about/data/edgar-log-file-data-sets), free CSV downloads covering 2003-2017 and 2020-present (gap from 2017-2020). Quarterly delivery restarted October 2024.

**Detection approach:**
1. Download EDGAR log data sets
2. Filter for accesses to target company's CIK
3. Identify patterns: sudden spike in access = someone investigating
4. Analyze accessor characteristics (IP ranges associated with regulatory agencies)
5. Correlate access spikes with subsequent enforcement actions

**False positive risk:** HIGH. Many legitimate reasons for download spikes (quarterly earnings, index rebalancing, academic research). IP anonymization limits identification of specific accessors.

**Feasibility: 2/5** - Data is freely available but massive (terabytes of log data); analysis requires significant infrastructure; IP anonymization limits usefulness.

---

### 5.7 Schedule 13D/13G Monitoring (Activist Accumulation)

**What it detects:** Activist investors building positions, which frequently precedes governance challenges and may signal perceived mismanagement.

**Signals:**
1. **13D filing** (activist intent) vs. **13G** (passive) - 13D requires disclosure of purpose
2. **Passive-to-active conversion** (13G -> 13D) - Investor shifting from passive to activist stance
3. **Multiple 13D/A amendments** - Increasing position or changing stated intentions
4. **"Purpose of Transaction" section** - Contains activist's specific demands

**Data source:** EDGAR SC 13D, SC 13G, and amendment filings.

**Detection approach:**
1. Monitor EDGAR for 13D/13G filings involving tracked companies
2. Flag new 13D filings (activist intent)
3. Track 13G-to-13D conversions
4. Analyze "Purpose of Transaction" for governance demands
5. Cross-reference with proxy fight filings (PRE 14A, DEFA14A)

**Feasibility: 5/5** - All EDGAR data; well-defined trigger event.

---

## 6. Cross-Filing Consistency Checks

### 6.1 Earnings Release vs. 10-K/10-Q Reconciliation

**What it detects:** Non-GAAP metrics in earnings releases that don't reconcile to GAAP figures in formal filings.

**SEC focus areas:**
- SEC Staff has targeted companies that disclose trends in earnings releases but not in MD&A
- Non-GAAP metrics in press releases that paint a rosier picture than GAAP results
- KPIs discussed in earnings calls but absent from periodic reports

**Detection approach:**
1. Extract financial metrics from 8-K earnings release
2. Compare to 10-K/10-Q GAAP financial statements
3. Compute Non-GAAP-to-GAAP bridge and verify reconciliation
4. Flag metrics that appear ONLY in press releases but not in formal filings
5. Track consistency of metric definitions quarter-to-quarter

**Feasibility: 4/5** - Requires parsing both 8-K and 10-K; structured data extraction.

---

### 6.2 MD&A vs. Financial Statements Inconsistency

**What it detects:** Narrative claims in Management Discussion & Analysis that are not supported by, or contradict, the financial statements.

**Detection approach:**
1. Extract numerical claims from MD&A text (revenue growth %, margin expansion, etc.)
2. Verify against actual financial statement figures
3. Flag discrepancies (MD&A says "revenue grew 15%" but income statement shows 8%)
4. Check qualitative claims ("improving margins") against actual margin trends
5. Analyze CEO letter tone vs. financial reality

**Feasibility: 3/5** - Requires NLP extraction of claims + structured financial data comparison.

---

### 6.3 Risk Factors vs. Insurance/Mitigation Disclosure

**What it detects:** Risks disclosed in Item 1A that have no corresponding mitigation or insurance disclosure elsewhere in the filing.

**Detection approach:**
1. Extract individual risk factors from Item 1A
2. Search remainder of filing for mitigation strategies, insurance coverage, or hedging activities related to each risk
3. Flag risks with no corresponding mitigation = potential unaddressed exposure
4. Year-over-year: new risks added without new mitigation strategies = escalating vulnerability

**Feasibility: 3/5** - Requires sophisticated NLP for topic matching across filing sections.

---

### 6.4 Proxy Statement vs. 10-K Compensation Reconciliation

**What it detects:** Executive compensation figures that differ between the proxy statement and 10-K filing.

**Detection approach:**
1. Extract executive compensation data from DEF 14A (Summary Compensation Table)
2. Compare to 10-K Note disclosure on compensation expense
3. Check related party transactions in both filings
4. Flag discrepancies in total compensation, stock-based comp, or perquisites

**Feasibility: 3/5** - Structured proxy tables available via XBRL; 10-K notes require NLP extraction.

---

## 7. Short Seller Playbook

### 7.1 Hindenburg Research Methodology (Comprehensive)

Based on analysis of Hindenburg's published reports and methodology, their investigation playbook includes:

**Target Selection Criteria:**
- Excessive valuation relative to fundamentals
- Aggressive promotional marketing
- Complex offshore corporate structures
- Heavy related-party transactions
- Founder-controlled governance with limited independent oversight
- SPAC or reverse merger origins
- Weak auditor oversight (non-Big Four for significant companies)
- High insider selling

**Investigation Techniques (3-12 month process):**

| Technique | Description | Public Data Available? |
|-----------|-------------|----------------------|
| SEC filing analysis (10-K, 10-Q, S-1, F-1) | Line-by-line review of financial statements | YES (EDGAR) |
| Corporate registry mapping | Checking offshore jurisdictions for undisclosed entities | PARTIAL (OpenCorporates, state SOS) |
| Satellite imagery verification | Checking if claimed facilities exist | YES (Google Earth, Sentinel Hub) |
| Physical site visits | On-the-ground verification of offices, factories | YES (public access) |
| Former employee interviews | Verifying operational claims | PARTIAL (LinkedIn for contacts) |
| Supplier/customer verification | Confirming business relationships exist | PARTIAL (EDGAR cross-reference) |
| IP/Patent analysis | Do patents match claimed technology? | YES (USPTO, Google Patents) |
| Executive background checks | Past fraud, regulatory violations | PARTIAL (PACER, state courts) |
| Stock imagery detection | Checking if company uses fake facility photos | YES (reverse image search) |
| FOIA requests | Government records on company interactions | YES (FOIA.gov) |
| Foreign regulatory filings | International corporate registrations | PARTIAL (varies by jurisdiction) |
| Social media analysis | Employee posts, whistleblower activity | YES (public social media) |

**Impact Track Record:**
- 65+ individuals subsequently charged with SEC fraud
- 24+ criminal DOJ indictments
- 7+ foreign regulator sanctions

### 7.2 Key Short Seller Verification Techniques

**Revenue Verification:**
- Cross-reference customer SEC filings for target company mentions
- Check if major customers actually exist (corporate registry, web presence, physical address)
- Compare claimed market share to industry data
- Verify government contract values through FPDS.gov

**Facility Verification:**
- Google Maps/Street View of claimed facilities
- Satellite imagery time series (was the factory actually built?)
- Compare claimed capacity to actual facility size
- Check building permits and construction records

**Executive Integrity:**
- Multi-jurisdictional court record searches
- Previous company track records (follow the people)
- LinkedIn career gaps and unexplained transitions
- SEC enforcement history for named individuals
- FINRA BrokerCheck for securities industry professionals

**Financial Statement Forensics:**
- Beneish M-Score computation (see Section 8.1 below)
- Benford's Law analysis of financial statement numbers
- Cash flow vs. earnings quality analysis
- Related party transaction analysis
- Revenue recognition pattern analysis
- Working capital anomalies
- Off-balance sheet obligation discovery

---

## 8. Academic Frontier

### 8.1 Forensic Accounting Models

#### Beneish M-Score (Enhanced)

**Formula:**
```
M-score = -4.84 + 0.92*DSRI + 0.528*GMI + 0.404*AQI + 0.892*SGI
          + 0.115*DEPI - 0.172*SGAI + 4.679*TATA - 0.327*LVGI
```

**Variables:**
| Variable | Full Name | What It Detects |
|----------|-----------|-----------------|
| DSRI | Days Sales in Receivables Index | Revenue recognition manipulation via accelerated booking |
| GMI | Gross Margin Index | Deteriorating margins creating incentive to manipulate |
| AQI | Asset Quality Index | Cost capitalization / asset inflation |
| SGI | Sales Growth Index | High growth companies under pressure to hit targets |
| DEPI | Depreciation Index | Slowing depreciation to inflate profits |
| SGAI | SGA Expense Index | Efficiency changes or cost deferral |
| TATA | Total Accruals to Total Assets | Accrual vs. cash earnings gap |
| LVGI | Leverage Index | Increasing debt pressure creating fraud incentive |

**Interpretation:** M-score > -1.78 = company is LIKELY a manipulator.
**Accuracy:** Correctly identifies 76% of manipulators; 17.5% false positive rate.

**Data source:** All variables computable from XBRL-tagged financial statements in EDGAR.

**Feasibility: 5/5** - Fully automatable from EDGAR XBRL data.

---

#### Benford's Law Analysis

**What it detects:** Fabricated or manipulated numbers in financial statements by testing whether digit distributions follow the expected natural pattern.

**Expected first digit distribution (Benford's Law):**
| Digit | Expected % |
|-------|-----------|
| 1 | 30.1% |
| 2 | 17.6% |
| 3 | 12.5% |
| 4 | 9.7% |
| 5 | 7.9% |
| 6 | 6.7% |
| 7 | 5.8% |
| 8 | 5.1% |
| 9 | 4.6% |

**Tests to perform:**
1. **First Digit Test** - Compare leading digit distribution to Benford's expected
2. **First Two-Digit Test** - More granular analysis (100 expected proportions)
3. **Chi-Square Test** - Statistical significance of deviations
4. **Apply to:** Total Assets, Total Liabilities, Revenue line items, Expense categories

**Data source:** EDGAR XBRL financial statements (all numerical values).

**Limitations:** Data constrained to narrow ranges violates Benford's assumptions. Best applied to datasets with >100 data points spanning multiple orders of magnitude.

**Real example:** Benford's Law deviations were confirmed in Enron's financial statements.

**Feasibility: 5/5** - Trivial computation on freely available XBRL data.

---

### 8.2 Deep Learning / ML Frontier (2024-2026)

**Most promising recent approaches:**

| Method | Description | Key Innovation |
|--------|-------------|----------------|
| **FinBERT + LDA** | Topic-driven sentiment analysis of MD&A for fraud detection | Captures contextual sentiment WITHIN financial topics, not just overall tone |
| **Graph Neural Networks (FraudGCN)** | Multi-relational graph encoding industrial, supply chain, and accounting relationships | Detects fraud through relationship patterns, not just individual company features |
| **LSTM temporal models** | Time-series analysis of financial statement sequences | Captures deteriorating trajectories that point-in-time analysis misses |
| **Hybrid Bayesian-LightGBM** | Combines Bayesian optimization with gradient boosting | Integrates executive attributes, ESG performance, and innovation capabilities |
| **FLAG (LLM + GNN)** | Fraud detection combining large language models with graph neural networks | 2025 paper; uses LLM reasoning + network structure |
| **Knowledge Distillation** | Training lightweight models from complex fraud detection models | Enables real-time scoring without heavyweight inference |

**Key insight from 2025 systematic review:** 19 non-financial indicators have been identified as fraud predictors, primarily focusing on internal executive information, management compensation, and shareholder ownership ratios.

**Data sources for ML models:**
- Financial statements (EDGAR XBRL)
- Textual filings (EDGAR full text)
- Corporate governance data (proxy statements)
- Supply chain relationships (10-K customer/supplier disclosures)
- Market data (stock prices, options, short interest)
- Employee data (Glassdoor, job postings)

**Feasibility: 2/5 for GNN/FLAG** (requires significant ML infrastructure); **4/5 for FinBERT** (pre-trained models available on HuggingFace).

---

### 8.3 Network Analysis Research

**Key findings:**
- Earnings management is CONTAGIOUS through board interlocks
- Shared directors in accounting-relevant positions (audit committee) amplify contagion
- Shared auditor effects: regulatory sanctions at one client cause stock drops at other clients of same auditor
- Well-connected audit committees REDUCE misstatement probability (governance network as protection)

**Implication for D&O system:** Building a director network graph and cross-referencing against SEC enforcement database would identify "contagion risk" - companies connected to known problem firms through shared directors or auditors.

---

## 9. Data Availability Matrix

| Signal | Data Source | Availability | Cost | API? | Update Frequency |
|--------|------------|-------------|------|------|-----------------|
| Linguistic deception (earnings calls) | Seeking Alpha, EDGAR 8-K | FREE | $0 | Partial | Quarterly |
| Readability metrics (10-K) | EDGAR | FREE | $0 | Yes (EDGAR API) | Annual |
| Sentiment analysis (FinBERT) | HuggingFace model + EDGAR text | FREE | $0 | Yes | Annual |
| Boilerplate detection | EDGAR (consecutive 10-Ks) | FREE | $0 | Yes | Annual |
| Specificity erosion | Earnings transcripts, EDGAR | FREE | $0 | Partial | Quarterly |
| Board interlocks | DEF 14A (EDGAR) | FREE | $0 | Yes | Annual |
| Auditor changes | 8-K Item 4.01 (EDGAR) | FREE | $0 | Yes | Event-driven |
| Executive backgrounds | PACER, state courts | PARTIAL | $0.10/page (PACER) | Partial | As-filed |
| Job postings | Indeed, LinkedIn, Glassdoor | FREE to view | $0 (scraping) | Limited | Daily |
| Employee sentiment | Glassdoor | FREE | $0 | No (scraping) | Daily |
| Patent filings | USPTO, Google Patents | FREE | $0 | Yes (PatentsView) | Weekly |
| Subsidiary registrations | State SOS databases | FREE-LOW | $0-10/search | Varies | As-filed |
| Government contracts | FPDS.gov, USASpending.gov | FREE | $0 | Yes | Daily |
| Supply chain cross-ref | EDGAR full-text search | FREE | $0 | Yes | Annual |
| Lobbying data | OpenSecrets.org | FREE | $0 | Yes | Quarterly |
| Options activity | Barchart, CBOE | FREEMIUM | $0-50/mo | Yes | Daily |
| Short interest | FINRA | FREE | $0 | Yes | Bi-monthly |
| Credit market signals | TRACE, FRED | FREE | $0 | Partial | Daily |
| Filing timing | EDGAR metadata | FREE | $0 | Yes | As-filed |
| NT filings | EDGAR | FREE | $0 | Yes | As-filed |
| 8-K patterns | EDGAR | FREE | $0 | Yes | As-filed |
| SEC comment letters | EDGAR CORRESP | FREE | $0 | Yes | 60-day delay |
| EDGAR download logs | SEC datasets | FREE | $0 | Bulk download | Quarterly |
| 13D/13G filings | EDGAR | FREE | $0 | Yes | As-filed |
| Beneish M-Score | EDGAR XBRL | FREE | $0 | Yes | Annual/Quarterly |
| Benford's Law | EDGAR XBRL | FREE | $0 | Yes | Annual/Quarterly |
| CDS spreads | Bloomberg/ICE | PAID | $$$$ | Yes | Daily |
| BoardEx network data | BoardEx/ISS | PAID | $$$ | Yes | Quarterly |
| Comprehensive court records | PACER + state courts | PAID | $0.10/page | Partial | As-filed |
| Satellite imagery | Google Earth, Sentinel Hub | FREE-PAID | $0-$$ | Yes | Varies |
| SAM.gov debarment | SAM.gov | FREE | $0 | Yes | Daily |
| FOIA requests | FOIA.gov | FREE | $0 (time cost) | Yes | 20+ business days |

---

## 10. Implementation Priority

### Tier 1: High Impact, High Feasibility (Implement First)

These signals are freely available, automatable, and have strong academic validation:

| Priority | Signal | Feasibility | Impact | Data Cost | Implementation Effort |
|----------|--------|-------------|--------|-----------|----------------------|
| 1 | **Beneish M-Score** | 5/5 | HIGH | FREE | LOW - formula on XBRL data |
| 2 | **Filing timing anomalies** | 5/5 | HIGH | FREE | LOW - EDGAR metadata |
| 3 | **NT filing monitoring** | 5/5 | HIGH | FREE | LOW - EDGAR search |
| 4 | **Auditor change detection** | 5/5 | HIGH | FREE | LOW - 8-K Item 4.01 |
| 5 | **Readability manipulation** | 5/5 | MEDIUM-HIGH | FREE | LOW - text metrics |
| 6 | **Boilerplate/stickiness detection** | 5/5 | MEDIUM | FREE | LOW - text comparison |
| 7 | **8-K pattern analysis** | 5/5 | MEDIUM-HIGH | FREE | LOW - filing metadata |
| 8 | **Benford's Law analysis** | 5/5 | MEDIUM | FREE | LOW - digit distribution |
| 9 | **13D/13G activist monitoring** | 5/5 | MEDIUM | FREE | LOW - EDGAR filings |
| 10 | **Short interest monitoring** | 5/5 | MEDIUM | FREE | LOW - FINRA data |

### Tier 2: High Impact, Moderate Feasibility (Implement Second)

These require some NLP infrastructure or data aggregation but offer significant detection power:

| Priority | Signal | Feasibility | Impact | Data Cost | Implementation Effort |
|----------|--------|-------------|--------|-----------|----------------------|
| 11 | **Linguistic deception scoring** | 4/5 | HIGH | FREE | MEDIUM - NLP pipeline |
| 12 | **Sentiment divergence** | 4/5 | HIGH | FREE | MEDIUM - multi-source NLP |
| 13 | **Employee sentiment (Glassdoor)** | 4/5 | MEDIUM-HIGH | FREE | MEDIUM - scraping + NLP |
| 14 | **SEC comment letter analysis** | 4/5 | MEDIUM-HIGH | FREE | MEDIUM - NLP on CORRESP |
| 15 | **Patent filing pattern analysis** | 5/5 | MEDIUM | FREE | MEDIUM - USPTO API + comparison |
| 16 | **Specificity erosion detection** | 4/5 | MEDIUM | FREE | MEDIUM - NLP |
| 17 | **Board meeting frequency** | 4/5 | MEDIUM | FREE | MEDIUM - proxy parsing |
| 18 | **Lobbying spend changes** | 4/5 | MEDIUM | FREE | LOW - OpenSecrets API |
| 19 | **Government contract monitoring** | 5/5 | MEDIUM | FREE | MEDIUM - FPDS.gov API |
| 20 | **Earnings release vs. 10-K reconciliation** | 4/5 | MEDIUM-HIGH | FREE | MEDIUM - dual parsing |

### Tier 3: High Impact, Lower Feasibility (Advanced / Phase 2)

These require more infrastructure, paid data, or manual investigation:

| Priority | Signal | Feasibility | Impact | Data Cost | Implementation Effort |
|----------|--------|-------------|--------|-----------|----------------------|
| 21 | **Board interlock network** | 3/5 | HIGH | FREE-PAID | HIGH - graph database |
| 22 | **Executive background checks** | 3/5 | HIGH | PAID | HIGH - multi-jurisdictional |
| 23 | **Supply chain cross-verification** | 3/5 | HIGH | FREE | HIGH - cross-filing analysis |
| 24 | **FinBERT topic-driven fraud scoring** | 3/5 | HIGH | FREE | HIGH - ML infrastructure |
| 25 | **Corporate subsidiary mapping** | 4/5 | MEDIUM-HIGH | LOW | HIGH - multi-state queries |
| 26 | **Job posting analysis** | 3/5 | MEDIUM | FREE | HIGH - monitoring infra |
| 27 | **Law firm / PR firm changes** | 3/5 | MEDIUM | FREE | HIGH - news monitoring |
| 28 | **Options market anomalies** | 3/5 | MEDIUM | FREEMIUM | MEDIUM - market data |
| 29 | **Revolving door hires** | 3/5 | MEDIUM | FREE | HIGH - biography NER |
| 30 | **Facility verification (satellite)** | 3/5 | HIGH (when applicable) | FREE | HIGH - image analysis |

### Tier 4: Specialized / Expensive (Future Consideration)

| Priority | Signal | Feasibility | Impact | Data Cost | Implementation Effort |
|----------|--------|-------------|--------|-----------|----------------------|
| 31 | **EDGAR download log analysis** | 2/5 | LOW-MEDIUM | FREE | VERY HIGH - terabytes of data |
| 32 | **Credit market signals (CDS)** | 2/5 | MEDIUM | PAID ($$$) | MEDIUM |
| 33 | **Graph Neural Network fraud detection** | 2/5 | HIGH | FREE | VERY HIGH - ML research |
| 34 | **Dark pool flow analysis** | 2/5 | LOW-MEDIUM | FREE (delayed) | HIGH |
| 35 | **FOIA request automation** | 2/5 | MEDIUM | FREE (time) | HIGH - weeks of delay |

---

## References and Sources

### Academic Papers
- Larcker, D.F. & Zakolyukina, A.A. (2012). "Detecting Deceptive Discussions in Conference Calls." Journal of Accounting Research. [Stanford GSB](https://www.gsb.stanford.edu/faculty-research/publications/detecting-deceptive-discussions-conference-calls)
- Li, F. (2008). "Annual Report Readability, Current Earnings, and Earnings Persistence." [Journal of Accounting and Economics](https://www.sciencedirect.com/science/article/abs/pii/S0165410108000141)
- Beneish, M.D. (1999). "The Detection of Earnings Manipulation." Financial Analysts Journal.
- Angelo (2025). "Tone Distance: Managerial Tone Divergence and Market Reaction." [Financial Review](https://onlinelibrary.wiley.com/doi/10.1111/fire.70002)
- Chiu, Teoh & Tian. "Board Interlocks and Earnings Management Contagion." [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1723714)
- Green, Huang, Wen & Zhou. "Crowdsourced Employer Reviews and Stock Returns." [Georgetown](https://faculty.georgetown.edu/qw50/Green,Huang,Wen,Zhou_EmpRatings.pdf)

### Data Sources
- [SEC EDGAR](https://www.sec.gov/edgar/search/)
- [SEC EDGAR Log Files](https://www.sec.gov/about/data/edgar-log-file-data-sets)
- [FINRA OTC Transparency](https://otctransparency.finra.org)
- [FINRA Short Interest](https://www.finra.org/finra-data/browse-catalog/equity-short-interest/data)
- [OpenSecrets Lobbying](https://www.opensecrets.org/federal-lobbying)
- [FPDS Federal Procurement](https://www.fpds.gov/)
- [SAM.gov Exclusions](https://sam.gov/)
- [USPTO PatentsView API](https://patentsview.org/)
- [ProsusAI FinBERT](https://huggingface.co/ProsusAI/finbert)
- [Hudson Labs Filing Analysis](https://www.hudson-labs.com/post/filing-after-hours-when-it-matters)

### Industry Sources
- [Hindenburg Research](https://hindenburgresearch.com/)
- [Harvard Law School Forum on Corporate Governance](https://corpgov.law.harvard.edu/)
- [Deloitte SEC Comment Letter Roadmap](https://dart.deloitte.com/USDART/home/publications/deloitte/additional-deloitte-guidance/roadmap-sec-comment-letter-considerations)
- [Audit Analytics](https://blog.auditanalytics.com/)
- [Barchart Unusual Options Activity](https://www.barchart.com/options/unusual-activity)

### Research Collections
- [Graph Fraud Detection Papers (GitHub)](https://github.com/safe-graph/graph-fraud-detection-papers)
- [SRAF Notre Dame EDGAR Server Logs](https://sraf.nd.edu/data/edgar-server-log/)
- [Loughran-McDonald Financial Sentiment Dictionary](https://sraf.nd.edu/loughranmcdonald-master-dictionary/)
