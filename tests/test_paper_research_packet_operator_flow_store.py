from __future__ import annotations

import importlib
import sys
import types
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest


class CursorCloseFailure(BaseException):
    pass


@dataclass(frozen=True)
class FakeResearchPacketOperatorFlowReport:
    generated_at: datetime
    config_version: str
    flow_status: str


@dataclass(frozen=True)
class FakeResearchPacketOperatorFlowDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    flow_status: str
    packet_generated_at: datetime
    packet_config_version: str
    packet_persisted: bool
    packet_row_count: int
    included_count: int
    skipped_count: int
    quality_generated_at: datetime
    quality_config_version: str
    quality_status: str
    quality_persisted: bool
    quality_check_count: int
    quality_pass_count: int
    quality_watch_count: int
    quality_blocked_count: int
    history_generated_at: datetime
    history_config_version: str
    history_status: str
    history_source_report_count: int
    history_latest_quality_status: str
    reason_codes_json: list[str]
    reason_code_count: int
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
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
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
        if cursor is None:
            cursor = FakeCursor(rows, rowcount)
        self.cursor_instance = cursor
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


def fake_db_row(
    *,
    report_sha256: str = "b" * 64,
    generated_at: datetime = datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
    config_version: str = "paper-research-packet-operator-flow-v0",
    flow_status: str = "pass",
) -> FakeResearchPacketOperatorFlowDbRow:
    packet_generated_at = datetime(2026, 6, 23, 11, 40, tzinfo=UTC)
    quality_generated_at = datetime(2026, 6, 23, 11, 50, tzinfo=UTC)
    history_generated_at = datetime(2026, 6, 23, 11, 55, tzinfo=UTC)
    return FakeResearchPacketOperatorFlowDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        flow_status=flow_status,
        packet_generated_at=packet_generated_at,
        packet_config_version="paper-research-packet-v0",
        packet_persisted=True,
        packet_row_count=4,
        included_count=3,
        skipped_count=1,
        quality_generated_at=quality_generated_at,
        quality_config_version="paper-research-packet-quality-v0",
        quality_status="watch",
        quality_persisted=True,
        quality_check_count=5,
        quality_pass_count=3,
        quality_watch_count=2,
        quality_blocked_count=0,
        history_generated_at=history_generated_at,
        history_config_version="paper-research-packet-quality-history-v0",
        history_status="watch",
        history_source_report_count=2,
        history_latest_quality_status="watch",
        reason_codes_json=["operator_flow_watch"],
        reason_code_count=1,
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "flow_status": flow_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_research_packet_operator_flow_db_row",
    )

    def to_db_row(
        report: FakeResearchPacketOperatorFlowReport,
    ) -> FakeResearchPacketOperatorFlowDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            flow_status=report.flow_status,
        )

    def from_db_row(
        row: FakeResearchPacketOperatorFlowDbRow,
    ) -> FakeResearchPacketOperatorFlowReport:
        return FakeResearchPacketOperatorFlowReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            flow_status=row.flow_status,
        )

    companion.PaperResearchPacketOperatorFlowDbRow = FakeResearchPacketOperatorFlowDbRow
    companion.paper_research_packet_operator_flow_report_to_db_row = to_db_row
    companion.paper_research_packet_operator_flow_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_research_packet_operator_flow_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_research_packet_operator_flow_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_research_packet_operator_flow_store",
    )


def test_insert_operator_flow_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeResearchPacketOperatorFlowReport(
        generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
        config_version="paper-research-packet-operator-flow-v0",
        flow_status="pass",
    )

    inserted = store_module.insert_paper_research_packet_operator_flow_report(
        connection,
        report,
    )

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        flow_status=report.flow_status,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_research_packet_operator_flow_reports (
            report_sha256,
            generated_at,
            config_version,
            flow_status,
            packet_generated_at,
            packet_config_version,
            packet_persisted,
            packet_row_count,
            included_count,
            skipped_count,
            quality_generated_at,
            quality_config_version,
            quality_status,
            quality_persisted,
            quality_check_count,
            quality_pass_count,
            quality_watch_count,
            quality_blocked_count,
            history_generated_at,
            history_config_version,
            history_status,
            history_source_report_count,
            history_latest_quality_status,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        report.flow_status,
        datetime(2026, 6, 23, 11, 40, tzinfo=UTC),
        "paper-research-packet-v0",
        True,
        4,
        3,
        1,
        datetime(2026, 6, 23, 11, 50, tzinfo=UTC),
        "paper-research-packet-quality-v0",
        "watch",
        True,
        5,
        3,
        2,
        0,
        datetime(2026, 6, 23, 11, 55, tzinfo=UTC),
        "paper-research-packet-quality-history-v0",
        "watch",
        2,
        "watch",
        ["operator_flow_watch"],
        1,
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "flow_status": report.flow_status,
        },
        True,
        True,
        True,
    )


def test_insert_operator_flow_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    report = FakeResearchPacketOperatorFlowReport(
        generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
        config_version="paper-research-packet-operator-flow-v0",
        flow_status="watch",
    )
    expected_row = fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        flow_status=report.flow_status,
    )

    inserted = store_module.insert_paper_research_packet_operator_flow_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store_module.insert_paper_research_packet_operator_flow_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_operator_flow_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="insert rowcount must be 0 or 1"):
        store_module.insert_paper_research_packet_operator_flow_report_with_result(
            FakeConnection(rowcount=2),
            FakeResearchPacketOperatorFlowReport(
                generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
                config_version="paper-research-packet-operator-flow-v0",
                flow_status="pass",
            ),
        )


def test_insert_operator_flow_report_preserves_operation_exception_when_cursor_close_fails(
    store_module: types.ModuleType,
) -> None:
    operation_error = RuntimeError("execute failed")
    close_error = CursorCloseFailure("close failed")
    cursor = FakeCursor(
        execute_error=operation_error,
        close_error=close_error,
    )
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.insert_paper_research_packet_operator_flow_report(
            connection,
            FakeResearchPacketOperatorFlowReport(
                generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
                config_version="paper-research-packet-operator-flow-v0",
                flow_status="pass",
            ),
        )

    assert exc_info.value is operation_error
    assert cursor.closed is True


def test_insert_operator_flow_report_propagates_cursor_close_error_after_success(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.insert_paper_research_packet_operator_flow_report(
            connection,
            FakeResearchPacketOperatorFlowReport(
                generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
                config_version="paper-research-packet-operator-flow-v0",
                flow_status="pass",
            ),
        )

    assert exc_info.value is close_error
    assert cursor.closed is True


def test_load_operator_flow_reports_preserves_fetchall_exception_when_cursor_close_fails(
    store_module: types.ModuleType,
) -> None:
    operation_error = RuntimeError("fetchall failed")
    close_error = CursorCloseFailure("close failed")
    cursor = FakeCursor(
        fetchall_error=operation_error,
        close_error=close_error,
    )
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="fetchall failed") as exc_info:
        store_module.load_paper_research_packet_operator_flow_reports(connection)

    assert exc_info.value is operation_error
    assert cursor.closed is True


def test_load_operator_flow_reports_propagates_cursor_close_error_after_success(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    cursor = FakeCursor(rows=(), close_error=close_error)
    connection = FakeConnection(cursor=cursor)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_research_packet_operator_flow_reports(connection)

    assert exc_info.value is close_error
    assert cursor.closed is True


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_research_packet_operator_flow_report(
            connection,
            FakeResearchPacketOperatorFlowReport(
                generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
                config_version="paper-research-packet-operator-flow-v0",
                flow_status="pass",
            ),
            table_name="paper_research_packet_operator_flow_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_operator_flow_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(flow_status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_research_packet_operator_flow_reports(
        connection,
        config_version="paper-research-packet-operator-flow-v0",
        flow_status="blocked",
        limit=25,
        table_name="audit.paper_research_packet_operator_flow_reports",
    )

    assert reports == (
        FakeResearchPacketOperatorFlowReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            flow_status=row.flow_status,
        ),
    )
    assert connection.cursor_instance.closed is True
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            flow_status,
            packet_generated_at,
            packet_config_version,
            packet_persisted,
            packet_row_count,
            included_count,
            skipped_count,
            quality_generated_at,
            quality_config_version,
            quality_status,
            quality_persisted,
            quality_check_count,
            quality_pass_count,
            quality_watch_count,
            quality_blocked_count,
            history_generated_at,
            history_config_version,
            history_status,
            history_source_report_count,
            history_latest_quality_status,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM audit.paper_research_packet_operator_flow_reports
        WHERE config_version = %s AND flow_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-research-packet-operator-flow-v0", "blocked", 25)


def test_load_operator_flow_reports_accepts_supported_row_records(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(flow_status="pass")
    positional_connection = FakeConnection(rows=(tuple(row.__dict__.values()),))
    typed_connection = FakeConnection(rows=(row,))
    dict_row = row.__dict__.copy()
    dict_row["flow_status"] = "watch"
    dict_connection = FakeConnection(rows=(dict_row,))
    record_type = namedtuple(
        "ResearchPacketOperatorFlowRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "flow_status",
            "packet_generated_at",
            "packet_config_version",
            "packet_persisted",
            "packet_row_count",
            "included_count",
            "skipped_count",
            "quality_generated_at",
            "quality_config_version",
            "quality_status",
            "quality_persisted",
            "quality_check_count",
            "quality_pass_count",
            "quality_watch_count",
            "quality_blocked_count",
            "history_generated_at",
            "history_config_version",
            "history_status",
            "history_source_report_count",
            "history_latest_quality_status",
            "reason_codes_json",
            "reason_code_count",
            "payload_json",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    namedtuple_connection = FakeConnection(
        rows=(
            record_type(
                row.report_sha256,
                row.generated_at,
                row.config_version,
                "blocked",
                row.packet_generated_at,
                row.packet_config_version,
                row.packet_persisted,
                row.packet_row_count,
                row.included_count,
                row.skipped_count,
                row.quality_generated_at,
                row.quality_config_version,
                row.quality_status,
                row.quality_persisted,
                row.quality_check_count,
                row.quality_pass_count,
                row.quality_watch_count,
                row.quality_blocked_count,
                row.history_generated_at,
                row.history_config_version,
                row.history_status,
                row.history_source_report_count,
                row.history_latest_quality_status,
                row.reason_codes_json,
                row.reason_code_count,
                row.payload_json,
                True,
                True,
                True,
            ),
        ),
    )

    assert store_module.load_paper_research_packet_operator_flow_reports(
        positional_connection,
    ) == (
        FakeResearchPacketOperatorFlowReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            flow_status="pass",
        ),
    )
    assert store_module.load_paper_research_packet_operator_flow_reports(
        typed_connection,
    ) == (
        FakeResearchPacketOperatorFlowReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            flow_status="pass",
        ),
    )
    assert store_module.load_paper_research_packet_operator_flow_reports(
        dict_connection,
    ) == (
        FakeResearchPacketOperatorFlowReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            flow_status="watch",
        ),
    )
    assert store_module.load_paper_research_packet_operator_flow_reports(
        namedtuple_connection,
    ) == (
        FakeResearchPacketOperatorFlowReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            flow_status="blocked",
        ),
    )


def test_load_operator_flow_reports_accepts_empty_reads(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=())

    assert store_module.load_paper_research_packet_operator_flow_reports(connection) == ()
    assert connection.cursor_count == 1
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit..paper_research_packet_operator_flow_reports"}, "table_name"),
        (
            {"table_name": "audit.paper.research_packet_operator_flow_reports"},
            "table_name",
        ),
        ({"table_name": "PaperResearchPacketOperatorFlowReports"}, "table_name"),
        ({"table_name": "paper-research-packet-operator-flow-reports"}, "table_name"),
        ({"table_name": "paper_research_packet_operator_flow_reports_"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"flow_status": "stable"}, "flow_status"),
        ({"flow_status": True}, "flow_status"),
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
        store_module.load_paper_research_packet_operator_flow_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_insert_result_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE == (
        "paper_research_packet_operator_flow_reports"
    )
    assert (
        "DEFAULT_PAPER_RESEARCH_PACKET_OPERATOR_FLOW_REPORTS_TABLE"
        in store_module.__all__
    )
    assert "PaperResearchPacketOperatorFlowInsertResult" in store_module.__all__
    assert "insert_paper_research_packet_operator_flow_report" in store_module.__all__
    assert (
        "insert_paper_research_packet_operator_flow_report_with_result"
        in store_module.__all__
    )
    assert "load_paper_research_packet_operator_flow_reports" in store_module.__all__
