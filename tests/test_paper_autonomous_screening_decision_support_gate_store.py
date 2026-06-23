from __future__ import annotations

from collections import namedtuple
from copy import deepcopy
import sys
from typing import Any

import pytest

from tests.test_paper_autonomous_screening_decision_support_gate_db_row import (
    REDUCER_MODULE_NAME,
    _install_fake_reducer_module,
    _report,
)


SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_status",
    "recommended_next_step",
    "reason_codes_json",
    "reason_code_counts_json",
    "operator_flow_gate_config_version",
    "operator_flow_gate_generated_at",
    "operator_flow_gate_status",
    "operator_flow_recommended_next_step",
    "queue_priority_generated_at",
    "queue_risk_generated_at",
    "queue_risk_config_version",
    "queue_risk_status",
    "queue_risk_recommended_next_step",
    "queue_source_report_count",
    "queue_research_ready_count",
    "queue_watch_count",
    "queue_blocked_count",
    "queue_candidate_count",
    "queue_ready_count",
    "queue_candidate_watch_count",
    "queue_candidate_blocked_count",
    "queue_total_ready_notional",
    "queue_largest_ready_notional",
    "queue_top_research_priority_score",
    "queue_average_research_priority_score",
    "trend_source_snapshot_count",
    "trend_latest_risk_status",
    "trend_consecutive_latest_watch_count",
    "trend_consecutive_latest_blocked_count",
    "trend_duplicate_generated_at_count",
    "rank_stability_status",
    "rank_stable_ready_count",
    "rank_unstable_ready_count",
    "rank_blocked_count",
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
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_db_row import (
        paper_autonomous_screening_decision_support_gate_report_to_db_row,
    )

    return paper_autonomous_screening_decision_support_gate_report_to_db_row(_report())


def _row_values(row: object) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def test_insert_autonomous_screening_gate_report_uses_parameterized_insert() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        insert_paper_autonomous_screening_decision_support_gate_report,
    )

    connection = FakeConnection()
    report = _report()
    expected_row = _db_row()

    inserted = insert_paper_autonomous_screening_decision_support_gate_report(
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
        """
        INSERT INTO paper_autonomous_screening_decision_support_gate_reports (
            report_sha256,
            generated_at,
            config_version,
            gate_status,
            recommended_next_step,
            reason_codes_json,
            reason_code_counts_json,
            operator_flow_gate_config_version,
            operator_flow_gate_generated_at,
            operator_flow_gate_status,
            operator_flow_recommended_next_step,
            queue_priority_generated_at,
            queue_risk_generated_at,
            queue_risk_config_version,
            queue_risk_status,
            queue_risk_recommended_next_step,
            queue_source_report_count,
            queue_research_ready_count,
            queue_watch_count,
            queue_blocked_count,
            queue_candidate_count,
            queue_ready_count,
            queue_candidate_watch_count,
            queue_candidate_blocked_count,
            queue_total_ready_notional,
            queue_largest_ready_notional,
            queue_top_research_priority_score,
            queue_average_research_priority_score,
            trend_source_snapshot_count,
            trend_latest_risk_status,
            trend_consecutive_latest_watch_count,
            trend_consecutive_latest_blocked_count,
            trend_duplicate_generated_at_count,
            rank_stability_status,
            rank_stable_ready_count,
            rank_unstable_ready_count,
            rank_blocked_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _row_values(expected_row)
    assert "paper_autonomous_screening_decision_support_gate_reports (" in sql
    assert "paper-autonomous-screening-decision-support-gate-v0" not in sql


def test_insert_autonomous_screening_gate_report_with_result_observes_duplicate() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store as store

    report = _report()
    expected_row = _db_row()

    inserted = (
        store.insert_paper_autonomous_screening_decision_support_gate_report_with_result(
            FakeConnection(rowcount=1),
            report,
        )
    )
    duplicate = (
        store.insert_paper_autonomous_screening_decision_support_gate_report_with_result(
            FakeConnection(rowcount=0),
            report,
        )
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_load_autonomous_screening_gate_reports_filters_by_config_status_source_and_limit() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_screening_decision_support_gate_reports(
        connection,
        config_version="paper-autonomous-screening-decision-support-gate-v0",
        gate_status="pass",
        queue_risk_config_version="action-gated-queue-risk-v0",
        operator_flow_gate_status="pass",
        limit=25,
        table_name="autonomous_screening_gate_archive",
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
            gate_status,
            recommended_next_step,
            reason_codes_json,
            reason_code_counts_json,
            operator_flow_gate_config_version,
            operator_flow_gate_generated_at,
            operator_flow_gate_status,
            operator_flow_recommended_next_step,
            queue_priority_generated_at,
            queue_risk_generated_at,
            queue_risk_config_version,
            queue_risk_status,
            queue_risk_recommended_next_step,
            queue_source_report_count,
            queue_research_ready_count,
            queue_watch_count,
            queue_blocked_count,
            queue_candidate_count,
            queue_ready_count,
            queue_candidate_watch_count,
            queue_candidate_blocked_count,
            queue_total_ready_notional,
            queue_largest_ready_notional,
            queue_top_research_priority_score,
            queue_average_research_priority_score,
            trend_source_snapshot_count,
            trend_latest_risk_status,
            trend_consecutive_latest_watch_count,
            trend_consecutive_latest_blocked_count,
            trend_duplicate_generated_at_count,
            rank_stability_status,
            rank_stable_ready_count,
            rank_unstable_ready_count,
            rank_blocked_count,
            payload_json,
            paper_only,
            report_only,
            readonly
        FROM autonomous_screening_gate_archive
        WHERE config_version = %s AND gate_status = %s AND queue_risk_config_version = %s AND operator_flow_gate_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert params == (
        "paper-autonomous-screening-decision-support-gate-v0",
        "pass",
        "action-gated-queue-risk-v0",
        "pass",
        25,
    )


def test_load_autonomous_screening_gate_reports_accepts_positional_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_paper_autonomous_screening_decision_support_gate_reports(connection)

    assert reports == (_report(),)


def test_load_autonomous_screening_gate_reports_accepts_dict_rows_without_mutation() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    row = _db_row()
    payload_before = deepcopy(row.payload_json)
    counts_before = deepcopy(row.reason_code_counts_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_paper_autonomous_screening_decision_support_gate_reports(connection)

    assert reports == (_report(),)
    assert record["payload_json"] == payload_before
    assert record["reason_code_counts_json"] == counts_before


def test_load_autonomous_screening_gate_reports_accepts_namedtuple_like_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_paper_autonomous_screening_decision_support_gate_reports(connection)

    assert reports == (_report(),)


def test_load_autonomous_screening_gate_reports_accepts_db_row_objects() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_screening_decision_support_gate_reports(connection)

    assert reports == (_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_autonomous_screening_decision_support_gate_reports; drop table users",
        "audit.paper_autonomous_screening_decision_support_gate_reports",
        "PaperAutonomousScreeningGateReports",
        "_paper_autonomous_screening_gate_reports",
        "paper_autonomous_screening_gate_reports_",
        "a",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(table_name: str) -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        insert_paper_autonomous_screening_decision_support_gate_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_screening_decision_support_gate_report(
            connection,
            _report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_insert_accepts_simple_lowercase_table_names() -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        insert_paper_autonomous_screening_decision_support_gate_report,
    )

    connection = FakeConnection()

    insert_paper_autonomous_screening_decision_support_gate_report(
        connection,
        _report(),
        table_name="autonomous_screening_gate_archive",
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert "INSERT INTO autonomous_screening_gate_archive" in sql


@pytest.mark.parametrize(
    "table_name",
    [
        "a0",
        "autonomous_screening_gate_archive",
        "gate_1_archive_2",
    ],
)
def test_load_accepts_simple_lowercase_table_names(table_name: str) -> None:
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    connection = FakeConnection()

    load_paper_autonomous_screening_decision_support_gate_reports(
        connection,
        table_name=table_name,
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"FROM {table_name}" in sql


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit.autonomous_screening_gate_archive"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"table_name": "a"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " gate-v0"}, "config_version"),
        ({"queue_risk_config_version": ""}, "queue_risk_config_version"),
        ({"operator_flow_gate_status": "paused"}, "operator_flow_gate_status"),
        ({"gate_status": "paused"}, "gate_status"),
        ({"gate_status": True}, "gate_status"),
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
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store import (
        load_paper_autonomous_screening_decision_support_gate_reports,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_screening_decision_support_gate_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_store as store

    assert (
        store.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_REPORTS_TABLE
        == "paper_autonomous_screening_decision_support_gate_reports"
    )
    assert (
        "insert_paper_autonomous_screening_decision_support_gate_report"
        in store.__all__
    )
    assert (
        "load_paper_autonomous_screening_decision_support_gate_reports"
        in store.__all__
    )
