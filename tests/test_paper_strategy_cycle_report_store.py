from __future__ import annotations

import importlib
import sys
import types
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeStrategyCycleReport:
    generated_at: datetime
    config_version: str
    scan_market_count: int
    blocked_counts_json: list[object]


@dataclass(frozen=True)
class FakeStrategyCycleReportDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    scan_market_count: int
    considered_count: int
    snapshot_ready_count: int
    cost_aware_report_count: int
    blocked_counts_json: list[object]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True


class FakeCursor:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))

    def fetchall(self) -> tuple[Any, ...]:
        return self.rows

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    def __init__(self, rows: tuple[Any, ...] = ()) -> None:
        self.cursor_instance = FakeCursor(rows)
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
def store_module(monkeypatch: pytest.MonkeyPatch) -> Any:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_strategy_cycle_report_db_row",
    )

    def to_db_row(report: FakeStrategyCycleReport) -> FakeStrategyCycleReportDbRow:
        return FakeStrategyCycleReportDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            scan_market_count=report.scan_market_count,
            considered_count=2,
            snapshot_ready_count=1,
            cost_aware_report_count=1,
            blocked_counts_json=[["blocked_fetch_error", 1]],
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "scan_market_count": report.scan_market_count,
                "paper_only": True,
                "report_only": True,
            },
        )

    def from_db_row(row: FakeStrategyCycleReportDbRow) -> FakeStrategyCycleReport:
        return FakeStrategyCycleReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            scan_market_count=row.scan_market_count,
            blocked_counts_json=row.blocked_counts_json,
        )

    companion.PaperStrategyCycleReportDbRow = FakeStrategyCycleReportDbRow
    companion.paper_strategy_cycle_report_to_db_row = to_db_row
    companion.paper_strategy_cycle_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_strategy_cycle_report_db_row",
        companion,
    )
    module_name = "polymarket_alpha_lab.paper_strategy_cycle_report_store"
    sys.modules.pop(module_name, None)
    module = importlib.import_module(
        "polymarket_alpha_lab.paper_strategy_cycle_report_store",
    )
    yield module
    sys.modules.pop(module_name, None)


def test_insert_paper_strategy_cycle_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeStrategyCycleReport(
        generated_at=datetime(2026, 6, 29, 12, 30, tzinfo=UTC),
        config_version="strategy-cycle-v1",
        scan_market_count=4,
        blocked_counts_json=[],
    )

    inserted = store_module.insert_paper_strategy_cycle_report(connection, report)

    assert inserted == FakeStrategyCycleReportDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version="strategy-cycle-v1",
        scan_market_count=4,
        considered_count=2,
        snapshot_ready_count=1,
        cost_aware_report_count=1,
        blocked_counts_json=[["blocked_fetch_error", 1]],
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": "strategy-cycle-v1",
            "scan_market_count": 4,
            "paper_only": True,
            "report_only": True,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_strategy_cycle_reports (
            report_sha256,
            generated_at,
            config_version,
            scan_market_count,
            considered_count,
            snapshot_ready_count,
            cost_aware_report_count,
            blocked_counts_json,
            payload_json,
            paper_only,
            report_only
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        "strategy-cycle-v1",
        4,
        2,
        1,
        1,
        [["blocked_fetch_error", 1]],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": "strategy-cycle-v1",
            "scan_market_count": 4,
            "paper_only": True,
            "report_only": True,
        },
        True,
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_strategy_cycle_report(
            connection,
            FakeStrategyCycleReport(
                generated_at=datetime(2026, 6, 29, 12, 30, tzinfo=UTC),
                config_version="strategy-cycle-v1",
                scan_market_count=4,
                blocked_counts_json=[],
            ),
            table_name="paper_strategy_cycle_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_paper_strategy_cycle_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeStrategyCycleReportDbRow(
        report_sha256="b" * 64,
        generated_at=datetime(2026, 6, 29, 14, 0, tzinfo=UTC),
        config_version="strategy-cycle-v1",
        scan_market_count=8,
        considered_count=5,
        snapshot_ready_count=3,
        cost_aware_report_count=2,
        blocked_counts_json=[["blocked_missing_book", 1]],
        payload_json={
            "generated_at": "2026-06-29T14:00:00+00:00",
            "config_version": "strategy-cycle-v1",
            "scan_market_count": 8,
            "paper_only": True,
            "report_only": True,
        },
    )
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_strategy_cycle_reports(
        connection,
        config_version="strategy-cycle-v1",
        limit=25,
        table_name="strategy_cycle_report_archive",
    )

    assert reports == (
        FakeStrategyCycleReport(
            generated_at=row.generated_at,
            config_version="strategy-cycle-v1",
            scan_market_count=8,
            blocked_counts_json=[["blocked_missing_book", 1]],
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            scan_market_count,
            considered_count,
            snapshot_ready_count,
            cost_aware_report_count,
            blocked_counts_json,
            payload_json,
            paper_only,
            report_only
        FROM strategy_cycle_report_archive
        WHERE config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("strategy-cycle-v1", 25)


def test_load_paper_strategy_cycle_reports_maps_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 29, 14, 0, tzinfo=UTC)
    row_values = (
        "c" * 64,
        generated_at,
        "strategy-cycle-v1",
        9,
        6,
        4,
        3,
        (("blocked_fetch_error", 2),),
        {
            "generated_at": "2026-06-29T14:00:00+00:00",
            "config_version": "strategy-cycle-v1",
            "scan_market_count": 9,
            "paper_only": True,
            "report_only": True,
        },
        True,
        True,
    )
    RowTuple = namedtuple(
        "RowTuple",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "scan_market_count",
            "considered_count",
            "snapshot_ready_count",
            "cost_aware_report_count",
            "blocked_counts_json",
            "payload_json",
            "paper_only",
            "report_only",
        ),
    )
    row_dict = dict(zip(RowTuple._fields, row_values, strict=True))
    connection = FakeConnection(
        rows=(
            row_values,
            row_dict,
            RowTuple(*row_values),
        ),
    )

    reports = store_module.load_paper_strategy_cycle_reports(connection)

    assert reports == (
        FakeStrategyCycleReport(
            generated_at=generated_at,
            config_version="strategy-cycle-v1",
            scan_market_count=9,
            blocked_counts_json=[["blocked_fetch_error", 2]],
        ),
        FakeStrategyCycleReport(
            generated_at=generated_at,
            config_version="strategy-cycle-v1",
            scan_market_count=9,
            blocked_counts_json=[["blocked_fetch_error", 2]],
        ),
        FakeStrategyCycleReport(
            generated_at=generated_at,
            config_version="strategy-cycle-v1",
            scan_market_count=9,
            blocked_counts_json=[["blocked_fetch_error", 2]],
        ),
    )


@pytest.mark.parametrize(
    ("row_values", "message"),
    (
        (
            (
                "c" * 64,
                datetime(2026, 6, 29, 14, 0, tzinfo=UTC),
                "strategy-cycle-v1",
                9,
                6,
                4,
                3,
                {"blocked_fetch_error": 2},
                {"paper_only": True, "report_only": True},
                True,
                True,
            ),
            "blocked_counts_json",
        ),
        (
            (
                "c" * 64,
                datetime(2026, 6, 29, 14, 0, tzinfo=UTC),
                "strategy-cycle-v1",
                9,
                6,
                4,
                3,
                [],
                [],
                True,
                True,
            ),
            "payload_json",
        ),
    ),
)
def test_load_rejects_invalid_json_column_shapes(
    store_module: types.ModuleType,
    row_values: tuple[Any, ...],
    message: str,
) -> None:
    connection = FakeConnection(rows=(row_values,))

    with pytest.raises(ValueError, match=message):
        store_module.load_paper_strategy_cycle_reports(connection)

    assert connection.cursor_count == 1
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_strategy_cycle_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "paper_strategy_cycle_reports_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " strategy-cycle-v1"}, "config_version"),
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
        store_module.load_paper_strategy_cycle_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
