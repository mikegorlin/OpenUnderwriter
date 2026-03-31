#!/usr/bin/env python3
"""Comprehensive yfinance data audit for a given ticker.

Dumps ALL available attributes, their types, shapes, and sample data
to help identify what we're pulling vs what's available.
"""

import json
import sys
from datetime import datetime

import yfinance as yf


def safe_repr(obj, max_len=200):
    """Safe repr with truncation."""
    try:
        r = repr(obj)
        if len(r) > max_len:
            return r[:max_len] + "..."
        return r
    except Exception as e:
        return f"<error: {e}>"


def describe_df(df, name):
    """Describe a DataFrame."""
    if df is None:
        return {"type": "None"}
    if hasattr(df, "empty"):
        if df.empty:
            return {"type": "DataFrame", "empty": True}
        return {
            "type": "DataFrame",
            "shape": list(df.shape),
            "columns": list(df.columns)[:20],
            "index_sample": [str(x) for x in list(df.index)[:5]],
            "dtypes": {str(k): str(v) for k, v in df.dtypes.items()},
            "head": df.head(3).to_string(),
        }
    return {"type": str(type(df).__name__), "value": safe_repr(df)}


def audit_ticker(ticker_symbol: str):
    """Run comprehensive audit of yfinance data."""
    t = yf.Ticker(ticker_symbol)
    results = {}

    # 1. Info dict - the big one
    print(f"\n{'='*80}")
    print(f"YFINANCE AUDIT: {ticker_symbol}")
    print(f"{'='*80}\n")

    print("## 1. INFO DICT (ticker.info)")
    print("-" * 60)
    try:
        info = t.info
        if isinstance(info, dict):
            results["info_keys"] = sorted(info.keys())
            print(f"Total keys: {len(info)}")

            # Group by category
            categories = {
                "Identity": ["shortName", "longName", "symbol", "exchange", "quoteType", "market", "currency", "financialCurrency"],
                "Sector/Industry": ["sector", "sectorKey", "industry", "industryKey", "sectorDisp", "industryDisp"],
                "Price": ["currentPrice", "previousClose", "open", "dayLow", "dayHigh", "regularMarketPrice", "regularMarketOpen", "regularMarketDayHigh", "regularMarketDayLow", "regularMarketVolume"],
                "52-Week": ["fiftyTwoWeekLow", "fiftyTwoWeekHigh", "fiftyTwoWeekChange", "SandP52WeekChange", "52WeekChange"],
                "Moving Averages": ["fiftyDayAverage", "twoHundredDayAverage"],
                "Market Cap": ["marketCap", "enterpriseValue"],
                "Volume": ["volume", "averageVolume", "averageVolume10days", "averageDailyVolume10Day"],
                "Valuation Ratios": ["trailingPE", "forwardPE", "priceToSalesTrailing12Months", "priceToBook", "enterpriseToRevenue", "enterpriseToEbitda", "pegRatio", "trailingPegRatio"],
                "Profitability": ["profitMargins", "operatingMargins", "grossMargins", "ebitdaMargins", "returnOnAssets", "returnOnEquity"],
                "Growth": ["revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth", "revenueQuarterlyGrowth"],
                "Financial Size": ["totalRevenue", "totalCash", "totalDebt", "totalCashPerShare", "ebitda", "freeCashflow", "operatingCashflow"],
                "Per Share": ["trailingEps", "forwardEps", "bookValue", "priceToBook", "revenuePerShare"],
                "Dividend": ["dividendRate", "dividendYield", "exDividendDate", "lastDividendDate", "lastDividendValue", "fiveYearAvgDividendYield", "payoutRatio", "trailingAnnualDividendRate", "trailingAnnualDividendYield"],
                "Shares": ["sharesOutstanding", "floatShares", "sharesShort", "sharesShortPriorMonth", "sharesPercentSharesOut", "shortRatio", "shortPercentOfFloat", "dateShortInterest", "impliedSharesOutstanding"],
                "Governance": ["auditRisk", "boardRisk", "compensationRisk", "shareHolderRightsRisk", "overallRisk", "governanceEpochDate", "compensationAsOfEpochDate"],
                "Insider/Institutional": ["heldPercentInsiders", "heldPercentInstitutions"],
                "Analyst": ["targetHighPrice", "targetLowPrice", "targetMeanPrice", "targetMedianPrice", "recommendationMean", "recommendationKey", "numberOfAnalystOpinions"],
                "Dates": ["mostRecentQuarter", "lastFiscalYearEnd", "nextFiscalYearEnd", "firstTradeDateEpochUtc", "lastSplitDate", "lastSplitFactor"],
                "Officers": ["companyOfficers"],
                "Description": ["longBusinessSummary"],
                "Other": ["beta", "beta3Year", "totalInsiderSharesHeld", "netIncomeToCommon", "fullTimeEmployees", "irWebsite", "maxAge", "phone", "address1", "city", "state", "zip", "country", "website"],
            }

            for cat_name, keys in categories.items():
                present = {k: info.get(k) for k in keys if k in info}
                if present:
                    print(f"\n  ### {cat_name}")
                    for k, v in present.items():
                        if k == "companyOfficers":
                            officers = v if isinstance(v, list) else []
                            print(f"    {k}: {len(officers)} officers")
                            for off in officers[:3]:
                                if isinstance(off, dict):
                                    print(f"      - {off.get('name', 'N/A')} | {off.get('title', 'N/A')} | pay: {off.get('totalPay', 'N/A')}")
                        elif k == "longBusinessSummary":
                            print(f"    {k}: [{len(str(v))} chars]")
                        else:
                            print(f"    {k}: {safe_repr(v, 100)}")

            # Find uncategorized keys
            all_categorized = set()
            for keys in categories.values():
                all_categorized.update(keys)
            uncategorized = sorted(set(info.keys()) - all_categorized)
            if uncategorized:
                print(f"\n  ### UNCATEGORIZED ({len(uncategorized)} keys)")
                for k in uncategorized:
                    print(f"    {k}: {safe_repr(info[k], 100)}")
    except Exception as e:
        print(f"  ERROR: {e}")

    # 2. DataFrame attributes we already pull
    print(f"\n\n## 2. DATAFRAME ATTRIBUTES (currently pulled)")
    print("-" * 60)
    pulled_attrs = [
        "insider_transactions", "institutional_holders",
        "recommendations", "upgrades_downgrades",
        "major_holders", "mutualfund_holders",
    ]
    for attr in pulled_attrs:
        try:
            df = getattr(t, attr, None)
            desc = describe_df(df, attr)
            shape = desc.get("shape", "N/A")
            cols = desc.get("columns", [])
            print(f"\n  {attr}: shape={shape}, cols={cols[:10]}")
        except Exception as e:
            print(f"\n  {attr}: ERROR - {e}")

    # 3. Financial statements we already pull
    print(f"\n\n## 3. FINANCIAL STATEMENTS (currently pulled)")
    print("-" * 60)
    stmt_attrs = [
        "income_stmt", "quarterly_income_stmt",
        "balance_sheet", "quarterly_balance_sheet",
        "cashflow", "quarterly_cashflow",
    ]
    for attr in stmt_attrs:
        try:
            df = getattr(t, attr, None)
            desc = describe_df(df, attr)
            shape = desc.get("shape", "N/A")
            print(f"\n  {attr}: shape={shape}")
            if isinstance(desc.get("index_sample"), list):
                print(f"    Sample rows: {desc['index_sample']}")
        except Exception as e:
            print(f"\n  {attr}: ERROR - {e}")

    # 4. Attributes we DON'T currently pull
    print(f"\n\n## 4. ATTRIBUTES NOT CURRENTLY PULLED")
    print("-" * 60)

    not_pulled = [
        "actions",           # Dividends + splits combined
        "capital_gains",     # Capital gains distributions
        "shares_full",       # Full shares outstanding history
        "earnings",          # Earnings data (may overlap income_stmt)
        "earnings_history",  # Historical earnings
        "eps_trend",         # EPS trend data
        "eps_revisions",     # EPS revision data
        "growth_estimates",  # Growth estimate data
        "revenue_estimate",  # Revenue estimates
        "earnings_estimate", # Earnings estimates
        "analyst_price_targets",  # Already partially pulled
        "insider_purchases", # Insider purchase data
        "insider_roster_holders", # Insider roster
        "sustainability",    # ESG sustainability data
        "options",           # Available option expiration dates
        "isin",              # ISIN code
        "sec_filings",       # SEC filings list
        "financials",        # Alias for income_stmt
        "quarterly_financials", # Alias for quarterly_income_stmt
    ]

    for attr in not_pulled:
        try:
            val = getattr(t, attr, "NOT_FOUND")
            if val == "NOT_FOUND":
                print(f"\n  {attr}: attribute not found")
                continue
            if val is None:
                print(f"\n  {attr}: None")
                continue
            if hasattr(val, "empty"):
                if val.empty:
                    print(f"\n  {attr}: DataFrame (empty)")
                else:
                    desc = describe_df(val, attr)
                    print(f"\n  {attr}: DataFrame shape={desc.get('shape')}")
                    cols = desc.get("columns", [])
                    if cols:
                        print(f"    Columns: {cols[:15]}")
                    head = desc.get("head", "")
                    if head:
                        # Indent head output
                        for line in head.split("\n")[:5]:
                            print(f"    {line}")
            elif isinstance(val, dict):
                print(f"\n  {attr}: dict with {len(val)} keys: {list(val.keys())[:10]}")
            elif isinstance(val, list):
                print(f"\n  {attr}: list with {len(val)} items")
                if val:
                    print(f"    Sample: {safe_repr(val[0], 150)}")
            elif isinstance(val, str):
                print(f"\n  {attr}: '{val}'")
            elif isinstance(val, tuple):
                print(f"\n  {attr}: tuple {val}")
            else:
                print(f"\n  {attr}: {type(val).__name__} = {safe_repr(val, 150)}")
        except Exception as e:
            print(f"\n  {attr}: ERROR - {e}")

    # 5. Summary of what we're NOT using from info dict
    print(f"\n\n## 5. KEY DATA IN INFO DICT NOT WIRED TO EXTRACT/RENDER")
    print("-" * 60)

    key_unused = {
        "Governance Risk Scores": ["auditRisk", "boardRisk", "compensationRisk", "shareHolderRightsRisk", "overallRisk"],
        "Officer Compensation": ["companyOfficers"],
        "Growth Metrics": ["revenueGrowth", "earningsGrowth", "earningsQuarterlyGrowth", "revenueQuarterlyGrowth"],
        "Profitability Ratios": ["profitMargins", "operatingMargins", "grossMargins", "ebitdaMargins", "returnOnAssets", "returnOnEquity"],
        "Short Interest": ["sharesShort", "sharesShortPriorMonth", "shortRatio", "shortPercentOfFloat", "dateShortInterest"],
        "Insider/Institutional %": ["heldPercentInsiders", "heldPercentInstitutions"],
        "Valuation Multiples": ["trailingPE", "forwardPE", "priceToSalesTrailing12Months", "priceToBook", "enterpriseToRevenue", "enterpriseToEbitda", "pegRatio"],
        "Financial Aggregates": ["totalRevenue", "totalCash", "totalDebt", "ebitda", "freeCashflow", "operatingCashflow", "totalCashPerShare", "revenuePerShare"],
        "Dividend Details": ["dividendRate", "dividendYield", "payoutRatio", "fiveYearAvgDividendYield", "trailingAnnualDividendRate"],
        "Employee Count": ["fullTimeEmployees"],
        "Beta": ["beta"],
    }

    try:
        info = t.info
        for cat, keys in key_unused.items():
            vals = {k: info.get(k) for k in keys if info.get(k) is not None}
            if vals:
                print(f"\n  ### {cat}")
                for k, v in vals.items():
                    if k == "companyOfficers":
                        officers = v if isinstance(v, list) else []
                        print(f"    {k}: {len(officers)} officers with compensation data")
                    else:
                        print(f"    {k}: {safe_repr(v, 100)}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print(f"\n{'='*80}")
    print("AUDIT COMPLETE")
    print(f"{'='*80}")


if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    audit_ticker(ticker)
