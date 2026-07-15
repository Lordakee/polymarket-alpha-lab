from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.market_liquidity_exit_risk_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def build_report(**overrides: object) -> Any:
    module = api()
    values = {
        "bid_depth_usdc": d("500.000000"),
        "ask_depth_usdc": d("750.000000"),
        "spread_probability": d("0.010000"),
        "estimated_slippage_probability": d("0.005000"),
        "position_size_usdc": d("100.000000"),
        "settlement_window_seconds": d("3600.000000"),
        "market_age_seconds": d("86400.000000"),
        "cost_gate_ready": True,
    }
    values.update(overrides)
    return module.build_market_liquidity_exit_risk_readiness_report(**values)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def test_liquidity_exit_ready_report_passes_when_depth_costs_and_timing_are_ready() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.MarketLiquidityExitRiskReadinessReport
    assert is_dataclass(report)
    assert report.liquidity_exit_ready is True
    assert report.exit_risk_score == d("0.000000")
    assert report.ready_ratio == d("1.000000")
    assert report.blocked_reason_codes == ()
    assert report.attention_reason_codes == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_liquidity_exit_report_separates_blockers_from_attention_reasons() -> None:
    report = build_report(
        bid_depth_usdc=d("75.000000"),
        ask_depth_usdc=d("200.000000"),
        spread_probability=d("0.040000"),
        estimated_slippage_probability=d("0.030000"),
        settlement_window_seconds=d("604800.000000"),
        market_age_seconds=d("7200.000000"),
        cost_gate_ready=False,
    )

    assert report.liquidity_exit_ready is False
    assert report.ready_ratio == d("0.285714")
    assert report.exit_risk_score == d("0.714286")
    assert report.blocked_reason_codes == (
        "market_liquidity_exit_cost_gate_not_ready",
        "market_liquidity_exit_bid_depth_below_position",
    )
    assert report.attention_reason_codes == (
        "market_liquidity_exit_spread_probability_watch",
        "market_liquidity_exit_slippage_probability_watch",
        "market_liquidity_exit_settlement_window_watch",
    )


def test_public_payload_is_string_numeric_deterministic_and_digest_verified() -> None:
    module = api()
    first = build_report(
        bid_depth_usdc=d("75.000000"),
        ask_depth_usdc=d("200.000000"),
        spread_probability=d("0.040000"),
        estimated_slippage_probability=d("0.030000"),
        settlement_window_seconds=d("604800.000000"),
        market_age_seconds=d("7200.000000"),
        cost_gate_ready=False,
    )
    second = build_report(
        bid_depth_usdc=d("75.000000"),
        ask_depth_usdc=d("200.000000"),
        spread_probability=d("0.040000"),
        estimated_slippage_probability=d("0.030000"),
        settlement_window_seconds=d("604800.000000"),
        market_age_seconds=d("7200.000000"),
        cost_gate_ready=False,
    )

    payload = first.public_payload

    assert payload == second.public_payload
    assert payload == module.market_liquidity_exit_risk_readiness_report_payload(first)
    assert payload["digest"] == first.digest
    assert payload["digest"] == canonical_digest(payload)
    assert len(payload["digest"]) == 64
    int(payload["digest"], 16)
    assert payload["bid_depth_usdc"] == "75.000000"
    assert payload["ready_ratio"] == "0.285714"
    assert json.dumps(payload, sort_keys=True)
    assert module.validate_market_liquidity_exit_risk_readiness_public_payload(payload)

    def assert_public_safe(value: object) -> None:
        forbidden_keys = (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "question",
            "source_url",
            "source_text",
            "source_reference",
            "source_id",
            "dsn",
            "table_name",
            "token",
            "wallet",
            "order",
            "trade",
        )
        if isinstance(value, dict):
            for key, item in value.items():
                assert not any(fragment in key.lower() for fragment in forbidden_keys)
                assert_public_safe(item)
        elif isinstance(value, list):
            for item in value:
                assert_public_safe(item)
        else:
            assert type(value) is not float
            assert type(value) is not int

    assert_public_safe(payload)


def test_validation_rejects_non_decimal_numbers_bad_flags_and_tampered_payload() -> None:
    module = api()
    with pytest.raises(ValueError, match="bid_depth_usdc must be a Decimal"):
        build_report(bid_depth_usdc=500)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_probability must be a Decimal"):
        build_report(spread_probability=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="position_size_usdc must be positive"):
        build_report(position_size_usdc=d("0.000000"))
    with pytest.raises(ValueError, match="spread_probability must not exceed one"):
        build_report(spread_probability=d("1.000001"))
    with pytest.raises(ValueError, match="cost_gate_ready must be a bool"):
        build_report(cost_gate_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        build_report(paper_only=False)

    report = build_report()
    with pytest.raises(FrozenInstanceError):
        report.ready_ratio = d("0.000000")
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)

    payload = report.public_payload
    payload["digest"] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        module.validate_market_liquidity_exit_risk_readiness_public_payload(payload)


def test_public_dataclass_exports_and_module_are_readonly_report_only() -> None:
    module = api()
    report = build_report()

    assert module.__all__ == (
        "MarketLiquidityExitRiskReadinessReport",
        "build_market_liquidity_exit_risk_readiness_report",
        "market_liquidity_exit_risk_readiness_report_payload",
        "validate_market_liquidity_exit_risk_readiness_public_payload",
    )
    assert is_dataclass(report)
    assert type(report).__dataclass_params__.frozen
    with pytest.raises(TypeError, match="does not support subclassing"):

        class BadReport(module.MarketLiquidityExitRiskReadinessReport):
            pass

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "scrapling",
        "agent_reach",
        "playwright",
        "selenium",
        "private_key",
        "credential",
        "wallet",
        "order",
        "trade",
        "auth",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "aiohttp",
        "boto",
        "browser",
        "db",
        "httpx",
        "psycopg",
        "requests",
        "scrapling",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
