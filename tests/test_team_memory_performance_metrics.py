from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from inspect import getsource
from typing import Any

import pytest

from polymarket_alpha_lab.team_memory_performance_metrics import (
    TeamMemoryPaperOutcomeRow,
    TeamMemoryPaperPredictionRow,
    TeamMemoryPerformanceMetricsConfig,
    build_team_memory_performance_metrics_report,
    team_memory_performance_metrics_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 12, 0, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def prediction(
    prediction_id: str,
    *,
    team_id: str = "crypto_btc",
    market_slug: str = "bitcoin-above-120k",
    forecast_probability: Decimal = d("0.800000"),
    implied_probability: Decimal = d("0.500000"),
    generated_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamMemoryPaperPredictionRow:
    return TeamMemoryPaperPredictionRow(
        prediction_id=prediction_id,
        team_id=team_id,
        market_slug=market_slug,
        forecast_probability=forecast_probability,
        implied_probability=implied_probability,
        generated_at=generated_at or GENERATED_AT,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def outcome(
    prediction_id: str,
    *,
    outcome_id: str | None = None,
    team_id: str = "crypto_btc",
    market_slug: str = "bitcoin-above-120k",
    actual_outcome: str = "yes",
    resolved_at: datetime | None = None,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> TeamMemoryPaperOutcomeRow:
    return TeamMemoryPaperOutcomeRow(
        outcome_id=outcome_id or f"outcome-{prediction_id}",
        prediction_id=prediction_id,
        team_id=team_id,
        market_slug=market_slug,
        actual_outcome=actual_outcome,
        resolved_at=resolved_at or GENERATED_AT + timedelta(days=1),
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def config(**overrides: object) -> TeamMemoryPerformanceMetricsConfig:
    values: dict[str, object] = {
        "config_version": "team-memory-performance-metrics-test",
        "edge_bucket_bounds": (d("0.050000"), d("0.150000")),
        "developing_sample_size": 2,
        "confident_sample_size": 3,
    }
    values.update(overrides)
    return TeamMemoryPerformanceMetricsConfig(**values)


def bypassed(value: object, **overrides: Any) -> object:
    malformed = object.__new__(type(value))
    for key, item in value.__dict__.items():
        object.__setattr__(malformed, key, item)
    for key, item in overrides.items():
        object.__setattr__(malformed, key, item)
    return malformed


def test_aggregates_team_memory_metrics_by_team_and_edge_bucket() -> None:
    report = build_team_memory_performance_metrics_report(
        (
            prediction(
                "btc-high-edge-hit",
                forecast_probability=d("0.800000"),
                implied_probability=d("0.500000"),
            ),
            prediction(
                "btc-medium-edge-hit",
                market_slug="bitcoin-above-100k",
                forecast_probability=d("0.400000"),
                implied_probability=d("0.300000"),
            ),
            prediction(
                "btc-low-edge-hit",
                market_slug="bitcoin-above-110k",
                forecast_probability=d("0.600000"),
                implied_probability=d("0.580000"),
            ),
            prediction(
                "eth-thin-miss",
                team_id="crypto_eth",
                market_slug="ethereum-above-8k",
                forecast_probability=d("0.700000"),
                implied_probability=d("0.620000"),
            ),
            prediction(
                "eth-unresolved",
                team_id="crypto_eth",
                market_slug="ethereum-above-10k",
                forecast_probability=d("0.550000"),
                implied_probability=d("0.500000"),
            ),
        ),
        (
            outcome("btc-high-edge-hit", actual_outcome="yes"),
            outcome(
                "btc-medium-edge-hit",
                market_slug="bitcoin-above-100k",
                actual_outcome="no",
            ),
            outcome(
                "btc-low-edge-hit",
                market_slug="bitcoin-above-110k",
                actual_outcome="yes",
            ),
            outcome(
                "eth-thin-miss",
                team_id="crypto_eth",
                market_slug="ethereum-above-8k",
                actual_outcome="no",
            ),
        ),
        config=config(),
        generated_at=datetime(2026, 7, 3, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-memory-performance-metrics-test"
    assert report.prediction_count == 5
    assert report.resolved_count == 4
    assert report.unresolved_count == 1
    assert report.team_count == 2
    assert report.status == "candidate"
    assert report.reason_codes == ("thin_team_sample", "unresolved_predictions")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    btc = report.team_rows[0]
    assert btc.team_id == "crypto_btc"
    assert btc.prediction_count == 3
    assert btc.resolved_count == 3
    assert btc.unresolved_count == 0
    assert btc.observed_rate == d("0.666667")
    assert btc.average_forecast_probability == d("0.600000")
    assert btc.calibration_error == d("0.066667")
    assert btc.brier_score == d("0.120000")
    assert btc.hit_rate == d("1.000000")
    assert btc.average_absolute_edge == d("0.140000")
    assert btc.sample_size_confidence == "confident"
    assert btc.sample_size_confidence_score == d("1.000000")
    assert btc.reason_codes == ("sample_size_confident",)

    assert tuple(bucket.bucket_key for bucket in btc.edge_bucket_rows) == (
        "0.000000-0.050000",
        "0.050000-0.150000",
        "0.150000+",
    )
    assert btc.edge_bucket_rows[0].resolved_count == 1
    assert btc.edge_bucket_rows[0].brier_score == d("0.160000")
    assert btc.edge_bucket_rows[0].hit_rate == d("1.000000")
    assert btc.edge_bucket_rows[1].average_absolute_edge == d("0.100000")
    assert btc.edge_bucket_rows[2].brier_score == d("0.040000")

    eth = report.team_rows[1]
    assert eth.team_id == "crypto_eth"
    assert eth.prediction_count == 2
    assert eth.resolved_count == 1
    assert eth.unresolved_count == 1
    assert eth.observed_rate == d("0.000000")
    assert eth.average_forecast_probability == d("0.700000")
    assert eth.calibration_error == d("0.700000")
    assert eth.brier_score == d("0.490000")
    assert eth.hit_rate == d("0.000000")
    assert eth.average_absolute_edge == d("0.080000")
    assert eth.sample_size_confidence == "thin"
    assert eth.sample_size_confidence_score == d("0.333333")
    assert eth.reason_codes == ("thin_sample_size", "unresolved_predictions")
    assert tuple(bucket.bucket_key for bucket in eth.edge_bucket_rows) == (
        "0.050000-0.150000",
    )


def test_latest_outcome_per_prediction_is_used_idempotently() -> None:
    report = build_team_memory_performance_metrics_report(
        (
            prediction("btc-revised", forecast_probability=d("0.900000")),
            prediction(
                "btc-low-edge-hit",
                market_slug="bitcoin-above-110k",
                forecast_probability=d("0.600000"),
                implied_probability=d("0.580000"),
            ),
        ),
        (
            outcome(
                "btc-revised",
                outcome_id="outcome-btc-revised-old",
                actual_outcome="no",
                resolved_at=GENERATED_AT,
            ),
            outcome(
                "btc-revised",
                outcome_id="outcome-btc-revised-latest",
                actual_outcome="yes",
                resolved_at=GENERATED_AT + timedelta(days=1),
            ),
            outcome(
                "btc-low-edge-hit",
                market_slug="bitcoin-above-110k",
                actual_outcome="yes",
            ),
        ),
        config=config(developing_sample_size=1, confident_sample_size=2),
        generated_at=GENERATED_AT,
    )

    row = report.team_rows[0]
    assert row.resolved_count == 2
    assert row.hit_rate == d("1.000000")
    assert row.brier_score == d("0.085000")
    assert row.sample_size_confidence == "confident"


def test_empty_input_and_json_payload_are_deterministic_and_float_free() -> None:
    empty_report = build_team_memory_performance_metrics_report(
        (),
        (),
        config=config(),
        generated_at=GENERATED_AT,
    )

    assert empty_report.status == "candidate"
    assert empty_report.reason_codes == ("empty_predictions",)
    assert empty_report.team_rows == ()

    report = build_team_memory_performance_metrics_report(
        (
            prediction("btc-hit", forecast_probability=d("0.800000")),
            prediction("btc-unresolved", forecast_probability=d("0.400000")),
        ),
        (outcome("btc-hit", actual_outcome="yes"),),
        config=config(developing_sample_size=1, confident_sample_size=2),
        generated_at=GENERATED_AT,
    )

    payload = team_memory_performance_metrics_payload(report)

    assert payload["generated_at"] == "2026-07-03T12:00:00+00:00"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["team_rows"][0]["brier_score"] == "0.040000"
    assert payload["team_rows"][0]["edge_bucket_rows"][0]["bucket_key"] == "0.150000+"

    def walk(value: object) -> tuple[object, ...]:
        if isinstance(value, dict):
            return tuple(value.keys()) + tuple(item for child in value.values() for item in walk(child))
        if isinstance(value, list):
            return tuple(item for child in value for item in walk(child))
        return (value,)

    flattened = walk(payload)
    assert not any(isinstance(value, float) for value in flattened)
    assert not any(
        fragment in str(value).lower()
        for value in flattened
        for fragment in ("auth", "wallet", "order", "account", "broker")
    )


def test_dataclasses_validate_exact_types_flags_ranges_and_boundaries() -> None:
    with pytest.raises(ValueError, match="edge_bucket_bounds"):
        TeamMemoryPerformanceMetricsConfig(edge_bucket_bounds=(d("0.200000"), d("0.100000")))
    with pytest.raises(ValueError, match="developing_sample_size"):
        TeamMemoryPerformanceMetricsConfig(developing_sample_size=0)
    with pytest.raises(ValueError, match="confident_sample_size"):
        TeamMemoryPerformanceMetricsConfig(developing_sample_size=3, confident_sample_size=2)
    with pytest.raises(ValueError, match="paper_only"):
        TeamMemoryPerformanceMetricsConfig(paper_only=False)
    with pytest.raises(ValueError, match="forecast_probability"):
        prediction("bad-probability", forecast_probability=d("1.000001"))
    with pytest.raises(ValueError, match="implied_probability"):
        prediction("bad-implied", implied_probability=d("-0.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        prediction("bad-generated", generated_at=datetime(2026, 7, 3))
    with pytest.raises(ValueError, match="actual_outcome"):
        outcome("bad-outcome", actual_outcome="maybe")
    with pytest.raises(ValueError, match="resolved_at"):
        outcome("bad-resolved", resolved_at=datetime(2026, 7, 4))

    valid_prediction = prediction("btc-valid")
    valid_outcome = outcome("btc-valid")
    cfg = config()
    with pytest.raises(ValueError, match="predictions"):
        build_team_memory_performance_metrics_report(
            (item for item in (valid_prediction,)),
            (valid_outcome,),
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="TeamMemoryPaperPredictionRow"):
        build_team_memory_performance_metrics_report(
            (bypassed(valid_prediction, paper_only=False),),
            (valid_outcome,),
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="outcome team_id must match prediction team_id"):
        build_team_memory_performance_metrics_report(
            (valid_prediction,),
            (bypassed(valid_outcome, team_id="crypto_eth"),),
            config=cfg,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_team_memory_performance_metrics_report(
            (valid_prediction,),
            (valid_outcome,),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

    report = build_team_memory_performance_metrics_report(
        (valid_prediction,),
        (valid_outcome,),
        config=cfg,
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.team_rows[0].team_id = "crypto_eth"  # type: ignore[misc]


def test_module_stays_pure_and_unwired() -> None:
    import polymarket_alpha_lab.team_memory_performance_metrics as module

    source = getsource(module)

    assert "open(" not in source
    assert "Path(" not in source
    assert "sqlite" not in source
    assert "psycopg" not in source
    assert "requests" not in source
    assert "urllib" not in source
