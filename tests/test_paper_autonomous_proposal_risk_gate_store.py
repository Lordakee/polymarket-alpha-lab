from __future__ import annotations

from collections import namedtuple
from collections.abc import Mapping
from typing import Any

import pytest

from tests.test_paper_autonomous_proposal_risk_gate_db_row import (
    _risk_gate_report,
)


SELECT_COLUMNS = (
    "report_sha256",
    "generated_at",
    "config_version",
    "gate_status",
    "recommended_next_step",
    "source_proposal_status",
    "source_proposal_count",
    "source_proposal_total_notional",
    "blocked_reason_codes_json",
    "watch_reason_codes_json",
    "reason_codes_json",
    "payload_json",
    "paper_only",
    "report_only",
    "readonly",
)
LOAD_COLUMNS = (*SELECT_COLUMNS, "inserted_at")


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
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_db_row import (
        to_db_row,
    )

    return to_db_row(_risk_gate_report())


def _row_values(row: object) -> tuple[Any, ...]:
    return tuple(getattr(row, column) for column in SELECT_COLUMNS)


def _mutable_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _mutable_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mutable_json(item) for item in value]
    return value


def _insert_values(row: object) -> tuple[Any, ...]:
    return tuple(_mutable_json(getattr(row, column)) for column in SELECT_COLUMNS)


def _columns_sql() -> str:
    return ",\n            ".join(SELECT_COLUMNS)


def _load_columns_sql() -> str:
    return ",\n            ".join(LOAD_COLUMNS)


def _placeholders_sql() -> str:
    return ", ".join("%s" for _ in SELECT_COLUMNS)


def test_insert_proposal_risk_gate_report_uses_parameterized_insert() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report,
    )

    connection = FakeConnection()
    report = _risk_gate_report()
    expected_row = _db_row()

    inserted = insert_paper_autonomous_proposal_risk_gate_report(
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
        INSERT INTO paper_autonomous_proposal_risk_gate_reports (
            {_columns_sql()}
        ) VALUES ({_placeholders_sql()})
        ON CONFLICT (report_sha256) DO NOTHING
        """,
    )
    assert params == _insert_values(expected_row)
    assert "paper_autonomous_proposal_risk_gate_reports (" in sql
    assert "paper-autonomous-proposal-risk-gate-v0" not in sql


def test_insert_proposal_risk_gate_report_with_result_observes_duplicate() -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store as store

    report = _risk_gate_report()
    expected_row = _db_row()

    inserted = store.insert_paper_autonomous_proposal_risk_gate_report_with_result(
        FakeConnection(rowcount=1),
        report,
    )
    duplicate = store.insert_paper_autonomous_proposal_risk_gate_report_with_result(
        FakeConnection(rowcount=0),
        report,
    )

    assert inserted.row == expected_row
    assert inserted.inserted is True
    assert duplicate.row == expected_row
    assert duplicate.inserted is False


def test_insert_rejects_unexpected_rowcount() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report_with_result,
    )

    with pytest.raises(ValueError, match="rowcount"):
        insert_paper_autonomous_proposal_risk_gate_report_with_result(
            FakeConnection(rowcount=2),
            _risk_gate_report(),
        )


def test_insert_closes_cursor_when_execute_fails_without_managing_transaction() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report,
    )

    connection = FakeConnection(execute_error=RuntimeError("boom"))

    with pytest.raises(RuntimeError, match="boom"):
        insert_paper_autonomous_proposal_risk_gate_report(
            connection,
            _risk_gate_report(),
        )

    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True


def test_insert_ignores_cursor_close_errors() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report,
    )

    connection = FakeConnection(close_error=RuntimeError("close failed"))

    row = insert_paper_autonomous_proposal_risk_gate_report(
        connection,
        _risk_gate_report(),
    )

    assert row == _db_row()
    assert connection.cursor_instance.closed is True


def test_load_proposal_risk_gate_reports_filters_newest_first_and_selects_inserted_at() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        load_paper_autonomous_proposal_risk_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(row,))

    reports = load_paper_autonomous_proposal_risk_gate_reports(
        connection,
        config_version="paper-autonomous-proposal-risk-gate-v0",
        gate_status="pass",
        source_proposal_status="candidate",
        limit=25,
        table_name="risk_gate_archive",
    )

    assert reports == (_risk_gate_report(),)
    assert connection.cursor_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0
    assert connection.cursor_instance.closed is True
    sql, params = connection.cursor_instance.calls[0]
    assert normalize_sql(sql) == normalize_sql(
        f"""
        SELECT
            {_load_columns_sql()}
        FROM risk_gate_archive
        WHERE config_version = %s AND gate_status = %s AND source_proposal_status = %s
        ORDER BY generated_at DESC, inserted_at DESC, report_sha256 DESC
        LIMIT %s
        """,
    )
    assert "inserted_at" in _load_columns_sql()
    assert params == (
        "paper-autonomous-proposal-risk-gate-v0",
        "pass",
        "candidate",
        25,
    )


def test_load_proposal_risk_gate_reports_accepts_positional_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        load_paper_autonomous_proposal_risk_gate_reports,
    )

    row = _db_row()
    connection = FakeConnection(rows=(_row_values(row),))

    reports = load_paper_autonomous_proposal_risk_gate_reports(connection)

    assert reports == (_risk_gate_report(),)


def test_load_proposal_risk_gate_reports_accepts_dict_rows_without_mutation() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        load_paper_autonomous_proposal_risk_gate_reports,
    )

    row = _db_row()
    payload_before = _mutable_json(row.payload_json)
    blocked_before = _mutable_json(row.blocked_reason_codes_json)
    watch_before = _mutable_json(row.watch_reason_codes_json)
    codes_before = _mutable_json(row.reason_codes_json)
    record = dict(zip(SELECT_COLUMNS, _row_values(row), strict=True))
    connection = FakeConnection(rows=(record,))

    reports = load_paper_autonomous_proposal_risk_gate_reports(connection)

    assert reports == (_risk_gate_report(),)
    assert _mutable_json(record["payload_json"]) == payload_before
    assert _mutable_json(record["blocked_reason_codes_json"]) == blocked_before
    assert _mutable_json(record["watch_reason_codes_json"]) == watch_before
    assert _mutable_json(record["reason_codes_json"]) == codes_before


def test_load_proposal_risk_gate_reports_accepts_namedtuple_like_rows() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        load_paper_autonomous_proposal_risk_gate_reports,
    )

    row = _db_row()
    Record = namedtuple("Record", SELECT_COLUMNS)
    connection = FakeConnection(rows=(Record(*_row_values(row)),))

    reports = load_paper_autonomous_proposal_risk_gate_reports(connection)

    assert reports == (_risk_gate_report(),)


@pytest.mark.parametrize(
    "table_name",
    [
        "paper_autonomous_proposal_risk_gate_reports; drop table x",
        "audit..paper_autonomous_proposal_risk_gate_reports",
        "audit.paper.autonomous_proposal_risk_gate_reports",
        "PaperAutonomousProposalRiskGateReports",
        "_paper_autonomous_proposal_risk_gate_reports",
        "paper_autonomous_proposal_risk_gate_reports_",
    ],
)
def test_insert_rejects_unsafe_table_name_before_cursor_creation(
    table_name: str,
) -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_proposal_risk_gate_report(
            connection,
            _risk_gate_report(),
            table_name=table_name,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    "table_name",
    (
        "a",
        "a0",
        "risk_gate_archive",
        "audit.risk_gate_archive",
        "risk_1_gate_2_archive",
    ),
)
def test_insert_accepts_lowercase_table_names(table_name: str) -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report,
    )

    connection = FakeConnection()

    insert_paper_autonomous_proposal_risk_gate_report(
        connection,
        _risk_gate_report(),
        table_name=table_name,
    )

    sql, _params = connection.cursor_instance.calls[0]
    assert f"INSERT INTO {table_name}" in sql


def test_insert_rejects_postgres_identifier_over_length_limit() -> None:
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        insert_paper_autonomous_proposal_risk_gate_report,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match="table_name"):
        insert_paper_autonomous_proposal_risk_gate_report(
            connection,
            _risk_gate_report(),
            table_name="a" * 64,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"table_name": "audit..risk_gate_archive"}, "table_name"),
        ({"table_name": "audit.risk.gate.archive"}, "table_name"),
        ({"table_name": "_"}, "table_name"),
        ({"config_version": ""}, "config_version"),
        ({"config_version": " risk-gate-v0"}, "config_version"),
        ({"gate_status": "paused"}, "gate_status"),
        ({"gate_status": True}, "gate_status"),
        ({"source_proposal_status": "paused"}, "source_proposal_status"),
        ({"source_proposal_status": True}, "source_proposal_status"),
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
    from polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store import (
        load_paper_autonomous_proposal_risk_gate_reports,
    )

    connection = FakeConnection()

    with pytest.raises(ValueError, match=message):
        load_paper_autonomous_proposal_risk_gate_reports(
            connection,
            **kwargs,
        )

    assert connection.cursor_count == 0
    assert connection.cursor_instance.calls == []


def test_public_exports_include_default_table_and_store_functions() -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_store as store

    assert store.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE",
        "PaperAutonomousProposalRiskGateInsertResult",
        "insert_paper_autonomous_proposal_risk_gate_report",
        "insert_paper_autonomous_proposal_risk_gate_report_with_result",
        "load_paper_autonomous_proposal_risk_gate_reports",
    )
    assert (
        store.DEFAULT_PAPER_AUTONOMOUS_PROPOSAL_RISK_GATE_REPORTS_TABLE
        == "paper_autonomous_proposal_risk_gate_reports"
    )
