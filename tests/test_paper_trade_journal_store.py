from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


@dataclass(frozen=True)
class FakePaperTradeRecord:
    packet_id: str
    condition_id: str
    token_id: str


@dataclass(frozen=True)
class FakePaperTradeJournalDbRow:
    record_sha256: str
    packet_id: str
    decision_timestamp_utc: datetime
    condition_id: str
    token_id: str
    market_slug: str
    outcome_name: str
    order_side: str
    fill_status: str
    fill_filled_size: Decimal
    fill_average_price: Decimal
    account_equity_before_trade: Decimal
    payload_json: dict[str, Any]
    paper_only: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False
        self.close_count = 0
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self) -> None:
        self.close_count += 1
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
        self.cursor_count = 0
        self.commit_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.paper_trade_journal_db_row")

    def to_db_row(record: FakePaperTradeRecord) -> FakePaperTradeJournalDbRow:
        return FakePaperTradeJournalDbRow(
            record_sha256="a" * 64,
            packet_id=record.packet_id,
            decision_timestamp_utc=datetime(2026, 6, 19, 12, 30, tzinfo=UTC),
            condition_id=record.condition_id,
            token_id=record.token_id,
            market_slug="example-market",
            outcome_name="Yes",
            order_side="buy",
            fill_status="complete",
            fill_filled_size=Decimal("100"),
            fill_average_price=Decimal("0.514"),
            account_equity_before_trade=Decimal("10000"),
            payload_json={
                "packet_id": record.packet_id,
                "condition_id": record.condition_id,
                "token_id": record.token_id,
            },
        )

    def from_db_row(row: FakePaperTradeJournalDbRow) -> FakePaperTradeRecord:
        return FakePaperTradeRecord(
            packet_id=row.packet_id,
            condition_id=row.condition_id,
            token_id=row.token_id,
        )

    companion.PaperTradeJournalDbRow = FakePaperTradeJournalDbRow
    companion.paper_trade_record_to_db_row = to_db_row
    companion.paper_trade_record_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_trade_journal_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_trade_journal_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_trade_journal_store")


def test_insert_paper_trade_record_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    record = FakePaperTradeRecord(
        packet_id="packet-1",
        condition_id="0xabc",
        token_id="111",
    )

    inserted = store_module.insert_paper_trade_record(connection, record)

    assert inserted == FakePaperTradeJournalDbRow(
        record_sha256="a" * 64,
        packet_id="packet-1",
        decision_timestamp_utc=datetime(2026, 6, 19, 12, 30, tzinfo=UTC),
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        outcome_name="Yes",
        order_side="buy",
        fill_status="complete",
        fill_filled_size=Decimal("100"),
        fill_average_price=Decimal("0.514"),
        account_equity_before_trade=Decimal("10000"),
        payload_json={
            "packet_id": "packet-1",
            "condition_id": "0xabc",
            "token_id": "111",
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_trade_journal_records (
            record_sha256,
            packet_id,
            decision_timestamp_utc,
            condition_id,
            token_id,
            market_slug,
            outcome_name,
            order_side,
            fill_status,
            fill_filled_size,
            fill_average_price,
            account_equity_before_trade,
            payload_json,
            paper_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (record_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        "packet-1",
        datetime(2026, 6, 19, 12, 30, tzinfo=UTC),
        "0xabc",
        "111",
        "example-market",
        "Yes",
        "buy",
        "complete",
        Decimal("100"),
        Decimal("0.514"),
        Decimal("10000"),
        {
            "packet_id": "packet-1",
            "condition_id": "0xabc",
            "token_id": "111",
        },
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_trade_record(
            connection,
            FakePaperTradeRecord(
                packet_id="packet-1",
                condition_id="0xabc",
                token_id="111",
            ),
            table_name="paper_trade_journal_records; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_paper_trade_record(
            connection,
            FakePaperTradeRecord(
                packet_id="packet-1",
                condition_id="0xabc",
                token_id="111",
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_insert_propagates_cursor_close_error_after_successful_execute(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_paper_trade_record(
            connection,
            FakePaperTradeRecord(
                packet_id="packet-1",
                condition_id="0xabc",
                token_id="111",
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


def test_load_paper_trade_records_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakePaperTradeJournalDbRow(
        record_sha256="b" * 64,
        packet_id="packet-2",
        decision_timestamp_utc=datetime(2026, 6, 19, 14, 0, tzinfo=UTC),
        condition_id="0xabc",
        token_id="111",
        market_slug="example-market",
        outcome_name="Yes",
        order_side="buy",
        fill_status="complete",
        fill_filled_size=Decimal("40"),
        fill_average_price=Decimal("0.510"),
        account_equity_before_trade=Decimal("10000"),
        payload_json={
            "packet_id": "packet-2",
            "condition_id": "0xabc",
            "token_id": "111",
        },
    )
    connection = FakeConnection(rows=(row,))

    records = store_module.load_paper_trade_records(
        connection,
        condition_id="0xabc",
        token_id="111",
        limit=25,
        table_name="paper_trade_archive",
    )

    assert records == (
        FakePaperTradeRecord(
            packet_id="packet-2",
            condition_id="0xabc",
            token_id="111",
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            record_sha256,
            packet_id,
            decision_timestamp_utc,
            condition_id,
            token_id,
            market_slug,
            outcome_name,
            order_side,
            fill_status,
            fill_filled_size,
            fill_average_price,
            account_equity_before_trade,
            payload_json,
            paper_only
        FROM paper_trade_archive
        WHERE condition_id = %s AND token_id = %s
        ORDER BY decision_timestamp_utc DESC, inserted_at DESC, record_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("0xabc", "111", 25)


def test_load_propagates_cursor_close_error_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_paper_trade_records(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


def test_load_preserves_fetchall_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_paper_trade_records(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_paper_trade_records_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    decision_timestamp = datetime(2026, 6, 19, 14, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                "packet-3",
                decision_timestamp,
                "0xdef",
                "222",
                "another-market",
                "No",
                "sell",
                "partial",
                Decimal("10"),
                Decimal("0.400"),
                Decimal("9000"),
                {
                    "packet_id": "packet-3",
                    "condition_id": "0xdef",
                    "token_id": "222",
                },
                True,
            ),
        ),
    )

    records = store_module.load_paper_trade_records(connection)

    assert records == (
        FakePaperTradeRecord(
            packet_id="packet-3",
            condition_id="0xdef",
            token_id="222",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_trade_journal_records"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"condition_id": ""}, "condition_id"),
        ({"condition_id": " 0xabc"}, "condition_id"),
        ({"token_id": ""}, "token_id"),
        ({"token_id": " 111"}, "token_id"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.load_paper_trade_records(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
