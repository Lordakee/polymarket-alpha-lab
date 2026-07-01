from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import inspect

import pytest

from polymarket_alpha_lab.paper_research_packet_quality_history import (
    PaperResearchPacketQualityHistoryCheckSummaryRow,
    PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
    PaperResearchPacketQualityHistoryReport,
    PaperResearchPacketQualityHistoryStatusRow,
)


GENERATED_AT = datetime(2026, 6, 23, 18, 0, tzinfo=UTC)
LATEST_HISTORY_AT = datetime(2026, 6, 23, 17, 30, tzinfo=UTC)
QUALITY_STATUSES = ("pass", "watch", "blocked")


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_research_packet_quality_history_trend",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-research-packet-quality-history-trend-v0",
        "min_history_report_count": 3,
        "max_latest_history_age_seconds": 86_400,
        "max_blocked_history_report_count": 0,
        "max_watch_history_report_count": 0,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
        "max_recurring_reason_code_history_report_count": 1,
    }
    values.update(overrides)
    return _api().PaperResearchPacketQualityHistoryTrendConfig(**values)


def _latest_check_rows(
    quality_status: str,
) -> tuple[PaperResearchPacketQualityHistoryCheckSummaryRow, ...]:
    source_status = "pass"
    source_reason = "source_freshness_passed"
    population_status = "pass"
    population_reason = "packet_population_passed"
    skip_status = "pass"
    skip_reason = "skip_pressure_passed"

    if quality_status == "blocked":
        population_status = "blocked"
        population_reason = "included_count_below_minimum"
    elif quality_status == "watch":
        skip_status = "watch"
        skip_reason = "skipped_share_above_threshold"

    return (
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            "source_freshness",
            source_status,
            (source_reason,),
        ),
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            "packet_population",
            population_status,
            (population_reason,),
        ),
        PaperResearchPacketQualityHistoryCheckSummaryRow(
            "skip_pressure",
            skip_status,
            (skip_reason,),
        ),
    )


def _quality_status_rows(
    *,
    source_report_count: int,
    latest_quality_status: str | None,
) -> tuple[PaperResearchPacketQualityHistoryStatusRow, ...]:
    counts = {"pass": source_report_count, "watch": 0, "blocked": 0}
    if source_report_count > 0 and latest_quality_status in ("watch", "blocked"):
        counts["pass"] = source_report_count - 1
        counts[latest_quality_status] = 1
    return tuple(
        PaperResearchPacketQualityHistoryStatusRow(status, counts[status])
        for status in QUALITY_STATUSES
    )


def _history_reason(history_status: str) -> tuple[str, ...]:
    if history_status == "blocked":
        return ("blocked_quality_report_threshold_exceeded",)
    if history_status == "watch":
        return ("watch_quality_report_threshold_exceeded",)
    return ("paper_research_packet_quality_history_passed",)


def _history_report(
    *,
    generated_at: datetime = LATEST_HISTORY_AT,
    history_status: str = "pass",
    source_report_count: int = 3,
    latest_quality_status: str | None = "pass",
    duplicate_generated_at_count: int = 0,
    recurring_reason_code_rows: tuple[
        PaperResearchPacketQualityHistoryRecurringReasonCodeRow,
        ...,
    ] = (),
    reason_codes: tuple[str, ...] | None = None,
) -> PaperResearchPacketQualityHistoryReport:
    if source_report_count == 0:
        return PaperResearchPacketQualityHistoryReport(
            generated_at=generated_at,
            config_version="paper-research-packet-quality-history-v0",
            history_status=history_status,
            source_report_count=0,
            first_source_generated_at=None,
            latest_source_generated_at=None,
            latest_quality_status=None,
            latest_source_age_seconds=None,
            latest_included_share=None,
            latest_skipped_share=None,
            latest_check_rows=(),
            quality_status_rows=_quality_status_rows(
                source_report_count=0,
                latest_quality_status=None,
            ),
            duplicate_generated_at_count=0,
            recurring_reason_code_rows=(),
            reason_codes=reason_codes
            if reason_codes is not None
            else ("insufficient_paper_research_packet_quality_history",),
        )

    if latest_quality_status is None:
        raise AssertionError("latest_quality_status is required for nonempty test reports")
    return PaperResearchPacketQualityHistoryReport(
        generated_at=generated_at,
        config_version="paper-research-packet-quality-history-v0",
        history_status=history_status,
        source_report_count=source_report_count,
        first_source_generated_at=generated_at - timedelta(hours=3),
        latest_source_generated_at=generated_at - timedelta(minutes=5),
        latest_quality_status=latest_quality_status,
        latest_source_age_seconds=300,
        latest_included_share=d("1.000000"),
        latest_skipped_share=d("0.000000"),
        latest_check_rows=_latest_check_rows(latest_quality_status),
        quality_status_rows=_quality_status_rows(
            source_report_count=source_report_count,
            latest_quality_status=latest_quality_status,
        ),
        duplicate_generated_at_count=duplicate_generated_at_count,
        recurring_reason_code_rows=recurring_reason_code_rows,
        reason_codes=reason_codes if reason_codes is not None else _history_reason(history_status),
    )


def _trend(*history_reports: PaperResearchPacketQualityHistoryReport, **config_overrides):
    return _api().build_paper_research_packet_quality_history_trend_report(
        history_reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _history_subclass(
    report: PaperResearchPacketQualityHistoryReport,
) -> PaperResearchPacketQualityHistoryReport:
    class HistoryReportSubclass(PaperResearchPacketQualityHistoryReport):
        pass

    subclass_report = HistoryReportSubclass.__new__(HistoryReportSubclass)
    for field_name, value in report.__dict__.items():
        object.__setattr__(subclass_report, field_name, value)
    return subclass_report


def test_quality_history_trend_stable_chronological_summary():
    api = _api()
    latest = _history_report(generated_at=LATEST_HISTORY_AT)
    first = _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=2))
    middle = _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=1))

    report = _trend(latest, first, middle)

    assert type(report) is api.PaperResearchPacketQualityHistoryTrendReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-research-packet-quality-history-trend-v0"
    assert report.trend_status == "stable"
    assert report.source_history_report_count == 3
    assert report.first_history_generated_at == first.generated_at
    assert report.latest_history_generated_at == latest.generated_at
    assert report.latest_history_age_seconds == 1_800
    assert report.latest_history_status == "pass"
    assert report.latest_quality_status == "pass"
    assert report.history_status_rows == (
        api.PaperResearchPacketQualityHistoryTrendStatusRow("pass", 3),
        api.PaperResearchPacketQualityHistoryTrendStatusRow("watch", 0),
        api.PaperResearchPacketQualityHistoryTrendStatusRow("blocked", 0),
    )
    assert report.duplicate_generated_at_count == 0
    assert report.consecutive_latest_pass_count == 3
    assert report.consecutive_latest_watch_count == 0
    assert report.consecutive_latest_blocked_count == 0
    assert report.latest_reason_codes == (
        "paper_research_packet_quality_history_passed",
    )
    assert report.recurring_reason_code_rows == ()
    assert report.reason_codes == (
        "paper_research_packet_quality_history_trend_stable",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_quality_history_trend_blocks_missing_and_latest_blocked_failures():
    missing = _trend()

    assert missing.trend_status == "blocked"
    assert missing.source_history_report_count == 0
    assert missing.latest_history_generated_at is None
    assert missing.latest_history_age_seconds is None
    assert missing.reason_codes == (
        "insufficient_paper_research_packet_quality_history_trend",
        "missing_latest_quality_history_report",
    )

    blocked = _trend(
        _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=2)),
        _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=1)),
        _history_report(
            generated_at=LATEST_HISTORY_AT,
            history_status="blocked",
            latest_quality_status="blocked",
        ),
    )

    assert blocked.trend_status == "blocked"
    assert blocked.consecutive_latest_blocked_count == 1
    assert blocked.reason_codes == (
        "blocked_quality_history_report_threshold_exceeded",
        "consecutive_quality_history_blocked_threshold_exceeded",
        "latest_quality_blocked",
        "latest_quality_history_blocked",
    )


def test_quality_history_trend_watches_stale_duplicates_and_recurring_watch_reasons():
    stale_latest_at = GENERATED_AT - timedelta(seconds=86_401)
    recurring = (
        PaperResearchPacketQualityHistoryRecurringReasonCodeRow(
            "watch",
            "skipped_share_above_threshold",
            2,
        ),
    )

    report = _trend(
        _history_report(
            generated_at=stale_latest_at - timedelta(hours=1),
            recurring_reason_code_rows=recurring,
        ),
        _history_report(
            generated_at=stale_latest_at,
            history_status="watch",
            latest_quality_status="watch",
            recurring_reason_code_rows=recurring,
        ),
        _history_report(
            generated_at=stale_latest_at,
            history_status="watch",
            latest_quality_status="watch",
            recurring_reason_code_rows=recurring,
        ),
        max_watch_history_report_count=2,
        max_consecutive_latest_watch_count=2,
    )

    assert report.trend_status == "watch"
    assert report.latest_history_age_seconds == 86_401
    assert report.duplicate_generated_at_count == 1
    assert report.recurring_reason_code_rows == (
        _api().PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow(
            "watch",
            "skipped_share_above_threshold",
            3,
        ),
    )
    assert report.reason_codes == (
        "duplicate_quality_history_generated_at_threshold_exceeded",
        "latest_quality_history_watch",
        "latest_quality_watch",
        "recurring_watch_quality_reason_codes_present",
        "stale_quality_history_trend",
    )


def test_quality_history_trend_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    report = _trend(
        _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=2)),
        _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=1)),
        _history_report(generated_at=LATEST_HISTORY_AT),
    )

    with pytest.raises(FrozenInstanceError):
        report.trend_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.history_status_rows[0].status_count = 99  # type: ignore[misc]

    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="status row must be report_only"):
        replace(report.history_status_rows[0], report_only=False)
    with pytest.raises(ValueError, match="recurring reason row must be readonly"):
        replace(
            api.PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow(
                "watch",
                "skipped_share_above_threshold",
                2,
            ),
            readonly=False,
        )
    with pytest.raises(ValueError, match="trend report must be readonly"):
        replace(report, readonly=False)


def test_quality_history_trend_rejects_invalid_inputs_exact_types_and_corruption():
    api = _api()
    source = _history_report()

    class ConfigSubclass(api.PaperResearchPacketQualityHistoryTrendConfig):
        pass

    for value in (object(), "reports", b"reports", {"report": source}):
        with pytest.raises(ValueError, match="history_reports must be a list or tuple"):
            api.build_paper_research_packet_quality_history_trend_report(
                value,
                config=_config(),
                generated_at=GENERATED_AT,
            )
    with pytest.raises(ValueError, match="history_reports must contain"):
        api.build_paper_research_packet_quality_history_trend_report(
            (object(),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="history_reports must contain"):
        api.build_paper_research_packet_quality_history_trend_report(
            (_history_subclass(source),),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_research_packet_quality_history_trend_report(
            (),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_research_packet_quality_history_trend_report(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 6, 23, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="max_watch_history_report_count"):
        api.PaperResearchPacketQualityHistoryTrendConfig(
            max_watch_history_report_count=-1,
        )
    with pytest.raises(ValueError, match="max_latest_history_age_seconds"):
        api.PaperResearchPacketQualityHistoryTrendConfig(
            max_latest_history_age_seconds=True,
        )
    with pytest.raises(ValueError, match="trend_status"):
        replace(
            _trend(
                _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=2)),
                _history_report(generated_at=LATEST_HISTORY_AT - timedelta(hours=1)),
                source,
            ),
            trend_status="pass",
        )


def test_quality_history_trend_normalizes_aware_datetimes_without_mutating_sources():
    offset = timezone(timedelta(hours=-4))
    source = _history_report(
        generated_at=datetime(2026, 6, 23, 13, 30, tzinfo=offset),
    )
    original_generated_at = source.generated_at

    report = _api().build_paper_research_packet_quality_history_trend_report(
        (
            source,
            _history_report(),
            _history_report(generated_at=LATEST_HISTORY_AT + timedelta(minutes=15)),
        ),
        config=_config(),
        generated_at=datetime(2026, 6, 23, 14, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.first_history_generated_at == LATEST_HISTORY_AT
    assert source.generated_at is original_generated_at


def test_quality_history_trend_module_is_pure_paper_report_only_readonly():
    source = inspect.getsource(_api()).lower()

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "polymarketpublicclient",
        "requests",
        "httpx",
        "private_key",
        "wallet",
        "open(",
        ".write(",
    ):
        assert banned not in source
