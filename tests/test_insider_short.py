"""Tests for insider trading and short interest extractors.

Covers SECT4-04 (insider trading) and SECT4-05 (short interest)
extraction logic with unit tests for parsing, detection, and
graceful degradation.
"""

from __future__ import annotations

from typing import Any

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.market_events import InsiderTransaction
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.insider_trading import (
    classify_yfinance_text,
    compute_aggregates,
    detect_10b5_1_from_text,
    detect_cluster_selling,
    extract_insider_trading,
    normalize_date,
    parse_form4_xml,
)
from do_uw.stages.extract.short_interest import (
    compare_vs_peers,
    extract_current_short_interest,
    extract_short_interest,
    identify_short_seller_reports,
)
from do_uw.stages.extract.sourced import now, sourced_float, sourced_str

# ---------------------------------------------------------------------------
# Helpers for building test state
# ---------------------------------------------------------------------------


def _make_state(
    ticker: str = "TEST",
    market_data: dict[str, Any] | None = None,
    filing_documents: dict[str, list[dict[str, str]]] | None = None,
    web_search_results: dict[str, Any] | None = None,
    company_name: str = "Test Corp",
) -> AnalysisState:
    """Build an AnalysisState with the specified acquired data."""
    state = AnalysisState(ticker=ticker)
    state.acquired_data = AcquiredData(
        market_data=market_data or {},
        filing_documents=filing_documents or {},
        web_search_results=web_search_results or {},
    )
    identity = CompanyIdentity(ticker=ticker)
    identity.legal_name = SourcedValue[str](
        value=company_name,
        source="test",
        confidence=Confidence.HIGH,
        as_of=now(),
    )
    state.company = CompanyProfile(identity=identity)
    return state


# Sample Form 4 XML for testing.
SAMPLE_FORM4_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerCik>0001234567</rptOwnerCik>
            <rptOwnerName>John Smith</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>0</isDirector>
            <isOfficer>1</isOfficer>
            <officerTitle>CEO</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <transactionDate>
                <value>2025-06-15</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>S</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>10000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>50.00</value>
                </transactionPricePerShare>
            </transactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>"""


SAMPLE_FORM4_10B5_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Jane Doe</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>0</isOfficer>
        </reportingOwnerRelationship>
    </reportingOwner>
    <aff10b5One>1</aff10b5One>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <transactionDate>
                <value>2025-07-01</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>S</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>5000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>45.00</value>
                </transactionPricePerShare>
            </transactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>"""


SAMPLE_FORM4_PURCHASE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Bob Johnson</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>0</isOfficer>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <transactionDate>
                <value>2025-08-01</value>
            </transactionDate>
            <transactionCoding>
                <transactionCode>P</transactionCode>
            </transactionCoding>
            <transactionAmounts>
                <transactionShares>
                    <value>2000</value>
                </transactionShares>
                <transactionPricePerShare>
                    <value>48.00</value>
                </transactionPricePerShare>
            </transactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>"""


# ===========================================================================
# INSIDER TRADING TESTS (8)
# ===========================================================================


class TestForm4XmlParseSale:
    """Test Form 4 XML sale transaction parsing."""

    def test_parse_sale_transaction(self) -> None:
        """Parse a basic sale transaction from Form 4 XML."""
        txns = parse_form4_xml(SAMPLE_FORM4_XML)

        assert len(txns) == 1
        tx = txns[0]
        assert tx.insider_name is not None
        assert tx.insider_name.value == "John Smith"
        assert tx.title is not None
        assert tx.title.value == "CEO"
        assert tx.transaction_code == "S"
        assert tx.transaction_type == "SELL"
        assert tx.shares is not None
        assert tx.shares.value == 10000.0
        assert tx.price_per_share is not None
        assert tx.price_per_share.value == 50.0
        assert tx.total_value is not None
        assert tx.total_value.value == 500000.0
        assert tx.transaction_date is not None
        assert tx.transaction_date.value == "2025-06-15"


class TestForm410b51Detection:
    """Test 10b5-1 plan detection from Form 4 XML."""

    def test_detect_10b5_1_from_aff_element(self) -> None:
        """Detect 10b5-1 plan indicator via AFF10B5ONE element."""
        txns = parse_form4_xml(SAMPLE_FORM4_10B5_XML)

        assert len(txns) == 1
        tx = txns[0]
        assert tx.is_10b5_1 is not None
        assert tx.is_10b5_1.value is True
        assert tx.is_discretionary is False

    def test_sale_without_10b5_1(self) -> None:
        """Sale without 10b5-1 indicator has None is_10b5_1."""
        txns = parse_form4_xml(SAMPLE_FORM4_XML)
        tx = txns[0]
        # No aff10b5One element and no 10b5-1 text.
        assert tx.is_10b5_1 is None


class TestForm4Purchase:
    """Test Form 4 purchase transaction parsing."""

    def test_parse_purchase(self) -> None:
        """Parse a purchase (P) transaction from Form 4 XML."""
        txns = parse_form4_xml(SAMPLE_FORM4_PURCHASE_XML)

        assert len(txns) == 1
        tx = txns[0]
        assert tx.transaction_code == "P"
        assert tx.transaction_type == "BUY"
        assert tx.insider_name is not None
        assert tx.insider_name.value == "Bob Johnson"
        assert tx.shares is not None
        assert tx.shares.value == 2000.0
        assert tx.total_value is not None
        assert tx.total_value.value == 96000.0


class TestClusterDetection:
    """Test cluster selling detection."""

    def _make_tx(
        self,
        name: str,
        date: str,
        value: float,
    ) -> InsiderTransaction:
        """Create a sale transaction for cluster testing."""
        return InsiderTransaction(
            insider_name=sourced_str(name, "test"),
            transaction_date=sourced_str(date, "test"),
            transaction_type="SELL",
            transaction_code="S",
            total_value=sourced_float(value, "test"),
        )

    def test_cluster_detected_3_insiders(self) -> None:
        """Detect cluster when 3+ insiders sell within 30 days."""
        txns = [
            self._make_tx("Alice", "2025-07-01", 100000.0),
            self._make_tx("Bob", "2025-07-10", 200000.0),
            self._make_tx("Carol", "2025-07-20", 150000.0),
        ]

        clusters = detect_cluster_selling(txns, window_days=30, min_insiders=3)

        assert len(clusters) == 1
        cluster = clusters[0]
        assert cluster.insider_count == 3
        assert sorted(cluster.insiders) == ["Alice", "Bob", "Carol"]
        assert cluster.total_value == 450000.0
        assert cluster.start_date == "2025-07-01"

    def test_below_threshold_no_cluster(self) -> None:
        """No cluster detected when fewer than min_insiders sell."""
        txns = [
            self._make_tx("Alice", "2025-07-01", 100000.0),
            self._make_tx("Bob", "2025-07-10", 200000.0),
        ]

        clusters = detect_cluster_selling(txns, window_days=30, min_insiders=3)
        assert len(clusters) == 0


class TestAggregates:
    """Test aggregate computation."""

    def test_net_selling(self) -> None:
        """Compute net selling when sells exceed buys."""
        txns = [
            InsiderTransaction(
                transaction_type="SELL",
                total_value=sourced_float(500000.0, "test"),
                is_10b5_1=SourcedValue[bool](
                    value=True,
                    source="test",
                    confidence=Confidence.HIGH,
                    as_of=now(),
                ),
            ),
            InsiderTransaction(
                transaction_type="SELL",
                total_value=sourced_float(300000.0, "test"),
            ),
            InsiderTransaction(
                transaction_type="BUY",
                total_value=sourced_float(50000.0, "test"),
            ),
        ]

        aggs = compute_aggregates(txns)

        assert aggs["total_sold_value"] == 800000.0
        assert aggs["total_bought_value"] == 50000.0
        assert aggs["net_direction"] == "NET_SELLING"
        assert aggs["pct_10b5_1"] == 50.0  # 1 of 2 sales is 10b5-1.


class TestYfinanceFallback:
    """Test yfinance fallback extraction."""

    def test_yfinance_extraction(self) -> None:
        """Extract insider transactions from yfinance format."""
        state = _make_state(
            market_data={
                "insider_transactions": {
                    "Insider Trading": ["John CEO", "Jane CFO"],
                    "Start Date": ["2025-06-15", "2025-07-01"],
                    "Shares": [10000, 5000],
                    "Value": [500000, 225000],
                    "Text": ["Sale", "Purchase"],
                },
            },
        )

        analysis, report = extract_insider_trading(state)

        assert len(analysis.transactions) == 2
        assert report.extractor_name == "insider_trading"
        assert "yfinance insider_transactions" in report.fallbacks_used
        # First is a sale.
        tx0 = analysis.transactions[0]
        assert tx0.transaction_type == "SELL"
        # Second is a purchase.
        tx1 = analysis.transactions[1]
        assert tx1.transaction_type == "BUY"


class Test10b51TextDetection:
    """Test 10b5-1 plan detection from yfinance text descriptions."""

    def test_explicit_10b5_1_mention(self) -> None:
        """Detect 10b5-1 from explicit text mention."""
        assert detect_10b5_1_from_text("Sale pursuant to Rule 10b5-1 trading plan") is True

    def test_10b5_1_plan_variant(self) -> None:
        """Detect 10b5-1 from '10b5-1 Plan' variant."""
        assert detect_10b5_1_from_text("10b5-1 Plan") is True

    def test_pre_arranged_plan(self) -> None:
        """Detect pre-arranged trading plan mention."""
        assert detect_10b5_1_from_text("Sale under pre-arranged trading plan") is True

    def test_trading_plan_mention(self) -> None:
        """Detect generic trading plan mention."""
        assert detect_10b5_1_from_text("Sold pursuant to a trading plan") is True

    def test_rule_10b5(self) -> None:
        """Detect Rule 10b5 without hyphen."""
        assert detect_10b5_1_from_text("Disposition under Rule 10b5") is True

    def test_no_plan_indicator(self) -> None:
        """Return None for plain sale text without plan indicator."""
        assert detect_10b5_1_from_text("Sale") is None

    def test_empty_text(self) -> None:
        """Return None for empty text."""
        assert detect_10b5_1_from_text("") is None

    def test_not_pursuant(self) -> None:
        """Return False when text explicitly negates 10b5-1."""
        assert detect_10b5_1_from_text("Sale not pursuant to 10b5-1 plan") is False

    def test_purchase_text_no_plan(self) -> None:
        """Purchase text without plan indicator returns None."""
        assert detect_10b5_1_from_text("Purchase of common stock") is None


class TestYfinance10b51Integration:
    """Test that yfinance fallback correctly tags 10b5-1 and computes pct_10b5_1."""

    def test_yfinance_10b5_1_detection(self) -> None:
        """yfinance transactions with 10b5-1 text produce non-zero pct_10b5_1."""
        state = _make_state(
            market_data={
                "insider_transactions": {
                    "Insider Trading": ["CEO Smith", "CFO Jones", "COO Brown"],
                    "Start Date": ["2025-06-15", "2025-07-01", "2025-07-10"],
                    "Shares": [10000, 5000, 8000],
                    "Value": [500000, 225000, 400000],
                    "Text": [
                        "Sale pursuant to Rule 10b5-1 trading plan",
                        "Sale",
                        "Sale under 10b5-1 Plan",
                    ],
                },
            },
        )

        analysis, _report = extract_insider_trading(state)

        # 3 SELL transactions, 2 with 10b5-1 => pct_10b5_1 ~ 66.7%
        assert analysis.pct_10b5_1 is not None
        assert analysis.pct_10b5_1.value > 60.0

        # Check individual transaction tagging
        tagged = [
            tx for tx in analysis.transactions
            if tx.is_10b5_1 is not None and tx.is_10b5_1.value is True
        ]
        assert len(tagged) == 2

    def test_yfinance_no_10b5_1_text(self) -> None:
        """yfinance transactions without 10b5-1 text produce 0% pct_10b5_1."""
        state = _make_state(
            market_data={
                "insider_transactions": {
                    "Insider Trading": ["CEO Smith", "CFO Jones"],
                    "Start Date": ["2025-06-15", "2025-07-01"],
                    "Shares": [10000, 5000],
                    "Value": [500000, 225000],
                    "Text": ["Sale", "Sale"],
                },
            },
        )

        analysis, _report = extract_insider_trading(state)

        assert analysis.pct_10b5_1 is not None
        assert analysis.pct_10b5_1.value == 0.0


class TestMissingDataGraceful:
    """Test graceful handling of missing insider data."""

    def test_no_data_returns_empty_analysis(self) -> None:
        """Empty state returns empty analysis with extraction report."""
        state = _make_state()

        analysis, report = extract_insider_trading(state)

        assert len(analysis.transactions) == 0
        assert len(analysis.cluster_events) == 0
        assert analysis.net_buying_selling is None
        assert report.coverage_pct == 0.0
        assert "No insider transaction data available" in report.warnings


# ===========================================================================
# SHORT INTEREST TESTS (4)
# ===========================================================================


class TestShortInterestExtracted:
    """Test basic short interest extraction."""

    def test_si_extracted_from_info(self) -> None:
        """Extract short interest metrics from yfinance info dict."""
        info: dict[str, Any] = {
            "shortPercentOfFloat": 0.08,
            "shortRatio": 3.5,
            "sharesShort": 5000000,
            "sharesShortPriorMonth": 4000000,
        }

        result = extract_current_short_interest(info)

        assert result["short_pct_float"] == 8.0
        assert result["days_to_cover"] == 3.5
        assert "trend_6m" in result

    def test_full_extraction_populates_profile(self) -> None:
        """Full extract_short_interest populates profile and report."""
        state = _make_state(
            market_data={
                "info": {
                    "shortPercentOfFloat": 0.12,
                    "shortRatio": 4.2,
                    "sharesShort": 8000000,
                    "sharesShortPriorMonth": 6000000,
                },
            },
        )

        profile, report = extract_short_interest(state)

        assert profile.short_pct_float is not None
        assert profile.short_pct_float.value == 12.0
        assert profile.days_to_cover is not None
        assert profile.days_to_cover.value == 4.2
        assert "short_pct_float" in report.found_fields
        assert "days_to_cover" in report.found_fields


class TestTrendRising:
    """Test short interest trend detection."""

    def test_rising_trend(self) -> None:
        """Detect RISING trend when current > prior by >10%."""
        info: dict[str, Any] = {
            "sharesShort": 10000000,
            "sharesShortPriorMonth": 7000000,
        }

        result = extract_current_short_interest(info)
        assert result["trend_6m"] == "RISING"

    def test_declining_trend(self) -> None:
        """Detect DECLINING trend when current < prior by >10%."""
        info: dict[str, Any] = {
            "sharesShort": 5000000,
            "sharesShortPriorMonth": 8000000,
        }

        result = extract_current_short_interest(info)
        assert result["trend_6m"] == "DECLINING"

    def test_stable_trend(self) -> None:
        """Detect STABLE trend when change is within +/-10%."""
        info: dict[str, Any] = {
            "sharesShort": 5000000,
            "sharesShortPriorMonth": 4800000,
        }

        result = extract_current_short_interest(info)
        assert result["trend_6m"] == "STABLE"


class TestShortSellerReportDetection:
    """Test short seller report identification."""

    def test_detect_hindenburg_report(self) -> None:
        """Detect Hindenburg Research report in web results."""
        web_results: dict[str, Any] = {
            "short_sellers": [
                {
                    "title": "Hindenburg Research: Test Corp Is Overstating Revenue",
                    "description": (
                        "Hindenburg Research published a report "
                        "alleging Test Corp has been overstating "
                        "revenue by 30%."
                    ),
                    "url": "https://example.com/hindenburg-test",
                },
            ],
        }

        reports = identify_short_seller_reports(web_results, "Test Corp")

        assert len(reports) == 1
        assert reports[0]["source"] == "Hindenburg"

    def test_no_seller_reports(self) -> None:
        """No short seller reports when none mentioned."""
        web_results: dict[str, Any] = {
            "news": [
                {
                    "title": "Test Corp Reports Strong Q3 Earnings",
                    "description": "Test Corp beat analyst expectations.",
                    "url": "https://example.com/news",
                },
            ],
        }

        reports = identify_short_seller_reports(web_results, "Test Corp")
        assert len(reports) == 0


class TestShortInterestMissingData:
    """Test graceful handling of missing short interest data."""

    def test_no_data_returns_empty_profile(self) -> None:
        """Empty state returns empty profile with extraction report."""
        state = _make_state()

        profile, report = extract_short_interest(state)

        assert profile.short_pct_float is None
        assert profile.days_to_cover is None
        assert profile.trend_6m is None
        # short_seller_reports should still be marked as found
        # (empty search result is still valid).
        assert "short_seller_reports" in report.found_fields


# ===========================================================================
# Utility tests
# ===========================================================================


class TestUtilities:
    """Test shared utility functions."""

    def test_classify_yfinance_text_sale(self) -> None:
        """Classify 'Sale' text as SELL."""
        assert classify_yfinance_text("Sale") == "SELL"
        assert classify_yfinance_text("Sold shares") == "SELL"

    def test_classify_yfinance_text_purchase(self) -> None:
        """Classify 'Purchase' text as BUY."""
        assert classify_yfinance_text("Purchase") == "BUY"
        assert classify_yfinance_text("Bought 1000 shares") == "BUY"

    def test_normalize_date_iso(self) -> None:
        """Normalize already ISO-formatted date."""
        assert normalize_date("2025-06-15") == "2025-06-15"

    def test_normalize_date_us_format(self) -> None:
        """Normalize US date format."""
        assert normalize_date("06/15/2025") == "2025-06-15"

    def test_peer_comparison_ratio(self) -> None:
        """Compute SI ratio vs peers."""
        peers: list[dict[str, Any]] = [
            {"shortPercentOfFloat": 0.04},
            {"shortPercentOfFloat": 0.06},
        ]
        # Company: 10%, peers avg: (4+6)/2 = 5%.
        ratio = compare_vs_peers(10.0, peers)
        assert ratio == 2.0

    def test_peer_comparison_no_peers(self) -> None:
        """Return None when no peer data available."""
        ratio = compare_vs_peers(10.0, [])
        assert ratio is None
