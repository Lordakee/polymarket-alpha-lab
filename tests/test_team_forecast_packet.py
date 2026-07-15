from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_probability_side_edge import (
    PaperProbabilitySideEdgeConfig,
    PaperProbabilitySideEdgeInput,
    build_paper_probability_side_edge_report,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastCostInterfaceInput,
    TeamForecastEvidencePacket,
    TeamForecastPacket,
    team_forecast_packet_payload,
    team_forecast_to_side_edge_input,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
DATA_TIMESTAMP = datetime(2026, 7, 1, 11, 59, tzinfo=timezone(timedelta(hours=-4)))


def d(value: str) -> Decimal:
    return Decimal(value)


def btc_evidence_packet(
    *,
    evidence_id: str = "evidence-btc-etf-flow",
    team_id: str = "crypto_btc",
    market_slug: str = "bitcoin-above-105k-on-july-4",
    source_id: str = "source-etf-flow-dashboard",
    source_type: str = "market_data",
    data_timestamp: datetime = DATA_TIMESTAMP,
    data_freshness_seconds: int = 60,
    evidence_type: str = "etf_flow",
    evidence_text: str = "US spot ETF net flow improved over the last session.",
    weight: Decimal = d("0.4200004"),
    reason_codes: tuple[str, ...] = ("team_crypto_btc", "flow_support"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id=evidence_id,
        team_id=team_id,
        market_slug=market_slug,
        source_id=source_id,
        source_type=source_type,
        data_timestamp=data_timestamp,
        data_freshness_seconds=data_freshness_seconds,
        evidence_type=evidence_type,
        evidence_text=evidence_text,
        weight=weight,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def btc_forecast_packet(
    *,
    forecast_id: str = "forecast-btc-july4",
    team_id: str = "crypto_btc",
    condition_id: str = "0xbtccondition",
    market_slug: str = "bitcoin-above-105k-on-july-4",
    question: str = "Will Bitcoin be above $105,000 on July 4?",
    category_id: str = "finance.crypto.btc",
    event_template: str = "crypto_price_threshold",
    selected_side: str = "yes",
    forecast_probability: Decimal = d("0.6200004"),
    confidence: Decimal = d("0.7000004"),
    evidence_quality: Decimal = d("0.6500004"),
    data_freshness_score: Decimal = d("0.9000004"),
    resolution_risk: Decimal = d("0.1200004"),
    base_rate: Decimal = d("0.5400004"),
    market_implied_probability_observed: Decimal = d("0.5700004"),
    reason_codes: tuple[str, ...] = ("team_crypto_btc", "flow_support"),
    memory_references: tuple[str, ...] = ("btc-memory-2026-q2",),
    source_references: tuple[str, ...] = ("source-etf-flow-dashboard",),
    known_failure_modes: tuple[str, ...] = ("weekend_liquidity_gap",),
    config_version: str = "team-forecast-v0",
    prompt_version: str = "btc-team-prompt-v0",
    generated_at: datetime = GENERATED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamForecastPacket:
    return TeamForecastPacket(
        forecast_id=forecast_id,
        team_id=team_id,
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        category_id=category_id,
        event_template=event_template,
        selected_side=selected_side,
        forecast_probability=forecast_probability,
        confidence=confidence,
        evidence_quality=evidence_quality,
        data_freshness_score=data_freshness_score,
        resolution_risk=resolution_risk,
        base_rate=base_rate,
        market_implied_probability_observed=market_implied_probability_observed,
        reason_codes=reason_codes,
        memory_references=memory_references,
        source_references=source_references,
        known_failure_modes=known_failure_modes,
        config_version=config_version,
        prompt_version=prompt_version,
        generated_at=generated_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def btc_cost_input(
    *,
    side_price: Decimal = d("0.570000"),
    fee_cost_per_share: Decimal = d("0.004902"),
    spread_cost_per_share: Decimal = d("0.010000"),
    slippage_cost_per_share: Decimal = d("0.001000"),
    funding_cost_per_share: Decimal = d("0.000000"),
    finalization_cost_per_share: Decimal = d("0.000000"),
    time_cost_per_share: Decimal = d("0.000000"),
    risk_cost_per_share: Decimal = d("0.002000"),
    capital_cost_per_share: Decimal = d("0.001000"),
    requested_paper_shares: Decimal = d("10.000000"),
    max_executable_shares: Decimal = d("25.000000"),
    market_context_fresh: bool = True,
    settlement_context_fresh: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamForecastCostInterfaceInput:
    return TeamForecastCostInterfaceInput(
        side_price=side_price,
        fee_cost_per_share=fee_cost_per_share,
        spread_cost_per_share=spread_cost_per_share,
        slippage_cost_per_share=slippage_cost_per_share,
        funding_cost_per_share=funding_cost_per_share,
        finalization_cost_per_share=finalization_cost_per_share,
        time_cost_per_share=time_cost_per_share,
        risk_cost_per_share=risk_cost_per_share,
        capital_cost_per_share=capital_cost_per_share,
        requested_paper_shares=requested_paper_shares,
        max_executable_shares=max_executable_shares,
        market_context_fresh=market_context_fresh,
        settlement_context_fresh=settlement_context_fresh,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def assert_probability_decimal(value: Decimal) -> None:
    assert type(value) is Decimal
    assert d("0.000000") <= value <= d("1.000000")
    assert value == value.quantize(d("0.000001"))


def test_btc_forecast_packet_normalizes_probabilities_and_references():
    forecast = btc_forecast_packet()
    evidence = btc_evidence_packet()

    assert forecast.selected_side == "yes"
    for value in (
        forecast.forecast_probability,
        forecast.confidence,
        forecast.evidence_quality,
        forecast.data_freshness_score,
        forecast.resolution_risk,
        forecast.base_rate,
        forecast.market_implied_probability_observed,
        evidence.weight,
    ):
        assert_probability_decimal(value)
    assert forecast.forecast_probability == d("0.620000")
    assert evidence.weight == d("0.420000")
    assert forecast.reason_codes == ("flow_support", "team_crypto_btc")
    assert forecast.memory_references == ("btc-memory-2026-q2",)
    assert forecast.source_references == ("source-etf-flow-dashboard",)
    assert forecast.known_failure_modes == ("weekend_liquidity_gap",)
    assert evidence.reason_codes == ("flow_support", "team_crypto_btc")
    assert evidence.data_timestamp == datetime(2026, 7, 1, 15, 59, tzinfo=UTC)
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.readonly is True
    assert evidence.paper_only is True
    assert evidence.report_only is True
    assert evidence.readonly is True

    with pytest.raises(FrozenInstanceError):
        forecast.forecast_probability = d("0.500000")


def test_forecast_and_evidence_packets_reject_invalid_values_and_false_flags():
    with pytest.raises(ValueError, match="selected_side"):
        btc_forecast_packet(selected_side="maybe")
    with pytest.raises(ValueError, match="forecast_probability"):
        btc_forecast_packet(forecast_probability=d("1.000001"))
    with pytest.raises(ValueError, match="team_id"):
        btc_forecast_packet(team_id="unknown_team")
    with pytest.raises(ValueError, match="category_id"):
        btc_forecast_packet(category_id="unknown.category")
    with pytest.raises(ValueError, match="category_id must match team_id"):
        btc_forecast_packet(category_id="finance.crypto.eth")
    with pytest.raises(ValueError, match="memory_references"):
        btc_forecast_packet(memory_references=(" bad ",))
    with pytest.raises(ValueError, match="paper_only"):
        btc_forecast_packet(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        btc_forecast_packet(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        btc_forecast_packet(readonly=False)

    with pytest.raises(ValueError, match="weight"):
        btc_evidence_packet(weight=d("-0.000001"))
    with pytest.raises(ValueError, match="data_freshness_seconds"):
        btc_evidence_packet(data_freshness_seconds=-1)
    with pytest.raises(ValueError, match="source_id"):
        btc_evidence_packet(source_id="")
    with pytest.raises(ValueError, match="readonly"):
        btc_evidence_packet(readonly=False)


@pytest.mark.parametrize(
    "forecast_probability",
    (d("-0.0000004"), d("1.0000004")),
)
def test_forecast_probability_rejects_raw_out_of_range_values_before_quantization(
    forecast_probability: Decimal,
) -> None:
    with pytest.raises(ValueError, match="forecast_probability must be between zero and one"):
        btc_forecast_packet(forecast_probability=forecast_probability)


def test_forecast_probability_preserves_signed_zero_for_legacy_payload_compatibility() -> None:
    forecast = btc_forecast_packet(forecast_probability=d("-0.000000"))

    assert forecast.forecast_probability == d("0.000000")
    assert forecast.forecast_probability.is_signed() is True
    assert team_forecast_packet_payload(forecast)["forecast_probability"] == "-0.000000"


def test_durable_payload_helper_rejects_unsafe_live_surface_fields():
    payload = team_forecast_packet_payload(btc_forecast_packet())

    assert payload["forecast_probability"] == "0.620000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["reason_codes"] == ["flow_support", "team_crypto_btc"]

    unsafe_payload = dict(payload)
    unsafe_payload["order_submission"] = "never"
    with pytest.raises(ValueError, match="unsafe live surface field"):
        team_forecast_packet_payload(unsafe_payload)

    unsafe_nested_payload = dict(payload)
    unsafe_nested_payload["metadata"] = {"wallet_address": "0x0"}
    with pytest.raises(ValueError, match="unsafe live surface field"):
        team_forecast_packet_payload(unsafe_nested_payload)

    false_flag_payload = dict(payload)
    false_flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        team_forecast_packet_payload(false_flag_payload)


def test_adapter_builds_side_edge_input_from_forecast_and_central_cost_values():
    forecast = btc_forecast_packet()

    side_edge_input = team_forecast_to_side_edge_input(
        forecast,
        cost_input=TeamForecastCostInterfaceInput(
            side_price=d("0.570000"),
            fee_cost_per_share=d("0.004902"),
            spread_cost_per_share=d("0.010000"),
            slippage_cost_per_share=d("0.001000"),
            funding_cost_per_share=d("0.000000"),
            finalization_cost_per_share=d("0.000000"),
            time_cost_per_share=d("0.000000"),
            risk_cost_per_share=d("0.002000"),
            capital_cost_per_share=d("0.001000"),
            requested_paper_shares=d("10.000000"),
            max_executable_shares=d("25.000000"),
            market_context_fresh=True,
            settlement_context_fresh=True,
        ),
    )

    assert type(side_edge_input) is PaperProbabilitySideEdgeInput
    assert side_edge_input.side == "yes"
    assert side_edge_input.forecast_probability == d("0.620000")
    assert "team_crypto_btc" in side_edge_input.reason_codes
    assert side_edge_input.side_price == d("0.570000")
    assert side_edge_input.fee_cost_per_share == d("0.004902")
    assert side_edge_input.spread_cost_per_share == d("0.010000")
    assert side_edge_input.slippage_cost_per_share == d("0.001000")
    assert side_edge_input.risk_cost_per_share == d("0.002000")
    assert side_edge_input.capital_cost_per_share == d("0.001000")
    assert side_edge_input.requested_paper_shares == d("10.000000")
    assert side_edge_input.max_executable_shares == d("25.000000")
    assert side_edge_input.market_context_fresh is True
    assert side_edge_input.settlement_context_fresh is True
    assert side_edge_input.paper_only is True
    assert side_edge_input.report_only is True
    assert side_edge_input.readonly is True


def test_no_side_adapter_preserves_pyes_and_reducer_derives_pno() -> None:
    adapted = team_forecast_to_side_edge_input(
        btc_forecast_packet(
            selected_side="no",
            forecast_probability=d("0.320000"),
        ),
        cost_input=btc_cost_input(
            side_price=d("0.600000"),
            fee_cost_per_share=d("0.010000"),
            spread_cost_per_share=d("0.000000"),
            slippage_cost_per_share=d("0.000000"),
            risk_cost_per_share=d("0.000000"),
            capital_cost_per_share=d("0.000000"),
        ),
    )

    assert adapted.side == "no"
    assert adapted.forecast_probability == d("0.320000")

    report = build_paper_probability_side_edge_report(
        (adapted,),
        config=PaperProbabilitySideEdgeConfig(
            config_version="probability-side-edge-pyes-contract-v1",
            min_net_probability_edge=d("0.010000"),
        ),
        generated_at=GENERATED_AT,
    )
    assert report.rows[0].side_probability == d("0.680000")


def test_team_forecast_packet_docstring_declares_canonical_pyes() -> None:
    contract = (
        "forecast_probability always denotes canonical Decimal P(YES), regardless of "
        "selected_side; selected_side identifies the paper-review side being evaluated "
        "and never reorients forecast_probability; P(NO) is 1 - P(YES)."
    )
    assert contract in (TeamForecastPacket.__doc__ or "")


def test_team_forecast_to_side_edge_input_docstring_declares_canonical_pyes() -> None:
    contract = (
        "forecast_probability always denotes canonical Decimal P(YES), regardless of "
        "selected_side; selected_side identifies the paper-review side being evaluated "
        "and never reorients forecast_probability; P(NO) is 1 - P(YES)."
    )
    assert contract in (team_forecast_to_side_edge_input.__doc__ or "")


@pytest.mark.parametrize(
    ("field_name", "bad_value", "match"),
    (
        ("side_price", Decimal("1.000001"), "side_price"),
        ("fee_cost_per_share", Decimal("-0.000001"), "fee_cost_per_share"),
        ("requested_paper_shares", Decimal("-0.000001"), "requested_paper_shares"),
        ("max_executable_shares", Decimal("NaN"), "max_executable_shares"),
        ("market_context_fresh", "true", "market_context_fresh"),
        ("paper_only", False, "paper_only"),
        ("report_only", False, "report_only"),
        ("readonly", False, "readonly"),
    ),
)
def test_cost_interface_rejects_invalid_values(field_name, bad_value, match):
    with pytest.raises(ValueError, match=match):
        replace(btc_cost_input(), **{field_name: bad_value})
