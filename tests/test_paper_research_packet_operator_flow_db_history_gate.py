from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from importlib import import_module
import inspect

import pytest

from polymarket_alpha_lab.paper_research_packet_operator_flow_db_history import (
    PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow,
    PaperResearchPacketOperatorFlowDbHistoryReport,
    PaperResearchPacketOperatorFlowDbHistoryStatusRow,
)


GENERATED_AT = datetime(2026, 6, 23, 18, 0, tzinfo=UTC)
LATEST_AT = datetime(2026, 6, 23, 17, 30, tzinfo=UTC)
FLOW_STATUSES = ("pass", "watch", "blocked")


def _api():
    return import_module(
        "polymarket_alpha_lab.paper_research_packet_operator_flow_db_history_gate",
    )


def _config(**overrides):
    values = {
        "config_version": "paper-research-packet-operator-flow-db-history-gate-v0",
        "min_history_report_count": 3,
        "max_latest_age_seconds": 86_400,
        "max_consecutive_latest_watch_count": 0,
        "max_consecutive_latest_blocked_count": 0,
        "max_duplicate_generated_at_count": 0,
    }
    values.update(overrides)
    return _api().PaperResearchPacketOperatorFlowDbHistoryGateConfig(**values)


def _source_reason(history_status: str, latest_flow_status: str) -> str:
    if history_status == "blocked":
        return "blocked_operator_flow_report_threshold_exceeded"
    if history_status == "watch":
        return "watch_operator_flow_report_threshold_exceeded"
    if latest_flow_status == "blocked":
        return "blocked_operator_flow_report_threshold_exceeded"
    if latest_flow_status == "watch":
        return "watch_operator_flow_report_threshold_exceeded"
    return "paper_research_packet_operator_flow_db_history_passed"


def _history_report(
    *,
    generated_at: datetime = GENERATED_AT,
    history_status: str = "pass",
    report_count: int = 3,
    latest_report_generated_at: datetime | None = LATEST_AT,
    latest_flow_status: str | None = "pass",
    duplicate_generated_at_count: int = 0,
    consecutive_latest_pass_count: int = 3,
    consecutive_latest_watch_count: int = 0,
    consecutive_latest_blocked_count: int = 0,
    reason_codes: tuple[str, ...] | None = None,
) -> PaperResearchPacketOperatorFlowDbHistoryReport:
    if report_count == 0:
        return PaperResearchPacketOperatorFlowDbHistoryReport(
            generated_at=generated_at,
            config_version="paper-research-packet-operator-flow-db-history-v0",
            history_status=history_status,
            report_count=0,
            first_report_generated_at=None,
            latest_report_generated_at=None,
            latest_flow_status=None,
            latest_packet_row_count=None,
            latest_quality_status=None,
            latest_history_status=None,
            flow_status_rows=tuple(
                PaperResearchPacketOperatorFlowDbHistoryStatusRow(status, 0)
                for status in FLOW_STATUSES
            ),
            duplicate_generated_at_count=0,
            consecutive_latest_pass_count=0,
            consecutive_latest_watch_count=0,
            consecutive_latest_blocked_count=0,
            latest_reason_codes=(),
            reason_code_rows=(),
            reason_codes=(
                reason_codes
                if reason_codes is not None
                else ("insufficient_paper_research_packet_operator_flow_history",)
            ),
        )

    if latest_flow_status is None:
        raise AssertionError("test helper requires latest_flow_status for nonempty history")
    status_counts = {
        "pass": report_count,
        "watch": 0,
        "blocked": 0,
    }
    if latest_flow_status == "watch":
        status_counts = {
            "pass": report_count - consecutive_latest_watch_count,
            "watch": consecutive_latest_watch_count,
            "blocked": 0,
        }
    elif latest_flow_status == "blocked":
        status_counts = {
            "pass": report_count - consecutive_latest_blocked_count,
            "watch": 0,
            "blocked": consecutive_latest_blocked_count,
        }

    source_reason = _source_reason(history_status, latest_flow_status)
    normalized_reason_codes = (
        reason_codes if reason_codes is not None else (source_reason,)
    )
    latest_reason_codes = (
        ("operator_flow_passed",)
        if latest_flow_status == "pass"
        else (f"packet_quality_{latest_flow_status}",)
    )

    return PaperResearchPacketOperatorFlowDbHistoryReport(
        generated_at=generated_at,
        config_version="paper-research-packet-operator-flow-db-history-v0",
        history_status=history_status,
        report_count=report_count,
        first_report_generated_at=latest_report_generated_at - timedelta(hours=2),
        latest_report_generated_at=latest_report_generated_at,
        latest_flow_status=latest_flow_status,
        latest_packet_row_count=1,
        latest_quality_status=latest_flow_status,
        latest_history_status=history_status,
        flow_status_rows=tuple(
            PaperResearchPacketOperatorFlowDbHistoryStatusRow(
                status,
                status_counts[status],
            )
            for status in FLOW_STATUSES
        ),
        duplicate_generated_at_count=duplicate_generated_at_count,
        consecutive_latest_pass_count=consecutive_latest_pass_count,
        consecutive_latest_watch_count=consecutive_latest_watch_count,
        consecutive_latest_blocked_count=consecutive_latest_blocked_count,
        latest_reason_codes=latest_reason_codes,
        reason_code_rows=tuple(
            PaperResearchPacketOperatorFlowDbHistoryReasonCodeRow(
                reason_code,
                report_count,
            )
            for reason_code in normalized_reason_codes
        ),
        reason_codes=normalized_reason_codes,
    )


def _gate_report(
    history_report: PaperResearchPacketOperatorFlowDbHistoryReport,
    **config_overrides,
):
    return _api().build_paper_research_packet_operator_flow_db_history_gate_report(
        history_report,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def _history_subclass(
    report: PaperResearchPacketOperatorFlowDbHistoryReport,
) -> PaperResearchPacketOperatorFlowDbHistoryReport:
    class HistoryReportSubclass(PaperResearchPacketOperatorFlowDbHistoryReport):
        pass

    subclass_report = HistoryReportSubclass.__new__(HistoryReportSubclass)
    for field_name, value in report.__dict__.items():
        object.__setattr__(subclass_report, field_name, value)
    return subclass_report


def test_operator_flow_db_history_gate_passes_clean_recent_history():
    api = _api()
    source = _history_report()

    report = _gate_report(source)

    assert type(report) is api.PaperResearchPacketOperatorFlowDbHistoryGateReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "paper-research-packet-operator-flow-db-history-gate-v0"
    )
    assert report.gate_status == "pass"
    assert report.recommended_next_step == (
        "allow_paper_autonomous_screening_decision_support"
    )
    assert report.source_report_count == 3
    assert report.source_history_status == "pass"
    assert report.latest_flow_status == "pass"
    assert report.latest_source_generated_at == LATEST_AT
    assert report.latest_source_age_seconds == 1_800
    assert report.duplicate_generated_at_count == 0
    assert report.consecutive_latest_watch_count == 0
    assert report.consecutive_latest_blocked_count == 0
    assert report.reason_code_counts == (
        api.PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            "paper_operator_flow_db_history_gate_passed",
            1,
        ),
    )
    assert report.reason_codes == (
        "paper_operator_flow_db_history_gate_passed",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _history_report(history_status="blocked", reason_codes=("z_source_blocked",)),
            "source_operator_flow_db_history_blocked",
        ),
        (
            _history_report(report_count=2, consecutive_latest_pass_count=2),
            "insufficient_operator_flow_db_history",
        ),
        (
            _history_report(
                latest_flow_status="blocked",
                consecutive_latest_pass_count=0,
                consecutive_latest_blocked_count=1,
                reason_codes=("z_latest_blocked",),
            ),
            "latest_operator_flow_blocked",
        ),
    ),
)
def test_operator_flow_db_history_gate_blocks_for_blocked_inputs(
    source: PaperResearchPacketOperatorFlowDbHistoryReport,
    expected_reason: str,
):
    report = _gate_report(source)

    assert report.gate_status == "blocked"
    assert report.recommended_next_step == (
        "block_paper_autonomous_screening_decision_support"
    )
    assert expected_reason in report.reason_codes
    assert "paper_operator_flow_db_history_gate_passed" not in report.reason_codes


@pytest.mark.parametrize(
    ("source", "expected_reason"),
    (
        (
            _history_report(history_status="watch", reason_codes=("z_source_watch",)),
            "source_operator_flow_db_history_watch",
        ),
        (
            _history_report(
                latest_flow_status="watch",
                consecutive_latest_pass_count=0,
                consecutive_latest_watch_count=1,
                reason_codes=("z_latest_watch",),
            ),
            "latest_operator_flow_watch",
        ),
        (
            _history_report(duplicate_generated_at_count=1),
            "duplicate_operator_flow_generated_at_threshold_exceeded",
        ),
    ),
)
def test_operator_flow_db_history_gate_watches_for_watch_inputs(
    source: PaperResearchPacketOperatorFlowDbHistoryReport,
    expected_reason: str,
):
    report = _gate_report(source)

    assert report.gate_status == "watch"
    assert report.recommended_next_step == (
        "throttle_paper_autonomous_screening_decision_support"
    )
    assert expected_reason in report.reason_codes
    assert "paper_operator_flow_db_history_gate_passed" not in report.reason_codes


def test_operator_flow_db_history_gate_watches_stale_latest_timestamp():
    source = _history_report(
        latest_report_generated_at=GENERATED_AT - timedelta(seconds=86_401),
    )

    report = _gate_report(source)

    assert report.gate_status == "watch"
    assert report.latest_source_age_seconds == 86_401
    assert report.reason_codes == ("stale_operator_flow_db_history",)


def test_operator_flow_db_history_gate_enforces_consecutive_thresholds():
    watch_source = _history_report(
        latest_flow_status="watch",
        consecutive_latest_pass_count=0,
        consecutive_latest_watch_count=2,
        reason_codes=("z_latest_watch",),
    )
    blocked_source = _history_report(
        latest_flow_status="blocked",
        consecutive_latest_pass_count=0,
        consecutive_latest_blocked_count=2,
        reason_codes=("z_latest_blocked",),
    )

    watch_report = _gate_report(
        watch_source,
        max_consecutive_latest_watch_count=1,
    )
    blocked_report = _gate_report(
        blocked_source,
        max_consecutive_latest_blocked_count=1,
    )

    assert watch_report.gate_status == "watch"
    assert "latest_operator_flow_watch" in watch_report.reason_codes
    assert (
        "consecutive_operator_flow_watch_threshold_exceeded"
        in watch_report.reason_codes
    )
    assert blocked_report.gate_status == "blocked"
    assert "latest_operator_flow_blocked" in blocked_report.reason_codes
    assert (
        "consecutive_operator_flow_blocked_threshold_exceeded"
        in blocked_report.reason_codes
    )


def test_operator_flow_db_history_gate_missing_latest_timestamp_blocks():
    source = _history_report(report_count=0)

    report = _gate_report(source, min_history_report_count=0)

    assert report.gate_status == "blocked"
    assert report.latest_source_generated_at is None
    assert report.latest_source_age_seconds is None
    assert "missing_latest_operator_flow_history_timestamp" in report.reason_codes


def test_operator_flow_db_history_gate_reason_code_counts_are_deterministic_and_positive():
    source = _history_report(
        history_status="blocked",
        latest_flow_status="blocked",
        duplicate_generated_at_count=1,
        consecutive_latest_pass_count=0,
        consecutive_latest_blocked_count=2,
        reason_codes=("z_latest_blocked",),
    )

    report = _gate_report(
        source,
        min_history_report_count=4,
        max_consecutive_latest_blocked_count=1,
    )

    assert report.gate_status == "blocked"
    assert report.reason_code_counts == (
        _api().PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            "consecutive_operator_flow_blocked_threshold_exceeded",
            1,
        ),
        _api().PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            "duplicate_operator_flow_generated_at_threshold_exceeded",
            1,
        ),
        _api().PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            "insufficient_operator_flow_db_history",
            1,
        ),
        _api().PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            "latest_operator_flow_blocked",
            1,
        ),
        _api().PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
            "source_operator_flow_db_history_blocked",
            1,
        ),
    )
    assert report.reason_codes == tuple(row.reason_code for row in report.reason_code_counts)
    assert all(row.report_count > 0 for row in report.reason_code_counts)


def test_operator_flow_db_history_gate_dataclasses_are_frozen_and_validate_hard_flags():
    api = _api()
    source = _history_report()
    config = _config()
    reason_count = api.PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
        "paper_operator_flow_db_history_gate_passed",
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
        ({"max_latest_age_seconds": -1}, "max_latest_age_seconds"),
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
def test_operator_flow_db_history_gate_config_rejects_invalid_thresholds(
    overrides: dict[str, object],
    message: str,
):
    with pytest.raises(ValueError, match=message):
        _config(**overrides)


def test_operator_flow_db_history_gate_rejects_wrong_types_subclasses_and_corruption():
    api = _api()
    source = _history_report()

    class ConfigSubclass(api.PaperResearchPacketOperatorFlowDbHistoryGateConfig):
        pass

    class DatetimeSubclass(datetime):
        pass

    with pytest.raises(ValueError, match="history_report must be"):
        api.build_paper_research_packet_operator_flow_db_history_gate_report(
            object(),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="history_report must be"):
        api.build_paper_research_packet_operator_flow_db_history_gate_report(
            _history_subclass(source),
            config=_config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config must be"):
        api.build_paper_research_packet_operator_flow_db_history_gate_report(
            source,
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        api.build_paper_research_packet_operator_flow_db_history_gate_report(
            source,
            config=_config(),
            generated_at=DatetimeSubclass(2026, 6, 23, 18, 0, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="gate_status"):
        replace(_gate_report(source), gate_status="paused")
    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(_gate_report(source), recommended_next_step="manual_review")
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(_gate_report(source), reason_code_counts=(object(),))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            _gate_report(source),
            reason_code_counts=(
                api.PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
                    "paper_operator_flow_db_history_gate_passed",
                    1,
                ),
                api.PaperResearchPacketOperatorFlowDbHistoryGateReasonCodeCount(
                    "paper_operator_flow_db_history_gate_passed",
                    1,
                ),
            ),
        )


def test_operator_flow_db_history_gate_normalizes_aware_datetimes():
    offset = timezone(timedelta(hours=-4))
    source = _history_report(
        latest_report_generated_at=datetime(2026, 6, 23, 13, 30, tzinfo=offset),
    )

    report = _api().build_paper_research_packet_operator_flow_db_history_gate_report(
        source,
        config=_config(),
        generated_at=datetime(2026, 6, 23, 14, 0, tzinfo=offset),
    )

    assert report.generated_at == GENERATED_AT
    assert report.latest_source_generated_at == LATEST_AT
    assert report.latest_source_age_seconds == 1_800


def test_operator_flow_db_history_gate_module_is_pure_paper_report_only_readonly():
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
        "order",
    ):
        assert banned not in source
