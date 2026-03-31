"""Converter and builder functions for program pricing store.

Converts between ORM models and Pydantic output models, and builds
TowerLayer ORM objects from EnhancedLayerInput with partial data support.
"""

from __future__ import annotations

from do_uw.knowledge.pricing_models import TowerLayer
from do_uw.knowledge.pricing_models_program import (
    Broker,
    PolicyYear,
    Program,
)
from do_uw.models.pricing import (
    BrokerOutput,
    EnhancedLayerInput,
    PolicyYearOutput,
    ProgramOutput,
    TowerLayerOutput,
)


def safe_divide(numerator: float, denominator: float) -> float:
    """Divide with zero-guard, returning 0.0 if denominator is zero."""
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def broker_to_output(broker: Broker) -> BrokerOutput:
    """Convert a Broker ORM object to a BrokerOutput Pydantic model."""
    return BrokerOutput(
        id=broker.id,
        brokerage_name=broker.brokerage_name,
        producer_name=broker.producer_name,
        email=broker.email,
        phone=broker.phone,
        notes_text=broker.notes_text,
        created_at=broker.created_at,
    )


def layer_to_output(layer: TowerLayer) -> TowerLayerOutput:
    """Convert a TowerLayer ORM object to TowerLayerOutput."""
    return TowerLayerOutput(
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


def policy_year_to_output(py: PolicyYear) -> PolicyYearOutput:
    """Convert a PolicyYear ORM object to PolicyYearOutput."""
    layers_out: list[TowerLayerOutput] = []
    if py.layers:
        for layer in py.layers:
            layers_out.append(layer_to_output(layer))
    return PolicyYearOutput(
        id=py.id,
        program_id=py.program_id,
        policy_year=py.policy_year,
        effective_date=py.effective_date,
        expiration_date=py.expiration_date,
        total_limit=py.total_limit,
        total_premium=py.total_premium,
        retention=py.retention,
        status=py.status,
        data_completeness=py.data_completeness,
        source=py.source,
        source_document=py.source_document,
        program_rate_on_line=py.program_rate_on_line,
        notes_text=py.notes_text,
        created_at=py.created_at,
        layers=layers_out,
    )


def program_to_output(program: Program) -> ProgramOutput:
    """Convert a Program ORM object to ProgramOutput."""
    broker_out: BrokerOutput | None = None
    if program.broker is not None:
        broker_out = broker_to_output(program.broker)

    py_outputs: list[PolicyYearOutput] = []
    if program.policy_years:
        for py in program.policy_years:
            py_outputs.append(policy_year_to_output(py))

    return ProgramOutput(
        id=program.id,
        ticker=program.ticker,
        company_name=program.company_name,
        anniversary_month=program.anniversary_month,
        anniversary_day=program.anniversary_day,
        broker_id=program.broker_id,
        notes_text=program.notes_text,
        created_at=program.created_at,
        updated_at=program.updated_at,
        broker=broker_out,
        policy_years=py_outputs,
    )


def build_tower_layer(
    layer_input: EnhancedLayerInput,
    quote_id: int,
) -> TowerLayer:
    """Build a TowerLayer ORM object from EnhancedLayerInput.

    Handles partial data: limit_amount, premium, and carrier
    information may all be None for fragment-level records.
    """
    limit = layer_input.limit_amount or 0.0
    premium = layer_input.premium or 0.0
    attachment = layer_input.attachment_point or 0.0
    carrier = layer_input.carrier_name or "TBD"

    layer_rol = safe_divide(premium, limit)
    ppm = safe_divide(premium, limit / 1e6) if limit > 0 else 0.0

    return TowerLayer(
        quote_id=quote_id,
        layer_position=layer_input.layer_type.value,
        layer_number=layer_input.layer_number,
        attachment_point=attachment,
        limit_amount=limit,
        premium=premium,
        carrier_name=carrier,
        carrier_rating=layer_input.carrier_rating,
        rate_on_line=layer_rol,
        premium_per_million=ppm,
        is_lead=layer_input.is_lead,
        share_pct=layer_input.share_pct,
        layer_type=layer_input.layer_type.value,
        layer_label=layer_input.layer_label,
        commission_pct=layer_input.commission_pct,
        data_source=layer_input.data_source.value,
        carrier_id=layer_input.carrier_id,
    )
