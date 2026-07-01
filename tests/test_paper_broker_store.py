"""Tests for paper broker execution DB-API store."""

from __future__ import annotations

import importlib
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_broker import PaperBrokerExecutionRecord
from polymarket_alpha_lab.paper_broker_db_row import (
    PaperBrokerExecutionDbRow,
    paper_broker_execution_record_to_db_row,
)


GENERATED_AT = datetime(2026, 6, 25, 10, 30, tzinfo=UTC)
CONFIG_VERSION = "paper-broker-store-test-v0"
SELECT_COLUMNS = (
    "record_sha256",
    "generated_at",
    "config_version",
    "execution_status",
    "recommended_next_step",
    "source_gate_status",
    "source_proposal_count",
    "source_proposal_total_notional",
    "execution_notional",
    "reason_codes",
    "payload",
    "paper_only",
    "report_only",
    "readonly",
)
PYTHON_ROW_ATTR_BY_DB_COLUMN = {
    "reason_codes": "reason_codes_json",
    "payload": "payload_json",
}


def d(value: str) -> Decimal:
    return Decimal(value)


def _store() -> Any:
    try:
        return importlib.import_module("polymarket_alpha_lab.paper_broker_store")
    except ModuleNotFoundError as exc:
        pytest.fail(f"store module missing: {exc}")


def _record() -> PaperBrokerExecutionRecord:
    return PaperBrokerExecutionRecord(
        generated_at=GENERATED_AT,
        config_version=CONFIG_VERSION,
        execution_status="paper_submitted",
        recommended_next_step="route_to_paper_order_lifecycle",
        source_gate_status="pass",
        source_proposal_count=2,
        source_proposal_total_notional=d("42.500000"),
        execution_notional=d("42.500000"),
        reason_codes=("paper_broker_execution_submitted",),
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


class FakeCursor:
    def __init__(
        self,
        *,
        rowcount: int = 1,
        records: tuple[Any, ...] = (),
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rowcount = rowcount
        self.records = records
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        if self.execute_error is not None:
            raise self.execute_error
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.records

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        *,
        rowcount: int = 1,
        records: tuple[Any, ...] = (),
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rowcount=rowcount,
            records=records,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1


def test_default_table_name_and_public_api() -> None:
    store = _store()

    assert (
        store.DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE
        == "paper_broker_execution_records"
    )
    assert set(store.__all__) == {
        "DEFAULT_PAPER_BROKER_EXECUTION_RECORDS_TABLE",
        "PaperBrokerExecutionInsertResult",
        "insert_paper_broker_execution_record",
        "insert_paper_broker_execution_record_with_result",
        "load_paper_broker_execution_records",
    }


def test_insert_result_validates_row_and_inserted_flag() -> None:
    store = _store()
    row = paper_broker_execution_record_to_db_row(_record())

    result = store.PaperBrokerExecutionInsertResult(row=row, inserted=True)

    assert result.row == row
    assert result.inserted is True
    with pytest.raises(ValueError, match="PaperBrokerExecutionDbRow"):
        store.PaperBrokerExecutionInsertResult(row="not-row", inserted=True)
    with pytest.raises(ValueError, match="inserted must be a bool"):
        store.PaperBrokerExecutionInsertResult(row=row, inserted=1)


def test_insert_uses_parameterized_db_api_insert_with_row_codec_values() -> None:
    store = _store()
    record = _record()
    expected_row = paper_broker_execution_record_to_db_row(record)
    connection = FakeConnection(rowcount=1)

    result = store.insert_paper_broker_execution_record_with_result(
        connection,
        record,
        table_name="paper_broker_execution_archive",
    )

    assert result == store.PaperBrokerExecutionInsertResult(
        row=expected_row,
        inserted=True,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_broker_execution_archive (
            record_sha256,
            generated_at,
            config_version,
            execution_status,
            recommended_next_step,
            source_gate_status,
            source_proposal_count,
            source_proposal_total_notional,
            execution_notional,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (record_sha256) DO NOTHING
        """,
    )
    assert params == tuple(
        getattr(expected_row, PYTHON_ROW_ATTR_BY_DB_COLUMN.get(column, column))
        for column in SELECT_COLUMNS
    )
    assert type(params[1]) is datetime
    assert params[1] == GENERATED_AT
    assert type(params[7]) is Decimal
    assert type(params[8]) is Decimal
    assert params[9] == expected_row.reason_codes_json
    assert params[10] == expected_row.payload_json
    assert params[10]["source_proposal_total_notional"] == "42.500000"
    assert params[10]["execution_notional"] == "42.500000"


def test_insert_convenience_returns_row_and_dedup_result_reports_false() -> None:
    store = _store()
    record = _record()

    inserted = store.insert_paper_broker_execution_record(
        FakeConnection(rowcount=1),
        record,
    )
    dedup = store.insert_paper_broker_execution_record_with_result(
        FakeConnection(rowcount=0),
        record,
    )

    assert isinstance(inserted, PaperBrokerExecutionDbRow)
    assert dedup.row == paper_broker_execution_record_to_db_row(record)
    assert dedup.inserted is False


def test_insert_rejects_unexpected_rowcount() -> None:
    store = _store()

    with pytest.raises(ValueError, match="rowcount must be 0 or 1"):
        store.insert_paper_broker_execution_record_with_result(
            FakeConnection(rowcount=2),
            _record(),
        )


def test_insert_propagates_cursor_close_error_after_success() -> None:
    store = _store()
    connection = FakeConnection(
        rowcount=1,
        close_error=RuntimeError("cursor close failed"),
    )

    with pytest.raises(RuntimeError, match="cursor close failed"):
        store.insert_paper_broker_execution_record_with_result(
            connection,
            _record(),
        )

    assert connection.cursor_instance.closed is True


def test_insert_execute_error_wins_when_cursor_close_also_fails() -> None:
    store = _store()
    execute_error = RuntimeError("insert execute failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=RuntimeError("cursor close failed"),
    )

    with pytest.raises(RuntimeError, match="insert execute failed") as exc_info:
        store.insert_paper_broker_execution_record_with_result(
            connection,
            _record(),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    "table_name",
    (
        "paper_broker_execution_records; drop table users",
        "PaperBrokerExecutionRecords",
        "paper.broker.execution.records",
        "_paper_broker_execution_records",
        "paper_broker_execution_records_",
    ),
)
def test_insert_rejects_unsafe_table_name_without_executing_sql(
    table_name: str,
) -> None:
    store = _store()
    connection = FakeConnection()

    with pytest.raises(ValueError, match="simple lowercase identifier"):
        store.insert_paper_broker_execution_record(
            connection,
            _record(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_filters_orders_and_reconstructs_records_from_db_rows() -> None:
    store = _store()
    record = _record()
    row = paper_broker_execution_record_to_db_row(record)
    row_dict = {
        column: getattr(row, PYTHON_ROW_ATTR_BY_DB_COLUMN.get(column, column))
        for column in SELECT_COLUMNS
    }
    connection = FakeConnection(records=(row, row_dict))

    loaded = store.load_paper_broker_execution_records(
        connection,
        config_version=CONFIG_VERSION,
        execution_status="paper_submitted",
        source_gate_status="pass",
        limit=5,
        table_name="paper_broker_execution_archive",
    )

    assert loaded == (record, record)
    assert connection.cursor_count == 1
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            record_sha256,
            generated_at,
            config_version,
            execution_status,
            recommended_next_step,
            source_gate_status,
            source_proposal_count,
            source_proposal_total_notional,
            execution_notional,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        FROM paper_broker_execution_archive
        WHERE config_version = %s AND execution_status = %s AND source_gate_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, record_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (CONFIG_VERSION, "paper_submitted", "pass", 5)


def test_load_propagates_cursor_close_error_after_success() -> None:
    store = _store()
    record = _record()
    row = paper_broker_execution_record_to_db_row(record)
    connection = FakeConnection(
        records=(row,),
        close_error=RuntimeError("cursor close failed"),
    )

    with pytest.raises(RuntimeError, match="cursor close failed"):
        store.load_paper_broker_execution_records(connection)

    assert connection.cursor_instance.closed is True


def test_load_fetchall_error_wins_when_cursor_close_also_fails() -> None:
    store = _store()
    fetchall_error = RuntimeError("load fetchall failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=RuntimeError("cursor close failed"),
    )

    with pytest.raises(RuntimeError, match="load fetchall failed") as exc_info:
        store.load_paper_broker_execution_records(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.closed is True


def test_load_rejects_invalid_filters_without_executing_sql() -> None:
    store = _store()
    connection = FakeConnection()

    with pytest.raises(ValueError, match="simple lowercase identifier"):
        store.load_paper_broker_execution_records(
            connection,
            table_name="123bad",
        )
    with pytest.raises(ValueError, match="canonical nonblank"):
        store.load_paper_broker_execution_records(
            connection,
            config_version="",
        )
    with pytest.raises(ValueError, match="canonical nonblank"):
        store.load_paper_broker_execution_records(
            connection,
            execution_status=" paper_submitted",
        )
    with pytest.raises(ValueError, match="must be positive"):
        store.load_paper_broker_execution_records(
            connection,
            limit=0,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
