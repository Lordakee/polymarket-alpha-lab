from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.crypto_eth_team import (
    CryptoEthEvidenceInput,
    CryptoEthTeamConfig,
    build_crypto_eth_team_forecast,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def eth_evidence(
    *,
    source_id: str = "eth_spot_reference",
    source_type: str = "market_data",
    evidence_text: str = "ETH spot trades below target with elevated gas volatility.",
    data_timestamp: datetime = GENERATED_AT,
    data_freshness_seconds: int = 120,
    evidence_type: str = "spot_gas_volatility",
    weight: Decimal = d("0.600000"),
    probability_impact: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = ("eth_spot_fresh",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CryptoEthEvidenceInput:
    return CryptoEthEvidenceInput(
        source_id=source_id,
        source_type=source_type,
        evidence_text=evidence_text,
        data_timestamp=data_timestamp,
        data_freshness_seconds=data_freshness_seconds,
        evidence_type=evidence_type,
        weight=weight,
        probability_impact=probability_impact,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_forecast(
    *,
    condition_id: str = "condition-eth",
    market_slug: str = "ethereum-above-5000",
    question: str = "Will Ethereum hit 5000 before August 31?",
    event_template: str = "eth_hit_price",
    evidence: tuple[CryptoEthEvidenceInput, ...] | None = None,
    base_probability: Decimal = d("0.600000"),
    config: CryptoEthTeamConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]:
    return build_crypto_eth_team_forecast(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        event_template=event_template,
        evidence=evidence if evidence is not None else (eth_evidence(),),
        base_probability=base_probability,
        config=config
        if config is not None
        else CryptoEthTeamConfig(config_version="crypto-eth-team-v0"),
        generated_at=generated_at,
    )


def test_builds_supplied_input_eth_hit_price_forecast_and_evidence_packets():
    forecast, evidence_rows = build_crypto_eth_team_forecast(
        condition_id="condition-eth",
        market_slug="ethereum-above-5000",
        question="Will Ethereum hit 5000 before August 31?",
        event_template="eth_hit_price",
        evidence=(
            CryptoEthEvidenceInput(
                source_id="eth_spot_reference",
                source_type="market_data",
                evidence_text="ETH spot trades below target with elevated gas volatility.",
                data_timestamp=GENERATED_AT,
                data_freshness_seconds=120,
                evidence_type="spot_gas_volatility",
                weight=d("0.600000"),
                probability_impact=d("0.020000"),
                reason_codes=("eth_spot_fresh",),
            ),
        ),
        base_probability=d("0.600000"),
        config=CryptoEthTeamConfig(config_version="crypto-eth-team-v0"),
        generated_at=GENERATED_AT,
    )

    assert type(forecast) is TeamForecastPacket
    assert type(evidence_rows) is tuple
    assert type(evidence_rows[0]) is TeamForecastEvidencePacket
    assert forecast.team_id == "crypto_eth"
    assert forecast.category_id == "finance.crypto.eth"
    assert forecast.condition_id == "condition-eth"
    assert forecast.market_slug == "ethereum-above-5000"
    assert forecast.question == "Will Ethereum hit 5000 before August 31?"
    assert forecast.event_template == "eth_hit_price"
    assert forecast.forecast_probability == d("0.620000")
    assert forecast.selected_side == "yes"
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.data_freshness_score == d("1.000000")
    assert forecast.market_implied_probability_observed == d("0.500000")
    assert forecast.base_rate == d("0.600000")
    assert forecast.reason_codes == ("eth_spot_fresh", "team_crypto_eth")
    assert forecast.source_references == ("eth_spot_reference",)
    assert forecast.memory_references == ("eth_supplied_evidence_only",)
    assert forecast.known_failure_modes == (
        "eth_gas_fee_dislocation",
        "crypto_weekend_liquidity",
    )
    assert forecast.config_version == "crypto-eth-team-v0"
    assert forecast.prompt_version == "crypto-eth-supplied-input-v0"
    assert forecast.generated_at == GENERATED_AT
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.readonly is True
    assert evidence_rows[0].evidence_id == "condition-eth:eth_spot_reference"
    assert evidence_rows[0].team_id == "crypto_eth"
    assert evidence_rows[0].market_slug == "ethereum-above-5000"
    assert evidence_rows[0].weight == d("0.600000")
    assert evidence_rows[0].reason_codes == ("eth_spot_fresh",)
    assert evidence_rows[0].paper_only is True
    assert evidence_rows[0].report_only is True
    assert evidence_rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        forecast.forecast_probability = d("0.500000")


def test_forecast_probability_clamps_to_zero_and_one():
    high_forecast, _ = build_forecast(
        base_probability=d("0.990000"),
        evidence=(eth_evidence(probability_impact=d("0.250000")),),
    )
    low_forecast, _ = build_forecast(
        base_probability=d("0.010000"),
        evidence=(eth_evidence(probability_impact=d("-0.250000")),),
    )

    assert high_forecast.forecast_probability == d("1.000000")
    assert high_forecast.selected_side == "yes"
    assert low_forecast.forecast_probability == d("0.000000")
    assert low_forecast.selected_side == "no"


@pytest.mark.parametrize(
    ("freshness_seconds", "expected_score"),
    (
        (300, d("1.000000")),
        (301, d("0.750000")),
        (3600, d("0.750000")),
        (3601, d("0.500000")),
        (21600, d("0.500000")),
        (21601, d("0.250000")),
    ),
)
def test_data_freshness_score_uses_plan_thresholds(
    freshness_seconds: int,
    expected_score: Decimal,
):
    forecast, _ = build_forecast(
        evidence=(eth_evidence(data_freshness_seconds=freshness_seconds),),
    )

    assert forecast.data_freshness_score == expected_score


def test_confidence_and_evidence_quality_average_weights_and_clamp_to_unit_interval():
    forecast, _ = build_forecast(
        evidence=(
            eth_evidence(
                source_id="eth_spot_reference",
                weight=d("0.900000"),
                probability_impact=d("0.010000"),
            ),
            eth_evidence(
                source_id="eth_derivatives_reference",
                evidence_type="derivatives_positioning",
                weight=d("0.300000"),
                probability_impact=d("-0.020000"),
                reason_codes=("eth_derivatives_soft",),
            ),
        ),
    )

    assert forecast.forecast_probability == d("0.590000")
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.reason_codes == (
        "eth_derivatives_soft",
        "eth_spot_fresh",
        "team_crypto_eth",
    )
    assert forecast.source_references == (
        "eth_derivatives_reference",
        "eth_spot_reference",
    )


def test_selected_side_uses_market_implied_probability_hint_threshold():
    yes_forecast, _ = build_forecast(
        base_probability=d("0.620000"),
        config=CryptoEthTeamConfig(
            config_version="crypto-eth-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(eth_evidence(probability_impact=d("0.000000")),),
    )
    no_forecast, _ = build_forecast(
        base_probability=d("0.619999"),
        config=CryptoEthTeamConfig(
            config_version="crypto-eth-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(eth_evidence(probability_impact=d("0.000000")),),
    )

    assert yes_forecast.selected_side == "yes"
    assert no_forecast.selected_side == "no"
    assert yes_forecast.market_implied_probability_observed == d("0.620000")


def test_empty_evidence_raises():
    with pytest.raises(ValueError, match="evidence must contain at least one item"):
        build_forecast(evidence=())


def test_unsafe_side_and_config_flags_raise():
    with pytest.raises(ValueError, match="market_implied_probability_hint"):
        CryptoEthTeamConfig(
            config_version="crypto-eth-team-v0",
            market_implied_probability_hint=d("1.000001"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        CryptoEthTeamConfig(config_version="crypto-eth-team-v0", paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        CryptoEthEvidenceInput(
            source_id="eth_spot_reference",
            source_type="market_data",
            evidence_text="ETH spot trades below target with elevated gas volatility.",
            data_timestamp=GENERATED_AT,
            data_freshness_seconds=120,
            evidence_type="spot_gas_volatility",
            weight=d("0.600000"),
            probability_impact=d("0.020000"),
            reason_codes=("eth_spot_fresh",),
            report_only=False,
        )

    unsafe_config = object.__new__(CryptoEthTeamConfig)
    object.__setattr__(unsafe_config, "config_version", "crypto-eth-team-v0")
    object.__setattr__(unsafe_config, "market_implied_probability_hint", d("0.500000"))
    object.__setattr__(unsafe_config, "resolution_risk", d("0.100000"))
    object.__setattr__(unsafe_config, "prompt_version", "crypto-eth-supplied-input-v0")
    object.__setattr__(unsafe_config, "paper_only", True)
    object.__setattr__(unsafe_config, "report_only", True)
    object.__setattr__(unsafe_config, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        build_forecast(config=unsafe_config)


def test_supplied_evidence_rejects_non_decimal_values_and_non_eth_event_fields():
    with pytest.raises(ValueError, match="weight must be a Decimal"):
        eth_evidence(weight="0.600000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_probability must be a Decimal"):
        build_forecast(base_probability="0.600000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="probability_impact must be a Decimal"):
        eth_evidence(probability_impact="0.020000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_template"):
        build_forecast(event_template=" eth_hit_price")


def test_canonical_strings_and_reason_codes_are_required():
    with pytest.raises(ValueError, match="config_version"):
        CryptoEthTeamConfig(config_version=" crypto-eth-team-v0")

    with pytest.raises(ValueError, match="reason_codes"):
        eth_evidence(reason_codes=())

    with pytest.raises(ValueError, match="source_id"):
        eth_evidence(source_id="")


def test_input_dataclasses_are_frozen():
    config = CryptoEthTeamConfig(config_version="crypto-eth-team-v0")
    evidence = eth_evidence()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"
    with pytest.raises(FrozenInstanceError):
        evidence.weight = d("0.100000")

    replaced = replace(config, market_implied_probability_hint=d("0.510000"))
    assert replaced.market_implied_probability_hint == d("0.510000")
