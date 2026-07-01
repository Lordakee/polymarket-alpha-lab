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
)

READ_ONLY_MODULES = (
    "polymarket_alpha_lab.action_gated_strategy_recommendation_queue_psycopg_read",
    "polymarket_alpha_lab.strategy_candidate_research_queue_psycopg_read",
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
    monkeypatch.setattr(module, "_connect", lambda dsn: connection)
    if hasattr(module, "_jsonb_adapter"):
        monkeypatch.setattr(module, "_jsonb_adapter", lambda: FakeJsonb)


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
def test_transactional_psycopg_adapter_close_failure_does_not_replace_success(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    result = module._with_owned_connection(
        LOCAL_DSN,
        lambda connection_arg: "ok",
    )

    assert result == "ok"
    assert connection.commit_count == 1
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
def test_read_only_psycopg_adapter_close_failure_does_not_replace_success(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
) -> None:
    module = _module(module_name)
    connection = FakeConnection(fail_close=True)
    _install_owned_connection_dependencies(monkeypatch, module, connection)

    result = module._with_owned_connection(
        LOCAL_DSN,
        lambda connection_arg: "ok",
    )

    assert result == "ok"
    assert connection.close_count == 1
