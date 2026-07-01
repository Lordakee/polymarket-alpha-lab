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
class FakeReport:
    generated_at: datetime
    config_version: str
    trade_count: int


@dataclass(frozen=True)
class FakeDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    trade_count: int
    row_count: int
    market_count: int
    filled_count: int
    complete_fill_count: int
    partial_fill_count: int
    resolved_count: int | None
    pending_count: int | None
    realized_win_count: int | None
    realized_loss_count: int | None
    total_requested_size: Decimal
    total_filled_size: Decimal
    total_unfilled_size: Decimal
    total_notional: Decimal
    first_trade_decision_at: datetime | None
    latest_trade_decision_at: datetime | None
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False
        self.execute_error: BaseException | None = None
        self.close_error: BaseException | None = None

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.cursor_instance = FakeCursor(rows)
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


def d(value: str) -> Decimal:
    return Decimal(value)


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _fake_db_row(report: FakeReport) -> FakeDbRow:
    return FakeDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        trade_count=report.trade_count,
        row_count=2,
        market_count=2,
        filled_count=4,
        complete_fill_count=2,
        partial_fill_count=2,
        resolved_count=2,
        pending_count=2,
        realized_win_count=1,
        realized_loss_count=1,
        total_requested_size=d("350"),
        total_filled_size=d("220"),
        total_unfilled_size=d("130"),
        total_notional=d("98.0000"),
        first_trade_decision_at=datetime(2026, 6, 18, 9, 1, 30, tzinfo=UTC),
        latest_trade_decision_at=datetime(2026, 6, 18, 9, 4, 30, tzinfo=UTC),
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "trade_count": report.trade_count,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.paper_trade_attribution_db_row")

    def to_db_row(report: FakeReport) -> FakeDbRow:
        return _fake_db_row(report)

    def from_db_row(row: FakeDbRow) -> FakeReport:
        return FakeReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            trade_count=row.trade_count,
        )

    companion.PaperTradeAttributionReportDbRow = FakeDbRow
    companion.paper_trade_attribution_report_to_db_row = to_db_row
    companion.paper_trade_attribution_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_trade_attribution_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_trade_attribution_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_trade_attribution_store")


def test_insert_report_uses_parameterized_insert_without_owning_transaction(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    connection = FakeConnection()
    report = FakeReport(
        generated_at=generated_at,
        config_version="paper-trade-attribution-db-v0",
        trade_count=4,
    )

    inserted = store_module.insert_paper_trade_attribution_report(connection, report)

    assert inserted == _fake_db_row(report)
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_trade_attribution_reports (
            report_sha256,
            generated_at,
            config_version,
            trade_count,
            row_count,
            market_count,
            filled_count,
            complete_fill_count,
            partial_fill_count,
            resolved_count,
            pending_count,
            realized_win_count,
            realized_loss_count,
            total_requested_size,
            total_filled_size,
            total_unfilled_size,
            total_notional,
            first_trade_decision_at,
            latest_trade_decision_at,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        generated_at,
        "paper-trade-attribution-db-v0",
        4,
        2,
        2,
        4,
        2,
        2,
        2,
        2,
        1,
        1,
        d("350"),
        d("220"),
        d("130"),
        d("98.0000"),
        datetime(2026, 6, 18, 9, 1, 30, tzinfo=UTC),
        datetime(2026, 6, 18, 9, 4, 30, tzinfo=UTC),
        {
            "generated_at": generated_at.isoformat(),
            "config_version": "paper-trade-attribution-db-v0",
            "trade_count": 4,
        },
        True,
        True,
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_trade_attribution_report(
            connection,
            FakeReport(
                generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
                config_version="paper-trade-attribution-db-v0",
                trade_count=0,
            ),
            table_name="paper_trade_attribution_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    execute_error = RuntimeError("execute failed")
    connection.cursor_instance.execute_error = execute_error
    connection.cursor_instance.close_error = RuntimeError("close failed")

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.insert_paper_trade_attribution_report(
            connection,
            FakeReport(
                generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
                config_version="paper-trade-attribution-db-v0",
                trade_count=4,
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_insert_success_close_propagates_after_execute(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    close_error = RuntimeError("close failed")
    connection.cursor_instance.close_error = close_error

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.insert_paper_trade_attribution_report(
            connection,
            FakeReport(
                generated_at=datetime(2026, 6, 18, 12, 0, tzinfo=UTC),
                config_version="paper-trade-attribution-db-v0",
                trade_count=4,
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_reports_filters_limits_orders_and_maps_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "b" * 64,
                "generated_at": generated_at,
                "config_version": "paper-trade-attribution-db-v0",
                "trade_count": 4,
                "row_count": 2,
                "market_count": 2,
                "filled_count": 4,
                "complete_fill_count": 2,
                "partial_fill_count": 2,
                "resolved_count": 2,
                "pending_count": 2,
                "realized_win_count": 1,
                "realized_loss_count": 1,
                "total_requested_size": d("350"),
                "total_filled_size": d("220"),
                "total_unfilled_size": d("130"),
                "total_notional": d("98.0000"),
                "first_trade_decision_at": datetime(2026, 6, 18, 9, 1, 30, tzinfo=UTC),
                "latest_trade_decision_at": datetime(2026, 6, 18, 9, 4, 30, tzinfo=UTC),
                "payload_json": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-trade-attribution-db-v0",
                    "trade_count": 4,
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_trade_attribution_reports(
        connection,
        config_version="paper-trade-attribution-db-v0",
        limit=25,
        table_name="public.paper_trade_attribution_reports",
    )

    assert reports == (
        FakeReport(
            generated_at=generated_at,
            config_version="paper-trade-attribution-db-v0",
            trade_count=4,
        ),
    )
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            trade_count,
            row_count,
            market_count,
            filled_count,
            complete_fill_count,
            partial_fill_count,
            resolved_count,
            pending_count,
            realized_win_count,
            realized_loss_count,
            total_requested_size,
            total_filled_size,
            total_unfilled_size,
            total_notional,
            first_trade_decision_at,
            latest_trade_decision_at,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM public.paper_trade_attribution_reports
        WHERE config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-trade-attribution-db-v0", 25)


def test_load_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    execute_error = RuntimeError("execute failed")
    connection.cursor_instance.execute_error = execute_error
    connection.cursor_instance.close_error = RuntimeError("close failed")

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.load_paper_trade_attribution_reports(connection)

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_load_success_close_propagates_after_fetch(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    connection = FakeConnection(rows=(_fake_db_row(FakeReport(
        generated_at=generated_at,
        config_version="paper-trade-attribution-db-v0",
        trade_count=4,
    )),))
    close_error = RuntimeError("close failed")
    connection.cursor_instance.close_error = close_error

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_trade_attribution_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_operation_failure_close_swallowed_for_db_row_error(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=((),))
    connection.cursor_instance.close_error = RuntimeError("close failed")

    with pytest.raises(
        ValueError,
        match="DB row must contain selected paper trade attribution columns",
    ):
        store_module.load_paper_trade_attribution_reports(connection)

    assert connection.cursor_instance.closed is True


def test_load_reports_accepts_positional_rows(store_module: types.ModuleType) -> None:
    generated_at = datetime(2026, 6, 18, 12, 30, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-trade-attribution-db-v0",
                0,
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                None,
                None,
                d("0"),
                d("0"),
                d("0"),
                d("0"),
                None,
                None,
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-trade-attribution-db-v0",
                    "trade_count": 0,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_trade_attribution_reports(connection)

    assert reports == (
        FakeReport(
            generated_at=generated_at,
            config_version="paper-trade-attribution-db-v0",
            trade_count=0,
        ),
    )


def test_load_reports_accepts_single_character_schema_and_table_names(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    reports = store_module.load_paper_trade_attribution_reports(
        connection,
        table_name="a.b",
    )

    assert reports == ()
    assert connection.cursor_count == 1
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert "FROM a.b" in normalize_sql(sql)
    assert params == ()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "Public.paper_trade_attribution_reports"}, "table_name"),
        ({"table_name": "public.attribution.reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "public." + ("a" * 64)}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-trade-attribution-db-v0"}, "config_version"),
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
        store_module.load_paper_trade_attribution_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
