from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_cost_thresholds"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "candidate_decision_cost_thresholds.py"
)


class DecimalSubclass(Decimal):
    pass


class StringSubclass(str):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing cost-threshold helper module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": module.DEFAULT_CANDIDATE_DECISION_COST_THRESHOLDS_VERSION,
        "min_net_edge_for_watch": d("0.000000"),
        "min_net_edge_for_research_more": d("0.005000"),
        "min_net_edge_for_paper_recommend": d("0.015000"),
        "transaction_cost_buffer": d("0.002000"),
        "settlement_cash_lockup_buffer": d("0.001000"),
        "model_uncertainty_buffer": d("0.002000"),
    }
    values.update(overrides)
    return module.CandidateDecisionCostThresholdConfig(**values)


def threshold_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "redacted_candidate_ref": "redacted_candidate_cost_threshold_001",
        "redacted_market_ref": "redacted_market_cost_threshold_001",
        "selected_side": "yes",
        "gross_edge": d("0.045000"),
        "taker_fee_drag": d("0.003000"),
        "spread_cost": d("0.010000"),
        "slippage": d("0.004000"),
        "settlement_cash_lockup_drag": d("0.003000"),
        "source_reason_codes": ("z_source", "a_source"),
    }
    values.update(overrides)
    return module.CandidateDecisionCostThresholdInput(**values)


def evaluate(subject: object | None = None, cfg: object | None = None) -> Any:
    module = api()
    return module.evaluate_candidate_decision_cost_thresholds(
        threshold_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_transaction_cost_drag_and_buffers_convert_to_safe_threshold_fields() -> None:
    module = api()
    result = evaluate()

    assert is_dataclass(result)
    assert type(result) is module.CandidateDecisionCostThresholdOutput
    assert result.redacted_candidate_ref == "redacted_candidate_cost_threshold_001"
    assert result.redacted_market_ref == "redacted_market_cost_threshold_001"
    assert result.selected_side == "yes"
    assert result.gross_edge == d("0.045000")
    assert result.taker_fee_drag == d("0.003000")
    assert result.spread_cost == d("0.010000")
    assert result.slippage == d("0.004000")
    assert result.transaction_cost_drag == d("0.017000")
    assert result.settlement_cash_lockup_drag == d("0.003000")
    assert result.total_cost_drag == d("0.020000")
    assert result.total_buffer_drag == d("0.005000")
    assert result.net_edge_before_buffers == d("0.025000")
    assert result.net_edge_after_buffers == d("0.020000")
    assert result.required_gross_edge_for_watch == d("0.025000")
    assert result.required_gross_edge_for_research_more == d("0.030000")
    assert result.required_gross_edge_for_paper_recommend == d("0.040000")
    assert result.action == "paper_recommend"
    assert result.hard_safety_flags == (
        "paper_only",
        "report_only",
        "readonly",
        "execution_disabled",
    )
    assert result.reason_codes == (
        "candidate_decision_cost_thresholds_paper_recommend",
        "a_source",
        "buffer_drag_applied",
        "candidate_cost_thresholds_v0",
        "net_edge_clears_paper_recommend_threshold",
        "settlement_cash_lockup_drag_applied",
        "transaction_cost_drag_applied",
        "z_source",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert result.candidate_decision_fields == {
        "action": "paper_recommend",
        "gross_edge": d("0.045000"),
        "transaction_cost_drag": d("0.017000"),
        "settlement_cash_lockup_drag": d("0.003000"),
        "total_cost_drag": d("0.020000"),
        "total_buffer_drag": d("0.005000"),
        "net_edge_before_buffers": d("0.025000"),
        "net_edge_after_buffers": d("0.020000"),
        "required_gross_edge_for_paper_recommend": d("0.040000"),
        "reason_codes": result.reason_codes,
        "hard_safety_flags": result.hard_safety_flags,
    }
    assert module.cost_thresholds_to_candidate_decision_fields(result) == (
        result.candidate_decision_fields
    )


def test_settlement_cash_lockup_penalty_changes_guidance_without_changing_txn_costs() -> None:
    low_lockup = evaluate(
        threshold_input(
            gross_edge=d("0.040000"),
            settlement_cash_lockup_drag=d("0.000000"),
        ),
    )
    high_lockup = evaluate(
        threshold_input(
            gross_edge=d("0.040000"),
            settlement_cash_lockup_drag=d("0.010000"),
        ),
    )

    assert low_lockup.transaction_cost_drag == high_lockup.transaction_cost_drag
    assert low_lockup.total_cost_drag == d("0.017000")
    assert low_lockup.net_edge_after_buffers == d("0.018000")
    assert low_lockup.action == "paper_recommend"
    assert high_lockup.total_cost_drag == d("0.027000")
    assert high_lockup.net_edge_after_buffers == d("0.008000")
    assert high_lockup.action == "research_more"
    assert "settlement_cash_lockup_drag_applied" in high_lockup.reason_codes


def test_threshold_transitions_are_deterministic_at_configured_boundaries() -> None:
    cases = (
        ("0.024999", "reject"),
        ("0.025000", "watch"),
        ("0.029999", "watch"),
        ("0.030000", "research_more"),
        ("0.039999", "research_more"),
        ("0.040000", "paper_recommend"),
    )

    for gross_edge, expected_action in cases:
        result = evaluate(threshold_input(gross_edge=d(gross_edge)))
        assert result.action == expected_action


def test_negative_unsafe_and_inconsistent_values_are_rejected() -> None:
    module = api()
    result = evaluate()

    for field_name in (
        "taker_fee_drag",
        "spread_cost",
        "slippage",
        "settlement_cash_lockup_drag",
    ):
        with pytest.raises(ValueError, match=field_name):
            threshold_input(**{field_name: d("-0.000001")})

    with pytest.raises(ValueError, match="transaction_cost_buffer"):
        config(transaction_cost_buffer=d("-0.000001"))
    with pytest.raises(ValueError, match="min_net_edge_for_paper_recommend"):
        config(
            min_net_edge_for_watch=d("0.010000"),
            min_net_edge_for_research_more=d("0.020000"),
            min_net_edge_for_paper_recommend=d("0.015000"),
        )
    with pytest.raises(ValueError, match="payload contains unsafe text"):
        threshold_input(redacted_candidate_ref="redacted_wallet_probe")
    with pytest.raises(ValueError, match="redacted_candidate_ref must be redacted"):
        threshold_input(redacted_candidate_ref="candidate-cost-threshold-001")
    with pytest.raises(ValueError, match="source_reason_codes must be unique"):
        threshold_input(source_reason_codes=("a_source", "a_source"))
    with pytest.raises(ValueError, match="source_reason_codes"):
        threshold_input(source_reason_codes=("candidate_decision_watch",))
    with pytest.raises(ValueError, match="config must be"):
        module.evaluate_candidate_decision_cost_thresholds(threshold_input(), config=object())
    with pytest.raises(ValueError, match="input_value must be"):
        module.evaluate_candidate_decision_cost_thresholds(object(), config=config())
    with pytest.raises(ValueError, match="total_cost_drag"):
        replace(result, total_cost_drag=d("0.021000"))
    with pytest.raises(ValueError, match="action"):
        replace(result, action="watch")
    with pytest.raises(ValueError, match="paper_only"):
        replace(result, paper_only=False)
    with pytest.raises(FrozenInstanceError):
        result.action = "watch"  # type: ignore[misc]


def test_no_floats_decimal_only_payload_and_deterministic_reason_ordering() -> None:
    module = api()
    first = evaluate(
        threshold_input(
            gross_edge=d("0.045000"),
            source_reason_codes=("z_source", "a_source"),
        ),
    )
    second = evaluate(
        threshold_input(
            gross_edge=d("0.045000"),
            source_reason_codes=("a_source", "z_source"),
        ),
    )

    assert first == second
    assert first.reason_codes == second.reason_codes
    payload = module.candidate_decision_cost_threshold_payload(first)
    assert payload["gross_edge"] == "0.045000"
    assert payload["transaction_cost_drag"] == "0.017000"
    assert payload["total_cost_drag"] == "0.020000"
    assert payload["net_edge_after_buffers"] == "0.020000"
    assert payload["reason_codes"] == list(first.reason_codes)
    assert payload["hard_safety_flags"] == list(first.hard_safety_flags)
    assert "candidate_id" not in payload
    assert "market_id" not in payload
    assert_no_float_values(payload)

    for instance in (config(), threshold_input(), first):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) in (bool, str, tuple):
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="gross_edge must be a Decimal"):
        threshold_input(gross_edge=0.045)
    with pytest.raises(ValueError, match="taker_fee_drag must be a Decimal"):
        threshold_input(taker_fee_drag=DecimalSubclass("0.003000"))
    with pytest.raises(ValueError, match="redacted_candidate_ref must be a string"):
        threshold_input(
            redacted_candidate_ref=StringSubclass(
                "redacted_candidate_cost_threshold_001",
            ),
        )
    with pytest.raises(ValueError, match="payload must be"):
        module.candidate_decision_cost_threshold_payload(object())


def test_pure_boundary_exports_and_source_guard() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_COST_THRESHOLDS_VERSION",
        "BOUNDARY_STATEMENT",
        "CandidateDecisionCostThresholdConfig",
        "CandidateDecisionCostThresholdInput",
        "CandidateDecisionCostThresholdOutput",
        "evaluate_candidate_decision_cost_thresholds",
        "cost_thresholds_to_candidate_decision_fields",
        "candidate_decision_cost_threshold_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for banned in (
        "requests",
        "httpx",
        "urllib",
        "websocket",
        "socket",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "subprocess",
        "click",
        "argparse",
        "open(",
        ".write(",
        "private_key",
        "wallet",
        "account",
        "auth",
        "balance",
        "place_order",
        "create_order",
        "cancel_order",
        "exchange",
        "live_trading",
        "os.",
        "environ",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"eval", "exec", "float", "open"}
