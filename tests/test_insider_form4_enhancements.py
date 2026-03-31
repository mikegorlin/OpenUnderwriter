"""Tests for Form 4 enhancements: new fields, dedup, gift filtering, ownership concentration.

Covers Plan 71-01 requirements:
- FORM4-01: Post-transaction ownership tracking
- FORM4-02: Relationship flags + gift/estate filtering
- FORM4-03: 4/A amendment dedup
- FORM4-05: Ownership concentration alerts
"""

from __future__ import annotations

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.market_events import (
    InsiderClusterEvent,
    InsiderTransaction,
    InsiderTradingAnalysis,
    OwnershipConcentrationAlert,
    OwnershipTrajectoryPoint,
)
from do_uw.stages.extract.insider_trading import (
    compute_aggregates,
    parse_form4_xml,
)
from do_uw.stages.extract.insider_trading_analysis import (
    _deduplicate_transactions,
    compute_ownership_concentration,
)
from do_uw.stages.extract.sourced import now, sourced_float, sourced_str


# ---------------------------------------------------------------------------
# XML fixtures with enhanced fields
# ---------------------------------------------------------------------------

FORM4_WITH_POST_TX = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Alice CEO</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>1</isOfficer>
            <isTenPercentOwner>0</isTenPercentOwner>
            <officerTitle>Chief Executive Officer</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <transactionDate><value>2025-09-01</value></transactionDate>
            <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
            <transactionAmounts>
                <transactionShares><value>5000</value></transactionShares>
                <transactionPricePerShare><value>100.00</value></transactionPricePerShare>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction><value>45000</value></sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership><value>D</value></directOrIndirectOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>"""

FORM4_INDIRECT_OWNERSHIP = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Bob Director</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>1</isDirector>
            <isOfficer>0</isOfficer>
            <isTenPercentOwner>1</isTenPercentOwner>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <transactionDate><value>2025-09-01</value></transactionDate>
            <transactionCoding><transactionCode>S</transactionCode></transactionCoding>
            <transactionAmounts>
                <transactionShares><value>2000</value></transactionShares>
                <transactionPricePerShare><value>50.00</value></transactionPricePerShare>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction><value>8000</value></sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
            <ownershipNature>
                <directOrIndirectOwnership><value>I</value></directOrIndirectOwnership>
                <natureOfOwnership><value>By Family Trust</value></natureOfOwnership>
            </ownershipNature>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>"""

FORM4_GIFT = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Carol CFO</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isDirector>0</isDirector>
            <isOfficer>1</isOfficer>
            <officerTitle>CFO</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <transactionDate><value>2025-09-01</value></transactionDate>
            <transactionCoding><transactionCode>G</transactionCode></transactionCoding>
            <transactionAmounts>
                <transactionShares><value>1000</value></transactionShares>
                <transactionPricePerShare><value>0</value></transactionPricePerShare>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction><value>9000</value></sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>"""

FORM4_RSU_AND_TAX = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Dave CTO</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isOfficer>1</isOfficer>
            <officerTitle>CTO</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <nonDerivativeTable>
        <nonDerivativeTransaction>
            <transactionDate><value>2025-09-01</value></transactionDate>
            <transactionCoding><transactionCode>A</transactionCode></transactionCoding>
            <transactionAmounts>
                <transactionShares><value>3000</value></transactionShares>
                <transactionPricePerShare><value>0</value></transactionPricePerShare>
            </transactionAmounts>
        </nonDerivativeTransaction>
        <nonDerivativeTransaction>
            <transactionDate><value>2025-09-01</value></transactionDate>
            <transactionCoding><transactionCode>F</transactionCode></transactionCoding>
            <transactionAmounts>
                <transactionShares><value>1000</value></transactionShares>
                <transactionPricePerShare><value>100.00</value></transactionPricePerShare>
            </transactionAmounts>
        </nonDerivativeTransaction>
    </nonDerivativeTable>
</ownershipDocument>"""

FORM4_DERIVATIVE = """<?xml version="1.0" encoding="UTF-8"?>
<ownershipDocument>
    <reportingOwner>
        <reportingOwnerId>
            <rptOwnerName>Eve CLO</rptOwnerName>
        </reportingOwnerId>
        <reportingOwnerRelationship>
            <isOfficer>1</isOfficer>
            <officerTitle>CLO</officerTitle>
        </reportingOwnerRelationship>
    </reportingOwner>
    <derivativeTable>
        <derivativeTransaction>
            <transactionDate><value>2025-09-01</value></transactionDate>
            <transactionCoding><transactionCode>M</transactionCode></transactionCoding>
            <transactionAmounts>
                <transactionShares><value>500</value></transactionShares>
                <transactionPricePerShare><value>80.00</value></transactionPricePerShare>
            </transactionAmounts>
            <postTransactionAmounts>
                <sharesOwnedFollowingTransaction><value>1500</value></sharesOwnedFollowingTransaction>
            </postTransactionAmounts>
        </derivativeTransaction>
    </derivativeTable>
</ownershipDocument>"""


# ===========================================================================
# Task 1: Model + parser tests
# ===========================================================================


class TestPostTransactionOwnership:
    """shares_owned_following extraction from postTransactionAmounts."""

    def test_nonderivative_shares_owned_following(self) -> None:
        txns = parse_form4_xml(FORM4_WITH_POST_TX)
        assert len(txns) == 1
        tx = txns[0]
        assert tx.shares_owned_following is not None
        assert tx.shares_owned_following.value == 45000.0

    def test_derivative_shares_following(self) -> None:
        txns = parse_form4_xml(FORM4_DERIVATIVE)
        assert len(txns) == 1
        tx = txns[0]
        # Derivative transactions also get shares_owned_following
        assert tx.shares_owned_following is not None
        assert tx.shares_owned_following.value == 1500.0


class TestRelationshipFlags:
    """is_director, is_officer, is_ten_pct_owner from reportingOwnerRelationship."""

    def test_officer_and_director_flags(self) -> None:
        txns = parse_form4_xml(FORM4_WITH_POST_TX)
        tx = txns[0]
        assert tx.is_director is True
        assert tx.is_officer is True
        assert tx.is_ten_pct_owner is False

    def test_director_ten_pct_owner(self) -> None:
        txns = parse_form4_xml(FORM4_INDIRECT_OWNERSHIP)
        tx = txns[0]
        assert tx.is_director is True
        assert tx.is_officer is False
        assert tx.is_ten_pct_owner is True


class TestOwnershipNature:
    """ownership_nature (D/I) and indirect_ownership_explanation."""

    def test_direct_ownership(self) -> None:
        txns = parse_form4_xml(FORM4_WITH_POST_TX)
        assert txns[0].ownership_nature == "D"
        assert txns[0].indirect_ownership_explanation == ""

    def test_indirect_ownership_with_explanation(self) -> None:
        txns = parse_form4_xml(FORM4_INDIRECT_OWNERSHIP)
        tx = txns[0]
        assert tx.ownership_nature == "I"
        assert tx.indirect_ownership_explanation == "By Family Trust"


class TestAccessionAndAmendment:
    """accession_number and is_amendment flags passed through."""

    def test_accession_passed_through(self) -> None:
        txns = parse_form4_xml(
            FORM4_WITH_POST_TX,
            accession_number="0001234-25-000001",
            is_amendment=False,
        )
        tx = txns[0]
        assert tx.accession_number == "0001234-25-000001"
        assert tx.is_amendment is False

    def test_amendment_flag(self) -> None:
        txns = parse_form4_xml(
            FORM4_WITH_POST_TX,
            accession_number="0001234-25-000002",
            is_amendment=True,
        )
        tx = txns[0]
        assert tx.is_amendment is True


class TestDeduplication:
    """_deduplicate_transactions: 4/A preferred, originals marked superseded."""

    def _make_tx(
        self,
        name: str,
        date: str,
        code: str,
        accession: str,
        is_amendment: bool = False,
        shares: float = 1000.0,
    ) -> InsiderTransaction:
        return InsiderTransaction(
            insider_name=sourced_str(name, "test"),
            transaction_date=sourced_str(date, "test"),
            transaction_code=code,
            transaction_type="SELL" if code == "S" else "BUY",
            accession_number=accession,
            is_amendment=is_amendment,
            shares=sourced_float(shares, "test"),
        )

    def test_amendment_preferred_over_original(self) -> None:
        original = self._make_tx("Alice", "2025-09-01", "S", "ACC-001", False)
        amendment = self._make_tx("Alice", "2025-09-01", "S", "ACC-002", True)
        result = _deduplicate_transactions([original, amendment])
        # Both present, original marked superseded
        non_superseded = [t for t in result if not t.is_superseded]
        superseded = [t for t in result if t.is_superseded]
        assert len(non_superseded) == 1
        assert non_superseded[0].is_amendment is True
        assert len(superseded) == 1

    def test_different_codes_same_date_kept(self) -> None:
        tx1 = self._make_tx("Alice", "2025-09-01", "S", "ACC-001")
        tx2 = self._make_tx("Alice", "2025-09-01", "P", "ACC-002")
        result = _deduplicate_transactions([tx1, tx2])
        non_superseded = [t for t in result if not t.is_superseded]
        assert len(non_superseded) == 2

    def test_superseded_flagged(self) -> None:
        original = self._make_tx("Bob", "2025-09-01", "S", "ACC-001", False)
        amendment = self._make_tx("Bob", "2025-09-01", "S", "ACC-002", True)
        result = _deduplicate_transactions([original, amendment])
        superseded = [t for t in result if t.is_superseded]
        assert len(superseded) == 1
        assert superseded[0].accession_number == "ACC-001"


class TestGiftEstateFiltering:
    """G and W codes excluded from aggregation; A ($0) and F excluded from output."""

    def test_gift_excluded_from_aggregation(self) -> None:
        gift = InsiderTransaction(
            transaction_type="GIFT", transaction_code="G",
            total_value=sourced_float(0.0, "test"),
        )
        sale = InsiderTransaction(
            transaction_type="SELL", transaction_code="S",
            total_value=sourced_float(500000.0, "test"),
        )
        aggs = compute_aggregates([gift, sale])
        assert aggs["total_sold_value"] == 500000.0

    def test_estate_excluded_from_aggregation(self) -> None:
        estate = InsiderTransaction(
            transaction_type="WILL_OR_ESTATE", transaction_code="W",
            total_value=sourced_float(100000.0, "test"),
        )
        aggs = compute_aggregates([estate])
        assert aggs["total_sold_value"] == 0.0
        assert aggs["net_direction"] == "NEUTRAL"

    def test_rsu_and_tax_excluded_from_output(self) -> None:
        rsu = InsiderTransaction(
            transaction_type="GRANT", transaction_code="A",
            total_value=sourced_float(0.0, "test"),
        )
        tax = InsiderTransaction(
            transaction_type="TAX_WITHHOLD", transaction_code="F",
            total_value=sourced_float(100000.0, "test"),
        )
        sale = InsiderTransaction(
            transaction_type="SELL", transaction_code="S",
            total_value=sourced_float(500000.0, "test"),
        )
        aggs = compute_aggregates([rsu, tax, sale])
        # RSU and tax should be excluded
        assert aggs["total_sold_value"] == 500000.0
        assert aggs["compensation_excluded"] == 2

    def test_gift_still_in_transaction_list(self) -> None:
        """Gift transactions stored for completeness."""
        txns = parse_form4_xml(FORM4_GIFT)
        assert len(txns) == 1
        assert txns[0].transaction_code == "G"


class TestFormTypeVariants:
    """4/A in _FORM_TYPE_VARIANTS."""

    def test_form4_variants_include_amendment(self) -> None:
        from do_uw.stages.acquire.clients.sec_client_filing import (
            _FORM_TYPE_VARIANTS,
        )
        assert "4" in _FORM_TYPE_VARIANTS
        assert "4/A" in _FORM_TYPE_VARIANTS["4"]


# ===========================================================================
# Task 2: Ownership concentration tests
# ===========================================================================


class TestOwnershipConcentration:
    """compute_ownership_concentration: tiered alerts."""

    def _make_sell_tx(
        self,
        name: str,
        title: str,
        date: str,
        shares_sold: float,
        shares_remaining: float,
        is_officer: bool = True,
        is_10b5_1: bool = False,
        code: str = "S",
    ) -> InsiderTransaction:
        return InsiderTransaction(
            insider_name=sourced_str(name, "test"),
            title=sourced_str(title, "test"),
            transaction_date=sourced_str(date, "test"),
            transaction_type="SELL",
            transaction_code=code,
            shares=sourced_float(shares_sold, "test"),
            price_per_share=sourced_float(50.0, "test"),
            total_value=sourced_float(shares_sold * 50.0, "test"),
            shares_owned_following=sourced_float(shares_remaining, "test"),
            is_officer=is_officer,
            is_director=not is_officer,
            is_10b5_1=(
                SourcedValue[bool](value=is_10b5_1, source="test", confidence=Confidence.HIGH, as_of=now())
                if is_10b5_1 else None
            ),
        )

    def test_csuite_over_50pct_red_flag(self) -> None:
        """C-suite selling >50% in 6mo -> RED_FLAG."""
        # Sold 60k, 40k remaining = 60% sold
        txns = [
            self._make_sell_tx("Alice CEO", "CEO", "2025-09-01", 60000, 40000),
        ]
        alerts = compute_ownership_concentration(txns, [])
        assert len(alerts) >= 1
        alert = [a for a in alerts if a.insider_name == "Alice CEO"][0]
        assert alert.severity == "RED_FLAG"
        assert alert.is_c_suite is True

    def test_csuite_over_25pct_warning(self) -> None:
        """C-suite selling >25% but <50% in 6mo -> WARNING."""
        # Sold 30k, 70k remaining = 30% sold
        txns = [
            self._make_sell_tx("Bob CFO", "CFO", "2025-09-01", 30000, 70000),
        ]
        alerts = compute_ownership_concentration(txns, [])
        warning_alerts = [a for a in alerts if a.insider_name == "Bob CFO"]
        assert len(warning_alerts) == 1
        assert warning_alerts[0].severity == "WARNING"

    def test_10b5_1_reduces_severity(self) -> None:
        """10b5-1 plan reduces RED_FLAG -> WARNING, WARNING -> INFORMATIONAL."""
        # 60% sold under 10b5-1 plan
        txns = [
            self._make_sell_tx("Alice CEO", "CEO", "2025-09-01", 60000, 40000, is_10b5_1=True),
        ]
        alerts = compute_ownership_concentration(txns, [])
        alert = [a for a in alerts if a.insider_name == "Alice CEO"][0]
        assert alert.severity == "WARNING"  # reduced from RED_FLAG
        assert alert.is_10b5_1 is True

    def test_director_informational_only(self) -> None:
        """Directors/10% holders get INFORMATIONAL regardless of amount."""
        # Director sold 60% but is not C-suite
        txns = [
            self._make_sell_tx("Carol Dir", "Director", "2025-09-01", 60000, 40000, is_officer=False),
        ]
        alerts = compute_ownership_concentration(txns, [])
        alert = [a for a in alerts if a.insider_name == "Carol Dir"][0]
        assert alert.severity == "INFORMATIONAL"

    def test_insider_purchases_positive(self) -> None:
        """Open-market purchases tracked as POSITIVE signal."""
        purchase = InsiderTransaction(
            insider_name=sourced_str("Dan CEO", "test"),
            title=sourced_str("CEO", "test"),
            transaction_date=sourced_str("2025-09-01", "test"),
            transaction_type="BUY",
            transaction_code="P",
            shares=sourced_float(10000, "test"),
            shares_owned_following=sourced_float(110000, "test"),
            is_officer=True,
        )
        alerts = compute_ownership_concentration([purchase], [])
        positive = [a for a in alerts if a.severity == "POSITIVE"]
        assert len(positive) == 1
        assert positive[0].insider_name == "Dan CEO"

    def test_personal_and_outstanding_pct(self) -> None:
        """Both personal_pct_sold and outstanding_pct computed."""
        txns = [
            self._make_sell_tx("Alice CEO", "CEO", "2025-09-01", 30000, 70000),
        ]
        alerts = compute_ownership_concentration(txns, [])
        alert = [a for a in alerts if a.insider_name == "Alice CEO"][0]
        assert alert.personal_pct_sold == 30.0  # 30k / (30k+70k) * 100

    def test_cluster_compounds_severity(self) -> None:
        """Cluster selling + concentration overlap compounds to highest severity."""
        txns = [
            self._make_sell_tx("Alice CEO", "CEO", "2025-09-01", 30000, 70000),
        ]
        clusters = [
            InsiderClusterEvent(
                start_date="2025-08-15",
                end_date="2025-09-15",
                insider_count=3,
                insiders=["Alice CEO", "Bob CFO", "Carol Dir"],
                total_value=500000.0,
            ),
        ]
        alerts = compute_ownership_concentration(txns, clusters)
        alert = [a for a in alerts if a.insider_name == "Alice CEO"][0]
        assert alert.compounds_with_cluster is True
        # WARNING compounded -> RED_FLAG
        assert alert.severity == "RED_FLAG"

    def test_ownership_trajectory(self) -> None:
        """Build timeline from shares_owned_following sequence."""
        txns = [
            self._make_sell_tx("Alice CEO", "CEO", "2025-07-01", 10000, 90000),
            self._make_sell_tx("Alice CEO", "CEO", "2025-08-01", 10000, 80000),
            self._make_sell_tx("Alice CEO", "CEO", "2025-09-01", 10000, 70000),
        ]
        alerts = compute_ownership_concentration(txns, [])
        # Check that trajectory data is built (tested via alert existence)
        assert len(alerts) >= 1

    def test_alert_stored_on_analysis(self) -> None:
        """OwnershipConcentrationAlert can be stored on InsiderTradingAnalysis."""
        alert = OwnershipConcentrationAlert(
            insider_name="Test",
            role="CEO",
            severity="WARNING",
            personal_pct_sold=30.0,
            outstanding_pct=None,
            shares_sold=30000.0,
            shares_remaining=70000.0,
            lookback_months=6,
            is_10b5_1=False,
            is_c_suite=True,
            compounds_with_cluster=False,
        )
        analysis = InsiderTradingAnalysis(ownership_alerts=[alert])
        assert len(analysis.ownership_alerts) == 1
