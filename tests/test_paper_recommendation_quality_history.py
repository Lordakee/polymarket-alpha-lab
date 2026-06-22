from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_recommendation_quality_summary import (
    PaperRecommendationQualityReasonCodeCount,
    PaperRecommendationQualitySubreportSummary,
    PaperRecommendationQualitySummaryReport,
)


GENERATED_AT = datetime(2026, 6, 22, 18, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
SUMMARY_STATUSES = ("pass", "watch", "blocked", "incomplete")
HISTORY_STATUSES = ("pass", "watch", "blocked")
SUBREPORT_NAMES = (
    "health",
    "consistency",
    "risk_budget",
    "reason_trend",
    "rank_stability",
)


class _DatetimeSubclass(datetime):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def _api():
    return import_module("polymarket_alpha_lab.paper_recommendation_quality_history")


def _config(**overrides):
    values = {
        "config_version": "paper-recommendation-quality-history-v0",
        "min_report_count": 3,
        "max_blocked_summary_count": 0,
        "max_incomplete_summary_count": 0,
        "max_duplicate_generated_at_count": 0,
        "max_recurring_incomplete_subreport_count": 1,
    }
    values.update(overrides)
    return _api().PaperRecommendationQualityHistoryConfig(**values)


def _subreports(
    *,
    status_by_name: dict[str, str] | None = None,
    reason_by_name: dict[str, tuple[str, ...]] | None = None,
) -> tuple[PaperRecommendationQualitySubreportSummary, ...]:
    status_by_name = status_by_name or {}
    reason_by_name = reason_by_name or {}
    rows = []
    for report_name in SUBREPORT_NAMES:
        status = status_by_name.get(report_name, "pass")
        reasons = reason_by_name.get(report_name, (f"{report_name}_passed",))
        rows.append(
            PaperRecommendationQualitySubreportSummary(
                report_name=report_name,
                status=status,
                generated_at=SOURCE_AT if status != "incomplete" else None,
                config_version=f"paper-recommendation-{report_name}-v0"
                if status != "incomplete"
                else None,
                row_count=1 if status != "incomplete" else 0,
                reason_codes=reasons,
            ),
        )
    return tuple(rows)


def _summary(
    *,
    generated_at: datetime = SOURCE_AT,
    summary_status: str = "pass",
    reason_codes: tuple[str, ...] = ("quality_summary_passed",),
    status_by_name: dict[str, str] | None = None,
    reason_by_name: dict[str, tuple[str, ...]] | None = None,
) -> PaperRecommendationQualitySummaryReport:
    if status_by_name is None:
        if summary_status == "blocked":
            status_by_name = {"risk_budget": "blocked"}
            reason_by_name = {
                **(reason_by_name or {}),
                "risk_budget": reason_codes,
            }
        elif summary_status == "incomplete":
            status_by_name = {"health": "incomplete"}
            reason_by_name = {
                **(reason_by_name or {}),
                "health": reason_codes,
            }
        elif summary_status == "watch":
            status_by_name = {"rank_stability": "watch"}
            reason_by_name = {
                **(reason_by_name or {}),
                "rank_stability": reason_codes,
            }
        else:
            reason_by_name = {
                **(reason_by_name or {}),
                "health": reason_codes,
            }
    subreports = _subreports(
        status_by_name=status_by_name,
        reason_by_name=reason_by_name,
    )
    pass_count = sum(1 for row in subreports if row.status == "pass")
    watch_count = sum(1 for row in subreports if row.status == "watch")
    blocked_count = sum(1 for row in subreports if row.status == "blocked")
    incomplete_count = sum(1 for row in subreports if row.status == "incomplete")
    reason_code_counts = _reason_code_counts(subreports)
    return PaperRecommendationQualitySummaryReport(
        generated_at=generated_at,
        config_version="paper-recommendation-quality-summary-v0",
        summary_status=summary_status,
        subreport_count=len(subreports),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        incomplete_count=incomplete_count,
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(row.reason_code for row in reason_code_counts),
        subreports=subreports,
    )


def _reason_code_counts(
    subreports: tuple[PaperRecommendationQualitySubreportSummary, ...],
) -> tuple[PaperRecommendationQualityReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for subreport in subreports:
        for reason_code in frozenset(subreport.reason_codes):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperRecommendationQualityReasonCodeCount(
            reason_code=reason_code,
            subreport_count=subreport_count,
        )
        for reason_code, subreport_count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _history(*reports: PaperRecommendationQualitySummaryReport, **config_overrides):
    return _api().build_paper_recommendation_quality_history_report(
        reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_quality_history_empty_and_insufficient_reports_are_blocked():
    api = _api()

    empty = _history()

    assert isinstance(empty, api.PaperRecommendationQualityHistoryReport)
    assert empty.generated_at == GENERATED_AT
    assert empty.config_version == "paper-recommendation-quality-history-v0"
    assert empty.history_status == "blocked"
    assert empty.source_report_count == 0
    assert empty.first_source_generated_at is None
    assert empty.latest_source_generated_at is None
    assert empty.summary_status_rows == tuple(
        api.PaperRecommendationQualityHistoryStatusRow(status, 0)
        for status in SUMMARY_STATUSES
    )
    assert empty.duplicate_generated_at_count == 0
    assert empty.recurring_blocked_reason_codes == ()
    assert empty.recurring_incomplete_subreports == ()
    assert empty.reason_codes == ("insufficient_quality_summary_history",)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    insufficient = _history(_summary())

    assert insufficient.history_status == "blocked"
    assert insufficient.source_report_count == 1
    assert insufficient.first_source_generated_at == SOURCE_AT
    assert insufficient.latest_source_generated_at == SOURCE_AT
    assert insufficient.reason_codes == ("insufficient_quality_summary_history",)


def test_quality_history_passes_when_thresholds_are_clean_and_reports_sort_chronologically():
    latest = _summary(generated_at=SOURCE_AT + timedelta(hours=2))
    first = _summary(generated_at=SOURCE_AT)
    middle = _summary(generated_at=SOURCE_AT + timedelta(hours=1))

    history = _history(latest, first, middle)

    assert history.history_status == "pass"
    assert history.source_report_count == 3
    assert history.first_source_generated_at == first.generated_at
    assert history.latest_source_generated_at == latest.generated_at
    assert history.summary_status_rows == (
        _api().PaperRecommendationQualityHistoryStatusRow("pass", 3),
        _api().PaperRecommendationQualityHistoryStatusRow("watch", 0),
        _api().PaperRecommendationQualityHistoryStatusRow("blocked", 0),
        _api().PaperRecommendationQualityHistoryStatusRow("incomplete", 0),
    )
    assert history.duplicate_generated_at_count == 0
    assert history.recurring_blocked_reason_codes == ()
    assert history.recurring_incomplete_subreports == ()
    assert history.reason_codes == ("quality_summary_history_passed",)


def test_quality_history_blocks_when_blocked_summary_count_exceeds_threshold():
    history = _history(
        _summary(generated_at=SOURCE_AT),
        _summary(
            generated_at=SOURCE_AT + timedelta(hours=1),
            summary_status="blocked",
            reason_codes=("empty_selection",),
        ),
        _summary(generated_at=SOURCE_AT + timedelta(hours=2)),
    )

    assert history.history_status == "blocked"
    assert history.summary_status_rows[2].status_count == 1
    assert history.recurring_blocked_reason_codes == ("empty_selection",)
    assert history.reason_codes == (
        "blocked_quality_summary_threshold_exceeded",
        "recurring_blocked_reason_codes_present",
    )


def test_quality_history_watches_duplicate_generated_at_with_stable_tie_handling():
    generated_at = SOURCE_AT + timedelta(hours=1)
    watch = _summary(
        generated_at=generated_at,
        summary_status="watch",
        reason_codes=("optional_rank_stability_report_missing",),
    )
    blocked = _summary(
        generated_at=generated_at,
        summary_status="blocked",
        reason_codes=("empty_selection",),
    )

    first = _history(
        _summary(generated_at=SOURCE_AT),
        watch,
        blocked,
        max_blocked_summary_count=1,
    )
    second = _history(
        _summary(generated_at=SOURCE_AT),
        blocked,
        watch,
        max_blocked_summary_count=1,
    )

    assert first.history_status == "watch"
    assert second.history_status == "watch"
    assert first.latest_source_generated_at == generated_at
    assert second.latest_source_generated_at == generated_at
    assert first.summary_status_rows == second.summary_status_rows
    assert first.duplicate_generated_at_count == 1
    assert second.duplicate_generated_at_count == 1
    assert first.reason_codes == ("duplicate_generated_at_threshold_exceeded",)
    assert second.reason_codes == ("duplicate_generated_at_threshold_exceeded",)


def test_quality_history_watches_recurring_incomplete_subreports():
    first_incomplete = _summary(
        generated_at=SOURCE_AT,
        summary_status="incomplete",
        reason_codes=("health_report_missing",),
        status_by_name={"health": "incomplete"},
        reason_by_name={"health": ("health_report_missing",)},
    )
    second_incomplete = _summary(
        generated_at=SOURCE_AT + timedelta(hours=1),
        summary_status="incomplete",
        reason_codes=("health_report_missing",),
        status_by_name={"health": "incomplete"},
        reason_by_name={"health": ("health_report_missing",)},
    )
    clean = _summary(generated_at=SOURCE_AT + timedelta(hours=2))

    history = _history(
        clean,
        second_incomplete,
        first_incomplete,
        max_incomplete_summary_count=2,
    )

    assert history.history_status == "watch"
    assert history.recurring_incomplete_subreports == (
        _api().PaperRecommendationQualityHistoryRecurringSubreportRow(
            report_name="health",
            incomplete_count=2,
        ),
    )
    assert history.reason_codes == (
        "recurring_incomplete_subreports_present",
    )


def test_quality_history_reason_codes_are_deterministically_ordered():
    history = _history(
        _summary(generated_at=SOURCE_AT),
        _summary(
            generated_at=SOURCE_AT + timedelta(hours=1),
            summary_status="blocked",
            reason_codes=("zeta_blocked",),
        ),
        _summary(
            generated_at=SOURCE_AT + timedelta(hours=1),
            summary_status="blocked",
            reason_codes=("alpha_blocked",),
        ),
        _summary(
            generated_at=SOURCE_AT + timedelta(hours=2),
            summary_status="incomplete",
            reason_codes=("health_report_missing",),
            status_by_name={"health": "incomplete"},
            reason_by_name={"health": ("health_report_missing",)},
        ),
        _summary(
            generated_at=SOURCE_AT + timedelta(hours=3),
            summary_status="incomplete",
            reason_codes=("health_report_missing",),
            status_by_name={"health": "incomplete"},
            reason_by_name={"health": ("health_report_missing",)},
        ),
        max_blocked_summary_count=1,
        max_incomplete_summary_count=1,
    )

    assert history.history_status == "blocked"
    assert history.recurring_blocked_reason_codes == ("alpha_blocked", "zeta_blocked")
    assert history.recurring_incomplete_subreports == (
        _api().PaperRecommendationQualityHistoryRecurringSubreportRow("health", 2),
    )
    assert history.reason_codes == (
        "blocked_quality_summary_threshold_exceeded",
        "duplicate_generated_at_threshold_exceeded",
        "incomplete_quality_summary_threshold_exceeded",
        "recurring_blocked_reason_codes_present",
        "recurring_incomplete_subreports_present",
    )


def test_quality_history_dataclasses_are_frozen_and_revalidate_hard_flags():
    api = _api()
    history = _history(
        _summary(generated_at=SOURCE_AT),
        _summary(generated_at=SOURCE_AT + timedelta(hours=1)),
        _summary(generated_at=SOURCE_AT + timedelta(hours=2)),
    )

    with pytest.raises(FrozenInstanceError):
        history.history_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(history, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(history, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(history, readonly=False)
    with pytest.raises(FrozenInstanceError):
        history.summary_status_rows[0].status_count = 99  # type: ignore[misc]

    recurring_history = _history(
        _summary(
            generated_at=SOURCE_AT,
            summary_status="incomplete",
            reason_codes=("health_report_missing",),
            status_by_name={"health": "incomplete"},
            reason_by_name={"health": ("health_report_missing",)},
        ),
        _summary(
            generated_at=SOURCE_AT + timedelta(hours=1),
            summary_status="incomplete",
            reason_codes=("health_report_missing",),
            status_by_name={"health": "incomplete"},
            reason_by_name={"health": ("health_report_missing",)},
        ),
        _summary(generated_at=SOURCE_AT + timedelta(hours=2)),
        max_incomplete_summary_count=2,
    )
    with pytest.raises(FrozenInstanceError):
        recurring_history.recurring_incomplete_subreports[0].incomplete_count = 99  # type: ignore[misc]
    with pytest.raises(ValueError, match="status_count"):
        api.PaperRecommendationQualityHistoryStatusRow("pass", -1)
    with pytest.raises(ValueError, match="report_name"):
        api.PaperRecommendationQualityHistoryRecurringSubreportRow("unknown", 1)


def test_quality_history_rejects_invalid_inputs_and_scalar_subclasses():
    api = _api()

    for reports in (object(), "reports", b"reports", {"report": _summary()}):
        with pytest.raises(ValueError, match="summary_reports must be a list or tuple"):
            api.build_paper_recommendation_quality_history_report(
                reports,
                config=_config(),
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="summary_reports must contain"):
        api.build_paper_recommendation_quality_history_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_recommendation_quality_history_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_paper_recommendation_quality_history_report(
            (),
            config=_config(),
            generated_at=object(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_paper_recommendation_quality_history_report(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 6, 22, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config_version"):
        api.PaperRecommendationQualityHistoryConfig(
            config_version=_StringSubclass("paper-recommendation-quality-history-v0"),
        )
    with pytest.raises(ValueError, match="min_report_count"):
        api.PaperRecommendationQualityHistoryConfig(
            config_version="paper-recommendation-quality-history-v0",
            min_report_count=_IntSubclass(1),
        )
    with pytest.raises(ValueError, match="min_report_count"):
        api.PaperRecommendationQualityHistoryConfig(
            config_version="paper-recommendation-quality-history-v0",
            min_report_count=True,
        )
    with pytest.raises(ValueError, match="max_blocked_summary_count"):
        api.PaperRecommendationQualityHistoryConfig(
            config_version="paper-recommendation-quality-history-v0",
            max_blocked_summary_count=-1,
        )


def test_quality_history_normalizes_utc_and_rejects_mutated_source_flags():
    source = _summary(
        generated_at=datetime(2026, 6, 22, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    history = _history(
        source,
        _summary(generated_at=SOURCE_AT + timedelta(hours=1)),
        _summary(generated_at=SOURCE_AT + timedelta(hours=2)),
    )

    assert history.first_source_generated_at == SOURCE_AT

    object.__setattr__(source, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _history(source)
