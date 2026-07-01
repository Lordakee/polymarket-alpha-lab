from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import import_module
import inspect

import pytest

from polymarket_alpha_lab.paper_research_packet_quality_history_trend import (
    PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow,
    PaperResearchPacketQualityHistoryTrendReport,
    PaperResearchPacketQualityHistoryTrendStatusRow,
)


GENERATED_AT = datetime(2026, 6, 23, 18, 0, tzinfo=UTC)
TREND_GENERATED_AT = datetime(2026, 6, 23, 17, 45, tzinfo=UTC)
LATEST_HISTORY_AT = datetime(2026, 6, 23, 17, 30, tzinfo=UTC)
QUALITY_STATUSES = ("pass", "watch", "blocked")


class _DatetimeSubclass(datetime):
    pass


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_research_packet_quality_history_trend_gate",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-research-packet-quality-history-trend-gate-v0",
        "min_history_report_count": 3,
        "max_latest_history_age_seconds": 86_400,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
    }
    values.update(overrides)
    return _api().PaperResearchPacketQualityHistoryTrendGateConfig(**values)


def _latest_age_seconds(
    generated_at: datetime,
    latest_history_generated_at: datetime | None,
) -> int | None:
    if latest_history_generated_at is None:
        return None
    return int((generated_at - latest_history_generated_at).total_seconds())


def _status_rows(
    *,
    source_history_report_count: int,
    latest_history_status: str | None,
    consecutive_latest_watch_count: int,
    consecutive_latest_blocked_count: int,
) -> tuple[PaperResearchPacketQualityHistoryTrendStatusRow, ...]:
    counts = {"pass": source_history_report_count, "watch": 0, "blocked": 0}
    if latest_history_status == "watch":
        counts["pass"] = source_history_report_count - consecutive_latest_watch_count
        counts["watch"] = consecutive_latest_watch_count
    elif latest_history_status == "blocked":
        counts["pass"] = source_history_report_count - consecutive_latest_blocked_count
        counts["blocked"] = consecutive_latest_blocked_count
    return tuple(
        PaperResearchPacketQualityHistoryTrendStatusRow(status, counts[status])
        for status in QUALITY_STATUSES
    )


def _trend_reason(trend_status: str) -> tuple[str, ...]:
    if trend_status == "blocked":
        return ("latest_quality_history_blocked",)
    if trend_status == "watch":
        return ("latest_quality_history_watch",)
    return ("paper_research_packet_quality_history_trend_stable",)


def _trend_report(
    *,
    generated_at: datetime = TREND_GENERATED_AT,
    trend_status: str = "stable",
    source_history_report_count: int = 3,
    latest_history_generated_at: datetime | None = LATEST_HISTORY_AT,
    latest_history_status: str | None = "pass",
    latest_quality_status: str | None = "pass",
    duplicate_generated_at_count: int = 0,
    consecutive_latest_pass_count: int = 3,
    consecutive_latest_watch_count: int = 0,
    consecutive_latest_blocked_count: int = 0,
    reason_codes: tuple[str, ...] | None = None,
) -> PaperResearchPacketQualityHistoryTrendReport:
    if source_history_report_count == 0:
        return PaperResearchPacketQualityHistoryTrendReport(
            generated_at=generated_at,
            config_version="paper-research-packet-quality-history-trend-v0",
            trend_status="blocked",
            source_history_report_count=0,
            first_history_generated_at=None,
            latest_history_generated_at=None,
            latest_history_age_seconds=None,
            latest_history_status=None,
            latest_quality_status=None,
            history_status_rows=_status_rows(
                source_history_report_count=0,
                latest_history_status=None,
                consecutive_latest_watch_count=0,
                consecutive_latest_blocked_count=0,
            ),
            duplicate_generated_at_count=0,
            consecutive_latest_pass_count=0,
            consecutive_latest_watch_count=0,
            consecutive_latest_blocked_count=0,
            latest_reason_codes=(),
            recurring_reason_code_rows=(),
            reason_codes=reason_codes
            if reason_codes is not None
            else (
                "insufficient_paper_research_packet_quality_history_trend",
                "missing_latest_quality_history_report",
            ),
        )

    if latest_history_generated_at is None:
        raise AssertionError("latest_history_generated_at is required for nonempty trends")
    if latest_history_status is None or latest_quality_status is None:
        raise AssertionError("latest status fields are required for nonempty trends")
    return PaperResearchPacketQualityHistoryTrendReport(
        generated_at=generated_at,
        config_version="paper-research-packet-quality-history-trend-v0",
        trend_status=trend_status,
        source_history_report_count=source_history_report_count,
        first_history_generated_at=latest_history_generated_at - timedelta(hours=2),
        latest_history_generated_at=latest_history_generated_at,
        latest_history_age_seconds=_latest_age_seconds(
            generated_at,
            latest_history_generated_at,
        ),
        latest_history_status=latest_history_status,
        latest_quality_status=latest_quality_status,
        history_status_rows=_status_rows(
            source_history_report_count=source_history_report_count,
            latest_history_status=latest_history_status,
            consecutive_latest_watch_count=consecutive_latest_watch_count,
            consecutive_latest_blocked_count=consecutive_latest_blocked_count,
        ),
        duplicate_generated_at_count=duplicate_generated_at_count,
        consecutive_latest_pass_count=consecutive_latest_pass_count,
        consecutive_latest_watch_count=consecutive_latest_watch_count,
        consecutive_latest_blocked_count=consecutive_latest_blocked_count,
        latest_reason_codes=_trend_reason(trend_status),
        recurring_reason_code_rows=(),
        reason_codes=reason_codes if reason_codes is not None else _trend_reason(trend_status),
    )


def _gate_report(
    trend_report: PaperResearchPacketQualityHistoryTrendReport,
    **config_overrides,
):
    return _api().build_paper_research_packet_quality_history_trend_gate_report(
        trend_report,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _trend_subclass(
    report: PaperResearchPacketQualityHistoryTrendReport,
) -> PaperResearchPacketQualityHistoryTrendReport:
    class TrendReportSubclass(PaperResearchPacketQualityHistoryTrendReport):
        pass

    subclass_report = TrendReportSubclass.__new__(TrendReportSubclass)
    for field_name, value in report.__dict__.items():
        object.__setattr__(subclass_report, field_name, value)
    return subclass_report


def _corrupted_trend_report(
    report: PaperResearchPacketQualityHistoryTrendReport,
    **overrides,
) -> PaperResearchPacketQualityHistoryTrendReport:
    corrupted = PaperResearchPacketQualityHistoryTrendReport.__new__(
        PaperResearchPacketQualityHistoryTrendReport,
    )
    for field_name, value in report.__dict__.items():
        object.__setattr__(corrupted, field_name, overrides.get(field_name, value))
    return corrupted


def test_quality_history_trend_gate_passes_stable_recent_trend():
    api = _api()
    source = _trend_report()

    report = _gate_report(source)

    assert type(report) is api.PaperResearchPacketQualityHistoryTrendGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-research-packet-quality-history-trend-gate-v0"
    assert report.source_config_version == "paper-research-packet-quality-history-trend-v0"
    assert report.source_generated_at == TREND_GENERATED_AT
    assert report.gate_status == "pass"
    assert report.recommended_next_step == "allow_paper_research_packet_quality_history_trend"
    assert report.source_trend_status == "stable"
    assert report.source_history_report_count == 3
    assert report.latest_history_generated_at == LATEST_HISTORY_AT
    assert report.latest_history_age_seconds == 1_800
    assert report.latest_history_status == "pass"
    assert report.latest_quality_status == "pass"
    assert report.duplicate_generated_at_count == 0
    assert report.consecutive_latest_pass_count == 3
    assert report.consecutive_latest_watch_count == 0
    assert report.consecutive_latest_blocked_count == 0
    assert report.reason_code_counts == (
        api.PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            "paper_research_packet_quality_history_trend_gate_passed",
            1,
        ),
    )
    assert report.reason_codes == (
        "paper_research_packet_quality_history_trend_gate_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _trend_report(trend_status="blocked"),
            "source_quality_history_trend_blocked",
        ),
        (
            _trend_report(source_history_report_count=2, consecutive_latest_pass_count=2),
            "insufficient_quality_history_trend",
        ),
        (
            _trend_report(
                trend_status="blocked",
                latest_history_status="blocked",
                latest_quality_status="blocked",
                consecutive_latest_pass_count=0,
                consecutive_latest_blocked_count=1,
            ),
            "latest_quality_blocked",
        ),
    ),
)
def test_quality_history_trend_gate_blocks_for_blocked_inputs(
    source: PaperResearchPacketQualityHistoryTrendReport,
    expected_reason: str,
):
    report = _gate_report(source)

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == "block_paper_research_packet_quality_history_trend"
    assert expected_reason in report.reason_codes
    assert "paper_research_packet_quality_history_trend_gate_passed" not in report.reason_codes


@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _trend_report(trend_status="watch"),
            "source_quality_history_trend_watch",
        ),
        (
            _trend_report(
                trend_status="watch",
                latest_history_status="watch",
                latest_quality_status="watch",
                consecutive_latest_pass_count=0,
                consecutive_latest_watch_count=1,
            ),
            "latest_quality_watch",
        ),
        (
            _trend_report(duplicate_generated_at_count=1),
            "duplicate_quality_history_generated_at_threshold_exceeded",
        ),
    ),
)
def test_quality_history_trend_gate_watches_for_watch_inputs(
    source: PaperResearchPacketQualityHistoryTrendReport,
    expected_reason: str,
):
    report = _gate_report(source)

    assert report.gate_status == "watch"
    assert report.recommended_next_step == "review_paper_research_packet_quality_history_trend"
    assert expected_reason in report.reason_codes
    assert "paper_research_packet_quality_history_trend_gate_passed" not in report.reason_codes


def test_quality_history_trend_gate_watches_stale_latest_history_timestamp():
    source = _trend_report(
        latest_history_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )

    report = _gate_report(source)

    assert report.gate_status == "watch"
    assert report.latest_history_age_seconds == 86_401
    assert report.reason_codes == ("stale_quality_history_trend",)


def test_quality_history_trend_gate_missing_latest_timestamp_blocks():
    source = _trend_report(source_history_report_count=0)

    report = _gate_report(source, min_history_report_count=0)

    assert report.gate_status == "blocked"
    assert report.latest_history_generated_at is None
    assert report.latest_history_age_seconds is None
    assert "missing_latest_quality_history_trend_timestamp" in report.reason_codes


def test_quality_history_trend_gate_enforces_consecutive_thresholds():
    watch_source = _trend_report(
        trend_status="watch",
        latest_history_status="watch",
        latest_quality_status="watch",
        consecutive_latest_pass_count=0,
        consecutive_latest_watch_count=2,
    )
    blocked_source = _trend_report(
        trend_status="blocked",
        latest_history_status="blocked",
        latest_quality_status="blocked",
        consecutive_latest_pass_count=0,
        consecutive_latest_blocked_count=2,
    )

    watch_report = _gate_report(watch_source, max_consecutive_latest_watch_count=1)
    blocked_report = _gate_report(
        blocked_source,
        max_consecutive_latest_blocked_count=1,
    )

    assert watch_report.gate_status == "watch"
    assert "latest_quality_history_watch" in watch_report.reason_codes
    assert "latest_quality_watch" in watch_report.reason_codes
    assert "consecutive_quality_history_watch_threshold_exceeded" in watch_report.reason_codes
    assert blocked_report.gate_status == "blocked"
    assert "latest_quality_history_blocked" in blocked_report.reason_codes
    assert "latest_quality_blocked" in blocked_report.reason_codes
    assert "consecutive_quality_history_blocked_threshold_exceeded" in blocked_report.reason_codes


def test_quality_history_trend_gate_reason_code_counts_are_deterministic_and_positive():
    source = _trend_report(
        trend_status="blocked",
        source_history_report_count=2,
        latest_history_status="blocked",
        latest_quality_status="blocked",
        duplicate_generated_at_count=1,
        consecutive_latest_pass_count=0,
        consecutive_latest_blocked_count=2,
    )

    report = _gate_report(source, max_consecutive_latest_blocked_count=1)

    assert report.gate_status == "blocked"
    assert report.reason_code_counts == (
        _api().PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            "consecutive_quality_history_blocked_threshold_exceeded",
            1,
        ),
        _api().PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            "duplicate_quality_history_generated_at_threshold_exceeded",
            1,
        ),
        _api().PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            "insufficient_quality_history_trend",
            1,
        ),
        _api().PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            "latest_quality_blocked",
            1,
        ),
        _api().PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            "latest_quality_history_blocked",
            1,
        ),
        _api().PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
            "source_quality_history_trend_blocked",
            1,
        ),
    )
    assert report.reason_codes == tuple(row.reason_code for row in report.reason_code_counts)
    assert all(row.report_count > 0 for row in report.reason_code_counts)


def test_quality_history_trend_gate_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    source = _trend_report()
    config = _config()
    reason_count = api.PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
        "paper_research_packet_quality_history_trend_gate_passed",
        1,
    )
    report = _gate_report(source)

    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_count.report_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.gate_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="reason code count must be report_only"):
        replace(reason_count, report_only=False)
    with pytest.raises(ValueError, match="gate report must be readonly"):
        replace(report, readonly=False)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"config_version": ""}, "config_version"),
        ({"min_history_report_count": -1}, "min_history_report_count"),
        ({"max_latest_history_age_seconds": -1}, "max_latest_history_age_seconds"),
        (
            {"max_consecutive_latest_watch_count": -1},
            "max_consecutive_latest_watch_count",
        ),
        (
            {"max_consecutive_latest_blocked_count": -1},
            "max_consecutive_latest_blocked_count",
        ),
        ({"max_duplicate_generated_at_count": -1}, "max_duplicate_generated_at_count"),
    ),
)
def test_quality_history_trend_gate_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
):
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_quality_history_trend_gate_rejects_wrong_types_subclasses_and_corruption():
    api = _api()
    source = _trend_report()

    class ConfigSubclass(api.PaperResearchPacketQualityHistoryTrendGateConfig):
        pass

    with pytest.raises(ValueError, match="trend_report must be"):
        api.build_paper_research_packet_quality_history_trend_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="trend_report must be"):
        api.build_paper_research_packet_quality_history_trend_gate_report(
            _trend_subclass(source),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_research_packet_quality_history_trend_gate_report(
            source,
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_research_packet_quality_history_trend_gate_report(
            source,
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 6, 23, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="gate_status"):
        replace(_gate_report(source), gate_status="stable")
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(_gate_report(source), recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(_gate_report(source), reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            _gate_report(source),
            reason_code_counts=(
                api.PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
                    "paper_research_packet_quality_history_trend_gate_passed",
                    1,
                ),
                api.PaperResearchPacketQualityHistoryTrendGateReasonCodeCount(
                    "paper_research_packet_quality_history_trend_gate_passed",
                    1,
                ),
            ),
        )


def test_quality_history_trend_gate_rejects_corrupted_recurring_pass_status():
    row = PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow.__new__(
        PaperResearchPacketQualityHistoryTrendRecurringReasonCodeRow,
    )
    object.__setattr__(row, "check_status", "pass")
    object.__setattr__(row, "reason_code", "paper_research_packet_quality_history_passed")
    object.__setattr__(row, "history_report_count", 1)
    object.__setattr__(row, "paper_only", True)
    object.__setattr__(row, "report_only", True)
    object.__setattr__(row, "readonly", True)
    source = _corrupted_trend_report(
        _trend_report(),
        recurring_reason_code_rows=(row,),
    )

    with pytest.raises(ValueError, match="check_status must be blocked or watch"):
        _gate_report(source)


def test_quality_history_trend_gate_normalizes_aware_datetimes():
    offset = timezone(timedelta(hours=-4))
    source = _trend_report(
        generated_at=datetime(2026, 6, 23, 13, 45, tzinfo=offset),
        latest_history_generated_at=datetime(2026, 6, 23, 13, 30, tzinfo=offset),
    )

    report = _api().build_paper_research_packet_quality_history_trend_gate_report(
        source,
        config=_config(),
        generated_at=datetime(2026, 6, 23, 14, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.source_generated_at == TREND_GENERATED_AT
    assert report.latest_history_generated_at == LATEST_HISTORY_AT
    assert report.latest_history_age_seconds == 1_800


def test_quality_history_trend_gate_module_is_pure_paper_report_only_readonly():
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
