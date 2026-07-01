from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from polymarket_alpha_lab.politics_team import (
    PoliticsEvidenceInput,
    PoliticsTeamConfig,
    build_politics_team_forecast,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def politics_evidence(
    *,
    source_id: str = "polling_average_reference",
    source_type: str = "polling_data",
    evidence_text: str = "Recent polling average shows the yes side leading inside the margin of error.",
    data_timestamp: datetime = GENERATED_AT,
    data_freshness_seconds: int = 120,
    evidence_type: str = "polling_average",
    weight: Decimal = d("0.600000"),
    probability_impact: Decimal = d("0.020000"),
    reason_codes: tuple[str, ...] = ("polling_average_fresh",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> PoliticsEvidenceInput:
    return PoliticsEvidenceInput(
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
    condition_id: str = "condition-politics",
    market_slug: str = "senate-control-after-election",
    question: str = "Will Democrats control the Senate after the 2026 election?",
    event_template: str = "us_election_control",
    evidence: tuple[PoliticsEvidenceInput, ...] | None = None,
    base_probability: Decimal = d("0.600000"),
    config: PoliticsTeamConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> tuple[TeamForecastPacket, tuple[TeamForecastEvidencePacket, ...]]:
    return build_politics_team_forecast(
        condition_id=condition_id,
        market_slug=market_slug,
        question=question,
        event_template=event_template,
        evidence=evidence if evidence is not None else (politics_evidence(),),
        base_probability=base_probability,
        config=config if config is not None else PoliticsTeamConfig(config_version="politics-team-v0"),
        generated_at=generated_at,
    )


def test_builds_supplied_input_politics_forecast_and_evidence_packets():
    forecast, evidence_rows = build_politics_team_forecast(
        condition_id="condition-politics",
        market_slug="senate-control-after-election",
        question="Will Democrats control the Senate after the 2026 election?",
        event_template="us_election_control",
        evidence=(
            PoliticsEvidenceInput(
                source_id="polling_average_reference",
                source_type="polling_data",
                evidence_text="Recent polling average shows the yes side leading inside the margin of error.",
                data_timestamp=GENERATED_AT,
                data_freshness_seconds=120,
                evidence_type="polling_average",
                weight=d("0.600000"),
                probability_impact=d("0.020000"),
                reason_codes=("polling_average_fresh",),
            ),
        ),
        base_probability=d("0.600000"),
        config=PoliticsTeamConfig(config_version="politics-team-v0"),
        generated_at=GENERATED_AT,
    )

    assert type(forecast) is TeamForecastPacket
    assert type(evidence_rows) is tuple
    assert type(evidence_rows[0]) is TeamForecastEvidencePacket
    assert forecast.team_id == "politics"
    assert forecast.category_id == "politics"
    assert forecast.condition_id == "condition-politics"
    assert forecast.market_slug == "senate-control-after-election"
    assert forecast.question == "Will Democrats control the Senate after the 2026 election?"
    assert forecast.event_template == "us_election_control"
    assert forecast.forecast_probability == d("0.620000")
    assert forecast.selected_side == "yes"
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.data_freshness_score == d("1.000000")
    assert forecast.market_implied_probability_observed == d("0.500000")
    assert forecast.base_rate == d("0.600000")
    assert forecast.reason_codes == ("polling_average_fresh", "team_politics")
    assert forecast.source_references == ("polling_average_reference",)
    assert forecast.memory_references == ("politics_supplied_evidence_only",)
    assert forecast.known_failure_modes == (
        "late_breaking_news",
        "polling_error",
        "turnout_model_error",
    )
    assert forecast.config_version == "politics-team-v0"
    assert forecast.prompt_version == "politics-supplied-input-v0"
    assert forecast.generated_at == GENERATED_AT
    assert forecast.paper_only is True
    assert forecast.report_only is True
    assert forecast.readonly is True
    assert evidence_rows[0].evidence_id == "condition-politics:polling_average_reference"
    assert evidence_rows[0].team_id == "politics"
    assert evidence_rows[0].market_slug == "senate-control-after-election"
    assert evidence_rows[0].weight == d("0.600000")
    assert evidence_rows[0].reason_codes == ("polling_average_fresh",)
    assert evidence_rows[0].paper_only is True
    assert evidence_rows[0].report_only is True
    assert evidence_rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        forecast.forecast_probability = d("0.500000")


def test_forecast_probability_clamps_to_zero_and_one():
    high_forecast, _ = build_forecast(
        base_probability=d("0.990000"),
        evidence=(politics_evidence(probability_impact=d("0.250000")),),
    )
    low_forecast, _ = build_forecast(
        base_probability=d("0.010000"),
        evidence=(politics_evidence(probability_impact=d("-0.250000")),),
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
        evidence=(politics_evidence(data_freshness_seconds=freshness_seconds),),
    )

    assert forecast.data_freshness_score == expected_score


def test_confidence_and_evidence_quality_average_weights_and_clamp_to_unit_interval():
    forecast, _ = build_forecast(
        evidence=(
            politics_evidence(
                source_id="polling_average_reference",
                weight=d("0.900000"),
                probability_impact=d("0.010000"),
            ),
            politics_evidence(
                source_id="turnout_model_reference",
                evidence_type="turnout_model",
                weight=d("0.300000"),
                probability_impact=d("-0.020000"),
                reason_codes=("turnout_model_soft",),
            ),
        ),
    )

    assert forecast.forecast_probability == d("0.590000")
    assert forecast.confidence == d("0.600000")
    assert forecast.evidence_quality == d("0.600000")
    assert forecast.reason_codes == (
        "polling_average_fresh",
        "team_politics",
        "turnout_model_soft",
    )
    assert forecast.source_references == (
        "polling_average_reference",
        "turnout_model_reference",
    )


def test_selected_side_uses_market_implied_probability_hint_threshold():
    yes_forecast, _ = build_forecast(
        base_probability=d("0.620000"),
        config=PoliticsTeamConfig(
            config_version="politics-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(politics_evidence(probability_impact=d("0.000000")),),
    )
    no_forecast, _ = build_forecast(
        base_probability=d("0.619999"),
        config=PoliticsTeamConfig(
            config_version="politics-team-v0",
            market_implied_probability_hint=d("0.620000"),
        ),
        evidence=(politics_evidence(probability_impact=d("0.000000")),),
    )

    assert yes_forecast.selected_side == "yes"
    assert no_forecast.selected_side == "no"
    assert yes_forecast.market_implied_probability_observed == d("0.620000")


def test_empty_evidence_raises():
    with pytest.raises(ValueError, match="evidence must contain at least one item"):
        build_forecast(evidence=())


def test_unsafe_side_and_config_flags_raise():
    with pytest.raises(ValueError, match="market_implied_probability_hint"):
        PoliticsTeamConfig(
            config_version="politics-team-v0",
            market_implied_probability_hint=d("1.000001"),
        )

    with pytest.raises(ValueError, match="paper_only"):
        PoliticsTeamConfig(config_version="politics-team-v0", paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        PoliticsEvidenceInput(
            source_id="polling_average_reference",
            source_type="polling_data",
            evidence_text="Recent polling average shows the yes side leading inside the margin of error.",
            data_timestamp=GENERATED_AT,
            data_freshness_seconds=120,
            evidence_type="polling_average",
            weight=d("0.600000"),
            probability_impact=d("0.020000"),
            reason_codes=("polling_average_fresh",),
            report_only=False,
        )

    unsafe_config = object.__new__(PoliticsTeamConfig)
    object.__setattr__(unsafe_config, "config_version", "politics-team-v0")
    object.__setattr__(unsafe_config, "market_implied_probability_hint", d("0.500000"))
    object.__setattr__(unsafe_config, "resolution_risk", d("0.100000"))
    object.__setattr__(unsafe_config, "prompt_version", "politics-supplied-input-v0")
    object.__setattr__(unsafe_config, "paper_only", True)
    object.__setattr__(unsafe_config, "report_only", True)
    object.__setattr__(unsafe_config, "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        build_forecast(config=unsafe_config)


def test_supplied_evidence_rejects_non_decimal_values_and_noncanonical_event_fields():
    with pytest.raises(ValueError, match="weight must be a Decimal"):
        politics_evidence(weight="0.600000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="base_probability must be a Decimal"):
        build_forecast(base_probability="0.600000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="probability_impact must be a Decimal"):
        politics_evidence(probability_impact="0.020000")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="event_template"):
        build_forecast(event_template=" us_election_control")


def test_input_dataclasses_are_frozen():
    config = PoliticsTeamConfig(config_version="politics-team-v0")
    evidence = politics_evidence()

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"
    with pytest.raises(FrozenInstanceError):
        evidence.weight = d("0.100000")

    assert replace(config, market_implied_probability_hint=d("0.510000")).market_implied_probability_hint == d(
        "0.510000",
    )
