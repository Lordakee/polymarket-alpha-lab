from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import importlib
import json
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_fee_liquidity_expected_value_guard_report"
)
GENERATED_AT = datetime(2026, 7, 9, 10, 30, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def config(**overrides: object) -> object:
    values: dict[str, object] = {
        "pass_adjusted_expected_value_threshold": d("0.030000"),
        "watch_adjusted_expected_value_threshold": d("0.005000"),
        "minimum_depth_coverage_ratio": d("1.000000"),
        "depth_shortfall_penalty_rate": d("0.020000"),
        "block_total_cost_drag_threshold": d("0.080000"),
    }
    values.update(overrides)
    return api().ResearchMarketFeeLiquidityExpectedValueGuardConfig(**values)


def sample(reference: str, **overrides: Any) -> object:
    values: dict[str, object] = {
        "research_reference": reference,
        "model_probability": d("0.610000"),
        "market_probability": d("0.540000"),
        "taker_fee_rate": d("0.010000"),
        "quoted_spread": d("0.020000"),
        "depth_coverage_ratio": d("0.750000"),
        "slippage_buffer_rate": d("0.005000"),
        "settlement_friction_rate": d("0.003000"),
        "confidence_haircut_rate": d("0.005000"),
    }
    values.update(overrides)
    return api().ResearchMarketFeeLiquidityExpectedValueGuardInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_market_fee_liquidity_expected_value_guard_report(
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
    if isinstance(value, list):
        for item in value:
            yield from walk_json(item)
        return
    yield value


def test_expected_value_guard_subtracts_fee_liquidity_and_confidence_costs() -> None:
    module = api()

    report = build_report(
        sample(
            "raw-candidate pass market-id slug question https://example.invalid "
            "source text token=secret wallet order trade",
        ),
    )

    assert type(report) is module.ResearchMarketFeeLiquidityExpectedValueGuardReport
    assert report.input_count == d("1.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.report_status == "pass"
    assert report.average_adjusted_expected_value_edge == d("0.032000")
    assert report.top_adjusted_expected_value_edge == d("0.032000")
    assert report.max_total_cost_drag == d("0.038000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    row = report.rows[0]
    assert row.rank == d("1.000000")
    assert row.gross_expected_value_edge == d("0.070000")
    assert row.fee_cost == d("0.010000")
    assert row.spread_cost == d("0.010000")
    assert row.liquidity_shortfall_cost == d("0.005000")
    assert row.slippage_buffer_cost == d("0.005000")
    assert row.settlement_friction_cost == d("0.003000")
    assert row.confidence_haircut_cost == d("0.005000")
    assert row.total_fee_liquidity_drag == d("0.033000")
    assert row.total_cost_drag == d("0.038000")
    assert row.adjusted_expected_value_edge == d("0.032000")
    assert row.guard_status == "pass"
    assert row.reason_codes == (
        "confidence_haircut_applied",
        "expected_value_guard_pass",
        "fee_drag_applied",
        "liquidity_shortfall_applied",
        "positive_model_market_edge",
        "settlement_friction_applied",
        "slippage_buffer_applied",
        "spread_drag_applied",
    )


def test_watch_and_block_rows_rank_deterministically_with_allowed_statuses() -> None:
    report = build_report(
        sample(
            "candidate-watch market-id raw question",
            model_probability=d("0.590000"),
            market_probability=d("0.540000"),
        ),
        sample(
            "candidate-block negative edge market slug question",
            model_probability=d("0.510000"),
            market_probability=d("0.540000"),
            taker_fee_rate=d("0.005000"),
            quoted_spread=d("0.010000"),
            depth_coverage_ratio=d("1.000000"),
            slippage_buffer_rate=d("0.001000"),
            settlement_friction_rate=d("0.001000"),
            confidence_haircut_rate=d("0.000000"),
        ),
        sample(
            "candidate-cost-block dsn=postgres table=markets",
            model_probability=d("0.820000"),
            market_probability=d("0.540000"),
            taker_fee_rate=d("0.050000"),
            quoted_spread=d("0.080000"),
            depth_coverage_ratio=d("0.000000"),
            slippage_buffer_rate=d("0.020000"),
            settlement_friction_rate=d("0.020000"),
            confidence_haircut_rate=d("0.000000"),
        ),
    )

    assert report.input_count == d("3.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("2.000000")
    assert report.report_status == "block"
    assert tuple(row.rank for row in report.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.guard_status for row in report.rows) == (
        "block",
        "watch",
        "block",
    )
    assert set(row.guard_status for row in report.rows) <= {"pass", "watch", "block"}
    assert tuple(row.adjusted_expected_value_edge for row in report.rows) == (
        d("0.130000"),
        d("0.012000"),
        d("-0.042000"),
    )
    assert "total_cost_drag_blocks_edge" in report.rows[0].reason_codes
    assert "expected_value_guard_watch" in report.rows[1].reason_codes
    assert "model_edge_not_positive" in report.rows[2].reason_codes


def test_empty_input_blocks_without_rows() -> None:
    report = build_report()

    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_adjusted_expected_value_edge is None
    assert report.top_adjusted_expected_value_edge is None
    assert report.max_total_cost_drag == d("0.000000")
    assert report.report_status == "block"
    assert report.reason_codes == ("missing_expected_value_guard_inputs",)
    assert report.rows == ()


def test_public_payload_is_deterministic_sha256_bound_and_safe() -> None:
    module = api()
    raw_reference = (
        "candidate-alpha market-id market-slug raw question text "
        "https://example.invalid dsn=postgres table=markets token=secret "
        "wallet order trade"
    )
    report = build_report(sample(raw_reference))
    same_report = module.build_research_market_fee_liquidity_expected_value_guard_report(
        (
            sample(
                raw_reference,
                observed_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4)))
                if "observed_at" in {
                    field.name
                    for field in fields(
                        module.ResearchMarketFeeLiquidityExpectedValueGuardInput,
                    )
                }
                else GENERATED_AT,
            ),
        ),
        config=config(),
        generated_at=GENERATED_AT,
    )

    payload = module.research_market_fee_liquidity_expected_value_guard_report_payload(
        report,
    )
    encoded = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T10:30:00+00:00"
    assert payload["rows"][0]["research_digest"] == report.rows[0].research_digest
    assert payload["rows"][0]["adjusted_expected_value_edge"] == "0.032000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (int, float) for value in walk_json(payload))

    for forbidden in (
        raw_reference,
        "candidate-alpha",
        "market-id",
        "market-slug",
        "raw question text",
        "https://",
        "dsn=",
        "table=markets",
        "token=secret",
        "wallet",
        "order",
        "trade",
        "research_reference",
    ):
        assert forbidden.lower() not in encoded.lower()

    changed_report = build_report(
        sample(raw_reference, depth_coverage_ratio=d("0.740000")),
    )
    assert changed_report.derived_validation_digest != report.derived_validation_digest
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_total_cost_drag=d("0.999999"))

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked-market"
    with pytest.raises(ValueError, match="unsafe"):
        module.research_market_fee_liquidity_expected_value_guard_report_payload(
            unsafe_payload,
        )

    tampered_payload = dict(payload)
    tampered_payload["max_total_cost_drag"] = "0.999999"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_fee_liquidity_expected_value_guard_report_payload(
            tampered_payload,
        )


def test_frozen_decimal_only_flags_and_source_surface_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketFeeLiquidityExpectedValueGuardConfig,
        module.ResearchMarketFeeLiquidityExpectedValueGuardInput,
        module.ResearchMarketFeeLiquidityExpectedValueGuardReportRow,
        module.ResearchMarketFeeLiquidityExpectedValueGuardReport,
    ):
        assert contract.__dataclass_params__.frozen is True
        defaults = {field.name: field.default for field in fields(contract)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True
        assert all(field.type not in (int, float) for field in fields(contract))

    with pytest.raises(FrozenInstanceError):
        report.report_status = "pass"  # type: ignore[misc]
    with pytest.raises(TypeError):

        class BadConfig(module.ResearchMarketFeeLiquidityExpectedValueGuardConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        replace(report, paper_only=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", model_probability=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="pass_adjusted_expected_value_threshold"):
        config(
            pass_adjusted_expected_value_threshold=d("0.004000"),
            watch_adjusted_expected_value_threshold=d("0.005000"),
        )
    with pytest.raises(ValueError, match="block_total_cost_drag_threshold"):
        config(block_total_cost_drag_threshold=d("0.000000"))

    source = module.__loader__.get_source(module.__name__).lower()
    assert "research_market_fee_liquidity_expected_value_guard_report_payload" in (
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
