from __future__ import annotations

import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_memory_source_confidence_router_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_memory_source_confidence_router_report.py",
)
GENERATED_AT = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _module() -> Any:
    spec = importlib.util.find_spec(MODULE_NAME)
    assert spec is not None, "memory source confidence router report module is missing"
    return importlib.import_module(MODULE_NAME)


def _config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_REPORT_VERSION
        ),
        "min_pass_route_score": d("0.700000"),
        "min_watch_route_score": d("0.400000"),
        "min_pass_memory_confidence_score": d("0.700000"),
        "min_watch_memory_confidence_score": d("0.500000"),
        "min_pass_source_confidence_score": d("0.700000"),
        "min_watch_source_confidence_score": d("0.500000"),
        "min_pass_trace_confidence_score": d("0.700000"),
        "min_watch_trace_confidence_score": d("0.500000"),
        "min_pass_freshness_score": d("0.700000"),
        "min_watch_freshness_score": d("0.500000"),
        "max_pass_conflict_score": d("0.200000"),
        "max_watch_conflict_score": d("0.500000"),
        "memory_confidence_weight": d("0.350000"),
        "source_confidence_weight": d("0.300000"),
        "trace_confidence_weight": d("0.200000"),
        "freshness_weight": d("0.150000"),
        "conflict_drag": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMemorySourceConfidenceRouterConfig(**values)


def _input(
    module: Any,
    route_ref: str = "memory-route-alpha",
    **overrides: object,
) -> Any:
    values = {
        "route_ref": route_ref,
        "evaluated_at": GENERATED_AT - timedelta(minutes=15),
        "memory_confidence_score": d("0.900000"),
        "source_confidence_score": d("0.850000"),
        "trace_confidence_score": d("0.800000"),
        "freshness_score": d("0.900000"),
        "conflict_score": d("0.050000"),
        "reason_codes": ("memory_source_confidence_route_ready",),
    }
    values.update(overrides)
    return module.ResearchStrategyMemorySourceConfidenceRouterInput(**values)


def _report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    cfg: Any | None = None,
    generated_at: datetime = GENERATED_AT,
) -> Any:
    return module.build_research_strategy_memory_source_confidence_router_report(
        rows,
        generated_at=generated_at,
        config=cfg or _config(module),
    )


def test_builds_pass_watch_and_block_router_rows_without_raw_route_leakage() -> None:
    module = _module()
    raw_private_ref = (
        "candidate=alpha&market=hidden&source_url=https://example.invalid/"
        "path?token=secret&dsn=postgres://db/table&raw_text=do-not-leak"
    )

    summary = _report(
        module,
        (
            _input(module, raw_private_ref),
            _input(
                module,
                "memory-route-watch",
                memory_confidence_score=d("0.650000"),
                source_confidence_score=d("0.620000"),
                trace_confidence_score=d("0.700000"),
                freshness_score=d("0.650000"),
                conflict_score=d("0.300000"),
                reason_codes=("memory_source_confidence_review_requested",),
            ),
            _input(
                module,
                "memory-route-block",
                memory_confidence_score=d("0.350000"),
                source_confidence_score=d("0.450000"),
                trace_confidence_score=d("0.300000"),
                freshness_score=d("0.500000"),
                conflict_score=d("0.700000"),
                reason_codes=("memory_source_confidence_review_requested",),
            ),
        ),
    )

    assert module.RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(summary)
    assert type(summary) is module.ResearchStrategyMemorySourceConfidenceRouterReport
    assert summary.status == "block"
    assert summary.route_count == d("3.000000")
    assert summary.pass_count == d("1.000000")
    assert summary.watch_count == d("1.000000")
    assert summary.block_count == d("1.000000")
    assert summary.average_route_score == d("0.461167")
    assert summary.lowest_route_score == d("0.042500")
    assert summary.highest_conflict_score == d("0.700000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.status for row in summary.rows) == ("block", "watch", "pass")

    blocked = summary.rows[0]
    assert blocked.aggregate_row_number == d("1.000000")
    assert blocked.route_score == d("0.042500")
    assert blocked.reason_codes == (
        "memory_source_confidence_review_requested",
        "route_score_block",
        "memory_confidence_block",
        "source_confidence_block",
        "trace_confidence_block",
        "conflict_block",
    )

    watched = summary.rows[1]
    assert watched.aggregate_row_number == d("2.000000")
    assert watched.route_score == d("0.501000")
    assert watched.reason_codes == (
        "memory_source_confidence_review_requested",
        "route_score_watch",
        "memory_confidence_watch",
        "source_confidence_watch",
        "freshness_watch",
        "conflict_watch",
    )

    passed = summary.rows[2]
    assert passed.aggregate_row_number == d("3.000000")
    assert passed.route_score == d("0.840000")
    assert passed.reason_codes == (
        "memory_source_confidence_router_pass",
        "memory_source_confidence_route_ready",
    )
    assert len(passed.route_digest) == 71
    assert passed.route_digest.startswith("sha256:")
    assert len(passed.derived_validation_digest) == 64

    payload_json = json.dumps(summary.payload, sort_keys=True).lower()
    for private_fragment in (
        "candidate=alpha",
        "market=hidden",
        "source_url",
        "https://",
        "token=secret",
        "postgres://",
        "raw_text",
        "do-not-leak",
    ):
        assert private_fragment not in payload_json

    reason_count_by_code = {
        item.reason_code: item for item in summary.reason_code_counts
    }
    assert reason_count_by_code["conflict_watch"].count == d("1.000000")
    assert reason_count_by_code["memory_source_confidence_router_pass"].row_ratio == d(
        "0.333333",
    )


def test_payload_is_deterministic_json_ready_and_digest_validated() -> None:
    module = _module()
    first = _report(
        module,
        (
            _input(module, "route-b"),
            _input(module, "route-a"),
        ),
    )
    second = _report(
        module,
        (
            _input(module, "route-a"),
            _input(module, "route-b"),
        ),
    )

    assert first.payload == second.payload
    json.dumps(first.payload, sort_keys=True)
    assert first.payload["route_count"] == "2.000000"
    assert first.payload["rows"][0]["route_score"] == "0.840000"
    assert first.payload["derived_validation_digest"] == first.derived_validation_digest
    assert (
        module.research_strategy_memory_source_confidence_router_report_digest(first)
        == first.derived_validation_digest
    )
    assert len(first.derived_validation_digest) == 64
    _assert_no_decimal_objects(first.payload)
    _assert_no_non_decimal_public_numbers(first)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, reason_codes=("memory_source_confidence_router_report_watch",))


def test_frozen_dataclasses_reject_subclassing_and_enforce_hard_flags() -> None:
    module = _module()
    report = _report(module, (_input(module),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(module.ResearchStrategyMemorySourceConfidenceRouterConfig):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        _config(module, paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        _input(module, report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)


def test_decimal_only_inputs_and_status_domain_are_enforced() -> None:
    module = _module()

    with pytest.raises(ValueError, match="Decimal"):
        _input(module, memory_confidence_score=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="Decimal"):
        _config(module, min_pass_route_score=_DecimalSubclass("0.700000"))

    report = _report(module, (_input(module),))
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")

    for row in report.rows:
        assert row.status in {"pass", "watch", "block"}
    assert report.status in {"pass", "watch", "block"}


def test_no_db_network_wallet_or_live_trading_capabilities_are_exposed() -> None:
    module = _module()
    forbidden_capability_names = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "sqlalchemy",
        "psycopg",
        "web3",
        "ccxt",
    )

    assert set(module.__all__) == {
        "DEFAULT_RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_REPORT_VERSION",
        "RESEARCH_STRATEGY_MEMORY_SOURCE_CONFIDENCE_ROUTER_STATUSES",
        "ResearchStrategyMemorySourceConfidenceRouterConfig",
        "ResearchStrategyMemorySourceConfidenceRouterInput",
        "ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount",
        "ResearchStrategyMemorySourceConfidenceRouterReport",
        "ResearchStrategyMemorySourceConfidenceRouterRow",
        "build_research_strategy_memory_source_confidence_router_report",
        "research_strategy_memory_source_confidence_router_report_digest",
        "research_strategy_memory_source_confidence_router_report_payload",
    }
    for forbidden_name in forbidden_capability_names:
        assert not hasattr(module, forbidden_name)

    forbidden_public_fragments = (
        "candidate",
        "market",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "live",
        "trading",
        "sizing",
        "recommendation",
    )
    for cls in (
        module.ResearchStrategyMemorySourceConfidenceRouterRow,
        module.ResearchStrategyMemorySourceConfidenceRouterReport,
        module.ResearchStrategyMemorySourceConfidenceRouterReasonCodeCount,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(term in lowered for term in forbidden_public_fragments)


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
        assert type(value) is Decimal
        return
    if type(value) is bool or value is None or isinstance(value, (str, datetime)):
        return
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"public numeric value is not Decimal: {value!r}")
    if isinstance(value, tuple):
        for item in value:
            _assert_no_non_decimal_public_numbers(item)
        return
    if is_dataclass(value):
        for field in fields(value):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            _assert_no_non_decimal_public_numbers(getattr(value, field.name))
