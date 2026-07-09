from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_market_fee_liquidity_reversion_pressure_report"
)
MODULE_PATH = (
    Path(__file__).parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_fee_liquidity_reversion_pressure_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 17, 45, tzinfo=UTC)


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
        "watch_raw_reversion_pressure_rate": d("0.100000"),
        "block_raw_reversion_pressure_rate": d("0.250000"),
        "watch_net_reversion_pressure_rate": d("0.050000"),
        "block_net_reversion_pressure_rate": d("0.120000"),
        "watch_fee_liquidity_drag_rate": d("0.030000"),
        "block_fee_liquidity_drag_rate": d("0.080000"),
        "watch_min_depth_coverage_ratio": d("1.000000"),
        "block_min_depth_coverage_ratio": d("0.500000"),
        "depth_shortfall_penalty_rate": d("0.020000"),
    }
    values.update(overrides)
    return api().ResearchMarketFeeLiquidityReversionPressureConfig(**values)


def sample(reference: str, **overrides: object) -> object:
    values: dict[str, object] = {
        "private_research_reference": reference,
        "observed_at": OBSERVED_AT,
        "anchor_probability": d("0.500000"),
        "market_probability": d("0.520000"),
        "taker_fee_rate": d("0.005000"),
        "quoted_spread_rate": d("0.004000"),
        "depth_coverage_ratio": d("2.000000"),
        "slippage_buffer_rate": d("0.001000"),
    }
    values.update(overrides)
    return api().ResearchMarketFeeLiquidityReversionPressureInput(**values)


def build_report(*inputs: object, cfg: object | None = None) -> object:
    return api().build_research_market_fee_liquidity_reversion_pressure_report(
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


def mutable_payload(report: object) -> dict[str, Any]:
    module = api()
    payload = module.research_market_fee_liquidity_reversion_pressure_report_payload(
        report,
    )
    return json.loads(json.dumps(payload, allow_nan=False, sort_keys=True))


def canonical_payload_digest(payload: dict[str, Any]) -> str:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        unsigned_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def resign_payload(payload: dict[str, Any]) -> None:
    payload["derived_validation_digest"] = canonical_payload_digest(payload)


def test_reversion_pressure_scores_sorts_and_summarizes_pass_watch_block() -> None:
    module = api()
    passed = sample(
        "candidate-pass market_id=mid market_slug=slug question=https://example.invalid",
    )
    watched = sample(
        "candidate-watch source_url=https://example.invalid/a source_text",
        market_probability=d("0.620000"),
        taker_fee_rate=d("0.010000"),
        quoted_spread_rate=d("0.020000"),
        depth_coverage_ratio=d("0.800000"),
        slippage_buffer_rate=d("0.005000"),
    )
    blocked = sample(
        "candidate-block dsn=postgres table_name=markets token=secret wallet order trade",
        anchor_probability=d("0.900000"),
        market_probability=d("0.600000"),
        taker_fee_rate=d("0.030000"),
        quoted_spread_rate=d("0.080000"),
        depth_coverage_ratio=d("0.250000"),
        slippage_buffer_rate=d("0.020000"),
    )

    report = build_report(passed, watched, blocked)
    repeated_report = build_report(blocked, passed, watched)

    assert type(report) is module.ResearchMarketFeeLiquidityReversionPressureReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.input_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_raw_reversion_pressure_rate == d("0.146667")
    assert report.average_net_reversion_pressure_rate == d("0.099333")
    assert report.max_net_reversion_pressure_rate == d("0.195000")
    assert report.max_fee_liquidity_drag_rate == d("0.105000")
    assert report.min_depth_coverage_ratio == d("0.250000")
    assert report.derived_validation_digest == repeated_report.derived_validation_digest

    block_row, watch_row, pass_row = report.rows
    assert [row.status for row in report.rows] == ["block", "watch", "pass"]
    assert [row.rank for row in report.rows] == [
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    ]

    assert block_row.raw_reversion_pressure_rate == d("0.300000")
    assert block_row.fee_cost_rate == d("0.030000")
    assert block_row.spread_cost_rate == d("0.040000")
    assert block_row.liquidity_shortfall_cost_rate == d("0.015000")
    assert block_row.fee_liquidity_drag_rate == d("0.105000")
    assert block_row.net_reversion_pressure_rate == d("0.195000")
    assert block_row.depth_coverage_ratio == d("0.250000")
    assert block_row.reason_codes == (
        "fee_liquidity_reversion_pressure_block",
        "raw_reversion_pressure_block",
        "net_reversion_pressure_block",
        "fee_liquidity_drag_block",
        "depth_coverage_block",
        "fee_drag_applied",
        "spread_drag_applied",
        "liquidity_shortfall_applied",
        "slippage_buffer_applied",
    )

    assert watch_row.raw_reversion_pressure_rate == d("0.120000")
    assert watch_row.fee_cost_rate == d("0.010000")
    assert watch_row.spread_cost_rate == d("0.010000")
    assert watch_row.liquidity_shortfall_cost_rate == d("0.004000")
    assert watch_row.fee_liquidity_drag_rate == d("0.029000")
    assert watch_row.net_reversion_pressure_rate == d("0.091000")
    assert watch_row.reason_codes == (
        "fee_liquidity_reversion_pressure_watch",
        "raw_reversion_pressure_watch",
        "net_reversion_pressure_watch",
        "depth_coverage_watch",
        "fee_drag_applied",
        "spread_drag_applied",
        "liquidity_shortfall_applied",
        "slippage_buffer_applied",
    )

    assert pass_row.raw_reversion_pressure_rate == d("0.020000")
    assert pass_row.fee_liquidity_drag_rate == d("0.008000")
    assert pass_row.net_reversion_pressure_rate == d("0.012000")
    assert pass_row.reason_codes == (
        "fee_liquidity_reversion_pressure_pass",
        "fee_drag_applied",
        "spread_drag_applied",
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
            anchor_probability=d("0.900000"),
            market_probability=d("0.600000"),
            taker_fee_rate=d("0.030000"),
            quoted_spread_rate=d("0.080000"),
            depth_coverage_ratio=d("0.250000"),
            slippage_buffer_rate=d("0.020000"),
        ),
    )
    same_instant_report = build_report(
        sample(
            raw_reference,
            observed_at=OBSERVED_AT.astimezone(timezone(timedelta(hours=-4))),
            anchor_probability=d("0.900000"),
            market_probability=d("0.600000"),
            taker_fee_rate=d("0.030000"),
            quoted_spread_rate=d("0.080000"),
            depth_coverage_ratio=d("0.250000"),
            slippage_buffer_rate=d("0.020000"),
        ),
    )

    payload = module.research_market_fee_liquidity_reversion_pressure_report_payload(
        report,
    )
    rendered_payload = json.dumps(payload, allow_nan=False, sort_keys=True)

    assert report.derived_validation_digest == same_instant_report.derived_validation_digest
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert set(report.derived_validation_digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-09T18:00:00+00:00"
    assert payload["rows"][0]["signal_digest"] == report.rows[0].signal_digest
    assert payload["rows"][0]["net_reversion_pressure_rate"] == "0.195000"
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
        module.research_market_fee_liquidity_reversion_pressure_report_payload(
            tampered,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["market_id"] = "leaked"
    with pytest.raises(ValueError, match="unsafe public field"):
        module.research_market_fee_liquidity_reversion_pressure_report_payload(
            unsafe_payload,
        )


def test_public_digest_and_strict_schema_validator_are_canonical() -> None:
    module = api()
    report = build_report(
        sample(
            "strict-schema",
            anchor_probability=d("0.900000"),
            market_probability=d("0.600000"),
            taker_fee_rate=d("0.030000"),
            quoted_spread_rate=d("0.080000"),
            depth_coverage_ratio=d("0.250000"),
            slippage_buffer_rate=d("0.020000"),
        ),
    )
    payload = mutable_payload(report)

    digest_name = (
        "research_market_fee_liquidity_reversion_pressure_report_digest"
    )
    validator_name = (
        "validate_research_market_fee_liquidity_reversion_pressure_public_payload"
    )
    assert digest_name in module.__all__
    assert validator_name in module.__all__
    assert getattr(module, digest_name)(report) == report.derived_validation_digest
    assert report.derived_validation_digest == canonical_payload_digest(payload)
    validator = getattr(module, validator_name)
    assert validator(payload)
    assert validator(report.payload)

    invalid_payloads: list[dict[str, Any]] = []

    extra_top_level = json.loads(json.dumps(payload))
    extra_top_level["diagnostic"] = "safe-extra"
    resign_payload(extra_top_level)
    invalid_payloads.append(extra_top_level)

    missing_top_level = json.loads(json.dumps(payload))
    missing_top_level.pop("average_raw_reversion_pressure_rate")
    resign_payload(missing_top_level)
    invalid_payloads.append(missing_top_level)

    extra_nested = json.loads(json.dumps(payload))
    extra_nested["rows"][0]["diagnostic"] = "safe-extra"
    resign_payload(extra_nested)
    invalid_payloads.append(extra_nested)

    missing_nested = json.loads(json.dumps(payload))
    missing_nested["rows"][0].pop("fee_cost_rate")
    resign_payload(missing_nested)
    invalid_payloads.append(missing_nested)

    noncanonical_decimal = json.loads(json.dumps(payload))
    noncanonical_decimal["input_count"] = "1.0"
    resign_payload(noncanonical_decimal)
    invalid_payloads.append(noncanonical_decimal)

    numeric_decimal = json.loads(json.dumps(payload))
    numeric_decimal["rows"][0]["rank"] = 1
    resign_payload(numeric_decimal)
    invalid_payloads.append(numeric_decimal)

    noncanonical_datetime = json.loads(json.dumps(payload))
    noncanonical_datetime["generated_at"] = "2026-07-09T14:00:00-04:00"
    resign_payload(noncanonical_datetime)
    invalid_payloads.append(noncanonical_datetime)

    tuple_rows = json.loads(json.dumps(payload))
    tuple_rows["rows"] = tuple(tuple_rows["rows"])
    resign_payload(tuple_rows)
    invalid_payloads.append(tuple_rows)

    for invalid_payload in invalid_payloads:
        assert not validator(invalid_payload)
        with pytest.raises(ValueError, match="public schema"):
            module.research_market_fee_liquidity_reversion_pressure_report_payload(
                invalid_payload,
            )


def test_empty_input_blocks_without_row_leakage() -> None:
    report = build_report()

    assert report.status == "block"
    assert report.input_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.average_raw_reversion_pressure_rate is None
    assert report.average_net_reversion_pressure_rate is None
    assert report.max_net_reversion_pressure_rate == d("0.000000")
    assert report.max_fee_liquidity_drag_rate == d("0.000000")
    assert report.min_depth_coverage_ratio is None
    assert report.reason_codes == ("missing_fee_liquidity_reversion_pressure_inputs",)
    assert report.reason_code_counts[0].reason_code == (
        "missing_fee_liquidity_reversion_pressure_inputs"
    )
    assert report.rows == ()


def test_frozen_decimal_only_flags_and_report_only_contracts() -> None:
    module = api()
    report = build_report(sample("contract-check"))

    for contract in (
        module.ResearchMarketFeeLiquidityReversionPressureConfig,
        module.ResearchMarketFeeLiquidityReversionPressureInput,
        module.ResearchMarketFeeLiquidityReversionPressureReasonCodeCount,
        module.ResearchMarketFeeLiquidityReversionPressureReportRow,
        module.ResearchMarketFeeLiquidityReversionPressureReport,
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

        class BadConfig(module.ResearchMarketFeeLiquidityReversionPressureConfig):
            pass

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="must be a Decimal"):
        sample("decimal-subclass", anchor_probability=DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="must be a datetime"):
        sample(
            "datetime-subclass",
            observed_at=DateTimeSubclass(2026, 7, 9, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="raw_reversion_pressure_rate"):
        config(
            watch_raw_reversion_pressure_rate=d("0.300000"),
            block_raw_reversion_pressure_rate=d("0.250000"),
        )
    with pytest.raises(ValueError, match="depth_coverage_ratio"):
        config(
            watch_min_depth_coverage_ratio=d("0.400000"),
            block_min_depth_coverage_ratio=d("0.500000"),
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, max_fee_liquidity_drag_rate=d("0.999999"))

    source = module.__loader__.get_source(module.__name__).lower()
    assert "research_market_fee_liquidity_reversion_pressure_report_payload" in (
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


def test_module_is_a_pure_report_reducer_without_execution_or_storage_surfaces() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "aiohttp",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "supabase",
        "urllib",
        "web3",
    }
    assert imported_roots.isdisjoint(forbidden_imports)

    forbidden_surface_terms = {
        "auth",
        "client",
        "database",
        "execute",
        "network",
        "order",
        "persist",
        "recommendation",
        "sizing",
        "storage",
        "trade",
        "wallet",
    }
    for public_name in module.__all__:
        lowered = public_name.lower()
        assert not any(term in lowered for term in forbidden_surface_terms)

    for contract in (
        module.ResearchMarketFeeLiquidityReversionPressureConfig,
        module.ResearchMarketFeeLiquidityReversionPressureInput,
        module.ResearchMarketFeeLiquidityReversionPressureReasonCodeCount,
        module.ResearchMarketFeeLiquidityReversionPressureReportRow,
        module.ResearchMarketFeeLiquidityReversionPressureReport,
    ):
        for field in fields(contract):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_surface_terms)
