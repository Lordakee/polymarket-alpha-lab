from __future__ import annotations

import ast
import importlib
import inspect
import sys
import types
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from typing import Any

import pytest


class FakeConnection:
    def __init__(self) -> None:
        self.close_count = 0
        self.commit_count = 0
        self.rollback_count = 0
        self.cursor_count = 0

    def cursor(self) -> object:
        self.cursor_count += 1
        raise AssertionError("read adapter must delegate SQL to the loader")

    def commit(self) -> None:
        self.commit_count += 1
        raise AssertionError("read adapter must not commit")

    def rollback(self) -> None:
        self.rollback_count += 1
        raise AssertionError("read adapter must not rollback")

    def close(self) -> None:
        self.close_count += 1


def _read_module() -> object:
    return importlib.import_module(
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg_read",
    )


def test_read_options_are_frozen() -> None:
    read_module = _read_module()
    PaperAutonomousAllocationProposalReadOptions = (
        read_module.PaperAutonomousAllocationProposalReadOptions
    )
    options = PaperAutonomousAllocationProposalReadOptions()

    with pytest.raises(FrozenInstanceError):
        options.limit = 10


@pytest.mark.parametrize(
    ("kwargs", "message"),
    (
        ({"limit": 0}, "limit"),
        ({"limit": True}, "limit"),
        ({"limit": 501}, "limit"),
        ({"screening_gate_table_name": "BadTable"}, "table_name"),
        (
            {"action_gated_queue_decision_support_table_name": "public.bad.table"},
            "table_name",
        ),
        ({"screening_gate_table_name": "a" * 64}, "table_name"),
        (
            {"action_gated_queue_decision_support_table_name": f"public.{'a' * 64}"},
            "table_name",
        ),
        ({"source_queue_table_name": "source-queue"}, "table_name"),
    ),
)
def test_read_options_reject_invalid_inputs(
    kwargs: dict[str, Any],
    message: str,
) -> None:
    read_module = _read_module()
    PaperAutonomousAllocationProposalReadOptions = (
        read_module.PaperAutonomousAllocationProposalReadOptions
    )
    with pytest.raises(ValueError, match=message):
        PaperAutonomousAllocationProposalReadOptions(**kwargs)


def test_read_options_accept_postgres_identifier_limit_boundary() -> None:
    read_module = _read_module()
    PaperAutonomousAllocationProposalReadOptions = (
        read_module.PaperAutonomousAllocationProposalReadOptions
    )

    options = PaperAutonomousAllocationProposalReadOptions(
        screening_gate_table_name="a" * 63,
        action_gated_queue_decision_support_table_name=f"public.{'b' * 63}",
        source_queue_table_name="c" * 63,
    )

    assert options.screening_gate_table_name == "a" * 63
    assert options.action_gated_queue_decision_support_table_name == f"public.{'b' * 63}"
    assert options.source_queue_table_name == "c" * 63


def test_load_delegates_options_and_generated_at_to_readonly_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    PaperAutonomousAllocationProposalReadOptions = (
        read_module.PaperAutonomousAllocationProposalReadOptions
    )
    load_paper_autonomous_allocation_proposal_report = (
        read_module.load_paper_autonomous_allocation_proposal_report
    )
    connection = FakeConnection()
    options = PaperAutonomousAllocationProposalReadOptions(limit=7)
    generated_at = datetime(2026, 6, 23, 15, 0, tzinfo=UTC)
    proposal = object()
    calls: list[dict[str, object]] = []

    def fake_loader(received_connection: object, **kwargs: object) -> object:
        calls.append({"connection": received_connection, **kwargs})
        return proposal

    monkeypatch.setattr(
        read_module,
        "_load_paper_autonomous_allocation_proposal_report",
        fake_loader,
    )

    loaded = load_paper_autonomous_allocation_proposal_report(
        connection,
        options=options,
        generated_at=generated_at,
    )

    assert loaded is proposal
    assert calls == [
        {
            "connection": connection,
            "screening_gate_limit": 7,
            "screening_gate_table_name": (
                "paper_autonomous_screening_decision_support_gate_reports"
            ),
            "action_gated_queue_decision_support_limit": 7,
            "action_gated_queue_decision_support_table_name": (
                "paper_action_gated_queue_decision_support_reports"
            ),
            "source_queue_limit": 7,
            "source_queue_table_name": (
                "paper_action_gated_strategy_recommendation_queue_reports"
            ),
            "generated_at": generated_at,
        },
    ]
    assert connection.cursor_count == 0
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_with_psycopg_opens_autocommit_connection_and_closes_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    PaperAutonomousAllocationProposalReadOptions = (
        read_module.PaperAutonomousAllocationProposalReadOptions
    )
    load_paper_autonomous_allocation_proposal_report_with_psycopg = (
        read_module.load_paper_autonomous_allocation_proposal_report_with_psycopg
    )
    connection = FakeConnection()
    proposal = object()
    connect_calls: list[tuple[str, dict[str, object]]] = []
    loader_calls: list[dict[str, object]] = []

    def connect(dsn: str, **kwargs: object) -> FakeConnection:
        connect_calls.append((dsn, kwargs))
        return connection

    def fake_loader(received_connection: object, **kwargs: object) -> object:
        loader_calls.append({"connection": received_connection, **kwargs})
        return proposal

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))
    monkeypatch.setattr(
        read_module,
        "_load_paper_autonomous_allocation_proposal_report",
        fake_loader,
    )

    loaded = load_paper_autonomous_allocation_proposal_report_with_psycopg(
        "postgresql://postgres:postgres@localhost:54322/postgres",
        options=PaperAutonomousAllocationProposalReadOptions(limit=5),
    )

    assert loaded is proposal
    assert connect_calls == [
        (
            "postgresql://postgres:postgres@localhost:54322/postgres",
            {"autocommit": True},
        ),
    ]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert isinstance(loader_calls[0]["generated_at"], datetime)
    assert loader_calls[0]["generated_at"].tzinfo is UTC
    assert connection.close_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_load_with_psycopg_closes_once_on_loader_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    read_module = _read_module()
    load_paper_autonomous_allocation_proposal_report_with_psycopg = (
        read_module.load_paper_autonomous_allocation_proposal_report_with_psycopg
    )
    connection = FakeConnection()

    def connect(_dsn: str, **_kwargs: object) -> FakeConnection:
        return connection

    def broken_loader(_connection: object, **_kwargs: object) -> object:
        raise RuntimeError("loader failed")

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=connect))
    monkeypatch.setattr(
        read_module,
        "_load_paper_autonomous_allocation_proposal_report",
        broken_loader,
    )

    with pytest.raises(RuntimeError, match="loader failed"):
        load_paper_autonomous_allocation_proposal_report_with_psycopg(
            "postgresql://postgres:postgres@localhost:54322/postgres",
        )

    assert connection.close_count == 1
    assert connection.commit_count == 0
    assert connection.rollback_count == 0


def test_psycopg_read_module_stays_select_only_by_source_boundary() -> None:
    read_module = _read_module()
    source = inspect.getsource(read_module)
    tree = ast.parse(source)
    call_names: set[str] = set()
    string_literals: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value.upper())

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

    assert call_names.isdisjoint(forbidden_calls)
    assert all(
        token not in literal
        for literal in string_literals
        for token in forbidden_sql_tokens
    )
