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
class FakeQueueReport:
    generated_at: datetime
    source_config_version: str
    input_count: int
    queue_count: int


@dataclass(frozen=True)
class FakeQueueDbRow:
    report_sha256: str
    generated_at: datetime
    source_config_version: str
    input_count: int
    queue_count: int
    research_review_count: int
    await_fresh_context_count: int
    skip_count: int
    excluded_count: int
    reason_code_counts_json: dict[str, int]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False
        self.close_count = 0
        self.execute_error = execute_error
        self.fetchall_error = fetchall_error
        self.close_error = close_error

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
        if self.fetchall_error is not None:
            raise self.fetchall_error
        return self.rows

    def close(self) -> None:
        self.close_count += 1
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeConnection:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
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


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_probability_recommendation_queue_db_row",
    )

    def to_db_row(report: FakeQueueReport) -> FakeQueueDbRow:
        return FakeQueueDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            source_config_version=report.source_config_version,
            input_count=report.input_count,
            queue_count=report.queue_count,
            research_review_count=2,
            await_fresh_context_count=1,
            skip_count=3,
            excluded_count=4,
            reason_code_counts_json={
                "missing_probability": 2,
                "stale_context": 1,
            },
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "source_config_version": report.source_config_version,
                "input_count": report.input_count,
                "queue_count": report.queue_count,
            },
        )

    def from_db_row(row: FakeQueueDbRow) -> FakeQueueReport:
        return FakeQueueReport(
            generated_at=row.generated_at,
            source_config_version=row.source_config_version,
            input_count=row.input_count,
            queue_count=row.queue_count,
        )

    companion.PaperProbabilityRecommendationQueueDbRow = FakeQueueDbRow
    companion.paper_probability_recommendation_queue_report_to_db_row = to_db_row
    companion.paper_probability_recommendation_queue_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_probability_recommendation_queue_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_probability_recommendation_queue_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_probability_recommendation_queue_store",
    )


def test_insert_paper_probability_recommendation_queue_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeQueueReport(
        generated_at=datetime(2026, 6, 20, 9, 15, tzinfo=UTC),
        source_config_version="paper-probability-queue-v0",
        input_count=10,
        queue_count=4,
    )

    inserted = store_module.insert_paper_probability_recommendation_queue_report(
        connection,
        report,
    )

    assert inserted == FakeQueueDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        source_config_version=report.source_config_version,
        input_count=10,
        queue_count=4,
        research_review_count=2,
        await_fresh_context_count=1,
        skip_count=3,
        excluded_count=4,
        reason_code_counts_json={
            "missing_probability": 2,
            "stale_context": 1,
        },
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "source_config_version": report.source_config_version,
            "input_count": 10,
            "queue_count": 4,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_probability_recommendation_queue_reports (
            report_sha256,
            generated_at,
            source_config_version,
            input_count,
            queue_count,
            research_review_count,
            await_fresh_context_count,
            skip_count,
            excluded_count,
            reason_code_counts,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        "paper-probability-queue-v0",
        10,
        4,
        2,
        1,
        3,
        4,
        {"missing_probability": 2, "stale_context": 1},
        {
            "generated_at": report.generated_at.isoformat(),
            "source_config_version": "paper-probability-queue-v0",
            "input_count": 10,
            "queue_count": 4,
        },
        True,
        True,
        True,
    )


def test_insert_rejects_unsafe_table_name_without_opening_cursor(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_probability_recommendation_queue_report(
            connection,
            FakeQueueReport(
                generated_at=datetime(2026, 6, 20, 9, 15, tzinfo=UTC),
                source_config_version="paper-probability-queue-v0",
                input_count=10,
                queue_count=4,
            ),
            table_name="paper_probability_recommendation_queue_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = CursorCloseFailure("close failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_paper_probability_recommendation_queue_report(
            connection,
            FakeQueueReport(
                generated_at=datetime(2026, 6, 20, 9, 15, tzinfo=UTC),
                source_config_version="paper-probability-queue-v0",
                input_count=10,
                queue_count=4,
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_insert_propagates_cursor_close_error_after_successful_execute(
    store_module: types.ModuleType,
) -> None:
    close_error = CursorCloseFailure("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(CursorCloseFailure) as exc_info:
        store_module.insert_paper_probability_recommendation_queue_report(
            connection,
            FakeQueueReport(
                generated_at=datetime(2026, 6, 20, 9, 15, tzinfo=UTC),
                source_config_version="paper-probability-queue-v0",
                input_count=10,
                queue_count=4,
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_paper_probability_recommendation_queue_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeQueueDbRow(
        report_sha256="b" * 64,
        generated_at=datetime(2026, 6, 20, 10, 30, tzinfo=UTC),
        source_config_version="paper-probability-queue-v0",
        input_count=12,
        queue_count=5,
        research_review_count=2,
        await_fresh_context_count=1,
        skip_count=3,
        excluded_count=4,
        reason_code_counts_json={
            "missing_probability": 2,
            "stale_context": 1,
        },
        payload_json={
            "generated_at": "2026-06-20T10:30:00+00:00",
            "source_config_version": "paper-probability-queue-v0",
            "input_count": 12,
            "queue_count": 5,
        },
    )
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_probability_recommendation_queue_reports(
        connection,
        source_config_version="paper-probability-queue-v0",
        limit=25,
        table_name="probability_queue_archive",
    )

    assert reports == (
        FakeQueueReport(
            generated_at=row.generated_at,
            source_config_version=row.source_config_version,
            input_count=12,
            queue_count=5,
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
            source_config_version,
            input_count,
            queue_count,
            research_review_count,
            await_fresh_context_count,
            skip_count,
            excluded_count,
            reason_code_counts,
            payload,
            paper_only,
            report_only,
            readonly
        FROM probability_queue_archive
        WHERE source_config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-probability-queue-v0", 25)


def test_load_propagates_cursor_close_error_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = CursorCloseFailure("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(CursorCloseFailure) as exc_info:
        store_module.load_paper_probability_recommendation_queue_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


def test_load_preserves_fetchall_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = CursorCloseFailure("close failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_paper_probability_recommendation_queue_reports(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_paper_probability_recommendation_queue_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 10, 30, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-probability-queue-v0",
                8,
                3,
                1,
                2,
                1,
                2,
                {"fresh_context_needed": 2},
                {
                    "generated_at": "2026-06-20T10:30:00+00:00",
                    "source_config_version": "paper-probability-queue-v0",
                    "input_count": 8,
                    "queue_count": 3,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_probability_recommendation_queue_reports(
        connection,
    )

    assert reports == (
        FakeQueueReport(
            generated_at=generated_at,
            source_config_version="paper-probability-queue-v0",
            input_count=8,
            queue_count=3,
        ),
    )


def test_load_paper_probability_recommendation_queue_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 11, 30, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "source_config_version": "paper-probability-queue-v0",
                "input_count": 9,
                "queue_count": 4,
                "research_review_count": 2,
                "await_fresh_context_count": 1,
                "skip_count": 1,
                "excluded_count": 2,
                "reason_code_counts": {"fresh_context_needed": 1},
                "payload": {
                    "generated_at": "2026-06-20T11:30:00+00:00",
                    "source_config_version": "paper-probability-queue-v0",
                    "input_count": 9,
                    "queue_count": 4,
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_probability_recommendation_queue_reports(
        connection,
    )

    assert reports == (
        FakeQueueReport(
            generated_at=generated_at,
            source_config_version="paper-probability-queue-v0",
            input_count=9,
            queue_count=4,
        ),
    )


def test_load_paper_probability_recommendation_queue_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 20, 12, 30, tzinfo=UTC)
    Record = namedtuple(
        "Record",
        (
            "report_sha256",
            "generated_at",
            "source_config_version",
            "input_count",
            "queue_count",
            "research_review_count",
            "await_fresh_context_count",
            "skip_count",
            "excluded_count",
            "reason_code_counts",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    connection = FakeConnection(
        rows=(
            Record(
                "e" * 64,
                generated_at,
                "paper-probability-queue-v0",
                11,
                6,
                3,
                1,
                2,
                2,
                {"fresh_context_needed": 1, "missing_probability": 2},
                {
                    "generated_at": "2026-06-20T12:30:00+00:00",
                    "source_config_version": "paper-probability-queue-v0",
                    "input_count": 11,
                    "queue_count": 6,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_probability_recommendation_queue_reports(
        connection,
    )

    assert reports == (
        FakeQueueReport(
            generated_at=generated_at,
            source_config_version="paper-probability-queue-v0",
            input_count=11,
            queue_count=6,
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_probability_recommendation_queue_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"source_config_version": ""}, "source_config_version"),
        ({"source_config_version": " paper-v0"}, "source_config_version"),
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
        store_module.load_paper_probability_recommendation_queue_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
