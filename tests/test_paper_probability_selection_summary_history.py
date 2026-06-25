from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_probability_selection_summary import (
    PaperProbabilitySelectionSummaryReport,
    PaperProbabilitySelectionSummaryRow,
)
from polymarket_alpha_lab.paper_probability_selection_summary_history import (
    PaperProbabilitySelectionSummaryHistoryConfig,
    PaperProbabilitySelectionSummaryHistoryReport,
    build_paper_probability_selection_summary_history_report,
)


GENERATED_AT = datetime(2026, 6, 25, 18, 0, tzinfo=UTC)
CONFIG = PaperProbabilitySelectionSummaryHistoryConfig(
    config_version="paper-probability-selection-summary-history-v0",
    min_source_report_count=2,
    max_latest_age_seconds=900,
    min_latest_selected_share=Decimal("0.250000"),
    min_average_selected_share=Decimal("0.250000"),
)


class SelectionSummaryReportSubclass(PaperProbabilitySelectionSummaryReport):
    pass


class _DatetimeSubclass(datetime):
    pass


class _IntSubclass(int):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def selection_row(
    queue_rank: int,
    *,
    market_slug: str,
    recommended_next_step: str,
    selection_status: str,
    reason_codes: tuple[str, ...],
) -> PaperProbabilitySelectionSummaryRow:
    return PaperProbabilitySelectionSummaryRow(
        queue_rank=queue_rank,
        market_slug=market_slug,
        question=f"Will {market_slug} resolve yes?",
        side="yes",
        action="recommend",
        recommendation_score=d("0.100000"),
        net_probability_edge=d("0.050000"),
        executable_paper_shares=d("10.000000"),
        recommended_next_step=recommended_next_step,
        selection_status=selection_status,
        stress_scenario_count=1,
        stress_pass_count=1 if selection_status == "ready" else 0,
        stress_watch_count=1 if selection_status == "watch" else 0,
        stress_fail_count=1 if selection_status == "blocked" else 0,
        worst_stressed_net_probability_edge=d("0.040000"),
        reason_codes=reason_codes,
    )


def summary_report(
    generated_at: datetime,
    *,
    config_version: str = "paper-probability-selection-summary-v0",
    ready_count: int = 1,
    watch_count: int = 0,
    blocked_count: int = 0,
    skip_count: int = 0,
    reason_codes: tuple[str, ...] | None = None,
) -> PaperProbabilitySelectionSummaryReport:
    rows: list[PaperProbabilitySelectionSummaryRow] = []
    rank = 1
    for index in range(ready_count):
        rows.append(
            selection_row(
                rank,
                market_slug=f"ready-{index + 1}",
                recommended_next_step="research_review",
                selection_status="ready",
                reason_codes=("cost_stress_passed",),
            ),
        )
        rank += 1
    for index in range(watch_count):
        rows.append(
            selection_row(
                rank,
                market_slug=f"watch-{index + 1}",
                recommended_next_step="await_fresh_context",
                selection_status="watch",
                reason_codes=("source_next_step_await_fresh_context",),
            ),
        )
        rank += 1
    for index in range(blocked_count):
        use_skip = index < skip_count
        rows.append(
            selection_row(
                rank,
                market_slug=f"blocked-{index + 1}",
                recommended_next_step="skip" if use_skip else "research_review",
                selection_status="blocked",
                reason_codes=(
                    ("source_next_step_skip",)
                    if use_skip
                    else ("cost_stress_failed",)
                ),
            ),
        )
        rank += 1

    return PaperProbabilitySelectionSummaryReport(
        generated_at=generated_at,
        config_version=config_version,
        source_queue_config_version="probability-recommendation-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        queue_count=len(rows),
        ready_count=ready_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        missing_stress_count=0,
        rows=tuple(rows),
        reason_codes=reason_codes
        if reason_codes is not None
        else _summary_reason_codes(rows),
    )


def _summary_reason_codes(
    rows: list[PaperProbabilitySelectionSummaryRow],
) -> tuple[str, ...]:
    if not rows:
        return ("no_probability_queue_rows",)
    if any(row.selection_status == "blocked" for row in rows):
        return ("blocked_selection_rows_present",)
    if any(row.selection_status == "watch" for row in rows):
        return ("watch_selection_rows_present",)
    return ("ready_selection_rows_present",)


def history_report(
    reports: tuple[PaperProbabilitySelectionSummaryReport, ...],
    *,
    config: PaperProbabilitySelectionSummaryHistoryConfig = CONFIG,
    generated_at: datetime = GENERATED_AT,
) -> PaperProbabilitySelectionSummaryHistoryReport:
    return build_paper_probability_selection_summary_history_report(
        reports,
        config=config,
        generated_at=generated_at,
    )


def test_history_report_summarizes_ordered_selection_summary_reports() -> None:
    first = summary_report(
        datetime(2026, 6, 25, 16, 40, tzinfo=timezone(timedelta(hours=-1))),
        ready_count=1,
        watch_count=1,
        blocked_count=0,
        reason_codes=("watch_selection_rows_present",),
    )
    latest = summary_report(
        datetime(2026, 6, 25, 17, 50, tzinfo=UTC),
        ready_count=2,
        watch_count=1,
        blocked_count=1,
        skip_count=1,
        reason_codes=("blocked_selection_rows_present",),
    )

    report = history_report((first, latest))

    assert type(report) is PaperProbabilitySelectionSummaryHistoryReport
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == CONFIG.config_version
    assert report.source_report_count == 2
    assert report.first_generated_at == datetime(2026, 6, 25, 17, 40, tzinfo=UTC)
    assert report.latest_generated_at == datetime(2026, 6, 25, 17, 50, tzinfo=UTC)
    assert report.history_span_seconds == 600
    assert report.latest_age_seconds == 600
    assert report.latest_queue_count == 4
    assert report.latest_selected_count == 2
    assert report.latest_pending_count == 1
    assert report.latest_rejected_count == 1
    assert report.latest_skipped_count == 1
    assert report.aggregate_queue_count == 6
    assert report.aggregate_selected_count == 3
    assert report.aggregate_pending_count == 2
    assert report.aggregate_rejected_count == 1
    assert report.aggregate_skipped_count == 1
    assert report.latest_selected_share == d("0.500000")
    assert report.average_selected_share == d("0.500000")
    assert report.distinct_config_versions == (
        "paper-probability-selection-summary-v0",
    )
    assert report.reason_code_counts == (
        ("blocked_selection_rows_present", 1),
        ("cost_stress_passed", 3),
        ("source_next_step_await_fresh_context", 2),
        ("source_next_step_skip", 1),
        ("watch_selection_rows_present", 1),
    )
    assert report.history_status == "watch"
    assert report.recommended_next_step == "review_probability_selection"
    assert report.reason_codes == (
        "latest_selection_has_blocked_rows",
        "latest_selection_has_watch_rows",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_report_marks_stable_ready_history() -> None:
    report = history_report(
        (
            summary_report(
                datetime(2026, 6, 25, 17, 45, tzinfo=UTC),
                ready_count=2,
            ),
            summary_report(
                datetime(2026, 6, 25, 17, 55, tzinfo=UTC),
                ready_count=3,
            ),
        ),
    )

    assert report.history_status == "ready"
    assert report.recommended_next_step == "proceed_to_paper_allocation"
    assert report.reason_codes == ("selection_summary_history_stable",)
    assert report.latest_selected_share == d("1.000000")
    assert report.average_selected_share == d("1.000000")


def test_history_report_blocks_empty_insufficient_stale_or_low_selection_history() -> None:
    empty = history_report(())
    assert empty.source_report_count == 0
    assert empty.first_generated_at is None
    assert empty.latest_generated_at is None
    assert empty.history_span_seconds is None
    assert empty.latest_age_seconds is None
    assert empty.history_status == "blocked"
    assert empty.recommended_next_step == "collect_more_history"
    assert empty.reason_codes == (
        "no_selection_summary_history",
        "insufficient_selection_summary_history",
    )

    stale = history_report(
        (
            summary_report(
                datetime(2026, 6, 25, 17, 0, tzinfo=UTC),
                ready_count=1,
                blocked_count=1,
            ),
        ),
    )
    assert stale.history_status == "blocked"
    assert stale.reason_codes == (
        "insufficient_selection_summary_history",
        "latest_selection_summary_stale",
        "latest_selection_has_blocked_rows",
    )

    low_selection = history_report(
        (
            summary_report(
                datetime(2026, 6, 25, 17, 45, tzinfo=UTC),
                ready_count=0,
                watch_count=1,
                blocked_count=1,
            ),
            summary_report(
                datetime(2026, 6, 25, 17, 55, tzinfo=UTC),
                ready_count=0,
                watch_count=2,
            ),
        ),
    )
    assert low_selection.history_status == "blocked"
    assert low_selection.latest_selected_share == d("0.000000")
    assert low_selection.average_selected_share == d("0.000000")
    assert low_selection.reason_codes == (
        "latest_selection_has_watch_rows",
        "latest_selected_share_below_minimum",
        "average_selected_share_below_minimum",
    )


def test_history_report_rejects_lists_duck_types_subclasses_and_false_flags() -> None:
    source = summary_report(datetime(2026, 6, 25, 17, 55, tzinfo=UTC), ready_count=1)

    with pytest.raises(ValueError, match="tuple"):
        history_report([source])  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryReport"):
        history_report((object(),))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="PaperProbabilitySelectionSummaryReport"):
        history_report((SelectionSummaryReportSubclass(**source.__dict__),))

    for flag_name in ("paper_only", "report_only", "readonly"):
        mutated = summary_report(datetime(2026, 6, 25, 17, 55, tzinfo=UTC), ready_count=1)
        object.__setattr__(mutated, flag_name, False)
        with pytest.raises(ValueError, match=flag_name):
            history_report((mutated,))


def test_history_report_rejects_non_chronological_source_reports() -> None:
    with pytest.raises(ValueError, match="chronological"):
        history_report(
            (
                summary_report(
                    datetime(2026, 6, 25, 17, 55, tzinfo=UTC),
                    ready_count=1,
                ),
                summary_report(
                    datetime(2026, 6, 25, 17, 45, tzinfo=UTC),
                    ready_count=1,
                ),
            ),
        )


def test_history_report_rejects_bad_config_and_generated_at_types() -> None:
    source = summary_report(datetime(2026, 6, 25, 17, 55, tzinfo=UTC), ready_count=1)

    with pytest.raises(ValueError, match="config"):
        build_paper_probability_selection_summary_history_report(
            (source,),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        history_report((source,), generated_at="bad")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        history_report((source,), generated_at=datetime(2026, 6, 25, 18, 0))
    with pytest.raises(ValueError, match="future"):
        history_report(
            (
                summary_report(
                    datetime(2026, 6, 25, 18, 1, tzinfo=UTC),
                    ready_count=1,
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        history_report(
            (
                summary_report(
                    _DatetimeSubclass(2026, 6, 25, 17, 55, tzinfo=UTC),
                    ready_count=1,
                ),
            ),
        )

    with pytest.raises(ValueError, match="config_version"):
        replace(CONFIG, config_version=_StringSubclass("history-v0"))
    with pytest.raises(ValueError, match="min_source_report_count"):
        replace(CONFIG, min_source_report_count=_IntSubclass(2))
    with pytest.raises(ValueError, match="min_latest_selected_share"):
        replace(CONFIG, min_latest_selected_share=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(CONFIG, paper_only=False)
    with pytest.raises(TypeError, match="HistoryConfig .*subclassing"):
        class HistoryConfigSubclass(PaperProbabilitySelectionSummaryHistoryConfig):
            pass


def test_history_report_constructor_rejects_inconsistent_reports_and_is_frozen() -> None:
    report = history_report(
        (
            summary_report(
                datetime(2026, 6, 25, 17, 45, tzinfo=UTC),
                ready_count=2,
            ),
            summary_report(
                datetime(2026, 6, 25, 17, 55, tzinfo=UTC),
                ready_count=3,
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        report.history_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="first_generated_at"):
        replace(report, source_report_count=0)
    with pytest.raises(ValueError, match="latest_selected_share"):
        replace(report, latest_selected_share=d("0.500000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=(("cost_stress_passed", 4),))
    with pytest.raises(ValueError, match="history_status"):
        replace(report, history_status="pass")
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(report, recommended_next_step="collect_more_history")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(report, reason_codes=("latest_selection_has_watch_rows",))
    with pytest.raises(ValueError, match="history report must be readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="history_span_seconds"):
        replace(report, history_span_seconds=-1)
    with pytest.raises(ValueError, match="latest_age_seconds"):
        replace(report, latest_age_seconds=-1)
    with pytest.raises(TypeError, match="HistoryReport .*subclassing"):
        class HistoryReportSubclass(PaperProbabilitySelectionSummaryHistoryReport):
            pass
