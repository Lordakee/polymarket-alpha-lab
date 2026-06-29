from __future__ import annotations

import ast
from datetime import datetime, UTC
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "strategy-cycle-history-gate"
SOURCE_DSN = "postgresql://source-user:source-pass@localhost/source-db"
GATE_DSN = "postgresql://gate-user:gate-pass@localhost/gate-db"
SOURCE_TABLE = "source_strategy_cycle_reports"
GATE_TABLE = "strategy_cycle_history_gate_reports"


def _run_main(argv: list[str]) -> int:
    try:
        return main(argv)
    except SystemExit as exc:  # pragma: no cover - keeps RED as assertion failure.
        pytest.fail(f"unexpected parser exit {exc.code}")


def _parse_cli() -> ast.AST:
    return ast.parse(CLI_PATH.read_text(encoding="utf-8"), filename=str(CLI_PATH))


def _call_or_attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _call_or_attribute_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _command_parser_variable(tree: ast.AST, command: str) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        call = node.value
        if not isinstance(call, ast.Call):
            continue
        if _call_or_attribute_name(call) != "add_parser":
            continue
        if (
            call.args
            and isinstance(call.args[0], ast.Constant)
            and call.args[0].value == command
        ):
            return target.id
    raise AssertionError(f"missing parser variable for {command}")


def _explicit_dest(call: ast.Call) -> str | None:
    for keyword in call.keywords:
        if (
            keyword.arg == "dest"
            and isinstance(keyword.value, ast.Constant)
            and isinstance(keyword.value.value, str)
        ):
            return keyword.value.value
    return None


def _derived_argparse_dest(option_strings: tuple[str, ...]) -> str | None:
    optional_strings = tuple(option for option in option_strings if option.startswith("-"))
    if not optional_strings:
        return None
    long_options = tuple(option for option in optional_strings if option.startswith("--"))
    option = (long_options or optional_strings)[0]
    return option.lstrip("-").replace("-", "_")


def _parser_argument_surface(tree: ast.AST, parser_variable: str) -> set[str]:
    surface: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if _call_or_attribute_name(node) != "add_argument":
            continue
        func = node.func
        if (
            not isinstance(func, ast.Attribute)
            or not isinstance(func.value, ast.Name)
            or func.value.id != parser_variable
        ):
            continue
        option_strings = tuple(
            arg.value
            for arg in node.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        )
        surface.update(option_strings)
        dest = _explicit_dest(node) or _derived_argparse_dest(option_strings)
        if dest is not None:
            surface.add(dest)
    return surface


def _source_db_config(
    *,
    enabled: bool = True,
    dsn: str | None = SOURCE_DSN,
    table_name: str = SOURCE_TABLE,
) -> SimpleNamespace:
    return SimpleNamespace(enabled=enabled, dsn=dsn, table_name=table_name)


def _gate_db_config(
    *,
    enabled: bool = True,
    dsn: str | None = GATE_DSN,
    table_name: str = GATE_TABLE,
) -> SimpleNamespace:
    return SimpleNamespace(enabled=enabled, dsn=dsn, table_name=table_name)


def _install_successful_gate_pipeline(
    monkeypatch: pytest.MonkeyPatch,
    *,
    source_reports: tuple[object, ...] = (
        SimpleNamespace(generated_at=datetime(2026, 6, 29, 12, 0, tzinfo=UTC)),
        SimpleNamespace(generated_at=datetime(2026, 6, 29, 11, 0, tzinfo=UTC)),
    ),
    gate_status: str = "pass",
    source_history_status: str = "pass",
    latest_snapshot_ready_share: Decimal = Decimal("0.250000"),
    blocked_market_share: Decimal = Decimal("0.125000"),
) -> dict[str, Any]:
    calls: dict[str, Any] = {
        "loaded": [],
        "history_reports": [],
        "gate_reports": [],
        "sink": [],
    }
    history_report = SimpleNamespace(
        history_status=source_history_status,
        report_count=len(source_reports),
        latest_snapshot_ready_share=latest_snapshot_ready_share,
        blocked_market_share=blocked_market_share,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    gate_report = SimpleNamespace(
        gate_status=gate_status,
        source_history_status=source_history_status,
        source_report_count=len(source_reports),
        latest_snapshot_ready_share=latest_snapshot_ready_share,
        blocked_market_share=blocked_market_share,
        paper_only=True,
        report_only=True,
        readonly=True,
    )
    gate_config = SimpleNamespace(
        config_version="paper-strategy-cycle-report-history-gate-v0",
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    def source_loader(
        dsn: str,
        *,
        config_version: str | None,
        limit: int,
        table_name: str,
    ) -> tuple[object, ...]:
        calls["loaded"].append((dsn, config_version, limit, table_name))
        return source_reports

    def history_builder(
        reports: tuple[object, ...],
        *,
        config: object,
        generated_at: datetime,
    ) -> object:
        calls["history_reports"].append((reports, config, generated_at))
        return history_report

    def gate_config_factory() -> object:
        return gate_config

    def gate_builder(
        source_history_report: object,
        *,
        config: object,
        generated_at: datetime,
    ) -> object:
        calls["gate_reports"].append((source_history_report, config, generated_at))
        return gate_report

    def gate_sink(*, dsn: str, report: object, table_name: str) -> object:
        calls["sink"].append((dsn, report, table_name))
        return SimpleNamespace(inserted=True)

    monkeypatch.setattr(cli, "load_paper_strategy_cycle_reports_with_psycopg", source_loader)
    monkeypatch.setattr(
        cli,
        "build_paper_strategy_cycle_report_history_report",
        history_builder,
    )
    monkeypatch.setattr(
        cli,
        "_paper_strategy_cycle_report_history_gate_config",
        gate_config_factory,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "_build_paper_strategy_cycle_report_history_gate_report",
        gate_builder,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "_insert_paper_strategy_cycle_report_history_gate_report_with_psycopg",
        gate_sink,
        raising=False,
    )
    return calls


def test_strategy_cycle_history_gate_fails_before_db_work_when_source_env_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    load_calls = 0

    def forbidden_loader(*_args: object, **_kwargs: object) -> object:
        nonlocal load_calls
        load_calls += 1
        raise AssertionError("source DB should not be read")

    monkeypatch.setattr(
        cli,
        "from_paper_strategy_cycle_report_db_env",
        lambda: _source_db_config(enabled=False, dsn=None),
    )
    monkeypatch.setattr(cli, "load_paper_strategy_cycle_reports_with_psycopg", forbidden_loader)

    assert _run_main([COMMAND]) == 1
    assert load_calls == 0
    captured = capsys.readouterr()
    assert "strategy-cycle-history-gate failed:" in captured.err
    assert "requires paper strategy cycle report DB to be enabled" in captured.err


def test_strategy_cycle_history_gate_fails_before_db_work_when_source_dsn_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    load_calls = 0

    def forbidden_loader(*_args: object, **_kwargs: object) -> object:
        nonlocal load_calls
        load_calls += 1
        raise AssertionError("source DB should not be read")

    monkeypatch.setattr(
        cli,
        "from_paper_strategy_cycle_report_db_env",
        lambda: _source_db_config(enabled=True, dsn=None),
    )
    monkeypatch.setattr(cli, "load_paper_strategy_cycle_reports_with_psycopg", forbidden_loader)

    assert _run_main([COMMAND]) == 1
    assert load_calls == 0
    captured = capsys.readouterr()
    assert "strategy-cycle-history-gate failed:" in captured.err
    assert cli.PAPER_STRATEGY_CYCLE_REPORT_DB_DSN_ENV_VAR in captured.err


def test_strategy_cycle_history_gate_accepts_only_planned_cli_arguments(
    capsys: pytest.CaptureFixture[str],
) -> None:
    tree = _parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)

    assert _parser_argument_surface(tree, parser_variable) == {
        "--source-config-version",
        "source_config_version",
        "--limit",
        "limit",
        "--persist",
        "persist",
    }

    for forbidden_flag in (
        "--dsn",
        "--table",
        "--source-dsn",
        "--source-table",
        "--gate-dsn",
        "--gate-table",
    ):
        with pytest.raises(SystemExit) as exc_info:
            main([COMMAND, forbidden_flag, "forbidden"])
        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "unrecognized arguments" in captured.err


def test_strategy_cycle_history_gate_reads_newest_first_reverses_and_prints_summary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    newest = SimpleNamespace(name="newest")
    older = SimpleNamespace(name="older")
    calls = _install_successful_gate_pipeline(
        monkeypatch,
        source_reports=(newest, older),
    )
    monkeypatch.setattr(
        cli,
        "from_paper_strategy_cycle_report_db_env",
        lambda: _source_db_config(),
    )

    assert (
        _run_main(
            [
                COMMAND,
                "--source-config-version",
                "strategy-cycle-v1",
                "--limit",
                "2",
            ],
        )
        == 0
    )

    assert calls["loaded"] == [
        (SOURCE_DSN, "strategy-cycle-v1", 2, SOURCE_TABLE),
    ]
    history_reports = calls["history_reports"]
    assert len(history_reports) == 1
    assert history_reports[0][0] == (older, newest)
    gate_reports = calls["gate_reports"]
    assert len(gate_reports) == 1
    assert gate_reports[0][0].history_status == "pass"
    assert calls["sink"] == []
    captured = capsys.readouterr()
    assert captured.out == (
        "strategy-cycle-history-gate: status=pass "
        "source_history_status=pass reports=2 "
        "latest_snapshot_ready_share=0.250000 "
        "blocked_market_share=0.125000 persisted=false\n"
    )


@pytest.mark.parametrize(
    ("gate_config", "expected"),
    (
        (
            _gate_db_config(enabled=False, dsn=None),
            "requires strategy cycle history gate DB to be enabled",
        ),
        (
            _gate_db_config(enabled=True, dsn=None),
            "POLYMARKET_ALPHA_LAB_STRATEGY_CYCLE_HISTORY_GATE_DB_DSN",
        ),
    ),
)
def test_strategy_cycle_history_gate_persist_requires_gate_db_env_and_dsn(
    gate_config: SimpleNamespace,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _install_successful_gate_pipeline(monkeypatch)
    monkeypatch.setattr(
        cli,
        "from_paper_strategy_cycle_report_db_env",
        lambda: _source_db_config(),
    )
    monkeypatch.setattr(
        cli,
        "_from_paper_strategy_cycle_report_history_gate_db_env",
        lambda: gate_config,
        raising=False,
    )

    assert _run_main([COMMAND, "--persist"]) == 1
    assert calls["sink"] == []
    captured = capsys.readouterr()
    assert "strategy-cycle-history-gate failed:" in captured.err
    assert expected in captured.err


def test_strategy_cycle_history_gate_persist_writes_report_and_prints_persisted_true(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _install_successful_gate_pipeline(monkeypatch)
    monkeypatch.setattr(
        cli,
        "from_paper_strategy_cycle_report_db_env",
        lambda: _source_db_config(),
    )
    monkeypatch.setattr(
        cli,
        "_from_paper_strategy_cycle_report_history_gate_db_env",
        lambda: _gate_db_config(),
        raising=False,
    )

    assert _run_main([COMMAND, "--persist"]) == 0

    assert len(calls["sink"]) == 1
    sink_dsn, sink_report, sink_table = calls["sink"][0]
    assert sink_dsn == GATE_DSN
    assert sink_report.gate_status == "pass"
    assert sink_table == GATE_TABLE
    captured = capsys.readouterr()
    assert captured.out.endswith("persisted=true\n")


def test_strategy_cycle_history_gate_redacts_source_read_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def broken_loader(
        _dsn: str,
        *,
        config_version: str | None,
        limit: int,
        table_name: str,
    ) -> object:
        raise RuntimeError(
            f"read failed dsn={SOURCE_DSN} table={table_name} "
            f"config={config_version} limit={limit}",
        )

    monkeypatch.setattr(
        cli,
        "from_paper_strategy_cycle_report_db_env",
        lambda: _source_db_config(),
    )
    monkeypatch.setattr(cli, "load_paper_strategy_cycle_reports_with_psycopg", broken_loader)

    assert _run_main([COMMAND]) == 1
    captured = capsys.readouterr()
    assert SOURCE_DSN not in captured.err
    assert SOURCE_TABLE not in captured.err
    assert "<redacted-dsn>" in captured.err
    assert "<redacted-table>" in captured.err


def test_strategy_cycle_history_gate_redacts_gate_write_failures(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    calls = _install_successful_gate_pipeline(monkeypatch)

    def broken_sink(*, dsn: str, report: object, table_name: str) -> object:
        calls["sink"].append((dsn, report, table_name))
        raise RuntimeError(
            f"write failed source={SOURCE_DSN} source_table={SOURCE_TABLE} "
            f"gate={dsn} gate_table={table_name}",
        )

    monkeypatch.setattr(
        cli,
        "from_paper_strategy_cycle_report_db_env",
        lambda: _source_db_config(),
    )
    monkeypatch.setattr(
        cli,
        "_from_paper_strategy_cycle_report_history_gate_db_env",
        lambda: _gate_db_config(),
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "_insert_paper_strategy_cycle_report_history_gate_report_with_psycopg",
        broken_sink,
        raising=False,
    )

    assert _run_main([COMMAND, "--persist"]) == 1
    captured = capsys.readouterr()
    assert SOURCE_DSN not in captured.err
    assert GATE_DSN not in captured.err
    assert SOURCE_TABLE not in captured.err
    assert GATE_TABLE not in captured.err
    assert captured.err.count("<redacted-dsn>") >= 2
    assert captured.err.count("<redacted-table>") >= 2
