from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.macro_rates_team import (
    MacroRatesEvidenceInput,
    MacroRatesTeamConfig,
    build_macro_rates_team_forecast,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def rates_evidence(
    *,
    source_id: str = "fed_funds_futures_reference",
    source_type: str = "rates_market_data",
    evidence_text: str = "Fed funds futures price a lower policy-rate path after soft inflation data.",
    data_timestamp: datetime = GENERATED_AT,
    data_freshness_seconds: int = 600,
    evidence_type: str = "fed_pricing",
    weight: Decimal = d("0.700000"),
    probability_impact: Decimal = d("0.030000"),
    reason_codes: tuple[str, ...] = ("fed_pricing_shift",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MacroRatesEvidenceInput:
    return MacroRatesEvidenceInput(
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
    condition_id: str = "condition-rates",
    market_slug: str = "fed-cut-before-september",
    question: str = "Will the Fed cut rates before September 30?",
    event_template: str = "fed_policy_rate_path",
    evidence: tuple[MacroRatesEvidenceInput, ...] | None = None,
    base_probability: Decimal = d("0.520000"),
    config: MacroRatesTeamConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]:
    return build_macro_rates_team_forecast(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        event_template=event_template,
        evidence=evidence if evidence is not None else (rates_evidence(),),
        base_probability=base_probability,
        config=config
        if config is not None
        else MacroRatesTeamConfig(config_version="macro-rates-team-v0"),
        generated_at=generated_at,
    )


def test_builds_supplied_input_macro_rates_forecast_and_evidence_packets():
    forecast, evidence_rows = build_macro_rates_team_forecast(
        condition_id="condition-rates",
        market_slug="fed-cut-before-september",
        question="Will the Fed cut rates before September 30?",
        event_template="fed_policy_rate_path",
        evidence=(
            MacroRatesEvidenceInput(
                source_id="fed_funds_futures_reference",
                source_type="rates_market_data",
                evidence_text="Fed funds futures price a lower policy-rate path after soft inflation data.",
                data_timestamp=GENERATED_AT,
                data_freshness_seconds=600,
                evidence_type="fed_pricing",
                weight=d("0.700000"),
                probability_impact=d("0.030000"),
                reason_codes=("fed_pricing_shift",),
            ),
        ),
        base_probability=d("0.520000"),
        config=MacroRatesTeamConfig(config_version="macro-rates-team-v0"),
        generated_at=GENERATED_AT,
    )

    assert type(forecast) is TeamForecastPacket
    assert type(evidence_rows) is tuple
    assert type(evidence_rows[0]) is TeamForecastEvidencePacket
    assert forecast.team_id == "macro_rates"
    assert forecast.category_id == "finance.macro.rates"
    assert forecast.condition_id == "condition-rates"
    assert forecast.market_slug == "fed-cut-before-september"
    assert forecast.question == "Will the Fed cut rates before September 30?"
    assert forecast.event_template == "fed_policy_rate_path"
    assert forecast.forecast_probability == d("0.550000")
    assert forecast.selected_side == "yes"
    assert forecast.confidence == d("0.700000")
    assert forecast.evidence_quality == d("0.700000")
    assert forecast.data_freshness_score == d("1.000000")
    assert forecast.market_implied_probability_observed == d("0.500000")
    assert forecast.base_rate == d("0.520000")
    assert forecast.reason_codes == ("fed_pricing_shift", "team_macro_rates")
    assert forecast.source_references == ("fed_funds_futures_reference",)
    assert forecast.memory_references == ("macro_rates_supplied_evidence_only",)
    assert forecast.known_failure_modes == (
        "central_bank_communication_surprise",
        "economic_data_revision_risk",
        "policy_path_resolution_ambiguity",
    )
    assert forecast.config_version == "macro-rates-team-v0"
    assert forecast.prompt_version == "macro-rates-supplied-input-v0"
    assert forecast.generated_at == GENERATED_AT
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.readonly is True
    assert evidence_rows[0].evidence_id == "condition-rates:fed_funds_futures_reference"
    assert evidence_rows[0].team_id == "macro_rates"
    assert evidence_rows[0].market_slug == "fed-cut-before-september"
    assert evidence_rows[0].weight == d("0.700000")
    assert evidence_rows[0].reason_codes == ("fed_pricing_shift",)
    assert evidence_rows[0].paper_only is True
    assert evidence_rows[0].report_only is True
    assert evidence_rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        forecast.forecast_probability = d("0.500000")


def test_forecast_probability_clamps_to_zero_and_one():
    high_forecast, _ = build_forecast(
        base_probability=d("0.990000"),
        evidence=(rates_evidence(probability_impact=d("0.250000")),),
    )
    low_forecast, _ = build_forecast(
        base_probability=d("0.010000"),
        evidence=(rates_evidence(probability_impact=d("-0.250000")),),
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
def test_data_freshness_score_uses_macro_rates_thresholds(
    freshness_seconds: int,
    expected_score: Decimal,
):
    forecast, _ = build_forecast(
        evidence=(rates_evidence(data_freshness_seconds=freshness_seconds),),
    )

    assert forecast.data_freshness_score == expected_score


def test_confidence_and_evidence_quality_average_weights_and_clamp_to_unit_interval():
    forecast, _ = build_forecast(
        evidence=(
            rates_evidence(
                source_id="fed_funds_futures_reference",
                weight=d("0.900000"),
                probability_impact=d("0.010000"),
            ),
            rates_evidence(
                source_id="inflation_surprise_reference",
                source_type="economic_release",
                evidence_text="Core inflation printed below consensus and supports easier policy.",
                evidence_type="inflation_surprise",
                weight=d("0.300000"),
                probability_impact=d("-0.020000"),
                reason_codes=("inflation_surprise_soft",),
            ),
        ),
    )

    assert forecast.forecast_probability == d("0.510000")
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.reason_codes == (
        "fed_pricing_shift",
        "inflation_surprise_soft",
        "team_macro_rates",
    )
    assert forecast.source_references == (
        "fed_funds_futures_reference",
        "inflation_surprise_reference",
    )


def test_selected_side_uses_market_implied_probability_hint_threshold():
    yes_forecast, _ = build_forecast(
        base_probability=d("0.620000"),
        config=MacroRatesTeamConfig(
            config_version="macro-rates-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(rates_evidence(probability_impact=d("0.000000")),),
    )
    no_forecast, _ = build_forecast(
        base_probability=d("0.619999"),
        config=MacroRatesTeamConfig(
            config_version="macro-rates-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(rates_evidence(probability_impact=d("0.000000")),),
    )

    assert yes_forecast.selected_side == "yes"
    assert no_forecast.selected_side == "no"
    assert yes_forecast.market_implied_probability_observed == d("0.620000")


def test_empty_evidence_raises():
    with pytest.raises(ValueError, match="evidence must contain at least one item"):
        build_forecast(evidence=())


def test_unsafe_side_and_config_flags_raise():
    with pytest.raises(ValueError, match="market_implied_probability_hint"):
        MacroRatesTeamConfig(
            config_version="macro-rates-team-v0",
            market_implied_probability_hint=d("1.000001"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        MacroRatesTeamConfig(config_version="macro-rates-team-v0", paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        MacroRatesEvidenceInput(
            source_id="fed_funds_futures_reference",
            source_type="rates_market_data",
            evidence_text="Fed funds futures price a lower policy-rate path after soft inflation data.",
            data_timestamp=GENERATED_AT,
            data_freshness_seconds=600,
            evidence_type="fed_pricing",
            weight=d("0.700000"),
            probability_impact=d("0.030000"),
            reason_codes=("fed_pricing_shift",),
            report_only=False,
        )

    unsafe_config = object.__new__(MacroRatesTeamConfig)
    object.__setattr__(unsafe_config, "config_version", "macro-rates-team-v0")
    object.__setattr__(unsafe_config, "market_implied_probability_hint", d("0.500000"))
    object.__setattr__(unsafe_config, "resolution_risk", d("0.120000"))
    object.__setattr__(unsafe_config, "prompt_version", "macro-rates-supplied-input-v0")
    object.__setattr__(unsafe_config, "paper_only", True)
    object.__setattr__(unsafe_config, "report_only", True)
    object.__setattr__(unsafe_config, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        build_forecast(config=unsafe_config)


def test_supplied_evidence_rejects_non_decimal_values_and_noncanonical_fields():
    with pytest.raises(ValueError, match="weight must be a Decimal"):
        rates_evidence(weight="0.600000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_probability must be a Decimal"):
        build_forecast(base_probability=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="probability_impact must be a Decimal"):
        rates_evidence(probability_impact="0.030000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_template"):
        build_forecast(event_template=" fed_policy_rate_path")

    with pytest.raises(ValueError, match="reason_codes"):
        rates_evidence(reason_codes=("fed_pricing_shift", ""))


def test_input_dataclasses_are_frozen():
    config = MacroRatesTeamConfig(config_version="macro-rates-team-v0")
    evidence = rates_evidence()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"
    with pytest.raises(FrozenInstanceError):
        evidence.weight = d("0.100000")

    assert replace(config, market_implied_probability_hint=d("0.510000")).market_implied_probability_hint == d(
        "0.510000",
    )
