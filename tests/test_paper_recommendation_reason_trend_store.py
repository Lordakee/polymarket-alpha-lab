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
class FakeReasonTrendReport:
    generated_at: datetime
    config_version: str
    source_report_count: int


@dataclass(frozen=True)
class FakeReasonTrendDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_report_count: int
    reason_trend_rows_json: list[dict[str, Any]]
    transition_trend_rows_json: list[dict[str, Any]]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        *,
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
    ) -> None:
        self.rows = rows
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
        *,
        execute_error: BaseException | None = None,
        fetchall_error: BaseException | None = None,
        close_error: BaseException | None = None,
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


def fake_db_row(
    *,
    report_sha256: str = "b" * 64,
    generated_at: datetime = datetime(2026, 6, 22, 10, 0, tzinfo=UTC),
    config_version: str = "paper-recommendation-reason-trend-v0",
    source_report_count: int = 3,
) -> FakeReasonTrendDbRow:
    return FakeReasonTrendDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        source_report_count=source_report_count,
        reason_trend_rows_json=[
            {
                "reason_code": "insufficient_edge",
                "source_status": "watch",
                "count": 2,
            },
        ],
        transition_trend_rows_json=[
            {
                "market_slug": "market-a",
                "side": "yes",
                "from_status": "watch",
                "to_status": "blocked",
                "transition_count": 1,
            },
        ],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "source_report_count": source_report_count,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_recommendation_reason_trend_db_row",
    )

    def to_db_row(report: FakeReasonTrendReport) -> FakeReasonTrendDbRow:
        return FakeReasonTrendDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            source_report_count=report.source_report_count,
            reason_trend_rows_json=[
                {
                    "reason_code": "insufficient_edge",
                    "source_status": "watch",
                    "count": 2,
                },
            ],
            transition_trend_rows_json=[
                {
                    "market_slug": "market-a",
                    "side": "yes",
                    "from_status": "watch",
                    "to_status": "blocked",
                    "transition_count": 1,
                },
            ],
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "source_report_count": report.source_report_count,
            },
        )

    def from_db_row(row: FakeReasonTrendDbRow) -> FakeReasonTrendReport:
        return FakeReasonTrendReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_report_count=row.source_report_count,
        )

    companion.PaperRecommendationReasonTrendDbRow = FakeReasonTrendDbRow
    companion.paper_recommendation_reason_trend_report_to_db_row = to_db_row
    companion.paper_recommendation_reason_trend_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_reason_trend_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_recommendation_reason_trend_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_reason_trend_store",
    )


def test_insert_paper_recommendation_reason_trend_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReasonTrendReport(
        generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
        config_version="paper-recommendation-reason-trend-v0",
        source_report_count=3,
    )

    inserted = store_module.insert_paper_recommendation_reason_trend_report(
        connection,
        report,
    )

    assert inserted == FakeReasonTrendDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_report_count=3,
        reason_trend_rows_json=[
            {
                "reason_code": "insufficient_edge",
                "source_status": "watch",
                "count": 2,
            },
        ],
        transition_trend_rows_json=[
            {
                "market_slug": "market-a",
                "side": "yes",
                "from_status": "watch",
                "to_status": "blocked",
                "transition_count": 1,
            },
        ],
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "source_report_count": 3,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_reason_trend_reports (
            report_sha256,
            generated_at,
            config_version,
            source_report_count,
            reason_trend_rows,
            transition_trend_rows,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        3,
        [
            {
                "reason_code": "insufficient_edge",
                "source_status": "watch",
                "count": 2,
            },
        ],
        [
            {
                "market_slug": "market-a",
                "side": "yes",
                "from_status": "watch",
                "to_status": "blocked",
                "transition_count": 1,
            },
        ],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "source_report_count": 3,
        },
        True,
        True,
        True,
    )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_recommendation_reason_trend_report(
            connection,
            FakeReasonTrendReport(
                generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                config_version="paper-recommendation-reason-trend-v0",
                source_report_count=3,
            ),
            table_name="paper_recommendation_reason_trend_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


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
        store_module.insert_paper_recommendation_reason_trend_report(
            connection,
            FakeReasonTrendReport(
                generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                config_version="paper-recommendation-reason-trend-v0",
                source_report_count=3,
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.closed is True


def test_insert_propagates_cursor_close_exception_after_successful_execute(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.insert_paper_recommendation_reason_trend_report(
            connection,
            FakeReasonTrendReport(
                generated_at=datetime(2026, 6, 22, 9, 30, tzinfo=UTC),
                config_version="paper-recommendation-reason-trend-v0",
                source_report_count=3,
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_propagates_cursor_close_exception_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        rows=(fake_db_row(source_report_count=1),),
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_recommendation_reason_trend_reports(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_preserves_fetchall_exception_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="fetchall failed") as exc_info:
        store_module.load_paper_recommendation_reason_trend_reports(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.closed is True


def test_load_paper_recommendation_reason_trend_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(source_report_count=4)
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_reason_trend_reports(
        connection,
        config_version="paper-recommendation-reason-trend-v0",
        limit=25,
        table_name="reason_trend_archive",
    )

    assert reports == (
        FakeReasonTrendReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_report_count=4,
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
            source_report_count,
            reason_trend_rows,
            transition_trend_rows,
            payload,
            paper_only,
            report_only,
            readonly
        FROM reason_trend_archive
        WHERE config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-reason-trend-v0", 25)


def test_load_paper_recommendation_reason_trend_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 11, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-recommendation-reason-trend-v0",
                2,
                [{"reason_code": "insufficient_edge"}],
                [{"market_slug": "market-a"}],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-reason-trend-v0",
                    "source_report_count": 2,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_reason_trend_reports(connection)

    assert reports == (
        FakeReasonTrendReport(
            generated_at=generated_at,
            config_version="paper-recommendation-reason-trend-v0",
            source_report_count=2,
        ),
    )


def test_load_paper_recommendation_reason_trend_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 12, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "paper-recommendation-reason-trend-v0",
                "source_report_count": 5,
                "reason_trend_rows": [{"reason_code": "insufficient_edge"}],
                "transition_trend_rows": [{"market_slug": "market-a"}],
                "payload": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-reason-trend-v0",
                    "source_report_count": 5,
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_recommendation_reason_trend_reports(connection)

    assert reports == (
        FakeReasonTrendReport(
            generated_at=generated_at,
            config_version="paper-recommendation-reason-trend-v0",
            source_report_count=5,
        ),
    )


def test_load_paper_recommendation_reason_trend_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 22, 13, 0, tzinfo=UTC)
    record_type = namedtuple(
        "ReasonTrendRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "source_report_count",
            "reason_trend_rows",
            "transition_trend_rows",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    connection = FakeConnection(
        rows=(
            record_type(
                "e" * 64,
                generated_at,
                "paper-recommendation-reason-trend-v0",
                6,
                [{"reason_code": "insufficient_edge"}],
                [{"market_slug": "market-a"}],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-reason-trend-v0",
                    "source_report_count": 6,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_reason_trend_reports(connection)

    assert reports == (
        FakeReasonTrendReport(
            generated_at=generated_at,
            config_version="paper-recommendation-reason-trend-v0",
            source_report_count=6,
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_reason_trend_reports"}, "table_name"),
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
        store_module.load_paper_recommendation_reason_trend_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
