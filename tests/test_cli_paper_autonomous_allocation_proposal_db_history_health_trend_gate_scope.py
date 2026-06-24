from __future__ import annotations

import builtins
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main


COMMAND = "paper-autonomous-allocation-proposal-db-history-health-trend-gate"
FORBIDDEN_FLAGS = (
    "--dsn",
    "--table",
    "--persist",
    "--fast",
    "--live",
    "--auth",
    "--wallet",
    "--private-key",
    "--api-key",
    "--account",
    "--order",
    "--trade",
    "--execute",
    "--submit",
    "--approve",
)


@pytest.mark.parametrize("flag", FORBIDDEN_FLAGS)
def test_health_trend_gate_rejects_forbidden_flags_before_env_runner_or_connect(
    flag: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0
    psycopg_import_calls = 0
    real_import = builtins.__import__

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("allocation proposal DB env should not be read")

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("health trend gate runner should not run")

    def forbidden_connect(*_args: Any, **_kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg connect should not run")

    def forbidden_import(
        name: str,
        globals: dict[str, object] | None = None,
        locals: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        nonlocal psycopg_import_calls
        if name == "psycopg":
            psycopg_import_calls += 1
            raise AssertionError("psycopg should not be imported")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_allocation_proposal_db_history_health_db_env",
        forbidden_env,
    )
    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    with pytest.raises(SystemExit) as exc_info:
        main(
            [COMMAND, flag, "forbidden-value"],
            paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner=forbidden_runner,
        )

    assert exc_info.value.code == 2
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_health_trend_gate_rejects_abbreviated_limit_flag_before_env_runner_or_connect(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("allocation proposal DB env should not be read")

    def forbidden_runner(**_kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("health trend gate runner should not run")

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_allocation_proposal_db_history_health_db_env",
        forbidden_env,
    )

    with pytest.raises(SystemExit) as exc_info:
        main(
            [COMMAND, "--lim", "7"],
            paper_autonomous_allocation_proposal_db_history_health_trend_gate_runner=forbidden_runner,
        )

    assert exc_info.value.code == 2
    assert env_calls == 0
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err
