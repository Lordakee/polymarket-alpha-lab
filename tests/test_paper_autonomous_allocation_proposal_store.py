from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
import sys
from typing import Any

import pytest

from tests.test_paper_autonomous_allocation_proposal_db_row import (
    REDUCER_MODULE_NAME,
    _install_fake_reducer_module,
    _report,
)


SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "proposal_status",
    "recommended_next_step",
    "reason_codes_json",
    "reason_code_counts_json",
    "screening_gate_generated_at",
    "screening_gate_config_version",
    "screening_gate_status",
    "screening_gate_recommended_next_step",
    "queue_risk_generated_at",
    "queue_risk_config_version",
    "queue_risk_status",
    "queue_risk_recommended_next_step",
    "source_queue_report_count",
    "source_queue_ready_count",
    "source_queue_watch_count",
    "source_queue_blocked_count",
    "allocation_config_version",
    "allocation_generated_at",
    "allocation_input_count",
    "allocation_row_count",
    "allocation_allocated_count",
    "allocation_capped_count",
    "allocation_no_budget_count",
    "allocation_non_recommend_count",
    "allocation_skipped_count",
    "allocation_total_requested_paper_notional",
    "allocation_total_allocated_paper_notional",
    "allocation_remaining_paper_budget",
    "allocation_total_paper_budget",
    "allocation_max_paper_notional_per_market",
    "allocation_max_paper_notional_per_event",
    "allocation_max_paper_notional_per_theme",
    "allocation_max_paper_notional_per_correlation_group",
    "allocation_rows_json",
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


@pytest.fixture(autouse=True)
def fake_reducer_module():
    previous = sys.modules.get(REDUCER_MODULE_NAME)
    _install_fake_reducer_module()
    try:
        yield
    finally:
        if previous is None:
            sys.modules.pop(REDUCER_MODULE_NAME, None)
        else:
            sys.modules[REDUCER_MODULE_NAME] = previous


def _db_row():
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_row import (
        paper_autonomous_allocation_proposal_report_to_db_row,
    )

    return paper_autonomous_allocation_proposal_report_to_db_row(_report())


def _row_values(row: object) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def _columns_sql() -> str:
    return ",\n            ".join(SELECT_COLUMNS)


def _placeholders_sql() -> str:
    return ", ".join("%s" for _ in SELECT_COLUMNS)


def test_insert_proposal_report_uses_parameterized_insert() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        insert_paper_autonomous_allocation_proposal_report,
    )

    connection = FakeConnection()
    report = _report()
    expected_row = _db_row()

    inserted = insert_paper_autonomous_allocation_proposal_report(
        connection,
        report,
    )

    assert inserted == expected_row
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        f"""
        INSERT INTO paper_autonomous_allocation_proposal_reports (
            {_columns_sql()}
        ) VALUES ({_placeholders_sql()})
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "paper_autonomous_allocation_proposal_reports (" in sql
    assert "paper-autonomous-allocation-proposal-v0" not in sql


def test_insert_proposal_report_with_result_observes_duplicate() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_store as store

    report = _report()
    expected_row = _db_row()

    inserted = store.insert_paper_autonomous_allocation_proposal_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store.insert_paper_autonomous_allocation_proposal_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_rejects_unexpected_rowcount() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        insert_paper_autonomous_allocation_proposal_report_with_result,
    )

    with pytest.raises(ValueError, match="rowcount"):
        insert_paper_autonomous_allocation_proposal_report_with_result(
            FakeConnection(rowcount=2),
            _report(),
        )


def test_load_proposal_reports_filters_newest_first_and_excludes_inserted_at() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        load_paper_autonomous_allocation_proposal_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_allocation_proposal_reports(
        connection,
        config_version="paper-autonomous-allocation-proposal-v0",
        proposal_status="pass",
        screening_gate_status="pass",
        allocation_config_version="allocation-v0",
        limit=25,
        table_name="allocation_proposal_archive",
    )

    assert reports == (_report(),)
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        f"""
        SELECT
            {_columns_sql()}
        FROM allocation_proposal_archive
        WHERE config_version = %s AND proposal_status = %s AND screening_gate_status = %s AND allocation_config_version = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert "inserted_at" not in _columns_sql()
    assert params == (
        "paper-autonomous-allocation-proposal-v0",
        "pass",
        "pass",
        "allocation-v0",
        25,
    )


def test_load_proposal_reports_accepts_positional_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        load_paper_autonomous_allocation_proposal_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_paper_autonomous_allocation_proposal_reports(connection)

    assert reports == (_report(),)


def test_load_proposal_reports_accepts_dict_rows_without_mutation() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        load_paper_autonomous_allocation_proposal_reports,
    )

    row = _db_row()
    payload_before = deepcopy(row.payload_json)
    counts_before = deepcopy(row.reason_code_counts_json)
    allocation_rows_before = deepcopy(row.allocation_rows_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_paper_autonomous_allocation_proposal_reports(connection)

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["reason_code_counts_json"] == counts_before
    assert record["allocation_rows_json"] == allocation_rows_before


def test_load_proposal_reports_accepts_namedtuple_like_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        load_paper_autonomous_allocation_proposal_reports,
    )

    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_paper_autonomous_allocation_proposal_reports(connection)

    assert reports == (_report(),)


def test_load_proposal_reports_accepts_db_row_objects() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        load_paper_autonomous_allocation_proposal_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_allocation_proposal_reports(connection)

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_autonomous_allocation_proposal_reports; drop table users",
        "audit.paper_autonomous_allocation_proposal_reports",
        "PaperAutonomousAllocationProposalReports",
        "_paper_autonomous_allocation_proposal_reports",
        "paper_autonomous_allocation_proposal_reports_",
        "a",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        insert_paper_autonomous_allocation_proposal_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_allocation_proposal_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_accepts_simple_lowercase_table_names() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        insert_paper_autonomous_allocation_proposal_report,
    )

    connection = FakeConnection()

    insert_paper_autonomous_allocation_proposal_report(
        connection,
        _report(),
        table_name="allocation_proposal_archive",
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert "INSERT INTO allocation_proposal_archive" in sql


def test_insert_accepts_postgres_identifier_at_length_limit() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        insert_paper_autonomous_allocation_proposal_report,
    )

    table_name = "a" * 63
    connection = FakeConnection()

    insert_paper_autonomous_allocation_proposal_report(
        connection,
        _report(),
        table_name=table_name,
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"INSERT INTO {table_name}" in sql


def test_insert_rejects_postgres_identifier_over_length_limit() -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        insert_paper_autonomous_allocation_proposal_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_allocation_proposal_report(
            connection,
            _report(),
            table_name="a" * 64,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "allocation_proposal_archive",
        "allocation_1_proposal_2_archive",
    ],
)
def test_load_accepts_simple_lowercase_table_names(table_name: str) -> None:
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        load_paper_autonomous_allocation_proposal_reports,
    )

    connection = FakeConnection()

    load_paper_autonomous_allocation_proposal_reports(
        connection,
        table_name=table_name,
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit.allocation_proposal_archive"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "a"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " proposal-v0"}, "config_version"),
        ({"allocation_config_version": ""}, "allocation_config_version"),
        ({"proposal_status": "paused"}, "proposal_status"),
        ({"proposal_status": True}, "proposal_status"),
        ({"screening_gate_status": "paused"}, "screening_gate_status"),
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
    from polymarket_alpha_lab.paper_autonomous_allocation_proposal_store import (
        load_paper_autonomous_allocation_proposal_reports,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_allocation_proposal_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    import polymarket_alpha_lab.paper_autonomous_allocation_proposal_store as store

    assert store.DEFAULT_PAPER_AUTONOMOUS_ALLOCATION_PROPOSAL_REPORTS_TABLE == (
        "paper_autonomous_allocation_proposal_reports"
    )
    assert "insert_paper_autonomous_allocation_proposal_report" in store.__all__
    assert (
        "insert_paper_autonomous_allocation_proposal_report_with_result"
        in store.__all__
    )
    assert "load_paper_autonomous_allocation_proposal_reports" in store.__all__
