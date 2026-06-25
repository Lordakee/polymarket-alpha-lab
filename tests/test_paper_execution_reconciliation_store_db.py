from __future__ import annotations

import importlib
import sys
import types
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeReconciliationReport:
    generated_at: datetime
    config_version: str
    reconciliation_status: str
    total_positions: int


@dataclass(frozen=True)
class FakeReconciliationDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    reconciliation_status: str
    total_positions: int
    filled_pending_count: int
    settled_win_count: int
    settled_loss_count: int
    expired_count: int
    cancelled_count: int
    total_fill_notional: Decimal
    total_cost_basis: Decimal
    total_outcome_value: Decimal | None
    total_pnl: Decimal | None
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    position_rows_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...] = (), rowcount: int = 1) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...] = (), rowcount: int = 1) -> None:
        self.cursor_instance = FakeCursor(rows, rowcount)
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


def d(value: str) -> Decimal:
    return Decimal(value)


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_execution_reconciliation_db_row",
    )

    def to_db_row(report: FakeReconciliationReport) -> FakeReconciliationDbRow:
        return FakeReconciliationDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            reconciliation_status=report.reconciliation_status,
            total_positions=report.total_positions,
            filled_pending_count=1,
            settled_win_count=0,
            settled_loss_count=1,
            expired_count=0,
            cancelled_count=0,
            total_fill_notional=d("15.000000"),
            total_cost_basis=d("17.000000"),
            total_outcome_value=d("0.000000"),
            total_pnl=d("-2.000000"),
            realized_pnl=d("-2.000000"),
            unrealized_pnl=d("0.000000"),
            position_rows_json=[{"condition_id": "condition-alpha"}],
            reason_codes_json=["paper_execution_reconciliation_has_pending"],
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "reconciliation_status": report.reconciliation_status,
                "total_positions": report.total_positions,
            },
        )

    def from_db_row(row: FakeReconciliationDbRow) -> FakeReconciliationReport:
        return FakeReconciliationReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            reconciliation_status=row.reconciliation_status,
            total_positions=row.total_positions,
        )

    companion.PaperExecutionReconciliationDbRow = FakeReconciliationDbRow
    companion.paper_execution_reconciliation_report_to_db_row = to_db_row
    companion.paper_execution_reconciliation_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_execution_reconciliation_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_execution_reconciliation_store", None)
    return importlib.import_module(
        "polymarket_alpha_lab.paper_execution_reconciliation_store",
    )


def _fake_report() -> FakeReconciliationReport:
    return FakeReconciliationReport(
        generated_at=datetime(2026, 6, 25, 10, 30, tzinfo=UTC),
        config_version="paper-execution-reconciliation-v0",
        reconciliation_status="has_pending",
        total_positions=2,
    )


def test_default_table_name(store_module: types.ModuleType) -> None:
    assert (
        store_module.DEFAULT_PAPER_EXECUTION_RECONCILIATION_REPORTS_TABLE
        == "paper_execution_reconciliation_reports"
    )


def test_insert_result_validates_row_and_inserted_flag(
    store_module: types.ModuleType,
) -> None:
    row = store_module.paper_execution_reconciliation_report_to_db_row(_fake_report())

    result = store_module.PaperExecutionReconciliationInsertResult(
        row=row,
        inserted=True,
    )

    assert result.row == row
    assert result.inserted is True
    with pytest.raises(ValueError, match="PaperExecutionReconciliationDbRow"):
        store_module.PaperExecutionReconciliationInsertResult(
            row="not-row",
            inserted=True,
        )
    with pytest.raises(ValueError, match="inserted must be a bool"):
        store_module.PaperExecutionReconciliationInsertResult(
            row=row,
            inserted=1,
        )


def test_insert_reconciliation_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rowcount=1)
    report = _fake_report()

    inserted = store_module.insert_paper_execution_reconciliation_report(
        connection,
        report,
    )
    result = store_module.insert_paper_execution_reconciliation_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )

    assert inserted == result.row
    assert result.inserted is True
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_execution_reconciliation_reports (
            report_sha256,
            generated_at,
            config_version,
            reconciliation_status,
            total_positions,
            filled_pending_count,
            settled_win_count,
            settled_loss_count,
            expired_count,
            cancelled_count,
            total_fill_notional,
            total_cost_basis,
            total_outcome_value,
            total_pnl,
            realized_pnl,
            unrealized_pnl,
            position_rows_json,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        "paper-execution-reconciliation-v0",
        "has_pending",
        2,
        1,
        0,
        1,
        0,
        0,
        d("15.000000"),
        d("17.000000"),
        d("0.000000"),
        d("-2.000000"),
        d("-2.000000"),
        d("0.000000"),
        [{"condition_id": "condition-alpha"}],
        ["paper_execution_reconciliation_has_pending"],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": "paper-execution-reconciliation-v0",
            "reconciliation_status": "has_pending",
            "total_positions": 2,
        },
        True,
        True,
        True,
    )


def test_insert_dedup_returns_inserted_false(store_module: types.ModuleType) -> None:
    result = store_module.insert_paper_execution_reconciliation_report_with_result(
        FakeConnection(rowcount=0),
        _fake_report(),
    )

    assert result.inserted is False


def test_insert_rejects_unexpected_rowcount(store_module: types.ModuleType) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_execution_reconciliation_report_with_result(
            FakeConnection(rowcount=2),
            _fake_report(),
        )


def test_insert_rejects_unsafe_table_name_without_opening_cursor(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_execution_reconciliation_report(
            connection,
            _fake_report(),
            table_name="paper_execution_reconciliation_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_reconciliation_reports_filters_limits_and_orders_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeReconciliationDbRow(
        report_sha256="b" * 64,
        generated_at=datetime(2026, 6, 25, 11, 30, tzinfo=UTC),
        config_version="paper-execution-reconciliation-v0",
        reconciliation_status="has_pending",
        total_positions=3,
        filled_pending_count=2,
        settled_win_count=0,
        settled_loss_count=1,
        expired_count=0,
        cancelled_count=0,
        total_fill_notional=d("25.000000"),
        total_cost_basis=d("27.000000"),
        total_outcome_value=d("0.000000"),
        total_pnl=d("-2.000000"),
        realized_pnl=d("-2.000000"),
        unrealized_pnl=d("0.000000"),
        position_rows_json=[{"condition_id": "condition-alpha"}],
        reason_codes_json=["paper_execution_reconciliation_has_pending"],
        payload_json={
            "generated_at": "2026-06-25T11:30:00+00:00",
            "config_version": "paper-execution-reconciliation-v0",
            "reconciliation_status": "has_pending",
            "total_positions": 3,
        },
    )
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_execution_reconciliation_reports(
        connection,
        config_version="paper-execution-reconciliation-v0",
        reconciliation_status="has_pending",
        limit=25,
        table_name="paper_execution_reconciliation_archive",
    )

    assert reports == (
        FakeReconciliationReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            reconciliation_status=row.reconciliation_status,
            total_positions=3,
        ),
    )
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            reconciliation_status,
            total_positions,
            filled_pending_count,
            settled_win_count,
            settled_loss_count,
            expired_count,
            cancelled_count,
            total_fill_notional,
            total_cost_basis,
            total_outcome_value,
            total_pnl,
            realized_pnl,
            unrealized_pnl,
            position_rows_json,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM paper_execution_reconciliation_archive
        WHERE config_version = %s AND reconciliation_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-execution-reconciliation-v0", "has_pending", 25)


def test_load_reconciliation_reports_accepts_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 25, 12, 30, tzinfo=UTC)
    positional_row = (
        "c" * 64,
        generated_at,
        "paper-execution-reconciliation-v0",
        "reconciled",
        1,
        0,
        1,
        0,
        0,
        0,
        d("10.000000"),
        d("8.000000"),
        d("12.000000"),
        d("4.000000"),
        d("4.000000"),
        d("0.000000"),
        [{"condition_id": "condition-alpha"}],
        ["paper_execution_reconciliation_has_settled"],
        {
            "generated_at": "2026-06-25T12:30:00+00:00",
            "config_version": "paper-execution-reconciliation-v0",
            "reconciliation_status": "reconciled",
            "total_positions": 1,
        },
        True,
        True,
        True,
    )
    dict_row = {
        "report_sha256": "d" * 64,
        "generated_at": generated_at,
        "config_version": "paper-execution-reconciliation-v0",
        "reconciliation_status": "has_pending",
        "total_positions": 2,
        "filled_pending_count": 2,
        "settled_win_count": 0,
        "settled_loss_count": 0,
        "expired_count": 0,
        "cancelled_count": 0,
        "total_fill_notional": d("20.000000"),
        "total_cost_basis": d("20.000000"),
        "total_outcome_value": None,
        "total_pnl": None,
        "realized_pnl": d("0.000000"),
        "unrealized_pnl": d("0.000000"),
        "position_rows_json": [{"condition_id": "condition-beta"}],
        "reason_codes_json": ["paper_execution_reconciliation_has_pending"],
        "payload_json": {
            "generated_at": "2026-06-25T12:30:00+00:00",
            "config_version": "paper-execution-reconciliation-v0",
            "reconciliation_status": "has_pending",
            "total_positions": 2,
        },
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    Record = namedtuple(
        "Record",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "reconciliation_status",
            "total_positions",
            "filled_pending_count",
            "settled_win_count",
            "settled_loss_count",
            "expired_count",
            "cancelled_count",
            "total_fill_notional",
            "total_cost_basis",
            "total_outcome_value",
            "total_pnl",
            "realized_pnl",
            "unrealized_pnl",
            "position_rows_json",
            "reason_codes_json",
            "payload_json",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    namedtuple_row = Record(*positional_row)
    connection = FakeConnection(rows=(positional_row, dict_row, namedtuple_row))

    reports = store_module.load_paper_execution_reconciliation_reports(connection)

    assert reports == (
        FakeReconciliationReport(
            generated_at=generated_at,
            config_version="paper-execution-reconciliation-v0",
            reconciliation_status="reconciled",
            total_positions=1,
        ),
        FakeReconciliationReport(
            generated_at=generated_at,
            config_version="paper-execution-reconciliation-v0",
            reconciliation_status="has_pending",
            total_positions=2,
        ),
        FakeReconciliationReport(
            generated_at=generated_at,
            config_version="paper-execution-reconciliation-v0",
            reconciliation_status="reconciled",
            total_positions=1,
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_execution_reconciliation_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"reconciliation_status": ""}, "reconciliation_status"),
        ({"reconciliation_status": "has_pending "}, "reconciliation_status"),
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_without_opening_cursor(
    store_module: types.ModuleType,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store_module.load_paper_execution_reconciliation_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_store_module_has_no_forbidden_surfaces(store_module: types.ModuleType) -> None:
    source = Path(
        "src/polymarket_alpha_lab/paper_execution_reconciliation_store.py",
    ).read_text(encoding="utf-8")

    for banned in (
        "psycopg",
        "supabase",
        "os.environ",
        "requests",
        "httpx",
        "urllib",
        "subprocess",
        "socket",
        "asyncio",
        "private_key",
        "wallet",
        "account",
        "submit_order",
        "cancel_order",
        "replace_order",
        "approve",
        "open(",
        "print(",
    ):
        assert banned not in source.lower()
