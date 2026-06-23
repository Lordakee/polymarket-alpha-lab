from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module

import pytest

from polymarket_alpha_lab.paper_research_packet_quality import (
    PaperResearchPacketQualityCheckRow,
    PaperResearchPacketQualityReasonCodeCount,
    PaperResearchPacketQualityReport,
)


GENERATED_AT = datetime(2026, 6, 23, 18, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
QUALITY_STATUSES = ("pass", "watch", "blocked")


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module("polymarket_alpha_lab.paper_research_packet_quality_history")


def _config(**overrides):
    values = {
        "config_version": "paper-research-packet-quality-history-v0",
        "min_report_count": 3,
        "max_blocked_quality_report_count": 0,
        "max_watch_quality_report_count": 0,
        "max_duplicate_generated_at_count": 0,
        "max_recurring_reason_code_report_count": 1,
    }
    values.update(overrides)
    return _api().PaperResearchPacketQualityHistoryConfig(**values)


def _check_rows(
    quality_status: str,
    *,
    reason_code: str | None = None,
) -> tuple[PaperResearchPacketQualityCheckRow, ...]:
    source_reason = "source_freshness_passed"
    population_reason = "packet_population_passed"
    skip_reason = "skip_pressure_passed"
    source_status = "pass"
    population_status = "pass"
    skip_status = "pass"

    if quality_status == "blocked":
        population_status = "blocked"
        population_reason = reason_code or "included_count_below_minimum"
    elif quality_status == "watch":
        skip_status = "watch"
        skip_reason = reason_code or "skipped_share_above_threshold"

    return (
        PaperResearchPacketQualityCheckRow(
            check_name="source_freshness",
            status=source_status,
            observed_value=120,
            threshold=21_600,
            reason_codes=(source_reason,),
        ),
        PaperResearchPacketQualityCheckRow(
            check_name="packet_population",
            status=population_status,
            observed_value=1,
            threshold=1,
            reason_codes=(population_reason,),
        ),
        PaperResearchPacketQualityCheckRow(
            check_name="skip_pressure",
            status=skip_status,
            observed_value=d("0.000000"),
            threshold=d("0.500000"),
            reason_codes=(skip_reason,),
        ),
    )


def _reason_code_counts(
    check_rows: tuple[PaperResearchPacketQualityCheckRow, ...],
) -> tuple[PaperResearchPacketQualityReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in check_rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        PaperResearchPacketQualityReasonCodeCount(reason_code, count)
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _quality_report(
    *,
    generated_at: datetime = SOURCE_AT,
    quality_status: str = "pass",
    reason_code: str | None = None,
    source_age_seconds: int = 120,
) -> PaperResearchPacketQualityReport:
    check_rows = _check_rows(quality_status, reason_code=reason_code)
    return PaperResearchPacketQualityReport(
        generated_at=generated_at,
        config_version="paper-research-packet-quality-v0",
        source_generated_at=generated_at - timedelta(seconds=source_age_seconds),
        source_config_version="paper-research-packet-v0",
        input_row_count=1,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        source_age_seconds=source_age_seconds,
        included_share=d("1.000000"),
        skipped_share=d("0.000000"),
        check_count=len(check_rows),
        pass_count=sum(1 for row in check_rows if row.status == "pass"),
        watch_count=sum(1 for row in check_rows if row.status == "watch"),
        blocked_count=sum(1 for row in check_rows if row.status == "blocked"),
        quality_status=quality_status,
        check_rows=check_rows,
        reason_code_counts=_reason_code_counts(check_rows),
    )


def _history(*reports: PaperResearchPacketQualityReport, **config_overrides):
    return _api().build_paper_research_packet_quality_history_report(
        reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_packet_quality_history_empty_and_insufficient_reports_are_blocked():
    api = _api()

    empty = _history()

    assert isinstance(empty, api.PaperResearchPacketQualityHistoryReport)
    assert empty.generated_at == GENERATED_AT
    assert empty.config_version == "paper-research-packet-quality-history-v0"
    assert empty.history_status == "blocked"
    assert empty.source_report_count == 0
    assert empty.first_source_generated_at is None
    assert empty.latest_source_generated_at is None
    assert empty.latest_quality_status is None
    assert empty.latest_source_age_seconds is None
    assert empty.latest_included_share is None
    assert empty.latest_skipped_share is None
    assert empty.latest_check_rows == ()
    assert empty.quality_status_rows == tuple(
        api.PaperResearchPacketQualityHistoryStatusRow(status, 0)
        for status in QUALITY_STATUSES
    )
    assert empty.duplicate_generated_at_count == 0
    assert empty.recurring_reason_code_rows == ()
    assert empty.reason_codes == ("insufficient_paper_research_packet_quality_history",)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    insufficient = _history(_quality_report())

    assert insufficient.history_status == "blocked"
    assert insufficient.source_report_count == 1
    assert insufficient.first_source_generated_at == SOURCE_AT
    assert insufficient.latest_source_generated_at == SOURCE_AT
    assert insufficient.latest_quality_status == "pass"
    assert insufficient.latest_source_age_seconds == 120
    assert insufficient.latest_included_share == d("1.000000")
    assert insufficient.latest_skipped_share == d("0.000000")
    assert insufficient.reason_codes == ("insufficient_paper_research_packet_quality_history",)


def test_packet_quality_history_passes_and_sorts_chronologically_with_latest_summary():
    api = _api()
    latest = _quality_report(
        generated_at=SOURCE_AT + timedelta(hours=2),
        source_age_seconds=600,
    )
    first = _quality_report(generated_at=SOURCE_AT)
    middle = _quality_report(generated_at=SOURCE_AT + timedelta(hours=1))

    history = _history(latest, first, middle)

    assert history.history_status == "pass"
    assert history.source_report_count == 3
    assert history.first_source_generated_at == first.generated_at
    assert history.latest_source_generated_at == latest.generated_at
    assert history.latest_quality_status == "pass"
    assert history.latest_source_age_seconds == 600
    assert history.latest_included_share == d("1.000000")
    assert history.latest_skipped_share == d("0.000000")
    assert history.latest_check_rows == (
        api.PaperResearchPacketQualityHistoryCheckSummaryRow(
            "source_freshness",
            "pass",
            ("source_freshness_passed",),
        ),
        api.PaperResearchPacketQualityHistoryCheckSummaryRow(
            "packet_population",
            "pass",
            ("packet_population_passed",),
        ),
        api.PaperResearchPacketQualityHistoryCheckSummaryRow(
            "skip_pressure",
            "pass",
            ("skip_pressure_passed",),
        ),
    )
    assert history.quality_status_rows == (
        api.PaperResearchPacketQualityHistoryStatusRow("pass", 3),
        api.PaperResearchPacketQualityHistoryStatusRow("watch", 0),
        api.PaperResearchPacketQualityHistoryStatusRow("blocked", 0),
    )
    assert history.duplicate_generated_at_count == 0
    assert history.recurring_reason_code_rows == ()
    assert history.reason_codes == ("paper_research_packet_quality_history_passed",)


def test_packet_quality_history_status_precedence_blocks_over_watch():
    history = _history(
        _quality_report(generated_at=SOURCE_AT),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=1),
            quality_status="watch",
        ),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=2),
            quality_status="blocked",
        ),
    )

    assert history.history_status == "blocked"
    assert history.latest_quality_status == "blocked"
    assert history.quality_status_rows == (
        _api().PaperResearchPacketQualityHistoryStatusRow("pass", 1),
        _api().PaperResearchPacketQualityHistoryStatusRow("watch", 1),
        _api().PaperResearchPacketQualityHistoryStatusRow("blocked", 1),
    )
    assert history.reason_codes == (
        "blocked_quality_report_threshold_exceeded",
        "watch_quality_report_threshold_exceeded",
    )


def test_packet_quality_history_watches_duplicate_generated_at_with_stable_bounds():
    generated_at = SOURCE_AT + timedelta(hours=1)

    history = _history(
        _quality_report(generated_at=SOURCE_AT),
        _quality_report(generated_at=generated_at),
        _quality_report(generated_at=generated_at),
    )

    assert history.history_status == "watch"
    assert history.first_source_generated_at == SOURCE_AT
    assert history.latest_source_generated_at == generated_at
    assert history.duplicate_generated_at_count == 1
    assert history.reason_codes == ("duplicate_generated_at_threshold_exceeded",)


def test_packet_quality_history_keeps_recurring_reasons_when_duplicate_timestamps_exist():
    generated_at = SOURCE_AT + timedelta(hours=1)

    history = _history(
        _quality_report(generated_at=SOURCE_AT),
        _quality_report(
            generated_at=generated_at,
            quality_status="watch",
            reason_code="skipped_share_above_threshold",
        ),
        _quality_report(
            generated_at=generated_at,
            quality_status="watch",
            reason_code="skipped_share_above_threshold",
        ),
        max_watch_quality_report_count=2,
    )

    assert history.history_status == "watch"
    assert history.duplicate_generated_at_count == 1
    assert history.recurring_reason_code_rows == (
        _api().PaperResearchPacketQualityHistoryRecurringReasonCodeRow(
            "watch",
            "skipped_share_above_threshold",
            2,
        ),
    )
    assert history.reason_codes == (
        "duplicate_generated_at_threshold_exceeded",
        "recurring_watch_reason_codes_present",
    )


def test_packet_quality_history_watches_recurring_blocked_and_watch_reason_codes():
    api = _api()

    history = _history(
        _quality_report(
            generated_at=SOURCE_AT,
            quality_status="watch",
            reason_code="skipped_share_above_threshold",
        ),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=1),
            quality_status="blocked",
            reason_code="included_count_below_minimum",
        ),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=2),
            quality_status="watch",
            reason_code="skipped_share_above_threshold",
        ),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=3),
            quality_status="blocked",
            reason_code="included_count_below_minimum",
        ),
        min_report_count=4,
        max_blocked_quality_report_count=2,
        max_watch_quality_report_count=2,
    )

    assert history.history_status == "watch"
    assert history.recurring_reason_code_rows == (
        api.PaperResearchPacketQualityHistoryRecurringReasonCodeRow(
            "blocked",
            "included_count_below_minimum",
            2,
        ),
        api.PaperResearchPacketQualityHistoryRecurringReasonCodeRow(
            "watch",
            "skipped_share_above_threshold",
            2,
        ),
    )
    assert history.reason_codes == (
        "recurring_blocked_reason_codes_present",
        "recurring_watch_reason_codes_present",
    )


def test_packet_quality_history_reason_codes_are_deterministically_ordered():
    history = _history(
        _quality_report(generated_at=SOURCE_AT),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=1),
            quality_status="blocked",
            reason_code="packet_rows_missing",
        ),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=1),
            quality_status="watch",
            reason_code="source_report_stale",
        ),
        _quality_report(
            generated_at=SOURCE_AT + timedelta(hours=2),
            quality_status="watch",
            reason_code="source_report_stale",
        ),
        max_blocked_quality_report_count=1,
        max_watch_quality_report_count=1,
    )

    assert history.history_status == "watch"
    assert history.reason_codes == (
        "duplicate_generated_at_threshold_exceeded",
        "recurring_watch_reason_codes_present",
        "watch_quality_report_threshold_exceeded",
    )


def test_packet_quality_history_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    history = _history(
        _quality_report(generated_at=SOURCE_AT),
        _quality_report(generated_at=SOURCE_AT + timedelta(hours=1)),
        _quality_report(generated_at=SOURCE_AT + timedelta(hours=2)),
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
        history.quality_status_rows[0].status_count = 99  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        history.latest_check_rows[0].status = "blocked"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        api.PaperResearchPacketQualityHistoryConfig(paper_only=False)
    with pytest.raises(ValueError, match="status_count"):
        api.PaperResearchPacketQualityHistoryStatusRow("pass", -1)
    with pytest.raises(ValueError, match="report_only"):
        api.PaperResearchPacketQualityHistoryCheckSummaryRow(
            "source_freshness",
            "pass",
            ("source_freshness_passed",),
            report_only=False,
        )
    with pytest.raises(ValueError, match="check_status"):
        api.PaperResearchPacketQualityHistoryRecurringReasonCodeRow("pass", "reason", 1)

    bad_flags_report = _quality_report()
    object.__setattr__(bad_flags_report, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        _history(bad_flags_report)


def test_packet_quality_history_rejects_invalid_inputs_and_exact_type():
    api = _api()
    report = _quality_report()

    class ReportSubclass(PaperResearchPacketQualityReport):
        pass

    class ConfigSubclass(api.PaperResearchPacketQualityHistoryConfig):
        pass

    report_subclass = ReportSubclass(
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_generated_at=report.source_generated_at,
        source_config_version=report.source_config_version,
        input_row_count=report.input_row_count,
        packet_row_count=report.packet_row_count,
        included_count=report.included_count,
        skipped_count=report.skipped_count,
        high_priority_count=report.high_priority_count,
        medium_priority_count=report.medium_priority_count,
        low_priority_count=report.low_priority_count,
        source_age_seconds=report.source_age_seconds,
        included_share=report.included_share,
        skipped_share=report.skipped_share,
        check_count=report.check_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        quality_status=report.quality_status,
        check_rows=report.check_rows,
        reason_code_counts=report.reason_code_counts,
    )

    for reports in (object(), "reports", b"reports", {"report": report}):
        with pytest.raises(ValueError, match="quality_reports must be a list or tuple"):
            api.build_paper_research_packet_quality_history_report(
                reports,
                config=_config(),
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="quality_reports must contain"):
        api.build_paper_research_packet_quality_history_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="quality_reports must contain"):
        api.build_paper_research_packet_quality_history_report(
            (report_subclass,),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_research_packet_quality_history_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_research_packet_quality_history_report(
            (),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_paper_research_packet_quality_history_report(
            (),
            config=_config(),
            generated_at=object(),
        )
    with pytest.raises(ValueError, match="generated_at"):
        api.build_paper_research_packet_quality_history_report(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 6, 23, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="min_report_count"):
        api.PaperResearchPacketQualityHistoryConfig(min_report_count=True)
    with pytest.raises(ValueError, match="max_watch_quality_report_count"):
        api.PaperResearchPacketQualityHistoryConfig(max_watch_quality_report_count=-1)


def test_packet_quality_history_validation_does_not_mutate_source_reports():
    offset_at = datetime(2026, 6, 23, 8, 0, tzinfo=timezone(timedelta(hours=-4)))
    report = _quality_report()
    object.__setattr__(report, "generated_at", offset_at)
    object.__setattr__(
        report,
        "source_generated_at",
        offset_at - timedelta(seconds=report.source_age_seconds),
    )
    original_generated_at = report.generated_at
    original_source_generated_at = report.source_generated_at

    _history(report, _quality_report(), _quality_report(generated_at=SOURCE_AT + timedelta(hours=2)))

    assert report.generated_at is original_generated_at
    assert report.source_generated_at is original_source_generated_at
