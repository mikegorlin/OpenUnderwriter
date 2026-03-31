"""Tests for section completeness gate.

Verifies that sections with excessive N/A values get flagged and
suppressed with an Insufficient Data banner.
"""

from __future__ import annotations

from do_uw.validation.section_completeness import (
    SectionCompleteness,
    SectionCompletenessGate,
    check_section_completeness,
)


# ---------------------------------------------------------------------------
# Test 1: 80% N/A section is flagged as incomplete
# ---------------------------------------------------------------------------

class TestHighNAFlagged:
    """Section with 8/10 fields as N/A (80%) is flagged."""

    def test_high_na_ratio_flagged(self) -> None:
        context = {
            "financials": {
                "revenue": "N/A",
                "net_income": "N/A",
                "assets": None,
                "liabilities": "N/A",
                "equity": "",
                "cash": "N/A",
                "debt": "Not Available",
                "shares": "N/A",
                "price": "$150.00",
                "exchange": "NASDAQ",
            }
        }
        gate = SectionCompletenessGate(threshold=0.5)
        results = gate.check(context)
        fin = [r for r in results if r.section_name == "financials"]
        assert len(fin) == 1
        assert fin[0].suppressed is True
        assert fin[0].na_ratio >= 0.5


# ---------------------------------------------------------------------------
# Test 2: 30% N/A section passes
# ---------------------------------------------------------------------------

class TestLowNAPasses:
    """Section with 3/10 fields as N/A (30%) passes."""

    def test_low_na_ratio_passes(self) -> None:
        context = {
            "financials": {
                "revenue": "$3.05B",
                "net_income": "$1.2B",
                "assets": "$10B",
                "liabilities": "$5B",
                "equity": "$5B",
                "cash": "$2B",
                "debt": "$1B",
                "price": "N/A",
                "exchange": None,
                "shares": "N/A",
            }
        }
        gate = SectionCompletenessGate(threshold=0.5)
        results = gate.check(context)
        fin = [r for r in results if r.section_name == "financials"]
        assert len(fin) == 1
        assert fin[0].suppressed is False
        assert fin[0].na_ratio < 0.5


# ---------------------------------------------------------------------------
# Test 3: Insufficient Data banner contains section name and reason
# ---------------------------------------------------------------------------

class TestBannerContent:
    """Banner dict contains section name and reason string."""

    def test_banner_has_required_fields(self) -> None:
        context = {
            "governance": {
                "board": None,
                "ceo": None,
                "compensation": "N/A",
                "directors": "N/A",
                "independence": "",
            }
        }
        gate = SectionCompletenessGate(threshold=0.5)
        result = gate.apply_banners(context)
        gov = result["governance"]
        assert gov.get("_insufficient_data") is True
        assert "governance" in gov.get("_section_name", "").lower()
        assert isinstance(gov.get("_na_ratio"), float)
        assert isinstance(gov.get("_reason"), str)
        assert len(gov["_reason"]) > 0


# ---------------------------------------------------------------------------
# Test 4: Returns completeness list for all sections
# ---------------------------------------------------------------------------

class TestAllSectionsReported:
    """Gate returns SectionCompleteness for all checked sections."""

    def test_multiple_sections(self) -> None:
        context = {
            "executive_summary": {"headline": "Good company", "score": 85},
            "financials": {
                "revenue": "N/A",
                "income": None,
                "assets": "",
                "liabilities": "N/A",
            },
            "market": {"price": "$100", "volume": "1M", "cap": "$50B"},
        }
        gate = SectionCompletenessGate(threshold=0.5)
        results = gate.check(context)
        names = {r.section_name for r in results}
        assert "executive_summary" in names
        assert "financials" in names
        assert "market" in names


# ---------------------------------------------------------------------------
# Test 5: Threshold is configurable
# ---------------------------------------------------------------------------

class TestConfigurableThreshold:
    """Default threshold 0.5 can be changed."""

    def test_custom_threshold(self) -> None:
        context = {
            "financials": {
                "a": "N/A",
                "b": "N/A",
                "c": "N/A",
                "d": "$100",
                "e": "$200",
                "f": "$300",
                "g": "$400",
            }
        }
        # 3/7 = ~43% N/A
        gate_strict = SectionCompletenessGate(threshold=0.3)
        results_strict = gate_strict.check(context)
        fin_strict = [r for r in results_strict if r.section_name == "financials"]
        assert fin_strict[0].suppressed is True

        gate_lenient = SectionCompletenessGate(threshold=0.5)
        results_lenient = gate_lenient.check(context)
        fin_lenient = [r for r in results_lenient if r.section_name == "financials"]
        assert fin_lenient[0].suppressed is False


# ---------------------------------------------------------------------------
# Test: Convenience function
# ---------------------------------------------------------------------------

class TestConvenienceFunction:
    """check_section_completeness works as a standalone call."""

    def test_convenience_returns_list(self) -> None:
        context = {
            "market": {"price": "$100", "volume": "N/A"},
        }
        results = check_section_completeness(context, threshold=0.5)
        assert isinstance(results, list)
        assert all(isinstance(r, SectionCompleteness) for r in results)


# ---------------------------------------------------------------------------
# Test: Nested dicts counted correctly (not as single N/A)
# ---------------------------------------------------------------------------

class TestNestedDicts:
    """Nested dicts should have their leaf values counted, not the dict itself."""

    def test_nested_dict_leaf_counting(self) -> None:
        context = {
            "financials": {
                "summary": {
                    "revenue": "$3B",
                    "income": "$1B",
                    "margin": "33%",
                },
                "extra_field": "N/A",
            }
        }
        gate = SectionCompletenessGate(threshold=0.5)
        results = gate.check(context)
        fin = [r for r in results if r.section_name == "financials"]
        assert len(fin) == 1
        # 3 leaf values from nested + 1 N/A = 4 total, 1 N/A = 25%
        assert fin[0].na_ratio < 0.5
        assert fin[0].suppressed is False


# ---------------------------------------------------------------------------
# Test: Sections not in known list are skipped
# ---------------------------------------------------------------------------

class TestNonSectionKeysSkipped:
    """Non-section context keys (e.g., 'ticker', 'pdf_mode') are not checked."""

    def test_scalar_keys_skipped(self) -> None:
        context = {
            "ticker": "AAPL",
            "pdf_mode": True,
            "financials": {"revenue": "$3B"},
        }
        gate = SectionCompletenessGate(threshold=0.5)
        results = gate.check(context)
        names = {r.section_name for r in results}
        assert "ticker" not in names
        assert "pdf_mode" not in names
        assert "financials" in names
