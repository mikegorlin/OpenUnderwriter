# Executive Forensics Research: D&O Underwriting People Risk

**Date**: 2026-02-11
**Purpose**: Research how to systematically investigate executive and board member backgrounds for D&O underwriting — the highest-priority signal according to experienced underwriters.

**Core Underwriter Question**: "How many lawsuits have these people been involved in when they were on boards or managing other companies? And if we can find anything about their personal life — negative news, legal issues — that gives me the shadiness score."

---

## 1. Data Sources: Free, Paid-Accessible, and Wish-List

### 1.1 FREE Sources (SEC + Public Records + Web)

| Source | What It Provides | Searchable By Individual? | API Available? | URL |
|--------|-----------------|--------------------------|----------------|-----|
| **SEC Action Lookup - Individuals (SALI)** | Defendants in SEC enforcement actions (1995-present) | YES - by name | NO (web form only) | https://www.sec.gov/litigations/sec-action-look-up |
| **SEC EDGAR Full Text Search (EFTS)** | Full text of all EDGAR filings since 2001 | YES - keyword search | YES - `efts.sec.gov/LATEST/search-index` | https://efts.sec.gov/LATEST/search-index |
| **SEC EDGAR Submissions API** | Filing history, company metadata | By CIK/company only | YES - `data.sec.gov/submissions/` | https://data.sec.gov/ |
| **SEC Litigation Releases** | Civil lawsuits brought by SEC | Searchable by text | Browsable, scraped | https://www.sec.gov/enforcement-litigation/litigation-releases |
| **SEC AAERs** | Accounting fraud enforcement actions | By text search | Via EFTS or third-party | https://www.sec.gov/divisions/enforce/friactions.htm |
| **NYU SEED Database** | SEC enforcement actions vs public companies/individuals (2009+) | YES - by defendant name and type "Individual" | NO (web search interface) | https://research.seed.law.nyu.edu/ |
| **Stanford SCAC** | Securities class actions since 1995 (6,879 cases) | By company/ticker; individual search LIMITED | NO (web search, requires free account) | https://securities.stanford.edu/ |
| **FINRA BrokerCheck** | Broker/advisor background: disclosures, disciplinary events, arbitration, criminal | YES - by name or CRD number | Unofficial (no public API; community Node.js wrapper exists) | https://brokercheck.finra.org/ |
| **CourtListener** | Federal court opinions, dockets, oral arguments | YES - by party name (`party_name` param in API v4) | YES - REST API v4, 5000 req/hr, free token | https://www.courtlistener.com/ |
| **PACER Case Locator** | Federal court case index (appellate, district, bankruptcy) | YES - by party name nationwide | YES - PCL REST API (requires PACER account, $0.10/page) | https://pcl.uscourts.gov/ |
| **judyrecords** | 760M+ US court cases (100x more than Google Scholar) | YES - by party name, case name, case number | YES - REST API (structured objects + full-text) | https://www.judyrecords.com/api |
| **OCC Enforcement Actions** | Actions against bank officers/directors/IAPs | YES - by individual name | NO (web search) | https://apps.occ.gov/EASearch |
| **FDIC Enforcement Actions** | Actions against bank-affiliated individuals | YES - search form | NO (web search) | https://orders.fdic.gov/s/searchform |
| **SEC Insider Trading (Form 3/4/5)** | Officer/director stock transactions | By company CIK; then filter by reporting person | YES - EDGAR bulk data (XML) | https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=4 |
| **DEF 14A Proxy Statements** | Director bios, other board seats, compensation, related-party transactions | By company; must parse HTML for individual names | Via EDGAR EFTS + EdgarTools Python library | https://www.sec.gov/cgi-bin/browse-edgar?type=DEF+14A |
| **Brave Search / Web Search** | News articles, blog posts, social media mentions | YES - by name + keywords | YES (MCP tool available) | Via Brave Search MCP |

### 1.2 PAID_ACCESSIBLE (S&P Capital IQ - User Has Access)

| Capability | What It Provides | Individual Searchable? |
|-----------|-----------------|----------------------|
| **People Profiles** | 4.5M+ professionals; biography, education, job history, board memberships, compensation | YES |
| **Board Membership History** | Current and prior board seats across public and private companies | YES |
| **Executive Screening** | Filter executives by function, title, company type, geography | YES |
| **Compensation Data** | Historical executive comp including stock options | YES |
| **Insider Activity** | Trading patterns and options holdings | YES |
| **Professional Affiliations** | Board relationships, committee memberships | YES |
| **Company Financials** | Financial health of companies where exec served | YES (by company) |

**Key Advantage**: S&P Capital IQ is the BEST available source for cross-referencing an executive's full board history and then checking what happened at each of those companies. This enables the "what companies were they at, and did those companies get sued?" workflow.

### 1.3 PAID_OTHER (Wish List - Not Currently Available)

| Source | What It Provides | Why It Matters | Approximate Cost |
|--------|-----------------|----------------|-----------------|
| **LexisNexis** | Comprehensive litigation history, state + federal courts, public records, liens, judgments, UCC filings | Most complete individual litigation history | $$$$ (enterprise) |
| **Westlaw** | Case law, litigation analytics, court records | Deep legal analysis of prior cases | $$$$ (enterprise) |
| **D&O Diary / Kevin LaCroix analysis** | Expert commentary on D&O trends and specific cases | Industry insight (free blog, paid consulting) | Free (blog) |
| **ISS (Institutional Shareholder Services)** | Governance scores, director data, overboarding flags, voting recommendations | Professional governance risk assessment | $$$ (enterprise) |
| **Glass Lewis** | Proxy advisory, governance ratings, overboarding analysis | Proxy advisor perspective on directors | $$$ (enterprise) |
| **Dun & Bradstreet** | Business failure history, company risk scores | Prior company failures while exec served | $$ (per report) |
| **Kroll / Infortal Executive Due Diligence** | Deep background investigations, global records | Professional-grade executive screening | $$$$$ (per investigation) |
| **UniCourt** | 114M+ state + federal cases, standardized data, party normalization | State court coverage (CourtListener/PACER cover federal only) | $$ (API plans) |
| **Bloomberg Terminal** | Board composition, executive profiles, litigation tracking | Real-time data, deep coverage | $$$$ (terminal) |

### 1.4 NOT_AVAILABLE (Public Access Limitations)

| Signal | Why Not Available | Workaround |
|--------|------------------|------------|
| Personal criminal history (non-public) | FCRA restrictions; most states limit public access | Check SEC/FINRA disclosures; web search for news coverage |
| Personal tax liens (since 2018) | IRS stopped reporting to credit bureaus | County recorder searches (manual, jurisdiction-specific) |
| Sealed court records | By definition, sealed | May be referenced in news coverage |
| Private arbitration results | FINRA arbitration public; most others private | Check FINRA BrokerCheck; search for news coverage |
| Ongoing investigations (pre-charge) | Not public until charges filed | Watch for "subject of investigation" language in 10-K risk factors |

---

## 2. Prior Litigation Search: How to Find Executive Involvement in Prior Suits

### 2.1 Step-by-Step Process

**Phase 1: Identify the People**

1. **Parse DEF 14A** (latest proxy statement) to extract:
   - All current directors: full name, age, biography
   - All named executive officers (NEOs): from compensation tables
   - Other board seats held (disclosed in bio paragraphs)
   - Committee memberships (audit, compensation, nominating)
   - Director tenure (year first elected)

2. **Parse 10-K Item 10** (Directors, Executive Officers) for:
   - Officer/director list with titles
   - Any disclosure of "involvement in certain legal proceedings" (Item 401(f) of Reg S-K requires disclosure of certain legal proceedings involving directors/officers in the past 10 years)

3. **Use S&P Capital IQ** to get:
   - Full career history (all prior companies and board seats)
   - Biographical details for name disambiguation
   - Prior company identifiers (CIK, ticker) for targeted searches

**Phase 2: Search for Litigation by Individual Name**

For each executive/director, search these sources in order:

| Priority | Source | Search Strategy | What You Find |
|----------|--------|----------------|---------------|
| 1 | **SEC SALI** | Search exact name | SEC enforcement actions as defendant/respondent |
| 2 | **NYU SEED** | Search defendant name, type=Individual | SEC enforcement vs public companies where they served |
| 3 | **FINRA BrokerCheck** | Search name (for anyone in financial services) | Disclosures, disciplinary history, customer complaints |
| 4 | **Stanford SCAC** | Search by prior company tickers (from S&P Cap IQ career history) | Securities class actions at prior companies |
| 5 | **CourtListener API** | `party_name` search for individual | Federal court cases as party |
| 6 | **PACER Case Locator** | Party name search nationwide | All federal cases (district, bankruptcy, appellate) |
| 7 | **judyrecords** | Full-text and structured search by name | 760M+ state and federal cases |
| 8 | **SEC EFTS** | `"First Last" AND (litigation OR complaint OR fraud)` | Mentions in any SEC filing |
| 9 | **Brave Search** | `"First Last" lawsuit OR litigation OR fraud OR SEC` | News coverage of legal issues |
| 10 | **OCC/FDIC** | Search by name (financial institutions only) | Banking regulatory actions |

**Phase 3: Search by Prior Companies**

For each company in the executive's career history:

1. Search Stanford SCAC for securities class actions filed while exec was at the company
2. Search SEC SALI for enforcement actions against the company during exec's tenure
3. Search SEC EFTS for litigation releases mentioning the company
4. Check if the company went bankrupt (PACER bankruptcy search by company name)
5. Web search for `"Company Name" SEC investigation OR lawsuit OR fraud` with date filters matching tenure

**Phase 4: Cross-Validate and Disambiguate**

- Common names require disambiguation: use middle initials, approximate age, and known employers
- Cross-reference findings from multiple sources to confirm identity
- Flag single-source findings as LOW confidence
- Mark multi-source confirmed findings as HIGH confidence

### 2.2 Name Disambiguation Strategy

Executive names are not unique. The system must handle:

| Problem | Solution |
|---------|----------|
| Common names (e.g., "John Smith") | Use full name from proxy + approximate age + known employers to filter |
| Name variations (Robert vs. Bob) | Search both formal and common variations |
| Maiden/married name changes | Check proxy bio for "formerly known as" |
| Jr./Sr./III suffixes | Include and exclude suffixes in searches |
| International name ordering | Check proxy for cultural context |

For CourtListener and PACER searches: filter results by date range matching when the person was at a specific company, and by court jurisdiction where the company was headquartered.

### 2.3 SEC EDGAR Full-Text Search (EFTS) Queries

The EFTS API at `efts.sec.gov/LATEST/search-index` supports:
- Boolean operators: `AND`, `OR`, `NOT`
- Exact phrase matching: `"John Q. Smith"`
- Date range filtering: `dateRange=custom&startdt=YYYY-MM-DD&enddt=YYYY-MM-DD`
- Form type filtering: `forms=LIT,10-K,DEF 14A`

**Useful queries for executive forensics:**

```
# Find mentions of an executive in SEC filings
"Jane Doe" AND (defendant OR respondent OR litigation OR complaint)

# Find enforcement-related mentions
"Jane Doe" AND (enforcement OR sanction OR violation OR penalty)

# Search across all filing types for a name
"Jane Doe" forms=LIT,AAER,DEF 14A,10-K,8-K

# Search for someone at a specific company
"Jane Doe" AND "Acme Corp" AND (lawsuit OR investigation)
```

---

## 3. Personal Background: What's Searchable and What Matters

### 3.1 What Experienced D&O Underwriters Care About (Priority Order)

Based on industry research, D&O underwriters rank personal background signals as follows:

| Priority | Signal | Why It Matters | Source |
|----------|--------|---------------|--------|
| **1** | **Prior securities litigation as defendant** | Direct predictor of future claims | SCAC, CourtListener, PACER |
| **2** | **SEC enforcement actions** | Regulatory history is strongest red flag | SEC SALI, NYU SEED |
| **3** | **Insider trading patterns** | "Most dangerous component of a serious SCA" per D&O Diary | SEC Form 4 data |
| **4** | **Prior company bankruptcies** | Failed governance oversight | PACER bankruptcy search, S&P Cap IQ |
| **5** | **Personal bankruptcy** | Financial judgment and integrity signal | PACER bankruptcy search |
| **6** | **Excessive compensation** | "Single most reliable risk marker" per industry observers | DEF 14A compensation tables |
| **7** | **FINRA/regulatory sanctions** | Professional disciplinary history | FINRA BrokerCheck, OCC, FDIC |
| **8** | **Negative news coverage** | Reputation and undiscovered risks | Brave Search, web scraping |
| **9** | **Criminal proceedings** | Integrity and judgment | FINRA BrokerCheck disclosures, news search |
| **10** | **Related party transactions** | Self-dealing risk | DEF 14A related-party section |
| **11** | **Frequent job/board changes** | Instability, forced departures | S&P Cap IQ career history, proxy bios |
| **12** | **Academic credential issues** | Integrity signal (rare but devastating) | Web search for controversies |

### 3.2 What Doesn't Matter (Per Underwriter Guidance)

- Personal divorce (unless it involves fraud or asset concealment)
- Minor traffic violations
- Political donations or affiliations
- Social media opinions (unless they constitute securities law violations)
- Hobbies or lifestyle choices

### 3.3 FINRA BrokerCheck: The Hidden Gold Mine

For any executive or director who has been in financial services, FINRA BrokerCheck reveals:

- **Customer disputes**: complaints, arbitrations, settlements
- **Regulatory actions**: by FINRA, SEC, state regulators
- **Employment terminations**: specifically terminations related to conduct
- **Criminal disclosures**: charges, convictions
- **Financial disclosures**: bankruptcy, judgments, liens
- **Civil judicial disclosures**: civil court actions

**Access strategy**: BrokerCheck has no public API. Options:
1. Manual web search at https://brokercheck.finra.org/ (one at a time)
2. Community Node.js wrapper: https://github.com/whats-a-handle/finra-broker-check
3. FINRA Query API (requires developer account): https://developer.finra.org/
4. Playwright automation (our MCP tool) to programmatically search and extract

The FINRA individual report PDFs follow a predictable URL pattern:
`https://files.brokercheck.finra.org/individual/individual_{CRD_NUMBER}.pdf`

### 3.4 Reg S-K Item 401(f): Required Disclosure of Legal Proceedings

Companies are REQUIRED to disclose if any director or executive officer has been involved in ANY of these during the past 10 years:

1. Petition under federal bankruptcy laws filed by or against any business where person was officer/director/partner
2. Conviction in criminal proceeding or subject of pending criminal case
3. Subject of any order, judgment, or decree permanently or temporarily enjoining from securities activities
4. Found by a court to have violated federal or state securities laws
5. Subject of an order by a commodities regulator
6. Subject of an SEC/CFTC cease-and-desist order
7. Subject of an order by an SRO that bars or limits association
8. Subject of SEC/CFTC enforcement action
9. Subject of federal or state regulatory authority order (banking, insurance, etc.)

**This is a self-reported goldmine in every 10-K filing.** If the company discloses nothing here, it means either:
- The officers/directors are clean, OR
- The company is violating disclosure requirements (also a red flag)

Parse 10-K Item 10 for this section. If present, it's HIGH confidence data.

---

## 4. Shadiness Score Framework: Proposed Quantitative Approach

### 4.1 Score Components

The "Shadiness Score" is an executive-level risk score that aggregates personal risk signals across all named officers and directors. It should be expressed at two levels:

1. **Individual Executive Risk Score** (per person)
2. **Board/Management Aggregate Risk Score** (weighted by role importance)

### 4.2 Individual Executive Risk Score (0-100 scale)

| Category | Max Points | Signals | Source Priority |
|----------|-----------|---------|----------------|
| **Prior Securities Litigation** | 25 | Named defendant in securities class action at ANY company | SCAC, CourtListener, PACER |
| **SEC/Regulatory Enforcement** | 25 | Subject of SEC enforcement action, FINRA sanction, OCC/FDIC action | SEC SALI, FINRA BrokerCheck, NYU SEED |
| **Prior Company Failures** | 15 | Served as officer/director at company that went bankrupt, restated financials, or faced SEC investigation | S&P Cap IQ + PACER + EFTS |
| **Insider Trading Patterns** | 10 | Suspicious timing/volume of trades; trading during blackout periods | SEC Form 4 analysis |
| **Personal Financial Issues** | 10 | Personal bankruptcy, tax liens, large judgments | PACER, BrokerCheck |
| **Negative News / Reputation** | 10 | Negative coverage in mainstream financial press | Brave Search, web |
| **Tenure/Stability Red Flags** | 5 | Forced departures, serial short-term roles, unexplained gaps | S&P Cap IQ, proxy bios |

**Scoring Rules:**

```
Prior Securities Litigation (25 max):
  - Named defendant in SCA that settled >$50M: +25
  - Named defendant in SCA that settled $10-50M: +20
  - Named defendant in SCA that settled <$10M: +15
  - Named defendant in SCA that was dismissed: +5
  - At company during SCA but not named: +3
  - Multiple SCAs: multiply by number (cap at 25)

SEC/Regulatory Enforcement (25 max):
  - Personal SEC enforcement action (charged): +25
  - Personal FINRA bar/suspension: +25
  - Company-level SEC action while serving as officer: +15
  - Company-level SEC action while serving as director: +10
  - FINRA customer complaint (settled): +5 each
  - OCC/FDIC action: +20

Prior Company Failures (15 max):
  - Company bankrupt while serving as CEO/CFO: +15
  - Company bankrupt while serving as director: +10
  - Company restated financials while serving as officer: +10
  - Company restated financials while serving as director: +5
  - Company delisted while serving: +8

Insider Trading Patterns (10 max):
  - Large sales before stock drop (>20%): +10
  - Pattern of selling ahead of bad news: +8
  - Sales during quiet period violations: +10
  - Abnormal trading volume vs. peers: +5

Personal Financial Issues (10 max):
  - Personal bankruptcy: +10
  - Tax lien/judgment: +5
  - Financial-related FINRA disclosure: +5

Negative News / Reputation (10 max):
  - SEC investigation mentioned in major press: +10
  - Fraud allegations in press: +8
  - Lawsuit coverage in press: +5
  - Social media controversy (securities-relevant): +3

Tenure/Stability Red Flags (5 max):
  - Forced departure / terminated for cause: +5
  - 4+ companies in 5 years: +3
  - Unexplained gap >1 year: +2
```

### 4.3 Board/Management Aggregate Risk Score

The aggregate score weights individuals by their role importance:

| Role | Weight |
|------|--------|
| CEO | 3.0x |
| CFO | 2.5x |
| COO/President | 2.0x |
| General Counsel | 2.0x |
| Board Chair | 2.5x |
| Audit Committee Chair | 2.0x |
| Other Named Executive Officers | 1.5x |
| Independent Directors | 1.0x |
| Other Directors | 1.0x |

```
Aggregate Score = Sum(Individual_Score_i * Role_Weight_i) / Sum(Role_Weight_i)
```

### 4.4 Risk Tiers

| Aggregate Score | Risk Tier | Underwriting Action |
|----------------|-----------|-------------------|
| 0-10 | LOW | Standard underwriting |
| 11-25 | MODERATE | Enhanced review, document findings |
| 26-50 | HIGH | Senior underwriter review required |
| 51-75 | VERY HIGH | Potential declination or significant surcharge |
| 76-100 | EXTREME | Declination recommended |

### 4.5 Important Caveats

- The score is a **screening tool**, not a final decision. Underwriter judgment remains paramount.
- Context matters: a dismissed lawsuit is very different from a settled fraud case.
- Recency matters: a 15-year-old issue is less relevant than a 2-year-old one.
- Industry norms matter: financial services executives will naturally have more FINRA disclosures.
- Apply a **time decay factor**: reduce points by 20% for each 5-year period since the event.

---

## 5. Board Composition Risk: Beyond Basic Independence Metrics

### 5.1 Overboarded Directors

ISS (Institutional Shareholder Services) defines overboarding thresholds:

| Director Type | ISS Threshold | Glass Lewis Threshold |
|--------------|--------------|----------------------|
| Non-CEO director | 5+ total public boards | 5+ total public boards |
| CEO of a public company serving on outside boards | 2+ outside public boards (total of 3 including own) | 2+ outside public boards |

**Data source**: DEF 14A proxy statements disclose other public board memberships per Item 401(e)(2) of Reg S-K. S&P Capital IQ has structured data for this.

**Risk assessment**:
- Count total public board seats for each director
- Flag anyone above ISS thresholds
- Higher risk if overboarded director chairs audit or compensation committee

### 5.2 Board Interlocks

A board interlock exists when two or more directors of the subject company also serve together on the board of another company.

**Why it matters**: Interlocks can indicate:
- Cronyism / reduced independence
- Groupthink risk
- Reciprocal compensation arrangements
- Regulatory risk (Clayton Act Section 8 prohibits interlocking directorates between competing companies)

**How to detect**:
1. Extract all directors from DEF 14A
2. For each director, get their other board seats (from proxy bio or S&P Cap IQ)
3. Cross-reference: do any two directors share another board?
4. Flag if more than 2 directors interlock at the same outside company

### 5.3 Director Tenure and Refreshment

| Signal | Risk Implication | Data Source |
|--------|-----------------|------------|
| Average director tenure >10 years | Entrenchment, reduced independence | DEF 14A director bios (year first elected) |
| No new directors in 3+ years | Stale perspectives, succession risk | DEF 14A year-over-year comparison |
| Multiple directors >75 years old | Succession concentration risk | DEF 14A director bios (age) |
| Classified/staggered board | Anti-takeover entrenchment | DEF 14A governance section |
| No mandatory retirement policy | Reduced accountability | Corporate governance guidelines |
| Founder still controlling board | Reduced independence from management | DEF 14A, company history |

### 5.4 Committee Composition Red Flags

| Red Flag | Why It Matters |
|----------|---------------|
| Audit committee member lacks financial expertise | SEC requires at least one "audit committee financial expert" |
| Compensation committee includes CEO or insiders | Self-dealing compensation risk |
| Nominating committee is not fully independent | Board selection captured by management |
| Same person chairs 2+ key committees | Over-concentration, attention dilution |
| Committee member also serves on audit committee of a company being investigated | Contagion risk |

### 5.5 Related Party Transactions

DEF 14A requires disclosure of related party transactions above $120,000 where an officer/director has a direct or indirect material interest.

**Red flags**:
- Transactions with companies owned by directors' family members
- Real estate leases with insider-affiliated entities
- Consulting agreements with former executives
- Loans to officers/directors (largely prohibited post-SOX, but watch for exceptions)
- Business relationships between company and a director's other company

### 5.6 Compensation Structure Red Flags

| Signal | What It Indicates |
|--------|------------------|
| CEO pay >3x median NEO pay | Imperial CEO risk |
| >50% of comp in salary (vs. equity) | Misaligned incentives, short-term focus |
| Golden parachute >3x base salary | Entrenchment, excessive payout risk |
| No clawback policy | Inability to recover in case of misconduct |
| Repriced stock options | Management-friendly comp committee |
| CEO pay significantly above peer median | "Single most reliable risk marker" per industry |
| Supplemental executive retirement plan (SERP) | Hidden compensation, retention concern |

---

## 6. Implementation Plan: What We Can Build with SEC + Web Search + S&P Cap IQ

### 6.1 Phase 1: Extract People (LOW effort, HIGH value)

**Goal**: Automatically identify all officers and directors from SEC filings.

**Implementation**:

1. **Parse DEF 14A** using EdgarTools Python library:
   ```python
   from edgar import Company
   company = Company("AAPL")
   proxy = company.get_filings(form="DEF 14A").latest()
   # Extract director names, ages, bios, other board seats
   # Extract executive compensation tables
   # Extract related party transactions section
   ```

2. **Parse 10-K Item 10** for officer/director list:
   - EdgarTools can extract specific sections from 10-K filings
   - Look for Item 401(f) legal proceedings disclosure

3. **Parse Form 4 filings** for insider trading data:
   - SEC provides bulk download of Form 3/4/5 data as flat files
   - Alternative: EDGAR API for filing-by-filing access
   - Track who is trading, when, and how much

4. **Store people data in AnalysisState model**:
   ```
   Executive(
     name: str,
     title: str,
     age: int,
     tenure_years: int,
     other_boards: list[str],
     bio_text: str,
     committee_memberships: list[str],
     compensation: CompensationData,
   )
   ```

### 6.2 Phase 2: Search Litigation History (MEDIUM effort, HIGH value)

**Goal**: For each identified person, search available databases for prior litigation.

**Implementation**:

1. **SEC SALI search** (no API; requires Playwright automation):
   - Navigate to https://www.sec.gov/litigations/sec-action-look-up
   - Submit each person's name
   - Parse results for matches
   - Rate limit: be respectful of SEC servers

2. **NYU SEED search** (no API; requires Playwright):
   - Navigate to https://research.seed.law.nyu.edu/
   - Search by defendant name, type=Individual
   - Extract case details

3. **SEC EFTS API search** (REST API available):
   ```python
   import httpx

   async def search_sec_filings(name: str) -> list[dict]:
       url = "https://efts.sec.gov/LATEST/search-index"
       params = {
           "q": f'"{name}" AND (litigation OR enforcement OR fraud OR complaint)',
           "dateRange": "custom",
           "startdt": "2000-01-01",
           "enddt": "2026-12-31",
       }
       headers = {"User-Agent": "CompanyName admin@company.com"}
       async with httpx.AsyncClient() as client:
           resp = await client.get(url, params=params, headers=headers)
           return resp.json()
   ```

4. **CourtListener API** (REST API, free):
   ```python
   async def search_courtlistener(name: str) -> list[dict]:
       url = "https://www.courtlistener.com/api/rest/v4/search/"
       params = {
           "type": "r",  # RECAP (federal court dockets)
           "party_name": name,
       }
       headers = {"Authorization": f"Token {CL_API_TOKEN}"}
       async with httpx.AsyncClient() as client:
           resp = await client.get(url, params=params, headers=headers)
           return resp.json()
   ```

5. **PACER Case Locator API** (REST API, requires account):
   ```python
   async def search_pacer(name: str) -> list[dict]:
       # Requires PACER authentication token
       url = "https://pcl.uscourts.gov/pcl-public-api/rest/parties"
       params = {
           "lastName": last_name,
           "firstName": first_name,
       }
       headers = {"X-NEXT-GEN-CSO": pacer_auth_token}
       async with httpx.AsyncClient() as client:
           resp = await client.get(url, params=params, headers=headers)
           return resp.json()
   ```

6. **judyrecords API** (REST API):
   ```python
   async def search_judyrecords(name: str) -> list[dict]:
       url = "https://www.judyrecords.com/api/v1/search"
       params = {"q": f'"{name}"'}
       async with httpx.AsyncClient() as client:
           resp = await client.get(url, params=params)
           return resp.json()
   ```

7. **Stanford SCAC** (no API; search by company ticker):
   - For each prior company (from S&P Cap IQ), search SCAC by ticker
   - Check filing dates against exec's tenure period
   - Requires Playwright automation for advanced search

8. **FINRA BrokerCheck** (no public API):
   - Use Playwright to search https://brokercheck.finra.org/
   - Or attempt to download PDF report at known URL pattern
   - Only relevant for executives with financial services background

9. **Web search** (Brave Search MCP):
   ```python
   queries = [
       f'"{name}" lawsuit securities fraud',
       f'"{name}" SEC investigation enforcement',
       f'"{name}" bankruptcy company failure',
       f'"{name}" indicted charged criminal',
       f'"{name}" FINRA bar suspension',
   ]
   ```

### 6.3 Phase 3: Board Composition Analysis (LOW effort, MEDIUM value)

**Goal**: Analyze board structure for governance risk signals.

**Implementation**:

1. **Overboarding detection**: Count other boards from proxy bios
2. **Interlock detection**: Cross-reference directors' other boards
3. **Tenure analysis**: Calculate average tenure, identify stale boards
4. **Committee analysis**: Verify qualification of committee chairs
5. **Compensation analysis**: Compare CEO pay to peers and detect red flags
6. **Related party scan**: Extract and flag related-party transactions from DEF 14A

### 6.4 Phase 4: Aggregate Scoring (LOW effort, HIGH value)

**Goal**: Compute individual and aggregate risk scores.

**Implementation**:

1. Map each finding to the scoring framework in Section 4
2. Apply time decay for older events
3. Weight by role importance
4. Generate individual and aggregate scores
5. Produce human-readable narrative explaining each score component

### 6.5 Technical Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Where in pipeline? | ACQUIRE (data gathering) + ANALYZE (scoring) | MCP tools only in ACQUIRE; scoring in ANALYZE |
| New stage or extend existing? | Extend ACQUIRE + ANALYZE | Consistent with pipeline architecture |
| State model additions | `ExecutiveProfile`, `LitigationFinding`, `ExecutiveRiskScore` | Pydantic models for each executive |
| Data caching | DuckDB for search results | Avoid re-querying same person across runs |
| API rate limiting | Per-source limits in config | SEC: 10 req/s; CourtListener: 5000 req/hr; PACER: account-limited |
| Name disambiguation | Fuzzy match + age + employer filter | Reduce false positives for common names |

### 6.6 Data Flow

```
ACQUIRE Stage:
  1. Parse DEF 14A → Extract directors + officers
  2. Parse 10-K Item 10 → Cross-reference
  3. For each person:
     a. Search SEC SALI (Playwright)
     b. Search NYU SEED (Playwright)
     c. Search SEC EFTS (API)
     d. Search CourtListener (API)
     e. Search PACER (API)
     f. Search judyrecords (API)
     g. Search SCAC by prior company tickers (Playwright)
     h. Search FINRA BrokerCheck (Playwright, if applicable)
     i. Web search for negative news (Brave)
  4. Parse Form 4 → Insider trading analysis
  5. Store all findings in AnalysisState.executive_profiles

ANALYZE Stage:
  6. Score each executive per framework
  7. Detect board composition risks
  8. Compute aggregate board risk score
  9. Generate narrative explanations

RENDER Stage:
  10. Executive Risk section in worksheet
  11. Individual executive profiles with findings
  12. Board composition risk summary
```

### 6.7 Cost Estimation

| Source | Cost Per Company | Notes |
|--------|-----------------|-------|
| SEC EDGAR APIs | FREE | 10 req/s limit |
| SEC EFTS | FREE | Rate limited |
| CourtListener | FREE | 5000 req/hr, free token |
| PACER Case Locator | ~$0.10-$3.00 per search | Could add up with many executives |
| judyrecords | FREE (API terms TBD) | Contact for commercial use |
| Brave Search | FREE (2000/month) | ~5-10 queries per executive |
| FINRA BrokerCheck | FREE | Manual or Playwright |
| SEC SALI | FREE | Playwright automation |
| NYU SEED | FREE | Playwright automation |
| Stanford SCAC | FREE | Requires free account |

**Estimated cost per company**: $0.50-$3.00 (primarily PACER fees), well within $2.00/company budget if we limit PACER to high-priority cases.

**Optimization**: Use free sources first. Only hit PACER if free sources suggest there might be something to find.

---

## 7. Recommendations: Priority Order for Building Executive Forensics

### 7.1 Must-Have (Build First)

| # | Capability | Effort | Value | Implementation |
|---|-----------|--------|-------|----------------|
| 1 | **DEF 14A person extraction** | Medium | Critical | EdgarTools + HTML parsing |
| 2 | **10-K Item 10 / Item 401(f) parsing** | Low | Critical | EdgarTools section extraction |
| 3 | **SEC SALI search** | Medium | Critical | Playwright automation |
| 4 | **SEC EFTS name search** | Low | High | REST API call |
| 5 | **Web search for negative news** | Low | High | Brave Search MCP |
| 6 | **Individual Executive Risk Score** | Medium | Critical | Scoring framework implementation |
| 7 | **Board Aggregate Risk Score** | Low | High | Aggregation of individual scores |

### 7.2 Should-Have (Build Second)

| # | Capability | Effort | Value | Implementation |
|---|-----------|--------|-------|----------------|
| 8 | **CourtListener litigation search** | Low | High | REST API integration |
| 9 | **Stanford SCAC by prior company** | Medium | High | Playwright + S&P Cap IQ career data |
| 10 | **NYU SEED search** | Medium | Medium | Playwright automation |
| 11 | **Insider trading analysis (Form 4)** | Medium | High | SEC bulk data parsing |
| 12 | **Overboarding detection** | Low | Medium | Proxy bio parsing |
| 13 | **Board interlock detection** | Medium | Medium | Cross-reference proxy data |
| 14 | **Compensation peer comparison** | Medium | High | DEF 14A + S&P Cap IQ |

### 7.3 Nice-to-Have (Build Third)

| # | Capability | Effort | Value | Implementation |
|---|-----------|--------|-------|----------------|
| 15 | **FINRA BrokerCheck** | Medium | Medium (only for financial services) | Playwright automation |
| 16 | **PACER Case Locator** | Medium | Medium | REST API (costs money) |
| 17 | **judyrecords search** | Low | Medium | REST API |
| 18 | **OCC/FDIC enforcement search** | Medium | Low (only for banks) | Playwright automation |
| 19 | **Director tenure/refreshment analysis** | Low | Low | Proxy data analysis |
| 20 | **Related party transaction extraction** | High | Medium | NLP extraction from proxy text |

### 7.4 Key API Endpoints Summary

```
SEC SALI:           https://www.sec.gov/litigations/sec-action-look-up (web form, Playwright)
SEC EFTS:           https://efts.sec.gov/LATEST/search-index?q=QUERY (GET, JSON)
SEC Submissions:    https://data.sec.gov/submissions/CIK{padded}.json (GET, JSON)
SEC Form 4 Bulk:    https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/
CourtListener:      https://www.courtlistener.com/api/rest/v4/search/?party_name=NAME (GET, JSON)
PACER PCL:          https://pcl.uscourts.gov/pcl-public-api/rest/parties (GET, JSON)
judyrecords:        https://www.judyrecords.com/api (GET, JSON)
FINRA BrokerCheck:  https://brokercheck.finra.org/ (web form, Playwright)
NYU SEED:           https://research.seed.law.nyu.edu/ (web form, Playwright)
Stanford SCAC:      https://securities.stanford.edu/filings.html (web form, Playwright)
OCC Enforcement:    https://apps.occ.gov/EASearch (web form, Playwright)
FDIC Enforcement:   https://orders.fdic.gov/s/searchform (web form, Playwright)
```

### 7.5 Critical Implementation Notes

1. **Rate Limiting**: SEC limits to 10 requests/second. CourtListener to 5000/hour. Build in proper throttling.

2. **User-Agent Header**: SEC requires a descriptive User-Agent header with contact email. Non-compliance results in IP blocking.

3. **Caching**: Cache all search results in DuckDB. Executive backgrounds don't change frequently — a 30-day cache TTL is appropriate.

4. **False Positive Management**: Common names will produce many false positives. The system must present findings with confidence levels, not as definitive matches. Always show the match context so the underwriter can evaluate.

5. **Playwright vs. API**: Where APIs exist, prefer them. Playwright is for sites with no API (SALI, SEED, SCAC, BrokerCheck). Playwright automation is fragile and must be maintained as sites change.

6. **S&P Capital IQ Integration**: This is the user's most powerful tool for career history data. Integration approach TBD — may need to be a manual step where the underwriter exports data from Cap IQ, or we build a structured input format for career history data.

7. **20% Rule**: Per executive due diligence industry research, approximately 20% of executives don't "check out well" and 10% have "serious issues." The system should flag these percentages as baseline expectations.

8. **Time Decay**: Apply a decay factor to older findings. A 2-year-old SEC action is far more relevant than a 15-year-old dismissed lawsuit. Suggested decay: reduce score by 20% for each 5-year period since the event.

---

## Appendix A: Reference URLs

- SEC Action Lookup Individuals: https://www.sec.gov/litigations/sec-action-look-up
- SEC EDGAR Full Text Search: https://efts.sec.gov/LATEST/search-index
- SEC Developer Resources: https://www.sec.gov/about/developer-resources
- Stanford SCAC: https://securities.stanford.edu/
- NYU SEED: https://research.seed.law.nyu.edu/
- FINRA BrokerCheck: https://brokercheck.finra.org/
- FINRA API Developer Center: https://developer.finra.org/
- CourtListener: https://www.courtlistener.com/
- CourtListener API: https://www.courtlistener.com/api/rest/v4/
- PACER Case Locator: https://pcl.uscourts.gov/
- judyrecords: https://www.judyrecords.com/
- judyrecords API: https://www.judyrecords.com/api
- OCC Enforcement Search: https://apps.occ.gov/EASearch
- FDIC Enforcement Search: https://orders.fdic.gov/s/searchform
- UniCourt (paid): https://unicourt.com/
- EdgarTools Python Library: https://github.com/dgunning/edgartools
- D&O Diary: https://www.dandodiary.com/
- S&P Capital IQ: https://www.capitaliq.com/
- SEC Insider Transactions Bulk Data: https://www.sec.gov/files/structureddata/data/insider-transactions-data-sets/
- ISS Voting Guidelines: https://www.issgovernance.com/file/policy/active/americas/US-Voting-Guidelines.pdf
- Cornerstone Research SCA Reports: https://www.cornerstone.com/insights/reports/securities-class-action-filings/

## Appendix B: Example Search Workflow for One Executive

**Target**: Jane Q. Smith, CEO of ACME Corp (CIK 0001234567), age 54, previously CFO at BigCo Inc. (2015-2020) and VP Finance at OldCorp (2010-2015).

```
Step 1: SEC SALI → Search "Jane Smith" → Filter by approximate dates
Step 2: NYU SEED → Search "Jane Smith" defendant type=Individual
Step 3: SEC EFTS → Query: "Jane Smith" AND (litigation OR enforcement)
Step 4: SEC EFTS → Query: "Jane Q. Smith" AND (fraud OR complaint OR defendant)
Step 5: CourtListener → party_name="Jane Smith" → filter by date ranges
Step 6: Stanford SCAC → Search ticker "BIGCO" → check filings during 2015-2020
Step 7: Stanford SCAC → Search ticker "OLDCORP" → check filings during 2010-2015
Step 8: FINRA BrokerCheck → Search "Jane Smith" (if applicable)
Step 9: Brave Search → "Jane Smith" CEO ACME lawsuit OR SEC OR fraud
Step 10: Brave Search → "Jane Smith" BigCo litigation OR investigation
Step 11: PACER → Party search "Smith, Jane" (if earlier searches suggest something)
Step 12: Cross-reference all findings → disambiguate → score
```

Total API calls: ~12-15 per executive. With 10 executives/directors on average, that's ~120-150 searches per company. At SEC's 10 req/s limit, this takes about 15 seconds of API time plus Playwright automation time.
