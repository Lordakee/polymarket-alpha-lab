import importlib
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_liquidity_quality_gate"
GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)
CONFIG_VERSION = "research-liquidity-quality-gate-v0"
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": CONFIG_VERSION,
        "max_pass_spread": d("0.030000"),
        "max_watch_spread": d("0.060000"),
        "max_pass_total_cost": d("0.020000"),
        "max_watch_total_cost": d("0.050000"),
        "min_pass_depth_coverage_ratio": d("2.000000"),
        "min_watch_depth_coverage_ratio": d("1.000000"),
        "max_pass_slippage_risk_score": d("0.020000"),
        "max_watch_slippage_risk_score": d("0.050000"),
    }
    values.update(overrides)
    return module.ResearchLiquidityQualityGateConfig(**values)


def candidate(raw_candidate_id: str = "candidate-alpha", **overrides: object) -> Any:
    module = api()
    values = {
        "raw_candidate_id": raw_candidate_id,
        "raw_market_id": "market-alpha-private",
        "raw_market_slug": "market-alpha-private-slug",
        "raw_question": "Will the private alpha market resolve?",
        "source_reference": "source-ref-private",
        "source_url": "https://example.invalid/private?token=secret-token",
        "source_text": "private source text for market-alpha-private",
        "observed_at": GENERATED_AT - timedelta(minutes=5),
        "target_size": d("100.000000"),
        "available_depth": d("300.000000"),
        "spread": d("0.020000"),
        "fee_cost": d("0.005000"),
        "impact_cost": d("0.003000"),
        "slippage_cost": d("0.004000"),
        "slippage_risk_score": d("0.015000"),
    }
    values.update(overrides)
    return module.ResearchLiquidityQualityGateCandidate(**values)


def report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_liquidity_quality_gate_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_values(item)


def assert_public_payload_safe(payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, sort_keys=True).lower()
    forbidden_fragments = (
        "candidate-alpha",
        "market-alpha-private",
        "market-alpha-private-slug",
        "will the private alpha market resolve",
        "source-ref-private",
        "example.invalid",
        "secret-token",
        "private source text",
        "source_url",
        "source_text",
        "source_reference",
        "market_id",
        "market_slug",
        "question",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    for fragment in forbidden_fragments:
        assert fragment not in rendered
    assert_no_float_values(payload)


def test_pass_path_redacts_depth_and_public_payload() -> None:
    module = api()
    result = report(candidate())

    assert result.generated_at == GENERATED_AT
    assert result.config_version == CONFIG_VERSION
    assert result.status == "pass"
    assert result.reason_codes == ("liquidity_quality_gate_pass", "liquidity_quality_pass")
    assert result.item_count == d("1.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == ZERO
    assert result.block_count == ZERO
    assert result.max_spread == d("0.020000")
    assert result.max_total_cost == d("0.012000")
    assert result.min_depth_coverage_ratio == d("3.000000")
    assert result.max_slippage_risk_score == d("0.015000")
    assert result.average_liquidity_quality_score == d("0.953000")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert result.derived_validation_digest

    row = result.rows[0]
    assert row.review_rank == d("1.000000")
    assert row.status == "pass"
    assert row.reason_codes == ("liquidity_quality_pass",)
    assert row.depth_coverage_band == "deep"
    assert row.depth_coverage_ratio == d("3.000000")
    assert row.spread == d("0.020000")
    assert row.total_cost == d("0.012000")
    assert row.slippage_risk_band == "low"
    assert row.liquidity_quality_score == d("0.953000")
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.derived_validation_digest

    payload = module.research_liquidity_quality_gate_payload(result)
    assert payload["item_count"] == "1.000000"
    assert payload["rows"][0]["depth_coverage_band"] == "deep"
    assert payload["rows"][0]["total_cost"] == "0.012000"
    assert_public_payload_safe(payload)
    json.dumps(payload, sort_keys=True, allow_nan=False)


def test_watch_path_combines_depth_spread_cost_and_slippage_reasons() -> None:
    result = report(
        candidate(
            raw_candidate_id="candidate-watch",
            available_depth=d("150.000000"),
            spread=d("0.040000"),
            fee_cost=d("0.010000"),
            impact_cost=d("0.010000"),
            slippage_cost=d("0.010000"),
            slippage_risk_score=d("0.030000"),
        ),
    )

    assert result.status == "watch"
    assert result.pass_count == ZERO
    assert result.watch_count == d("1.000000")
    assert result.block_count == ZERO
    assert result.reason_codes == (
        "liquidity_quality_gate_watch",
        "depth_coverage_watch",
        "spread_watch",
        "cost_watch",
        "slippage_risk_watch",
    )
    row = result.rows[0]
    assert row.status == "watch"
    assert row.depth_coverage_band == "adequate"
    assert row.slippage_risk_band == "elevated"
    assert row.total_cost == d("0.030000")
    assert row.liquidity_quality_score == d("0.900000")
    assert row.reason_codes == (
        "depth_coverage_watch",
        "spread_watch",
        "cost_watch",
        "slippage_risk_watch",
    )


def test_block_path_prioritizes_block_reasons_and_sorts_by_severity() -> None:
    result = report(
        candidate(raw_candidate_id="candidate-pass", raw_market_id="market-pass"),
        candidate(
            raw_candidate_id="candidate-watch",
            raw_market_id="market-watch",
            available_depth=d("150.000000"),
            spread=d("0.040000"),
            fee_cost=d("0.010000"),
            impact_cost=d("0.010000"),
            slippage_cost=d("0.010000"),
            slippage_risk_score=d("0.030000"),
        ),
        candidate(
            raw_candidate_id="candidate-block",
            raw_market_id="market-block",
            available_depth=d("80.000000"),
            spread=d("0.070000"),
            fee_cost=d("0.020000"),
            impact_cost=d("0.020000"),
            slippage_cost=d("0.030000"),
            slippage_risk_score=d("0.060000"),
        ),
    )

    assert result.status == "block"
    assert result.item_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.reason_codes == (
        "liquidity_quality_gate_block",
        "depth_coverage_block",
        "spread_block",
        "cost_block",
        "slippage_risk_block",
        "depth_coverage_watch",
        "spread_watch",
        "cost_watch",
        "slippage_risk_watch",
        "liquidity_quality_pass",
    )

    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")
    assert tuple(row.review_rank for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    blocked = result.rows[0]
    assert blocked.depth_coverage_band == "thin"
    assert blocked.depth_coverage_ratio == d("0.800000")
    assert blocked.total_cost == d("0.070000")
    assert blocked.slippage_risk_band == "high"
    assert blocked.liquidity_quality_score == d("0.600000")


def test_exact_decimal_types_and_timezone_inputs_are_enforced() -> None:
    with pytest.raises(ValueError, match="max_pass_spread must be a Decimal"):
        config(max_pass_spread=0.03)

    with pytest.raises(ValueError, match="target_size must be a Decimal"):
        candidate(target_size=100)

    with pytest.raises(ValueError, match="available_depth must be a Decimal"):
        candidate(available_depth=_DecimalSubclass("100.000000"))

    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 7, 11, 55, tzinfo=UTC))

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 7, 12, 0))

    with pytest.raises(ValueError, match="items must contain"):
        report(object())


def test_public_leak_rejection_and_hard_flags() -> None:
    module = api()
    result = report(candidate())
    assert_public_payload_safe(module.research_liquidity_quality_gate_payload(result))

    with pytest.raises(ValueError, match="public"):
        module.ResearchLiquidityQualityGateRow(
            review_rank=d("1.000000"),
            status="pass",
            reason_codes=("wallet_leak",),
            depth_coverage_band="deep",
            depth_coverage_ratio=d("3.000000"),
            spread=d("0.020000"),
            fee_cost=d("0.005000"),
            impact_cost=d("0.003000"),
            slippage_cost=d("0.004000"),
            total_cost=d("0.012000"),
            slippage_risk_score=d("0.015000"),
            slippage_risk_band="low",
            liquidity_quality_score=d("0.953000"),
        )

    with pytest.raises(ValueError, match="public"):
        config(config_version="token-config-v0")

    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        replace(candidate(), report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)

    with pytest.raises(FrozenInstanceError):
        result.status = "pass"  # type: ignore[misc]


def test_output_is_deterministic_for_input_order_and_timezone_offsets() -> None:
    module = api()
    first = candidate(
        raw_candidate_id="candidate-zulu",
        raw_market_id="market-zulu",
        observed_at=datetime(2026, 7, 7, 7, 55, tzinfo=timezone(timedelta(hours=-4))),
    )
    second = candidate(
        raw_candidate_id="candidate-alpha",
        raw_market_id="market-alpha",
        available_depth=d("80.000000"),
        spread=d("0.070000"),
        fee_cost=d("0.020000"),
        impact_cost=d("0.020000"),
        slippage_cost=d("0.030000"),
        slippage_risk_score=d("0.060000"),
    )

    left = module.research_liquidity_quality_gate_payload(report(first, second))
    right = module.research_liquidity_quality_gate_payload(report(second, first))

    assert left == right
    assert left["rows"][1]["observed_age_seconds"] == "300.000000"
    assert_public_payload_safe(left)
