from __future__ import annotations

import importlib
import sys
import types
from collections import namedtuple
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeResearchPacketQualityReport:
    generated_at: datetime
    config_version: str
    quality_status: str


@dataclass(frozen=True)
class FakeResearchPacketQualityDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_generated_at: datetime
    source_config_version: str
    input_row_count: int
    packet_row_count: int
    included_count: int
    skipped_count: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    source_age_seconds: int
    included_share: Decimal | None
    skipped_share: Decimal | None
    check_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    quality_status: str
    check_rows_json: list[dict[str, Any]]
    reason_code_counts_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    reason_code_count: int
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
    generated_at: datetime = datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
    config_version: str = "paper-research-packet-quality-v0",
    quality_status: str = "pass",
) -> FakeResearchPacketQualityDbRow:
    source_generated_at = datetime(2026, 6, 23, 11, 55, tzinfo=UTC)
    check_rows = [
        {
            "check_name": "source_freshness",
            "status": "pass",
            "observed_value": 300,
            "threshold": 21600,
            "reason_codes": ["source_freshness_passed"],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    reason_counts = [
        {
            "reason_code": "source_freshness_passed",
            "count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    return FakeResearchPacketQualityDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        source_generated_at=source_generated_at,
        source_config_version="paper-research-packet-v0",
        input_row_count=3,
        packet_row_count=3,
        included_count=2,
        skipped_count=1,
        high_priority_count=1,
        medium_priority_count=1,
        low_priority_count=0,
        source_age_seconds=300,
        included_share=Decimal("0.666667"),
        skipped_share=Decimal("0.333333"),
        check_count=3,
        pass_count=3,
        watch_count=0,
        blocked_count=0,
        quality_status=quality_status,
        check_rows_json=check_rows,
        reason_code_counts_json=reason_counts,
        reason_codes_json=["source_freshness_passed"],
        reason_code_count=1,
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "quality_status": quality_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_research_packet_quality_db_row",
    )

    def to_db_row(
        report: FakeResearchPacketQualityReport,
    ) -> FakeResearchPacketQualityDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            quality_status=report.quality_status,
        )

    def from_db_row(
        row: FakeResearchPacketQualityDbRow,
    ) -> FakeResearchPacketQualityReport:
        return FakeResearchPacketQualityReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            quality_status=row.quality_status,
        )

    companion.PaperResearchPacketQualityDbRow = FakeResearchPacketQualityDbRow
    companion.paper_research_packet_quality_report_to_db_row = to_db_row
    companion.paper_research_packet_quality_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_research_packet_quality_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_research_packet_quality_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_research_packet_quality_store")


def test_insert_quality_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeResearchPacketQualityReport(
        generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
        config_version="paper-research-packet-quality-v0",
        quality_status="pass",
    )

    inserted = store_module.insert_paper_research_packet_quality_report(connection, report)

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        quality_status=report.quality_status,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_research_packet_quality_reports (
            report_sha256,
            generated_at,
            config_version,
            source_generated_at,
            source_config_version,
            input_row_count,
            packet_row_count,
            included_count,
            skipped_count,
            high_priority_count,
            medium_priority_count,
            low_priority_count,
            source_age_seconds,
            included_share,
            skipped_share,
            check_count,
            pass_count,
            watch_count,
            blocked_count,
            quality_status,
            check_rows_json,
            reason_code_counts_json,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        datetime(2026, 6, 23, 11, 55, tzinfo=UTC),
        "paper-research-packet-v0",
        3,
        3,
        2,
        1,
        1,
        1,
        0,
        300,
        Decimal("0.666667"),
        Decimal("0.333333"),
        3,
        3,
        0,
        0,
        "pass",
        fake_db_row().check_rows_json,
        fake_db_row().reason_code_counts_json,
        ["source_freshness_passed"],
        1,
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "quality_status": report.quality_status,
        },
        True,
        True,
        True,
    )


def test_insert_quality_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    report = FakeResearchPacketQualityReport(
        generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
        config_version="paper-research-packet-quality-v0",
        quality_status="watch",
    )
    expected_row = fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        quality_status=report.quality_status,
    )

    inserted = store_module.insert_paper_research_packet_quality_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store_module.insert_paper_research_packet_quality_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_quality_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_research_packet_quality_report_with_result(
            FakeConnection(rowcount=2),
            FakeResearchPacketQualityReport(
                generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
                config_version="paper-research-packet-quality-v0",
                quality_status="pass",
            ),
        )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_research_packet_quality_report(
            connection,
            FakeResearchPacketQualityReport(
                generated_at=datetime(2026, 6, 23, 12, 30, tzinfo=UTC),
                config_version="paper-research-packet-quality-v0",
                quality_status="pass",
            ),
            table_name="paper_research_packet_quality_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_quality_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(quality_status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_research_packet_quality_reports(
        connection,
        config_version="paper-research-packet-quality-v0",
        quality_status="blocked",
        limit=25,
        table_name="audit.paper_research_packet_quality_reports",
    )

    assert reports == (
        FakeResearchPacketQualityReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            quality_status=row.quality_status,
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
            source_generated_at,
            source_config_version,
            input_row_count,
            packet_row_count,
            included_count,
            skipped_count,
            high_priority_count,
            medium_priority_count,
            low_priority_count,
            source_age_seconds,
            included_share,
            skipped_share,
            check_count,
            pass_count,
            watch_count,
            blocked_count,
            quality_status,
            check_rows_json,
            reason_code_counts_json,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM audit.paper_research_packet_quality_reports
        WHERE config_version = %s AND quality_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-research-packet-quality-v0", "blocked", 25)


def test_load_quality_reports_accepts_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(quality_status="pass")
    positional_connection = FakeConnection(rows=(tuple(row.__dict__.values()),))
    dict_connection = FakeConnection(
        rows=(
            {
                "report_sha256": row.report_sha256,
                "generated_at": row.generated_at,
                "config_version": row.config_version,
                "source_generated_at": row.source_generated_at,
                "source_config_version": row.source_config_version,
                "input_row_count": row.input_row_count,
                "packet_row_count": row.packet_row_count,
                "included_count": row.included_count,
                "skipped_count": row.skipped_count,
                "high_priority_count": row.high_priority_count,
                "medium_priority_count": row.medium_priority_count,
                "low_priority_count": row.low_priority_count,
                "source_age_seconds": row.source_age_seconds,
                "included_share": row.included_share,
                "skipped_share": row.skipped_share,
                "check_count": row.check_count,
                "pass_count": row.pass_count,
                "watch_count": row.watch_count,
                "blocked_count": row.blocked_count,
                "quality_status": "watch",
                "check_rows_json": row.check_rows_json,
                "reason_code_counts_json": row.reason_code_counts_json,
                "reason_codes_json": row.reason_codes_json,
                "reason_code_count": row.reason_code_count,
                "payload_json": row.payload_json,
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )
    record_type = namedtuple(
        "ResearchPacketQualityRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "source_generated_at",
            "source_config_version",
            "input_row_count",
            "packet_row_count",
            "included_count",
            "skipped_count",
            "high_priority_count",
            "medium_priority_count",
            "low_priority_count",
            "source_age_seconds",
            "included_share",
            "skipped_share",
            "check_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "quality_status",
            "check_rows_json",
            "reason_code_counts_json",
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
                row.source_generated_at,
                row.source_config_version,
                row.input_row_count,
                row.packet_row_count,
                row.included_count,
                row.skipped_count,
                row.high_priority_count,
                row.medium_priority_count,
                row.low_priority_count,
                row.source_age_seconds,
                row.included_share,
                row.skipped_share,
                row.check_count,
                row.pass_count,
                row.watch_count,
                row.blocked_count,
                "blocked",
                row.check_rows_json,
                row.reason_code_counts_json,
                row.reason_codes_json,
                row.reason_code_count,
                row.payload_json,
                True,
                True,
                True,
            ),
        ),
    )

    assert store_module.load_paper_research_packet_quality_reports(
        positional_connection,
    ) == (
        FakeResearchPacketQualityReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            quality_status="pass",
        ),
    )
    assert store_module.load_paper_research_packet_quality_reports(dict_connection) == (
        FakeResearchPacketQualityReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            quality_status="watch",
        ),
    )
    assert store_module.load_paper_research_packet_quality_reports(
        namedtuple_connection,
    ) == (
        FakeResearchPacketQualityReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            quality_status="blocked",
        ),
    )


def test_load_quality_reports_accepts_empty_reads(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection(rows=())

    assert store_module.load_paper_research_packet_quality_reports(connection) == ()
    assert connection.cursor_count == 1
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit..paper_research_packet_quality_reports"}, "table_name"),
        ({"table_name": "audit.paper.research_packet_quality_reports"}, "table_name"),
        ({"table_name": "PaperResearchPacketQualityReports"}, "table_name"),
        ({"table_name": "paper-research-packet-quality-reports"}, "table_name"),
        ({"table_name": "paper_research_packet_quality_reports_"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"quality_status": "stable"}, "quality_status"),
        ({"quality_status": True}, "quality_status"),
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
        store_module.load_paper_research_packet_quality_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_insert_result_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_REPORTS_TABLE == (
        "paper_research_packet_quality_reports"
    )
    assert "DEFAULT_PAPER_RESEARCH_PACKET_QUALITY_REPORTS_TABLE" in store_module.__all__
    assert "PaperResearchPacketQualityInsertResult" in store_module.__all__
    assert "insert_paper_research_packet_quality_report" in store_module.__all__
    assert "insert_paper_research_packet_quality_report_with_result" in store_module.__all__
    assert "load_paper_research_packet_quality_reports" in store_module.__all__
