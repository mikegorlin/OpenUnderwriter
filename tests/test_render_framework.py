"""Tests for the RENDER stage framework: design system and formatters.

Docx helpers, chart helpers, word renderer, and RenderStage integration
are in test_render_framework_ext.py.
"""

from __future__ import annotations

from datetime import UTC, datetime

from docx import Document  # type: ignore[import-untyped]

from do_uw.models.common import Confidence, SourcedValue
from do_uw.stages.render.design_system import (
    DesignSystem,
    configure_matplotlib_defaults,
    get_risk_color,
    setup_styles,
)
from do_uw.stages.render.formatters import (
    format_change_indicator,
    format_citation,
    format_compact,
    format_compact_table_value,
    format_currency,
    format_date,
    format_date_range,
    format_number,
    format_percentage,
    format_risk_level,
    format_source_trail,
    format_sourced_value,
    na_if_none,
    sv_val,
)

# ---- DesignSystem tests ----


class TestDesignSystem:
    """Tests for the DesignSystem frozen dataclass."""

    def test_primary_color_is_liberty_blue(self) -> None:
        ds = DesignSystem()
        # RGBColor stores as integer; check hex representation
        assert str(ds.color_primary) == "1A1446"

    def test_accent_color_is_liberty_gold(self) -> None:
        ds = DesignSystem()
        assert str(ds.color_accent) == "FFD000"

    def test_no_green_in_risk_spectrum(self) -> None:
        ds = DesignSystem()
        risk_colors = [
            ds.risk_critical,
            ds.risk_high,
            ds.risk_elevated,
            ds.risk_moderate,
            ds.risk_neutral,
        ]
        for color in risk_colors:
            # No green hue: reject pure green (#00XX00) or green-dominant
            assert "green" not in color.lower()
            # Check no #00FF00 style greens
            if color.startswith("#") and len(color) == 7:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                # Green-dominant would have G > R and G > B significantly
                assert not (g > 200 and g > r * 2 and g > b * 2), (
                    f"Color {color} appears green"
                )

    def test_font_names(self) -> None:
        ds = DesignSystem()
        assert ds.font_heading == "Georgia"
        assert ds.font_body == "Calibri"
        assert ds.font_mono == "Consolas"

    def test_header_bg_is_navy(self) -> None:
        ds = DesignSystem()
        assert ds.header_bg == "1A1446"

    def test_chart_dpi(self) -> None:
        ds = DesignSystem()
        assert ds.chart_dpi == 200


class TestSetupStyles:
    """Tests for setup_styles function."""

    def test_creates_styles_in_document(self) -> None:
        doc = Document()
        setup_styles(doc)
        style_names = [s.name for s in doc.styles]
        assert "DOHeading1" in style_names
        assert "DOHeading2" in style_names
        assert "DOHeading3" in style_names
        assert "DOBody" in style_names
        assert "DOCaption" in style_names
        assert "DOCitation" in style_names


class TestGetRiskColor:
    """Tests for get_risk_color function."""

    def test_critical_is_dark_red(self) -> None:
        assert get_risk_color("CRITICAL") == "#CC0000"

    def test_high_is_orange(self) -> None:
        assert get_risk_color("HIGH") == "#E67300"

    def test_elevated_is_amber(self) -> None:
        assert get_risk_color("ELEVATED") == "#FFB800"

    def test_moderate_is_blue(self) -> None:
        assert get_risk_color("MODERATE") == "#4A90D9"

    def test_low_is_blue(self) -> None:
        assert get_risk_color("LOW") == "#4A90D9"

    def test_neutral_is_gray(self) -> None:
        assert get_risk_color("NEUTRAL") == "#999999"

    def test_unknown_defaults_to_gray(self) -> None:
        assert get_risk_color("BOGUS") == "#999999"

    def test_case_insensitive(self) -> None:
        assert get_risk_color("critical") == "#CC0000"
        assert get_risk_color("High") == "#E67300"


class TestConfigureMatplotlib:
    """Tests for configure_matplotlib_defaults."""

    def test_sets_agg_backend(self) -> None:
        import matplotlib

        configure_matplotlib_defaults()
        assert matplotlib.get_backend().lower() == "agg"


# ---- Formatters tests ----


class TestFormatCurrency:
    """Tests for format_currency function."""

    def test_basic(self) -> None:
        assert format_currency(1234567.0) == "$1,234,567"

    def test_compact(self) -> None:
        assert format_currency(1_200_000_000.0, compact=True) == "$1.2B"

    def test_compact_millions(self) -> None:
        assert format_currency(345_000_000.0, compact=True) == "$345.0M"

    def test_none(self) -> None:
        assert format_currency(None) == "N/A"

    def test_negative(self) -> None:
        assert format_currency(-500.0) == "-$500"

    def test_zero(self) -> None:
        assert format_currency(0.0) == "$0"


class TestFormatPercentage:
    """Tests for format_percentage function."""

    def test_basic(self) -> None:
        assert format_percentage(12.34) == "12.3%"

    def test_zero_decimals(self) -> None:
        assert format_percentage(12.34, decimals=0) == "12%"

    def test_none(self) -> None:
        assert format_percentage(None) == "N/A"


class TestFormatNumber:
    """Tests for format_number function."""

    def test_basic(self) -> None:
        assert format_number(1234567) == "1,234,567"

    def test_with_decimals(self) -> None:
        assert format_number(1234.567, decimals=2) == "1,234.57"

    def test_none(self) -> None:
        assert format_number(None) == "N/A"


class TestFormatCompact:
    """Tests for format_compact function."""

    def test_billions(self) -> None:
        assert format_compact(1_200_000_000.0) == "1.2B"

    def test_millions(self) -> None:
        assert format_compact(345_000_000.0) == "345.0M"

    def test_thousands(self) -> None:
        assert format_compact(12_000.0) == "12.0K"

    def test_small(self) -> None:
        assert format_compact(42.0) == "42"

    def test_none(self) -> None:
        assert format_compact(None) == "N/A"

    def test_trillions(self) -> None:
        assert format_compact(2_500_000_000_000.0) == "2.5T"

    def test_negative(self) -> None:
        assert format_compact(-1_000_000.0) == "-1.0M"


class TestFormatDate:
    """Tests for format_date function."""

    def test_basic(self) -> None:
        dt = datetime(2024, 6, 15, tzinfo=UTC)
        assert format_date(dt) == "2024-06-15"

    def test_custom_format(self) -> None:
        dt = datetime(2024, 6, 15, tzinfo=UTC)
        assert format_date(dt, fmt="%m/%d/%Y") == "06/15/2024"

    def test_none(self) -> None:
        assert format_date(None) == "N/A"


class TestFormatCitation:
    """Tests for format_citation function."""

    def test_basic(self) -> None:
        sv: SourcedValue[str] = SourcedValue(
            value="test",
            source="SEC 10-K",
            confidence=Confidence.HIGH,
            as_of=datetime(2024, 12, 31, tzinfo=UTC),
        )
        result = format_citation(sv)
        assert result == "[SEC 10-K, 2024-12-31, HIGH]"


class TestFormatSourcedValue:
    """Tests for format_sourced_value function."""

    def test_with_sv(self) -> None:
        sv: SourcedValue[float] = SourcedValue(
            value=42.0,
            source="SEC 10-K",
            confidence=Confidence.HIGH,
            as_of=datetime(2024, 12, 31, tzinfo=UTC),
        )
        val, cite = format_sourced_value("$42", sv)
        assert val == "$42"
        assert "[SEC 10-K, 2024-12-31, HIGH]" in cite

    def test_without_sv(self) -> None:
        val, cite = format_sourced_value("test", None)
        assert val == "test"
        assert cite == ""


class TestNaIfNone:
    """Tests for na_if_none function."""

    def test_none(self) -> None:
        assert na_if_none(None) == "N/A"

    def test_value(self) -> None:
        assert na_if_none(42) == "42"

    def test_custom_fallback(self) -> None:
        assert na_if_none(None, fallback="--") == "--"


# ---- V2 formatter tests ----


class TestFormatSourceTrail:
    """Tests for format_source_trail function."""

    def test_basic(self) -> None:
        sv: SourcedValue[str] = SourcedValue(
            value="test",
            source="SEC 10-K",
            confidence=Confidence.HIGH,
            as_of=datetime(2024, 2, 15, tzinfo=UTC),
        )
        result = format_source_trail(sv)
        assert "SEC 10-K" in result
        assert "filed 2024-02-15" in result
        assert "HIGH confidence" in result

    def test_with_item_section(self) -> None:
        sv: SourcedValue[float] = SourcedValue(
            value=42.0,
            source="SEC 10-K, Item 7",
            confidence=Confidence.HIGH,
            as_of=datetime(2024, 12, 31, tzinfo=UTC),
        )
        result = format_source_trail(sv)
        assert "Item 7" in result
        assert "filed 2024-12-31" in result

    def test_low_confidence(self) -> None:
        sv: SourcedValue[str] = SourcedValue(
            value="data",
            source="Brave Search",
            confidence=Confidence.LOW,
            as_of=datetime(2024, 6, 1, tzinfo=UTC),
        )
        result = format_source_trail(sv)
        assert "LOW confidence" in result


class TestFormatRiskLevel:
    """Tests for format_risk_level function."""

    def test_critical(self) -> None:
        assert format_risk_level("critical") == "CRITICAL"

    def test_elevated(self) -> None:
        assert format_risk_level("Elevated") == "ELEVATED"

    def test_moderate(self) -> None:
        assert format_risk_level("MODERATE") == "MODERATE"

    def test_low(self) -> None:
        assert format_risk_level("low") == "LOW"

    def test_unknown_uppercased(self) -> None:
        assert format_risk_level("custom level") == "CUSTOM LEVEL"


class TestFormatDateRange:
    """Tests for format_date_range function."""

    def test_full_range(self) -> None:
        result = format_date_range("2023-01-15", "2024-03-20")
        assert result == "Jan 2023 - Mar 2024"

    def test_start_only(self) -> None:
        result = format_date_range("2023-06-01", None)
        assert result == "Jun 2023 - present"

    def test_end_only(self) -> None:
        result = format_date_range(None, "2024-12-31")
        assert result == "through Dec 2024"

    def test_both_none(self) -> None:
        assert format_date_range(None, None) == "N/A"


class TestFormatCompactTableValue:
    """Tests for format_compact_table_value function."""

    def test_none(self) -> None:
        assert format_compact_table_value(None) == "N/A"

    def test_currency(self) -> None:
        result = format_compact_table_value(1_500_000, is_currency=True)
        assert result == "$1.5M"

    def test_percentage(self) -> None:
        result = format_compact_table_value(12.34, is_pct=True)
        assert result == "12.3%"

    def test_integer(self) -> None:
        result = format_compact_table_value(1234)
        assert result == "1,234"

    def test_float_default(self) -> None:
        result = format_compact_table_value(1234.567)
        assert result == "1,234.6"

    def test_negative_currency(self) -> None:
        result = format_compact_table_value(-500_000, is_currency=True)
        assert result == "$-500.0K"


class TestSvVal:
    """Tests for sv_val function."""

    def test_with_value(self) -> None:
        sv: SourcedValue[float] = SourcedValue(
            value=42.0,
            source="SEC 10-K",
            confidence=Confidence.HIGH,
            as_of=datetime(2024, 12, 31, tzinfo=UTC),
        )
        assert sv_val(sv) == 42.0

    def test_none_returns_default(self) -> None:
        assert sv_val(None) == "N/A"

    def test_custom_default(self) -> None:
        assert sv_val(None, default=0.0) == 0.0

    def test_string_value(self) -> None:
        sv: SourcedValue[str] = SourcedValue(
            value="hello",
            source="test",
            confidence=Confidence.LOW,
            as_of=datetime(2024, 1, 1, tzinfo=UTC),
        )
        assert sv_val(sv) == "hello"


class TestFormatChangeIndicator:
    """Tests for format_change_indicator function."""

    def test_positive_change(self) -> None:
        result = format_change_indicator(112.3, 100.0)
        assert result == "+12.3%"

    def test_negative_change(self) -> None:
        result = format_change_indicator(94.3, 100.0)
        assert result == "-5.7%"

    def test_no_change(self) -> None:
        assert format_change_indicator(100.0, 100.0) == "0.0%"

    def test_zero_prior(self) -> None:
        assert format_change_indicator(50.0, 0.0) == "N/A (no prior)"

    def test_large_increase(self) -> None:
        result = format_change_indicator(200.0, 100.0)
        assert result == "+100.0%"

    def test_large_decrease(self) -> None:
        result = format_change_indicator(25.0, 100.0)
        assert result == "-75.0%"


