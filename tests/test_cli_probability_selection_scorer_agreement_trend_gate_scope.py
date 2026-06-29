from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main


COMMAND = "probability-selection-scorer-agreement-trend-gate"

FORBIDDEN_FLAGS = (
    "--dsn",
    "--table",
    "--persist",
    "--input",
    "--output",
    "--live",
    "--wallet",
    "--order",
    "--execute",
    "--auth",
    "--private-key",
    "--account",
    "--fast",
    "--api-key",
    "--trade",
    "--submit",
    "--approve",
)


def test_agreement_trend_gate_help_is_readonly_report_only_with_limit_only(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main([COMMAND, "--help"])

    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    assert "read-only" in help_text
    assert "report-only" in help_text
    assert "--limit" in help_text
    for flag in FORBIDDEN_FLAGS:
        assert flag not in help_text


def test_agreement_trend_gate_rejects_limit_abbreviation_before_env_runner_or_connect(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("agreement DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement trend gate runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_probability_selection_scorer_agreement_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    with pytest.raises(SystemExit) as exc_info:
        main(
            [COMMAND, "--lim", "5"],
            probability_selection_scorer_agreement_trend_gate_runner=forbidden_runner,
        )

    assert exc_info.value.code == 2
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert "unrecognized arguments: --lim" in capsys.readouterr().err


@pytest.mark.parametrize("flag", FORBIDDEN_FLAGS)
def test_agreement_trend_gate_forbidden_flags_fail_before_env_runner_or_connect(
    flag: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("agreement DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement trend gate runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect")

    monkeypatch.setattr(
        cli,
        "from_probability_selection_scorer_agreement_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    with pytest.raises(SystemExit) as exc_info:
        main(
            [COMMAND, flag, "forbidden-value"],
            probability_selection_scorer_agreement_trend_gate_runner=forbidden_runner,
        )

    assert exc_info.value.code == 2
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert f"unrecognized arguments: {flag}" in capsys.readouterr().err


def test_agreement_trend_gate_limit_is_accepted_but_still_does_not_require_local_db(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def disabled_env() -> object:
        nonlocal env_calls
        env_calls += 1
        return SimpleNamespace(enabled=False, dsn=None, table_name="unused_reports")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("agreement trend gate runner should not run without DB")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("psycopg should not connect without DB")

    monkeypatch.setattr(
        cli,
        "from_probability_selection_scorer_agreement_db_env",
        disabled_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", "5"],
        probability_selection_scorer_agreement_trend_gate_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 1
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert f"{COMMAND} requires probability selection scorer agreement DB" in captured.err
