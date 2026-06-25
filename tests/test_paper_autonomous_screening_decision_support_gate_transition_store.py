from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
from typing import Any

import pytest

from tests.test_paper_autonomous_screening_decision_support_gate_transition_db_row import (
    _report,
)


SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_report_count",
    "transition_count",
    "first_report_generated_at",
    "latest_report_generated_at",
    "latest_from_gate_status",
    "latest_to_gate_status",
    "latest_introduced_reason_codes_json",
    "latest_cleared_reason_codes_json",
    "latest_persistent_reason_codes_json",
    "status_transition_rows_json",
    "reason_change_rows_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)


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


def _db_row():
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_db_row import (
        paper_autonomous_screening_decision_support_gate_transition_report_to_db_row,
    )

    return paper_autonomous_screening_decision_support_gate_transition_report_to_db_row(
        _report(),
    )


def _row_values(row: object) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def test_insert_transition_report_uses_parameterized_insert() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        insert_paper_autonomous_screening_decision_support_gate_transition_report,
    )

    connection = FakeConnection()
    report = _report()
    expected_row = _db_row()

    inserted = (
        insert_paper_autonomous_screening_decision_support_gate_transition_report(
            connection,
            report,
        )
    )

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        """
        INSERT INTO paper_autonomous_screening_gate_transition_reports (
            report_sha256,
            generated_at,
            config_version,
            gate_report_count,
            transition_count,
            first_report_generated_at,
            latest_report_generated_at,
            latest_from_gate_status,
            latest_to_gate_status,
            latest_introduced_reason_codes_json,
            latest_cleared_reason_codes_json,
            latest_persistent_reason_codes_json,
            status_transition_rows_json,
            reason_change_rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "paper-autonomous-screening-decision-support-gate-transition-v0" not in sql


def test_insert_transition_report_with_result_observes_duplicate() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store as store

    report = _report()
    expected_row = _db_row()

    inserted = (
        store.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_result(
            FakeConnection(rowcount=1),
            report,
        )
    )
    duplicate = (
        store.insert_paper_autonomous_screening_decision_support_gate_transition_report_with_result(
            FakeConnection(rowcount=0),
            report,
        )
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_load_transition_reports_filters_by_config_statuses_and_limit() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        load_paper_autonomous_screening_decision_support_gate_transition_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_screening_decision_support_gate_transition_reports(
        connection,
        config_version="paper-autonomous-screening-decision-support-gate-transition-v0",
        latest_from_gate_status="pass",
        latest_to_gate_status="watch",
        limit=25,
        table_name="autonomous_screening_gate_transition_archive",
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
            gate_report_count,
            transition_count,
            first_report_generated_at,
            latest_report_generated_at,
            latest_from_gate_status,
            latest_to_gate_status,
            latest_introduced_reason_codes_json,
            latest_cleared_reason_codes_json,
            latest_persistent_reason_codes_json,
            status_transition_rows_json,
            reason_change_rows_json,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM autonomous_screening_gate_transition_archive
        WHERE config_version = %s AND latest_from_gate_status = %s AND latest_to_gate_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-autonomous-screening-decision-support-gate-transition-v0",
        "pass",
        "watch",
        25,
    )


def test_load_transition_reports_accepts_positional_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        load_paper_autonomous_screening_decision_support_gate_transition_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_paper_autonomous_screening_decision_support_gate_transition_reports(
        connection,
    )

    assert reports == (_report(),)


def test_load_transition_reports_accepts_dict_rows_without_mutation() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        load_paper_autonomous_screening_decision_support_gate_transition_reports,
    )

    row = _db_row()
    payload_before = deepcopy(row.payload_json)
    status_rows_before = deepcopy(row.status_transition_rows_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_paper_autonomous_screening_decision_support_gate_transition_reports(
        connection,
    )

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["status_transition_rows_json"] == status_rows_before


def test_load_transition_reports_accepts_namedtuple_like_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        load_paper_autonomous_screening_decision_support_gate_transition_reports,
    )

    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_paper_autonomous_screening_decision_support_gate_transition_reports(
        connection,
    )

    assert reports == (_report(),)


def test_load_transition_reports_accepts_db_row_objects() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        load_paper_autonomous_screening_decision_support_gate_transition_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_screening_decision_support_gate_transition_reports(
        connection,
    )

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_autonomous_screening_gate_transition_reports; drop table users",
        "audit.paper_autonomous_screening_gate_transition_reports",
        "PaperAutonomousScreeningGateTransitionReports",
        "_paper_autonomous_screening_gate_transition_reports",
        "paper_autonomous_screening_gate_transition_reports_",
        "a",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        insert_paper_autonomous_screening_decision_support_gate_transition_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_screening_decision_support_gate_transition_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "autonomous_screening_gate_transition_archive",
        "gate_transition_1_archive_2",
    ],
)
def test_load_accepts_simple_lowercase_table_names(table_name: str) -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        load_paper_autonomous_screening_decision_support_gate_transition_reports,
    )

    connection = FakeConnection()

    load_paper_autonomous_screening_decision_support_gate_transition_reports(
        connection,
        table_name=table_name,
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit.autonomous_screening_gate_transition_archive"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "a"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " transition-v0"}, "config_version"),
        ({"latest_from_gate_status": "paused"}, "latest_from_gate_status"),
        ({"latest_to_gate_status": "paused"}, "latest_to_gate_status"),
        ({"latest_to_gate_status": True}, "latest_to_gate_status"),
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
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store import (
        load_paper_autonomous_screening_decision_support_gate_transition_reports,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_screening_decision_support_gate_transition_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_store as store

    assert (
        store.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TRANSITION_REPORTS_TABLE
        == "paper_autonomous_screening_gate_transition_reports"
    )
    assert (
        "insert_paper_autonomous_screening_decision_support_gate_transition_report"
        in store.__all__
    )
    assert (
        "load_paper_autonomous_screening_decision_support_gate_transition_reports"
        in store.__all__
    )
