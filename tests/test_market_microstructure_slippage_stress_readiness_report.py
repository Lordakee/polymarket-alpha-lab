from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_microstructure_slippage_stress_readiness_report"
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "market_microstructure_slippage_stress_readiness_report.py"
)
GENERATED_AT = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing slippage stress readiness report module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "min_ready_spread_probability": d("0.750000"),
        "min_watch_spread_probability": d("0.500000"),
        "min_ready_depth_probability": d("0.750000"),
        "min_watch_depth_probability": d("0.500000"),
        "max_ready_slippage_probability": d("0.100000"),
        "max_watch_slippage_probability": d("0.250000"),
        "min_ready_exit_depth_probability": d("0.750000"),
        "min_watch_exit_depth_probability": d("0.500000"),
        "min_ready_depth_coverage_ratio": d("2.000000"),
        "min_watch_depth_coverage_ratio": d("1.000000"),
    }
    values.update(overrides)
    return module.MarketMicrostructureSlippageStressReadinessConfig(**values)


def stress_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "spread_probability": d("0.920000"),
        "depth_probability": d("0.880000"),
        "expected_trade_notional": d("100.000000"),
        "available_depth": d("250.000000"),
        "slippage_probability": d("0.040000"),
        "exit_depth_probability": d("0.900000"),
    }
    values.update(overrides)
    return module.MarketMicrostructureSlippageStressInput(**values)


def report(item: object | None = None, *, cfg: object | None = None) -> Any:
    module = api()
    return module.build_market_microstructure_slippage_stress_readiness_report(
        stress_input() if item is None else item,
        config=config() if cfg is None else cfg,
        generated_at=GENERATED_AT,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            assert_no_float_values(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_float_values(item)


def assert_public_payload_has_no_execution_surface(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, allow_nan=False, sort_keys=True).lower()
    for fragment in (
        "auth",
        "wallet",
        "private_key",
        "order",
        "execute",
        "execution",
        "cancel",
        "broker",
        "live",
        "database",
        "db",
    ):
        assert fragment not in rendered


def test_ready_stress_report_is_readonly_manual_filter_output() -> None:
    module = api()
    result = report()

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "market-microstructure-slippage-stress-readiness-v0"
    assert result.spread_probability == d("0.920000")
    assert result.depth_probability == d("0.880000")
    assert result.expected_trade_notional == d("100.000000")
    assert result.available_depth == d("250.000000")
    assert result.depth_coverage_ratio == d("2.500000")
    assert result.slippage_probability == d("0.040000")
    assert result.exit_depth_probability == d("0.900000")
    assert result.stress_status == "ready"
    assert result.reason_codes == ("slippage_stress_ready",)
    assert result.manual_next_step == "manual_filter_pass_liquidity_slippage_stress"
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    payload = module.market_microstructure_slippage_stress_readiness_payload(result)
    assert payload == result.payload
    assert payload["generated_at"] == "2026-07-12T12:00:00+00:00"
    assert payload["expected_trade_notional"] == "100.000000"
    assert payload["depth_coverage_ratio"] == "2.500000"
    assert payload["stress_status"] == "ready"
    assert payload["reason_codes"] == ["slippage_stress_ready"]
    assert payload["manual_next_step"] == "manual_filter_pass_liquidity_slippage_stress"
    assert_no_float_values(payload)
    assert_public_payload_has_no_execution_surface(payload)


def test_watch_and_block_statuses_prioritize_manual_screening_reasons() -> None:
    watch = report(
        stress_input(
            spread_probability=d("0.700000"),
            depth_probability=d("0.650000"),
            available_depth=d("150.000000"),
            slippage_probability=d("0.180000"),
            exit_depth_probability=d("0.600000"),
        ),
    )

    assert watch.stress_status == "watch"
    assert watch.reason_codes == (
        "spread_probability_watch",
        "depth_probability_watch",
        "depth_coverage_watch",
        "slippage_probability_watch",
        "exit_depth_probability_watch",
    )
    assert watch.manual_next_step == "manual_review_microstructure_stress_before_shortlist"

    blocked = report(
        stress_input(
            spread_probability=d("0.490000"),
            depth_probability=d("0.400000"),
            expected_trade_notional=d("100.000000"),
            available_depth=d("80.000000"),
            slippage_probability=d("0.260000"),
            exit_depth_probability=d("0.450000"),
        ),
    )

    assert blocked.stress_status == "blocked"
    assert blocked.depth_coverage_ratio == d("0.800000")
    assert blocked.reason_codes == (
        "spread_probability_block",
        "depth_probability_block",
        "depth_coverage_block",
        "slippage_probability_block",
        "exit_depth_probability_block",
    )
    assert blocked.manual_next_step == "manual_exclude_until_depth_or_slippage_stress_improves"


def test_decimal_only_validation_and_frozen_paper_flags() -> None:
    module = api()
    item = stress_input()
    result = report(item)

    for klass in (
        module.MarketMicrostructureSlippageStressReadinessConfig,
        module.MarketMicrostructureSlippageStressInput,
        module.MarketMicrostructureSlippageStressReadinessReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    for instance in (config(), item, result):
        assert instance.paper_only is True
        assert instance.report_only is True
        assert instance.readonly is True
        for field in fields(instance):
            value = getattr(instance, field.name)
            if field.name in {
                "paper_only",
                "report_only",
                "readonly",
                "payload",
                "config_version",
                "generated_at",
                "stress_status",
                "reason_codes",
                "manual_next_step",
            }:
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(FrozenInstanceError):
        item.available_depth = d("1")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(item, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(config(), report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)

    with pytest.raises(ValueError, match="spread_probability must be a Decimal"):
        stress_input(spread_probability=0.9)
    with pytest.raises(ValueError, match="available_depth must be a Decimal"):
        stress_input(available_depth=250)
    with pytest.raises(ValueError, match="exact Decimal"):
        stress_input(depth_probability=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="between 0 and 1"):
        stress_input(slippage_probability=d("1.100000"))
    with pytest.raises(ValueError, match="expected_trade_notional must be positive"):
        stress_input(expected_trade_notional=d("0.000000"))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_market_microstructure_slippage_stress_readiness_report(
            stress_input(),
            config=config(),
            generated_at=datetime(2026, 7, 12, 12, 0),
        )


def test_report_consistency_rejects_tampered_outputs() -> None:
    module = api()
    result = report(
        stress_input(
            spread_probability=d("0.700000"),
            slippage_probability=d("0.180000"),
        ),
    )

    with pytest.raises(ValueError, match="depth_coverage_ratio must match"):
        replace(result, depth_coverage_ratio=d("9.000000"))
    with pytest.raises(ValueError, match="stress_status must match"):
        replace(result, stress_status="ready")
    with pytest.raises(ValueError, match="reason_codes must match"):
        replace(result, reason_codes=("slippage_stress_ready",))
    with pytest.raises(ValueError, match="manual_next_step must match"):
        replace(result, manual_next_step="manual_filter_pass_liquidity_slippage_stress")


def test_source_has_no_io_persistence_or_execution_surface() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    banned_import_roots = {
        "asyncio",
        "csv",
        "http",
        "json",
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
    assert not (set(imported_modules) & banned_import_roots)

    public_api_text = "\n".join(module.__all__).lower()
    for forbidden in (
        "auth",
        "wallet",
        "private_key",
        "order",
        "execute",
        "execution",
        "cancel",
        "broker",
        "live",
        "database",
        "db",
        "persist",
    ):
        assert forbidden not in public_api_text
