"""Tests for paper order lifecycle DB history reports."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.paper_order_lifecycle import (
    LIFECYCLE_STATUSES,
    NEXT_STEP_BY_STATUS,
    TERMINAL_STATUSES,
    PaperOrderLifecycleRecord,
)
from polymarket_alpha_lab.paper_order_lifecycle_db_history import (
    PaperOrderLifecycleDbHistoryConfig,
    PaperOrderLifecycleDbHistoryReasonCodeCount,
    PaperOrderLifecycleDbHistoryReport,
    PaperOrderLifecycleDbHistoryStatusRow,
    build_paper_order_lifecycle_db_history_report,
)


CONFIG = PaperOrderLifecycleDbHistoryConfig()
GENERATED_AT = datetime(2026, 6, 25, 12, 30, tzinfo=UTC)
DEFAULT_REASON_CODES = object()


def _record(
    lifecycle_status: str,
    *,
    minutes: int,
    fill_notional: Decimal = Decimal("0.000000"),
    reason_codes: tuple[str, ...] | object = DEFAULT_REASON_CODES,
    source_execution_status: str | None = None,
) -> PaperOrderLifecycleRecord:
    normalized_reason_codes = (
        (f"{lifecycle_status}_reason",)
        if reason_codes is DEFAULT_REASON_CODES
        else reason_codes
    )
    return PaperOrderLifecycleRecord(
        generated_at=datetime(2026, 6, 25, 9, 0, tzinfo=UTC) + timedelta(minutes=minutes),
        config_version="paper-order-lifecycle-v0",
        lifecycle_status=lifecycle_status,
        recommended_next_step=NEXT_STEP_BY_STATUS[lifecycle_status],
        source_execution_status=source_execution_status or f"source_{lifecycle_status}",
        source_execution_notional=fill_notional,
        fill_notional=fill_notional,
        is_terminal=lifecycle_status in TERMINAL_STATUSES,
        reason_codes=normalized_reason_codes,  # type: ignore[arg-type]
    )


def _status_counts(
    rows: tuple[PaperOrderLifecycleDbHistoryStatusRow, ...],
) -> dict[str, int]:
    return {row.lifecycle_status: row.status_count for row in rows}


def test_empty_history_report_is_readonly_and_has_zeroed_summary() -> None:
    report = build_paper_order_lifecycle_db_history_report(
        (),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report == PaperOrderLifecycleDbHistoryReport(
        generated_at=GENERATED_AT,
        config_version=CONFIG.config_version,
        record_count=0,
        first_record_generated_at=None,
        latest_record_generated_at=None,
        latest_lifecycle_status=None,
        terminal_record_count=0,
        nonterminal_record_count=0,
        filled_record_count=0,
        blocked_record_count=0,
        held_record_count=0,
        total_fill_notional=Decimal("0.000000"),
        latest_fill_notional=None,
        lifecycle_status_rows=tuple(
            PaperOrderLifecycleDbHistoryStatusRow(status, 0)
            for status in LIFECYCLE_STATUSES
        ),
        duplicate_generated_at_count=0,
        latest_same_status_streak=0,
        reason_code_counts=(),
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_sorts_records_and_summarizes_key_lifecycle_counts() -> None:
    records = (
        _record(
            "paper_filled",
            minutes=3,
            fill_notional=Decimal("7.500000"),
            reason_codes=("zeta",),
            source_execution_status="paper_submitted",
        ),
        _record(
            "risk_blocked",
            minutes=2,
            reason_codes=("alpha", "shared"),
            source_execution_status="paper_blocked",
        ),
        _record(
            "human_approval_pending",
            minutes=1,
            reason_codes=("shared",),
            source_execution_status="paper_held",
        ),
        _record(
            "paper_filled",
            minutes=4,
            fill_notional=Decimal("2.250000"),
            reason_codes=("alpha",),
            source_execution_status="paper_submitted",
        ),
    )

    report = build_paper_order_lifecycle_db_history_report(
        records,
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.record_count == 4
    assert report.first_record_generated_at == records[2].generated_at
    assert report.latest_record_generated_at == records[3].generated_at
    assert report.latest_lifecycle_status == "paper_filled"
    assert report.terminal_record_count == 3
    assert report.nonterminal_record_count == 1
    assert report.filled_record_count == 2
    assert report.blocked_record_count == 1
    assert report.held_record_count == 1
    assert report.total_fill_notional == Decimal("9.750000")
    assert report.latest_fill_notional == Decimal("2.250000")
    assert report.duplicate_generated_at_count == 0
    assert report.latest_same_status_streak == 2
    assert _status_counts(report.lifecycle_status_rows)["paper_filled"] == 2
    assert _status_counts(report.lifecycle_status_rows)["risk_blocked"] == 1
    assert _status_counts(report.lifecycle_status_rows)["human_approval_pending"] == 1
    assert report.reason_code_counts == (
        PaperOrderLifecycleDbHistoryReasonCodeCount("alpha", 2),
        PaperOrderLifecycleDbHistoryReasonCodeCount("shared", 2),
        PaperOrderLifecycleDbHistoryReasonCodeCount("zeta", 1),
    )


def test_history_covers_all_lifecycle_statuses_and_latest_same_status_streak() -> None:
    records = tuple(
        _record(
            status,
            minutes=index,
            fill_notional=Decimal("1.000000") if status == "paper_filled" else Decimal("0.000000"),
        )
        for index, status in enumerate(LIFECYCLE_STATUSES)
    ) + (
        _record("rejected", minutes=len(LIFECYCLE_STATUSES)),
        _record("rejected", minutes=len(LIFECYCLE_STATUSES) + 1),
    )

    report = build_paper_order_lifecycle_db_history_report(
        tuple(reversed(records)),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    counts = _status_counts(report.lifecycle_status_rows)
    assert tuple(counts) == LIFECYCLE_STATUSES
    assert counts == {
        status: 3 if status == "rejected" else 1 for status in LIFECYCLE_STATUSES
    }
    assert report.latest_lifecycle_status == "rejected"
    assert report.latest_same_status_streak == 3
    assert report.terminal_record_count == 7
    assert report.nonterminal_record_count == 4


def test_duplicate_generated_at_count_counts_extra_records_per_timestamp() -> None:
    timestamp = datetime(2026, 6, 25, 9, 0, tzinfo=UTC)
    first = _record("paper_filled", minutes=0, fill_notional=Decimal("1.000000"))
    second = _record("risk_blocked", minutes=0)
    third = _record("human_approval_pending", minutes=0)
    object.__setattr__(first, "generated_at", timestamp)
    object.__setattr__(second, "generated_at", timestamp)
    object.__setattr__(third, "generated_at", timestamp)

    report = build_paper_order_lifecycle_db_history_report(
        (third, first, second),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.duplicate_generated_at_count == 2
    assert report.latest_lifecycle_status == "risk_blocked"


def test_nonempty_history_can_report_empty_reason_code_counts() -> None:
    report = build_paper_order_lifecycle_db_history_report(
        (
            _record(
                "paper_filled",
                minutes=1,
                fill_notional=Decimal("1.000000"),
                reason_codes=(),
            ),
        ),
        config=CONFIG,
        generated_at=GENERATED_AT,
    )

    assert report.reason_code_counts == ()


def test_history_dataclasses_are_frozen_validate_exact_types_and_hard_flags() -> None:
    report = build_paper_order_lifecycle_db_history_report(
        (
            _record(
                "paper_filled",
                minutes=1,
                fill_notional=Decimal("1.000000"),
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
        replace(PaperOrderLifecycleDbHistoryStatusRow("paper_filled", 1), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(PaperOrderLifecycleDbHistoryReasonCodeCount("reason", 1), readonly=False)
    with pytest.raises(ValueError, match="config must be a PaperOrderLifecycleDbHistoryConfig"):
        build_paper_order_lifecycle_db_history_report(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="records must contain PaperOrderLifecycleRecord values"):
        build_paper_order_lifecycle_db_history_report(
            (object(),),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="source record readonly"):
        bad_record = _record("risk_blocked", minutes=2)
        object.__setattr__(bad_record, "readonly", False)
        build_paper_order_lifecycle_db_history_report(
            (bad_record,),
            config=CONFIG,
            generated_at=GENERATED_AT,
        )


def test_history_dataclasses_do_not_support_subclassing() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadConfig(PaperOrderLifecycleDbHistoryConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadStatusRow(PaperOrderLifecycleDbHistoryStatusRow):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReasonCount(PaperOrderLifecycleDbHistoryReasonCodeCount):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(PaperOrderLifecycleDbHistoryReport):
            pass
