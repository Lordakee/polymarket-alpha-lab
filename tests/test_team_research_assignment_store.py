from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import importlib
import sys
import types
from typing import Any

import pytest


STORE_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment_store"
DB_ROW_MODULE_NAME = "polymarket_alpha_lab.team_research_assignment_db_row"
DEFAULT_TABLE = "team_research_assignment_reports"
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "source_queue_config_version",
    "source_route_config_version",
    "source_memory_config_version",
    "assignment_status",
    "assignment_count",
    "assigned_count",
    "watch_count",
    "blocked_count",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


@dataclass(frozen=True)
class FakeReport:
    assignment_status: str
    config_version: str


@dataclass(frozen=True)
class FakeDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    source_route_config_version: str
    source_memory_config_version: str
    assignment_status: str
    assignment_count: int
    assigned_count: int
    watch_count: int
    blocked_count: int
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        *,
        execute_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.execute_error = execute_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

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
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        *,
        cursor: FakeCursor | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(rows, rowcount) if cursor is None else cursor
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


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _row(**overrides: Any) -> FakeDbRow:
    generated_at = datetime(2026, 7, 1, 16, 30, tzinfo=UTC)
    values: dict[str, Any] = {
        "report_sha256": "b" * 64,
        "generated_at": generated_at,
        "config_version": "team-research-assignment-test-v0",
        "source_queue_config_version": "paper-strategy-candidate-research-queue-v0",
        "source_route_config_version": "team-market-route-v0",
        "source_memory_config_version": "team-memory-readiness-digest-v0",
        "assignment_status": "watch",
        "assignment_count": 4,
        "assigned_count": 2,
        "watch_count": 1,
        "blocked_count": 1,
        "reason_codes_json": ["team_assignment_watch"],
        "payload_json": {
            "generated_at": generated_at.isoformat(),
            "config_version": "team-research-assignment-test-v0",
            "source_queue_config_version": "paper-strategy-candidate-research-queue-v0",
            "source_route_config_version": "team-market-route-v0",
            "source_memory_config_version": "team-memory-readiness-digest-v0",
            "assignment_status": "watch",
            "assignment_count": 4,
            "assigned_count": 2,
            "watch_count": 1,
            "blocked_count": 1,
            "team_summaries": [],
            "rows": [],
            "reason_codes": ["team_assignment_watch"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return FakeDbRow(**values)


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
    expected_report = (
        FakeReport(
            assignment_status=expected_row.assignment_status,
            config_version=expected_row.config_version,
        )
        if report is None
        else report
    )
    module.TeamResearchAssignmentDbRow = FakeDbRow
    module.team_research_assignment_report_to_db_row = lambda report_arg: expected_row
    module.team_research_assignment_report_from_db_row = lambda row_arg: expected_report
    monkeypatch.setitem(sys.modules, DB_ROW_MODULE_NAME, module)


def _import_store(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    _install_fake_db_row(monkeypatch)
    sys.modules.pop(STORE_MODULE_NAME, None)
    return importlib.import_module(STORE_MODULE_NAME)


def test_insert_assignment_report_uses_parameterized_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()
    report = FakeReport(
        assignment_status="watch",
        config_version="team-research-assignment-test-v0",
    )
    expected_row = _row()

    inserted = store.insert_team_research_assignment_report(
        connection,
        report,
        table_name="research.team_research_assignment_reports",
    )

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO research.team_research_assignment_reports (
            report_sha256,
            generated_at,
            config_version,
            source_queue_config_version,
            source_route_config_version,
            source_memory_config_version,
            assignment_status,
            assignment_count,
            assigned_count,
            watch_count,
            blocked_count,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "team-research-assignment-test-v0" not in sql
    assert "team_assignment_watch" not in sql


def test_insert_assignment_report_with_result_observes_conflict_noop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)
    report = FakeReport(
        assignment_status="watch",
        config_version="team-research-assignment-test-v0",
    )
    expected_row = _row()

    inserted = store.insert_team_research_assignment_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store.insert_team_research_assignment_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_load_assignment_reports_filters_limits_orders_and_maps_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _row()
    report = FakeReport(
        assignment_status="watch",
        config_version="team-research-assignment-test-v0",
    )
    _install_fake_db_row(monkeypatch, row=row, report=report)
    sys.modules.pop(STORE_MODULE_NAME, None)
    store = importlib.import_module(STORE_MODULE_NAME)
    connection = FakeConnection(
        rows=(dict(zip(SELECT_COLUMNS, _row_values(row), strict=True)),),
    )

    reports = store.load_team_research_assignment_reports(
        connection,
        assignment_status="watch",
        config_version="team-research-assignment-test-v0",
        limit=25,
        table_name="research.team_research_assignment_reports",
    )

    assert reports == (report,)
    assert connection.cursor_count == 1
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
            source_queue_config_version,
            source_route_config_version,
            source_memory_config_version,
            assignment_status,
            assignment_count,
            assigned_count,
            watch_count,
            blocked_count,
            reason_codes_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM research.team_research_assignment_reports
        WHERE assignment_status = %s AND config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "watch",
        "team-research-assignment-test-v0",
        25,
    )


def test_load_assignment_reports_uses_default_table(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    store.load_team_research_assignment_reports(connection)

    sql, params = connection.cursor_instance.calls[0]
    assert f"FROM {DEFAULT_TABLE}" in normalize_sql(sql)
    assert params == ()


@pytest.mark.parametrize(
    "store_call",
    (
        "insert_team_research_assignment_report_with_result",
        "load_team_research_assignment_reports",
    ),
)
def test_store_operation_errors_redact_table_payload_market_hash_and_order_fields(
    monkeypatch: pytest.MonkeyPatch,
    store_call: str,
) -> None:
    store = _import_store(monkeypatch)
    table_name = "team_research_assignment_report_archive"
    market_slug = "btc-up-or-down-july-2"
    market_question = "Will BTC close above 100000 on July 2?"
    report_hash = "a" * 64
    connection = FakeConnection(
        cursor=FakeCursor(
            execute_error=RuntimeError(
                "operation failed on table "
                f"{table_name} payload_json market_slug {market_slug} "
                f"question {market_question} report_sha256 {report_hash} "
                "wallet_address 0x123 order_id ord_123",
            ),
        ),
    )

    with pytest.raises(RuntimeError) as exc_info:
        if store_call == "insert_team_research_assignment_report_with_result":
            store.insert_team_research_assignment_report_with_result(
                connection,
                FakeReport(
                    assignment_status="watch",
                    config_version="team-research-assignment-test-v0",
                ),
                table_name=table_name,
            )
        else:
            store.load_team_research_assignment_reports(
                connection,
                table_name=table_name,
            )

    message = str(exc_info.value)
    assert message == "team research assignment database operation failed for <redacted>"
    assert table_name not in message
    assert "payload_json" not in message
    assert market_slug not in message
    assert market_question not in message
    assert report_hash not in message
    assert "wallet_address" not in message
    assert "order_id" not in message
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": "25"}, "limit"),
    ),
)
def test_load_rejects_invalid_limit_before_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store.load_team_research_assignment_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"assignment_status": ""}, "assignment_status"),
        ({"assignment_status": " watch"}, "assignment_status"),
        ({"assignment_status": 1}, "assignment_status"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " team-research-assignment-test-v0"}, "config_version"),
        ({"config_version": 1}, "config_version"),
    ),
)
def test_load_rejects_invalid_filters_before_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    kwargs: dict[str, Any],
    message: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        store.load_team_research_assignment_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize("assignment_status", ("assigned", "done", "READY"))
def test_load_rejects_unknown_assignment_status_before_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    assignment_status: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match="assignment_status"):
        store.load_team_research_assignment_reports(
            connection,
            assignment_status=assignment_status,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    "table_name",
    (
        "schema.too.many.parts",
        "TeamResearchAssignmentReports",
        "_team_research_assignment_reports",
        "team_research_assignment_reports_",
        "public." + ("a" * 64),
        "team_research_assignment_reports; drop table users",
    ),
)
def test_table_name_validation_rejects_unsafe_names_without_cursor_creation(
    monkeypatch: pytest.MonkeyPatch,
    table_name: str,
) -> None:
    store = _import_store(monkeypatch)
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store.load_team_research_assignment_reports(
            connection,
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
