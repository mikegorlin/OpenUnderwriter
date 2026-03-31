# Directors & Officers (D&O) Liability Underwriting: Comprehensive Regulatory Data Source Inventory

## SEC and Federal/State Regulatory Data Sources

**Prepared: 2026-02-06**
**Purpose: Inform construction of a D&O liability underwriting system**

---

## Table of Contents

1. [SEC EDGAR Filing Data](#1-sec-edgar-filing-data)
2. [SEC EDGAR Full-Text Search (EFTS)](#2-sec-edgar-full-text-search-efts)
3. [SEC XBRL / iXBRL Structured Data](#3-sec-xbrl--ixbrl-structured-data)
4. [SEC Enforcement Actions Database](#4-sec-enforcement-actions-database)
5. [SEC Whistleblower Program Data](#5-sec-whistleblower-program-data)
6. [SEC Comment Letters](#6-sec-comment-letters)
7. [SEC No-Action Letters](#7-sec-no-action-letters)
8. [PCAOB Inspection Reports and Enforcement](#8-pcaob-inspection-reports-and-enforcement)
9. [DOJ Corporate Fraud Prosecutions](#9-doj-corporate-fraud-prosecutions)
10. [FINRA BrokerCheck and Enforcement Actions](#10-finra-brokercheck-and-enforcement-actions)
11. [CFTC Enforcement Actions](#11-cftc-enforcement-actions)
12. [State Securities Regulators (NASAA)](#12-state-securities-regulators-nasaa)
13. [State Attorney General Enforcement Actions](#13-state-attorney-general-enforcement-actions)
14. [Delaware Chancery Court Records](#14-delaware-chancery-court-records)
15. [OCC Enforcement Actions](#15-occ-enforcement-actions)
16. [Federal Reserve Enforcement Actions](#16-federal-reserve-enforcement-actions)
17. [FDIC Enforcement Actions](#17-fdic-enforcement-actions)
18. [FTC Enforcement Actions](#18-ftc-enforcement-actions)
19. [EPA Enforcement (Environmental Liability)](#19-epa-enforcement-environmental-liability)
20. [IRS Corporate Penalty Data](#20-irs-corporate-penalty-data)
21. [SEC Accounting and Auditing Enforcement Releases (AAERs)](#21-sec-accounting-and-auditing-enforcement-releases-aaers)
22. [SEC Staff Accounting Bulletins](#22-sec-staff-accounting-bulletins)
23. [Congressional Hearing Transcripts](#23-congressional-hearing-transcripts)
24. [GAO Reports on Corporate Governance](#24-gao-reports-on-corporate-governance)
25. [Treasury OFAC Enforcement](#25-treasury-ofac-enforcement)
26. [Supplementary Sources](#26-supplementary-sources)

---

## 1. SEC EDGAR Filing Data

### 1A. EDGAR Submissions API (Company Filing Histories)

- **Full Name:** SEC EDGAR Submissions API
- **URL:** `https://data.sec.gov/submissions/CIK##########.json`
- **Bulk Download:** `https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip`
- **What It Contains:** Complete filing history for every SEC registrant, including: company name, CIK, SIC code, state of incorporation, fiscal year end, stock exchange/ticker, all filing accession numbers, form types, filing dates, acceptance timestamps, primary document URLs, and links to all filed exhibits. Former company names and historical changes are also included.
- **Access Method:** RESTful JSON API -- no authentication or API keys required. Must include a User-Agent header with contact information. Rate-limited to 10 requests per second.
- **Historical Coverage:** All EDGAR electronic filings from 1993-Q3 to present. Index files available from 1993-Q1.
- **Data Format:** JSON (API responses); TSV/IDX (index files); ZIP (bulk archives)
- **Update Frequency:** Real-time (sub-second processing delay as filings are disseminated). Bulk ZIP files recompiled nightly.
- **Cost:** Free
- **Known Limitations:** Only covers electronically filed documents. Pre-1993 filings not available digitally. Very old filings may lack structured metadata. The 10-request-per-second rate limit can slow large-scale scraping. The User-Agent requirement means anonymous access is blocked.

### 1B. Key Filing Types for D&O Underwriting

#### Form 10-K (Annual Report) and 10-K/A (Amended)
- **URL:** Accessible via EDGAR Company Search: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=10-K`
- **D&O Relevance:** Contains Item 1A (Risk Factors), Item 3 (Legal Proceedings), Item 7 (MD&A including going concern language), Item 8 (Audited Financial Statements), Item 9A (Controls and Procedures including internal control deficiencies / material weaknesses), and Item 11 (Executive Compensation by reference to proxy). Restatements appear as 10-K/A filings.
- **Historical Coverage:** Electronic filings from 1993-Q3 forward; most comprehensive from 1996 onward.

#### Form 10-Q (Quarterly Report) and 10-Q/A (Amended)
- **D&O Relevance:** Quarterly financial statements, updated risk factors, legal proceedings updates, and disclosure of any material changes. Amended filings (10-Q/A) signal restatements.

#### Form 8-K (Current Report) and 8-K/A (Amended)
- **D&O Relevance:** Material event disclosures filed within 4 business days. Key items for D&O:
  - **Item 1.01:** Entry into a Material Definitive Agreement
  - **Item 1.02:** Termination of a Material Definitive Agreement
  - **Item 1.03:** Bankruptcy or Receivership
  - **Item 2.01:** Completion of Acquisition or Disposition of Assets
  - **Item 2.02:** Results of Operations and Financial Condition
  - **Item 2.04:** Triggering Events That Accelerate or Increase a Direct Financial Obligation
  - **Item 2.06:** Material Impairments
  - **Item 3.01:** Notice of Delisting or Failure to Satisfy a Continued Listing Rule
  - **Item 4.01:** Changes in Registrant's Certifying Accountant (auditor change -- major red flag)
  - **Item 4.02:** Non-Reliance on Previously Issued Financial Statements or a Related Audit Report (restatement trigger -- extremely important for D&O)
  - **Item 5.01:** Changes in Control of Registrant
  - **Item 5.02:** Departure of Directors or Certain Officers; Election of Directors; Appointment of Certain Officers; Compensatory Arrangements (critical for D&O underwriting -- captures all executive turnover)
  - **Item 5.03:** Amendments to Articles of Incorporation or Bylaws
  - **Item 5.05:** Amendments to the Registrant's Code of Ethics, or Waiver of a Provision
  - **Item 8.01:** Other Events (catch-all, often includes litigation updates, investigations, regulatory inquiries)

#### Form DEF 14A (Definitive Proxy Statement)
- **URL:** Searchable on EDGAR by form type "DEF 14A"
- **D&O Relevance:** The single most important filing for D&O profiling. Contains: executive compensation tables (Summary Compensation Table, Grants of Plan-Based Awards, Outstanding Equity Awards), director compensation, related party transactions, corporate governance provisions (board committees, independence determinations, risk oversight), shareholder proposals, and director/officer biographical information. Pay vs. Performance disclosures became XBRL-tagged effective December 16, 2022.

#### Forms 3, 4, and 5 (Insider Ownership and Transactions)
- **URL:** `https://www.sec.gov/data-research/sec-markets-data/insider-transactions-data-sets`
- **D&O Relevance:** Track director and officer stock transactions in near real-time. Form 3 = initial beneficial ownership statement upon becoming an insider. Form 4 = changes in ownership (must be filed within 2 business days). Form 5 = annual statement of changes not previously reported. Unusual selling patterns by insiders ahead of bad news are a major D&O risk signal.
- **Data Format:** XML-based fillable forms; SEC provides flattened bulk data sets quarterly with SUBMISSION and REPORTINGOWNER tables.
- **Historical Coverage:** Structured XML data sets available from approximately 2003 onward. Earlier filings exist in EDGAR but in less structured formats.
- **Access Method:** Quarterly bulk ZIP downloads from SEC, or individual filing retrieval via EDGAR. Third-party APIs (sec-api.io) also provide parsed JSON.

#### Form NT 10-K / NT 10-Q (Notification of Late Filing, Form 12b-25)
- **D&O Relevance:** A late filing notification is a significant risk indicator. Companies that cannot file on time often face accounting issues, restatements, or internal control failures. Filing a Form 12b-25 grants 5 extra days for 10-Q or 15 extra days for 10-K. SEC enforcement has targeted companies that failed to disclose the true reasons (e.g., pending restatements) in their NT filings.

#### Schedule 13D / 13G (Beneficial Ownership Reports)
- **D&O Relevance:** Disclose activist investors acquiring >5% stakes, often preceding governance challenges, board shakeups, or pressure on management. Schedule 13D (activist intent) vs. 13G (passive). Amendments signal changes in strategy.

#### Form S-1 / S-3 / F-1 (Registration Statements)
- **D&O Relevance:** Contains risk factors, use of proceeds, and management discussion for IPOs and secondary offerings. Section 11 and 12 liability attaches to directors who sign these documents.

### 1C. EDGAR Bulk Data Archives

- **Full Index:** `https://www.sec.gov/Archives/edgar/full-index/` (quarterly, from 1993-Q3)
- **Daily Index:** `https://www.sec.gov/Archives/edgar/daily-index/`
- **Daily Filing Feed:** `https://www.sec.gov/Archives/edgar/Feed/` (tar/gzip archives of each filing day)
- **Old Loads:** `https://www.sec.gov/Archives/edgar/Oldloads/` (concatenated daily archive files)
- **Notre Dame Master Index:** University of Notre Dame SRAF provides `master.idx` files from 1993-Q1 to 2024-Q4 in a single download: `https://sraf.nd.edu/sec-edgar-data/master-index-data/`

---

## 2. SEC EDGAR Full-Text Search (EFTS)

- **Full Name:** EDGAR Full-Text Search System
- **URL:** `https://efts.sec.gov/LATEST/search-index` (API endpoint); `https://www.sec.gov/edgar/search/` (web interface)
- **What It Contains:** Full-text searchable index of all EDGAR filings submitted electronically since 2001, including all attachments and exhibits. Supports keyword, ticker, company name, CIK, and reporter name searches with Boolean operators (AND, OR, NOT), exact phrase matching, and wildcards.
- **Access Method:** Web interface with AJAX JSON API backend. The API endpoint at `https://efts.sec.gov/LATEST/search-index` can be queried programmatically with parameters for `q` (query), `dateRange`, `startdt`, `enddt`, `forms`, `ciks`, etc. Returns JSON results with filing metadata and highlighted snippets.
- **Historical Coverage:** All filings from 2001 to present.
- **Data Format:** JSON (API); HTML (web interface)
- **Update Frequency:** Near real-time as filings are disseminated.
- **Cost:** Free
- **Known Limitations:** Does not cover filings before 2001. Rate limiting applies. Not designed for bulk extraction -- best used for targeted searches (e.g., finding mentions of "SEC investigation," "subpoena," "restatement," "material weakness," or specific officer names across all filings). No official bulk download of the search index itself.
- **D&O Use Cases:** Search for mentions of regulatory investigations, subpoenas, Wells notices, restatements, auditor changes, officer terminations, whistleblower complaints, and specific litigation across all public company filings. Extremely powerful for identifying undisclosed or emerging risks.

---

## 3. SEC XBRL / iXBRL Structured Data

### 3A. XBRL Company Facts API

- **Full Name:** SEC EDGAR XBRL Company Facts API
- **URL:** `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`
- **Bulk Download:** `https://www.sec.gov/Archives/edgar/daily-index/xbrl/companyfacts.zip`
- **What It Contains:** All XBRL-tagged financial data points for a single company across all its filings, organized by taxonomy (us-gaap, dei, ifrs-full, srt, ecd) and concept tag. Each fact includes the value, units, period, filing accession number, and form type.
- **Access Method:** REST API (no auth required). Bulk ZIP download available.
- **Historical Coverage:** XBRL filing requirements phased in 2009-2012 for operating companies. Most large accelerated filers have XBRL data from 2009+; smaller companies from 2012+. iXBRL required from 2020 (phased).
- **Data Format:** JSON
- **Update Frequency:** Updated within approximately one minute of filing dissemination. Bulk ZIP recompiled nightly.
- **Cost:** Free
- **Known Limitations:** Quality depends on filer tagging accuracy. Different companies may tag similar items with different concepts. Custom extensions reduce comparability. Pre-2009 data not available in XBRL.

### 3B. XBRL Company Concept API

- **URL:** `https://data.sec.gov/api/xbrl/companyconcept/CIK##########/{taxonomy}/{tag}.json`
- **Example:** `https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/Revenue/USD.json`
- **What It Contains:** All disclosures of a single concept (e.g., Revenue, NetIncome, StockholdersEquity) for a single company. Useful for pulling time series of specific financial metrics.
- **D&O Relevance:** Rapid extraction of financial trend data for underwriting models -- revenue trajectory, profitability, leverage ratios, going concern indicators.

### 3C. XBRL Frames API

- **URL:** `https://data.sec.gov/api/xbrl/frames/{taxonomy}/{tag}/{unit}/{period}.json`
- **Example:** `https://data.sec.gov/api/xbrl/frames/us-gaap/NetIncomeLoss/USD/CY2024Q4I.json`
- **What It Contains:** Cross-company comparison data: the last-filed fact for each reporting entity for a given concept and period. Enables peer benchmarking across all SEC filers.
- **D&O Relevance:** Peer comparison for financial health indicators relevant to D&O pricing.

### 3D. Executive Compensation Disclosure (ECD) Taxonomy (iXBRL)

- **URL:** Tagged data within DEF 14A filings from fiscal years ended December 16, 2022 onward
- **What It Contains:** Pay vs. Performance tables, Summary Compensation Tables, and related executive compensation disclosures tagged in iXBRL using the ECD taxonomy. Includes CEO and named executive officer compensation figures, total shareholder return metrics, and financial performance measures.
- **D&O Relevance:** Machine-readable executive compensation data is critical for D&O underwriting. Compensation levels, pay-for-performance alignment, and equity grant structures all correlate with D&O risk.
- **Known Limitations:** Only available from late 2022 onward. Prior years' compensation data must be extracted via NLP/parsing of unstructured DEF 14A filings.

---

## 4. SEC Enforcement Actions Database

### 4A. Litigation Releases

- **Full Name:** SEC Litigation Releases
- **URL:** `https://www.sec.gov/enforcement-litigation/litigation-releases`
- **What It Contains:** Summaries of civil lawsuits filed by the SEC in federal court, including complaints, settlements, final judgments, injunctions, and consent decrees against individuals and entities for securities law violations. Each release identifies the defendants, the alleged violations, and the relief sought or obtained.
- **Access Method:** Browsable HTML pages on SEC.gov. Searchable via EFTS. Third-party APIs (sec-api.io) provide structured JSON from 1995 to present.
- **Historical Coverage:** 1995 to present (online). Earlier releases available via FOIA or legal databases (Westlaw, LexisNexis).
- **Data Format:** HTML (on SEC.gov); JSON (via third-party APIs)
- **Update Frequency:** Published as actions occur. Note: Under the current administration (as of 2025), the SEC has reduced press releases for enforcement actions; many are now publicized only via litigation releases.
- **Cost:** Free on SEC.gov. Third-party APIs are paid services (sec-api.io pricing varies).
- **Known Limitations:** Unstructured HTML format makes bulk analysis difficult without parsing. No official SEC API for enforcement-specific data. Party names and penalty amounts must be extracted via NLP or manual review.

### 4B. Administrative Proceedings

- **Full Name:** SEC Administrative Proceedings
- **URL:** `https://www.sec.gov/enforcement-litigation/administrative-proceedings`
- **What It Contains:** Orders and releases from administrative proceedings including: cease-and-desist orders, suspension/revocation of broker-dealer/investment adviser registrations, bars from association, civil money penalties, disgorgement orders, and notices of proposed plans of distribution. Covers proceedings against regulated entities and individuals.
- **Access Method:** Browsable on SEC.gov. Structured data via third-party API (sec-api.io) covering 18,000+ proceedings from 1995 to present.
- **Historical Coverage:** 1995 to present (online).
- **Data Format:** HTML/PDF (on SEC.gov); JSON (via third-party API)
- **Update Frequency:** Published as orders are issued.
- **Cost:** Free on SEC.gov.
- **Known Limitations:** Same as litigation releases -- unstructured format. Consent orders often contain limited factual detail. Some proceedings are non-public during investigation phase.

### 4C. ALJ Orders and Initial Decisions

- **Full Name:** SEC Office of Administrative Law Judges -- Orders and Initial Decisions
- **URL (Orders):** `https://www.sec.gov/enforcement-litigation/administrative-law-judges-orders`
- **URL (Decisions):** `https://www.sec.gov/enforcement-litigation/administrative-law-judges-decisions`
- **URL (Proceeding Documents):** `https://www.sec.gov/litigation/apdocuments`
- **What It Contains:** All principal pleadings, orders, and decisions in present or past SEC administrative proceedings. Open proceeding documents are organized by Commission file number or case name. ALJ initial decisions include findings of fact and conclusions of law.
- **Access Method:** Browsable HTML on SEC.gov. Individual documents downloadable as PDF. Open and closed/archived proceedings available.
- **Historical Coverage:** Administrative proceeding documents available on SEC.gov from approximately 1995 onward.
- **Data Format:** HTML, PDF
- **Update Frequency:** As decisions and orders are issued.
- **Cost:** Free
- **Known Limitations:** Not available in structured/machine-readable format from the SEC directly. Must be scraped or processed with NLP. No API.

### 4D. Civil Actions (Federal Court)

- **Full Name:** SEC Civil Actions in Federal Court
- **URL:** Case documents available via PACER; SEC press releases and litigation releases summarize actions.
- **What It Contains:** Federal court complaints, motions, orders, and judgments in SEC enforcement cases filed in U.S. District Courts.
- **Access Method:** PACER (paid, $0.10/page); CourtListener/RECAP (free for cached documents); SEC litigation releases (free summaries).
- **Historical Coverage:** PACER electronic records from approximately 2001+; older cases via courthouse records.
- **Cost:** PACER: $0.10/page, $3 max per document, $30 quarterly fee waiver. CourtListener: Free for cached documents.

---

## 5. SEC Whistleblower Program Data

- **Full Name:** SEC Office of the Whistleblower
- **URL:** `https://www.sec.gov/enforcement-litigation/whistleblower-program`
- **Press Releases:** `https://www.sec.gov/whistleblower/pressreleases`
- **Annual Reports:** Published as PDFs, e.g., `https://www.sec.gov/files/fy24-annual-whistleblower-report.pdf`
- **What It Contains:** Aggregate statistics on whistleblower tips received, award determinations (grants and denials), total dollar amounts awarded, and program trends. Individual award orders identify the enforcement action but not the whistleblower. Press releases announce significant awards.
- **Access Method:** PDF annual reports (downloadable). Press releases browsable on SEC.gov. Individual award orders published on SEC.gov.
- **Historical Coverage:** Program established by Dodd-Frank in 2011. Annual reports from FY2012 onward. Individual award orders from 2012 onward.
- **Data Format:** PDF (annual reports); HTML (press releases and orders)
- **Update Frequency:** Annual reports published annually. Award orders and press releases published as actions occur.
- **Cost:** Free
- **Known Limitations:** Whistleblower identity is protected and not disclosed. Individual tip data is confidential. Only aggregate statistics are public. You cannot determine which specific company had whistleblower tips filed against it (unless an enforcement action results and the award order references it). FY2025 saw a dramatic drop to $59.7M in awards (from $255M in FY2024) with an 83% denial rate, reflecting policy shifts.
- **D&O Relevance:** Aggregate trends indicate regulatory enforcement intensity. A high volume of tips in a particular sector may signal elevated D&O risk for that sector.

---

## 6. SEC Comment Letters

- **Full Name:** SEC Division of Corporation Finance Review Correspondence (Comment Letters)
- **URL:** Available on EDGAR as form types `UPLOAD` (SEC staff letters) and `CORRESP` (company response letters). Browse at: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=UPLOAD`
- **What It Contains:** Correspondence between SEC staff and filing companies during the filing review process. SEC staff raise questions about accounting treatments, disclosure adequacy, risk factor specificity, MD&A analysis, revenue recognition, related party transactions, and compliance with accounting standards. Company responses detail their positions.
- **Access Method:** Searchable via EDGAR by CIK and form type (UPLOAD, CORRESP). Also searchable via EFTS full-text search. No dedicated API from the SEC. Third-party tools (sec-api.io Query API with `formType:CORRESP` filter) provide structured access.
- **Historical Coverage:** Released publicly from August 1, 2004 onward, at least 20 business days after completion of the filing review.
- **Data Format:** HTML/text documents within EDGAR filings
- **Update Frequency:** Ongoing as reviews are completed and the 20-business-day hold period expires.
- **Cost:** Free
- **Known Limitations:** Unstructured text format. No standardized fields for issue type, severity, or resolution. Significant NLP/text mining required to categorize issues. The SEC does not tag or classify the topics raised in comment letters. 20-business-day delay means letters are not available in real-time.
- **D&O Relevance:** Comment letters revealing accounting questions, revenue recognition concerns, or disclosure deficiencies are leading indicators of potential restatement risk. Repeated or unresolved comment letter issues elevate D&O risk. Companies that receive comment letters on internal controls or related party transactions are statistically more likely to face future enforcement.

---

## 7. SEC No-Action Letters

- **Full Name:** SEC No-Action, Interpretive, and Exemptive Letters
- **URL:** `https://www.sec.gov/rules-regulations/no-action-interpretive-exemptive-letters`
- **Division of Corporation Finance:** `https://www.sec.gov/corpfin/corpfin-no-action-letters` (from January 15, 2002)
- **Division of Trading and Markets:** `https://www.sec.gov/divisions/marketreg/mr-noaction` (from January 1, 2002)
- **What It Contains:** Staff responses to requests for guidance on whether proposed transactions or arrangements would violate securities laws. Includes shareholder proposal no-action requests (Rule 14a-8) which reveal governance disputes between companies and shareholders.
- **Access Method:** Browsable on SEC.gov by division and date. Searchable via EFTS. Historical letters (pre-2002) available via FOIA or subscription databases (LexisNexis coverage from 1971, Westlaw, Bloomberg Law).
- **Historical Coverage:** Online from 2002 forward. Subscription databases back to 1971.
- **Data Format:** HTML/PDF on SEC.gov
- **Update Frequency:** Published as issued.
- **Cost:** Free on SEC.gov. Historical access requires paid subscription databases.
- **Known Limitations:** No structured database or API. Letters must be individually reviewed. Pre-2002 letters require FOIA request or commercial database.
- **D&O Relevance:** Rule 14a-8 no-action requests reveal contentious governance disputes (e.g., shareholders proposing board changes, executive compensation reforms, or risk oversight measures that management seeks to exclude). These disputes can signal governance weakness.

---

## 8. PCAOB Inspection Reports and Enforcement

### 8A. PCAOB Inspection Reports

- **Full Name:** Public Company Accounting Oversight Board -- Firm Inspection Reports
- **URL:** `https://pcaobus.org/oversight/inspections/firm-inspection-reports`
- **Downloadable Datasets:** `https://pcaobus.org/oversight/inspections/firm-inspection-reports` (CSV, XML, JSON)
- **What It Contains:** Public portions of inspection reports for audit firms registered with the PCAOB. Identifies audit engagements reviewed and deficiencies found, including failures in auditing revenue recognition, internal controls, fair value measurements, and going concern assessments. Datasets include firm data, audits selected for review, and inspection findings.
- **Access Method:** Web browsable with search/filter tools. Downloadable datasets in CSV, XML, and JSON formats from 2018 onward for annually inspected firms and 2019 for triennially inspected firms. Updated quarterly.
- **Historical Coverage:** Inspection reports from PCAOB's creation (2003) to present in HTML/PDF format. Structured downloadable datasets from 2018/2019 onward.
- **Data Format:** HTML/PDF (individual reports); CSV, XML, JSON (downloadable datasets)
- **Update Frequency:** Reports published as inspections are completed (with time lag). Datasets updated quarterly.
- **Cost:** Free
- **Known Limitations:** No API. Part II findings (which contain more serious deficiencies) remain nonpublic for 12 months to give the firm time to remediate, and become public only if the firm fails to address the deficiency. Pre-2018 data requires manual parsing of PDF/HTML reports.
- **D&O Relevance:** If a company's auditor has significant PCAOB inspection deficiencies, the risk of undetected accounting errors (and therefore restatements and D&O claims) increases. Audit quality is a leading indicator of financial reporting reliability.

### 8B. PCAOB Enforcement Actions

- **Full Name:** PCAOB Enforcement Actions
- **URL:** `https://pcaobus.org/oversight/enforcement/enforcement-actions`
- **All Updates:** `https://pcaobus.org/all-enforcement-updates`
- **What It Contains:** Settled disciplinary orders, opinions, sanctions (including censures, monetary penalties up to $100K for individuals / $2M for firms, bars, and suspensions), and related SEC/court actions on review. Identifies sanctioned firms and individual auditors.
- **Access Method:** Browsable on PCAOB website with search. No API or bulk download in structured format.
- **Historical Coverage:** From PCAOB's inception (2003) to present.
- **Data Format:** HTML/PDF
- **Update Frequency:** Published as actions are finalized.
- **Cost:** Free
- **Known Limitations:** No structured database or API. Manual extraction required. Some investigations remain nonpublic.
- **D&O Relevance:** If an auditor or engagement partner involved with a company has been sanctioned by the PCAOB, this is a red flag for audit quality and potential undetected misstatements at clients they audit.

---

## 9. DOJ Corporate Fraud Prosecutions

### 9A. DOJ Criminal Division -- Fraud Section

- **Full Name:** U.S. Department of Justice, Criminal Division, Fraud Section -- Enforcement Actions
- **URL:** `https://www.justice.gov/criminal/criminal-fraud/enforcement-actions`
- **What It Contains:** Criminal enforcement actions related to corporate fraud, securities fraud, healthcare fraud, and FCPA violations. Includes indictments, plea agreements, deferred prosecution agreements (DPAs), non-prosecution agreements (NPAs), sentences, and restitution orders against both corporations and individuals (including directors and officers).
- **Access Method:** Browsable on DOJ website. Press releases available via DOJ newsroom. No structured API. FCPA-specific actions maintained in alphabetical (A-M, N-Z) and chronological lists.
- **Historical Coverage:** DOJ press releases from approximately 1994 onward. FCPA actions from the Act's passage (1977), with comprehensive online records from mid-2000s.
- **Data Format:** HTML/PDF
- **Update Frequency:** Published as actions are taken.
- **Cost:** Free
- **Known Limitations:** No structured database or API from DOJ. Highly fragmented across divisions and U.S. Attorney's offices. Must often cross-reference with PACER for full case details.

### 9B. Stanford FCPA Clearinghouse

- **Full Name:** Stanford Law School Foreign Corrupt Practices Act Clearinghouse
- **URL:** `https://fcpa.stanford.edu/`
- **Statistics:** `https://fcpa.stanford.edu/statistics-analytics.html`
- **What It Contains:** Comprehensive database of all DOJ and SEC FCPA enforcement actions, including case details, settlements, penalties, individual defendants, and disposition outcomes. Provides statistical analytics on enforcement trends.
- **Access Method:** Web searchable. Statistics available for free browsing. Updated through July 2025 as of last check.
- **Historical Coverage:** Comprehensive from FCPA's inception (1977) to present.
- **Data Format:** HTML (web); some data available for academic download.
- **Cost:** Free for public access.
- **Known Limitations:** Academic resource; may have delays in updates. Not available as a structured API for commercial integration.
- **D&O Relevance:** FCPA violations are a major D&O exposure, particularly for multinational companies. Individual officers can face criminal prosecution, and settlements often run into hundreds of millions of dollars.

### 9C. DOJ Press Releases

- **Full Name:** Department of Justice Office of Public Affairs -- Press Releases
- **URL:** `https://www.justice.gov/news`
- **What It Contains:** Press releases for all DOJ actions, filterable by topic (corporate fraud, securities fraud, FCPA, antitrust, etc.), U.S. Attorney's office, and date.
- **Access Method:** Searchable on DOJ.gov. RSS feeds available.
- **Cost:** Free
- **Known Limitations:** Text-based; no structured data fields for penalty amounts, defendant names, or charge types.

---

## 10. FINRA BrokerCheck and Enforcement Actions

### 10A. FINRA BrokerCheck

- **Full Name:** FINRA BrokerCheck
- **URL:** `https://brokercheck.finra.org/`
- **What It Contains:** Registration and employment history, disciplinary actions, regulatory events, customer complaints, and arbitration outcomes for individual brokers and brokerage firms. Includes details on customer disputes, regulatory actions, criminal matters, civil judicial actions, and financial disclosures (bankruptcies, judgments, liens).
- **Access Method:** Web search tool (free). FINRA API Developer Center (`https://developer.finra.org/`) provides programmatic access with a Query API supporting 50+ datasets. Synchronous requests return up to 5,000 records; asynchronous up to 100,000 records. Requires registration for API access.
- **Historical Coverage:** CRD (Central Registration Depository) data from the system's inception. BrokerCheck online records generally from the mid-1990s onward.
- **Data Format:** HTML (web search); JSON (API)
- **Update Frequency:** BrokerCheck updated as disclosures are reported (typically within 30 days). API data updated per FINRA's internal schedule.
- **Cost:** BrokerCheck web search is free. API access requires registration; commercial use may require licensing arrangements.
- **Known Limitations:** BrokerCheck only covers individuals and firms registered with FINRA. Does not cover individuals who are solely corporate directors/officers at non-broker-dealer companies. Some disclosures are expunged through arbitration. API rate limits and record caps apply.
- **D&O Relevance:** Critical for underwriting D&O policies at financial services firms. Director or officer disciplinary history in the securities industry is a significant risk factor.

### 10B. FINRA Disciplinary Actions Online

- **Full Name:** FINRA Disciplinary Actions Online Database
- **URL:** `https://www.finra.org/rules-guidance/oversight-enforcement/finra-disciplinary-actions`
- **What It Contains:** All formal FINRA disciplinary actions from January 1, 2005 onward, including fines, suspensions, bars, expulsions, and cease-and-desist orders. Searchable by case number, document text, document type, action date, individual/firm name, and CRD number.
- **Access Method:** Web searchable. Documents downloadable as searchable PDFs. Monthly disciplinary action summaries published as PDFs.
- **Historical Coverage:** January 1, 2005 to present.
- **Data Format:** HTML (search interface); PDF (individual documents and monthly summaries)
- **Update Frequency:** Monthly summaries published. Individual actions added as finalized.
- **Cost:** Free
- **Known Limitations:** No API or bulk download option from FINRA directly. OpenSanctions (`https://www.opensanctions.org/datasets/us_finra_actions/`) provides a structured alternative with daily updates in JSON format.

---

## 11. CFTC Enforcement Actions

- **Full Name:** Commodity Futures Trading Commission -- Division of Enforcement Actions
- **URL:** `https://www.cftc.gov/LawRegulation/EnforcementActions/index.htm`
- **Dispositions and Orders:** `https://www.cftc.gov/LawRegulation/Enforcement/OfficeofDirectorEnforcement.html`
- **Disciplinary History:** `https://www.cftc.gov/LearnAndProtect/DisciplinaryHistory/index.htm`
- **What It Contains:** Administrative and civil enforcement actions for violations of the Commodity Exchange Act and CFTC regulations, including fraud, manipulation, disruptive trading, and registration violations. Covers actions against firms and individuals, including fines, trading bans, and restitution orders. Annual enforcement results published with detailed addendums listing all actions.
- **Access Method:** Browsable on CFTC.gov. Annual addendums available as downloadable PDFs. OpenSanctions provides structured JSON data at `https://www.opensanctions.org/datasets/us_cftc_enforcement_actions/` with daily updates.
- **Historical Coverage:** Actions listed on CFTC.gov from approximately 2002 onward. Older actions via FOIA.
- **Data Format:** HTML/PDF (CFTC.gov); JSON (OpenSanctions)
- **Update Frequency:** Published as actions are taken. Annual addendums released with fiscal year results.
- **Cost:** Free
- **Known Limitations:** No official CFTC API. Website is not well-structured for programmatic access. Limited search functionality on the CFTC site itself.

### NFA Enforcement and Registration Actions

- **Full Name:** National Futures Association -- Enforcement and Registration Actions
- **URL:** `https://www.nfa.futures.org/EnforcementReg/EnforceRegActionsSimple.aspx`
- **What It Contains:** Disciplinary actions against NFA members and associates, including fines, suspensions, expulsions, and bars. Searchable by time period.
- **D&O Relevance:** Relevant for D&O underwriting at commodity trading and futures-related firms.

---

## 12. State Securities Regulators (NASAA)

- **Full Name:** North American Securities Administrators Association
- **URL:** `https://www.nasaa.org/`
- **Enforcement Statistics:** `https://www.nasaa.org/policy/enforcement-statistics/`
- **Annual Reports:** E.g., `https://www.nasaa.org/77718/nasaa-releases-2025-enforcement-report/`
- **What It Contains:** NASAA publishes aggregate enforcement statistics from all state and provincial securities regulators. In 2024: 8,833 cases investigated, 1,183 enforcement actions initiated (145 criminal, 69 civil, 853 administrative). Annual reports provide trend data on enforcement priorities, common fraud schemes, and monetary sanctions.
- **Access Method:** Annual enforcement reports downloadable as PDFs. Individual state enforcement actions must be accessed through each state's securities regulator website separately.
- **Historical Coverage:** Annual enforcement reports published from mid-2000s onward. Individual state records vary.
- **Data Format:** PDF (reports); HTML (individual state sites)
- **Update Frequency:** Annual reports. Individual state actions vary.
- **Cost:** Free
- **Known Limitations:** NASAA does not maintain a centralized, searchable database of individual enforcement actions across all states. You must visit each state's securities regulator website separately (50 states + territories). No API. Aggregate data only at the NASAA level.
- **D&O Relevance:** State securities regulators are increasingly active in enforcement, particularly against smaller and mid-cap companies. State blue sky law violations can trigger D&O claims independently of federal actions.

---

## 13. State Attorney General Enforcement Actions

### 13A. New York Attorney General

- **Full Name:** New York State Office of the Attorney General -- Advocacy and Enforcement Actions
- **URL:** `https://ag.ny.gov/libraries-documents/advocacy-and-enforcement-actions`
- **What It Contains:** Court filings, settlements, decisions, and press releases for enforcement actions brought by the NY AG. Searchable by type (amicus, court filings, decisions, letters, settlements/agreements). Covers securities fraud (Martin Act -- one of the broadest state securities fraud statutes, no intent requirement), consumer fraud, environmental violations, and corporate governance violations.
- **Key Units:** Criminal Enforcement and Financial Crimes Bureau; Securities and Commodities Fraud; Real Estate Enforcement Unit; Medicaid Fraud Control Unit.
- **Access Method:** Web searchable at `https://ag.ny.gov/search`. Press releases browsable. No API or bulk download.
- **Historical Coverage:** Online records vary; press releases from approximately mid-2000s onward.
- **Data Format:** HTML/PDF
- **Cost:** Free
- **Known Limitations:** No structured database or API. The Martin Act gives the NY AG unique power to bring securities fraud cases without proving intent, making NY a particularly important jurisdiction for D&O risk.

### 13B. California Attorney General

- **Full Name:** California Department of Justice, Office of the Attorney General -- Corporate Fraud Section
- **URL:** `https://oag.ca.gov/cfs` (Corporate Fraud Section); `https://oag.ca.gov/cfs/security` (Securities Unit)
- **What It Contains:** Investigations and prosecutions of securities and commodities fraud, energy crisis fraud, underground economy violations, and fraud against the state. Prosecutes under the California Unfair Competition Law, California False Claims Act, and California Corporate Securities and Commodities Laws.
- **Access Method:** Press releases at `https://oag.ca.gov/news/press-releases`. No dedicated searchable enforcement actions database identified for corporate fraud specifically.
- **Historical Coverage:** Press releases from approximately 2010 onward.
- **Data Format:** HTML/PDF
- **Cost:** Free
- **Known Limitations:** No centralized, publicly searchable enforcement database for the corporate fraud section. Must monitor press releases and court filings individually.
- **D&O Relevance:** California AG has warned that FCPA violations are actionable under state law, creating parallel state-level exposure for directors and officers.

### 13C. Texas State Securities Board

- **Full Name:** Texas State Securities Board -- Enforcement Actions
- **URL:** `https://www.ssb.texas.gov/news-publications/enforcement-actions-criminal-civil`
- **What It Contains:** Criminal and civil enforcement actions related to securities fraud in Texas, including indictments, cease-and-desist orders, and administrative penalties. The Enforcement Division refers evidence to the Texas Attorney General's office for civil injunctions and receiverships.
- **Access Method:** Browsable on SSB website. Paginated list of actions.
- **Historical Coverage:** Actions listed from approximately mid-2000s onward.
- **Data Format:** HTML/PDF
- **Cost:** Free
- **Known Limitations:** Limited search functionality. No API or structured data. Small team relative to the size of Texas's economy.

---

## 14. Delaware Chancery Court Records

- **Full Name:** Delaware Court of Chancery
- **URL:** `https://courts.delaware.gov/chancery/`
- **Electronic Filing System:** File & ServeXpress (`https://www.fileandservexpress.com/delaware/`)
- **Docket Search:** `https://courts.delaware.gov/docket.aspx`
- **What It Contains:** Dockets, complaints, motions, opinions, and orders from the Delaware Court of Chancery -- the preeminent forum for corporate governance litigation in the United States. Cases include: shareholder derivative actions, breach of fiduciary duty claims against directors/officers, merger challenges (Revlon, Unocal, entire fairness claims), books and records demands (Section 220), and corporate dissolution actions. Over 60% of Fortune 500 companies are incorporated in Delaware.
- **Access Method:** File & ServeXpress (paid subscription for full docket access). Delaware courts docket search available at courts.delaware.gov for basic case information. Full opinions also available on Bloomberg Law, LexisNexis, and Westlaw. Note: This is NOT on PACER (state court, not federal).
- **Historical Coverage:** File & ServeXpress electronic records from approximately 2009 onward. Older case files available through the court clerk's office.
- **Data Format:** HTML (docket search); PDF (individual filings via File & ServeXpress)
- **Update Frequency:** Real-time as filings are made.
- **Cost:** File & ServeXpress requires paid subscription. Delaware Courts docket search is free for basic information. Legal databases (Westlaw, LexisNexis, Bloomberg) require subscription.
- **Known Limitations:** Not available via PACER. Full docket access requires paid File & ServeXpress subscription. No API for programmatic access. Opinions are the most accessible component (available on court website and legal databases); underlying pleadings are harder to access in bulk.
- **D&O Relevance:** This is arguably the single most important court for D&O liability case law. Chancery Court opinions define the standards of conduct for directors (business judgment rule, enhanced scrutiny, entire fairness). A company's litigation history in Chancery Court is directly relevant to D&O pricing.

---

## 15. OCC Enforcement Actions

- **Full Name:** Office of the Comptroller of the Currency -- Enforcement Actions
- **URL:** `https://www.occ.treas.gov/topics/laws-and-regulations/enforcement-actions/index-enforcement-actions.html`
- **Searchable Database:** `https://apps.occ.gov/EASearch`
- **What It Contains:** All public enforcement actions taken since August 1989 against nationally chartered banks and their institution-affiliated parties (IAPs), including directors, officers, employees, controlling stockholders, and agents. Action types include: cease and desist orders, civil money penalties (CMPs), removal/prohibition orders (barring individuals from banking), formal agreements, consent orders, prompt corrective action directives, and safety and soundness orders.
- **Access Method:** Searchable web database with download capability. Enforcement actions that are not available online can be requested via FOIA. OTS (former thrift regulator) enforcement orders prior to July 21, 2011 available in a separate XLS archive.
- **Historical Coverage:** August 1989 to present.
- **Data Format:** HTML (search interface); downloadable spreadsheet format with defined data fields (see OCC Enforcement Order Listing Definitions PDF).
- **Update Frequency:** Monthly (OCC announces enforcement actions monthly via press releases).
- **Cost:** Free
- **Known Limitations:** No REST API. Older actions (pre-1989) not available digitally. OTS historical archive is a separate download. Data definitions document should be consulted to understand field meanings.
- **D&O Relevance:** Critical for D&O underwriting at banks and financial holding companies. Individual prohibition orders effectively end a banking career and indicate severe misconduct. CMPs against officers/directors signal material governance failures.

---

## 16. Federal Reserve Enforcement Actions

- **Full Name:** Board of Governors of the Federal Reserve System -- Enforcement Actions
- **URL:** `https://www.federalreserve.gov/supervisionreg/enforcementactions.htm`
- **Data Definitions:** `https://www.federalreserve.gov/supervisionreg/search-enforcement-actions-data-definitions.htm`
- **What It Contains:** Formal enforcement actions against state member banks, bank holding companies, savings and loan holding companies, and their institution-affiliated parties (directors, officers, employees). Includes: cease and desist orders, written agreements, civil money penalties, removal/prohibition orders, prompt corrective action directives, and denial/revocation of applications.
- **Access Method:** Searchable web database on Federal Reserve website. Fields include effective date, termination date, banking organization name, individual name, action type, and URL to the enforcement action document. OpenSanctions provides structured JSON data at `https://www.opensanctions.org/datasets/us_fed_enforcements/` with daily updates.
- **Historical Coverage:** Available from approximately 1989 to present on the website. Older actions via FOIA.
- **Data Format:** HTML (search interface); PDF (individual actions); JSON (OpenSanctions)
- **Update Frequency:** Published as actions are taken.
- **Cost:** Free
- **Known Limitations:** No official Fed API for enforcement data. Search interface is functional but lacks advanced filtering. Must cross-reference with FFIEC for complete picture of a bank's regulatory history.

---

## 17. FDIC Enforcement Actions

- **Full Name:** Federal Deposit Insurance Corporation -- Enforcement Decisions and Orders System (EDOS)
- **URL:** `https://orders.fdic.gov/s/`
- **Search Form:** `https://orders.fdic.gov/s/searchform`
- **What It Contains:** Enforcement orders, adjudicated decisions, notices, and administrative hearing documents for FDIC-supervised institutions and their affiliated parties. Action types include: cease and desist orders (Section 8(b)), removal/prohibition orders (Section 8(e)), civil money penalties (Section 8(i)), orders of restitution, and terminated consent orders.
- **Access Method:** Searchable web interface. Press releases for enforcement actions published monthly.
- **Types of Actions Reference:** `https://orders.fdic.gov/s/types-of-action`
- **Historical Coverage:** Extensive historical coverage; FDIC enforcement authority dates to 1989 FIRREA Act.
- **Data Format:** HTML (search); PDF (individual orders)
- **Update Frequency:** Monthly (FDIC publishes monthly enforcement action summaries).
- **Cost:** Free
- **Known Limitations:** No API. Limited bulk download options. Must search individually. The EDOS system interface can be cumbersome for large-scale research.
- **D&O Relevance:** Same as OCC and Fed -- directly relevant for D&O underwriting at FDIC-supervised banks. Individual removal/prohibition orders are the most severe sanction and indicate the most serious misconduct.

### FFIEC Cross-Reference

- **Full Name:** Federal Financial Institutions Examination Council -- Enforcement Actions and Orders
- **URL:** `https://www.ffiec.gov/resources/enforcement`
- **What It Contains:** Links to enforcement action databases of all five member agencies (Fed, FDIC, OCC, NCUA, CFPB). Does NOT maintain a consolidated database; serves as a directory pointing to individual agency databases.
- **D&O Relevance:** Use as a starting point to ensure all relevant banking regulators are checked for a given institution.

---

## 18. FTC Enforcement Actions

- **Full Name:** Federal Trade Commission -- Enforcement Actions and Data
- **URL (Developer Portal):** `https://www.ftc.gov/developer`
- **URL (Competition Enforcement):** `https://www.ftc.gov/competition-enforcement-database`
- **URL (Data Sets):** `https://www.ftc.gov/policy-notices/open-government/data-sets`
- **API Documentation:** `https://github.com/FederalTradeCommission/ftc-api-docs`
- **What It Contains:** The Competition Enforcement Database tracks antitrust matters. Consumer protection enforcement actions cover deceptive practices, data security failures, and unfair business practices. The FTC publishes data sets on Data.gov.
- **Access Method:** The FTC API (base URL: `https://api.ftc.gov/v0`) currently provides two endpoints: Early Termination Notices (HSR Act merger reviews) and Do Not Call complaints. Both return JSON. Registration for a free Data.gov API key is required. The Competition Enforcement Database is web-searchable.
- **Historical Coverage:** Competition enforcement database covers actions from 1915 to present. Consumer protection actions from approximately 1996 onward.
- **Data Format:** JSON (API); HTML (web databases)
- **Update Frequency:** API data updated as new entries are added. Web databases updated regularly.
- **Cost:** Free (API key required but free via Data.gov)
- **Known Limitations:** The API is extremely limited -- only two endpoints currently. The Competition Enforcement Database and consumer protection cases are not available via API. Most FTC enforcement data must be scraped from the web interface. The FTC develops new API endpoints gradually.
- **D&O Relevance:** FTC actions against companies for deceptive practices, data breaches, or antitrust violations can result in director/officer liability, particularly when the FTC alleges that management was aware of violations. Consent decrees impose ongoing compliance obligations that, if violated, create additional liability.

---

## 19. EPA Enforcement (Environmental Liability)

### 19A. ECHO (Enforcement and Compliance History Online)

- **Full Name:** EPA Enforcement and Compliance History Online
- **URL:** `https://echo.epa.gov/`
- **Data Downloads:** `https://echo.epa.gov/tools/data-downloads`
- **Web Services/API:** `https://echo.epa.gov/tools/web-services`
- **What It Contains:** Federal administrative and judicial enforcement actions under the Clean Air Act, Clean Water Act, RCRA, CERCLA (Superfund), TSCA, EPCRA Section 313, FIFRA, SDWA, and MPRSA. Data includes: case number, case name, violation information (law/section, violation date), milestone dates (referred to DOJ, filed, concluded), and penalty amounts (fines, supplemental environmental projects). Also includes state formal enforcement actions under delegated authority.
- **Access Method:**
  - **Web Interface:** Searchable by facility, geography, or enforcement case.
  - **REST API:** GET-only RESTlike services providing XML, JSON, or JSONP output. Endpoints include: `get_facilities`, `get_qid`, `get_map`, `get_download` (CSV generation).
  - **Bulk Downloads:** Weekly CSV files from ICIS-FE&C (Integrated Compliance Information System -- Federal Enforcement and Compliance) at `https://echo.epa.gov/tools/data-downloads/icis-fec-download-summary`.
  - **Data.gov:** Full dataset available at `https://catalog.data.gov/dataset/epa-enforcement-and-compliance-history-online`
- **Historical Coverage:** ICIS data from approximately 2000 onward; some datasets go back further.
- **Data Format:** CSV (bulk downloads); JSON/XML/JSONP (API); HTML (web interface)
- **Update Frequency:** Weekly (data refresh for downloads and web interface).
- **Cost:** Free
- **Known Limitations:** ECHO does not specifically track individual director or officer liability -- it tracks facility-level and company-level enforcement. Criminal cases are tracked separately in the Summary of Criminal Prosecutions database. EPA environmental enforcement rarely names individual D&Os unless criminal prosecution is involved. The API has usage limits; bulk downloads are recommended for large-scale analysis.
- **D&O Relevance:** Environmental liabilities (particularly Superfund liability and criminal environmental violations) can expose directors and officers personally. Companies with significant EPA enforcement history face elevated D&O risk, especially if violations involve knowing/willful conduct that could pierce the corporate veil.

---

## 20. IRS Corporate Penalty Data

- **Full Name:** Internal Revenue Service -- Collections, Activities, Penalties, and Appeals Data
- **URL:** `https://www.irs.gov/statistics/collections-activities-penalties-and-appeals`
- **Office of Fraud Enforcement:** `https://www.irs.gov/about-irs/office-of-fraud-enforcement-at-a-glance`
- **Criminal Investigation:** `https://www.irs.gov/compliance/criminal-investigation/program-and-emphasis-areas-for-irs-criminal-investigation`
- **What It Contains:**
  - **Aggregate Penalty Data:** Civil penalties assessed and abated by type of tax and type of penalty, published as fiscal year tables (downloadable).
  - **Criminal Investigation Data:** Annual reports on investigations initiated, prosecution recommendations, indictments, sentencing results, and restitution for tax fraud cases including corporate fraud.
  - **Whistleblower Data:** Annual reports to Congress on IRS Whistleblower Office activity (Section 7623).
  - **Offers in Compromise:** Statistics on tax debt settlements.
- **Access Method:** Aggregate statistics downloadable as Excel/CSV tables. IRS Criminal Investigation press releases available on IRS.gov. Individual company penalty data is protected by IRC Section 6103 (tax return confidentiality) and not publicly available except in criminal cases or via FOIA (heavily redacted).
- **Historical Coverage:** Aggregate statistics from approximately 2000 onward. Criminal investigation data from approximately 2005 onward.
- **Data Format:** Excel/CSV (aggregate tables); PDF (annual reports); HTML (press releases)
- **Update Frequency:** Annual (fiscal year statistics and reports).
- **Cost:** Free (aggregate data). Individual company data requires FOIA (often denied under Section 6103).
- **Known Limitations:** This is the most restricted data source in this inventory. Individual company tax penalty data is protected by federal tax return confidentiality laws (IRC Section 6103) and is generally NOT publicly available. Only aggregate statistics are published. Criminal tax fraud cases become public through DOJ press releases and court filings, but civil penalties remain confidential. FOIA requests for individual company tax data are routinely denied.
- **D&O Relevance:** Tax fraud by corporate officers is a significant D&O exposure. IRS Criminal Investigation has exclusive jurisdiction over criminal violations of the Internal Revenue Code. When tax fraud is discovered, it often leads to parallel SEC actions for misstated financial statements. The primary way to identify IRS-related D&O risk is through: (a) DOJ press releases for criminal tax cases, (b) SEC enforcement actions that reference tax issues, and (c) company disclosures in 10-K filings (Item 3 - Legal Proceedings, Item 1A - Risk Factors, tax-related contingencies in financial statement footnotes).

---

## 21. SEC Accounting and Auditing Enforcement Releases (AAERs)

- **Full Name:** SEC Accounting and Auditing Enforcement Releases
- **URL:** `https://www.sec.gov/enforcement-litigation/accounting-auditing-enforcement-releases`
- **What It Contains:** Enforcement actions specifically related to accounting and auditing violations, including financial statement fraud, auditor independence violations, improper professional conduct by auditors, and failures in financial reporting. AAERs are a subset of the broader SEC enforcement program specifically focused on financial reporting integrity. Each AAER identifies respondents, details the alleged violations, and describes the sanctions imposed.
- **Access Method:**
  - **SEC Website:** Browsable list of releases sorted by date.
  - **Third-Party API:** sec-api.io provides structured JSON AAER data from 1997 to present, with bulk download in ZIP format.
  - **Academic Datasets:**
    - **USC AAER Dataset:** 4,278 AAERs covering 1,816 firm misstatement events from May 17, 1982 to December 31, 2021. Available at `https://sites.google.com/usc.edu/aaerdataset/` and `https://www.marshall.usc.edu/departments/leventhal-school-accounting/faculty/aaer-dataset`.
    - **Harvard Baker Library:** Curated AAER dataset: `https://www.library.hbs.edu/databases-cases-and-more/datasets/accounting-and-auditing-enforcement-releases`
- **Historical Coverage:** AAERs from 1982 to present. Online SEC records from approximately 1997. Academic datasets provide cleaned data back to 1982.
- **Data Format:** HTML/PDF (SEC.gov); JSON (third-party API); CSV/structured data (academic datasets)
- **Update Frequency:** Published as enforcement actions are taken.
- **Cost:** Free (SEC.gov and academic datasets). Third-party API services are paid.
- **Known Limitations:** AAERs on SEC.gov are unstructured text. Academic datasets may have a lag (USC dataset updated through 2021). Identifying which specific officers/directors were named requires parsing each release.
- **D&O Relevance:** AAERs are the most directly relevant SEC enforcement data for D&O underwriting. They specifically address the types of accounting misconduct (financial statement fraud, revenue manipulation, earnings management, improper disclosures) that generate the largest D&O claims. A company that has been the subject of an AAER is at significantly elevated risk for future D&O claims, and any individual named in an AAER is effectively uninsurable in a D&O capacity.

### Commercial Enhancement: Audit Analytics

- **Full Name:** Audit Analytics (Ideagen) -- Financial Restatements Database and AAER Module
- **URL:** `https://www.auditanalytics.com/`
- **What It Contains:** Structured database of 10,000+ SEC registrant restatements since 2001, with 40+ accounting error category taxonomy. Also maintains AAER dataset with parsed enforcement details. Additional modules: director/officer changes, auditor changes, audit fees, internal control reports, and legal exposure data.
- **Access Method:** Subscription database. Available via WRDS (Wharton Research Data Services) for academic institutions.
- **Historical Coverage:** 2000/2001 to present (depending on module).
- **Data Format:** Structured relational data (accessible via SAS, R, Python through WRDS; direct feed for commercial subscribers).
- **Cost:** Paid subscription (pricing varies; academic access through WRDS). Commercial licenses are substantial (typically five to six figures annually).
- **D&O Relevance:** This is the gold standard commercial data source for D&O underwriting. The ability to cross-reference restatements, auditor changes, D&O turnover, internal control weaknesses, and enforcement actions in a single structured database is extremely valuable. Most major D&O underwriters use Audit Analytics or similar commercial data.

---

## 22. SEC Staff Accounting Bulletins

- **Full Name:** SEC Staff Accounting Bulletins (SABs)
- **URL:** `https://www.sec.gov/rules-regulations/staff-guidance/staff-accounting-bulletins`
- **Codification:** `https://www.sec.gov/rules-regulations/staff-guidance/selected-staff-accounting-bulletins/sec-staff-accounting-bulletin-codification-staff-accounting-bulletins`
- **What It Contains:** Staff views on accounting-related disclosure practices, representing interpretations and policies followed by the Division of Corporation Finance and the Office of the Chief Accountant. Covers revenue recognition, restructuring charges, loss contingencies, materiality, and other accounting topics.
- **Access Method:** Browsable on SEC.gov. Codification document available as a single reference. Individual SABs downloadable as HTML/PDF.
- **Historical Coverage:** SAB No. 1 (1975) through SAB No. 122 (current).
- **Data Format:** HTML/PDF
- **Update Frequency:** Issued as needed (irregularly; a few per year at most).
- **Cost:** Free
- **Known Limitations:** Interpretive guidance only; not binding rules. No structured data or API. The codification was last comprehensively updated in March 2022.
- **D&O Relevance:** SABs establish the accounting disclosure standards that companies must follow. Non-compliance with SAB guidance (particularly SAB 99 on materiality, SAB 101/104 on revenue recognition) is frequently cited in SEC enforcement actions and D&O litigation. Understanding applicable SABs is important context for evaluating whether a company's accounting practices create D&O risk.

---

## 23. Congressional Hearing Transcripts

- **Full Name:** Congressional Hearing Transcripts via GovInfo and Congress.gov
- **URL (GovInfo Collection):** `https://www.govinfo.gov/app/collection/CHRG`
- **URL (Congress.gov House):** `https://www.congress.gov/house-hearing-transcripts/`
- **URL (Congress.gov Senate):** `https://www.congress.gov/senate-hearing-transcripts/`
- **GovInfo API:** `https://api.govinfo.gov/docs` (OpenAPI/Swagger documentation)
- **What It Contains:** Official transcripts of congressional committee hearings, including hearings on corporate fraud, securities regulation, banking oversight, and corporate governance. Notable examples: Enron hearings, financial crisis hearings, FTX hearings, etc. Includes witness testimony, member questioning, and submitted written statements.
- **Access Method:**
  - **GovInfo API:** Free API requiring a data.gov API key. Supports querying by collection (CHRG for hearings), date range, and keywords. Returns metadata and links to full documents. Bulk XML downloads available for select collections.
  - **Congress.gov:** Browsable by Congress number and committee. Limited API at `https://api.congress.gov/`.
  - **GPO Bulk Data Repository:** XML content for Congressional Bill Text, Bill Status, Bill Summaries, and CFR (hearings not currently in bulk XML).
- **Historical Coverage:** GovInfo has select hearings from the 104th Congress (1995-96) forward, with growing digitized coverage of earlier hearings. Hearings back to the 1st Congress available at university libraries and HeinOnline.
- **Data Format:** PDF, HTML, XML (via GovInfo); plain text (transcripts)
- **Update Frequency:** Published after GPO processing (may be months after the hearing).
- **Cost:** Free (GovInfo API key is free via Data.gov).
- **Known Limitations:** Hearing transcripts offered as plain text with no embedded metadata for speaker turns. Significant NLP required to extract structured information. Coverage is incomplete for older hearings. Time lag between hearing and publication can be significant. Not all hearings are published.
- **D&O Relevance:** Congressional attention to a company or industry sector is a leading indicator of regulatory action. Companies whose executives testify before Congress (particularly in combative hearings) face elevated D&O risk. Congressional investigations often precede or parallel SEC/DOJ enforcement. Monitoring hearing transcripts for mentions of specific companies or industries provides early warning signals.

---

## 24. GAO Reports on Corporate Governance

- **Full Name:** U.S. Government Accountability Office -- Reports and Testimony
- **URL:** `https://www.gao.gov/`
- **GovInfo Collection:** `https://www.govinfo.gov/app/collection/gaoreports`
- **What It Contains:** Audits, surveys, investigations, and evaluations of federal programs, including reports on SEC enforcement effectiveness, corporate governance regulation, financial restatement trends, and investor protection. Notable historical report: GAO's Financial Restatement Database (1,390 restatements from July 2002 - September 2005).
- **Access Method:** Free search on gao.gov. Also available on GovInfo with API access. HeinOnline provides comprehensive historical access.
- **Historical Coverage:** Reports from 1921 to present. Comprehensive online access from mid-1990s onward.
- **Data Format:** PDF (reports); HTML (summaries); XML (via GovInfo API)
- **Update Frequency:** Published continuously (GAO issues approximately 700-900 reports per year).
- **Cost:** Free
- **Known Limitations:** GAO reports are policy-oriented, not data-oriented. They provide analysis and recommendations but not raw enforcement data. Useful for understanding regulatory trends and identifying systemic risks, but not for individual company D&O assessment.
- **D&O Relevance:** GAO reports identifying weaknesses in SEC enforcement, auditing standards, or corporate governance regulations can signal areas where D&O risk is elevated due to regulatory gaps. The Financial Restatement Database (though dated) established important baseline data on restatement trends.

---

## 25. Treasury OFAC Enforcement

### 25A. OFAC SDN List and Consolidated Sanctions List

- **Full Name:** Office of Foreign Assets Control -- Specially Designated Nationals and Blocked Persons List (SDN List) and Consolidated Sanctions List
- **URL (Sanctions List Service):** `https://ofac.treasury.gov/sanctions-list-service`
- **URL (Search Tool):** `https://sanctionssearch.ofac.treas.gov/`
- **URL (SDN List Site):** `https://sanctionslist.ofac.treas.gov/Home/SdnList`
- **What It Contains:** Individuals and entities whose assets are blocked and with whom U.S. persons are generally prohibited from dealing, including terrorists, narcotics traffickers, and persons acting on behalf of sanctioned countries. The Consolidated (non-SDN) List includes additional sanctioned parties under various programs.
- **Access Method:**
  - **Downloads:** SDN list available in XML, CSV, fixed-field, and delimited formats. Customize Sanctions Dataset tool allows custom downloads by program.
  - **Web Search:** Fuzzy logic name matching via Sanctions List Search.
  - **Third-Party APIs:** OpenSanctions (`https://www.opensanctions.org/datasets/us_ofac_sdn/`) provides daily-updated structured JSON. Middesk, sanctions.network, and other commercial providers offer API endpoints.
- **Historical Coverage:** SDN list maintained since OFAC's creation. Downloads reflect current list (not historical snapshots unless archived externally).
- **Data Format:** XML, CSV, fixed-field text, delimited text, PDF
- **Update Frequency:** Updated as designations are made (multiple times per week).
- **Cost:** Free (official OFAC). Third-party APIs may be paid.
- **Known Limitations:** The official OFAC download provides only the current list, not historical changes. You must maintain your own archive to track additions/removals over time. The fuzzy matching tool is useful but generates false positives. No official REST API from OFAC.

### 25B. OFAC Enforcement Actions and Civil Penalties

- **Full Name:** OFAC Civil Penalties and Enforcement Information
- **URL:** `https://ofac.treasury.gov/civil-penalties-and-enforcement-information`
- **Recent Actions:** `https://ofac.treasury.gov/recent-actions/enforcement-actions`
- **What It Contains:** Year-by-year listings of OFAC enforcement actions from 2003 to present, including: company/individual name, sanctions program violated, penalty amount, settlement details, aggravating/mitigating factors, and links to full enforcement action documents (PDFs).
- **Access Method:** Browsable on OFAC website, organized by year. Over 290 enforcement actions listed. Individual PDF reports for each action.
- **Historical Coverage:** 2003 to present (organized by calendar year: 2003-2024+ available).
- **Data Format:** HTML (listings); PDF (individual enforcement action reports)
- **Update Frequency:** Published as settlements/penalties are finalized.
- **Cost:** Free
- **Known Limitations:** No API or structured database. Must be scraped or manually reviewed. Penalty amounts and entity names must be extracted from HTML or PDF documents.
- **D&O Relevance:** Sanctions violations by corporate officers can result in personal criminal liability and civil penalties. OFAC penalties have escalated dramatically (multi-billion dollar settlements in some cases). Directors and officers can be held responsible for failure to maintain adequate sanctions compliance programs. Companies in international trade, banking, and energy are particularly exposed.

---

## 26. Supplementary Sources

### 26A. PACER / CourtListener (Federal Court Records)

- **Full Name:** Public Access to Court Electronic Records (PACER) / CourtListener RECAP Archive
- **URL (PACER):** `https://pacer.uscourts.gov/`
- **URL (PACER Case Locator API):** `https://pacer.uscourts.gov/help/pacer/pacer-case-locator-pcl-api-user-guide`
- **URL (CourtListener):** `https://www.courtlistener.com/`
- **URL (CourtListener API):** `https://www.courtlistener.com/help/api/`
- **What It Contains:** PACER provides electronic access to case and docket information from federal appellate, district, and bankruptcy courts. The PACER Case Locator (PCL) is a nationwide index with an API. CourtListener's RECAP archive contains hundreds of millions of docket entries and millions of PACER documents obtained through the RECAP browser extension, available free of charge.
- **Access Method:**
  - **PACER:** Web search and PCL API (authentication required via PACER authentication API). Billable per search in production.
  - **CourtListener:** Free REST API for RECAP archive data. Bulk data downloads available.
- **Historical Coverage:** PACER electronic records from approximately 2001 onward. CourtListener RECAP archive contains both historical and ongoing contributions.
- **Cost:** PACER: $0.10/page, $3 max/document, $30 quarterly fee waiver. CourtListener: Free.
- **D&O Relevance:** Essential for tracking securities class actions, shareholder derivative suits, SEC civil enforcement cases, and other federal litigation involving directors and officers.

### 26B. Stanford Securities Class Action Clearinghouse

- **Full Name:** Securities Class Action Clearinghouse (SCAC) / Stanford Securities Litigation Analytics (SLA)
- **URL (SCAC):** `https://securities.stanford.edu/`
- **URL (SLA):** `https://sla.law.stanford.edu/`
- **What It Contains:** Comprehensive database of federal securities fraud class action lawsuits filed since 1996 (post-PSLRA). Contains 3,600+ lawsuits and 43,000+ related documents (complaints, briefs, filings). SLA additionally tracks SEC enforcement actions and DOJ criminal actions from 2000 onward.
- **Access Method:** Web searchable with full-text and advanced field searches. New Filings email alert available.
- **Historical Coverage:** 1996 to present.
- **Cost:** Free
- **Known Limitations:** SCAC is currently undergoing restructuring and has paused website updates. SLA continues providing new filings alerts. No API for programmatic access.
- **D&O Relevance:** The most directly relevant litigation database for D&O underwriting. Every securities class action in this database is a potential (or actual) D&O insurance claim. Cross-referencing with SEC enforcement data provides a comprehensive view of a company's litigation and regulatory risk profile.

### 26C. Cornerstone Research / NERA Economic Consulting Reports

- **Full Name:** Cornerstone Research -- Securities Class Action Filings Reports / NERA Economic Consulting -- Recent Trends in Securities Class Action Litigation
- **URL (Cornerstone):** `https://www.cornerstone.com/insights/reports/securities-class-action-filings/`
- **What It Contains:** Annual and semi-annual reports analyzing trends in securities class action filings, SEC enforcement, settlements, and dismissal rates. Provides aggregate statistics on filing volume, industry distribution, settlement amounts, and claim types.
- **Access Method:** Reports downloadable as PDFs for free.
- **Historical Coverage:** Annual reports from approximately 2000 onward.
- **Cost:** Free (reports); paid (consulting engagements).
- **D&O Relevance:** Industry-standard reference for D&O pricing actuarial assumptions and loss trends. Cornerstone's annual SEC enforcement reports and securities litigation reports are widely used by D&O underwriters.

### 26D. OpenSanctions (Aggregated Enforcement Data)

- **Full Name:** OpenSanctions
- **URL:** `https://www.opensanctions.org/`
- **API:** `https://api.opensanctions.org/docs` (Swagger documentation)
- **Datasets Catalog:** `https://www.opensanctions.org/datasets/`
- **What It Contains:** Aggregated data from 320+ data sources worldwide, including: OFAC SDN list, CFTC enforcement actions, FINRA enforcement actions, OCC enforcement actions, Federal Reserve enforcement actions, and many others. Provides entity matching and screening capabilities.
- **Access Method:** API with entity matching, text search, and detailed entity fetching. Bulk data downloads in multiple formats. Pay-as-you-go API service or data license for commercial use.
- **Data Format:** JSON (structured, Follow-the-Money data model), CSV (simplified tabular)
- **Update Frequency:** Daily updates.
- **Cost:** Free for non-commercial use. Commercial use requires data license or API subscription.
- **D&O Relevance:** Extremely useful as an aggregation layer for screening directors and officers across multiple regulatory enforcement databases simultaneously. A single API call can check an individual against OCC, Fed, FDIC, FINRA, CFTC, and OFAC databases.

### 26E. SEC RSS Feeds

- **Full Name:** SEC.gov RSS Feeds
- **URL (Structured Disclosure RSS):** `https://www.sec.gov/structureddata/rss-feeds`
- **URL (General RSS):** `https://www.sec.gov/about/rss-feeds`
- **Available Feeds Include:**
  - XBRL/iXBRL filing RSS (updated every 10 minutes, Mon-Fri, 6am-10pm EST)
  - Press Releases RSS
  - Litigation Releases RSS
  - Administrative Proceedings RSS
  - Staff Accounting Bulletins RSS
  - Investor Alerts RSS
  - Trading Suspensions RSS
  - Company filing RSS (customizable by CIK or form type via EDGAR Company Search)
- **Data Format:** RSS/Atom XML
- **Cost:** Free
- **D&O Relevance:** RSS feeds provide the fastest free notification channel for new enforcement actions, trading suspensions, and material filings. Critical for real-time monitoring in an underwriting system.

### 26F. Third-Party Commercial API: sec-api.io

- **Full Name:** SEC-API (sec-api.io)
- **URL:** `https://sec-api.io/`
- **Documentation:** `https://sec-api.io/docs/`
- **What It Contains:** Commercial API wrapper providing structured JSON access to 18+ million EDGAR filings across all 150+ form types, from 1993 to present. Specific endpoints include:
  - Query API (Lucene-syntax search across all filings)
  - Full-Text Search API
  - Real-Time Stream API (WebSocket)
  - XBRL-to-JSON Converter
  - Insider Trading Data API (Forms 3/4/5)
  - Enforcement Actions Database API (1997+)
  - Litigation Releases Database API (1995+)
  - Administrative Proceedings Database API (1995+, 18,000+ proceedings)
  - AAER Database API (1997+)
  - SEC Comment Letters
  - Form 8-K Item-Level Data APIs
- **Access Method:** REST API with API key. Python (`sec-api` on PyPI) and JavaScript SDKs available.
- **Cost:** Paid (tiered pricing based on usage; free tier available for limited queries).
- **D&O Relevance:** The most comprehensive single commercial API for SEC-related D&O underwriting data. Consolidates multiple SEC data sources into a unified, structured API.

---

## Summary: Access Method Matrix

| Source | Free API | Paid API | Bulk Download | Web Scrape | RSS | FOIA |
|--------|----------|----------|---------------|------------|-----|------|
| EDGAR Submissions | Yes | Yes (sec-api.io) | Yes (ZIP) | N/A | Yes | N/A |
| EDGAR EFTS | Yes | Yes (sec-api.io) | No | Yes | No | N/A |
| XBRL/iXBRL | Yes | Yes (XBRL US) | Yes (ZIP) | N/A | Yes | N/A |
| SEC Enforcement | No | Yes (sec-api.io) | No | Yes | Yes | Yes |
| SEC ALJ Decisions | No | No | No | Yes | No | Yes |
| SEC Whistleblower | No | No | No | Yes | No | Yes |
| SEC Comment Letters | No | Yes (sec-api.io) | No | Yes | No | N/A |
| SEC No-Action Letters | No | No | No | Yes | No | Yes |
| SEC AAERs | No | Yes (sec-api.io) | No | Yes | No | N/A |
| PCAOB Inspections | No | No | Yes (CSV/JSON) | Yes | No | N/A |
| PCAOB Enforcement | No | No | No | Yes | No | N/A |
| DOJ Press Releases | No | No | No | Yes | Yes | Yes |
| FINRA BrokerCheck | No | Yes (FINRA API) | No | No | No | N/A |
| FINRA Disciplinary | No | No | No | Yes | No | N/A |
| CFTC Enforcement | No | No | No | Yes | No | Yes |
| NFA Enforcement | No | No | No | Yes | No | N/A |
| NASAA | No | No | No | Yes | No | N/A |
| NY AG | No | No | No | Yes | No | Yes |
| CA AG | No | No | No | Yes | No | Yes |
| TX SSB | No | No | No | Yes | No | Yes |
| Delaware Chancery | No | No | No | No (paywall) | No | No |
| OCC Enforcement | No | No | Yes (XLS) | Yes | No | Yes |
| Fed Enforcement | No | No | No | Yes | No | Yes |
| FDIC Enforcement | No | No | No | Yes | No | Yes |
| FTC | Yes (limited) | No | No | Yes | No | Yes |
| EPA ECHO | Yes | No | Yes (CSV) | N/A | No | N/A |
| IRS Penalty Data | No | No | Yes (aggregate) | No | No | Yes (limited) |
| OFAC SDN List | No | Yes (3rd party) | Yes (XML/CSV) | N/A | No | N/A |
| OFAC Enforcement | No | No | No | Yes | No | Yes |
| GovInfo/GPO | Yes | No | Yes (XML) | N/A | No | N/A |
| GAO Reports | No | No | No | Yes | No | N/A |
| PACER | Yes (PCL API) | Yes | No | N/A | No | N/A |
| CourtListener | Yes | No | Yes | N/A | No | N/A |
| Stanford SCAC | No | No | No | Yes | Yes (email) | N/A |
| OpenSanctions | Yes (non-commercial) | Yes | Yes | N/A | No | N/A |
| Insider Transactions | No | Yes (sec-api.io) | Yes (SEC bulk) | N/A | No | N/A |

---

## Data Source Priority Ranking for D&O Underwriting

### Tier 1 -- Essential (Must Have)
1. **SEC EDGAR Submissions API** -- Complete filing histories, real-time updates
2. **SEC XBRL/iXBRL Data** -- Structured financial data for quantitative risk models
3. **SEC Enforcement Actions (Litigation Releases + Administrative Proceedings + AAERs)** -- Direct enforcement history
4. **SEC EDGAR Full-Text Search** -- Risk keyword monitoring across all filings
5. **SEC EDGAR 8-K Filings (especially Items 4.01, 4.02, 5.02)** -- Real-time material event monitoring
6. **Forms 3/4/5 Insider Transactions** -- Insider trading pattern analysis
7. **Stanford Securities Class Action Clearinghouse** -- Litigation tracking
8. **FINRA BrokerCheck** -- Individual regulatory history (financial services D&Os)

### Tier 2 -- Highly Valuable
9. **SEC Comment Letters** -- Leading indicator of accounting risk
10. **DEF 14A Proxy Statements** -- Executive compensation and governance analysis
11. **PCAOB Inspection Reports** -- Audit quality assessment
12. **OCC/Fed/FDIC Enforcement Actions** -- Banking D&O history
13. **DOJ Criminal Division / FCPA Clearinghouse** -- Criminal fraud exposure
14. **OFAC SDN List + Enforcement** -- Sanctions risk screening
15. **Audit Analytics (commercial)** -- Structured restatement and D&O change data

### Tier 3 -- Important Context
16. **Delaware Chancery Court Records** -- Corporate governance litigation history
17. **PACER / CourtListener** -- Federal litigation tracking
18. **State AG Enforcement (NY, CA, TX)** -- State-level regulatory risk
19. **CFTC/NFA Enforcement** -- Commodities-related D&O risk
20. **FTC Enforcement** -- Consumer protection and antitrust exposure
21. **EPA ECHO** -- Environmental liability exposure
22. **SEC No-Action Letters** -- Governance dispute indicators
23. **Congressional Hearing Transcripts** -- Political/regulatory attention signals
24. **GAO Reports** -- Systemic risk and regulatory gap analysis
25. **OFAC Enforcement Actions** -- Sanctions compliance failures
26. **IRS Penalty Data** -- Tax fraud exposure (limited availability)
27. **SEC Whistleblower Program Data** -- Aggregate enforcement intensity signals
28. **NASAA State Regulators** -- Aggregate state enforcement trends
29. **SEC Staff Accounting Bulletins** -- Accounting standards context
30. **OpenSanctions** -- Aggregated screening layer

---

## Key Technical Recommendations for System Architecture

1. **Primary Data Ingestion Layer:** Build around the SEC EDGAR APIs (data.sec.gov) for real-time filing data. Supplement with EFTS search API for text analysis. Use bulk ZIP downloads (submissions.zip, companyfacts.zip) for initial database seeding.

2. **Enforcement Data Layer:** Use sec-api.io (commercial) or build scrapers for SEC.gov enforcement pages. Integrate OpenSanctions API as a single aggregation point for OCC, Fed, FDIC, FINRA, CFTC, and OFAC enforcement data.

3. **Real-Time Monitoring:** Subscribe to SEC RSS feeds for new filings, enforcement actions, and trading suspensions. Implement WebSocket streaming via sec-api.io for immediate filing alerts.

4. **Court Records Layer:** Use PACER PCL API for federal case searching. CourtListener RECAP API for free cached documents. File & ServeXpress subscription for Delaware Chancery access.

5. **NLP/Text Mining Layer:** Required for extracting structured information from unstructured sources (SEC comment letters, enforcement releases, ALJ decisions, state AG actions, DOJ press releases, congressional hearings).

6. **Screening Layer:** OFAC SDN list downloads (XML/CSV) for sanctions screening. OpenSanctions API for comprehensive cross-regulatory screening of individual directors and officers.

7. **Data Refresh Cadence:**
   - Real-time: SEC filings, insider transactions, enforcement actions
   - Daily: OFAC SDN list, OpenSanctions
   - Weekly: EPA ECHO bulk data
   - Monthly: OCC/Fed/FDIC enforcement, FINRA disciplinary
   - Quarterly: PCAOB inspection datasets, SEC insider transaction bulk data
   - Annually: NASAA enforcement statistics, IRS aggregate penalty data, SEC Whistleblower reports, GAO reports
