from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import inspect

import pytest

from polymarket_alpha_lab.paper_research_packet_operator_flow import (
    PaperResearchPacketOperatorFlowReport,
)


GENERATED_AT = datetime(2026, 6, 23, 18, 0, tzinfo=UTC)
SOURCE_AT = datetime(2026, 6, 23, 12, 0, tzinfo=UTC)
FLOW_STATUSES = ("pass", "watch", "blocked")


def d(value: str) -> Decimal:
    return Decimal(value)


def _api():
    return import_module("polymarket_alpha_lab.paper_research_packet_operator_flow_db_history")


def _config(**overrides):
    values = {
        "config_version": "paper-research-packet-operator-flow-db-history-v0",
        "min_report_count": 3,
        "max_blocked_flow_report_count": 0,
        "max_watch_flow_report_count": 0,
        "max_duplicate_generated_at_count": 0,
    }
    values.update(overrides)
    return _api().PaperResearchPacketOperatorFlowDbHistoryConfig(**values)


def _constructor_reason_codes(flow_status: str) -> tuple[str, ...]:
    if flow_status == "blocked":
        return ("packet_quality_blocked",)
    if flow_status == "watch":
        return ("packet_quality_watch",)
    return ("operator_flow_passed",)


def _flow_report(
    *,
    generated_at: datetime = SOURCE_AT,
    flow_status: str = "pass",
) -> PaperResearchPacketOperatorFlowReport:
    quality_status = "pass"
    history_status = "pass"
    quality_blocked_count = 0
    quality_watch_count = 0
    quality_pass_count = 3
    if flow_status == "blocked":
        quality_status = "blocked"
        quality_blocked_count = 1
        quality_watch_count = 0
        quality_pass_count = 2
    elif flow_status == "watch":
        quality_status = "watch"
        quality_blocked_count = 0
        quality_watch_count = 1
        quality_pass_count = 2
    report = PaperResearchPacketOperatorFlowReport(
        generated_at=generated_at,
        config_version="paper-research-packet-operator-flow-v0",
        flow_status=flow_status,
        packet_generated_at=generated_at - timedelta(minutes=12),
        packet_config_version="paper-research-packet-v0",
        packet_persisted=True,
        packet_row_count=1,
        included_count=1,
        skipped_count=0,
        quality_generated_at=generated_at - timedelta(minutes=6),
        quality_config_version="paper-research-packet-quality-v0",
        quality_source_generated_at=generated_at - timedelta(minutes=12),
        quality_source_config_version="paper-research-packet-v0",
        quality_source_age_seconds=360,
        quality_included_share=d("1.000000"),
        quality_skipped_share=d("0.000000"),
        quality_persisted=True,
        quality_status=quality_status,
        quality_check_count=3,
        quality_pass_count=quality_pass_count,
        quality_watch_count=quality_watch_count,
        quality_blocked_count=quality_blocked_count,
        history_generated_at=generated_at - timedelta(minutes=1),
        history_config_version="paper-research-packet-quality-history-v0",
        history_source_report_count=3,
        history_first_source_generated_at=generated_at - timedelta(hours=2),
        history_latest_source_generated_at=generated_at - timedelta(minutes=6),
        history_latest_quality_status=quality_status,
        history_latest_source_age_seconds=360,
        history_latest_included_share=d("1.000000"),
        history_latest_skipped_share=d("0.000000"),
        history_duplicate_generated_at_count=0,
        history_status=history_status,
        reason_codes=_constructor_reason_codes(flow_status),
    )
    return report


def _history(*reports: PaperResearchPacketOperatorFlowReport, **config_overrides):
    return _api().build_paper_research_packet_operator_flow_db_history_report(
        reports,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("operator-flow DB history reports must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)
    elif hasattr(value, "__dict__"):
        _assert_no_floats(vars(value))


def _operator_flow_subclass(
    report: PaperResearchPacketOperatorFlowReport,
) -> PaperResearchPacketOperatorFlowReport:
    class OperatorFlowReportSubclass(PaperResearchPacketOperatorFlowReport):
        pass

    subclass_report = OperatorFlowReportSubclass.__new__(OperatorFlowReportSubclass)
    for field_name, value in report.__dict__.items():
        object.__setattr__(subclass_report, field_name, value)
    return subclass_report


def test_operator_flow_db_history_empty_and_insufficient_reports_are_blocked():
    api = _api()
    empty = _history()
    assert type(empty) is api.PaperResearchPacketOperatorFlowDbHistoryReport
    assert empty.generated_at == GENERATED_AT
    assert empty.config_version == (
        "paper-research-packet-operator-flow-db-history-v0"
    )
    assert empty.history_status == "blocked"
    assert empty.report_count == 0
    assert empty.first_report_generated_at is None
    assert empty.latest_report_generated_at is None
    assert empty.latest_flow_status is None
    assert empty.latest_packet_row_count is None
    assert empty.latest_quality_status is None
    assert empty.latest_history_status is None
    assert empty.flow_status_rows == tuple(
        api.PaperResearchPacketOperatorFlowDbHistoryStatusRow(status, 0)
        for status in FLOW_STATUSES
    )
    assert empty.duplicate_generated_at_count == 0
    assert empty.consecutive_latest_pass_count == 0
    assert empty.consecutive_latest_watch_count == 0
    assert empty.consecutive_latest_blocked_count == 0
    assert empty.latest_reason_codes == ()
    assert empty.reason_code_rows == ()
    assert empty.reason_codes == (
        "insufficient_paper_research_packet_operator_flow_history",
    )
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    report = _flow_report()
    insufficient = _history(report)
    assert insufficient.history_status == "blocked"
    assert insufficient.report_count == 1
    assert insufficient.first_report_generated_at == report.generated_at
    assert insufficient.latest_report_generated_at == report.generated_at
    assert insufficient.latest_flow_status == "pass"
    assert insufficient.latest_packet_row_count == 1
    assert insufficient.latest_quality_status == "pass"
    assert insufficient.latest_history_status == "pass"
    assert insufficient.latest_reason_codes == ("operator_flow_passed",)
    assert insufficient.reason_codes == (
        "insufficient_paper_research_packet_operator_flow_history",
    )
    _assert_no_floats(insufficient)


def test_operator_flow_db_history_passes_and_sorts_chronologically():
    first = _flow_report(generated_at=SOURCE_AT)
    middle = _flow_report(generated_at=SOURCE_AT + timedelta(hours=1))
    latest = _flow_report(generated_at=SOURCE_AT + timedelta(hours=2))
    history = _history(latest, first, middle)
    assert history.history_status == "pass"
    assert history.report_count == 3
    assert history.first_report_generated_at == first.generated_at
    assert history.latest_report_generated_at == latest.generated_at
    assert history.latest_flow_status == "pass"
    assert history.flow_status_rows == (
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", 3),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("watch", 0),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("blocked", 0),
    )
    assert history.consecutive_latest_pass_count == 3
    assert history.consecutive_latest_watch_count == 0
    assert history.consecutive_latest_blocked_count == 0
    assert history.latest_reason_codes == ("operator_flow_passed",)
    assert history.reason_code_rows == (
        _api().PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
            "operator_flow_passed",
            3,
        ),
    )
    assert history.reason_codes == (
        "paper_research_packet_operator_flow_db_history_passed",
    )


def test_operator_flow_db_history_status_precedence_blocks_over_watch():
    history = _history(
        _flow_report(generated_at=SOURCE_AT),
        _flow_report(
            generated_at=SOURCE_AT + timedelta(hours=1),
            flow_status="watch",
        ),
        _flow_report(
            generated_at=SOURCE_AT + timedelta(hours=2),
            flow_status="blocked",
        ),
    )
    assert history.history_status == "blocked"
    assert history.latest_flow_status == "blocked"
    assert history.flow_status_rows == (
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", 1),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("watch", 1),
        _api().PaperResearchPacketOperatorFlowDbHistoryStatusRow("blocked", 1),
    )
    assert history.consecutive_latest_blocked_count == 1
    assert history.reason_codes == (
        "blocked_operator_flow_report_threshold_exceeded",
        "watch_operator_flow_report_threshold_exceeded",
    )


def test_operator_flow_db_history_watches_duplicate_generated_at():
    duplicate_at = SOURCE_AT + timedelta(hours=1)
    history = _history(
        _flow_report(generated_at=SOURCE_AT),
        _flow_report(generated_at=duplicate_at),
        _flow_report(generated_at=duplicate_at),
    )
    assert history.history_status == "watch"
    assert history.duplicate_generated_at_count == 1
    assert history.reason_codes == ("duplicate_generated_at_threshold_exceeded",)


def test_operator_flow_db_history_counts_latest_consecutive_status_only():
    history = _history(
        _flow_report(
            generated_at=SOURCE_AT,
            flow_status="watch",
        ),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=1)),
        _flow_report(
            generated_at=SOURCE_AT + timedelta(hours=2),
            flow_status="watch",
        ),
        _flow_report(
            generated_at=SOURCE_AT + timedelta(hours=3),
            flow_status="watch",
        ),
        min_report_count=4,
        max_watch_flow_report_count=4,
    )
    assert history.history_status == "pass"
    assert history.consecutive_latest_pass_count == 0
    assert history.consecutive_latest_watch_count == 2
    assert history.consecutive_latest_blocked_count == 0


def test_operator_flow_db_history_reason_code_rows_are_distinct_and_deterministic():
    history = _history(
        _flow_report(generated_at=SOURCE_AT),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=1)),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=2), flow_status="watch"),
    )

    assert history.latest_reason_codes == ("packet_quality_watch",)
    assert history.reason_code_rows == (
        _api().PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
            "operator_flow_passed",
            2,
        ),
        _api().PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
            "packet_quality_watch",
            1,
        ),
    )
    assert tuple(type(row) for row in history.reason_code_rows) == (
        _api().PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow,
        _api().PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow,
    )


def test_operator_flow_db_history_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    history = _history(
        _flow_report(generated_at=SOURCE_AT),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=1)),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=2)),
    )
    config = _config()
    status_row = api.PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", 1)
    reason_row = api.PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
        "operator_flow_passed",
        1,
    )

    with pytest.raises(FrozenInstanceError):
        history.report_count = 0  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        status_row.status_count = 2  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason_row.report_count = 2  # type: ignore[misc]

    with pytest.raises(ValueError, match="config must be paper_only"):
        replace(config, paper_only=False)
    with pytest.raises(ValueError, match="history report must be report_only"):
        replace(history, report_only=False)
    with pytest.raises(ValueError, match="status row must be readonly"):
        replace(status_row, readonly=False)
    with pytest.raises(ValueError, match="reason code row must be paper_only"):
        replace(reason_row, paper_only=False)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"min_report_count": 0}, "min_report_count"),
        ({"min_report_count": -1}, "min_report_count"),
        ({"max_blocked_flow_report_count": -1}, "max_blocked_flow_report_count"),
        ({"max_watch_flow_report_count": -1}, "max_watch_flow_report_count"),
        ({"max_duplicate_generated_at_count": -1}, "max_duplicate_generated_at_count"),
    ),
)
def test_operator_flow_db_history_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
):
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_operator_flow_db_history_rows_reject_invalid_values_and_types():
    api = _api()

    with pytest.raises(ValueError, match="flow_status"):
        api.PaperResearchPacketOperatorFlowDbHistoryStatusRow("stable", 1)
    with pytest.raises(ValueError, match="status_count"):
        api.PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", -1)
    with pytest.raises(ValueError, match="reason_code"):
        api.PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow("", 1)
    with pytest.raises(ValueError, match="report_count"):
        api.PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow("reason", 0)

    status_row = api.PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", 1)
    reason_row = api.PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
        "operator_flow_passed",
        1,
    )
    history = _history(
        _flow_report(generated_at=SOURCE_AT),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=1)),
        _flow_report(generated_at=SOURCE_AT + timedelta(hours=2)),
    )

    with pytest.raises(ValueError, match="flow_status_rows"):
        replace(history, flow_status_rows=(object(),))
    with pytest.raises(ValueError, match="reason_code_rows"):
        replace(history, reason_code_rows=(object(),))

    class StatusRowSubclass(api.PaperResearchPacketOperatorFlowDbHistoryStatusRow):
        pass

    class ReasonCodeRowSubclass(api.PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow):
        pass

    with pytest.raises(ValueError, match="flow_status_rows"):
        replace(
            history,
            flow_status_rows=(
                StatusRowSubclass(status_row.flow_status, status_row.status_count),
            ),
        )
    with pytest.raises(ValueError, match="reason_code_rows"):
        replace(
            history,
            reason_code_rows=(
                ReasonCodeRowSubclass(reason_row.reason_code, reason_row.report_count),
            ),
        )
    with pytest.raises(ValueError, match="flow_status_rows must cover latest_flow_status"):
        replace(
            history,
            latest_flow_status="watch",
            flow_status_rows=(
                api.PaperResearchPacketOperatorFlowDbHistoryStatusRow("pass", 3),
                api.PaperResearchPacketOperatorFlowDbHistoryStatusRow("watch", 0),
                api.PaperResearchPacketOperatorFlowDbHistoryStatusRow("blocked", 0),
            ),
            consecutive_latest_pass_count=0,
            consecutive_latest_watch_count=1,
        )
    with pytest.raises(ValueError, match="consecutive_latest_pass_count must not exceed"):
        replace(history, consecutive_latest_pass_count=4)
    with pytest.raises(ValueError, match="reason_code_rows is required"):
        replace(history, reason_code_rows=())
    with pytest.raises(ValueError, match="reason_code_rows report_count"):
        replace(
            history,
            reason_code_rows=(
                api.PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
                    "operator_flow_passed",
                    4,
                ),
            ),
        )


def test_operator_flow_db_history_builder_rejects_wrong_types_and_subclasses():
    api = _api()
    report = _flow_report()

    class ConfigSubclass(api.PaperResearchPacketOperatorFlowDbHistoryConfig):
        pass

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="operator_flow_reports must be a list or tuple"):
        api.build_paper_research_packet_operator_flow_db_history_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="operator_flow_reports must contain"):
        api.build_paper_research_packet_operator_flow_db_history_report(
            [object()],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="operator_flow_reports must contain"):
        api.build_paper_research_packet_operator_flow_db_history_report(
            [_operator_flow_subclass(report)],
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_research_packet_operator_flow_db_history_report(
            [],
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_research_packet_operator_flow_db_history_report(
            [],
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 23, 18, 0, tzinfo=UTC),
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        ("paper_only", False, "operator flow report must be paper_only"),
        ("config_version", " paper-research-packet-operator-flow-v0", "config_version"),
        ("packet_row_count", -1, "packet_row_count"),
        ("flow_status", "stable", "flow_status"),
        ("reason_codes", (" bad_reason",), "reason_codes"),
        ("reason_codes", ("same_reason", "same_reason"), "reason_codes"),
        ("reason_codes", ("z_reason", "a_reason"), "reason_codes"),
        ("history_generated_at", GENERATED_AT + timedelta(seconds=1), "history_generated_at"),
    ),
)
def test_operator_flow_db_history_builder_rejects_corrupted_source_reports(
    field_name: str,
    bad_value: object,
    message: str,
):
    report = _flow_report()
    object.__setattr__(report, field_name, bad_value)

    with pytest.raises(ValueError, match=message):
        _history(report)


def test_operator_flow_db_history_builder_rejects_semantically_corrupted_reason_codes():
    report = _flow_report()
    object.__setattr__(report, "reason_codes", ("bogus_operator_reason",))

    with pytest.raises(ValueError, match="reason_codes must match source statuses"):
        _history(report)


def test_operator_flow_db_history_normalizes_aware_datetimes_without_mutating_sources():
    offset = timezone(timedelta(hours=-4))
    offset_source_at = datetime(2026, 6, 23, 8, 0, tzinfo=offset)
    report = _flow_report()
    object.__setattr__(report, "generated_at", offset_source_at)

    history = _history(report, min_report_count=1)

    assert history.first_report_generated_at == SOURCE_AT
    assert history.latest_report_generated_at == SOURCE_AT
    assert history.first_report_generated_at.tzinfo is UTC
    assert history.latest_report_generated_at.tzinfo is UTC
    assert report.generated_at == offset_source_at
    assert report.generated_at.tzinfo is offset


def test_operator_flow_db_history_module_is_pure_paper_report_only_readonly():
    source = inspect.getsource(_api()).lower()

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "polymarketpublicclient",
        "requests",
        "httpx",
        "wallet",
        "private_key",
        "relayer",
        "account",
        "signing",
        "exchange",
        "live_trading",
    ):
        assert banned not in source
