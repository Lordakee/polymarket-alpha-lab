from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastEvidenceDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    team_forecast_evidence_to_db_row,
    team_forecast_outcome_to_db_row,
    team_forecast_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)
from polymarket_alpha_lab.team_memory_synthesis import (
    TeamMemoryReferenceRow,
    TeamMemorySynthesisConfig,
    TeamMemorySynthesisReport,
    build_team_memory_synthesis_report,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
DATA_TIMESTAMP = datetime(2026, 7, 1, 11, 55, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def forecast_packet(
    index: int,
    *,
    team_id: str = "crypto_btc",
    category_id: str = "finance.crypto.btc",
    event_template: str = "btc_hit_price",
    market_slug: str | None = None,
    generated_at: datetime | None = None,
    payload_probability: Decimal | None = None,
    row_probability: Decimal | None = None,
    confidence: Decimal = d("0.700000"),
) -> TeamForecastPacket:
    probability = payload_probability or d("0.600000")
    return TeamForecastPacket(
        forecast_id=f"forecast-{index:03d}",
        team_id=team_id,
        condition_id=f"condition-{index:03d}",
        market_slug=market_slug or f"{team_id}-market-{index:03d}",
        question=f"Will {team_id} market {index:03d} resolve yes?",
        category_id=category_id,
        event_template=event_template,
        selected_side="yes",
        forecast_probability=row_probability or probability,
        confidence=confidence,
        evidence_quality=d("0.800000"),
        data_freshness_score=d("0.900000"),
        resolution_risk=d("0.100000"),
        base_rate=d("0.500000"),
        market_implied_probability_observed=d("0.550000"),
        reason_codes=(f"team_{team_id}",),
        memory_references=(f"{team_id}-memory",),
        source_references=(f"source-{index:03d}",),
        known_failure_modes=(f"failure-mode-{index:03d}",),
        config_version="team-forecast-v0",
        prompt_version="team-prompt-v0",
        generated_at=generated_at or GENERATED_AT,
    )


def forecast_row(
    index: int,
    *,
    payload_probability: Decimal | None = None,
    row_probability: Decimal | None = None,
    **overrides: Any,
) -> TeamForecastDbRow:
    packet = forecast_packet(
        index,
        payload_probability=payload_probability,
        row_probability=row_probability,
        **overrides,
    )
    return team_forecast_to_db_row(packet)


def evidence_packet(
    index: int,
    *,
    team_id: str = "crypto_btc",
    market_slug: str | None = None,
) -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id=f"evidence-{index:03d}",
        team_id=team_id,
        market_slug=market_slug or f"{team_id}-market-{index:03d}",
        source_id=f"source-{index:03d}",
        source_type="market_data",
        data_timestamp=DATA_TIMESTAMP,
        data_freshness_seconds=300,
        evidence_type="supplied_evidence",
        evidence_text=f"Evidence for market {index:03d}.",
        weight=d("0.500000"),
        reason_codes=(f"team_{team_id}",),
    )


def evidence_row(
    index: int,
    *,
    forecast_id: str | None = None,
    team_id: str = "crypto_btc",
    market_slug: str | None = None,
) -> TeamForecastEvidenceDbRow:
    return team_forecast_evidence_to_db_row(
        evidence_packet(index, team_id=team_id, market_slug=market_slug),
        forecast_id=forecast_id or f"forecast-{index:03d}",
        config_version="team-forecast-evidence-v0",
        generated_at=GENERATED_AT,
    )


def outcome(
    index: int,
    *,
    outcome_id: str | None = None,
    forecast_id: str | None = None,
    team_id: str = "crypto_btc",
    market_slug: str | None = None,
    actual_outcome: str = "yes",
    resolved_at: datetime | None = None,
    generated_at: datetime | None = None,
    forecast_error: Decimal = d("0.400000"),
    brier_score: Decimal = d("0.160000"),
    directionally_correct: bool = True,
) -> TeamForecastOutcomeDbRow:
    resolved = resolved_at or GENERATED_AT
    outcome_value = TeamForecastOutcome(
        outcome_id=outcome_id or f"outcome-{index:03d}",
        forecast_id=forecast_id or f"forecast-{index:03d}",
        team_id=team_id,
        market_slug=market_slug or f"{team_id}-market-{index:03d}",
        actual_outcome=actual_outcome,
        resolved_at=resolved,
        settlement_source="polymarket_public_resolution",
        forecast_error=forecast_error,
        brier_score=brier_score,
        paper_pnl=d("0.000000"),
        cost_adjusted_return=d("0.000000"),
        directionally_correct=directionally_correct,
        profitable_after_cost=False,
        resolution_dispute_flag=False,
        reason_codes=(f"settled_{actual_outcome}",),
    )
    return team_forecast_outcome_to_db_row(
        outcome_value,
        config_version="team-forecast-outcome-v0",
        generated_at=generated_at or resolved,
    )


def low_threshold_config() -> TeamMemorySynthesisConfig:
    return TeamMemorySynthesisConfig(
        config_version="team-memory-synthesis-test-v0",
        min_category_settled_forecasts=2,
        min_event_template_settled_forecasts=2,
    )


def build_sample_report() -> TeamMemorySynthesisReport:
    forecasts = (
        forecast_row(1, payload_probability=d("0.900000")),
        forecast_row(2, payload_probability=d("0.400000")),
        forecast_row(
            3,
            event_template="btc_etf_flow",
            payload_probability=d("0.700000"),
        ),
    )
    evidence = tuple(evidence_row(index) for index in (1, 2, 3))
    outcomes = (
        outcome(1, forecast_error=d("0.100000"), brier_score=d("0.010000")),
        outcome(2, forecast_error=d("0.400000"), brier_score=d("0.160000")),
        outcome(
            3,
            market_slug="crypto_btc-market-003",
            forecast_error=d("0.300000"),
            brier_score=d("0.090000"),
        ),
    )

    return build_team_memory_synthesis_report(
        forecasts,
        evidence,
        outcomes,
        config=low_threshold_config(),
        generated_at=GENERATED_AT,
    )


def test_build_team_memory_synthesis_report_emits_category_and_event_template_rows() -> None:
    report = build_sample_report()

    assert type(report) is TeamMemorySynthesisReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-memory-synthesis-test-v0"
    assert report.forecast_row_count == 3
    assert report.unique_forecast_count == 3
    assert report.duplicate_forecast_count == 0
    assert report.evidence_row_count == 3
    assert report.outcome_row_count == 3
    assert report.orphan_evidence_count == 0
    assert report.orphan_outcome_count == 0
    assert report.eligible_reference_count == 2
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert report.reference_count == 3
    assert [row.reference_scope for row in report.rows] == [
        "team_category",
        "event_template",
        "event_template",
    ]
    category_row, etf_template_row, template_row = report.rows
    assert type(category_row) is TeamMemoryReferenceRow
    assert category_row.reference_id == (
        "team_memory:crypto_btc:finance.crypto.btc:all_event_templates"
    )
    assert category_row.team_id == "crypto_btc"
    assert category_row.category_id == "finance.crypto.btc"
    assert category_row.event_template == "all_event_templates"
    assert category_row.settled_forecast_count == 3
    assert category_row.evidence_row_count == 3
    assert category_row.directionally_correct_count == 3
    assert category_row.directionally_correct_ratio == d("1.000000")
    assert category_row.average_forecast_probability == d("0.666667")
    assert category_row.average_forecast_error == d("0.266667")
    assert category_row.average_brier_score == d("0.086667")
    assert category_row.gate_status == "eligible"
    assert category_row.reason_codes == ("eligible_memory_reference",)
    assert category_row.paper_only is True
    assert category_row.report_only is True
    assert category_row.readonly is True

    assert etf_template_row.reference_id == (
        "team_memory:crypto_btc:finance.crypto.btc:btc_etf_flow"
    )
    assert etf_template_row.reference_scope == "event_template"
    assert etf_template_row.settled_forecast_count == 1
    assert etf_template_row.gate_status == "low_sample"
    assert etf_template_row.reason_codes == ("below_min_settled_forecasts",)

    assert template_row.reference_id == (
        "team_memory:crypto_btc:finance.crypto.btc:btc_hit_price"
    )
    assert template_row.reference_scope == "event_template"
    assert template_row.event_template == "btc_hit_price"
    assert template_row.settled_forecast_count == 2
    assert template_row.evidence_row_count == 2
    assert template_row.directionally_correct_ratio == d("1.000000")
    assert template_row.average_forecast_probability == d("0.650000")
    assert template_row.average_forecast_error == d("0.250000")
    assert template_row.average_brier_score == d("0.085000")
    assert template_row.gate_status == "eligible"


def test_default_gates_suppress_small_samples_but_report_low_sample_rows() -> None:
    report = build_team_memory_synthesis_report(
        (forecast_row(1), forecast_row(2)),
        (),
        (outcome(1), outcome(2)),
        config=TeamMemorySynthesisConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.reference_count == 2
    assert report.eligible_reference_count == 0
    assert [row.reference_scope for row in report.rows] == [
        "team_category",
        "event_template",
    ]
    assert [row.gate_status for row in report.rows] == [
        "low_sample",
        "low_sample",
    ]
    assert report.rows[0].required_settled_forecast_count == 30
    assert report.rows[1].required_settled_forecast_count == 10
    assert report.rows[0].reason_codes == ("below_min_settled_forecasts",)


def test_deduplicates_forecasts_and_keeps_latest_outcome_deterministically() -> None:
    older_forecast = forecast_row(
        1,
        generated_at=GENERATED_AT - timedelta(hours=2),
        payload_probability=d("0.100000"),
    )
    latest_forecast = forecast_row(
        1,
        generated_at=GENERATED_AT - timedelta(hours=1),
        payload_probability=d("0.800000"),
    )
    later_outcome = outcome(
        1,
        outcome_id="outcome-older-id",
        resolved_at=GENERATED_AT,
        generated_at=GENERATED_AT,
        forecast_error=d("0.200000"),
        brier_score=d("0.040000"),
    )
    tie_break_outcome = outcome(
        1,
        outcome_id="outcome-z-latest-id",
        resolved_at=GENERATED_AT,
        generated_at=GENERATED_AT,
        forecast_error=d("0.600000"),
        brier_score=d("0.360000"),
    )

    report = build_team_memory_synthesis_report(
        (older_forecast, latest_forecast, forecast_row(2, payload_probability=d("0.200000"))),
        (evidence_row(1), evidence_row(2)),
        (
            later_outcome,
            tie_break_outcome,
            outcome(2, forecast_error=d("0.800000"), brier_score=d("0.640000")),
        ),
        config=low_threshold_config(),
        generated_at=GENERATED_AT,
    )

    assert report.forecast_row_count == 3
    assert report.unique_forecast_count == 2
    assert report.duplicate_forecast_count == 1
    assert report.outcome_row_count == 3
    assert report.settled_forecast_count == 2
    category_row = report.rows[0]
    assert category_row.reference_scope == "team_category"
    assert category_row.average_forecast_probability == d("0.500000")
    assert category_row.average_forecast_error == d("0.700000")
    assert category_row.average_brier_score == d("0.500000")


def test_deduplicates_forecasts_by_payload_sha256_when_generated_at_ties() -> None:
    tied_rows = (
        forecast_row(1, payload_probability=d("0.200000")),
        forecast_row(1, payload_probability=d("0.700000")),
    )
    selected_duplicate = max(tied_rows, key=lambda row: row.payload_sha256)
    expected_average = (
        selected_duplicate.forecast_probability + d("0.300000")
    ) / Decimal(2)

    report = build_team_memory_synthesis_report(
        (*tied_rows, forecast_row(2, payload_probability=d("0.300000"))),
        (),
        (outcome(1), outcome(2)),
        config=low_threshold_config(),
        generated_at=GENERATED_AT,
    )

    assert report.duplicate_forecast_count == 1
    assert report.rows[0].average_forecast_probability == expected_average.quantize(
        d("0.000001"),
    )


def test_counts_orphan_evidence_and_outcomes_without_creating_reference_rows() -> None:
    report = build_team_memory_synthesis_report(
        (forecast_row(1), forecast_row(2)),
        (
            evidence_row(1),
            evidence_row(999, forecast_id="missing-forecast-id"),
        ),
        (
            outcome(1),
            outcome(999, forecast_id="missing-forecast-id"),
        ),
        config=low_threshold_config(),
        generated_at=GENERATED_AT,
    )

    assert report.evidence_row_count == 2
    assert report.outcome_row_count == 2
    assert report.orphan_evidence_count == 1
    assert report.orphan_outcome_count == 1
    assert report.settled_forecast_count == 1
    assert report.reference_count == 2
    assert all(row.settled_forecast_count == 1 for row in report.rows)


@pytest.mark.parametrize(
    ("evidence_kwargs", "outcome_kwargs", "message"),
    (
        ({"team_id": "crypto_eth"}, {}, "evidence team_id"),
        ({"market_slug": "different-market"}, {}, "evidence market_slug"),
        ({}, {"team_id": "crypto_eth"}, "outcome team_id"),
        ({}, {"market_slug": "different-market"}, "outcome market_slug"),
    ),
)
def test_rejects_matched_evidence_or_outcome_team_and_market_mismatches(
    evidence_kwargs: dict[str, Any],
    outcome_kwargs: dict[str, Any],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_team_memory_synthesis_report(
            (forecast_row(1),),
            (evidence_row(1, **evidence_kwargs),),
            (outcome(1, **outcome_kwargs),),
            config=low_threshold_config(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    ("forecasts", "evidence", "outcomes", "config", "generated_at", "message"),
    (
        ((forecast_row(1) for _ in range(1)), (), (), low_threshold_config(), GENERATED_AT, "forecasts"),
        ({"forecast": forecast_row(1)}, (), (), low_threshold_config(), GENERATED_AT, "forecasts"),
        ("not rows", (), (), low_threshold_config(), GENERATED_AT, "forecasts"),
        (b"not rows", (), (), low_threshold_config(), GENERATED_AT, "forecasts"),
        (Path("/tmp/forecasts"), (), (), low_threshold_config(), GENERATED_AT, "forecasts"),
        ((), (evidence_row(1) for _ in range(1)), (), low_threshold_config(), GENERATED_AT, "evidence"),
        ((), {"evidence": evidence_row(1)}, (), low_threshold_config(), GENERATED_AT, "evidence"),
        ((), (), (outcome(1) for _ in range(1)), low_threshold_config(), GENERATED_AT, "outcomes"),
        ((), (), {"outcome": outcome(1)}, low_threshold_config(), GENERATED_AT, "outcomes"),
        ((), (), (), object(), GENERATED_AT, "config"),
        ((), (), (), low_threshold_config(), object(), "generated_at"),
    ),
)
def test_rejects_non_exact_input_containers_and_required_options(
    forecasts: object,
    evidence: object,
    outcomes: object,
    config: object,
    generated_at: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_team_memory_synthesis_report(
            forecasts,  # type: ignore[arg-type]
            evidence,  # type: ignore[arg-type]
            outcomes,  # type: ignore[arg-type]
            config=config,  # type: ignore[arg-type]
            generated_at=generated_at,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    ("forecasts", "evidence", "outcomes", "message"),
    (
        ((object(),), (), (), "TeamForecastDbRow"),
        ((forecast_packet(1),), (), (), "TeamForecastDbRow"),
        ((), (object(),), (), "TeamForecastEvidenceDbRow"),
        ((), (evidence_packet(1),), (), "TeamForecastEvidenceDbRow"),
        ((), (), (object(),), "TeamForecastOutcomeDbRow"),
    ),
)
def test_rejects_non_exact_db_row_items(
    forecasts: tuple[object, ...],
    evidence: tuple[object, ...],
    outcomes: tuple[object, ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        build_team_memory_synthesis_report(
            forecasts,  # type: ignore[arg-type]
            evidence,  # type: ignore[arg-type]
            outcomes,  # type: ignore[arg-type]
            config=low_threshold_config(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_rejects_constructor_bypassed_false_forecast_safety_flags(flag_name: str) -> None:
    row = forecast_row(1)
    malformed = object.__new__(TeamForecastDbRow)
    for field_name in (
        "payload_sha256",
        "generated_at",
        "forecast_id",
        "condition_id",
        "team_id",
        "market_slug",
        "config_version",
        "selected_side",
        "forecast_probability",
        "confidence",
        "payload_json",
        "paper_only",
        "report_only",
        "readonly",
    ):
        object.__setattr__(malformed, field_name, getattr(row, field_name))
    object.__setattr__(malformed, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        build_team_memory_synthesis_report(
            (malformed,),
            (),
            (),
            config=low_threshold_config(),
            generated_at=GENERATED_AT,
        )


def test_dataclasses_are_frozen_and_validate_safety_flags_and_thresholds() -> None:
    config = low_threshold_config()
    report = build_sample_report()
    row = report.rows[0]

    with pytest.raises(FrozenInstanceError):
        row.gate_status = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.config_version = "other"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config, readonly=False)
    with pytest.raises(ValueError, match="min_category_settled_forecasts"):
        TeamMemorySynthesisConfig(min_category_settled_forecasts=0)
    with pytest.raises(ValueError, match="config_version"):
        TeamMemorySynthesisConfig(config_version=" team-memory-synthesis-v0")
