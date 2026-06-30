from __future__ import annotations

from typing import Any

import pytest

from tests.test_paper_autonomous_proposal_risk_gate_db_row import (
    _db_row,
    _risk_gate_report,
)


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


class FakeCursor:
    def __init__(
        self,
        *,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        execute_error: Exception | None = None,
    ) -> None:
        self.rows = rows
        self.rowcount = rowcount
        self.execute_error = execute_error
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


class FakeConnection:
    def __init__(
        self,
        *,
        rows: tuple[Any, ...] = (),
        rowcount: int = 1,
        execute_error: Exception | None = None,
    ) -> None:
        self.cursor_instance = FakeCursor(
            rows=rows,
            rowcount=rowcount,
            execute_error=execute_error,
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


def test_insert_with_psycopg_wraps_json_params_and_manages_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_psycopg as adapter

    connection = FakeConnection()
    monkeypatch.setattr(adapter, "_connect", lambda dsn: connection)
    monkeypatch.setattr(adapter, "_jsonb_adapter", lambda: FakeJsonb)

    result = adapter.insert_paper_autonomous_proposal_risk_gate_report_with_psycopg(
        "postgresql://localhost/postgres",
        _risk_gate_report(),
        table_name="risk_gate_archive",
    )

    assert result.inserted is True
    assert connection.cursor_count == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
    assert connection.cursor_instance.closed is True
    _sql, params = connection.cursor_instance.calls[0]
    assert not isinstance(params[7], FakeJsonb)
    for index in (8, 9, 10, 11):
        assert isinstance(params[index], FakeJsonb)


def test_insert_with_psycopg_rolls_back_and_closes_on_execute_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_psycopg as adapter

    connection = FakeConnection(execute_error=RuntimeError("boom"))
    monkeypatch.setattr(adapter, "_connect", lambda dsn: connection)
    monkeypatch.setattr(adapter, "_jsonb_adapter", lambda: FakeJsonb)

    with pytest.raises(RuntimeError, match="boom"):
        adapter.insert_paper_autonomous_proposal_risk_gate_report_with_psycopg(
            "postgresql://localhost/postgres",
            _risk_gate_report(),
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1
    assert connection.cursor_instance.closed is True


def test_load_with_psycopg_passes_filters_and_manages_connection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_psycopg as adapter

    connection = FakeConnection(rows=(_db_row(),))
    monkeypatch.setattr(adapter, "_connect", lambda dsn: connection)
    monkeypatch.setattr(adapter, "_jsonb_adapter", lambda: FakeJsonb)

    reports = adapter.load_paper_autonomous_proposal_risk_gate_reports_with_psycopg(
        "postgresql://localhost/postgres",
        config_version="paper-autonomous-proposal-risk-gate-v0",
        gate_status="pass",
        source_proposal_status="candidate",
        limit=10,
        table_name="risk_gate_archive",
    )

    assert reports == (_risk_gate_report(),)
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
    sql, params = connection.cursor_instance.calls[0]
    assert "FROM risk_gate_archive" in sql
    assert params == (
        "paper-autonomous-proposal-risk-gate-v0",
        "pass",
        "candidate",
        10,
    )


def test_public_exports_are_exact() -> None:
    import polymarket_alpha_lab.paper_autonomous_proposal_risk_gate_psycopg as adapter

    assert adapter.__all__ == (
        "insert_paper_autonomous_proposal_risk_gate_report_with_psycopg",
        "load_paper_autonomous_proposal_risk_gate_reports_with_psycopg",
    )
