#!/usr/bin/env python3
"""Test LLMExtractor with DeepSeek."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from do_uw.stages.extract.llm.extractor import LLMExtractor
from do_uw.stages.extract.llm.schemas.ten_k import TenKExtraction

# Sample filing text (simplified)
sample_text = """
UNITED STATES SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20549

FORM 10-K

ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934
For the fiscal year ended December 31, 2023

Commission file number 001-12345

SAMPLE CORPORATION
(Exact name of registrant as specified in its charter)

Delaware                          1234                 12-3456789
(State or other jurisdiction of   (Primary Standard    (IRS Employer
incorporation or organization)    Industrial           Identification No.)
                                  Classification Code)

123 Main Street, Anytown, CA 12345
(Address of principal executive offices)

Registrant's telephone number: (123) 456-7890

Securities registered pursuant to Section 12(b) of the Act:

Title of each class:      Common Stock, $0.01 par value
Trading Symbol:           SAMP
Name of each exchange on which registered: NASDAQ

Securities registered pursuant to Section 12(g) of the Act: None

Indicate by check mark if the registrant is a well‑known seasoned issuer, as defined in Rule 405 of the Securities Act. Yes ☐ No ☒

Indicate by check mark if the registrant is not required to file reports pursuant to Section 13 or Section 15(d) of the Act. Yes ☐ No ☒

Indicate by check mark whether the registrant (1) has filed all reports required to be filed by Section 13 or 15(d) of the Securities Exchange Act of 1934 during the preceding 12 months (or for such shorter period that the registrant was required to file such reports), and (2) has been subject to such filing requirements for the past 90 days. Yes ☒ No ☐

Indicate by check mark whether the registrant has submitted electronically every Interactive Data File required to be submitted pursuant to Rule 405 of Regulation S‑T (§232.405 of this chapter) during the preceding 12 months (or for such shorter period that the registrant was required to submit such files). Yes ☒ No ☐

Indicate by check mark whether the registrant is a large accelerated filer, an accelerated filer, a non‑accelerated filer, a smaller reporting company, or an emerging growth company. See the definitions of “large accelerated filer,” “accelerated filer,” “smaller reporting company,” and “emerging growth company” in Rule 12b‑2 of the Exchange Act.

Large accelerated filer ☐   Accelerated filer ☒   Non‑accelerated filer ☐
Smaller reporting company ☐   Emerging growth company ☐

If an emerging growth company, indicate by check mark if the registrant has elected not to use the extended transition period for complying with any new or revised financial accounting standards provided pursuant to Section 13(a) of the Exchange Act. ☐

Indicate by check mark whether the registrant has filed a report on and attestation to its management’s assessment of the effectiveness of its internal control over financial reporting under Section 404(b) of the Sarbanes‑Oxley Act (15 U.S.C. 7262(b)) by the registered public accounting firm that prepared or issued its audit report. ☒

Indicate by check mark whether the registrant is a shell company (as defined in Rule 12b‑2 of the Exchange Act). Yes ☐ No ☒

Aggregate market value of the voting and non‑voting common equity held by non‑affiliates of the registrant as of June 30, 2023: $1,234,567,890

Number of shares of registrant’s common stock outstanding as of February 28, 2024: 100,000,000

DOCUMENTS INCORPORATED BY REFERENCE

Portions of the registrant’s definitive proxy statement for the 2024 Annual Meeting of Stockholders are incorporated by reference into Part III of this Annual Report on Form 10‑K.

TABLE OF CONTENTS

PART I

Item 1. Business

Sample Corporation is a leading provider of sample products and services. We were incorporated in Delaware in 2010. Our principal executive offices are located at 123 Main Street, Anytown, CA 12345.

Item 1A. Risk Factors

Our business is subject to numerous risks, including market competition, regulatory changes, and dependence on key personnel.

Item 1B. Unresolved Staff Comments

None.

Item 2. Properties

We lease approximately 50,000 square feet of office space in Anytown, CA.

Item 3. Legal Proceedings

We are not party to any material legal proceedings.

Item 4. Mine Safety Disclosures

Not applicable.

PART II

Item 5. Market for Registrant’s Common Equity, Related Stockholder Matters and Issuer Purchases of Equity Securities

Our common stock is traded on NASDAQ under the symbol SAMP. The high and low sales prices for our common stock during each fiscal quarter of 2023 were as follows:

Quarter        High       Low
Q1             $25.00     $20.00
Q2             $28.00     $22.00
Q3             $30.00     $25.00
Q4             $32.00     $28.00

As of February 28, 2024, there were approximately 1,000 holders of record of our common stock.

Item 6. Selected Financial Data

Not applicable.

Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations

We generated total revenue of $500 million in fiscal year 2023, compared to $450 million in 2022. Net income was $50 million in 2023, compared to $40 million in 2022.

Item 7A. Quantitative and Qualitative Disclosures About Market Risk

Not applicable.

Item 8. Financial Statements and Supplementary Data

Consolidated Statements of Income
For the Years Ended December 31, 2023 and 2022
(in thousands, except per share data)

                                  2023       2022
Revenue                          $500,000   $450,000
Cost of revenue                   300,000    270,000
Gross profit                      200,000    180,000
Operating expenses                120,000    110,000
Operating income                   80,000     70,000
Interest expense                    5,000      4,000
Income before income taxes         75,000     66,000
Provision for income taxes         25,000     26,000
Net income                        $50,000    $40,000

Basic earnings per share           $0.50      $0.40
Diluted earnings per share         $0.48      $0.38

Item 9. Changes in and Disagreements with Accountants on Accounting and Financial Disclosure

None.

Item 9A. Controls and Procedures

Disclosure controls and procedures are effective.

Item 9B. Other Information

None.

Item 9C. Disclosure Regarding Foreign Jurisdictions that Prevent Inspections

Not applicable.

PART III

Item 10. Directors, Executive Officers and Corporate Governance

Our board of directors consists of 7 members, 5 of whom are independent.

Item 11. Executive Compensation

Total compensation for our named executive officers in 2023 was $10 million.

Item 12. Security Ownership of Certain Beneficial Owners and Management and Related Stockholder Matters

Directors and executive officers own approximately 15% of our outstanding common stock.

Item 13. Certain Relationships and Related Transactions, and Director Independence

We have transactions with related parties as disclosed in our proxy statement.

Item 14. Principal Accountant Fees and Services

Fees paid to our independent auditor in 2023 were $2 million.

PART IV

Item 15. Exhibits and Financial Statement Schedules

The exhibits listed in the Exhibit Index are filed as part of this Annual Report.

Item 16. Form 10‑K Summary

None.
"""


def main():
    print("Testing LLMExtractor with DeepSeek...")

    # Check API key
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("ERROR: DEEPSEEK_API_KEY not set")
        return

    # Create extractor
    extractor = LLMExtractor(
        model="openai/deepseek-chat",
        budget_usd=1.0,  # Small budget for test
    )

    # System prompt (simplified)
    system_prompt = (
        """You are an expert SEC filing analyst. Extract structured data from the 10-K filing."""
    )

    print("Extracting...")
    result = extractor.extract(
        filing_text=sample_text,
        schema=TenKExtraction,
        accession="0001234567-23-123456",
        form_type="10-K",
        system_prompt=system_prompt,
        max_tokens=2000,
    )

    if result:
        print("SUCCESS: Extraction completed!")
        print(f"Company name: {getattr(result, 'company_name', 'N/A')}")
        print(f"Revenue: {getattr(result, 'revenue', 'N/A')}")
        print(f"Net income: {getattr(result, 'net_income', 'N/A')}")
        print(f"Shares outstanding: {getattr(result, 'shares_outstanding', 'N/A')}")
    else:
        print("FAILED: Extraction returned None")
        print("Check logs for errors")


if __name__ == "__main__":
    main()
