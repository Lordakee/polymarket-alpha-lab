from __future__ import annotations

import importlib
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli


CLI_DB_HELPERS = (
    {
        "helper": "_run_nav_snapshot_db_trend",
        "loader_module": "polymarket_alpha_lab.paper_nav_snapshot_db_trend_load",
        "loader": "load_paper_nav_snapshot_db_trend_report",
        "extra_kwargs": {},
    },
    {
        "helper": "_run_strategy_audit_db_history",
        "loader_module": "polymarket_alpha_lab.strategy_audit_db_history_load",
        "loader": "load_strategy_audit_db_history_report",
        "extra_kwargs": {},
    },
    {
        "helper": "_run_cost_audit_db_trend",
        "loader_module": "polymarket_alpha_lab.paper_trade_cost_audit_db_history_load",
        "loader": "load_paper_trade_cost_audit_db_history_report",
        "extra_kwargs": {},
    },
    {
        "helper": "_run_outcome_tracking_db_history",
        "loader_module": "polymarket_alpha_lab.outcome_tracking_db_history_load",
        "loader": "load_outcome_tracking_db_history_report",
        "extra_kwargs": {"stale_after_seconds": 7200},
    },
    {
        "helper": "_run_local_observability_trends_db_history",
        "loader_module": "polymarket_alpha_lab.local_observability_trends_db_history_load",
        "loader": "load_local_observability_trends_db_history_report",
        "extra_kwargs": {},
    },
)


class FakeConnection:
    def __init__(
        self,
        *,
        fail_commit: bool = False,
        fail_rollback: bool = False,
        fail_close: bool = False,
    ) -> None:
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0
        self.fail_commit = fail_commit
        self.fail_rollback = fail_rollback
        self.fail_close = fail_close

    def commit(self) -> None:
        self.commit_count += 1
        if self.fail_commit:
            raise RuntimeError("commit failed without dsn")

    def rollback(self) -> None:
        self.rollback_count += 1
        if self.fail_rollback:
            raise RuntimeError("rollback failed without dsn")

    def close(self) -> None:
        self.close_count += 1
        if self.fail_close:
            raise RuntimeError("close failed without dsn")


def _install_psycopg(
    monkeypatch: pytest.MonkeyPatch,
    connection: FakeConnection,
) -> list[str]:
    connect_calls: list[str] = []

    def fake_connect(dsn: str) -> FakeConnection:
        connect_calls.append(dsn)
        return connection

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    return connect_calls


def _install_loader(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
    loader: Any,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    loader_module = importlib.import_module(case["loader_module"])

    def wrapped_loader(**kwargs: Any) -> Any:
        calls.append(dict(kwargs))
        return loader(**kwargs)

    monkeypatch.setattr(loader_module, case["loader"], wrapped_loader)
    return calls


def _run_case(case: dict[str, Any]) -> Any:
    kwargs = {
        "dsn": "postgresql://user:secret@example.invalid/db",
        "table_name": "paper_report_archive",
        "limit": 7,
        "runner": None,
    }
    kwargs.update(case["extra_kwargs"])
    return getattr(cli, case["helper"])(**kwargs)


@pytest.mark.parametrize("case", CLI_DB_HELPERS, ids=lambda case: case["helper"])
def test_cli_inline_db_cleanup_does_not_mask_loader_exception(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
) -> None:
    connection = FakeConnection(fail_rollback=True, fail_close=True)
    connect_calls = _install_psycopg(monkeypatch, connection)

    def fail_loader(**kwargs: Any) -> None:
        raise ValueError("read failed without dsn")

    loader_calls = _install_loader(monkeypatch, case, fail_loader)

    with pytest.raises(ValueError) as exc_info:
        _run_case(case)

    assert str(exc_info.value) == "read failed without dsn"
    assert connect_calls == ["postgresql://user:secret@example.invalid/db"]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is connection
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("case", CLI_DB_HELPERS, ids=lambda case: case["helper"])
def test_cli_inline_db_cleanup_does_not_mask_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
) -> None:
    connection = FakeConnection(
        fail_commit=True,
        fail_rollback=True,
        fail_close=True,
    )
    _install_psycopg(monkeypatch, connection)
    _install_loader(monkeypatch, case, lambda **kwargs: "ok")

    with pytest.raises(RuntimeError) as exc_info:
        _run_case(case)

    assert str(exc_info.value) == "commit failed without dsn"
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("case", CLI_DB_HELPERS, ids=lambda case: case["helper"])
def test_cli_inline_db_close_failure_does_not_replace_success(
    monkeypatch: pytest.MonkeyPatch,
    case: dict[str, Any],
) -> None:
    connection = FakeConnection(fail_close=True)
    _install_psycopg(monkeypatch, connection)
    _install_loader(monkeypatch, case, lambda **kwargs: "ok")

    result = _run_case(case)

    assert result == "ok"
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1
