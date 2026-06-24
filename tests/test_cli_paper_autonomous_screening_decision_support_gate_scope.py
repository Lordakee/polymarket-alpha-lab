from __future__ import annotations

import importlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

from polymarket_alpha_lab import cli
from polymarket_alpha_lab.cli import main
from polymarket_alpha_lab.supabase_action_gated_strategy_recommendation_queue_decision_support_config import (
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
    ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_project_screening_rank_stability_config import (
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR,
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR,
    PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_autonomous_screening_decision_support_gate_config import (
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
    PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR,
)
from polymarket_alpha_lab.supabase_paper_research_packet_operator_flow_config import (
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR,
    PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
)


COMMAND = "paper-autonomous-screening-decision-support-gate"
PERSIST_COMMAND = "paper-autonomous-screening-decision-support-gate-persist"
GATE_CONFIG_VERSION = "paper-autonomous-screening-decision-support-gate-v0"
GATE_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate"
)
GATE_LOADER_MODULE = (
    "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_load"
)


def _set_upstream_db_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    rank_stability_dsn: str | None = None,
    rank_stability_table_name: str = "paper_project_screening_rank_stability_reports",
    operator_flow_dsn: str,
    operator_flow_table_name: str = "paper_research_packet_operator_flow_reports",
    action_queue_dsn: str,
    action_queue_table_name: str = (
        "paper_action_gated_queue_decision_support_reports"
    ),
) -> None:
    if rank_stability_dsn is None:
        monkeypatch.delenv(
            PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR,
            raising=False,
        )
        monkeypatch.delenv(
            PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR,
            raising=False,
        )
        monkeypatch.delenv(
            PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR,
            raising=False,
        )
    else:
        monkeypatch.setenv(
            PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_ENABLED_ENV_VAR,
            "true",
        )
        monkeypatch.setenv(
            PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_DSN_ENV_VAR,
            rank_stability_dsn,
        )
        monkeypatch.setenv(
            PAPER_PROJECT_SCREENING_RANK_STABILITY_DB_TABLE_ENV_VAR,
            rank_stability_table_name,
        )
    monkeypatch.setenv(PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR, "true")
    monkeypatch.setenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
        operator_flow_dsn,
    )
    monkeypatch.setenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_TABLE_ENV_VAR,
        operator_flow_table_name,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        action_queue_dsn,
    )
    monkeypatch.setenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_TABLE_ENV_VAR,
        action_queue_table_name,
    )


def _set_gate_db_env(
    monkeypatch: pytest.MonkeyPatch,
    *,
    dsn: str,
    table_name: str = "paper_autonomous_screening_decision_support_gate_reports",
) -> None:
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
        "true",
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
        dsn,
    )
    monkeypatch.setenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_TABLE_ENV_VAR,
        table_name,
    )


def _install_or_get_gate_api(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    try:
        return importlib.import_module(GATE_MODULE)
    except ModuleNotFoundError as exc:
        if exc.name != GATE_MODULE:
            raise

    module = ModuleType(GATE_MODULE)
    module.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION = (
        GATE_CONFIG_VERSION
    )
    monkeypatch.setitem(sys.modules, GATE_MODULE, module)
    return module


def _install_gate_loader(
    monkeypatch: pytest.MonkeyPatch,
    load_paper_autonomous_screening_decision_support_gate_report: object,
) -> None:
    module = ModuleType(GATE_LOADER_MODULE)
    module.load_paper_autonomous_screening_decision_support_gate_report = (
        load_paper_autonomous_screening_decision_support_gate_report
    )
    monkeypatch.setitem(sys.modules, GATE_LOADER_MODULE, module)


def _count(gate_signal: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(gate_signal=gate_signal, report_count=report_count)


def _reason_count(reason_code: str, report_count: int) -> SimpleNamespace:
    return SimpleNamespace(reason_code=reason_code, report_count=report_count)


def _gate_report() -> SimpleNamespace:
    return SimpleNamespace(
        generated_at=datetime(2026, 6, 23, 14, 0, tzinfo=UTC),
        config_version=GATE_CONFIG_VERSION,
        gate_status="watch",
        recommended_next_step="throttle_paper_autonomous_screening_decision_support",
        queue_source_report_count=2,
        gate_signal_counts=(
            _count("pass", 1),
            _count("watch", 1),
            _count("blocked", 0),
        ),
        reason_code_counts=(
            _reason_count("rank_stability_watch", 1),
            _reason_count("operator_flow_gate_pass", 1),
        ),
        operator_flow_gate_status="pass",
        queue_risk_status="watch",
        queue_research_ready_count=3,
        trend_source_snapshot_count=2,
        rank_stability_status="watch",
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def test_gate_cli_requires_enabled_operator_flow_db_before_runner_or_client(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        operator_flow_dsn="postgresql://operator-flow.example.invalid/db",
        action_queue_dsn="postgresql://action-queue.example.invalid/db",
    )
    monkeypatch.delenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    client_factory_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper autonomous screening gate runner should not run")

    def forbidden_client_factory() -> object:
        nonlocal client_factory_calls
        client_factory_calls += 1
        raise AssertionError("client should not be constructed")

    exit_code = main(
        [COMMAND],
        paper_autonomous_screening_decision_support_gate_runner=forbidden_runner,
        client_factory=forbidden_client_factory,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert client_factory_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{COMMAND} requires paper research packet operator-flow DB to be enabled"
        in captured.err
    )


def test_gate_persist_cli_uses_injected_runner_sink_and_prints_persistence_marker(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://screening-gate.example.invalid/db"
    table_name = "paper_autonomous_screening_decision_support_gate_reports"
    _set_upstream_db_env(
        monkeypatch,
        operator_flow_dsn=dsn,
        action_queue_dsn=dsn,
    )
    _set_gate_db_env(monkeypatch, dsn=dsn, table_name=table_name)
    report = _gate_report()
    runner_calls: list[dict[str, object]] = []
    sink_calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: Any) -> object:
        runner_calls.append(dict(kwargs))
        return report

    def fake_sink(**kwargs: Any) -> object:
        sink_calls.append(dict(kwargs))
        return SimpleNamespace(inserted=True)

    exit_code = main(
        [PERSIST_COMMAND, "--limit", "9"],
        paper_autonomous_screening_decision_support_gate_runner=fake_runner,
        paper_autonomous_screening_decision_support_gate_db_sink=fake_sink,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(runner_calls) == 1
    assert runner_calls[0]["operator_flow_dsn"] == dsn
    assert runner_calls[0]["action_queue_dsn"] == dsn
    assert runner_calls[0]["limit"] == 9
    assert len(sink_calls) == 1
    assert sink_calls[0] == {
        "dsn": dsn,
        "report": report,
        "table_name": table_name,
    }
    captured = capsys.readouterr()
    assert f"{PERSIST_COMMAND}: persisted=True" in captured.out
    assert "gate_status=watch" in captured.out
    assert captured.err == ""
    assert dsn not in captured.out
    assert table_name not in captured.out


def test_gate_persist_cli_requires_enabled_gate_db_before_runner_or_sink(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dsn = "postgresql://screening-gate.example.invalid/db"
    _set_upstream_db_env(
        monkeypatch,
        operator_flow_dsn=dsn,
        action_queue_dsn=dsn,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_DB_DSN_ENV_VAR,
        raising=False,
    )
    runner_calls = 0
    sink_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper autonomous screening gate runner should not run")

    def forbidden_sink(**kwargs: Any) -> object:
        nonlocal sink_calls
        sink_calls += 1
        raise AssertionError("screening gate DB sink should not run")

    exit_code = main(
        [PERSIST_COMMAND],
        paper_autonomous_screening_decision_support_gate_runner=forbidden_runner,
        paper_autonomous_screening_decision_support_gate_db_sink=forbidden_sink,
    )

    assert exit_code == 1
    assert runner_calls == 0
    assert sink_calls == 0
    captured = capsys.readouterr()
    assert f"{PERSIST_COMMAND} failed:" in captured.err
    assert f"{PERSIST_COMMAND} requires autonomous screening gate DB to be enabled" in (
        captured.err
    )


def test_gate_cli_requires_enabled_action_queue_decision_support_db(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        operator_flow_dsn="postgresql://operator-flow.example.invalid/db",
        action_queue_dsn="postgresql://action-queue.example.invalid/db",
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_ENABLED_ENV_VAR,
        raising=False,
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        raising=False,
    )

    def forbidden_runner(**kwargs: Any) -> object:
        raise AssertionError("paper autonomous screening gate runner should not run")

    exit_code = main(
        [COMMAND],
        paper_autonomous_screening_decision_support_gate_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert (
        f"{COMMAND} requires action-gated queue decision-support DB to be enabled"
        in captured.err
    )


def test_gate_cli_requires_operator_flow_dsn_when_operator_flow_db_is_enabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        operator_flow_dsn="postgresql://operator-flow.example.invalid/db",
        action_queue_dsn="postgresql://action-queue.example.invalid/db",
    )
    monkeypatch.delenv(
        PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR,
        raising=False,
    )

    def forbidden_runner(**kwargs: Any) -> object:
        raise AssertionError("paper autonomous screening gate runner should not run")

    exit_code = main(
        [COMMAND],
        paper_autonomous_screening_decision_support_gate_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert PAPER_RESEARCH_PACKET_OPERATOR_FLOW_DB_DSN_ENV_VAR in captured.err
    assert "must be set when DB is enabled" in captured.err


def test_gate_cli_requires_action_queue_dsn_when_decision_support_db_is_enabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _set_upstream_db_env(
        monkeypatch,
        operator_flow_dsn="postgresql://operator-flow.example.invalid/db",
        action_queue_dsn="postgresql://action-queue.example.invalid/db",
    )
    monkeypatch.delenv(
        ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR,
        raising=False,
    )

    def forbidden_runner(**kwargs: Any) -> object:
        raise AssertionError("paper autonomous screening gate runner should not run")

    exit_code = main(
        [COMMAND],
        paper_autonomous_screening_decision_support_gate_runner=forbidden_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert ACTION_GATED_QUEUE_DECISION_SUPPORT_DB_DSN_ENV_VAR in captured.err
    assert "must be set when DB is enabled" in captured.err


@pytest.mark.parametrize("limit", ("0", "-1"))
def test_gate_cli_rejects_non_positive_limit_before_env_runner_or_connect(
    limit: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    env_calls = 0
    runner_calls = 0
    connect_calls = 0

    def forbidden_env() -> object:
        nonlocal env_calls
        env_calls += 1
        raise AssertionError("upstream DB env should not be read")

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper autonomous screening gate runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("upstream DB connect should not run")

    monkeypatch.setattr(
        cli,
        "from_paper_project_screening_rank_stability_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "from_paper_research_packet_operator_flow_db_env",
        forbidden_env,
        raising=False,
    )
    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    exit_code = main(
        [COMMAND, "--limit", limit],
        paper_autonomous_screening_decision_support_gate_runner=forbidden_runner,
    )

    assert exit_code == 1
    assert env_calls == 0
    assert runner_calls == 0
    assert connect_calls == 0
    captured = capsys.readouterr()
    assert f"{COMMAND} failed: {COMMAND} limit must be positive" in captured.err


@pytest.mark.parametrize("bad_limit", (0, -1, True, "1", 1.0))
def test_gate_helper_rejects_invalid_limit_before_runner_or_connect(
    bad_limit: object,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner_calls = 0
    connect_calls = 0

    def forbidden_runner(**kwargs: Any) -> object:
        nonlocal runner_calls
        runner_calls += 1
        raise AssertionError("paper autonomous screening gate runner should not run")

    def forbidden_connect(*args: Any, **kwargs: Any) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("upstream DB connect should not run")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))
    helper = getattr(cli, "_run_paper_autonomous_screening_decision_support_gate")

    with pytest.raises(ValueError, match=f"{COMMAND} limit must be positive"):
        helper(
            rank_stability_dsn="postgresql://rank-stability.example.invalid/db",
            rank_stability_table_name="paper_project_screening_rank_stability_reports",
        operator_flow_dsn="postgresql://operator-flow.example.invalid/db",
        operator_flow_table_name="paper_research_packet_operator_flow_reports",
        action_queue_dsn="postgresql://action-queue.example.invalid/db",
        action_queue_table_name=(
            "paper_action_gated_queue_decision_support_reports"
        ),
        limit=bad_limit,
        runner=forbidden_runner,
    )

    assert runner_calls == 0
    assert connect_calls == 0


def test_gate_cli_omits_rank_stability_inputs_when_rank_db_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_gate_api(monkeypatch)
    operator_flow_dsn = "postgresql://shared-gate.example.invalid/db"
    action_queue_dsn = "postgresql://shared-gate.example.invalid/db"
    _set_upstream_db_env(
        monkeypatch,
        operator_flow_dsn=operator_flow_dsn,
        action_queue_dsn=action_queue_dsn,
    )
    calls: list[dict[str, object]] = []

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert "rank_stability_dsn" not in kwargs
        assert "rank_stability_table_name" not in kwargs
        assert kwargs["operator_flow_dsn"] == operator_flow_dsn
        assert kwargs["action_queue_dsn"] == action_queue_dsn
        return _gate_report()

    exit_code = main(
        [COMMAND],
        paper_autonomous_screening_decision_support_gate_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.err == ""


def test_gate_cli_scope_uses_only_injected_gate_runner_and_readonly_configs(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    gate_api = _install_or_get_gate_api(monkeypatch)
    rank_stability_dsn = "postgresql://operator-flow-gate.example.invalid/db"
    rank_stability_table_name = "paper_project_screening_rank_stability_reports"
    operator_flow_dsn = "postgresql://operator-flow-gate.example.invalid/db"
    operator_flow_table_name = "paper_research_packet_operator_flow_reports"
    action_queue_dsn = "postgresql://action-queue-gate.example.invalid/db"
    action_queue_table_name = (
        "paper_action_gated_queue_decision_support_reports"
    )
    _set_upstream_db_env(
        monkeypatch,
        rank_stability_dsn=rank_stability_dsn,
        rank_stability_table_name=rank_stability_table_name,
        operator_flow_dsn=operator_flow_dsn,
        operator_flow_table_name=operator_flow_table_name,
        action_queue_dsn=action_queue_dsn,
        action_queue_table_name=action_queue_table_name,
    )
    calls: list[dict[str, object]] = []
    dangerous_calls: list[str] = []

    def forbidden(name: str) -> object:
        dangerous_calls.append(name)
        raise AssertionError(f"{name} should not be called")

    def fake_runner(**kwargs: Any) -> object:
        calls.append(dict(kwargs))
        assert kwargs["rank_stability_dsn"] == rank_stability_dsn
        assert kwargs["rank_stability_table_name"] == rank_stability_table_name
        assert kwargs["operator_flow_dsn"] == operator_flow_dsn
        assert kwargs["operator_flow_table_name"] == operator_flow_table_name
        assert kwargs["action_queue_dsn"] == action_queue_dsn
        assert kwargs["action_queue_table_name"] == action_queue_table_name
        assert kwargs["limit"] == 25
        gate_config = kwargs["gate_config"]
        assert (
            gate_config.config_version
            == gate_api.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
        )
        assert gate_config.paper_only is True
        assert gate_config.report_only is True
        assert gate_config.readonly is True
        generated_at = kwargs["generated_at"]
        assert isinstance(generated_at, datetime)
        assert generated_at.tzinfo is UTC
        return _gate_report()

    exit_code = main(
        [COMMAND],
        runner=lambda **kwargs: forbidden("market_scan"),
        cycle_runner=lambda **kwargs: forbidden("strategy_cycle"),
        nav_runner=lambda **kwargs: forbidden("portfolio_nav"),
        loop_runner=lambda **kwargs: forbidden("strategy_loop"),
        outcome_runner=lambda **kwargs: forbidden("outcome_tracking"),
        paper_trade_record_db_sink=lambda **kwargs: forbidden("paper_trade_sink"),
        paper_nav_snapshot_db_sink=lambda **kwargs: forbidden("nav_snapshot_sink"),
        strategy_risk_audit_db_sink=lambda **kwargs: forbidden("risk_audit_sink"),
        paper_research_packet_builder=lambda **kwargs: forbidden("packet_builder"),
        paper_research_packet_db_sink=lambda **kwargs: forbidden("packet_sink"),
        paper_research_packet_operator_flow_db_sink=(
            lambda **kwargs: forbidden("operator_flow_sink")
        ),
        paper_autonomous_screening_decision_support_gate_runner=fake_runner,
        client_factory=lambda: forbidden("client_factory"),
    )

    assert exit_code == 0
    assert len(calls) == 1
    assert dangerous_calls == []
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: gate_status=watch "
            "recommended_next_step="
            "throttle_paper_autonomous_screening_decision_support "
            "source_report_count=2 "
            "operator_flow_gate_status=pass "
            "queue_risk_status=watch "
            "queue_research_ready_count=3 "
            "trend_present=True "
            "rank_stability_present=True"
        ),
        "gate_signal_counts: pass=1 watch=1 blocked=0",
        "reason_code_counts: rank_stability_watch=1 operator_flow_gate_pass=1",
    ]
    assert captured.err == ""
    for secret in (
        rank_stability_dsn,
        rank_stability_table_name,
        operator_flow_dsn,
        operator_flow_table_name,
        action_queue_dsn,
        action_queue_table_name,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


def test_gate_cli_prints_real_gate_report_shape_without_extra_payload(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    rank_stability_dsn = "postgresql://rank-stability-gate.example.invalid/db"
    operator_flow_dsn = "postgresql://operator-flow-gate.example.invalid/db"
    action_queue_dsn = "postgresql://action-queue-gate.example.invalid/db"
    _set_upstream_db_env(
        monkeypatch,
        rank_stability_dsn=rank_stability_dsn,
        operator_flow_dsn=operator_flow_dsn,
        action_queue_dsn=action_queue_dsn,
    )

    def fake_runner(**kwargs: Any) -> object:
        return SimpleNamespace(
            gate_status="watch",
            recommended_next_step=(
                "throttle_paper_autonomous_screening_recommendations"
            ),
            operator_flow_gate_status="pass",
            queue_risk_status="watch",
            queue_research_ready_count=5,
            trend_latest_risk_status="blocked",
            trend_source_snapshot_count=3,
            rank_stability_status="stable",
            reason_code_counts=(
                _reason_count("queue_risk_watch", 1),
                _reason_count(
                    "queue_decision_support_trend_latest_risk_blocked",
                    1,
                ),
            ),
            paper_only=True,
            report_only=True,
            readonly=True,
        )

    exit_code = main(
        [COMMAND, "--limit", "9"],
        paper_autonomous_screening_decision_support_gate_runner=fake_runner,
        client_factory=lambda: (_ for _ in ()).throw(
            AssertionError("client should not be constructed"),
        ),
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out.splitlines() == [
        (
            f"{COMMAND}: gate_status=watch "
            "recommended_next_step="
            "throttle_paper_autonomous_screening_recommendations "
            "operator_flow_gate_status=pass "
            "queue_risk_status=watch "
            "queue_research_ready_count=5 "
            "trend_present=True "
            "rank_stability_present=True"
        ),
        "gate_signal_counts: pass=2 watch=1 blocked=1",
        (
            "reason_code_counts: queue_risk_watch=1 "
            "queue_decision_support_trend_latest_risk_blocked=1"
        ),
    ]
    assert "payload" not in captured.out
    assert "dsn" not in captured.out


def test_gate_helper_default_load_path_uses_autocommit_and_closes_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate_api = _install_or_get_gate_api(monkeypatch)
    operator_flow_dsn = "postgresql://operator-flow-gate.example.invalid/db"
    rank_stability_dsn = operator_flow_dsn
    rank_stability_table_name = "paper_project_screening_rank_stability_reports"
    operator_flow_table_name = "paper_research_packet_operator_flow_reports"
    action_queue_dsn = operator_flow_dsn
    action_queue_table_name = (
        "paper_action_gated_queue_decision_support_reports"
    )
    report = _gate_report()
    connect_calls: list[tuple[str, bool]] = []
    loader_calls: list[dict[str, object]] = []

    class FakeConnection:
        def __init__(self, name: str) -> None:
            self.name = name
            self.close_count = 0
            self.commit_count = 0
            self.rollback_count = 0

        def commit(self) -> None:
            self.commit_count += 1
            raise AssertionError("read-only helper must not commit")

        def rollback(self) -> None:
            self.rollback_count += 1
            raise AssertionError("read-only helper must not rollback")

        def close(self) -> None:
            self.close_count += 1

    operator_connection = FakeConnection("operator")

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        connect_calls.append((connect_dsn, autocommit))
        if connect_dsn == operator_flow_dsn:
            return operator_connection
        raise AssertionError(f"unexpected dsn {connect_dsn}")

    def fake_load(
        connection: object,
        **kwargs: object,
    ) -> object:
        loader_calls.append({"connection": connection, **kwargs})
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_gate_loader(monkeypatch, fake_load)

    helper = getattr(cli, "_run_paper_autonomous_screening_decision_support_gate")
    result = helper(
        rank_stability_dsn=rank_stability_dsn,
        rank_stability_table_name=rank_stability_table_name,
        operator_flow_dsn=operator_flow_dsn,
        operator_flow_table_name=operator_flow_table_name,
        action_queue_dsn=action_queue_dsn,
        action_queue_table_name=action_queue_table_name,
        limit=11,
        runner=None,
    )

    assert result is report
    assert connect_calls == [(operator_flow_dsn, True)]
    assert len(loader_calls) == 1
    assert loader_calls[0]["connection"] is operator_connection
    assert loader_calls[0]["operator_flow_history_limit"] == 11
    assert loader_calls[0]["project_screening_rank_stability_limit"] == 11
    assert loader_calls[0]["action_gated_queue_limit"] == 11
    assert (
        loader_calls[0]["project_screening_rank_stability_table_name"]
        == rank_stability_table_name
    )
    assert loader_calls[0]["operator_flow_table_name"] == operator_flow_table_name
    assert loader_calls[0]["action_gated_queue_table_name"] == action_queue_table_name
    gate_config = loader_calls[0]["gate_config"]
    assert (
        gate_config.config_version
        == gate_api.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
    )
    generated_at = loader_calls[0]["generated_at"]
    assert isinstance(generated_at, datetime)
    assert generated_at.tzinfo is UTC
    assert operator_connection.commit_count == 0
    assert operator_connection.rollback_count == 0
    assert operator_connection.close_count == 1


def test_gate_helper_default_load_path_omits_rank_loader_when_rank_db_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_gate_api(monkeypatch)
    shared_dsn = "postgresql://shared-gate.example.invalid/db"
    operator_flow_table_name = "paper_research_packet_operator_flow_reports"
    action_queue_table_name = (
        "paper_action_gated_queue_decision_support_reports"
    )
    report = _gate_report()
    loader_calls: list[dict[str, object]] = []

    class FakeConnection:
        def close(self) -> None:
            pass

    def fake_connect(connect_dsn: str, *, autocommit: bool = False) -> FakeConnection:
        assert connect_dsn == shared_dsn
        assert autocommit is True
        return FakeConnection()

    def fake_load(connection: object, **kwargs: object) -> object:
        loader_calls.append({"connection": connection, **kwargs})
        return report

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=fake_connect))
    _install_gate_loader(monkeypatch, fake_load)

    helper = getattr(cli, "_run_paper_autonomous_screening_decision_support_gate")
    result = helper(
        rank_stability_dsn=None,
        rank_stability_table_name=None,
        operator_flow_dsn=shared_dsn,
        operator_flow_table_name=operator_flow_table_name,
        action_queue_dsn=shared_dsn,
        action_queue_table_name=action_queue_table_name,
        limit=7,
        runner=None,
    )

    assert result is report
    assert len(loader_calls) == 1
    assert "project_screening_rank_stability_limit" not in loader_calls[0]
    assert "project_screening_rank_stability_table_name" not in loader_calls[0]
    assert "project_screening_rank_stability_config_version" not in loader_calls[0]
    assert "project_screening_rank_stability_status" not in loader_calls[0]


def test_gate_helper_default_load_path_requires_required_db_dsns_to_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_or_get_gate_api(monkeypatch)
    connect_calls = 0

    def forbidden_connect(*args: object, **kwargs: object) -> object:
        nonlocal connect_calls
        connect_calls += 1
        raise AssertionError("upstream DB connect should not run")

    monkeypatch.setitem(sys.modules, "psycopg", SimpleNamespace(connect=forbidden_connect))

    helper = getattr(cli, "_run_paper_autonomous_screening_decision_support_gate")
    with pytest.raises(
        RuntimeError,
        match=(
            "requires operator-flow and action-gated queue decision-support "
            "DB DSNs to use the same DSN"
        ),
    ):
        helper(
            rank_stability_dsn=None,
            rank_stability_table_name=None,
            operator_flow_dsn="postgresql://operator-flow.example.invalid/db",
            operator_flow_table_name="paper_research_packet_operator_flow_reports",
            action_queue_dsn="postgresql://action-queue.example.invalid/db",
            action_queue_table_name=(
                "paper_action_gated_queue_decision_support_reports"
            ),
            limit=7,
            runner=None,
        )

    assert connect_calls == 0


def test_gate_cli_runner_failure_redacts_dsns_tables_and_payloads(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_or_get_gate_api(monkeypatch)
    rank_stability_dsn = "postgresql://rank-stability-secret.example.invalid/db"
    rank_stability_table_name = "paper_project_screening_rank_stability_reports"
    operator_flow_dsn = "postgresql://operator-flow-secret.example.invalid/db"
    operator_flow_table_name = "paper_research_packet_operator_flow_reports"
    action_queue_dsn = "postgresql://action-queue-secret.example.invalid/db"
    action_queue_table_name = (
        "paper_action_gated_queue_decision_support_reports"
    )
    payload_json = '{"secret":"autonomous-screening-gate-payload-secret"}'
    colon_payload_json = (
        '{"secret":"autonomous-screening-gate-colon-payload-secret"}'
    )
    json_key_payload_json = (
        '{"secret":"autonomous-screening-gate-json-key-payload-secret"}'
    )
    question = "Will hidden autonomous screening market resolve yes?"
    colon_question = "Will colon hidden autonomous screening market resolve yes?"
    json_key_question = "Will JSON key hidden autonomous screening market resolve yes?"
    report_sha256 = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    bare_sha256 = "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
    _set_upstream_db_env(
        monkeypatch,
        rank_stability_dsn=rank_stability_dsn,
        rank_stability_table_name=rank_stability_table_name,
        operator_flow_dsn=operator_flow_dsn,
        operator_flow_table_name=operator_flow_table_name,
        action_queue_dsn=action_queue_dsn,
        action_queue_table_name=action_queue_table_name,
    )

    def broken_runner(**kwargs: Any) -> object:
        raise RuntimeError(
            f"read failed rank_dsn={rank_stability_dsn} "
            f"rank_table={rank_stability_table_name} "
            f"operator_dsn={operator_flow_dsn} "
            f"operator_table={operator_flow_table_name} "
            f"action_queue_dsn={action_queue_dsn} "
            f"action_queue_table={action_queue_table_name} "
            f"payload_json={payload_json} question={question} "
            f"payload_json: {colon_payload_json} question: {colon_question} "
            f'"payload_json": {json_key_payload_json} '
            f'"question": "{json_key_question}" '
            f"report_sha256={report_sha256} bare_hash={bare_sha256}",
        )

    exit_code = main(
        [COMMAND],
        paper_autonomous_screening_decision_support_gate_runner=broken_runner,
    )

    assert exit_code == 1
    captured = capsys.readouterr()
    assert f"{COMMAND} failed:" in captured.err
    assert "rank_dsn=<redacted-dsn>" in captured.err
    assert "rank_table=<redacted-table>" in captured.err
    assert "operator_dsn=<redacted-dsn>" in captured.err
    assert "operator_table=<redacted-table>" in captured.err
    assert "action_queue_dsn=<redacted-dsn>" in captured.err
    assert "action_queue_table=<redacted-table>" in captured.err
    assert "payload_json=<redacted-payload>" in captured.err
    assert "question=<redacted-question>" in captured.err
    assert "report_sha256=<redacted-sha256>" in captured.err
    assert "bare_hash=<redacted-sha256>" in captured.err
    for secret in (
        rank_stability_dsn,
        rank_stability_table_name,
        operator_flow_dsn,
        operator_flow_table_name,
        action_queue_dsn,
        action_queue_table_name,
        "paper_project_screening_rank_stability_reports",
        "paper_research_packet_operator_flow_reports",
        "paper_action_gated_queue_decision_support_reports",
        payload_json,
        "autonomous-screening-gate-payload-secret",
        colon_payload_json,
        "autonomous-screening-gate-colon-payload-secret",
        json_key_payload_json,
        "autonomous-screening-gate-json-key-payload-secret",
        question,
        colon_question,
        json_key_question,
        report_sha256,
        bare_sha256,
    ):
        assert secret not in captured.out
        assert secret not in captured.err


@pytest.mark.parametrize(
    "argv",
    (
        [COMMAND, "--dsn", "postgresql://autonomous-gate.example.invalid/db"],
        [COMMAND, "--table", "paper_autonomous_screening_gate_reports"],
        [COMMAND, "--persist"],
        [COMMAND, "--source-limit", "1"],
        [COMMAND, "--require-decision-support-trend"],
        [COMMAND, "--require-rank-stability"],
        [COMMAND, "--max-source-age-seconds", "86400"],
    ),
)
def test_gate_cli_rejects_dsn_table_and_persist_flags(
    argv: list[str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err


def test_gate_docs_and_plan_describe_current_env_only_limit_cli_contract() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    operator_doc = Path(
        "docs/paper-autonomous-screening-decision-support-gate.md",
    ).read_text(encoding="utf-8")
    plan = Path(
        "docs/superpowers/plans/"
        "2026-06-23-paper-autonomous-screening-decision-support-gate.md",
    ).read_text(encoding="utf-8")

    assert f"{COMMAND} --limit" in readme
    assert f"{COMMAND} --limit" in operator_doc
    assert "operator-flow DB" in readme
    assert "action-gated queue decision-support DB" in readme
    assert "rank-stability DB is optional" in readme
    assert "operator-flow DB" in operator_doc
    assert "action-gated queue decision-support DB" in operator_doc
    assert "rank-stability DB is optional" in operator_doc
    assert "same DSN" in operator_doc
    assert "read-only env-only CLI" in plan
    assert "`--limit`" in plan
    task_5 = plan.split("### Task 5: CLI Process Boundary", 1)[1].split(
        "### Task 6:",
        1,
    )[0]
    for unsupported_flag in (
        "`--persist`",
        "`--require-decision-support-trend`",
        "`--require-rank-stability`",
        "`--max-source-age-seconds`",
        "`--source-limit`",
    ):
        assert unsupported_flag not in task_5


def test_autonomous_gate_package_root_exports_match_actual_public_api() -> None:
    import polymarket_alpha_lab as lab
    from polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate import (
        DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION,
        PaperAutonomousScreeningDecisionSupportGateReasonCodeCount,
        PaperAutonomousScreeningDecisionSupportGateReport,
        build_paper_autonomous_screening_decision_support_gate_report,
    )

    expected_exports = {
        "DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION",
        "PaperAutonomousScreeningDecisionSupportGateReasonCodeCount",
        "PaperAutonomousScreeningDecisionSupportGateReport",
        "build_paper_autonomous_screening_decision_support_gate_report",
    }
    forbidden_exports = {
        "PaperAutonomousScreeningDecisionSupportGateConfig",
        "PaperAutonomousScreeningDecisionSupportGateRunner",
        "_PaperAutonomousScreeningDecisionSupportGateConfig",
    }

    assert expected_exports <= set(lab.__all__)
    assert not (forbidden_exports & set(lab.__all__))
    assert (
        lab.DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
        is DEFAULT_PAPER_AUTONOMOUS_SCREENING_DECISION_SUPPORT_GATE_CONFIG_VERSION
    )
    assert (
        lab.PaperAutonomousScreeningDecisionSupportGateReasonCodeCount
        is PaperAutonomousScreeningDecisionSupportGateReasonCodeCount
    )
    assert (
        lab.PaperAutonomousScreeningDecisionSupportGateReport
        is PaperAutonomousScreeningDecisionSupportGateReport
    )
    assert (
        lab.build_paper_autonomous_screening_decision_support_gate_report
        is build_paper_autonomous_screening_decision_support_gate_report
    )
    for name in forbidden_exports:
        assert not hasattr(lab, name)
