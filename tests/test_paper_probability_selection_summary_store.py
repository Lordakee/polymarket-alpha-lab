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
class FakeSelectionSummaryReport:
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    source_cost_stress_config_version: str
    queue_count: int


@dataclass(frozen=True)
class FakeSelectionSummaryDbRow:
    report_sha256: str
    generated_at: datetime
    config_version: str
    source_queue_config_version: str
    source_cost_stress_config_version: str
    queue_count: int
    ready_count: int
    watch_count: int
    blocked_count: int
    missing_stress_count: int
    rows_json: list[dict[str, Any]]
    reason_codes_json: list[str]
    payload_json: dict[str, Any]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


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


def fake_db_row(
    *,
    report_sha256: str = "b" * 64,
    generated_at: datetime = datetime(2026, 6, 21, 15, 0, tzinfo=UTC),
    config_version: str = "paper-probability-selection-summary-v0",
    source_queue_config_version: str = "probability-recommendation-queue-v0",
    source_cost_stress_config_version: str = "paper-cost-stress-v0",
    queue_count: int = 2,
) -> FakeSelectionSummaryDbRow:
    return FakeSelectionSummaryDbRow(
        report_sha256=report_sha256,
        generated_at=generated_at,
        config_version=config_version,
        source_queue_config_version=source_queue_config_version,
        source_cost_stress_config_version=source_cost_stress_config_version,
        queue_count=queue_count,
        ready_count=1,
        watch_count=1,
        blocked_count=0,
        missing_stress_count=0,
        rows_json=[
            {
                "queue_rank": 1,
                "market_slug": "event-alpha",
                "selection_status": "ready",
            },
        ],
        reason_codes_json=["watch_selection_rows_present"],
        payload_json={
            "generated_at": generated_at.isoformat(),
            "config_version": config_version,
            "source_queue_config_version": source_queue_config_version,
            "source_cost_stress_config_version": source_cost_stress_config_version,
            "queue_count": queue_count,
        },
    )


def fake_report() -> FakeSelectionSummaryReport:
    return FakeSelectionSummaryReport(
        generated_at=datetime(2026, 6, 21, 15, 0, tzinfo=UTC),
        config_version="paper-probability-selection-summary-v0",
        source_queue_config_version="probability-recommendation-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        queue_count=2,
    )


@pytest.fixture()
def store_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    companion = types.ModuleType(
        "polymarket_alpha_lab.paper_probability_selection_summary_db_row",
    )

    def to_db_row(report: FakeSelectionSummaryReport) -> FakeSelectionSummaryDbRow:
        return fake_db_row(
            report_sha256="a" * 64,
            generated_at=report.generated_at,
            config_version=report.config_version,
            source_queue_config_version=report.source_queue_config_version,
            source_cost_stress_config_version=report.source_cost_stress_config_version,
            queue_count=report.queue_count,
        )

    def from_db_row(row: FakeSelectionSummaryDbRow) -> FakeSelectionSummaryReport:
        return FakeSelectionSummaryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_queue_config_version=row.source_queue_config_version,
            source_cost_stress_config_version=row.source_cost_stress_config_version,
            queue_count=row.queue_count,
        )

    companion.PaperProbabilitySelectionSummaryDbRow = FakeSelectionSummaryDbRow
    companion.paper_probability_selection_summary_report_to_db_row = to_db_row
    companion.paper_probability_selection_summary_report_from_db_row = from_db_row
    monkeypatch.setitem(
        sys.modules,
        "polymarket_alpha_lab.paper_probability_selection_summary_db_row",
        companion,
    )
    sys.modules.pop(
        "polymarket_alpha_lab.paper_probability_selection_summary_store",
        None,
    )
    return importlib.import_module(
        "polymarket_alpha_lab.paper_probability_selection_summary_store",
    )


def test_insert_selection_summary_report_uses_parameterized_insert(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()
    report = FakeSelectionSummaryReport(
        generated_at=datetime(2026, 6, 21, 15, 0, tzinfo=UTC),
        config_version="paper-probability-selection-summary-v0",
        source_queue_config_version="probability-recommendation-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        queue_count=2,
    )

    inserted = store_module.insert_paper_probability_selection_summary_report(
        connection,
        report,
    )

    assert inserted == fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_queue_config_version=report.source_queue_config_version,
        source_cost_stress_config_version=report.source_cost_stress_config_version,
        queue_count=2,
    )
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_probability_selection_summary_reports (
            report_sha256,
            generated_at,
            config_version,
            source_queue_config_version,
            source_cost_stress_config_version,
            queue_count,
            ready_count,
            watch_count,
            blocked_count,
            missing_stress_count,
            rows,
            reason_codes,
            payload,
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
        "paper-probability-selection-summary-v0",
        "probability-recommendation-queue-v0",
        "paper-cost-stress-v0",
        2,
        1,
        1,
        0,
        0,
        [
            {
                "queue_rank": 1,
                "market_slug": "event-alpha",
                "selection_status": "ready",
            },
        ],
        ["watch_selection_rows_present"],
        {
            "generated_at": report.generated_at.isoformat(),
            "config_version": "paper-probability-selection-summary-v0",
            "source_queue_config_version": "probability-recommendation-queue-v0",
            "source_cost_stress_config_version": "paper-cost-stress-v0",
            "queue_count": 2,
        },
        True,
        True,
        True,
    )


def test_insert_selection_summary_report_with_result_observes_duplicate_insert(
    store_module: types.ModuleType,
) -> None:
    assert hasattr(
        store_module,
        "insert_paper_probability_selection_summary_report_with_result",
    )
    report = FakeSelectionSummaryReport(
        generated_at=datetime(2026, 6, 21, 15, 0, tzinfo=UTC),
        config_version="paper-probability-selection-summary-v0",
        source_queue_config_version="probability-recommendation-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        queue_count=2,
    )
    expected_row = fake_db_row(
        report_sha256="a" * 64,
        generated_at=report.generated_at,
        config_version=report.config_version,
        source_queue_config_version=report.source_queue_config_version,
        source_cost_stress_config_version=report.source_cost_stress_config_version,
        queue_count=2,
    )

    inserted = store_module.insert_paper_probability_selection_summary_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store_module.insert_paper_probability_selection_summary_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_selection_summary_report_rejects_unexpected_rowcount(
    store_module: types.ModuleType,
) -> None:
    with pytest.raises(ValueError, match="rowcount"):
        store_module.insert_paper_probability_selection_summary_report_with_result(
            FakeConnection(rowcount=2),
            FakeSelectionSummaryReport(
                generated_at=datetime(2026, 6, 21, 15, 0, tzinfo=UTC),
                config_version="paper-probability-selection-summary-v0",
                source_queue_config_version="probability-recommendation-queue-v0",
                source_cost_stress_config_version="paper-cost-stress-v0",
                queue_count=2,
            ),
        )


def test_insert_rejects_unsafe_table_name_without_executing_sql(
    store_module: types.ModuleType,
) -> None:
    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        store_module.insert_paper_probability_selection_summary_report(
            connection,
            FakeSelectionSummaryReport(
                generated_at=datetime(2026, 6, 21, 15, 0, tzinfo=UTC),
                config_version="paper-probability-selection-summary-v0",
                source_queue_config_version="probability-recommendation-queue-v0",
                source_cost_stress_config_version="paper-cost-stress-v0",
                queue_count=2,
            ),
            table_name="paper_probability_selection_summary_reports; drop table users",
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_selection_summary_reports_filters_and_limits_with_params(
    store_module: types.ModuleType,
) -> None:
    row = fake_db_row(queue_count=3)
    connection = FakeConnection(rows=(row,))

    reports = store_module.load_paper_probability_selection_summary_reports(
        connection,
        config_version="paper-probability-selection-summary-v0",
        source_queue_config_version="probability-recommendation-queue-v0",
        source_cost_stress_config_version="paper-cost-stress-v0",
        selection_status="watch",
        limit=25,
        table_name="selection_summary_archive",
    )

    assert reports == (
        FakeSelectionSummaryReport(
            generated_at=row.generated_at,
            config_version=row.config_version,
            source_queue_config_version=row.source_queue_config_version,
            source_cost_stress_config_version=row.source_cost_stress_config_version,
            queue_count=3,
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
            source_queue_config_version,
            source_cost_stress_config_version,
            queue_count,
            ready_count,
            watch_count,
            blocked_count,
            missing_stress_count,
            rows,
            reason_codes,
            payload,
            paper_only,
            report_only,
            readonly
        FROM selection_summary_archive
        WHERE config_version = %s
            AND source_queue_config_version = %s
            AND source_cost_stress_config_version = %s
            AND watch_count > 0
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-probability-selection-summary-v0",
        "probability-recommendation-queue-v0",
        "paper-cost-stress-v0",
        25,
    )


def test_load_selection_summary_reports_accepts_positional_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 16, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            (
                "c" * 64,
                generated_at,
                "paper-probability-selection-summary-v0",
                "probability-recommendation-queue-v0",
                "paper-cost-stress-v0",
                2,
                1,
                1,
                0,
                0,
                [{"queue_rank": 1}],
                ["watch_selection_rows_present"],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-probability-selection-summary-v0",
                    "queue_count": 2,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_probability_selection_summary_reports(connection)

    assert reports == (
        FakeSelectionSummaryReport(
            generated_at=generated_at,
            config_version="paper-probability-selection-summary-v0",
            source_queue_config_version="probability-recommendation-queue-v0",
            source_cost_stress_config_version="paper-cost-stress-v0",
            queue_count=2,
        ),
    )


def test_load_selection_summary_reports_accepts_dict_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 17, 0, tzinfo=UTC)
    connection = FakeConnection(
        rows=(
            {
                "report_sha256": "d" * 64,
                "generated_at": generated_at,
                "config_version": "paper-probability-selection-summary-v0",
                "source_queue_config_version": "probability-recommendation-queue-v0",
                "source_cost_stress_config_version": "paper-cost-stress-v0",
                "queue_count": 4,
                "ready_count": 2,
                "watch_count": 1,
                "blocked_count": 1,
                "missing_stress_count": 1,
                "rows": [{"queue_rank": 1}],
                "reason_codes": ["blocked_selection_rows_present"],
                "payload": {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-probability-selection-summary-v0",
                    "queue_count": 4,
                },
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        ),
    )

    reports = store_module.load_paper_probability_selection_summary_reports(connection)

    assert reports == (
        FakeSelectionSummaryReport(
            generated_at=generated_at,
            config_version="paper-probability-selection-summary-v0",
            source_queue_config_version="probability-recommendation-queue-v0",
            source_cost_stress_config_version="paper-cost-stress-v0",
            queue_count=4,
        ),
    )


def test_load_selection_summary_reports_accepts_namedtuple_rows(
    store_module: types.ModuleType,
) -> None:
    generated_at = datetime(2026, 6, 21, 18, 0, tzinfo=UTC)
    record_type = namedtuple(
        "SelectionSummaryRecord",
        (
            "report_sha256",
            "generated_at",
            "config_version",
            "source_queue_config_version",
            "source_cost_stress_config_version",
            "queue_count",
            "ready_count",
            "watch_count",
            "blocked_count",
            "missing_stress_count",
            "rows",
            "reason_codes",
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
                "paper-probability-selection-summary-v0",
                "probability-recommendation-queue-v0",
                "paper-cost-stress-v0",
                5,
                3,
                1,
                1,
                0,
                [{"queue_rank": 1}],
                ["watch_selection_rows_present"],
                {
                    "generated_at": generated_at.isoformat(),
                    "config_version": "paper-probability-selection-summary-v0",
                    "queue_count": 5,
                },
                True,
                True,
                True,
            ),
        ),
    )

    reports = store_module.load_paper_probability_selection_summary_reports(connection)

    assert reports == (
        FakeSelectionSummaryReport(
            generated_at=generated_at,
            config_version="paper-probability-selection-summary-v0",
            source_queue_config_version="probability-recommendation-queue-v0",
            source_cost_stress_config_version="paper-cost-stress-v0",
            queue_count=5,
        ),
    )


@pytest.mark.parametrize("operation", ("insert", "load"))
def test_cursor_close_error_after_success_is_propagated(
    store_module: types.ModuleType,
    operation: str,
) -> None:
    connection = FakeConnection(close_error=RuntimeError("cursor close failed"))

    with pytest.raises(RuntimeError, match="cursor close failed") as exc_info:
        if operation == "insert":
            store_module.insert_paper_probability_selection_summary_report(
                connection,
                fake_report(),
            )
        else:
            store_module.load_paper_probability_selection_summary_reports(connection)

    assert exc_info.value is connection.cursor_instance.close_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_operation_error_wins_when_cursor_close_also_fails(
    store_module: types.ModuleType,
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
            store_module.insert_paper_probability_selection_summary_report(
                connection,
                fake_report(),
            )
        else:
            store_module.load_paper_probability_selection_summary_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("operation", "operation_error_name"),
    (("insert", "execute_error"), ("load", "fetchall_error")),
)
def test_base_exception_operation_error_still_closes_cursor(
    store_module: types.ModuleType,
    operation: str,
    operation_error_name: str,
) -> None:
    class NonExceptionOperationFailure(BaseException):
        pass

    operation_error = NonExceptionOperationFailure("operation interrupted")
    connection = FakeConnection(**{operation_error_name: operation_error})

    with pytest.raises(NonExceptionOperationFailure) as exc_info:
        if operation == "insert":
            store_module.insert_paper_probability_selection_summary_report(
                connection,
                fake_report(),
            )
        else:
            store_module.load_paper_probability_selection_summary_reports(connection)

    assert exc_info.value is operation_error
    assert connection.cursor_instance.closed is True


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "schema.paper_probability_selection_summary_reports"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " paper-v0"}, "config_version"),
        ({"source_queue_config_version": ""}, "source_queue_config_version"),
        ({"source_cost_stress_config_version": " cost-v0"}, "source_cost_stress_config_version"),
        ({"selection_status": "stable"}, "selection_status"),
        ({"selection_status": True}, "selection_status"),
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
        store_module.load_paper_probability_selection_summary_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_public_exports_include_default_table_insert_result_and_store_functions(
    store_module: types.ModuleType,
) -> None:
    assert store_module.DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_REPORTS_TABLE == (
        "paper_probability_selection_summary_reports"
    )
    assert "DEFAULT_PAPER_PROBABILITY_SELECTION_SUMMARY_REPORTS_TABLE" in store_module.__all__
    assert "PaperProbabilitySelectionSummaryInsertResult" in store_module.__all__
    assert "insert_paper_probability_selection_summary_report" in store_module.__all__
    assert (
        "insert_paper_probability_selection_summary_report_with_result"
        in store_module.__all__
    )
    assert "load_paper_probability_selection_summary_reports" in store_module.__all__
