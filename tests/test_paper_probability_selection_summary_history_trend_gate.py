from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_probability_selection_summary_history_trend import (
    PaperProbabilitySelectionSummaryHistoryTrendReport,
)


GENERATED_AT = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 29, 11, 45, tzinfo=UTC)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_probability_selection_summary_history_trend_gate",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides):
    values = {
        "config_version": (
            "paper-probability-selection-summary-history-trend-gate-v0"
        ),
        "min_source_history_count": 3,
        "max_latest_status_streak_for_watch": 1,
        "max_trend_report_age_seconds": 86_400,
        "max_recurring_reason_code_count": 2,
    }
    values.update(overrides)
    return _api().PaperProbabilitySelectionSummaryHistoryTrendGateConfig(**values)


def _trend_report(
    *,
    generated_at: datetime = SOURCE_AT,
    source_history_count: int = 4,
    first_generated_at: datetime | None = None,
    latest_generated_at: datetime | None = None,
    latest_history_status: str = "ready",
    latest_status_streak: int = 1,
    latest_selected_share: Decimal = d("0.750000"),
    average_selected_share: Decimal = d("0.750000"),
    selected_share_delta: Decimal = d("0.000000"),
    stale_history_count: int = 0,
    thin_history_count: int = 0,
    recurring_reason_code_counts: tuple[tuple[str, int], ...] = (),
    trend_status: str = "stable",
    recommended_next_step: str = "continue_monitoring",
    reason_codes: tuple[str, ...] = ("history_trend_stable",),
) -> PaperProbabilitySelectionSummaryHistoryTrendReport:
    if first_generated_at is None:
        first_generated_at = generated_at - timedelta(hours=3)
    if latest_generated_at is None:
        latest_generated_at = generated_at
    return PaperProbabilitySelectionSummaryHistoryTrendReport(
        generated_at=generated_at,
        config_version="paper-probability-selection-summary-history-trend-v0",
        source_history_count=source_history_count,
        first_generated_at=first_generated_at,
        latest_generated_at=latest_generated_at,
        history_span_seconds=int((latest_generated_at - first_generated_at).total_seconds()),
        latest_history_status=latest_history_status,
        latest_status_streak=latest_status_streak,
        latest_selected_share=latest_selected_share,
        average_selected_share=average_selected_share,
        selected_share_delta=selected_share_delta,
        stale_history_count=stale_history_count,
        thin_history_count=thin_history_count,
        recurring_reason_code_counts=recurring_reason_code_counts,
        trend_status=trend_status,
        recommended_next_step=recommended_next_step,
        reason_codes=reason_codes,
    )


def _direct_report_from(report, **overrides):
    values = {field.name: getattr(report, field.name) for field in fields(report)}
    values.update(overrides)
    return _api().PaperProbabilitySelectionSummaryHistoryTrendGateReport(**values)


def _reason_count_rows(*reason_codes: str):
    return tuple(
        _api().PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
            reason_code,
            1,
        )
        for reason_code in reason_codes
    )


def test_selection_summary_trend_gate_exports_expected_api() -> None:
    api = _api()

    for name in (
        "DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_HISTORY_TREND_GATE_CONFIG_VERSION",
        "PaperProbabilitySelectionSummaryHistoryTrendGateConfig",
        "PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount",
        "PaperProbabilitySelectionSummaryHistoryTrendGateReport",
        "build_paper_probability_selection_summary_history_trend_gate_report",
    ):
        assert name in api.__all__
        assert hasattr(api, name)


def test_selection_summary_trend_gate_passes_stable_selection_trend() -> None:
    source = _trend_report(
        trend_status="stable",
        reason_codes=("history_trend_stable",),
    )

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert type(report) is _api().PaperProbabilitySelectionSummaryHistoryTrendGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "paper-probability-selection-summary-history-trend-gate-v0"
    )
    assert report.source_config_version == source.config_version
    assert report.source_generated_at == SOURCE_AT
    assert report.trend_report_age_seconds == 900
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "allow_probability_selection_summary_history_trend_review"
    )
    assert report.source_history_count == 4
    assert report.source_trend_status == "stable"
    assert report.source_recommended_next_step == "continue_monitoring"
    assert report.latest_history_status == "ready"
    assert report.latest_status_streak == 1
    assert report.latest_selected_share == d("0.750000")
    assert report.average_selected_share == d("0.750000")
    assert report.selected_share_delta == d("0.000000")
    assert report.stale_history_count == 0
    assert report.thin_history_count == 0
    assert report.latest_source_reason_codes == ("history_trend_stable",)
    assert report.recurring_source_reason_code_counts == ()
    assert report.reason_codes == (
        "paper_probability_selection_summary_history_trend_gate_passed",
    )
    assert report.reason_code_counts == (
        _api().PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
            "paper_probability_selection_summary_history_trend_gate_passed",
            1,
        ),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_selection_summary_trend_gate_watches_source_watch_and_stale_reports() -> None:
    source = _trend_report(
        trend_status="watch",
        stale_history_count=1,
        reason_codes=("stale_history_reports_present",),
    )

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_probability_selection_summary_history_trend_review"
    )
    assert "latest_paper_probability_selection_summary_history_trend_watch" in (
        report.reason_codes
    )
    assert report.stale_history_count == 1


def test_selection_summary_trend_gate_blocks_insufficient_source_history() -> None:
    source = _trend_report(
        source_history_count=2,
        trend_status="insufficient_history",
        recommended_next_step="collect_more_history",
        reason_codes=("insufficient_history_count",),
    )

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(min_source_history_count=3),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_probability_selection_summary_history_trend_review"
    )
    assert report.reason_codes == (
        "insufficient_paper_probability_selection_summary_history_trend_samples",
    )


def test_selection_summary_trend_gate_blocks_stale_source_trend() -> None:
    source = _trend_report(
        trend_status="stale",
        recommended_next_step="refresh_source_history",
        stale_history_count=1,
        reason_codes=("latest_history_stale",),
    )

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "stale_paper_probability_selection_summary_history_trend",
    )


def test_selection_summary_trend_gate_blocks_deteriorating_source_trend() -> None:
    source = _trend_report(
        latest_selected_share=d("0.500000"),
        average_selected_share=d("0.650000"),
        selected_share_delta=d("-0.250000"),
        trend_status="deteriorating",
        recommended_next_step="review_probability_selection",
        reason_codes=("selected_share_deteriorated",),
    )

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "blocked"
    assert report.reason_codes == (
        "deteriorating_paper_probability_selection_summary_history_trend",
    )


def test_selection_summary_trend_gate_keeps_repeated_watch_streak_as_watch() -> None:
    source = _trend_report(
        latest_history_status="watch",
        latest_status_streak=3,
        trend_status="watch",
        recommended_next_step="continue_monitoring",
        reason_codes=("latest_history_watch",),
    )

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(max_latest_status_streak_for_watch=1),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.reason_codes == (
        "latest_paper_probability_selection_summary_history_trend_watch",
        "repeated_paper_probability_selection_summary_history_trend_watch_threshold_exceeded",
    )


def test_selection_summary_trend_gate_watches_thin_and_recurring_source_signals() -> None:
    source = _trend_report(
        trend_status="watch",
        thin_history_count=1,
        recurring_reason_code_counts=(("latest_selection_has_watch_rows", 3),),
        reason_codes=(
            "thin_history_reports_present",
            "recurring_history_reason_codes",
        ),
    )

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(max_recurring_reason_code_count=2),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.reason_codes == (
        "latest_paper_probability_selection_summary_history_trend_watch",
        "thin_paper_probability_selection_summary_history_trend_reports",
        "recurring_paper_probability_selection_summary_history_trend_reason_codes",
    )
    assert report.recurring_source_reason_code_counts == (
        ("latest_selection_has_watch_rows", 3),
    )


def test_selection_summary_trend_gate_watches_aged_trend_report() -> None:
    source = _trend_report(generated_at=GENERATED_AT - timedelta(seconds=86_401))

    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        source,
        config=_config(max_trend_report_age_seconds=86_400),
        generated_at=GENERATED_AT,
    )

    assert report.gate_status == "watch"
    assert report.trend_report_age_seconds == 86_401
    assert report.reason_codes == (
        "aged_paper_probability_selection_summary_history_trend_report",
    )


def test_selection_summary_trend_gate_rejects_wrong_source_type_and_future_source() -> None:
    with pytest.raises(
        ValueError,
        match=(
            "source_report must be exactly "
            "PaperProbabilitySelectionSummaryHistoryTrendReport"
        ),
    ):
        _api().build_paper_probability_selection_summary_history_trend_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="source_generated_at must not be after generated_at"):
        _api().build_paper_probability_selection_summary_history_trend_gate_report(
            _trend_report(generated_at=GENERATED_AT + timedelta(seconds=1)),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_selection_summary_trend_gate_validates_exact_config_type_and_hard_flags() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        class ConfigSubclass(_api().PaperProbabilitySelectionSummaryHistoryTrendGateConfig):
            pass

    with pytest.raises(ValueError, match="config must be exactly"):
        _api().build_paper_probability_selection_summary_history_trend_gate_report(
            _trend_report(),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="paper_only"):
        _config(paper_only=False)
    with pytest.raises(ValueError, match="max_trend_report_age_seconds"):
        _config(max_trend_report_age_seconds=-1)

    source = _trend_report()
    object.__setattr__(source, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _api().build_paper_probability_selection_summary_history_trend_gate_report(
            source,
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_selection_summary_trend_gate_dataclasses_are_frozen() -> None:
    config = _config()
    count = _api().PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
        "paper_probability_selection_summary_history_trend_gate_passed",
        1,
    )
    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        _trend_report(),
        config=config,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        config.min_source_history_count = 5  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]


def test_selection_summary_trend_gate_uses_decimal_only_for_share_fields() -> None:
    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        _trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert type(report.latest_selected_share) is Decimal
    assert type(report.average_selected_share) is Decimal
    assert type(report.selected_share_delta) is Decimal

    source = _trend_report()
    object.__setattr__(source, "latest_selected_share", 0.75)
    with pytest.raises(ValueError, match="latest_selected_share"):
        _api().build_paper_probability_selection_summary_history_trend_gate_report(
            source,
            config=_config(),
            generated_at=GENERATED_AT,
        )

    with pytest.raises(ValueError, match="selected_share_delta"):
        _direct_report_from(report, selected_share_delta=-0.1)


def test_selection_summary_trend_gate_report_validates_direct_construction() -> None:
    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        _trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    pass_reason = "paper_probability_selection_summary_history_trend_gate_passed"
    watch_reason = "latest_paper_probability_selection_summary_history_trend_watch"

    with pytest.raises(ValueError, match="recommended_next_step"):
        _direct_report_from(report, recommended_next_step="wrong_next_step")
    with pytest.raises(ValueError, match="reason_code_counts"):
        _direct_report_from(report, reason_code_counts=())
    with pytest.raises(ValueError, match="reason_codes"):
        _direct_report_from(
            report,
            reason_codes=("unknown_gate_reason",),
            reason_code_counts=_reason_count_rows("unknown_gate_reason"),
        )
    with pytest.raises(ValueError, match="pass"):
        _direct_report_from(
            report,
            gate_status="watch",
            recommended_next_step=(
                "throttle_probability_selection_summary_history_trend_review"
            ),
            reason_codes=(pass_reason, watch_reason),
            reason_code_counts=_reason_count_rows(pass_reason, watch_reason),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        _direct_report_from(
            report,
            reason_codes=(pass_reason, pass_reason),
            reason_code_counts=_reason_count_rows(pass_reason, pass_reason),
        )
    with pytest.raises(ValueError, match="source_trend_status"):
        _direct_report_from(report, source_trend_status="unexpected")
    with pytest.raises(ValueError, match="latest_history_status"):
        _direct_report_from(report, latest_history_status="unexpected")
    with pytest.raises(ValueError, match="latest_status_streak"):
        _direct_report_from(report, latest_status_streak=report.source_history_count + 1)
    with pytest.raises(ValueError, match="thin_history_count"):
        _direct_report_from(
            report,
            gate_status="watch",
            recommended_next_step=(
                "throttle_probability_selection_summary_history_trend_review"
            ),
            thin_history_count=1,
            reason_codes=(watch_reason,),
            reason_code_counts=_reason_count_rows(watch_reason),
        )
    with pytest.raises(ValueError, match="recurring_source_reason_code_counts"):
        _direct_report_from(
            report,
            recurring_source_reason_code_counts=(("duplicate_reason", 1),) * 2,
        )


def test_selection_summary_trend_gate_report_rejects_inconsistent_gate_reasons() -> None:
    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        _trend_report(
            trend_status="watch",
            stale_history_count=1,
            reason_codes=("stale_history_reports_present",),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="source_trend_status"):
        _direct_report_from(
            report,
            source_trend_status="stable",
        )
    with pytest.raises(ValueError, match="gate_status"):
        _direct_report_from(
            report,
            gate_status="pass",
            recommended_next_step=(
                "allow_probability_selection_summary_history_trend_review"
            ),
        )


def test_selection_summary_trend_gate_reason_count_rejects_false_flags() -> None:
    with pytest.raises(ValueError, match="report_only"):
        _api().PaperProbabilitySelectionSummaryHistoryTrendGateReasonCodeCount(
            "paper_probability_selection_summary_history_trend_gate_passed",
            1,
            report_only=False,
        )


def test_selection_summary_trend_gate_report_constructor_rejects_false_flags() -> None:
    report = _api().build_paper_probability_selection_summary_history_trend_gate_report(
        _trend_report(),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    with pytest.raises(ValueError, match="gate report readonly"):
        replace(report, readonly=False)
