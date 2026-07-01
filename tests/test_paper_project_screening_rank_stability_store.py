from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    PaperProjectScreeningRankStabilityReport,
    PaperProjectScreeningRankStabilityRow,
)
from polymarket_alpha_lab.paper_project_screening_rank_stability_db_row import (
    PaperProjectScreeningRankStabilityDbRow,
    paper_project_screening_rank_stability_report_to_db_row,
)
import polymarket_alpha_lab.paper_project_screening_rank_stability_store as rank_stability_store
from polymarket_alpha_lab.paper_project_screening_rank_stability_store import (
    DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_REPORTS_TABLE,
    insert_paper_project_screening_rank_stability_report,
    load_paper_project_screening_rank_stability_reports,
)


GENERATED_AT = datetime(2026, 6, 22, 13, 30, tzinfo=UTC)
LATEST_GENERATED_AT = datetime(2026, 6, 22, 13, 25, tzinfo=UTC)
SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "stability_status",
    "reason_codes_json",
    "source_report_count",
    "candidate_count",
    "stable_count",
    "watch_count",
    "blocked_count",
    "stable_ready_count",
    "unstable_ready_count",
    "scoring_side_changed_count",
    "source_status_changed_count",
    "screening_status_changed_count",
    "research_bucket_changed_count",
    "latest_generated_at",
    "top_stable_market_slug",
    "rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


class FakeCursor:
    def __init__(
        self,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
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
        execute_error: Exception | None = None,
        fetchall_error: Exception | None = None,
        close_error: Exception | None = None,
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


def d(value: str) -> Decimal:
    return Decimal(value)


def _row() -> PaperProjectScreeningRankStabilityRow:
    return PaperProjectScreeningRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_research_bucket="research_ready",
        latest_screening_status="screening_ready",
        latest_source_status="paper_review_ready",
        latest_scoring_side="yes",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_screening_score=d("0.700000"),
        latest_screening_score=d("0.710000"),
        screening_score_delta=d("0.010000"),
        max_screening_score_delta=d("0.010000"),
        scoring_side_changed=False,
        source_status_changed=False,
        screening_status_changed=False,
        research_bucket_changed=False,
        reason_codes=("stable_research_ready",),
    )


def _report() -> PaperProjectScreeningRankStabilityReport:
    return PaperProjectScreeningRankStabilityReport(
        generated_at=GENERATED_AT,
        config_version="project-screening-rank-stability-v0",
        source_report_count=2,
        candidate_count=1,
        stability_status="stable",
        stable_count=1,
        watch_count=0,
        blocked_count=0,
        stable_ready_count=1,
        unstable_ready_count=0,
        scoring_side_changed_count=0,
        source_status_changed_count=0,
        screening_status_changed_count=0,
        research_bucket_changed_count=0,
        latest_generated_at=LATEST_GENERATED_AT,
        top_stable_market_slug="alpha",
        reason_codes=("stable_ready_candidates_present",),
        rows=(_row(),),
    )


def _db_row() -> PaperProjectScreeningRankStabilityDbRow:
    return paper_project_screening_rank_stability_report_to_db_row(_report())


def _row_values(row: PaperProjectScreeningRankStabilityDbRow) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def test_insert_project_rank_stability_report_uses_parameterized_insert() -> None:
    connection = FakeConnection()
    report = _report()
    expected_row = _db_row()

    inserted = insert_paper_project_screening_rank_stability_report(connection, report)

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_project_screening_rank_stability_reports (
            report_sha256,
            generated_at,
            config_version,
            stability_status,
            reason_codes_json,
            source_report_count,
            candidate_count,
            stable_count,
            watch_count,
            blocked_count,
            stable_ready_count,
            unstable_ready_count,
            scoring_side_changed_count,
            source_status_changed_count,
            screening_status_changed_count,
            research_bucket_changed_count,
            latest_generated_at,
            top_stable_market_slug,
            rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "paper_project_screening_rank_stability_reports (" in sql
    assert "project-screening-rank-stability-v0" not in sql


def test_insert_project_rank_stability_report_with_result_observes_duplicate_insert() -> None:
    assert hasattr(
        rank_stability_store,
        "insert_paper_project_screening_rank_stability_report_with_result",
    )
    report = _report()
    expected_row = _db_row()

    inserted = (
        rank_stability_store.insert_paper_project_screening_rank_stability_report_with_result(
            FakeConnection(rowcount=1),
            report,
        )
    )
    duplicate = (
        rank_stability_store.insert_paper_project_screening_rank_stability_report_with_result(
            FakeConnection(rowcount=0),
            report,
        )
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_load_project_rank_stability_reports_filters_by_config_status_and_limit() -> None:
    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_project_screening_rank_stability_reports(
        connection,
        config_version="project-screening-rank-stability-v0",
        stability_status="stable",
        limit=25,
        table_name="project_rank_stability_archive",
    )

    assert reports == (_report(),)
    assert connection.cursor_count == 1
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
            stability_status,
            reason_codes_json,
            source_report_count,
            candidate_count,
            stable_count,
            watch_count,
            blocked_count,
            stable_ready_count,
            unstable_ready_count,
            scoring_side_changed_count,
            source_status_changed_count,
            screening_status_changed_count,
            research_bucket_changed_count,
            latest_generated_at,
            top_stable_market_slug,
            rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM project_rank_stability_archive
        WHERE config_version = %s AND stability_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == ("project-screening-rank-stability-v0", "stable", 25)


def test_load_project_rank_stability_reports_accepts_positional_rows() -> None:
    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_paper_project_screening_rank_stability_reports(connection)

    assert reports == (_report(),)


def test_load_project_rank_stability_reports_accepts_dict_rows_without_mutation() -> None:
    row = _db_row()
    payload_before = deepcopy(row.payload_json)
    rows_before = deepcopy(row.rows_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_paper_project_screening_rank_stability_reports(connection)

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["rows_json"] == rows_before


def test_load_project_rank_stability_reports_accepts_namedtuple_like_rows() -> None:
    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_paper_project_screening_rank_stability_reports(connection)

    assert reports == (_report(),)


def test_load_project_rank_stability_reports_accepts_db_row_objects() -> None:
    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_project_screening_rank_stability_reports(connection)

    assert reports == (_report(),)


@pytest.mark.parametrize("operation", ("insert", "load"))
def test_cursor_close_error_after_success_is_propagated(operation: str) -> None:
    connection = FakeConnection(close_error=RuntimeError("cursor close failed"))

    with pytest.raises(RuntimeError, match="cursor close failed") as exc_info:
        if operation == "insert":
            insert_paper_project_screening_rank_stability_report(
                connection,
                _report(),
            )
        else:
            load_paper_project_screening_rank_stability_reports(connection)

    assert exc_info.value is connection.cursor_instance.close_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_operation_error_wins_when_cursor_close_also_fails(
    operation: str,
    operation_error_name: str,
) -> None:
    operation_error = RuntimeError("db operation failed")
    close_error = RuntimeError("cursor close failed")
    connection = FakeConnection(
        **{
            operation_error_name: operation_error,
            "close_error": close_error,
        },
    )

    with pytest.raises(RuntimeError, match="db operation failed") as exc_info:
        if operation == "insert":
            insert_paper_project_screening_rank_stability_report(
                connection,
                _report(),
            )
        else:
            load_paper_project_screening_rank_stability_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_base_exception_operation_error_still_closes_cursor(
    operation: str,
    operation_error_name: str,
) -> None:
    class NonExceptionOperationFailure(BaseException):
        pass

    operation_error = NonExceptionOperationFailure("operation interrupted")
    connection = FakeConnection(**{operation_error_name: operation_error})

    with pytest.raises(NonExceptionOperationFailure) as exc_info:
        if operation == "insert":
            insert_paper_project_screening_rank_stability_report(connection, _report())
        else:
            load_paper_project_screening_rank_stability_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_project_screening_rank_stability_reports; drop table users",
        "audit.paper_project_screening_rank_stability_reports",
        "PaperProjectScreeningRankStabilityReports",
        "_paper_project_screening_rank_stability_reports",
        "paper_project_screening_rank_stability_reports_",
        "a",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_project_screening_rank_stability_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_accepts_simple_lowercase_table_names() -> None:
    connection = FakeConnection()

    insert_paper_project_screening_rank_stability_report(
        connection,
        _report(),
        table_name="project_rank_stability_archive",
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert "INSERT INTO project_rank_stability_archive" in sql


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "project_rank_stability_archive",
        "rank_1_stability_2_archive",
    ],
)
def test_load_accepts_simple_lowercase_table_names(table_name: str) -> None:
    connection = FakeConnection()

    load_paper_project_screening_rank_stability_reports(connection, table_name=table_name)

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "public.audit.paper_project_screening_rank_stability_reports"}, "table_name"),
        ({"table_name": "audit.paper_project_screening_rank_stability_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "a"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " project-screening-rank-stability-v0"}, "config_version"),
        ({"stability_status": "pass"}, "stability_status"),
        ({"stability_status": True}, "stability_status"),
        ({"limit": 0}, "limit"),
        ({"limit": -1}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": "5"}, "limit"),
    ),
)
def test_load_rejects_invalid_query_inputs_before_cursor_creation(
    kwargs: dict[str, Any],
    message: str,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_paper_project_screening_rank_stability_reports(connection, **kwargs)

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    assert DEFAULT_PAPER_PROJECT_SCREENING_RANK_STABILITY_REPORTS_TABLE == (
        "paper_project_screening_rank_stability_reports"
    )
    assert "insert_paper_project_screening_rank_stability_report" in rank_stability_store.__all__
    assert "load_paper_project_screening_rank_stability_reports" in rank_stability_store.__all__
