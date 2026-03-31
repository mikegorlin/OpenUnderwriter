"""Tests for brain enrichment: v6 risk questions, hazards, report sections, framework layers.

Validates that after enrichment:
- Every check has a non-null report_section (from 5 v6 sections)
- Every EVALUATIVE_CHECK has at least one risk_question (v6 X.Y format)
- Every check with factors also has risk_questions
- MANAGEMENT_DISPLAY checks have report_section but may have empty risk_questions
- brain_changelog has entries for the enrichment
- Spot-check 5 known checks for correct v6 enrichment values
"""

from __future__ import annotations

import re

import duckdb
import pytest

from do_uw.brain.brain_enrich import enrich_brain_signals
from do_uw.brain.brain_migrate import migrate_checks_to_brain
from do_uw.brain.brain_schema import connect_brain_db, create_schema


@pytest.fixture
def enriched_db() -> duckdb.DuckDBPyConnection:
    """Create in-memory DuckDB with migrated + enriched brain data."""
    conn = connect_brain_db(":memory:")
    create_schema(conn)
    # Run migration without enrichment, then enrich manually
    migrate_checks_to_brain(conn, run_enrichment=False)
    enrich_brain_signals(conn)
    return conn


class TestEnrichmentCompleteness:
    """Test that enrichment covers all 388 checks."""

    def test_all_checks_have_report_section(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Every check in brain_signals_current must have a non-null report_section."""
        count = enriched_db.execute(
            "SELECT COUNT(*) FROM brain_signals_current WHERE report_section IS NULL OR report_section = ''"
        ).fetchone()[0]
        assert count == 0, f"{count} checks have null/empty report_section"

    def test_report_section_distribution(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Report sections should cover all 5 v6 sections."""
        sections = enriched_db.execute(
            "SELECT DISTINCT report_section FROM brain_signals_current ORDER BY report_section"
        ).fetchall()
        section_names = [s[0] for s in sections]
        expected = ["company", "financial", "governance", "litigation", "market"]
        assert section_names == expected, f"Expected {expected}, got {section_names}"

    def test_evaluative_signals_have_risk_questions(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Every EVALUATIVE_CHECK must have at least one risk_question."""
        missing = enriched_db.execute(
            """SELECT signal_id FROM brain_signals_current
               WHERE content_type = 'EVALUATIVE_CHECK'
               AND (risk_questions IS NULL OR len(risk_questions) = 0)"""
        ).fetchall()
        assert len(missing) == 0, f"{len(missing)} evaluative checks missing risk_questions: {[m[0] for m in missing[:10]]}"

    def test_inference_pattern_signals_have_risk_questions(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Every INFERENCE_PATTERN must have at least one risk_question."""
        missing = enriched_db.execute(
            """SELECT signal_id FROM brain_signals_current
               WHERE content_type = 'INFERENCE_PATTERN'
               AND (risk_questions IS NULL OR len(risk_questions) = 0)"""
        ).fetchall()
        assert len(missing) == 0, f"{len(missing)} inference checks missing risk_questions: {[m[0] for m in missing[:10]]}"

    def test_checks_with_factors_have_questions(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Every check with scoring factors must also have risk_questions."""
        missing = enriched_db.execute(
            """SELECT signal_id FROM brain_signals_current
               WHERE factors IS NOT NULL AND len(factors) > 0
               AND (risk_questions IS NULL OR len(risk_questions) = 0)"""
        ).fetchall()
        assert len(missing) == 0, f"{len(missing)} checks with factors missing risk_questions: {[m[0] for m in missing[:10]]}"

    def test_management_display_have_report_section(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """MANAGEMENT_DISPLAY checks (98) must have report_section.

        64 original + 34 reclassified from EVALUATIVE_CHECK (phase 32 threshold triage).
        """
        count = enriched_db.execute(
            """SELECT COUNT(*) FROM brain_signals_current
               WHERE content_type = 'MANAGEMENT_DISPLAY'
               AND report_section IS NOT NULL AND report_section != ''"""
        ).fetchone()[0]
        assert count == 98, f"Expected 98 MANAGEMENT_DISPLAY with report_section, got {count}"

    def test_total_enriched_count(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """All 384 checks should be enriched (version 2 exists).

        388 original minus 4 deleted placeholder stubs (phase 32 threshold triage).
        """
        count = enriched_db.execute(
            "SELECT COUNT(*) FROM brain_signals_current"
        ).fetchone()[0]
        assert count == 400, f"Expected 400 current checks, got {count}"

    def test_version_2_exists(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """All current checks should be version 2 after enrichment."""
        v2_count = enriched_db.execute(
            "SELECT COUNT(*) FROM brain_signals_current WHERE version = 2"
        ).fetchone()[0]
        assert v2_count == 400, f"Expected 400 version-2 checks, got {v2_count}"

    def test_all_risk_questions_are_v6_format(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """All risk_questions should use v6 X.Y subsection format, no Q-old."""
        rows = enriched_db.execute(
            """SELECT signal_id, risk_questions FROM brain_signals_current
               WHERE risk_questions IS NOT NULL AND len(risk_questions) > 0"""
        ).fetchall()
        for signal_id, questions in rows:
            for q in questions:
                assert re.match(r"^\d+\.\d+$", q), (
                    f"{signal_id} has non-v6 question ID: {q}"
                )

    def test_no_old_q_ids_remain(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """No risk_questions should contain old Q1-Q25 identifiers."""
        rows = enriched_db.execute(
            """SELECT signal_id, risk_questions FROM brain_signals_current
               WHERE risk_questions IS NOT NULL AND len(risk_questions) > 0"""
        ).fetchall()
        for signal_id, questions in rows:
            for q in questions:
                assert not (q.startswith("Q") and q[1:].isdigit()), (
                    f"{signal_id} still has old Q-ID: {q}"
                )


class TestEnrichmentChangelog:
    """Test that changelog is populated correctly."""

    def test_changelog_has_entries(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """brain_changelog should have 384 entries (one per enriched check)."""
        count = enriched_db.execute(
            "SELECT COUNT(*) FROM brain_changelog"
        ).fetchone()[0]
        assert count == 400, f"Expected 400 changelog entries, got {count}"

    def test_changelog_change_type(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """All changelog entries should be MODIFIED type."""
        modified = enriched_db.execute(
            "SELECT COUNT(*) FROM brain_changelog WHERE change_type = 'MODIFIED'"
        ).fetchone()[0]
        assert modified == 400, f"Expected 400 MODIFIED entries, got {modified}"

    def test_changelog_triggered_by(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """All changelog entries should be triggered by phase_32_enrichment."""
        count = enriched_db.execute(
            "SELECT COUNT(*) FROM brain_changelog WHERE triggered_by = 'phase_32_enrichment'"
        ).fetchone()[0]
        assert count == 400, f"Expected 400 phase_32_enrichment entries, got {count}"


class TestSpotChecks:
    """Spot-check 5 known checks for correct v6 enrichment values."""

    def test_fin_liq_position(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """FIN.LIQ.position: financial, 3.1, risk_modifier."""
        row = enriched_db.execute(
            """SELECT report_section, risk_questions, risk_framework_layer,
                      characteristic_direction, characteristic_strength
               FROM brain_signals_current WHERE signal_id = 'FIN.LIQ.position'"""
        ).fetchone()
        assert row is not None, "FIN.LIQ.position not found"
        assert row[0] == "financial", f"report_section={row[0]}"
        assert "3.1" in row[1], f"risk_questions={row[1]}"
        assert row[2] == "risk_modifier", f"framework_layer={row[2]}"
        assert row[3] == "amplifier", f"direction={row[3]}"
        assert row[4] == "very_strong", f"strength={row[4]}"

    def test_lit_sca_active(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """LIT.SCA.active: litigation, 5.1, hazard."""
        row = enriched_db.execute(
            """SELECT report_section, risk_questions, risk_framework_layer,
                      hazards
               FROM brain_signals_current WHERE signal_id = 'LIT.SCA.active'"""
        ).fetchone()
        assert row is not None, "LIT.SCA.active not found"
        assert row[0] == "litigation", f"report_section={row[0]}"
        assert "5.1" in row[1], f"risk_questions={row[1]}"
        assert row[2] == "peril_indicator", f"framework_layer={row[2]}"
        assert "HAZ-SCA" in row[3], f"hazards={row[3]}"

    def test_gov_board_independence(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """GOV.BOARD.independence: governance, 4.1, risk_modifier."""
        row = enriched_db.execute(
            """SELECT report_section, risk_questions, risk_framework_layer,
                      characteristic_direction, characteristic_strength
               FROM brain_signals_current WHERE signal_id = 'GOV.BOARD.independence'"""
        ).fetchone()
        assert row is not None, "GOV.BOARD.independence not found"
        assert row[0] == "governance", f"report_section={row[0]}"
        assert "4.1" in row[1], f"risk_questions={row[1]}"
        assert row[2] == "risk_modifier", f"framework_layer={row[2]}"
        assert row[3] == "amplifier", f"direction={row[3]}"

    def test_biz_class_primary(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """BIZ.CLASS.primary: company, 1.1, inherent_risk."""
        row = enriched_db.execute(
            """SELECT report_section, risk_questions, risk_framework_layer
               FROM brain_signals_current WHERE signal_id = 'BIZ.CLASS.primary'"""
        ).fetchone()
        assert row is not None, "BIZ.CLASS.primary not found"
        assert row[0] == "company", f"report_section={row[0]}"
        assert "1.1" in row[1], f"risk_questions={row[1]}"
        assert row[2] == "inherent_risk", f"framework_layer={row[2]}"

    def test_fwrd_event_earnings_calendar(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """FWRD.EVENT.earnings_calendar: company (v6), 1.11, hazard."""
        row = enriched_db.execute(
            """SELECT report_section, risk_questions, risk_framework_layer
               FROM brain_signals_current WHERE signal_id = 'FWRD.EVENT.earnings_calendar'"""
        ).fetchone()
        assert row is not None, "FWRD.EVENT.earnings_calendar not found"
        assert row[0] == "company", f"report_section={row[0]}"
        assert "1.11" in row[1], f"risk_questions={row[1]}"
        assert row[2] == "peril_indicator", f"framework_layer={row[2]}"

    def test_nlp_risk_maps_to_governance(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """NLP.RISK.new_risk_factors: governance (v6 transparency), 4.3."""
        row = enriched_db.execute(
            """SELECT report_section, risk_questions
               FROM brain_signals_current WHERE signal_id = 'NLP.RISK.new_risk_factors'"""
        ).fetchone()
        assert row is not None, "NLP.RISK.new_risk_factors not found"
        assert row[0] == "governance", f"report_section={row[0]} (expected governance, transparency in v6)"
        assert "4.3" in row[1], f"risk_questions={row[1]}"

    def test_insider_trading_maps_to_market(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """GOV.INSIDER.cluster_sales: governance prefix but 2.8 (insider trading in Market)."""
        row = enriched_db.execute(
            """SELECT report_section, risk_questions
               FROM brain_signals_current WHERE signal_id = 'GOV.INSIDER.cluster_sales'"""
        ).fetchone()
        assert row is not None, "GOV.INSIDER.cluster_sales not found"
        assert row[0] == "governance", f"report_section={row[0]}"
        assert "2.8" in row[1], f"risk_questions={row[1]} (insider trading moved to Market 2.8 in v6)"


class TestRiskFrameworkDistribution:
    """Test that framework layer distribution is correct."""

    def test_inherent_risk_is_biz_checks(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Inherent risk checks should be primarily BIZ.* prefix."""
        inherent = enriched_db.execute(
            """SELECT signal_id FROM brain_signals_current
               WHERE risk_framework_layer = 'inherent_risk'"""
        ).fetchall()
        biz_count = sum(1 for r in inherent if r[0].startswith("BIZ."))
        assert biz_count >= 30, f"Expected 30+ BIZ.* inherent_risk checks, got {biz_count}"

    def test_peril_indicator_layer_includes_lit_and_fwrd(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Peril indicator layer should include LIT.* and FWRD.EVENT.* checks."""
        peril_ind = enriched_db.execute(
            """SELECT signal_id FROM brain_signals_current
               WHERE risk_framework_layer = 'peril_indicator'"""
        ).fetchall()
        lit_count = sum(1 for r in peril_ind if r[0].startswith("LIT."))
        fwrd_event_count = sum(1 for r in peril_ind if r[0].startswith("FWRD.EVENT."))
        assert lit_count >= 50, f"Expected 50+ LIT.* peril_indicator checks, got {lit_count}"
        assert fwrd_event_count >= 10, f"Expected 10+ FWRD.EVENT.* peril_indicator checks, got {fwrd_event_count}"

    def test_risk_modifier_is_majority(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Risk modifier should be the majority layer (FIN, GOV, STOCK, NLP)."""
        rm_count = enriched_db.execute(
            """SELECT COUNT(*) FROM brain_signals_current
               WHERE risk_framework_layer = 'risk_modifier'"""
        ).fetchone()[0]
        total = enriched_db.execute(
            "SELECT COUNT(*) FROM brain_signals_current"
        ).fetchone()[0]
        assert rm_count > total * 0.3, f"Expected >30% risk_modifier, got {rm_count}/{total}"


class TestHazardMappings:
    """Test hazard mapping correctness."""

    def test_hazard_count_minimum(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """At least 80 checks should have hazard mappings."""
        count = enriched_db.execute(
            """SELECT COUNT(*) FROM brain_signals_current
               WHERE hazards IS NOT NULL AND len(hazards) > 0"""
        ).fetchone()[0]
        assert count >= 80, f"Expected 80+ checks with hazards, got {count}"

    def test_insider_checks_have_sca_sec_hazards(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """Insider trading checks should map to HAZ-SCA and HAZ-SEC."""
        insider_checks = enriched_db.execute(
            """SELECT signal_id, hazards FROM brain_signals_current
               WHERE signal_id LIKE 'GOV.INSIDER.cluster%'
               OR signal_id LIKE 'EXEC.INSIDER.cluster%'"""
        ).fetchall()
        for cid, hazards in insider_checks:
            if hazards:
                assert "HAZ-SCA" in hazards, f"{cid} missing HAZ-SCA in {hazards}"
                assert "HAZ-SEC" in hazards, f"{cid} missing HAZ-SEC in {hazards}"

    def test_litigation_checks_have_hazards(self, enriched_db: duckdb.DuckDBPyConnection) -> None:
        """LIT.SCA.* checks should have HAZ-SCA hazard."""
        sca_checks = enriched_db.execute(
            """SELECT signal_id, hazards FROM brain_signals_current
               WHERE signal_id LIKE 'LIT.SCA.%'"""
        ).fetchall()
        for cid, hazards in sca_checks:
            assert "HAZ-SCA" in hazards, f"{cid} missing HAZ-SCA in {hazards}"


class TestEnrichmentReturn:
    """Test the return value from enrich_brain_signals."""

    def test_enrich_returns_counts(self) -> None:
        """enrich_brain_signals should return meaningful counts."""
        conn = connect_brain_db(":memory:")
        create_schema(conn)
        migrate_checks_to_brain(conn, run_enrichment=False)
        stats = enrich_brain_signals(conn)

        assert stats["enriched"] == 400, f"enriched={stats['enriched']}"
        assert stats["with_questions"] >= 300, f"with_questions={stats['with_questions']}"
        assert stats["with_hazards"] >= 80, f"with_hazards={stats['with_hazards']}"
        assert stats["inherent_risk"] >= 30, f"inherent_risk={stats['inherent_risk']}"
        assert stats["peril_indicator_layer"] >= 70, f"peril_indicator_layer={stats['peril_indicator_layer']}"
        conn.close()
