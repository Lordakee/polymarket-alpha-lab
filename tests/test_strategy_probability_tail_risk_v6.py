from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_probability_tail_risk_v6.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_probability_tail_risk_v6",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def risk_input(**overrides: object):
    module = api()
    values = {
        "forecast_probability": d("0.610000"),
        "market_probability": d("0.600000"),
        "resolution_risk": d("0.100000"),
        "source_conflict": d("0.120000"),
        "liquidity_depth": d("0.850000"),
        "time_to_resolution": d("72.000000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityTailRiskV6Input(**values)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "strategy-probability-tail-risk-v6",
        "watch_tail_risk_score": d("0.350000"),
        "block_tail_risk_score": d("0.700000"),
        "watch_probability_gap": d("0.100000"),
        "block_probability_gap": d("0.250000"),
        "watch_resolution_risk": d("0.350000"),
        "block_resolution_risk": d("0.700000"),
        "watch_source_conflict": d("0.350000"),
        "block_source_conflict": d("0.700000"),
        "watch_liquidity_depth": d("0.700000"),
        "block_liquidity_depth": d("0.250000"),
        "near_resolution_window": d("24.000000"),
        "watch_time_to_resolution_risk": d("0.350000"),
        "block_time_to_resolution_risk": d("0.700000"),
    }
    values.update(overrides)
    return module.StrategyProbabilityTailRiskV6Config(**values)


def report(input_value=None, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_strategy_probability_tail_risk_v6_report(
        input_value if input_value is not None else risk_input(),
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_int_or_float_values(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric payload value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_int_or_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_int_or_float_values(item)


def test_tail_risk_generates_pass_watch_and_block_outputs_from_probability_inputs() -> None:
    passed = report(
        risk_input(
            forecast_probability=d("0.610000"),
            market_probability=d("0.600000"),
            resolution_risk=d("0.100000"),
            source_conflict=d("0.120000"),
            liquidity_depth=d("0.850000"),
            time_to_resolution=d("72.000000"),
        ),
    )
    watched = report(
        risk_input(
            forecast_probability=d("0.720000"),
            market_probability=d("0.600000"),
            resolution_risk=d("0.350000"),
            source_conflict=d("0.200000"),
            liquidity_depth=d("0.650000"),
            time_to_resolution=d("12.000000"),
        ),
    )
    blocked = report(
        risk_input(
            forecast_probability=d("0.900000"),
            market_probability=d("0.150000"),
            resolution_risk=d("0.800000"),
            source_conflict=d("0.750000"),
            liquidity_depth=d("0.100000"),
            time_to_resolution=d("1.200000"),
        ),
    )

    assert is_dataclass(passed)
    assert passed.generated_at == GENERATED_AT
    assert passed.config_version == "strategy-probability-tail-risk-v6"
    assert passed.probability_gap == d("0.010000")
    assert passed.liquidity_depth_risk == d("0.150000")
    assert passed.time_to_resolution_risk == ZERO
    assert passed.tail_risk_score == d("0.150000")
    assert passed.tail_risk_status == "pass"
    assert passed.reason_codes == ("probability_tail_risk_v6_pass",)
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    assert watched.probability_gap == d("0.120000")
    assert watched.liquidity_depth_risk == d("0.350000")
    assert watched.time_to_resolution_risk == d("0.500000")
    assert watched.tail_risk_score == d("0.500000")
    assert watched.tail_risk_status == "watch"
    assert watched.reason_codes == (
        "probability_gap_watch",
        "resolution_risk_watch",
        "liquidity_depth_watch",
        "time_to_resolution_watch",
    )

    assert blocked.probability_gap == d("0.750000")
    assert blocked.liquidity_depth_risk == d("0.900000")
    assert blocked.time_to_resolution_risk == d("0.950000")
    assert blocked.tail_risk_score == d("0.950000")
    assert blocked.tail_risk_status == "block"
    assert blocked.reason_codes == (
        "probability_gap_block",
        "resolution_risk_block",
        "source_conflict_block",
        "liquidity_depth_block",
        "time_to_resolution_block",
    )


def test_payload_uses_decimal_strings_utc_timestamps_and_no_public_numbers() -> None:
    module = api()
    result = report(
        risk_input(
            forecast_probability=d("0.720000"),
            market_probability=d("0.600000"),
            time_to_resolution=d("12.000000"),
        ),
        generated_at=datetime(2026, 7, 6, 5, 0, tzinfo=timezone(timedelta(hours=-7))),
    )

    payload = module.strategy_probability_tail_risk_v6_payload(result)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["forecast_probability"] == "0.720000"
    assert payload["market_probability"] == "0.600000"
    assert payload["probability_gap"] == "0.120000"
    assert payload["tail_risk_score"] == "0.500000"
    assert payload["tail_risk_status"] == "watch"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_int_or_float_values(payload)


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    result = report()

    for klass in (
        module.StrategyProbabilityTailRiskV6Config,
        module.StrategyProbabilityTailRiskV6Input,
        module.StrategyProbabilityTailRiskV6Report,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.tail_risk_status = "block"  # type: ignore[misc]

    for item in fields(result):
        item_value = getattr(result, item.name)
        if item.name in {"paper_only", "report_only", "readonly"}:
            continue
        if item.name.endswith(
            (
                "_probability",
                "_risk",
                "_depth",
                "_resolution",
                "_gap",
                "_score",
            ),
        ):
            assert type(item_value) is Decimal

    with pytest.raises(ValueError, match="forecast_probability"):
        risk_input(forecast_probability=0.61)
    with pytest.raises(ValueError, match="market_probability"):
        risk_input(market_probability=1)
    with pytest.raises(ValueError, match="resolution_risk"):
        risk_input(resolution_risk=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))


def test_validation_rejects_bounds_threshold_sequences_flags_and_types() -> None:
    module = api()
    valid_input = risk_input()

    with pytest.raises(ValueError, match="input_value"):
        module.build_strategy_probability_tail_risk_v6_report(
            object(),
            config=config(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="config"):
        module.build_strategy_probability_tail_risk_v6_report(
            valid_input,
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        risk_input(forecast_probability=d("1.000001"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        risk_input(liquidity_depth=d("-0.000001"))
    with pytest.raises(ValueError, match="time_to_resolution"):
        risk_input(time_to_resolution=d("-1.000000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="block_tail_risk_score"):
        config(block_tail_risk_score=d("0.300000"))
    with pytest.raises(ValueError, match="block_probability_gap"):
        config(block_probability_gap=d("0.050000"))
    with pytest.raises(ValueError, match="block_liquidity_depth"):
        config(block_liquidity_depth=d("0.800000"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(valid_input, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        module.strategy_probability_tail_risk_v6_payload(
            replace(report(), readonly=False),
        )
    with pytest.raises(ValueError, match="report"):
        module.strategy_probability_tail_risk_v6_payload(object())


def test_module_scope_has_no_external_io_db_or_live_action_surface() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: list[str] = []
    forbidden_import_roots = {
        "asyncio",
        "csv",
        "http",
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
    forbidden_call_names = {
        "open",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
        "sign",
    }
    forbidden_attr_fragments = (
        "account",
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0
            imports.append(node.module or "")
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)

    assert imports
    for module_name in imports:
        assert module_name.split(".")[0] not in forbidden_import_roots
