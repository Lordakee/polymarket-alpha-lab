"""Tests for paper execution reconciliation lifecycle loader node."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab.paper_execution_reconciliation import (
    PaperExecutionReconciliationConfig,
    PaperExecutionReconciliationReport,
    build_paper_execution_reconciliation_report,
)
from polymarket_alpha_lab.paper_order_lifecycle import PaperOrderLifecycleRecord


GENERATED_AT = datetime(2026, 6, 25, 12, 0, tzinfo=UTC)


class NoSqlConnection:
    cursor_count = 0
    commit_count = 0
    rollback_count = 0
    write_count = 0

    def cursor(self) -> object:
        self.cursor_count += 1
        raise AssertionError("loader must not open cursors directly")

    def commit(self) -> None:
        self.commit_count += 1
        raise AssertionError("loader must not commit")

    def rollback(self) -> None:
        self.rollback_count += 1
        raise AssertionError("loader must not rollback")

    def write(self, *_args: object, **_kwargs: object) -> None:
        self.write_count += 1
        raise AssertionError("loader must not write")


def _lifecycle_record(
    *,
    lifecycle_status: str = "paper_filled",
    source_execution_notional: Decimal = Decimal("12.500000"),
    fill_notional: Decimal = Decimal("12.500000"),
) -> PaperOrderLifecycleRecord:
    return PaperOrderLifecycleRecord(
        generated_at=GENERATED_AT,
        config_version="paper-order-lifecycle-v0",
        lifecycle_status=lifecycle_status,
        recommended_next_step="record_paper_outcome",
        source_execution_status="paper_submitted",
        source_execution_notional=source_execution_notional,
        fill_notional=fill_notional,
        is_terminal=True,
        reason_codes=("paper_order_lifecycle_filled",),
    )


def _unsafe_lifecycle_record(**overrides: object) -> PaperOrderLifecycleRecord:
    values: dict[str, object] = {
        "generated_at": GENERATED_AT,
        "config_version": "paper-order-lifecycle-v0",
        "lifecycle_status": "paper_filled",
        "recommended_next_step": "record_paper_outcome",
        "source_execution_status": "paper_submitted",
        "source_execution_notional": Decimal("12.500000"),
        "fill_notional": Decimal("12.500000"),
        "is_terminal": True,
        "reason_codes": ("paper_order_lifecycle_filled",),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    record = object.__new__(PaperOrderLifecycleRecord)
    for field_name, value in values.items():
        object.__setattr__(record, field_name, value)
    return record


def test_load_reconciliation_reads_lifecycle_records_and_calls_reducer() -> None:
    from polymarket_alpha_lab.paper_execution_reconciliation_load import (
        load_paper_execution_reconciliation_report_from_lifecycle,
    )

    connection = NoSqlConnection()
    record = _lifecycle_record()
    config = PaperExecutionReconciliationConfig(
        config_version="paper-execution-reconciliation-test-v0",
    )
    calls: list[tuple[str, dict[str, Any]]] = []

    def lifecycle_loader(received_connection: object, **kwargs: Any) -> tuple[object, ...]:
        calls.append(("loader", {"connection": received_connection, **kwargs}))
        return (record,)

    def reconciliation_builder(**kwargs: Any) -> PaperExecutionReconciliationReport:
        calls.append(("builder", dict(kwargs)))
        return build_paper_execution_reconciliation_report(**kwargs)

    report = load_paper_execution_reconciliation_report_from_lifecycle(
        connection,
        lifecycle_status=None,
        lifecycle_limit=5,
        lifecycle_table_name="paper_order_lifecycle_records",
        generated_at=GENERATED_AT,
        config=config,
        lifecycle_loader=lifecycle_loader,
        reconciliation_report_builder=reconciliation_builder,
    )

    assert type(report) is PaperExecutionReconciliationReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "paper-execution-reconciliation-test-v0"
    assert report.total_positions == 1
    assert report.total_fill_notional == Decimal("12.500000")
    assert calls == [
        (
            "loader",
            {
                "connection": connection,
                "lifecycle_status": None,
                "limit": 5,
                "table_name": "paper_order_lifecycle_records",
            },
        ),
        (
            "builder",
            {
                "lifecycle_records": (record,),
                "config": config,
                "generated_at": GENERATED_AT,
            },
        ),
    ]
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.write_count == 0


def test_load_reconciliation_rejects_duck_typed_lifecycle_records_before_reducer() -> None:
    from polymarket_alpha_lab.paper_execution_reconciliation_load import (
        load_paper_execution_reconciliation_report_from_lifecycle,
    )

    builder_calls = 0
    duck_typed_record = SimpleNamespace(
        lifecycle_status="paper_filled",
        source_execution_notional=Decimal("12.500000"),
        fill_notional=Decimal("12.500000"),
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    def reconciliation_builder(**_kwargs: Any) -> object:
        nonlocal builder_calls
        builder_calls += 1
        raise AssertionError("reducer must not run after lifecycle type rejection")

    with pytest.raises(
        ValueError,
        match="lifecycle_records.0 must be exactly PaperOrderLifecycleRecord",
    ):
        load_paper_execution_reconciliation_report_from_lifecycle(
            NoSqlConnection(),
            lifecycle_limit=1,
            lifecycle_table_name="paper_order_lifecycle_records",
            generated_at=GENERATED_AT,
            config=PaperExecutionReconciliationConfig(),
            lifecycle_loader=lambda _connection, **_kwargs: (duck_typed_record,),
            reconciliation_report_builder=reconciliation_builder,
        )

    assert builder_calls == 0


def test_load_reconciliation_rejects_non_hard_flagged_lifecycle_records() -> None:
    from polymarket_alpha_lab.paper_execution_reconciliation_load import (
        load_paper_execution_reconciliation_report_from_lifecycle,
    )

    builder_calls = 0
    bad_record = _unsafe_lifecycle_record(readonly=False)

    def reconciliation_builder(**_kwargs: Any) -> object:
        nonlocal builder_calls
        builder_calls += 1
        raise AssertionError("reducer must not run after hard-flag rejection")

    with pytest.raises(ValueError, match="lifecycle_records.0 must be readonly"):
        load_paper_execution_reconciliation_report_from_lifecycle(
            NoSqlConnection(),
            lifecycle_limit=1,
            lifecycle_table_name="paper_order_lifecycle_records",
            generated_at=GENERATED_AT,
            config=PaperExecutionReconciliationConfig(),
            lifecycle_loader=lambda _connection, **_kwargs: (bad_record,),
            reconciliation_report_builder=reconciliation_builder,
        )

    assert builder_calls == 0


def test_load_reconciliation_rejects_bad_reducer_return_type() -> None:
    from polymarket_alpha_lab.paper_execution_reconciliation_load import (
        load_paper_execution_reconciliation_report_from_lifecycle,
    )

    with pytest.raises(
        ValueError,
        match="reconciliation report must be a PaperExecutionReconciliationReport",
    ):
        load_paper_execution_reconciliation_report_from_lifecycle(
            NoSqlConnection(),
            lifecycle_limit=1,
            lifecycle_table_name="paper_order_lifecycle_records",
            generated_at=GENERATED_AT,
            config=PaperExecutionReconciliationConfig(),
            lifecycle_loader=lambda _connection, **_kwargs: (_lifecycle_record(),),
            reconciliation_report_builder=lambda **_kwargs: SimpleNamespace(
                paper_only=True,
                report_only=True,
                readonly=True,
            ),
        )
