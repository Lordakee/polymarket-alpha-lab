from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import import_module

import pytest


GENERATED_AT = datetime(2026, 6, 25, 20, 0, tzinfo=UTC)
BASE_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)
NEXT_STEP_BY_STATUS = {
    "pass": "allow_paper_project_screening_rank_stability_review",
    "watch": "throttle_paper_project_screening_rank_stability_review",
    "blocked": "block_paper_project_screening_rank_stability_review",
}


class DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab."
        "paper_project_screening_rank_stability_db_history_health_trend",
    )


def _health_api():
    return import_module(
        "polymarket_alpha_lab."
        "paper_project_screening_rank_stability_db_history_health",
    )


def _config(**overrides):
    values = {
        "config_version": (
            "paper-project-screening-rank-stability-db-history-health-trend-v0"
        ),
    }
    values.update(overrides)
    return _api().PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig(
        **values,
    )


def _reason_count(
    reason_code: str,
    report_count: int,
) -> object:
    return _health_api().PaperProjectScreeningRankStabilityDbHistoryHealthReasonCodeCount(
        reason_code,
        report_count,
    )


def _health_report(
    *,
    generated_at: datetime,
    health_status: str = "pass",
    rank_stability_report_count: int | None = None,
    stable_rank_stability_report_count: int | None = None,
    watch_rank_stability_report_count: int | None = None,
    blocked_rank_stability_report_count: int | None = None,
    latest_rank_stability_status: str | None = None,
    latest_candidate_count: int | None = 1,
    latest_stable_ready_count: int | None = 1,
    latest_unstable_ready_count: int | None = 0,
    latest_source_generated_at: datetime | None = None,
    latest_source_age_seconds: int | None = 300,
    max_source_age_seconds: int | None = 600,
    duplicate_latest_generated_at_count: int = 0,
    reason_codes: tuple[str, ...] | None = None,
) -> object:
    status_counts = {
        "pass": (3, 3, 0, 0),
        "watch": (3, 2, 1, 0),
        "blocked": (3, 2, 0, 1),
    }[health_status]
    rank_stability_report_count = (
        status_counts[0]
        if rank_stability_report_count is None
        else rank_stability_report_count
    )
    stable_rank_stability_report_count = (
        status_counts[1]
        if stable_rank_stability_report_count is None
        else stable_rank_stability_report_count
    )
    watch_rank_stability_report_count = (
        status_counts[2]
        if watch_rank_stability_report_count is None
        else watch_rank_stability_report_count
    )
    blocked_rank_stability_report_count = (
        status_counts[3]
        if blocked_rank_stability_report_count is None
        else blocked_rank_stability_report_count
    )
    if latest_rank_stability_status is None:
        latest_rank_stability_status = {
            "pass": "stable",
            "watch": "watch",
            "blocked": "blocked",
        }[health_status]
    if reason_codes is None:
        reason_codes = {
            "pass": ("paper_project_screening_rank_stability_db_history_health_passed",),
            "watch": ("latest_paper_project_screening_rank_stability_watch",),
            "blocked": ("latest_paper_project_screening_rank_stability_blocked",),
        }[health_status]
    if latest_source_generated_at is None:
        latest_source_generated_at = generated_at - timedelta(seconds=300)
    return _health_api().PaperProjectScreeningRankStabilityDbHistoryHealthReport(
        generated_at=generated_at,
        config_version=(
            "paper-project-screening-rank-stability-db-history-health-v0"
        ),
        health_status=health_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[health_status],
        rank_stability_report_count=rank_stability_report_count,
        stable_rank_stability_report_count=stable_rank_stability_report_count,
        watch_rank_stability_report_count=watch_rank_stability_report_count,
        blocked_rank_stability_report_count=blocked_rank_stability_report_count,
        latest_rank_stability_status=latest_rank_stability_status,
        latest_candidate_count=latest_candidate_count,
        latest_stable_ready_count=latest_stable_ready_count,
        latest_unstable_ready_count=latest_unstable_ready_count,
        latest_source_generated_at=latest_source_generated_at,
        latest_source_age_seconds=latest_source_age_seconds,
        max_source_age_seconds=max_source_age_seconds,
        duplicate_latest_generated_at_count=duplicate_latest_generated_at_count,
        reason_code_counts=(
            _reason_count("stable_ready_candidates_present", 1),
        ),
        reason_codes=reason_codes,
    )


def test_health_trend_config_defaults_are_safe_phase1_defaults() -> None:
    api = _api()

    config = api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig()

    assert config.config_version == (
        api.DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION
    )
    assert config.config_version == (
        "paper-project-screening-rank-stability-db-history-health-trend-v0"
    )
    assert config.paper_only is True
    assert config.report_only is True
    assert config.readonly is True


def test_health_trend_public_all_exports_constants_dataclasses_and_builder() -> None:
    api = _api()

    assert set(api.__all__) == {
        "DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_HISTORY_HEALTH_TREND_CONFIG_VERSION",
        "PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig",
        "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow",
        "PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary",
        "PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport",
        "build_paper_project_screening_rank_stability_db_history_health_trend_report",
    }


def test_health_trend_empty_input_yields_valid_empty_report() -> None:
    trend = _api().build_paper_project_screening_rank_stability_db_history_health_trend_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert trend.generated_at == GENERATED_AT
    assert trend.config_version == (
        "paper-project-screening-rank-stability-db-history-health-trend-v0"
    )
    assert trend.source_health_report_count == 0
    assert trend.first_generated_at is None
    assert trend.latest_generated_at is None
    assert trend.latest_health_status is None
    assert trend.health_status_counts == (("pass", 0), ("watch", 0), ("blocked", 0))
    assert trend.consecutive_latest_watch_count == 0
    assert trend.consecutive_latest_blocked_count == 0
    assert trend.duplicate_generated_at_count == 0
    assert trend.rank_stability_report_count_first is None
    assert trend.rank_stability_report_count_latest is None
    assert trend.rank_stability_report_count_delta is None
    assert trend.stable_rank_stability_report_count_first is None
    assert trend.stable_rank_stability_report_count_latest is None
    assert trend.stable_rank_stability_report_count_delta is None
    assert trend.watch_rank_stability_report_count_first is None
    assert trend.watch_rank_stability_report_count_latest is None
    assert trend.watch_rank_stability_report_count_delta is None
    assert trend.blocked_rank_stability_report_count_first is None
    assert trend.blocked_rank_stability_report_count_latest is None
    assert trend.blocked_rank_stability_report_count_delta is None
    assert trend.latest_candidate_count_first is None
    assert trend.latest_candidate_count_latest is None
    assert trend.latest_candidate_count_delta is None
    assert trend.latest_stable_ready_count_first is None
    assert trend.latest_stable_ready_count_latest is None
    assert trend.latest_stable_ready_count_delta is None
    assert trend.latest_unstable_ready_count_first is None
    assert trend.latest_unstable_ready_count_latest is None
    assert trend.latest_unstable_ready_count_delta is None
    assert trend.latest_source_generated_at_first is None
    assert trend.latest_source_generated_at_latest is None
    assert trend.latest_source_generated_at_delta_seconds is None
    assert trend.latest_source_age_seconds_first is None
    assert trend.latest_source_age_seconds_latest is None
    assert trend.latest_source_age_seconds_delta is None
    assert trend.max_source_age_seconds_first is None
    assert trend.max_source_age_seconds_latest is None
    assert trend.max_source_age_seconds_delta is None
    assert trend.duplicate_latest_generated_at_count_first is None
    assert trend.duplicate_latest_generated_at_count_latest is None
    assert trend.duplicate_latest_generated_at_count_delta is None
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
        rank_stability_report_count=3,
        stable_rank_stability_report_count=3,
        watch_rank_stability_report_count=0,
        blocked_rank_stability_report_count=0,
        latest_candidate_count=1,
        latest_stable_ready_count=1,
        latest_unstable_ready_count=0,
        latest_source_generated_at=BASE_AT - timedelta(minutes=10),
        latest_source_age_seconds=600,
        max_source_age_seconds=1_200,
        reason_codes=("paper_project_screening_rank_stability_db_history_health_passed",),
    )
    second_same_time = _health_report(
        generated_at=BASE_AT + timedelta(hours=1),
        health_status="blocked",
        rank_stability_report_count=4,
        stable_rank_stability_report_count=3,
        watch_rank_stability_report_count=0,
        blocked_rank_stability_report_count=1,
        latest_candidate_count=2,
        latest_stable_ready_count=1,
        latest_unstable_ready_count=1,
        latest_source_generated_at=BASE_AT + timedelta(minutes=45),
        latest_source_age_seconds=900,
        max_source_age_seconds=1_500,
        reason_codes=(
            "latest_paper_project_screening_rank_stability_blocked",
            "stale_paper_project_screening_rank_stability_source_history",
        ),
    )
    latest_same_time = _health_report(
        generated_at=BASE_AT + timedelta(hours=1),
        health_status="watch",
        rank_stability_report_count=5,
        stable_rank_stability_report_count=3,
        watch_rank_stability_report_count=1,
        blocked_rank_stability_report_count=1,
        latest_candidate_count=4,
        latest_stable_ready_count=2,
        latest_unstable_ready_count=2,
        latest_source_generated_at=BASE_AT + timedelta(minutes=50),
        latest_source_age_seconds=800,
        max_source_age_seconds=1_600,
        duplicate_latest_generated_at_count=1,
        reason_codes=(
            "latest_paper_project_screening_rank_stability_watch",
            "stale_paper_project_screening_rank_stability_source_history",
        ),
    )

    trend = _api().build_paper_project_screening_rank_stability_db_history_health_trend_report(
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
    assert trend.rank_stability_report_count_first == 3
    assert trend.rank_stability_report_count_latest == 5
    assert trend.rank_stability_report_count_delta == 2
    assert trend.stable_rank_stability_report_count_first == 3
    assert trend.stable_rank_stability_report_count_latest == 3
    assert trend.stable_rank_stability_report_count_delta == 0
    assert trend.watch_rank_stability_report_count_first == 0
    assert trend.watch_rank_stability_report_count_latest == 1
    assert trend.watch_rank_stability_report_count_delta == 1
    assert trend.blocked_rank_stability_report_count_first == 0
    assert trend.blocked_rank_stability_report_count_latest == 1
    assert trend.blocked_rank_stability_report_count_delta == 1
    assert trend.latest_candidate_count_first == 1
    assert trend.latest_candidate_count_latest == 4
    assert trend.latest_candidate_count_delta == 3
    assert trend.latest_stable_ready_count_first == 1
    assert trend.latest_stable_ready_count_latest == 2
    assert trend.latest_stable_ready_count_delta == 1
    assert trend.latest_unstable_ready_count_first == 0
    assert trend.latest_unstable_ready_count_latest == 2
    assert trend.latest_unstable_ready_count_delta == 2
    assert trend.latest_source_generated_at_first == BASE_AT - timedelta(minutes=10)
    assert trend.latest_source_generated_at_latest == BASE_AT + timedelta(minutes=50)
    assert trend.latest_source_generated_at_delta_seconds == 3_600
    assert trend.latest_source_age_seconds_first == 600
    assert trend.latest_source_age_seconds_latest == 800
    assert trend.latest_source_age_seconds_delta == 200
    assert trend.max_source_age_seconds_first == 1_200
    assert trend.max_source_age_seconds_latest == 1_600
    assert trend.max_source_age_seconds_delta == 400
    assert trend.duplicate_latest_generated_at_count_first == 0
    assert trend.duplicate_latest_generated_at_count_latest == 1
    assert trend.duplicate_latest_generated_at_count_delta == 1
    assert trend.latest_reason_code_counts == (
        ("latest_paper_project_screening_rank_stability_watch", 1),
        ("stale_paper_project_screening_rank_stability_source_history", 1),
    )
    assert trend.total_reason_code_counts == (
        ("stale_paper_project_screening_rank_stability_source_history", 2),
        ("latest_paper_project_screening_rank_stability_blocked", 1),
        ("latest_paper_project_screening_rank_stability_watch", 1),
        ("paper_project_screening_rank_stability_db_history_health_passed", 1),
    )
    assert trend.repeated_reason_code_counts == (
        ("stale_paper_project_screening_rank_stability_source_history", 2),
    )
    assert trend.reason_code_rows == (
        _api().PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow(
            "stale_paper_project_screening_rank_stability_source_history",
            2,
            1,
            2,
        ),
        _api().PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow(
            "latest_paper_project_screening_rank_stability_blocked",
            1,
            0,
            1,
        ),
        _api().PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow(
            "latest_paper_project_screening_rank_stability_watch",
            1,
            1,
            1,
        ),
        _api().PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow(
            "paper_project_screening_rank_stability_db_history_health_passed",
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
    trend = _api().build_paper_project_screening_rank_stability_db_history_health_trend_report(
        (
            _health_report(
                generated_at=BASE_AT,
                health_status="pass",
            ),
            _health_report(
                generated_at=BASE_AT + timedelta(hours=1),
                health_status="blocked",
            ),
            _health_report(
                generated_at=BASE_AT + timedelta(hours=2),
                health_status="blocked",
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
    reason_row = api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow(
        "stale_paper_project_screening_rank_stability_source_history",
        1,
        0,
        1,
    )
    summary = api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary(
        input_position=1,
        generated_at=BASE_AT,
        health_status="pass",
        rank_stability_report_count=3,
        stable_rank_stability_report_count=3,
        watch_rank_stability_report_count=0,
        blocked_rank_stability_report_count=0,
        latest_rank_stability_status="stable",
        latest_candidate_count=1,
        latest_stable_ready_count=1,
        latest_unstable_ready_count=0,
        latest_source_generated_at=BASE_AT - timedelta(minutes=5),
        latest_source_age_seconds=300,
        max_source_age_seconds=600,
        duplicate_latest_generated_at_count=0,
        reason_codes=("paper_project_screening_rank_stability_db_history_health_passed",),
    )
    report = api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
        (
            _health_report(
                generated_at=BASE_AT,
                reason_codes=(
                    "stale_paper_project_screening_rank_stability_source_history",
                ),
                health_status="watch",
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


def test_health_trend_public_dataclass_subclasses_are_rejected() -> None:
    api = _api()

    with pytest.raises(TypeError, match="TrendConfig .*subclassing"):
        class ConfigSubclass(api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendConfig):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="TrendReasonCodeRow .*subclassing"):
        class ReasonRowSubclass(
            api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendReasonCodeRow,
        ):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="TrendSnapshotSummary .*subclassing"):
        class SummarySubclass(
            api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary,
        ):
            def __post_init__(self) -> None:
                pass

    with pytest.raises(TypeError, match="TrendReport .*subclassing"):
        class ReportSubclass(api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendReport):
            def __post_init__(self) -> None:
                pass


def test_health_trend_rejects_wrong_types_naive_datetimes_and_corrupt_values() -> None:
    api = _api()
    source = _health_report(generated_at=BASE_AT)

    with pytest.raises(ValueError, match="health_reports"):
        api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="health_reports"):
        api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
            (source,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
            (source,),
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 25, 20, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
            (source,),
            config=_config(),
            generated_at=datetime(2026, 6, 25, 20, 0),
        )

    corrupted = object.__new__(
        _health_api().PaperProjectScreeningRankStabilityDbHistoryHealthReport,
    )
    for field_name, value in source.__dict__.items():
        object.__setattr__(corrupted, field_name, value)
    object.__setattr__(corrupted, "paper_only", False)
    with pytest.raises(ValueError, match="health report .*paper_only"):
        api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
            (corrupted,),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    trend = api.build_paper_project_screening_rank_stability_db_history_health_trend_report(
        (source,),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(ValueError, match="source_health_report_count"):
        replace(trend, source_health_report_count=2)
    with pytest.raises(ValueError, match="health_status_counts"):
        replace(trend, health_status_counts=(("watch", 0), ("pass", 1), ("blocked", 0)))
    with pytest.raises(ValueError, match="reason_code_rows"):
        replace(trend, reason_code_rows=(object(),))
    with pytest.raises(ValueError, match="latest_candidate_count_delta"):
        replace(trend, latest_candidate_count_delta=99)


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("stable_rank_stability_report_count_latest", 99),
        ("watch_rank_stability_report_count_delta", 99),
        ("blocked_rank_stability_report_count_delta", 99),
        ("latest_source_generated_at_delta_seconds", 99),
        ("latest_source_age_seconds_latest", 0),
        ("max_source_age_seconds_delta", 99),
        ("duplicate_latest_generated_at_count_delta", 99),
    ),
)
def test_health_trend_rejects_inconsistent_public_metric_pairs(
    field_name: str,
    value: object,
) -> None:
    trend = _api().build_paper_project_screening_rank_stability_db_history_health_trend_report(
        (_health_report(generated_at=BASE_AT),),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match=field_name.rsplit("_", 1)[0]):
        replace(trend, **{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("stable_rank_stability_report_count_latest", 1),
        ("watch_rank_stability_report_count_delta", 1),
        ("blocked_rank_stability_report_count_delta", 1),
        ("latest_source_age_seconds_latest", 1),
        ("max_source_age_seconds_delta", 1),
        ("duplicate_latest_generated_at_count_delta", 1),
    ),
)
def test_health_trend_empty_report_rejects_populated_public_metric_fields(
    field_name: str,
    value: object,
) -> None:
    trend = _api().build_paper_project_screening_rank_stability_db_history_health_trend_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match=field_name):
        replace(trend, **{field_name: value})


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("latest_stable_ready_count", 1),
        ("latest_unstable_ready_count", 1),
        ("latest_source_generated_at", BASE_AT),
        ("latest_source_age_seconds", 1),
        ("max_source_age_seconds", 1),
        ("duplicate_latest_generated_at_count", 1),
    ),
)
def test_health_trend_empty_snapshot_summary_rejects_populated_source_fields(
    field_name: str,
    value: object,
) -> None:
    api = _api()
    values = {
        "input_position": 1,
        "generated_at": BASE_AT,
        "health_status": "pass",
        "rank_stability_report_count": 0,
        "stable_rank_stability_report_count": 0,
        "watch_rank_stability_report_count": 0,
        "blocked_rank_stability_report_count": 0,
        "latest_rank_stability_status": None,
        "latest_candidate_count": None,
        "latest_stable_ready_count": None,
        "latest_unstable_ready_count": None,
        "latest_source_generated_at": None,
        "latest_source_age_seconds": None,
        "max_source_age_seconds": None,
        "duplicate_latest_generated_at_count": 0,
        "reason_codes": ("paper_project_screening_rank_stability_db_history_health_passed",),
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        api.PaperProjectScreeningRankStabilityDbHistoryHealthTrendSnapshotSummary(
            **values,
        )


def test_health_trend_normalizes_aware_datetimes_to_utc() -> None:
    offset = timezone(timedelta(hours=-4))
    report = _api().build_paper_project_screening_rank_stability_db_history_health_trend_report(
        (
            _health_report(
                generated_at=datetime(2026, 6, 25, 12, 0, tzinfo=offset),
                latest_source_generated_at=datetime(2026, 6, 25, 11, 50, tzinfo=offset),
                latest_source_age_seconds=600,
                max_source_age_seconds=600,
            ),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 25, 16, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.first_generated_at == datetime(2026, 6, 25, 16, 0, tzinfo=UTC)
    assert report.latest_source_generated_at_latest == datetime(
        2026,
        6,
        25,
        15,
        50,
        tzinfo=UTC,
    )
