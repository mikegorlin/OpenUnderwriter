"""Tests for the RESOLVE pipeline stage.

All HTTP calls are mocked -- no real network requests.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from do_uw.models.common import Confidence, StageStatus
from do_uw.models.state import AnalysisState
from do_uw.stages.resolve import ResolveStage
from do_uw.stages.resolve.sec_identity import (
    resolve_company_identity,
    sic_to_sector,
)
from do_uw.stages.resolve.ticker_resolver import (
    ResolvedTicker,
    resolve_ticker,
)

# --- Sample SEC data for mocking ---

SAMPLE_COMPANY_TICKERS: dict[str, dict[str, Any]] = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    "2": {"cik_str": 1652044, "ticker": "GOOGL", "title": "Alphabet Inc."},
    "3": {"cik_str": 1652044, "ticker": "GOOG", "title": "Alphabet Inc."},
    "4": {"cik_str": 1318605, "ticker": "TSLA", "title": "Tesla, Inc."},
    "5": {
        "cik_str": 1046179,
        "ticker": "TSM",
        "title": "Taiwan Semiconductor Manufacturing Co Ltd",
    },
}

SAMPLE_SUBMISSIONS_APPLE: dict[str, Any] = {
    "cik": "320193",
    "entityType": "operating",
    "sic": "3571",
    "sicDescription": "Electronic Computers",
    "name": "Apple Inc.",
    "tickers": ["AAPL"],
    "exchanges": ["Nasdaq"],
    "stateOfIncorporation": "CA",
    "fiscalYearEnd": "0930",
    "filings": {"recent": {"form": ["10-K", "10-Q", "8-K"]}, "files": []},
}

SAMPLE_SUBMISSIONS_FPI: dict[str, Any] = {
    "cik": "1046179",
    "entityType": "foreign-private-issuer",
    "sic": "3674",
    "sicDescription": "Semiconductors and Related Devices",
    "name": "Taiwan Semiconductor Manufacturing Co Ltd",
    "tickers": ["TSM"],
    "exchanges": ["NYSE"],
    "stateOfIncorporation": "",
    "fiscalYearEnd": "1231",
    "filings": {"recent": {"form": ["20-F", "6-K"]}, "files": []},
}


# --- Ticker Resolver Tests ---


class TestResolveTickerByTicker:
    """Test ticker-based resolution."""

    @patch("do_uw.stages.resolve.ticker_resolver.sec_get")
    def test_exact_ticker_match(self, mock_get: MagicMock) -> None:
        mock_get.return_value = SAMPLE_COMPANY_TICKERS
        result = resolve_ticker("AAPL")
        assert result.ticker == "AAPL"
        assert result.cik == 320193
        assert result.company_name == "Apple Inc."
        assert result.confidence == 100.0

    @patch("do_uw.stages.resolve.ticker_resolver.sec_get")
    def test_parent_entity_goog_googl(self, mock_get: MagicMock) -> None:
        mock_get.return_value = SAMPLE_COMPANY_TICKERS
        result_goog = resolve_ticker("GOOG")
        result_googl = resolve_ticker("GOOGL")
        assert result_goog.cik == result_googl.cik == 1652044
        assert sorted(result_goog.all_tickers) == ["GOOG", "GOOGL"]
        assert sorted(result_googl.all_tickers) == ["GOOG", "GOOGL"]

    @patch("do_uw.stages.resolve.ticker_resolver.sec_get")
    def test_unknown_ticker_raises(self, mock_get: MagicMock) -> None:
        mock_get.return_value = SAMPLE_COMPANY_TICKERS
        with pytest.raises(ValueError, match="not found"):
            resolve_ticker("ZZZZZ")

    @patch("do_uw.stages.resolve.ticker_resolver.sec_get")
    def test_empty_input_raises(self, mock_get: MagicMock) -> None:
        with pytest.raises(ValueError, match="empty"):
            resolve_ticker("")


class TestResolveTickerByName:
    """Test company name fuzzy matching."""

    @patch("do_uw.stages.resolve.ticker_resolver.sec_get")
    def test_fuzzy_match_apple(self, mock_get: MagicMock) -> None:
        mock_get.return_value = SAMPLE_COMPANY_TICKERS
        result = resolve_ticker("Apple")
        assert result.cik == 320193
        assert result.confidence >= 80.0

    @patch("do_uw.stages.resolve.ticker_resolver.sec_get")
    def test_fuzzy_match_alphabet(self, mock_get: MagicMock) -> None:
        mock_get.return_value = SAMPLE_COMPANY_TICKERS
        result = resolve_ticker("Alphabet")
        assert result.cik == 1652044
        assert result.confidence >= 80.0


# --- SEC Identity Tests ---


class TestResolveCompanyIdentity:
    """Test SEC submissions API identity resolution."""

    @patch("do_uw.stages.resolve.sec_identity.sec_get")
    def test_apple_identity(self, mock_get: MagicMock) -> None:
        mock_get.return_value = SAMPLE_SUBMISSIONS_APPLE
        identity = resolve_company_identity(320193, "AAPL")

        assert identity.ticker == "AAPL"
        assert identity.legal_name is not None
        assert identity.legal_name.value == "Apple Inc."
        assert identity.legal_name.confidence == Confidence.HIGH
        assert identity.cik is not None
        assert identity.cik.value == "320193"
        assert identity.sic_code is not None
        assert identity.sic_code.value == "3571"
        assert identity.sic_description is not None
        assert identity.sic_description.value == "Electronic Computers"
        assert identity.exchange is not None
        assert identity.exchange.value == "Nasdaq"
        assert identity.state_of_incorporation is not None
        assert identity.state_of_incorporation.value == "CA"
        assert identity.fiscal_year_end is not None
        assert identity.fiscal_year_end.value == "09-30"
        assert identity.is_fpi is False
        assert identity.sector is not None
        assert identity.sector.value == "TECH"

    @patch("do_uw.stages.resolve.sec_identity.sec_get")
    def test_fpi_detection_entity_type(self, mock_get: MagicMock) -> None:
        mock_get.return_value = SAMPLE_SUBMISSIONS_FPI
        identity = resolve_company_identity(1046179, "TSM")

        assert identity.is_fpi is True
        assert identity.entity_type is not None
        assert "foreign-private-issuer" in identity.entity_type.value

    @patch("do_uw.stages.resolve.sec_identity.sec_get")
    def test_fpi_detection_from_filing_history(
        self, mock_get: MagicMock
    ) -> None:
        submissions: dict[str, Any] = {
            **SAMPLE_SUBMISSIONS_APPLE,
            "entityType": "operating",
            "filings": {
                "recent": {"form": ["20-F", "6-K"]},
                "files": [],
            },
        }
        mock_get.return_value = submissions
        identity = resolve_company_identity(320193, "AAPL")
        assert identity.is_fpi is True


class TestSicToSector:
    """Test SIC code to sector mapping."""

    def test_tech_sic(self) -> None:
        assert sic_to_sector("3571") == "TECH"  # Electronic computers
        assert sic_to_sector("7372") == "TECH"  # Computer services

    def test_healthcare_sic(self) -> None:
        assert sic_to_sector("2834") == "HLTH"  # Pharma
        assert sic_to_sector("8011") == "HLTH"  # Health services

    def test_financials_sic(self) -> None:
        assert sic_to_sector("6020") == "FINS"  # Banking

    def test_energy_sic(self) -> None:
        assert sic_to_sector("1311") == "ENGY"  # Crude petroleum
        assert sic_to_sector("2911") == "ENGY"  # Petroleum refining

    def test_unknown_returns_default(self) -> None:
        assert sic_to_sector("0100") == "DEFAULT"
        assert sic_to_sector("9999") == "DEFAULT"
        assert sic_to_sector("") == "DEFAULT"

    @pytest.mark.parametrize(
        ("sic", "expected", "description"),
        [
            # COMM: Motion picture (78xx)
            ("7812", "COMM", "Motion picture production"),
            ("7819", "COMM", "Motion picture services"),
            ("7841", "COMM", "Netflix - video tape rental/streaming"),
            # COMM: Amusement & recreation (79xx)
            ("7922", "COMM", "Theatrical producers/entertainment"),
            ("7990", "COMM", "Disney - amusement/recreation services"),
            # TECH: Computer services (73xx) -- must remain TECH
            ("7371", "TECH", "Computer programming services"),
            ("7372", "TECH", "Prepackaged software"),
            ("7374", "TECH", "Computer processing/data preparation"),
            # CONS: Hotels/personal services (70-72) -- must remain CONS
            ("7011", "CONS", "Hotels and motels"),
            ("7211", "CONS", "Laundry/personal services"),
            # INDU: Management/engineering (74-76) -- must remain INDU
            ("7411", "INDU", "Travel agencies"),
            ("7500", "INDU", "Automotive repair services"),
            ("7600", "INDU", "Miscellaneous repair services"),
            # HLTH: Health services (80xx) -- must remain HLTH
            ("8011", "HLTH", "Offices of physicians"),
            ("8049", "HLTH", "Health practitioners offices"),
            # TECH: Engineering/management consulting (87xx) -- must remain TECH
            ("8711", "TECH", "Engineering services"),
            ("8742", "TECH", "Management consulting services"),
        ],
    )
    def test_sic_to_sector_refined_services(
        self, sic: str, expected: str, description: str
    ) -> None:
        """Regression: SIC 70-89 services mapped with finer granularity."""
        result = sic_to_sector(sic)
        assert result == expected, (
            f"SIC {sic} ({description}): expected {expected}, got {result}"
        )


# --- ResolveStage Integration Tests ---


class TestResolveStage:
    """Test ResolveStage.run with mocked dependencies."""

    def test_validate_input_empty_ticker(self) -> None:
        stage = ResolveStage()
        state = AnalysisState(ticker="")
        with pytest.raises(ValueError, match="Ticker is required"):
            stage.validate_input(state)

    def test_validate_input_valid_ticker(self) -> None:
        stage = ResolveStage()
        state = AnalysisState(ticker="AAPL")
        stage.validate_input(state)  # Should not raise.

    @patch("do_uw.stages.resolve._enrich_from_yfinance")
    @patch("do_uw.stages.resolve.resolve_company_identity")
    @patch("do_uw.stages.resolve.resolve_ticker")
    @patch("do_uw.stages.resolve.AnalysisCache")
    def test_run_populates_state(
        self,
        mock_cache_cls: MagicMock,
        mock_resolve_ticker: MagicMock,
        mock_resolve_identity: MagicMock,
        mock_enrich: MagicMock,
    ) -> None:
        from do_uw.models.common import SourcedValue
        from do_uw.models.company import CompanyIdentity

        mock_cache_cls.return_value = MagicMock()

        mock_resolve_ticker.return_value = ResolvedTicker(
            ticker="AAPL",
            cik=320193,
            company_name="Apple Inc.",
            confidence=100.0,
            all_tickers=["AAPL"],
        )

        now = __import__("datetime").datetime.now(
            tz=__import__("datetime").UTC
        )
        mock_identity = CompanyIdentity(
            ticker="AAPL",
            legal_name=SourcedValue[str](
                value="Apple Inc.",
                source="SEC EDGAR submissions",
                confidence=Confidence.HIGH,
                as_of=now,
            ),
            cik=SourcedValue[str](
                value="320193",
                source="SEC EDGAR submissions",
                confidence=Confidence.HIGH,
                as_of=now,
            ),
        )
        mock_resolve_identity.return_value = mock_identity

        stage = ResolveStage()
        state = AnalysisState(ticker="AAPL")
        stage.run(state)

        assert state.company is not None
        assert state.company.identity.ticker == "AAPL"
        assert state.company.identity.legal_name is not None
        assert state.company.identity.legal_name.value == "Apple Inc."
        assert state.stages["resolve"].status == StageStatus.COMPLETED

    @patch("do_uw.stages.resolve._enrich_from_yfinance")
    @patch("do_uw.stages.resolve.resolve_company_identity")
    @patch("do_uw.stages.resolve.resolve_ticker")
    @patch("do_uw.stages.resolve.AnalysisCache")
    def test_run_activates_tech_playbook(
        self,
        mock_cache_cls: MagicMock,
        mock_resolve_ticker: MagicMock,
        mock_resolve_identity: MagicMock,
        mock_enrich: MagicMock,
    ) -> None:
        """ResolveStage activates TECH_SAAS playbook for SIC 3571."""
        from do_uw.models.common import SourcedValue
        from do_uw.models.company import CompanyIdentity

        mock_cache_cls.return_value = MagicMock()
        mock_resolve_ticker.return_value = ResolvedTicker(
            ticker="AAPL", cik=320193,
            company_name="Apple Inc.", confidence=100.0,
            all_tickers=["AAPL"],
        )
        now = __import__("datetime").datetime.now(
            tz=__import__("datetime").UTC
        )
        mock_resolve_identity.return_value = CompanyIdentity(
            ticker="AAPL",
            legal_name=SourcedValue[str](
                value="Apple Inc.", source="SEC", confidence=Confidence.HIGH,
                as_of=now,
            ),
            cik=SourcedValue[str](
                value="320193", source="SEC", confidence=Confidence.HIGH,
                as_of=now,
            ),
            sic_code=SourcedValue[str](
                value="3571", source="SEC", confidence=Confidence.HIGH,
                as_of=now,
            ),
        )

        stage = ResolveStage()
        state = AnalysisState(ticker="AAPL")
        stage.run(state)

        assert state.active_playbook_id == "TECH_SAAS"
        assert state.stages["resolve"].status == StageStatus.COMPLETED

    @patch("do_uw.stages.resolve._enrich_from_yfinance")
    @patch("do_uw.stages.resolve.resolve_company_identity")
    @patch("do_uw.stages.resolve.resolve_ticker")
    @patch("do_uw.stages.resolve.AnalysisCache")
    def test_run_no_playbook_for_unknown_sic(
        self,
        mock_cache_cls: MagicMock,
        mock_resolve_ticker: MagicMock,
        mock_resolve_identity: MagicMock,
        mock_enrich: MagicMock,
    ) -> None:
        """ResolveStage sets no playbook for unmatched SIC code."""
        from do_uw.models.common import SourcedValue
        from do_uw.models.company import CompanyIdentity

        mock_cache_cls.return_value = MagicMock()
        mock_resolve_ticker.return_value = ResolvedTicker(
            ticker="XYZ", cik=99999,
            company_name="Unknown Corp", confidence=100.0,
            all_tickers=["XYZ"],
        )
        now = __import__("datetime").datetime.now(
            tz=__import__("datetime").UTC
        )
        mock_resolve_identity.return_value = CompanyIdentity(
            ticker="XYZ",
            legal_name=SourcedValue[str](
                value="Unknown Corp", source="SEC",
                confidence=Confidence.HIGH, as_of=now,
            ),
            cik=SourcedValue[str](
                value="99999", source="SEC",
                confidence=Confidence.HIGH, as_of=now,
            ),
            sic_code=SourcedValue[str](
                value="0100", source="SEC",
                confidence=Confidence.HIGH, as_of=now,
            ),
        )

        stage = ResolveStage()
        state = AnalysisState(ticker="XYZ")
        stage.run(state)

        assert state.active_playbook_id is None
        assert state.stages["resolve"].status == StageStatus.COMPLETED

    def test_playbook_activation_non_blocking_with_invalid_sic(
        self,
    ) -> None:
        """_activate_industry_playbook handles invalid SIC gracefully."""
        from do_uw.models.common import SourcedValue
        from do_uw.models.company import CompanyIdentity
        from do_uw.stages.resolve import _activate_industry_playbook

        now = __import__("datetime").datetime.now(
            tz=__import__("datetime").UTC
        )
        identity = CompanyIdentity(
            ticker="BAD",
            sic_code=SourcedValue[str](
                value="INVALID", source="test",
                confidence=Confidence.LOW, as_of=now,
            ),
        )
        state = AnalysisState(ticker="BAD")
        # Should not raise even with non-numeric SIC
        _activate_industry_playbook(state, identity)
        assert state.active_playbook_id is None

    def test_playbook_activation_non_blocking_no_sic(self) -> None:
        """_activate_industry_playbook handles missing SIC/NAICS."""
        from do_uw.models.company import CompanyIdentity
        from do_uw.stages.resolve import _activate_industry_playbook

        identity = CompanyIdentity(ticker="NONE")
        state = AnalysisState(ticker="NONE")
        # No SIC or NAICS at all -- should return without error
        _activate_industry_playbook(state, identity)
        assert state.active_playbook_id is None
