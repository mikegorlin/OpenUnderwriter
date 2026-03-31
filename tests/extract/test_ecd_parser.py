"""Tests for ECD inline XBRL parser.

Validates parsing of ``ecd:`` namespace tags from DEF 14A HTML,
multi-year PvP table extraction, boolean flag parsing, and
merge-into-compensation logic.
"""

from __future__ import annotations

import pytest

from do_uw.stages.extract.ecd_parser import (
    ECDYearData,
    _extract_year_from_context,
    _parse_bool_flag,
    _parse_numeric,
    parse_ecd_tags,
    merge_ecd_into_compensation,
)


# ---------------------------------------------------------------------------
# Numeric parsing
# ---------------------------------------------------------------------------


class TestParseNumeric:
    def test_simple_integer(self) -> None:
        assert _parse_numeric("1234567") == 1234567.0

    def test_comma_separated(self) -> None:
        assert _parse_numeric("1,234,567") == 1234567.0

    def test_with_dollar_sign(self) -> None:
        assert _parse_numeric("$1,234,567") == 1234567.0

    def test_negative(self) -> None:
        assert _parse_numeric("-500000") == -500000.0

    def test_parenthetical_negative(self) -> None:
        assert _parse_numeric("(1,234)") == -1234.0

    def test_decimal(self) -> None:
        assert _parse_numeric("123.45") == 123.45

    def test_whitespace(self) -> None:
        assert _parse_numeric("  1234  ") == 1234.0

    def test_empty(self) -> None:
        assert _parse_numeric("") is None

    def test_non_numeric(self) -> None:
        assert _parse_numeric("N/A") is None


# ---------------------------------------------------------------------------
# Boolean flag parsing
# ---------------------------------------------------------------------------


class TestParseBoolFlag:
    def test_true_lowercase(self) -> None:
        assert _parse_bool_flag("true") is True

    def test_true_mixed_case(self) -> None:
        assert _parse_bool_flag("True") is True

    def test_yes(self) -> None:
        assert _parse_bool_flag("Yes") is True

    def test_false_lowercase(self) -> None:
        assert _parse_bool_flag("false") is False

    def test_no(self) -> None:
        assert _parse_bool_flag("No") is False

    def test_unknown(self) -> None:
        assert _parse_bool_flag("maybe") is None

    def test_empty(self) -> None:
        assert _parse_bool_flag("") is None


# ---------------------------------------------------------------------------
# Context year extraction
# ---------------------------------------------------------------------------


class TestExtractYearFromContext:
    def test_apple_style_context(self) -> None:
        # Apple uses C_CIK_STARTDATE_ENDDATE format
        assert _extract_year_from_context(
            "C_0001308179_20240928_20250927"
        ) == "2025"

    def test_fy_prefix(self) -> None:
        assert _extract_year_from_context("FY2024") == "2024"

    def test_pvp_table_context(self) -> None:
        assert _extract_year_from_context("ecd_PvpTable_2024") == "2024"

    def test_no_year(self) -> None:
        assert _extract_year_from_context("some_random_context") is None

    def test_multiple_years_picks_latest(self) -> None:
        # When multiple years appear, pick the latest
        result = _extract_year_from_context("C_0001_20220101_20230101")
        assert result in ("2022", "2023")


# ---------------------------------------------------------------------------
# ECDYearData
# ---------------------------------------------------------------------------


class TestECDYearData:
    def test_to_dict_omits_none(self) -> None:
        yd = ECDYearData("2024")
        yd.ceo_total_comp = 15000000.0
        result = yd.to_dict()
        assert result == {"year": "2024", "ceo_total_comp": 15000000.0}

    def test_to_dict_full(self) -> None:
        yd = ECDYearData("2024")
        yd.ceo_total_comp = 15000000.0
        yd.company_tsr = 180.5
        result = yd.to_dict()
        assert result["year"] == "2024"
        assert result["ceo_total_comp"] == 15000000.0
        assert result["company_tsr"] == 180.5


# ---------------------------------------------------------------------------
# Full tag parsing
# ---------------------------------------------------------------------------

# Minimal DEF 14A HTML snippet with ECD inline XBRL tags
SAMPLE_HTML = """
<html>
<body>
<h2>Pay vs Performance Table</h2>
<table>
<tr>
<td><ix:nonFraction contextRef="C_0001_20240101_20241231"
    name="ecd:PeoTotalCompAmt" unitRef="USD"
    decimals="0">15,682,219</ix:nonFraction></td>
<td><ix:nonFraction contextRef="C_0001_20240101_20241231"
    name="ecd:PeoActuallyPaidCompAmt" unitRef="USD"
    decimals="0">22,461,005</ix:nonFraction></td>
<td><ix:nonFraction contextRef="C_0001_20240101_20241231"
    name="ecd:NonPeoNeoAvgTotalCompAmt" unitRef="USD"
    decimals="0">6,718,277</ix:nonFraction></td>
<td><ix:nonFraction contextRef="C_0001_20240101_20241231"
    name="ecd:NonPeoNeoAvgCompActuallyPaidAmt" unitRef="USD"
    decimals="0">8,511,920</ix:nonFraction></td>
<td><ix:nonFraction contextRef="C_0001_20240101_20241231"
    name="ecd:TotalShareholderRtnAmt" unitRef="USD"
    decimals="2">218.36</ix:nonFraction></td>
<td><ix:nonFraction contextRef="C_0001_20240101_20241231"
    name="ecd:PeerGroupTotalShareholderRtnAmt" unitRef="USD"
    decimals="2">195.74</ix:nonFraction></td>
</tr>
<tr>
<td><ix:nonFraction contextRef="C_0001_20230101_20231231"
    name="ecd:PeoTotalCompAmt" unitRef="USD"
    decimals="0">14,000,000</ix:nonFraction></td>
<td><ix:nonFraction contextRef="C_0001_20230101_20231231"
    name="ecd:PeoActuallyPaidCompAmt" unitRef="USD"
    decimals="0">19,000,000</ix:nonFraction></td>
</tr>
</table>

<p><ix:nonNumeric contextRef="C_0001_20240101_20241231"
    name="ecd:PeoName">Tim Cook</ix:nonNumeric></p>

<p><ix:nonNumeric contextRef="C_0001_20240101_20241231"
    name="ecd:InsiderTrdPoliciesProcAdoptedFlag">true</ix:nonNumeric></p>

<p><ix:nonNumeric contextRef="C_0001_20240101_20241231"
    name="ecd:AwardTmgMnpiCnsdrdFlag">true</ix:nonNumeric></p>

<p><ix:nonNumeric contextRef="C_0001_20240101_20241231"
    name="ecd:AwardTmgPredtrmndFlag">false</ix:nonNumeric></p>

<p><ix:nonNumeric contextRef="C_0001_20240101_20241231"
    name="ecd:CoSelectedMeasureName">Revenue</ix:nonNumeric></p>

<p><ix:nonFraction contextRef="C_0001_20240101_20241231"
    name="ecd:CoSelectedMeasureAmt" unitRef="USD"
    decimals="0">391,035,000,000</ix:nonFraction></p>

</body>
</html>
"""


class TestParseEcdTags:
    def test_parses_ceo_name(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert result["ceo_name"] == "Tim Cook"

    def test_parses_ceo_total_comp(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert result["ceo_total_comp"] == 15682219.0

    def test_parses_ceo_actually_paid(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert result["ceo_comp_actually_paid"] == 22461005.0

    def test_parses_neo_avg(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert result["neo_avg_total_comp"] == 6718277.0
        assert result["neo_avg_comp_actually_paid"] == 8511920.0

    def test_parses_tsr(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert result["company_tsr"] == 218.36
        assert result["peer_group_tsr"] == 195.74

    def test_parses_boolean_flags(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert result["insider_trading_policy"] is True
        assert result["award_timing_mnpi_considered"] is True
        assert result["award_timing_predetermined"] is False

    def test_parses_company_selected_measure(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert result["company_selected_measure_name"] == "Revenue"
        assert result["company_selected_measure_amt"] == 391035000000.0

    def test_multi_year_pvp_table(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        assert "pvp_table" in result
        pvp = result["pvp_table"]
        assert len(pvp) == 2
        # Most recent year first
        assert pvp[0]["year"] == "2024"
        assert pvp[1]["year"] == "2023"
        assert pvp[1]["ceo_total_comp"] == 14000000.0

    def test_top_level_uses_most_recent_year(self) -> None:
        result = parse_ecd_tags(SAMPLE_HTML)
        # Top-level should be 2024 data, not 2023
        assert result["ceo_total_comp"] == 15682219.0

    def test_empty_html(self) -> None:
        result = parse_ecd_tags("")
        assert result == {}

    def test_no_ecd_tags(self) -> None:
        result = parse_ecd_tags("<html><body>No XBRL here</body></html>")
        assert result == {}


# ---------------------------------------------------------------------------
# Fallback: nonFraction without contextRef
# ---------------------------------------------------------------------------

SIMPLE_HTML = """
<ix:nonFraction name="ecd:PeoTotalCompAmt" unitRef="USD"
    decimals="0">5,000,000</ix:nonFraction>
<ix:nonNumeric name="ecd:PeoName">Jane Doe</ix:nonNumeric>
<ix:nonNumeric name="ecd:InsiderTrdPoliciesProcAdoptedFlag">Yes</ix:nonNumeric>
"""


class TestSimpleParsingWithoutContext:
    def test_parses_without_context_ref(self) -> None:
        result = parse_ecd_tags(SIMPLE_HTML)
        assert result.get("ceo_total_comp") == 5000000.0

    def test_parses_name_without_context(self) -> None:
        result = parse_ecd_tags(SIMPLE_HTML)
        assert result["ceo_name"] == "Jane Doe"

    def test_parses_yes_as_true(self) -> None:
        result = parse_ecd_tags(SIMPLE_HTML)
        assert result["insider_trading_policy"] is True


# ---------------------------------------------------------------------------
# Merge into CompensationAnalysis
# ---------------------------------------------------------------------------


class TestMergeEcdIntoCompensation:
    def test_merges_ceo_total_comp(self) -> None:
        from do_uw.models.common import Confidence, SourcedValue
        from do_uw.models.governance_forensics import CompensationAnalysis
        from do_uw.stages.extract.sourced import now, sourced_float

        comp = CompensationAnalysis()
        # Set LLM value (MEDIUM confidence)
        comp.ceo_total_comp = SourcedValue[float](
            value=14000000.0,
            source="DEF 14A (LLM)",
            confidence=Confidence.MEDIUM,
            as_of=now(),
        )

        ecd_data = {
            "ceo_total_comp": sourced_float(
                15682219.0, "DEF 14A XBRL", Confidence.HIGH
            ),
        }

        merge_ecd_into_compensation(ecd_data, comp)

        # XBRL should override LLM
        assert comp.ceo_total_comp is not None
        assert comp.ceo_total_comp.value == 15682219.0
        assert comp.ceo_total_comp.confidence == Confidence.HIGH

    def test_does_not_override_high_confidence(self) -> None:
        from do_uw.models.common import Confidence, SourcedValue
        from do_uw.models.governance_forensics import CompensationAnalysis
        from do_uw.stages.extract.sourced import now, sourced_float

        comp = CompensationAnalysis()
        # Already HIGH confidence
        comp.ceo_total_comp = SourcedValue[float](
            value=14000000.0,
            source="Some other HIGH source",
            confidence=Confidence.HIGH,
            as_of=now(),
        )

        ecd_data = {
            "ceo_total_comp": sourced_float(
                15682219.0, "DEF 14A XBRL", Confidence.HIGH
            ),
        }

        merge_ecd_into_compensation(ecd_data, comp)

        # Should NOT override existing HIGH
        assert comp.ceo_total_comp.value == 14000000.0

    def test_fills_empty_comp(self) -> None:
        from do_uw.models.governance_forensics import CompensationAnalysis
        from do_uw.models.common import Confidence
        from do_uw.stages.extract.sourced import sourced_float

        comp = CompensationAnalysis()
        assert comp.ceo_total_comp is None

        ecd_data = {
            "ceo_total_comp": sourced_float(
                15682219.0, "DEF 14A XBRL", Confidence.HIGH
            ),
        }

        merge_ecd_into_compensation(ecd_data, comp)
        assert comp.ceo_total_comp is not None
        assert comp.ceo_total_comp.value == 15682219.0

    def test_empty_ecd_is_noop(self) -> None:
        from do_uw.models.governance_forensics import CompensationAnalysis

        comp = CompensationAnalysis()
        merge_ecd_into_compensation({}, comp)
        assert comp.ceo_total_comp is None
