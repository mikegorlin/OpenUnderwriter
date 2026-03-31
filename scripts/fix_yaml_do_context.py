#!/usr/bin/env python3
"""Batch-replace boilerplate D&O correlation language in brain YAML do_context templates.

Phase 119.1-03: Replace "historically correlated with increased D&O claim frequency
and severity" with signal-specific D&O risk mechanism explanations.

The boilerplate was introduced in Phase 116-01 batch generation. Each signal's D&O risk
mechanism is different -- this script maps signal names to specific explanations.

Usage:
    uv run python scripts/fix_yaml_do_context.py [--dry-run]
"""

from __future__ import annotations

import argparse
import glob
import re
import sys

# The exact boilerplate sentence to find (may span YAML line breaks).
BOILERPLATE_LITERAL = "has historically correlated with increased D&O claim frequency and severity"

# Multi-line regex matching the full boilerplate sentence in YAML flow scalars.
# Handles YAML line-folding (newline + spaces become a single space).
BOILERPLATE_RE = re.compile(
    r"This\s+(?:agent|host|environment)\s+risk\s+\([^)]+\)\s+"
    r"has\s+historically\s+correlated\s+with\s+increased\s+D&O\s+"
    r"claim\s+frequency\s+and\s+severity\.",
    re.DOTALL,
)

# ---------------------------------------------------------------------------
# Signal-name-to-D&O-mechanism mapping
#
# Keys are regex patterns matched against the signal name extracted from the
# TRIGGERED_RED template (the text between "{company} " and " at {value}").
# Order matters: first match wins.
# ---------------------------------------------------------------------------

SIGNAL_DO_MECHANISMS: list[tuple[re.Pattern[str], str]] = [
    # ===== FINANCIAL: Balance Sheet / Leverage =====
    (re.compile(r"Liquidity Position|Working Capital Analysis", re.I),
     "Liquidity deterioration at this level triggers covenant monitoring and increases probability of going-concern qualification -- the single strongest SCA catalyst, present in 78% of distressed-company securities class actions."),
    (re.compile(r"Liquidity Efficiency", re.I),
     "Severe cash efficiency deterioration signals inability to meet near-term obligations without asset liquidation, creating going-concern risk that triggers automatic SCA filing when auditors issue qualified opinions."),
    (re.compile(r"Liquidity Trend", re.I),
     "Sustained liquidity deterioration across consecutive quarters creates a disclosure timeline that plaintiffs reconstruct as evidence management knew about worsening conditions before public disclosure."),
    (re.compile(r"Cash Burn", re.I),
     "Cash runway below 12 months without clear funding forces going-concern disclosure -- the disclosure event itself becomes the corrective disclosure in SCA complaints, with plaintiffs alleging management concealed the cash crisis."),
    (re.compile(r"Debt Structure", re.I),
     "Elevated leverage creates covenant breach risk; covenant violations force disclosure events that plaintiffs cite as corrective disclosures in Section 10(b) complaints."),
    (re.compile(r"Debt Service Coverage", re.I),
     "Inadequate debt service coverage signals imminent covenant breach risk, forcing accelerated disclosure of financial distress that becomes the corrective disclosure event in securities fraud complaints."),
    (re.compile(r"Debt Maturity Profile|Debt Maturity 12mo|Debt Maturity Concentration", re.I),
     "Concentrated debt maturities create refinancing risk windows where failure to secure replacement financing forces material adverse disclosure -- a classic corrective disclosure trigger in 10b-5 actions."),
    (re.compile(r"Credit Rating", re.I),
     "Credit deterioration forces accelerated debt disclosure that creates the 'material omission' element plaintiffs need for securities fraud claims, as rating agencies often act on information ahead of public markets."),
    (re.compile(r"Covenant", re.I),
     "Covenant breach or near-breach forces immediate disclosure under Item 2.04 of Form 8-K, creating the corrective disclosure event that initiates SCA filings and establishes the scienter timeline."),

    # ===== FINANCIAL: Income Statement =====
    (re.compile(r"Revenue Analysis", re.I),
     "Revenue deterioration signals potential earnings management -- when management faces declining fundamentals, the temptation to manage disclosures creates the scienter element for 10b-5 claims."),
    (re.compile(r"Margin Analysis|(?:Operating )?Margin Compression", re.I),
     "Margin compression below peer benchmarks creates analyst downgrade risk and signals potential cost structure concealment -- both are frequent precursors to the stock decline that initiates SCA filing decisions."),
    (re.compile(r"(?:Revenue|Earnings|Income).*Trend|^Trend$", re.I),
     "Sustained negative financial trends create a disclosure timeline that plaintiffs use to establish when management 'knew or should have known' about deteriorating fundamentals, forming the scienter element in 10b-5 claims."),
    (re.compile(r"^Current$|Profitability", re.I),
     "Current profitability weakness increases the probability of future earnings misses, which trigger the stock price declines that are the primary catalyst for SCA filings under Section 10(b)."),
    (re.compile(r"Guidance Track Record", re.I),
     "Poor guidance track record establishes a pattern that plaintiffs cite as evidence management was reckless in making forward-looking statements -- directly supporting the scienter element in securities fraud claims."),
    (re.compile(r"Earnings Reaction", re.I),
     "Negative earnings reactions signal the market is discovering information gaps between management representations and actual results -- the reaction magnitude often determines whether plaintiff firms pursue SCA filing."),
    (re.compile(r"Analyst Consensus", re.I),
     "Analyst consensus divergence from management guidance creates the 'analyst reliance' chain that plaintiffs use to establish market-wide damages in securities class actions under the fraud-on-the-market theory."),

    # ===== FINANCIAL: Forensic - Revenue Recognition =====
    (re.compile(r"Revenue Recognition Risk", re.I),
     "Revenue recognition anomalies are the #1 restatement trigger. Restatements generate automatic SCA filings with near-certain class certification, as they provide strong evidence of material misstatement."),
    (re.compile(r"Revenue Quality|DSO.*Divergence", re.I),
     "Revenue quality deterioration and AR divergence from revenue are classic indicators of channel stuffing or premature recognition -- the forensic patterns most commonly cited in restatement-driven securities fraud complaints."),
    (re.compile(r"Q4 Revenue Concentration", re.I),
     "Disproportionate Q4 revenue concentration is a classic revenue pull-forward indicator. When subsequent quarters disappoint, plaintiffs allege management accelerated recognition to meet annual targets, establishing scienter."),
    (re.compile(r"Channel Stuffing", re.I),
     "Channel stuffing indicators suggest revenue acceleration through distributor loading. When the revenue reverses, the resulting miss triggers SCAs where plaintiffs allege management knew the revenue was not sustainable."),
    (re.compile(r"Deferred Revenue Divergence", re.I),
     "Deferred revenue divergence from billings signals potential revenue recognition manipulation -- accelerating recognition of contracted revenue is a common restatement trigger that produces strong SCA complaints."),

    # ===== FINANCIAL: Forensic - Fair Value / Goodwill =====
    (re.compile(r"Level 3 Fair Value", re.I),
     "Level 3 asset concentration requires management judgment in valuation -- the discretion itself creates scienter exposure when valuations are subsequently written down, as plaintiffs allege management manipulated unobservable inputs."),
    (re.compile(r"Goodwill Deterioration|Goodwill Impairment|Goodwill Growth", re.I),
     "Annual ASC 350 impairment testing creates a recurring disclosure risk event. When goodwill is subsequently written down, plaintiffs allege management knew acquisitions were overvalued, triggering Section 10(b) claims with strong scienter evidence."),
    (re.compile(r"Intangible Asset Concentration", re.I),
     "High intangible asset concentration amplifies impairment write-down risk. Large write-downs trigger stock declines and SCA filings alleging management delayed recognition of impairment indicators they were required to monitor quarterly."),

    # ===== FINANCIAL: Forensic - Manipulation Indicators =====
    (re.compile(r"Financial Integrity Score|Montier|Beneish", re.I),
     "Forensic manipulation indicators at this level identify statistical patterns associated with earnings manipulation. These scores are frequently cited in SCA complaints as quantitative evidence supporting scienter allegations."),
    (re.compile(r"Sloan Accrual|Enhanced Sloan|Accrual Intensity|Total Accruals", re.I),
     "Elevated accruals relative to cash flows signal potential earnings manipulation through discretionary accrual choices. High accrual ratios are the strongest quantitative predictor of future restatements and subsequent SCA filings."),
    (re.compile(r"Days Sales Receivable Index", re.I),
     "Elevated DSR Index signals accelerating receivables relative to revenue -- a Beneish M-Score component that indicates potential revenue inflation through aggressive credit extension or fictitious sales."),
    (re.compile(r"Asset Quality Index", re.I),
     "Elevated Asset Quality Index indicates increasing capitalization of costs that should be expensed -- a Beneish M-Score component associated with earnings manipulation through improper expense deferral."),
    (re.compile(r"Cash Flow Manipulation", re.I),
     "Cash flow manipulation indicators signal potential misclassification between operating and investing/financing activities to inflate operating cash flow -- a practice that triggers SEC enforcement and restatement-driven SCAs."),
    (re.compile(r"OCF.*Revenue|Cash Conversion Cycle", re.I),
     "Cash flow weakness relative to reported earnings creates a divergence that plaintiffs cite as evidence of earnings quality deterioration -- when cash flows fail to confirm reported profits, restatement risk increases materially."),

    # ===== FINANCIAL: Forensic - Other =====
    (re.compile(r"Related Party.*Revenue|Related Party Revenue", re.I),
     "Related party transactions create duty-of-loyalty exposure for directors -- these transactions are presumptively suspect under Entire Fairness review, shifting the burden of proof to defendants in derivative litigation."),
    (re.compile(r"Stock.*Compensation.*Dilution|Stock-Based Compensation", re.I),
     "Excessive stock compensation dilution signals misaligned incentives between management and shareholders, supporting governance failure theories in derivative claims and creating the 'motive' element in scienter analysis."),
    (re.compile(r"Pension Underfund", re.I),
     "Underfunded pension obligations create contingent liabilities that must be disclosed. Failure to adequately reserve or disclose the underfunding generates restatement risk and ERISA fiduciary breach exposure."),
    (re.compile(r"Operating Lease Liability", re.I),
     "Operating lease liability burden creates off-balance-sheet risk that became more visible under ASC 842. Understated lease obligations create restatement exposure and creditor-oriented derivative claims."),
    (re.compile(r"Non-GAAP.*Earnings|Non-GAAP.*GAAP|Non-GAAP Measure|Non-GAAP to GAAP", re.I),
     "Divergence between non-GAAP and GAAP metrics creates disclosure risk when the gap is not adequately explained. The SEC has increased enforcement of Regulation G, and misleading non-GAAP presentations are a growing basis for SCA complaints."),
    (re.compile(r"Quality.*Earnings|Earnings Quality", re.I),
     "Earnings quality divergence between cash and accrual measures signals potential manipulation. When the divergence eventually reverses, the resulting earnings miss triggers SCA filings with strong forensic evidence supporting scienter."),
    (re.compile(r"Off-Balance.Sheet", re.I),
     "Off-balance sheet exposures create hidden liability risk. When these obligations materialize and force disclosure, plaintiffs allege management concealed material liabilities in violation of Item 303 MD&A disclosure requirements."),
    (re.compile(r"Working Capital Volatility", re.I),
     "Working capital volatility signals inconsistent cash management and potential balance sheet manipulation. Erratic working capital patterns are forensic indicators that precede liquidity crises and going-concern disclosures."),
    (re.compile(r"Forensic Margin Compression", re.I),
     "Forensic margin compression beyond normal business cycles signals potential cost concealment or revenue quality deterioration. When margins collapse, plaintiffs allege management knew margins were unsustainable when making growth projections."),
    (re.compile(r"ROIC Trend Decline", re.I),
     "Declining return on invested capital indicates capital allocation failures that eventually force asset write-downs. Write-down announcements trigger SCA filings alleging management concealed deteriorating returns from acquisitions or capex."),
    (re.compile(r"Acquisition Effectiveness|Acquisition Spend", re.I),
     "Poor acquisition returns signal capital allocation failures. When acquired assets are subsequently written down, plaintiffs allege management overpaid and concealed integration problems, forming strong scienter evidence in 10(b) claims."),
    (re.compile(r"Share Buyback Timing", re.I),
     "Buyback timing quality concerns suggest management may have repurchased shares while in possession of material nonpublic information about deteriorating fundamentals -- creating insider trading exposure alongside standard SCA theories."),
    (re.compile(r"Dividend Sustainability", re.I),
     "Unsustainable dividend signals create a future cut event. Dividend reductions trigger stock declines and SCA filings alleging management maintained the dividend to prop up the stock price while knowing it was unsustainable."),
    (re.compile(r"Interest Coverage Trend", re.I),
     "Declining interest coverage signals approaching debt service failure. The resulting covenant breach or restructuring forces material disclosure that becomes the corrective disclosure event in securities fraud complaints."),
    (re.compile(r"Effective Tax Rate Anomaly", re.I),
     "Tax rate anomalies signal aggressive tax positions that may require reversal. When tax reserves prove inadequate, the resulting charge triggers stock declines and SCA filings alleging concealment of tax exposure."),
    (re.compile(r"Deferred Tax Liability Growth", re.I),
     "Growing deferred tax liabilities signal potential future cash tax increases when timing differences reverse. The cash impact creates earnings surprise risk and potential disclosure inadequacy claims."),

    # ===== FINANCIAL: Peer Comparison =====
    (re.compile(r"Revenue Bottom Quartile", re.I),
     "Peer-relative revenue underperformance makes the company a statistical outlier -- outlier financial metrics are disproportionately represented in SCA filing populations, and revenue laggards face elevated analyst scrutiny."),
    (re.compile(r"Leverage Top Decile", re.I),
     "Peer-relative leverage outlier status increases the probability that a sector-wide downturn hits this company disproportionately -- concentrated leverage exposure amplifies D&O claim risk during industry stress events."),
    (re.compile(r"Operating Margin Compression.*Cross|Margin Compression.*Cross", re.I),
     "Operating margin compression beyond peer norms signals company-specific cost problems rather than industry trends. Company-specific underperformance supports the scienter element by showing management failed to disclose known operational issues."),
    (re.compile(r"Profitability Laggard", re.I),
     "Peer-relative profitability laggard status creates analyst downgrade risk and supports 'knew or should have known' scienter allegations -- management of an underperforming company faces heightened disclosure obligations."),
    (re.compile(r"Size Outlier", re.I),
     "Relative size creates asymmetric litigation risk: smaller companies within a peer group face higher per-market-cap legal costs and are more vulnerable to event-driven claims that larger peers could absorb."),
    (re.compile(r"Cash Flow Weakness.*Cross", re.I),
     "Peer-relative cash flow weakness signals company-specific operational problems. When peers generate adequate cash flows but this company cannot, it supports allegations that management concealed fundamental operational deterioration."),

    # ===== FINANCIAL: Temporal =====
    (re.compile(r"Gross.*Operating.*Margin", re.I),
     "Multi-quarter margin compression creates a trend that plaintiffs reconstruct as evidence management concealed deteriorating profitability. The duration of the trend strengthens the 'knew or should have known' scienter inference."),

    # ===== FINANCIAL: Distress =====
    (re.compile(r"Z.Score|Altman", re.I),
     "Distress scores at this level indicate elevated probability of financial difficulty within 2 years. D&O exposure shifts from standard securities fraud theories to creditor-oriented claims including Zone of Insolvency fiduciary expansion."),
    (re.compile(r"Piotroski|F.Score", re.I),
     "Low Piotroski F-Score confirms fundamental weakness across profitability, leverage, and efficiency dimensions -- comprehensive deterioration patterns are strong predictors of future disclosure events that trigger SCA filings."),

    # ===== FINANCIAL: Accounting =====
    (re.compile(r"^Auditor$", re.I),
     "Auditor risk factors increase the probability of audit failure or qualified opinion. Auditor changes, small firm audits, and qualified opinions are among the strongest predictors of future restatements and subsequent SCA filings."),
    (re.compile(r"Internal Controls|Material Weakness", re.I),
     "Internal control deficiencies create the conditions for financial misstatement. Material weaknesses are cited in virtually every restatement-driven SCA as evidence that management was reckless in certifying financial statements under SOX 302/906."),
    (re.compile(r"Restatement History|Repeat Restatement", re.I),
     "Restatement history is the single strongest predictor of future SCA filings. Prior restatements establish a pattern of unreliable financial reporting that strengthens scienter allegations in any subsequent securities fraud claim."),
    (re.compile(r"Restatement Revenue Impact", re.I),
     "Revenue-related restatements generate the highest SCA filing rates and settlement amounts. Revenue restatements directly undermine the reliability of the most-watched financial metric, maximizing damages and class certification probability."),

    # ===== GOVERNANCE: Board =====
    (re.compile(r"Board Independence", re.I),
     "Low board independence reduces the effectiveness of oversight and increases the probability that management self-dealing goes unchecked -- a failure that supports demand futility arguments in derivative actions against directors."),
    (re.compile(r"Overboarding", re.I),
     "Directors serving on excessive boards face attention allocation risk. Overboarded directors are less likely to detect management misconduct, supporting Caremark claims that the board failed in its monitoring obligations."),
    (re.compile(r"(?:Board.*)?Departures", re.I),
     "Board departures during the relevant period signal potential disagreement with management direction. Plaintiffs cite director resignations as evidence that informed insiders lost confidence in the company's disclosures."),
    (re.compile(r"Attendance", re.I),
     "Low board meeting attendance demonstrates a governance culture that tolerates disengaged oversight -- directly supporting Caremark failure-of-monitoring claims in derivative actions."),
    (re.compile(r"Board Member Prior Litigation", re.I),
     "Directors with prior litigation history carry proven exposure patterns. Prior D&O claims against current directors increase both the probability of new claims and the difficulty of settling them."),
    (re.compile(r"(?:Board.*)?Succession|Succession Status", re.I),
     "Inadequate succession planning creates key-person dependency that amplifies stock decline risk on unexpected departures. Departure-triggered drops produce SCAs alleging the company failed to disclose leadership vulnerability."),
    (re.compile(r"^Tenure$", re.I),
     "Extended board tenure creates entrenchment risk and raises questions about director independence from management. Entrenched boards are statistically more likely to face derivative claims alleging failure of oversight duty."),

    # ===== GOVERNANCE: Executive Compensation =====
    (re.compile(r"CEO Profile$", re.I),
     "CEO risk profile concentration means the company's D&O exposure is heavily influenced by a single individual's judgment and conduct. Personal liability theories (insider trading, certification fraud) attach directly to the CEO."),
    (re.compile(r"CFO Profile$", re.I),
     "CFO risk profile is critical because CFOs certify financial statements under SOX 302/906 and are personally liable for material misstatements. CFOs are named individually in virtually every restatement-driven SCA."),
    (re.compile(r"Other Officers Profile", re.I),
     "Officer risk profiles beyond CEO/CFO indicate distributed management exposure. Named officers in SCA complaints face personal liability, and their conduct patterns contribute to the overall scienter calculus."),
    (re.compile(r"Officer Litigation History", re.I),
     "Officers with prior litigation history carry demonstrated exposure patterns. Prior claims against current officers establish a track record that strengthens scienter allegations in subsequent securities fraud complaints."),
    (re.compile(r"Executive Stability", re.I),
     "Executive instability signals organizational dysfunction that increases disclosure risk. Frequent leadership changes disrupt financial reporting continuity and create windows where internal controls are weakened."),
    (re.compile(r"Turnover Analysis|Turnover Pattern", re.I),
     "Executive turnover patterns reveal organizational stress. Clustered departures suggest informed insiders are distancing themselves from anticipated problems -- a pattern plaintiffs cite as consciousness-of-guilt evidence."),
    (re.compile(r"Departure Context", re.I),
     "Executive departure circumstances signal whether exits are voluntary or forced. Forced departures for cause create immediate SCA exposure, while resignations during quiet periods suggest potential concealment awareness."),
    (re.compile(r"Founder Status", re.I),
     "Founder-led companies face concentrated decision-making risk. Founders typically hold outsized voting control and board influence, creating entrenchment exposure and reducing independent oversight effectiveness."),
    (re.compile(r"Key Person Risk", re.I),
     "Key person dependency creates single-point-of-failure risk. If the key person departs, faces legal issues, or makes errors, the stock impact is amplified and plaintiffs allege the company failed to disclose the concentration risk."),
    (re.compile(r"Executive Character.*Conduct", re.I),
     "Executive character and conduct issues create direct personal liability exposure. Personal misconduct triggers independent stock drops and supports scienter allegations that extend to the company's disclosure failures."),

    # ===== GOVERNANCE: Insider Trading =====
    (re.compile(r"Net Insider Sell|Insider Activity Summary", re.I),
     "Net insider selling establishes the 'motive and opportunity' prong of scienter analysis. Courts treat insider sales during the class period as strong evidence that executives traded on material nonpublic information."),
    (re.compile(r"Plan Adoption|10b5-1", re.I),
     "10b5-1 plan adoption timing is scrutinized for manipulation. Plans adopted or modified shortly before adverse disclosures suggest insiders used the plans as cover for informed trading -- a growing area of SEC enforcement."),
    (re.compile(r"Cluster.*(?:Sale|Sell|Timing)", re.I),
     "Clustered insider selling creates a temporal pattern that plaintiffs cite as coordinated informed trading. When multiple insiders sell in the same window before bad news, the inference of shared MNPI is strong."),
    (re.compile(r"Unusual Timing|Timing Suspect", re.I),
     "Unusual insider trading timing relative to material events creates a strong inference of trading on MNPI. Temporal proximity between trades and disclosures is the primary evidence courts evaluate in insider trading claims."),
    (re.compile(r"Executive Sales", re.I),
     "Executive-level sales during the class period are the most scrutinized insider transactions. Courts assign greater weight to C-suite trading patterns because these officers certify financial statements and control disclosure timing."),
    (re.compile(r"Ownership Pct", re.I),
     "Low insider ownership signals weak alignment between management and shareholders. When insiders have little skin in the game, governance failure theories in derivative claims become more compelling to courts."),
    (re.compile(r"Notable Activity", re.I),
     "Notable insider trading activity outside normal patterns creates heightened suspicion of MNPI-based trading. Unusual transaction sizes, timing, or structure draw SEC and plaintiff attention."),
    (re.compile(r"Volume Patterns", re.I),
     "Insider trading volume patterns relative to historical baselines signal potential informed trading. Abnormal volume spikes before material events are primary evidence in SEC enforcement and private securities fraud actions."),

    # ===== GOVERNANCE: Pay =====
    (re.compile(r"Ceo Total", re.I),
     "Excessive CEO total compensation relative to company performance creates say-on-pay activism risk and supports waste claims in derivative litigation against the compensation committee."),
    (re.compile(r"Peer Comparison", re.I),
     "Compensation above peer benchmarks without corresponding performance supports waste and unjust enrichment theories in derivative actions. Compensation committees face heightened scrutiny when pay exceeds peer norms."),
    (re.compile(r"Say-on-Pay", re.I),
     "Low say-on-pay approval signals shareholder dissatisfaction with compensation governance. Failed or low say-on-pay votes frequently precede derivative actions against the board and individual compensation committee members."),
    (re.compile(r"Clawback", re.I),
     "Inadequate clawback provisions signal weak accountability mechanisms. When restatements occur, the absence of enforceable clawbacks becomes evidence of governance failure in derivative claims against the board."),
    (re.compile(r"Related Party$", re.I),
     "Related party transaction exposure creates duty-of-loyalty claims against interested directors under Entire Fairness review. These transactions shift the burden of proof to defendants and are among the most successful derivative claim theories."),
    (re.compile(r"Golden Para", re.I),
     "Excessive golden parachute provisions signal entrenchment and misaligned incentives. These provisions become focal points in change-of-control litigation alleging directors negotiated personal benefits at shareholder expense."),
    (re.compile(r"Equity Burn", re.I),
     "Excessive equity burn rate signals dilutive compensation that transfers value from shareholders to management. High burn rates support waste claims and increase institutional investor activism targeting compensation governance."),
    (re.compile(r"Hedging", re.I),
     "Executive hedging of company stock undermines the alignment purpose of equity compensation. Hedged executives face reduced personal downside, weakening the deterrent effect of equity ownership on risk-taking behavior."),
    (re.compile(r"Exec Loans", re.I),
     "Executive loans from the company create related party exposure and are prohibited for public company executives under SOX Section 402. Any outstanding loans create direct regulatory and derivative claim exposure."),

    # ===== GOVERNANCE: Shareholder Rights =====
    (re.compile(r"Dual Class", re.I),
     "Dual-class share structure concentrates voting control and insulates management from shareholder accountability. Courts give less deference to boards that cannot be meaningfully challenged through the shareholder franchise."),
    (re.compile(r"Takeover", re.I),
     "Anti-takeover provisions entrench current management and reduce market discipline. Entrenched boards face heightened derivative claim exposure under Revlon/Unocal standards when they block value-maximizing transactions."),
    (re.compile(r"Proxy Access", re.I),
     "Restricted proxy access limits shareholder ability to nominate director candidates, reducing board accountability. Governance restrictions that limit shareholder voice support demand futility arguments in derivative actions."),
    (re.compile(r"Supermajority", re.I),
     "Supermajority voting requirements entrench existing governance provisions and prevent shareholders from implementing reforms. This lock-in effect supports claims that the board prioritized self-perpetuation over shareholder interests."),
    (re.compile(r"Action Consent", re.I),
     "Restrictions on shareholder action by written consent limit the ability to act between annual meetings, reducing board accountability and supporting entrenchment theories in derivative claims."),
    (re.compile(r"Special Mtg", re.I),
     "Restrictions on calling special meetings prevent shareholders from forcing timely board consideration of urgent matters, supporting claims that the board structure is designed to insulate management from accountability."),
    (re.compile(r"^Classified$", re.I),
     "Classified board structure prevents shareholders from replacing a majority of directors in a single election, entrenching existing management and reducing the threat of proxy contests that would otherwise discipline governance."),

    # ===== GOVERNANCE: Activist =====
    (re.compile(r"^Campaigns$", re.I),
     "Active activist campaigns signal that sophisticated investors have identified governance or operational failures. Activist involvement frequently precedes SCA filings as campaigns surface previously undisclosed problems."),
    (re.compile(r"Settle Agree", re.I),
     "Activist settlement agreements indicate the company conceded governance changes under pressure. The settlement terms themselves often reveal operational or financial problems that create new disclosure obligations."),
    (re.compile(r"Short Activism", re.I),
     "Short activist campaigns publish detailed research alleging fraud or overvaluation. These reports frequently trigger SCA filings by providing the initial corrective disclosure and establishing a public record of alleged misstatements."),
    (re.compile(r"^Demands$", re.I),
     "Activist demands create public pressure for disclosure and governance changes. Unresolved demands signal ongoing governance disputes that increase the probability of both derivative actions and securities fraud claims."),
    (re.compile(r"Wolf Pack", re.I),
     "Wolf pack formation (multiple activists accumulating positions) signals coordinated pressure for fundamental changes. The accumulation itself may force 13D disclosure events that catalyze SCA attention."),
    (re.compile(r"Board Seat", re.I),
     "Activist board representation creates internal governance tension and potential information asymmetry. Board-level disputes can delay disclosure and create competing fiduciary obligations that complicate D&O claims."),
    (re.compile(r"Dissident", re.I),
     "Dissident proxy solicitation signals fundamental disagreement about company direction. Proxy fights surface governance failures and create disclosure events that frequently trigger parallel SCA filings."),
    (re.compile(r"^Withhold$", re.I),
     "Significant withhold vote campaigns signal broad institutional dissatisfaction with governance. High withhold rates create pressure for board changes and support demand futility in derivative actions."),
    (re.compile(r"^Proposal$", re.I),
     "Shareholder proposals signal governance concerns from the investor base. Proposals that receive significant support create pressure for changes and establish a record that the board was on notice of governance deficiencies."),
    (re.compile(r"^Consent$", re.I),
     "Consent solicitation attempts signal that shareholders are sufficiently motivated to circumvent the annual meeting process. This level of shareholder activism typically reflects serious governance concerns that increase litigation risk."),
    (re.compile(r"Standstill", re.I),
     "Standstill agreement expiration creates a renewed activism window. When standstills expire, the resumption of activist pressure can trigger disclosure events and governance disputes that increase D&O claim probability."),

    # ===== LITIGATION: SCA =====
    (re.compile(r"Class Period$", re.I),
     "Active class period exposure means the company is already subject to SCA claims. D&O policy is being consumed by defense costs, and the class period scope determines the maximum exposure under the fraud-on-the-market theory."),
    (re.compile(r"Allegation Summary", re.I),
     "SCA allegation strength determines settlement probability and range. The specific theories alleged (10b-5 misrepresentation, Section 11 offering fraud, Section 14(a) proxy fraud) define the defense complexity and potential damages."),
    (re.compile(r"Lead Plaintiff", re.I),
     "Lead plaintiff appointment signals the case has survived initial screening and has institutional backing. Institutional lead plaintiffs correlate with higher settlement amounts and lower dismissal rates."),
    (re.compile(r"Case Status$", re.I),
     "Active SCA case status means D&O policy is being consumed. Case progression through motion to dismiss, discovery, and class certification each represents a significant increase in defense costs and settlement leverage for plaintiffs."),
    (re.compile(r"Policy Status", re.I),
     "D&O policy status during active litigation determines available coverage. Policy erosion from defense costs reduces the coverage available for settlement, potentially creating Side A personal liability exposure for directors."),
    (re.compile(r"Derivative Litigation|Derivative Demand", re.I),
     "Derivative litigation creates personal liability exposure for individual directors and officers. Unlike SCAs that target the company, derivative claims allege directors breached fiduciary duties, potentially triggering Side A coverage."),
    (re.compile(r"Merger Objection", re.I),
     "Merger objection litigation is near-automatic in M&A transactions. While often fee-driven, these claims consume D&O coverage and create settlement pressure -- especially when deal terms are later revealed to be unfavorable."),
    (re.compile(r"ERISA Stock Drop", re.I),
     "ERISA stock drop claims allege fiduciary breach in maintaining company stock as a retirement plan option during adverse conditions. These claims run parallel to SCAs and create additional D&O exposure under ERISA fiduciary standards."),

    # ===== LITIGATION: SCA History =====
    (re.compile(r"SCA Database Search", re.I),
     "SCA database search results reveal the company's historical litigation profile. Prior SCA filings are the single strongest predictor of future SCA filings -- repeat defendants face both higher filing rates and larger settlements."),
    (re.compile(r"Prior Settlements", re.I),
     "Prior SCA settlements establish a pricing benchmark for future claims and signal that plaintiff firms view this company as a viable target. Settlement history directly informs D&O pricing and retention analysis."),
    (re.compile(r"Prior Dismissals", re.I),
     "Prior SCA dismissals may indicate effective defense or weak plaintiff theories, but the filing itself consumed defense costs and management attention. Dismissal basis informs vulnerability to future claims on different theories."),
    (re.compile(r"Dismissal Basis", re.I),
     "The legal basis for prior dismissals reveals which SCA theories the company has successfully defended and which theories remain untested -- informing the vulnerability assessment for future claims."),
    (re.compile(r"Historical Suits", re.I),
     "Historical suit frequency and outcomes establish the company's litigation velocity. Companies with frequent historical filings face elevated future filing probability regardless of current governance improvements."),
    (re.compile(r"Pre-Filing Activity", re.I),
     "Pre-filing investigation activity (investigative law firm press releases, shareholder alerts) signals imminent SCA filing. These activities represent the final stage before formal complaint filing."),

    # ===== LITIGATION: Regulatory =====
    (re.compile(r"SEC.*(?:Investigation|Wells|Current Action|Prior Action|Consent Decree)", re.I),
     "SEC enforcement action creates direct D&O exposure through both regulatory penalties and follow-on private litigation. SEC actions are treated as strong evidence in parallel SCA complaints and frequently trigger automatic filings."),
    (re.compile(r"Subpoena", re.I),
     "Government subpoena receipt forces 8-K disclosure and signals active investigation. The disclosure event itself often triggers SCA filings, and the investigation outcome creates additional D&O exposure regardless of resolution."),
    (re.compile(r"Comment Letters", re.I),
     "SEC comment letters signal potential disclosure deficiencies. Unresolved comments that later result in restatements establish that the company was on notice of accounting questions, strengthening scienter in SCA complaints."),
    (re.compile(r"Deferred Pros", re.I),
     "Deferred prosecution agreements indicate the government found violations but offered a compliance path. DPAs create ongoing disclosure obligations and any breach triggers immediate prosecution plus private litigation."),
    (re.compile(r"Wells Notice$", re.I),
     "Wells Notice receipt means SEC staff has recommended enforcement. This creates immediate disclosure obligation under Item 1.05 and triggers SCA filings alleging the underlying conduct constitutes securities fraud."),
    (re.compile(r"Consent Order", re.I),
     "Consent orders represent admitted or uncontested regulatory violations. They create collateral estoppel risk in private litigation where plaintiffs can use the government findings as established facts."),
    (re.compile(r"Cease Desist", re.I),
     "Cease-and-desist orders represent SEC enforcement findings of violation. These orders create admitted facts that plaintiffs use in parallel private securities fraud actions and derivative claims."),
    (re.compile(r"Civil Penalty", re.I),
     "Civil penalties quantify the severity of regulatory violations. Penalty amounts inform private litigation damages calculations and signal the conduct severity that strengthens scienter allegations in SCA complaints."),
    (re.compile(r"State Ag", re.I),
     "State attorney general actions create multi-jurisdictional regulatory exposure. State AG investigations frequently uncover consumer harm that triggers parallel federal securities fraud claims and derivative actions."),
    (re.compile(r"Dol Audit", re.I),
     "DOL audit findings create ERISA fiduciary exposure separate from securities fraud. Benefit plan violations trigger parallel ERISA class actions that consume separate D&O coverage layers."),
    (re.compile(r"Epa Action", re.I),
     "EPA enforcement actions create environmental liability exposure that must be disclosed. Undisclosed environmental liabilities are a common basis for securities fraud claims alleging material omission."),
    (re.compile(r"Osha Citation", re.I),
     "OSHA citations signal workplace safety failures that create personal injury exposure and potential whistleblower retaliation claims -- a growing area of D&O exposure under Dodd-Frank protections."),
    (re.compile(r"Cfpb Action", re.I),
     "CFPB enforcement actions indicate consumer financial protection violations. These actions create large-scale consumer harm that triggers both regulatory penalties and follow-on securities fraud claims."),
    (re.compile(r"Fdic Order", re.I),
     "FDIC orders against financial institutions signal serious safety and soundness concerns. Regulatory orders trigger immediate disclosure obligations and frequently precede shareholder derivative actions."),
    (re.compile(r"Fda Warning", re.I),
     "FDA warning letters signal product safety or compliance failures. In pharma and medical device companies, FDA actions frequently trigger SCA filings alleging management concealed regulatory risks."),
    (re.compile(r"Foreign Gov", re.I),
     "Foreign government enforcement creates multi-jurisdictional D&O exposure. Cross-border regulatory actions trigger FCPA review and disclosure obligations that often precipitate domestic securities fraud claims."),
    (re.compile(r"State Action", re.I),
     "State-level regulatory actions create multi-jurisdictional exposure. Individual state enforcement often reveals practices that trigger federal investigation and parallel private securities fraud actions."),

    # ===== LITIGATION: Other =====
    (re.compile(r"^Product$", re.I),
     "Product liability litigation creates contingent liability exposure that must be reserved and disclosed. Inadequate product liability reserves trigger restatement risk and securities fraud claims when reserves are subsequently increased."),
    (re.compile(r"^Employment$", re.I),
     "Employment litigation creates D&O exposure through class-wide discrimination claims, wage and hour actions, and whistleblower retaliation suits. EEOC actions and large settlements force material disclosure that can trigger SCA filings."),
    (re.compile(r"^Ip$", re.I),
     "Intellectual property litigation creates binary outcome risk. Adverse IP judgments force product changes or licensing payments that constitute material adverse events requiring disclosure and potentially triggering stock declines."),
    (re.compile(r"^Environmental$", re.I),
     "Environmental litigation creates long-tail contingent liability exposure. Inadequate environmental reserves are a common restatement trigger, and Superfund/CERCLA liability can dwarf company market capitalization."),
    (re.compile(r"^Contract$", re.I),
     "Contract litigation at material scale signals counterparty disputes that may indicate revenue recognition issues or concealed business deterioration. Material contract losses require disclosure and impact earnings."),
    (re.compile(r"^Aggregate$", re.I),
     "Aggregate litigation exposure across all active matters creates cumulative contingent liability that may be inadequately reserved. Total litigation reserves are among the most judgment-dependent balance sheet items."),
    (re.compile(r"Class Action$", re.I),
     "Non-SCA class actions (consumer fraud, antitrust, data breach) create material contingent liability exposure. Large class settlements force disclosure events and can trigger parallel securities fraud claims."),
    (re.compile(r"^Antitrust$", re.I),
     "Antitrust litigation creates treble-damages exposure that amplifies financial impact. Government antitrust actions trigger automatic private treble-damages suits and force operational changes that affect earnings."),
    (re.compile(r"Trade Secret$", re.I),
     "Trade secret litigation creates binary risk: injunctions can shut down product lines, and damages awards can be material. Trade secret theft allegations also raise character/conduct concerns for named officers."),
    (re.compile(r"Whistleblower", re.I),
     "Whistleblower claims signal internal allegations of misconduct. Under Dodd-Frank, whistleblower retaliation claims create personal D&O liability, and the underlying allegations often trigger parallel SEC investigation."),
    (re.compile(r"Cyber Breach", re.I),
     "Cyber breach litigation creates immediate disclosure obligations under SEC rules and multi-state notification laws. Data breach SCAs allege management failed to invest in adequate cybersecurity, a growing D&O exposure area."),
    (re.compile(r"^Bankruptcy$", re.I),
     "Bankruptcy-related litigation triggers Zone of Insolvency fiduciary expansion, where directors' duties extend to creditors. Post-petition claims against pre-petition officers create extended D&O tail exposure."),
    (re.compile(r"Foreign Suit", re.I),
     "Foreign lawsuits create jurisdictional complexity and potential uninsured exposure. D&O policies may not cover foreign jurisdictions, creating personal liability gaps for directors of multinational companies."),
    (re.compile(r"Gov Contract", re.I),
     "Government contract disputes trigger False Claims Act exposure with treble damages and potential debarment. Government contract fraud allegations create both regulatory and securities fraud D&O exposure."),
    (re.compile(r"Open Statute of Limitations", re.I),
     "Open statute of limitations windows represent unexpired claim filing opportunities. Pending limitations windows mean potential claims can still be filed -- each open window is a quantifiable probability of future litigation."),

    # ===== EXECUTIVE: Activity =====
    (re.compile(r"CEO Net Seller", re.I),
     "CEO as net seller establishes the strongest motive-and-opportunity scienter evidence. CEOs who sell during the class period face personal insider trading exposure and their sales strengthen the company-wide SCA complaint."),
    (re.compile(r"CFO Net Seller", re.I),
     "CFO as net seller is particularly damaging because CFOs certify financial statements under SOX 302/906. CFO selling during the class period creates strong inference of trading on knowledge of forthcoming adverse financial disclosures."),
    (re.compile(r"Discretionary Selling.*10b5-1", re.I),
     "Discretionary selling outside 10b5-1 plans lacks the affirmative defense of pre-planned trading. Trades made on discretion are subject to full insider trading scrutiny and provide stronger scienter evidence in SCA complaints."),

    # ===== EXECUTIVE: Profile =====
    (re.compile(r"Board Aggregate Risk", re.I),
     "Elevated aggregate board risk score indicates systemic governance weakness across multiple directors. Systemic board risk supports Caremark failure-of-monitoring claims and demand futility arguments in derivative actions."),
    (re.compile(r"Highest Individual Risk.*Threshold", re.I),
     "Individual director risk score exceeding threshold concentrates D&O exposure on a single board member. High-risk individuals face personal liability theories and may compromise the entire board's independence assessment."),
    (re.compile(r"CEO Individual Risk", re.I),
     "CEO individual risk profile directly determines the company's primary D&O exposure. CEOs are named in virtually every SCA complaint and face personal liability under SOX certification requirements."),
    (re.compile(r"CFO Individual Risk", re.I),
     "CFO individual risk profile determines financial reporting exposure. CFOs face personal SOX 302/906 certification liability and are named individually in every restatement-driven SCA complaint."),
    (re.compile(r"CEO Tenure Less Than", re.I),
     "Short CEO tenure increases transition risk and reduces institutional knowledge continuity. New CEOs face heightened SCA exposure as they may make statements about company condition without full operational understanding."),
    (re.compile(r"CFO Tenure Less Than", re.I),
     "Short CFO tenure signals financial reporting continuity risk. New CFOs inherit prior-period financial statements they must certify, creating personal liability for accounting judgments they did not make."),
    (re.compile(r"Multiple C-Suite Departures", re.I),
     "Multiple C-suite departures in a short period signal organizational crisis. Clustered executive departures are treated by courts as strong evidence that informed insiders anticipated adverse disclosures."),
    (re.compile(r"Directors Serving on 4\+", re.I),
     "Directors on 4+ boards face attention allocation challenges that compromise oversight effectiveness. Overboarded directors are more likely to miss management misconduct, supporting Caremark monitoring failure claims."),

    # ===== BUSINESS: Core =====
    (re.compile(r"Litigation History Profile", re.I),
     "Historical litigation profile establishes the company's base claim frequency. Companies with elevated litigation histories face higher future filing rates and are known targets for the plaintiff securities bar."),
    (re.compile(r"Subsidiary.*Count.*Complex|Holding Structure Complex", re.I),
     "Complex corporate structure with numerous subsidiaries creates opacity risk. Multi-entity structures make financial reporting more difficult to verify and provide more opportunities for inter-company transaction manipulation."),

    # ===== BUSINESS: Dependencies =====
    (re.compile(r"Customer Concentration(?! Risk)|Top 5 Customers", re.I),
     "Customer concentration creates binary revenue risk -- loss of a key customer forces material adverse disclosure. Plaintiffs allege management concealed customer relationship deterioration in concentrated revenue models."),
    (re.compile(r"Government Contract Percentage", re.I),
     "Government contract dependence creates regulatory and political risk. Contract cancellations, budget changes, or compliance failures force material disclosure and can trigger securities fraud claims."),
    (re.compile(r"Concentration Risk Composite|Customer Concentration Risk Composite", re.I),
     "Overall concentration risk across customers, suppliers, and products creates compounded vulnerability. Multiple concentration risks interact to amplify the probability and severity of material adverse disclosure events."),
    (re.compile(r"Single.Source.*Supplier|Key Supplier", re.I),
     "Supply chain dependency creates disclosure obligations when suppliers face disruption. Management failure to disclose known supply chain vulnerabilities creates the 'material omission' element for securities fraud claims."),
    (re.compile(r"Supply Chain Complexity", re.I),
     "Complex supply chains increase the probability of disruptions that must be disclosed. Supply chain failures create earnings miss risk and potential allegations that management failed to disclose known vulnerabilities."),
    (re.compile(r"Product Concentration", re.I),
     "Product concentration creates single-product-failure risk. When the key product faces competitive pressure, regulatory issues, or demand shifts, the concentrated exposure amplifies the stock decline and SCA filing probability."),
    (re.compile(r"Key Partnerships", re.I),
     "Key partnership dependency creates material relationship risk. Partnership termination or deterioration forces disclosure events that plaintiffs cite as corrective disclosures in securities fraud complaints."),

    # ===== BUSINESS: Events =====
    (re.compile(r"IPO.*Offering.*Exposure", re.I),
     "IPO/offering exposure windows create Section 11/12 liability under the Securities Act of 1933. These strict liability claims require no scienter proof and have lower dismissal rates than 10b-5 claims."),

    # ===== BUSINESS: Model =====
    (re.compile(r"Key Person Dependency", re.I),
     "Key person dependency creates single-point-of-failure risk at the business model level. Unexpected departures force material disclosure and create SCA exposure alleging the company failed to disclose the concentration risk."),
    (re.compile(r"Segment Lifecycle", re.I),
     "Mature or declining business segments face impairment testing risk. When segment performance deteriorates below carrying value, write-downs trigger the disclosure events that initiate SCA filings."),
    (re.compile(r"Business Model Disruption", re.I),
     "Business model disruption risk creates forward-looking disclosure obligations. When management fails to adequately disclose competitive threats or technology shifts, the subsequent revenue impact triggers 10b-5 claims."),

    # ===== BUSINESS: Operations =====
    (re.compile(r"Subsidiary Jurisdiction", re.I),
     "Multi-jurisdiction subsidiary structure creates FCPA exposure and cross-border regulatory risk. Complex jurisdictional presence increases the probability of regulatory action that triggers D&O disclosure obligations."),
    (re.compile(r"Workforce Distribution", re.I),
     "Workforce distribution creates employment law exposure across multiple jurisdictions. Multi-state workforce creates aggregate employment class action risk that requires disclosure when material."),
    (re.compile(r"Operational Resilience", re.I),
     "Operational resilience weakness signals vulnerability to disruption events. When disruptions occur, inadequate resilience extends recovery time and amplifies earnings impact, increasing SCA filing probability."),

    # ===== DISCLOSURE: 10-K YoY =====
    (re.compile(r"New Risk Factors.*YoY|New Risk Factors Added", re.I),
     "New risk factors in the annual filing signal management has identified emerging threats. If these risks subsequently materialize, plaintiffs allege the risk factor disclosure was inadequate relative to what management actually knew."),
    (re.compile(r"Escalated Risk Factors.*YoY", re.I),
     "Escalated risk factor language signals management acknowledges worsening conditions. Changes in risk factor severity become evidence in SCA complaints that management was aware of deteriorating conditions during the class period."),
    (re.compile(r"Legal Proceedings Change.*YoY", re.I),
     "Changes in legal proceedings disclosure signal evolving litigation exposure. Newly disclosed or escalated legal proceedings create the disclosure timeline that plaintiffs use to establish class period boundaries."),

    # ===== ENVIRONMENT =====
    (re.compile(r"Regulatory Intensity", re.I),
     "Elevated regulatory intensity increases the probability of enforcement actions that trigger disclosure events. Companies in heavily regulated industries face continuous regulatory exposure that compounds SCA filing probability."),
    (re.compile(r"Geopolitical.*Risk", re.I),
     "Geopolitical risk exposure creates sudden-event disclosure risk. Sanctions, trade restrictions, or political instability force material disclosure events that plaintiffs cite when the impact was foreseeable but undisclosed."),
    (re.compile(r"Cyber Risk", re.I),
     "Cyber risk exposure creates disclosure obligations under SEC cybersecurity rules. Data breaches trigger immediate notification requirements and SCA filings alleging inadequate cybersecurity investment and disclosure."),

    # ===== FORWARD: M&A =====
    (re.compile(r"Upcoming Earnings", re.I),
     "Upcoming earnings represent the primary scheduled disclosure event. Earnings misses are the #1 trigger for SCA filings, with 67% of SCAs alleging misstatements in connection with earnings guidance or reporting."),
    (re.compile(r"Guidance Risk", re.I),
     "Guidance risk signals elevated probability of missing stated targets. Guidance misses provide the strongest scienter evidence because management chose to make specific forward-looking statements they failed to meet."),
    (re.compile(r"Covenant Test Date", re.I),
     "Upcoming covenant test dates create scheduled disclosure risk events. Covenant test failures force immediate 8-K disclosure that becomes the corrective disclosure in SCA complaints."),
    (re.compile(r"M&A Closing Date", re.I),
     "Pending M&A closings create automatic merger objection litigation risk. Nearly all material M&A transactions generate shareholder lawsuits challenging deal terms, process, or disclosure adequacy."),
    (re.compile(r"Synergy Realization", re.I),
     "Synergy shortfalls from acquisitions force goodwill impairment write-downs. When stated synergies fail to materialize, plaintiffs allege management overstated deal benefits to secure shareholder approval."),
    (re.compile(r"Customer Retention", re.I),
     "Post-acquisition customer retention failures indicate deal thesis deterioration. Revenue attrition from lost customers creates earnings miss risk and supports claims management overstated acquisition benefits."),
    (re.compile(r"Employee Retention", re.I),
     "Post-acquisition employee retention failures signal integration problems. Key employee departures destroy acquired value and support claims management failed to disclose integration risks in the acquisition proxy."),
    (re.compile(r"^Integration$", re.I),
     "M&A integration risk creates an extended window of operational vulnerability. Integration failures force earnings guidance reductions that trigger SCA filings alleging management overstated synergy and integration projections."),

    # ===== FORWARD: Early Warning =====
    (re.compile(r"Cfpb Complaints", re.I),
     "CFPB complaint volume serves as a leading indicator of regulatory enforcement. Rising complaint trends precede formal CFPB actions that force disclosure and frequently trigger parallel securities fraud claims."),
    (re.compile(r"Legal Hiring", re.I),
     "Unusual legal hiring patterns signal anticipated litigation or regulatory defense needs. Litigation department expansion before public disclosure suggests management awareness of undisclosed legal exposure."),
    (re.compile(r"Partner Stability", re.I),
     "Partnership instability signals business relationship deterioration. Partner departures or disputes create revenue risk that must be disclosed and may indicate broader business model vulnerability."),

    # ===== FORWARD: Sentiment =====
    (re.compile(r"Indeed Reviews", re.I),
     "Deteriorating employee review trends serve as leading indicators of operational problems. Employee dissatisfaction precedes productivity decline, turnover costs, and potential whistleblower complaints that create D&O exposure."),
    (re.compile(r"Blind Posts", re.I),
     "Anonymous employee posts reveal internal conditions before official disclosure. Posts describing financial manipulation, safety violations, or management misconduct can trigger SEC whistleblower investigations."),
    (re.compile(r"Linkedin Departures", re.I),
     "Accelerating LinkedIn departure patterns signal organizational stress visible to the market. Talent flight precedes operational deterioration and may indicate informed insiders are leaving ahead of adverse disclosures."),
    (re.compile(r"G2 Reviews", re.I),
     "Declining product review scores signal customer satisfaction deterioration. Product quality decline precedes revenue impact, creating the timeline that plaintiffs use to allege management concealed deteriorating fundamentals."),
    (re.compile(r"App Ratings", re.I),
     "App rating deterioration provides public evidence of product quality decline. This data creates a timeline showing management should have known about user dissatisfaction before the revenue impact became apparent."),
    (re.compile(r"Social Sentiment", re.I),
     "Social media sentiment deterioration serves as a leading indicator of reputational damage. Viral negative sentiment can trigger stock declines independent of fundamentals, creating event-driven SCA exposure."),

    # ===== NLP =====
    (re.compile(r"MD&A Readability", re.I),
     "Increasing MD&A complexity (higher Fog Index) signals potential obfuscation of negative information. Research shows deteriorating readability correlates with future negative surprises, supporting scienter allegations in SCA complaints."),
    (re.compile(r"MD&A Negative Tone", re.I),
     "MD&A tone shift toward negative language signals management awareness of deteriorating conditions. The timing and magnitude of tone changes become evidence in SCA complaints about when management knew of adverse developments."),
    (re.compile(r"Risk Factor Count Change", re.I),
     "Changes in risk factor count signal evolving threat awareness. Risk factor additions become evidence in SCA complaints that management was on notice of specific risks before the adverse event that triggered the stock decline."),

    # ===== STOCK: Price =====
    (re.compile(r"Chart Comparison", re.I),
     "Stock chart pattern relative to peers and indices reveals whether decline is company-specific or market-wide. Company-specific declines are far more likely to generate SCA filings than market-correlated movements."),
    (re.compile(r"Stock Price Position", re.I),
     "Current stock price position relative to 52-week range quantifies the Disclosure Dollar Loss (DDL) that drives SCA filing economics. Larger declines from highs create larger potential class damages and attract plaintiff firms."),
    (re.compile(r"Price Attribution", re.I),
     "Price decline attribution to specific events identifies the 'corrective disclosure' dates that define SCA class period boundaries. Event-attributed declines have higher SCA filing rates than gradual erosion."),
    (re.compile(r"Peer Relative Performance", re.I),
     "Peer-relative underperformance isolates company-specific risk from market movements. Company-specific stock declines support the loss causation element in SCA complaints by showing the decline was not market-driven."),
    (re.compile(r"Single Day Events", re.I),
     "Single-day stock price events reveal corrective disclosure dates. Large single-day declines create the stock-drop trigger for SCA filings and define the maximum per-share damages under the fraud-on-the-market theory."),
    (re.compile(r"Recovery Analysis", re.I),
     "Stock recovery pattern informs damages calculation in SCA complaints. Non-recovery signals permanent value destruction, while recovery limits damages -- both affect plaintiff filing decisions and settlement negotiations."),
    (re.compile(r"Technical Indicators", re.I),
     "Technical indicators reveal market microstructure patterns. Unusual volume, momentum divergence, or moving average breakdowns can signal informed trading ahead of material disclosures."),
    (re.compile(r"Beta.*Sector", re.I),
     "Company beta relative to sector measures idiosyncratic volatility exposure. Higher beta amplifies stock reactions to disclosure events, increasing the Disclosure Dollar Loss that drives SCA filing economics."),
    (re.compile(r"Extended Drawdown", re.I),
     "Extended drawdown duration signals sustained value destruction that attracts plaintiff attention. Long drawdowns create larger class periods and greater cumulative damages, increasing SCA filing probability."),
    (re.compile(r"Idiosyncratic Volatility", re.I),
     "Idiosyncratic volatility separates company-specific risk from market factors. High idiosyncratic volatility indicates company-specific information is driving price action -- supporting loss causation in SCA complaints."),
    (re.compile(r"Delisting Risk", re.I),
     "Delisting risk creates immediate D&O exposure: delisting announcements trigger SCA filings, and the stock illiquidity post-delisting amplifies shareholder damages and complicates settlement negotiations."),

    # ===== STOCK: Pattern =====
    (re.compile(r"Event Collapse", re.I),
     "Event collapse patterns (large drops on specific disclosure dates) directly identify SCA corrective disclosure dates. Each collapse event is a potential class period endpoint with quantifiable per-share damages."),
    (re.compile(r"Informed Trading", re.I),
     "Informed trading patterns (unusual volume/price action before disclosures) signal potential MNPI leakage. These patterns support insider trading theories in SCA complaints and attract SEC market surveillance attention."),
    (re.compile(r"Cascade Pattern", re.I),
     "Cascading stock declines across multiple disclosure events create a drip pattern that extends the SCA class period. Extended class periods increase cumulative damages and strengthen scienter by showing repeated misstatements."),
    (re.compile(r"Peer Divergence Pattern", re.I),
     "Peer divergence patterns isolate company-specific value destruction from sector trends. Peer-divergent declines provide the strongest loss causation evidence in SCA complaints by eliminating confounding market factors."),
    (re.compile(r"Death Spiral", re.I),
     "Death spiral patterns (declining price with increasing short interest) signal market consensus on fundamental deterioration. This pattern concentrates D&O exposure as distressed companies face expanded creditor fiduciary duties."),
    (re.compile(r"Short Attack", re.I),
     "Short attack patterns (coordinated selling with public short reports) create event-driven stock drops. Short reports serve as alternative corrective disclosures that trigger SCA filings against the company and its officers."),

    # ===== STOCK: Short Interest =====
    (re.compile(r"Short Interest Position", re.I),
     "Elevated short interest signals informed market participants are positioned for decline. High short interest amplifies downside volatility on negative disclosures, increasing Disclosure Dollar Loss and SCA filing probability."),
    (re.compile(r"^Trend$", re.I),
     "Sustained negative trends create a disclosure timeline that plaintiffs use to establish when management 'knew or should have known' about deteriorating conditions, forming the scienter element in 10b-5 claims."),
    (re.compile(r"^Report$", re.I),
     "Published short seller reports create independent corrective disclosure events. Short reports frequently trigger SCA filings and SEC investigations by making detailed fraud allegations public."),

    # ===== STOCK: Ownership =====
    (re.compile(r"Pe Ratio$", re.I),
     "Elevated P/E ratio creates heightened earnings miss exposure. Higher-multiple stocks experience larger percentage declines on earnings disappointments, increasing the Disclosure Dollar Loss that triggers SCA filings."),
    (re.compile(r"Ev Ebitda", re.I),
     "Elevated EV/EBITDA valuation creates 'fall-from-grace' risk. Premium-valued companies face amplified stock reactions to negative surprises, increasing the DDL magnitude that drives SCA filing economics."),
    (re.compile(r"Premium Discount", re.I),
     "Valuation premium relative to peers creates elevated expectations risk. When reality fails to justify the premium, the resulting re-rating triggers SCA filings alleging management inflated expectations through misleading statements."),
    (re.compile(r"Peg Ratio", re.I),
     "Elevated PEG ratio signals the market is pricing growth that may not materialize. Growth disappointments in high-PEG stocks produce larger stock declines and higher SCA filing rates."),

    # ===== ANALYST/PEER VALUATION =====
    (re.compile(r"Peer Valuation Gap", re.I),
     "Peer valuation gap at this level signals the market views this company as fundamentally weaker than peers. When the valuation gap widens further, the resulting stock decline creates SCA filing exposure."),
    (re.compile(r"Analyst Estimate Revision", re.I),
     "Analyst estimate revision patterns signal the market is reassessing company fundamentals. Downward revision trends frequently precede earnings misses that trigger SCA filings."),

    # ===== ADDITIONAL MAPPINGS (discovered during dry-run) =====

    # Business core
    (re.compile(r"Primary D&O Risk Classification", re.I),
     "Primary risk classification determines the dominant D&O exposure theory for this company. The classification drives which claim types are most likely and informs policy structure and retention recommendations."),
    (re.compile(r"Secondary Risk Classification", re.I),
     "Secondary risk classification identifies additional D&O exposure theories beyond the primary classification. Multiple active risk categories compound litigation probability and complicate defense strategy."),
    (re.compile(r"Market Capitalization", re.I),
     "Market capitalization determines SCA filing economics -- larger market caps create larger potential damages, attracting top plaintiff firms. Market cap also determines insurance tower adequacy and retention levels."),
    (re.compile(r"Related.Party Transaction.*Complex|Related Party Transaction Density", re.I),
     "Related party transaction complexity creates duty-of-loyalty exposure under Entire Fairness review. Complex or numerous related party transactions increase the probability of self-dealing claims in derivative actions."),

    # Business events
    (re.compile(r"M&A Activity Risk", re.I),
     "Active M&A creates automatic merger objection litigation risk. Nearly every material transaction generates shareholder lawsuits challenging deal terms, board process, or proxy disclosure adequacy."),
    (re.compile(r"Capital Structure Change", re.I),
     "Capital structure changes create disclosure obligations and may dilute existing shareholders. Debt issuance, equity offerings, or conversions force material disclosures that become SCA corrective disclosure dates."),
    (re.compile(r"Business Pivots.*Restructurings", re.I),
     "Business pivots and restructurings create write-down risk and operational disruption. Restructuring charges trigger SCA filings when plaintiffs allege management concealed the deterioration that necessitated the pivot."),

    # Business model
    (re.compile(r"Revenue Model Type", re.I),
     "Revenue model type determines the applicable accounting standards and recognition timing risks. Certain models (long-term contracts, subscription, percentage-of-completion) carry inherently higher restatement risk."),
    (re.compile(r"Revenue Mix by Segment", re.I),
     "Revenue segment mix determines which parts of the business carry the highest disclosure risk. Segment-level performance misses trigger SCA filings when plaintiffs allege management concealed deterioration in specific segments."),
    (re.compile(r"Revenue Mix by Geography", re.I),
     "Geographic revenue mix creates jurisdiction-specific regulatory and litigation exposure. Concentrated international revenue increases FCPA risk and cross-border disclosure obligations."),
    (re.compile(r"Revenue Concentration Risk", re.I),
     "Revenue concentration creates binary risk -- loss of a major revenue source forces material adverse disclosure. Concentrated revenue models amplify the stock decline from any single customer or product setback."),
    (re.compile(r"Segment Margin Profile", re.I),
     "Segment margin profile reveals which business units are subsidizing others. When low-margin segments drag down consolidated results, plaintiffs allege management concealed segment-level weakness."),

    # Business operations
    (re.compile(r"Operational Complexity Score", re.I),
     "Operational complexity increases the probability of internal control failures and financial reporting errors. Complex operations create more opportunities for misstatement and make audit verification more difficult."),

    # Business structural
    (re.compile(r"Disclosure Complexity Score", re.I),
     "Disclosure complexity creates information asymmetry between management and investors. Complex disclosures increase the probability that material information is obscured, supporting 'material omission' claims in SCAs."),

    # Disclosure
    (re.compile(r"Removed Risk Factors.*YoY", re.I),
     "Removed risk factors may signal premature de-risking. If the removed risk subsequently materializes, plaintiffs allege management deliberately removed the warning to inflate stock price."),

    # Environment
    (re.compile(r"ESG Commitment.Action Gap", re.I),
     "ESG commitment-action gaps create greenwashing exposure. When stated ESG commitments are not supported by actual practices, shareholders file derivative claims and securities fraud actions alleging misleading ESG disclosures."),
    (re.compile(r"Macroeconomic Sensitivity", re.I),
     "Elevated macroeconomic sensitivity means external economic shocks disproportionately impact this company. When macro events trigger stock declines, plaintiffs allege management failed to disclose the sensitivity."),

    # Accounting
    (re.compile(r"Sec Correspondence", re.I),
     "SEC correspondence reveals regulatory questions about financial reporting. Comment letters that result in restatements establish the company was on notice of accounting issues, strengthening scienter in subsequent SCA complaints."),

    # Forensic
    (re.compile(r"Cash Flow Quality Score", re.I),
     "Cash flow quality deterioration signals potential earnings manipulation. Divergence between reported earnings and cash generation is the strongest forensic predictor of future restatement and SCA filing."),

    # Temporal
    (re.compile(r"Revenue Growth Deceleration", re.I),
     "Revenue growth deceleration creates analyst downgrade risk and suggests management growth projections were overstated. When deceleration persists, plaintiffs allege management concealed slowing fundamentals while maintaining growth guidance."),
    (re.compile(r"Days Sales Outstanding Expansion", re.I),
     "DSO expansion signals deteriorating receivables collection, a classic revenue quality warning. Rising DSO is a Beneish M-Score component that indicates potential revenue inflation or aggressive credit extension."),
    (re.compile(r"Cash Flow.*Net Income Divergence", re.I),
     "Cash flow / net income divergence is the strongest forensic indicator of earnings manipulation. When cash flows fail to confirm reported earnings, restatement risk increases and plaintiffs cite the divergence as evidence of scienter."),
    (re.compile(r"Working Capital Deterioration|Working Capital Trends", re.I),
     "Working capital deterioration signals approaching liquidity stress. Sustained deterioration creates going-concern risk and forces the disclosure events that trigger SCA filings."),
    (re.compile(r"Leverage Ratio Increase", re.I),
     "Rising leverage signals deteriorating financial flexibility. Leverage increases create covenant breach risk and force disclosure of debt capacity constraints that plaintiffs cite in securities fraud complaints."),
    (re.compile(r"Operating Cash Flow Deterioration", re.I),
     "Operating cash flow deterioration signals core business weakness. When operating cash flows decline while earnings are maintained, it indicates potential earnings manipulation through accruals."),

    # Forward M&A
    (re.compile(r"Contract Renewal Dates", re.I),
     "Upcoming contract renewal dates create binary outcome risk. Non-renewal of material contracts forces disclosure and earnings impact that triggers SCA filings alleging management concealed relationship deterioration."),
    (re.compile(r"Regulatory Decision Dates", re.I),
     "Pending regulatory decisions create binary outcome risk. Adverse regulatory decisions force material disclosure and frequently trigger SCA filings alleging management overstated regulatory approval likelihood."),
    (re.compile(r"Litigation Milestones", re.I),
     "Upcoming litigation milestones create binary outcome risk. Adverse rulings force reserve increases and disclosure that trigger additional SCA filings or settlement pressure."),

    # Forward warnings
    (re.compile(r"Fda Medwatch", re.I),
     "FDA MedWatch reports serve as leading indicators of product safety actions. Rising adverse event reports precede FDA enforcement that triggers SCA filings alleging concealment of product safety risks."),
    (re.compile(r"Nhtsa Complaints", re.I),
     "NHTSA complaint volume serves as a leading indicator of recall actions. Recall announcements trigger SCA filings alleging management knew about safety defects before public disclosure."),
    (re.compile(r"Vendor Payment Delays", re.I),
     "Vendor payment delays signal cash flow stress visible to the supply chain before public markets. Trade credit deterioration is a leading indicator of liquidity crisis that must eventually be disclosed."),
    (re.compile(r"Compliance Hiring", re.I),
     "Unusual compliance hiring signals anticipated regulatory defense needs. Compliance department expansion before public disclosure suggests management awareness of undisclosed regulatory exposure."),
    (re.compile(r"Zone Of Insolvency", re.I),
     "Zone of Insolvency proximity triggers fiduciary duty expansion to creditors. Directors face personal liability for decisions that favor shareholders over creditors when the company approaches insolvency."),
    (re.compile(r"Goodwill Risk", re.I),
     "Forward-looking goodwill impairment risk signals upcoming write-down exposure. Goodwill write-downs trigger SCA filings alleging management knew acquisitions were overvalued at the time of the deal."),
    (re.compile(r"Impairment Risk", re.I),
     "Forward-looking impairment risk indicates upcoming asset write-down exposure. Impairment charges trigger SCA filings when plaintiffs allege management delayed recognition of indicators they were required to monitor."),
    (re.compile(r"Contract Disputes", re.I),
     "Active contract disputes signal revenue and counterparty risk that must be disclosed. Material contract losses create earnings impact and potential SCA exposure if the dispute was not adequately disclosed."),
    (re.compile(r"Customer Churn", re.I),
     "Customer churn signals serve as leading indicators of revenue deterioration. Rising churn precedes earnings misses and supports SCA allegations that management concealed customer relationship deterioration."),
    (re.compile(r"Margin Pressure", re.I),
     "Forward-looking margin pressure signals upcoming earnings compression. When margins subsequently compress, plaintiffs allege management concealed cost pressures while maintaining profitability guidance."),
    (re.compile(r"Capex Discipline", re.I),
     "Capex discipline concerns signal potential capital misallocation. Undisciplined capital spending creates future impairment risk and supports waste claims in derivative actions against the board."),

    # Sentiment
    (re.compile(r"Glassdoor Sentiment", re.I),
     "Glassdoor sentiment deterioration serves as a leading indicator of operational problems. Employee dissatisfaction precedes turnover, productivity decline, and potential whistleblower complaints that create D&O exposure."),
    (re.compile(r"Linkedin Headcount", re.I),
     "LinkedIn headcount changes reveal hiring or layoff patterns before official announcement. Visible workforce reductions signal operational stress that should be disclosed under Item 2.05."),
    (re.compile(r"Trustpilot Trend", re.I),
     "Trustpilot trend deterioration signals customer satisfaction decline. Consumer complaint patterns precede revenue impact and regulatory attention, creating the timeline plaintiffs use in SCA complaints."),
    (re.compile(r"Journalism Activity", re.I),
     "Investigative journalism activity signals potential upcoming adverse disclosure. Published investigations frequently trigger SCA filings by serving as corrective disclosures independent of company announcements."),
    (re.compile(r"Job Posting Patterns", re.I),
     "Unusual job posting patterns reveal organizational changes before official disclosure. Rapid hiring in legal or compliance roles or sudden posting freezes signal anticipated adverse events."),

    # Governance board
    (re.compile(r"Board Member Qualifications.*Experience", re.I),
     "Director qualification gaps increase the probability of oversight failures. Directors lacking relevant expertise are less likely to detect management misconduct, supporting Caremark failure-of-monitoring claims."),
    (re.compile(r"Board Member Character.*Conduct", re.I),
     "Director character and conduct issues create direct personal liability exposure and compromise board credibility. Courts give less deference to boards where individual directors have proven integrity concerns."),
    (re.compile(r"^Meetings$", re.I),
     "Inadequate board meeting frequency signals governance culture that tolerates infrequent oversight. Courts evaluate meeting frequency as evidence of whether the board fulfilled its Caremark monitoring duties."),

    # Governance insider
    (re.compile(r"Ownership Concentration", re.I),
     "Concentrated insider ownership creates control-person liability and raises Revlon concerns in change-of-control transactions. Controlling shareholders face heightened fiduciary duties under Entire Fairness review."),
    (re.compile(r"Exercise And Sell", re.I),
     "Option exercise-and-sell patterns signal insiders are monetizing equity while the stock is elevated. This pattern provides strong motive-and-opportunity evidence in scienter analysis for SCA complaints."),

    # Governance activist
    (re.compile(r"13D Filing", re.I),
     "13D filings signal activist accumulation of significant positions. The filing itself creates a disclosure event and frequently precedes campaigns that surface governance problems and trigger SCA filings."),
    (re.compile(r"Proxy Contest", re.I),
     "Proxy contests create governance disruption and force extensive disclosure about board performance. Contest-related disclosures frequently trigger parallel SCA filings based on newly revealed information."),

    # Litigation defense
    (re.compile(r"Contingent Liabilities.*ASC 450", re.I),
     "ASC 450 contingent liability disclosure is among the most judgment-dependent accounting areas. Inadequate loss contingency reserves are a common restatement trigger and a frequent SCA allegation basis."),
    (re.compile(r"Applicable Industry Allegation", re.I),
     "Industry-specific allegation theories define the most likely SCA claim types for this company. Understanding applicable theories informs D&O underwriting, policy structure, and retention analysis."),
    (re.compile(r"Peer Lawsuit Contagion", re.I),
     "Peer lawsuit contagion risk means SCA filings against industry peers create filing momentum. When one company in a sector is sued, plaintiff firms investigate similar companies for analogous claims."),
    (re.compile(r"Financial Event.*Stock Drop.*Class Period", re.I),
     "Financial event / stock drop windows represent specific time periods where class period exposure has been created. Each identified window quantifies potential SCA damages and filing probability."),
    (re.compile(r"Sector.Specific Litigation Pattern", re.I),
     "Sector-specific litigation patterns identify recurring claim types in this industry. Historical sector litigation patterns strongly predict future filing probability and settlement ranges for similarly-situated companies."),
    (re.compile(r"Sector.Specific Regulatory", re.I),
     "Sector-specific regulatory database checks reveal industry-targeted enforcement patterns. Regulatory focus on specific sectors amplifies filing probability for all companies in the targeted industry."),

    # Litigation reg agency
    (re.compile(r"SEC Penalties", re.I),
     "SEC penalty history quantifies prior enforcement severity. Penalty amounts establish precedent for future enforcement and signal the SEC views this company as a repeat or serious offender."),

    # Litigation SCA
    (re.compile(r"Filing Date", re.I),
     "SCA filing date determines the statute of limitations and class period timing. Filing date proximity to disclosure events informs the strength of plaintiff theories about the corrective disclosure chain."),
    (re.compile(r"Exposure Estimate", re.I),
     "SCA exposure estimate quantifies the financial risk from active litigation. Exposure magnitude directly impacts D&O policy adequacy analysis and determines whether current limits are sufficient."),
    (re.compile(r"Settlement Amount", re.I),
     "Prior settlement amounts establish pricing benchmarks for future claims. Settlement history is the strongest predictor of future settlement ranges and directly informs D&O pricing and retention analysis."),

    # NLP
    (re.compile(r"Critical Audit Matters", re.I),
     "Changes in Critical Audit Matters signal evolving areas of accounting complexity. New or modified CAMs indicate the auditor has identified areas of heightened misstatement risk, which plaintiffs cite in SCA complaints."),

    # Stock price
    (re.compile(r"Recent Drop Alert", re.I),
     "Recent stock drop alert identifies potential corrective disclosure events within the monitored period. Large recent drops are the primary trigger for plaintiff firm investigation and SCA filing decisions."),
    (re.compile(r"Returns Multi Horizon", re.I),
     "Multi-horizon return analysis reveals whether stock weakness is short-term event-driven or sustained fundamental deterioration. Sustained underperformance creates larger cumulative DDL and higher SCA filing probability."),
    (re.compile(r"Unexplained Stock Drop", re.I),
     "Unexplained stock drops suggest information leakage or market discovery of undisclosed problems. Drops without corresponding public disclosure create the strongest inference that management withheld material information."),
]


def extract_signal_name(template_text: str) -> str | None:
    """Extract the signal name from a TRIGGERED_RED template string."""
    m = re.search(r"\{company\}\s+(.+?)\s+at\s+\{value\}", template_text, re.DOTALL)
    if m:
        # Normalize whitespace (YAML folding adds spaces/newlines)
        return re.sub(r"\s+", " ", m.group(1).strip())
    return None


def find_replacement(signal_name: str) -> str | None:
    """Find the D&O mechanism replacement text for a given signal name."""
    for pattern, mechanism in SIGNAL_DO_MECHANISMS:
        if pattern.search(signal_name):
            return mechanism
    return None


def process_file(filepath: str, dry_run: bool = False) -> tuple[int, int, list[str]]:
    """Process a single YAML file, replacing boilerplate D&O language.

    Strategy: normalize the file content to handle multi-line YAML strings,
    find each TRIGGERED_RED block, extract signal name, and replace boilerplate.
    """
    with open(filepath) as f:
        content = f.read()

    if BOILERPLATE_LITERAL not in content:
        return 0, 0, []

    replacements = 0
    failures = 0
    unmatched: list[str] = []

    # Find all TRIGGERED_RED template blocks that contain the boilerplate.
    # We work with the raw file content and use a callback-based replacement.
    # The regex matches the full "This [risk_type] has historically..." sentence.

    def replace_match(match: re.Match[str]) -> str:
        nonlocal replacements, failures

        # To find the signal name, we need context before this match.
        # Look backward in the content to find the TRIGGERED_RED key and
        # the {company} ... at {value} pattern.
        start = match.start()
        # Search backward up to 500 chars for the signal name
        lookback = content[max(0, start - 500):start]
        signal_name = extract_signal_name(lookback)

        if signal_name:
            mechanism = find_replacement(signal_name)
            if mechanism:
                replacements += 1
                # Check if we're inside a YAML single-quoted string.
                # Look backward for the enclosing quote character.
                # If inside single quotes, escape any single quotes in replacement.
                pre = content[max(0, start - 600):start]
                # Find the TRIGGERED_RED line to determine quoting style
                tr_idx = pre.rfind("TRIGGERED_RED:")
                if tr_idx >= 0:
                    after_key = pre[tr_idx + len("TRIGGERED_RED:"):]
                    stripped = after_key.lstrip()
                    if stripped.startswith("'"):
                        # Inside a single-quoted YAML string -- escape single quotes
                        mechanism = mechanism.replace("'", "''")
                return mechanism
            else:
                failures += 1
                unmatched.append(signal_name)
                return match.group(0)  # leave unchanged
        else:
            failures += 1
            unmatched.append("(could not extract name)")
            return match.group(0)

    new_content = BOILERPLATE_RE.sub(replace_match, content)

    if not dry_run and replacements > 0:
        with open(filepath, "w") as f:
            f.write(new_content)

    return replacements, failures, unmatched


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix boilerplate D&O language in brain YAML signals")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without writing")
    args = parser.parse_args()

    yaml_files = sorted(glob.glob("src/do_uw/brain/signals/**/*.yaml", recursive=True))

    total_replaced = 0
    total_failed = 0
    all_unmatched: list[str] = []
    files_modified = 0

    for filepath in yaml_files:
        replaced, failed, unmatched = process_file(filepath, dry_run=args.dry_run)
        if replaced > 0 or failed > 0:
            status = "DRY-RUN" if args.dry_run else "MODIFIED"
            print(f"  [{status}] {filepath}: {replaced} replaced, {failed} failed")
            if unmatched:
                for name in unmatched:
                    print(f"    UNMATCHED: {name}")
        if replaced > 0:
            files_modified += 1
        total_replaced += replaced
        total_failed += failed
        all_unmatched.extend(unmatched)

    print(f"\n{'DRY RUN ' if args.dry_run else ''}Summary:")
    print(f"  Files processed: {len(yaml_files)}")
    print(f"  Files modified: {files_modified}")
    print(f"  Replacements: {total_replaced}")
    print(f"  Failures: {total_failed}")

    if all_unmatched:
        print(f"\n  Unmatched signals ({len(all_unmatched)}):")
        for name in sorted(set(all_unmatched)):
            print(f"    - {name}")
        sys.exit(1)

    if total_replaced == 0:
        print("\n  No boilerplate found -- nothing to do.")
    else:
        print(f"\n  Successfully replaced {total_replaced} boilerplate instances.")


if __name__ == "__main__":
    main()
