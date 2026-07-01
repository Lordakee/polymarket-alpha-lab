from __future__ import annotations

import ast
import inspect
import sys
import types
from dataclasses import FrozenInstanceError
from typing import Any

import pytest


def _read_module():
    import polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_psycopg_read as read_module

    return read_module


class FakeConnection:
    def __init__(self) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.close_count += 1


def test_load_gate_reports_delegates_to_store_read_with_current_filters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    connection = FakeConnection()
    expected_reports = (object(),)
    calls: list[dict[str, object]] = []

    def fake_store_loader(connection_arg: object, **kwargs: object) -> tuple[object, ...]:
        calls.append({"connection": connection_arg, **kwargs})
        return expected_reports

    monkeypatch.setattr(read_module, "_load_store_reports", fake_store_loader)

    loaded = read_module.load_paper_autonomous_screening_decision_support_gate_reports(
        connection,
        options=read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(
            config_version="paper-autonomous-screening-decision-support-gate-v0",
            gate_status="watch",
            queue_risk_config_version="action-gated-queue-risk-v0",
            operator_flow_gate_status="pass",
            limit=25,
            table_name="paper_autonomous_screening_decision_support_gate_reports",
        ),
    )

    assert loaded == expected_reports
    assert calls == [
        {
            "connection": connection,
            "config_version": "paper-autonomous-screening-decision-support-gate-v0",
            "gate_status": "watch",
            "queue_risk_config_version": "action-gated-queue-risk-v0",
            "operator_flow_gate_status": "pass",
            "limit": 25,
            "table_name": "paper_autonomous_screening_decision_support_gate_reports",
        },
    ]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 0


def test_options_validate_current_statuses_limit_and_table_name() -> None:
    read_module = _read_module()

    options = read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(
        gate_status="watch",
        operator_flow_gate_status="blocked",
        limit=500,
        table_name="paper_autonomous_screening_decision_support_gate_reports",
    )

    assert options.gate_status == "watch"
    assert options.operator_flow_gate_status == "blocked"

    with pytest.raises(ValueError, match="gate_status"):
        read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(
            gate_status="review",
        )
    with pytest.raises(ValueError, match="operator_flow_gate_status"):
        read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(
            operator_flow_gate_status="review",
        )
    with pytest.raises(ValueError, match="limit"):
        read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(limit=True)
    with pytest.raises(ValueError, match="limit"):
        read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(limit=501)
    with pytest.raises(ValueError, match="table_name"):
        read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(
            table_name="audit.paper_autonomous_screening_decision_support_gate_reports",
        )
    with pytest.raises(ValueError, match="options"):
        read_module.load_paper_autonomous_screening_decision_support_gate_reports(
            object(),
            options=object(),
        )


def test_read_options_are_frozen() -> None:
    read_module = _read_module()
    options = read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions()

    with pytest.raises(FrozenInstanceError):
        options.limit = 25


def test_load_with_psycopg_opens_autocommit_connection_and_closes_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    connection = FakeConnection()
    expected_reports = (object(),)
    connect_calls: list[tuple[str, dict[str, Any]]] = []
    loader_connections: list[object] = []

    def connect(dsn: str, **kwargs: Any) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    def fake_store_loader(connection_arg: object, **kwargs: object) -> tuple[object, ...]:
        loader_connections.append(connection_arg)
        return expected_reports

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))
    monkeypatch.setattr(read_module, "_load_store_reports", fake_store_loader)

    loaded = (
        read_module.load_paper_autonomous_screening_decision_support_gate_reports_with_psycopg(
            "postgresql://postgres:postgres@localhost:54322/postgres",
            options=read_module.PaperAutonomousScreeningDecisionSupportGateReadOptions(
                limit=10,
            ),
        )
    )

    assert loaded == expected_reports
    assert connect_calls == [
        ("postgresql://postgres:postgres@localhost:54322/postgres", {"autocommit": True}),
    ]
    assert loader_connections == [connection]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1


def test_load_with_psycopg_closes_owned_connection_once_on_loader_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    connection = FakeConnection()

    def connect(dsn: str, **kwargs: Any) -> FakeConnection:
        return connection

    def fake_store_loader(connection_arg: object, **kwargs: object) -> tuple[object, ...]:
        raise RuntimeError("boom")

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))
    monkeypatch.setattr(read_module, "_load_store_reports", fake_store_loader)

    with pytest.raises(RuntimeError, match="boom"):
        read_module.load_paper_autonomous_screening_decision_support_gate_reports_with_psycopg(
            "postgresql://postgres:postgres@localhost:54322/postgres",
        )

    assert connection.close_count == 1


def test_psycopg_read_module_stays_read_only_by_source_boundary() -> None:
    read_module = _read_module()
    source = inspect.getsource(read_module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    string_literals: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value.upper())

    forbidden_imports = {
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.runner",
        "polymarket_alpha_lab.paper_execution",
    }
    forbidden_calls = {
        "commit",
        "rollback",
        "executemany",
        "execute_batch",
        "execute_values",
    }
    forbidden_sql_tokens = (
        "INSERT",
        "UPDATE",
        "DELETE",
        "CREATE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "COMMIT",
        "ROLLBACK",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert all(
        token not in literal
        for literal in string_literals
        for token in forbidden_sql_tokens
    )


def test_public_exports_include_read_boundary() -> None:
    read_module = _read_module()

    assert read_module.__all__ == (
        "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_TABLE",
        "MAX_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_READ_LIMIT",
        "PaperAutonomousScreeningDecisionSupportGateReadOptions",
        "load_paper_autonomous_screening_decision_support_gate_reports",
        "load_paper_autonomous_screening_decision_support_gate_reports_with_psycopg",
    )
