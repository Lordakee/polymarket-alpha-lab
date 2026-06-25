"""Tests for paper order lifecycle DB-API store."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_order_lifecycle import (
    PaperOrderLifecycleRecord,
    build_paper_order_lifecycle_record,
)
from polymarket_alpha_lab.paper_order_lifecycle_db_row import (
    PaperOrderLifecycleDbRow,
    paper_order_lifecycle_record_to_db_row,
)
from polymarket_alpha_lab.paper_order_lifecycle_store import (
    DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE,
    PaperOrderLifecycleInsertResult,
    insert_paper_order_lifecycle_record,
    insert_paper_order_lifecycle_record_with_result,
    load_paper_order_lifecycle_records,
)
from tests.test_paper_autonomous_screening_decision_support_gate_transition import (
    _gate_report,
)
from polymarket_alpha_lab.paper_autonomous_proposal import (
    build_paper_autonomous_proposal_report,
)
from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate import (
    build_paper_autonomous_proposal_risk_gate_report,
)
from polymarket_alpha_lab.paper_broker import (
    build_paper_broker_execution_record,
)


def _lifecycle_record(*, gate_status: str = "pass") -> PaperOrderLifecycleRecord:
    gate = _gate_report(generated_at=datetime(2026, 6, 24, tzinfo=UTC), gate_status=gate_status)
    proposal = build_paper_autonomous_proposal_report(
        gate_report=gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    risk_gate = build_paper_autonomous_proposal_risk_gate_report(
        proposal_report=proposal,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    broker = build_paper_broker_execution_record(
        risk_gate_report=risk_gate,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )
    return build_paper_order_lifecycle_record(
        broker_record=broker,
        generated_at=datetime(2026, 6, 25, tzinfo=UTC),
    )


class _FakeCursor:
    def __init__(self, rowcount: int = 1) -> None:
        self.rowcount = rowcount
        self._closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        pass

    def fetchall(self) -> list[Any]:
        return []

    def close(self) -> None:
        self._closed = True


class _FakeConnection:
    def __init__(self, rowcount: int = 1) -> None:
        self._rowcount = rowcount

    def cursor(self) -> _FakeCursor:
        return _FakeCursor(self._rowcount)


def test_default_table_name() -> None:
    assert DEFAULT_PAPER_ORDER_LIFECYCLE_RECORDS_TABLE == "paper_order_lifecycle_records"


def test_insert_result_frozen() -> None:
    record = _lifecycle_record()
    row = paper_order_lifecycle_record_to_db_row(record)
    result = PaperOrderLifecycleInsertResult(row=row, inserted=True)
    assert result.inserted is True
    assert result.row is row


def test_insert_result_rejects_non_bool_inserted() -> None:
    record = _lifecycle_record()
    row = paper_order_lifecycle_record_to_db_row(record)
    with pytest.raises(ValueError, match="inserted must be a bool"):
        PaperOrderLifecycleInsertResult(row=row, inserted="yes")  # type: ignore[arg-type]


def test_insert_result_rejects_wrong_row_type() -> None:
    with pytest.raises(ValueError, match="PaperOrderLifecycleDbRow"):
        PaperOrderLifecycleInsertResult(row="not_a_row", inserted=True)  # type: ignore[arg-type]


def test_insert_returns_row() -> None:
    record = _lifecycle_record()
    conn = _FakeConnection(rowcount=1)
    result = insert_paper_order_lifecycle_record(conn, record)
    assert isinstance(result, PaperOrderLifecycleDbRow)


def test_insert_with_result_returns_insert_result() -> None:
    record = _lifecycle_record()
    conn = _FakeConnection(rowcount=1)
    result = insert_paper_order_lifecycle_record_with_result(conn, record)
    assert isinstance(result, PaperOrderLifecycleInsertResult)
    assert result.inserted is True


def test_insert_dedup_returns_inserted_false() -> None:
    record = _lifecycle_record()
    conn = _FakeConnection(rowcount=0)
    result = insert_paper_order_lifecycle_record_with_result(conn, record)
    assert result.inserted is False


def test_insert_rejects_bad_table_name() -> None:
    record = _lifecycle_record()
    conn = _FakeConnection()
    with pytest.raises(ValueError, match="simple lowercase identifier"):
        insert_paper_order_lifecycle_record(conn, record, table_name="DROP TABLE;")


def test_load_returns_empty_tuple() -> None:
    conn = _FakeConnection(rowcount=0)
    records = load_paper_order_lifecycle_records(conn)
    assert records == ()


def test_load_rejects_bad_table_name() -> None:
    conn = _FakeConnection()
    with pytest.raises(ValueError, match="simple lowercase identifier"):
        load_paper_order_lifecycle_records(conn, table_name="123bad")


def test_load_rejects_non_positive_limit() -> None:
    conn = _FakeConnection()
    with pytest.raises(ValueError, match="must be positive"):
        load_paper_order_lifecycle_records(conn, limit=0)


def test_load_rejects_blank_lifecycle_status() -> None:
    conn = _FakeConnection()
    with pytest.raises(ValueError, match="canonical nonblank"):
        load_paper_order_lifecycle_records(conn, lifecycle_status="")
