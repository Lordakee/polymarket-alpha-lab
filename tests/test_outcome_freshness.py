from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.forecast_evidence import (
    PaperForecastEvidenceConfig,
    PaperForecastEvidenceObservation,
    build_paper_forecast_evidence_report,
)
from polymarket_alpha_lab.outcome_freshness import (
    OutcomeFreshnessConfig,
    OutcomeFreshnessReport,
    OutcomeFreshnessStatusRow,
    build_outcome_freshness_report,
)
from polymarket_alpha_lab.outcome_tracker import OutcomeTrackingReport


GENERATED_AT = datetime(2026, 6, 17, 18, 0, tzinfo=UTC)
RATIO_QUANTUM = Decimal("0.000001")
OUTCOME_FRESHNESS_STATUSES = (
    "empty_outcome_history",
    "latest_outcomes_fresh",
    "latest_outcomes_pending",
    "latest_outcomes_stale",
)


def _config(**overrides) -> OutcomeFreshnessConfig:
    values = {
        "config_version": "outcome-freshness-v0",
        "stale_after_seconds": 3600,
    }
    values.update(overrides)
    return OutcomeFreshnessConfig(**values)


def _observation(
    generated_at: datetime,
    suffix: str,
) -> PaperForecastEvidenceObservation:
    return PaperForecastEvidenceObservation(
        observed_at=generated_at,
        source_packet_id=f"pkt-{suffix}",
        condition_id=f"0x{suffix}",
        token_id=f"tok-{suffix}",
        market_slug=f"market-{suffix}",
        strategy_type="market_quality",
        risk_tags=("liquidity",),
        predicted_probability=Decimal("0.6000"),
        actual_outcome_value=Decimal("1"),
    )


def _tracking_report(
    *,
    generated_at: datetime = GENERATED_AT,
    total_markets_checked: int,
    resolved_count: int,
    pending_count: int,
    suffix: str,
    paper_only: bool = True,
    report_only: bool = True,
) -> OutcomeTrackingReport:
    observations = tuple(
        _observation(generated_at, f"{suffix}-{index}")
        for index in range(resolved_count)
    )
    forecast_evidence_report = (
        build_paper_forecast_evidence_report(
            observations,
            config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
            generated_at=generated_at,
        )
        if observations
        else None
    )
    return OutcomeTrackingReport(
        generated_at=generated_at,
        config_version="outcome-tracker-v1",
        total_markets_checked=total_markets_checked,
        resolved_count=resolved_count,
        pending_count=pending_count,
        observations=observations,
        forecast_evidence_report=forecast_evidence_report,
        paper_only=paper_only,
        report_only=report_only,
    )


def _status_rows(
    counts: dict[str, int],
    total: int,
) -> tuple[OutcomeFreshnessStatusRow, ...]:
    return tuple(
        OutcomeFreshnessStatusRow(
            status=status,
            outcome_report_count=counts.get(status, 0),
            outcome_report_ratio=(
                None
                if total == 0
                else (Decimal(counts.get(status, 0)) / Decimal(total)).quantize(
                    RATIO_QUANTUM,
                )
            ),
        )
        for status in OUTCOME_FRESHNESS_STATUSES
    )


def test_outcome_freshness_empty_report_uses_spec_api_and_hard_flags():
    report = build_outcome_freshness_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, OutcomeFreshnessReport)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "outcome-freshness-v0"
    assert report.outcome_report_count == 0
    assert report.first_report_generated_at is None
    assert report.latest_report_generated_at is None
    assert report.latest_total_markets_checked == 0
    assert report.latest_resolved_count == 0
    assert report.latest_pending_count == 0
    assert report.latest_resolved_ratio is None
    assert report.latest_pending_ratio is None
    assert report.latest_report_age_seconds is None
    assert report.consecutive_pending_count == 0
    assert report.status == "empty_outcome_history"
    assert report.status_rows == _status_rows({}, 0)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_outcome_freshness_preserves_append_order_and_computes_latest_ratios():
    first = datetime(2026, 6, 17, 16, 0, tzinfo=UTC)
    second = datetime(2026, 6, 17, 17, 0, tzinfo=UTC)
    older_appended_latest = datetime(2026, 6, 17, 15, 30, tzinfo=UTC)
    reports = (
        _tracking_report(
            generated_at=first,
            total_markets_checked=4,
            resolved_count=4,
            pending_count=0,
            suffix="first",
        ),
        _tracking_report(
            generated_at=second,
            total_markets_checked=3,
            resolved_count=2,
            pending_count=1,
            suffix="second",
        ),
        _tracking_report(
            generated_at=older_appended_latest,
            total_markets_checked=3,
            resolved_count=1,
            pending_count=2,
            suffix="latest-by-append",
        ),
    )

    report = build_outcome_freshness_report(
        reports,
        config=_config(stale_after_seconds=10_000),
        generated_at=GENERATED_AT,
    )

    assert report.outcome_report_count == 3
    assert report.first_report_generated_at == first
    assert report.latest_report_generated_at == older_appended_latest
    assert report.latest_total_markets_checked == 3
    assert report.latest_resolved_count == 1
    assert report.latest_pending_count == 2
    assert report.latest_resolved_ratio == Decimal("0.333333")
    assert report.latest_pending_ratio == Decimal("0.666667")
    assert report.latest_report_age_seconds == 9000
    assert report.consecutive_pending_count == 2
    assert report.status == "latest_outcomes_pending"
    assert report.status_rows == _status_rows(
        {
            "latest_outcomes_fresh": 1,
            "latest_outcomes_pending": 2,
        },
        3,
    )


def test_outcome_freshness_marks_stale_only_after_exact_threshold():
    latest = _tracking_report(
        generated_at=datetime(2026, 6, 17, 17, 0, tzinfo=UTC),
        total_markets_checked=2,
        resolved_count=2,
        pending_count=0,
        suffix="latest",
    )

    threshold_report = build_outcome_freshness_report(
        (latest,),
        config=_config(stale_after_seconds=3600),
        generated_at=GENERATED_AT,
    )
    stale_report = build_outcome_freshness_report(
        (latest,),
        config=_config(stale_after_seconds=3599),
        generated_at=GENERATED_AT,
    )

    assert threshold_report.latest_report_age_seconds == 3600
    assert threshold_report.status == "latest_outcomes_fresh"
    assert stale_report.latest_report_age_seconds == 3600
    assert stale_report.status == "latest_outcomes_stale"


def test_outcome_freshness_accepts_list_and_normalizes_datetimes_to_utc():
    generated_at = datetime(2026, 6, 17, 13, 0, tzinfo=timezone(timedelta(hours=-5)))
    report_generated_at = datetime(
        2026,
        6,
        17,
        10,
        0,
        tzinfo=timezone(timedelta(hours=-7)),
    )

    report = build_outcome_freshness_report(
        [
            _tracking_report(
                generated_at=report_generated_at,
                total_markets_checked=1,
                resolved_count=1,
                pending_count=0,
                suffix="timezone",
            ),
        ],
        config=_config(),
        generated_at=generated_at,
    )

    assert report.generated_at == datetime(2026, 6, 17, 18, 0, tzinfo=UTC)
    assert report.first_report_generated_at == datetime(2026, 6, 17, 17, 0, tzinfo=UTC)
    assert report.latest_report_generated_at == datetime(2026, 6, 17, 17, 0, tzinfo=UTC)
    assert report.latest_report_age_seconds == 3600


def test_outcome_freshness_rejects_negative_latest_age():
    future_latest = _tracking_report(
        generated_at=GENERATED_AT + timedelta(seconds=1),
        total_markets_checked=1,
        resolved_count=1,
        pending_count=0,
        suffix="future",
    )

    with pytest.raises(
        ValueError,
        match="latest_report_age_seconds must be nonnegative",
    ):
        build_outcome_freshness_report(
            (future_latest,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


@pytest.mark.parametrize(
    "invalid_reports",
    (
        "not reports",
        b"not reports",
        {"report": "not allowed"},
        (item for item in ()),
    ),
)
def test_outcome_freshness_rejects_non_list_tuple_inputs(invalid_reports):
    with pytest.raises(ValueError, match="reports must be a list or tuple"):
        build_outcome_freshness_report(
            invalid_reports,
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_outcome_freshness_rejects_invalid_builder_inputs_and_source_flags():
    with pytest.raises(ValueError, match="config must be an OutcomeFreshnessConfig"):
        build_outcome_freshness_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        build_outcome_freshness_report(
            (),
            config=_config(),
            generated_at="2026-06-17",
        )
    with pytest.raises(ValueError, match="OutcomeTrackingReport"):
        build_outcome_freshness_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    non_paper = _tracking_report(
        total_markets_checked=1,
        resolved_count=1,
        pending_count=0,
        suffix="non-paper",
    )
    object.__setattr__(non_paper, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        build_outcome_freshness_report(
            (non_paper,),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    non_report = _tracking_report(
        total_markets_checked=1,
        resolved_count=1,
        pending_count=0,
        suffix="non-report",
    )
    object.__setattr__(non_report, "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        build_outcome_freshness_report(
            (non_report,),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_outcome_freshness_dataclasses_are_frozen_and_validate_invariants():
    report = build_outcome_freshness_report(
        (
            _tracking_report(
                total_markets_checked=1,
                resolved_count=1,
                pending_count=0,
                suffix="valid",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.outcome_report_count = 2
    with pytest.raises(ValueError, match="stale_after_seconds"):
        _config(stale_after_seconds=-1)
    with pytest.raises(ValueError, match="stale_after_seconds"):
        _config(stale_after_seconds=True)
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version="")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="latest resolved and pending counts"):
        replace(report, latest_pending_count=1)
    with pytest.raises(ValueError, match="latest_report_age_seconds"):
        replace(report, latest_report_age_seconds=-1)
    with pytest.raises(ValueError, match="latest_resolved_ratio"):
        replace(report, latest_resolved_ratio=Decimal("1.0000001"))
    with pytest.raises(ValueError, match="outcome_report_ratio"):
        replace(
            report,
            status_rows=(
                OutcomeFreshnessStatusRow(
                    "empty_outcome_history",
                    0,
                    Decimal("0.0000001"),
                ),
                *report.status_rows[1:],
            ),
        )
    with pytest.raises(ValueError, match="status_rows must cover"):
        replace(report, status_rows=report.status_rows[:-1])
    with pytest.raises(ValueError, match="status must match"):
        replace(report, status="latest_outcomes_pending")
