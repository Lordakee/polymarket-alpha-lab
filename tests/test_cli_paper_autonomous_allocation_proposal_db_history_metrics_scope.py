from __future__ import annotations

import ast
import builtins
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"
COMMAND = "paper-autonomous-allocation-proposal-db-history-metrics"
METRICS_CONFIG_VERSION = "paper-autonomous-allocation-proposal-db-history-metrics-v0"
METRICS_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics"
)
RUN_HELPER = "_run_paper_autonomous_allocation_proposal_db_history_metrics"
SUMMARY_PRINTER = (
    "_print_paper_autonomous_allocation_proposal_db_history_metrics_summary"
)


def _install_metrics_api_stub_for_package_import() -> None:
    if METRICS_MODULE in sys.modules:
        return

    module = ModuleType(METRICS_MODULE)

    @dataclass(frozen=True)
    class PaperAutonomousAllocationProposalDbHistoryMetricsConfig:
        config_version: str = METRICS_CONFIG_VERSION
        paper_only: bool = True
        report_only: bool = True
        readonly: bool = True

    class PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow:
        pass

    class PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow:
        pass

    class PaperAutonomousAllocationProposalDbHistoryMetricsReport:
        pass

    class PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary:
        pass

    def build_paper_autonomous_allocation_proposal_db_history_metrics_report(
        *_args: object,
        **_kwargs: object,
    ) -> object:
        raise AssertionError("metrics reducer should not run in CLI tests")

    module.PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow = (
        PaperAutonomousAllocationProposalDbHistoryMetricsCapReasonRow
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConcentrationRow
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsConfig = (
        PaperAutonomousAllocationProposalDbHistoryMetricsConfig
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsReport = (
        PaperAutonomousAllocationProposalDbHistoryMetricsReport
    )
    module.PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary = (
        PaperAutonomousAllocationProposalDbHistoryMetricsSnapshotSummary
    )
    module.build_paper_autonomous_allocation_proposal_db_history_metrics_report = (
        build_paper_autonomous_allocation_proposal_db_history_metrics_report
    )
    sys.modules[METRICS_MODULE] = module


_install_metrics_api_stub_for_package_import()

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main

EXPECTED_PARSER_ARGUMENT_SURFACE = {
    "--limit",
    "limit",
}

FORBIDDEN_PARSER_ARGUMENT_SURFACE = {
    "--dsn",
    "dsn",
    "--db-dsn",
    "db_dsn",
    "--table",
    "table",
    "--db-table",
    "db_table",
    "--persist",
    "persist",
    "--paper-autonomous-allocation-proposal-db-dsn",
    "paper_autonomous_allocation_proposal_db_dsn",
    "--paper-autonomous-allocation-proposal-db-table",
    "paper_autonomous_allocation_proposal_db_table",
    "--paper-autonomous-allocation-proposal-db-enabled",
    "paper_autonomous_allocation_proposal_db_enabled",
    "--live",
    "live",
    "--execute",
    "execute",
    "--trade",
    "trade",
    "--auth",
    "auth",
    "--wallet",
    "wallet",
    "--private-key",
    "private_key",
    "--api-key",
    "api_key",
    "--account",
    "account",
    "--order",
    "order",
    "--submit",
    "submit",
    "--approve",
    "approve",
    "--fast",
    "fast",
}

RUNTIME_FORBIDDEN_FLAGS = (
    "--account",
    "--api-key",
    "--approve",
    "--auth",
    "--db-dsn",
    "--db-table",
    "--dsn",
    "--execute",
    "--fast",
    "--live",
    "--order",
    "--paper-autonomous-allocation-proposal-db-dsn",
    "--paper-autonomous-allocation-proposal-db-table",
    "--persist",
    "--private-key",
    "--submit",
    "--table",
    "--trade",
    "--wallet",
)

FORBIDDEN_RAW_FRAGMENTS = {
    "account",
    "approve",
    "cancel_order",
    "httpx",
    "private_key",
    "replace_order",
    "requests",
    "socket",
    "submit_order",
    "subprocess",
    "supabase",
    "trade",
    "urllib",
    "wallet",
}

ALLOWED_RUN_HELPER_IMPORTS = {
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics",
    "polymarket_alpha_lab.paper_autonomous_allocation_proposal_db_history_metrics_load",
    "psycopg",
}

SUMMARY_REQUIRED_FIELDS = {
    "source_report_count",
    "latest_proposal_status",
    "latest_budget_utilization",
    "latest_requested_fill_ratio",
    "latest_total_allocated_paper_notional",
    "latest_largest_market_share",
    "latest_added_market_side_count",
    "latest_removed_market_side_count",
    "latest_notional_turnover",
    "latest_allocated_edge_share",
    "latest_expected_edge_notional",
}

SUMMARY_FORBIDDEN_DETAIL_FRAGMENTS = {
    "account",
    "hash",
    "key",
    "market_question",
    "market_slug",
    "order",
    "payload",
    "question",
    "sha256",
    "table",
    "trade",
    "wallet",
}


def parse_cli() -> ast.AST:
    return ast.parse(CLI_PATH.read_text(encoding="utf-8"), filename=str(CLI_PATH))


def call_or_attribute_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return call_or_attribute_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_command_literal(node: ast.AST, command: str) -> bool:
    return isinstance(node, ast.Constant) and node.value == command


def _command_parser_variable(tree: ast.AST, command: str) -> str:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        if call_or_attribute_name(value.func) != "add_parser":
            continue
        if value.args and _is_command_literal(value.args[0], command):
            return target.id
    raise AssertionError(f"parser variable for {command} not found")


def _parser_call(tree: ast.AST, command: str) -> ast.Call:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_or_attribute_name(node.func) != "add_parser":
            continue
        if node.args and _is_command_literal(node.args[0], command):
            return node
    raise AssertionError(f"parser call for {command} not found")


def _literal_arg(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _explicit_dest(node: ast.Call) -> str | None:
    for keyword in node.keywords:
        if keyword.arg == "dest":
            return _literal_arg(keyword.value)
    return None


def _derived_argparse_dest(option_strings: tuple[str, ...]) -> str | None:
    long_options = [option for option in option_strings if option.startswith("--")]
    if not long_options:
        return None
    return long_options[0][2:].replace("-", "_")


def _parser_argument_surface(tree: ast.AST, parser_variable: str) -> set[str]:
    surface: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_or_attribute_name(node.func) != "add_argument":
            continue
        if not isinstance(node.func, ast.Attribute):
            continue
        receiver = node.func.value
        if not isinstance(receiver, ast.Name) or receiver.id != parser_variable:
            continue
        option_strings = tuple(
            value
            for value in (_literal_arg(argument) for argument in node.args)
            if value is not None
        )
        surface.update(option_strings)
        dest = _explicit_dest(node) or _derived_argparse_dest(option_strings)
        if dest is not None:
            surface.add(dest)
    return surface


def _function_def(tree: ast.AST, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} function not found")


def _string_literals(node: ast.AST) -> set[str]:
    return {
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    }


def _imports_inside(node: ast.AST) -> set[str]:
    imports: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Import):
            imports.update(alias.name for alias in child.names)
        elif isinstance(child, ast.ImportFrom) and child.module is not None:
            imports.add(child.module)
    return imports


def _normalized_source(node: ast.AST) -> str:
    return ast.unparse(node).replace("-", "_").lower()


def test_metrics_command_parser_is_readonly_limit_only_and_rejects_abbrev() -> None:
    tree = parse_cli()
    parser_variable = _command_parser_variable(tree, COMMAND)
    parser_call = _parser_call(tree, COMMAND)
    allow_abbrev_keywords = [
        keyword
        for keyword in parser_call.keywords
        if keyword.arg == "allow_abbrev"
    ]

    assert len(allow_abbrev_keywords) == 1
    assert isinstance(allow_abbrev_keywords[0].value, ast.Constant)
    assert allow_abbrev_keywords[0].value.value is False
    assert _parser_argument_surface(tree, parser_variable) == (
        EXPECTED_PARSER_ARGUMENT_SURFACE
    )
    assert not (
        _parser_argument_surface(tree, parser_variable)
        & FORBIDDEN_PARSER_ARGUMENT_SURFACE
    )


@pytest.mark.parametrize("flag", RUNTIME_FORBIDDEN_FLAGS)
def test_metrics_command_rejects_forbidden_flags_before_env_runner_or_connect(
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
        raise AssertionError("metrics runner should not run")

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
        "from_paper_autonomous_allocation_proposal_db_env",
        forbidden_env,
    )
    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    with pytest.raises(SystemExit) as exc_info:
        main(
            [COMMAND, flag, "forbidden-value"],
            paper_autonomous_allocation_proposal_db_history_metrics_runner=(
                forbidden_runner
            ),
        )

    assert exc_info.value.code == 2
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    assert psycopg_import_calls == 0
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_metrics_command_rejects_abbreviated_limit_flag_before_env_runner_or_connect(
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
        raise AssertionError("metrics runner should not run")

    monkeypatch.setattr(
        cli,
        "from_paper_autonomous_allocation_proposal_db_env",
        forbidden_env,
    )

    with pytest.raises(SystemExit) as exc_info:
        main(
            [COMMAND, "--lim", "7"],
            paper_autonomous_allocation_proposal_db_history_metrics_runner=(
                forbidden_runner
            ),
        )

    assert exc_info.value.code == 2
    assert env_calls == 0
    assert runner_calls == 0
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_metrics_run_helper_imports_only_reducer_loader_and_psycopg() -> None:
    tree = parse_cli()
    run_helper = _function_def(tree, RUN_HELPER)

    assert _imports_inside(run_helper) == ALLOWED_RUN_HELPER_IMPORTS


def test_metrics_command_branch_has_no_raw_network_trade_or_secret_dependencies() -> None:
    tree = parse_cli()
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if COMMAND not in _string_literals(node.test):
            continue
        source = _normalized_source(node)
        for forbidden in FORBIDDEN_RAW_FRAGMENTS:
            assert forbidden not in source
        return
    raise AssertionError(f"{COMMAND} branch not found")


def test_metrics_summary_printer_only_mentions_approved_aggregate_fields() -> None:
    tree = parse_cli()
    printer = _function_def(tree, SUMMARY_PRINTER)
    literals = _string_literals(printer)

    for field in SUMMARY_REQUIRED_FIELDS:
        assert any(
            literal == field or literal.startswith(f"{field}=")
            for literal in literals
        ), field
    assert not any(
        forbidden in literal
        for literal in literals
        for forbidden in SUMMARY_FORBIDDEN_DETAIL_FRAGMENTS
    )


def test_metrics_summary_prints_only_aggregate_fields_and_none_largest_market_share(
    capsys: pytest.CaptureFixture[str],
) -> None:
    report = SimpleNamespace(
        generated_at=datetime(2026, 6, 24, 13, 0, tzinfo=UTC),
        config_version="paper-autonomous-allocation-proposal-db-history-metrics-v0",
        source_report_count=4,
        latest_proposal_status="watch",
        latest_budget_utilization="0.750000",
        latest_requested_fill_ratio="0.500000",
        latest_total_allocated_paper_notional="125.000000",
        latest_largest_concentration_rows=(
            SimpleNamespace(kind="side", share="0.800000"),
        ),
        latest_added_market_side_count=2,
        latest_removed_market_side_count=1,
        latest_notional_turnover="33.250000",
        latest_allocated_edge_share="0.875000",
        latest_expected_edge_notional="12.500000",
        dsn="postgresql://secret.example.invalid/db",
        table_name="analytics.paper_autonomous_allocation_proposal_reports",
        payload_json={"market_slug": "secret-market-slug"},
        report_sha256=(
            "abcdef0123456789abcdef0123456789"
            "abcdef0123456789abcdef0123456789"
        ),
        market_slug="secret-market-slug",
        market_question="Will hidden allocation proposal market resolve yes?",
        wallet="secret-wallet",
        account="secret-account",
        private_key="secret-key",
        order="secret-order",
        trade="secret-trade",
        paper_only=True,
        report_only=True,
        readonly=True,
    )

    printer = getattr(cli, SUMMARY_PRINTER)
    printer(report)

    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: source_report_count=4 latest_proposal_status=watch "
            "latest_budget_utilization=0.750000 "
            "latest_requested_fill_ratio=0.500000 "
            "latest_total_allocated_paper_notional=125.000000 "
            "latest_largest_market_share=none "
            "latest_added_market_side_count=2 "
            "latest_removed_market_side_count=1 "
            "latest_notional_turnover=33.250000 "
            "latest_allocated_edge_share=0.875000 "
            "latest_expected_edge_notional=12.500000"
        ),
    ]
    assert captured.err == ""
    for forbidden in (
        "postgresql://secret.example.invalid/db",
        "analytics.paper_autonomous_allocation_proposal_reports",
        "payload_json",
        "secret-market-slug",
        "report_sha256",
        "market_slug",
        "market_question",
        "Will hidden allocation proposal market resolve yes?",
        "wallet",
        "secret-wallet",
        "account",
        "secret-account",
        "private_key",
        "secret-key",
        "order",
        "secret-order",
        "trade",
        "secret-trade",
    ):
        assert forbidden not in captured.out
        assert forbidden not in captured.err
