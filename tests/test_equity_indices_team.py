from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.equity_indices_team import (
    EquityIndicesEvidenceInput,
    EquityIndicesTeamConfig,
    build_equity_indices_team_forecast,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def index_evidence(
    *,
    source_id: str = "spx_futures_reference",
    source_type: str = "market_data",
    evidence_text: str = "S&P 500 futures trade above cash close with improving breadth.",
    data_timestamp: datetime = GENERATED_AT,
    data_freshness_seconds: int = 120,
    evidence_type: str = "index_futures_breadth",
    weight: Decimal = d("0.600000"),
    probability_impact: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = ("index_futures_fresh",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> EquityIndicesEvidenceInput:
    return EquityIndicesEvidenceInput(
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
    condition_id: str = "condition-index",
    market_slug: str = "sp500-above-7000",
    question: str = "Will the S&P 500 close above 7000 before August 31?",
    event_template: str = "equity_index_close_level",
    evidence: tuple[EquityIndicesEvidenceInput, ...] | None = None,
    base_probability: Decimal = d("0.600000"),
    config: EquityIndicesTeamConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]:
    return build_equity_indices_team_forecast(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        event_template=event_template,
        evidence=evidence if evidence is not None else (index_evidence(),),
        base_probability=base_probability,
        config=config
        if config is not None
        else EquityIndicesTeamConfig(config_version="equity-indices-team-v0"),
        generated_at=generated_at,
    )


def test_builds_supplied_input_equity_index_forecast_and_evidence_packets():
    forecast, evidence_rows = build_equity_indices_team_forecast(
        condition_id="condition-index",
        market_slug="sp500-above-7000",
        question="Will the S&P 500 close above 7000 before August 31?",
        event_template="equity_index_close_level",
        evidence=(
            EquityIndicesEvidenceInput(
                source_id="spx_futures_reference",
                source_type="market_data",
                evidence_text="S&P 500 futures trade above cash close with improving breadth.",
                data_timestamp=GENERATED_AT,
                data_freshness_seconds=120,
                evidence_type="index_futures_breadth",
                weight=d("0.600000"),
                probability_impact=d("0.020000"),
                reason_codes=("index_futures_fresh",),
            ),
        ),
        base_probability=d("0.600000"),
        config=EquityIndicesTeamConfig(config_version="equity-indices-team-v0"),
        generated_at=GENERATED_AT,
    )

    assert type(forecast) is TeamForecastPacket
    assert type(evidence_rows) is tuple
    assert type(evidence_rows[0]) is TeamForecastEvidencePacket
    assert forecast.team_id == "equity_indices"
    assert forecast.category_id == "finance.equity.indices"
    assert forecast.condition_id == "condition-index"
    assert forecast.market_slug == "sp500-above-7000"
    assert forecast.question == "Will the S&P 500 close above 7000 before August 31?"
    assert forecast.event_template == "equity_index_close_level"
    assert forecast.forecast_probability == d("0.620000")
    assert forecast.selected_side == "yes"
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.data_freshness_score == d("1.000000")
    assert forecast.market_implied_probability_observed == d("0.500000")
    assert forecast.base_rate == d("0.600000")
    assert forecast.reason_codes == ("index_futures_fresh", "team_equity_indices")
    assert forecast.source_references == ("spx_futures_reference",)
    assert forecast.memory_references == ("equity_indices_supplied_evidence_only",)
    assert forecast.known_failure_modes == (
        "index_gap_risk",
        "earnings_event_cluster_risk",
        "macro_headline_beta_risk",
    )
    assert forecast.config_version == "equity-indices-team-v0"
    assert forecast.prompt_version == "equity-indices-supplied-input-v0"
    assert forecast.generated_at == GENERATED_AT
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.readonly is True
    assert evidence_rows[0].evidence_id == "condition-index:spx_futures_reference"
    assert evidence_rows[0].team_id == "equity_indices"
    assert evidence_rows[0].market_slug == "sp500-above-7000"
    assert evidence_rows[0].weight == d("0.600000")
    assert evidence_rows[0].reason_codes == ("index_futures_fresh",)
    assert evidence_rows[0].paper_only is True
    assert evidence_rows[0].report_only is True
    assert evidence_rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        forecast.forecast_probability = d("0.500000")


def test_forecast_probability_clamps_to_zero_and_one():
    high_forecast, _ = build_forecast(
        base_probability=d("0.990000"),
        evidence=(index_evidence(probability_impact=d("0.250000")),),
    )
    low_forecast, _ = build_forecast(
        base_probability=d("0.010000"),
        evidence=(index_evidence(probability_impact=d("-0.250000")),),
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
def test_data_freshness_score_uses_equity_indices_thresholds(
    freshness_seconds: int,
    expected_score: Decimal,
):
    forecast, _ = build_forecast(
        evidence=(index_evidence(data_freshness_seconds=freshness_seconds),),
    )

    assert forecast.data_freshness_score == expected_score


def test_confidence_and_evidence_quality_average_weights_and_clamp_to_unit_interval():
    forecast, _ = build_forecast(
        evidence=(
            index_evidence(
                source_id="spx_futures_reference",
                weight=d("0.900000"),
                probability_impact=d("0.010000"),
            ),
            index_evidence(
                source_id="ndx_volatility_reference",
                evidence_type="index_volatility_path",
                weight=d("0.300000"),
                probability_impact=d("-0.020000"),
                reason_codes=("index_volatility_soft",),
            ),
        ),
    )

    assert forecast.forecast_probability == d("0.590000")
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.reason_codes == (
        "index_futures_fresh",
        "index_volatility_soft",
        "team_equity_indices",
    )
    assert forecast.source_references == (
        "ndx_volatility_reference",
        "spx_futures_reference",
    )


def test_selected_side_uses_market_implied_probability_hint_threshold():
    yes_forecast, _ = build_forecast(
        base_probability=d("0.620000"),
        config=EquityIndicesTeamConfig(
            config_version="equity-indices-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(index_evidence(probability_impact=d("0.000000")),),
    )
    no_forecast, _ = build_forecast(
        base_probability=d("0.619999"),
        config=EquityIndicesTeamConfig(
            config_version="equity-indices-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(index_evidence(probability_impact=d("0.000000")),),
    )

    assert yes_forecast.selected_side == "yes"
    assert no_forecast.selected_side == "no"
    assert yes_forecast.market_implied_probability_observed == d("0.620000")


def test_empty_evidence_raises():
    with pytest.raises(ValueError, match="evidence must contain at least one item"):
        build_forecast(evidence=())


def test_unsafe_side_and_config_flags_raise():
    with pytest.raises(ValueError, match="market_implied_probability_hint"):
        EquityIndicesTeamConfig(
            config_version="equity-indices-team-v0",
            market_implied_probability_hint=d("1.000001"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        EquityIndicesTeamConfig(
            config_version="equity-indices-team-v0",
            paper_only=False,
        )

    with pytest.raises(ValueError, match="report_only"):
        EquityIndicesEvidenceInput(
            source_id="spx_futures_reference",
            source_type="market_data",
            evidence_text="S&P 500 futures trade above cash close with improving breadth.",
            data_timestamp=GENERATED_AT,
            data_freshness_seconds=120,
            evidence_type="index_futures_breadth",
            weight=d("0.600000"),
            probability_impact=d("0.020000"),
            reason_codes=("index_futures_fresh",),
            report_only=False,
        )

    unsafe_config = object.__new__(EquityIndicesTeamConfig)
    object.__setattr__(unsafe_config, "config_version", "equity-indices-team-v0")
    object.__setattr__(unsafe_config, "market_implied_probability_hint", d("0.500000"))
    object.__setattr__(unsafe_config, "resolution_risk", d("0.100000"))
    object.__setattr__(
        unsafe_config,
        "prompt_version",
        "equity-indices-supplied-input-v0",
    )
    object.__setattr__(unsafe_config, "paper_only", True)
    object.__setattr__(unsafe_config, "report_only", True)
    object.__setattr__(unsafe_config, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        build_forecast(config=unsafe_config)


def test_supplied_evidence_rejects_non_decimal_values_and_non_index_event_fields():
    with pytest.raises(ValueError, match="weight must be a Decimal"):
        index_evidence(weight="0.6")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_probability must be a Decimal"):
        build_forecast(base_probability="0.6")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="probability_impact must be a Decimal"):
        index_evidence(probability_impact="0.020000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_template"):
        build_forecast(event_template=" equity_index_close_level")


def test_input_dataclasses_are_frozen():
    config = EquityIndicesTeamConfig(config_version="equity-indices-team-v0")
    evidence = index_evidence()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"
    with pytest.raises(FrozenInstanceError):
        evidence.weight = d("0.100000")

    assert replace(
        config,
        market_implied_probability_hint=d("0.510000"),
    ).market_implied_probability_hint == d("0.510000")
