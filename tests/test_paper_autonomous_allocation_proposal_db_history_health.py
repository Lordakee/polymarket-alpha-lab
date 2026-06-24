from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history import (
    PaperAutonomousAllocationProposalDbHistoryReasonCodeRow,
    PaperAutonomousAllocationProposalDbHistoryReport,
    PaperAutonomousAllocationProposalDbHistoryStatusRow,
)


GENERATED_AT = datetime(2026, 6, 24, 18, 0, tzinfo=UTC)
SOURCE_GENERATED_AT = datetime(2026, 6, 24, 17, 55, tzinfo=UTC)
LATEST_AT = datetime(2026, 6, 24, 17, 50, tzinfo=UTC)
PROPOSAL_STATUSES = ("pass", "watch", "blocked")


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health",
    )


def _config(**overrides):
    values = {
        "config_version": (
            "paper-autonomous-allocation-proposal-db-history-health-v0"
        ),
        "min_history_report_count": 3,
        "max_watch_history_report_count": 0,
        "max_blocked_history_report_count": 0,
        "max_duplicate_latest_report_generated_at_count": 0,
        "max_latest_age_seconds": 86_400,
    }
    values.update(overrides)
    return _api().PaperAutonomousAllocationProposalDbHistoryHealthConfig(**values)


def _source_reason(history_status: str) -> str:
    return {
        "pass": "paper_autonomous_allocation_proposal_db_history_passed",
        "watch": "watch_allocation_proposal_report_threshold_exceeded",
        "blocked": "blocked_allocation_proposal_report_threshold_exceeded",
    }[history_status]


def _history_report(
    *,
    generated_at: datetime = SOURCE_GENERATED_AT,
    history_status: str = "pass",
    report_count: int = 3,
    latest_report_generated_at: datetime | None = LATEST_AT,
    latest_proposal_status: str | None = "pass",
    latest_allocated_count: int | None = 1,
    latest_total_allocated_paper_notional: Decimal | None = d("25.000000"),
    reason_codes: tuple[str, ...] | None = None,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    if report_count == 0:
        return PaperAutonomousAllocationProposalDbHistoryReport(
            generated_at=generated_at,
            config_version="paper-autonomous-allocation-proposal-db-history-v0",
            history_status=history_status,
            report_count=0,
            first_report_generated_at=None,
            latest_report_generated_at=None,
            latest_proposal_status=None,
            latest_screening_gate_status=None,
            latest_queue_risk_status=None,
            latest_allocation_input_count=None,
            latest_allocation_row_count=None,
            latest_allocated_count=None,
            latest_total_allocated_paper_notional=None,
            proposal_status_rows=tuple(
                PaperAutonomousAllocationProposalDbHistoryStatusRow(status, 0)
                for status in PROPOSAL_STATUSES
            ),
            duplicate_generated_at_count=0,
            consecutive_latest_pass_count=0,
            consecutive_latest_watch_count=0,
            consecutive_latest_blocked_count=0,
            latest_reason_codes=(),
            reason_code_rows=(),
            reason_codes=reason_codes
            if reason_codes is not None
            else ("insufficient_paper_autonomous_allocation_proposal_history",),
        )

    if latest_report_generated_at is None:
        raise AssertionError("use _corrupt_history_report for missing latest timestamp")
    if latest_proposal_status is None:
        raise AssertionError("latest_proposal_status is required with reports")

    status_counts = {
        "pass": report_count,
        "watch": 0,
        "blocked": 0,
    }
    latest_counts = {
        "pass": report_count,
        "watch": 0,
        "blocked": 0,
    }
    if latest_proposal_status == "watch":
        status_counts = {"pass": report_count - 1, "watch": 1, "blocked": 0}
        latest_counts = {"pass": 0, "watch": 1, "blocked": 0}
    elif latest_proposal_status == "blocked":
        status_counts = {"pass": report_count - 1, "watch": 0, "blocked": 1}
        latest_counts = {"pass": 0, "watch": 0, "blocked": 1}

    normalized_reason_codes = (
        reason_codes if reason_codes is not None else (_source_reason(history_status),)
    )

    return PaperAutonomousAllocationProposalDbHistoryReport(
        generated_at=generated_at,
        config_version="paper-autonomous-allocation-proposal-db-history-v0",
        history_status=history_status,
        report_count=report_count,
        first_report_generated_at=latest_report_generated_at - timedelta(hours=2),
        latest_report_generated_at=latest_report_generated_at,
        latest_proposal_status=latest_proposal_status,
        latest_screening_gate_status="pass",
        latest_queue_risk_status="pass",
        latest_allocation_input_count=2,
        latest_allocation_row_count=2,
        latest_allocated_count=latest_allocated_count,
        latest_total_allocated_paper_notional=latest_total_allocated_paper_notional,
        proposal_status_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryStatusRow(
                status,
                status_counts[status],
            )
            for status in PROPOSAL_STATUSES
        ),
        duplicate_generated_at_count=0,
        consecutive_latest_pass_count=latest_counts["pass"],
        consecutive_latest_watch_count=latest_counts["watch"],
        consecutive_latest_blocked_count=latest_counts["blocked"],
        latest_reason_codes=(
            ("paper_autonomous_allocation_proposal_passed",)
            if latest_proposal_status == "pass"
            else (f"allocation_proposal_{latest_proposal_status}",)
        ),
        reason_code_rows=tuple(
            PaperAutonomousAllocationProposalDbHistoryReasonCodeRow(
                reason_code,
                1,
            )
            for reason_code in normalized_reason_codes
        ),
        reason_codes=normalized_reason_codes,
    )


def _health_report(
    history_reports: tuple[PaperAutonomousAllocationProposalDbHistoryReport, ...],
    **config_overrides,
):
    return _api().build_paper_autonomous_allocation_proposal_db_history_health_report(
        history_reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _corrupt_history_report(
    report: PaperAutonomousAllocationProposalDbHistoryReport,
    **overrides,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    corrupted = PaperAutonomousAllocationProposalDbHistoryReport.__new__(
        PaperAutonomousAllocationProposalDbHistoryReport,
    )
    values = dict(report.__dict__)
    values.update(overrides)
    for field_name, value in values.items():
        object.__setattr__(corrupted, field_name, value)
    return corrupted


def _history_subclass(
    report: PaperAutonomousAllocationProposalDbHistoryReport,
) -> PaperAutonomousAllocationProposalDbHistoryReport:
    class HistoryReportSubclass(PaperAutonomousAllocationProposalDbHistoryReport):
        pass

    subclass_report = HistoryReportSubclass.__new__(HistoryReportSubclass)
    for field_name, value in report.__dict__.items():
        object.__setattr__(subclass_report, field_name, value)
    return subclass_report


def test_health_config_defaults_are_safe_phase1_defaults() -> None:
    api = _api()
    config = api.PaperAutonomousAllocationProposalDbHistoryHealthConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_CONFIG_VERSION
    )
    assert config.min_history_report_count == 3
    assert config.max_watch_history_report_count == 0
    assert config.max_blocked_history_report_count == 0
    assert config.max_duplicate_latest_report_generated_at_count == 0
    assert config.max_latest_age_seconds == 86_400
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_blocks_empty_and_insufficient_source_history_samples() -> None:
    empty = _health_report(())
    insufficient = _health_report(
        (
            _history_report(latest_report_generated_at=LATEST_AT - timedelta(minutes=2)),
            _history_report(latest_report_generated_at=LATEST_AT - timedelta(minutes=1)),
        ),
    )

    assert empty.history_report_count == 0
    assert empty.health_status == "blocked"
    assert empty.recommended_next_step == (
        "block_paper_autonomous_allocation_proposal_history_review"
    )
    assert empty.latest_history_status is None
    assert empty.latest_proposal_status is None
    assert empty.latest_allocated_count is None
    assert empty.latest_total_allocated_paper_notional is None
    assert empty.max_source_age_seconds is None
    assert empty.latest_source_age_seconds is None
    assert empty.reason_code_counts == ()
    assert empty.reason_codes == (
        "insufficient_allocation_proposal_db_history_health_samples",
    )

    assert insufficient.history_report_count == 2
    assert insufficient.health_status == "blocked"
    assert insufficient.pass_report_count == 2
    assert insufficient.reason_codes == (
        "insufficient_allocation_proposal_db_history_health_samples",
    )


def test_health_config_rejects_zero_minimum_history_report_count() -> None:
    with pytest.raises(ValueError, match="min_history_report_count"):
        _config(min_history_report_count=0)


def test_health_passes_clean_recent_history_and_copies_latest_trends() -> None:
    report = _health_report(
        (
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=1_800),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=1_200),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=600),
                latest_allocated_count=5,
                latest_total_allocated_paper_notional=d("42.000000"),
            ),
        ),
    )

    assert report.health_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_allocation_proposal_history_review"
    )
    assert report.history_report_count == 3
    assert report.pass_report_count == 3
    assert report.watch_report_count == 0
    assert report.blocked_report_count == 0
    assert report.latest_history_status == "pass"
    assert report.latest_proposal_status == "pass"
    assert report.latest_allocated_count == 5
    assert report.latest_total_allocated_paper_notional == d("42.000000")
    assert type(report.latest_total_allocated_paper_notional) is Decimal
    assert report.max_source_age_seconds == 1_800
    assert report.latest_source_age_seconds == 600
    assert report.duplicate_latest_report_generated_at_count == 0
    assert report.reason_code_counts == (
        _api().PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
            "paper_autonomous_allocation_proposal_db_history_passed",
            3,
        ),
    )
    assert report.reason_codes == (
        "paper_autonomous_allocation_proposal_db_history_health_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_health_report_rejects_direct_empty_pass_construction() -> None:
    empty = _health_report(())
    api = _api()

    assert empty.health_status == "blocked"
    assert empty.recommended_next_step == (
        "block_paper_autonomous_allocation_proposal_history_review"
    )
    assert empty.reason_codes == (
        "insufficient_allocation_proposal_db_history_health_samples",
    )
    assert empty.reason_code_counts == ()

    with pytest.raises(ValueError, match="health_status"):
        replace(
            empty,
            health_status="pass",
            recommended_next_step=(
                "allow_paper_autonomous_allocation_proposal_history_review"
            ),
            reason_codes=(
                "paper_autonomous_allocation_proposal_db_history_health_passed",
            ),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            empty,
            reason_codes=("latest_allocation_proposal_db_history_blocked",),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            empty,
            reason_code_counts=(
                api.PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
                    "paper_autonomous_allocation_proposal_db_history_passed",
                    1,
                ),
            ),
        )
    with pytest.raises(ValueError, match="history_report_count"):
        replace(empty, pass_report_count=1)


def test_health_blocks_when_latest_source_history_is_blocked() -> None:
    report = _health_report(
        (
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=3)),
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=2)),
            _history_report(
                history_status="blocked",
                latest_report_generated_at=GENERATED_AT - timedelta(hours=1),
            ),
        ),
        max_blocked_history_report_count=2,
    )

    assert report.health_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_allocation_proposal_history_review"
    )
    assert report.latest_history_status == "blocked"
    assert report.reason_codes == (
        "latest_allocation_proposal_db_history_blocked",
    )


def test_health_watches_excess_recent_watch_history_count() -> None:
    report = _health_report(
        (
            _history_report(
                history_status="watch",
                latest_report_generated_at=GENERATED_AT - timedelta(hours=3),
            ),
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=2)),
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    assert report.health_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_allocation_proposal_history_review"
    )
    assert report.watch_report_count == 1
    assert report.latest_history_status == "pass"
    assert report.reason_codes == (
        "watch_allocation_proposal_db_history_count_threshold_exceeded",
    )


def test_health_blocks_excess_recent_blocked_history_count() -> None:
    report = _health_report(
        (
            _history_report(
                history_status="blocked",
                latest_report_generated_at=GENERATED_AT - timedelta(hours=3),
            ),
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=2)),
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    assert report.health_status == "blocked"
    assert report.blocked_report_count == 1
    assert report.latest_history_status == "pass"
    assert report.reason_codes == (
        "blocked_allocation_proposal_db_history_count_threshold_exceeded",
    )


def test_health_watches_stale_latest_source_history() -> None:
    report = _health_report(
        (
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_403),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_402),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_401),
            ),
        ),
    )

    assert report.health_status == "watch"
    assert report.latest_source_age_seconds == 86_401
    assert report.max_source_age_seconds == 86_403
    assert report.reason_codes == ("stale_allocation_proposal_db_history",)


def test_health_blocks_missing_latest_source_history_timestamp() -> None:
    source = _corrupt_history_report(
        _history_report(),
        latest_report_generated_at=None,
    )

    report = _health_report((source,), min_history_report_count=1)

    assert report.health_status == "blocked"
    assert report.latest_source_age_seconds is None
    assert report.max_source_age_seconds is None
    assert report.reason_codes == (
        "missing_latest_allocation_proposal_db_history_timestamp",
    )


def test_health_watches_duplicate_latest_source_history_timestamps() -> None:
    report = _health_report(
        (
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=900),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=900),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=600),
            ),
        ),
    )

    assert report.health_status == "watch"
    assert report.duplicate_latest_report_generated_at_count == 1
    assert report.reason_codes == (
        "duplicate_allocation_proposal_history_timestamp_threshold_exceeded",
    )


def test_health_reason_code_counts_are_source_presence_counts_and_deterministic() -> None:
    report = _health_report(
        (
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=1_800),
                reason_codes=("shared_source_reason", "zeta_source_reason"),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=1_200),
                reason_codes=("alpha_source_reason", "shared_source_reason"),
            ),
            _history_report(
                latest_report_generated_at=GENERATED_AT - timedelta(seconds=600),
                reason_codes=("alpha_source_reason", "shared_source_reason"),
            ),
        ),
    )

    assert report.reason_code_counts == (
        _api().PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
            "shared_source_reason",
            3,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
            "alpha_source_reason",
            2,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
            "zeta_source_reason",
            1,
        ),
    )


def test_health_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    api = _api()
    config = _config()
    reason_count = api.PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
        "paper_autonomous_allocation_proposal_db_history_passed",
        1,
    )
    report = _health_report(
        (
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=3)),
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=2)),
            _history_report(latest_report_generated_at=GENERATED_AT - timedelta(hours=1)),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.health_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="reason code count .*report_only"):
        replace(reason_count, report_only=False)
    with pytest.raises(ValueError, match="health report .*readonly"):
        replace(report, readonly=False)


def test_health_public_dataclass_subclasses_cannot_be_constructed() -> None:
    api = _api()

    with pytest.raises(TypeError, match="HealthConfig .*subclassing"):
        class ConfigSubclass(api.PaperAutonomousAllocationProposalDbHistoryHealthConfig):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReasonCodeCount .*subclassing"):
        class ReasonCodeCountSubclass(
            api.PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount,
        ):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="HealthReport .*subclassing"):
        class ReportSubclass(api.PaperAutonomousAllocationProposalDbHistoryHealthReport):
            def __post_init__(self) -> None:
                pass


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_history_report_count": True}, "min_history_report_count"),
        ({"max_watch_history_report_count": True}, "max_watch_history_report_count"),
        ({"max_blocked_history_report_count": -1}, "max_blocked_history_report_count"),
        (
            {"max_duplicate_latest_report_generated_at_count": -1},
            "max_duplicate_latest_report_generated_at_count",
        ),
        ({"max_latest_age_seconds": 1.5}, "max_latest_age_seconds"),
    ),
)
def test_health_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_health_rejects_wrong_types_subclasses_naive_datetimes_and_corruption() -> None:
    api = _api()
    source = _history_report()

    with pytest.raises(ValueError, match="history_reports"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="history_reports"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_report(
            (_history_subclass(source),),
            config=_config(min_history_report_count=1),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_report(
            (source,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_report(
            (source,),
            config=_config(min_history_report_count=1),
            generated_at=DatetimeSubclass(2026, 6, 24, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_report(
            (source,),
            config=_config(min_history_report_count=1),
            generated_at=datetime(2026, 6, 24, 18, 0),
        )

    report = _health_report((source,), min_history_report_count=1)
    with pytest.raises(ValueError, match="history_report_count"):
        replace(report, history_report_count=2)
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="latest_total_allocated_paper_notional"):
        replace(report, latest_total_allocated_paper_notional=25.0)
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report,
            reason_codes=(
                "paper_autonomous_allocation_proposal_db_history_health_passed",
                "stale_allocation_proposal_db_history",
            ),
        )


def test_health_normalizes_aware_datetimes_to_utc() -> None:
    offset = timezone(timedelta(hours=-4))
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_report(
        (
            _history_report(
                latest_report_generated_at=datetime(2026, 6, 24, 12, 0, tzinfo=offset),
            ),
            _history_report(
                latest_report_generated_at=datetime(2026, 6, 24, 12, 10, tzinfo=offset),
            ),
            _history_report(
                latest_report_generated_at=datetime(2026, 6, 24, 12, 30, tzinfo=offset),
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 24, 14, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.latest_source_age_seconds == 5_400
    assert report.max_source_age_seconds == 7_200
