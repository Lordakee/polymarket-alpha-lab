from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import json
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_fee_liquidity_break_even_report"
NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _api() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def _observation(**overrides: Any) -> object:
    api = _api()
    values = {
        "taker_fee_rate": Decimal("0.010000"),
        "quoted_spread": Decimal("0.020000"),
        "depth_score": Decimal("0.750000"),
        "slippage_buffer": Decimal("0.005000"),
        "settlement_friction": Decimal("0.003000"),
    }
    values.update(overrides)
    return api.ResearchMarketFeeLiquidityBreakEvenObservation(**values)


def _report(observations: tuple[object, ...], *, config: object | None = None) -> object:
    api = _api()
    return api.build_research_market_fee_liquidity_break_even_report(
        observations,
        generated_at=NOW,
        config=config,
    )


def test_break_even_threshold_includes_fee_spread_depth_slippage_and_settlement() -> None:
    api = _api()
    config = api.ResearchMarketFeeLiquidityBreakEvenConfig(
        depth_shortfall_penalty_rate=Decimal("0.020000"),
        pass_threshold=Decimal("0.020000"),
        block_threshold=Decimal("0.050000"),
    )

    report = _report((_observation(),), config=config)

    row = report.rows[0]
    assert row.taker_fee_cost == Decimal("0.010000")
    assert row.spread_cost == Decimal("0.010000")
    assert row.depth_cost == Decimal("0.005000")
    assert row.slippage_buffer_cost == Decimal("0.005000")
    assert row.settlement_friction_cost == Decimal("0.003000")
    assert row.break_even_edge_threshold == Decimal("0.033000")
    assert row.edge_status == "watch"
    assert report.edge_status == "watch"
    assert report.sample_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert row.reason_codes == (
        "fee_component",
        "spread_component",
        "depth_shortfall_component",
        "slippage_component",
        "settlement_component",
        "break_even_watch",
    )


def test_statuses_roll_up_as_pass_watch_and_block_only() -> None:
    api = _api()
    config = api.ResearchMarketFeeLiquidityBreakEvenConfig(
        depth_shortfall_penalty_rate=Decimal("0.020000"),
        pass_threshold=Decimal("0.010000"),
        block_threshold=Decimal("0.050000"),
    )

    report = _report(
        (
            _observation(
                taker_fee_rate=Decimal("0.001000"),
                quoted_spread=Decimal("0.002000"),
                depth_score=Decimal("1.000000"),
                slippage_buffer=Decimal("0.001000"),
                settlement_friction=Decimal("0.001000"),
            ),
            _observation(),
            _observation(
                taker_fee_rate=Decimal("0.030000"),
                quoted_spread=Decimal("0.040000"),
                depth_score=Decimal("0.000000"),
                slippage_buffer=Decimal("0.020000"),
                settlement_friction=Decimal("0.020000"),
            ),
        ),
        config=config,
    )

    statuses = tuple(row.edge_status for row in report.rows)
    assert set(statuses) == {"pass", "watch", "block"}
    assert report.edge_status == "block"
    assert report.pass_count == Decimal("1.000000")
    assert report.watch_count == Decimal("1.000000")
    assert report.block_count == Decimal("1.000000")
    assert set(statuses) <= {"pass", "watch", "block"}


def test_payload_serializes_decimals_as_strings_and_validates_digest() -> None:
    report = _report((_observation(),))

    payload = report.payload
    json.dumps(payload, sort_keys=True)
    assert payload["sample_count"] == "1.000000"
    assert payload["rows"][0]["break_even_edge_threshold"] == "0.033000"
    assert payload["generated_at"] == "2026-01-01T00:00:00+00:00"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert isinstance(payload["derived_validation_digest"], str)
    assert len(payload["derived_validation_digest"]) == 64
    _assert_no_non_decimal_public_numbers(report)
    _assert_no_decimal_objects(payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_dataclasses_are_frozen_reject_subclassing_and_require_hard_flags() -> None:
    api = _api()
    report = _report((_observation(),))

    with pytest.raises(FrozenInstanceError):
        report.edge_status = "pass"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(api.ResearchMarketFeeLiquidityBreakEvenConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        api.ResearchMarketFeeLiquidityBreakEvenConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _observation(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_public_payload_excludes_raw_identifiers_and_live_surfaces() -> None:
    api = _api()
    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "url",
        "text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
    )

    for cls in (
        api.ResearchMarketFeeLiquidityBreakEvenConfig,
        api.ResearchMarketFeeLiquidityBreakEvenObservation,
        api.ResearchMarketFeeLiquidityBreakEvenRow,
        api.ResearchMarketFeeLiquidityBreakEvenReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)

    payload = _report((_observation(),)).payload
    _assert_no_unsafe_payload_strings(payload, forbidden_fragments)

    source = api.__loader__.get_source(api.__name__)
    assert source is not None
    source_forbidden_fragments = tuple(
        "".join(parts)
        for parts in (
            ("candidate", "_", "id"),
            ("market", "_", "id"),
            ("market", "_", "slug"),
            ("source", "_", "url"),
            ("source", "_", "text"),
            ("dsn",),
            ("table",),
            ("token",),
            ("wallet",),
            ("order",),
            ("trade",),
            ("recommend",),
            ("sizing",),
        )
    )
    lowered_source = source.lower()
    for fragment in source_forbidden_fragments:
        assert fragment not in lowered_source

    for forbidden_name in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    ):
        assert not hasattr(api, forbidden_name)


def test_decimal_only_numeric_inputs_are_required() -> None:
    with pytest.raises(ValueError, match="Decimal"):
        _observation(taker_fee_rate=0.01)

    with pytest.raises(ValueError, match="Decimal"):
        _observation(quoted_spread=1)


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload contains a Decimal object")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_decimal_objects(item)
    if isinstance(value, list):
        for item in value:
            _assert_no_decimal_objects(item)


def _assert_no_non_decimal_public_numbers(value: object) -> None:
    if isinstance(value, Decimal):
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if hasattr(value, "__dataclass_fields__"):
        for field in fields(value):
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))


def _assert_no_unsafe_payload_strings(
    value: object,
    forbidden_fragments: tuple[str, ...],
) -> None:
    if type(value) is str:
        lowered = value.lower()
        assert not any(fragment in lowered for fragment in forbidden_fragments)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = key.lower()
            assert not any(fragment in lowered_key for fragment in forbidden_fragments)
            _assert_no_unsafe_payload_strings(item, forbidden_fragments)
        return
    if isinstance(value, list):
        for item in value:
            _assert_no_unsafe_payload_strings(item, forbidden_fragments)
