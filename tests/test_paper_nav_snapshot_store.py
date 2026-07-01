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
class FakeNavSnapshot:
    marked_at: datetime
    exit_nav: Decimal


@dataclass(frozen=True)
class FakeNavSnapshotDbRow:
    snapshot_sha256: str
    marked_at: datetime
    starting_cash: Decimal
    cash_balance: Decimal
    exit_nav: Decimal
    midpoint_nav: Decimal | None
    total_cost_basis: Decimal
    unrealized_exit_pnl: Decimal
    mark_count: int
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


def d(value: str) -> Decimal:
    return Decimal(value)


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.paper_nav_snapshot_db_row")

    def to_db_row(snapshot: FakeNavSnapshot) -> FakeNavSnapshotDbRow:
        return FakeNavSnapshotDbRow(
            snapshot_sha256="a" * 64,
            marked_at=snapshot.marked_at,
            starting_cash=d("100.00"),
            cash_balance=d("96.00"),
            exit_nav=snapshot.exit_nav,
            midpoint_nav=d("101.55"),
            total_cost_basis=d("4.00"),
            unrealized_exit_pnl=d("1.50"),
            mark_count=1,
            payload_json={
                "marked_at": snapshot.marked_at.isoformat(),
                "exit_nav": str(snapshot.exit_nav),
            },
        )

    def from_db_row(row: FakeNavSnapshotDbRow) -> FakeNavSnapshot:
        return FakeNavSnapshot(marked_at=row.marked_at, exit_nav=row.exit_nav)

    companion.PaperNavSnapshotDbRow = FakeNavSnapshotDbRow
    companion.paper_nav_snapshot_to_db_row = to_db_row
    companion.paper_nav_snapshot_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_nav_snapshot_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_nav_snapshot_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_nav_snapshot_store")


def test_insert_paper_nav_snapshot_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    snapshot = FakeNavSnapshot(
        marked_at=datetime(2026, 6, 19, 18, 15, tzinfo=UTC),
        exit_nav=d("101.50"),
    )

    inserted = store_module.insert_paper_nav_snapshot(connection, snapshot)

    assert inserted == FakeNavSnapshotDbRow(
        snapshot_sha256="a" * 64,
        marked_at=snapshot.marked_at,
        starting_cash=d("100.00"),
        cash_balance=d("96.00"),
        exit_nav=d("101.50"),
        midpoint_nav=d("101.55"),
        total_cost_basis=d("4.00"),
        unrealized_exit_pnl=d("1.50"),
        mark_count=1,
        payload_json={
            "marked_at": snapshot.marked_at.isoformat(),
            "exit_nav": "101.50",
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_nav_snapshots (
            snapshot_sha256,
            marked_at,
            starting_cash,
            cash_balance,
            exit_nav,
            midpoint_nav,
            total_cost_basis,
            unrealized_exit_pnl,
            mark_count,
            payload_json,
            paper_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        snapshot.marked_at,
        d("100.00"),
        d("96.00"),
        d("101.50"),
        d("101.55"),
        d("4.00"),
        d("1.50"),
        1,
        {
            "marked_at": snapshot.marked_at.isoformat(),
            "exit_nav": "101.50",
        },
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_nav_snapshot(
            connection,
            FakeNavSnapshot(
                marked_at=datetime(2026, 6, 19, 18, 15, tzinfo=UTC),
                exit_nav=d("101.50"),
            ),
            table_name="paper_nav_snapshots; drop table users",
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
        store_module.insert_paper_nav_snapshot(
            connection,
            FakeNavSnapshot(
                marked_at=datetime(2026, 6, 19, 18, 15, tzinfo=UTC),
                exit_nav=d("101.50"),
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_insert_preserves_execute_error_when_cursor_close_raises_base_exception(
    store_module: types.ModuleType,
) -> None:
    class NonExceptionCloseFailure(BaseException):
        pass

    execute_error = RuntimeError("execute failed")
    close_error = NonExceptionCloseFailure("close interrupted")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,  # type: ignore[arg-type]
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_paper_nav_snapshot(
            connection,
            FakeNavSnapshot(
                marked_at=datetime(2026, 6, 19, 18, 15, tzinfo=UTC),
                exit_nav=d("101.50"),
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
        store_module.insert_paper_nav_snapshot(
            connection,
            FakeNavSnapshot(
                marked_at=datetime(2026, 6, 19, 18, 15, tzinfo=UTC),
                exit_nav=d("101.50"),
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


def test_load_paper_nav_snapshots_limits_with_params_and_maps_dict_rows(
    store_module: types.ModuleType,
) -> None:
    marked_at = datetime(2026, 6, 19, 18, 20, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "snapshot_sha256": "b" * 64,
                "marked_at": marked_at,
                "starting_cash": d("100.00"),
                "cash_balance": d("97.00"),
                "exit_nav": d("102.00"),
                "midpoint_nav": None,
                "total_cost_basis": d("3.00"),
                "unrealized_exit_pnl": d("2.00"),
                "mark_count": 1,
                "payload_json": {
                    "marked_at": "2026-06-19T18:20:00+00:00",
                    "exit_nav": "102.00",
                },
                "paper_only": True,
            },
        ),
    )

    snapshots = store_module.load_paper_nav_snapshots(
        connection,
        limit=25,
        table_name="nav_snapshot_archive",
    )

    assert snapshots == (FakeNavSnapshot(marked_at=marked_at, exit_nav=d("102.00")),)
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            snapshot_sha256,
            marked_at,
            starting_cash,
            cash_balance,
            exit_nav,
            midpoint_nav,
            total_cost_basis,
            unrealized_exit_pnl,
            mark_count,
            payload_json,
            paper_only
        FROM nav_snapshot_archive
        ORDER BY marked_at DESC, snapshot_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (25,)


def test_load_propagates_cursor_close_error_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_paper_nav_snapshots(connection)

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
        store_module.load_paper_nav_snapshots(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_paper_nav_snapshots_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    marked_at = datetime(2026, 6, 19, 18, 30, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                marked_at,
                d("100.00"),
                d("98.00"),
                d("103.00"),
                d("103.10"),
                d("2.00"),
                d("3.00"),
                1,
                {
                    "marked_at": "2026-06-19T18:30:00+00:00",
                    "exit_nav": "103.00",
                },
                True,
            ),
        ),
    )

    snapshots = store_module.load_paper_nav_snapshots(connection)

    assert snapshots == (FakeNavSnapshot(marked_at=marked_at, exit_nav=d("103.00")),)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_nav_snapshots"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
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
        store_module.load_paper_nav_snapshots(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
