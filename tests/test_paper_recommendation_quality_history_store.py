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
class FakeQualityHistoryReport:
    generated_at: datetime
    config_version: str
    history_status: str


@dataclass(frozen=True)
class FakeQualityHistoryDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    history_status: str
    source_report_count: int
    first_source_generated_at: datetime | None
    latest_source_generated_at: datetime | None
    summary_status_rows_json: list[dict[str, Any]]
    pass_summary_count: int
    watch_summary_count: int
    blocked_summary_count: int
    incomplete_summary_count: int
    duplicate_generated_at_count: int
    recurring_blocked_reason_codes_json: list[str]
    recurring_incomplete_subreports_json: list[dict[str, Any]]
    recurring_incomplete_subreport_count: int
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
    generated_at: datetime = datetime(2026, 6, 22, 18, 0, tzinfo=UTC),
    config_version: str = "paper-recommendation-quality-history-v0",
    history_status: str = "watch",
) -> FakeQualityHistoryDbRow:
    first_source = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    latest_source = datetime(2026, 6, 22, 14, 0, tzinfo=UTC)
    summary_rows = [
        {
            "summary_status": "pass",
            "status_count": 2,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "summary_status": "watch",
            "status_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "summary_status": "blocked",
            "status_count": 0,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "summary_status": "incomplete",
            "status_count": 0,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    recurring_rows = [
        {
            "report_name": "health",
            "incomplete_count": 2,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    reason_codes = [
        "duplicate_generated_at_threshold_exceeded",
        "recurring_incomplete_subreports_present",
    ]
    return FakeQualityHistoryDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        history_status=history_status,
        source_report_count=3,
        first_source_generated_at=first_source,
        latest_source_generated_at=latest_source,
        summary_status_rows_json=summary_rows,
        pass_summary_count=2,
        watch_summary_count=1,
        blocked_summary_count=0,
        incomplete_summary_count=0,
        duplicate_generated_at_count=1,
        recurring_blocked_reason_codes_json=["empty_selection"],
        recurring_incomplete_subreports_json=recurring_rows,
        recurring_incomplete_subreport_count=1,
        reason_codes_json=reason_codes,
        reason_code_count=2,
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "history_status": history_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_recommendation_quality_history_db_row",
    )

    def to_db_row(report: FakeQualityHistoryReport) -> FakeQualityHistoryDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            history_status=report.history_status,
        )

    def from_db_row(row: FakeQualityHistoryDbRow) -> FakeQualityHistoryReport:
        return FakeQualityHistoryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            history_status=row.history_status,
        )

    companion.PaperRecommendationQualityHistoryDbRow = FakeQualityHistoryDbRow
    companion.paper_recommendation_quality_history_report_to_db_row = to_db_row
    companion.paper_recommendation_quality_history_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_quality_history_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_recommendation_quality_history_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_quality_history_store",
    )


def test_insert_quality_history_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeQualityHistoryReport(
        generated_at=datetime(2026, 6, 22, 18, 30, tzinfo=UTC),
        config_version="paper-recommendation-quality-history-v0",
        history_status="watch",
    )

    inserted = store_module.insert_paper_recommendation_quality_history_report(
        connection,
        report,
    )

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        history_status=report.history_status,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_quality_history_reports (
            report_sha256,
            generated_at,
            config_version,
            history_status,
            source_report_count,
            first_source_generated_at,
            latest_source_generated_at,
            summary_status_rows_json,
            pass_summary_count,
            watch_summary_count,
            blocked_summary_count,
            incomplete_summary_count,
            duplicate_generated_at_count,
            recurring_blocked_reason_codes_json,
            recurring_incomplete_subreports_json,
            recurring_incomplete_subreport_count,
            reason_codes_json,
            reason_code_count,
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
        report.config_version,
        "watch",
        3,
        datetime(2026, 6, 22, 12, 0, tzinfo=UTC),
        datetime(2026, 6, 22, 14, 0, tzinfo=UTC),
        fake_db_row().summary_status_rows_json,
        2,
        1,
        0,
        0,
        1,
        ["empty_selection"],
        fake_db_row().recurring_incomplete_subreports_json,
        1,
        [
            "duplicate_generated_at_threshold_exceeded",
            "recurring_incomplete_subreports_present",
        ],
        2,
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "history_status": report.history_status,
        },
        True,
        True,
        True,
    )


def test_insert_quality_history_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    assert hasattr(
        store_module,
        "insert_paper_recommendation_quality_history_report_with_result",
    )
    report = FakeQualityHistoryReport(
        generated_at=datetime(2026, 6, 22, 18, 30, tzinfo=UTC),
        config_version="paper-recommendation-quality-history-v0",
        history_status="watch",
    )
    expected_row = fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        history_status=report.history_status,
    )

    inserted = store_module.insert_paper_recommendation_quality_history_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = (
        store_module.insert_paper_recommendation_quality_history_report_with_result(
            FakeConnection(rowcount=0),
            report,
        )
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_quality_history_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_recommendation_quality_history_report_with_result(
            FakeConnection(rowcount=2),
            FakeQualityHistoryReport(
                generated_at=datetime(2026, 6, 22, 18, 30, tzinfo=UTC),
                config_version="paper-recommendation-quality-history-v0",
                history_status="watch",
            ),
        )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_recommendation_quality_history_report(
            connection,
            FakeQualityHistoryReport(
                generated_at=datetime(2026, 6, 22, 18, 30, tzinfo=UTC),
                config_version="paper-recommendation-quality-history-v0",
                history_status="pass",
            ),
            table_name="paper_recommendation_quality_history_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_quality_history_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(history_status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_quality_history_reports(
        connection,
        config_version="paper-recommendation-quality-history-v0",
        history_status="blocked",
        limit=25,
        table_name="quality_history_archive",
    )

    assert reports == (
        FakeQualityHistoryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            history_status=row.history_status,
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
            history_status,
            source_report_count,
            first_source_generated_at,
            latest_source_generated_at,
            summary_status_rows_json,
            pass_summary_count,
            watch_summary_count,
            blocked_summary_count,
            incomplete_summary_count,
            duplicate_generated_at_count,
            recurring_blocked_reason_codes_json,
            recurring_incomplete_subreports_json,
            recurring_incomplete_subreport_count,
            reason_codes_json,
            reason_code_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM quality_history_archive
        WHERE config_version = %s AND history_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-quality-history-v0", "blocked", 25)


def test_load_quality_history_reports_accepts_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(history_status="pass")
    positional_connection = FakeConnection(rows=(tuple(row.__dict__.values()),))
    dict_connection = FakeConnection(
        rows=(
            {
                "report_sha256": row.report_sha256,
                "generated_at": row.generated_at,
                "config_version": row.config_version,
                "history_status": "watch",
                "source_report_count": row.source_report_count,
                "first_source_generated_at": row.first_source_generated_at,
                "latest_source_generated_at": row.latest_source_generated_at,
                "summary_status_rows_json": row.summary_status_rows_json,
                "pass_summary_count": row.pass_summary_count,
                "watch_summary_count": row.watch_summary_count,
                "blocked_summary_count": row.blocked_summary_count,
                "incomplete_summary_count": row.incomplete_summary_count,
                "duplicate_generated_at_count": row.duplicate_generated_at_count,
                "recurring_blocked_reason_codes_json": row.recurring_blocked_reason_codes_json,
                "recurring_incomplete_subreports_json": row.recurring_incomplete_subreports_json,
                "recurring_incomplete_subreport_count": row.recurring_incomplete_subreport_count,
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
        "QualityHistoryRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "history_status",
            "source_report_count",
            "first_source_generated_at",
            "latest_source_generated_at",
            "summary_status_rows_json",
            "pass_summary_count",
            "watch_summary_count",
            "blocked_summary_count",
            "incomplete_summary_count",
            "duplicate_generated_at_count",
            "recurring_blocked_reason_codes_json",
            "recurring_incomplete_subreports_json",
            "recurring_incomplete_subreport_count",
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
                row.source_report_count,
                row.first_source_generated_at,
                row.latest_source_generated_at,
                row.summary_status_rows_json,
                row.pass_summary_count,
                row.watch_summary_count,
                row.blocked_summary_count,
                row.incomplete_summary_count,
                row.duplicate_generated_at_count,
                row.recurring_blocked_reason_codes_json,
                row.recurring_incomplete_subreports_json,
                row.recurring_incomplete_subreport_count,
                row.reason_codes_json,
                row.reason_code_count,
                row.payload_json,
                True,
                True,
                True,
            ),
        ),
    )

    assert store_module.load_paper_recommendation_quality_history_reports(
        positional_connection,
    ) == (
        FakeQualityHistoryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            history_status="pass",
        ),
    )
    assert store_module.load_paper_recommendation_quality_history_reports(
        dict_connection,
    ) == (
        FakeQualityHistoryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            history_status="watch",
        ),
    )
    assert store_module.load_paper_recommendation_quality_history_reports(
        namedtuple_connection,
    ) == (
        FakeQualityHistoryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            history_status="blocked",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_quality_history_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"history_status": "stable"}, "history_status"),
        ({"history_status": True}, "history_status"),
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
        store_module.load_paper_recommendation_quality_history_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_insert_result_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.DEFAULT_PAPER_RECOMMENDATION_QUALITY_HISTORY_REPORTS_TABLE == (
        "paper_recommendation_quality_history_reports"
    )
    assert "DEFAULT_PAPER_RECOMMENDATION_QUALITY_HISTORY_REPORTS_TABLE" in store_module.__all__
    assert "PaperRecommendationQualityHistoryInsertResult" in store_module.__all__
    assert "insert_paper_recommendation_quality_history_report" in store_module.__all__
    assert (
        "insert_paper_recommendation_quality_history_report_with_result"
        in store_module.__all__
    )
    assert "load_paper_recommendation_quality_history_reports" in store_module.__all__
