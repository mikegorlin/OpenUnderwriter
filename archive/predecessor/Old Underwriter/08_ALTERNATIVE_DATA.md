# SECTION F: ALTERNATIVE DATA & EARLY WARNING
## 97 Checks | Load when: Any elevated risk identified, or industry-specific triggers

**NOTE**: Category F requires 2+ independent sources for any red flag before escalating severity.

---

## F.1: EMPLOYEE SIGNALS (15 checks)

### F.1.1: Glassdoor Overall Rating
- **What**: Aggregate employee satisfaction
- **Source**: Glassdoor.com (cite date, review count)
- **Threshold**:
  - ðŸ”´ HIGH: <3.0 rating (verified with >50 reviews)
  - âš ï¸ MODERATE: 3.0-3.5
  - âœ… LOW: >3.5
- **Document**: Rating, review count, access date

### F.1.2: Glassdoor Rating Trend
- **What**: Direction of employee sentiment
- **Source**: Historical Glassdoor ratings (6-12 months)
- **Threshold**:
  - ðŸ”´ HIGH: Declined >0.5 in 12 months
  - âš ï¸ MODERATE: Declined 0.2-0.5
  - âœ… LOW: Stable or improving

### F.1.3: CEO Approval Rating
- **What**: Employee view of leadership
- **Source**: Glassdoor CEO approval
- **Threshold**:
  - ðŸ”´ HIGH: <50% approval
  - âš ï¸ MODERATE: 50-70%
  - âœ… LOW: >70%

### F.1.4: "Recommend to Friend"
- **What**: Would employees recommend the company?
- **Source**: Glassdoor metric
- **Threshold**:
  - ðŸ”´ HIGH: <50%
  - âš ï¸ MODERATE: 50-70%
  - âœ… LOW: >70%

### F.1.5: Business Outlook
- **What**: Employee view of company's future
- **Source**: Glassdoor outlook metric
- **Threshold**:
  - ðŸ”´ HIGH: <30% positive
  - âš ï¸ MODERATE: 30-50%
  - âœ… LOW: >50%

### F.1.6: Glassdoor Review Themes
- **What**: Common complaints or concerns
- **Source**: Review content analysis
- **Threshold**:
  - ðŸ”´ HIGH: Fraud/ethics mentions, "sinking ship," mass layoffs
  - âš ï¸ MODERATE: Management concerns, work-life balance
  - âœ… LOW: Minor/typical complaints

### F.1.7: LinkedIn Employee Count
- **What**: Headcount trends
- **Source**: LinkedIn company page
- **Threshold**:
  - ðŸ”´ HIGH: >15% decline in 6 months (unreported layoffs)
  - âš ï¸ MODERATE: 5-15% decline
  - âœ… LOW: Stable or growing

### F.1.8: LinkedIn Executive Departures
- **What**: Senior departures not disclosed
- **Source**: LinkedIn profile changes
- **Threshold**:
  - ðŸ”´ HIGH: Multiple C-suite/VP departures not in 8-K
  - âš ï¸ MODERATE: Some departures
  - âœ… LOW: Stable leadership

### F.1.9: LinkedIn Department Analysis
- **What**: Which teams are shrinking/growing
- **Source**: LinkedIn employee analysis
- **Threshold**:
  - ðŸ”´ HIGH: Sales/revenue teams shrinking
  - âš ï¸ MODERATE: Some restructuring
  - âœ… LOW: Normal patterns

### F.1.10: Job Posting Analysis
- **What**: Hiring patterns signal strategy
- **Source**: LinkedIn Jobs, Indeed, company careers
- **Threshold**:
  - ðŸ”´ HIGH: Hiring freeze + layoffs
  - âš ï¸ MODERATE: Reduced postings
  - âœ… LOW: Active hiring

### F.1.11: Critical Role Vacancies
- **What**: Key positions unfilled
- **Source**: Job postings for critical roles
- **Threshold**:
  - ðŸ”´ HIGH: CFO/Controller/GC open >3 months
  - âš ï¸ MODERATE: VP-level vacancies
  - âœ… LOW: Normal hiring

### F.1.12: Indeed Rating
- **What**: Second source for employee sentiment
- **Source**: Indeed.com company reviews
- **Threshold**:
  - ðŸ”´ HIGH: <3.0 (corroborates Glassdoor)
  - âš ï¸ MODERATE: 3.0-3.5
  - âœ… LOW: >3.5

### F.1.13: Blind App Activity
- **What**: Anonymous employee discussions
- **Source**: Blind app (tech companies)
- **Threshold**:
  - ðŸ”´ HIGH: Fraud/layoff discussions
  - âš ï¸ MODERATE: General complaints
  - âœ… LOW: Normal chatter

### F.1.14: H-1B Data
- **What**: Visa sponsorship trends
- **Source**: H1bdata.info
- **Threshold**:
  - ðŸ”´ HIGH: Dramatic decline in sponsorships
  - âš ï¸ MODERATE: Some reduction
  - âœ… LOW: Consistent sponsorship

### F.1.15: Layoff Tracker Data
- **What**: Reported layoffs
- **Source**: Layoffs.fyi, WARN notices
- **Threshold**:
  - ðŸ”´ HIGH: Multiple rounds not fully disclosed
  - âš ï¸ MODERATE: Some layoffs
  - âœ… LOW: No recent layoffs

---

## F.2: CUSTOMER SIGNALS (12 checks)

### F.2.1: App Store Rating (if applicable)
- **What**: Customer app satisfaction
- **Source**: Apple App Store, Google Play
- **Threshold**:
  - ðŸ”´ HIGH: <3.0 stars
  - âš ï¸ MODERATE: 3.0-4.0
  - âœ… LOW: >4.0

### F.2.2: App Store Rating Trend
- **What**: Direction of customer satisfaction
- **Source**: Historical app ratings
- **Threshold**:
  - ðŸ”´ HIGH: Declined >0.5 in 6 months
  - âš ï¸ MODERATE: Slight decline
  - âœ… LOW: Stable/improving

### F.2.3: App Store Review Themes
- **What**: Common customer complaints
- **Source**: Recent review content
- **Threshold**:
  - ðŸ”´ HIGH: Billing fraud, service failures, data breaches
  - âš ï¸ MODERATE: Bugs, customer service issues
  - âœ… LOW: Minor issues

### F.2.4: BBB Rating
- **What**: Better Business Bureau assessment
- **Source**: BBB.org
- **Threshold**:
  - ðŸ”´ HIGH: F or D rating
  - âš ï¸ MODERATE: C or B
  - âœ… LOW: A or A+

### F.2.5: BBB Complaint Volume
- **What**: Customer complaint trends
- **Source**: BBB complaint history
- **Threshold**:
  - ðŸ”´ HIGH: >100% increase in complaints YoY
  - âš ï¸ MODERATE: Some increase
  - âœ… LOW: Stable/declining

### F.2.6: Trustpilot Rating
- **What**: Third-party review aggregator
- **Source**: Trustpilot.com
- **Threshold**:
  - ðŸ”´ HIGH: <3.0 stars
  - âš ï¸ MODERATE: 3.0-4.0
  - âœ… LOW: >4.0

### F.2.7: G2/Capterra Reviews (B2B)
- **What**: Business software reviews
- **Source**: G2.com, Capterra.com
- **Threshold**:
  - ðŸ”´ HIGH: <3.5 with declining trend
  - âš ï¸ MODERATE: Mixed reviews
  - âœ… LOW: Strong reviews

### F.2.8: NPS/Customer Satisfaction
- **What**: Net Promoter Score if disclosed
- **Source**: Company disclosures, earnings calls
- **Threshold**:
  - ðŸ”´ HIGH: <0 NPS or significant decline
  - âš ï¸ MODERATE: 0-30
  - âœ… LOW: >30

### F.2.9: CFPB Complaints (Financial Services)
- **What**: Consumer Financial Protection Bureau complaints
- **Source**: CFPB complaint database
- **Threshold**:
  - ðŸ”´ HIGH: Significant complaint spike
  - âš ï¸ MODERATE: Elevated complaints
  - âœ… LOW: Industry average

### F.2.10: Social Media Complaints
- **What**: Twitter/X customer complaints
- **Source**: Social media monitoring
- **Threshold**:
  - ðŸ”´ HIGH: Viral negative content
  - âš ï¸ MODERATE: Elevated complaints
  - âœ… LOW: Normal levels

### F.2.11: Reddit Discussion
- **What**: Community sentiment
- **Source**: Relevant subreddits
- **Threshold**:
  - ðŸ”´ HIGH: Coordinated negative campaigns
  - âš ï¸ MODERATE: Mixed sentiment
  - âœ… LOW: Positive/neutral

### F.2.12: Churn Indicators
- **What**: Signs of customer attrition
- **Source**: Reviews, social media, industry
- **Threshold**:
  - ðŸ”´ HIGH: Mass cancellation reports
  - âš ï¸ MODERATE: Some churn mentions
  - âœ… LOW: No unusual churn signals

---

## F.3: REGULATORY DATABASES (20 checks)

### F.3.1: FDA Warning Letters
- **What**: Official FDA enforcement
- **Source**: FDA.gov Warning Letters database
- **Threshold**:
  - ðŸ”´ CRITICAL: Warning letter <12 months
  - ðŸ”´ HIGH: Warning letter 12-24 months
  - âš ï¸ MODERATE: Resolved >24 months
  - âœ… LOW: None

### F.3.2: FDA 483 Observations
- **What**: Inspection findings
- **Source**: FDA 483 database, import alerts
- **Threshold**:
  - ðŸ”´ HIGH: Multiple OAI (Official Action Indicated) findings
  - âš ï¸ MODERATE: VAI (Voluntary Action Indicated)
  - âœ… LOW: NAI (No Action Indicated) or none

### F.3.3: FDA Import Alerts
- **What**: Products detained at border
- **Source**: FDA Import Alert database
- **Threshold**:
  - ðŸ”´ HIGH: Active import alert
  - âš ï¸ MODERATE: Historical, resolved
  - âœ… LOW: None

### F.3.4: FDA Recalls
- **What**: Product recalls
- **Source**: FDA Recalls database, company 8-K
- **Threshold**:
  - ðŸ”´ CRITICAL: Class I recall (serious health risk)
  - ðŸ”´ HIGH: Class II recall <12 months
  - âš ï¸ MODERATE: Class III or older
  - âœ… LOW: None

### F.3.5: FDA Clinical Trial Database
- **What**: Trial status and results
- **Source**: ClinicalTrials.gov
- **Threshold**:
  - ðŸ”´ HIGH: Failed trials, terminated studies
  - âš ï¸ MODERATE: Delayed trials
  - âœ… LOW: On-track trials

### F.3.6: FDA MAUDE Database
- **What**: Medical device adverse events
- **Source**: FDA MAUDE
- **Threshold**:
  - ðŸ”´ HIGH: Death/serious injury reports trending up
  - âš ï¸ MODERATE: Some reports
  - âœ… LOW: Minimal reports

### F.3.7: OSHA Violations
- **What**: Workplace safety violations
- **Source**: OSHA.gov establishment search
- **Threshold**:
  - ðŸ”´ CRITICAL: Willful violation <3 years
  - ðŸ”´ HIGH: Serious violations <3 years
  - âš ï¸ MODERATE: Other-than-serious
  - âœ… LOW: Clean record

### F.3.8: OSHA Fatalities
- **What**: Workplace deaths
- **Source**: OSHA fatality inspection data
- **Threshold**:
  - ðŸ”´ CRITICAL: Any fatality under investigation
  - ðŸ”´ HIGH: Fatality <3 years
  - âš ï¸ MODERATE: Historical fatality
  - âœ… LOW: None

### F.3.9: EPA ECHO Database
- **What**: Environmental violations
- **Source**: EPA ECHO (Enforcement and Compliance History)
- **Threshold**:
  - ðŸ”´ CRITICAL: Significant non-compliance (SNC)
  - ðŸ”´ HIGH: High Priority Violation (HPV)
  - âš ï¸ MODERATE: Minor violations
  - âœ… LOW: In compliance

### F.3.10: EPA Superfund
- **What**: Toxic cleanup liability
- **Source**: EPA Superfund site list
- **Threshold**:
  - ðŸ”´ CRITICAL: Named PRP (Potentially Responsible Party)
  - ðŸ”´ HIGH: Site near operations
  - âš ï¸ MODERATE: Historical involvement
  - âœ… LOW: No association

### F.3.11: EPA Air Quality Permits
- **What**: Clean Air Act compliance
- **Source**: EPA ECHO Air data
- **Threshold**:
  - ðŸ”´ HIGH: NOV (Notice of Violation) <2 years
  - âš ï¸ MODERATE: Permit issues
  - âœ… LOW: Compliant

### F.3.12: EPA Water Quality
- **What**: Clean Water Act compliance
- **Source**: EPA ECHO Water data
- **Threshold**:
  - ðŸ”´ HIGH: SNC for water effluents
  - âš ï¸ MODERATE: Minor violations
  - âœ… LOW: Compliant

### F.3.13: MSHA (Mining)
- **What**: Mine Safety violations
- **Source**: MSHA.gov violation data
- **Threshold**:
  - ðŸ”´ CRITICAL: Pattern of violations
  - ðŸ”´ HIGH: Significant & substantial violations
  - âš ï¸ MODERATE: Minor violations
  - âœ… LOW: Clean

### F.3.14: NHTSA (Auto)
- **What**: Vehicle safety investigations
- **Source**: NHTSA.gov complaints and investigations
- **Threshold**:
  - ðŸ”´ CRITICAL: Open defect investigation
  - ðŸ”´ HIGH: Recent recall
  - âš ï¸ MODERATE: Elevated complaints
  - âœ… LOW: Normal

### F.3.15: CPSC (Consumer Products)
- **What**: Consumer product safety
- **Source**: CPSC.gov recalls database
- **Threshold**:
  - ðŸ”´ CRITICAL: Active recall
  - ðŸ”´ HIGH: Recall <12 months
  - âš ï¸ MODERATE: Historical recall
  - âœ… LOW: None

### F.3.16: FTC Enforcement
- **What**: Consumer protection, advertising
- **Source**: FTC.gov cases database
- **Threshold**:
  - ðŸ”´ HIGH: Active investigation or settlement <2 years
  - âš ï¸ MODERATE: Historical settlement
  - âœ… LOW: None

### F.3.17: State AG Actions
- **What**: State attorney general investigations
- **Source**: State AG press releases
- **Threshold**:
  - ðŸ”´ HIGH: Multi-state investigation
  - âš ï¸ MODERATE: Single state action
  - âœ… LOW: None

### F.3.18: EEOC Charges
- **What**: Employment discrimination charges
- **Source**: EEOC.gov, news, 10-K
- **Threshold**:
  - ðŸ”´ HIGH: Pattern or practice lawsuit
  - âš ï¸ MODERATE: Individual charges
  - âœ… LOW: None significant

### F.3.19: DOL/Wage & Hour
- **What**: Labor law violations
- **Source**: DOL.gov enforcement database
- **Threshold**:
  - ðŸ”´ HIGH: Significant back wages owed
  - âš ï¸ MODERATE: Minor violations
  - âœ… LOW: Compliant

### F.3.20: OCC/Banking Regulators
- **What**: Bank examination results
- **Source**: OCC enforcement actions, regulatory filings
- **Threshold**:
  - ðŸ”´ CRITICAL: Consent order or MOU
  - ðŸ”´ HIGH: CRA downgrade
  - âš ï¸ MODERATE: MRA (Matters Requiring Attention)
  - âœ… LOW: Satisfactory exam

---

## F.4: RESEARCH & ACADEMIC SIGNALS (10 checks)

### F.4.1: PubPeer Activity (Life Sciences)
- **What**: Post-publication peer review flags
- **Source**: PubPeer.com
- **Threshold**:
  - ðŸ”´ CRITICAL: Management publications flagged
  - ðŸ”´ HIGH: Key research flagged
  - âš ï¸ MODERATE: Minor concerns raised
  - âœ… LOW: No flags

### F.4.2: Retraction Watch
- **What**: Paper retractions
- **Source**: RetractionWatch.com database
- **Threshold**:
  - ðŸ”´ CRITICAL: Company-authored retractions
  - ðŸ”´ HIGH: Key researcher retractions
  - âš ï¸ MODERATE: Historical retractions
  - âœ… LOW: None

### F.4.3: Clinical Trial Data Integrity
- **What**: Data quality concerns
- **Source**: Academic analysis, FDA reviews
- **Threshold**:
  - ðŸ”´ HIGH: FDA issued data integrity letter
  - âš ï¸ MODERATE: Some data questions
  - âœ… LOW: Clean

### F.4.4: Patent Challenges
- **What**: IPR/PGR proceedings
- **Source**: USPTO PTAB database
- **Threshold**:
  - ðŸ”´ HIGH: Key patent claims invalidated
  - âš ï¸ MODERATE: Challenge pending
  - âœ… LOW: No challenges

### F.4.5: Academic Litigation
- **What**: IP disputes with universities
- **Source**: Court records, news
- **Threshold**:
  - ðŸ”´ HIGH: Active dispute over foundational IP
  - âš ï¸ MODERATE: Resolved dispute
  - âœ… LOW: None

### F.4.6: KOL Sentiment (Life Sciences)
- **What**: Key Opinion Leader views
- **Source**: Conference presentations, social media
- **Threshold**:
  - ðŸ”´ HIGH: KOLs publicly critical
  - âš ï¸ MODERATE: Mixed views
  - âœ… LOW: Supportive KOLs

### F.4.7: Conference Presentation Issues
- **What**: Abstract/presentation withdrawals
- **Source**: Conference records
- **Threshold**:
  - ðŸ”´ HIGH: Withdrawn presentation
  - âš ï¸ MODERATE: Late-breaking changes
  - âœ… LOW: Normal

### F.4.8: Peer Review Concerns
- **What**: Journal editor statements
- **Source**: Journal notices, expressions of concern
- **Threshold**:
  - ðŸ”´ HIGH: Expression of concern issued
  - âš ï¸ MODERATE: Correction issued
  - âœ… LOW: Clean

### F.4.9: Research Fraud Database
- **What**: ORI (Office of Research Integrity) findings
- **Source**: ORI.hhs.gov
- **Threshold**:
  - ðŸ”´ CRITICAL: ORI finding involving company
  - ðŸ”´ HIGH: Key researcher with ORI finding
  - âš ï¸ MODERATE: Historical
  - âœ… LOW: None

### F.4.10: Technology Assessment
- **What**: Third-party technology validation
- **Source**: Academic reviews, independent testing
- **Threshold**:
  - ðŸ”´ HIGH: Technology validity questioned
  - âš ï¸ MODERATE: Mixed assessments
  - âœ… LOW: Validated technology

---

## F.5: MEDIA MONITORING (12 checks)

### F.5.1: Investigative Journalism
- **What**: Deep investigative pieces
- **Source**: Major publications (WSJ, NYT, Bloomberg)
- **Threshold**:
  - ðŸ”´ CRITICAL: Fraud/misconduct investigation published
  - ðŸ”´ HIGH: Negative investigation <6 months
  - âš ï¸ MODERATE: Critical coverage
  - âœ… LOW: Normal coverage

### F.5.2: Whistleblower Reports
- **What**: Employee or insider allegations
- **Source**: News, SEC tips (if disclosed)
- **Threshold**:
  - ðŸ”´ CRITICAL: Detailed fraud allegations
  - ðŸ”´ HIGH: Misconduct allegations
  - âš ï¸ MODERATE: Workplace complaints
  - âœ… LOW: None

### F.5.3: Documentary/Podcast Coverage
- **What**: Long-form negative content
- **Source**: Streaming platforms, podcast platforms
- **Threshold**:
  - ðŸ”´ HIGH: Documentary about company fraud
  - âš ï¸ MODERATE: Critical coverage
  - âœ… LOW: None

### F.5.4: Industry Publication Coverage
- **What**: Trade press sentiment
- **Source**: Industry-specific publications
- **Threshold**:
  - ðŸ”´ HIGH: Industry critics of company
  - âš ï¸ MODERATE: Mixed coverage
  - âœ… LOW: Positive industry standing

### F.5.5: Local News Coverage
- **What**: Community/local issues
- **Source**: Local news outlets
- **Threshold**:
  - ðŸ”´ HIGH: Environmental/community conflict
  - âš ï¸ MODERATE: Some local issues
  - âœ… LOW: Positive local presence

### F.5.6: International Media
- **What**: Coverage in non-US markets
- **Source**: International news sources
- **Threshold**:
  - ðŸ”´ HIGH: Negative coverage in key markets
  - âš ï¸ MODERATE: Some concerns
  - âœ… LOW: Normal

### F.5.7: Financial Media Sentiment
- **What**: CNBC, Bloomberg TV, etc.
- **Source**: Financial news programs
- **Threshold**:
  - ðŸ”´ HIGH: Repeated negative segments
  - âš ï¸ MODERATE: Critical commentary
  - âœ… LOW: Neutral/positive

### F.5.8: Blog/Newsletter Coverage
- **What**: Influential financial bloggers
- **Source**: Seeking Alpha, Substack
- **Threshold**:
  - ðŸ”´ HIGH: Fraud allegations from credible source
  - âš ï¸ MODERATE: Critical analysis
  - âœ… LOW: Mixed/positive

### F.5.9: News Volume Spike
- **What**: Unusual news activity
- **Source**: Google News, news aggregators
- **Threshold**:
  - ðŸ”´ HIGH: News spike + negative sentiment
  - âš ï¸ MODERATE: Elevated coverage
  - âœ… LOW: Normal volume

### F.5.10: Executive Interviews
- **What**: How management presents publicly
- **Source**: TV appearances, podcasts
- **Threshold**:
  - ðŸ”´ HIGH: Evasive, defensive behavior
  - âš ï¸ MODERATE: Vague responses
  - âœ… LOW: Confident, transparent

### F.5.11: Conference Call Sentiment
- **What**: Analyst call tone
- **Source**: Earnings call transcripts
- **Threshold**:
  - ðŸ”´ HIGH: Contentious, defensive management
  - âš ï¸ MODERATE: Pointed questions
  - âœ… LOW: Normal Q&A

### F.5.12: PR Crisis History
- **What**: Past crisis management
- **Source**: News archives
- **Threshold**:
  - ðŸ”´ HIGH: Poorly managed past crisis
  - âš ï¸ MODERATE: Some past issues
  - âœ… LOW: Clean or well-handled

---

## F.6: COMPETITIVE INTELLIGENCE (10 checks)

### F.6.1: Market Share Trend
- **What**: Competitive position changes
- **Source**: Industry reports, company disclosures
- **Threshold**:
  - ðŸ”´ HIGH: Losing share significantly
  - âš ï¸ MODERATE: Stable but pressured
  - âœ… LOW: Gaining or stable leader

### F.6.2: Competitor Announcements
- **What**: Competitive threats announced
- **Source**: Competitor press releases
- **Threshold**:
  - ðŸ”´ HIGH: Direct competitive product launch
  - âš ï¸ MODERATE: Competitive pressure
  - âœ… LOW: Normal competition

### F.6.3: Pricing Pressure
- **What**: Industry pricing dynamics
- **Source**: Industry reports, earnings calls
- **Threshold**:
  - ðŸ”´ HIGH: Significant price wars
  - âš ï¸ MODERATE: Some pressure
  - âœ… LOW: Stable pricing

### F.6.4: Technology Disruption
- **What**: Emerging technology threats
- **Source**: Tech news, industry analysis
- **Threshold**:
  - ðŸ”´ HIGH: Disruptive technology gaining traction
  - âš ï¸ MODERATE: Emerging threat
  - âœ… LOW: Stable technology position

### F.6.5: New Entrant Threat
- **What**: Well-funded new competitors
- **Source**: Funding news, industry analysis
- **Threshold**:
  - ðŸ”´ HIGH: Major new entrant (big tech, well-funded startup)
  - âš ï¸ MODERATE: Emerging competitors
  - âœ… LOW: High barriers maintained

### F.6.6: Customer Win/Loss
- **What**: Key customer movements
- **Source**: Press releases, industry news
- **Threshold**:
  - ðŸ”´ HIGH: Lost major customers to competitors
  - âš ï¸ MODERATE: Some customer churn
  - âœ… LOW: Winning competitive deals

### F.6.7: Talent Competition
- **What**: Losing key talent to competitors
- **Source**: LinkedIn, news
- **Threshold**:
  - ðŸ”´ HIGH: Key executives joined competitor
  - âš ï¸ MODERATE: Some talent loss
  - âœ… LOW: Attracting talent

### F.6.8: Patent Activity
- **What**: IP positioning vs. competitors
- **Source**: USPTO, patent databases
- **Threshold**:
  - ðŸ”´ HIGH: Competitor patent blocks key products
  - âš ï¸ MODERATE: IP concerns
  - âœ… LOW: Strong IP position

### F.6.9: Partnership Losses
- **What**: Key partnerships ending
- **Source**: 8-K, press releases
- **Threshold**:
  - ðŸ”´ HIGH: Critical partnership terminated
  - âš ï¸ MODERATE: Some partnership changes
  - âœ… LOW: Stable/growing partnerships

### F.6.10: Industry Consolidation
- **What**: M&A activity creating larger competitors
- **Source**: Deal announcements
- **Threshold**:
  - ðŸ”´ HIGH: Competitors merging to challenge
  - âš ï¸ MODERATE: Industry consolidating
  - âœ… LOW: Fragmented market

---

## F.7: SUPPLY CHAIN SIGNALS (8 checks)

### F.7.1: Supplier News
- **What**: Key supplier issues
- **Source**: Supplier public filings, news
- **Threshold**:
  - ðŸ”´ HIGH: Key supplier bankruptcy/disruption
  - âš ï¸ MODERATE: Supplier stress
  - âœ… LOW: Stable supply chain

### F.7.2: Port/Logistics Data
- **What**: Import/export volumes
- **Source**: Trade databases, shipping data
- **Threshold**:
  - ðŸ”´ HIGH: Significant volume decline
  - âš ï¸ MODERATE: Some disruption
  - âœ… LOW: Normal volumes

### F.7.3: Commodity Price Impact
- **What**: Input cost changes
- **Source**: Commodity pricing databases
- **Threshold**:
  - ðŸ”´ HIGH: Key input up >30% unhedged
  - âš ï¸ MODERATE: Moderate increases
  - âœ… LOW: Stable/hedged

### F.7.4: Contract Manufacturing Issues
- **What**: Outsourced production problems
- **Source**: Supplier news, regulatory filings
- **Threshold**:
  - ðŸ”´ HIGH: Contract manufacturer cited by FDA/EPA
  - âš ï¸ MODERATE: Quality concerns
  - âœ… LOW: Stable

### F.7.5: Shipping/Freight Rates
- **What**: Logistics cost exposure
- **Source**: Freight indices
- **Threshold**:
  - ðŸ”´ HIGH: Major cost increase exposure
  - âš ï¸ MODERATE: Some exposure
  - âœ… LOW: Minimal impact

### F.7.6: Inventory Channel
- **What**: Distributor/retailer inventory levels
- **Source**: Channel checks, industry
- **Threshold**:
  - ðŸ”´ HIGH: Channel stuffing indicators
  - âš ï¸ MODERATE: Elevated inventory
  - âœ… LOW: Normal

### F.7.7: Vendor Payment Practices
- **What**: How company pays suppliers
- **Source**: D&B, supplier forums
- **Threshold**:
  - ðŸ”´ HIGH: Stretched payables, slow pay
  - âš ï¸ MODERATE: Some delays
  - âœ… LOW: On-time payment

### F.7.8: Supplier Concentration
- **What**: Single-source dependencies
- **Source**: 10-K Risk Factors
- **Threshold**:
  - ðŸ”´ HIGH: Single-source for critical inputs
  - âš ï¸ MODERATE: Limited alternatives
  - âœ… LOW: Diversified

---

## F.8: DIGITAL SIGNALS (10 checks)

### F.8.1: Website Traffic Trend
- **What**: Directional indicator of business
- **Source**: SimilarWeb, Semrush (directional only)
- **Threshold**:
  - ðŸ”´ HIGH: >30% decline YoY
  - âš ï¸ MODERATE: 10-30% decline
  - âœ… LOW: Stable/growing

### F.8.2: App Download Trend
- **What**: Mobile app momentum
- **Source**: Sensor Tower, App Annie
- **Threshold**:
  - ðŸ”´ HIGH: >30% decline in downloads
  - âš ï¸ MODERATE: Declining
  - âœ… LOW: Growing

### F.8.3: SEO/SEM Position
- **What**: Search visibility
- **Source**: Search rankings
- **Threshold**:
  - ðŸ”´ HIGH: Lost key rankings
  - âš ï¸ MODERATE: Declining
  - âœ… LOW: Strong position

### F.8.4: Social Media Following
- **What**: Brand engagement
- **Source**: Social platforms
- **Threshold**:
  - ðŸ”´ HIGH: Declining following + negative sentiment
  - âš ï¸ MODERATE: Flat engagement
  - âœ… LOW: Growing engagement

### F.8.5: Domain Authority
- **What**: Website credibility
- **Source**: Moz, Ahrefs
- **Threshold**:
  - ðŸ”´ HIGH: Low/declining authority
  - âš ï¸ MODERATE: Average
  - âœ… LOW: High authority

### F.8.6: Email Marketing Indicators
- **What**: Customer engagement
- **Source**: Industry data, competitor analysis
- **Threshold**:
  - ðŸ”´ HIGH: Signs of list degradation
  - âš ï¸ MODERATE: Average engagement
  - âœ… LOW: Strong engagement

### F.8.7: Conversion Rate Indicators
- **What**: Sales efficiency
- **Source**: Industry benchmarks
- **Threshold**:
  - ðŸ”´ HIGH: Below industry benchmarks
  - âš ï¸ MODERATE: Average
  - âœ… LOW: Above average

### F.8.8: Server/Infrastructure Status
- **What**: Technical reliability
- **Source**: Down Detector, status pages
- **Threshold**:
  - ðŸ”´ HIGH: Frequent outages
  - âš ï¸ MODERATE: Some incidents
  - âœ… LOW: Reliable

### F.8.9: Cybersecurity Posture
- **What**: Security vulnerabilities
- **Source**: SecurityScorecard, BitSight
- **Threshold**:
  - ðŸ”´ HIGH: Low security rating
  - âš ï¸ MODERATE: Average
  - âœ… LOW: High rating

### F.8.10: Data Breach History
- **What**: Past security incidents
- **Source**: HaveIBeenPwned, breach databases
- **Threshold**:
  - ðŸ”´ HIGH: Major breach <2 years
  - âš ï¸ MODERATE: Minor incidents
  - âœ… LOW: Clean record

---

## SECTION F CHECKPOINT

**Complete this checkpoint before proceeding:**

```
SECTION F: ALTERNATIVE DATA CHECKPOINT
======================================
Company: [Name]
Completed: [Date/Time]

EMPLOYEE SIGNALS (F.1):
â–¡ F.1.1 Glassdoor Rating: [X]/5.0 ([X] reviews)
â–¡ F.1.2 Rating Trend: [Direction]
â–¡ F.1.7 LinkedIn Headcount Trend: [+/-X]%
â–¡ F.1.10 Hiring Patterns: [Assessment]

CUSTOMER SIGNALS (F.2):
â–¡ F.2.1 App Store (if appl.): [X]/5.0
â–¡ F.2.4 BBB Rating: [Grade]
â–¡ F.2.6 Trustpilot: [X]/5.0

REGULATORY DATABASES (F.3):
â–¡ F.3.1 FDA Warning Letters: [Y/N]
â–¡ F.3.4 FDA Recalls: [Y/N - Class if yes]
â–¡ F.3.7 OSHA Violations: [Y/N - Type if yes]
â–¡ F.3.9 EPA ECHO: [Status]
â–¡ F.3.15 CPSC Recalls: [Y/N]

RESEARCH/ACADEMIC (F.4):
â–¡ F.4.1 PubPeer (if Life Sci): [Y/N flags]
â–¡ F.4.2 Retraction Watch: [Y/N]
â–¡ F.4.4 Patent Challenges: [Status]

MEDIA (F.5):
â–¡ F.5.1 Investigative Reports: [Y/N]
â–¡ F.5.2 Whistleblower Reports: [Y/N]
â–¡ F.5.9 News Volume: [Normal/Elevated]

COMPETITIVE (F.6):
â–¡ F.6.1 Market Share Trend: [Direction]
â–¡ F.6.4 Technology Disruption: [Assessment]

SUPPLY CHAIN (F.7):
â–¡ F.7.1 Supplier Issues: [Y/N]
â–¡ F.7.3 Commodity Impact: [Assessment]

DIGITAL (F.8):
â–¡ F.8.1 Website Traffic: [Trend]
â–¡ F.8.9 Cybersecurity Score: [Rating]
â–¡ F.8.10 Data Breach History: [Y/N]

CORROBORATION CHECK:
â–¡ Any red flags verified by 2+ sources? [Y/N]

RED FLAGS IDENTIFIED:
[List any ðŸ”´ findings with corroboration]

PROCEED TO: [Next Section per Trigger Matrix]
```

---

**END OF SECTION F**
