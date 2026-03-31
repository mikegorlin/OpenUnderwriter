# D&O Liability Underwriting: Comprehensive Data Source Inventory

## Purpose
This document is an exhaustive inventory of academic, industry, insurance, corporate governance, financial, and alternative data sources relevant to building a Directors and Officers (D&O) liability underwriting system. Each entry documents the source name, URL, data contents, access method, historical coverage, data format, cost, and known limitations.

---

# SECTION 1: ACADEMIC AND RESEARCH SOURCES

---

## 1. Cornerstone Research Annual Securities Class Action Reports

**Full Name:** Cornerstone Research Securities Class Action Filings/Settlements Reports (in cooperation with Stanford Law School Securities Class Action Clearinghouse)

**URL:** https://www.cornerstone.com/insights/reports/securities-class-action-filings/

**Data Contents:**
- Annual and mid-year reports on securities class action filings in federal and state courts
- Filing counts, Disclosure Dollar Loss (DDL) Index, Maximum Dollar Loss (MDL) Index
- Breakdown by sector (healthcare, technology, etc.), allegation type, court/jurisdiction
- Settlement data: aggregate settlement value, median settlement value, resolution counts (dismissals vs. settlements)
- Trend data on AI-related filings, event-driven litigation, and emerging claim categories
- In 2025: 207 filings; DDL of $694 billion; MDL of $2,862 billion (third-highest on record)

**How to Access:** Free PDF downloads from Cornerstone Research website. Reports are published annually (full year) and semi-annually (mid-year update).

**Historical Coverage:** Reports published since 1996, coinciding with the Private Securities Litigation Reform Act (PSLRA) of 1995. Comprehensive longitudinal data spanning nearly 30 years.

**Data Format:** PDF reports with charts, tables, and trend analysis. Raw data not directly downloadable.

**Cost:** Free

**Known Limitations:**
- Data is aggregated/summarized; granular case-level data requires pairing with the Stanford SCAC database
- Reports focus on federal securities class actions; coverage of state-court-only filings may be less complete
- DDL/MDL indices are estimates based on stock price declines, not actual damages
- Lag between filing activity and report publication (typically 1-3 months)

---

## 2. NERA Economic Consulting Securities Litigation Reports

**Full Name:** NERA Economic Consulting -- Recent Trends in Securities Class Action Litigation

**URL:** https://www.nera.com/insights/publications/2026/recent-trends-in-securities-class-action-litigation--2025-full-y.html

**Data Contents:**
- Annual and semi-annual (H1) reports on federal securities class action trends
- Filing counts, sector breakdowns (healthcare, technology = 57% of filings in 2025)
- Allegation type analysis (missed earnings guidance, regulatory issues, accounting fraud)
- Case resolution data: dismissal rates, settlement counts, aggregate and median settlement values
- Settlement value analysis: $2.9 billion aggregate in 2025; median settlement $17 million (10-year high)
- Time-to-resolution metrics and class certification data

**How to Access:** Free PDF downloads from NERA website. Webinars often accompany report releases.

**Historical Coverage:** Annual reports published since 1996. H1 updates added in recent years.

**Data Format:** PDF reports with detailed statistical analysis, charts, and tables.

**Cost:** Free

**Known Limitations:**
- Federal court filings only; excludes state-court-only securities actions
- Settlement analysis limited to resolved cases (survivorship bias)
- No case-level downloadable data; summary statistics only
- Methodology for counting filings may differ slightly from Cornerstone Research (compare both for completeness)

---

## 3. Advisen/Zywave Loss Insight Database

**Full Name:** Zywave Loss Insight (formerly Advisen Loss Insight)

**URL:** https://www.advisenltd.com/data/loss-data/ and https://www.zywave.com/insurer/loss-insight/

**Data Contents:**
- Over 1 million historical loss records covering $3+ trillion in loss value
- D&O-specific relational database covering events relating to directors and officers liability
- Coverage spans public and private companies, 93 countries
- Data fields: geography, company size, company type, sub-industry, coverage type, loss amounts, settlement data
- Separate modules for cyber, casualty, D&O, and EPLI losses
- Public D&O Loss Data module available separately

**How to Access:** Commercial subscription via Zywave. Demo requests available online. Data delivered via FTP for integration with BI systems. Also available via web-based search interface.

**Historical Coverage:** Oldest entry from 1938. Extremely comprehensive for the last 20+ years.

**Data Format:** Relational database accessible via FTP/API. Searchable by geography, company size, company type, sub-industry, and coverage type.

**Cost:** Paid subscription (enterprise licensing). Pricing not publicly disclosed; contact Zywave for quotes. Over 250 insurance carriers, brokerages, and service providers are subscribers.

**Known Limitations:**
- Proprietary/closed; no free tier
- Data completeness varies by geography (strongest for US/UK/Canada)
- Historical data quality degrades for older entries
- Some loss amounts are estimates rather than confirmed settlements
- Integration requires technical capability (FTP setup, data modeling)
- Zywave acquired Advisen in November 2020; some legacy data structures may vary

---

## 4. Stanford Law School Securities Class Action Clearinghouse (SCAC)

**Full Name:** Securities Class Action Clearinghouse, Stanford Law School (in cooperation with Cornerstone Research)

**URL:** https://securities.stanford.edu/ (main SCAC site) and https://sla.law.stanford.edu/ (Stanford Securities Litigation Analytics)

**Data Contents:**
- Database of 3,600+ securities class action lawsuits filed since passage of the PSLRA (1995)
- Over 43,000 complaints, briefs, filings, and other litigation-related materials
- Case-level data: company name, industry, filing date, court, lead plaintiff, alleged violations, outcomes
- Full-text search across filings
- Advanced search by data fields (date range, industry, type of allegation, status)
- New filings email alerts

**How to Access:** Free public access via securities.stanford.edu. Full-text search and advanced search available. NOTE: As of recent updates, the SCAC is undergoing restructuring and has paused updates to the main Clearinghouse website. The Stanford Securities Litigation Analytics (SSLA) project continues providing New Filings emails.

**Historical Coverage:** 1995-present (post-PSLRA). Some historical data on pre-PSLRA filings may be available.

**Data Format:** Web-based searchable database. Individual case files downloadable as PDFs.

**Cost:** Free

**Known Limitations:**
- Currently undergoing restructuring; updates paused on main Clearinghouse website
- Federal court filings primarily; limited state court coverage
- Data extraction for quantitative analysis requires manual work or scraping (no bulk download API)
- Settlement amounts not always available for all cases
- Reliance on voluntary case submissions and public filings

---

## 5. Harvard Law School Forum on Corporate Governance

**Full Name:** The Harvard Law School Forum on Corporate Governance (founded by Professor Lucian Bebchuk, 2006)

**URL:** https://corpgov.law.harvard.edu/

**Data Contents:**
- Daily articles, commentaries, and speeches by prominent scholars, public officials, and practitioners
- Topics: corporate governance, financial regulation, D&O liability, ESG, executive compensation, shareholder activism, board practices, M&A governance
- Over 10,000 posts by 5,000+ contributors since 2006
- Posts cited in 800+ law review articles and regulatory materials
- Legislative and regulatory development updates
- Working paper announcements and summaries

**How to Access:** Free public access. Email subscription available for daily digest. Searchable archive.

**Historical Coverage:** 2006-present. Archive of all posts maintained.

**Data Format:** Blog posts (HTML). No structured data download.

**Cost:** Free

**Known Limitations:**
- Commentary/analysis rather than raw data
- No structured database for quantitative analysis
- Quality varies by contributor (opinion pieces mixed with empirical research summaries)
- Not peer-reviewed; relies on contributor expertise
- Search functionality limited compared to academic databases

---

## 6. Columbia Law School CLS Blue Sky Blog

**Full Name:** CLS Blue Sky Blog, Columbia Law School

**URL:** https://clsbluesky.law.columbia.edu/

**Data Contents:**
- Original and aggregated commentary on securities regulation, capital markets, corporate governance, M&A, Dodd-Frank, financial reform, the SEC, insider trading
- Categories include: Securities Regulation, Corporate Governance, Securities Litigation
- Editorial board includes John C. Coffee Jr. (leading securities law scholar)
- Guest contributions from law firm partners, law professors, finance professors, and PhD students
- Analysis of landmark D&O cases, regulatory changes, and market trends

**How to Access:** Free public access. Tagged and categorized for easy navigation.

**Historical Coverage:** Since 2011. Full archive maintained.

**Data Format:** Blog posts (HTML). No structured data.

**Cost:** Free

**Known Limitations:**
- Commentary/analysis format; not a data source per se
- Irregular posting frequency
- No structured data for quantitative analysis
- Focuses on securities regulation broadly; D&O-specific content is a subset

---

## 7. NYU Pollack Center for Law & Business / SEED Database

**Full Name:** NYU Pollack Center for Law & Business; Securities Enforcement Empirical Database (SEED)

**URL:** https://www.law.nyu.edu/centers/pollackcenterlawbusiness/seed and https://research.seed.law.nyu.edu/

**Data Contents:**
- SEED tracks SEC enforcement actions against public companies since October 1, 2009
- Variables: defendant names and types, violations, venues, and resolutions
- Created in cooperation with Cornerstone Research
- Regular updates of new filings and settlement information
- Analysis of multi-year trends and priorities in federal securities enforcement
- Original academic and industry research publications

**How to Access:** Free public access via SEED website. Searchable online database. Publications available for download.

**Historical Coverage:** October 2009-present (SEC enforcement actions filed since that date).

**Data Format:** Web-based searchable database. Research reports in PDF.

**Cost:** Free

**Known Limitations:**
- Covers SEC enforcement actions only (not private securities class actions or state actions)
- Limited to actions against public companies traded on major U.S. exchanges and their subsidiaries
- Does not include all SEC enforcement activity (focuses on public company actions)
- Database structure may require manual data extraction for bulk analysis
- Limited international coverage

---

## 8. Wharton Research Data Services (WRDS)

**Full Name:** Wharton Research Data Services (WRDS), The Wharton School, University of Pennsylvania

**URL:** https://wrds-www.wharton.upenn.edu/

**Data Contents:**
- 350+ TB of data across finance, accounting, banking, economics, management, and marketing
- Key datasets for D&O underwriting:
  - **CRSP**: Stock returns, prices, volumes (1925-present)
  - **Compustat**: Financial statement data (1950-present)
  - **ExecuComp**: Executive compensation (1992-present)
  - **BoardEx**: Director networks and biographical data (1999-present)
  - **Audit Analytics**: Restatements, auditor changes, SOX compliance (2000-present)
  - **Sustainalytics**: ESG risk ratings
  - **ISS (RiskMetrics)**: Corporate governance provisions
  - **Directors data**: Board composition, tenure, gender, committee memberships
  - **Governance data**: Takeover defenses, classified boards, poison pills
  - **Incentive Lab**: Executive compensation performance metrics

**How to Access:** Institutional subscription required (primarily academic institutions). Nearly 450 academic institutions in 35 countries have access. Web-based interface for queries; also supports SAS, Python, R, and Stata.

**Historical Coverage:** Varies by dataset; some data back to 1925 (CRSP). Processing speeds up to 400MB/second.

**Data Format:** Multiple formats: SAS, CSV, Stata, R, Python. Cloud-based query system.

**Cost:** Institutional subscription. Pricing varies by institution size and datasets selected. Individual access typically through university affiliation. S&P Global Academic Research Essentials provides Compustat and CRSP via WRDS.

**Known Limitations:**
- Requires institutional (typically academic) affiliation for access
- No individual consumer subscriptions
- Dataset coverage varies (some datasets US-only, some global)
- Learning curve for query interface
- Some datasets have additional licensing requirements beyond base WRDS subscription
- No dedicated "D&O insurance" dataset, but governance-adjacent data is extensive

---

## 9. SSRN (Social Science Research Network) -- D&O Liability Papers

**Full Name:** Social Science Research Network (SSRN), an Elsevier property

**URL:** https://papers.ssrn.com/

**Data Contents:**
- Pre-print and working paper repository for social sciences including law, finance, and economics
- Extensive collection of D&O liability research papers, including:
  - "The Role of D&O Insurance in Securities Fraud Class Action Settlements" (Donelson et al.)
  - "How Protective is D&O Insurance in Securities Class Actions?" (Klausner et al.)
  - "Directors' and Officers' Liability Insurance and Loan Spreads" (Lin et al.)
  - "Information Embedded in Directors and Officers Insurance Purchases" (Gupta, Prakash)
  - "The Missing Monitor in Corporate Governance: The Directors' & Officers' Liability Insurer" (Baker, Griffith)
  - "Predicting Corporate Governance Risk: Evidence from the D&O Liability Insurance Market" (Baker, Griffith)
- Searchable by topic, author, keyword, and abstract

**How to Access:** Free to read most papers. Authors upload papers directly. Some papers may be behind paywalls at the journal level.

**Historical Coverage:** SSRN launched in 1994. Papers span several decades of research.

**Data Format:** PDF papers. Metadata searchable via web interface.

**Cost:** Free for reading. Authors may pay for certain services.

**Known Limitations:**
- Working papers / pre-prints; not all are peer-reviewed
- Quality varies significantly across papers
- Not a structured data source; qualitative research findings
- Search results may include tangentially related papers
- Data within papers (e.g., empirical datasets) typically not directly downloadable
- SSRN increasingly owned by Elsevier; some access restrictions may evolve

---

## 10. National Bureau of Economic Research (NBER) Working Papers

**Full Name:** National Bureau of Economic Research Working Papers

**URL:** https://www.nber.org/papers

**Data Contents:**
- Working papers by leading economists on corporate governance, director liability, and related topics
- Key papers include:
  - "The State of Corporate Governance Research" (w15537)
  - "Powerful Independent Directors" (w19809)
  - "The New Corporate Governance" (w29975)
  - "Behavioral Finance in Corporate Governance" (w10644)
  - "The Corporate Governance Role of the Media" (w9309)
  - "A Survey of Corporate Governance" (w5554)
- Papers cover shareholder activism, board structures, executive compensation, controlling shareholders, comparative corporate governance

**How to Access:** Abstracts are free. Full papers require NBER subscription or institutional access. Many papers are also posted on authors' personal websites or SSRN.

**Historical Coverage:** NBER established 1920; working paper series dates back decades. Over 30,000 working papers.

**Data Format:** PDF papers.

**Cost:** Abstracts free. Full text: NBER subscription ($170/year for non-academic individual; free for affiliates of subscribing institutions). Many also on SSRN for free.

**Known Limitations:**
- Working papers, not peer-reviewed journal articles
- Not a data source per se; provides research findings and methodology
- Access cost for full papers if no institutional affiliation
- Corporate governance papers are a subset of broader NBER coverage
- Data referenced in papers must be sourced separately

---

## 11. Journal of Financial Economics -- D&O Research

**Full Name:** Journal of Financial Economics (JFE), published by Elsevier

**URL:** https://www.sciencedirect.com/journal/journal-of-financial-economics

**Data Contents:**
- Peer-reviewed research articles on D&O liability, corporate governance, securities fraud
- Key research findings relevant to underwriting:
  - D&O insurance coverage's relationship to loan spreads
  - Information content of D&O insurance purchases
  - Cost of equity and D&O insurance
  - D&O insurance and corporate risk-taking
- Empirical studies using ExecuComp, CRSP, Compustat, and proprietary D&O policy data

**How to Access:** ScienceDirect subscription (institutional or individual). Many university libraries provide access.

**Historical Coverage:** Published since 1974. D&O-specific research concentrated in post-2000 era.

**Data Format:** PDF journal articles.

**Cost:** Elsevier subscription required. Institutional pricing varies. Individual articles typically $30-40 each if purchased separately.

**Known Limitations:**
- Behind paywall for non-subscribers
- Research findings, not raw data
- Publication lag (research may be 1-3 years behind current market conditions)
- Replication data sometimes available from authors but not guaranteed

---

## 12. Journal of Law and Economics

**Full Name:** The Journal of Law and Economics, published by University of Chicago Press

**URL:** https://academic.oup.com/jleo (Journal of Law, Economics, and Organization) and https://www.journals.uchicago.edu/toc/jle/current (Journal of Law and Economics)

**Data Contents:**
- Peer-reviewed research at the intersection of law and economics
- D&O-relevant topics: director liability, securities regulation, corporate governance mechanisms, litigation economics, regulatory enforcement
- Key papers include Baker & Griffith's work on D&O insurance as governance mechanism

**How to Access:** University of Chicago Press subscription or institutional access. JSTOR access for archival issues.

**Historical Coverage:** Published since 1958.

**Data Format:** PDF journal articles.

**Cost:** Institutional subscription. Individual articles purchasable.

**Known Limitations:**
- Research-focused, not a data source
- Behind paywall
- Broader than D&O; requires filtering for relevant content
- Publication cycle lag

---

## 13. Review of Financial Studies

**Full Name:** The Review of Financial Studies (RFS), published by Oxford University Press on behalf of the Society for Financial Studies

**URL:** https://academic.oup.com/rfs

**Data Contents:**
- Top-tier peer-reviewed finance journal
- Corporate governance special issues co-sponsored with NBER
- Research on D&O insurance determinants, pricing, and governance effects
- Studies linking D&O insurance to corporate outcomes: investment behavior, financial reporting quality, audit outcomes, capital market performance

**How to Access:** Oxford University Press subscription or institutional access. Some articles available via SSRN pre-prints.

**Historical Coverage:** Published since 1988.

**Data Format:** PDF journal articles.

**Cost:** Institutional or individual subscription via OUP.

**Known Limitations:**
- Behind paywall
- Research findings rather than data
- Highly selective publication; limited number of D&O-specific articles per year
- Significant publication lag

---

## 14. Georgetown Law Center Securities Regulation Papers

**Full Name:** Georgetown University Law Center -- Securities and Financial Regulation Research

**URL:** https://scholarship.law.georgetown.edu/ and https://www.ssrn.com/link/Georgetown-LEG.html

**Data Contents:**
- Faculty working papers on securities regulation, D&O liability, SEC enforcement
- Notable contributors include Donald C. Langevoort (SEC regulation, securities law)
- Georgetown Law Faculty Working Papers series on SSRN
- Securities law research guides and treatise finders
- Securities & Financial Law Certificate program publications

**How to Access:** Free access to many papers via Georgetown scholarship repository and SSRN. Research guides free online.

**Historical Coverage:** Faculty papers span multiple decades. SSRN series ongoing.

**Data Format:** PDF papers. Web-based research guides.

**Cost:** Free for most papers.

**Known Limitations:**
- Research/commentary, not structured data
- Smaller volume of D&O-specific papers compared to Stanford or Harvard
- Not a dedicated D&O research center
- Papers may be exploratory/working rather than definitive

---

# SECTION 2: INSURANCE INDUSTRY SOURCES

---

## 15. AM Best D&O Insurance Market Reports

**Full Name:** AM Best -- Best's Market Segment Report: Directors & Officers Liability

**URL:** https://news.ambest.com/ (search for D&O reports)

**Data Contents:**
- Annual market segment reports on D&O liability insurance
- Direct written premiums ($10.8 billion in 2024, down 6% from 2023)
- Direct calendar year loss ratios (49.0% in 2024)
- Underwriting profitability trends
- Rate trend analysis
- Emerging risk assessment (AI, cyber, tariffs, regulatory shifts)
- Capacity analysis and market cycle positioning

**How to Access:** Some press releases and summaries free. Full reports require AM Best subscription.

**Historical Coverage:** AM Best has tracked insurance markets for over 100 years. D&O-specific reports available for at least 10-15 years.

**Data Format:** PDF reports. AM Best also offers data via its BestLink platform.

**Cost:** AM Best subscription required for full reports. BestLink access priced separately. Individual reports available for purchase.

**Known Limitations:**
- Full reports behind paywall
- Aggregated industry-level data (not company-specific policy data)
- US-focused (limited international D&O market data)
- Annual publication cadence (data may be 6-12 months old)

---

## 16. Willis Towers Watson (WTW) D&O Liability Survey

**Full Name:** WTW Global Directors' and Officers' Survey Report / Insurance Marketplace Realities -- D&O

**URL:** https://www.wtwco.com/en-us/insights/2025/01/directors-and-officers-d-and-o-liability-a-look-ahead-to-2025

**Data Contents:**
- Global D&O risk survey covering directors and officers worldwide
- Top risk concerns: health and safety (80%), data loss/cyber (77%), civil litigation (63%), supplier practices (59%), human rights (62%)
- Insurance Marketplace Realities (IMR) quarterly/semi-annual updates on D&O pricing and market conditions
- D&O Insights Hub with trend analysis
- Rate movement data and market cycle analysis

**How to Access:** Some reports freely downloadable from WTW website. Others may require registration. IMR updates published regularly.

**Historical Coverage:** Annual survey published for multiple years (2024/2025 survey is the latest). Global coverage.

**Data Format:** PDF reports and web-based content.

**Cost:** Free (most reports available after registration).

**Known Limitations:**
- Survey-based data (subjective perceptions of risk, not claims data)
- Sample may skew toward WTW client base
- Pricing data based on WTW's book of business, not industry-wide
- Limited granularity for underwriting model inputs

---

## 17. Marsh D&O Benchmarking Reports

**Full Name:** Marsh McLennan -- D&O Benchmarking & FINPRO Management Liability Reports

**URL:** https://www.marsh.com/en/services/financial-professional-liability/expertise/directors-and-officers-liability.html

**Data Contents:**
- D&O benchmarking service with predictive modelling for claim frequency and severity
- Quarterly rate change data (D&O rates declined 5% in Q1 2025)
- Primary and excess layer pricing trends
- Retention analysis (average retention dropped from $2.5M to $1.5M)
- FINPRO quarterly management liability newsletters
- Market capacity and insurer appetite analysis

**How to Access:** Benchmarking service available to Marsh clients. Some reports and newsletters freely available on Marsh website. Quarterly US Insurance Rate reports published publicly.

**Historical Coverage:** Marsh has published D&O benchmarking data for many years. Quarterly rate data available.

**Data Format:** PDF reports. Benchmarking tool available to clients.

**Cost:** Benchmarking service free to Marsh clients. Reports generally free with registration.

**Known Limitations:**
- Benchmarking data reflects Marsh's client portfolio (potential bias toward larger companies)
- Detailed benchmarking requires Marsh client relationship
- Rate data is aggregate (not policy-level)
- May not capture non-Marsh market segments (E&S, small commercial)

---

## 18. Aon D&O Liability Reports

**Full Name:** Aon Financial Services Group -- D&O Liability Reports & Quarterly Pricing Index

**URL:** https://www.aon.com/risk-services/financial-services-group/fsg-content-center.jsp and https://www.aon.com/risk-services/financial-services-group/quarterly-d-o-pricing-index-report-downloads

**Data Contents:**
- Quarterly D&O Pricing Index: tracks cost per $1M of D&O limits over time (decreased to 1.06 in Q2 2025)
- Primary and excess layer pricing trends (mid-single digit decreases trending to flat)
- NACD Director Essentials reports (D&O Insurance guide for directors)
- Management liability market outlook reports
- Claims environment analysis (AI, cyber, ESG)
- Public vs. private company D&O market conditions

**How to Access:** Some reports freely downloadable. Quarterly Pricing Index available for download. NACD collaboration reports may require NACD membership.

**Historical Coverage:** Pricing Index tracks changes over 10+ years with quarterly granularity. Reports published annually.

**Data Format:** PDF reports. Pricing Index data in report format.

**Cost:** Free (most reports). Some NACD-partnered content may require membership.

**Known Limitations:**
- Pricing data reflects Aon's book of business
- Index-based rather than absolute pricing data
- Public company focus for pricing index
- Limited granularity for building underwriting models (aggregate, not policy-level)

---

## 19. AIG D&O Claims Data Publications

**Full Name:** AIG Claims Intelligence Series -- Directors & Officers Liability

**URL:** https://www.aig.com/home/claims/claims-intelligence-series

**Data Contents:**
- Analysis of 10,500+ D&O matters noticed on policies from 2016-2020 (North American D&O)
- Financial institution and commercial account breakdowns
- Claims Intelligence Series case studies and trend reports
- 10-year claims payment data ($20.6 billion paid, 250,000+ Financial Lines claims handled)
- Public Company D&O Claims Report
- Analysis of non-SCA D&O exposures (regulatory, derivative, criminal, bankruptcy)
- 60 years of D&O data and expertise

**How to Access:** Free PDF downloads from AIG website. Claims Intelligence Series publicly available.

**Historical Coverage:** 60+ years of D&O expertise. Published claims data spans 2016-2020 policy years. 10-year payment data.

**Data Format:** PDF reports and case studies.

**Cost:** Free

**Known Limitations:**
- Based solely on AIG's book of business (one carrier's perspective)
- Claims data aggregated, not case-level
- Policy years analyzed may lag current market conditions
- May not represent full market experience (market share limitations)
- Designed for marketing/education, not actuarial analysis

---

## 20. Chubb D&O Insights

**Full Name:** Chubb Management Liability Insights / Private Company Risk Survey

**URL:** https://www.chubb.com/us-en/business-insurance/management-liability-insights.html

**Data Contents:**
- Private Company Risk Survey: risk perceptions and loss experience among private company executives
- Finding: 1 in 4 private companies experienced a D&O loss in a 3-year period (2016 survey)
- Management liability insights covering D&O, EPL, cyber, and crime
- D&O coverage analysis for public, private, and nonprofit organizations
- Loss prevention guidance
- Coverage available in 40+ countries

**How to Access:** Free reports available on Chubb website. Survey results published periodically.

**Historical Coverage:** Chubb has published D&O research for many years. Periodic surveys.

**Data Format:** PDF reports, web content.

**Cost:** Free

**Known Limitations:**
- Survey-based data (self-reported loss experience)
- Based on Chubb's client base and survey respondents
- Periodic rather than continuous publication
- Private company focus for surveys (less relevant for public company D&O)
- Marketing-oriented content

---

## 21. Allianz Commercial (AGCS) D&O Reports

**Full Name:** Allianz Commercial -- Directors and Officers (D&O) Insurance Insights (Annual Report)

**URL:** https://commercial.allianz.com/news-and-insights/reports/directors-and-officers-insurance-insights.html

**Data Contents:**
- Annual D&O Insurance Insights report (2023, 2024, 2025, 2026 editions)
- Global D&O risk trends: geopolitical uncertainty, AI risks, cyber, ESG, insolvencies
- Claims rebound analysis: 50+ AI-related lawsuits in 5 years
- Securities class action settlement cost data (average up 27% to $56M in H1 2025)
- Global business insolvency forecasts (+6% in 2025, +5% in 2026)
- Geographic risk analysis (US, UK, Europe, Asia)

**How to Access:** Free PDF downloads from Allianz Commercial website.

**Historical Coverage:** Annual reports published for at least 4-5 years (2022-2026). Claims analysis may reference longer historical periods.

**Data Format:** PDF reports.

**Cost:** Free

**Known Limitations:**
- Allianz-centric view; based on their claims experience and outlook
- Global focus may lack US-specific granularity needed for domestic underwriting
- Forward-looking risk assessments are inherently uncertain
- Annual publication cycle

---

## 22. Swiss Re Sigma Studies on Liability

**Full Name:** Swiss Re Institute Sigma Studies (Liability and Social Inflation Focus)

**URL:** https://www.swissre.com/institute/research/sigma-research.html

**Data Contents:**
- Sigma studies covering global insurance market trends
- Key liability-relevant publications:
  - Sigma 4/2024: "Social inflation: litigation costs drive claims inflation"
  - Sigma 3/2025: "Growing stronger: P&C market adapts to riskier world"
  - Sigma 5/2025: Global economic and insurance market outlook
- Social inflation quantification: 5.4% annually (US, 2017-2022); ~7% in 2023 (20-year high)
- Liability premium growth forecast: 7.7% annual growth
- Liability claims severity: CAGR of ~3.8% (2014-2019)
- Geographic variation analysis (US, UK, Australia, Canada, Germany, Japan)

**How to Access:** Free downloads from Swiss Re Institute website. Sigma Explorer tool provides interactive data access.

**Historical Coverage:** Sigma studies published since 1965. Comprehensive historical time series.

**Data Format:** PDF reports. Sigma Explorer provides interactive data visualization.

**Cost:** Free

**Known Limitations:**
- Focuses on overall liability, not D&O-specific
- Reinsurance perspective may differ from primary market view
- Global/macro-level; limited company-specific data
- Social inflation metrics are Swiss Re's proprietary estimates

---

## 23. Lloyd's of London D&O Market Reports

**Full Name:** Lloyd's of London -- Market Data, Syndicate Reports, and D&O Performance Statistics

**URL:** https://www.lloyds.com/news-and-insights/data-and-research/market-data and https://www.lloyds.com/about-lloyds/investor-relations/financial-performance/syndicate-reports-and-accounts

**Data Contents:**
- Market-level statistics: 78 syndicates, 51 managing agencies, GBP 52.1 billion gross premiums (2023)
- Professional lines premium data (D&O premiums contracted 6% YoY)
- Syndicate-level reports and accounts (downloadable from 2014 onward)
- Market data dashboards with key performance measures
- D&O line-specific data within broader management liability class
- Management Liability breakdown: Commercial D&O, Transactional Liability, Individual Directors' Liability, Pension Trustee Liability, Prospectus Liability, EPL

**How to Access:** Syndicate reports freely available for download. Market data dashboards publicly accessible. Some data may require Lloyd's market participant credentials.

**Historical Coverage:** Syndicate reports from 2014 onward. Market data archives span multiple years.

**Data Format:** PDF reports. Interactive dashboards. Data extractable from dashboards.

**Cost:** Free (public data). Some detailed analytics may require Lloyd's market access.

**Known Limitations:**
- London market perspective; may not reflect broader US market
- D&O is a subset of professional lines; disaggregated data may be limited
- Syndicate-level data requires aggregation for market-level analysis
- Specialty/excess layers focus (less primary D&O)
- UK regulatory and accounting standards differ from US

---

## 24. NAIC Financial Data

**Full Name:** National Association of Insurance Commissioners (NAIC) Financial Data Repository

**URL:** https://content.naic.org/industry_financial_filing.htm

**Data Contents:**
- Statutory financial filings from all US-licensed insurance companies
- Annual and quarterly statement data
- Director and Officer Insurance Coverage Supplement filings
- Insurance Regulatory Information System (IRIS) Financial Ratio Reports
- Risk-based capital analysis data
- Premium, loss, expense, and reserve data by line of business
- Market share data by company and state

**How to Access:** NAIC maintains the Financial Data Repository. Filings submitted by state-regulated insurers. Data available through NAIC products (State/Zip data, Financial Statement Data) and via state insurance department records. Some data available through commercial redistributors.

**Historical Coverage:** Updated annually. Historical data available for multiple years.

**Data Format:** Structured data (statutory filing format). Available via NAIC data products.

**Cost:** NAIC data products are paid. Pricing varies by product and user type. Some state-level data may be free through individual state insurance department websites.

**Known Limitations:**
- D&O data is a subset of broader financial statement filings
- Line-of-business coding may not precisely isolate D&O from other management liability
- Statutory accounting (SAP) differs from GAAP
- Data is insurer-level, not policy-level
- Access to detailed data requires NAIC product purchase
- Reporting lag (annual filings may be 3-6 months after year-end)

---

## 25. ISO/Verisk D&O Loss Cost Data

**Full Name:** ISO (Insurance Services Office), a Verisk Business -- Management Liability Loss Costs and Analytics

**URL:** https://www.verisk.com/products/forms-rules-and-loss-costs/ and https://www.verisk.com/insurance/markets/specialty-commercial-lines/

**Data Contents:**
- ISO forms, rules, and loss costs for management and professional liability
- Loss cost experience data (20+ years of history, refreshed annually with quarterly inflation reports)
- Management Protection Program: D&O, EPL, fiduciary liability, financial institutions, professional liability
- ISO DataCube and Market Landscape: 72 markets, 6.9 million loss and premium triangles, $1.4 trillion loss data
- ISO Risk Analyzer: predictive analytics for specialty lines
- ISO Size-of-Loss Matrix for loss distribution analysis

**How to Access:** ISO member/subscriber access. Verisk commercial products. Data accessible via Verisk platform or data feeds.

**Historical Coverage:** 20+ years of loss cost data. Forms and rules updated regularly.

**Data Format:** Structured data via Verisk platform. Various delivery methods (API, cloud, downloads).

**Cost:** Paid (Verisk commercial subscription). ISO membership for insurers. Pricing varies by product and data scope.

**Known Limitations:**
- Primarily for ISO member companies
- D&O loss cost data may be limited due to low-frequency/high-severity nature of D&O claims
- Management liability is a newer ISO line (less historical depth than standard lines)
- Credibility of D&O loss costs may be lower than for high-frequency lines
- Not all D&O carriers report to ISO

---

## 26. Advisen/Zywave Loss Insight Database

*See entry #3 above (same source).*

---

## 27. Insurance Information Institute (III) D&O Reports

**Full Name:** Insurance Information Institute (Triple-I)

**URL:** https://www.iii.org/

**Data Contents:**
- General insurance industry education and data resources
- D&O liability insurance market overviews and fact sheets
- Industry-wide statistics on commercial lines including D&O
- Background information on D&O coverage types (Side A, B, C)
- Market size data references
- Links to other data sources

**How to Access:** Free public access to most content on III website.

**Historical Coverage:** III has operated since 1960. D&O content available for recent years.

**Data Format:** Web content, fact sheets, PDFs.

**Cost:** Free

**Known Limitations:**
- Educational/overview content rather than deep data
- Limited original D&O-specific research
- Relies on aggregating data from other sources
- Not suitable as primary underwriting data source
- Infrequent updates to D&O-specific content

---

## 28. Betterley Risk Consultants D&O Market Survey

**Full Name:** The Betterley Report -- Management Liability / Side A D&O Insurance Market Survey

**URL:** https://subscribe.irmi.com/betterley-report-private-company-management-liability and https://thebetterleyreport.wordpress.com/

**Data Contents:**
- Independent annual survey of D&O insurance products from major carriers
- Product feature comparisons across insurers
- Coverage analysis: Side A D&O, management liability, private company D&O
- No advertising; completely independent evaluations
- Published 6 reports per year covering management liability, cyber, IP, media, and more
- Market trend analysis

**How to Access:** Subscription via IRMI (International Risk Management Institute). Reports published annually.

**Historical Coverage:** The Betterley Report created in 1994. Annual surveys published since then.

**Data Format:** PDF reports (detailed product comparison matrices).

**Cost:** Paid subscription through IRMI. Individual reports available for purchase. Pricing not publicly listed.

**Known Limitations:**
- Subscription required
- Product comparison focus (not claims/loss data)
- Survey-based; relies on carrier submissions
- May not cover all market participants (smaller/specialty carriers may be excluded)
- Annual cycle; may not capture mid-year product changes

---

## 29. Woodruff Sawyer D&O Looking Ahead Guide

**Full Name:** Woodruff Sawyer -- D&O Looking Ahead Guide (Annual)

**URL:** https://woodruffsawyer.com/insights/do-looking-ahead-guide

**Data Contents:**
- 13th annual edition (2026 Looking Ahead published September 2025)
- Emerging risk analysis: AI-driven disclosure challenges, reincorporation debates, DEI backlash, cyber risk, FCPA enforcement
- D&O insurance market data: pricing trends, benchmarking statistics, capacity analysis
- Underwriters Weigh In survey with advice from D&O underwriters
- Private Company D&O Insurance Guide (separate publication)
- D&O Notebook blog series with ongoing analysis

**How to Access:** Free download from Woodruff Sawyer website (registration may be required).

**Historical Coverage:** Published annually for 13+ years. Archived editions available.

**Data Format:** PDF guide (comprehensive report format).

**Cost:** Free

**Known Limitations:**
- Woodruff Sawyer's client perspective (West Coast broker focus)
- Market data based on their book of business
- Forward-looking analysis inherently speculative
- Annual publication; may not capture rapid market changes
- Primarily US market focused

---

# SECTION 3: CORPORATE GOVERNANCE DATA

---

## 30. ISS (Institutional Shareholder Services) Governance QualityScore

**Full Name:** ISS ESG Governance QualityScore

**URL:** https://www.issgovernance.com/esg/ratings/governance-qualityscore/

**Data Contents:**
- Decile-based governance risk score (1 = low risk, 10 = high risk)
- 230+ governance factors across four categories:
  1. Board Structure
  2. Compensation/Remuneration
  3. Shareholder Rights and Takeover Defenses
  4. Audit and Risk Oversight
- Coverage: 6,800+ companies in 30 markets
- Updated annually with verification periods for issuers
- Proxy voting recommendations
- Custom governance analytics

**How to Access:** ISS DataDesk platform, data feeds, API, or third-party platforms (FactSet, Bloomberg). Subscription required.

**Historical Coverage:** ISS governance data available since early 2000s (legacy RiskMetrics data).

**Data Format:** Structured data via DataDesk, API, or data feed.

**Cost:** Starting at $10,000/year. Pricing varies by delivery method and scope.

**Known Limitations:**
- Significant cost barrier
- Methodology changes over time make longitudinal comparisons difficult
- Decile-based scoring reduces granularity
- US-centric methodology may not translate perfectly to non-US markets
- Governance scores can be gamed by issuers (form over substance)
- Annual update cycle with lag

---

## 31. Glass Lewis Governance Data

**Full Name:** Glass Lewis & Co. -- Governance Hub and Proxy Advisory Services

**URL:** https://www.glasslewis.com/

**Data Contents:**
- Independent proxy research and voting recommendations
- Governance analysis for institutional investors (1,300+ globally)
- Governance Hub for public companies: governance data, insights, vote recommendations
- Proxy Paper analysis for each company's annual meeting
- In-depth special reports on governance themes
- Policy guidelines and season previews/reviews
- Compensation analysis and say-on-pay recommendations

**How to Access:** Subscription service for institutional investors. Governance Hub for corporate issuers. Proxy Paper and recommendations available to subscribers.

**Historical Coverage:** Glass Lewis founded 2003. Coverage data from that period forward.

**Data Format:** Web platform, PDF reports, data feeds for institutional clients.

**Cost:** Paid subscription. Pricing not publicly disclosed; varies by client type and scope.

**Known Limitations:**
- Second-largest proxy advisory firm (~28% market share); ISS is larger
- Subscription required for detailed data
- Voting recommendations may differ from ISS (creating confusion for issuers)
- Annual meeting cycle creates data refresh cadence
- Limited free public data

---

## 32. BoardEx (Director Network and Biographical Data)

**Full Name:** BoardEx (part of LSEG/Refinitiv)

**URL:** https://boardex.com/ (commercial) and https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/boardex/ (academic via WRDS)

**Data Contents:**
- Profiles of 1.7 million individuals across 2.2 million organizations globally
- Data from 1999-present covering 20,000+ companies
- Biographical data: age, gender, positions held (current, past, future), educational qualifications, compensation, stock holdings
- Professional network mapping (board interlocks, shared connections)
- Committee roles and corporate activities (M&A transactions)
- 350+ human researchers; 2,500 new profiles and 27,000 updates weekly
- Updates within 24 hours of disclosure

**How to Access:** Commercial subscription via BoardEx/LSEG. Academic access via WRDS.

**Historical Coverage:** 1999-present.

**Data Format:** Structured relational database. Available via web platform, API, and WRDS.

**Cost:** Commercial subscription (pricing not publicly disclosed; enterprise-level). Academic access through WRDS institutional subscription.

**Known Limitations:**
- Expensive commercial subscription
- Data quality depends on public disclosure (gaps for private companies)
- Network analysis may not capture informal relationships
- Historical data less complete for earlier years
- International coverage varies by region
- Academic vs. commercial versions may differ in scope

---

## 33. Equilar Executive Compensation and Board Data

**Full Name:** Equilar Inc. -- Executive Compensation and Board Intelligence

**URL:** https://www.equilar.com/

**Data Contents:**
- Executive compensation benchmarking for Russell 3000 NEOs and Section 16 officers
- Board compensation data: annual retainers, meeting fees, equity awards, committee pay
- Director and executive biographical data
- Pay-for-performance analysis
- Peer group comparison tools
- SEC filing search and analysis
- Equilar Top 50 CEO compensation survey
- Board recruiting intelligence

**How to Access:** Commercial subscription via Equilar platform. Also available through FactSet integration. Equilar Institute publications freely available.

**Historical Coverage:** Equilar has tracked compensation data for 20+ years. Coverage of Russell 3000+.

**Data Format:** Web platform, data feeds via FactSet, API. PDF publications.

**Cost:** Commercial subscription. Pricing not publicly disclosed. Enterprise clients include 70% of Fortune 500.

**Known Limitations:**
- Subscription required for detailed data
- Focus on publicly traded companies (limited private company data)
- Compensation data depends on SEC proxy filing quality
- Data may lag proxy filing dates
- Some historical data may have gaps

---

## 34. GMI Ratings (now part of MSCI ESG Research)

**Full Name:** GMI Ratings (formerly GovernanceMetrics International / The Corporate Library / Audit Integrity), acquired by MSCI in 2014

**URL:** https://www.msci.com/data-and-analytics/sustainability-solutions/esg-ratings

**Data Contents:**
- Corporate governance research and ratings on 6,000+ companies worldwide
- 150 ESG KeyMetrics for assessing sustainable investment value
- Accounting and Governance Risk (AGR) ratings on 20,000+ public companies
- Governance themes: board composition, executive compensation, shareholder rights, audit practices
- Historical annual data captures for each proxy year beginning in 2001
- Now integrated into MSCI ESG Ratings time series (from January 1, 2007)

**How to Access:** Through MSCI ESG Research platform. Legacy GMI Ratings historical data may be available through MSCI.

**Historical Coverage:** GMI Ratings data from 2001. MSCI ESG Ratings time series from 2007.

**Data Format:** Structured data via MSCI platform and data feeds.

**Cost:** MSCI ESG subscription required. Pricing not publicly disclosed.

**Known Limitations:**
- Legacy GMI Ratings methodology differs from current MSCI ESG methodology
- Historical data continuity issues due to methodology changes and acquisition
- May be difficult to obtain pre-2014 GMI data separately
- Integrated into broader MSCI ESG product (cannot access governance-only data separately in some cases)

---

## 35. MSCI ESG Ratings

**Full Name:** MSCI ESG Ratings (MSCI ESG Research LLC)

**URL:** https://www.msci.com/data-and-analytics/sustainability-solutions/esg-ratings

**Data Contents:**
- Industry-relative letter ratings from AAA (leader) to CCC (laggard)
- Coverage of thousands of companies globally
- Governance pillar includes: Board (structure, independence, diversity), Pay (compensation alignment), Ownership & Control (shareholder rights), Accounting (financial reporting quality)
- 35 Key Issues across E, S, and G pillars
- Key Issue Scores (0-10 scale)
- Daily monitoring of media and governance events
- MSCI Governance-Quality Index methodology

**How to Access:** MSCI ESG platform, DataDesk, data feeds, API. Free ESG Rating search tool for basic company ratings.

**Historical Coverage:** ESG Ratings time series from January 2007. Ongoing monitoring.

**Data Format:** Structured data via platform/API/feed.

**Cost:** Subscription required for detailed data. Basic rating lookup free.

**Known Limitations:**
- Methodology changes reduce historical comparability
- Industry-relative scoring means absolute governance quality is obscured
- Lag between governance events and rating updates
- Coverage gaps for smaller/emerging market companies
- Cost barrier for full data access

---

## 36. Sustainalytics ESG Risk Ratings

**Full Name:** Sustainalytics ESG Risk Ratings (a Morningstar company)

**URL:** https://www.sustainalytics.com/esg-data

**Data Contents:**
- ESG Risk Rating: overall risk score assigned to five categories (negligible, low, medium, high, severe)
- Corporate Governance as baseline material issue regardless of business model
- Coverage: 16,300+ analyst-based ratings (public equity, fixed-income, private companies)
- Material ESG Issues, Stakeholder Governance, Systemic and Idiosyncratic Issues
- Controversy tracking and incident monitoring
- Used by 1,100+ institutional investors globally

**How to Access:** Global Access platform, datafeeds, API, third-party distribution. Also available through WRDS for academic research.

**Historical Coverage:** Sustainalytics has provided ESG research for 30+ years.

**Data Format:** Structured data via platform, API, and feeds.

**Cost:** Subscription required. Pricing not publicly disclosed.

**Known Limitations:**
- ESG Risk Rating methodology evolves (v3.1 as of 2024)
- Governance is one component of broader ESG score
- Controversy monitoring may have lag
- Analyst-based ratings introduce subjective judgment
- Private company coverage more limited than public

---

## 37. Bloomberg ESG Data

**Full Name:** Bloomberg ESG Data and Scores (via Bloomberg Terminal and Enterprise Data)

**URL:** https://www.bloomberg.com/professional/products/data/enterprise-catalog/sustainable-finance/

**Data Contents:**
- Proprietary Bloomberg ESG Scores for 15,500+ companies
- 330+ ESG data fields
- 12 years of annual ESG data for ~13,000 companies
- Daily granular governance data for ~4,500 companies (back to 2013)
- Board Composition scores: diversity, tenure, overboarding, independence
- MSCI ESG data also available on Bloomberg Terminal
- 700+ ESG measures processed by 700+ content research analysts
- Sources: annual reports, sustainability reports, AGM results, press releases, policy documents

**How to Access:** Bloomberg Terminal subscription or Enterprise Data license.

**Historical Coverage:** ESG data from 2010+ (12 years). Governance-specific daily data from 2013.

**Data Format:** Terminal interface (BESG function). Enterprise data via API/feed. CSV/Excel export.

**Cost:** Bloomberg Terminal: ~$30,000/user/year. Enterprise Data license priced separately.

**Known Limitations:**
- Very expensive access requirement
- ESG methodology changes over time
- Data sourced from public disclosures (voluntary reporting may be incomplete)
- Non-reporting companies have data gaps
- Governance data granularity less than specialized providers (ISS, Glass Lewis)

---

## 38. S&P Global ESG Scores

**Full Name:** S&P Global ESG Scores (based on Corporate Sustainability Assessment / CSA)

**URL:** https://www.spglobal.com/esg/solutions/esg-data-intelligence

**Data Contents:**
- ESG Scores on 0-100 scale based on Corporate Sustainability Assessment (CSA)
- 62 industry-specific questionnaires
- ~120 questions per company with up to 1,000 data points
- 20+ years of SAM CSA data (since 2000)
- Governance category within broader ESG framework
- Third-party audited methodology (IOSCO Principles)
- S&P DJI ESG Score for index methodology

**How to Access:** S&P Global Marketplace, Capital IQ Pro, Xpressfeed, API, Cloud (Snowflake), FTP.

**Historical Coverage:** SAM data from 1999/2000. S&P Global ESG Scores launched 2020.

**Data Format:** Structured data via multiple delivery channels.

**Cost:** Subscription required. Pricing varies by platform and data scope.

**Known Limitations:**
- Methodology evolution over 20+ years
- CSA-based: relies partly on company self-reporting
- Governance is one pillar of broader ESG score
- Industry-specific scoring reduces cross-industry comparability
- Coverage gaps for non-participating companies

---

## 39. The Conference Board Corporate Governance Data

**Full Name:** The Conference Board -- Corporate Governance & Sustainability Center

**URL:** https://www.conference-board.org/north-america/corporate-governance

**Data Contents:**
- Board Composition and Practices Benchmarking Tool (custom peer group analysis)
- Shareholder voting data and analysis
- CEO succession data
- Executive and director compensation data
- Environmental, social & human capital practices
- Corporate Governance Handbook: legal standards and board practices
- Activist surveillance tools

**How to Access:** Conference Board membership required for full access. Some publications available for purchase. Benchmarking Tool for members.

**Historical Coverage:** Conference Board founded 1916. Corporate governance data for recent decades.

**Data Format:** Web-based benchmarking tool. PDF reports and publications.

**Cost:** Conference Board membership required. Membership pricing varies by organization size.

**Known Limitations:**
- Membership required for most data
- US-focused primarily
- Benchmarking tool requires peer group setup
- Data depth varies by topic area
- Not designed specifically for insurance underwriting

---

## 40. Proxy Monitor Database

**Full Name:** Proxy Monitor, Manhattan Institute

**URL:** https://www.proxymonitor.org/

**Data Contents:**
- Every shareholder proposal submitted to the 250 largest US public companies (2006-2024)
- Expanded to full S&P 500 coverage starting 2025
- Searchable by company, industry, year, proposal type, proponent, proponent category
- Exportable tabulated data: titles, industry, proponent, vote outcomes
- Full proposal text, sponsor statements, and management responses
- External links to SEC proxy statements
- Analysis of ESG shareholder activism trends

**How to Access:** Free public access via proxymonitor.org.

**Historical Coverage:** 2006-present. S&P 500 coverage from 2025.

**Data Format:** Web-based searchable database. Exportable tables.

**Cost:** Free

**Known Limitations:**
- Limited to shareholder proposals (not all proxy items)
- Coverage limited to top 250 companies (pre-2025) / S&P 500 (2025+)
- Smaller companies not included
- Manhattan Institute perspective may influence analysis framing
- Data export functionality may be limited

---

## 41. CEO Turnover Databases

**Full Name:** Multiple academic CEO turnover databases

**URLs:**
- Gentry et al. (2021): https://www.terry.uga.edu/wp-content/uploads/2021-Gentry-et-al-Database-of-CEO-Turnover.pdf
- Peters & Wagner Forced Turnover Dataset: https://www.florianpeters.org/data/
- US CEO Turnover Dataset (1992-2020): https://data.mendeley.com/datasets/9mh4dg4rfn/1

**Data Contents:**
- **Gentry et al.**: Open-source dataset of CEO departure reasons in S&P 1500 firms (2000-2018). Eight classifications for turnover type, narrative descriptions, links to sources.
- **Peters & Wagner**: Forced CEO turnovers in ExecuComp universe (1993-2020). 1,438 forced turnovers with announcement dates.
- **Mendeley Dataset**: CEO turnover types (1992-2020). Five categories: resignation, firing, retirement, death/illness, change of duty.
- Data collected via ProQuest news database and Google web searches

**How to Access:** Freely downloadable academic datasets.

**Historical Coverage:** Varies: 1992-2020 (broadest). S&P 1500 coverage.

**Data Format:** CSV/Excel files. Stata datasets.

**Cost:** Free

**Known Limitations:**
- Manual data collection introduces potential classification errors
- S&P 1500 focus; smaller companies excluded
- "Forced" vs. "voluntary" classification is inherently subjective
- Updates may lag; datasets may not be continuously maintained
- Need to merge with other datasets for full analysis

---

## 42. ExecuComp (Executive Compensation Database via WRDS)

**Full Name:** Compustat ExecuComp, S&P Global (via WRDS)

**URL:** https://wrds-www.wharton.upenn.edu/pages/grid-items/compustat-execucomp-basics/

**Data Contents:**
- Executive compensation data for S&P 1500 companies (2,500+ companies, active and inactive)
- Top 5 named executive officers per company
- 80+ compensation variables: salary, bonus, stock/option awards, non-equity incentive plans, pensions, other compensation
- Sub-datasets: AnnComp (summary compensation), PlanBasedAwards, OutstandingAwards, DeferredComp, Pension
- Data sourced from annual proxy statements

**How to Access:** WRDS institutional subscription. Queryable via web, SAS, Python, R, Stata.

**Historical Coverage:** S&P 1500 from 1994. Some data back to 1992.

**Data Format:** Structured data via WRDS (SAS, CSV, Stata, R formats).

**Cost:** Included in WRDS institutional subscription.

**Known Limitations:**
- S&P 1500 only (excludes smaller public and private companies)
- Data from proxy statements may have lag (120 days after fiscal year-end)
- Complex compensation structures may not be fully captured
- Stock option valuation methodology may vary
- Requires WRDS institutional access

---

## 43. Board Diversity Databases

**Full Name:** Spencer Stuart U.S. Board Index / S&P 500 Board Diversity Data

**URL:** https://www.spencerstuart.com/research-and-insight/us-board-index

**Data Contents:**
- Annual U.S. Spencer Stuart Board Index (39th edition in 2024)
- S&P 500 board composition data: gender, race/ethnicity, LGBTQ+ self-identification
- New director appointment statistics: 46% female in 2024 (down from 56% in 2023)
- Underrepresented minority statistics: 7% of independent board chairs
- Director age, tenure, independence, and skills data
- International Board Indexes (UK, other markets)
- S&P 500 New Director and Diversity Snapshot

**How to Access:** Free PDF downloads from Spencer Stuart website.

**Historical Coverage:** Published annually for 39+ years. Longitudinal trends available.

**Data Format:** PDF reports with data tables and charts.

**Cost:** Free

**Known Limitations:**
- S&P 500 focus; smaller companies not covered
- Self-reported diversity data (companies opt-in to disclosure)
- Annual snapshot (no real-time updates)
- PDF format requires manual data extraction
- Diversity definitions and categories may evolve over time

---

## 44. Audit Committee Composition Data

**Full Name:** Multiple sources -- ISS, BoardEx, ExecuComp, Audit Analytics

**URLs:** Various (see entries #30, #32, #42, #55)

**Data Contents:**
- Audit committee membership and chair identification
- Committee member qualifications (financial expertise, accounting background)
- Committee meeting frequency
- Independence standards compliance
- Audit committee oversight indicators (restatements, material weaknesses)
- Available through ISS Governance QualityScore, BoardEx, and Audit Analytics

**How to Access:** Through respective platform subscriptions (ISS, BoardEx via WRDS, Audit Analytics).

**Historical Coverage:** Varies by source. Sarbanes-Oxley Act (2002) significantly expanded audit committee data requirements.

**Data Format:** Structured data within larger governance datasets.

**Cost:** Included in respective platform subscriptions.

**Known Limitations:**
- Data scattered across multiple sources requiring integration
- Committee quality metrics are proxy-based (not direct performance measures)
- Small committees may not have enough variation for statistical analysis
- Historical data pre-SOX is limited

---

## 45. Related Party Transaction Data

**Full Name:** SEC Filing Data on Related Party Transactions / Academic Datasets

**URLs:**
- SEC EDGAR (10-K filings, proxy statements): https://www.sec.gov/cgi-bin/browse-edgar
- Audit Analytics: https://www.ideagen.com/solutions/compliance/audit-intelligence

**Data Contents:**
- Material related party transaction disclosures from SEC filings (10-K, proxy statements)
- Transaction nature, terms, dollar amounts, relationship descriptions
- NYSE Section 314.00 compliance data
- Audit Analytics tracks related party transaction disclosures
- Academic datasets from individual researchers (various)

**How to Access:** SEC EDGAR (free). Audit Analytics (subscription). Academic datasets (per author).

**Historical Coverage:** SEC disclosure requirements strengthened post-SOX (2002). Data available from that period forward.

**Data Format:** Unstructured text within SEC filings (requires NLP/parsing). Structured data via Audit Analytics.

**Cost:** SEC EDGAR: free. Audit Analytics: subscription. Academic datasets: varies.

**Known Limitations:**
- Related party transactions are disclosed in narrative form (difficult to parse systematically)
- No standardized database exists
- Disclosure quality varies significantly across companies
- Materiality thresholds mean smaller transactions are not disclosed
- International coverage extremely limited
- NLP/text mining required for systematic extraction from filings

---

# SECTION 4: FINANCIAL AND MARKET DATA

---

## 46. CRSP (Center for Research in Security Prices)

**Full Name:** Center for Research in Security Prices, LLC (CRSP), University of Chicago Booth School of Business

**URL:** https://www.crsp.org/ and via WRDS: https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/center-for-research-in-security-prices-crsp/

**Data Contents:**
- Most comprehensive collection of security price, return, and volume data for NYSE, AMEX, NASDAQ
- Identity information: name histories, CUSIPs, share classes, tickers, SIC codes
- Price histories and trading volumes
- Delisting information
- Distribution history (dividends, stock splits, special distributions)
- Shares outstanding
- Stock indices, beta-based and cap-based portfolios
- Treasury bond and risk-free rates
- Permanent identifiers (PERMNO for stock, PERMCO for company)

**How to Access:** WRDS institutional subscription. Also available via LSEG/Refinitiv. Academic institutions primarily.

**Historical Coverage:** 1925-present (daily and monthly). Updated quarterly and annually.

**Data Format:** Structured data via WRDS (SAS, CSV, Stata, R, Python).

**Cost:** Institutional subscription via WRDS or direct CRSP license.

**Known Limitations:**
- US exchanges only (no international coverage)
- Requires institutional affiliation
- Historical data quality varies for earliest periods
- Delisting returns may have survivorship bias issues in older data
- OTC/pink sheet securities not included

---

## 47. Compustat (Financial Statement Data)

**Full Name:** S&P Global Compustat North America / Compustat Global

**URL:** https://wrds-www.wharton.upenn.edu/pages/grid-items/compustat-annual-updates-fundamentals-annual-demo/ and https://www.marketplace.spglobal.com/

**Data Contents:**
- Standardized annual and quarterly financial statement data
- Income Statement, Balance Sheet, Statement of Cash Flows
- North America: 50,000+ active and inactive publicly held companies
- Global: 65,000+ non-US/Canadian companies
- Point-in-time snapshots from 1987
- Industry classifications, market data, supplemental items

**How to Access:** WRDS institutional subscription. S&P Global Marketplace. S&P Capital IQ Pro.

**Historical Coverage:** As far back as 1950 (North America). Point-in-time from 1987.

**Data Format:** Structured data via WRDS/S&P platforms.

**Cost:** Institutional subscription (WRDS or S&P Global).

**Known Limitations:**
- Standardization process may lose company-specific nuance
- Historical data availability varies by item
- Quarterly data less complete than annual
- Requires understanding of accounting standards for proper use
- Mergers/acquisitions create data continuity challenges

---

## 48. S&P Capital IQ Pro

**Full Name:** S&P Capital IQ Pro, S&P Global Market Intelligence

**URL:** https://www.spglobal.com/market-intelligence/en/solutions/products/sp-capital-iq-pro

**Data Contents:**
- 109,000+ public companies (49,000 active with current financials)
- 58M+ private companies (1.3M+ early-stage)
- 140+ estimates metrics for 19,800+ companies from 110+ countries
- 19.4M+ government, supranational, agency, and corporate securities
- 115,000+ loan facilities
- 4.5M+ global professionals
- Credit ratings, financial models, screening tools
- AI-powered ChatIQ for multi-document analysis
- M&A transactions, key developments, ownership data

**How to Access:** S&P Global subscription. Desktop platform, Excel plug-in, API.

**Historical Coverage:** Decades of financial data. Global coverage.

**Data Format:** Web platform, Excel, API, data feeds.

**Cost:** Enterprise subscription. Pricing not publicly disclosed (estimated $20,000-$40,000+/user/year).

**Known Limitations:**
- Very expensive
- Complex platform with learning curve
- Data quality for private companies varies significantly
- International financial data may have standardization issues
- Requires S&P relationship for access

---

## 49. Bloomberg Terminal

**Full Name:** Bloomberg Terminal (Bloomberg L.P.)

**URL:** https://www.bloomberg.com/professional/products/bloomberg-terminal/

**Data Contents:**
- Real-time and historical market data across all asset classes
- 200+ billion pieces of financial data daily
- 13M+ instruments, 6.5M+ entities
- Reference data, pricing, regulatory, and alternative data
- ESG data (see entry #37)
- News and research
- Analytics and risk management tools
- Court filing and litigation data
- Credit ratings from all major agencies
- Company financials, estimates, corporate actions

**How to Access:** Bloomberg Terminal subscription. Enterprise data via API/cloud.

**Historical Coverage:** Decades of financial data. Real-time updates.

**Data Format:** Proprietary terminal interface. API for enterprise data. Excel plug-in.

**Cost:** ~$30,000/user/year for Terminal. Enterprise pricing varies.

**Known Limitations:**
- Very expensive
- Proprietary interface (vendor lock-in)
- D&O-specific analytics limited (must be built from component data)
- Requires significant expertise to use effectively
- Data redistribution restrictions

---

## 50. Refinitiv/LSEG

**Full Name:** Refinitiv (now LSEG Data & Analytics), London Stock Exchange Group

**URL:** https://www.lseg.com/en/data-analytics

**Data Contents:**
- ESG data covering 15,000+ companies across 76 countries (88% of global market cap)
- 860+ ESG measures processed by 700+ analysts
- ESG scores with history back to 2002
- 10 ESG themes including governance categories
- Diversity and Inclusion Ratings
- Financial data, pricing, reference data
- News and events data
- Eikon/Workspace platform for analysis

**How to Access:** LSEG Data Platform subscription. Eikon/Workspace terminal. Data feeds and API.

**Historical Coverage:** ESG data from 2002. Financial data spans decades.

**Data Format:** Multiple platforms: terminal, API, cloud, feeds.

**Cost:** Subscription required. Pricing not publicly disclosed.

**Known Limitations:**
- ESG data based on public disclosures (voluntary reporting gaps)
- Methodology changes over time
- Integration complexity post-Refinitiv/LSEG merger
- Competing/overlapping products create confusion
- Cost comparable to Bloomberg for enterprise access

---

## 51. FRED (Federal Reserve Economic Data)

**Full Name:** Federal Reserve Economic Data, Federal Reserve Bank of St. Louis

**URL:** https://fred.stlouisfed.org/

**Data Contents:**
- 816,000+ economic time series from multiple sources
- Macroeconomic indicators: GDP, employment, inflation, interest rates, exchange rates
- Insurance-tagged series: 17,029 series
- Banking, monetary, trade, consumer, and producer data
- FRED-MD and FRED-QD: large macroeconomic databases (300+ series)
- Data from Bureau of Labor Statistics, Census, Fed, and other agencies

**How to Access:** Free public access. API available (FRED API). Excel add-in available.

**Historical Coverage:** Varies by series; many go back decades. Some from 1920s.

**Data Format:** CSV, Excel, API (JSON/XML). Interactive charts.

**Cost:** Free

**Known Limitations:**
- Macroeconomic data, not D&O-specific
- Requires hypothesis about which macro variables drive D&O losses
- Insurance-specific series may be aggregate (not D&O line-specific)
- Some series discontinued or revised
- Lag in economic data reporting

---

## 52. Short Interest Data (FINRA, Exchanges)

**Full Name:** FINRA Equity Short Interest Data

**URL:** https://www.finra.org/finra-data/browse-catalog/equity-short-interest/data

**Data Contents:**
- Short interest positions in all equity securities reported twice monthly
- OTC and exchange-listed securities (comprehensive from June 2021)
- Data fields: symbol, security name, market, current short position, previous short position, change, average daily volume, days to cover
- Settlement date information
- Prior to June 2021: OTC securities only

**How to Access:** Free via FINRA website. API available: https://api.finra.org. Downloadable pipe-delimited text files.

**Historical Coverage:** OTC data historical; comprehensive exchange + OTC from June 2021.

**Data Format:** CSV/JSON via API. Pipe-delimited text files for bulk download.

**Cost:** Free

**Known Limitations:**
- Reported twice monthly (not daily)
- Pre-June 2021 data limited to OTC securities
- Does not show individual short positions (aggregated by security)
- Short interest is reported, not real-time
- Does not directly indicate fraud (correlation, not causation)
- Synthetic shorts via options not captured

---

## 53. Options Market Data

**Full Name:** CBOE Options Market Data / Unusual Options Activity

**URL:** https://www.cboe.com/market_data_services/us/options/

**Data Contents:**
- Options trading data from four CBOE exchanges
- Volume, open interest, implied volatility
- Unusual options activity alerts (high volume-to-open interest ratios)
- Real-time and historical market data feeds
- Risk management tools for unusual activity detection
- VIX and other volatility indices

**How to Access:** CBOE Market Data Services subscription. Real-time alerts via Cboe platform. Third-party data providers (Barchart, etc.) offer unusual activity screens.

**Historical Coverage:** CBOE data from 1973 (options exchange founding). Extensive historical archives.

**Data Format:** Proprietary data feeds. Third-party platforms offer various formats.

**Cost:** CBOE data fees vary by product and use case. Third-party aggregators have separate pricing.

**Known Limitations:**
- Options data requires sophisticated interpretation
- Unusual activity may reflect legitimate hedging, not insider knowledge
- False positive rate for fraud signals is high
- Requires real-time processing for maximum utility
- Historical analysis challenging due to data volume
- Not a direct D&O underwriting input (experimental/alternative signal)

---

## 54. Credit Rating Agency Data (Moody's, S&P, Fitch)

**Full Name:** Moody's Investors Service / S&P Global Ratings / Fitch Ratings

**URLs:**
- Moody's: https://www.moodys.com/web/en/us/datahub/data-sets.html
- S&P: https://www.spglobal.com/ratings/
- Fitch: https://www.fitchratings.com/

**Data Contents:**
- **Moody's**: Default and Recovery Database (DRD), Default Risk Service (DRS), Risk Data Suite (RDS), Market Implied Ratings (MIR)
- **S&P**: Credit ratings, CreditPro, Probability of Default models
- **Fitch**: Ratings, default studies, sector analysis
- All three: Corporate issuer ratings, rating transitions, default rates, recovery rates, industry outlook reports
- Daily probability of default estimates

**How to Access:** Commercial subscriptions for detailed data. Some rating opinions freely available on agency websites.

**Historical Coverage:** Rating agencies have operated for 100+ years. Detailed default databases span decades.

**Data Format:** Web platforms, data feeds, API (varies by provider).

**Cost:** Significant commercial subscription costs. Basic rating lookup often free. Full data products priced for enterprise use.

**Known Limitations:**
- Ratings are opinions, not guarantees (rating agencies faced criticism post-2008)
- Ratings may lag fundamental credit deterioration
- Different agencies may rate same entity differently (split ratings)
- Historical default data may have survivorship bias
- Expensive for full data access
- D&O insurance pricing is related but not identical to credit risk

---

## 55. Audit Analytics

**Full Name:** Ideagen Audit Analytics (formerly Audit Analytics, Inc.)

**URL:** https://www.ideagen.com/solutions/compliance/audit-intelligence

**Data Contents:**
- 70+ integrated databases covering:
  - Financial restatements (type, severity, impact)
  - Auditor changes (timing, reason, successor)
  - SOX Section 404 internal control weaknesses
  - SEC comment letters
  - Enforcement actions
  - Audit fees and non-audit fees
  - Late filers
  - Going concern opinions
- 20 years of audit history since 2000
- US, UK, Canadian, and European market coverage
- Real-time updates on auditor changes
- 450+ institutional users

**How to Access:** Commercial subscription. Also available through WRDS for academic institutions.

**Historical Coverage:** 2000-present (comprehensive). Some data earlier.

**Data Format:** Structured database via web platform and WRDS. API access available.

**Cost:** Commercial subscription (pricing not publicly disclosed). Academic access via WRDS.

**Known Limitations:**
- Subscription required
- US-centric (international coverage more recent and less deep)
- Classification of restatement severity requires judgment
- Not all audit-related events captured in real-time
- Integration with other datasets requires mapping (CIK, ticker, GVKEY linkages)

---

# SECTION 5: NEWS, MEDIA, AND ALTERNATIVE DATA

---

## 56. GDELT Project

**Full Name:** The GDELT Project (Global Database of Events, Language, and Tone)

**URL:** https://www.gdeltproject.org/

**Data Contents:**
- Global catalog of human societal-scale behavior and beliefs
- Events database: monitors news from virtually every country in 65+ translated languages
- GDELT 2.0: updates every 15 minutes
- Event records: actors, action types, locations, dates, tone/sentiment
- Global Knowledge Graph: entities, themes, organizations, counts, tone
- Television news monitoring (Internet Archive's Television News Archive)

**How to Access:** Free. Raw data downloadable as CSV files. Available on Google BigQuery. Python package available (gdelt on PyPI).

**Historical Coverage:** Events data from 1979 (GDELT 1.0). GDELT 2.0 from 2015 with continuous updates.

**Data Format:** Tab-separated CSV files. Google BigQuery tables.

**Cost:** Free

**Known Limitations:**
- Not D&O-specific; requires filtering for relevant events
- Event coding may be noisy (automated extraction from news text)
- Tone/sentiment measures are crude
- English-language bias in coverage despite translation
- Massive data volume requires significant processing infrastructure
- No direct corporate governance coding

---

## 57. Event Registry (NewsAPI.ai)

**Full Name:** Event Registry / NewsAPI.ai

**URL:** https://eventregistry.org/ and https://newsapi.ai/

**Data Contents:**
- 150,000+ news sources globally in 60+ languages
- AI-enriched content: entities, categories, sentiment, event clustering
- Event-level data: title, summary, location, date, related concepts, articles
- Real-time content with minimal publication delay
- REST API, Python SDK, Node.js SDK

**How to Access:** Free tier: 2,000 tokens, last 30 days of content, non-commercial use only. Paid plans for commercial use and full archive.

**Historical Coverage:** Archive back to 2014. Ongoing real-time updates.

**Data Format:** JSON via REST API.

**Cost:** Free tier available. Paid plans: variable pricing (extra tokens at $0.015 each). Enterprise pricing available.

**Known Limitations:**
- Free tier limited (30 days, non-commercial)
- Token-based pricing can become expensive at scale
- Entity recognition accuracy varies
- Sentiment analysis is general-purpose (not financial/legal-specific)
- May miss paywalled content
- Not D&O-specific; requires custom filtering

---

## 58. NewsAPI

**Full Name:** NewsAPI.org

**URL:** https://newsapi.org/

**Data Contents:**
- REST API returning JSON search results for current and historic news articles
- 150,000+ worldwide sources
- 14 languages, 55 countries
- Search by keyword, source, domain, date range
- Top headlines and everything endpoints

**How to Access:** Free for development. Paid plans for production/commercial use.

**Historical Coverage:** Article archive varies (typically weeks to months for free tier).

**Data Format:** JSON via REST API.

**Cost:** Free (development, 100 requests/day). Paid plans starting at $449/month for production use.

**Known Limitations:**
- Free tier is severely limited (100 requests/day, 1-month history)
- Articles from paywalled sources may only provide headlines
- No built-in financial/legal categorization
- Rate limits on all tiers
- Article text may be truncated
- Not designed for insurance/underwriting use cases

---

## 59. LexisNexis News Archives

**Full Name:** Nexis / LexisNexis (RELX Group)

**URL:** https://www.lexisnexis.com/en-us/products/nexis.page

**Data Contents:**
- 45+ years of news archives from 36,000+ licensed sources (45,000 total)
- CourtLink: federal and state court dockets and documents
- Company profiles and corporate intelligence
- Legal research databases
- Nexis Data+: data integration platform for AI and analytics
- Public records, regulatory filings, and financial data

**How to Access:** Institutional or corporate subscription. Multiple product tiers (Nexis, Nexis+, Lexis+).

**Historical Coverage:** 45+ years of news archives.

**Data Format:** Web platform. API available (Nexis Data+). Various export formats.

**Cost:** Starting at ~$171/month for individual. Multi-user and enterprise pricing varies significantly (custom quotes).

**Known Limitations:**
- Expensive for comprehensive access
- Complex product lineup (multiple overlapping products)
- API access (Nexis Data+) priced separately and substantially
- International coverage varies by region
- Historical archive search may have relevance issues for older content

---

## 60. Factiva (Dow Jones)

**Full Name:** Factiva, a Dow Jones product (ProQuest/Clarivate for academic distribution)

**URL:** https://about.proquest.com/en/products-services/factiva/

**Data Contents:**
- 32,000+ sources: newspapers, journals, magazines, TV/radio transcripts, photos
- 200 countries, 33 languages
- 600+ continuously updated newswires
- Key Developments tracking: M&A, bankruptcies, management changes, regulatory actions
- Company profiles and industry reports
- Intelligent Indexing for content categorization

**How to Access:** Academic access via ProQuest/institutional library. Corporate subscription via Dow Jones.

**Historical Coverage:** Decades of news archives. Some sources back to 1980s.

**Data Format:** Web platform. Feeds available for enterprise.

**Cost:** Not publicly disclosed. Academic access through library subscriptions. Corporate pricing varies.

**Known Limitations:**
- Expensive for corporate access
- Academic access may have content restrictions
- No public API for independent developers
- Key Developments categories may not precisely map to D&O risk factors
- International coverage varies by source availability

---

## 61. SEC Whistleblower Tip Data

**Full Name:** SEC Office of the Whistleblower -- Annual Reports and Tip Statistics

**URL:** https://www.sec.gov/whistleblower (Annual reports at sec.gov/files/)

**Data Contents:**
- Annual whistleblower tip volume (24,980 tips in FY2024; 18,354 in FY2023)
- Tip categories: Manipulation (37%), Offering Fraud (21%), ICO/Crypto (8%), Corporate Disclosures/Financials (8%)
- Award amounts ($255M in FY2024; $2.2 billion cumulative to 444 individuals)
- Geographic distribution of tips (domestic and international)
- Enforcement action outcomes
- Trend analysis year-over-year

**How to Access:** Free annual reports published on SEC website. Summary statistics publicly available.

**Historical Coverage:** Whistleblower program since 2011 (Dodd-Frank). Annual reports from FY2012.

**Data Format:** PDF annual reports. Limited structured data.

**Cost:** Free

**Known Limitations:**
- Aggregate statistics only (individual tip details confidential)
- Not company-specific (cannot link tips to specific firms)
- Significant data anomalies (e.g., 14,000+ tips from 2 individuals in FY2024)
- Tip volume does not equal fraud incidence
- Lag between tips and enforcement outcomes
- Limited use for predictive underwriting (aggregate trends only)

---

## 62. Glassdoor Employee Reviews

**Full Name:** Glassdoor (Recruit Holdings)

**URL:** https://www.glassdoor.com/

**Data Contents:**
- Employee reviews with overall ratings and category ratings (Culture & Values, Senior Leadership, Compensation, Career Opportunities, Work-Life Balance)
- CEO approval ratings
- Salary data
- Company ratings and rankings
- MIT/Glassdoor Culture 500 dataset: measures culture on agility, collaboration, customer focus, diversity, execution, innovation, integrity, respect, performance rewards
- Validated as correlated with financial performance (257,454 reviews of 425 organizations)

**How to Access:** Free browsing on Glassdoor website. API historically available but increasingly restricted. Third-party data providers (Bright Data, Coresignal) offer datasets. MIT/Glassdoor Culture 500 available for academic research.

**Historical Coverage:** Glassdoor launched 2007/2008. Reviews accumulate over time.

**Data Format:** Web (structured HTML). Third-party datasets in CSV/JSON. Culture 500 as academic dataset.

**Cost:** Free to browse. Third-party datasets: ~$250/100K records (Bright Data). API access may require Glassdoor partnership.

**Known Limitations:**
- Self-selection bias (disgruntled employees more likely to review)
- Fake review risk
- Company manipulation (solicited positive reviews)
- API access increasingly restricted
- Third-party scraping may violate Terms of Service
- Uneven coverage across companies and industries
- Reviews are subjective and may not correlate consistently with D&O risk

---

## 63. LinkedIn Data (Executive Movement Patterns)

**Full Name:** LinkedIn (Microsoft)

**URL:** https://www.linkedin.com/

**Data Contents:**
- Professional profiles for 1 billion+ members globally
- Executive biographical data and career histories
- Company employee counts and growth trends
- Job postings and hiring patterns
- Leadership transitions and succession events
- Network connections and professional relationships

**How to Access:** LinkedIn Official APIs (heavily restricted; requires partnership). Third-party data providers (Coresignal, Revelio Labs, People Data Labs). LinkedIn Economic Graph for aggregate insights.

**Historical Coverage:** LinkedIn founded 2003. Profile data accumulates over time.

**Data Format:** API (JSON). Third-party datasets various formats.

**Cost:** LinkedIn API: free for approved partners (approval difficult). Third-party data: varies significantly. LinkedIn Talent Insights: enterprise pricing.

**Known Limitations:**
- Official API access is extremely restricted
- Scraping violates Terms of Service (hiQ Labs v. LinkedIn litigation notwithstanding)
- Self-reported data (accuracy varies)
- Executive-level profiles may be sparse or out of date
- Privacy concerns and regulatory restrictions (GDPR, CCPA)
- Difficult to use systematically for underwriting at scale

---

## 64. Twitter/X Sentiment Data

**Full Name:** X (formerly Twitter) Financial Sentiment Data

**URLs:**
- X Developer Platform: https://developer.x.com/
- Nasdaq Social Sentiment: https://business.nasdaq.com/intel/GIS/Twitter-Sentiment.html
- EODHD Tweets Sentiment API: https://eodhd.com/

**Data Contents:**
- Nasdaq Analytics Hub: daily sentiment indicators from X for 1,526 tickers
- Tweet volume, sentiment polarity, engagement metrics
- Aggregated financial sentiment by ticker
- Hugging Face financial news sentiment datasets
- Real-time social media monitoring

**How to Access:** X API (Basic: free with limits; Pro: $5,000/month; Enterprise: varies). Third-party APIs (Nasdaq, EODHD). Hugging Face datasets for research.

**Historical Coverage:** X/Twitter from 2006. Financial sentiment APIs vary.

**Data Format:** JSON via API. Datasets in CSV/Parquet.

**Cost:** X API Basic: free (limited). X API Pro: $5,000/month. Third-party services: varies.

**Known Limitations:**
- X API costs increased dramatically since Elon Musk acquisition
- Bot activity and manipulation create noise
- Sentiment analysis accuracy for financial text is imperfect
- Correlation with D&O risk is speculative/unproven
- Real-time data requires continuous processing infrastructure
- Historical data access expensive/difficult
- Privacy and data usage restrictions

---

## 65. Reddit (WallStreetBets and Investing Forums)

**Full Name:** Reddit r/WallStreetBets, r/investing, and related subreddits

**URL:** https://www.reddit.com/r/wallstreetbets/

**Data Contents:**
- User-generated investment discussions, stock picks, and market commentary
- Historical posts datasets available on Kaggle and academic archives
- SwaggyStocks: sentiment signals from WSB and other sources
- Research shows WSB signals can outperform S&P 500 in some periods
- Potential fraud allegation signals (companies discussed negatively)

**How to Access:** Reddit API (rate-limited). Kaggle datasets (historical WSB posts). Third-party sentiment aggregators (SwaggyStocks, SentryDock).

**Historical Coverage:** r/WallStreetBets created 2012. Significant data from 2018 onward.

**Data Format:** JSON via API. CSV/Parquet for historical datasets.

**Cost:** Reddit API: free with rate limits. Third-party tools: varies.

**Known Limitations:**
- Extremely noisy data
- Dominated by retail investor sentiment (not institutional)
- Manipulation and pump-and-dump risk
- Limited predictive value for D&O liability specifically
- Requires significant NLP processing
- Community culture (memes, irony) makes sentiment analysis difficult
- Regulatory scrutiny of social media market manipulation

---

## 66. Seeking Alpha Articles and Comments

**Full Name:** Seeking Alpha

**URL:** https://seekingalpha.com/

**Data Contents:**
- Crowdsourced investment analysis articles (100,000+ since 2004)
- Author ratings and track records
- Reader comments with sentiment
- Bull/bear cases and price targets
- Earnings analysis and transcripts
- Research shows articles predict future stock returns (1 month to 3 years)
- Research shows articles predict earnings surprises

**How to Access:** Some articles free on seekingalpha.com. Premium subscription for full access. API available via RapidAPI. Scrapers available (Apify).

**Historical Coverage:** Articles from 2004/2005 onward.

**Data Format:** Web content. API returns JSON. Historical datasets on Kaggle.

**Cost:** Free (limited articles). Premium: ~$239/year. API: varies by provider.

**Known Limitations:**
- Contributor quality varies enormously
- Potential conflicts of interest (authors may hold positions)
- Behind paywall for premium content
- Scraping may violate Terms of Service
- Comment quality is highly variable
- Not designed for D&O risk assessment

---

## 67. Short Seller Research Reports

**Full Name:** Activist Short Seller Reports (Hindenburg Research, Muddy Waters, Citron Research, Viceroy Research, Gotham City Research, et al.)

**URLs:**
- Hindenburg Research: https://hindenburgresearch.com/
- Muddy Waters Research: https://www.muddywatersresearch.com/
- Citron Research: https://citronresearch.com/
- Breakout Point (tracker): https://breakoutpoint.com/

**Data Contents:**
- Detailed short thesis reports alleging fraud, misrepresentation, or overvaluation
- Due diligence findings on specific companies
- Evidence of accounting irregularities, related party transactions, governance failures
- Breakout Point tracks: 129 major short calls in 2023; 65 in H1 2024
- Historical campaign performance tracking
- Stock price reaction data

**How to Access:** Individual firm reports: free on their websites. Breakout Point: subscription service.

**Historical Coverage:** Muddy Waters from 2010. Hindenburg from 2017. Citron from 2001. Breakout Point tracks comprehensively.

**Data Format:** PDF reports from individual firms. Breakout Point offers dashboard and API access.

**Cost:** Individual reports: free. Breakout Point: paid subscription. API access available.

**Known Limitations:**
- Authors have financial interest (short positions) creating inherent bias
- Reports may contain errors or misleading claims
- Small sample size (60-130 major campaigns per year)
- Not all allegations prove true
- Regulatory scrutiny of short-and-distort tactics
- Hindenburg Research ceased operations in January 2025
- Limited structured data (reports are narrative PDFs)

---

## 68. Activist Investor Campaign Databases

**Full Name:** 13D Monitor / SharkRepellent (FactSet) / Activist Insight

**URLs:**
- 13D Monitor: https://www.13dmonitor.com/
- SharkRepellent: via FactSet platform
- Activist Insight: https://www.activistinsight.com/

**Data Contents:**
- **13D Monitor**: 13D filing alerts, proxy fight tracking, activist letters and agreements, campaign analysis
- **SharkRepellent (FactSet)**: Governance characteristics of 5,000+ US public companies, corporate bylaws, state corporation laws, 1,100+ activist situations since 2006
- **Activist Insight**: Comprehensive activist campaign data, investor profiles, campaign outcomes
- All track: campaign types, tactics, outcomes, proponent identification

**How to Access:** Subscription services. 13D Monitor: direct subscription. SharkRepellent: via FactSet platform. Activist Insight: separate subscription.

**Historical Coverage:** 13D Monitor: ongoing. SharkRepellent: since 2006. Activist Insight: comprehensive historical data.

**Data Format:** Web platforms, alerts, reports, data feeds.

**Cost:** 13D Monitor: ~$18,000/year (as of 2013; likely higher now). SharkRepellent: included in FactSet subscription. Activist Insight: enterprise pricing.

**Known Limitations:**
- Very expensive
- Coverage focuses on larger companies and well-known activists
- Campaign outcome coding may be subjective
- Real-time tracking requires constant monitoring
- Limited predictive value for D&O claims specifically
- Small-cap activist situations may be underreported

---

## 69. Congressional Stock Trading Data

**Full Name:** STOCK Act Financial Disclosure Data / Congressional Trading Trackers

**URLs:**
- House disclosures: https://disclosures-clerk.house.gov/FinancialDisclosure
- Senate disclosures: https://efdsearch.senate.gov/
- Quiver Quantitative: https://www.quiverquant.com/congresstrading/
- Capitol Trades: https://www.capitoltrades.com/

**Data Contents:**
- Financial transactions of Members of Congress (STOCK Act requirement since 2012)
- Transaction type, date, asset, amount range, filing date
- 45-day filing deadline after transaction
- Third-party platforms aggregate and analyze data:
  - Quiver Quantitative: free congressional trading tracker
  - Capitol Trades: searchable database of Congress trades
  - InsiderFinance: congress trades tracker

**How to Access:** Official disclosures: free but difficult to search systematically. Third-party platforms: free (basic) to subscription.

**Historical Coverage:** 2012-present (STOCK Act).

**Data Format:** Official: PDF/image forms (many not text-searchable, some handwritten). Third-party: structured databases, web interfaces.

**Cost:** Free (official and basic third-party).

**Known Limitations:**
- Official data is in non-machine-readable format (PDFs, some handwritten)
- Dollar amounts reported in ranges (not exact)
- 45-day filing lag (not real-time)
- Compliance is imperfect (late filings common)
- Speculative connection to D&O risk (unusual congressional trades near companies may signal regulatory knowledge)
- Third-party databases may have extraction errors
- Trades by spouses and dependents may not be fully captured

---

## 70. Patent Litigation Data

**Full Name:** Lex Machina / RPX Corporation / USPTO Data

**URLs:**
- Lex Machina: https://lexmachina.com/
- RPX: https://empower.rpxcorp.com/
- USPTO: https://www.uspto.gov/

**Data Contents:**
- **Lex Machina**: Legal analytics from 45M+ court documents across 10M+ cases. Patent litigation covering 94 federal districts, 13 appellate courts, PTAB. 8,000+ judges, 6,000+ expert witnesses. 2025 report: 22% surge in patent filings, record $4.3B in damages.
- **RPX**: Worldwide patent data, US patent assignments, secondary market transactions, USPTO image file wrappers, Standard Essential Patent declarations.
- **USPTO**: Patent grants, applications, PTAB proceedings.

**How to Access:** Lex Machina: LexisNexis IP subscription. RPX: membership or subscription. USPTO: free for raw data.

**Historical Coverage:** Lex Machina: extensive court records. RPX: comprehensive patent data. USPTO: from 1790.

**Data Format:** Web platforms, API, data feeds. USPTO: bulk data in XML/JSON.

**Cost:** Lex Machina: included in LexisNexis IP subscription. RPX: membership fees. USPTO: free.

**Known Limitations:**
- Patent litigation is one component of D&O risk (not the primary driver)
- Requires hypothesis about patent risk and D&O claims linkage
- Lex Machina requires subscription
- Patent litigation data requires legal expertise to interpret
- Not all patent disputes result in D&O claims
- Processing PTAB and court data requires significant infrastructure

---

# SECTION 6: ADDITIONAL CRITICAL DATA SOURCES

---

## 71. SEC EDGAR

**Full Name:** SEC Electronic Data Gathering, Analysis, and Retrieval (EDGAR)

**URL:** https://www.sec.gov/edgar and https://data.sec.gov/

**Data Contents:**
- All SEC filings: 10-K, 10-Q, 8-K, proxy statements (DEF 14A), 13F, 13D/13G, insider trading (Forms 3/4/5)
- XBRL-tagged financial data (since 2009)
- Full-text search across filings
- RESTful APIs for submissions and XBRL data
- Company and filing metadata
- 18M+ filings for 8,000+ publicly listed companies since 1993

**How to Access:** Free. RESTful API (no API key needed). Rate limit: 10 requests/second.

**Historical Coverage:** Electronic filings from 1993/1996. Some earlier filings available.

**Data Format:** HTML, XBRL, XML, JSON (via API). Raw filing text.

**Cost:** Free

**Known Limitations:**
- Raw data requires significant parsing and processing
- XBRL coverage begins 2009 (earlier filings lack structured data)
- Filing quality varies (some filings are scanned images)
- Rate limits restrict bulk downloading speed
- D&O-relevant information (risk factors, legal proceedings, governance) is embedded in unstructured text
- Requires NLP for systematic extraction of D&O risk signals

---

## 72. PACER (Federal Court Records)

**Full Name:** Public Access to Court Electronic Records (PACER)

**URL:** https://pacer.uscourts.gov/

**Data Contents:**
- Federal court records: district courts, courts of appeals, bankruptcy courts
- Case dockets, filings, orders, opinions
- Party and attorney information
- Securities class action complaint documents
- Settlement orders and consent decrees

**How to Access:** User registration required. Per-page fee ($0.10/page, $3/document cap). Quarterly fee waiver if under $30.

**Historical Coverage:** Electronic records vary by court; generally from mid-2000s onward. Some courts have earlier records.

**Data Format:** Web-based search. PDF documents.

**Cost:** $0.10/page (most users under $30/quarter free). $125M class action settlement in 2024 found fees excessive.

**Known Limitations:**
- Per-page fees can add up for large-scale research
- Search functionality is basic and court-specific
- Not designed for systematic data extraction
- PDF documents require parsing for structured analysis
- Court-by-court variation in filing practices and data quality
- No API for bulk access
- RECAP (Free Law Project) provides some PACER documents for free

---

## 73. The D&O Diary Blog

**Full Name:** The D&O Diary by Kevin M. LaCroix

**URL:** https://www.dandodiary.com/

**Data Contents:**
- Industry-leading blog on D&O liability, securities litigation, and insurance
- Filing tracking, settlement analysis, market commentary
- Guest posts from industry experts on emerging risks
- Annual "Top Ten Stories in D&O" retrospective
- Coverage of AI, ESG, cyber, regulatory, and other emerging D&O risk topics
- Referenced by New York Times ("influential") and Wall Street Journal ("widely followed")

**How to Access:** Free public access. Email subscription available.

**Historical Coverage:** Blog has been active for 15+ years.

**Data Format:** Blog posts (HTML).

**Cost:** Free

**Known Limitations:**
- Commentary/analysis, not structured data
- Single author perspective (though guest posts add diversity)
- Written from broker/underwriting perspective (RT ProExec)
- Not suitable for quantitative modeling directly
- Posts are not peer-reviewed

---

## 74. SEC EDGAR Full-Text Search & Enforcement Actions

**Full Name:** SEC EDGAR Full-Text Search / SEC Enforcement Actions Database

**URL:** https://efts.sec.gov/LATEST/search-index?q= and https://www.sec.gov/enforce/sec-enforcement-actions

**Data Contents:**
- Full-text search across all EDGAR filings
- SEC enforcement actions: administrative proceedings, civil actions, trading suspensions
- Litigation releases
- Administrative proceedings
- SEC charges and settlements

**How to Access:** Free via SEC website.

**Historical Coverage:** Enforcement actions database spans decades.

**Data Format:** Web search. PDF documents.

**Cost:** Free

**Known Limitations:**
- Enforcement actions represent a subset of D&O-relevant events
- Search functionality can be imprecise
- No bulk download API for enforcement actions
- Actions may be resolved years after initial event
- SEED database (entry #7) provides more structured enforcement data

---

# SECTION 7: DATA INTEGRATION AND CROSS-REFERENCE NOTES

---

## Common Identifiers for Cross-Source Linking

| Identifier | Source | Coverage |
|---|---|---|
| CIK (Central Index Key) | SEC EDGAR | All SEC filers |
| CUSIP | Standard & Poor's | US/Canadian securities |
| ISIN | ISO 6166 | Global securities |
| Ticker Symbol | Exchanges | Exchange-listed companies |
| PERMNO/PERMCO | CRSP | CRSP universe |
| GVKEY | Compustat | Compustat universe |
| LEI (Legal Entity Identifier) | GLEIF | Global entities |
| DUNS Number | Dun & Bradstreet | Global businesses |

## Recommended Linkage Tables
- **CRSP/Compustat Merged**: Available on WRDS (most commonly used in academic research)
- **SEC CIK to Ticker mapping**: Available via SEC EDGAR API
- **BoardEx to CRSP/Compustat**: Available through WRDS linkage files
- **Audit Analytics to CRSP/Compustat**: Available through WRDS

---

# SECTION 8: COST SUMMARY

| Category | Free Sources | Paid (Moderate) | Paid (Enterprise) |
|---|---|---|---|
| Academic/Research | Cornerstone, NERA, Stanford SCAC, Harvard Forum, Blue Sky Blog, Georgetown, SSRN, SEED, D&O Diary | NBER ($170/yr), Journal subscriptions | WRDS (institutional) |
| Insurance Industry | AIG Claims, Allianz, Aon (some), WTW (some), Woodruff Sawyer, Swiss Re, III | AM Best (reports), Betterley (IRMI) | Advisen/Zywave, ISO/Verisk |
| Corporate Governance | Proxy Monitor, Spencer Stuart Board Index, CEO Turnover datasets | ISS (from $10K/yr) | BoardEx, Equilar, Glass Lewis |
| Financial/Market | SEC EDGAR, FRED, FINRA Short Interest, PACER | | CRSP, Compustat, Capital IQ, Bloomberg, Refinitiv, Audit Analytics |
| News/Alternative | GDELT, SEC Whistleblower, Reddit, Congressional trading | NewsAPI, Event Registry | LexisNexis, Factiva, X/Twitter API |
| ESG/Governance Ratings | MSCI (basic lookup), S&P (basic) | | MSCI ESG, Sustainalytics, Bloomberg ESG, S&P Global ESG |
| Litigation Tracking | Stanford SCAC, SEC Enforcement | | Lex Machina, 13D Monitor, SharkRepellent |

---

# SECTION 9: DATA SOURCE PRIORITY RANKING FOR D&O UNDERWRITING

## Tier 1: Essential / Foundational
1. **Advisen/Zywave Loss Insight** -- Most comprehensive D&O loss database
2. **Stanford SCAC + Cornerstone Research** -- Securities class action filing and settlement data
3. **SEC EDGAR** -- Fundamental company filings, risk factors, governance disclosures
4. **CRSP + Compustat (via WRDS)** -- Stock returns and financial statement data for loss modeling
5. **Audit Analytics** -- Restatements, auditor changes, and SOX compliance flags
6. **ExecuComp (via WRDS)** -- Executive compensation data
7. **BoardEx (via WRDS)** -- Director network and biographical data
8. **ISS Governance QualityScore** -- Governance risk scoring

## Tier 2: Highly Valuable
9. **NERA Economic Consulting reports** -- Litigation trend context
10. **AM Best D&O market reports** -- Market pricing and loss ratio data
11. **Credit rating agency data** -- Corporate creditworthiness signals
12. **MSCI ESG Ratings** -- ESG risk signals including governance
13. **Bloomberg Terminal / Capital IQ** -- Comprehensive financial data
14. **NYU SEED** -- SEC enforcement action tracking
15. **AIG / Allianz / WTW / Aon reports** -- Claims trends and market intelligence
16. **FINRA short interest data** -- Market skepticism signals

## Tier 3: Supplementary / Alternative
17. **Glassdoor reviews** -- Corporate culture signals
18. **GDELT / Event Registry** -- News event monitoring
19. **LexisNexis / Factiva** -- Deep news archive for due diligence
20. **Short seller reports** -- Fraud allegation signals
21. **Activist investor databases** -- Governance challenge signals
22. **Congressional trading data** -- Regulatory/political risk signals
23. **Options unusual activity** -- Pre-announcement trading signals
24. **Reddit / Twitter sentiment** -- Retail investor sentiment
25. **Patent litigation data** -- IP-related D&O risk

---

*Document compiled: February 6, 2026*
*Purpose: D&O Liability Underwriting System Data Source Inventory*
*Classification: Research Reference*
