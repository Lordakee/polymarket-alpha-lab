from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.sports_soccer_team import (
    SportsSoccerEvidenceInput,
    SportsSoccerTeamConfig,
    build_sports_soccer_team_forecast,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def soccer_evidence(
    *,
    source_id: str = "soccer_lineup_reference",
    source_type: str = "team_news",
    evidence_text: str = "Home side confirmed first-choice goalkeeper and attacking starters.",
    data_timestamp: datetime = GENERATED_AT,
    data_freshness_seconds: int = 600,
    evidence_type: str = "lineup_team_news",
    weight: Decimal = d("0.650000"),
    probability_impact: Decimal = d("0.030000"),
    reason_codes: tuple[str, ...] = ("soccer_lineup_confirmed",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SportsSoccerEvidenceInput:
    return SportsSoccerEvidenceInput(
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
    condition_id: str = "condition-soccer",
    market_slug: str = "arsenal-win-vs-chelsea",
    question: str = "Will Arsenal beat Chelsea on July 12?",
    event_template: str = "soccer_match_result",
    evidence: tuple[SportsSoccerEvidenceInput, ...] | None = None,
    base_probability: Decimal = d("0.540000"),
    config: SportsSoccerTeamConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]:
    return build_sports_soccer_team_forecast(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        event_template=event_template,
        evidence=evidence if evidence is not None else (soccer_evidence(),),
        base_probability=base_probability,
        config=config
        if config is not None
        else SportsSoccerTeamConfig(config_version="sports-soccer-team-v0"),
        generated_at=generated_at,
    )


def test_builds_supplied_input_soccer_match_result_forecast_and_evidence_packets():
    forecast, evidence_rows = build_sports_soccer_team_forecast(
        condition_id="condition-soccer",
        market_slug="arsenal-win-vs-chelsea",
        question="Will Arsenal beat Chelsea on July 12?",
        event_template="soccer_match_result",
        evidence=(
            SportsSoccerEvidenceInput(
                source_id="soccer_lineup_reference",
                source_type="team_news",
                evidence_text="Home side confirmed first-choice goalkeeper and attacking starters.",
                data_timestamp=GENERATED_AT,
                data_freshness_seconds=600,
                evidence_type="lineup_team_news",
                weight=d("0.650000"),
                probability_impact=d("0.030000"),
                reason_codes=("soccer_lineup_confirmed",),
            ),
        ),
        base_probability=d("0.540000"),
        config=SportsSoccerTeamConfig(config_version="sports-soccer-team-v0"),
        generated_at=GENERATED_AT,
    )

    assert type(forecast) is TeamForecastPacket
    assert type(evidence_rows) is tuple
    assert type(evidence_rows[0]) is TeamForecastEvidencePacket
    assert forecast.team_id == "sports_soccer"
    assert forecast.category_id == "sports.soccer"
    assert forecast.condition_id == "condition-soccer"
    assert forecast.market_slug == "arsenal-win-vs-chelsea"
    assert forecast.question == "Will Arsenal beat Chelsea on July 12?"
    assert forecast.event_template == "soccer_match_result"
    assert forecast.forecast_probability == d("0.570000")
    assert forecast.selected_side == "yes"
    assert forecast.confidence == d("0.650000")
    assert forecast.evidence_quality == d("0.650000")
    assert forecast.data_freshness_score == d("1.000000")
    assert forecast.market_implied_probability_observed == d("0.500000")
    assert forecast.base_rate == d("0.540000")
    assert forecast.reason_codes == ("soccer_lineup_confirmed", "team_sports_soccer")
    assert forecast.source_references == ("soccer_lineup_reference",)
    assert forecast.memory_references == ("soccer_supplied_evidence_only",)
    assert forecast.known_failure_modes == (
        "soccer_late_lineup_change",
        "soccer_low_scoring_variance",
        "soccer_rules_resolution_mismatch",
    )
    assert forecast.config_version == "sports-soccer-team-v0"
    assert forecast.prompt_version == "sports-soccer-supplied-input-v0"
    assert forecast.generated_at == GENERATED_AT
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.readonly is True
    assert evidence_rows[0].evidence_id == "condition-soccer:soccer_lineup_reference"
    assert evidence_rows[0].team_id == "sports_soccer"
    assert evidence_rows[0].market_slug == "arsenal-win-vs-chelsea"
    assert evidence_rows[0].weight == d("0.650000")
    assert evidence_rows[0].reason_codes == ("soccer_lineup_confirmed",)
    assert evidence_rows[0].paper_only is True
    assert evidence_rows[0].report_only is True
    assert evidence_rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        forecast.forecast_probability = d("0.500000")


def test_forecast_probability_clamps_to_zero_and_one():
    high_forecast, _ = build_forecast(
        base_probability=d("0.990000"),
        evidence=(soccer_evidence(probability_impact=d("0.250000")),),
    )
    low_forecast, _ = build_forecast(
        base_probability=d("0.010000"),
        evidence=(soccer_evidence(probability_impact=d("-0.250000")),),
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
        (10800, d("0.750000")),
        (10801, d("0.500000")),
        (86400, d("0.500000")),
        (86401, d("0.250000")),
    ),
)
def test_data_freshness_score_uses_soccer_thresholds(
    freshness_seconds: int,
    expected_score: Decimal,
):
    forecast, _ = build_forecast(
        evidence=(soccer_evidence(data_freshness_seconds=freshness_seconds),),
    )

    assert forecast.data_freshness_score == expected_score


def test_confidence_and_evidence_quality_average_weights_and_clamp_to_unit_interval():
    forecast, _ = build_forecast(
        evidence=(
            soccer_evidence(
                source_id="soccer_lineup_reference",
                weight=d("0.900000"),
                probability_impact=d("0.010000"),
            ),
            soccer_evidence(
                source_id="soccer_odds_reference",
                source_type="market_odds",
                evidence_type="odds_consensus",
                weight=d("0.300000"),
                probability_impact=d("-0.020000"),
                reason_codes=("soccer_odds_drift_against",),
            ),
        ),
    )

    assert forecast.forecast_probability == d("0.530000")
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.reason_codes == (
        "soccer_lineup_confirmed",
        "soccer_odds_drift_against",
        "team_sports_soccer",
    )
    assert forecast.source_references == (
        "soccer_lineup_reference",
        "soccer_odds_reference",
    )


def test_selected_side_uses_market_implied_probability_hint_threshold():
    yes_forecast, _ = build_forecast(
        base_probability=d("0.620000"),
        config=SportsSoccerTeamConfig(
            config_version="sports-soccer-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(soccer_evidence(probability_impact=d("0.000000")),),
    )
    no_forecast, _ = build_forecast(
        base_probability=d("0.619999"),
        config=SportsSoccerTeamConfig(
            config_version="sports-soccer-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(soccer_evidence(probability_impact=d("0.000000")),),
    )

    assert yes_forecast.selected_side == "yes"
    assert no_forecast.selected_side == "no"
    assert yes_forecast.market_implied_probability_observed == d("0.620000")


def test_empty_evidence_raises():
    with pytest.raises(ValueError, match="evidence must contain at least one item"):
        build_forecast(evidence=())


def test_unsafe_side_and_config_flags_raise():
    with pytest.raises(ValueError, match="market_implied_probability_hint"):
        SportsSoccerTeamConfig(
            config_version="sports-soccer-team-v0",
            market_implied_probability_hint=d("1.000001"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        SportsSoccerTeamConfig(config_version="sports-soccer-team-v0", paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        SportsSoccerEvidenceInput(
            source_id="soccer_lineup_reference",
            source_type="team_news",
            evidence_text="Home side confirmed first-choice goalkeeper and attacking starters.",
            data_timestamp=GENERATED_AT,
            data_freshness_seconds=600,
            evidence_type="lineup_team_news",
            weight=d("0.650000"),
            probability_impact=d("0.030000"),
            reason_codes=("soccer_lineup_confirmed",),
            report_only=False,
        )

    unsafe_config = object.__new__(SportsSoccerTeamConfig)
    object.__setattr__(unsafe_config, "config_version", "sports-soccer-team-v0")
    object.__setattr__(unsafe_config, "market_implied_probability_hint", d("0.500000"))
    object.__setattr__(unsafe_config, "resolution_risk", d("0.100000"))
    object.__setattr__(
        unsafe_config,
        "prompt_version",
        "sports-soccer-supplied-input-v0",
    )
    object.__setattr__(unsafe_config, "paper_only", True)
    object.__setattr__(unsafe_config, "report_only", True)
    object.__setattr__(unsafe_config, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        build_forecast(config=unsafe_config)


def test_supplied_evidence_rejects_non_decimal_and_non_soccer_event_fields():
    with pytest.raises(ValueError, match="weight must be a Decimal"):
        soccer_evidence(weight="0.650000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_probability must be a Decimal"):
        build_forecast(base_probability="0.540000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="probability_impact must be a Decimal"):
        soccer_evidence(probability_impact="0.030000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_template"):
        build_forecast(event_template=" soccer_match_result")


def test_input_dataclasses_are_frozen():
    config = SportsSoccerTeamConfig(config_version="sports-soccer-team-v0")
    evidence = soccer_evidence()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"
    with pytest.raises(FrozenInstanceError):
        evidence.weight = d("0.100000")

    assert replace(
        config,
        market_implied_probability_hint=d("0.510000"),
    ).market_implied_probability_hint == d("0.510000")
