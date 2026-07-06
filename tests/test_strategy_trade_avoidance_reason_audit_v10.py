from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_trade_avoidance_reason_audit_v10"


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": module.DEFAULT_STRATEGY_AVOIDANCE_REASON_AUDIT_V10_CONFIG_VERSION,
        "minimum_edge_score": d("0.550000"),
        "maximum_cost_drag_score": d("0.450000"),
        "clear_recheck_minutes": d("30.000000"),
        "review_recheck_minutes": d("120.000000"),
        "avoid_recheck_minutes": d("480.000000"),
    }
    values.update(overrides)
    return module.StrategyAvoidanceReasonAuditV10Config(**values)


def candidate(**overrides: object) -> Any:
    module = api()
    values = {
        "edge_score": d("0.780000"),
        "cost_drag_score": d("0.180000"),
        "liquidity_status": "pass",
        "resolution_risk_tier": "low",
        "source_quorum_status": "pass",
        "human_review_required": False,
        "team_capacity_status": "available",
    }
    values.update(overrides)
    return module.StrategyAvoidanceReasonAuditV10Input(**values)


def audit(row: Any | None = None, *, cfg: Any | None = None) -> Any:
    module = api()
    return module.audit_strategy_avoidance_reason_v10(
        row or candidate(),
        config=cfg or config(),
    )


def assert_public_numeric_fields_are_decimal(instance: object) -> None:
    for field in fields(instance):
        value = getattr(instance, field.name)
        if type(value) is bool:
            continue
        assert type(value) is not float, field.name
        assert type(value) is not int, field.name


def assert_no_runtime_numeric(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    assert not isinstance(value, Decimal)
    if isinstance(value, dict):
        for child in value.values():
            assert_no_runtime_numeric(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_runtime_numeric(child)


def test_clear_candidate_reports_no_avoidance_and_json_ready_payload() -> None:
    module = api()

    result = audit()
    payload = module.strategy_avoidance_reason_audit_v10_payload(result)

    assert is_dataclass(result)
    assert result.__dataclass_params__.frozen
    assert result.avoidance_status == "clear"
    assert result.primary_avoidance_reason == "no_avoidance_reason"
    assert result.secondary_reasons == ()
    assert result.recheck_minutes == d("30.000000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.payload.edge_score == d("0.780000")
    assert result.payload.cost_drag_score == d("0.180000")
    assert type(result.payload.edge_score) is Decimal
    assert_public_numeric_fields_are_decimal(result)
    assert_public_numeric_fields_are_decimal(result.payload)

    assert payload["avoidance_status"] == "clear"
    assert payload["primary_avoidance_reason"] == "no_avoidance_reason"
    assert payload["secondary_reasons"] == []
    assert payload["recheck_minutes"] == "30.000000"
    assert payload["payload"]["edge_score"] == "0.780000"
    assert payload["payload"]["cost_drag_score"] == "0.180000"
    assert payload["payload"]["paper_only"] is True
    json.dumps(payload, sort_keys=True, allow_nan=False)
    assert_no_runtime_numeric(payload)
    assert module.strategy_avoidance_reason_audit_v10_payload(payload) == payload


def test_avoidance_uses_highest_priority_primary_reason_and_secondary_reasons() -> None:
    result = audit(
        candidate(
            edge_score=d("0.300000"),
            cost_drag_score=d("0.800000"),
            liquidity_status="blocked",
            resolution_risk_tier="high",
            source_quorum_status="blocked",
            human_review_required=True,
            team_capacity_status="blocked",
        ),
    )

    assert result.avoidance_status == "avoid"
    assert result.primary_avoidance_reason == "liquidity_blocked"
    assert result.secondary_reasons == (
        "source_quorum_blocked",
        "resolution_risk_high",
        "team_capacity_blocked",
        "edge_score_below_floor",
        "cost_drag_score_above_limit",
        "human_review_required",
    )
    assert result.recheck_minutes == d("480.000000")


def test_watch_inputs_require_review_without_hard_avoidance() -> None:
    result = audit(
        candidate(
            liquidity_status="watch",
            resolution_risk_tier="medium",
            source_quorum_status="watch",
            human_review_required=True,
            team_capacity_status="constrained",
        ),
    )

    assert result.avoidance_status == "review"
    assert result.primary_avoidance_reason == "human_review_required"
    assert result.secondary_reasons == (
        "liquidity_watch",
        "resolution_risk_medium",
        "source_quorum_watch",
        "team_capacity_constrained",
    )
    assert result.recheck_minutes == d("120.000000")


def test_direct_function_accepts_required_input_surface() -> None:
    module = api()

    result = module.audit_strategy_avoidance_reason_v10_from_fields(
        edge_score=d("0.520000"),
        cost_drag_score=d("0.200000"),
        liquidity_status="pass",
        resolution_risk_tier="low",
        source_quorum_status="pass",
        human_review_required=False,
        team_capacity_status="available",
    )

    assert result.avoidance_status == "avoid"
    assert result.primary_avoidance_reason == "edge_score_below_floor"
    assert result.recheck_minutes == d("480.000000")


def test_dataclasses_validate_decimal_inputs_statuses_flags_and_consistency() -> None:
    module = api()
    result = audit()

    for dataclass_type in (
        module.StrategyAvoidanceReasonAuditV10Config,
        module.StrategyAvoidanceReasonAuditV10Input,
        module.StrategyAvoidanceReasonAuditV10Payload,
        module.StrategyAvoidanceReasonAuditV10Result,
    ):
        assert is_dataclass(dataclass_type)

    with pytest.raises(FrozenInstanceError):
        result.avoidance_status = "avoid"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.payload.edge_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="edge_score must be a Decimal"):
        candidate(edge_score=1)
    with pytest.raises(ValueError, match="edge_score must be exactly Decimal"):
        candidate(edge_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="cost_drag_score must be between zero and one"):
        candidate(cost_drag_score=d("1.000001"))
    with pytest.raises(ValueError, match="liquidity_status"):
        candidate(liquidity_status="ready")
    with pytest.raises(ValueError, match="human_review_required must be a bool"):
        candidate(human_review_required=1)
    with pytest.raises(ValueError, match="paper_only"):
        candidate(paper_only=False)
    with pytest.raises(ValueError, match="config thresholds"):
        config(minimum_edge_score=d("0.400000"), maximum_cost_drag_score=d("0.500000"))
    with pytest.raises(ValueError, match="input_row must be"):
        module.audit_strategy_avoidance_reason_v10(object(), config=config())
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="primary_avoidance_reason"):
        replace(result, primary_avoidance_reason="edge_score_below_floor")
    with pytest.raises(ValueError, match="payload"):
        replace(result, payload={})


def test_payload_rejects_float_downgraded_flags_and_unsafe_surface() -> None:
    module = api()
    payload = module.strategy_avoidance_reason_audit_v10_payload(audit())

    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.strategy_avoidance_reason_audit_v10_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="JSON value must not be a float"):
        module.strategy_avoidance_reason_audit_v10_payload(
            {**payload, "recheck_minutes": 30.0},
        )
    with pytest.raises(ValueError, match="JSON numeric value must use Decimal"):
        module.strategy_avoidance_reason_audit_v10_payload(
            {**payload, "recheck_minutes": 30},
        )
    with pytest.raises(ValueError, match="unsafe live surface"):
        module.strategy_avoidance_reason_audit_v10_payload(
            {**payload, "wallet": "redacted"},
        )


def test_module_scope_stays_paper_report_readonly_without_side_effects() -> None:
    source = Path(
        "src/polymarket_alpha_lab/strategy_trade_avoidance_reason_audit_v10.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "auth",
        "wallet",
        "broker",
        "signing",
        "submit",
        "cancel",
        "replace",
        "network",
        "database",
        "db",
        "file io",
        "open(",
        "advice",
        "order",
        "live trading",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    banned_imports = {
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    banned_call_names = {
        "open",
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "float",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        if isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_call_names
