from __future__ import annotations

import importlib
import sys
import types
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import pytest


@dataclass(frozen=True)
class FakeSnapshotReport:
    generated_at: datetime
    config_version: str
    final_status: str


@dataclass(frozen=True)
class FakeSnapshotDbRow:
    snapshot_sha256: str
    generated_at: datetime
    config_version: str
    final_status: str
    stage_count: int
    artifact_count: int
    blocked_artifact_count: int
    watch_artifact_count: int
    reason_codes: tuple[str, ...]
    stage_counts_json: dict[str, int]
    artifact_counts_json: dict[str, int]
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

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_row",
    )

    def to_db_row(report: FakeSnapshotReport) -> FakeSnapshotDbRow:
        return FakeSnapshotDbRow(
            snapshot_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            final_status=report.final_status,
            stage_count=3,
            artifact_count=5,
            blocked_artifact_count=1,
            watch_artifact_count=2,
            reason_codes=("pipeline_final_status_watch",),
            stage_counts_json={
                "stage_count": 3,
                "pass_count": 1,
                "watch_count": 1,
                "blocked_count": 1,
            },
            artifact_counts_json={
                "artifact_count": 5,
                "pass_count": 2,
                "watch_count": 2,
                "blocked_count": 1,
            },
            payload_json={
                "generated_at": report.generated_at.isoformat(),
                "config_version": report.config_version,
                "final_status": report.final_status,
            },
        )

    def from_db_row(row: FakeSnapshotDbRow) -> FakeSnapshotReport:
        return FakeSnapshotReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            final_status=row.final_status,
        )

    companion.PaperRecommendationCycleSnapshotDbRow = FakeSnapshotDbRow
    companion.paper_recommendation_cycle_snapshot_to_db_row = to_db_row
    companion.paper_recommendation_cycle_snapshot_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_store",
    )


def test_insert_paper_recommendation_cycle_snapshot_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeSnapshotReport(
        generated_at=datetime(2026, 6, 19, 12, 30, tzinfo=UTC),
        config_version="paper-recommendation-cycle-snapshot-v0",
        final_status="watch",
    )

    inserted = store_module.insert_paper_recommendation_cycle_snapshot(
        connection,
        report,
    )

    assert inserted == FakeSnapshotDbRow(
        snapshot_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        final_status=report.final_status,
        stage_count=3,
        artifact_count=5,
        blocked_artifact_count=1,
        watch_artifact_count=2,
        reason_codes=("pipeline_final_status_watch",),
        stage_counts_json={
            "stage_count": 3,
            "pass_count": 1,
            "watch_count": 1,
            "blocked_count": 1,
        },
        artifact_counts_json={
            "artifact_count": 5,
            "pass_count": 2,
            "watch_count": 2,
            "blocked_count": 1,
        },
        payload_json={
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "final_status": report.final_status,
        },
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_recommendation_cycle_snapshots (
            snapshot_sha256,
            generated_at,
            config_version,
            final_status,
            stage_counts,
            artifact_counts,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (snapshot_sha256) DO NOTHING
        """,
    )
    assert params == (
        "a" * 64,
        report.generated_at,
        report.config_version,
        "watch",
        {"stage_count": 3, "pass_count": 1, "watch_count": 1, "blocked_count": 1},
        {"artifact_count": 5, "pass_count": 2, "watch_count": 2, "blocked_count": 1},
        ["pipeline_final_status_watch"],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": report.config_version,
            "final_status": report.final_status,
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
        store_module.insert_paper_recommendation_cycle_snapshot(
            connection,
            FakeSnapshotReport(
                generated_at=datetime(2026, 6, 19, 12, 30, tzinfo=UTC),
                config_version="paper-recommendation-cycle-snapshot-v0",
                final_status="pass",
            ),
            table_name="paper_recommendation_cycle_snapshots; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_preserves_execute_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    execute_error = RuntimeError("execute failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        execute_error=execute_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_paper_recommendation_cycle_snapshot(
            connection,
            FakeSnapshotReport(
                generated_at=datetime(2026, 6, 19, 12, 30, tzinfo=UTC),
                config_version="paper-recommendation-cycle-snapshot-v0",
                final_status="pass",
            ),
        )

    assert exc_info.value is execute_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_insert_propagates_cursor_close_error_after_successful_execute(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as exc_info:
        store_module.insert_paper_recommendation_cycle_snapshot(
            connection,
            FakeSnapshotReport(
                generated_at=datetime(2026, 6, 19, 12, 30, tzinfo=UTC),
                config_version="paper-recommendation-cycle-snapshot-v0",
                final_status="pass",
            ),
        )

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


def test_load_paper_recommendation_cycle_snapshots_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = FakeSnapshotDbRow(
        snapshot_sha256="b" * 64,
        generated_at=datetime(2026, 6, 19, 14, 0, tzinfo=UTC),
        config_version="paper-recommendation-cycle-snapshot-v0",
        final_status="blocked",
        stage_count=4,
        artifact_count=7,
        blocked_artifact_count=2,
        watch_artifact_count=1,
        reason_codes=("artifact_index_blocked",),
        stage_counts_json={
            "stage_count": 4,
            "pass_count": 1,
            "watch_count": 1,
            "blocked_count": 2,
        },
        artifact_counts_json={
            "artifact_count": 7,
            "pass_count": 4,
            "watch_count": 1,
            "blocked_count": 2,
        },
        payload_json={
            "generated_at": "2026-06-19T14:00:00+00:00",
            "config_version": "paper-recommendation-cycle-snapshot-v0",
            "final_status": "blocked",
        },
    )
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_recommendation_cycle_snapshots(
        connection,
        config_version="paper-recommendation-cycle-snapshot-v0",
        limit=25,
        table_name="cycle_snapshot_archive",
    )

    assert reports == (
        FakeSnapshotReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            final_status=row.final_status,
        ),
    )
    assert connection.commit_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        SELECT
            snapshot_sha256,
            generated_at,
            config_version,
            final_status,
            stage_counts,
            artifact_counts,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        FROM cycle_snapshot_archive
        WHERE config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, snapshot_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("paper-recommendation-cycle-snapshot-v0", 25)


def test_load_propagates_cursor_close_error_after_successful_query(
    store_module: types.ModuleType,
) -> None:
    close_error = RuntimeError("close failed")
    connection = FakeConnection(close_error=close_error)

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_paper_recommendation_cycle_snapshots(connection)

    assert exc_info.value is close_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.calls


def test_load_preserves_fetchall_error_when_cursor_close_also_fails(
    store_module: types.ModuleType,
) -> None:
    fetchall_error = RuntimeError("fetchall failed")
    close_error = RuntimeError("close failed")
    connection = FakeConnection(
        fetchall_error=fetchall_error,
        close_error=close_error,
    )

    with pytest.raises(RuntimeError) as exc_info:
        store_module.load_paper_recommendation_cycle_snapshots(connection)

    assert exc_info.value is fetchall_error
    assert connection.cursor_instance.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_paper_recommendation_cycle_snapshots_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 19, 14, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-recommendation-cycle-snapshot-v0",
                "pass",
                {"stage_count": 2, "pass_count": 2, "watch_count": 0, "blocked_count": 0},
                {"artifact_count": 6, "pass_count": 6, "watch_count": 0, "blocked_count": 0},
                ("all_clear",),
                {
                    "generated_at": "2026-06-19T14:00:00+00:00",
                    "config_version": "paper-recommendation-cycle-snapshot-v0",
                    "final_status": "pass",
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_recommendation_cycle_snapshots(connection)

    assert reports == (
        FakeSnapshotReport(
            generated_at=generated_at,
            config_version="paper-recommendation-cycle-snapshot-v0",
            final_status="pass",
        ),
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_recommendation_cycle_snapshots"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
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
        store_module.load_paper_recommendation_cycle_snapshots(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
