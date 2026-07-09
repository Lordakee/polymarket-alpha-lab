from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_liquidity_cost_memory_floor_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_liquidity_cost_memory_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def market_ref(suffix: str) -> str:
    return f"market_ref_{suffix}"


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_cost_floor": d("0.030000"),
        "block_cost_floor": d("0.075000"),
        "min_memory_observations": d("2.000000"),
    }
    values.update(overrides)
    return module.ResearchMarketLiquidityCostMemoryFloorConfig(**values)


def observation(
    market_key: str,
    *,
    liquidity_cost: Decimal = d("0.020000"),
    memory_observation_count: Decimal = d("4.000000"),
    pressure_score: Decimal = d("0.250000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketLiquidityCostMemoryFloorObservation(
        market_key=market_key,
        market_family="macro",
        cost_bucket="medium",
        liquidity_cost=liquidity_cost,
        memory_observation_count=memory_observation_count,
        pressure_score=pressure_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_market_liquidity_cost_memory_floor_report(
        observations,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_decimal_digest_and_json_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchMarketLiquidityCostMemoryFloorReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.market_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.memory_floor_breach_count == d("0.000000")
    assert report.watch_ratio == d("0.000000")
    assert report.max_liquidity_cost == d("0.000000")
    assert report.max_pressure_score == d("0.000000")
    assert report.reason_codes == ("liquidity_cost_memory_floor_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    payload = module.research_market_liquidity_cost_memory_floor_report_payload(report)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["market_count"] == "0.000000"
    assert payload["watch_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    module.validate_research_market_liquidity_cost_memory_floor_public_payload(payload)
    json.dumps(payload, sort_keys=True)
    _assert_no_public_float_or_int(payload)
    _assert_no_unsafe_public_fragments(payload)


def test_status_rollups_rows_and_payload_are_deterministic() -> None:
    module = api()
    report = build_report(
        observation(
            market_ref("000000000001"),
            liquidity_cost=d("0.010000"),
            memory_observation_count=d("5.000000"),
            pressure_score=d("0.100000"),
        ),
        observation(
            market_ref("000000000002"),
            liquidity_cost=d("0.040000"),
            memory_observation_count=d("5.000000"),
            pressure_score=d("0.300000"),
        ),
        observation(
            market_ref("000000000003"),
            liquidity_cost=d("0.090000"),
            memory_observation_count=d("5.000000"),
            pressure_score=d("0.800000"),
        ),
        observation(
            market_ref("000000000004"),
            liquidity_cost=d("0.020000"),
            memory_observation_count=d("1.000000"),
            pressure_score=d("0.450000"),
        ),
    )

    assert report.status == "block"
    assert report.market_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("2.000000")
    assert report.memory_floor_breach_count == d("1.000000")
    assert report.watch_ratio == d("0.750000")
    assert report.max_liquidity_cost == d("0.090000")
    assert report.max_pressure_score == d("0.800000")
    assert report.reason_codes == (
        "liquidity_cost_memory_floor_watch_cost",
        "liquidity_cost_memory_floor_block_cost",
        "liquidity_cost_memory_floor_insufficient_memory",
    )

    assert tuple(row.market_key for row in report.rows) == (
        market_ref("000000000003"),
        market_ref("000000000004"),
        market_ref("000000000002"),
        market_ref("000000000001"),
    )
    assert tuple(row.status for row in report.rows) == (
        "block",
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.reason_codes for row in report.rows) == (
        ("liquidity_cost_memory_floor_block_cost",),
        ("liquidity_cost_memory_floor_insufficient_memory",),
        ("liquidity_cost_memory_floor_watch_cost",),
        ("liquidity_cost_memory_floor_pass",),
    )

    payload = module.research_market_liquidity_cost_memory_floor_report_payload(report)
    payload_again = module.research_market_liquidity_cost_memory_floor_report_payload(
        build_report(
            observation(
                market_ref("000000000004"),
                liquidity_cost=d("0.020000"),
                memory_observation_count=d("1.000000"),
                pressure_score=d("0.450000"),
            ),
            observation(
                market_ref("000000000001"),
                liquidity_cost=d("0.010000"),
                memory_observation_count=d("5.000000"),
                pressure_score=d("0.100000"),
            ),
            observation(
                market_ref("000000000003"),
                liquidity_cost=d("0.090000"),
                memory_observation_count=d("5.000000"),
                pressure_score=d("0.800000"),
            ),
            observation(
                market_ref("000000000002"),
                liquidity_cost=d("0.040000"),
                memory_observation_count=d("5.000000"),
                pressure_score=d("0.300000"),
            ),
        ),
    )
    assert payload == payload_again
    module.validate_research_market_liquidity_cost_memory_floor_public_payload(payload)


def test_dataclasses_are_frozen_exact_decimal_only_and_flags_are_hard() -> None:
    module = api()
    report = build_report(
        observation(market_ref("000000000005")),
        observation(market_ref("000000000006"), liquidity_cost=d("0.040000")),
    )

    for cls in (
        module.ResearchMarketLiquidityCostMemoryFloorConfig,
        module.ResearchMarketLiquidityCostMemoryFloorObservation,
        module.ResearchMarketLiquidityCostMemoryFloorRow,
        module.ResearchMarketLiquidityCostMemoryFloorReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    _assert_decimal_public_fields(report)
    for row in report.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="watch_cost_floor"):
        config(watch_cost_floor=0.03)
    with pytest.raises(ValueError, match="block_cost_floor"):
        config(block_cost_floor=_DecimalSubclass("0.075000"))
    with pytest.raises(ValueError, match="memory_observation_count"):
        observation(market_ref("000000000007"), memory_observation_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="pressure_score"):
        observation(market_ref("000000000008"), pressure_score=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(market_ref("000000000009"), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_payload_validator_rejects_leaks_numerics_and_digest_tampering() -> None:
    module = api()
    payload = module.research_market_liquidity_cost_memory_floor_report_payload(
        build_report(observation(market_ref("00000000000a"), liquidity_cost=d("0.040000"))),
    )

    module.validate_research_market_liquidity_cost_memory_floor_public_payload(payload)
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            {**payload, "source_url": "redacted"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            {**payload, "rows": [{**payload["rows"][0], "market_key": "https://example.test"}]},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            {**payload, "market_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            {**payload, "market_count": "9.000000"},
        )


def test_public_payload_validator_rejects_recomputed_digest_policy_bypasses() -> None:
    module = api()
    payload = module.research_market_liquidity_cost_memory_floor_report_payload(
        build_report(observation(market_ref("000000000010"), liquidity_cost=d("0.040000"))),
    )

    with pytest.raises(ValueError, match="status"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            _resign_payload({**payload, "status": "hold"}),
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            _resign_payload(
                {
                    **payload,
                    "rows": [{**payload["rows"][0], "readonly": False}],
                },
            ),
        )
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            _resign_payload({**payload, "execution_surface": "none"}),
        )
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            _resign_payload({**payload, "position_size": "0.000000"}),
        )
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_market_liquidity_cost_memory_floor_public_payload(
            _resign_payload({**payload, "recommend": "watch"}),
        )


def test_market_references_are_redacted_and_public_labels_are_canonical() -> None:
    report = build_report(observation(market_ref("000000000011")))
    assert report.rows[0].market_key == market_ref("000000000011")

    with pytest.raises(ValueError, match="market_key"):
        observation("will-fed-cut-rates-before-july")
    with pytest.raises(ValueError, match="market_key"):
        observation("0x1234567890abcdef")
    with pytest.raises(ValueError, match="market_family"):
        api().ResearchMarketLiquidityCostMemoryFloorObservation(
            market_key=market_ref("000000000012"),
            market_family="will fed cut rates?",
            cost_bucket="medium",
            liquidity_cost=d("0.020000"),
            memory_observation_count=d("4.000000"),
            pressure_score=d("0.250000"),
        )
    with pytest.raises(ValueError, match="cost_bucket"):
        api().ResearchMarketLiquidityCostMemoryFloorObservation(
            market_key=market_ref("000000000013"),
            market_family="macro",
            cost_bucket="high-cost",
            liquidity_cost=d("0.020000"),
            memory_observation_count=d("4.000000"),
            pressure_score=d("0.250000"),
        )


def test_module_scope_is_report_only_readonly_and_forbidden_surface_free() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_MARKET_LIQUIDITY_COST_MEMORY_FLOOR_CONFIG_VERSION",
        "ResearchMarketLiquidityCostMemoryFloorConfig",
        "ResearchMarketLiquidityCostMemoryFloorObservation",
        "ResearchMarketLiquidityCostMemoryFloorRow",
        "ResearchMarketLiquidityCostMemoryFloorReport",
        "build_research_market_liquidity_cost_memory_floor_report",
        "research_market_liquidity_cost_memory_floor_report_payload",
        "validate_research_market_liquidity_cost_memory_floor_public_payload",
    }

    tree = ast.parse(MODULE_PATH.read_text())
    imported_roots: set[str] = set()
    called_names: set[str] = set()
    identifier_names: set[str] = set()
    string_values: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_names.add(node.func.attr)
        elif isinstance(node, ast.Name):
            identifier_names.add(node.id)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_values.append(node.value)

    assert not imported_roots.intersection(
        {
            "requests",
            "urllib",
            "httpx",
            "socket",
            "websocket",
            "psycopg",
            "sqlite3",
            "sqlalchemy",
            "supabase",
            "subprocess",
        },
    )
    assert not called_names.intersection(
        {
            "open",
            "connect",
            "request",
            "post",
            "put",
            "patch",
            "delete",
            "execute",
            "commit",
            "rollback",
            "place_order",
            "submit_order",
            "cancel_order",
            "recommend",
        },
    )
    forbidden_identifiers = {
        "auth",
        "database",
        "dsn",
        "live_trading",
        "network_client",
        "order_client",
        "order_size",
        "recommendation",
        "source_text",
        "source_url",
        "table",
        "token",
        "wallet",
    }
    assert not identifier_names.intersection(forbidden_identifiers)
    assert not any(_has_forbidden_literal_fragment(value) for value in string_values)


def _assert_decimal_public_fields(value: Any) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal


def _assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_public_float_or_int(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_public_float_or_int(item)


def _assert_no_unsafe_public_fragments(value: Any) -> None:
    if isinstance(value, str):
        assert not _has_forbidden_literal_fragment(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            assert not _has_forbidden_literal_fragment(key)
            _assert_no_unsafe_public_fragments(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_unsafe_public_fragments(item)


def _resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(unsigned_payload, sort_keys=True, separators=(",", ":")).encode()
    return {
        **unsigned_payload,
        "derived_validation_digest": hashlib.sha256(encoded).hexdigest(),
    }


def _has_forbidden_literal_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(
        fragment in normalized
        for fragment in (
            "://",
            "api_key",
            "auth",
            "database",
            "dsn",
            "execution",
            "live trading",
            "order",
            "position_size",
            "private_key",
            "raw",
            "recommend",
            "recommendation",
            "slug",
            "source text",
            "source url",
            "table",
            "token",
            "wallet",
        )
    )
