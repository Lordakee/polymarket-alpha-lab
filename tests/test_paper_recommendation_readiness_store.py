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
class FakeReadinessReport:
    generated_at: datetime
    config_version: str
    blocked_count: int


@dataclass(frozen=True)
class FakeReadinessDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    input_count: int
    row_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    top_adjusted_net_probability_edge: Decimal
    total_cost_per_share: Decimal
    readiness_status_counts_json: dict[str, int]
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
    generated_at: datetime = datetime(2026, 6, 25, 8, 0, tzinfo=UTC),
    config_version: str = "paper-recommendation-readiness-v0",
    blocked_count: int = 1,
) -> FakeReadinessDbRow:
    return FakeReadinessDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        input_count=5,
        row_count=3,
        ready_count=1,
        watch_count=1,
        blocked_count=blocked_count,
        top_adjusted_net_probability_edge=Decimal("0.070000"),
        total_cost_per_share=Decimal("0.045000"),
        readiness_status_counts_json={"ready": 1, "watch": 1, "blocked": blocked_count},
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "blocked_count": blocked_count,
        },
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType("polymarket_alpha_lab.paper_recommendation_readiness_db_row")

    def to_db_row(report: FakeReadinessReport) -> FakeReadinessDbRow:
        return FakeReadinessDbRow(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            input_count=5,
            row_count=3,
            ready_count=1,
            watch_count=1,
            blocked_count=report.blocked_count,
            top_adjusted_net_probability_edge=Decimal("0.070000"),
            total_cost_per_share=Decimal("0.045000"),
            readiness_status_counts_json={
                "ready": 1,
                "watch": 1,
                "blocked": report.blocked_count,
            },
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "blocked_count": report.blocked_count,
            },
        )

    def from_db_row(row: FakeReadinessDbRow) -> FakeReadinessReport:
        return FakeReadinessReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            blocked_count=row.blocked_count,
        )

    companion.PaperRecommendationReadinessDbRow = FakeReadinessDbRow
    companion.paper_recommendation_readiness_report_to_db_row = to_db_row
    companion.paper_recommendation_readiness_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_readiness_db_row",
        companion,
    )
    sys.modules.pop("polymarket_alpha_lab.paper_recommendation_readiness_store", None)
    return importlib.import_module("polymarket_alpha_lab.paper_recommendation_readiness_store")


def test_insert_paper_recommendation_readiness_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeReadinessReport(
        generated_at=datetime(2026, 6, 25, 8, 30, tzinfo=UTC),
        config_version="paper-recommendation-readiness-v0",
        blocked_count=1,
    )

    inserted = store_module.insert_paper_recommendation_readiness_report(connection, report)

    assert inserted == FakeReadinessDbRow(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        input_count=5,
        row_count=3,
        ready_count=1,
        watch_count=1,
        blocked_count=1,
        top_adjusted_net_probability_edge=Decimal("0.070000"),
        total_cost_per_share=Decimal("0.045000"),
        readiness_status_counts_json={"ready": 1, "watch": 1, "blocked": 1},
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "blocked_count": 1,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_readiness_reports (
            report_sha256,
            generated_at,
            config_version,
            input_count,
            row_count,
            ready_count,
            watch_count,
            blocked_count,
            top_adjusted_net_probability_edge,
            total_cost_per_share,
            readiness_status_counts,
            payload,
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
        5,
        3,
        1,
        1,
        1,
        Decimal("0.070000"),
        Decimal("0.045000"),
        {"ready": 1, "watch": 1, "blocked": 1},
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "blocked_count": 1,
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
        store_module.insert_paper_recommendation_readiness_report(
            connection,
            FakeReadinessReport(
                generated_at=datetime(2026, 6, 25, 8, 30, tzinfo=UTC),
                config_version="paper-recommendation-readiness-v0",
                blocked_count=1,
            ),
            table_name="paper_recommendation_readiness_reports; drop table users",
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
        store_module.insert_paper_recommendation_readiness_report(
            connection,
            FakeReadinessReport(
                generated_at=datetime(2026, 6, 25, 8, 30, tzinfo=UTC),
                config_version="paper-recommendation-readiness-v0",
                blocked_count=1,
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
        store_module.insert_paper_recommendation_readiness_report(
            connection,
            FakeReadinessReport(
                generated_at=datetime(2026, 6, 25, 8, 30, tzinfo=UTC),
                config_version="paper-recommendation-readiness-v0",
                blocked_count=1,
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.closed is True


def test_load_propagates_cursor_close_exception_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        rows=(fake_db_row(blocked_count=0),),
        close_error=close_error,
    )

    with pytest.raises(RuntimeError, match="close failed") as exc_info:
        store_module.load_paper_recommendation_readiness_reports(connection)

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
        store_module.load_paper_recommendation_readiness_reports(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.closed is True


def test_load_paper_recommendation_readiness_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(blocked_count=2)
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_readiness_reports(
        connection,
        config_version="paper-recommendation-readiness-v0",
        min_blocked_count=1,
        limit=25,
        table_name="readiness_archive",
    )

    assert reports == (
        FakeReadinessReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            blocked_count=row.blocked_count,
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
            input_count,
            row_count,
            ready_count,
            watch_count,
            blocked_count,
            top_adjusted_net_probability_edge,
            total_cost_per_share,
            readiness_status_counts,
            payload,
            paper_only,
            report_only,
            readonly
        FROM readiness_archive
        WHERE config_version = %s AND blocked_count >= %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-readiness-v0", 1, 25)


def test_load_paper_recommendation_readiness_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 25, 9, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-recommendation-readiness-v1",
                4,
                2,
                1,
                0,
                1,
                Decimal("0.050000"),
                Decimal("0.025000"),
                {"ready": 1, "watch": 0, "blocked": 1},
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-recommendation-readiness-v1",
                    "blocked_count": 1,
                },
                True,
                True,
                True,
            ),
        ),
    )

    loaded = store_module.load_paper_recommendation_readiness_reports(connection)

    assert loaded == (
        FakeReadinessReport(
            generated_at=generated_at,
            config_version="paper-recommendation-readiness-v1",
            blocked_count=1,
        ),
    )


def test_load_paper_recommendation_readiness_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    Row = namedtuple(
        "Row",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "input_count",
            "row_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "top_adjusted_net_probability_edge",
            "total_cost_per_share",
            "readiness_status_counts",
            "payload",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    row = fake_db_row()
    connection = FakeConnection(
        rows=(
            Row(
                row.report_sha256,
                row.generated_at,
                row.config_version,
                row.input_count,
                row.row_count,
                row.ready_count,
                row.watch_count,
                row.blocked_count,
                row.top_adjusted_net_probability_edge,
                row.total_cost_per_share,
                row.readiness_status_counts_json,
                row.payload_json,
                row.paper_only,
                row.report_only,
                row.readonly,
            ),
        ),
    )

    loaded = store_module.load_paper_recommendation_readiness_reports(connection)

    assert loaded == (
        FakeReadinessReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            blocked_count=row.blocked_count,
        ),
    )


def test_load_paper_recommendation_readiness_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row()
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": row.report_sha256,
                "generated_at": row.generated_at,
                "config_version": row.config_version,
                "input_count": row.input_count,
                "row_count": row.row_count,
                "ready_count": row.ready_count,
                "watch_count": row.watch_count,
                "blocked_count": row.blocked_count,
                "top_adjusted_net_probability_edge": row.top_adjusted_net_probability_edge,
                "total_cost_per_share": row.total_cost_per_share,
                "readiness_status_counts": row.readiness_status_counts_json,
                "payload": row.payload_json,
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            },
        ),
    )

    loaded = store_module.load_paper_recommendation_readiness_reports(connection)

    assert loaded == (
        FakeReadinessReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            blocked_count=row.blocked_count,
        ),
    )


@pytest.mark.parametrize(
    "kwargs",
    (
        {"config_version": " paper-recommendation-readiness-v0"},
        {"min_blocked_count": -1},
        {"min_blocked_count": True},
        {"limit": 0},
        {"limit": True},
        {"table_name": "PaperReports"},
    ),
)
def test_load_rejects_invalid_filters_without_executing_sql(
    store_module: types.ModuleType,
    kwargs: dict[str, object],
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError):
        store_module.load_paper_recommendation_readiness_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_load_rejects_rows_with_wrong_column_count(store_module: types.ModuleType) -> None:
    connection = FakeConnection(rows=(("too-few",),))

    with pytest.raises(ValueError, match="selected readiness columns"):
        store_module.load_paper_recommendation_readiness_reports(connection)

    assert connection.cursor_instance.closed is True
