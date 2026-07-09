from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 16, 30, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 16, 10, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return import_module(
        "polymarket_alpha_lab."
        "research_market_liquidity_probability_reversal_buffer_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def sample(reference: str, **overrides: object) -> Any:
    module = api()
    values = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "prior_probability": d("0.500000"),
        "current_probability": d("0.540000"),
        "liquidity_buffer_rate": d("0.120000"),
        "exit_spread_rate": d("0.010000"),
        "exit_slippage_buffer_rate": d("0.004000"),
        "confidence_buffer_rate": d("0.001000"),
        "available_depth": d("2000.000000"),
        "required_depth": d("1000.000000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityProbabilityReversalBufferInput(**values)


def build_report(*inputs: object, config: object | None = None) -> Any:
    module = api()
    return module.build_research_market_liquidity_probability_reversal_buffer_report(
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


def test_reversal_buffer_scores_sorts_and_summarizes_pass_watch_block() -> None:
    module = api()
    passed = sample(
        "candidate-pass market_id=mid market_slug=slug question https://example.invalid",
    )
    watched = sample(
        "candidate-watch source_text source_url=https://example.invalid/a",
        current_probability=d("0.620000"),
        liquidity_buffer_rate=d("0.150000"),
        exit_spread_rate=d("0.020000"),
        exit_slippage_buffer_rate=d("0.010000"),
        confidence_buffer_rate=d("0.005000"),
        available_depth=d("800.000000"),
    )
    blocked = sample(
        "candidate-block dsn=postgres table_name=markets token=secret wallet order trade",
        prior_probability=d("0.900000"),
        current_probability=d("0.600000"),
        liquidity_buffer_rate=d("0.200000"),
        exit_spread_rate=d("0.080000"),
        exit_slippage_buffer_rate=d("0.080000"),
        confidence_buffer_rate=d("0.010000"),
        available_depth=d("200.000000"),
    )

    report = build_report(passed, watched, blocked)
    repeated_report = build_report(blocked, passed, watched)

    assert type(report) is module.ResearchMarketLiquidityProbabilityReversalBufferReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_probability_reversal_rate == d("0.153333")
    assert report.min_net_reversal_buffer_rate == d("-0.230000")
    assert report.max_reversal_to_buffer_ratio == d("4.285714")
    assert report.min_depth_coverage_ratio == d("0.200000")
    assert report.max_friction_buffer_rate == d("0.130000")
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    block_row, watch_row, pass_row = report.rows
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]

    assert block_row.probability_reversal_rate == d("0.300000")
    assert block_row.friction_buffer_rate == d("0.130000")
    assert block_row.usable_liquidity_buffer_rate == d("0.070000")
    assert block_row.net_reversal_buffer_rate == d("-0.230000")
    assert block_row.reversal_to_buffer_ratio == d("4.285714")
    assert block_row.depth_coverage_ratio == d("0.200000")
    assert block_row.reason_codes == (
        "liquidity_probability_reversal_buffer_block",
        "net_reversal_buffer_block",
        "probability_reversal_block",
        "depth_coverage_block",
        "reversal_to_buffer_ratio_block",
        "friction_buffer_block",
    )

    assert watch_row.probability_reversal_rate == d("0.120000")
    assert watch_row.friction_buffer_rate == d("0.025000")
    assert watch_row.usable_liquidity_buffer_rate == d("0.125000")
    assert watch_row.net_reversal_buffer_rate == d("0.005000")
    assert watch_row.reversal_to_buffer_ratio == d("0.960000")
    assert watch_row.depth_coverage_ratio == d("0.800000")
    assert watch_row.reason_codes == (
        "liquidity_probability_reversal_buffer_watch",
        "net_reversal_buffer_watch",
        "probability_reversal_watch",
        "depth_coverage_watch",
        "reversal_to_buffer_ratio_watch",
    )

    assert pass_row.probability_reversal_rate == d("0.040000")
    assert pass_row.friction_buffer_rate == d("0.010000")
    assert pass_row.usable_liquidity_buffer_rate == d("0.110000")
    assert pass_row.net_reversal_buffer_rate == d("0.070000")
    assert pass_row.reversal_to_buffer_ratio == d("0.363636")
    assert pass_row.reason_codes == (
        "liquidity_probability_reversal_buffer_pass",
    )
    assert len({row.signal_digest for row in report.rows}) == 3
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)


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
            prior_probability=d("0.900000"),
            current_probability=d("0.600000"),
            liquidity_buffer_rate=d("0.200000"),
            exit_spread_rate=d("0.080000"),
            exit_slippage_buffer_rate=d("0.080000"),
            confidence_buffer_rate=d("0.010000"),
            available_depth=d("200.000000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            prior_probability=d("0.900000"),
            current_probability=d("0.600000"),
            liquidity_buffer_rate=d("0.200000"),
            exit_spread_rate=d("0.080000"),
            exit_slippage_buffer_rate=d("0.080000"),
            confidence_buffer_rate=d("0.010000"),
            available_depth=d("200.000000"),
        ),
    )

    payload = module.research_market_liquidity_probability_reversal_buffer_report_payload(
        report,
    )
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T16:30:00+00:00"
    assert payload["rows"][0]["signal_digest"] == report.rows[0].signal_digest
    assert payload["rows"][0]["net_reversal_buffer_rate"] == "-0.230000"
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
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_liquidity_probability_reversal_buffer_report_payload(
            tampered,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_liquidity_probability_reversal_buffer_report_payload(
            unsafe_payload,
        )


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_probability_reversal_rate == d("0.000000")
    assert report.min_net_reversal_buffer_rate == d("0.000000")
    assert report.max_reversal_to_buffer_ratio == d("0.000000")
    assert report.min_depth_coverage_ratio == d("0.000000")
    assert report.max_friction_buffer_rate == d("0.000000")
    assert report.reason_codes == (
        "missing_liquidity_probability_reversal_buffer_inputs",
    )
    assert report.reason_code_counts == ()
    assert report.rows == ()


def test_contracts_are_frozen_decimal_only_strict_and_flag_locked() -> None:
    module = api()
    report = build_report(sample("strict-contracts"))

    for contract in (
        module.ResearchMarketLiquidityProbabilityReversalBufferConfig,
        module.ResearchMarketLiquidityProbabilityReversalBufferInput,
        module.ResearchMarketLiquidityProbabilityReversalBufferRow,
        module.ResearchMarketLiquidityProbabilityReversalBufferReasonCodeCount,
        module.ResearchMarketLiquidityProbabilityReversalBufferReport,
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
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", exit_spread_rate=DecimalSubclass("0.001000"))
    with pytest.raises(ValueError, match="datetime"):
        sample(
            "datetime-subclass",
            observed_at=DateTimeSubclass(2026, 7, 9, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="block threshold"):
        module.ResearchMarketLiquidityProbabilityReversalBufferConfig(
            watch_reversal_to_buffer_ratio=d("1.000000"),
            block_reversal_to_buffer_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="clear")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_reversal_to_buffer_ratio=d("99.000000"))


def test_source_excludes_storage_network_wallet_action_and_advice_surfaces() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__).lower()

    assert (
        "research_market_liquidity_probability_reversal_buffer_report_payload"
        in module.__all__
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
        "connect(",
        "place_order",
        "submit_order",
        "cancel_order",
        "sign_order",
        "live_trading",
        "recommendation",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
    ):
        assert banned not in source
