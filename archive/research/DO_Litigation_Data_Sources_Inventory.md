# Directors & Officers (D&O) Liability Underwriting System
# Comprehensive Litigation & Court Data Source Inventory

**Prepared:** 2026-02-06
**Purpose:** Exhaustive inventory of litigation and court data sources relevant to D&O liability underwriting

---

## TABLE OF CONTENTS

1. [Securities Class Action Databases](#1-securities-class-action-databases)
2. [Federal Court Systems (PACER & Related)](#2-federal-court-systems)
3. [Free / Open-Source Court Data](#3-free--open-source-court-data)
4. [Commercial Legal Research Platforms](#4-commercial-legal-research-platforms)
5. [Litigation Analytics Platforms](#5-litigation-analytics-platforms)
6. [State Court Systems](#6-state-court-systems)
7. [SEC Enforcement & Regulatory Databases](#7-sec-enforcement--regulatory-databases)
8. [Insurance-Specific Loss & Claims Databases](#8-insurance-specific-loss--claims-databases)
9. [Settlement, Verdict & Fee Databases](#9-settlement-verdict--fee-databases)
10. [Specialized Litigation Databases](#10-specialized-litigation-databases)
11. [Government Enforcement & Fraud Databases](#11-government-enforcement--fraud-databases)
12. [Arbitration Databases](#12-arbitration-databases)
13. [International / Foreign Court Databases](#13-international--foreign-court-databases)
14. [Sentencing & Criminal Justice Databases](#14-sentencing--criminal-justice-databases)
15. [Academic & Research Databases](#15-academic--research-databases)
16. [Supplemental Intelligence Sources](#16-supplemental-intelligence-sources)
17. [D&O Analytics: Motion to Dismiss, Class Certification, Lead Plaintiff & Fee Data](#17-do-analytics-rates-and-statistics)

---

## 1. SECURITIES CLASS ACTION DATABASES

### 1.1 Stanford Securities Class Action Clearinghouse (SCAC)

- **Full Name:** Securities Class Action Clearinghouse (SCAC), Stanford Law School
- **URL:** https://securities.stanford.edu/
- **What It Contains:**
  - Database of 7,070+ federal securities class action filings since passage of the Private Securities Litigation Reform Act (PSLRA) of 1995 through December 31, 2025.
  - Filing details: complaint text, defendant names, court, filing date, case status, settlement amounts, dismissal information, lead plaintiff identity, lead counsel, industry classification, nature of allegations (accounting irregularities, missed earnings, insider trading, etc.).
  - Annual and semi-annual research reports produced in collaboration with Cornerstone Research.
  - Top 10 settlements list.
- **How to Access:**
  - **Web search interface:** Free public access to basic case filings database at securities.stanford.edu/filings.html.
  - **Academic researchers:** Can request Excel spreadsheet exports of the underlying raw data for non-commercial empirical research, subject to a Non-Disclosure Agreement. Contact: scac@law.stanford.edu.
  - **Commercial access:** Not available through the Clearinghouse; commercial users are directed to Stanford Securities Litigation Analytics (SSLA) -- see 1.2 below.
  - **No public API.** An R package (scac.database.downloader on GitHub by br00t999) has been created by third parties to scrape/download the database, though this is not officially sanctioned.
- **Historical Coverage:** 1996-present (post-PSLRA filings).
- **Data Format:** HTML web interface (public); Excel spreadsheets (academic access).
- **Update Frequency:** Updated each business day for new filings. Currently undergoing restructuring; new filings email continues via SSLA.
- **Cost:** Free for public web access. Academic access free under NDA. Commercial access requires SSLA license.
- **Known Limitations:**
  - Does not cover state-court-only securities class actions comprehensively (though some state filings are included).
  - No API or structured data feed for public users.
  - Currently undergoing organizational restructuring, which may delay updates.
  - Does not include non-class-action securities litigation (individual suits, derivative actions, etc.).
  - Data prior to 1996 not covered.

### 1.2 Stanford Securities Litigation Analytics (SSLA)

- **Full Name:** Stanford Securities Litigation Analytics (SSLA)
- **URL:** https://sla.law.stanford.edu/
- **What It Contains:**
  - Successor/commercial arm of SCAC data. Enhanced, structured, and normalized dataset with additional analytical variables.
  - Case-level data enriched with company identifiers, stock price data, litigation outcome variables, settlement amounts, attorney fee awards, class period dates, officer/director defendant information.
  - Interactive web tool with search, filtering, and reporting capabilities.
- **How to Access:**
  - Three access methods: (a) wholesale data licensing via Excel exports; (b) online web tool with full search/reporting; (c) project-by-project consulting engagements.
  - Annual paid data license required. Contact: jhegland@law.stanford.edu.
- **Historical Coverage:** 1996-present (same underlying dataset as SCAC, with enhanced variables).
- **Data Format:** Excel exports (wholesale license); interactive web tool.
- **Update Frequency:** Regularly updated (specific cadence not publicly disclosed).
- **Cost:** Paid annual license. Pricing not publicly disclosed; quoted on a per-client basis. Licenses sold to D&O insurers, brokers, law firms, and institutional investors.
- **Known Limitations:**
  - Pricing may be prohibitive for smaller operations.
  - Not API-accessible (no programmatic integration without custom arrangement).
  - Same underlying coverage limitations as SCAC regarding state-only filings.

### 1.3 ISS Securities Class Action Services (ISS SCAS)

- **Full Name:** ISS Securities Class Action Services (ISS SCAS), an ISS STOXX brand
- **URL:** https://www.iss-scas.com/ and https://www.issgovernance.com/
- **What It Contains:**
  - Proprietary "RecoverMax" database of 14,000+ securities class action cases.
  - End-to-end tracking: new filings, ongoing litigation, settlement announcements, filing deadlines, claim eligibility analysis, claims filing and recovery tracking.
  - Settlement distribution amounts, recovery rates, claim filing deadlines.
  - Focus on actionable claims recovery for institutional investors rather than purely analytical/research use.
- **How to Access:**
  - Commercial subscription (annual license or contingency fee arrangement).
  - Under contingency model, ISS SCAS receives a percentage deduction from recoveries.
  - Fixed-fee annual subscription also available.
  - No public API disclosed.
- **Historical Coverage:** 35+ years of operation (since approximately 1990).
- **Data Format:** Proprietary web platform; reports and alerts delivered to clients.
- **Update Frequency:** Continuous monitoring of new filings and settlements.
- **Cost:** Paid. Two pricing models: (a) contingency fee on recoveries; (b) fixed annual subscription. Averages over $1 billion/year in recoveries for clients.
- **Known Limitations:**
  - Primarily designed for claims recovery, not underwriting analytics; data may not be structured for actuarial modeling.
  - Pricing details not publicly available.
  - Data is proprietary and not easily exportable for integration into third-party systems without negotiation.

---

## 2. FEDERAL COURT SYSTEMS

### 2.1 PACER (Public Access to Court Electronic Records)

- **Full Name:** Public Access to Court Electronic Records (PACER)
- **URL:** https://pacer.uscourts.gov/
- **What It Contains:**
  - Complete docket sheets and filed documents for all cases in U.S. federal courts: District Courts, Bankruptcy Courts, Courts of Appeals, and the Judicial Panel on Multidistrict Litigation.
  - Case metadata: parties, attorneys, judges, nature of suit codes, filing dates, disposition dates.
  - Full-text documents: complaints, motions, orders, opinions, settlement agreements (where filed).
  - Covers civil, criminal, bankruptcy, and appellate proceedings.
- **How to Access:**
  - **Web interface:** Individual case lookups via CM/ECF systems at each court.
  - **PACER Case Locator (PCL):** National index for searching across all courts. API available for PCL.
  - **Developer APIs:** PACER Authentication API and PACER Case Locator API documented at pacer.uscourts.gov/file-case/developer-resources.
  - **Bulk data:** Per-search fee of $30 plus per-page charges. Not designed for mass scraping.
  - **Third-party aggregators:** UniCourt, CourtListener/RECAP, Docket Alarm, and others provide restructured PACER data via APIs (see their respective entries).
- **Historical Coverage:**
  - Electronic records availability varies by court. Most courts have electronic dockets from approximately 2001-2004 onward. Some courts have backdated historical records into the 1990s. Pre-electronic records not available through PACER.
- **Data Format:** HTML docket pages; PDF documents; XML feeds via API.
- **Update Frequency:** Real-time (documents available as soon as filed).
- **Cost:**
  - $0.10 per page viewed, capped at $3.00 per document (30-page equivalent).
  - Fees waived if quarterly usage is $30 or less.
  - Bulk searches: $30 per batch search plus per-page document charges.
  - Audio files of court proceedings: $2.40 per file.
- **Known Limitations:**
  - Per-page fees make large-scale data collection expensive (cost can run into tens of thousands of dollars for comprehensive D&O case collection).
  - No standardized API for full-text document search; searches are limited to case metadata.
  - Document formats are inconsistent (scanned PDFs vs. electronic PDFs).
  - Sealed documents and settlement agreements under seal are not accessible.
  - Nature-of-suit codes are assigned by filing attorneys and may be inaccurate.
  - Terms of service prohibit systematic redistribution of data.

### 2.2 PACER Bankruptcy Courts

- **Full Name:** PACER Bankruptcy Court Records
- **URL:** Accessed through https://pacer.uscourts.gov/ (individual bankruptcy court CM/ECF sites)
- **What It Contains:**
  - All bankruptcy petitions, schedules, plans, and associated adversary proceedings.
  - Chapter 7, 11, 12, 13, and 15 cases.
  - D&O relevance: Chapter 11 corporate reorganization filings (often involve D&O liability disputes), adversary proceedings naming officers/directors, preference actions, fraudulent conveyance claims, claims against insiders.
  - Statement of Financial Affairs disclosing officer compensation and insider transactions.
- **How to Access:** Same as PACER (see 2.1). Separate CM/ECF login per bankruptcy court or via PCL.
- **Historical Coverage:** Generally 2001-present electronically; varies by court.
- **Data Format:** Same as PACER.
- **Update Frequency:** Real-time.
- **Cost:** Same fee structure as PACER.
- **Known Limitations:**
  - Bankruptcy records are voluminous; extracting D&O-relevant information requires parsing thousands of docket entries per case.
  - Adversary proceedings (most relevant to D&O) have separate docket numbers from main cases and must be searched separately.
  - No standardized tagging for "D&O-relevant" claims within bankruptcy dockets.

### 2.3 Judicial Panel on Multidistrict Litigation (JPML)

- **Full Name:** Judicial Panel on Multidistrict Litigation (JPML)
- **URL:** https://www.jpml.uscourts.gov/
- **What It Contains:**
  - All pending MDL proceedings across the federal system.
  - MDL case number, transferee court and judge, number of pending actions, statistical data on transfers.
  - Monthly pending MDL reports (posted first business day of each month since January 2024).
  - Historical statistical data on MDL proceedings.
- **How to Access:**
  - **Web:** Pending MDL reports available for free download from JPML website.
  - **PACER:** Full docket and filings for JPML cases accessible through PACER (Court: JPMLDC).
  - No dedicated API; statistical reports available as PDFs.
- **Historical Coverage:** JPML has existed since 1968. Electronic data available approximately from early 2000s; statistical information available in reports going back further.
- **Data Format:** PDF reports; PACER docket entries.
- **Update Frequency:** Monthly (pending MDL reports); real-time via PACER for individual filings.
- **Cost:** Free for JPML website reports; PACER fees for individual docket/document access.
- **Known Limitations:**
  - MDL data on the JPML website is summary-level; detailed case-by-case data requires PACER access.
  - No structured data export (only PDF reports).
  - Does not track post-remand activity after MDL transfer.

---

## 3. FREE / OPEN-SOURCE COURT DATA

### 3.1 CourtListener / RECAP Archive (Free Law Project)

- **Full Name:** CourtListener.com and RECAP Archive, operated by Free Law Project
- **URL:** https://www.courtlistener.com/ and https://free.law/recap/
- **What It Contains:**
  - Nearly half a billion PACER-related objects: dockets, docket entries, documents, parties, and attorneys.
  - Full-text opinions from federal and state appellate courts.
  - Oral argument audio recordings.
  - RECAP Archive: crowdsourced collection of millions of PACER documents gathered via RECAP browser extension (Firefox, Chrome, Safari).
  - Covers virtually every federal case at the docket level, with millions of full-text documents.
- **How to Access:**
  - **REST API v4.3:** Comprehensive API with endpoints for dockets, RECAP documents, opinions, parties, attorneys. 5,000 queries/hour for authenticated users. Documentation at courtlistener.com/help/api/rest/.
  - **PACER Data APIs:** Allows scraping PACER data and uploading into CourtListener. Documentation at courtlistener.com/help/api/rest/pacer/.
  - **Bulk data downloads:** PostgreSQL database exports available. Courts metadata and docket data available in tab-delimited format. Available at courtlistener.com/help/api/bulk-data/.
  - **Web search interface:** Free full-text search of opinions and RECAP archive.
  - **RECAP browser extension:** Automatically uploads PACER documents viewed by users to the RECAP archive, making them freely available.
- **Historical Coverage:**
  - Opinions: Varies by court; some federal appellate courts back to 18th century.
  - RECAP Archive: Coverage depends on user contributions. Major cases have extensive coverage; smaller cases may have minimal or no documents.
  - Docket-level data: Attempts to index nearly every federal case, though document-level coverage varies.
- **Data Format:** JSON (API); PostgreSQL bulk exports (CSV with double-quote quoting as of Jan 2025); PDF documents.
- **Update Frequency:** Continuous (thousands of new documents per day via RECAP contributions and automated scraping).
- **Cost:** Free for all access methods. Free Law Project is a 501(c)(3) non-profit.
- **Known Limitations:**
  - Document coverage is uneven -- depends on RECAP user contributions. Many PACER documents are NOT in the RECAP archive.
  - Not a complete mirror of PACER; should be treated as a supplement, not a replacement.
  - Bulk data files are very large (multi-gigabyte); requires significant storage and processing capability.
  - API rate limits (5,000/hour) may constrain large-scale automated queries.
  - State court coverage is limited to appellate opinions; no state trial court dockets.
  - As of summer 2025, the v4 API has processed over 100 million requests, indicating heavy usage and potential for rate limiting.

### 3.2 Justia Dockets & Filings

- **Full Name:** Justia Dockets & Filings
- **URL:** https://dockets.justia.com/
- **What It Contains:**
  - Free searchable index of federal cases, dockets, and selected filings from U.S. District Courts and U.S. Courts of Appeal.
  - Case metadata: parties, judges, jurisdiction, nature of suit, filing dates.
  - Links to actual documents (may redirect to PACER for full documents).
  - RSS feeds for new cases matching search criteria.
- **How to Access:** Free web search interface. No API publicly documented. RSS feeds available for customized searches.
- **Historical Coverage:** 2004-present for docket data.
- **Data Format:** HTML web interface; RSS feeds.
- **Update Frequency:** Regular updates as new cases are filed.
- **Cost:** Free.
- **Known Limitations:**
  - Federal courts only (no state court dockets).
  - Selected filings only; not all documents from every case are indexed.
  - No API for programmatic access or bulk download.
  - Links to PACER for full documents, so PACER fees still apply for document retrieval.
  - Not as comprehensive as PACER or CourtListener for document-level data.

### 3.3 Federal Judicial Center (FJC) Integrated Database

- **Full Name:** Federal Court Cases: FJC Integrated Database
- **URL:** https://www.fjc.gov/research/federal-court-cases-fjc-integrated-database-1979-present
- **What It Contains:**
  - Case-level data on ALL civil, criminal, bankruptcy, and appellate cases filed and terminated in the federal court system.
  - Variables include: nature of suit, filing date, termination date, disposition type, procedural progress at termination, jurisdictional basis, amount demanded, origin of case, weight of case (complexity measure), judge.
  - Does NOT contain full-text documents or party names for most records.
  - Contains information about every case filed in the PACER system.
- **How to Access:**
  - **Free download** from FJC website. Available in annual and multi-year batches.
  - **Interactive online tool** for selecting target cases.
  - Also available through ICPSR (Inter-university Consortium for Political and Social Research) at University of Michigan.
  - Also available through WRDS (Wharton Research Data Services) for academic subscribers.
- **Historical Coverage:** Civil cases from 1970; criminal cases from 1971; appellate cases from 1971; bankruptcy cases from around 2008. Most commonly cited as 1979-present.
- **Data Format:** Tab-delimited text file (approximately 2.7 GB for full dataset). Codebook/documentation provided.
- **Update Frequency:** Updated periodically (typically quarterly or semi-annually; specific schedule varies).
- **Cost:** Free.
- **Known Limitations:**
  - **Critical for D&O use:** Contains case-level aggregate data but NOT individual docket entries or documents. Cannot determine specific allegations, settlement amounts, or case outcomes beyond coded disposition variables.
  - Nature of suit codes may be inaccurate (assigned by filing attorneys).
  - Does not directly identify D&O cases; requires filtering by nature of suit codes (e.g., 850 for Securities/Commodities/Exchange).
  - Party name fields have limited availability in older records.
  - No full-text search capability.
  - Bankruptcy data coverage is more recent (2008+).
  - Excellent for quantitative trend analysis but insufficient for case-specific underwriting intelligence.

---

## 4. COMMERCIAL LEGAL RESEARCH PLATFORMS

### 4.1 Westlaw (Thomson Reuters)

- **Full Name:** Westlaw Precision (Thomson Reuters)
- **URL:** https://www.westlaw.com/
- **What It Contains:**
  - Comprehensive legal research database: full-text opinions, statutes, regulations, secondary sources.
  - **Westlaw Litigation Analytics:** Data-driven insights on judges, courts, attorneys, law firms, and case types across state and federal courts. Covers 8 million federal dockets and 150 million state dockets.
  - **Practical Law:** Transactional practice resources including D&O insurance checklists, sample policies, and litigation trend analyses.
  - Motion success rate analytics by judge, court, and case type.
  - Damages analytics.
  - Expert witness data (Expert Witness Profiler).
- **How to Access:**
  - Subscription-based web platform. No public API for litigation analytics (API available for certain enterprise products via Westlaw Edge/Precision integrations).
  - D&O-specific content accessible through Practical Law and litigation analytics modules.
- **Historical Coverage:** Case law back to 18th century; litigation analytics data from approximately 2007+ for attorney analytics; dockets back to varying dates by jurisdiction.
- **Data Format:** Proprietary web interface; PDF/RTF document exports; data visualization dashboards.
- **Update Frequency:** Daily for case law; litigation analytics updated regularly.
- **Cost:** Enterprise subscription pricing; typically $100-$400+/month per user depending on modules. Litigation Analytics is a premium add-on module. Institutional pricing negotiable.
- **Known Limitations:**
  - No bulk data export for litigation analytics (no CSV/Excel download of analytics datasets).
  - Does not have a dedicated "D&O litigation" practice area category -- requires manual search construction.
  - Expensive for large-team deployments.
  - API access limited and typically restricted to large enterprise customers.
  - Analytics coverage can be uneven across less-active jurisdictions.

### 4.2 LexisNexis

- **Full Name:** LexisNexis (RELX Group)
- **URL:** https://www.lexisnexis.com/
- **What It Contains:**
  - Comprehensive legal research: full-text case law, statutes, regulations, dockets, news, public records.
  - **Lexis+ Analytics:** Litigation analytics including judge behavior, attorney performance, motion outcomes, case timing.
  - **Lex Machina** (owned by LexisNexis -- see 5.1 below): Specialized litigation analytics.
  - **Lexis+ AI / Protege AI:** AI-powered research assistant integrated with analytics.
  - Company/corporate dossiers with litigation history.
  - Verdicts & settlements databases.
- **How to Access:**
  - Subscription-based web platform. Enterprise API available for bulk data access (by negotiation).
  - Lexis+ modules for litigation analytics. Brief Analyzer for automated case analysis.
- **Historical Coverage:** Case law back centuries; docket data varies by jurisdiction; analytics data generally 2000s-present.
- **Data Format:** Proprietary web interface; PDF/document exports; API (JSON/XML) for enterprise clients.
- **Update Frequency:** Daily updates for core legal content.
- **Cost:** Enterprise subscription. Typically $200-$500+/month per user. Lex Machina is a separate add-on.
- **Known Limitations:**
  - Similar to Westlaw: no dedicated D&O underwriting module.
  - Bulk data extraction requires enterprise agreement.
  - Cost can be significant for comprehensive access.
  - Verdicts & settlements data may have reporting bias (voluntary submissions).

### 4.3 Bloomberg Law

- **Full Name:** Bloomberg Law (Bloomberg Industry Group)
- **URL:** https://www.bloomberglaw.com/ and https://pro.bloomberglaw.com/
- **What It Contains:**
  - Legal research platform with integrated Bloomberg financial and corporate data.
  - **Litigation Intelligence Center:** Litigation analytics searchable by company, law firm, judge, or attorney.
  - Practice area coverage: patent, copyright, trademark, antitrust, **securities**, employment, commercial, product liability, federal bankruptcy.
  - **Judge Analytics:** Career history, motion ruling patterns (motions to dismiss, summary judgment, class certification), affirmance/reversal rates.
  - **Attorney Analytics:** Representation data for 100,000+ attorneys at 775+ law firms, from U.S. District Court and Courts of Appeal dockets filed 2007-present.
  - **Enterprise Dockets API:** API-accessible court docket data with analytics by company, firm, court, and judge, plus custom analytics dashboards.
  - Full integration with Bloomberg Terminal financial data.
  - Delaware Chancery Court docket coverage.
- **How to Access:**
  - Subscription-based platform.
  - **Enterprise Dockets API:** Available for programmatic access with custom analytics and dashboards, alert capacity, and custom scripts. Contact Bloomberg sales.
  - Web interface with search, visualization, and export tools.
- **Historical Coverage:** Attorney analytics from 2007-present; judge analytics varies; case law back centuries.
- **Data Format:** Web interface; API (JSON); PDF exports; integration with Bloomberg Terminal.
- **Update Frequency:** Daily for docket data; regular updates for analytics.
- **Cost:** Subscription starting around $500/month per user for full Bloomberg Law access. Enterprise API pricing separate and negotiable.
- **Known Limitations:**
  - Securities litigation analytics are available but not specifically branded as "D&O analytics."
  - Bloomberg Law's primary advantage (financial data integration) is most valuable when used alongside Bloomberg Terminal (additional cost).
  - Enterprise API access requires sales negotiation; not self-service.
  - Coverage is strongest for federal courts; state court coverage varies.

---

## 5. LITIGATION ANALYTICS PLATFORMS

### 5.1 Lex Machina (LexisNexis)

- **Full Name:** Lex Machina, a LexisNexis Company
- **URL:** https://www.lexisnexis.com/en-us/products/lex-machina.page
- **What It Contains:**
  - Litigation analytics across 10 million+ cases, 45 million+ customer-facing documents.
  - Data on 8,000+ judges, 6,000+ expert witnesses.
  - Practice areas: Securities, antitrust, employment, patent, copyright, trademark, trade secret, commercial, product liability, insurance, bankruptcy, environmental, ERISA, consumer protection, government contracts, tax, and more.
  - Predictive analytics: case duration, motion outcomes, damages ranges, judge behavior patterns.
  - **Securities-specific analytics:** Filing trends, dismissal rates, settlement ranges, judge preferences in securities cases.
  - Attorney and law firm analytics: win rates, settlement history, case volume.
  - As of 2025, includes Protege AI for natural-language analytics queries.
- **How to Access:**
  - Subscription-based web platform. API available for custom integrations.
  - Can export analytics reports and datasets.
- **Historical Coverage:** Federal cases generally from 2000 onward; some practice areas have deeper historical coverage (e.g., patent from 2000, securities varies).
- **Data Format:** Web interface; API (for integrations); exportable reports (PDF, CSV).
- **Update Frequency:** Continuously updated with new filings and case events.
- **Cost:** Starting price around $300/year for basic access; full enterprise subscriptions range from several thousand to tens of thousands of dollars annually depending on practice areas, seats, and API access.
- **Known Limitations:**
  - Federal court focus; state court coverage is more limited.
  - Securities litigation analytics exist but are not as deep as Stanford/SSLA for pure securities class action analysis.
  - API integration requires paid subscription tier.
  - Historical depth for securities-specific analytics may not go back as far as SCAC/SSLA (1996).
  - Pricing can be opaque; requires sales engagement for quotes.

### 5.2 Docket Alarm (vLex)

- **Full Name:** Docket Alarm, a vLex product
- **URL:** https://www.docketalarm.com/
- **What It Contains:**
  - 730 million+ searchable documents and dockets with 300,000+ new additions daily.
  - Coverage: federal, district, bankruptcy, supreme, appellate courts, research agencies, PTAB (Patent Trial and Appeal Board), TTAB (Trademark Trial and Appeal Board).
  - Full-text document search with natural language and Boolean capabilities.
  - Custom litigation analytics in every practice area for state, federal, and administrative courts.
  - Rule-based calendaring and real-time alerts.
  - Predictive analytics for case outcomes.
  - Bulk docket pull tools (GitHub: DocketAlarm/state-court-bulk-docket-pull).
- **How to Access:**
  - **Web interface:** Search and browse.
  - **API:** Available on Pay-As-You-Go plan; reduced rates for bulk users. Also available on RapidAPI marketplace.
  - **Bulk docket pull:** GitHub tools for pulling state court cases in bulk via API.
- **Historical Coverage:** Varies by court; generally comprehensive from early 2000s forward.
- **Data Format:** Web interface; API (JSON); PDF documents.
- **Update Frequency:** Daily (300,000+ new documents/day).
- **Cost:**
  - Flat-fee membership: $99/month per legal professional.
  - Pay-as-you-go: $39.99/month base plus per-document charges.
  - API access included in Pay-As-You-Go; bulk pricing available.
- **Known Limitations:**
  - Per-document charges can accumulate quickly for large-scale research.
  - Not specifically designed for D&O/securities analysis; general-purpose litigation database.
  - State court coverage varies by jurisdiction.
  - Bulk pull tools require technical setup and API key.

### 5.3 UniCourt

- **Full Name:** UniCourt Enterprise API
- **URL:** https://unicourt.com/
- **What It Contains:**
  - Court data from 4,000+ state and federal courts across 40+ states.
  - All federal (PACER) courts: District Courts, Bankruptcy Courts, Courts of Appeals.
  - State trial and appellate courts.
  - AI-normalized data: party names, attorney names, judge names standardized across jurisdictions.
  - Case analytics, docket tracking, party monitoring.
  - PACER data delivered with reduced fees compared to direct PACER access.
- **How to Access:**
  - **API-first platform:** RESTful API with sample code, Python library, and proprietary tools. Plug-and-play architecture.
  - **PACER Data API:** Normalized PACER data accessible via UniCourt's API without direct PACER interaction.
  - **Web interface** for search and case tracking.
- **Historical Coverage:** Varies by jurisdiction; comprehensive for federal courts from approximately 2001 onward; state court coverage varies.
- **Data Format:** JSON (API); web interface; exportable data.
- **Update Frequency:** Real-time to near-real-time for federal courts; state court update frequency varies.
- **Cost:**
  - Personal: $49/month
  - Professional: $149/month
  - Premium: $299/month
  - Enterprise: from $2,250/month
  - Custom pricing for large deployments.
  - Free trial available.
- **Known Limitations:**
  - State court coverage, while extensive (40+ states), is not universal -- some states have limited or no coverage.
  - Data normalization, while a strength, can sometimes introduce errors in entity matching.
  - Higher tiers needed for full API access and bulk data.
  - PACER-sourced data carries the same underlying limitations as PACER itself.

### 5.4 Trellis Law

- **Full Name:** Trellis (AI-Powered State Court Research & Litigation Analytics)
- **URL:** https://trellis.law/
- **What It Contains:**
  - State trial court data across 46 states, 3,335 courts, 2,574 counties.
  - Federal, appellate, supreme court, and bankruptcy cases.
  - Judge analytics: ruling patterns on motions, judicial tendencies, case duration.
  - State court tentative rulings and orders (unique differentiator).
  - Case, party, county, document, and judicial ruling search.
  - PACER data integration.
- **How to Access:**
  - **Trial Court Data API:** Suite of endpoints for case, party, county, document, and judicial rulings for state, federal, and bankruptcy courts. PACER API endpoint also available.
  - **Web platform:** Search, alerts, judge analytics, motion/issue analytics.
- **Historical Coverage:** Varies by state; strong coverage from approximately 2005-present for most states.
- **Data Format:** JSON (API); web interface; PDF exports.
- **Update Frequency:** Regular updates; state court data updated as filed.
- **Cost:**
  - Research & Judge Analytics: $199.95/month or $1,999.95/year (single state, 900 annual content views).
  - Starting at $129.95/month for base subscription.
  - API pricing available by quote.
- **Known Limitations:**
  - State court data depth varies by jurisdiction.
  - Content view limits on lower tiers.
  - API pricing not publicly disclosed; requires quote.
  - Strongest for state court data; federal/PACER data available but not primary differentiator.

---

## 6. STATE COURT SYSTEMS

### 6.1 Delaware Chancery Court

- **Full Name:** Court of Chancery, State of Delaware
- **URL:** https://courts.delaware.gov/chancery/ and https://courtconnect.courts.delaware.gov/
- **What It Contains:**
  - **Critically important for D&O:** Delaware is the incorporation state for ~68% of Fortune 500 companies and ~50% of all U.S. publicly traded companies. Chancery Court handles the vast majority of corporate governance litigation, including: fiduciary duty breach claims against directors/officers, merger objection lawsuits, books-and-records (Section 220) demands, appraisal actions (Section 262), derivative suits, controller/squeeze-out claims.
  - Docket information for civil actions.
  - Court opinions (many are landmark D&O liability precedents).
- **How to Access:**
  - **File & ServeXpress:** Electronic filing system; docket information available for a fee through this platform (fileandservexpress.com and fileandservedelaware.com).
  - **Delaware Court Connect:** Online public access portal (courtconnect.courts.delaware.gov).
  - **Third-party platforms:** Bloomberg Law, LexisNexis, and Westlaw all carry Delaware Chancery Court dockets and opinions.
  - No public API. No bulk data download.
- **Historical Coverage:** Electronic dockets available from approximately 2005-present through File & ServeXpress; opinions go back further through legal research databases.
- **Data Format:** HTML docket pages; PDF filings; no structured data export.
- **Update Frequency:** Real-time as documents are filed.
- **Cost:** File & ServeXpress charges per-document and per-docket access fees. Third-party platform access requires respective subscriptions.
- **Known Limitations:**
  - **Data mining/scraping explicitly prohibited.** Data may not be mined, sold, or used in pay-for-use applications; automated access for data extraction is prohibited.
  - No API or bulk export; must access case-by-case.
  - Docket data not freely available -- requires File & ServeXpress account.
  - Not integrated into PACER (state court system).
  - Historical coverage limited for older electronic records.
  - Many important settlement agreements are filed under seal.

### 6.2 New York Supreme Court (Commercial Division) -- NYSCEF

- **Full Name:** New York State Courts Electronic Filing System (NYSCEF), including Commercial Division
- **URL:** https://iapps.courts.state.ny.us/nyscef/HomePage
- **What It Contains:**
  - Electronic filings for NY Supreme Court (all divisions), Surrogate's Court, Court of Claims.
  - **Commercial Division** mandatory e-filing since 2010 for commercial cases in New York County (Manhattan) and other participating counties.
  - Covers corporate governance disputes, securities fraud state-law claims, breach of fiduciary duty, indemnification actions, D&O insurance coverage disputes.
  - Full docket entries and filed documents.
- **How to Access:**
  - **Web interface:** Free case search and document viewing at NYSCEF website.
  - **No API available.**
  - **Explicit prohibition on data mining:** All data in NYSCEF is property of NY Unified Court System. Data may NOT be mined, sold, or used in pay-for-use applications. Automated programs for data extraction are prohibited.
- **Historical Coverage:** Electronic filings generally available from 2010 onward for Commercial Division; varies for other courts.
- **Data Format:** HTML docket pages; PDF filed documents.
- **Update Frequency:** Real-time as documents are filed.
- **Cost:** Free to search and view on NYSCEF.
- **Known Limitations:**
  - **Scraping/data mining strictly prohibited** per NYSCEF terms.
  - No API or bulk data access.
  - Not searchable by case type or nature of suit (must know party name, index number, or attorney name).
  - Filed documents may be scanned/non-searchable PDFs.
  - Coverage limited to e-filing-mandatory courts; older cases and non-mandatory courts may not have electronic records.

### 6.3 California State Courts

- **Full Name:** California Courts -- Odyssey eFileCA and Individual Superior Court Case Management Systems
- **URL:** https://courts.ca.gov/ and http://www.odysseyefileca.com/
- **What It Contains:**
  - E-filing for civil, family, probate, and some criminal cases across California superior courts.
  - D&O-relevant: shareholder derivative suits, breach of fiduciary duty, securities fraud under California corporate law, PAGA (Private Attorneys General Act) claims against officers.
  - Case information varies by county (each superior court maintains its own case management system).
- **How to Access:**
  - **E-filing:** Through electronic filing service providers (EFSPs) connected to Odyssey eFileCA.
  - **Case information:** County-by-county; each superior court has its own public access portal (e.g., Los Angeles Superior Court at lacourt.org; San Francisco at sfsuperiorcourt.org).
  - **eFiling API:** Available for document submission but NOT for bulk data extraction.
  - Third-party services (UniCourt, Trellis, Docket Alarm) aggregate and normalize California state court data.
- **Historical Coverage:** Varies by county; some counties have electronic records back to 2000; e-filing mandates are more recent (2010s-2020s).
- **Data Format:** Varies by county; generally HTML web interfaces and PDF documents.
- **Update Frequency:** Real-time for e-filed documents.
- **Cost:** Free to search case information at most county portals; document retrieval may have nominal fees.
- **Known Limitations:**
  - Highly fragmented across 58 counties with different systems and coverage.
  - No statewide unified database or API for case data.
  - Bulk data access not generally available directly from court systems.
  - Third-party aggregation is the most practical approach but adds cost.

### 6.4 Texas State Courts -- eFileTexas

- **Full Name:** eFileTexas.gov (Official E-Filing System for Texas Courts)
- **URL:** https://www.efiletexas.gov/
- **What It Contains:**
  - Mandatory e-filing for all attorneys in civil, family, probate, and criminal cases in Supreme Court, Court of Criminal Appeals, Courts of Appeals, all district and county courts.
  - Managed by Office of Court Administration (OCA); contract with Tyler Technologies (Odyssey platform).
  - D&O-relevant: Texas-incorporated company disputes, energy sector corporate governance litigation, breach of fiduciary duty claims.
- **How to Access:**
  - Web interface for filing and case lookup. Public access through individual county clerk websites and re:SearchTX (research.txcourts.gov) for case-level data.
  - No bulk data API publicly available from eFileTexas.
  - Third-party aggregators (UniCourt, Trellis) provide Texas state court data.
- **Historical Coverage:** E-filing mandate phased in across courts from 2014 onward.
- **Data Format:** Web interface; PDF documents.
- **Update Frequency:** Real-time.
- **Cost:** Free to search case information; filing fees apply to attorneys filing documents.
- **Known Limitations:**
  - No public bulk data API.
  - Coverage completeness depends on when each court went live with e-filing.
  - Case type categorization may be inconsistent across counties.

### 6.5 Illinois State Courts -- eFileIL

- **Full Name:** eFileIL (Illinois Supreme Court statewide e-filing system)
- **URL:** https://efileil.tylertech.cloud/ and https://efile.illinoiscourts.gov/
- **What It Contains:**
  - Mandatory e-filing for civil cases in Supreme, Appellate, and Circuit Courts.
  - Built on Tyler Technologies Odyssey platform.
  - D&O-relevant: Corporate disputes, insurance coverage actions, derivative suits for Illinois-incorporated entities.
- **How to Access:** Web interface; public access through individual county circuit clerk offices. No bulk data API.
- **Historical Coverage:** E-filing mandate implemented progressively; coverage from approximately 2016-2018 onward depending on county.
- **Data Format:** Web interface; PDF documents.
- **Update Frequency:** Real-time.
- **Cost:** Free to search basic case information.
- **Known Limitations:** Same as other state systems -- fragmented, no bulk data, no API.

### 6.6 Florida State Courts

- **Full Name:** Florida Courts E-Filing Portal
- **URL:** https://www.myflcourtaccess.com/
- **What It Contains:**
  - Statewide e-filing portal connecting users to Florida's court system.
  - Covers civil, family, probate, criminal, and appellate cases.
  - D&O-relevant: Corporate governance disputes, insurance coverage litigation (Florida is a major D&O insurance market), securities claims under Florida law.
- **How to Access:** Web interface. No filing fee for account registration. Document access through individual county clerk of court websites.
- **Historical Coverage:** E-filing implementation varies by county; most counties online by 2013-2015.
- **Data Format:** Web interface; PDF documents.
- **Update Frequency:** Real-time.
- **Cost:** Free to register and search; statutory filing fees still apply.
- **Known Limitations:** No statewide bulk data access; county-by-county fragmentation; no API.

---

## 7. SEC ENFORCEMENT & REGULATORY DATABASES

### 7.1 SEC EDGAR (Enforcement Actions, Litigation Releases, Administrative Proceedings)

- **Full Name:** SEC Electronic Data Gathering, Analysis, and Retrieval (EDGAR) System
- **URL:** https://www.sec.gov/search-filings/edgar-application-programming-interfaces and https://www.sec.gov/divisions/enforce/friactions.htm
- **What It Contains:**
  - **Litigation Releases:** All SEC litigation releases from 1995-present detailing civil actions filed in federal court.
  - **Administrative Proceedings:** 18,000+ administrative proceedings from 1995-present.
  - **Enforcement Actions:** Complete database of SEC enforcement actions against companies and individuals.
  - **Company filings:** 10-K, 10-Q, 8-K, proxy statements, insider trading forms (Form 4), all with legal proceedings disclosures.
  - Data includes: respondents, type of proceeding, publication dates, complaints, orders, violated rules/regulations, disgorgement amounts, penalties.
- **How to Access:**
  - **Official SEC EDGAR APIs:** RESTful APIs at data.sec.gov returning JSON; no authentication or API keys required.
  - **Full-text search:** EDGAR Full-Text Search System (EFTS).
  - **Third-party APIs:** sec-api.io provides enhanced Python and JavaScript libraries for enforcement actions, litigation releases, and AAER data (see 7.2). Up to 50 requests/second supported.
  - **Bulk download:** EDGAR filing download API supports access to 18 million+ filings and 100 million+ exhibit files across 400+ form types from 1993-present.
- **Historical Coverage:**
  - Company filings: 1993-present (EDGAR inception).
  - Litigation releases: 1995-present.
  - Administrative proceedings: 1995-present.
  - Enforcement actions: 1997-present (through sec-api.io).
- **Data Format:** XBRL, HTML, XML, JSON (via API), PDF, plain text.
- **Update Frequency:** Real-time as filings and releases are issued.
- **Cost:** Free (official SEC APIs). Third-party APIs (sec-api.io) have tiered pricing starting around $50/month.
- **Known Limitations:**
  - Official SEC APIs are not designed for enforcement-specific analytics; third-party tools needed for structured enforcement data.
  - XBRL data quality varies (some companies file with errors).
  - Legal proceedings disclosures in 10-K/10-Q are narrative text requiring NLP to extract structured data.
  - Enforcement action data covers SEC actions only, not private litigation.

### 7.2 SEC Accounting & Auditing Enforcement Releases (AAER) Databases

- **Full Name:** SEC Accounting and Auditing Enforcement Releases (AAER)
- **URLs:**
  - Official SEC: https://www.sec.gov/divisions/enforce/friactions.htm
  - USC Academic Dataset: https://sites.google.com/usc.edu/aaerdataset/home
  - API: https://sec-api.io/docs/aaer-database-api
  - Audit Analytics (Ideagen): https://www.auditanalytics.com/
- **What It Contains:**
  - Since 1982, the SEC has issued AAERs during/at conclusion of investigations against companies, auditors, or officers for alleged accounting and/or auditing misconduct.
  - Details on: nature of misconduct, individuals and entities involved, effects on financial statements, penalties, disgorgement, bars from serving as officers/directors.
  - **D&O critical:** AAERs directly identify officers and directors involved in accounting fraud and misconduct.
- **How to Access:**
  - **USC Academic Dataset:** 4,278 AAERs (1,816 firm misstatement events), May 1982 - December 2021. Free for academic use.
  - **sec-api.io AAER Database API:** All AAERs from 1997-present with metadata, structured data, and associated documents (PDF, HTML, text). Bulk download APIs available for entire dataset in ZIP files. Python examples available.
  - **Audit Analytics (Ideagen):** Commercial database with enhanced AAER data, including respondent-level details, violation types, and integration with broader corporate/audit data. Pricing by quote (contact Sales@AuditAnalytics.com).
  - **Official SEC website:** Individual AAER lookup.
- **Historical Coverage:** 1982-present (SEC); 1982-2021 (USC dataset); 1997-present (sec-api.io).
- **Data Format:** PDF/HTML (SEC website); structured dataset (USC -- likely CSV/Excel); JSON/API (sec-api.io); proprietary database (Audit Analytics).
- **Update Frequency:** As released by SEC (irregular; roughly 50-100 new AAERs per year).
- **Cost:** Free (SEC website, USC dataset); Paid (sec-api.io tiers, Audit Analytics enterprise pricing).
- **Known Limitations:**
  - AAERs represent only a fraction of actual accounting misconduct (SEC enforcement is selective).
  - USC dataset has a lag (currently through 2021).
  - Matching AAER respondents to company identifiers (CIK, CUSIP, ticker) requires entity resolution work.
  - AAERs do not capture private settlements or non-SEC enforcement actions.

### 7.3 NYU SEED (Securities Enforcement Empirical Database)

- **Full Name:** Securities Enforcement Empirical Database (SEED), NYU Pollack Center for Law & Business and Cornerstone Research
- **URL:** https://research.seed.law.nyu.edu/ and https://www.law.nyu.edu/centers/pollackcenterlawbusiness/seed
- **What It Contains:**
  - Tracks SEC enforcement actions filed against public companies traded on major U.S. exchanges and their subsidiaries.
  - Variables: defendant names and types, violations, judicial venues, and resolutions.
  - Analysis and reporting of SEC enforcement activity with regular updates on new filings and settlement information.
- **How to Access:**
  - **Public access:** A portion of SEED is available to the general public through the web search interface at research.seed.law.nyu.edu.
  - **Academic scholars:** Extended access available by request. Contact: law.seed@nyu.edu.
  - No known commercial license or API.
- **Historical Coverage:** October 1, 2009 (SEC FY2010) to present.
- **Data Format:** Web search interface; structured data for academic access (format not publicly specified).
- **Update Frequency:** Regular updates with new filings and settlements.
- **Cost:** Free for public access; academic access by arrangement.
- **Known Limitations:**
  - Coverage begins only in FY2010 (no historical data before 2009).
  - Excludes enforcement actions with only delinquent filing allegations.
  - Limited to public companies on major exchanges (no private company or OTC-only data).
  - Academic-only extended access; not designed for commercial underwriting use.
  - Covers SEC enforcement only, not private securities litigation.

---

## 8. INSURANCE-SPECIFIC LOSS & CLAIMS DATABASES

### 8.1 Advisen Loss Data (now part of Zywave)

- **Full Name:** Advisen Ltd. Loss Insight Database (now Zywave/Advisen)
- **URL:** https://www.advisenltd.com/data/ and https://go.zywave.com/
- **What It Contains:**
  - **Public D&O Loss Data:** Proprietary relational database of events relating to D&O liability affecting public companies that have or could result in significant financial judgments or loss.
  - **Private D&O Loss Data:** Similar database for private company D&O events.
  - **Casualty, Cyber, EPLI datasets** also available.
  - Data sourced from publicly available information (court records, SEC filings, news, regulatory actions).
  - Fields include: company, event type, event description, allegations, court/regulatory body, filing date, disposition, settlement amounts, defense costs, insurance involvement.
  - Not claims data: NOT truncated by policy limits, censored by retentions, or limited by policy wording application.
  - D&O claims totaled approximately 1,000 in 2006, doubling at peak in 2011.
- **How to Access:**
  - **LOSS INSIGHT platform:** Web-based analytical tool with data search, trend analysis, and reporting.
  - API access available for enterprise clients (contact Advisen/Zywave).
  - Data feeds available for integration into underwriting systems.
- **Historical Coverage:** Loss data going back to at least 2000; some events tracked to earlier dates.
- **Data Format:** Proprietary web interface; data feeds (CSV, API -- by arrangement); analytical reports.
- **Update Frequency:** Continuously updated as new events are identified.
- **Cost:** Commercial subscription required. Enterprise pricing by quote. Typically in the range of tens of thousands of dollars annually.
- **Known Limitations:**
  - **This is arguably the single most directly relevant data source for D&O underwriting** -- specifically designed for insurance industry use.
  - However, it relies on publicly available information, so it may miss non-public settlements and confidential resolutions.
  - Pricing is significant.
  - Data quality depends on source material; some events may have incomplete or delayed information.
  - Historical depth is limited compared to academic databases (SCAC goes back to 1996 with more detail on securities class actions specifically).

### 8.2 Audit Analytics (Ideagen)

- **Full Name:** Audit Analytics, an Ideagen Company
- **URL:** https://www.auditanalytics.com/
- **What It Contains:**
  - **Litigation Database:** Federal cases referenced in all public registrant SEC disclosures of material legal proceedings.
  - Coverage of all publicly disclosed federal securities class actions.
  - SEC and DOJ-disclosed federal litigation against SEC registrants.
  - **AAER Database:** Detailed AAER data (see 7.2).
  - **Additional modules:** Restatements, auditor changes, going concern opinions, internal controls, SOX compliance data.
  - D&O-relevant: Officer/director turnover data, SEC enforcement actions, accounting restatements (major D&O claim triggers).
- **How to Access:**
  - Commercial subscription. Available in module bundles. Data feeds sold separately.
  - Integrated with WRDS (Wharton Research Data Services) for academic access.
  - Contact Sales@AuditAnalytics.com for pricing.
- **Historical Coverage:** Varies by module; litigation data from approximately 2000 onward; AAER data from 1982.
- **Data Format:** Proprietary database; data feeds (CSV/database integration); web interface.
- **Update Frequency:** Regular updates (monthly for some modules, as-needed for others).
- **Cost:** Commercial pricing by quote; academic pricing through WRDS.
- **Known Limitations:**
  - Focused on public companies only (registrants with SEC filings).
  - Litigation data derived from company disclosures, which may be incomplete or delayed.
  - Modules sold separately can make comprehensive access expensive.
  - Not specifically designed as a D&O underwriting tool, though the data is highly relevant.

---

## 9. SETTLEMENT, VERDICT & FEE DATABASES

### 9.1 Cornerstone Research Securities Settlement Database

- **Full Name:** Cornerstone Research Securities Class Action Settlements Reports
- **URL:** https://www.cornerstone.com/insights/reports/securities-class-action-settlements/
- **What It Contains:**
  - Comprehensive database of all securities class action settlements for cases filed after the PSLRA of 1995.
  - Settlement amounts, case characteristics, relationship between settlement outcomes and case variables.
  - Annual reports analyzing settlement trends: median settlement ($14M in 2024), average settlement ($42.4M in 2024), total settlements ($4.1B in 2024), settlement timing (median 3.2 years filing to hearing in 2024).
  - Analysis of pre-MTD settlements, post-class-certification settlements, etc.
  - Data on 88 settlements in 2024.
- **How to Access:**
  - **Free reports:** Annual and semi-annual reports available for free download from Cornerstone Research website.
  - **Underlying data:** Access to raw settlement data requires engagement with Cornerstone Research or collaboration with Stanford SCAC/SSLA.
  - Not available as a standalone database product to the public.
- **Historical Coverage:** 1996-present (post-PSLRA).
- **Data Format:** PDF reports (free); underlying data likely in Excel/database format (restricted access).
- **Update Frequency:** Annual (full-year review) and semi-annual (midyear update) reports.
- **Cost:** Free for published reports. Data access requires research collaboration or commercial engagement.
- **Known Limitations:**
  - Published reports contain aggregate statistics, not case-level detail.
  - Raw data not publicly downloadable; requires relationship with Cornerstone.
  - Focuses on federal securities class actions only; does not cover state-only filings, derivative suits, or non-securities D&O claims.
  - Settlement amounts only; does not capture defense costs or insurance payments separately.

### 9.2 NERA Economic Consulting Securities Litigation Trends Reports

- **Full Name:** NERA Economic Consulting -- Recent Trends in Securities Class Action Litigation Reports
- **URL:** https://www.nera.com/insights/publications.html
- **What It Contains:**
  - Annual and semi-annual reports on securities class action filing trends, settlement trends, dismissal trends.
  - Proprietary counting methodology that includes: lawsuits alleging federal securities law violations, common law claims (including fiduciary duty breach as in merger objections), foreign/state law claims in federal court.
  - Data on filing volumes, dismissal rates, settlement amounts, case duration.
  - Industry breakdown, geographic distribution, allegation type analysis.
  - D&O Insurance-focused analysis (NERA has a dedicated D&O and Other Coverage Litigation practice).
- **How to Access:**
  - **Free reports:** Available for download from NERA website.
  - **Consulting engagement:** NERA provides settlement analyses, damages calculations, and expert testimony for D&O cases on a project basis.
  - No standalone database product available to the public.
- **Historical Coverage:** Reports typically cover trends over multiple years; NERA has published these reports since the early 2000s.
- **Data Format:** PDF reports.
- **Update Frequency:** Annual (full-year) and semi-annual (midyear) reports.
- **Cost:** Free for published reports; consulting services are fee-based.
- **Known Limitations:**
  - **Important methodology caveat:** NERA counts multiple cases based on same allegations in different circuits as separate filings (adjusted later if consolidated). This means NERA's filing counts differ from SCAC and Cornerstone Research counts -- important for reconciling data across sources.
  - Published reports are aggregate; no case-level data available without consulting engagement.
  - Reports focus on trends, not individual case details for underwriting.

### 9.3 Woodruff Sawyer Databox Reports

- **Full Name:** Woodruff Sawyer D&O Databox Reports and D&O Looking Ahead Guides
- **URL:** https://woodruffsawyer.com/insights/securities-class-action-year-end and https://woodruffsawyer.com/insights/do-looking-ahead-guide
- **What It Contains:**
  - Annual Databox Report: Securities class action filing volumes, settlement data, industry analysis.
  - D&O Looking Ahead Guide (13th annual edition in 2025): Emerging D&O risks, insurance market conditions, litigation trend analysis.
  - Data on: 206 securities class action lawsuits filed in 2024; $4.1B total settlement dollars in 2024 (record).
  - Underwriters Weigh In survey data on D&O market conditions.
  - Sources data from NERA, SCAC/SSLA, FactSet, and SNL.
- **How to Access:** Free download from Woodruff Sawyer website.
- **Historical Coverage:** Annual reports going back 13+ years.
- **Data Format:** PDF reports with charts and tables.
- **Update Frequency:** Annual (Looking Ahead Guide typically September/October; Databox typically Q1 following year).
- **Cost:** Free.
- **Known Limitations:**
  - Curated analysis, not raw data. Cannot perform custom queries or analysis.
  - Primarily designed for insurance broking clients, not underwriting model building.
  - Data sourced from third-party providers (not primary research).

### 9.4 VerdictSearch / ALM Verdict & Settlement Database

- **Full Name:** VerdictSearch (ALM Media)
- **URL:** https://verdictsearch.com/
- **What It Contains:**
  - Large database of jury verdicts, settlements, and arbitration awards across practice areas.
  - Searchable by case type, jurisdiction, amount, parties, attorneys, experts.
  - Covers: securities litigation, corporate governance, fiduciary duty, employment, product liability, medical malpractice, and many other areas.
  - D&O-relevant: Can search for verdicts and settlements involving directors, officers, corporate defendants.
- **How to Access:** Subscription-based web platform. Part of ALM (American Lawyer Media).
- **Historical Coverage:** Data going back decades; comprehensive from approximately 1990s-present.
- **Data Format:** Searchable web database; PDF case reports.
- **Update Frequency:** Regularly updated with new verdicts and settlements.
- **Cost:** Subscription required; pricing varies (typically thousands of dollars annually).
- **Known Limitations:**
  - Relies on voluntary submissions; not comprehensive for all jurisdictions.
  - Settlement data may have reporting bias (larger and more notable cases more likely to be reported).
  - Securities and D&O cases may be underrepresented compared to personal injury.
  - No API for automated data extraction.

---

## 10. SPECIALIZED LITIGATION DATABASES

### 10.1 ClassAction.org Database

- **Full Name:** ClassAction.org Class Action Lawsuit Database
- **URL:** https://www.classaction.org/database
- **What It Contains:**
  - Daily-updated database of proposed class actions filed in federal courts.
  - Coverage includes: consumer protection, product liability, data breach/privacy, employment, securities, corporate misconduct.
  - Lawsuit details, settlement information, filing deadlines.
  - Free weekly newsletter on new cases and settlement deadlines.
- **How to Access:** Free web search; browse by category.
- **Historical Coverage:** Several years of active tracking; older resolved cases may be archived.
- **Data Format:** HTML articles and database entries.
- **Update Frequency:** Daily.
- **Cost:** Free.
- **Known Limitations:**
  - Not a comprehensive legal database; focuses on consumer-facing class actions.
  - Securities/D&O cases are not the primary focus.
  - No API or structured data export.
  - Selection bias toward consumer-interest cases.
  - Limited analytical capabilities; primarily a news/information resource.

### 10.2 Top Class Actions

- **Full Name:** Top Class Actions
- **URL:** https://topclassactions.com/
- **What It Contains:**
  - Legal news source reporting on class action lawsuits, settlements, drug injury lawsuits, product liability.
  - Open settlements list with claim filing information.
  - Lead generation platform for plaintiffs' attorneys.
  - Operating since 2008.
  - Receives tens of thousands of leads per month.
- **How to Access:** Free web browsing.
- **Historical Coverage:** 2008-present.
- **Data Format:** HTML articles; no structured database.
- **Update Frequency:** Daily reporting.
- **Cost:** Free.
- **Known Limitations:**
  - Primarily a news/media site, not a structured database.
  - Focus on consumer class actions and mass torts; limited securities/D&O coverage.
  - No API or data export.
  - Not suitable as a primary data source for underwriting analytics.

### 10.3 Consumer Action Class Action Database

- **Full Name:** Consumer Action Class Action Database
- **URL:** https://www.consumer-action.org/lawsuits
- **What It Contains:**
  - Listing of notable class actions: sortable by status (open to claims, pending, closed).
  - Calendar of upcoming claim deadlines.
  - Consumer-focused class actions.
- **How to Access:** Free web browsing with sortable/searchable interface.
- **Historical Coverage:** Several years of tracked cases.
- **Data Format:** HTML database; sortable table.
- **Update Frequency:** Regular updates.
- **Cost:** Free.
- **Known Limitations:**
  - Consumer-focused; minimal securities/D&O content.
  - No API or bulk data access.
  - Not comprehensive; curated selection of notable cases.

### 10.4 NAAG Multistate Settlements Database

- **Full Name:** National Association of Attorneys General (NAAG) Multistate Settlements Database
- **URL:** https://www.naag.org/news-resources/research-data/multistate-settlements-database/
- **What It Contains:**
  - Multistate settlements between state attorneys general and private entities from early 1980s to present.
  - Filterable by: topic, year, state, issue, company, keyword.
  - Settlement documents (where available).
  - Covers: consumer protection, antitrust, environmental, financial services, healthcare, technology sectors.
- **How to Access:** Free searchable web database. Also see StateAG.org by Prof. Paul Nolette (Marquette) for complementary AG activity data.
- **Historical Coverage:** Early 1980s to present.
- **Data Format:** Searchable HTML table; PDF settlement documents.
- **Update Frequency:** Regularly updated.
- **Cost:** Free.
- **Known Limitations:**
  - Multistate AG actions only; does not cover private class actions or federal enforcement.
  - Settlement document availability varies.
  - No API or structured data export.
  - AG enforcement is one component of D&O risk but not the primary driver.

### 10.5 NAAG State Antitrust Litigation and Settlement Database

- **Full Name:** NAAG State Antitrust Litigation and Settlement Database
- **URL:** https://www.naag.org/issues/antitrust/state-antitrust-litigation-and-settlement-database/
- **What It Contains:**
  - Criminal and civil antitrust cases brought by state attorneys general from 1990-present.
  - Case details, settlements, and outcomes.
- **How to Access:** Free searchable web database.
- **Historical Coverage:** 1990-present.
- **Data Format:** Searchable HTML interface.
- **Update Frequency:** Regular.
- **Cost:** Free.
- **Known Limitations:**
  - State AG antitrust actions only; does not cover federal DOJ antitrust or private antitrust class actions.
  - No bulk data access.

---

## 11. GOVERNMENT ENFORCEMENT & FRAUD DATABASES

### 11.1 DOJ False Claims Act / Qui Tam Data

- **Full Name:** U.S. Department of Justice, Civil Division -- False Claims Act Statistics
- **URL:** https://www.justice.gov/civil/false-claims-act
- **What It Contains:**
  - Annual FCA statistics: total recoveries, number of new civil cases, new qui tam cases, settlements and judgments.
  - FY2025 records: $6.8B in recoveries (all-time high); 1,297 qui tam suits filed (record); 401 government investigations opened.
  - Cumulative: $85B+ in FCA recoveries since 1986 amendments.
  - Industry breakdown: healthcare ($5.7B in FY2025), government contracting, cybersecurity, pandemic-related, trade compliance.
  - D&O relevance: Officers and directors can face personal liability and may be named in FCA suits. FCA claims are a significant D&O insurance trigger.
  - Tracked by Taxpayers Against Fraud (TAF) at taf.org/doj-trendlines/ with visualization of DOJ trendlines.
- **How to Access:**
  - **DOJ press releases and annual reports:** Free download from DOJ website.
  - **TAF DOJ Trendlines:** Free interactive visualization.
  - **Individual cases:** Accessible through PACER (federal court filings); many qui tam cases are initially sealed.
  - No structured database or API for FCA case data from DOJ.
- **Historical Coverage:** 1986-present (modern FCA); statistics published annually.
- **Data Format:** PDF reports; HTML press releases.
- **Update Frequency:** Annual (DOJ publishes FCA statistics each fiscal year).
- **Cost:** Free.
- **Known Limitations:**
  - DOJ publishes aggregate statistics, not case-level data.
  - Individual qui tam cases are often sealed for years, making real-time tracking impossible.
  - No structured database; data must be manually extracted from annual reports or found through PACER.
  - FCA-specific D&O exposure data (what portion involves officer/director personal liability) not separately reported.

### 11.2 FTC Cases and Proceedings / Competition Enforcement Database

- **Full Name:** Federal Trade Commission Cases and Proceedings / Competition Enforcement Database
- **URL:** https://www.ftc.gov/legal-library/browse/cases-proceedings and https://www.ftc.gov/competition-enforcement-database
- **What It Contains:**
  - All FTC enforcement actions: antitrust/competition, consumer protection, privacy.
  - Case documents, complaints, orders, settlements.
  - Competition Enforcement Database: searchable index of FTC competition enforcement actions.
  - D&O relevance: FTC actions against companies for anticompetitive conduct, deceptive practices, privacy violations; officers may be individually named.
  - FTC Data Sets available at ftc.gov/policy-notices/open-government/data-sets.
- **How to Access:** Free web browsing; searchable databases. Data sets available for download. No API.
- **Historical Coverage:** Decades of case history; Competition Enforcement Database covers major actions comprehensively.
- **Data Format:** HTML web interface; PDF case documents; downloadable data sets.
- **Update Frequency:** As new actions are filed/resolved.
- **Cost:** Free.
- **Known Limitations:**
  - Federal enforcement actions only; no private litigation data.
  - No structured API.
  - D&O-specific exposure not separately flagged.

### 11.3 DOJ Antitrust Division Data

- **Full Name:** U.S. Department of Justice, Antitrust Division
- **URL:** https://www.justice.gov/atr and https://catalog.data.gov/dataset?publisher=Antitrust+Division
- **What It Contains:**
  - Index of select antitrust cases and documents.
  - Statistics on Sherman Act violations, workload statistics, appellate cases dating back to 1993.
  - Case filings, trial memoranda, competitive impact statements.
  - D&O relevance: Antitrust criminal indictments can name individual officers/directors; civil antitrust enforcement creates derivative and class action exposure.
- **How to Access:** Free web access; data sets on Data.gov. Lexis provides DOJ/FTC Antitrust Case Tracker.
- **Historical Coverage:** Data sets from 1993; case documents going back further.
- **Data Format:** HTML, PDF, data sets on Data.gov (various formats).
- **Update Frequency:** Ongoing as cases are filed.
- **Cost:** Free.
- **Known Limitations:**
  - Federal DOJ actions only.
  - Data sets on Data.gov may be outdated or incomplete.
  - Private follow-on antitrust class actions not tracked here.

### 11.4 EPA Enforcement (ECHO) and Environmental Litigation

- **Full Name:** EPA Enforcement and Compliance History Online (ECHO)
- **URL:** https://echo.epa.gov/ and https://www.epa.gov/enforcement
- **What It Contains:**
  - 800,000+ regulated facilities with compliance and enforcement data.
  - Civil enforcement cases in Integrated Compliance Information System (ICIS).
  - Criminal cases in Summary of Criminal Prosecutions database.
  - Cases searchable by statute: CAA, CWA, RCRA, CERCLA, TSCA, EPCRA, FIFRA, SDWA, MPRSA.
  - Significant civil and cleanup cases and settlements from 1998 onward.
  - D&O relevance: Environmental criminal liability (knowing violations) can attach to corporate officers; environmental remediation costs and penalties are major D&O/corporate insurance triggers.
- **How to Access:**
  - **ECHO web interface:** Free searchable database.
  - **EPA Cases and Settlements:** Filterable by statute and date.
  - **Criminal Case Search:** Concluded criminal enforcement cases.
  - **ECHO APIs:** Available for programmatic access to facility data.
- **Historical Coverage:** Civil cases from 1998; criminal cases for concluded investigations; facility data comprehensive.
- **Data Format:** Web interface; API; downloadable data sets.
- **Update Frequency:** Regularly updated.
- **Cost:** Free.
- **Known Limitations:**
  - EPA enforcement data, not private environmental litigation (citizen suits, toxic tort class actions tracked separately in PACER/state courts).
  - Individual officer/director liability not specifically flagged in ECHO.
  - Criminal prosecutions database covers only concluded cases.

### 11.5 CFPB Enforcement Actions and Consumer Complaint Database

- **Full Name:** Consumer Financial Protection Bureau (CFPB) Enforcement Actions / Consumer Complaint Database
- **URLs:** https://www.consumerfinance.gov/enforcement/actions/ and https://www.consumerfinance.gov/data-research/consumer-complaints/search/
- **What It Contains:**
  - **Enforcement Actions:** Court documents and materials for CFPB enforcement actions against entities/persons. Covers violations of consumer financial protection laws.
  - **Consumer Complaint Database:** Public database of complaints about consumer financial products/services sent to companies for response.
  - **Enforcement by the Numbers:** Summary statistics of enforcement activity.
  - D&O relevance: CFPB enforcement actions against financial services companies create significant D&O liability exposure; consumer complaints can be early warning signals of emerging litigation.
- **How to Access:**
  - Free web access. Complaint database is searchable and downloadable.
  - Complaint data available through API (compliant with OPEN Government Data Act).
  - Enforcement actions browsable with full case documents.
- **Historical Coverage:** CFPB established 2011; data from 2011-present.
- **Data Format:** Web interface; downloadable CSV; API.
- **Update Frequency:** Continuous for complaints; as-needed for enforcement actions.
- **Cost:** Free.
- **Known Limitations:**
  - Complaint data reflects consumer submissions, not adjudicated violations.
  - Enforcement coverage limited to CFPB's jurisdiction (consumer financial products/services).
  - CFPB's future uncertain depending on political environment and funding battles.

---

## 12. ARBITRATION DATABASES

### 12.1 FINRA Arbitration Awards Online

- **Full Name:** FINRA Arbitration Awards Online (AAO)
- **URL:** https://www.finra.org/arbitration-mediation/arbitration-awards
- **What It Contains:**
  - Searchable database of arbitration awards from FINRA, historical NASD, NYSE, AMEX, PHLX, and MSRB.
  - Searchable by: Case ID, keyword, name, date range, forum, document type, panel composition.
  - Awards viewable online as text-searchable PDFs.
  - D&O relevance: Securities broker-dealer disputes often involve officer/director liability; FINRA arbitration data provides insight into financial industry disputes that may trigger D&O claims.
  - 2024 FINRA statistics available showing case volumes, resolution rates, arbitrator information.
- **How to Access:**
  - Free web-based search at FINRA website, available 7 days/week.
  - Awards downloadable as text-searchable PDFs.
  - Dispute resolution statistics available separately.
  - **Dispute Resolution Portal (DR Portal):** For case participants to manage case information (not general public access).
- **Historical Coverage:** Historical awards from NASD (pre-2007) onward; comprehensive FINRA awards from 2007-present.
- **Data Format:** Searchable web interface; PDF awards.
- **Update Frequency:** Updated as awards are issued.
- **Cost:** Free.
- **Known Limitations:**
  - Individual awards must be searched one at a time; no bulk download capability.
  - Only contains final awards, not interim proceedings, briefs, or discovery.
  - Many cases settle before an award is issued and therefore are not in the database.
  - No API for automated data extraction.
  - Award PDFs may have inconsistent formatting, making text extraction difficult.
  - Not all party identifying information may be included in published awards.

### 12.2 AAA (American Arbitration Association) Award Search

- **Full Name:** AAA Award Search / AAA Research, Data & Analytics
- **URL:** https://apps.adr.org/AwardSearch/faces/awardSearch.jsf and https://www.adr.org/research
- **What It Contains:**
  - Searchable database of AAA commercial arbitration awards.
  - Awards are redacted (party names and witness names removed).
  - 13,000+ B2B cases filed in 2024.
  - Research data showing resolution times, industry trends, outcomes across commercial disputes.
  - D&O relevance: Employment, commercial contract, and corporate governance disputes often go to AAA arbitration; outcomes inform D&O exposure estimates.
- **How to Access:**
  - AAA Award Search tool available online.
  - AAA Research, Data & Analytics reports available at adr.org/research.
  - Awards in electronic databases (LexisNexis, others) with party names redacted.
- **Historical Coverage:** Varies; award database goes back years (specific start date not publicly stated).
- **Data Format:** Web search interface; PDF awards (redacted).
- **Update Frequency:** As awards are finalized.
- **Cost:** Free to search.
- **Known Limitations:**
  - **Party names redacted** from publicly available awards -- severely limits utility for D&O underwriting (cannot link awards to specific companies/officers).
  - Arbitration is private; not all awards are published.
  - Parties must approve publication before AAA makes awards public.
  - No bulk download or API.
  - Limited to AAA-administered cases only.

### 12.3 JAMS Consumer Arbitration Data

- **Full Name:** JAMS Consumer Case Information
- **URL:** https://www.jamsadr.com/consumercases
- **What It Contains:**
  - Information on consumer arbitrations administered by JAMS, completed in last 5 years.
  - Data includes: non-consumer party name, result, JAMS usage history by non-consumer party.
  - Updated quarterly.
- **How to Access:** Free web access.
- **Historical Coverage:** Last 5 years (rolling window).
- **Data Format:** Web interface.
- **Update Frequency:** Quarterly.
- **Cost:** Free.
- **Known Limitations:**
  - Consumer arbitrations only (not commercial/corporate governance).
  - Very limited D&O relevance.
  - No API or bulk export.
  - Five-year rolling window only.

---

## 13. INTERNATIONAL / FOREIGN COURT DATABASES

### 13.1 United Kingdom

**13.1.1 London Commercial Court / Business and Property Courts**

- **Full Name:** Commercial Court, Business and Property Courts, High Court of Justice
- **URL:** https://www.judiciary.uk/courts-and-tribunals/business-and-property-courts/commercial-court/
- **What It Contains:**
  - Commercial disputes, many international. Includes securities litigation, shareholder disputes, corporate governance claims.
  - UK securities litigation is rising due to increased litigation funding, growing shareholder activism, and strategic use of litigation for corporate governance.
- **How to Access:**
  - HM Courts & Tribunals Service (HMCTS) online services.
  - Case information through Find a Court Judgment service: caselaw.nationalarchives.gov.uk.
  - Third-party litigation search services (GlobalX, CRO) provide corporate and individual litigation searches covering England and Wales at the High Court.
- **Historical Coverage:** Court judgments increasingly available online; comprehensive from approximately 2010-present.
- **Data Format:** PDF judgments; web search interfaces.
- **Update Frequency:** As judgments are published.
- **Cost:** Official services generally free; third-party services paid.
- **Known Limitations:**
  - No centralized API or bulk data access for court records.
  - Many cases settle privately and do not generate public judgments.
  - Pre-2010 electronic records may be limited.
  - Third-party litigation search services charge per-search fees.

**13.1.2 UK Companies House**

- **URL:** https://find-and-update.company-information.service.gov.uk/
- **What It Contains:** Company registration data, filing history, accounts, officers, charges.
- **D&O Relevance:** Officer/director appointment/resignation data, disqualification records, company insolvency data.
- **How to Access:** Free API available. Bulk data downloads available.
- **Cost:** Free.
- **Known Limitations:** Not a litigation database; limited to corporate registration data. However, director disqualification records are valuable for D&O risk assessment.

### 13.2 Canada

**13.2.1 Ontario Securities Commission / Capital Markets Tribunal**

- **Full Name:** Capital Markets Tribunal (established under Securities Commission Act, 2021)
- **URL:** https://www.capitalmarketstribunal.ca/en
- **What It Contains:**
  - Hearings under the Ontario Securities Act and Commodity Futures Act.
  - Determinations, orders, and tribunal decisions on securities regulatory matters.
- **How to Access:** Web access for published decisions.
- **Historical Coverage:** Current tribunal from 2021; OSC decisions available going back further.
- **Data Format:** Web interface; PDF decisions.
- **Cost:** Free.
- **Known Limitations:**
  - Regulatory enforcement actions only; not private class actions.
  - Ontario-focused; other provinces have separate regulators.

**13.2.2 Canadian Class Action Databases**

- **Ontario Class Action Database:** Created by Law Commission of Ontario as part of its Class Action Project (2019). Tracks class action litigation in Ontario.
- **Canadian Bar Association (CBA) Class Action Database:** Voluntary initiative relying on lawyer submissions. URL: https://cba.org/resources/class-action-database/
  - Coverage: National but voluntary/incomplete.
- **Securities Litigation Blog (Osler):** https://www.securitieslitigation.blog/ -- Tracks Canadian securities litigation decisions.
- **Known Limitations:**
  - CBA database is voluntary and not comprehensive.
  - No unified Canadian national class action database.
  - Ontario database focuses on Ontario court proceedings.
  - Canadian securities class actions are relatively infrequent compared to the U.S.

### 13.3 Australia

**13.3.1 Federal Court of Australia -- Class Actions List**

- **Full Name:** Federal Court of Australia, Class Actions
- **URL:** https://www.fedcourt.gov.au/law-and-practice/class-actions/class-actions
- **What It Contains:**
  - List of all current first instance class actions in the Federal Court.
  - Case names, parties, court information.
  - Includes: shareholder class actions, managed investment scheme class actions, cartel class actions.
  - Last updated December 5, 2025.
- **How to Access:** Free web access; publicly available list.
- **Historical Coverage:** Current cases; historical cases available through Federal Court judgment database.
- **Data Format:** HTML list; PDF judgments.
- **Update Frequency:** Regular updates (approximately monthly).
- **Cost:** Free.
- **Known Limitations:**
  - Only current cases listed; resolved/historical cases must be searched separately.
  - Limited structured data; primarily a case list, not an analytics database.
  - Does not include Victorian or NSW Supreme Court class actions (significant volume).
  - Australia has relatively few securities class actions compared to the U.S.

**13.3.2 ASIC (Australian Securities and Investments Commission)**

- **URL:** https://www.asic.gov.au/
- **What It Contains:** Regulatory enforcement actions, company register data, financial services licensing.
- **D&O Relevance:** Officer banning orders, company director disqualifications, enforcement against companies for market misconduct.
- **How to Access:** Free web access; ASIC Connect for company searches.
- **Known Limitations:** Regulatory data, not private litigation.

### 13.4 European Union

**13.4.1 CMS European Class Actions Reports**

- **Full Name:** CMS European Class Actions Reports (annual)
- **URL:** https://cms.law/en/int/publication/cms-european-class-action-report-2024
- **What It Contains:**
  - Annual tracking of class action filings across Europe.
  - Statistics: 133 claims filed in 2023 (up from 55 in 2018).
  - By claim type: Financial Products/Securities (31%), Competition (26%), Products Liability (24%).
  - By country: UK, Netherlands, Germany, and Portugal account for 78% of all European class actions.
  - Analysis of EU Directive 2020/1828 on representative actions.
- **How to Access:** Free PDF download from CMS website.
- **Historical Coverage:** Annual reports from at least 2018.
- **Data Format:** PDF reports.
- **Update Frequency:** Annual.
- **Cost:** Free.
- **Known Limitations:**
  - Report-level data only, not case-level database.
  - EU collective redress framework still evolving; historical data reflects a rapidly changing landscape.
  - Cross-border class action mechanisms are new (EU Directive transposition deadline was June 2023).

**13.4.2 EU Qualified Entities Database**

- **What It Contains:** Publicly accessible database of all designated qualified entities authorized to bring representative actions under EU framework.
- **How to Access:** European Commission website.
- **D&O Relevance:** Identifies entities that can bring collective actions that may name officers/directors.
- **Known Limitations:** Lists entities, not cases or outcomes.

---

## 14. SENTENCING & CRIMINAL JUSTICE DATABASES

### 14.1 U.S. Sentencing Commission (USSC) Datafiles

- **Full Name:** United States Sentencing Commission, Commission Datafiles
- **URL:** https://www.ussc.gov/research/datafiles/commission-datafiles
- **What It Contains:**
  - **Individual Datafiles:** Annual data on all felony and Class A misdemeanor cases where an individual was sentenced in federal court. 2023 datafile contains 64,124 cases.
  - Variables: primary offense, applicable Guidelines sentencing range, actual sentence, departure type, criminal history, offender demographics.
  - **Economic Crime Type Variable:** 29 specific offense categories under guideline section 2B1.1, covering fraud, embezzlement, forgery, theft, and other economic crimes.
  - **Interactive Data Analyzer:** Online tool for querying sentencing data.
  - **Sourcebook of Federal Sentencing Statistics:** Annual compilation.
  - White collar crime sentencing data: median prison term of 6 months, average 19 months (FY1986-FY2024).
- **How to Access:**
  - **Free download** from USSC website (Commission Datafiles page).
  - **Interactive Data Analyzer** available online.
  - **Sourcebooks** available as PDF downloads.
  - Data excludes individual identifiers.
- **Historical Coverage:** Datafiles from FY1984-present; comprehensive from FY1991+.
- **Data Format:** Data files (SAS, SPSS, Stata formats historically; tab-delimited also available); PDF sourcebooks.
- **Update Frequency:** Annual (typically released 6-12 months after fiscal year end).
- **Cost:** Free.
- **Known Limitations:**
  - Individual identifiers removed, so cannot directly link to specific D&O cases.
  - Economic crime is a broad category; extracting D&O-specific corporate fraud sentencing requires careful coding.
  - Covers federal sentencing only (state prosecutions not included).
  - Data lags 6-12 months behind actual sentencing.
  - Cannot determine whether sentenced individuals were officers/directors without cross-referencing.

### 14.2 Bureau of Justice Statistics (BJS)

- **Full Name:** Bureau of Justice Statistics, Office of Justice Programs, U.S. DOJ
- **URL:** https://bjs.ojp.gov/ and https://bjs.ojp.gov/taxonomy/term/financial-fraud
- **What It Contains:**
  - Supplemental Fraud Survey (SFS): Data on personal financial fraud experiences.
  - Financial Fraud in the United States reports.
  - Identity theft and financial fraud statistics.
  - National Crime Victimization Survey (NCVS) data.
  - Archived data at National Archive of Criminal Justice Data (NACJD).
- **How to Access:**
  - Free download of published reports from BJS.
  - Raw datasets downloadable through NACJD for secondary analysis.
  - Interactive tools on BJS website.
- **Historical Coverage:** Varies by survey; NCVS data from 1973+.
- **Data Format:** Reports (PDF); datasets (various statistical software formats via NACJD).
- **Update Frequency:** Varies by publication; major surveys every few years.
- **Cost:** Free.
- **Known Limitations:**
  - **BJS does NOT have a dedicated corporate fraud database.** Data focuses on individual victimization, not corporate officer/director prosecutions.
  - Very limited direct D&O relevance.
  - Best used for contextual background on fraud trends, not specific case data.

### 14.3 TRAC (Transactional Records Access Clearinghouse) -- Syracuse University

- **Full Name:** TRAC Reports, Syracuse University
- **URL:** https://tracreports.org/
- **What It Contains:**
  - Analysis of federal enforcement data, including prosecution of white-collar crimes.
  - Tracking of federal prosecution rates by offense type, district, and time period.
  - Reports on declining or increasing enforcement emphasis areas.
- **How to Access:** Web access; some reports free, some subscription-based.
- **Historical Coverage:** Decades of federal enforcement tracking.
- **Data Format:** Web reports, interactive tools.
- **Cost:** Mixed (some free reports, subscription for full access).
- **Known Limitations:**
  - Analytical/reporting tool, not a case-level database.
  - White-collar crime is one of many enforcement areas covered.
  - Subscription needed for detailed data access.

---

## 15. ACADEMIC & RESEARCH DATABASES

### 15.1 ICPSR (Inter-university Consortium for Political and Social Research)

- **URL:** https://www.icpsr.umich.edu/
- **What It Contains:** Archive of social science research data including FJC Integrated Database, USSC data, and various judicial/legal datasets.
- **How to Access:** Academic institutional membership; some datasets freely available.
- **D&O Relevance:** Access point for FJC, USSC, and other government datasets useful for longitudinal analysis.
- **Cost:** Free for members of participating institutions; individual memberships available.

### 15.2 WRDS (Wharton Research Data Services)

- **URL:** https://wrds-www.wharton.upenn.edu/
- **What It Contains:** Platform providing access to: FJC Integrated Database, Audit Analytics modules, CRSP (stock data), Compustat (financial data), and many others.
- **How to Access:** Academic institutional subscription.
- **D&O Relevance:** Can combine litigation data (FJC, Audit Analytics) with financial data (Compustat, CRSP) for empirical analysis of D&O risk factors.
- **Cost:** Academic institutional subscription (typically $10,000-$50,000+/year depending on modules).
- **Known Limitations:** Academic use only; licensing restrictions on commercial use of many datasets.

---

## 16. SUPPLEMENTAL INTELLIGENCE SOURCES

### 16.1 The D&O Diary

- **Full Name:** The D&O Diary, by Kevin LaCroix (RT ProExec)
- **URL:** https://www.dandodiary.com/
- **What It Contains:**
  - Commentary and analysis on D&O liability developments.
  - Regular posts on: securities litigation, shareholder derivative suits, merger litigation, ERISA litigation, SEC enforcement, D&O insurance market trends.
  - Aggregates data from SCAC, NERA, Cornerstone, ISS, and other sources.
  - Tracks notable D&O cases, settlements, and coverage disputes.
- **How to Access:** Free web access; email subscription.
- **Historical Coverage:** Blog running since approximately 2006.
- **Data Format:** Blog posts (HTML).
- **Cost:** Free.
- **Known Limitations:**
  - Commentary/analysis, not structured data.
  - Curated selection of topics, not comprehensive database.
  - Cannot be queried programmatically for data extraction.
  - **However, this is an invaluable qualitative intelligence source for D&O underwriting context.**

### 16.2 D&O Discourse

- **Full Name:** D&O Discourse, by Doug Greene
- **URL:** https://www.dandodiscourse.com/
- **What It Contains:** Analysis of securities and corporate governance litigation, class certification decisions, and D&O coverage issues.
- **How to Access:** Free web access.
- **Cost:** Free.
- **Known Limitations:** Same as D&O Diary -- commentary, not structured data.

### 16.3 Moody's / EDF-X Underwriting Solutions

- **URL:** https://www.moodys.com/web/en/us/solutions/underwriting.html
- **What It Contains:**
  - EDF-X (Expected Default Frequency) Early Warning System for bankruptcy risk assessment.
  - Underwriting analytics integrating financial risk data with litigation exposure.
  - D&O series reports on evolving boardroom risks.
- **How to Access:** Commercial subscription / enterprise API.
- **Cost:** Enterprise pricing.
- **D&O Relevance:** Links financial health (bankruptcy probability) to D&O claims frequency.

### 16.4 Patent Litigation Databases (for IP-related D&O exposure)

**16.4.1 USPTO PTAB Dashboard and Open Data Portal**

- **URL:** https://www.uspto.gov/dashboard/ptab/ and https://data.uspto.gov/
- **What It Contains:** PTAB operations data, inter partes review (IPR) and post-grant review proceedings, patent appeal outcomes.
- **API:** https://data.uspto.gov/apis/ptab-trials/search-proceedings (free, no authentication).
- **D&O Relevance:** Officer decisions on patent prosecution/enforcement strategy that lead to failed IPR defenses or large patent judgments.

**16.4.2 Docket Navigator**

- **URL:** https://docketnavigator.com/
- **What It Contains:** Every significant order for every patent case in every U.S. district court, plus PTAB and ITC cases.
- **How to Access:** Subscription-based.
- **Cost:** Paid subscription.

**16.4.3 RPX Insight**

- **URL:** https://insight.rpxcorp.com/
- **What It Contains:** Patent litigation data for District Courts, PTAB, ITC, and Federal Circuit. Advanced search by jurisdiction, parties, patent owners, sectors.
- **How to Access:** Subscription-based.
- **Cost:** Paid.

### 16.5 SEC.gov Litigation Releases and Administrative Proceedings (Direct Access)

- **URL:** https://www.sec.gov/litigation/litreleases.htm and https://www.sec.gov/litigation/admin.htm
- **What It Contains:** Direct listings of all SEC litigation releases and administrative proceedings.
- **How to Access:** Free web browsing; RSS feeds available.
- **Cost:** Free.
- **Known Limitations:** No structured search or export beyond basic chronological listing.

---

## 17. D&O ANALYTICS: MOTION TO DISMISS, CLASS CERTIFICATION, LEAD PLAINTIFF & FEE DATA

### 17.1 Motion to Dismiss Success Rates

**Available Data Sources:**
- **Cornerstone Research** annual reports: Track dismissal rates as part of securities class action settlement analysis.
- **NERA Economic Consulting:** 2024 data shows 124 securities class action dismissals (up 29% from 96 in 2023).
- **Bloomberg Law Judge Analytics:** Motion to dismiss ruling patterns by judge for federal district courts.
- **Lex Machina:** Practice-area-specific motion outcome analytics.
- **Woodruff Sawyer / D&O Diary:** Report on dismissal trends.

**Key Statistics (2024):**
- Life sciences companies: MTD granted in 59% of cases (24/41 decisions).
- Non-U.S. companies: MTD granted in entirety in 68% of cases (15/22 decisions); however, many were without prejudice.
- Primary dismissal ground: failure to allege actionable misstatement/omission.
- Secondary ground: failure to allege strong inference of scienter.
- Dismissals in first half of 2025: up from 2024.

**How to Build a Systematic MTD Dataset:**
- Combine FJC Integrated Database (disposition codes for dismissals) with PACER docket data (identify MTD filings and rulings).
- Use Lex Machina or Bloomberg Law for pre-built analytics by judge and case type.
- Cross-reference with SCAC/SSLA data for securities-specific MTD rates.

### 17.2 Class Certification Rates

**Available Data Sources:**
- **Bloomberg Law Judge Analytics:** Class certification ruling data by judge.
- **Lex Machina:** Class certification analytics by practice area and jurisdiction.
- **Federal Judicial Center studies:** Published reports on class certification rates.
- **Cornerstone Research:** Reports on settlement differences between certified and uncertified classes.

**Key Statistics:**
- Post-Halliburton II (2014): Increased work required at class certification stage due to price impact defense.
- Class certification is rarely denied in securities fraud cases where the case survives MTD, though defendants increasingly use Halliburton II to challenge the fraud-on-the-market presumption at certification.
- For D&O underwriting: cases reaching class certification are significantly more expensive to resolve than those resolved pre-certification.

### 17.3 Lead Plaintiff Data

**Available Data Sources:**
- **SCAC/SSLA:** Track lead plaintiff identity and type (individual vs. institutional).
- **NERA Economic Consulting:** Reports on lead plaintiff trends.
- **Academic research** (available through SSRN, law reviews).

**Key Statistics:**
- Pre-PSLRA (1995): Professional individual plaintiffs dominated.
- By 2002: 27.2% of cases led by pension funds.
- 2010-2012: 40% of cases led by pension funds.
- Currently: Institutional investors appointed lead plaintiffs in roughly 50% of newly filed federal securities class actions.
- Institutional-led cases: Settle for more money and pay lower attorneys' fees.
- **Source:** University of Pennsylvania Law School empirical study; GFOA (Government Finance Officers Association) publications.

### 17.4 Attorney Fee Data in D&O Cases

**Available Data Sources:**
- **Academic studies:**
  - Columbia Law Review: "Is the Price Right? An Empirical Study of Fee-Setting in Securities Class Actions" -- comprehensive data on 1,719 cases filed 2005-2016.
  - Michigan Law Review: "Working Hard or Making Work? Plaintiffs' Attorneys Fees in Securities Fraud Class Actions."
  - Eisenberg & Miller (2010): "Attorneys' Fees and Expenses in Class Action Settlements: 1993-2008" (published by Federal Judicial Center/Administrative Office of U.S. Courts).
- **VerdictSearch/ALM:** Fee award data in settlements.
- **PACER filings:** Fee petitions are public filings in class action cases.

**Key Statistics:**
- Federal judges typically award contingency fees of 20-25% of settlement.
- Larger settlements push percentage lower.
- Mean attorney hours: 72,800 hours for cases with class certification filing vs. 13,000 hours without.
- Post-Halliburton II: Significant increase in attorney hours for cases with multiple lead counsel.
- Fee percentages vary by circuit and subject matter; securities cases tend to have lower percentages than other class actions.
- Range: 20-35% for securities class action lawyer fees.

### 17.5 Settlement Amount Databases -- Summary

| Source | Coverage | Access | Cost |
|--------|----------|--------|------|
| SCAC/SSLA | Federal securities class actions, 1996-present | Web/license | Free (basic) / Paid (license) |
| Cornerstone Research Reports | Post-PSLRA settlements | Free reports / restricted data | Free (reports) |
| NERA Reports | Securities class action settlements | Free reports | Free |
| ISS SCAS RecoverMax | 14,000+ cases | Commercial subscription | Paid |
| Advisen Loss Data | Public & private D&O events | Commercial subscription | Paid (high) |
| Audit Analytics | SEC-disclosed litigation | Commercial / academic | Paid |
| VerdictSearch | Cross-practice verdicts & settlements | Subscription | Paid |
| Woodruff Sawyer Databox | Annual settlement analysis | Free reports | Free |

**Top Securities Class Action Settlements (for reference / benchmarking):**
- Alibaba: $433.5M (announced ~2025, pending approval)
- General Electric: $362.5M (announced ~2025, pending approval)
- Grab Holdings: $80M (2025)
- Record total settlement year: $4.1B in 2024 (per Woodruff Sawyer)
- Median settlement 2024: $14M (per Cornerstone)
- Average settlement 2024: $42.4M (per Cornerstone)

---

## APPENDIX A: RECOMMENDED DATA ARCHITECTURE FOR D&O UNDERWRITING SYSTEM

Based on the inventory above, a comprehensive D&O underwriting system should integrate the following tiers:

### Tier 1: Core Data Sources (Must-Have)
1. **Stanford SCAC / SSLA** -- Securities class action filings, outcomes, settlements (commercial license)
2. **Advisen / Zywave Loss Data** -- D&O-specific loss events for both public and private companies
3. **PACER / CourtListener RECAP** -- Federal court docket and document data
4. **SEC EDGAR** -- Enforcement actions, litigation releases, company filings
5. **FJC Integrated Database** -- Federal case-level quantitative data
6. **Cornerstone Research / NERA Reports** -- Settlement and filing trend benchmarks

### Tier 2: Enhanced Analytics Sources (High Value)
7. **Lex Machina** or **Bloomberg Law** -- Litigation analytics (judge behavior, motion outcomes)
8. **UniCourt** or **Trellis** -- State court data integration
9. **Audit Analytics** -- Restatement, AAER, and financial misconduct data
10. **NYU SEED** -- SEC enforcement action tracking
11. **USSC Datafiles** -- White-collar sentencing data

### Tier 3: Specialized / Supplemental Sources
12. **Delaware Chancery Court** -- Corporate governance litigation
13. **NYSCEF** -- NY commercial litigation
14. **FINRA Arbitration Awards** -- Securities arbitration outcomes
15. **EPA ECHO** -- Environmental enforcement
16. **DOJ FCA Statistics / TAF Trendlines** -- False Claims Act exposure
17. **FTC Competition Enforcement Database** -- Antitrust enforcement
18. **CFPB Enforcement** -- Consumer financial protection
19. **JPML MDL data** -- Multidistrict litigation tracking
20. **CMS European Class Actions Reports** -- International exposure

### Tier 4: Qualitative Intelligence
21. **The D&O Diary** -- Industry commentary and case tracking
22. **Woodruff Sawyer Looking Ahead / Databox** -- Market condition reports
23. **D&O Discourse** -- Class certification and coverage analysis
24. **WTW, Aon, Marsh D&O reports** -- Broker market reports

---

## APPENDIX B: KEY DATA GAPS AND CHALLENGES

1. **State court data remains the largest gap.** Most D&O litigation beyond securities class actions (derivative suits, fiduciary duty claims, insurance coverage disputes) is filed in state court. State court data is fragmented across 50+ systems with varying quality, coverage, and accessibility. Delaware and New York prohibit data mining. Third-party aggregators (UniCourt, Trellis) are the best current option but still have gaps.

2. **Settlement confidentiality.** Many D&O settlements are reached under confidentiality agreements, meaning the actual amounts are never publicly disclosed. The observable settlement data (SCAC/SSLA, Cornerstone) represents a biased sample of publicly disclosed settlements.

3. **Defense cost data is essentially unavailable.** D&O policies typically cover defense costs in addition to settlements/judgments, but defense cost data is not publicly reported and cannot be obtained from court records. Advisen's loss data is the closest proxy but still limited.

4. **Private company D&O data is extremely sparse.** Most databases focus on public companies. Private company D&O claims are largely invisible in public data sources. Advisen's Private D&O database is one of few sources.

5. **Sealed documents.** Many critical filings in D&O cases (settlement agreements, insurance coverage details, mediation briefs) are filed under seal and inaccessible.

6. **Entity resolution.** Matching parties across databases (PACER, SCAC, SEC EDGAR, Advisen) requires sophisticated entity resolution because company names, officer names, and case identifiers are not standardized.

7. **International data.** Cross-listed company exposure in non-U.S. jurisdictions is poorly tracked. EU collective redress is still nascent, and UK/Canadian/Australian databases lack the depth of U.S. sources.

8. **ERISA litigation tracking.** There is no dedicated ERISA litigation database. ERISA fiduciary breach suits must be found through general federal court databases (PACER, FJC) using nature-of-suit codes and keyword searches.

9. **Merger objection litigation tracking.** While SCAC/NERA track these as part of their broader securities counts, no dedicated merger objection database exists. The D&O Diary and Cornerstone Research are the best sources for analysis of this specific claim type.

10. **Shareholder derivative suit data.** Derivative suits are particularly difficult to track because they may be filed in state or federal court, often settle through corporate governance reforms rather than monetary payments, and settlement terms are frequently confidential.

---

*This inventory reflects data source availability as of February 2026. Data sources, pricing, coverage, and access methods are subject to change. Users should verify current terms directly with each provider before building data integrations.*
