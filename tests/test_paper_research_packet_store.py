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
class FakeResearchPacketReport:
    generated_at: datetime
    config_version: str
    packet_row_count: int


@dataclass(frozen=True)
class FakeResearchPacketDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    input_row_count: int
    packet_row_count: int
    included_count: int
    skipped_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    packet_rows_json: list[dict[str, Any]]
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


def fake_db_row(
    *,
    report_sha256: str = "b" * 64,
    generated_at: datetime = datetime(2026, 6, 22, 21, 0, tzinfo=UTC),
    config_version: str = "paper-research-packet-v0",
    packet_row_count: int = 2,
) -> FakeResearchPacketDbRow:
    return FakeResearchPacketDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        input_row_count=3,
        packet_row_count=packet_row_count,
        included_count=1,
        skipped_count=1,
        high_priority_count=1,
        medium_priority_count=0,
        low_priority_count=0,
        packet_rows_json=[
            {
                "packet_rank": 1,
                "market_slug": "high-ready",
                "question": "Will high-ready resolve yes?",
            },
        ],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "packet_row_count": packet_row_count,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.paper_research_packet_db_row")

    def to_db_row(report: FakeResearchPacketReport) -> FakeResearchPacketDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            packet_row_count=report.packet_row_count,
        )

    def from_db_row(row: FakeResearchPacketDbRow) -> FakeResearchPacketReport:
        return FakeResearchPacketReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            packet_row_count=row.packet_row_count,
        )

    companion.PaperResearchPacketDbRow = FakeResearchPacketDbRow
    companion.paper_research_packet_report_to_db_row = to_db_row
    companion.paper_research_packet_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_research_packet_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_research_packet_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_research_packet_store")


def test_insert_research_packet_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeResearchPacketReport(
        generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
        config_version="paper-research-packet-v0",
        packet_row_count=2,
    )

    inserted = store_module.insert_paper_research_packet_report(connection, report)

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        packet_row_count=2,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_research_packet_reports (
            report_sha256,
            generated_at,
            config_version,
            input_row_count,
            packet_row_count,
            included_count,
            skipped_count,
            high_priority_count,
            medium_priority_count,
            low_priority_count,
            packet_rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        3,
        2,
        1,
        1,
        1,
        0,
        0,
        [
            {
                "packet_rank": 1,
                "market_slug": "high-ready",
                "question": "Will high-ready resolve yes?",
            },
        ],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "packet_row_count": 2,
        },
        True,
        True,
        True,
    )


def test_insert_research_packet_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    report = FakeResearchPacketReport(
        generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
        config_version="paper-research-packet-v0",
        packet_row_count=2,
    )
    expected_row = fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        packet_row_count=2,
    )

    inserted = store_module.insert_paper_research_packet_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store_module.insert_paper_research_packet_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_research_packet_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_research_packet_report_with_result(
            FakeConnection(rowcount=2),
            FakeResearchPacketReport(
                generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
                config_version="paper-research-packet-v0",
                packet_row_count=2,
            ),
        )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_research_packet_report(
            connection,
            FakeResearchPacketReport(
                generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
                config_version="paper-research-packet-v0",
                packet_row_count=2,
            ),
            table_name="paper_research_packet_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_research_packet_report_accepts_single_character_table_name(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeResearchPacketReport(
        generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
        config_version="paper-research-packet-v0",
        packet_row_count=2,
    )

    store_module.insert_paper_research_packet_report(
        connection,
        report,
        table_name="a",
    )

    sql, params = connection.cursor_instance.calls[0]
    assert "INSERT INTO a (" in normalize_sql(sql)
    assert params[0] == "a" * 64


def test_load_research_packet_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(packet_row_count=1)
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_research_packet_reports(
        connection,
        config_version="paper-research-packet-v0",
        limit=25,
        table_name="audit.paper_research_packet_reports",
    )

    assert reports == (
        FakeResearchPacketReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            packet_row_count=row.packet_row_count,
        ),
    )
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            report_sha256,
            generated_at,
            config_version,
            input_row_count,
            packet_row_count,
            included_count,
            skipped_count,
            high_priority_count,
            medium_priority_count,
            low_priority_count,
            packet_rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM audit.paper_research_packet_reports
        WHERE config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-research-packet-v0", 25)


def test_load_research_packet_reports_accepts_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 21, 0, tzinfo=UTC)
    positional_connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-research-packet-v0",
                3,
                2,
                1,
                1,
                1,
                0,
                0,
                [{"packet_rank": 1}],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-research-packet-v0",
                    "packet_row_count": 2,
                },
                True,
                True,
                True,
            ),
        ),
    )
    dict_connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "paper-research-packet-v0",
                "input_row_count": 2,
                "packet_row_count": 1,
                "included_count": 1,
                "skipped_count": 0,
                "high_priority_count": 1,
                "medium_priority_count": 0,
                "low_priority_count": 0,
                "packet_rows_json": [{"packet_rank": 1}],
                "payload_json": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-research-packet-v0",
                    "packet_row_count": 1,
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )
    record_type = namedtuple(
        "ResearchPacketRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "input_row_count",
            "packet_row_count",
            "included_count",
            "skipped_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "packet_rows_json",
            "payload_json",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    namedtuple_connection = FakeConnection(
        rows=(
            record_type(
                "e" * 64,
                generated_at,
                "paper-research-packet-v0",
                1,
                0,
                0,
                0,
                0,
                0,
                0,
                [],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-research-packet-v0",
                    "packet_row_count": 0,
                },
                True,
                True,
                True,
            ),
        ),
    )

    assert store_module.load_paper_research_packet_reports(positional_connection) == (
        FakeResearchPacketReport(
            generated_at=generated_at,
            config_version="paper-research-packet-v0",
            packet_row_count=2,
        ),
    )
    assert store_module.load_paper_research_packet_reports(dict_connection) == (
        FakeResearchPacketReport(
            generated_at=generated_at,
            config_version="paper-research-packet-v0",
            packet_row_count=1,
        ),
    )
    assert store_module.load_paper_research_packet_reports(namedtuple_connection) == (
        FakeResearchPacketReport(
            generated_at=generated_at,
            config_version="paper-research-packet-v0",
            packet_row_count=0,
        ),
    )


def test_load_research_packet_reports_accepts_empty_reads(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=())

    assert store_module.load_paper_research_packet_reports(connection) == ()
    assert connection.cursor_count == 1
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit..paper_research_packet_reports"}, "table_name"),
        ({"table_name": "audit.paper.research_packet_reports"}, "table_name"),
        ({"table_name": "PaperResearchPacketReports"}, "table_name"),
        ({"table_name": "paper-research-packet-reports"}, "table_name"),
        ({"table_name": "paper_research_packet_reports_"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
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
        store_module.load_paper_research_packet_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_insert_result_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE == (
        "paper_research_packet_reports"
    )
    assert "DEFAULT_PAPER_RESEARCH_PACKET_REPORTS_TABLE" in store_module.__all__
    assert "PaperResearchPacketInsertResult" in store_module.__all__
    assert "insert_paper_research_packet_report" in store_module.__all__
    assert "insert_paper_research_packet_report_with_result" in store_module.__all__
    assert "load_paper_research_packet_reports" in store_module.__all__
