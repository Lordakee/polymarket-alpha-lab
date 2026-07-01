from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.commodities_gold_team import (
    CommoditiesGoldEvidenceInput,
    CommoditiesGoldTeamConfig,
    build_commodities_gold_team_forecast,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def gold_evidence(
    *,
    source_id: str = "gold_spot_reference",
    source_type: str = "market_data",
    evidence_text: str = "Gold spot trades above target with supportive real-rate momentum.",
    data_timestamp: datetime = GENERATED_AT,
    data_freshness_seconds: int = 900,
    evidence_type: str = "spot_real_rates",
    weight: Decimal = d("0.700000"),
    probability_impact: Decimal = d("0.030000"),
    reason_codes: tuple[str, ...] = ("gold_spot_real_rates_fresh",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CommoditiesGoldEvidenceInput:
    return CommoditiesGoldEvidenceInput(
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
    condition_id: str = "condition-gold",
    market_slug: str = "gold-above-2500",
    question: str = "Will gold trade above 2500 before August 31?",
    event_template: str = "gold_hit_price",
    evidence: tuple[CommoditiesGoldEvidenceInput, ...] | None = None,
    base_probability: Decimal = d("0.570000"),
    config: CommoditiesGoldTeamConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]:
    return build_commodities_gold_team_forecast(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        event_template=event_template,
        evidence=evidence if evidence is not None else (gold_evidence(),),
        base_probability=base_probability,
        config=config
        if config is not None
        else CommoditiesGoldTeamConfig(config_version="commodities-gold-team-v0"),
        generated_at=generated_at,
    )


def test_builds_supplied_input_gold_hit_price_forecast_and_evidence_packets():
    forecast, evidence_rows = build_commodities_gold_team_forecast(
        condition_id="condition-gold",
        market_slug="gold-above-2500",
        question="Will gold trade above 2500 before August 31?",
        event_template="gold_hit_price",
        evidence=(
            CommoditiesGoldEvidenceInput(
                source_id="gold_spot_reference",
                source_type="market_data",
                evidence_text="Gold spot trades above target with supportive real-rate momentum.",
                data_timestamp=GENERATED_AT,
                data_freshness_seconds=900,
                evidence_type="spot_real_rates",
                weight=d("0.700000"),
                probability_impact=d("0.030000"),
                reason_codes=("gold_spot_real_rates_fresh",),
            ),
        ),
        base_probability=d("0.570000"),
        config=CommoditiesGoldTeamConfig(config_version="commodities-gold-team-v0"),
        generated_at=GENERATED_AT,
    )

    assert type(forecast) is TeamForecastPacket
    assert type(evidence_rows) is tuple
    assert type(evidence_rows[0]) is TeamForecastEvidencePacket
    assert forecast.team_id == "commodities_gold"
    assert forecast.category_id == "finance.commodities.gold"
    assert forecast.condition_id == "condition-gold"
    assert forecast.market_slug == "gold-above-2500"
    assert forecast.question == "Will gold trade above 2500 before August 31?"
    assert forecast.event_template == "gold_hit_price"
    assert forecast.forecast_probability == d("0.600000")
    assert forecast.selected_side == "yes"
    assert forecast.confidence == d("0.700000")
    assert forecast.evidence_quality == d("0.700000")
    assert forecast.data_freshness_score == d("1.000000")
    assert forecast.market_implied_probability_observed == d("0.500000")
    assert forecast.base_rate == d("0.570000")
    assert forecast.reason_codes == ("gold_spot_real_rates_fresh", "team_commodities_gold")
    assert forecast.source_references == ("gold_spot_reference",)
    assert forecast.memory_references == ("gold_supplied_evidence_only",)
    assert forecast.known_failure_modes == (
        "gold_real_rates_usd_risk",
        "gold_session_liquidity_gap",
    )
    assert forecast.config_version == "commodities-gold-team-v0"
    assert forecast.prompt_version == "commodities-gold-supplied-input-v0"
    assert forecast.generated_at == GENERATED_AT
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.readonly is True
    assert evidence_rows[0].evidence_id == "condition-gold:gold_spot_reference"
    assert evidence_rows[0].team_id == "commodities_gold"
    assert evidence_rows[0].market_slug == "gold-above-2500"
    assert evidence_rows[0].weight == d("0.700000")
    assert evidence_rows[0].reason_codes == ("gold_spot_real_rates_fresh",)
    assert evidence_rows[0].paper_only is True
    assert evidence_rows[0].report_only is True
    assert evidence_rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        forecast.forecast_probability = d("0.500000")


def test_forecast_probability_clamps_to_zero_and_one():
    high_forecast, _ = build_forecast(
        base_probability=d("0.990000"),
        evidence=(gold_evidence(probability_impact=d("0.250000")),),
    )
    low_forecast, _ = build_forecast(
        base_probability=d("0.010000"),
        evidence=(gold_evidence(probability_impact=d("-0.250000")),),
    )

    assert high_forecast.forecast_probability == d("1.000000")
    assert high_forecast.selected_side == "yes"
    assert low_forecast.forecast_probability == d("0.000000")
    assert low_forecast.selected_side == "no"


@pytest.mark.parametrize(
    ("freshness_seconds", "expected_score"),
    (
        (900, d("1.000000")),
        (901, d("0.750000")),
        (7200, d("0.750000")),
        (7201, d("0.500000")),
        (43200, d("0.500000")),
        (43201, d("0.250000")),
    ),
)
def test_data_freshness_score_uses_gold_thresholds(
    freshness_seconds: int,
    expected_score: Decimal,
):
    forecast, _ = build_forecast(
        evidence=(gold_evidence(data_freshness_seconds=freshness_seconds),),
    )

    assert forecast.data_freshness_score == expected_score


def test_confidence_and_evidence_quality_average_weights_and_clamp_to_unit_interval():
    forecast, _ = build_forecast(
        evidence=(
            gold_evidence(
                source_id="gold_spot_reference",
                weight=d("0.900000"),
                probability_impact=d("0.010000"),
            ),
            gold_evidence(
                source_id="gold_macro_reference",
                evidence_type="macro_real_rates",
                weight=d("0.300000"),
                probability_impact=d("-0.020000"),
                reason_codes=("gold_real_rates_soft",),
            ),
        ),
    )

    assert forecast.forecast_probability == d("0.560000")
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.reason_codes == (
        "gold_real_rates_soft",
        "gold_spot_real_rates_fresh",
        "team_commodities_gold",
    )
    assert forecast.source_references == (
        "gold_macro_reference",
        "gold_spot_reference",
    )


def test_selected_side_uses_market_implied_probability_hint_threshold():
    yes_forecast, _ = build_forecast(
        base_probability=d("0.620000"),
        config=CommoditiesGoldTeamConfig(
            config_version="commodities-gold-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(gold_evidence(probability_impact=d("0.000000")),),
    )
    no_forecast, _ = build_forecast(
        base_probability=d("0.619999"),
        config=CommoditiesGoldTeamConfig(
            config_version="commodities-gold-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(gold_evidence(probability_impact=d("0.000000")),),
    )

    assert yes_forecast.selected_side == "yes"
    assert no_forecast.selected_side == "no"
    assert yes_forecast.market_implied_probability_observed == d("0.620000")


def test_empty_evidence_raises():
    with pytest.raises(ValueError, match="evidence must contain at least one item"):
        build_forecast(evidence=())


def test_unsafe_side_and_config_flags_raise():
    with pytest.raises(ValueError, match="market_implied_probability_hint"):
        CommoditiesGoldTeamConfig(
            config_version="commodities-gold-team-v0",
            market_implied_probability_hint=d("1.000001"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        CommoditiesGoldTeamConfig(config_version="commodities-gold-team-v0", paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        CommoditiesGoldEvidenceInput(
            source_id="gold_spot_reference",
            source_type="market_data",
            evidence_text="Gold spot trades above target with supportive real-rate momentum.",
            data_timestamp=GENERATED_AT,
            data_freshness_seconds=900,
            evidence_type="spot_real_rates",
            weight=d("0.700000"),
            probability_impact=d("0.030000"),
            reason_codes=("gold_spot_real_rates_fresh",),
            report_only=False,
        )

    unsafe_config = object.__new__(CommoditiesGoldTeamConfig)
    object.__setattr__(unsafe_config, "config_version", "commodities-gold-team-v0")
    object.__setattr__(unsafe_config, "market_implied_probability_hint", d("0.500000"))
    object.__setattr__(unsafe_config, "resolution_risk", d("0.100000"))
    object.__setattr__(unsafe_config, "prompt_version", "commodities-gold-supplied-input-v0")
    object.__setattr__(unsafe_config, "paper_only", True)
    object.__setattr__(unsafe_config, "report_only", True)
    object.__setattr__(unsafe_config, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        build_forecast(config=unsafe_config)


def test_supplied_evidence_rejects_non_decimals_and_non_gold_event_fields():
    with pytest.raises(ValueError, match="weight must be a Decimal"):
        gold_evidence(weight="0.700000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_probability must be a Decimal"):
        build_forecast(base_probability="0.570000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="probability_impact must be a Decimal"):
        gold_evidence(probability_impact="0.030000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_template"):
        build_forecast(event_template=" gold_hit_price")


def test_input_dataclasses_are_frozen():
    config = CommoditiesGoldTeamConfig(config_version="commodities-gold-team-v0")
    evidence = gold_evidence()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"
    with pytest.raises(FrozenInstanceError):
        evidence.weight = d("0.100000")

    assert replace(
        config,
        market_implied_probability_hint=d("0.510000"),
    ).market_implied_probability_hint == d("0.510000")
