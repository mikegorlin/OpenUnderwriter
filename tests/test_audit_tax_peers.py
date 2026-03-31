"""Tests for audit risk, tax indicators, and peer group extraction.

Covers 16 tests:
- Audit: Big 4 detection, opinion parsing, going concern, material weakness,
  CAMs, extraction report
- Tax: ETR normal, ETR aggressive flag, tax haven cross-reference, missing data
- Peers: composite scoring, market cap filter, minimum peers, override peers,
  tier assignment, partial SIC match
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

from do_uw.models.common import Confidence, SourcedValue
from do_uw.models.company import CompanyIdentity, CompanyProfile
from do_uw.models.state import AcquiredData, AnalysisState
from do_uw.stages.extract.audit_risk import (
    extract_audit_risk,
)
from do_uw.stages.extract.peer_group import (
    MIN_PEER_COUNT,
    construct_peer_group,
)
from do_uw.stages.extract.peer_scoring import (
    compute_composite_score,
    score_description_overlap,
    score_industry_match,
    score_market_cap_proximity,
    score_revenue_similarity,
    score_sic_match,
)
from do_uw.stages.extract.tax_indicators import (
    extract_tax_indicators,
    load_tax_havens,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sourced_str(val: str) -> SourcedValue[str]:
    """Create a test SourcedValue[str]."""
    from datetime import UTC, datetime

    return SourcedValue[str](
        value=val, source="test", confidence=Confidence.HIGH,
        as_of=datetime.now(tz=UTC),
    )


def _make_state(
    filing_texts: dict[str, str] | None = None,
    company_facts: dict[str, Any] | None = None,
    exhibit_21: str = "",
    market_info: dict[str, Any] | None = None,
    sic_code: str = "7372",
    filer_category: str | None = None,
    geo_footprint: int = 0,
    subsidiary_count: int | None = None,
) -> AnalysisState:
    """Build a minimal AnalysisState for testing."""
    from datetime import UTC, datetime

    filings: dict[str, Any] = {}
    if filing_texts is not None:
        filings["filing_texts"] = filing_texts
    if company_facts is not None:
        filings["company_facts"] = company_facts
    if exhibit_21:
        filings["exhibit_21"] = exhibit_21

    market_data: dict[str, Any] = {}
    if market_info is not None:
        market_data["info"] = market_info

    identity = CompanyIdentity(
        ticker="TEST",
        cik=_sourced_str("0001234567"),
        sic_code=_sourced_str(sic_code),
        sector=_sourced_str("TECH"),
    )
    profile = CompanyProfile(identity=identity)
    if filer_category:
        profile.filer_category = _sourced_str(filer_category)
    if subsidiary_count is not None:
        profile.subsidiary_count = SourcedValue[int](
            value=subsidiary_count, source="test",
            confidence=Confidence.HIGH,
            as_of=datetime.now(tz=UTC),
        )
    if geo_footprint > 0:
        for i in range(geo_footprint):
            from do_uw.stages.extract.sourced import sourced_dict
            profile.geographic_footprint.append(
                sourced_dict(
                    {"region": f"Region_{i}", "revenue": 100.0},
                    "test", Confidence.MEDIUM,
                )
            )

    return AnalysisState(
        ticker="TEST",
        company=profile,
        acquired_data=AcquiredData(
            filings=filings,
            market_data=market_data,
        ),
    )


def _make_xbrl_facts(
    *concept_defs: tuple[str, str, str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build Company Facts response.

    Each concept_def is (namespace, concept, unit, entries).
    Namespace is 'us-gaap' or 'dei'.
    """
    facts: dict[str, Any] = {}
    for namespace, concept, unit, entries in concept_defs:
        if namespace not in facts:
            facts[namespace] = {}
        facts[namespace][concept] = {"units": {unit: entries}}
    return {"cik": 1234567, "entityName": "Test Corp", "facts": facts}


def _xbrl_entry(
    val: float | str, end: str, fy: int = 2024, form: str = "10-K",
) -> dict[str, Any]:
    """Build a single XBRL fact entry."""
    return {
        "val": val, "end": end, "fy": fy, "fp": "FY",
        "form": form, "filed": "2025-02-15", "accn": "0001234-24-001",
    }


# ===========================================================================
# Audit Risk Tests
# ===========================================================================


class TestAuditRiskBig4:
    """Test auditor identity extraction."""

    def test_extract_auditor_big4(self) -> None:
        """Filing with PwC name -> auditor_name=PricewaterhouseCoopers, is_big4=True."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "Report of Independent Registered Public Accounting Firm\n"
                    "We, PricewaterhouseCoopers LLP, have audited the financial "
                    "statements... presents fairly, in all material respects."
                ),
            },
        )
        profile, report = extract_audit_risk(state)

        assert profile.auditor_name is not None
        assert profile.auditor_name.value == "PricewaterhouseCoopers"
        assert profile.is_big4 is not None
        assert profile.is_big4.value is True
        assert "auditor_name" in report.found_fields
        assert "is_big4" in report.found_fields

    def test_extract_auditor_from_xbrl(self) -> None:
        """AuditorName in XBRL DEI -> extracted."""
        facts = _make_xbrl_facts(
            ("dei", "AuditorName", "N/A", [
                _xbrl_entry("KPMG LLP", "2024-12-31"),
            ]),
        )
        state = _make_state(company_facts=facts)
        profile, _ = extract_audit_risk(state)

        assert profile.auditor_name is not None
        assert profile.auditor_name.value == "KPMG LLP"
        assert profile.is_big4 is not None
        assert profile.is_big4.value is True


class TestAuditOpinion:
    """Test opinion type parsing."""

    def test_extract_opinion_unqualified(self) -> None:
        """Standard opinion language -> unqualified."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "In our opinion, the financial statements present fairly, "
                    "in all material respects, the financial position..."
                ),
            },
        )
        profile, report = extract_audit_risk(state)

        assert profile.opinion_type is not None
        assert profile.opinion_type.value == "unqualified"
        assert "opinion_type" in report.found_fields

    def test_extract_opinion_qualified(self) -> None:
        """Qualified opinion language -> qualified."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "In our qualified opinion, except for the matter "
                    "described in the Basis for Qualified Opinion section..."
                ),
            },
        )
        profile, _ = extract_audit_risk(state)
        assert profile.opinion_type is not None
        assert profile.opinion_type.value == "qualified"


class TestGoingConcern:
    """Test going concern detection."""

    def test_extract_going_concern(self) -> None:
        """Text with substantial doubt language -> going_concern=True."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "There is substantial doubt about its ability to "
                    "continue as a going concern."
                ),
            },
        )
        profile, report = extract_audit_risk(state)

        assert profile.going_concern is not None
        assert profile.going_concern.value is True
        assert "going_concern" in report.found_fields

    def test_no_going_concern(self) -> None:
        """Normal filing -> going_concern=False."""
        state = _make_state(
            filing_texts={
                "item8": "The financial statements are fairly presented.",
            },
        )
        profile, _ = extract_audit_risk(state)
        assert profile.going_concern is not None
        assert profile.going_concern.value is False

    def test_benign_going_concern_not_triggered(self) -> None:
        """Accounting methodology 'as a going concern' must NOT trigger."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "The income approach considers the future cash flows "
                    "from a reporting unit's ongoing operations as a going "
                    "concern, while the market approach considers the "
                    "current financial environment in establishing fair "
                    "value. The financial statements present fairly, in "
                    "all material respects, the financial position."
                ),
            },
        )
        profile, _ = extract_audit_risk(state)
        assert profile.going_concern is not None
        assert profile.going_concern.value is False

    def test_negated_going_concern_not_triggered(self) -> None:
        """Management evaluation with 'no substantial doubt' must NOT trigger."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "Management has evaluated the Company's ability to "
                    "continue as a going concern and determined there are "
                    "no substantial doubt conditions. The financial "
                    "statements present fairly in all material respects."
                ),
            },
        )
        profile, _ = extract_audit_risk(state)
        assert profile.going_concern is not None
        assert profile.going_concern.value is False


class TestMaterialWeakness:
    """Test material weakness extraction."""

    def test_extract_material_weakness(self) -> None:
        """SOX 404 text with material weakness -> extracted description."""
        state = _make_state(
            filing_texts={
                "item9a": (
                    "Management identified a material weakness in "
                    "internal control over financial reporting related "
                    "to the accounting for complex financial instruments."
                ),
            },
        )
        profile, report = extract_audit_risk(state)

        assert len(profile.material_weaknesses) > 0
        assert "material weakness" in profile.material_weaknesses[0].value.lower()
        assert "material_weaknesses" in report.found_fields


class TestCAMs:
    """Test Critical Audit Matters extraction."""

    def test_extract_cams(self) -> None:
        """Auditor report with CAM -> extracted."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "Critical Audit Matters\n"
                    "Critical Audit Matter: Revenue Recognition\n"
                    "The Company recognizes revenue from complex "
                    "multi-element arrangements."
                ),
            },
        )
        profile, report = extract_audit_risk(state)

        assert len(profile.critical_audit_matters) > 0
        assert "critical_audit_matters" in report.found_fields


class TestAuditReport:
    """Test extraction report completeness."""

    def test_extraction_report_audit(self) -> None:
        """All 10 fields expected, coverage reported."""
        state = _make_state(
            filing_texts={
                "item8": (
                    "Report of Independent Registered Public Accounting Firm\n"
                    "We, Deloitte & Touche LLP, present fairly, in all "
                    "material respects."
                ),
            },
        )
        _, report = extract_audit_risk(state)

        assert len(report.expected_fields) == 10
        assert report.coverage_pct > 0
        assert report.extractor_name == "audit_risk"


# ===========================================================================
# Tax Indicator Tests
# ===========================================================================


class TestETR:
    """Test effective tax rate computation."""

    def test_etr_normal(self) -> None:
        """Tax=21M, Pretax=100M -> ETR=0.21."""
        facts = _make_xbrl_facts(
            ("us-gaap", "IncomeTaxExpenseBenefit", "USD", [
                _xbrl_entry(21_000_000.0, "2024-12-31", 2024),
            ]),
            (
                "us-gaap",
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                "USD",
                [_xbrl_entry(100_000_000.0, "2024-12-31", 2024)],
            ),
        )
        state = _make_state(company_facts=facts)
        result, report = extract_tax_indicators(state)

        assert result is not None
        assert result.value["effective_tax_rate"] == 0.21
        assert "etr" in report.found_fields

    def test_etr_aggressive_flag(self) -> None:
        """Tax=10M, Pretax=100M -> ETR=0.10 (flagged)."""
        facts = _make_xbrl_facts(
            ("us-gaap", "IncomeTaxExpenseBenefit", "USD", [
                _xbrl_entry(10_000_000.0, "2024-12-31", 2024),
            ]),
            (
                "us-gaap",
                "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
                "USD",
                [_xbrl_entry(100_000_000.0, "2024-12-31", 2024)],
            ),
        )
        state = _make_state(company_facts=facts)
        result, report = extract_tax_indicators(state)

        assert result is not None
        assert result.value["effective_tax_rate"] == 0.10
        assert any("aggressive" in w.lower() for w in report.warnings)


class TestTaxHavens:
    """Test tax haven subsidiary detection."""

    def test_tax_haven_cross_reference(self) -> None:
        """Exhibit 21 with Cayman subsidiaries -> detected."""
        state = _make_state(
            exhibit_21=(
                "SUBSIDIARY LIST\n"
                "1. ABC Holdings Ltd - Cayman Islands\n"
                "2. DEF Corp - Cayman Islands\n"
                "3. GHI Services - Cayman Islands\n"
                "4. JKL Inc - Delaware\n"
                "5. MNO LLC - New York\n"
            ),
            subsidiary_count=5,
        )
        result, report = extract_tax_indicators(state)

        assert result is not None
        assert result.value["tax_haven_subsidiary_count"] >= 3
        assert "tax_havens" in report.found_fields

    def test_tax_indicators_missing_data(self) -> None:
        """No pretax income in XBRL -> ETR 'Not Available' / None."""
        state = _make_state()
        result, report = extract_tax_indicators(state)

        # With no XBRL data, ETR should be None.
        if result is not None:
            assert result.value.get("effective_tax_rate") is None
        assert any("missing" in w.lower() or "compute" in w.lower()
                    for w in report.warnings)

    def test_load_tax_havens(self) -> None:
        """Tax havens config loads correctly."""
        havens = load_tax_havens()
        assert len(havens) > 0
        categories = {h.get("category") for h in havens}
        assert "zero_tax" in categories
        assert "low_tax" in categories
        assert "preferential_regime" in categories


# ===========================================================================
# Peer Scoring Tests
# ===========================================================================


class TestPeerScoring:
    """Test individual peer scoring signals."""

    def test_composite_peer_score_exact_match(self) -> None:
        """Same SIC + same industry + similar market cap -> high score."""
        score = compute_composite_score(
            sic=100.0,       # 4-digit SIC match
            industry=100.0,  # exact industry match
            mcap=100.0,      # identical market cap
            revenue=100.0,   # identical revenue
            description=50.0,  # some overlap
        )
        assert score > 90.0

    def test_composite_peer_score_partial_match(self) -> None:
        """Different SIC but same sector -> moderate score."""
        score = compute_composite_score(
            sic=0.0,         # no SIC match
            industry=50.0,   # sector match only
            mcap=80.0,       # close market cap
            revenue=60.0,    # similar revenue
            description=30.0,  # some overlap
        )
        assert 20.0 < score < 60.0

    def test_sic_match_4_digit(self) -> None:
        """4-digit SIC exact match -> 100."""
        assert score_sic_match("7372", "7372") == 100.0

    def test_sic_match_3_digit(self) -> None:
        """3-digit SIC match -> 75."""
        assert score_sic_match("7372", "7371") == 75.0

    def test_sic_match_2_digit(self) -> None:
        """2-digit SIC match -> 50."""
        assert score_sic_match("7372", "7311") == 50.0

    def test_sic_no_match(self) -> None:
        """No SIC digit match -> 0."""
        assert score_sic_match("7372", "2800") == 0.0


class TestMarketCapFilter:
    """Test market cap band filtering."""

    def test_market_cap_band_filter(self) -> None:
        """Candidate outside 0.5x-2x band -> score=0."""
        # 0.2x target -> out of band
        score = score_market_cap_proximity(100_000_000, 20_000_000)
        assert score == 0.0

        # 3x target -> out of band
        score = score_market_cap_proximity(100_000_000, 300_000_000)
        assert score == 0.0

    def test_market_cap_in_band(self) -> None:
        """Candidate at 1.0x target -> score=100."""
        score = score_market_cap_proximity(100_000_000, 100_000_000)
        assert score == 100.0

    def test_revenue_similarity(self) -> None:
        """Identical revenue -> 100, 10x difference -> 10."""
        assert score_revenue_similarity(100.0, 100.0) == 100.0
        assert score_revenue_similarity(100.0, 10.0) == 10.0

    def test_description_overlap(self) -> None:
        """Overlapping descriptions -> positive score."""
        score = score_description_overlap(
            "cloud computing software enterprise platform",
            "enterprise cloud computing infrastructure platform",
        )
        assert score > 0.0

    def test_industry_exact_match(self) -> None:
        """Same industry -> 100."""
        score = score_industry_match(
            "Software", "Technology", "Software", "Technology",
        )
        assert score == 100.0


# ===========================================================================
# Peer Group Construction Tests
# ===========================================================================


def _mock_yfinance_info(
    symbol: str,
    market_cap: float = 50_000_000_000,
    revenue: float = 10_000_000_000,
    sic: str = "7372",
    industry: str = "Software",
    sector: str = "Technology",
) -> dict[str, Any]:
    """Build mock data matching _enrich_candidate_yfinance output format.

    NOTE: This returns the *enriched* format (sic_code, market_cap, etc.)
    as returned by _enrich_candidate_yfinance, not raw yfinance info.
    Used both as market_info for state (raw format keys like marketCap)
    and as mock return for _enrich_candidate_yfinance (enriched keys).
    """
    return {
        # Enriched format (used by _make_peer / _score_candidate).
        "market_cap": market_cap,
        "revenue": revenue,
        "sic_code": sic,
        "industry": industry,
        "sector": sector,
        "description": f"{symbol} provides technology solutions.",
        "name": f"{symbol} Inc",
        # Raw yfinance format (used when passed as market_info to state).
        "marketCap": market_cap,
        "totalRevenue": revenue,
        "sic": sic,
        "longBusinessSummary": f"{symbol} provides technology solutions.",
        "shortName": f"{symbol} Inc",
    }


class TestPeerGroupConstruction:
    """Test construct_peer_group with mocked dependencies."""

    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch("do_uw.stages.extract.peer_group._enrich_candidate_yfinance")
    def test_minimum_peer_count(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        """At least 5 peers returned."""
        # Return enough candidates.
        mock_fetch.return_value = [
            {"symbol": f"PEER{i}", "name": f"Peer {i}",
             "sector": "Technology", "industry": "Software"}
            for i in range(10)
        ]
        mock_enrich.side_effect = lambda sym: _mock_yfinance_info(sym)

        state = _make_state(
            market_info=_mock_yfinance_info("TEST"),
        )
        peer_group, _report = construct_peer_group(state)

        assert len(peer_group.peers) >= MIN_PEER_COUNT

    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch("do_uw.stages.extract.peer_group._enrich_candidate_yfinance")
    def test_override_peers_included(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        """Override tickers appear in final peer list."""
        mock_fetch.return_value = [
            {"symbol": f"AUTO{i}", "name": f"Auto {i}",
             "sector": "Technology", "industry": "Software"}
            for i in range(5)
        ]
        mock_enrich.side_effect = lambda sym: _mock_yfinance_info(sym)

        state = _make_state(
            market_info=_mock_yfinance_info("TEST"),
        )
        peer_group, _ = construct_peer_group(
            state, override_peers=["OVERRIDE1", "OVERRIDE2"],
        )

        tickers = [p.ticker for p in peer_group.peers]
        assert "OVERRIDE1" in tickers
        assert "OVERRIDE2" in tickers

    @patch(
        "do_uw.stages.extract.peer_group._fetch_candidates_financedatabase"
    )
    @patch("do_uw.stages.extract.peer_group._enrich_candidate_yfinance")
    def test_peer_tier_assignment(
        self,
        mock_enrich: MagicMock,
        mock_fetch: MagicMock,
    ) -> None:
        """Peers correctly assigned to tiers."""
        mock_fetch.return_value = [
            # Same SIC -> primary_sic
            {"symbol": "SIC_MATCH", "name": "SIC Match",
             "sector": "Technology", "industry": "Software"},
            # Different SIC, has industry -> sector_etf
            {"symbol": "IND_MATCH", "name": "Ind Match",
             "sector": "Technology", "industry": "Hardware"},
        ]

        def _enrich(sym: str) -> dict[str, Any]:
            if sym == "SIC_MATCH":
                return _mock_yfinance_info(sym, sic="7372")
            if sym == "IND_MATCH":
                return _mock_yfinance_info(sym, sic="3674", industry="Semiconductors")
            return _mock_yfinance_info(sym)

        mock_enrich.side_effect = _enrich

        state = _make_state(
            market_info=_mock_yfinance_info("TEST"),
        )
        peer_group, _ = construct_peer_group(state)

        tiers = {p.ticker: p.peer_tier for p in peer_group.peers}
        if "SIC_MATCH" in tiers:
            assert tiers["SIC_MATCH"] == "primary_sic"
        if "IND_MATCH" in tiers:
            assert tiers["IND_MATCH"] == "sector_etf"
