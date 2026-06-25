"""Tests for paper broker execution history reports."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_broker import (
    EXECUTION_STATUSES,
    NEXT_STEP_BY_STATUS,
    PaperBrokerExecutionRecord,
)
from polymarket_alpha_lab.paper_broker_history import (
    PaperBrokerHistoryConfig,
    PaperBrokerHistoryReasonCodeCount,
    PaperBrokerHistoryReport,
    PaperBrokerHistoryStatusRow,
    build_paper_broker_history_report,
)


CONFIG = PaperBrokerHistoryConfig()
GENERATED_AT = datetime(2026, 6, 25, 12, 30, tzinfo=UTC)
DEFAULT_REASON_CODES = object()


def _record(
    execution_status: str,
    *,
    minutes: int,
    execution_notional: Decimal = Decimal("0.000000"),
    source_proposal_count: int = 1,
    reason_codes: tuple[str, ...] | object = DEFAULT_REASON_CODES,
) -> PaperBrokerExecutionRecord:
    normalized_reason_codes = (
        (f"{execution_status}_reason",)
        if reason_codes is DEFAULT_REASON_CODES
        else reason_codes
    )
    return PaperBrokerExecutionRecord(
        generated_at=datetime(2026, 6, 25, 9, 0, tzinfo=UTC) + timedelta(minutes=minutes),
        config_version="paper-broker-v0",
        execution_status=execution_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[execution_status],
        source_gate_status={
            "paper_submitted": "pass",
            "paper_blocked": "blocked",
            "paper_held": "watch",
        }[execution_status],
        source_proposal_count=source_proposal_count,
        source_proposal_total_notional=execution_notional,
        execution_notional=execution_notional,
        reason_codes=normalized_reason_codes,  # type: ignore[arg-type]
    )


def _status_counts(rows: tuple[PaperBrokerHistoryStatusRow, ...]) -> dict[str, int]:
    return {row.execution_status: row.status_count for row in rows}


def test_empty_history_report_is_readonly_and_has_zeroed_summary() -> None:
    report = build_paper_broker_history_report(
        (),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report == PaperBrokerHistoryReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG.config_version,
        record_count=0,
        first_record_generated_at=None,
        latest_record_generated_at=None,
        latest_execution_status=None,
        latest_recommended_next_step=None,
        submitted_record_count=0,
        blocked_record_count=0,
        held_record_count=0,
        total_execution_notional=Decimal("0.000000"),
        latest_execution_notional=None,
        total_source_proposal_count=0,
        execution_status_rows=tuple(
            PaperBrokerHistoryStatusRow(status, 0)
            for status in EXECUTION_STATUSES
        ),
        reason_code_counts=(),
        history_status="empty",
        recommended_next_step="await_paper_broker_executions",
        reason_codes=("paper_broker_history_empty",),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_sorts_records_and_summarizes_execution_counts_and_reasons() -> None:
    records = (
        _record(
            "paper_submitted",
            minutes=3,
            execution_notional=Decimal("7.500000"),
            source_proposal_count=3,
            reason_codes=("zeta",),
        ),
        _record(
            "paper_blocked",
            minutes=2,
            source_proposal_count=2,
            reason_codes=("alpha", "shared"),
        ),
        _record(
            "paper_held",
            minutes=1,
            source_proposal_count=1,
            reason_codes=("shared",),
        ),
        _record(
            "paper_submitted",
            minutes=4,
            execution_notional=Decimal("2.250000"),
            source_proposal_count=4,
            reason_codes=("alpha",),
        ),
    )

    report = build_paper_broker_history_report(
        records,
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.record_count == 4
    assert report.first_record_generated_at == records[2].generated_at
    assert report.latest_record_generated_at == records[3].generated_at
    assert report.latest_execution_status == "paper_submitted"
    assert report.latest_recommended_next_step == "route_to_paper_order_lifecycle"
    assert report.submitted_record_count == 2
    assert report.blocked_record_count == 1
    assert report.held_record_count == 1
    assert report.total_execution_notional == Decimal("9.750000")
    assert report.latest_execution_notional == Decimal("2.250000")
    assert report.total_source_proposal_count == 10
    assert _status_counts(report.execution_status_rows) == {
        "paper_submitted": 2,
        "paper_blocked": 1,
        "paper_held": 1,
    }
    assert report.reason_code_counts == (
        PaperBrokerHistoryReasonCodeCount("alpha", 2),
        PaperBrokerHistoryReasonCodeCount("shared", 2),
        PaperBrokerHistoryReasonCodeCount("zeta", 1),
    )
    assert report.history_status == "pass"
    assert report.recommended_next_step == "route_to_paper_order_lifecycle"
    assert report.reason_codes == ("paper_broker_history_latest_submitted",)


@pytest.mark.parametrize(
    ("latest_status", "history_status", "next_step", "reason_codes"),
    (
        (
            "paper_blocked",
            "blocked",
            "repair_paper_broker_executions",
            ("paper_broker_history_latest_blocked",),
        ),
        (
            "paper_held",
            "watch",
            "review_paper_broker_executions",
            ("paper_broker_history_latest_held",),
        ),
    ),
)
def test_history_status_and_next_step_follow_latest_broker_status(
    latest_status: str,
    history_status: str,
    next_step: str,
    reason_codes: tuple[str, ...],
) -> None:
    report = build_paper_broker_history_report(
        (
            _record(
                "paper_submitted",
                minutes=1,
                execution_notional=Decimal("1.000000"),
            ),
            _record(latest_status, minutes=2),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.latest_execution_status == latest_status
    assert report.history_status == history_status
    assert report.recommended_next_step == next_step
    assert report.reason_codes == reason_codes


def test_history_dataclasses_are_frozen_validate_exact_types_and_hard_flags() -> None:
    report = build_paper_broker_history_report(
        (
            _record(
                "paper_submitted",
                minutes=1,
                execution_notional=Decimal("1.000000"),
            ),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    with pytest.raises(FrozenInstanceError):
        report.record_count = 2  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(PaperBrokerHistoryStatusRow("paper_submitted", 1), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(PaperBrokerHistoryReasonCodeCount("reason", 1), readonly=False)
    with pytest.raises(ValueError, match="config must be a PaperBrokerHistoryConfig"):
        build_paper_broker_history_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="records must be a tuple"):
        build_paper_broker_history_report(
            [],
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="records must contain PaperBrokerExecutionRecord values"):
        build_paper_broker_history_report(
            (object(),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source record readonly"):
        bad_record = _record("paper_blocked", minutes=2)
        object.__setattr__(bad_record, "readonly", False)
        build_paper_broker_history_report(
            (bad_record,),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_history_dataclasses_do_not_support_subclassing() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadConfig(PaperBrokerHistoryConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadStatusRow(PaperBrokerHistoryStatusRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReasonCount(PaperBrokerHistoryReasonCodeCount):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(PaperBrokerHistoryReport):
            pass
