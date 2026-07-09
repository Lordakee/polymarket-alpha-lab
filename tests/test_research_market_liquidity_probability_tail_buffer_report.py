from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_liquidity_probability_tail_buffer_report"
)
GENERATED_AT = datetime(2026, 7, 9, 19, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 18, 45, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DateTimeSubclass(datetime):
    pass


def api() -> ModuleType:
    try:
        return import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> object:
    values: dict[str, object] = {
        "watch_tail_pressure_probability": d("0.080000"),
        "block_tail_pressure_probability": d("0.180000"),
        "watch_buffer_shortfall_probability": d("0.030000"),
        "block_buffer_shortfall_probability": d("0.080000"),
        "watch_stress_probability": d("0.120000"),
        "block_stress_probability": d("0.300000"),
        "watch_min_depth_support_score": d("0.650000"),
        "block_min_depth_support_score": d("0.350000"),
    }
    values.update(overrides)
    return api().ResearchMarketLiquidityProbabilityTailBufferReportConfig(**values)


def sample(reference: str, **overrides: object) -> object:
    values: dict[str, object] = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "model_probability": d("0.510000"),
        "quoted_probability": d("0.500000"),
        "downside_tail_probability": d("0.030000"),
        "upside_tail_probability": d("0.040000"),
        "liquidity_buffer_probability": d("0.080000"),
        "depth_support_score": d("0.900000"),
        "spread_cost_probability": d("0.002000"),
        "slippage_buffer_probability": d("0.003000"),
    }
    values.update(overrides)
    return api().ResearchMarketLiquidityProbabilityTailBufferInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_market_liquidity_probability_tail_buffer_report(
        inputs,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
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


def rendered(value: object) -> str:
    return json.dumps(value, allow_nan=False, sort_keys=True)


def payload_digest(payload: dict[str, Any]) -> str:
    def strip_digest(value: object) -> object:
        if isinstance(value, dict):
            return {
                key: strip_digest(item)
                for key, item in sorted(value.items())
                if key != "derived_validation_digest"
            }
        if isinstance(value, (list, tuple)):
            return [strip_digest(item) for item in value]
        return value

    canonical = json.dumps(
        strip_digest(payload),
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def test_tail_buffer_scores_sorts_and_summarizes_pass_watch_block() -> None:
    module = api()
    passed = sample(
        "candidate-pass market_id=mid market_slug=slug question=https://example.invalid",
    )
    watched = sample(
        "candidate-watch source_url=https://example.invalid/a source_text",
        model_probability=d("0.610000"),
        quoted_probability=d("0.520000"),
        downside_tail_probability=d("0.070000"),
        upside_tail_probability=d("0.120000"),
        liquidity_buffer_probability=d("0.090000"),
        depth_support_score=d("0.600000"),
        spread_cost_probability=d("0.005000"),
        slippage_buffer_probability=d("0.010000"),
    )
    blocked = sample(
        "candidate-block dsn=postgres table_name=markets token=secret wallet order trade",
        model_probability=d("0.900000"),
        quoted_probability=d("0.600000"),
        downside_tail_probability=d("0.250000"),
        upside_tail_probability=d("0.100000"),
        liquidity_buffer_probability=d("0.100000"),
        depth_support_score=d("0.200000"),
        spread_cost_probability=d("0.040000"),
        slippage_buffer_probability=d("0.030000"),
    )

    report = build_report(passed, watched, blocked)
    repeated_report = build_report(blocked, passed, watched)

    assert type(report) is module.ResearchMarketLiquidityProbabilityTailBufferReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_tail_pressure_probability == d("0.136667")
    assert report.max_buffer_shortfall_probability == d("0.150000")
    assert report.max_stress_probability == d("0.770000")
    assert report.min_depth_support_score == d("0.200000")
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    block_row, watch_row, pass_row = report.rows
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]
    assert [row.rank for row in report.rows] == [
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    ]

    assert block_row.absolute_probability_gap == d("0.300000")
    assert block_row.tail_pressure_probability == d("0.250000")
    assert block_row.buffer_shortfall_probability == d("0.150000")
    assert block_row.friction_buffer_probability == d("0.070000")
    assert block_row.stress_probability == d("0.770000")
    assert block_row.reason_codes == (
        "liquidity_probability_tail_buffer_block",
        "tail_pressure_block",
        "buffer_shortfall_block",
        "stress_probability_block",
        "depth_support_block",
        "probability_gap_observed",
        "spread_cost_applied",
        "slippage_buffer_applied",
    )

    assert watch_row.absolute_probability_gap == d("0.090000")
    assert watch_row.tail_pressure_probability == d("0.120000")
    assert watch_row.buffer_shortfall_probability == d("0.030000")
    assert watch_row.friction_buffer_probability == d("0.015000")
    assert watch_row.stress_probability == d("0.255000")
    assert watch_row.reason_codes == (
        "liquidity_probability_tail_buffer_watch",
        "tail_pressure_watch",
        "buffer_shortfall_watch",
        "stress_probability_watch",
        "depth_support_watch",
        "probability_gap_observed",
        "spread_cost_applied",
        "slippage_buffer_applied",
    )

    assert pass_row.absolute_probability_gap == d("0.010000")
    assert pass_row.tail_pressure_probability == d("0.040000")
    assert pass_row.buffer_shortfall_probability == d("0.000000")
    assert pass_row.friction_buffer_probability == d("0.005000")
    assert pass_row.stress_probability == d("0.055000")
    assert pass_row.reason_codes == (
        "liquidity_probability_tail_buffer_pass",
        "probability_gap_observed",
        "spread_cost_applied",
        "slippage_buffer_applied",
    )
    assert len({row.signal_digest for row in report.rows}) == 3
    assert all(len(row.derived_validation_digest) == 64 for row in report.rows)


def test_public_payload_is_deterministic_sha256_bound_immutable_and_safe() -> None:
    module = api()
    raw_reference = (
        "raw_candidate=alpha candidate_id=cid market_id=mid market_slug=slug "
        "question text source_url=https://example.invalid/a source_text dsn=postgres "
        "table_name=markets token=secret wallet order trade"
    )
    report = build_report(
        sample(
            raw_reference,
            model_probability=d("0.900000"),
            quoted_probability=d("0.600000"),
            downside_tail_probability=d("0.250000"),
            upside_tail_probability=d("0.100000"),
            liquidity_buffer_probability=d("0.100000"),
            depth_support_score=d("0.200000"),
            spread_cost_probability=d("0.040000"),
            slippage_buffer_probability=d("0.030000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            model_probability=d("0.900000"),
            quoted_probability=d("0.600000"),
            downside_tail_probability=d("0.250000"),
            upside_tail_probability=d("0.100000"),
            liquidity_buffer_probability=d("0.100000"),
            depth_support_score=d("0.200000"),
            spread_cost_probability=d("0.040000"),
            slippage_buffer_probability=d("0.030000"),
        ),
    )

    payload = module.research_market_liquidity_probability_tail_buffer_report_payload(
        report,
    )
    rendered_payload = rendered(payload)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T19:00:00+00:00"
    assert payload["rows"][0]["signal_digest"] == report.rows[0].signal_digest
    assert payload["rows"][0]["stress_probability"] == "0.770000"
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
        "private_research_reference",
    ):
        assert forbidden.lower() not in rendered_payload.lower()

    with pytest.raises(TypeError, match="payload is immutable"):
        payload["status"] = "pass"
    with pytest.raises(TypeError, match="payload is immutable"):
        payload["rows"].append({})  # type: ignore[attr-defined]

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_liquidity_probability_tail_buffer_report_payload(
            tampered,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_liquidity_probability_tail_buffer_report_payload(
            unsafe_payload,
        )

    invalid_status_payload = dict(payload)
    invalid_status_payload["status"] = "review"
    invalid_status_payload["derived_validation_digest"] = payload_digest(
        invalid_status_payload,
    )
    with pytest.raises(ValueError, match="status"):
        module.research_market_liquidity_probability_tail_buffer_report_payload(
            invalid_status_payload,
        )


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_tail_pressure_probability is None
    assert report.max_buffer_shortfall_probability == d("0.000000")
    assert report.max_stress_probability == d("0.000000")
    assert report.min_depth_support_score is None
    assert report.reason_codes == ("missing_liquidity_probability_tail_buffer_inputs",)
    assert report.reason_code_counts[0].reason_code == (
        "missing_liquidity_probability_tail_buffer_inputs"
    )
    assert report.rows == ()


def test_frozen_decimal_only_flags_and_report_only_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketLiquidityProbabilityTailBufferReportConfig,
        module.ResearchMarketLiquidityProbabilityTailBufferInput,
        module.ResearchMarketLiquidityProbabilityTailBufferReasonCodeCount,
        module.ResearchMarketLiquidityProbabilityTailBufferReportRow,
        module.ResearchMarketLiquidityProbabilityTailBufferReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    with pytest.raises(FrozenInstanceError):
        report.status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(module.ResearchMarketLiquidityProbabilityTailBufferReportConfig):
            pass

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", model_probability=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="must be a datetime"):
        sample(
            "datetime-subclass",
            observed_at=DateTimeSubclass(2026, 7, 9, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="tail_pressure_probability"):
        config(
            watch_tail_pressure_probability=d("0.300000"),
            block_tail_pressure_probability=d("0.250000"),
        )
    with pytest.raises(ValueError, match="depth_support_score"):
        config(
            watch_min_depth_support_score=d("0.400000"),
            block_min_depth_support_score=d("0.500000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_stress_probability=d("0.999999"))

    source = module.__loader__.get_source(module.__name__).lower()
    assert "research_market_liquidity_probability_tail_buffer_report_payload" in (
        module.__all__
    )
    for banned in (
        "api_key",
        "private_key",
        "wallet",
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
        "recommendation",
        "sizing",
    ):
        assert banned not in source
