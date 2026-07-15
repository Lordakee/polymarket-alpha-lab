from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Context, Decimal, localcontext
import hashlib
import inspect
import json
from typing import Any

import pytest

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastEvidenceDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    team_forecast_evidence_to_db_row,
    team_forecast_outcome_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import TeamForecastEvidencePacket
from polymarket_alpha_lab.team_source_reliability import (
    TeamSourceReliabilityConfig,
    TeamSourceReliabilityReport,
    TeamSourceReliabilityRow,
    build_team_source_reliability_report,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
DATA_TIMESTAMP = datetime(2026, 7, 1, 11, 58, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _payload_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _row_values(row: object) -> dict[str, Any]:
    return {field.name: getattr(row, field.name) for field in fields(row)}


def _payload_copy(row: object) -> dict[str, Any]:
    return json.loads(json.dumps(getattr(row, "payload_json"), allow_nan=False))


def _bypassed_row(row: object, **overrides: Any):
    malformed = object.__new__(type(row))
    kwargs = _row_values(row)
    kwargs.update(overrides)
    for key, value in kwargs.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _evidence_row(
    *,
    evidence_id: str,
    forecast_id: str,
    source_id: str = "source-etf-flow-dashboard",
    team_id: str = "crypto_btc",
    market_slug: str = "bitcoin-above-120k",
    weight: Decimal = d("0.420000"),
    confidence: Decimal | None = None,
    generated_at: datetime = GENERATED_AT,
) -> TeamForecastEvidenceDbRow:
    packet = TeamForecastEvidencePacket(
        evidence_id=evidence_id,
        team_id=team_id,
        market_slug=market_slug,
        source_id=source_id,
        source_type="market_data",
        data_timestamp=DATA_TIMESTAMP,
        data_freshness_seconds=120,
        evidence_type="etf_flow",
        evidence_text="US spot ETF net flow improved over the last session.",
        weight=weight,
        reason_codes=("team_crypto_btc", "flow_support"),
    )
    row = team_forecast_evidence_to_db_row(
        packet,
        forecast_id=forecast_id,
        config_version="team-forecast-evidence-v0",
        generated_at=generated_at,
    )
    if confidence is None:
        return row

    payload_json = _payload_copy(row)
    payload_json["evidence"]["confidence"] = str(confidence.quantize(d("0.000001")))
    return _bypassed_row(
        row,
        payload_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )


def _outcome_row(
    *,
    outcome_id: str,
    forecast_id: str,
    directionally_correct: bool,
    profitable_after_cost: bool,
    resolution_dispute_flag: bool = False,
    brier_score: Decimal = d("0.144400"),
    team_id: str = "crypto_btc",
    market_slug: str = "bitcoin-above-120k",
    generated_at: datetime = GENERATED_AT,
) -> TeamForecastOutcomeDbRow:
    outcome = TeamForecastOutcome(
        outcome_id=outcome_id,
        forecast_id=forecast_id,
        team_id=team_id,
        market_slug=market_slug,
        actual_outcome="yes",
        resolved_at=generated_at,
        settlement_source="polymarket_public_resolution",
        forecast_error=d("0.380000"),
        brier_score=brier_score,
        paper_pnl=d("0.000000"),
        cost_adjusted_return=d("0.010000" if profitable_after_cost else "-0.010000"),
        directionally_correct=directionally_correct,
        profitable_after_cost=profitable_after_cost,
        resolution_dispute_flag=resolution_dispute_flag,
        reason_codes=("settled_yes",),
    )
    return team_forecast_outcome_to_db_row(
        outcome,
        config_version="team-forecast-outcome-v0",
        generated_at=generated_at,
    )


def test_build_team_source_reliability_report_groups_settled_sources() -> None:
    evidence_rows = (
        _evidence_row(
            evidence_id="evidence-btc-1",
            forecast_id="forecast-btc-1",
            weight=d("0.400000"),
            confidence=d("0.700000"),
            generated_at=GENERATED_AT - timedelta(minutes=10),
        ),
        _evidence_row(
            evidence_id="evidence-btc-2",
            forecast_id="forecast-btc-2",
            weight=d("0.800000"),
            confidence=d("0.900000"),
            generated_at=GENERATED_AT,
        ),
        _evidence_row(
            evidence_id="evidence-eth-1",
            forecast_id="forecast-eth-1",
            source_id="source-onchain-dashboard",
            team_id="crypto_eth",
            market_slug="ethereum-above-4k",
            weight=d("0.300000"),
        ),
        _evidence_row(
            evidence_id="evidence-btc-pending",
            forecast_id="forecast-btc-pending",
            weight=d("0.990000"),
        ),
    )
    outcome_rows = (
        _outcome_row(
            outcome_id="outcome-btc-1",
            forecast_id="forecast-btc-1",
            directionally_correct=True,
            profitable_after_cost=True,
            brier_score=d("0.100000"),
        ),
        _outcome_row(
            outcome_id="outcome-btc-2",
            forecast_id="forecast-btc-2",
            directionally_correct=False,
            profitable_after_cost=False,
            resolution_dispute_flag=True,
            brier_score=d("0.300000"),
        ),
        _outcome_row(
            outcome_id="outcome-eth-1",
            forecast_id="forecast-eth-1",
            directionally_correct=True,
            profitable_after_cost=True,
            brier_score=d("0.050000"),
            team_id="crypto_eth",
            market_slug="ethereum-above-4k",
        ),
    )

    report = build_team_source_reliability_report(
        evidence_rows,
        outcome_rows,
        config=TeamSourceReliabilityConfig(
            min_settled_evidence_count=2,
            max_dispute_rate=d("0.750000"),
            min_profitable_rate=d("0.400000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert type(report) is TeamSourceReliabilityReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "team-source-reliability-v0"
    assert report.evidence_count == 4
    assert report.outcome_count == 3
    assert report.settled_evidence_count == 3
    assert report.pending_evidence_count == 1
    assert report.missing_source_evidence_count == 0
    assert report.row_count == 2
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    btc, eth = report.rows
    assert type(btc) is TeamSourceReliabilityRow
    assert (btc.team_id, btc.source_id) == ("crypto_btc", "source-etf-flow-dashboard")
    assert btc.evidence_count == 2
    assert btc.settled_evidence_count == 2
    assert btc.directionally_correct_count == 1
    assert btc.profitable_after_cost_count == 1
    assert btc.dispute_count == 1
    assert btc.average_brier_score == d("0.200000")
    assert btc.hit_rate == d("0.500000")
    assert btc.profitable_rate == d("0.500000")
    assert btc.average_weight == d("0.600000")
    assert btc.average_confidence == d("0.800000")
    assert btc.latest_generated_at == GENERATED_AT
    assert btc.status == "source_reliability_validated"
    assert btc.paper_only is True
    assert btc.report_only is True
    assert btc.readonly is True

    assert (eth.team_id, eth.source_id) == ("crypto_eth", "source-onchain-dashboard")
    assert eth.evidence_count == 1
    assert eth.settled_evidence_count == 1
    assert eth.directionally_correct_count == 1
    assert eth.profitable_after_cost_count == 1
    assert eth.dispute_count == 0
    assert eth.average_brier_score == d("0.050000")
    assert eth.hit_rate == d("1.000000")
    assert eth.profitable_rate == d("1.000000")
    assert eth.average_weight == d("0.300000")
    assert eth.average_confidence is None
    assert eth.status == "source_reliability_candidate"


def test_source_reliability_scores_capture_phase_1_summary_fields() -> None:
    evidence_rows = (
        _evidence_row(
            evidence_id="evidence-primary-1",
            forecast_id="forecast-primary-1",
            source_id="source-primary-desk",
            generated_at=GENERATED_AT - timedelta(minutes=30),
        ),
        _evidence_row(
            evidence_id="evidence-primary-2",
            forecast_id="forecast-primary-2",
            source_id="source-primary-desk",
            generated_at=GENERATED_AT - timedelta(minutes=10),
        ),
        _evidence_row(
            evidence_id="evidence-primary-3",
            forecast_id="forecast-primary-3",
            source_id="source-primary-desk",
            generated_at=GENERATED_AT - timedelta(seconds=60),
        ),
        _evidence_row(
            evidence_id="evidence-secondary-1",
            forecast_id="forecast-secondary-1",
            source_id="source-secondary-desk",
            generated_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )
    outcome_rows = (
        _outcome_row(
            outcome_id="outcome-primary-1",
            forecast_id="forecast-primary-1",
            directionally_correct=True,
            profitable_after_cost=True,
            brier_score=d("0.040000"),
            generated_at=GENERATED_AT - timedelta(minutes=30),
        ),
        _outcome_row(
            outcome_id="outcome-primary-2",
            forecast_id="forecast-primary-2",
            directionally_correct=False,
            profitable_after_cost=False,
            brier_score=d("0.360000"),
            generated_at=GENERATED_AT - timedelta(minutes=10),
        ),
        _outcome_row(
            outcome_id="outcome-primary-3",
            forecast_id="forecast-primary-3",
            directionally_correct=False,
            profitable_after_cost=False,
            brier_score=d("0.250000"),
            generated_at=GENERATED_AT - timedelta(seconds=60),
        ),
        _outcome_row(
            outcome_id="outcome-secondary-1",
            forecast_id="forecast-secondary-1",
            directionally_correct=True,
            profitable_after_cost=True,
            brier_score=d("0.010000"),
            generated_at=GENERATED_AT - timedelta(seconds=120),
        ),
    )

    report = build_team_source_reliability_report(
        evidence_rows,
        outcome_rows,
        config=TeamSourceReliabilityConfig(
            min_settled_evidence_count=3,
            max_freshness_age_seconds=600,
            min_corroboration_count=2,
            failure_streak_watch_threshold=2,
        ),
        generated_at=GENERATED_AT,
    )

    primary, secondary = report.rows
    assert (primary.source_id, secondary.source_id) == (
        "source-primary-desk",
        "source-secondary-desk",
    )
    assert primary.freshness_age_seconds == 60
    assert primary.freshness_score == d("0.900000")
    assert primary.corroboration_count == 1
    assert primary.failure_streak == 2
    assert primary.reliability_score == d("0.589166")
    assert primary.reliability_grade == "C"
    assert secondary.freshness_age_seconds == 120
    assert secondary.corroboration_count == 1
    assert secondary.failure_streak == 0
    assert secondary.reliability_grade == "A"
    assert report.reliability_grade_counts == (("A", 1), ("C", 1))


def test_source_reliability_rejects_future_evidence_timestamp() -> None:
    evidence = _evidence_row(
        evidence_id="evidence-future",
        forecast_id="forecast-future",
        generated_at=GENERATED_AT + timedelta(microseconds=1),
    )

    with pytest.raises(ValueError, match="must not be later than generated_at"):
        build_team_source_reliability_report(
            (evidence,),
            (),
            config=TeamSourceReliabilityConfig(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("field_name", ("generated_at", "resolved_at"))
def test_source_reliability_rejects_future_outcome_timestamp(
    field_name: str,
) -> None:
    evidence = _evidence_row(
        evidence_id="evidence-future-outcome",
        forecast_id="forecast-future-outcome",
        generated_at=GENERATED_AT - timedelta(minutes=1),
    )
    outcome = _outcome_row(
        outcome_id="outcome-future",
        forecast_id="forecast-future-outcome",
        directionally_correct=True,
        profitable_after_cost=True,
    )
    future_outcome = _bypassed_row(
        outcome,
        **{field_name: GENERATED_AT + timedelta(microseconds=1)},
    )

    with pytest.raises(
        ValueError,
        match=rf"outcome {field_name} must not be later than generated_at",
    ):
        build_team_source_reliability_report(
            (evidence,),
            (future_outcome,),
            config=TeamSourceReliabilityConfig(min_settled_evidence_count=1),
            generated_at=GENERATED_AT,
        )


def test_derived_source_reliability_rows_revalidate_score_relationships() -> None:
    values = {
        "team_id": "crypto_btc",
        "source_id": "source-etf-flow-dashboard",
        "evidence_count": 1,
        "settled_evidence_count": 1,
        "directionally_correct_count": 1,
        "profitable_after_cost_count": 1,
        "dispute_count": 0,
        "average_brier_score": d("0.100000"),
        "hit_rate": d("1.000000"),
        "profitable_rate": d("1.000000"),
        "average_weight": d("0.420000"),
        "average_confidence": None,
        "latest_generated_at": GENERATED_AT,
        "status": "source_reliability_validated",
        "freshness_age_seconds": 60,
        "freshness_score": d("0.900000"),
        "freshness_horizon_seconds": 600,
        "corroboration_count": 1,
        "failure_streak": 0,
        "reliability_score": d("0.900000"),
        "reliability_grade": "A",
    }

    row = TeamSourceReliabilityRow(**values)
    assert row.freshness_horizon_seconds == 600

    with pytest.raises(ValueError, match="freshness_score must match"):
        TeamSourceReliabilityRow(**{**values, "freshness_score": d("0.800000")})
    with pytest.raises(ValueError, match="reliability_grade must match"):
        TeamSourceReliabilityRow(**{**values, "reliability_grade": "F"})


@pytest.mark.parametrize(
    ("field_name", "bad_value", "error_match"),
    (
        ("freshness_score", d("0.800000"), "freshness_score must match"),
        ("reliability_grade", "F", "reliability_grade must match"),
    ),
)
def test_report_revalidates_tampered_derived_source_rows(
    field_name: str,
    bad_value: object,
    error_match: str,
) -> None:
    evidence = _evidence_row(
        evidence_id="evidence-derived-row",
        forecast_id="forecast-derived-row",
        generated_at=GENERATED_AT - timedelta(seconds=60),
    )
    outcome = _outcome_row(
        outcome_id="outcome-derived-row",
        forecast_id="forecast-derived-row",
        directionally_correct=True,
        profitable_after_cost=True,
    )
    report = build_team_source_reliability_report(
        (evidence,),
        (outcome,),
        config=TeamSourceReliabilityConfig(min_settled_evidence_count=1),
        generated_at=GENERATED_AT,
    )
    object.__setattr__(report.rows[0], field_name, bad_value)

    with pytest.raises(ValueError, match=error_match):
        replace(report, reliability_grade_counts=(("F", 1),))


def test_source_reliability_uses_decimal_time_math_without_float_surfaces() -> None:
    import polymarket_alpha_lab.team_source_reliability as api

    source = inspect.getsource(api)

    assert ".total_seconds(" not in source
    assert "float(" not in source


def test_pending_reliability_score_ignores_ambient_decimal_context() -> None:
    evidence = _evidence_row(
        evidence_id="evidence-pending-context",
        forecast_id="forecast-pending-context",
        generated_at=GENERATED_AT - timedelta(seconds=60),
    )

    with localcontext(Context(prec=1)):
        report = build_team_source_reliability_report(
            (evidence,),
            (),
            config=TeamSourceReliabilityConfig(
                include_pending=True,
                max_freshness_age_seconds=600,
            ),
            generated_at=GENERATED_AT,
        )

    assert report.rows[0].freshness_score == d("0.900000")
    assert report.rows[0].reliability_score == d("0.450000")


def test_settled_reliability_score_ignores_ambient_decimal_context() -> None:
    evidence = _evidence_row(
        evidence_id="evidence-settled-context",
        forecast_id="forecast-settled-context",
        generated_at=GENERATED_AT - timedelta(seconds=60),
    )
    outcome = _outcome_row(
        outcome_id="outcome-settled-context",
        forecast_id="forecast-settled-context",
        directionally_correct=True,
        profitable_after_cost=True,
    )

    with localcontext(Context(prec=1)):
        report = build_team_source_reliability_report(
            (evidence,),
            (outcome,),
            config=TeamSourceReliabilityConfig(
                min_settled_evidence_count=1,
                max_freshness_age_seconds=600,
            ),
            generated_at=GENERATED_AT,
        )

    assert report.rows[0].freshness_score == d("0.900000")
    assert report.rows[0].reliability_score == d("0.843713")


def test_freshness_age_ignores_ambient_decimal_context() -> None:
    evidence = _evidence_row(
        evidence_id="evidence-age-context",
        forecast_id="forecast-age-context",
        generated_at=GENERATED_AT - timedelta(days=1, seconds=1),
    )

    with localcontext(Context(prec=1)):
        report = build_team_source_reliability_report(
            (evidence,),
            (),
            config=TeamSourceReliabilityConfig(
                include_pending=True,
                max_freshness_age_seconds=200_000,
            ),
            generated_at=GENERATED_AT,
        )

    assert report.rows[0].freshness_age_seconds == 86_401


def test_source_reliability_treats_naive_report_timestamp_as_utc() -> None:
    report = build_team_source_reliability_report(
        (),
        (),
        config=TeamSourceReliabilityConfig(),
        generated_at=datetime(2026, 7, 2, 12, 0),
    )

    assert report.generated_at == datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


def test_source_reliability_rejects_timezone_without_utc_offset() -> None:
    class MissingUtcOffsetTimezone(tzinfo):
        def utcoffset(self, value: datetime | None) -> timedelta | None:
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        build_team_source_reliability_report(
            (),
            (),
            config=TeamSourceReliabilityConfig(),
            generated_at=datetime(
                2026,
                7,
                2,
                12,
                0,
                tzinfo=MissingUtcOffsetTimezone(),
            ),
        )


def test_source_reliability_rejects_sensitive_source_ids_before_public_rows() -> None:
    evidence = _evidence_row(
        evidence_id="evidence-sensitive-source",
        forecast_id="forecast-sensitive-source",
    )
    payload_json = _payload_copy(evidence)
    payload_json["evidence"]["source_id"] = "wallet_private_source"
    sensitive_source = _bypassed_row(
        evidence,
        source_id="wallet_private_source",
        payload_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )
    outcome = _outcome_row(
        outcome_id="outcome-sensitive-source",
        forecast_id="forecast-sensitive-source",
        directionally_correct=True,
        profitable_after_cost=True,
    )

    with pytest.raises(ValueError, match="source_id"):
        build_team_source_reliability_report(
            (sensitive_source,),
            (outcome,),
            config=TeamSourceReliabilityConfig(),
            generated_at=GENERATED_AT,
        )


def test_source_reliability_report_exposes_no_raw_sensitive_output_fields() -> None:
    evidence = _evidence_row(
        evidence_id="evidence-btc-1",
        forecast_id="forecast-btc-1",
    )
    outcome = _outcome_row(
        outcome_id="outcome-btc-1",
        forecast_id="forecast-btc-1",
        directionally_correct=True,
        profitable_after_cost=True,
    )

    report = build_team_source_reliability_report(
        (evidence,),
        (outcome,),
        config=TeamSourceReliabilityConfig(),
        generated_at=GENERATED_AT,
    )

    report_field_names = {field.name for field in fields(report)}
    row_field_names = {field.name for field in fields(report.rows[0])}
    exposed_names = report_field_names | row_field_names

    assert {
        "payload_json",
        "payload_sha256",
        "evidence_text",
        "actual_outcome",
        "settlement_source",
        "paper_pnl",
        "cost_adjusted_return",
    }.isdisjoint(exposed_names)
    rendered = repr(report)
    assert "US spot ETF net flow improved over the last session." not in rendered
    assert "polymarket_public_resolution" not in rendered


def test_source_reliability_report_dataclasses_are_frozen() -> None:
    row = TeamSourceReliabilityRow(
        team_id="crypto_btc",
        source_id="source-etf-flow-dashboard",
        evidence_count=1,
        settled_evidence_count=1,
        directionally_correct_count=1,
        profitable_after_cost_count=1,
        dispute_count=0,
        average_brier_score=d("0.100000"),
        hit_rate=d("1.000000"),
        profitable_rate=d("1.000000"),
        average_weight=d("0.420000"),
        average_confidence=None,
        latest_generated_at=GENERATED_AT,
        status="source_reliability_validated",
        freshness_age_seconds=0,
        freshness_score=d("1.000000"),
        corroboration_count=1,
        failure_streak=0,
        reliability_score=d("0.960000"),
        reliability_grade="A",
    )

    with pytest.raises(FrozenInstanceError):
        row.reliability_grade = "A"  # type: ignore[misc]


def test_build_team_source_reliability_report_marks_watch_for_bad_disputes_or_profit() -> None:
    evidence_rows = (
        _evidence_row(evidence_id="evidence-btc-1", forecast_id="forecast-btc-1"),
        _evidence_row(evidence_id="evidence-btc-2", forecast_id="forecast-btc-2"),
    )
    outcome_rows = (
        _outcome_row(
            outcome_id="outcome-btc-1",
            forecast_id="forecast-btc-1",
            directionally_correct=True,
            profitable_after_cost=False,
            resolution_dispute_flag=True,
        ),
        _outcome_row(
            outcome_id="outcome-btc-2",
            forecast_id="forecast-btc-2",
            directionally_correct=True,
            profitable_after_cost=False,
        ),
    )

    report = build_team_source_reliability_report(
        list(evidence_rows),
        list(outcome_rows),
        config=TeamSourceReliabilityConfig(
            min_settled_evidence_count=1,
            max_dispute_rate=d("0.250000"),
            min_profitable_rate=d("0.500000"),
        ),
        generated_at=GENERATED_AT,
    )

    assert report.rows[0].status == "source_reliability_watch"
    assert report.rows[0].hit_rate == d("1.000000")
    assert report.rows[0].profitable_rate == d("0.000000")


def test_pending_evidence_is_reported_and_only_grouped_when_enabled() -> None:
    pending = _evidence_row(
        evidence_id="evidence-btc-pending",
        forecast_id="forecast-btc-pending",
    )

    excluded_report = build_team_source_reliability_report(
        (pending,),
        (),
        config=TeamSourceReliabilityConfig(),
        generated_at=GENERATED_AT,
    )

    assert excluded_report.evidence_count == 1
    assert excluded_report.settled_evidence_count == 0
    assert excluded_report.pending_evidence_count == 1
    assert excluded_report.rows == ()

    included_report = build_team_source_reliability_report(
        (pending,),
        (),
        config=TeamSourceReliabilityConfig(include_pending=True),
        generated_at=GENERATED_AT,
    )

    assert included_report.evidence_count == 1
    assert included_report.settled_evidence_count == 0
    assert included_report.pending_evidence_count == 1
    assert len(included_report.rows) == 1
    assert included_report.rows[0].evidence_count == 1
    assert included_report.rows[0].settled_evidence_count == 0
    assert included_report.rows[0].average_brier_score is None
    assert included_report.rows[0].hit_rate is None
    assert included_report.rows[0].profitable_rate is None
    assert included_report.rows[0].status == "source_reliability_candidate"


def test_missing_source_is_counted_or_grouped_as_unknown_source() -> None:
    evidence = _evidence_row(
        evidence_id="evidence-btc-1",
        forecast_id="forecast-btc-1",
    )
    payload_json = _payload_copy(evidence)
    del payload_json["evidence"]["source_id"]
    missing_source = _bypassed_row(
        evidence,
        source_id="",
        payload_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )
    outcome = _outcome_row(
        outcome_id="outcome-btc-1",
        forecast_id="forecast-btc-1",
        directionally_correct=True,
        profitable_after_cost=True,
    )

    counted_report = build_team_source_reliability_report(
        (missing_source,),
        (outcome,),
        config=TeamSourceReliabilityConfig(),
        generated_at=GENERATED_AT,
    )

    assert counted_report.evidence_count == 1
    assert counted_report.missing_source_evidence_count == 1
    assert counted_report.settled_evidence_count == 0
    assert counted_report.rows == ()

    grouped_report = build_team_source_reliability_report(
        (missing_source,),
        (outcome,),
        config=TeamSourceReliabilityConfig(allow_unknown_source=True),
        generated_at=GENERATED_AT,
    )

    assert grouped_report.missing_source_evidence_count == 0
    assert grouped_report.settled_evidence_count == 1
    assert len(grouped_report.rows) == 1
    assert grouped_report.rows[0].source_id == "unknown_source"
    assert grouped_report.rows[0].settled_evidence_count == 1


@pytest.mark.parametrize(
    "evidence_rows",
    [
        (_evidence_row(evidence_id="evidence-btc-1", forecast_id="forecast-btc-1") for _ in range(1)),
        {"evidence": _evidence_row(evidence_id="evidence-btc-1", forecast_id="forecast-btc-1")},
        "not-evidence-rows",
        (
            TeamForecastEvidencePacket(
                evidence_id="evidence-btc-1",
                team_id="crypto_btc",
                market_slug="bitcoin-above-120k",
                source_id="source-etf-flow-dashboard",
                source_type="market_data",
                data_timestamp=DATA_TIMESTAMP,
                data_freshness_seconds=120,
                evidence_type="etf_flow",
                evidence_text="US spot ETF net flow improved over the last session.",
                weight=d("0.420000"),
                reason_codes=("team_crypto_btc", "flow_support"),
            ),
        ),
    ],
)
def test_builder_rejects_non_list_tuple_or_non_exact_evidence_rows(
    evidence_rows: object,
) -> None:
    with pytest.raises(ValueError, match="evidence_rows"):
        build_team_source_reliability_report(
            evidence_rows,
            (),
            config=TeamSourceReliabilityConfig(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    "outcome_rows",
    [
        (_outcome_row(
            outcome_id="outcome-btc-1",
            forecast_id="forecast-btc-1",
            directionally_correct=True,
            profitable_after_cost=True,
        ) for _ in range(1)),
        {"outcome": "row"},
        "not-outcome-rows",
        (object(),),
    ],
)
def test_builder_rejects_non_list_tuple_or_non_exact_outcome_rows(
    outcome_rows: object,
) -> None:
    with pytest.raises(ValueError, match="outcome_rows"):
        build_team_source_reliability_report(
            (),
            outcome_rows,
            config=TeamSourceReliabilityConfig(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_builder_rejects_false_evidence_hard_flags(flag_name: str) -> None:
    evidence = _evidence_row(evidence_id="evidence-btc-1", forecast_id="forecast-btc-1")
    malformed = _bypassed_row(evidence, **{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        build_team_source_reliability_report(
            (malformed,),
            (),
            config=TeamSourceReliabilityConfig(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_builder_rejects_false_outcome_hard_flags(flag_name: str) -> None:
    outcome = _outcome_row(
        outcome_id="outcome-btc-1",
        forecast_id="forecast-btc-1",
        directionally_correct=True,
        profitable_after_cost=True,
    )
    malformed = _bypassed_row(outcome, **{flag_name: False})

    with pytest.raises(ValueError, match=flag_name):
        build_team_source_reliability_report(
            (),
            (malformed,),
            config=TeamSourceReliabilityConfig(),
            generated_at=GENERATED_AT,
        )


def test_report_dataclasses_reject_false_hard_flags() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        TeamSourceReliabilityConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        TeamSourceReliabilityRow(
            team_id="crypto_btc",
            source_id="source-etf-flow-dashboard",
            evidence_count=1,
            settled_evidence_count=1,
            directionally_correct_count=1,
            profitable_after_cost_count=1,
            dispute_count=0,
            average_brier_score=d("0.100000"),
            hit_rate=d("1.000000"),
            profitable_rate=d("1.000000"),
            average_weight=d("0.420000"),
            average_confidence=None,
            latest_generated_at=GENERATED_AT,
            status="source_reliability_validated",
            freshness_age_seconds=0,
            freshness_score=d("1.000000"),
            corroboration_count=1,
            failure_streak=0,
            reliability_score=d("0.960000"),
            reliability_grade="A",
            report_only=False,
        )

    with pytest.raises(ValueError, match="readonly"):
        TeamSourceReliabilityReport(
            generated_at=GENERATED_AT,
            config_version="team-source-reliability-v0",
            evidence_count=0,
            outcome_count=0,
            settled_evidence_count=0,
            pending_evidence_count=0,
            missing_source_evidence_count=0,
            row_count=0,
            rows=(),
            readonly=False,
        )


def test_source_reliability_row_preserves_legacy_constructor_defaults() -> None:
    row = TeamSourceReliabilityRow(
        team_id="crypto_btc",
        source_id="source-etf-flow-dashboard",
        evidence_count=1,
        settled_evidence_count=1,
        directionally_correct_count=1,
        profitable_after_cost_count=1,
        dispute_count=0,
        average_brier_score=d("0.100000"),
        hit_rate=d("1.000000"),
        profitable_rate=d("1.000000"),
        average_weight=d("0.420000"),
        average_confidence=None,
        latest_generated_at=GENERATED_AT,
        status="source_reliability_validated",
    )

    assert row.freshness_age_seconds == 0
    assert row.freshness_score == d("1.000000")
    assert row.corroboration_count == 0
    assert row.failure_streak == 0
    assert row.reliability_score == d("0.000000")
    assert row.reliability_grade == "F"
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
