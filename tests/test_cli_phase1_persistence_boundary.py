from __future__ import annotations

import ast
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import polymarket_alpha_lab.cli as cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.strategy_cycle import PaperStrategyCycleReport


REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_PATH = REPO_ROOT / "src" / "polymarket_alpha_lab" / "cli.py"

PAPER_DB_ENV_VARS = (
    "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_PAPER_STRATEGY_CYCLE_REPORT_DB_DSN",
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_PAPER_TRADE_JOURNAL_DB_DSN",
    "POLYMARKET_ALPHA_LAB_PAPER_NAV_SNAPSHOT_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_PAPER_NAV_SNAPSHOT_DB_DSN",
    "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_CYCLE_SNAPSHOT_DB_DSN",
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_ACTION_GATED_QUEUE_DB_DSN",
    "POLYMARKET_ALPHA_LAB_PAPER_EXECUTION_PIPELINE_DB_ENABLED",
    "POLYMARKET_ALPHA_LAB_PAPER_EXECUTION_PIPELINE_DB_DSN",
)

LOCAL_DB_ENV_FUNCTIONS = {
    "from_action_gated_strategy_recommendation_queue_db_env",
    "from_action_gated_strategy_recommendation_queue_decision_support_db_env",
    "from_action_gated_strategy_recommendation_queue_decision_support_trend_db_env",
    "from_action_gated_strategy_recommendation_queue_history_db_env",
    "from_autonomous_market_scorer_db_env",
    "from_cycle_snapshot_db_env",
    "from_local_observability_trends_db_env",
    "from_outcome_tracking_db_env",
    "from_paper_autonomous_allocation_proposal_db_env",
    "from_paper_autonomous_allocation_proposal_db_history_health_db_env",
    "from_paper_autonomous_investment_ledger_db_env",
    "from_paper_autonomous_investment_ledger_db_history_health_db_env",
    "from_paper_autonomous_readiness_digest_db_env",
    "from_paper_autonomous_readiness_gate_db_env",
    "from_paper_autonomous_screening_decision_support_gate_db_env",
    "from_paper_broker_db_env",
    "from_paper_execution_pipeline_db_env",
    "from_paper_nav_snapshot_db_env",
    "from_paper_probability_recommendation_queue_db_env",
    "from_paper_probability_selection_summary_db_env",
    "from_paper_probability_selection_summary_history_db_env",
    "from_paper_project_screening_rank_stability_db_env",
    "from_paper_recommendation_reason_trend_db_env",
    "from_paper_recommendation_risk_budget_db_env",
    "from_paper_research_packet_db_env",
    "from_paper_research_packet_operator_flow_db_env",
    "from_paper_research_packet_quality_db_env",
    "from_paper_strategy_cycle_report_db_env",
    "from_paper_strategy_cycle_report_history_gate_db_env",
    "from_paper_trade_cost_audit_db_env",
    "from_paper_trade_journal_db_env",
    "from_probability_selection_scorer_agreement_db_env",
    "from_strategy_candidate_research_queue_db_env",
    "from_strategy_candidate_research_queue_history_db_env",
    "from_strategy_risk_audit_db_env",
    "from_team_diagnostics_snapshot_db_env",
    "from_team_research_assignment_db_env",
}

FORBIDDEN_LIVE_TRADING_OPTIONS = {
    "--account",
    "--api-key",
    "--auth",
    "--cancel",
    "--cancel-order",
    "--clob-api-key",
    "--exchange",
    "--live",
    "--live-trading",
    "--market-order",
    "--order",
    "--private-key",
    "--sign",
    "--signing-key",
    "--submit",
    "--submit-order",
    "--trade",
    "--wallet",
}

FORBIDDEN_LIVE_TRADING_DESTS = {
    "account",
    "api_key",
    "auth",
    "cancel",
    "cancel_order",
    "clob_api_key",
    "exchange",
    "live",
    "live_trading",
    "market_order",
    "order",
    "private_key",
    "sign",
    "signing_key",
    "submit",
    "submit_order",
    "trade",
    "wallet",
}


def _parse_cli() -> ast.AST:
    return ast.parse(CLI_PATH.read_text(encoding="utf-8"), filename=str(CLI_PATH))


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_call(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Call) and _call_name(node) == name


def _parser_variables(tree: ast.AST) -> dict[str, str]:
    variables: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not _is_call(node.value, "add_parser"):
            continue
        command = node.value.args[0]
        if isinstance(command, ast.Constant) and isinstance(command.value, str):
            variables[target.id] = command.value
    return variables


def _argparse_dest(option_strings: tuple[str, ...]) -> str | None:
    optional_strings = tuple(option for option in option_strings if option.startswith("-"))
    if not optional_strings:
        return None
    long_options = tuple(option for option in optional_strings if option.startswith("--"))
    return (long_options or optional_strings)[0].lstrip("-").replace("-", "_")


def _keyword_constant(call: ast.Call, keyword_name: str) -> object:
    for keyword in call.keywords:
        if keyword.arg == keyword_name and isinstance(keyword.value, ast.Constant):
            return keyword.value.value
    return None


def _argument_surface(tree: ast.AST) -> tuple[dict[str, set[str]], dict[str, bool]]:
    parser_variables = _parser_variables(tree)
    surfaces = {command: set() for command in parser_variables.values()}
    persist_defaults: dict[str, bool] = {}

    for node in ast.walk(tree):
        if not _is_call(node, "add_argument"):
            continue
        func = node.func
        if (
            not isinstance(func, ast.Attribute)
            or not isinstance(func.value, ast.Name)
            or func.value.id not in parser_variables
        ):
            continue

        command = parser_variables[func.value.id]
        option_strings = tuple(
            arg.value
            for arg in node.args
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str)
        )
        surfaces[command].update(option_strings)

        dest = _keyword_constant(node, "dest") or _argparse_dest(option_strings)
        if isinstance(dest, str):
            surfaces[command].add(dest)

        if "--persist" in option_strings:
            assert _keyword_constant(node, "action") == "store_true"
            persist_defaults[command] = _keyword_constant(node, "default") is False

    return surfaces, persist_defaults


def _main_function(tree: ast.AST) -> ast.FunctionDef:
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "main"
    ]
    assert len(matches) == 1
    return matches[0]


def _is_args_command(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "command"
        and isinstance(node.value, ast.Name)
        and node.value.id == "args"
    )


def _command_test_matches(test: ast.AST, command: str) -> bool:
    if isinstance(test, ast.BoolOp):
        return any(_command_test_matches(value, command) for value in test.values)
    if not isinstance(test, ast.Compare) or len(test.ops) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq) or len(test.comparators) != 1:
        return False
    comparator = test.comparators[0]
    return (
        _is_args_command(test.left)
        and isinstance(comparator, ast.Constant)
        and comparator.value == command
    ) or (
        isinstance(test.left, ast.Constant)
        and test.left.value == command
        and _is_args_command(comparator)
    )


def _command_branch(tree: ast.AST, command: str) -> list[ast.stmt]:
    branches = [
        node.body
        for node in ast.walk(tree)
        if isinstance(node, ast.If) and _command_test_matches(node.test, command)
    ]
    runtime_branches = [
        branch for branch in branches if any(isinstance(stmt, ast.Try) for stmt in branch)
    ]
    if len(runtime_branches) == 1:
        return runtime_branches[0]
    assert len(branches) == 1, (command, len(branches))
    return branches[0]


def _references(nodes: list[ast.stmt]) -> set[str]:
    values: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                values.add(node.name)
            elif isinstance(node, ast.Name):
                values.add(node.id)
            elif isinstance(node, ast.Attribute):
                values.add(node.attr)
            elif isinstance(node, ast.arg):
                values.add(node.arg)
            elif isinstance(node, ast.keyword) and node.arg is not None:
                values.add(node.arg)
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                values.add(node.value)
    return values


def _calls(nodes: list[ast.stmt]) -> set[str]:
    call_names: set[str] = set()
    for statement in nodes:
        for node in ast.walk(statement):
            if isinstance(node, ast.Call):
                name = _call_name(node)
                if name is not None:
                    call_names.add(name)
    return call_names


def _function_default_name(default: ast.AST | None) -> str | None:
    if isinstance(default, ast.Name):
        return default.id
    if isinstance(default, ast.Constant) and default.value is None:
        return None
    return ast.unparse(default) if default is not None else None


def _blank_paper_db_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for env_var in PAPER_DB_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)


def test_cli_argparse_surface_has_no_live_trading_auth_key_or_order_mutation() -> None:
    surfaces, _ = _argument_surface(_parse_cli())
    all_surface_values = set().union(*surfaces.values())

    assert not (all_surface_values & FORBIDDEN_LIVE_TRADING_OPTIONS)
    assert not (all_surface_values & FORBIDDEN_LIVE_TRADING_DESTS)
    assert "--paper-execute" in surfaces["strategy-cycle"]
    assert "--paper-execute" in surfaces["run"]
    assert "paper_execute" in surfaces["strategy-cycle"]
    assert "paper_execute" in surfaces["run"]


def test_main_boundary_does_not_accept_live_auth_private_key_or_order_mutators() -> None:
    main_def = _main_function(_parse_cli())
    defaults_by_kwarg = {
        arg.arg: _function_default_name(default)
        for arg, default in zip(main_def.args.kwonlyargs, main_def.args.kw_defaults)
    }
    forbidden_fragments = (
        "auth",
        "cancel_order",
        "clob",
        "exchange_order",
        "live_trade",
        "order_mutation",
        "private_key",
        "sign_order",
        "submit_order",
        "wallet",
    )
    forbidden_kwargs = tuple(
        name
        for name in defaults_by_kwarg
        if any(fragment in name.lower() for fragment in forbidden_fragments)
    )

    assert forbidden_kwargs == ()
    assert defaults_by_kwarg["client_factory"] == "PolymarketPublicClient"
    allowed_sink_name_fragments = {
        "action_gated_queue",
        "cycle_snapshot",
        "local_observability",
        "outcome_tracking",
        "paper",
        "probability_selection_scorer_agreement",
        "strategy_candidate_research_queue",
        "strategy_cycle_history_gate",
        "strategy_risk_audit",
        "team_diagnostics_snapshot",
        "team_research_assignment",
    }
    assert all(
        any(fragment in name for fragment in allowed_sink_name_fragments)
        for name in defaults_by_kwarg
        if "db_sink" in name or "db_loader" in name or "persister" in name
    )


def test_db_persistence_surface_is_local_paper_report_sink_and_env_config_only() -> None:
    tree = _parse_cli()
    main_refs = _references([_main_function(tree)])
    main_def = _main_function(tree)
    db_kwargs = {
        arg.arg: _function_default_name(default)
        for arg, default in zip(main_def.args.kwonlyargs, main_def.args.kw_defaults)
        if "db_sink" in arg.arg or "db_loader" in arg.arg or "persister" in arg.arg
    }
    local_db_env_refs = {
        ref for ref in main_refs if ref.startswith("from_") and ref.endswith("_env")
    }

    assert local_db_env_refs <= LOCAL_DB_ENV_FUNCTIONS
    assert {
        "from_paper_strategy_cycle_report_db_env",
        "from_paper_trade_journal_db_env",
        "from_paper_nav_snapshot_db_env",
        "from_paper_execution_pipeline_db_env",
    } <= local_db_env_refs
    assert all(
        sink_default is None
        or sink_default.startswith(("insert_paper_", "load_paper_", "_persist_paper_"))
        or sink_default == "insert_outcome_tracking_report_with_psycopg"
        or sink_default == "insert_strategy_risk_audit_report_with_psycopg"
        for sink_default in db_kwargs.values()
    )
    allowed_sink_name_fragments = {
        "action_gated_queue",
        "cycle_snapshot",
        "local_observability",
        "outcome_tracking",
        "paper",
        "probability_selection_scorer_agreement",
        "strategy_candidate_research_queue",
        "strategy_cycle_history_gate",
        "strategy_risk_audit",
        "team_diagnostics_snapshot",
        "team_research_assignment",
    }
    assert all(
        any(fragment in name for fragment in allowed_sink_name_fragments)
        for name in db_kwargs
    )
    assert not {
        "from_exchange_env",
        "from_live_trading_env",
        "from_order_env",
        "from_private_key_env",
        "from_wallet_env",
    } & main_refs


def test_explicit_persist_flags_are_store_true_and_default_off() -> None:
    surfaces, persist_defaults = _argument_surface(_parse_cli())

    assert persist_defaults
    assert all(persist_defaults.values())
    assert set(persist_defaults) == {
        command
        for command, surface in surfaces.items()
        if "--persist" in surface
    }


def test_live_cycle_db_persistence_is_env_gated_and_default_off(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _blank_paper_db_env(monkeypatch)
    calls: list[dict[str, object]] = []

    def fake_cycle_runner(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return PaperStrategyCycleReport(
            generated_at=datetime(2026, 1, 1, tzinfo=UTC),
            config_version="strategy-cycle-v1",
            scan_market_count=0,
            considered_count=0,
            snapshot_ready_count=0,
            cost_aware_report_count=0,
            blocked_counts=(),
            screening_report=None,
        )

    def forbidden_db_sink(**kwargs: object) -> object:
        raise AssertionError(f"DB persistence must be default-off: {kwargs!r}")

    monkeypatch.setattr(cli.PaperStrategyCycleLog, "append", lambda self, report: None)

    exit_code = main(
        [
            "strategy-cycle",
            "--archive-root",
            str(tmp_path / "raw"),
            "--output",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        cycle_runner=fake_cycle_runner,
        client_factory=lambda: "public-client",
        paper_strategy_cycle_report_db_sink=forbidden_db_sink,
        paper_trade_record_db_sink=forbidden_db_sink,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert "paper_trade_record_sink" not in calls[0]


def test_run_db_persistence_is_env_gated_default_off_and_paper_sink_only(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _blank_paper_db_env(monkeypatch)
    calls: list[dict[str, object]] = []

    def fake_loop_runner(**kwargs: object) -> SimpleNamespace:
        calls.append(kwargs)
        return SimpleNamespace(
            iterations_completed=1,
            iterations_failed=0,
            first_iteration_at=datetime(2026, 1, 1, tzinfo=UTC),
            last_iteration_at=datetime(2026, 1, 1, tzinfo=UTC),
            last_error=None,
            nav_marks_skipped=0,
            cycle_snapshots_persisted=0,
            action_gated_queues_persisted=0,
            paper_only=True,
            report_only=True,
        )

    def forbidden_db_sink(**kwargs: object) -> object:
        raise AssertionError(f"DB persistence must be default-off: {kwargs!r}")

    exit_code = main(
        [
            "run",
            "--archive-root",
            str(tmp_path / "raw"),
            "--starting-cash",
            "10000",
            "--cycle-log",
            str(tmp_path / "strategy-cycle.jsonl"),
        ],
        loop_runner=fake_loop_runner,
        client_factory=lambda: "public-client",
        paper_strategy_cycle_report_db_sink=forbidden_db_sink,
        paper_trade_record_db_sink=forbidden_db_sink,
        paper_nav_snapshot_db_sink=forbidden_db_sink,
        cycle_snapshot_db_sink=forbidden_db_sink,
        action_gated_queue_db_sink=forbidden_db_sink,
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert calls[0]["cycle_report_sink"] is None
    assert calls[0]["cycle_snapshot_source"] is None
    assert calls[0]["cycle_snapshot_sink"] is None
    assert calls[0]["paper_trade_record_sink"] is None
    assert calls[0]["paper_trade_record_source"] is None
    assert calls[0]["nav_snapshot_sink"] is None


def test_persistence_branches_are_explicitly_gated_by_env_or_persist() -> None:
    tree = _parse_cli()
    branch_expectations = {
        "strategy-cycle": {
            "from_paper_strategy_cycle_report_db_env",
            "from_paper_trade_journal_db_env",
        },
        "run": {
            "from_paper_strategy_cycle_report_db_env",
            "from_paper_trade_journal_db_env",
            "from_paper_nav_snapshot_db_env",
            "from_paper_execution_pipeline_db_env",
        },
        "paper-autonomous-readiness-digest": {
            "from_paper_autonomous_readiness_digest_db_env",
            "persist",
        },
        "paper-probability-selection-summary-history": {
            "from_paper_probability_selection_summary_history_db_env",
            "persist",
        },
    }

    for command, expected_refs in branch_expectations.items():
        branch = _command_branch(tree, command)
        refs = _references(branch)
        call_names = _calls(branch)
        assert expected_refs <= refs
        assert not {
            "auth",
            "private_key",
            "submit_order",
            "cancel_order",
            "wallet",
        } & refs
        assert not {"submit_order", "cancel_order", "sign_order"} & call_names
