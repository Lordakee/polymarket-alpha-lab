from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_market_memory_cost_depth_floor_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_market_memory_cost_depth_floor_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_memory_cost_floor": d("0.030000"),
        "block_memory_cost_floor": d("0.075000"),
        "min_memory_points": d("2.000000"),
        "min_depth_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchMarketMemoryCostDepthFloorConfig(**values)


def observation(
    private_reference: str,
    *,
    segment_key: str = "macro-alpha",
    memory_cost: Decimal = d("0.020000"),
    memory_point_count: Decimal = d("4.000000"),
    depth_ratio: Decimal = d("0.700000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchMarketMemoryCostDepthFloorObservation(
        private_reference=private_reference,
        segment_key=segment_key,
        memory_cost=memory_cost,
        memory_point_count=memory_point_count,
        depth_ratio=depth_ratio,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*observations: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_market_memory_cost_depth_floor_report(
        observations,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_decimal_digest_and_json_safe() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchMarketMemoryCostDepthFloorReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen is True
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.item_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.memory_floor_breach_count == d("0.000000")
    assert report.cost_floor_breach_count == d("0.000000")
    assert report.depth_floor_breach_count == d("0.000000")
    assert report.watch_ratio == d("0.000000")
    assert report.max_memory_cost == d("0.000000")
    assert report.min_depth_ratio_observed == d("0.000000")
    assert report.reason_codes == ("memory_cost_depth_floor_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.derived_validation_digest) == 64

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    payload = module.research_market_memory_cost_depth_floor_report_payload(report)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["item_count"] == "0.000000"
    assert payload["watch_ratio"] == "0.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    module.validate_research_market_memory_cost_depth_floor_public_payload(payload)
    json.dumps(payload, sort_keys=True)
    _assert_no_public_float_or_int(payload)
    _assert_no_private_fragments(payload)


def test_status_rollups_rows_redaction_and_payload_are_deterministic() -> None:
    module = api()
    report = build_report(
        observation(
            "https://markets.example/alpha?token=secret-candidate",
            segment_key="alpha-pass",
            memory_cost=d("0.010000"),
            memory_point_count=d("5.000000"),
            depth_ratio=d("0.900000"),
        ),
        observation(
            "postgres://user:pass@host/db?table=source_text",
            segment_key="beta-watch-cost",
            memory_cost=d("0.040000"),
            memory_point_count=d("5.000000"),
            depth_ratio=d("0.800000"),
        ),
        observation(
            "wallet://live-order/depth-cost",
            segment_key="gamma-block-cost",
            memory_cost=d("0.090000"),
            memory_point_count=d("5.000000"),
            depth_ratio=d("0.700000"),
        ),
        observation(
            "candidate-source-raw-market",
            segment_key="delta-memory-block",
            memory_cost=d("0.020000"),
            memory_point_count=d("1.000000"),
            depth_ratio=d("0.450000"),
        ),
    )

    assert report.status == "block"
    assert report.item_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("2.000000")
    assert report.memory_floor_breach_count == d("1.000000")
    assert report.cost_floor_breach_count == d("2.000000")
    assert report.depth_floor_breach_count == d("1.000000")
    assert report.watch_ratio == d("0.750000")
    assert report.max_memory_cost == d("0.090000")
    assert report.min_depth_ratio_observed == d("0.450000")
    assert report.reason_codes == (
        "memory_cost_depth_floor_watch_cost",
        "memory_cost_depth_floor_block_cost",
        "memory_cost_depth_floor_insufficient_memory",
        "memory_cost_depth_floor_thin_depth",
    )

    assert tuple(row.segment_key for row in report.rows) == (
        "delta-memory-block",
        "gamma-block-cost",
        "beta-watch-cost",
        "alpha-pass",
    )
    assert tuple(row.status for row in report.rows) == (
        "block",
        "block",
        "watch",
        "pass",
    )
    assert tuple(row.reason_codes for row in report.rows) == (
        (
            "memory_cost_depth_floor_insufficient_memory",
            "memory_cost_depth_floor_thin_depth",
        ),
        ("memory_cost_depth_floor_block_cost",),
        ("memory_cost_depth_floor_watch_cost",),
        ("memory_cost_depth_floor_pass",),
    )

    payload = module.research_market_memory_cost_depth_floor_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True).lower()
    for private_fragment in (
        "markets.example",
        "secret-candidate",
        "postgres",
        "source_text",
        "wallet",
        "live-order",
        "candidate-source-raw-market",
    ):
        assert private_fragment not in encoded
    _assert_no_private_fragments(payload)

    payload_again = module.research_market_memory_cost_depth_floor_report_payload(
        build_report(
            observation(
                "candidate-source-raw-market",
                segment_key="delta-memory-block",
                memory_cost=d("0.020000"),
                memory_point_count=d("1.000000"),
                depth_ratio=d("0.450000"),
            ),
            observation(
                "https://markets.example/alpha?token=secret-candidate",
                segment_key="alpha-pass",
                memory_cost=d("0.010000"),
                memory_point_count=d("5.000000"),
                depth_ratio=d("0.900000"),
            ),
            observation(
                "wallet://live-order/depth-cost",
                segment_key="gamma-block-cost",
                memory_cost=d("0.090000"),
                memory_point_count=d("5.000000"),
                depth_ratio=d("0.700000"),
            ),
            observation(
                "postgres://user:pass@host/db?table=source_text",
                segment_key="beta-watch-cost",
                memory_cost=d("0.040000"),
                memory_point_count=d("5.000000"),
                depth_ratio=d("0.800000"),
            ),
        ),
    )
    assert payload == payload_again
    module.validate_research_market_memory_cost_depth_floor_public_payload(payload)


def test_dataclasses_are_frozen_exact_decimal_only_and_flags_are_hard() -> None:
    module = api()
    report = build_report(
        observation("private-a", segment_key="alpha-pass"),
        observation(
            "private-b",
            segment_key="beta-watch",
            memory_cost=d("0.040000"),
        ),
    )

    for cls in (
        module.ResearchMarketMemoryCostDepthFloorConfig,
        module.ResearchMarketMemoryCostDepthFloorObservation,
        module.ResearchMarketMemoryCostDepthFloorRow,
        module.ResearchMarketMemoryCostDepthFloorReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True

    _assert_decimal_public_fields(report)
    for row in report.rows:
        _assert_decimal_public_fields(row)

    with pytest.raises(ValueError, match="watch_memory_cost_floor"):
        config(watch_memory_cost_floor=0.03)
    with pytest.raises(ValueError, match="block_memory_cost_floor"):
        config(block_memory_cost_floor=_DecimalSubclass("0.075000"))
    with pytest.raises(ValueError, match="memory_point_count"):
        observation("private-c", memory_point_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="depth_ratio"):
        observation("private-d", depth_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        observation("private-e", paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_public_payload_validator_rejects_leaks_numerics_and_digest_tampering() -> None:
    module = api()
    payload = module.research_market_memory_cost_depth_floor_report_payload(
        build_report(
            observation(
                "https://private.example/path?token=secret",
                segment_key="alpha-watch",
                memory_cost=d("0.040000"),
            ),
        ),
    )

    module.validate_research_market_memory_cost_depth_floor_public_payload(payload)
    with pytest.raises(ValueError, match="unsafe public field"):
        module.validate_research_market_memory_cost_depth_floor_public_payload(
            {**payload, "source_url": "redacted"},
        )
    with pytest.raises(ValueError, match="unsafe public value"):
        module.validate_research_market_memory_cost_depth_floor_public_payload(
            {
                **payload,
                "rows": [
                    {
                        **payload["rows"][0],
                        "segment_key": "https://private.example/path",
                    },
                ],
            },
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.validate_research_market_memory_cost_depth_floor_public_payload(
            {**payload, "item_count": 1},
        )
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_market_memory_cost_depth_floor_public_payload(
            {**payload, "readonly": False},
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_market_memory_cost_depth_floor_public_payload(
            {**payload, "item_count": "9.000000"},
        )


def test_module_scope_is_report_only_readonly_and_forbidden_surface_free() -> None:
    module = api()

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_MARKET_MEMORY_COST_DEPTH_FLOOR_CONFIG_VERSION",
        "ResearchMarketMemoryCostDepthFloorConfig",
        "ResearchMarketMemoryCostDepthFloorObservation",
        "ResearchMarketMemoryCostDepthFloorRow",
        "ResearchMarketMemoryCostDepthFloorReport",
        "build_research_market_memory_cost_depth_floor_report",
        "research_market_memory_cost_depth_floor_report_payload",
        "validate_research_market_memory_cost_depth_floor_public_payload",
    }

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
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
        "sizing",
        "source_text",
        "source_url",
        "table",
        "token",
        "wallet",
    }
    assert not identifier_names.intersection(forbidden_identifiers)
    assert not any(_has_forbidden_public_fragment(value) for value in string_values)


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


def _assert_no_private_fragments(value: Any) -> None:
    if isinstance(value, str):
        assert not _has_forbidden_public_fragment(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            assert not _has_forbidden_public_fragment(key)
            _assert_no_private_fragments(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_private_fragments(item)


def _has_forbidden_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(
        fragment in normalized
        for fragment in (
            "://",
            "api_key",
            "auth",
            "candidate",
            "database",
            "dsn",
            "live trading",
            "market.example",
            "order",
            "private_key",
            "recommendation",
            "source text",
            "source url",
            "source_",
            "table",
            "token",
            "wallet",
        )
    )
