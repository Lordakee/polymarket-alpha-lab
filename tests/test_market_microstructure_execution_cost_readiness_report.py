from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 11, 14, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 11, 14, 15, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "market_microstructure_execution_cost_readiness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def sample(reference: str, **overrides: object) -> Any:
    module = api()
    values = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "bid_probability": d("0.520000"),
        "ask_probability": d("0.540000"),
        "mid_probability": d("0.530000"),
        "taker_fee_probability": d("0.004000"),
        "estimated_slippage_probability": d("0.006000"),
        "depth_usdc": d("2500.000000"),
        "min_depth_usdc": d("1000.000000"),
        "edge_to_threshold_probability": d("0.080000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.MarketMicrostructureExecutionCostReadinessInput(**values)


def build_report(*inputs: object, config: object | None = None) -> Any:
    module = api()
    return module.build_market_microstructure_execution_cost_readiness_report(
        inputs,
        generated_at=GENERATED_AT,
        config=config,
    )


def walk_json(value: object):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from walk_json(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def test_execution_cost_readiness_scores_sorts_and_summarizes_bands() -> None:
    module = api()
    ready = sample(
        "ready market_id=mid market_slug=slug question https://example.invalid",
    )
    attention = sample(
        "attention source_text source_url=https://example.invalid/a",
        bid_probability=d("0.500000"),
        ask_probability=d("0.560000"),
        mid_probability=d("0.530000"),
        taker_fee_probability=d("0.012000"),
        estimated_slippage_probability=d("0.010000"),
        depth_usdc=d("1100.000000"),
        min_depth_usdc=d("1000.000000"),
        edge_to_threshold_probability=d("0.070000"),
    )
    blocker = sample(
        "blocker dsn=postgres table_name=markets token=secret wallet order trade",
        bid_probability=d("0.480000"),
        ask_probability=d("0.620000"),
        mid_probability=d("0.550000"),
        taker_fee_probability=d("0.030000"),
        estimated_slippage_probability=d("0.040000"),
        depth_usdc=d("400.000000"),
        min_depth_usdc=d("1000.000000"),
        edge_to_threshold_probability=d("0.050000"),
    )

    report = build_report(ready, attention, blocker)
    repeated_report = build_report(blocker, ready, attention)

    assert type(report) is module.MarketMicrostructureExecutionCostReadinessReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.band == "blocker"
    assert report.input_count == d("3.000000")
    assert report.ready_count == d("1.000000")
    assert report.attention_count == d("1.000000")
    assert report.blocker_count == d("1.000000")
    assert report.average_total_cost_probability == d("0.070667")
    assert report.max_spread_probability == d("0.140000")
    assert report.max_cost_burden_ratio == d("2.800000")
    assert report.min_depth_usdc == d("400.000000")
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    blocker_row, attention_row, ready_row = report.rows
    assert [row.band for row in report.rows] == ["blocker", "attention", "ready"]
    assert set(row.band for row in report.rows) <= {"ready", "attention", "blocker"}

    assert blocker_row.spread_probability == d("0.140000")
    assert blocker_row.total_cost_probability == d("0.140000")
    assert blocker_row.cost_burden_ratio == d("2.800000")
    assert blocker_row.depth_coverage_ratio == d("0.400000")
    assert blocker_row.reason_codes == (
        "execution_cost_readiness_blocker",
        "cost_burden_blocker",
        "depth_below_minimum_blocker",
        "spread_probability_blocker",
        "total_cost_probability_blocker",
    )

    assert attention_row.spread_probability == d("0.060000")
    assert attention_row.total_cost_probability == d("0.052000")
    assert attention_row.cost_burden_ratio == d("0.742857")
    assert attention_row.depth_coverage_ratio == d("1.100000")
    assert attention_row.reason_codes == (
        "execution_cost_readiness_attention",
        "cost_burden_attention",
        "spread_probability_attention",
        "total_cost_probability_attention",
    )

    assert ready_row.spread_probability == d("0.020000")
    assert ready_row.total_cost_probability == d("0.020000")
    assert ready_row.cost_burden_ratio == d("0.250000")
    assert ready_row.depth_coverage_ratio == d("2.500000")
    assert ready_row.reason_codes == ("execution_cost_readiness_ready",)
    assert len({row.signal_digest for row in report.rows}) == 3
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.band == "blocker"
    assert report.input_count == d("0.000000")
    assert report.ready_count == d("0.000000")
    assert report.attention_count == d("0.000000")
    assert report.blocker_count == d("0.000000")
    assert report.average_total_cost_probability == d("0.000000")
    assert report.max_spread_probability == d("0.000000")
    assert report.max_cost_burden_ratio == d("0.000000")
    assert report.min_depth_usdc == d("0.000000")
    assert report.reason_codes == ("missing_execution_cost_readiness_inputs",)
    assert report.reason_code_counts == ()
    assert report.rows == ()


def test_public_payload_is_json_ready_immutable_digest_bound_and_safe() -> None:
    module = api()
    raw_reference = (
        "raw_candidate=alpha candidate_id=cid market_id=mid market_slug=slug "
        "question text source_url=https://example.invalid/a source_text dsn=postgres "
        "table_name=markets token=secret wallet order trade"
    )
    report = build_report(
        sample(
            raw_reference,
            bid_probability=d("0.480000"),
            ask_probability=d("0.620000"),
            mid_probability=d("0.550000"),
            taker_fee_probability=d("0.030000"),
            estimated_slippage_probability=d("0.040000"),
            depth_usdc=d("400.000000"),
            min_depth_usdc=d("1000.000000"),
            edge_to_threshold_probability=d("0.050000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            bid_probability=d("0.480000"),
            ask_probability=d("0.620000"),
            mid_probability=d("0.550000"),
            taker_fee_probability=d("0.030000"),
            estimated_slippage_probability=d("0.040000"),
            depth_usdc=d("400.000000"),
            min_depth_usdc=d("1000.000000"),
            edge_to_threshold_probability=d("0.050000"),
        ),
    )

    payload = module.market_microstructure_execution_cost_readiness_report_payload(
        report,
    )
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-11T14:30:00+00:00"
    assert payload["rows"][0]["signal_digest"] == report.rows[0].signal_digest
    assert payload["rows"][0]["total_cost_probability"] == "0.140000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in walk_json(payload))

    for forbidden in (
        raw_reference,
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "question text",
        "source_url",
        "source_text",
        "https://example.invalid/a",
        "dsn=postgres",
        "table_name",
        "token=secret",
        "wallet",
        "order",
        "trade",
    ):
        assert forbidden.lower() not in rendered_payload.lower()

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["band"] = "ready"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["band"] = "attention"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.market_microstructure_execution_cost_readiness_report_payload(tampered)

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.market_microstructure_execution_cost_readiness_report_payload(
            unsafe_payload,
        )


def test_contracts_are_frozen_decimal_only_strict_and_flag_locked() -> None:
    module = api()
    report = build_report(sample("strict-contracts"))

    for contract in (
        module.MarketMicrostructureExecutionCostReadinessConfig,
        module.MarketMicrostructureExecutionCostReadinessInput,
        module.MarketMicrostructureExecutionCostReadinessRow,
        module.MarketMicrostructureExecutionCostReadinessReasonCodeCount,
        module.MarketMicrostructureExecutionCostReadinessReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{contract.__name__}Child", (contract,), {})

    with pytest.raises(FrozenInstanceError):
        report.band = "ready"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", taker_fee_probability=_DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="datetime"):
        sample("datetime-subclass", observed_at=_DateTimeSubclass(2026, 7, 11, tzinfo=UTC))
    with pytest.raises(ValueError, match="block threshold"):
        module.MarketMicrostructureExecutionCostReadinessConfig(
            cost_burden_attention_threshold=d("1.000000"),
            cost_burden_blocker_threshold=d("0.500000"),
        )
    with pytest.raises(ValueError, match="band"):
        replace(report.rows[0], band="clear")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_cost_burden_ratio=d("99.000000"))


def test_source_excludes_database_network_wallet_live_trading_and_action_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__).lower()

    assert "market_microstructure_execution_cost_readiness_report_payload" in (
        module.__all__
    )
    for banned in (
        "api_key",
        "private_key",
        "psycopg",
        "supabase",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "open(",
        ".read(",
        ".write(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
        "auth",
        "recommendation",
        "sizing",
        "wallet",
    ):
        assert banned not in source
