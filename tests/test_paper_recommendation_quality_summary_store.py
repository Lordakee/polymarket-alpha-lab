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
class FakeQualitySummaryReport:
    generated_at: datetime
    config_version: str
    summary_status: str


@dataclass(frozen=True)
class FakeQualitySummaryDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    summary_status: str
    subreport_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    incomplete_count: int
    reason_code_counts_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    subreports_json: list[dict[str, Any]]
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
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            rowcount,
            execute_error=execute_error,
            fetchall_error=fetchall_error,
            close_error=close_error,
        )
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
    config_version: str = "paper-recommendation-quality-summary-v0",
    summary_status: str = "watch",
) -> FakeQualitySummaryDbRow:
    return FakeQualitySummaryDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        summary_status=summary_status,
        subreport_count=5,
        pass_count=3,
        watch_count=2,
        blocked_count=0,
        incomplete_count=0,
        reason_code_counts_json=[{"reason_code": "wide_spread", "subreport_count": 2}],
        reason_codes_json=["wide_spread"],
        subreports_json=[
            {
                "report_name": "health",
                "status": "pass",
                "generated_at": generated_at.isoformat(),
                "config_version": "paper-recommendation-health-v0",
                "row_count": 3,
                "reason_codes": ["wide_spread"],
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "summary_status": summary_status,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_recommendation_quality_summary_db_row",
    )

    def to_db_row(report: FakeQualitySummaryReport) -> FakeQualitySummaryDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            summary_status=report.summary_status,
        )

    def from_db_row(row: FakeQualitySummaryDbRow) -> FakeQualitySummaryReport:
        return FakeQualitySummaryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            summary_status=row.summary_status,
        )

    companion.PaperRecommendationQualitySummaryDbRow = FakeQualitySummaryDbRow
    companion.paper_recommendation_quality_summary_report_to_db_row = to_db_row
    companion.paper_recommendation_quality_summary_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_quality_summary_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_recommendation_quality_summary_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_quality_summary_store",
    )


def test_insert_quality_summary_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeQualitySummaryReport(
        generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
        config_version="paper-recommendation-quality-summary-v0",
        summary_status="watch",
    )

    inserted = store_module.insert_paper_recommendation_quality_summary_report(
        connection,
        report,
    )

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        summary_status=report.summary_status,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_quality_summary_reports (
            report_sha256,
            generated_at,
            config_version,
            summary_status,
            subreport_count,
            pass_count,
            watch_count,
            blocked_count,
            incomplete_count,
            reason_code_counts_json,
            reason_codes_json,
            subreports_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        "watch",
        5,
        3,
        2,
        0,
        0,
        [{"reason_code": "wide_spread", "subreport_count": 2}],
        ["wide_spread"],
        [
            {
                "report_name": "health",
                "status": "pass",
                "generated_at": report.generated_at.isoformat(),
                "config_version": "paper-recommendation-health-v0",
                "row_count": 3,
                "reason_codes": ["wide_spread"],
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "summary_status": report.summary_status,
        },
        True,
        True,
        True,
    )


def test_insert_quality_summary_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    assert hasattr(
        store_module,
        "insert_paper_recommendation_quality_summary_report_with_result",
    )
    report = FakeQualitySummaryReport(
        generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
        config_version="paper-recommendation-quality-summary-v0",
        summary_status="watch",
    )
    expected_row = fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        summary_status=report.summary_status,
    )

    inserted = store_module.insert_paper_recommendation_quality_summary_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = (
        store_module.insert_paper_recommendation_quality_summary_report_with_result(
            FakeConnection(rowcount=0),
            report,
        )
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_quality_summary_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_recommendation_quality_summary_report_with_result(
            FakeConnection(rowcount=2),
            FakeQualitySummaryReport(
                generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
                config_version="paper-recommendation-quality-summary-v0",
                summary_status="watch",
            ),
        )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_recommendation_quality_summary_report(
            connection,
            FakeQualitySummaryReport(
                generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
                config_version="paper-recommendation-quality-summary-v0",
                summary_status="pass",
            ),
            table_name="paper_recommendation_quality_summary_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_preserves_execute_exception_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="execute failed") as exc_info:
        store_module.insert_paper_recommendation_quality_summary_report(
            connection,
            FakeQualitySummaryReport(
                generated_at=datetime(2026, 6, 22, 21, 30, tzinfo=UTC),
                config_version="paper-recommendation-quality-summary-v0",
                summary_status="pass",
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_load_propagates_cursor_close_exception_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        rows=(fake_db_row(summary_status="pass"),),
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_recommendation_quality_summary_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_quality_summary_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(summary_status="blocked")
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_quality_summary_reports(
        connection,
        config_version="paper-recommendation-quality-summary-v0",
        summary_status="blocked",
        limit=25,
        table_name="quality_summary_archive",
    )

    assert reports == (
        FakeQualitySummaryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            summary_status=row.summary_status,
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
            summary_status,
            subreport_count,
            pass_count,
            watch_count,
            blocked_count,
            incomplete_count,
            reason_code_counts_json,
            reason_codes_json,
            subreports_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM quality_summary_archive
        WHERE config_version = %s AND summary_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-quality-summary-v0", "blocked", 25)


def test_load_quality_summary_reports_accepts_positional_dict_and_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 21, 0, tzinfo=UTC)
    positional_connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-recommendation-quality-summary-v0",
                "pass",
                5,
                5,
                0,
                0,
                0,
                [{"reason_code": "wide_spread", "subreport_count": 2}],
                ["wide_spread"],
                [{"report_name": "health"}],
                {"generated_at": generated_at.isoformat(), "summary_status": "pass"},
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
                "config_version": "paper-recommendation-quality-summary-v0",
                "summary_status": "watch",
                "subreport_count": 5,
                "pass_count": 3,
                "watch_count": 2,
                "blocked_count": 0,
                "incomplete_count": 0,
                "reason_code_counts_json": [{"reason_code": "wide_spread", "subreport_count": 2}],
                "reason_codes_json": ["wide_spread"],
                "subreports_json": [{"report_name": "health"}],
                "payload_json": {"generated_at": generated_at.isoformat(), "summary_status": "watch"},
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )
    record_type = namedtuple(
        "QualitySummaryRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "summary_status",
            "subreport_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "incomplete_count",
            "reason_code_counts_json",
            "reason_codes_json",
            "subreports_json",
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
                "paper-recommendation-quality-summary-v0",
                "blocked",
                5,
                3,
                1,
                1,
                0,
                [{"reason_code": "wide_spread", "subreport_count": 2}],
                ["wide_spread"],
                [{"report_name": "health"}],
                {"generated_at": generated_at.isoformat(), "summary_status": "blocked"},
                True,
                True,
                True,
            ),
        ),
    )

    assert store_module.load_paper_recommendation_quality_summary_reports(
        positional_connection,
    ) == (
        FakeQualitySummaryReport(
            generated_at=generated_at,
            config_version="paper-recommendation-quality-summary-v0",
            summary_status="pass",
        ),
    )
    assert store_module.load_paper_recommendation_quality_summary_reports(
        dict_connection,
    ) == (
        FakeQualitySummaryReport(
            generated_at=generated_at,
            config_version="paper-recommendation-quality-summary-v0",
            summary_status="watch",
        ),
    )
    assert store_module.load_paper_recommendation_quality_summary_reports(
        namedtuple_connection,
    ) == (
        FakeQualitySummaryReport(
            generated_at=generated_at,
            config_version="paper-recommendation-quality-summary-v0",
            summary_status="blocked",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_quality_summary_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"summary_status": "stable"}, "summary_status"),
        ({"summary_status": True}, "summary_status"),
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
        store_module.load_paper_recommendation_quality_summary_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_insert_result_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE == (
        "paper_recommendation_quality_summary_reports"
    )
    assert "DEFAULT_PAPER_RECOMMENDATION_QUALITY_SUMMARY_REPORTS_TABLE" in store_module.__all__
    assert "PaperRecommendationQualitySummaryInsertResult" in store_module.__all__
    assert "insert_paper_recommendation_quality_summary_report" in store_module.__all__
    assert (
        "insert_paper_recommendation_quality_summary_report_with_result"
        in store_module.__all__
    )
    assert "load_paper_recommendation_quality_summary_reports" in store_module.__all__
