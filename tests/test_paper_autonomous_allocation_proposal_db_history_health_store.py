from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from typing import Any

import pytest

from tests.test_paper_autonomous_allocation_proposal_db_history_health_db_row import (
    _report,
)


SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "health_status",
    "recommended_next_step",
    "history_report_count",
    "pass_report_count",
    "watch_report_count",
    "blocked_report_count",
    "latest_history_status",
    "latest_proposal_status",
    "latest_allocated_count",
    "latest_total_allocated_paper_notional",
    "max_source_age_seconds",
    "latest_source_age_seconds",
    "duplicate_latest_report_generated_at_count",
    "reason_code_counts_json",
    "reason_codes_json",
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
        *,
        execute_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.execute_error = execute_error
        self.close_error = close_error
        self.calls: list[tuple[str, tuple[Any, ...]]] = []
        self.closed = False

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.calls.append((sql, params))
        if self.execute_error is not None:
            raise self.execute_error

    def fetchall(self) -> tuple[Any, ...]:
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
        execute_error: Exception | None = None,
        close_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows,
            rowcount,
            execute_error=execute_error,
            close_error=close_error,
        )
        self.cursor_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def cursor(self) -> FakeCursor:
        self.cursor_count += 1
        return self.cursor_instance

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


def normalize_sql(value: str) -> str:
    return " ".join(value.split())


def _db_row():
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_db_row import (
        to_db_row,
    )

    return to_db_row(_report())


def _row_values(row: object) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def _columns_sql() -> str:
    return ",\n            ".join(SELECT_COLUMNS)


def _placeholders_sql() -> str:
    return ", ".join("%s" for _ in SELECT_COLUMNS)


def test_insert_health_report_uses_parameterized_insert() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        insert_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    connection = FakeConnection()
    report = _report()
    expected_row = _db_row()

    inserted = insert_paper_autonomous_allocation_proposal_db_history_health_report(
        connection,
        report,
    )

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        f"""
        INSERT INTO paper_autonomous_allocation_proposal_db_history_health_reports (
            {_columns_sql()}
        ) VALUES ({_placeholders_sql()})
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "paper_autonomous_allocation_proposal_db_history_health_reports (" in sql
    assert "paper-autonomous-allocation-proposal-db-history-health-v0" not in sql


def test_insert_health_report_with_result_observes_duplicate() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store as store

    report = _report()
    expected_row = _db_row()

    inserted = (
        store.insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result(
            FakeConnection(rowcount=1),
            report,
        )
    )
    duplicate = (
        store.insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result(
            FakeConnection(rowcount=0),
            report,
        )
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_rejects_unexpected_rowcount() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result,
    )

    with pytest.raises(ValueError, match="rowcount"):
        insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result(
            FakeConnection(rowcount=2),
            _report(),
        )


def test_insert_closes_cursor_when_execute_fails_without_managing_transaction() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        insert_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    connection = FakeConnection(execute_error=RuntimeError("boom"))

    with pytest.raises(RuntimeError, match="boom"):
        insert_paper_autonomous_allocation_proposal_db_history_health_report(
            connection,
            _report(),
        )

    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True


def test_insert_ignores_cursor_close_errors() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        insert_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    connection = FakeConnection(close_error=RuntimeError("close failed"))

    row = insert_paper_autonomous_allocation_proposal_db_history_health_report(
        connection,
        _report(),
    )

    assert row == _db_row()
    assert connection.cursor_instance.closed is True


def test_load_health_reports_filters_newest_first_and_excludes_inserted_at() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        load_paper_autonomous_allocation_proposal_db_history_health_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_allocation_proposal_db_history_health_reports(
        connection,
        config_version="paper-autonomous-allocation-proposal-db-history-health-v0",
        health_status="pass",
        latest_history_status="pass",
        limit=25,
        table_name="health_archive",
    )

    assert reports == (_report(),)
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        f"""
        SELECT
            {_columns_sql()}
        FROM health_archive
        WHERE config_version = %s AND health_status = %s AND latest_history_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert "inserted_at" not in _columns_sql()
    assert params == (
        "paper-autonomous-allocation-proposal-db-history-health-v0",
        "pass",
        "pass",
        25,
    )


def test_load_health_reports_accepts_positional_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        load_paper_autonomous_allocation_proposal_db_history_health_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_paper_autonomous_allocation_proposal_db_history_health_reports(
        connection,
    )

    assert reports == (_report(),)


def test_load_health_reports_accepts_dict_rows_without_mutation() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        load_paper_autonomous_allocation_proposal_db_history_health_reports,
    )

    row = _db_row()
    payload_before = deepcopy(row.payload_json)
    counts_before = deepcopy(row.reason_code_counts_json)
    codes_before = deepcopy(row.reason_codes_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_paper_autonomous_allocation_proposal_db_history_health_reports(
        connection,
    )

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["reason_code_counts_json"] == counts_before
    assert record["reason_codes_json"] == codes_before


def test_load_health_reports_accepts_namedtuple_like_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        load_paper_autonomous_allocation_proposal_db_history_health_reports,
    )

    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_paper_autonomous_allocation_proposal_db_history_health_reports(
        connection,
    )

    assert reports == (_report(),)


def test_load_health_reports_accepts_db_row_objects() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        load_paper_autonomous_allocation_proposal_db_history_health_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_allocation_proposal_db_history_health_reports(
        connection,
    )

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_autonomous_allocation_proposal_db_history_health_reports; drop table x",
        "audit..paper_autonomous_allocation_proposal_db_history_health_reports",
        "audit.paper.autonomous_allocation_proposal_db_history_health_reports",
        "PaperAutonomousAllocationProposalDbHistoryHealthReports",
        "_paper_autonomous_allocation_proposal_db_history_health_reports",
        "paper_autonomous_allocation_proposal_db_history_health_reports_",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        insert_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_allocation_proposal_db_history_health_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    "table_name",
    (
        "a",
        "a0",
        "health_archive",
        "audit.health_archive",
        "health_1_archive_2",
    ),
)
def test_insert_accepts_lowercase_table_names(table_name: str) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        insert_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    connection = FakeConnection()

    insert_paper_autonomous_allocation_proposal_db_history_health_report(
        connection,
        _report(),
        table_name=table_name,
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"INSERT INTO {table_name}" in sql


def test_insert_rejects_postgres_identifier_over_length_limit() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        insert_paper_autonomous_allocation_proposal_db_history_health_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_allocation_proposal_db_history_health_report(
            connection,
            _report(),
            table_name="a" * 64,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit..health_archive"}, "table_name"),
        ({"table_name": "audit.health.archive"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " health-v0"}, "config_version"),
        ({"health_status": "paused"}, "health_status"),
        ({"health_status": True}, "health_status"),
        ({"latest_history_status": "paused"}, "latest_history_status"),
        ({"latest_history_status": True}, "latest_history_status"),
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
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store import (
        load_paper_autonomous_allocation_proposal_db_history_health_reports,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_allocation_proposal_db_history_health_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_health_store as store

    assert (
        store.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_DB_HISTORY_HEALTH_REPORTS_TABLE
        == "paper_autonomous_allocation_proposal_db_history_health_reports"
    )
    assert (
        "insert_paper_autonomous_allocation_proposal_db_history_health_report"
        in store.__all__
    )
    assert (
        "insert_paper_autonomous_allocation_proposal_db_history_health_report_with_result"
        in store.__all__
    )
    assert (
        "load_paper_autonomous_allocation_proposal_db_history_health_reports"
        in store.__all__
    )
