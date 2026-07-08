from __future__ import annotations

import dataclasses
import hashlib
import json
from dataclasses import FrozenInstanceError, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import MappingProxyType

import pytest

from polymarket_alpha_lab.research_market_liquidity_cost_regime_classifier_report import (
    LIQUIDITY_COST_REGIME_CLASSIFIER_STATUSES,
    ResearchMarketLiquidityCostRegimeClassifierConfig,
    ResearchMarketLiquidityCostRegimeClassifierInput,
    ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount,
    ResearchMarketLiquidityCostRegimeClassifierReport,
    ResearchMarketLiquidityCostRegimeClassifierRow,
    build_research_market_liquidity_cost_regime_classifier_report,
    research_market_liquidity_cost_regime_classifier_public_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketLiquidityCostRegimeClassifierConfig:
    values = {
        "min_pass_depth_score": d("0.750000"),
        "min_watch_depth_score": d("0.500000"),
        "max_pass_spread_rate": d("0.020000"),
        "max_watch_spread_rate": d("0.050000"),
        "max_pass_fee_drag_rate": d("0.010000"),
        "max_watch_fee_drag_rate": d("0.030000"),
        "max_pass_slippage_pressure_rate": d("0.015000"),
        "max_watch_slippage_pressure_rate": d("0.040000"),
        "max_pass_settlement_friction_rate": d("0.005000"),
        "max_watch_settlement_friction_rate": d("0.020000"),
        "max_pass_total_cost_rate": d("0.030000"),
        "max_watch_total_cost_rate": d("0.080000"),
    }
    values.update(overrides)
    return ResearchMarketLiquidityCostRegimeClassifierConfig(**values)


def input_row(
    sanitized_event_group: str = "policy-liquid-group",
    domain: str = "policy",
    *,
    depth_score: Decimal = d("0.900000"),
    spread_rate: Decimal = d("0.010000"),
    fee_drag_rate: Decimal = d("0.002000"),
    slippage_pressure_rate: Decimal = d("0.003000"),
    settlement_friction_rate: Decimal = d("0.001000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchMarketLiquidityCostRegimeClassifierInput:
    return ResearchMarketLiquidityCostRegimeClassifierInput(
        sanitized_event_group=sanitized_event_group,
        domain=domain,
        depth_score=depth_score,
        spread_rate=spread_rate,
        fee_drag_rate=fee_drag_rate,
        slippage_pressure_rate=slippage_pressure_rate,
        settlement_friction_rate=settlement_friction_rate,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *items: ResearchMarketLiquidityCostRegimeClassifierInput,
    cfg: ResearchMarketLiquidityCostRegimeClassifierConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketLiquidityCostRegimeClassifierReport:
    return build_research_market_liquidity_cost_regime_classifier_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_regime_thresholds_cost_math_and_rollups_are_deterministic() -> None:
    passed = input_row("policy-liquid-group", "policy")
    watched = input_row(
        "sports-watch-group",
        "sports",
        depth_score=d("0.600000"),
        spread_rate=d("0.030000"),
        fee_drag_rate=d("0.020000"),
        slippage_pressure_rate=d("0.020000"),
        settlement_friction_rate=d("0.010000"),
    )
    blocked = input_row(
        "crypto-block-group",
        "crypto",
        depth_score=d("0.400000"),
        spread_rate=d("0.070000"),
        fee_drag_rate=d("0.040000"),
        slippage_pressure_rate=d("0.050000"),
        settlement_friction_rate=d("0.030000"),
    )

    first = report(passed, watched, blocked)
    second = report(blocked, passed, watched)

    assert first == second
    assert LIQUIDITY_COST_REGIME_CLASSIFIER_STATUSES == ("pass", "watch", "block")
    assert tuple(row.sanitized_event_group for row in first.rows) == (
        "crypto-block-group",
        "policy-liquid-group",
        "sports-watch-group",
    )
    assert first.status == "block"
    assert first.input_count == d("3.000000")
    assert first.pass_count == d("1.000000")
    assert first.watch_count == d("1.000000")
    assert first.block_count == d("1.000000")
    assert first.depth_pressure_count == d("2.000000")
    assert first.wide_spread_count == d("2.000000")
    assert first.high_fee_drag_count == d("2.000000")
    assert first.slippage_pressure_count == d("2.000000")
    assert first.settlement_friction_count == d("2.000000")
    assert first.high_total_cost_count == d("2.000000")
    assert first.max_total_cost_rate == d("0.155000")
    assert first.average_total_cost_rate == d("0.077000")

    block_row, pass_row, watch_row = first.rows
    assert type(block_row) is ResearchMarketLiquidityCostRegimeClassifierRow
    assert block_row.effective_spread_cost_rate == d("0.035000")
    assert block_row.total_cost_rate == d("0.155000")
    assert block_row.depth_status == "block"
    assert block_row.spread_status == "block"
    assert block_row.fee_drag_status == "block"
    assert block_row.slippage_pressure_status == "block"
    assert block_row.settlement_friction_status == "block"
    assert block_row.total_cost_status == "block"
    assert block_row.liquidity_cost_regime == "block_cost_friction"
    assert block_row.status == "block"
    assert block_row.reason_codes == (
        "depth_block",
        "fee_drag_block",
        "liquidity_cost_regime_block",
        "settlement_friction_block",
        "slippage_pressure_block",
        "spread_block",
        "total_cost_block",
    )

    assert pass_row.effective_spread_cost_rate == d("0.005000")
    assert pass_row.total_cost_rate == d("0.011000")
    assert pass_row.liquidity_cost_regime == "pass_liquid_low_cost"
    assert pass_row.reason_codes == ("liquidity_cost_regime_pass",)

    assert watch_row.effective_spread_cost_rate == d("0.015000")
    assert watch_row.total_cost_rate == d("0.065000")
    assert watch_row.depth_status == "watch"
    assert watch_row.liquidity_cost_regime == "watch_cost_pressure"
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "depth_watch",
        "fee_drag_watch",
        "liquidity_cost_regime_watch",
        "settlement_friction_watch",
        "slippage_pressure_watch",
        "spread_watch",
        "total_cost_watch",
    )


def test_public_payload_digest_is_deterministic_and_uses_decimal_strings() -> None:
    first = report(
        input_row("zeta-safe-group", "policy"),
        input_row("alpha-safe-group", "sports"),
    )
    timezone_equivalent = report(
        input_row("alpha-safe-group", "sports"),
        input_row("zeta-safe-group", "policy"),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    first_payload = first.public_payload
    second_payload = timezone_equivalent.public_payload
    payload_without_digest = dict(first_payload)
    payload_without_digest.pop("derived_validation_digest")
    expected_digest = hashlib.sha256(
        json.dumps(payload_without_digest, sort_keys=True, separators=(",", ":")).encode(
            "utf-8",
        ),
    ).hexdigest()

    assert first.derived_validation_digest == timezone_equivalent.derived_validation_digest
    assert first_payload == second_payload
    assert isinstance(first_payload, MappingProxyType)
    assert len(first.derived_validation_digest) == 64
    assert set(first.derived_validation_digest) <= set("0123456789abcdef")
    assert first.derived_validation_digest == expected_digest
    assert first_payload["derived_validation_digest"] == expected_digest
    assert first_payload["generated_at"] == "2026-07-08T16:00:00+00:00"
    assert first_payload["input_count"] == "2.000000"
    assert first_payload["rows"][0]["depth_score"] == "0.900000"
    assert first_payload["rows"][0]["total_cost_rate"] == "0.011000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert not any(isinstance(value, Decimal) for value in _walk_values(first_payload))
    assert not any(isinstance(value, float) for value in _walk_values(first_payload))
    assert not any(type(value) is int for value in _walk_values(first_payload))

    with pytest.raises(TypeError, match="mappingproxy"):
        first_payload["status"] = "pass"  # type: ignore[index]

    tampered_payload = dict(first_payload)
    tampered_payload["pass_count"] = "9.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_market_liquidity_cost_regime_classifier_public_payload(tampered_payload)


def test_public_payload_excludes_raw_ids_sources_and_execution_surfaces() -> None:
    classifier_report = report(input_row())
    payload = research_market_liquidity_cost_regime_classifier_public_payload(
        classifier_report,
    )
    forbidden_fragments = (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "auth",
        "recommendation",
        "sizing",
    )

    for key, value in _walk_key_values(payload):
        lowered_key = key.lower()
        assert not [fragment for fragment in forbidden_fragments if fragment in lowered_key]
        if type(value) is str:
            lowered_value = value.lower()
            assert "://" not in lowered_value
            assert not [fragment for fragment in forbidden_fragments if fragment in lowered_value]

    with pytest.raises(ValueError, match="unsafe"):
        input_row("candidate-123")

    unsafe_payload = dict(payload)
    unsafe_payload["wallet"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        research_market_liquidity_cost_regime_classifier_public_payload(unsafe_payload)


def test_config_drives_validation_and_frozen_decimal_only_contract() -> None:
    permissive = config(
        min_pass_depth_score=d("0.600000"),
        max_pass_spread_rate=d("0.030000"),
        max_pass_fee_drag_rate=d("0.020000"),
        max_pass_slippage_pressure_rate=d("0.020000"),
        max_pass_settlement_friction_rate=d("0.010000"),
        max_pass_total_cost_rate=d("0.065000"),
    )
    classifier_report = report(
        input_row(
            "custom-threshold-group",
            depth_score=d("0.600000"),
            spread_rate=d("0.030000"),
            fee_drag_rate=d("0.020000"),
            slippage_pressure_rate=d("0.020000"),
            settlement_friction_rate=d("0.010000"),
        ),
        cfg=permissive,
    )

    assert classifier_report.status == "pass"
    assert classifier_report.rows[0].status == "pass"
    assert classifier_report.rows[0].total_cost_rate == d("0.065000")

    for value in (
        permissive,
        input_row(),
        classifier_report.rows[0],
        classifier_report.reason_code_counts[0],
        classifier_report,
    ):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        classifier_report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="depth_score must be a Decimal"):
        input_row(depth_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="spread_rate must be exactly Decimal"):
        input_row(spread_rate=_DecimalSubclass("0.010000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="watch depth threshold"):
        config(min_pass_depth_score=d("0.500000"), min_watch_depth_score=d("0.600000"))
    with pytest.raises(ValueError, match="pass spread threshold"):
        config(max_pass_spread_rate=d("0.060000"), max_watch_spread_rate=d("0.050000"))
    with pytest.raises(ValueError, match="max_pass_total_cost_rate"):
        config(max_pass_total_cost_rate=d("1.100000"))


def test_empty_report_and_module_keep_readonly_report_only_scope() -> None:
    classifier_report = report()

    assert classifier_report.status == "block"
    assert classifier_report.input_count == ZERO
    assert classifier_report.rows == ()
    assert classifier_report.reason_codes == ("no_liquidity_cost_inputs",)
    assert classifier_report.reason_code_counts == (
        ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount(
            reason_code="no_liquidity_cost_inputs",
            count=d("1.000000"),
            row_ratio=ZERO,
        ),
    )
    assert classifier_report.paper_only is True
    assert classifier_report.report_only is True
    assert classifier_report.readonly is True

    for cls in (
        ResearchMarketLiquidityCostRegimeClassifierConfig,
        ResearchMarketLiquidityCostRegimeClassifierInput,
        ResearchMarketLiquidityCostRegimeClassifierRow,
        ResearchMarketLiquidityCostRegimeClassifierReasonCodeCount,
        ResearchMarketLiquidityCostRegimeClassifierReport,
    ):
        assert cls.__dataclass_params__.frozen

    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_liquidity_cost_regime_classifier_report.py"
    )
    source = source_path.read_text(encoding="utf-8")
    forbidden_imports = (
        "ccxt",
        "eth_account",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    )
    forbidden_surfaces = (
        "api_key",
        "private_key",
        "target_notional",
        "notional_usdc",
        "shares",
        "quantity",
        ".execute(",
        ".post(",
        ".put(",
        ".delete(",
        "INSERT ",
        "UPDATE ",
        "DELETE ",
    )

    assert not [term for term in forbidden_imports if f"import {term}" in source]
    assert not [term for term in forbidden_surfaces if term in source]


def _walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for child in value.values() for item in _walk_values(child))
    if isinstance(value, list):
        return tuple(item for child in value for item in _walk_values(child))
    return (value,)


def _walk_key_values(value: object) -> tuple[tuple[str, object], ...]:
    if isinstance(value, dict):
        pairs: list[tuple[str, object]] = []
        for key, item in value.items():
            pairs.append((str(key), item))
            pairs.extend(_walk_key_values(item))
        return tuple(pairs)
    if isinstance(value, list):
        return tuple(pair for item in value for pair in _walk_key_values(item))
    return ()
