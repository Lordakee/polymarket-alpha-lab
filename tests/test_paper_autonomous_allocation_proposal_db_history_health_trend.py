from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health import (
    PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount,
    PaperAutonomousAllocationProposalDbHistoryHealthReport,
)


GENERATED_AT = datetime(2026, 6, 24, 18, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_autonomous_allocation_proposal_history_review",
    "watch": "throttle_paper_autonomous_allocation_proposal_history_review",
    "blocked": "block_paper_autonomous_allocation_proposal_history_review",
}


class DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_trend",
    )


def _config(**overrides):
    values = {
        "config_version": (
            "paper-autonomous-allocation-proposal-db-history-health-trend-v0"
        ),
    }
    values.update(overrides)
    return _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig(**values)


def _reason_count(
    reason_code: str,
    report_count: int,
) -> PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount:
    return PaperAutonomousAllocationProposalDbHistoryHealthReasonCodeCount(
        reason_code,
        report_count,
    )


def _health_report(
    *,
    generated_at: datetime,
    health_status: str = "pass",
    history_report_count: int = 3,
    pass_report_count: int = 3,
    watch_report_count: int = 0,
    blocked_report_count: int = 0,
    latest_allocated_count: int | None = 1,
    latest_total_allocated_paper_notional: Decimal | None = d("10.000000"),
    latest_source_age_seconds: int | None = 300,
    max_source_age_seconds: int | None = 600,
    reason_codes: tuple[str, ...] | None = None,
) -> PaperAutonomousAllocationProposalDbHistoryHealthReport:
    if reason_codes is None:
        reason_codes = {
            "pass": ("paper_autonomous_allocation_proposal_db_history_health_passed",),
            "watch": ("stale_allocation_proposal_db_history",),
            "blocked": ("latest_allocation_proposal_db_history_blocked",),
        }[health_status]
    return PaperAutonomousAllocationProposalDbHistoryHealthReport(
        generated_at=generated_at,
        config_version="paper-autonomous-allocation-proposal-db-history-health-v0",
        health_status=health_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[health_status],
        history_report_count=history_report_count,
        pass_report_count=pass_report_count,
        watch_report_count=watch_report_count,
        blocked_report_count=blocked_report_count,
        latest_history_status=health_status,
        latest_proposal_status=health_status,
        latest_allocated_count=latest_allocated_count,
        latest_total_allocated_paper_notional=latest_total_allocated_paper_notional,
        max_source_age_seconds=max_source_age_seconds,
        latest_source_age_seconds=latest_source_age_seconds,
        duplicate_latest_report_generated_at_count=0,
        reason_code_counts=tuple(
            _reason_count(reason_code, 1) for reason_code in reason_codes
        ),
        reason_codes=reason_codes,
    )


def test_health_trend_config_defaults_are_safe_phase1_defaults() -> None:
    api = _api()
    config = api.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION
    )
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_trend_empty_input_yields_valid_empty_report() -> None:
    trend = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.generated_at == GENERATED_AT
    assert trend.config_version == (
        "paper-autonomous-allocation-proposal-db-history-health-trend-v0"
    )
    assert trend.source_health_report_count == 0
    assert trend.first_generated_at is None
    assert trend.latest_generated_at is None
    assert trend.latest_health_status is None
    assert trend.health_status_counts == (("pass", 0), ("watch", 0), ("blocked", 0))
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 0
    assert trend.duplicate_generated_at_count == 0
    assert trend.history_report_count_first is None
    assert trend.history_report_count_latest is None
    assert trend.history_report_count_delta is None
    assert trend.latest_allocated_count_first is None
    assert trend.latest_allocated_count_latest is None
    assert trend.latest_allocated_count_delta is None
    assert trend.latest_total_allocated_paper_notional_first is None
    assert trend.latest_total_allocated_paper_notional_latest is None
    assert trend.latest_total_allocated_paper_notional_delta is None
    assert trend.latest_reason_code_counts == ()
    assert trend.total_reason_code_counts == ()
    assert trend.repeated_reason_code_counts == ()
    assert trend.reason_code_rows == ()
    assert trend.source_summaries == ()
    assert trend.paper_only is True
    assert trend.report_only is True
    assert trend.readonly is True


def test_health_trend_sorts_chronologically_and_computes_counts_deltas_and_reasons() -> None:
    first = _health_report(
        generated_at=BASE_AT,
        health_status="pass",
        history_report_count=3,
        pass_report_count=3,
        watch_report_count=0,
        blocked_report_count=0,
        latest_allocated_count=1,
        latest_total_allocated_paper_notional=d("10.000000"),
        latest_source_age_seconds=100,
        max_source_age_seconds=200,
        reason_codes=("paper_autonomous_allocation_proposal_db_history_health_passed",),
    )
    second_same_time = _health_report(
        generated_at=BASE_AT + timedelta(hours=1),
        health_status="blocked",
        history_report_count=4,
        pass_report_count=3,
        watch_report_count=0,
        blocked_report_count=1,
        latest_allocated_count=2,
        latest_total_allocated_paper_notional=d("20.500000"),
        latest_source_age_seconds=200,
        max_source_age_seconds=400,
        reason_codes=(
            "latest_allocation_proposal_db_history_blocked",
            "stale_allocation_proposal_db_history",
        ),
    )
    latest_same_time = _health_report(
        generated_at=BASE_AT + timedelta(hours=1),
        health_status="watch",
        history_report_count=5,
        pass_report_count=3,
        watch_report_count=1,
        blocked_report_count=1,
        latest_allocated_count=4,
        latest_total_allocated_paper_notional=d("25.750000"),
        latest_source_age_seconds=250,
        max_source_age_seconds=450,
        reason_codes=(
            "latest_allocation_proposal_db_history_watch",
            "stale_allocation_proposal_db_history",
        ),
    )

    trend = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (second_same_time, first, latest_same_time),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.source_health_report_count == 3
    assert trend.first_generated_at == BASE_AT
    assert trend.latest_generated_at == BASE_AT + timedelta(hours=1)
    assert trend.latest_health_status == "watch"
    assert trend.health_status_counts == (("pass", 1), ("watch", 1), ("blocked", 1))
    assert trend.consecutive_latest_watch_count == 1
    assert trend.consecutive_latest_blocked_count == 0
    assert trend.duplicate_generated_at_count == 1
    assert trend.history_report_count_first == 3
    assert trend.history_report_count_latest == 5
    assert trend.history_report_count_delta == 2
    assert trend.pass_report_count_first == 3
    assert trend.pass_report_count_latest == 3
    assert trend.pass_report_count_delta == 0
    assert trend.watch_report_count_first == 0
    assert trend.watch_report_count_latest == 1
    assert trend.watch_report_count_delta == 1
    assert trend.blocked_report_count_first == 0
    assert trend.blocked_report_count_latest == 1
    assert trend.blocked_report_count_delta == 1
    assert trend.latest_allocated_count_first == 1
    assert trend.latest_allocated_count_latest == 4
    assert trend.latest_allocated_count_delta == 3
    assert trend.latest_total_allocated_paper_notional_first == d("10.000000")
    assert trend.latest_total_allocated_paper_notional_latest == d("25.750000")
    assert trend.latest_total_allocated_paper_notional_delta == d("15.750000")
    assert trend.latest_source_age_seconds_first == 100
    assert trend.latest_source_age_seconds_latest == 250
    assert trend.latest_source_age_seconds_delta == 150
    assert trend.max_source_age_seconds_first == 200
    assert trend.max_source_age_seconds_latest == 450
    assert trend.max_source_age_seconds_delta == 250
    assert trend.latest_reason_code_counts == (
        ("latest_allocation_proposal_db_history_watch", 1),
        ("stale_allocation_proposal_db_history", 1),
    )
    assert trend.total_reason_code_counts == (
        ("stale_allocation_proposal_db_history", 2),
        ("latest_allocation_proposal_db_history_blocked", 1),
        ("latest_allocation_proposal_db_history_watch", 1),
        ("paper_autonomous_allocation_proposal_db_history_health_passed", 1),
    )
    assert trend.repeated_reason_code_counts == (
        ("stale_allocation_proposal_db_history", 2),
    )
    assert trend.reason_code_rows == (
        _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
            "stale_allocation_proposal_db_history",
            2,
            1,
            2,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
            "latest_allocation_proposal_db_history_blocked",
            1,
            0,
            1,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
            "latest_allocation_proposal_db_history_watch",
            1,
            1,
            1,
        ),
        _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
            "paper_autonomous_allocation_proposal_db_history_health_passed",
            1,
            0,
            1,
        ),
    )
    assert tuple(summary.generated_at for summary in trend.source_summaries) == (
        BASE_AT,
        BASE_AT + timedelta(hours=1),
        BASE_AT + timedelta(hours=1),
    )
    assert tuple(summary.input_position for summary in trend.source_summaries) == (
        2,
        1,
        3,
    )
    assert trend.source_summaries[-1].health_status == "watch"


def test_health_trend_computes_latest_status_streaks() -> None:
    trend = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (
            _health_report(
                generated_at=BASE_AT,
                health_status="pass",
            ),
            _health_report(
                generated_at=BASE_AT + timedelta(hours=1),
                health_status="blocked",
                pass_report_count=2,
                blocked_report_count=1,
                history_report_count=3,
            ),
            _health_report(
                generated_at=BASE_AT + timedelta(hours=2),
                health_status="blocked",
                pass_report_count=2,
                blocked_report_count=2,
                history_report_count=4,
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.latest_health_status == "blocked"
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 2


def test_health_trend_dataclasses_are_frozen_and_validate_hard_flags() -> None:
    api = _api()
    config = _config()
    reason_row = api.PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow(
        "stale_allocation_proposal_db_history",
        1,
        0,
        1,
    )
    summary = api.PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary(
        input_position=1,
        generated_at=BASE_AT,
        health_status="pass",
        history_report_count=3,
        pass_report_count=3,
        watch_report_count=0,
        blocked_report_count=0,
        latest_allocated_count=1,
        latest_total_allocated_paper_notional=d("10.000000"),
        latest_source_age_seconds=100,
        max_source_age_seconds=200,
        reason_codes=("stale_allocation_proposal_db_history",),
    )
    report = api.build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (
            _health_report(
                generated_at=BASE_AT,
                reason_codes=("stale_allocation_proposal_db_history",),
                health_status="watch",
                pass_report_count=2,
                watch_report_count=1,
                history_report_count=3,
            ),
        ),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_row.total_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.health_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.latest_health_status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config .*paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="reason code row .*report_only"):
        replace(reason_row, report_only=False)
    with pytest.raises(ValueError, match="snapshot summary .*readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="trend report .*paper_only"):
        replace(report, paper_only=False)


def test_health_trend_public_dataclass_subclasses_cannot_be_constructed() -> None:
    api = _api()

    with pytest.raises(TypeError, match="TrendConfig .*subclassing"):
        class ConfigSubclass(api.PaperAutonomousAllocationProposalDbHistoryHealthTrendConfig):
            pass

    with pytest.raises(TypeError, match="TrendReasonCodeRow .*subclassing"):
        class ReasonCodeRowSubclass(
            api.PaperAutonomousAllocationProposalDbHistoryHealthTrendReasonCodeRow,
        ):
            pass

    with pytest.raises(TypeError, match="TrendSnapshotSummary .*subclassing"):
        class SnapshotSummarySubclass(
            api.PaperAutonomousAllocationProposalDbHistoryHealthTrendSnapshotSummary,
        ):
            pass

    with pytest.raises(TypeError, match="TrendReport .*subclassing"):
        class ReportSubclass(api.PaperAutonomousAllocationProposalDbHistoryHealthTrendReport):
            pass


def test_health_trend_rejects_wrong_types_subclasses_naive_datetimes_and_corruption() -> None:
    api = _api()
    source = _health_report(generated_at=BASE_AT)

    with pytest.raises(ValueError, match="health_reports"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            (source,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            (source,),
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 24, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
            (source,),
            config=_config(),
            generated_at=datetime(2026, 6, 24, 18, 0),
        )

    report = api.build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (
            source,
            _health_report(
                generated_at=BASE_AT + timedelta(hours=1),
                health_status="watch",
                pass_report_count=2,
                watch_report_count=1,
                history_report_count=3,
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="latest_total_allocated_paper_notional_delta"):
        replace(report, latest_total_allocated_paper_notional_delta=25.0)
    with pytest.raises(ValueError, match="health_status_counts"):
        replace(
            report,
            health_status_counts=(("watch", 0), ("pass", 1), ("blocked", 0)),
        )
    with pytest.raises(ValueError, match="reason_code_rows"):
        replace(report, reason_code_rows=(object(),))
    with pytest.raises(ValueError, match="source_summaries"):
        replace(report, source_summaries=tuple(reversed(report.source_summaries)))


def test_health_trend_rejects_reason_code_row_snapshot_count_mismatch() -> None:
    report = _api().build_paper_autonomous_allocation_proposal_db_history_health_trend_report(
        (
            _health_report(
                generated_at=BASE_AT,
                health_status="watch",
                history_report_count=3,
                pass_report_count=2,
                watch_report_count=1,
                blocked_report_count=0,
                reason_codes=("stale_allocation_proposal_db_history",),
            ),
            _health_report(
                generated_at=BASE_AT + timedelta(hours=1),
                health_status="watch",
                history_report_count=4,
                pass_report_count=2,
                watch_report_count=2,
                blocked_report_count=0,
                reason_codes=("stale_allocation_proposal_db_history",),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    bad_row = replace(report.reason_code_rows[0], snapshot_count=1)

    with pytest.raises(ValueError, match="reason_code_rows must align with reason code counts"):
        _api().PaperAutonomousAllocationProposalDbHistoryHealthTrendReport(
            generated_at=report.generated_at,
            config_version=report.config_version,
            source_health_report_count=report.source_health_report_count,
            first_generated_at=report.first_generated_at,
            latest_generated_at=report.latest_generated_at,
            latest_health_status=report.latest_health_status,
            health_status_counts=report.health_status_counts,
            consecutive_latest_watch_count=report.consecutive_latest_watch_count,
            consecutive_latest_blocked_count=report.consecutive_latest_blocked_count,
            duplicate_generated_at_count=report.duplicate_generated_at_count,
            history_report_count_first=report.history_report_count_first,
            history_report_count_latest=report.history_report_count_latest,
            history_report_count_delta=report.history_report_count_delta,
            pass_report_count_first=report.pass_report_count_first,
            pass_report_count_latest=report.pass_report_count_latest,
            pass_report_count_delta=report.pass_report_count_delta,
            watch_report_count_first=report.watch_report_count_first,
            watch_report_count_latest=report.watch_report_count_latest,
            watch_report_count_delta=report.watch_report_count_delta,
            blocked_report_count_first=report.blocked_report_count_first,
            blocked_report_count_latest=report.blocked_report_count_latest,
            blocked_report_count_delta=report.blocked_report_count_delta,
            latest_allocated_count_first=report.latest_allocated_count_first,
            latest_allocated_count_latest=report.latest_allocated_count_latest,
            latest_allocated_count_delta=report.latest_allocated_count_delta,
            latest_total_allocated_paper_notional_first=(
                report.latest_total_allocated_paper_notional_first
            ),
            latest_total_allocated_paper_notional_latest=(
                report.latest_total_allocated_paper_notional_latest
            ),
            latest_total_allocated_paper_notional_delta=(
                report.latest_total_allocated_paper_notional_delta
            ),
            latest_source_age_seconds_first=report.latest_source_age_seconds_first,
            latest_source_age_seconds_latest=report.latest_source_age_seconds_latest,
            latest_source_age_seconds_delta=report.latest_source_age_seconds_delta,
            max_source_age_seconds_first=report.max_source_age_seconds_first,
            max_source_age_seconds_latest=report.max_source_age_seconds_latest,
            max_source_age_seconds_delta=report.max_source_age_seconds_delta,
            latest_reason_code_counts=report.latest_reason_code_counts,
            total_reason_code_counts=report.total_reason_code_counts,
            repeated_reason_code_counts=report.repeated_reason_code_counts,
            reason_code_rows=(bad_row,),
            source_summaries=report.source_summaries,
        )
