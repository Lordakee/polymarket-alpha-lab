from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    PaperProbabilitySelectionSummaryHistoryReport,
)


BASE_AT = datetime(2026, 6, 25, 10, 0, tzinfo=UTC)
GENERATED_AT = datetime(2026, 6, 25, 10, 15, tzinfo=UTC)


class DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_trend",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides):
    values = {
        "min_history_count": 3,
        "stale_age_seconds": 1_800,
        "min_average_selected_share": d("0.250000"),
    }
    values.update(overrides)
    return _api().PaperProbabilitySelectionSummaryHistoryTrendConfig(**values)


def _history_report(
    *,
    generated_at: datetime,
    source_report_count: int = 3,
    latest_age_seconds: int = 60,
    latest_queue_count: int = 4,
    latest_selected_count: int = 3,
    latest_pending_count: int = 0,
    latest_rejected_count: int = 0,
    reason_codes: tuple[str, ...] = ("selection_summary_history_stable",),
) -> PaperProbabilitySelectionSummaryHistoryReport:
    latest_generated_at = generated_at - timedelta(seconds=latest_age_seconds)
    first_generated_at = latest_generated_at - timedelta(minutes=10)
    latest_skipped_count = 0
    aggregate_queue_count = source_report_count * latest_queue_count
    aggregate_selected_count = source_report_count * latest_selected_count
    aggregate_pending_count = source_report_count * latest_pending_count
    aggregate_rejected_count = (
        aggregate_queue_count - aggregate_selected_count - aggregate_pending_count
    )
    if latest_selected_count + latest_pending_count + latest_rejected_count > latest_queue_count:
        raise AssertionError("test fixture latest counts exceed queue count")
    latest_rejected_count = (
        latest_queue_count - latest_selected_count - latest_pending_count
    )
    reason_count_values = {"cost_stress_passed": max(aggregate_queue_count, 1)}
    for reason_code in reason_codes:
        if reason_code != "selection_summary_history_stable":
            reason_count_values[reason_code] = reason_count_values.get(reason_code, 0) + 1

    return PaperProbabilitySelectionSummaryHistoryReport(
        generated_at=generated_at,
        config_version="paper-probability-selection-summary-history-v0",
        source_report_count=source_report_count,
        first_generated_at=first_generated_at,
        latest_generated_at=latest_generated_at,
        history_span_seconds=600,
        latest_age_seconds=latest_age_seconds,
        latest_queue_count=latest_queue_count,
        latest_selected_count=latest_selected_count,
        latest_pending_count=latest_pending_count,
        latest_rejected_count=latest_rejected_count,
        latest_skipped_count=latest_skipped_count,
        aggregate_queue_count=aggregate_queue_count,
        aggregate_selected_count=aggregate_selected_count,
        aggregate_pending_count=aggregate_pending_count,
        aggregate_rejected_count=aggregate_rejected_count,
        aggregate_skipped_count=0,
        latest_selected_share=_ratio(latest_selected_count, latest_queue_count),
        average_selected_share=_ratio(aggregate_selected_count, aggregate_queue_count),
        distinct_config_versions=("paper-probability-selection-summary-v0",),
        reason_code_counts=tuple(sorted(reason_count_values.items())),
        history_status=_history_status(reason_codes),
        recommended_next_step=_history_next_step(reason_codes),
        reason_codes=reason_codes,
    )


def _ratio(numerator: int, denominator: int) -> Decimal:
    return (Decimal(numerator) / Decimal(denominator)).quantize(d("0.000001"))


def _history_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("selection_summary_history_stable",):
        return "ready"
    blocked_reasons = {
        "no_selection_summary_history",
        "insufficient_selection_summary_history",
        "latest_selection_summary_stale",
        "latest_selected_share_below_minimum",
        "average_selected_share_below_minimum",
    }
    if any(reason_code in blocked_reasons for reason_code in reason_codes):
        return "blocked"
    return "watch"


def _history_next_step(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("selection_summary_history_stable",):
        return "proceed_to_paper_allocation"
    if (
        "no_selection_summary_history" in reason_codes
        or "insufficient_selection_summary_history" in reason_codes
    ):
        return "collect_more_history"
    if "latest_selection_summary_stale" in reason_codes:
        return "refresh_selection_summary"
    return "review_probability_selection"


def _trend(
    reports: tuple[PaperProbabilitySelectionSummaryHistoryReport, ...],
    *,
    config=None,
    generated_at: datetime = GENERATED_AT,
):
    return _api().build_paper_probability_selection_summary_history_trend_report(
        reports,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def _valid_trend_report():
    return _trend(
        (
            _history_report(generated_at=BASE_AT, latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=5), latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=10), latest_selected_count=3),
        ),
    )


def _direct_report_from(report, **overrides):
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values.update(overrides)
    return _api().PaperProbabilitySelectionSummaryHistoryTrendReport(**values)


def test_history_trend_stable_history_continues_monitoring() -> None:
    report = _trend(
        (
            _history_report(generated_at=BASE_AT, latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=5), latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=10), latest_selected_count=3),
        ),
    )

    assert type(report) is _api().PaperProbabilitySelectionSummaryHistoryTrendReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "paper-probability-selection-summary-history-trend-v0"
    )
    assert report.source_history_count == 3
    assert report.first_generated_at == BASE_AT
    assert report.latest_generated_at == BASE_AT + timedelta(minutes=10)
    assert report.history_span_seconds == 600
    assert report.latest_history_status == "ready"
    assert report.latest_status_streak == 3
    assert report.latest_selected_share == d("0.750000")
    assert report.average_selected_share == d("0.750000")
    assert report.selected_share_delta == d("0.000000")
    assert report.stale_history_count == 0
    assert report.thin_history_count == 0
    assert report.recurring_reason_code_counts == ()
    assert report.trend_status == "stable"
    assert report.recommended_next_step == "continue_monitoring"
    assert report.reason_codes == ("history_trend_stable",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_trend_summarizes_watch_streak_share_delta_and_recurring_reasons() -> None:
    shared_reasons = ("latest_selection_has_watch_rows", "shared_watch_reason")

    report = _trend(
        (
            _history_report(generated_at=BASE_AT, latest_selected_count=2),
            _history_report(
                generated_at=BASE_AT + timedelta(minutes=5),
                latest_selected_count=2,
                latest_pending_count=1,
                reason_codes=shared_reasons,
            ),
            _history_report(
                generated_at=BASE_AT + timedelta(minutes=10),
                latest_selected_count=3,
                latest_pending_count=1,
                reason_codes=shared_reasons,
            ),
        ),
    )

    assert report.source_history_count == 3
    assert report.latest_history_status == "watch"
    assert report.latest_status_streak == 2
    assert report.latest_selected_share == d("0.750000")
    assert report.average_selected_share == d("0.583333")
    assert report.selected_share_delta == d("0.250000")
    assert report.recurring_reason_code_counts == (
        ("latest_selection_has_watch_rows", 2),
        ("shared_watch_reason", 2),
    )
    assert report.trend_status == "watch"
    assert report.recommended_next_step == "continue_monitoring"
    assert report.reason_codes == (
        "latest_history_watch",
        "recurring_history_reason_codes",
    )


def test_history_trend_rejects_empty_input_and_collects_more_when_insufficient() -> None:
    with pytest.raises(ValueError, match="nonempty"):
        _trend(())

    report = _trend(
        (
            _history_report(generated_at=BASE_AT, latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=5), latest_selected_count=3),
        ),
    )

    assert report.source_history_count == 2
    assert report.trend_status == "insufficient_history"
    assert report.recommended_next_step == "collect_more_history"
    assert report.reason_codes == ("insufficient_history_count",)


def test_history_trend_marks_stale_and_counts_thin_source_history() -> None:
    config = _config(stale_age_seconds=120)

    report = _trend(
        (
            _history_report(
                generated_at=BASE_AT,
                source_report_count=2,
                latest_selected_count=3,
            ),
            _history_report(
                generated_at=BASE_AT + timedelta(minutes=5),
                source_report_count=3,
                latest_selected_count=3,
            ),
            _history_report(
                generated_at=BASE_AT + timedelta(minutes=10),
                source_report_count=2,
                latest_selected_count=3,
            ),
        ),
        config=config,
    )

    assert report.stale_history_count == 3
    assert report.thin_history_count == 2
    assert report.trend_status == "stale"
    assert report.recommended_next_step == "refresh_source_history"
    assert report.reason_codes == (
        "latest_history_stale",
        "thin_history_reports_present",
    )


def test_history_trend_watches_when_only_older_history_is_stale() -> None:
    report = _trend(
        (
            _history_report(generated_at=GENERATED_AT - timedelta(seconds=90), latest_selected_count=3),
            _history_report(generated_at=GENERATED_AT - timedelta(seconds=30), latest_selected_count=3),
            _history_report(generated_at=GENERATED_AT - timedelta(seconds=30), latest_selected_count=3),
        ),
        config=_config(stale_age_seconds=60),
    )

    assert report.stale_history_count == 1
    assert report.trend_status == "watch"
    assert report.recommended_next_step == "continue_monitoring"
    assert report.reason_codes == ("stale_history_reports_present",)


def test_history_trend_marks_deteriorating_for_declining_or_low_average_share() -> None:
    report = _trend(
        (
            _history_report(generated_at=BASE_AT, latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=5), latest_selected_count=2),
            _history_report(generated_at=BASE_AT + timedelta(minutes=10), latest_selected_count=1),
        ),
        config=_config(min_average_selected_share=d("0.600000")),
    )

    assert report.latest_selected_share == d("0.250000")
    assert report.average_selected_share == d("0.500000")
    assert report.selected_share_delta == d("-0.500000")
    assert report.trend_status == "deteriorating"
    assert report.recommended_next_step == "review_probability_selection"
    assert report.reason_codes == (
        "selected_share_deteriorated",
        "average_selected_share_below_minimum",
    )


def test_history_trend_rejects_non_chronological_reports() -> None:
    with pytest.raises(ValueError, match="chronological"):
        _trend(
            (
                _history_report(generated_at=BASE_AT + timedelta(minutes=5)),
                _history_report(generated_at=BASE_AT),
            ),
        )


def test_history_trend_uses_decimal_only_for_shares_and_thresholds() -> None:
    report = _trend(
        (
            _history_report(generated_at=BASE_AT, latest_selected_count=1),
            _history_report(generated_at=BASE_AT + timedelta(minutes=5), latest_selected_count=2),
            _history_report(generated_at=BASE_AT + timedelta(minutes=10), latest_selected_count=3),
        ),
    )

    assert type(report.latest_selected_share) is Decimal
    assert type(report.average_selected_share) is Decimal
    assert type(report.selected_share_delta) is Decimal

    mutated = _history_report(generated_at=BASE_AT)
    object.__setattr__(mutated, "latest_selected_share", 0.75)
    with pytest.raises(ValueError, match="latest_selected_share"):
        _trend((mutated, mutated, mutated))

    with pytest.raises(ValueError, match="min_average_selected_share"):
        _config(min_average_selected_share=0.1)


def test_history_trend_rejects_false_flags_in_config_and_sources() -> None:
    config = _config()

    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="config must be report_only"):
        replace(config, report_only=False)
    with pytest.raises(ValueError, match="config must be readonly"):
        replace(config, readonly=False)

    for flag_name in ("paper_only", "report_only", "readonly"):
        source = _history_report(generated_at=BASE_AT)
        object.__setattr__(source, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            _trend((source, source, source))


def test_history_trend_dataclasses_are_frozen_and_validate_consistency() -> None:
    config = _config()
    report = _trend(
        (
            _history_report(generated_at=BASE_AT, latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=5), latest_selected_count=3),
            _history_report(generated_at=BASE_AT + timedelta(minutes=10), latest_selected_count=3),
        ),
        config=config,
    )

    with pytest.raises(FrozenInstanceError):
        config.min_history_count = 5  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.trend_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        _trend(
            (
                _history_report(generated_at=BASE_AT),
                _history_report(generated_at=BASE_AT + timedelta(minutes=5)),
                _history_report(generated_at=BASE_AT + timedelta(minutes=10)),
            ),
            generated_at=DatetimeSubclass(2026, 6, 25, 10, 15, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="refresh_source_history")
    with pytest.raises(ValueError, match="selected_share_delta"):
        replace(report, selected_share_delta=d("0.100000"))
    with pytest.raises(ValueError, match="trend report must be readonly"):
        replace(report, readonly=False)

    with pytest.raises(TypeError, match="TrendConfig .*subclassing"):
        class ConfigSubclass(_api().PaperProbabilitySelectionSummaryHistoryTrendConfig):
            pass

    with pytest.raises(TypeError, match="TrendReport .*subclassing"):
        class ReportSubclass(_api().PaperProbabilitySelectionSummaryHistoryTrendReport):
            pass


def test_history_trend_report_rejects_empty_and_unknown_reasons() -> None:
    report = _valid_trend_report()

    with pytest.raises(ValueError, match="reason_codes"):
        _direct_report_from(
            report,
            trend_status="watch",
            recommended_next_step="continue_monitoring",
            reason_codes=(),
        )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            report,
            trend_status="watch",
            recommended_next_step="continue_monitoring",
            reason_codes=("unknown_public_trend_reason",),
        )


@pytest.mark.parametrize(
    ("overrides", "match"),
    (
        (
            {
                "latest_history_status": "watch",
                "stale_history_count": 1,
                "trend_status": "watch",
                "reason_codes": ("latest_history_watch",),
            },
            "stale_history_count",
        ),
        (
            {
                "latest_history_status": "watch",
                "thin_history_count": 1,
                "trend_status": "watch",
                "reason_codes": ("latest_history_watch",),
            },
            "thin_history_count",
        ),
        (
            {
                "latest_history_status": "blocked",
                "stale_history_count": 1,
                "trend_status": "watch",
                "reason_codes": ("stale_history_reports_present",),
            },
            "latest_history_status",
        ),
        (
            {
                "latest_history_status": "watch",
                "recurring_reason_code_counts": (("shared_source_reason", 2),),
                "trend_status": "watch",
                "reason_codes": ("latest_history_watch",),
            },
            "recurring_reason_code_counts",
        ),
    ),
)
def test_history_trend_report_requires_reason_codes_for_supporting_data(
    overrides,
    match,
) -> None:
    with pytest.raises(ValueError, match=match):
        _direct_report_from(_valid_trend_report(), **overrides)


@pytest.mark.parametrize(
    ("recurring_reason_code_counts", "match"),
    (
        ((("shared_source_reason", 1),), "recurring_reason_code_counts"),
        ((("shared_source_reason", 4),), "source_history_count"),
    ),
)
def test_history_trend_report_rejects_impossible_recurring_reason_counts(
    recurring_reason_code_counts,
    match,
) -> None:
    with pytest.raises(ValueError, match=match):
        _direct_report_from(
            _valid_trend_report(),
            latest_history_status="watch",
            recurring_reason_code_counts=recurring_reason_code_counts,
            trend_status="watch",
            reason_codes=(
                "latest_history_watch",
                "recurring_history_reason_codes",
            ),
        )
