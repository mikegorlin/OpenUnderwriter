"""Pricing store CRUD API for market intelligence data.

Provides the PricingStore class for adding, querying, and managing
insurance quotes and tower layer structures. Auto-computes rate-on-line
and premium-per-million metrics on insert.

For program-based operations (programs, policy years, brokers,
carriers), see ProgramStore in pricing_store_programs.py.

Follows the KnowledgeStore pattern: contextmanager _session, engine
creation, Base.metadata.create_all for table setup.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, joinedload, sessionmaker

from do_uw.knowledge.models import Base
from do_uw.knowledge.pricing_models import Quote, TowerLayer
from do_uw.models.pricing import (
    QuoteInput,
    QuoteOutput,
    TowerLayerInput,
    TowerLayerOutput,
)

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path(__file__).parent / "knowledge.db"


def _safe_divide(numerator: float, denominator: float) -> float:
    """Divide with zero-guard, returning 0.0 if denominator is zero."""
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _quote_to_output(quote: Quote) -> QuoteOutput:
    """Convert a Quote ORM object to a QuoteOutput Pydantic model."""
    layer_outputs: list[TowerLayerOutput] = []
    for layer in quote.layers:
        layer_outputs.append(
            TowerLayerOutput(
                id=layer.id,
                layer_position=layer.layer_position,
                layer_number=layer.layer_number,
                attachment_point=layer.attachment_point,
                limit_amount=layer.limit_amount,
                premium=layer.premium,
                carrier_name=layer.carrier_name,
                carrier_rating=layer.carrier_rating,
                rate_on_line=layer.rate_on_line,
                premium_per_million=layer.premium_per_million,
                is_lead=layer.is_lead,
                share_pct=layer.share_pct,
            )
        )
    return QuoteOutput(
        id=quote.id,
        ticker=quote.ticker,
        company_name=quote.company_name,
        effective_date=quote.effective_date,
        expiration_date=quote.expiration_date,
        quote_date=quote.quote_date,
        status=quote.status,
        total_limit=quote.total_limit,
        total_premium=quote.total_premium,
        retention=quote.retention,
        market_cap_tier=quote.market_cap_tier,
        sic_code=quote.sic_code,
        sector=quote.sector,
        quality_score=quote.quality_score,
        tier=quote.tier,
        program_rate_on_line=quote.program_rate_on_line,
        source=quote.source,
        notes_text=quote.notes_text,
        created_at=quote.created_at,
        layers=layer_outputs,
    )


class PricingStore:
    """CRUD API for D&O insurance pricing and market intelligence.

    Stores quotes, tower layer structures, and provides segment-based
    rate queries for the analytics engine.

    Args:
        db_path: Path to SQLite database. Use None for in-memory.
            Defaults to knowledge.db in the knowledge package directory.
    """

    def __init__(self, db_path: str | Path | None = _DEFAULT_DB_PATH) -> None:
        if db_path is None:
            url = "sqlite://"
        else:
            url = f"sqlite:///{db_path}"
        self._engine: Engine = create_engine(url, echo=False)
        self._session_factory = sessionmaker(bind=self._engine)
        Base.metadata.create_all(self._engine)

    @contextmanager
    def _session(self) -> Iterator[Session]:
        """Yield a session with commit/rollback handling."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_quote(self, quote_input: QuoteInput) -> int:
        """Add a new insurance quote with optional tower layers.

        Computes program_rate_on_line automatically from total
        premium and total limit. For each layer, computes
        rate_on_line and premium_per_million.

        Returns:
            The database ID of the created quote.
        """
        now = datetime.now(UTC)
        rol = _safe_divide(
            quote_input.total_premium, quote_input.total_limit
        )

        quote = Quote(
            ticker=quote_input.ticker.upper(),
            company_name=quote_input.company_name,
            effective_date=quote_input.effective_date,
            expiration_date=quote_input.expiration_date,
            quote_date=quote_input.quote_date,
            status=quote_input.status.value,
            total_limit=quote_input.total_limit,
            total_premium=quote_input.total_premium,
            retention=quote_input.retention,
            market_cap_tier=quote_input.market_cap_tier.value,
            sic_code=quote_input.sic_code,
            sector=quote_input.sector,
            quality_score=quote_input.quality_score,
            tier=quote_input.tier,
            program_rate_on_line=rol,
            source=quote_input.source,
            notes_text=quote_input.notes_text,
            created_at=now,
        )

        for layer_input in quote_input.layers:
            layer_rol = _safe_divide(
                layer_input.premium, layer_input.limit_amount
            )
            ppm = _safe_divide(
                layer_input.premium, layer_input.limit_amount / 1e6
            )
            layer = TowerLayer(
                layer_position=layer_input.layer_position,
                layer_number=layer_input.layer_number,
                attachment_point=layer_input.attachment_point,
                limit_amount=layer_input.limit_amount,
                premium=layer_input.premium,
                carrier_name=layer_input.carrier_name,
                carrier_rating=layer_input.carrier_rating,
                rate_on_line=layer_rol,
                premium_per_million=ppm,
                is_lead=layer_input.is_lead,
                share_pct=layer_input.share_pct,
            )
            quote.layers.append(layer)

        with self._session() as session:
            session.add(quote)
            session.flush()
            quote_id: int = quote.id

        return quote_id

    def get_quote(self, quote_id: int) -> QuoteOutput | None:
        """Get a quote by ID with eager-loaded layers.

        Returns:
            QuoteOutput Pydantic model, or None if not found.
        """
        with self._session() as session:
            stmt = (
                select(Quote)
                .options(joinedload(Quote.layers))
                .where(Quote.id == quote_id)
            )
            quote = session.execute(stmt).unique().scalar_one_or_none()
            if quote is None:
                return None
            return _quote_to_output(quote)

    def list_quotes(
        self,
        ticker: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[QuoteOutput]:
        """List quotes with optional ticker and status filters.

        Results are ordered by effective_date descending (most recent first).

        Returns:
            List of QuoteOutput Pydantic models.
        """
        with self._session() as session:
            stmt = (
                select(Quote)
                .options(joinedload(Quote.layers))
                .order_by(Quote.effective_date.desc())
            )
            if ticker is not None:
                stmt = stmt.where(Quote.ticker == ticker.upper())
            if status is not None:
                stmt = stmt.where(Quote.status == status.upper())
            stmt = stmt.limit(limit)
            quotes = list(
                session.execute(stmt).unique().scalars().all()
            )
            return [_quote_to_output(q) for q in quotes]

    def add_tower_layer(
        self, quote_id: int, layer: TowerLayerInput
    ) -> int:
        """Add a tower layer to an existing quote.

        Computes rate_on_line and premium_per_million automatically.

        Returns:
            The database ID of the created tower layer.

        Raises:
            ValueError: If the quote_id does not exist.
        """
        layer_rol = _safe_divide(layer.premium, layer.limit_amount)
        ppm = _safe_divide(layer.premium, layer.limit_amount / 1e6)

        with self._session() as session:
            quote = session.get(Quote, quote_id)
            if quote is None:
                msg = f"Quote {quote_id} not found"
                raise ValueError(msg)

            tower_layer = TowerLayer(
                quote_id=quote_id,
                layer_position=layer.layer_position,
                layer_number=layer.layer_number,
                attachment_point=layer.attachment_point,
                limit_amount=layer.limit_amount,
                premium=layer.premium,
                carrier_name=layer.carrier_name,
                carrier_rating=layer.carrier_rating,
                rate_on_line=layer_rol,
                premium_per_million=ppm,
                is_lead=layer.is_lead,
                share_pct=layer.share_pct,
            )
            session.add(tower_layer)
            session.flush()
            layer_id: int = tower_layer.id

        return layer_id

    def get_tower_comparison(
        self, ticker: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Get recent tower structures for a company for comparison.

        Returns a list of dicts with quote info and nested layers,
        ordered by effective_date descending.
        """
        with self._session() as session:
            stmt = (
                select(Quote)
                .options(joinedload(Quote.layers))
                .where(Quote.ticker == ticker.upper())
                .order_by(Quote.effective_date.desc())
                .limit(limit)
            )
            quotes = list(
                session.execute(stmt).unique().scalars().all()
            )
            results: list[dict[str, Any]] = []
            for q in quotes:
                layers_data: list[dict[str, Any]] = []
                for layer in sorted(
                    q.layers, key=lambda x: x.layer_number
                ):
                    layers_data.append(
                        {
                            "layer_number": layer.layer_number,
                            "position": layer.layer_position,
                            "attachment_point": layer.attachment_point,
                            "limit_amount": layer.limit_amount,
                            "premium": layer.premium,
                            "carrier_name": layer.carrier_name,
                            "rate_on_line": layer.rate_on_line,
                            "premium_per_million": layer.premium_per_million,
                        }
                    )
                results.append(
                    {
                        "quote_id": q.id,
                        "effective_date": q.effective_date.isoformat(),
                        "status": q.status,
                        "total_limit": q.total_limit,
                        "total_premium": q.total_premium,
                        "program_rate_on_line": q.program_rate_on_line,
                        "layers": layers_data,
                    }
                )
            return results

    def update_quote_status(
        self, quote_id: int, new_status: str
    ) -> bool:
        """Update the status of a quote.

        Returns:
            True if the quote was found and updated, False otherwise.
        """
        with self._session() as session:
            quote = session.get(Quote, quote_id)
            if quote is None:
                return False
            quote.status = new_status.upper()
            session.flush()
        return True

    def _segment_filters(
        self,
        market_cap_tier: str | None,
        sector: str | None,
        status_filter: list[str] | None,
        months_back: int,
    ) -> tuple[list[str], datetime]:
        """Build common filter parameters for segment queries."""
        statuses = status_filter or ["QUOTED", "BOUND"]
        cutoff = datetime.now(UTC) - timedelta(days=months_back * 30)
        return statuses, cutoff

    def _apply_segment_where(
        self,
        stmt: Any,
        market_cap_tier: str | None,
        sector: str | None,
    ) -> Any:
        """Apply market_cap_tier and sector filters to a statement."""
        if market_cap_tier is not None:
            stmt = stmt.where(
                Quote.market_cap_tier == market_cap_tier.upper()
            )
        if sector is not None:
            stmt = stmt.where(Quote.sector == sector)
        return stmt

    def get_rates_for_segment(
        self,
        market_cap_tier: str | None = None,
        sector: str | None = None,
        layer_position: str | None = None,
        status_filter: list[str] | None = None,
        months_back: int = 24,
    ) -> list[float]:
        """Get rate_on_line values for a market segment.

        Returns:
            List of rate_on_line float values.
        """
        statuses, cutoff = self._segment_filters(
            market_cap_tier, sector, status_filter, months_back
        )
        with self._session() as session:
            if layer_position is not None:
                stmt = (
                    select(TowerLayer.rate_on_line)
                    .join(Quote, TowerLayer.quote_id == Quote.id)
                    .where(Quote.effective_date >= cutoff)
                    .where(Quote.status.in_(statuses))
                    .where(TowerLayer.layer_position == layer_position.upper())
                )
            else:
                stmt = (
                    select(Quote.program_rate_on_line)
                    .where(Quote.effective_date >= cutoff)
                    .where(Quote.status.in_(statuses))
                )
            stmt = self._apply_segment_where(stmt, market_cap_tier, sector)
            rows = session.execute(stmt).all()
            return [float(r[0]) for r in rows]

    def get_rates_with_dates(
        self,
        market_cap_tier: str | None = None,
        sector: str | None = None,
        layer_position: str | None = None,
        status_filter: list[str] | None = None,
        months_back: int = 24,
    ) -> list[tuple[float, datetime]]:
        """Get rate_on_line paired with effective dates for trend analysis."""
        statuses, cutoff = self._segment_filters(
            market_cap_tier, sector, status_filter, months_back
        )
        with self._session() as session:
            if layer_position is not None:
                stmt = (
                    select(TowerLayer.rate_on_line, Quote.effective_date)
                    .join(Quote, TowerLayer.quote_id == Quote.id)
                    .where(Quote.effective_date >= cutoff)
                    .where(Quote.status.in_(statuses))
                    .where(TowerLayer.layer_position == layer_position.upper())
                )
            else:
                stmt = (
                    select(Quote.program_rate_on_line, Quote.effective_date)
                    .where(Quote.effective_date >= cutoff)
                    .where(Quote.status.in_(statuses))
                )
            stmt = self._apply_segment_where(stmt, market_cap_tier, sector)
            rows = session.execute(stmt).all()
            return [(float(r[0]), r[1]) for r in rows]

    def get_rates_with_dates_and_scores(
        self,
        market_cap_tier: str | None = None,
        sector: str | None = None,
        status_filter: list[str] | None = None,
        months_back: int = 24,
    ) -> list[tuple[float, datetime, float | None]]:
        """Get rates with dates and quality scores for score filtering."""
        statuses, cutoff = self._segment_filters(
            market_cap_tier, sector, status_filter, months_back
        )
        with self._session() as session:
            stmt = (
                select(
                    Quote.program_rate_on_line,
                    Quote.effective_date,
                    Quote.quality_score,
                )
                .where(Quote.effective_date >= cutoff)
                .where(Quote.status.in_(statuses))
            )
            stmt = self._apply_segment_where(stmt, market_cap_tier, sector)
            rows = session.execute(stmt).all()
            result: list[tuple[float, datetime, float | None]] = []
            for r in rows:
                score: float | None = (
                    float(r[2]) if r[2] is not None else None
                )
                result.append((float(r[0]), r[1], score))
            return result
