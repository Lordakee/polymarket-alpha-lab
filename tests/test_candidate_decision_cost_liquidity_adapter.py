from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_cost_liquidity_adapter"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "candidate_decision_cost_liquidity_adapter.py"
)
OBSERVED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class StringSubclass(str):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing adapter module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": module.DEFAULT_CANDIDATE_DECISION_COST_LIQUIDITY_ADAPTER_VERSION,
        "watch_min_depth_coverage_ratio": d("1.250000"),
        "block_min_depth_coverage_ratio": d("0.750000"),
        "watch_max_spread_drag": d("0.030000"),
        "block_max_spread_drag": d("0.060000"),
        "watch_max_cost_drag": d("0.040000"),
        "block_max_cost_drag": d("0.080000"),
        "cost_score_full_drag": d("0.080000"),
        "minimum_pass_liquidity_score": d("0.700000"),
        "blocked_max_liquidity_score": d("0.250000"),
    }
    values.update(overrides)
    return module.CandidateDecisionCostLiquidityAdapterConfig(**values)


def facts(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "candidate_id": "candidate-cost-liquidity-001",
        "market_id": "market-cost-liquidity-001",
        "selected_side": "yes",
        "observed_at": OBSERVED_AT,
        "forecast_probability": d("0.650000"),
        "executable_price": d("0.590000"),
        "fee_cost_per_share": d("0.003000"),
        "spread_cost_per_share": d("0.010000"),
        "slippage_cost_per_share": d("0.004000"),
        "funding_cost_per_share": d("0.001000"),
        "finalization_cost_per_share": d("0.001000"),
        "time_cost_per_share": d("0.001000"),
        "risk_cost_per_share": d("0.002000"),
        "capital_cost_per_share": d("0.003000"),
        "requested_paper_shares": d("100.000000"),
        "available_depth_shares": d("200.000000"),
        "reason_codes": ("cost_liquidity_input",),
    }
    values.update(overrides)
    return module.CandidateDecisionCostLiquidityFacts(**values)


def adapt(subject: object | None = None, cfg: object | None = None) -> Any:
    module = api()
    return module.adapt_candidate_decision_cost_liquidity(
        facts() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_adapts_side_aware_costs_into_candidate_decision_fields_and_net_edge() -> None:
    module = api()
    result = adapt()

    assert is_dataclass(result)
    assert type(result) is module.CandidateDecisionCostLiquidityAdapterOutput
    assert result.candidate_id == "candidate-cost-liquidity-001"
    assert result.market_id == "market-cost-liquidity-001"
    assert result.selected_side == "yes"
    assert result.observed_at == OBSERVED_AT
    assert result.side_probability == d("0.650000")
    assert result.gross_edge == d("0.060000")
    assert result.estimated_cost_drag == d("0.025000")
    assert result.net_edge == d("0.035000")
    assert result.cost_score == d("0.687500")
    assert result.depth_coverage_ratio == d("2.000000")
    assert result.liquidity_score == d("0.916667")
    assert result.liquidity_status == "pass"
    assert result.reason_codes == (
        "candidate_cost_liquidity_adapter_v0",
        "cost_liquidity_input",
        "net_edge_positive",
        "cost_drag_pass",
        "liquidity_pass",
        "depth_coverage_pass",
        "spread_drag_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    decision_fields = result.candidate_decision_fields
    assert decision_fields == {
        "gross_edge": d("0.060000"),
        "estimated_cost_drag": d("0.025000"),
        "cost_score": d("0.687500"),
        "liquidity_score": d("0.916667"),
        "adapter_reason_codes": result.reason_codes,
    }
    assert module.adapter_output_to_candidate_decision_fields(result) == decision_fields


def test_no_side_uses_inverse_forecast_probability_for_gross_edge() -> None:
    result = adapt(
        facts(
            selected_side="no",
            forecast_probability=d("0.650000"),
            executable_price=d("0.310000"),
        ),
    )

    assert result.side_probability == d("0.350000")
    assert result.gross_edge == d("0.040000")
    assert result.estimated_cost_drag == d("0.025000")
    assert result.net_edge == d("0.015000")


def test_liquidity_block_watch_pass_scoring_and_hard_flags() -> None:
    passed = adapt()
    watched = adapt(
        facts(
            available_depth_shares=d("100.000000"),
            spread_cost_per_share=d("0.040000"),
        ),
    )
    blocked = adapt(
        facts(
            available_depth_shares=d("50.000000"),
            spread_cost_per_share=d("0.070000"),
        ),
    )
    costly_blocked = adapt(
        facts(
            fee_cost_per_share=d("0.050000"),
            spread_cost_per_share=d("0.010000"),
            slippage_cost_per_share=d("0.030000"),
        ),
    )

    assert passed.liquidity_status == "pass"
    assert passed.liquidity_score == d("0.916667")
    assert "liquidity_pass" in passed.reason_codes

    assert watched.depth_coverage_ratio == d("1.000000")
    assert watched.liquidity_status == "watch"
    assert watched.liquidity_score == d("0.566667")
    assert "liquidity_watch" in watched.reason_codes
    assert "depth_coverage_watch" in watched.reason_codes
    assert "spread_drag_watch" in watched.reason_codes

    assert blocked.depth_coverage_ratio == d("0.500000")
    assert blocked.liquidity_status == "blocked"
    assert blocked.liquidity_score == d("0.000000")
    assert "liquidity_blocked" in blocked.reason_codes
    assert "depth_coverage_blocked" in blocked.reason_codes
    assert "spread_drag_blocked" in blocked.reason_codes

    assert costly_blocked.estimated_cost_drag == d("0.098000")
    assert costly_blocked.cost_score == d("0.000000")
    assert costly_blocked.liquidity_status == "blocked"
    assert "cost_drag_blocked" in costly_blocked.reason_codes

    with pytest.raises(FrozenInstanceError):
        passed.net_edge = ZERO  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(facts(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(passed, readonly=False)


def test_unit_conversion_guardrails_decimal_only_and_utc_datetimes() -> None:
    eastern = timezone(timedelta(hours=-4))
    result = adapt(
        facts(
            observed_at=datetime(2026, 7, 7, 8, 0, tzinfo=eastern),
        ),
    )
    assert result.observed_at == OBSERVED_AT

    for instance in (config(), facts(), result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) in (bool, str, datetime, tuple) or value is None:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="forecast_probability must be a Decimal"):
        facts(forecast_probability=0.65)
    with pytest.raises(ValueError, match="executable_price must be a Decimal"):
        facts(executable_price=DecimalSubclass("0.590000"))
    with pytest.raises(ValueError, match="candidate_id must be a string"):
        facts(candidate_id=StringSubclass("candidate-cost-liquidity-001"))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        facts(observed_at=DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        facts(observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="selected_side"):
        facts(selected_side="maybe")
    with pytest.raises(ValueError, match="forecast_probability"):
        facts(forecast_probability=d("1.000001"))
    with pytest.raises(ValueError, match="fee_cost_per_share"):
        facts(fee_cost_per_share=d("-0.000001"))
    with pytest.raises(ValueError, match="requested_paper_shares must be positive"):
        facts(requested_paper_shares=ZERO)
    with pytest.raises(ValueError, match="watch_min_depth_coverage_ratio"):
        config(watch_min_depth_coverage_ratio=d("0.500000"))
    with pytest.raises(ValueError, match="cost_score_full_drag"):
        config(cost_score_full_drag=ZERO)
    with pytest.raises(ValueError, match="config must be"):
        api().adapt_candidate_decision_cost_liquidity(facts(), config=object())
    with pytest.raises(ValueError, match="facts must be"):
        api().adapt_candidate_decision_cost_liquidity(object(), config=config())


def test_duplicate_invalid_reason_codes_and_output_consistency_are_rejected() -> None:
    module = api()
    result = adapt()

    with pytest.raises(ValueError, match="reason_codes must be unique"):
        facts(reason_codes=("cost_liquidity_input", "cost_liquidity_input"))
    with pytest.raises(ValueError, match="reason_codes"):
        facts(reason_codes=("",))
    with pytest.raises(ValueError, match="reason_codes"):
        facts(reason_codes=(" leading_space",))
    with pytest.raises(ValueError, match="reason_codes"):
        facts(reason_codes=("has space",))
    with pytest.raises(ValueError, match="reason_codes"):
        facts(reason_codes=("candidate_decision_watch",))

    with pytest.raises(ValueError, match="net_edge"):
        replace(result, net_edge=d("0.040000"))
    with pytest.raises(ValueError, match="estimated_cost_drag"):
        replace(result, estimated_cost_drag=d("0.030000"))
    with pytest.raises(ValueError, match="cost_score"):
        replace(result, cost_score=d("0.700000"))
    with pytest.raises(ValueError, match="liquidity_status"):
        replace(result, liquidity_status="watch")
    with pytest.raises(ValueError, match="adapter output"):
        module.adapter_output_to_candidate_decision_fields(object())


def test_payload_json_contains_no_floats_and_is_safe() -> None:
    module = api()
    result = adapt()
    payload = module.candidate_decision_cost_liquidity_adapter_payload(result)

    assert payload["observed_at"] == "2026-07-07T12:00:00+00:00"
    assert payload["forecast_probability"] == "0.650000"
    assert payload["gross_edge"] == "0.060000"
    assert payload["estimated_cost_drag"] == "0.025000"
    assert payload["net_edge"] == "0.035000"
    assert payload["cost_score"] == "0.687500"
    assert payload["liquidity_score"] == "0.916667"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)
    assert "wallet" not in repr(payload).lower()
    assert "private_key" not in repr(payload).lower()

    with pytest.raises(ValueError, match="payload must be"):
        module.candidate_decision_cost_liquidity_adapter_payload(object())


def test_forbidden_surface_scan_and_exports_are_paper_only() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_CANDIDATE_DECISION_COST_LIQUIDITY_ADAPTER_VERSION",
        "CandidateDecisionCostLiquidityAdapterConfig",
        "CandidateDecisionCostLiquidityFacts",
        "CandidateDecisionCostLiquidityAdapterOutput",
        "adapt_candidate_decision_cost_liquidity",
        "adapter_output_to_candidate_decision_fields",
        "candidate_decision_cost_liquidity_adapter_payload",
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
        "balance",
        "place_order",
        "cancel_order",
    ):
        assert banned not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"open", "float"}
