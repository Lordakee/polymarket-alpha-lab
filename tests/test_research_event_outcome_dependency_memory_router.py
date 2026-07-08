from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from typing import Any

import pytest


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_outcome_dependency_memory_router",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def metrics(**overrides: object):
    module = api()
    values = {
        "aggregate_dependency_strength": d("0.250000"),
        "freshness_score": d("0.950000"),
        "conflict_score": d("0.050000"),
        "calibration_score": d("0.920000"),
        "resolution_lag_score": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchEventOutcomeDependencyMemoryMetrics(**values)


def route(metrics_value=None):
    module = api()
    return module.route_research_event_outcome_dependency_memory(
        metrics_value if metrics_value is not None else metrics(),
    )


def payload(route_value=None) -> dict[str, object]:
    module = api()
    return module.research_event_outcome_dependency_memory_router_payload(
        route_value if route_value is not None else route(),
    )


def assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_scalars(item)


def test_pass_route_uses_aggregate_metrics_only_and_public_safe_payload() -> None:
    result = route()

    assert result.status == "pass"
    assert result.routed_team == "dependency_memory_monitor"
    assert result.dependency_risk_score == d("0.119500")
    assert result.reason_codes == (
        "dependency_memory_router_pass",
        "routed_team_dependency_memory_monitor",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    public_payload = payload(result)
    assert public_payload == {
        "config_version": "research-event-outcome-dependency-memory-router-v0",
        "status": "pass",
        "routed_team": "dependency_memory_monitor",
        "aggregate_dependency_strength": "0.250000",
        "freshness_score": "0.950000",
        "conflict_score": "0.050000",
        "calibration_score": "0.920000",
        "resolution_lag_score": "0.100000",
        "dependency_risk_score": "0.119500",
        "reason_codes": [
            "dependency_memory_router_pass",
            "routed_team_dependency_memory_monitor",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "derived_validation_digest": result.derived_validation_digest,
    }
    assert set(public_payload).isdisjoint(
        {
            "event_id",
            "event_slug",
            "market_id",
            "market_slug",
            "question",
            "source_id",
            "source_url",
        },
    )
    assert_no_public_numeric_scalars(public_payload)


def test_watch_route_uses_dependency_strength_and_freshness_pressure() -> None:
    result = route(
        metrics(
            aggregate_dependency_strength=d("0.700000"),
            freshness_score=d("0.580000"),
            conflict_score=d("0.200000"),
            calibration_score=d("0.850000"),
            resolution_lag_score=d("0.200000"),
        ),
    )

    assert result.status == "watch"
    assert result.routed_team == "dependency_mapping"
    assert result.dependency_risk_score == d("0.386500")
    assert result.reason_codes == (
        "dependency_memory_router_watch",
        "aggregate_dependency_strength_elevated",
        "freshness_decay_elevated",
        "routed_team_dependency_mapping",
    )


def test_block_routes_to_conflict_or_freshness_specialists() -> None:
    conflict = route(
        metrics(
            aggregate_dependency_strength=d("0.700000"),
            freshness_score=d("0.900000"),
            conflict_score=d("0.900000"),
            calibration_score=d("0.700000"),
            resolution_lag_score=d("0.300000"),
        ),
    )
    stale = route(
        metrics(
            aggregate_dependency_strength=d("0.800000"),
            freshness_score=d("0.100000"),
            conflict_score=d("0.300000"),
            calibration_score=d("0.600000"),
            resolution_lag_score=d("0.700000"),
        ),
    )

    assert conflict.status == "block"
    assert conflict.routed_team == "conflict_review"
    assert conflict.dependency_risk_score == d("0.530000")
    assert conflict.reason_codes == (
        "dependency_memory_router_block",
        "aggregate_dependency_strength_elevated",
        "conflict_pressure_blocking",
        "routed_team_conflict_review",
    )
    assert stale.status == "block"
    assert stale.routed_team == "freshness_review"
    assert stale.reason_codes == (
        "dependency_memory_router_block",
        "aggregate_dependency_strength_elevated",
        "freshness_decay_blocking",
        "calibration_gap_elevated",
        "resolution_lag_elevated",
        "routed_team_freshness_review",
    )


def test_statuses_are_exact_and_dataclasses_are_frozen_decimal_only() -> None:
    module = api()
    result = route()

    assert module.ROUTE_STATUSES == ("pass", "watch", "block")
    for klass in (
        module.ResearchEventOutcomeDependencyMemoryMetrics,
        module.ResearchEventOutcomeDependencyMemoryRoute,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        result.status = "watch"  # type: ignore[misc]

    decimal_fields = {
        "aggregate_dependency_strength",
        "freshness_score",
        "conflict_score",
        "calibration_score",
        "resolution_lag_score",
        "dependency_risk_score",
    }
    for field in fields(result):
        if field.name in decimal_fields:
            assert type(getattr(result, field.name)) is Decimal

    with pytest.raises(ValueError, match="aggregate_dependency_strength"):
        metrics(aggregate_dependency_strength=1)
    with pytest.raises(ValueError, match="freshness_score"):
        metrics(freshness_score=0.5)
    with pytest.raises(ValueError, match="conflict_score"):
        metrics(conflict_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="calibration_score"):
        metrics(calibration_score=d("1.000001"))
    with pytest.raises(ValueError, match="resolution_lag_score"):
        metrics(resolution_lag_score=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(metrics(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)


def test_payload_digest_is_deterministic_and_rejects_tampering() -> None:
    module = api()
    first = route()
    second = route()

    assert first == second
    assert payload(first) == payload(second)
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)

    with pytest.raises(ValueError, match="metrics"):
        module.route_research_event_outcome_dependency_memory(object())
    with pytest.raises(ValueError, match="route"):
        module.research_event_outcome_dependency_memory_router_payload(object())
    with pytest.raises(ValueError, match="status"):
        replace(first, status="hold")
    with pytest.raises(ValueError, match="routed_team"):
        replace(first, routed_team="unlisted_team")
    with pytest.raises(ValueError, match="dependency_risk_score"):
        replace(first, dependency_risk_score=d("0.120000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(first, reason_codes=("dependency_memory_router_pass",))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_module_is_report_only_public_safe_and_external_io_free() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
        "json",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
    }
    forbidden_call_names = {
        "open",
        "print",
        "input",
        "compile",
        "eval",
        "exec",
        "connect",
        "execute",
        "fetch",
        "request",
        "submit",
        "cancel",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots = {alias.name.split(".", 1)[0] for alias in node.names}
            assert imported_roots.isdisjoint(forbidden_import_roots)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            callee_name = None
            if isinstance(node.func, ast.Name):
                callee_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee_name = node.func.attr
            assert callee_name not in forbidden_call_names
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")

    lowered_source = source.lower()
    forbidden_text = (
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "live execution",
        "buy",
        "sell",
        "recommend",
        "position sizing",
    )
    assert not any(token in lowered_source for token in forbidden_text)

    public_payload = payload()
    assert public_payload["paper_only"] is True
    assert public_payload["report_only"] is True
    assert public_payload["readonly"] is True
