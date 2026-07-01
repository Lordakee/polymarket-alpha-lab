from __future__ import annotations

import importlib
from typing import Any

import pytest


LOCAL_DSN = "postgresql://postgres:postgres@localhost:54322/postgres"


TRANSACTIONAL_MODULES = (
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_psycopg",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_decision_support_trend_psycopg",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_history_psycopg",
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg",
    "polymarket_alpha_lab.local_observability_trends_psycopg",
    "polymarket_alpha_lab.outcome_tracking_psycopg",
    "polymarket_alpha_lab.paper_nav_snapshot_psycopg",
    "polymarket_alpha_lab.paper_recommendation_consistency_psycopg",
    "polymarket_alpha_lab.paper_probability_recommendation_queue_psycopg",
    "polymarket_alpha_lab.paper_recommendation_health_psycopg",
    "polymarket_alpha_lab.paper_recommendation_reason_trend_health_psycopg",
    "polymarket_alpha_lab.paper_recommendation_cycle_snapshot_psycopg",
    "polymarket_alpha_lab.paper_strategy_cycle_report_psycopg",
    "polymarket_alpha_lab.paper_recommendation_reason_trend_psycopg",
    "polymarket_alpha_lab.paper_recommendation_risk_budget_psycopg",
    "polymarket_alpha_lab.paper_trade_cost_audit_psycopg",
    "polymarket_alpha_lab.paper_trade_journal_psycopg",
    "polymarket_alpha_lab.strategy_candidate_research_queue_history_psycopg",
    "polymarket_alpha_lab.strategy_candidate_research_queue_psycopg",
    "polymarket_alpha_lab.strategy_recommendation_rank_stability_psycopg",
    "polymarket_alpha_lab.strategy_recommendation_reason_trend_psycopg",
    "polymarket_alpha_lab.strategy_risk_audit_psycopg",
    "polymarket_alpha_lab.team_forecast_psycopg",
)

READ_ONLY_MODULES = (
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg_read",
    "polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read",
)

ASSIGNED_TRANSACTIONAL_HELPERS = (
    (
        "polymarket_alpha_lab.autonomous_market_scorer_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_investment_ledger_db_history_health_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_readiness_digest_psycopg",
        "_with_owned_write_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_readiness_gate_psycopg",
        "_with_owned_write_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_psycopg",
        "_with_owned_write_connection",
    ),
    (
        "polymarket_alpha_lab.paper_execution_reconciliation_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_order_lifecycle_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_recommendation_quality_history_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_recommendation_quality_summary_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_recommendation_readiness_psycopg",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate_psycopg",
        "_with_owned_write_connection",
    ),
)

ASSIGNED_READ_ONLY_HELPERS = (
    (
        "polymarket_alpha_lab.paper_autonomous_allocation_proposal_psycopg_read",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_readiness_digest_psycopg",
        "_with_owned_read_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_readiness_gate_psycopg",
        "_with_owned_read_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_transition_psycopg",
        "_with_owned_read_connection",
    ),
    (
        "polymarket_alpha_lab.paper_autonomous_screening_decision_support_gate_psycopg_read",
        "_with_owned_connection",
    ),
    (
        "polymarket_alpha_lab.paper_strategy_cycle_report_history_gate_psycopg",
        "_with_owned_read_connection",
    ),
)

ASSIGNED_SUCCESS_CLOSE_HELPERS = (
    *(
        (module_name, helper_name, True)
        for module_name, helper_name in ASSIGNED_TRANSACTIONAL_HELPERS
    ),
    *(
        (module_name, helper_name, False)
        for module_name, helper_name in ASSIGNED_READ_ONLY_HELPERS
    ),
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


class FakeJsonb:
    def __init__(self, value: Any) -> None:
        self.value = value


def _module(module_name: str) -> Any:
    return importlib.import_module(module_name)


def _install_owned_connection_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    module: Any,
    connection: FakeConnection,
) -> None:
    monkeypatch.setattr(module, "_connect", lambda dsn, **kwargs: connection)
    if hasattr(module, "_jsonb_adapter"):
        monkeypatch.setattr(module, "_jsonb_adapter", lambda: FakeJsonb)


def _call_owned_helper(
    module: Any,
    helper_name: str,
    operation: Any,
) -> Any:
    return getattr(module, helper_name)(LOCAL_DSN, operation)


@pytest.mark.parametrize("module_name", TRANSACTIONAL_MODULES)
def test_transactional_psycopg_adapter_cleanup_does_not_mask_store_exception(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_rollback=True, fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    def fail_operation(connection_arg: Any) -> None:
        raise ValueError("store failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        module._with_owned_connection(LOCAL_DSN, fail_operation)

    assert str(exc_info.value) == "store failed without dsn"
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("module_name", TRANSACTIONAL_MODULES)
def test_transactional_psycopg_adapter_cleanup_does_not_mask_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_commit=True, fail_rollback=True, fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    with pytest.raises(RuntimeError) as exc_info:
        module._with_owned_connection(
            LOCAL_DSN,
            lambda connection_arg: "ok",
        )

    assert str(exc_info.value) == "commit failed without dsn"
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize("module_name", TRANSACTIONAL_MODULES)
def test_transactional_psycopg_adapter_success_close_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    with pytest.raises(RuntimeError, match="close failed without dsn"):
        module._with_owned_connection(
            LOCAL_DSN,
            lambda connection_arg: "ok",
        )

    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.close_count == 1


@pytest.mark.parametrize(("module_name", "helper_name"), ASSIGNED_TRANSACTIONAL_HELPERS)
def test_assigned_transactional_psycopg_adapter_cleanup_does_not_mask_store_exception(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    helper_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_rollback=True, fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    def fail_operation(connection_arg: Any) -> None:
        raise ValueError("store failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        _call_owned_helper(module, helper_name, fail_operation)

    assert str(exc_info.value) == "store failed without dsn"
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize(("module_name", "helper_name"), ASSIGNED_TRANSACTIONAL_HELPERS)
def test_assigned_transactional_psycopg_adapter_cleanup_does_not_mask_commit_exception(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    helper_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_commit=True, fail_rollback=True, fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    with pytest.raises(RuntimeError) as exc_info:
        _call_owned_helper(
            module,
            helper_name,
            lambda connection_arg: "ok",
        )

    assert str(exc_info.value) == "commit failed without dsn"
    assert connection.commit_count == 1
    assert connection.rollback_count == 1
    assert connection.close_count == 1


@pytest.mark.parametrize(
    ("module_name", "helper_name", "commits"),
    ASSIGNED_SUCCESS_CLOSE_HELPERS,
)
def test_assigned_psycopg_adapter_success_close_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    helper_name: str,
    commits: bool,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    with pytest.raises(RuntimeError, match="close failed without dsn"):
        _call_owned_helper(
            module,
            helper_name,
            lambda connection_arg: "ok",
        )

    assert connection.commit_count == (1 if commits else 0)
    assert connection.rollback_count == 0
    assert connection.close_count == 1


@pytest.mark.parametrize("module_name", READ_ONLY_MODULES)
def test_read_only_psycopg_adapter_close_does_not_mask_operation_exception(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    def fail_operation(connection_arg: Any) -> None:
        raise ValueError("read failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        module._with_owned_connection(LOCAL_DSN, fail_operation)

    assert str(exc_info.value) == "read failed without dsn"
    assert connection.close_count == 1


@pytest.mark.parametrize("module_name", READ_ONLY_MODULES)
def test_read_only_psycopg_adapter_success_close_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    with pytest.raises(RuntimeError, match="close failed without dsn"):
        module._with_owned_connection(
            LOCAL_DSN,
            lambda connection_arg: "ok",
        )

    assert connection.close_count == 1


@pytest.mark.parametrize(("module_name", "helper_name"), ASSIGNED_READ_ONLY_HELPERS)
def test_assigned_read_only_psycopg_adapter_close_does_not_mask_operation_exception(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    helper_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    def fail_operation(connection_arg: Any) -> None:
        raise ValueError("read failed without dsn")

    with pytest.raises(ValueError) as exc_info:
        _call_owned_helper(module, helper_name, fail_operation)

    assert str(exc_info.value) == "read failed without dsn"
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.close_count == 1
