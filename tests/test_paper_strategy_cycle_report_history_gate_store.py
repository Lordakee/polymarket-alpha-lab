from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import sys
import types
from typing import Any

import pytest


STORE_MODULE_NAME = (
    "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate_store"
)
DB_ROW_MODULE_NAME = (
    "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate_db_row"
)
DEFAULT_TABLE = "paper_strategy_cycle_report_history_gate_reports"
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_config_version",
    "source_generated_at",
    "gate_status",
    "recommended_next_step",
    "source_history_status",
    "source_report_count",
    "latest_source_generated_at",
    "latest_source_age_seconds",
    "latest_snapshot_ready_share",
    "blocked_market_share",
    "latest_snapshot_ready_count",
    "latest_considered_count",
    "total_blocked_market_count",
    "reason_code_counts_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class FakeReport:
    gate_status: str


@dataclass(frozen=True)
class FakeDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_config_version: str
    source_generated_at: datetime
    gate_status: str
    recommended_next_step: str
    source_history_status: str
    source_report_count: int
    latest_source_generated_at: datetime | None
    latest_source_age_seconds: int | None
    latest_snapshot_ready_share: Decimal
    blocked_market_share: Decimal
    latest_snapshot_ready_count: int
    latest_considered_count: int
    total_blocked_market_count: int
    reason_code_counts_json: list[dict[str, Any]]
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


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _row() -> FakeDbRow:
    generated_at = datetime(2026, 6, 29, 12, tzinfo=UTC)
    source_generated_at = datetime(2026, 6, 29, 11, 58, tzinfo=UTC)
    return FakeDbRow(
        report_sha256="a" * 64,
        generated_at=generated_at,
        config_version="paper-strategy-cycle-report-history-gate-test-v0",
        source_config_version="paper-strategy-cycle-report-history-v0",
        source_generated_at=source_generated_at,
        gate_status="watch",
        recommended_next_step="throttle_strategy_cycle_history_gate",
        source_history_status="watch",
        source_report_count=3,
        latest_source_generated_at=source_generated_at,
        latest_source_age_seconds=120,
        latest_snapshot_ready_share=Decimal("0.250000"),
        blocked_market_share=Decimal("0.600000"),
        latest_snapshot_ready_count=1,
        latest_considered_count=4,
        total_blocked_market_count=6,
        reason_code_counts_json=[
            {
                "reason_code": "source_strategy_cycle_report_history_watch",
                "report_count": 1,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ],
        reason_codes_json=["source_strategy_cycle_report_history_watch"],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": "paper-strategy-cycle-report-history-gate-test-v0",
            "source_config_version": "paper-strategy-cycle-report-history-v0",
            "source_generated_at": source_generated_at.isoformat(),
            "gate_status": "watch",
            "recommended_next_step": "throttle_strategy_cycle_history_gate",
            "source_history_status": "watch",
            "source_report_count": 3,
            "latest_source_generated_at": source_generated_at.isoformat(),
            "latest_source_age_seconds": 120,
            "latest_snapshot_ready_share": "0.250000",
            "blocked_market_share": "0.600000",
            "latest_snapshot_ready_count": 1,
            "latest_considered_count": 4,
            "total_blocked_market_count": 6,
            "reason_code_counts": [
                {
                    "reason_code": "source_strategy_cycle_report_history_watch",
                    "report_count": 1,
                    "paper_only": True,
                    "report_only": True,
                    "readonly": True,
                },
            ],
            "reason_codes": ["source_strategy_cycle_report_history_watch"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    )


def _row_values(row: FakeDbRow) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def _install_fake_db_row(
    monkeypatch: pytest.MonkeyPatch,
    *,
    row: FakeDbRow | None = None,
    report: FakeReport | None = None,
) -> None:
    module = types.ModuleType(DB_ROW_MODULE_NAME)
    expected_row = _row() if row is None else row
    expected_report = FakeReport(gate_status=expected_row.gate_status) if report is None else report
    module.PaperStrategyCycleReportHistoryGateDbRow = FakeDbRow
    module.paper_strategy_cycle_report_history_gate_report_to_db_row = (
        lambda report_arg: expected_row
    )
    module.paper_strategy_cycle_report_history_gate_report_from_db_row = (
        lambda row_arg: expected_report
    )
    monkeypatch.setitem(sys.modules, DB_ROW_MODULE_NAME, module)


def _import_store(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    _install_fake_db_row(monkeypatch)
    sys.modules.pop(STORE_MODULE_NAME, None)
    return importlib.import_module(STORE_MODULE_NAME)


def test_insert_history_gate_report_uses_parameterized_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()
    report = FakeReport(gate_status="watch")
    expected_row = _row()

    inserted = store.insert_paper_strategy_cycle_report_history_gate_report(
        connection,
        report,
    )

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_strategy_cycle_report_history_gate_reports (
            report_sha256,
            generated_at,
            config_version,
            source_config_version,
            source_generated_at,
            gate_status,
            recommended_next_step,
            source_history_status,
            source_report_count,
            latest_source_generated_at,
            latest_source_age_seconds,
            latest_snapshot_ready_share,
            blocked_market_share,
            latest_snapshot_ready_count,
            latest_considered_count,
            total_blocked_market_count,
            reason_code_counts_json,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "paper-strategy-cycle-report-history-gate-test-v0" not in sql
    assert "paper-strategy-cycle-report-history-v0" not in sql
    assert "throttle_strategy_cycle_history_gate" not in sql


def test_insert_history_gate_report_with_result_observes_duplicate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)
    report = FakeReport(gate_status="watch")
    expected_row = _row()

    inserted = store.insert_paper_strategy_cycle_report_history_gate_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store.insert_paper_strategy_cycle_report_history_gate_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_history_gate_report_rejects_unexpected_rowcount(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)

    with pytest.raises(ValueError, match="rowcount"):
        store.insert_paper_strategy_cycle_report_history_gate_report_with_result(
            FakeConnection(rowcount=2),
            FakeReport(gate_status="watch"),
        )


def test_load_history_gate_reports_filters_in_deterministic_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row()
    report = FakeReport(gate_status="watch")
    _install_fake_db_row(monkeypatch, row=row, report=report)
    sys.modules.pop(STORE_MODULE_NAME, None)
    store = importlib.import_module(STORE_MODULE_NAME)
    connection = FakeConnection(rows=(row,))

    reports = store.load_paper_strategy_cycle_report_history_gate_reports(
        connection,
        config_version="paper-strategy-cycle-report-history-gate-test-v0",
        gate_status="watch",
        source_config_version="paper-strategy-cycle-report-history-v0",
        source_history_status="watch",
        limit=25,
        table_name="history_gate_archive",
    )

    assert reports == (report,)
    assert connection.cursor_count == 1
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
            source_config_version,
            source_generated_at,
            gate_status,
            recommended_next_step,
            source_history_status,
            source_report_count,
            latest_source_generated_at,
            latest_source_age_seconds,
            latest_snapshot_ready_share,
            blocked_market_share,
            latest_snapshot_ready_count,
            latest_considered_count,
            total_blocked_market_count,
            reason_code_counts_json,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM history_gate_archive
        WHERE config_version = %s AND gate_status = %s AND source_config_version = %s
            AND source_history_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-strategy-cycle-report-history-gate-test-v0",
        "watch",
        "paper-strategy-cycle-report-history-v0",
        "watch",
        25,
    )


def test_load_history_gate_reports_accepts_positional_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row()
    report = FakeReport(gate_status="watch")
    _install_fake_db_row(monkeypatch, row=row, report=report)
    sys.modules.pop(STORE_MODULE_NAME, None)
    store = importlib.import_module(STORE_MODULE_NAME)

    reports = store.load_paper_strategy_cycle_report_history_gate_reports(
        FakeConnection(rows=(_row_values(row),)),
    )

    assert reports == (report,)


def test_load_history_gate_reports_accepts_dict_rows_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row()
    report = FakeReport(gate_status="watch")
    _install_fake_db_row(monkeypatch, row=row, report=report)
    sys.modules.pop(STORE_MODULE_NAME, None)
    store = importlib.import_module(STORE_MODULE_NAME)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    payload_before = dict(row.payload_json)
    reason_counts_before = [dict(item) for item in row.reason_code_counts_json]

    reports = store.load_paper_strategy_cycle_report_history_gate_reports(
        FakeConnection(rows=(record,)),
    )

    assert reports == (report,)
    assert record["payload_json"] == payload_before
    assert record["reason_code_counts_json"] == reason_counts_before


def test_load_history_gate_reports_accepts_namedtuple_like_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row()
    report = FakeReport(gate_status="watch")
    _install_fake_db_row(monkeypatch, row=row, report=report)
    sys.modules.pop(STORE_MODULE_NAME, None)
    store = importlib.import_module(STORE_MODULE_NAME)
    Record = namedtuple("Record", SELECT_COLUMNS)

    reports = store.load_paper_strategy_cycle_report_history_gate_reports(
        FakeConnection(rows=(Record(*_row_values(row)),)),
    )

    assert reports == (report,)


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_strategy_cycle_report_history_gate_reports; drop table users",
        "audit.paper_strategy_cycle_report_history_gate_reports",
        "PaperStrategyCycleReportHistoryGateReports",
        "_paper_strategy_cycle_report_history_gate_reports",
        "paper_strategy_cycle_report_history_gate_reports_",
        "a",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    table_name: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store.insert_paper_strategy_cycle_report_history_gate_report(
            connection,
            FakeReport(gate_status="watch"),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize("table_name", ["a0", "history_gate_archive", "gate_1_archive_2"])
def test_load_accepts_simple_lowercase_table_names(
    monkeypatch: pytest.MonkeyPatch,
    table_name: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    store.load_paper_strategy_cycle_report_history_gate_reports(
        connection,
        table_name=table_name,
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit.history_gate_archive"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "a"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " gate-v0"}, "config_version"),
        ({"gate_status": "paused"}, "gate_status"),
        ({"gate_status": True}, "gate_status"),
        ({"source_config_version": ""}, "source_config_version"),
        ({"source_history_status": "paused"}, "source_history_status"),
        ({"source_history_status": True}, "source_history_status"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": "5"}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_before_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store.load_paper_strategy_cycle_report_history_gate_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_insert_result_and_store_functions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)

    assert (
        store.DEFAULT_PAPER_STRATEGY_CYCLE_REPORT_HISTORY_GATE_REPORTS_TABLE
        == DEFAULT_TABLE
    )
    assert "PaperStrategyCycleReportHistoryGateInsertResult" in store.__all__
    assert "insert_paper_strategy_cycle_report_history_gate_report" in store.__all__
    assert "insert_paper_strategy_cycle_report_history_gate_report_with_result" in store.__all__
    assert "load_paper_strategy_cycle_report_history_gate_reports" in store.__all__
