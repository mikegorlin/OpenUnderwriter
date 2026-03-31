# D&O Data Sources & Signals Research

## Purpose

Comprehensive inventory of publicly available data sources for automated D&O (Directors & Officers) liability underwriting analysis. For each source: what it is, where to find it, what signals to extract, access method, reliability, and whether our current system uses it.

**Key principle**: Broad web searches are a FIRST-CLASS acquisition method, not a fallback. Structured APIs miss: short seller reports, state AG actions, employee lawsuits, social media, early news signals. The power of this system lies in casting wide nets across unstructured sources to find blind spots that structured data alone cannot reveal.

---

## 1. Structured Data Sources

### 1.1 SEC EDGAR Filings

**What it is**: The SEC's Electronic Data Gathering, Analysis, and Retrieval system. All public companies must file periodic reports, proxy statements, insider transactions, and event-driven disclosures.

**Where to find it**: https://www.sec.gov/cgi-bin/browse-edgar, https://efts.sec.gov/LATEST/search-index (full text search API)

**Filing types and D&O signals**:

| Filing | Content | D&O Risk Signals |
|--------|---------|-----------------|
| **10-K** (Annual) | Full financials, risk factors, legal proceedings, MD&A | Item 1A risk factor changes year-over-year; Item 3 legal proceedings; Item 7 MD&A tone shifts; going concern language; related party disclosures |
| **10-Q** (Quarterly) | Interim financials, updates | Quarter-over-quarter deterioration; new litigation disclosures; restatement language |
| **8-K** (Current) | Material events within 4 business days | Item 4.01: auditor changes; Item 4.02: non-reliance on prior financials (restatement signal); Item 5.02: executive departures; multiple 8-Ks in quick succession = developing crisis |
| **DEF 14A** (Proxy) | Board composition, executive comp, related party transactions, say-on-pay | Board independence ratios; excessive comp vs. peers; related party transactions; failed say-on-pay votes; staggered board structures |
| **Form 4** (Insider) | Insider buys/sells within 2 business days | Cluster selling before bad news; unusual volume; C-suite selling while issuing positive guidance |
| **Form 13F** (Institutional) | Quarterly institutional holdings >$100M | Concentration risk; activist investor accumulation; institutional exodus |
| **Schedule 13D** | 5%+ beneficial ownership with activist intent | Activist campaigns; proxy fight initiation; demand for board seats or strategy changes |
| **Form S-1/S-3** | Registration statements | IPO/secondary offering risk; lock-up expiration timelines |
| **CORRESP** (Comment Letters) | SEC staff questions about filings | Revenue recognition concerns; accounting policy challenges; -5.8% abnormal returns for firms with "signaled" comment letters in 90 days post-disclosure |

**Access method**: EdgarTools MCP (primary), SEC EDGAR REST APIs (data.sec.gov), SEC EFTS full-text search API (free), sec-api.io (third-party, free tier available)

**Reliability**: HIGH -- audited/official filings with legal liability for misstatements

**Current system usage**: YES -- EdgarTools MCP for filing retrieval; EFTS search for litigation references in 10-K filings. SEC client (`sec_client.py`) fetches 10-K, 10-Q, 8-K, DEF 14A. Filing text extraction via `filing_text.py`.

**Gaps in current system**:
- No systematic 8-K event monitoring (auditor changes, executive departures, non-reliance)
- No SEC comment letter (CORRESP) analysis
- No 13D/13G activist investor tracking
- No Form 4 insider transaction pattern analysis (cluster detection)
- No year-over-year Item 1A risk factor diff analysis
- No Schedule 13F institutional holder concentration tracking
- DEF 14A parsing incomplete (board composition, executive tenure extraction returns None)

---

### 1.2 XBRL Financial Data

**What it is**: eXtensible Business Reporting Language tags on SEC filings, making financial data machine-readable. Covers 10-K, 10-Q, 8-K, 20-F, 40-F, 6-K.

**Where to find it**: https://data.sec.gov/api/xbrl/ (official API), https://xbrl.us/academic-repository/sec-edgar-data/

**D&O risk signals extractable directly from XBRL**:
- **Financial distress**: Current ratio, quick ratio, debt-to-equity, interest coverage, working capital
- **Altman Z-Score inputs**: Working capital/TA, retained earnings/TA, EBIT/TA, market cap/TL, revenue/TA
- **Revenue trends**: Revenue growth/decline, revenue concentration by segment
- **Profitability**: Gross margin, operating margin, net margin, ROE, ROA
- **Cash flow**: Operating cash flow, free cash flow, cash burn rate
- **Leverage**: Total debt, debt maturity schedule, covenant compliance indicators
- **Restatement indicators**: Changes in previously reported figures quarter-over-quarter

**Access method**: SEC XBRL API (free, JSON), EdgarTools (Python library), xbrl.us data

**Reliability**: HIGH -- audited figures with XBRL validation

**Current system usage**: YES -- EdgarTools extracts XBRL financial data. `xbrl_concepts.json` config maps concept names.

**Gaps**: Revenue segment extraction incomplete (e.g., AAPL returns no segments). Geographic revenue breakdown not reliably extracted.

---

### 1.3 Stock Market Data

**What it is**: Real-time and historical stock price, volume, options, and market data.

**Where to find it**: Yahoo Finance via yfinance Python library

**D&O risk signals**:
- **Price decline from 52-week high**: Primary trigger for securities class actions (>20% decline with corrective disclosure)
- **Abnormal volume spikes**: Often precede or accompany material events
- **Beta/volatility**: Higher volatility = higher litigation probability (historical correlation)
- **Short interest ratio**: FINRA publishes twice monthly; high short interest = market skepticism
- **Options implied volatility**: Elevated IV before earnings = market uncertainty about upcoming disclosures
- **Market cap changes**: Large market cap companies are disproportionate lawsuit targets
- **Insider selling patterns**: Cross-reference with Form 4 data for timing analysis

**Access method**: yfinance (free, Python), FINRA short interest data (free, semi-monthly), NYSE/NASDAQ short interest files

**Reliability**: HIGH for price/volume data; MEDIUM for derived signals (short interest has 2-week reporting lag)

**Current system usage**: YES -- `market_client.py` uses yfinance for stock data. Scoring factor F2 (Stock Decline, 15pts) and F7 (Volatility, 9pts) consume this data.

**Gaps**:
- No options implied volatility extraction
- Short interest data from yfinance may be stale (2-week FINRA reporting lag)
- No fails-to-deliver tracking
- No intraday short volume data
- Top institutional holders extraction incomplete (missing pct_out computation)

---

### 1.4 Short Interest Data

**What it is**: Twice-monthly reports of uncovered short positions, required by FINRA Rule 4560.

**Where to find it**:
- FINRA: https://www.finra.org/finra-data/browse-catalog/equity-short-interest (official, semi-monthly)
- NYSE Group Short Interest File (historical back to 1988)
- Third-party aggregators: ShortSqueeze.com, Fintel.io

**D&O risk signals**:
- **Short interest as % of float**: >10% = significant bearish sentiment
- **Days to cover**: >5 days = heavily shorted
- **Short interest trend**: Increasing short interest = growing skepticism
- **Short squeeze risk**: High SI + low float = potential for extreme volatility events (a la GameStop)
- **Fails-to-deliver**: Persistent FTDs indicate potential naked shorting or settlement concerns

**Access method**: FINRA data (free download), yfinance (includes basic SI), SEC fails-to-deliver data (free, twice monthly)

**Reliability**: MEDIUM -- data is 2 weeks old by time of publication; short positions can change rapidly

**Current system usage**: PARTIAL -- yfinance provides basic short interest. Scoring factor F6 (Short Interest, 8pts) uses this.

**Gaps**: No direct FINRA short interest data feed; no fails-to-deliver analysis; no days-to-cover trend tracking.

---

### 1.5 Court & Litigation Databases

**What it is**: Federal and state court records, dockets, and specialized litigation databases.

**Sources and access**:

| Source | What | Access | Cost |
|--------|------|--------|------|
| **Stanford SCAC** | 5,811+ securities class actions since 1995 | Web scraping (Playwright) | Free |
| **CourtListener/RECAP** | Hundreds of millions of docket entries, millions of PACER documents | REST API, bulk data | Free |
| **PACER** | Official federal court electronic records | PACER API (REST/JSON) | $0.10/page, $3 cap per document |
| **Docket Alarm** | Litigation analytics and outcomes | API | Paid |
| **UniCourt** | Federal court records API | Enterprise API | Paid |
| **Stanford NPE Litigation** | Patent troll/NPE lawsuits since 2000 | Web | Free |

**D&O risk signals**:
- **Active securities class actions**: Strongest single predictor of D&O loss (F1, 20pts max)
- **Settlement amounts and timing**: Historical loss development patterns
- **Derivative lawsuits**: Board-level governance challenges
- **Lead counsel identity**: Top-tier plaintiff firms (Bernstein Litowitz, Robbins Geller) = higher settlement probability
- **Case progression**: Motion to dismiss outcomes, class certification status
- **Multi-district litigation (MDL)**: Product liability or mass tort exposure

**Reliability**: HIGH for federal courts; MEDIUM for state courts (less standardized access)

**Current system usage**: YES -- Stanford SCAC via Playwright MCP; CourtListener API; SEC EFTS for legal proceedings in filings. `litigation_client.py` runs web searches first, then SEC references.

**Gaps**:
- State court litigation not systematically tracked
- No lead counsel tier analysis against known plaintiff firm database (config exists in `plaintiff_firms.json` but extraction/matching unclear)
- No case progression/outcome tracking over time
- No derivative lawsuit specific tracking
- No MDL/mass tort exposure assessment

---

### 1.6 SEC Enforcement Databases

**What it is**: SEC enforcement actions against companies and individuals for securities law violations.

**Sources**:

| Source | What | Access |
|--------|------|--------|
| **SEED (NYU/Cornerstone)** | All SEC enforcement actions vs. public companies since 1972 | Free academic database |
| **SEC AAER Database** | Accounting/auditing enforcement releases since 1982 | SEC website + sec-api.io API |
| **SEC Litigation Releases** | All SEC civil/admin enforcement | sec.gov/litigation |
| **SEC Administrative Proceedings** | Administrative orders and settlements | sec.gov/litigation |

**D&O risk signals**:
- **Active SEC investigation**: Strongest indicator (F1 scoring, up to 20pts)
- **AAER history**: Prior accounting fraud enforcement predicts future issues
- **Wells Notice receipt**: Pre-enforcement notification (disclosed in 8-K or 10-K)
- **Consent decrees**: Limits on future activities, ongoing monitoring obligations
- **Enforcement trends by sector**: Life sciences and disclosure cases remain core focus in 2025-2026

**FY2025 context**: SEC enforcement actions dropped 27% to 313 (lowest in a decade) under new administration, with total monetary settlements declining 45% to $808M. Expected to rebound in certain areas in FY2026.

**Reliability**: HIGH -- official government records

**Current system usage**: PARTIAL -- blind spot sweep searches for "SEC subpoena Wells notice" and SEC EFTS references. No direct SEED or AAER database integration.

**Gaps**: No systematic AAER tracking; no SEED database queries; no Wells Notice detection in 8-K/10-K filings; no enforcement trend analysis by sector.

---

### 1.7 PCAOB Inspection Reports

**What it is**: Public Company Accounting Oversight Board inspection reports on audit firms, including deficiency findings.

**Where to find it**: https://pcaobus.org/oversight/inspections/firm-inspection-reports (downloadable datasets in CSV, XML, JSON going back to 2018)

**D&O risk signals**:
- **Audit firm deficiency rate**: High deficiency rates at the audit firm = higher risk of audit failures
- **Specific engagement deficiencies**: If the target company's audit was flagged
- **Audit firm size and specialization**: Smaller firms auditing large companies = higher risk
- **Remediation failures**: Non-remediated Part II findings (published after 12 months)

**Access method**: PCAOB website (free download, machine-readable datasets)

**Reliability**: HIGH -- regulatory inspection data

**Current system usage**: NO

**Gap**: Complete gap. PCAOB data could cross-reference with auditor identified from 10-K to assess audit quality risk.

---

## 2. Unstructured Intelligence Sources

### 2.1 Short Seller Reports

**What it is**: Investigative research reports published by activist short sellers who take short positions and then publish evidence of fraud, accounting manipulation, or business model problems.

**Key firms**: Hindenburg Research (shutting down 2025), Muddy Waters Research, Citron Research, Viceroy Research, Grizzly Research, Kerrisdale Capital, Blue Orca Capital, Wolfpack Research, Spruce Point Capital, Jehoshaphat Research

**Where to find reports**:
- **Breakout Point** (https://breakoutpoint.com/): Tracks ~42 active short seller firms, campaign database, real-time alerts
- **Individual firm websites**: Most publish reports publicly (e.g., hindenburgresearch.com, muddywatersresearch.com)
- **Twitter/X**: Many firms announce via social media first
- **Web search**: `"{company}" short seller report` or `"{company}" Hindenburg Muddy Waters Citron`

**D&O risk signals**:
- **Target of activist short report**: Immediate governance/fraud risk indicator
- **Report allegations**: Accounting fraud, related party transactions, undisclosed liabilities, business model concerns
- **Stock price reaction**: Magnitude of post-report decline indicates market credibility assessment
- **Historical accuracy**: Citron's Valeant investigation led to $1.21B class action; Hindenburg's Nikola report led to 80% stock decline and fraud conviction
- **Repeat targeting**: Companies targeted multiple times by different firms

**Access method**: Broad web search (primary), Breakout Point (tracker), individual firm websites, Twitter/X monitoring

**Reliability**: LOW-MEDIUM -- short sellers have financial incentives but also strong track records. Require cross-validation. Single-source = LOW confidence; corroborated = MEDIUM.

**Current system usage**: PARTIAL -- blind spot sweep includes `"{company}" short seller report Hindenburg Muddy Waters Citron` search. Scoring factor F6 (Short Interest, 8pts) partially captures this.

**Gaps**: No Breakout Point database integration; no structured parsing of short seller report allegations; no tracking of report accuracy/outcomes; no alert for new reports targeting portfolio companies.

---

### 2.2 Whistleblower & Scientific Integrity Sites

**What it is**: Platforms where whistleblowers, scientists, and researchers flag potential fraud, misconduct, or data manipulation.

**Sources**:

| Source | Focus | D&O Signal | URL |
|--------|-------|------------|-----|
| **SEC Whistleblower Program** | Securities fraud tips (~27,000 tips in FY2025) | Tip volume by category (aggregate stats only; individual tips not public) | sec.gov/whistleblower |
| **PubPeer** | Scientific paper integrity | 63.7% of flagged articles have potential data/image manipulation; biotech investors get early warning of scientific fraud | pubpeer.com |
| **Retraction Watch** | Paper retractions database (26,000+ retractions) | Retracted papers underlying drug approvals, clinical trials, or product claims | retractionwatch.com |
| **OSHA Whistleblower Program** | Workplace safety + SOX retaliation | SOX whistleblower complaints indicate possible securities fraud + retaliation culture | osha.gov/whistleblower |
| **FCA (False Claims Act) qui tam** | Government fraud | DOJ recovered $6.8B in FCA settlements FY2025; signals for healthcare/defense companies | justice.gov |

**D&O risk signals**:
- **PubPeer flags on company-sponsored research**: Critical for biotech/pharma -- if key publications underlying drug approvals are questioned, D&O exposure escalates dramatically
- **Retracted papers by company executives or funded researchers**: Direct liability concern
- **OSHA SOX complaint volume**: High complaint volume = toxic culture + potential securities fraud
- **SEC whistleblower award announcements**: Can sometimes identify subject companies

**Access method**: Broad web search (primary), PubPeer API/search, Retraction Watch database search, OSHA search

**Reliability**: LOW for unverified complaints; MEDIUM for PubPeer with expert analysis; HIGH for confirmed retractions and FCA settlements

**Current system usage**: PARTIAL -- blind spot sweep includes `"{company}" restatement whistleblower scandal"`. No PubPeer or Retraction Watch integration.

**Gaps**: No PubPeer search for company executives' publications; no Retraction Watch cross-reference; no OSHA SOX complaint tracking; no FCA qui tam monitoring. Critical gap for biotech/pharma/life sciences companies.

---

### 2.3 Employee Sentiment (Glassdoor/Indeed)

**What it is**: Employee reviews and ratings on employer review platforms that can serve as early warning indicators of corporate misconduct.

**Where to find it**: Glassdoor.com, Indeed.com

**Research backing**: Harvard Business School research found that specific language patterns in Glassdoor reviews can distinguish between firms with high and low numbers of violations -- **at least a year before misconduct was exposed by whistleblowers or press**. Wells Fargo risk indicators spiked on Glassdoor from 2009-2013, years before the fake accounts scandal became public.

**D&O risk signals**:
- **Overall rating decline**: Sudden drops in employee satisfaction correlate with internal problems
- **CEO approval rating**: Low/declining approval = leadership risk
- **"Culture" keyword analysis**: Toxic culture language predicts SEC fraud investigations
- **Review volume spikes**: Sudden increase in reviews (especially negative) = internal crisis
- **Specific keyword flags**: "ethics," "compliance," "legal," "fraud," "retaliation," "hostile," "toxic"
- **Comparison to industry peers**: Below-industry-average ratings

**Access method**: Web scraping (Playwright MCP), Glassdoor API (limited/deprecated), broad web search for `"{company}" Glassdoor reviews toxic culture`

**Reliability**: MEDIUM -- research-validated as predictive signal, but subject to selection bias and manipulation. Requires baseline comparison.

**Current system usage**: NO

**Gap**: Complete gap. No employee sentiment data acquisition. This is a validated leading indicator of fraud risk with academic research backing.

---

### 2.4 Proxy Advisory Firms (ISS / Glass Lewis)

**What it is**: ISS and Glass Lewis analyze corporate governance and issue voting recommendations to institutional investors managing $26.8T and $23.6T respectively.

**What's publicly available**:
- Annual proxy voting policy guidelines (published freely)
- Governance scoring frameworks and methodology
- Policy updates for upcoming proxy season (currently 2026 guidelines available)
- Some research reports (behind paywall for most)
- Proxy vote recommendations (partially available through SEC N-PX filings of funds)

**D&O risk signals**:
- **Against recommendations**: ISS/GL recommending "against" management = governance red flag
- **Say-on-pay failures**: Failed say-on-pay votes (disclosed in 8-K) indicate comp concerns
- **Board classification concerns**: ISS opposition to staggered boards, plurality voting
- **Governance scores**: ISS QualityScore (1-10 scale) and Glass Lewis equivalent

**Access method**: Policy guidelines (free download), actual recommendations (limited public access via N-PX, or paid subscription)

**Reliability**: HIGH for published policies; N/A for recommendations unless obtained through subscription or N-PX mining

**Current system usage**: NO

**Gap**: No ISS/Glass Lewis data. Proxy voting recommendations could be partially reconstructed from institutional N-PX filings on EDGAR, though labor-intensive.

---

### 2.5 Social Media Signals

**What it is**: Public discussions about companies on social media platforms, particularly Reddit (r/WallStreetBets, r/stocks, r/investing), Twitter/X, and StockTwits.

**Where to find it**: Reddit API, Twitter/X API (restricted), StockTwits API, broad web search

**Research backing**: Academic research shows Reddit discussions (particularly r/WallStreetBets) exhibit "stronger predictive signals for abrupt volatility shifts" than Twitter sentiment. Social media attention drives retail trading volume and can create or amplify stock price movements.

**D&O risk signals**:
- **Negative sentiment surges**: Coordinated negative discussion can precede or amplify stock drops
- **Fraud allegations on forums**: Early whistleblower-type disclosures
- **Short squeeze dynamics**: Reddit-driven short squeezes create D&O exposure for companies caught in the crossfire
- **Unusual attention patterns**: Sudden spikes in social media mentions
- **Executive-specific criticism**: Personal attacks on executives can indicate deeper issues

**Access method**: Broad web search (primary), Reddit API (free tier), StockTwits public data

**Reliability**: LOW -- noise-to-signal ratio is high; manipulation risk; requires careful filtering

**Current system usage**: NO

**Gap**: No social media sentiment monitoring. Low priority for initial implementation but valuable as a confirming signal.

---

## 3. News & Media Signals

### 3.1 News Monitoring & Sentiment

**What it is**: Monitoring financial news, investigative journalism, and trade publications for company-specific risk signals.

**Sources**:
- **Financial press**: WSJ, NYT, FT, Bloomberg, Reuters
- **Investigative journalism**: ProPublica, The Intercept, industry-specific outlets
- **Trade publications**: Industry-specific (e.g., STAT News for biotech, American Banker for financial services)
- **Analyst downgrades**: Publicly visible through news and filing cross-references
- **Wire services**: PR Newswire, Business Wire (company press releases)

**D&O risk signals**:
- **Negative news volume spike**: Sudden increase in negative coverage
- **Investigative reporting**: Long-form investigations often precede enforcement actions
- **Analyst downgrade clusters**: Multiple downgrades in short window
- **Management credibility language**: News tone around earnings calls, guidance
- **"Concerns," "investigation," "probe" language**: Specific risk-indicator keywords
- **Loughran-McDonald financial sentiment dictionary**: 2,355 negative words, 297 uncertainty words, 904 litigious words specifically calibrated for financial text analysis

**Access method**: Brave Search MCP (primary), web scraping (Playwright), RSS feeds, news APIs

**Reliability**: MEDIUM -- varies by source. Major financial press = HIGH; blogs/commentary = LOW

**Current system usage**: YES -- `news_client.py` uses WebSearchClient for news/sentiment acquisition. Blind spot sweep searches cover litigation, regulatory, short seller, whistleblower, and industry regulatory categories.

**Gaps**:
- No structured sentiment scoring using Loughran-McDonald dictionary
- No news volume trend analysis (frequency of mentions over time)
- No investigative journalism specific monitoring
- No analyst downgrade tracking
- No earnings call tone analysis

---

### 3.2 Congressional & Legislative Signals

**What it is**: Congressional hearings, investigations, subpoenas, and legislative actions targeting specific companies or industries.

**Where to find it**:
- GovInfo (govinfo.gov): Congressional hearing transcripts
- Congress.gov: Committee schedules, witness lists, testimony
- Committee websites: Prepared statements, often available day-of
- Library of Congress: Historical hearings archive

**D&O risk signals**:
- **Subpoena or testimony demand**: Direct indication company is under political scrutiny
- **Hearing mentions**: Company named in hearing title or witness testimony
- **Proposed legislation targeting industry**: Regulatory risk indicator
- **Bipartisan attention**: More dangerous than single-party interest

**Access method**: Broad web search (`"{company}" congressional hearing subpoena investigation`), GovInfo.gov, committee RSS feeds

**Reliability**: MEDIUM -- political theater vs. genuine enforcement risk varies. Bipartisan committee actions = higher signal.

**Current system usage**: NO

**Gap**: No congressional investigation tracking. Web search could catch major hearings, but no systematic monitoring.

---

## 4. Regulatory & Government Sources

### 4.1 DOJ Enforcement

**What it is**: Department of Justice criminal and civil enforcement actions against corporations.

**Sources**:
- DOJ Criminal Division Fraud Section Press Releases (https://www.justice.gov/criminal/press-room)
- DOJ Civil Division Fraud Section Press Releases (https://www.justice.gov/civil/fraud-section-press-releases)
- False Claims Act settlements and judgments ($6.8B in FY2025)
- Deferred Prosecution Agreements (DPAs) and Non-Prosecution Agreements (NPAs)

**D&O risk signals**:
- **Active DOJ investigation**: Maximum severity -- criminal liability for executives
- **DPA/NPA terms**: Ongoing monitoring, compliance obligations
- **False Claims Act actions**: Major exposure for healthcare, defense, government contractor companies
- **FCPA enforcement**: Foreign bribery investigations
- **Individual indictments**: Personal liability for directors/officers

**Access method**: Broad web search (`"{company}" DOJ investigation indictment`), DOJ press release pages, news monitoring

**Reliability**: HIGH -- official government proceedings

**Current system usage**: PARTIAL -- blind spot sweep catches "SEC subpoena Wells notice" but not DOJ-specific terms like "DOJ investigation," "indictment," "deferred prosecution agreement."

**Gap**: No DOJ-specific search queries in blind spot sweep; no systematic False Claims Act monitoring; no FCPA-specific checks.

---

### 4.2 State Attorney General Actions

**What it is**: State-level enforcement actions covering consumer protection, data privacy, environmental, and antitrust violations.

**Sources**:
- **StateAG.org**: Cross-state database of AG actions (maintained by Prof. Paul Nolette)
- **NAAG/NAGTRI**: National Association of Attorneys General resources
- **Individual state AG websites**: Searchable databases vary by state
- **Multi-state actions**: Coordinated enforcement across multiple states (highest severity)

**D&O risk signals**:
- **Multi-state AG investigation**: Significant exposure (e.g., opioid litigation, data breaches)
- **State consumer protection actions**: Product safety, deceptive practices
- **State data privacy enforcement**: CCPA, state privacy law violations
- **State environmental enforcement**: State-level EPA equivalent actions
- **Settlement amounts and terms**: Consent decrees with ongoing obligations

**Access method**: Broad web search (`"{company}" attorney general investigation settlement`), StateAG.org database, individual state AG websites

**Reliability**: HIGH for confirmed actions; MEDIUM for investigations (may not be publicly announced)

**Current system usage**: NO -- blind spot sweep does not include state AG search terms

**Gap**: Complete gap. State AG actions are an increasingly important enforcement vector, especially for data privacy, consumer protection, and environmental issues. Need search queries like `"{company}" attorney general" investigation settlement state`.

---

### 4.3 EPA / Environmental Enforcement

**What it is**: Environmental violations, permits, inspections, and enforcement actions tracked by the EPA.

**Where to find it**: EPA ECHO (https://echo.epa.gov/) -- Enforcement and Compliance History Online, covering 800,000+ regulated facilities

**Data available**:
- Clean Air Act (CAA) violations and inspections
- Clean Water Act (CWA) violations
- Resource Conservation and Recovery Act (RCRA) violations
- Safe Drinking Water Act (SDWA) compliance
- Toxics Release Inventory (TRI) data
- Penalty amounts and enforcement history

**D&O risk signals**:
- **Significant Non-Compliance (SNC) status**: Formal designation of serious violations
- **Penalty history**: Large or repeated penalties indicate systematic problems
- **Consent decrees**: Ongoing monitoring and remediation obligations
- **Toxic release volumes**: Environmental liability exposure
- **Industry-specific patterns**: Chemical, energy, manufacturing sectors

**Access method**: EPA ECHO search (free, web interface + downloadable data), broad web search

**Reliability**: HIGH -- regulatory data with inspection records

**Current system usage**: PARTIAL -- blind spot sweep includes `"{company}" FDA warning CFPB OSHA` but not EPA specifically

**Gap**: No EPA ECHO integration; EPA not in search terms; no TRI data analysis. Relevant for industrial, energy, and chemical companies.

---

### 4.4 OSHA / Workplace Safety

**What it is**: Occupational Safety and Health Administration inspection data, citations, and violations.

**Where to find it**: https://www.osha.gov/ords/imis/establishment.html (Establishment Search), https://www.osha.gov/data

**Data available**:
- Inspection details, citations, and violation classifications
- Penalty amounts and case statuses
- Injury and illness data (electronically submitted)
- Severe injury and fatality reports
- Chemical exposure health data

**D&O risk signals**:
- **Willful violations**: Highest severity -- indicates management knowledge of hazard
- **Repeated violations**: Systematic safety failures
- **Fatality investigations**: Maximum exposure
- **SOX whistleblower complaints through OSHA**: Indicates potential securities fraud + retaliation
- **Penalty trends**: Increasing penalties = worsening compliance

**Access method**: OSHA Establishment Search (free, web), downloadable data, broad web search

**Reliability**: HIGH -- regulatory inspection data

**Current system usage**: PARTIAL -- blind spot sweep mentions OSHA in search template

**Gap**: No direct OSHA database queries; no SOX whistleblower complaint tracking through OSHA.

---

### 4.5 FTC Enforcement

**What it is**: Federal Trade Commission enforcement actions covering antitrust and consumer protection.

**Where to find it**:
- Cases and Proceedings: https://www.ftc.gov/legal-library/browse/cases-proceedings
- Competition Enforcement Database: https://www.ftc.gov/competition-enforcement-database
- Case Document Search: https://www.ftc.gov/legal-library/browse/cases-proceedings/case-document-search

**D&O risk signals**:
- **Antitrust investigations**: Merger challenges, price-fixing, monopoly conduct
- **Consumer protection actions**: False advertising, privacy violations, data security
- **Consent orders**: Ongoing compliance obligations
- **Civil penalties**: Financial exposure

**Access method**: FTC website (free, searchable), broad web search

**Reliability**: HIGH -- official government records

**Current system usage**: NO

**Gap**: No FTC enforcement monitoring. Relevant for consumer-facing and technology companies.

---

### 4.6 CFPB Consumer Complaints

**What it is**: Consumer Financial Protection Bureau's public database of consumer complaints against financial companies.

**Where to find it**: https://www.consumerfinance.gov/data-research/consumer-complaints/search/ (searchable web interface + public API)

**Data available**: Complaint type, company name, response status, timely response indicator, consumer disputed status. API returns JSON/CSV/XLS.

**D&O risk signals**:
- **Complaint volume trends**: Increasing complaints = product or service problems
- **Complaint types**: Specific complaint categories (e.g., deceptive lending, unfair practices)
- **Company response patterns**: Poor response rates indicate governance failures
- **Comparison to industry peers**: Above-average complaint rates

**Access method**: CFPB API (free, documented at cfpb.github.io/ccdb5-api/), web search

**Reliability**: MEDIUM -- complaints are not verified; not statistically representative. But volume trends are meaningful.

**Current system usage**: PARTIAL -- blind spot sweep mentions CFPB in search template

**Gap**: No direct CFPB API integration; no complaint trend analysis. Important for financial services companies.

---

### 4.7 BBB Complaints

**What it is**: Better Business Bureau ratings, reviews, and complaint history for 6.3M+ businesses.

**Where to find it**: https://www.bbb.org/search

**D&O risk signals**:
- **BBB rating (A+ to F)**: Based on complaint history, transparency, licensing
- **Complaint patterns**: Volume, type, and response quality
- **Government actions disclosed**: BBB profiles include known government actions

**Access method**: Web scraping (BBB.org), broad web search

**Reliability**: LOW-MEDIUM -- BBB is not a regulatory body; ratings methodology is debated; participation is voluntary

**Current system usage**: NO

**Gap**: Low priority compared to regulatory databases, but could provide supplemental consumer-facing risk data.

---

## 5. Governance & Insider Signals

### 5.1 Insider Trading Patterns (Form 4)

**What it is**: SEC-mandated disclosures when corporate insiders (executives, directors, 10%+ shareholders) buy or sell company stock.

**Where to find it**:
- SEC EDGAR: https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets (downloadable datasets)
- OpenInsider: http://openinsider.com/ (free screener)
- SECForm4.com: https://www.secform4.com/ (analytics)
- InsiderScreener: https://www.insiderscreener.com/ (cluster detection)

**D&O risk signals**:
- **Cluster selling**: Multiple insiders selling simultaneously = strongest signal (often precedes bad news)
- **Unusual volume**: Sales significantly larger than historical pattern
- **Timing relative to disclosures**: Selling before earnings misses, restatements, or negative news
- **C-suite vs. board**: CEO/CFO selling carries more weight than independent director sales
- **10b5-1 plan modifications**: Changes to pre-planned selling programs can indicate awareness of coming problems
- **Net insider buying/selling ratio**: Sustained net selling across multiple quarters

**Academic research**: Network analysis of 12M+ transactions (1986-2012) found that transaction timing similarity networks can identify suspicious patterns.

**Access method**: SEC EDGAR bulk data (free), OpenInsider (free), InsiderScreener (free)

**Reliability**: HIGH for raw data; MEDIUM for signal interpretation (many benign explanations for selling)

**Current system usage**: NO -- Form 4 data not acquired or analyzed

**Gap**: Critical gap. Insider trading patterns are a key D&O risk factor. Scoring factor F2 (Stock Decline) references "insider trading amplifier" in description but the data is not currently acquired. Need: cluster selling detection, timing analysis relative to material events, unusual volume flagging.

---

### 5.2 Executive Turnover & Departures

**What it is**: Tracking changes in C-suite executives, board members, and other key officers through 8-K Item 5.02 filings and news.

**Research backing**: Academic databases track CEO and CFO turnover in S&P 1500 firms (2000-2022). Research shows:
- CEOs and CFOs face 14% and 10% greater replacement probability around restatements
- CFOs are often "made scapegoats for financial fraud or misrepresentation"
- Non-CEO/non-CFO turnover also increases financial reporting risk perception
- Forced CEO turnover significantly predicts forced CFO turnover

**D&O risk signals**:
- **CFO departure**: Strongest signal (financial reporting risk). Particularly if: no clear successor, mid-year departure, or no farewell press release
- **CEO departure**: Especially if forced/sudden, or during ongoing investigation
- **Auditor rotation + CFO departure**: Combined signal is very high risk
- **Multiple executive departures in short window**: Systemic problem indicator
- **General Counsel departure**: Legal risk indicator
- **Board member resignations**: Especially with public disagreement statements (8-K Item 5.02 requires reason disclosure)

**Access method**: 8-K Item 5.02 monitoring (EdgarTools), broad web search (`"{company}" CEO CFO resign departure`), news monitoring

**Reliability**: HIGH for filing-based data; MEDIUM for interpretation of reasons

**Current system usage**: PARTIAL -- Scoring factor F10 (Officer Stability, 2pts) exists but data extraction for executive tenure returns None. 8-K Item 5.02 not systematically parsed.

**Gap**: Major gap between the scoring factor's existence and actual data acquisition. Need: 8-K Item 5.02 event stream monitoring, executive appointment date extraction from DEF 14A, departure pattern analysis.

---

### 5.3 Auditor Changes & Going Concern Opinions

**What it is**: Changes in a company's independent auditor (disclosed via 8-K Item 4.01) and auditor opinions expressing doubt about a company's ability to continue operating.

**Data sources**:
- 8-K Item 4.01 filings (auditor change disclosures)
- 8-K Item 4.02 filings (non-reliance on previously issued financial statements)
- 10-K auditor's report (going concern opinion)
- Audit Analytics (commercial -- restatement database, auditor changes, going concern database)
- PCAOB inspection reports (discussed in Section 1.7)

**D&O risk signals**:
- **Auditor resignation (vs. non-renewal)**: Resignation is far more severe -- suggests disagreements on accounting treatment
- **Downgrade from Big 4 to smaller firm**: Potential red flag for financial reporting quality
- **Going concern opinion**: 1,674 companies received in FY2021 (26.8% increase over FY2020). Strong predictor of financial distress.
- **Non-reliance on prior financials (8-K 4.02)**: Signals upcoming restatement
- **Rapid auditor changes**: Multiple auditors in 2-3 years = very high risk
- **Combined signals**: Auditor change + CFO departure + restatement = maximum risk cluster

**Access method**: 8-K Item 4.01/4.02 monitoring (EdgarTools), 10-K auditor report parsing, Audit Analytics (paid), broad web search

**Reliability**: HIGH -- all based on mandatory SEC filings

**Current system usage**: PARTIAL -- Scoring factor F3 (Restatement/Audit Issues, 12pts) covers this conceptually, but actual 8-K Item 4.01/4.02 event parsing not implemented.

**Gap**: No 8-K event stream monitoring for auditor changes; no going concern opinion extraction from 10-K; no restatement tracking. Audit Analytics is commercial and expensive.

---

### 5.4 Executive Compensation Analysis

**What it is**: Compensation data for named executive officers disclosed in DEF 14A proxy statements.

**D&O risk signals**:
- **Excessive total compensation vs. peers**: Attracts shareholder lawsuits
- **Pay-for-performance disconnect**: High comp + poor stock performance = litigation target
- **Golden parachute provisions**: Change-of-control payments that misalign incentives
- **Related party transactions**: Self-dealing, related entity contracts
- **Failed say-on-pay vote**: Direct shareholder rejection of compensation plan (disclosed in 8-K)
- **Compensation clawback provisions**: Absence of clawbacks = weaker governance
- **Stock-heavy compensation without holding requirements**: Incentivizes short-term stock price inflation

**Access method**: DEF 14A parsing (EdgarTools), XBRL compensation data (limited), broad web search

**Reliability**: HIGH -- mandatory SEC disclosures

**Current system usage**: PARTIAL -- DEF 14A is acquired but compensation parsing is incomplete.

**Gap**: Need structured extraction of: total comp for NEOs, pay-for-performance analysis, say-on-pay vote results, related party transaction identification, peer compensation benchmarking.

---

### 5.5 Activist Investor Campaigns

**What it is**: Activist investors who acquire significant positions and push for changes in corporate strategy, governance, or management.

**Tracking sources**:
- **13D Monitor** (https://www.13dmonitor.com/): Comprehensive 13D/13G/13F analysis
- **Conference Board Activist Surveillance**: 13D filings, proxy fights, exempt solicitations
- **Fintel** (https://fintel.io/activists): Free 13D screener
- **Whale Wisdom** (https://whalewisdom.com/schedule13d): 13D/G filings since 2006
- **SEC EDGAR**: Schedule 13D filings directly

**D&O risk signals**:
- **13D filing with activist intent**: Board change demands, strategy criticism
- **Proxy contest initiation**: Attempt to replace board members
- **Exempt solicitations (14A-103)**: Public letters to shareholders criticizing management
- **Known activist involvement**: Firms in `activist_investors.json` config (Carl Icahn, Elliott Management, Starboard Value, etc.)
- **Campaign escalation**: Letter -> 13D -> proxy fight -> consent solicitation

**Access method**: SEC EDGAR 13D filings (EdgarTools), broad web search (`"{company}" activist investor proxy fight`), Fintel (free)

**Reliability**: HIGH for filings; MEDIUM for campaign outcome prediction

**Current system usage**: PARTIAL -- `activist_investors.json` config exists. Unclear if systematically used in acquisition/analysis.

**Gap**: No systematic 13D monitoring; no proxy fight tracking; no campaign escalation detection. The config file exists but may not be connected to acquisition pipeline.

---

## 6. Alternative & Emerging Data

### 6.1 WARN Act / Layoff Tracking

**What it is**: Worker Adjustment and Retraining Notification Act requires 60-day advance notice of mass layoffs (50+ employees) at companies with 100+ employees.

**Where to find it**:
- **WARNTracker.com**: Live tracking across states, with office-level detail
- **layoffdata.com**: Standardized WARN notices from 49 states, 80,000+ notices, 8.6M+ workers
- **Individual state databases**: CA (edd.ca.gov), NY (dol.ny.gov), TX (twc.texas.gov), WA (esd.wa.gov)

**D&O risk signals**:
- **Mass layoff announcements**: Indicate financial distress or strategic restructuring
- **Layoff timing relative to guidance**: Layoffs shortly after positive guidance = potential misrepresentation
- **Facility closures**: More severe than layoffs; indicates fundamental business problems
- **Multiple WARN notices in succession**: Accelerating deterioration
- **Comparison to peers**: Industry-wide vs. company-specific layoffs

**Access method**: WARNTracker.com (free), layoffdata.com (searchable), state databases (free), broad web search

**Reliability**: HIGH for WARN filings; MEDIUM for non-WARN layoff reporting

**Current system usage**: NO

**Gap**: No WARN Act tracking. Valuable early indicator of financial distress (F8, 8pts) and potential securities fraud if layoffs contradict prior public statements.

---

### 6.2 Patent & IP Litigation

**What it is**: Patent filing trends, IP litigation, and innovation trajectory indicators.

**Sources**:
- **USPTO**: Patent filings, grants, and assignments
- **Stanford NPE Litigation Database**: Patent troll lawsuits since 2000
- **Lex Machina / Docket Navigator**: Patent litigation analytics (paid)
- **Google Patents**: Free patent search

**D&O risk signals**:
- **Patent infringement lawsuits**: Defense costs and potential damages
- **Patent portfolio decline**: Declining filing rates may indicate innovation slowdown
- **Trade secret litigation**: Often accompanies employee departures to competitors
- **NPE/patent troll targeting**: Some companies are repeat targets

**Access method**: USPTO (free), Stanford NPE database (free), broad web search, Google Patents

**Reliability**: HIGH for filing data; MEDIUM for litigation outcome prediction

**Current system usage**: NO

**Gap**: Patent/IP litigation not tracked. Relevant for technology, pharma, and manufacturing companies. Lower priority than other gaps.

---

### 6.3 Supply Chain Data

**What it is**: Import/export records, shipping data, and supply chain monitoring.

**Sources**:
- **Panjiva (S&P Global)**: 2B+ shipment records from 22 customs sources, AI-based risk detection (paid)
- **ImportGenius**: Import/export records (paid)
- **US Customs data**: Bill of lading records (partially public)

**D&O risk signals**:
- **Supply chain disruption**: Shipping volume changes indicate production/demand problems
- **Sanctions exposure**: Trading with sanctioned entities
- **Geographic concentration risk**: Over-reliance on single-country supply chains
- **Dual-use export concerns**: Regulatory risk for technology companies

**Access method**: Panjiva/ImportGenius (paid), broad web search for supply chain issues

**Reliability**: HIGH for customs data; MEDIUM for derived risk signals

**Current system usage**: NO

**Gap**: Supply chain data is primarily behind commercial paywalls. Broad web search for supply chain disruptions (`"{company}" supply chain disruption recall shortage`) could partially address this.

---

### 6.4 Job Posting Analysis

**What it is**: Analysis of company job postings as indicators of business health, strategic direction, and potential problems.

**Where to find it**: Indeed Hiring Lab (public research), LinkedIn (job listings), company career pages

**D&O risk signals**:
- **Sudden hiring freeze**: Contradicts growth guidance = potential misrepresentation
- **Legal/compliance hiring surge**: May indicate internal investigation or regulatory scrutiny
- **Mass removal of job postings**: Precedes layoff announcements
- **Executive position postings**: CFO/CLO/CISO openings indicate recent or impending departures
- **Comparison to industry trends**: Company-specific vs. industry-wide patterns

**Access method**: Broad web search, Indeed (public listings), LinkedIn (public listings)

**Reliability**: LOW-MEDIUM -- indirect signal; many benign explanations for hiring changes

**Current system usage**: NO

**Gap**: No job posting monitoring. Lower priority but useful as confirming signal for executive departure concerns (F10).

---

### 6.5 Financial Sentiment Lexicons

**What it is**: Specialized word lists calibrated for financial text analysis, used to quantify sentiment, uncertainty, and litigiousness in SEC filings and news.

**Primary resource**: Loughran-McDonald Master Dictionary (University of Notre Dame SRAF)
- https://sraf.nd.edu/loughranmcdonald-master-dictionary/
- Free for academic/research use

**Dictionary composition**:
- **Negative**: 2,355 words (e.g., deficit, default, deteriorate)
- **Positive**: 354 words (e.g., achieve, benefit, efficient)
- **Uncertainty**: 297 words (e.g., approximate, contingent, doubt)
- **Litigious**: 903 words (e.g., adjudicate, claimant, defendant)
- **Constraining**: 184 words (e.g., cap, ceiling, limit)
- **Modal strong**: confidence language
- **Modal weak**: hedging language

**D&O risk signals**:
- **Litigious word frequency increase** in 10-K/10-Q over prior year: Signals growing legal exposure awareness
- **Uncertainty word increase**: Management hedging about future performance
- **Negative-to-positive ratio shift**: Deteriorating outlook
- **MD&A tone shift**: Year-over-year tone change in Management Discussion & Analysis section
- **Risk factor verbosity increase**: More risk factor text = more recognized risks

**Access method**: Free download from Notre Dame SRAF

**Reliability**: HIGH -- academically validated, widely used in financial NLP research

**Current system usage**: NO

**Gap**: No financial text sentiment analysis. Could be applied to: 10-K/10-Q filings (especially MD&A and Risk Factors sections), 8-K text, earnings call transcripts, news articles about the company.

---

## 7. Signal-to-Risk Mapping

Maps data sources to the 10 D&O scoring factors used in the system.

### F1: Prior Litigation (20 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| Stanford SCAC | Active securities class actions | YES |
| CourtListener | Federal court docket entries | YES |
| Web search | Broad litigation discovery | YES |
| SEC EFTS | 10-K Item 3 legal proceedings | YES |
| DOJ press releases | Criminal/civil fraud actions | NO |
| State AG databases | Multi-state enforcement | NO |
| FTC enforcement | Antitrust/consumer cases | NO |

### F2: Stock Decline (15 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| yfinance | Price decline from 52-week high | YES |
| Form 4 insider data | Cluster selling before decline | NO |
| Options implied volatility | Pre-decline IV spike | NO |
| Social media | Sentiment shift before decline | NO |

### F3: Restatement/Audit Issues (12 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| 8-K Item 4.01 | Auditor change disclosure | NO |
| 8-K Item 4.02 | Non-reliance on prior financials | NO |
| 10-K auditor report | Going concern opinion | NO |
| AAER database | Prior accounting enforcement | NO |
| SEC comment letters | Accounting policy challenges | NO |
| PCAOB reports | Audit firm deficiency rates | NO |

### F4: IPO/SPAC/M&A (10 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| SEC filings (S-1/S-4) | IPO/SPAC/merger filings | PARTIAL |
| 8-K Item 1.01 | Material agreement (M&A) | NO |
| News search | M&A announcement monitoring | PARTIAL |

### F5: Guidance Misses (10 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| 8-K Item 2.02 | Earnings release | PARTIAL |
| News search | Guidance miss reporting | PARTIAL |
| Stock price reaction | Post-earnings decline | YES |
| Analyst estimates | Consensus vs. actual | NO |

### F6: Short Interest (8 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| yfinance | Short interest ratio | YES |
| FINRA data | Official short interest | NO |
| Breakout Point | Activist short campaigns | NO |
| Short seller reports | Published research | PARTIAL |
| Fails-to-deliver | SEC FTD data | NO |

### F7: Stock Volatility (9 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| yfinance | Beta, historical volatility | YES |
| Options data | Implied volatility | NO |
| Social media | Retail-driven volatility | NO |

### F8: Financial Distress (8 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| XBRL financials | Altman Z-Score, ratios | YES |
| Going concern opinion | 10-K auditor report | NO |
| WARN Act notices | Mass layoff filings | NO |
| Credit rating changes | Rating downgrades | NO |
| CFPB complaints | Financial product issues | NO |

### F9: Governance Issues (6 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| DEF 14A | Board independence, comp | PARTIAL |
| Say-on-pay results | Shareholder vote outcomes | NO |
| 13D filings | Activist investor campaigns | NO |
| Glassdoor | Employee culture signals | NO |
| ISS/Glass Lewis | Governance scores | NO |
| Related party transactions | DEF 14A disclosure | NO |

### F10: Officer Stability (2 pts)
| Signal Source | Signal | Current? |
|--------------|--------|----------|
| 8-K Item 5.02 | Executive departures | NO |
| DEF 14A | Executive tenure data | PARTIAL (returns None) |
| News search | Departure announcements | PARTIAL |
| Job postings | Executive position openings | NO |

---

## 8. Acquisition Priority

### Tier 1: High Impact, Achievable Now (Phase 32 Priority)
These fill the largest scoring gaps and use existing infrastructure (web search, SEC filings):

1. **8-K Event Stream Monitoring** -- Parse Item 4.01 (auditor change), 4.02 (non-reliance), 5.02 (executive departure), 1.01 (material agreements). Fills gaps in F3, F4, F10.
2. **Form 4 Insider Transaction Analysis** -- Cluster selling detection, timing analysis. Fills major F2 gap.
3. **Expanded Blind Spot Search Queries** -- Add DOJ, state AG, FTC, congressional, WARN Act search terms. Fills gaps in F1 + regulatory coverage.
4. **10-K Risk Factor Diff Analysis** -- Year-over-year comparison of Item 1A. Signals emerging risks.
5. **SEC Comment Letter (CORRESP) Monitoring** -- Flag companies receiving SEC review questions.

### Tier 2: High Impact, Moderate Effort
These require new data source integrations but provide significant signal value:

6. **AAER / SEC Enforcement Database** -- Direct query of SEED/NYU database or SEC AAER listings. Critical for F1, F3.
7. **EPA ECHO + OSHA Integration** -- Direct database queries for environmental/workplace violations. Industry-specific but powerful.
8. **CFPB API Integration** -- Complaint volume trends for financial services companies.
9. **Going Concern + Auditor Report Parsing** -- Extract opinion type from 10-K auditor's report. Critical for F3, F8.
10. **Glassdoor Employee Sentiment** -- Research-validated leading indicator. Scraping or search-based.

### Tier 3: Valuable, Longer-Term
These provide supplementary signals or require more complex implementation:

11. **FINRA Direct Short Interest Data** -- Replace yfinance SI with official FINRA data for accuracy.
12. **PubPeer / Retraction Watch** -- Scientific integrity monitoring (high value for biotech/pharma).
13. **Loughran-McDonald Sentiment Analysis** -- Apply financial NLP to 10-K text, news articles.
14. **Schedule 13D / Activist Investor Tracking** -- Connect existing `activist_investors.json` config to live data.
15. **PCAOB Inspection Reports** -- Cross-reference audit firm quality with target company.
16. **WARN Act / Layoff Tracking** -- Financial distress early warning.
17. **Congressional Investigation Monitoring** -- Political/regulatory risk signals.
18. **Patent/IP Litigation Tracking** -- Innovation and legal exposure for tech/pharma.
19. **Options Implied Volatility** -- Market-derived uncertainty signals.
20. **Social Media Sentiment** -- Reddit/Twitter/StockTwits monitoring.

### Tier 4: Nice-to-Have
21. **Supply chain monitoring** (mostly behind paywalls)
22. **Job posting analysis** (indirect, noisy signal)
23. **BBB complaint tracking** (low reliability)
24. **ISS/Glass Lewis scores** (mostly behind paywalls)
25. **Credit rating monitoring** (partially behind paywalls)

---

## Sources

### SEC & EDGAR
- [SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
- [EDGAR Full Text Search (EFTS)](https://www.sec.gov/edgar/search/)
- [SEC Insider Transactions Data Sets](https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets)
- [SEC Form 13F Data Sets](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets)
- [SEC XBRL Data](https://www.sec.gov/data-research/structured-data/inline-xbrl)
- [EdgarTools PyPI](https://pypi.org/project/edgartools/)
- [SEC Accounting and Auditing Enforcement](https://www.sec.gov/enforcement-litigation/accounting-auditing-enforcement-releases)
- [SEC Whistleblower Program](https://www.sec.gov/enforcement-litigation/whistleblower-program)
- [EDGAR XBRL Guide 2026](https://www.sec.gov/files/edgar/filer-information/specifications/xbrl-guide.pdf)
- [XBRL US SEC EDGAR Data](https://xbrl.us/academic-repository/sec-edgar-data/)

### Enforcement & Regulatory
- [SEED Database (NYU/Cornerstone)](https://www.law.nyu.edu/centers/pollackcenterlawbusiness/seed)
- [SEC Enforcement 2025 Year in Review (Harvard)](https://corpgov.law.harvard.edu/2026/01/21/sec-enforcement-2025-year-in-review/)
- [SEC Enforcement FY2025 Actions (Cornerstone)](https://www.cornerstone.com/insights/press-releases/sec-enforcement-actions-fy-2025/)
- [DOJ Fraud Section Press Releases](https://www.justice.gov/civil/fraud-section-press-releases)
- [DOJ Criminal Division Press Room](https://www.justice.gov/criminal/press-room)
- [DOJ FY2025 False Claims Act Report (Wiley)](https://www.wiley.law/alert-Key-Takeaways-from-DOJs-FY-2025-False-Claims-Act-Report)
- [FTC Cases and Proceedings](https://www.ftc.gov/legal-library/browse/cases-proceedings)
- [FTC Competition Enforcement Database](https://www.ftc.gov/competition-enforcement-database)
- [EPA ECHO](https://echo.epa.gov/)
- [OSHA Establishment Search](https://www.osha.gov/ords/imis/establishment.html)
- [CFPB Consumer Complaint Database](https://www.consumerfinance.gov/data-research/consumer-complaints/)
- [CFPB API Documentation](https://cfpb.github.io/ccdb5-api/)
- [StateAG.org Consumer Protection](https://www.stateag.org/policy-areas/consumer-protection)
- [State AG Consumer Protection (NAAG)](https://www.naag.org/issues/consumer-protection/consumer-protection-101/)

### Court & Litigation
- [Stanford SCAC](https://securities.stanford.edu/)
- [Stanford Securities Litigation Analytics](https://sla.law.stanford.edu/)
- [CourtListener / Free Law Project](https://free.law/projects/courtlistener/)
- [RECAP Archive](https://free.law/recap/)
- [PACER](https://pacer.uscourts.gov/)
- [Stanford NPE Litigation Database](https://npe.law.stanford.edu/)

### Market Data
- [yfinance GitHub](https://github.com/ranaroussi/yfinance)
- [FINRA Short Interest Data](https://www.finra.org/finra-data/browse-catalog/equity-short-interest/data)
- [NYSE Group Short Interest](https://www.nyse.com/market-data/reference/nyse-group-short-interest)
- [OpenInsider](http://openinsider.com/)
- [SECForm4.com](https://www.secform4.com/)

### Short Seller & Activist Tracking
- [Breakout Point](https://breakoutpoint.com/)
- [Short Sellers Are Back (Yahoo Finance)](https://finance.yahoo.com/news/short-sellers-back-flurry-big-180013298.html)
- [Hindenburg Research Shutting Down](https://finance.yahoo.com/news/hindenburg-research-shutting-down-highlights-wear-and-tear-of-activist-short-selling-143652817.html)
- [13D Monitor](https://www.13dmonitor.com/)
- [Fintel 13D Screener](https://fintel.io/activists)
- [Whale Wisdom 13D/G](https://whalewisdom.com/schedule13d)

### Audit Quality
- [PCAOB Inspection Reports](https://pcaobus.org/oversight/inspections/firm-inspection-reports)
- [PCAOB New Downloadable Datasets](https://pcaobus.org/news-events/news-releases/news-release-detail/pcaob-makes-available-new-downloadable-datasets-featuring-pcaob-inspection-findings-from-audit-firm-inspection-reports)
- [Audit Analytics AAER Database](https://www.auditanalytics.com/doc/AA_AAERs_ds.pdf)
- [AAER Dataset (USC)](https://sites.google.com/usc.edu/aaerdataset/home)
- [Going Concerns 21-Year Review (Audit Analytics)](https://www.auditanalytics.com/doc/Going_Concerns_A_21-Year_Review.pdf)

### Governance & Proxy
- [ISS and Glass Lewis 2026 Policy Updates (Harvard)](https://corpgov.law.harvard.edu/2026/01/20/iss-and-glass-lewis-2026-policy-updates/)
- [ISS/GL Policy Updates (Gibson Dunn)](https://www.gibsondunn.com/iss-and-glass-lewis-issue-proxy-voting-policy-updates-for-2026/)
- [D&O Looking Ahead 2026 (Woodruff Sawyer)](https://woodruffsawyer.com/insights/do-looking-ahead-guide)
- [Predicting Corporate Governance Risk (Baker & Griffith)](https://chicagounbound.uchicago.edu/uclrev/vol74/iss2/3/)

### Employee Sentiment
- [Glassdoor Reviews Predict Misconduct (HBS)](https://www.library.hbs.edu/working-knowledge/company-reviews-on-glassdoor-petty-complaints-or-signs-of-potential-misconduct)
- [Corporate Fraud Linked to Poor Glassdoor Reviews](https://www.glassdoor.com/research/corporate-fraud-linked-to-poor-glassdoor-reviews/)

### Scientific Integrity
- [PubPeer](https://pubpeer.com/)
- [Online Forums Give Investors Early Warning (STAT News)](https://www.statnews.com/2018/01/30/pubpeer-biotech-investors/)
- [Retraction Watch](https://retractionwatch.com/)

### Financial Sentiment
- [Loughran-McDonald Master Dictionary (Notre Dame SRAF)](https://sraf.nd.edu/loughranmcdonald-master-dictionary/)
- [Financial Sentiment Analysis: Techniques and Applications (ACM)](https://dl.acm.org/doi/10.1145/3649451)
- [Moody's: Power of News Sentiment](https://www.moodys.com/web/en/us/insights/digital-transformation/the-power-of-news-sentiment-in-modern-financial-analysis.html)

### Social Media & Alternative
- [Reddit WallStreetBets Retail Investor Behavior (ScienceDirect)](https://www.sciencedirect.com/science/article/pii/S1057521924006537)
- [WARNTracker.com](https://www.warntracker.com/)
- [WARN Database (layoffdata.com)](https://layoffdata.com/)
- [Panjiva Supply Chain Intelligence](https://panjiva.com/)
- [BBB Search](https://www.bbb.org/search)
- [GovInfo Congressional Hearings](https://www.govinfo.gov/app/collection/chrg)

### D&O Underwriting Context
- [D&O Underwriting: What to Know (Vouch)](https://www.vouch.us/insurance101/directors-and-officers-insurance-underwriting)
- [Information Embedded in D&O Insurance Purchases (Springer)](https://link.springer.com/article/10.1057/gpp.2012.27)
- [Understanding Five D&O Risk Factors (Alliant)](https://alliant.com/news-resources/article-understanding-five-do-risk-factors/)
- [5 Ways Financial Statements Deliver D&O Risk Insights](https://insurancetrainingcenter.com/resource/5-ways-financial-statements-deliver-do-risk-insights/)
- [Alternative Data in Insurance Underwriting (Swiss Re)](https://www.swissre.com/reinsurance/insights/principles-alternative-data-underwriting.html)
- [D&O Evolving Risks in the Boardroom (Moody's)](https://www.moodys.com/web/en/us/insights/insurance/d-o-series-evolving-risks-in-the-boardroom-a-new-era-of-d-o-liability-part-1.html)
- [SEC Enforcement Public Companies 2025-2026 (Cooley)](https://investigations.cooley.com/2025/12/23/sec-public-companies-enforcement-fy-2025-review-and-what-to-expect-in-2026/)
