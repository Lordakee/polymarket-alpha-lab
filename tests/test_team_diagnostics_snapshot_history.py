from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.team_diagnostics_snapshot import TeamDiagnosticsSnapshotReport
from polymarket_alpha_lab.team_diagnostics_snapshot_history import (
    TeamDiagnosticsSnapshotHistoryConfig,
    build_team_diagnostics_snapshot_history_report,
)


GENERATED_AT = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)


class _StringSubclass(str):
    pass


class _DateTimeSubclass(datetime):
    pass


def _config(**overrides) -> TeamDiagnosticsSnapshotHistoryConfig:
    values = {"config_version": "team-diagnostics-snapshot-history-v0"}
    values.update(overrides)
    return TeamDiagnosticsSnapshotHistoryConfig(**values)


def _snapshot(
    minute_offset: int,
    *,
    evidence_quality_status: str = "watch",
    evidence_quality_average_quality_score: Decimal = Decimal("0.5000"),
    memory_eligible_reference_count: int = 0,
    calibration_settled_count: int = 0,
    evidence_row_count: int = 4,
) -> TeamDiagnosticsSnapshotReport:
    pass_count = 0
    watch_count = 0
    blocked_count = 0
    if evidence_quality_status == "pass":
        pass_count = evidence_row_count
    elif evidence_quality_status == "blocked":
        blocked_count = evidence_row_count
    else:
        watch_count = evidence_row_count
    return TeamDiagnosticsSnapshotReport(
        generated_at=GENERATED_AT + timedelta(minutes=minute_offset),
        config_version="team-diagnostics-snapshot-v0",
        source_config_version="team-diagnostics-v0",
        filters=(),
        forecast_row_count=max(calibration_settled_count, 20),
        evidence_row_count=evidence_row_count,
        outcome_row_count=calibration_settled_count,
        memory_eligible_reference_count=memory_eligible_reference_count,
        calibration_status="validated",
        calibration_settled_count=calibration_settled_count,
        calibration_group_count=1,
        event_template_row_count=1,
        event_template_status="observed",
        source_reliability_row_count=1,
        source_reliability_missing_source_evidence_count=0,
        evidence_quality_status=evidence_quality_status,
        evidence_quality_pass_count=pass_count,
        evidence_quality_watch_count=watch_count,
        evidence_quality_blocked_count=blocked_count,
        evidence_quality_average_quality_score=evidence_quality_average_quality_score,
        reason_codes=(),
    )


def _history(snapshots):
    return build_team_diagnostics_snapshot_history_report(
        snapshots,
        config=_config(),
        generated_at=GENERATED_AT,
    )


def _unsafe_clone_with_flag(snapshot: TeamDiagnosticsSnapshotReport, flag_name: str):
    clone = object.__new__(type(snapshot))
    for field_name, field_value in snapshot.__dict__.items():
        object.__setattr__(clone, field_name, field_value)
    object.__setattr__(clone, flag_name, False)
    return clone


def test_snapshot_history_marks_insufficient_history_for_single_snapshot():
    report = _history([_snapshot(0, evidence_quality_status="pass")])

    assert report.snapshot_count == 1
    assert report.required_snapshot_count == 2
    assert report.status == "insufficient_history"
    assert report.reason_codes == ("insufficient_history",)
    assert report.duplicate_latest_generated_at is False


def test_snapshot_history_counts_statuses_and_preserves_latest_snapshot():
    earliest = _snapshot(0, evidence_quality_status="pass")
    middle = _snapshot(1, evidence_quality_status="watch")
    latest = _snapshot(2, evidence_quality_status="pass")
    blocked = _snapshot(1, evidence_quality_status="blocked")

    report = _history([middle, latest, earliest, blocked])

    assert report.status == "observed"
    assert report.latest_snapshot is latest
    assert report.latest_generated_at == latest.generated_at
    assert report.status_counts == (
        ("blocked", 1),
        ("pass", 2),
        ("watch", 1),
    )


def test_snapshot_history_computes_span_seconds_and_metric_deltas():
    earliest = _snapshot(
        0,
        evidence_quality_average_quality_score=Decimal("0.6250"),
        memory_eligible_reference_count=3,
        calibration_settled_count=7,
    )
    latest = _snapshot(
        3,
        evidence_quality_average_quality_score=Decimal("0.8125"),
        memory_eligible_reference_count=10,
        calibration_settled_count=18,
    )

    report = _history([latest, earliest])

    assert report.earliest_generated_at == earliest.generated_at
    assert report.latest_generated_at == latest.generated_at
    assert report.span_seconds == 180
    assert report.evidence_quality_average_delta == Decimal("0.1875")
    assert report.evidence_quality_delta == Decimal("0.1875")
    assert report.memory_eligible_delta == 7
    assert report.settled_calibration_delta == 11


def test_snapshot_history_detects_duplicate_latest_generated_at():
    earlier = _snapshot(0)
    first_latest = _snapshot(2, evidence_quality_status="pass")
    second_latest = _snapshot(2, evidence_quality_status="watch")

    report = _history([earlier, first_latest, second_latest])

    assert report.status == "duplicate_latest_generated_at"
    assert report.duplicate_latest_generated_at is True
    assert report.latest_generated_at == first_latest.generated_at
    assert report.reason_codes == ("duplicate_latest_generated_at",)


def test_snapshot_history_normalizes_report_generated_at_to_utc():
    latest = _snapshot(1)
    eastern_generated_at = datetime(
        2026,
        6,
        24,
        8,
        0,
        tzinfo=timezone(timedelta(hours=-4)),
    )

    report = build_team_diagnostics_snapshot_history_report(
        [_snapshot(0), latest],
        config=_config(),
        generated_at=eastern_generated_at,
    )

    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC


def test_snapshot_history_rejects_invalid_inputs_and_false_flags():
    snapshot = _snapshot(0)
    subclassed_config_type = type(
        "SubclassedHistoryConfig",
        (TeamDiagnosticsSnapshotHistoryConfig,),
        {},
    )

    with pytest.raises(ValueError, match="snapshots"):
        _history((item for item in (snapshot,)))
    with pytest.raises(ValueError, match="snapshots"):
        _history(tuple.__new__(type("SnapshotTuple", (tuple,), {}), (snapshot,)))
    with pytest.raises(ValueError, match="TeamDiagnosticsSnapshotReport"):
        _history([object()])
    with pytest.raises(ValueError, match="config"):
        build_team_diagnostics_snapshot_history_report(
            [snapshot],
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        build_team_diagnostics_snapshot_history_report(
            [snapshot],
            config=subclassed_config_type(
                config_version="team-diagnostics-snapshot-history-v0",
            ),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_team_diagnostics_snapshot_history_report(
            [snapshot],
            config=_config(),
            generated_at="2026-06-24",
        )
    with pytest.raises(ValueError, match="snapshots paper_only"):
        _history([_unsafe_clone_with_flag(snapshot, "paper_only")])
    with pytest.raises(ValueError, match="snapshots report_only"):
        _history([_unsafe_clone_with_flag(snapshot, "report_only")])
    with pytest.raises(ValueError, match="snapshots readonly"):
        _history([_unsafe_clone_with_flag(snapshot, "readonly")])


def test_snapshot_history_config_and_report_are_frozen_and_validate_scalars():
    config = _config()
    report = _history([_snapshot(0), _snapshot(1)])

    assert config.config_version == "team-diagnostics-snapshot-history-v0"
    assert config.min_snapshot_count == 2
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    with pytest.raises(FrozenInstanceError):
        config.min_snapshot_count = 3
    with pytest.raises(FrozenInstanceError):
        report.status = "other"
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=_StringSubclass("team-diagnostics-snapshot-history-v0"))
    with pytest.raises(ValueError, match="config_version"):
        _config(config_version=" team-diagnostics-snapshot-history-v0 ")
    with pytest.raises(ValueError, match="min_snapshot_count"):
        _config(min_snapshot_count=True)
    with pytest.raises(ValueError, match="generated_at"):
        build_team_diagnostics_snapshot_history_report(
            [_snapshot(0), _snapshot(1)],
            config=_config(),
            generated_at=_DateTimeSubclass(2026, 6, 24, 12, 0, tzinfo=UTC),
        )
