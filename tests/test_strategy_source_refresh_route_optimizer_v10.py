from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_source_refresh_route_optimizer_v10.py"
)


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.strategy_source_refresh_route_optimizer_v10",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def candidate(**overrides: object):
    module = api()
    values = {
        "market_id": "market-resolution-source-risk",
        "category": "politics",
        "source_family": "official_resolution",
        "stale_source_count": d("4"),
        "source_reliability": d("0.400000"),
        "resolution_urgency": d("0.850000"),
        "disagreement_rate": d("0.700000"),
        "specialist_queue_pressure": d("0.550000"),
    }
    values.update(overrides)
    return module.StrategySourceRefreshRouteOptimizerV10Candidate(**values)


def route(candidate_value=None):
    module = api()
    return module.route_strategy_source_refresh_route_optimizer_v10(
        candidate_value if candidate_value is not None else candidate(),
    )


def assert_no_public_float_or_int(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_public_float_or_int(item)


def validation_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        {
            key: value
            for key, value in payload.items()
            if key != "validation_digest"
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_stale_unreliable_urgent_disagreement_routes_to_specialist_expedited() -> None:
    decision = route()

    assert is_dataclass(decision)
    assert decision.refresh_route == "specialist_expedited_refresh"
    assert decision.target_refresh_queues == (
        "source_refresh_stale_source_queue",
        "source_refresh_reliability_queue",
        "source_refresh_resolution_urgency_queue",
        "source_refresh_disagreement_queue",
        "source_refresh_specialist_queue",
    )
    assert decision.priority_score == d("100.000000")
    assert decision.reason_codes == (
        "stale_source_count_high",
        "source_reliability_low",
        "resolution_urgency_high",
        "disagreement_rate_high",
        "specialist_queue_pressure_moderate",
        "priority_score_clamped",
        "refresh_route_specialist_expedited_refresh",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True
    assert decision.validation_digest == validation_digest(decision.payload)
    assert decision.payload["validation_digest"] == decision.validation_digest
    assert len(decision.validation_digest) == 64


def test_low_signal_reliable_source_defers_with_payload_decimal_strings() -> None:
    decision = route(
        candidate(
            market_id="market-low-refresh-risk",
            stale_source_count=d("0"),
            source_reliability=d("0.950000"),
            resolution_urgency=d("0.000000"),
            disagreement_rate=d("0.000000"),
            specialist_queue_pressure=d("0.100000"),
        ),
    )

    assert decision.refresh_route == "defer_refresh"
    assert decision.target_refresh_queues == ("source_refresh_monitor_queue",)
    assert decision.priority_score == d("2.750000")
    assert decision.reason_codes == (
        "source_reliability_high",
        "specialist_queue_pressure_low",
        "refresh_route_defer_refresh",
    )

    payload = decision.payload
    assert payload["config_version"] == "strategy-source-refresh-route-optimizer-v10"
    assert payload["market_id"] == "market-low-refresh-risk"
    assert payload["category"] == "politics"
    assert payload["source_family"] == "official_resolution"
    assert payload["stale_source_count"] == "0"
    assert payload["source_reliability"] == "0.950000"
    assert payload["resolution_urgency"] == "0.000000"
    assert payload["disagreement_rate"] == "0.000000"
    assert payload["specialist_queue_pressure"] == "0.100000"
    assert payload["refresh_route"] == "defer_refresh"
    assert payload["target_refresh_queues"] == ["source_refresh_monitor_queue"]
    assert payload["priority_score"] == "2.750000"
    assert payload["validation_digest"] == decision.validation_digest
    assert validation_digest(payload) == decision.validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_float_or_int(payload)


def test_high_specialist_pressure_routes_to_backlog_when_not_emergency() -> None:
    decision = route(
        candidate(
            stale_source_count=d("2"),
            source_reliability=d("0.700000"),
            resolution_urgency=d("0.600000"),
            disagreement_rate=d("0.400000"),
            specialist_queue_pressure=d("0.950000"),
        ),
    )

    assert decision.refresh_route == "specialist_backlog_refresh"
    assert decision.target_refresh_queues == (
        "source_refresh_stale_source_queue",
        "source_refresh_resolution_urgency_queue",
        "source_refresh_disagreement_queue",
        "source_refresh_specialist_queue",
    )
    assert decision.priority_score == d("64.000000")
    assert decision.reason_codes == (
        "stale_source_count_present",
        "source_reliability_watch",
        "resolution_urgency_watch",
        "disagreement_rate_watch",
        "specialist_queue_pressure_high",
        "refresh_route_specialist_backlog_refresh",
    )


def test_moderate_refresh_pressure_routes_to_standard_refresh() -> None:
    decision = route(
        candidate(
            stale_source_count=d("1"),
            source_reliability=d("0.820000"),
            resolution_urgency=d("0.400000"),
            disagreement_rate=d("0.200000"),
            specialist_queue_pressure=d("0.300000"),
        ),
    )

    assert decision.refresh_route == "standard_refresh"
    assert decision.priority_score == d("34.300000")
    assert decision.reason_codes == (
        "stale_source_count_present",
        "source_reliability_watch",
        "resolution_urgency_watch",
        "disagreement_rate_watch",
        "specialist_queue_pressure_low",
        "refresh_route_standard_refresh",
    )


def test_dataclasses_are_frozen_exact_and_decimal_only() -> None:
    module = api()
    decision = route()

    for klass in (
        module.StrategySourceRefreshRouteOptimizerV10Candidate,
        module.StrategySourceRefreshRouteOptimizerV10Decision,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        decision.refresh_route = "defer_refresh"  # type: ignore[misc]

    decimal_fields = {
        "stale_source_count",
        "source_reliability",
        "resolution_urgency",
        "disagreement_rate",
        "specialist_queue_pressure",
        "priority_score",
    }
    for field in fields(decision):
        if field.name in decimal_fields:
            assert type(getattr(decision, field.name)) is Decimal

    with pytest.raises(ValueError, match="stale_source_count"):
        candidate(stale_source_count=4)
    with pytest.raises(ValueError, match="source_reliability"):
        candidate(source_reliability=0.4)
    with pytest.raises(ValueError, match="resolution_urgency"):
        candidate(resolution_urgency=_DecimalSubclass("0.850000"))
    with pytest.raises(ValueError, match="disagreement_rate"):
        candidate(disagreement_rate=d("1.000001"))
    with pytest.raises(ValueError, match="specialist_queue_pressure"):
        candidate(specialist_queue_pressure=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(decision, readonly=False)


def test_validation_rejects_unknown_inputs_and_tampered_outputs() -> None:
    module = api()

    with pytest.raises(ValueError, match="candidate"):
        module.route_strategy_source_refresh_route_optimizer_v10(object())
    with pytest.raises(ValueError, match="market_id"):
        candidate(market_id=" market")
    with pytest.raises(ValueError, match="category"):
        candidate(category="")
    with pytest.raises(ValueError, match="source_family"):
        candidate(source_family=" official")
    with pytest.raises(ValueError, match="stale_source_count"):
        candidate(stale_source_count=d("1.500000"))

    decision = route()
    with pytest.raises(ValueError, match="refresh_route"):
        replace(decision, refresh_route="defer_refresh")
    with pytest.raises(ValueError, match="target_refresh_queues"):
        replace(decision, target_refresh_queues=("source_refresh_monitor_queue",))
    with pytest.raises(ValueError, match="priority_score"):
        replace(decision, priority_score=d("99.000000"))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(decision, reason_codes=("refresh_route_specialist_expedited_refresh",))
    with pytest.raises(ValueError, match="validation_digest"):
        replace(decision, validation_digest="0" * 64)
    with pytest.raises(ValueError, match="payload"):
        replace(decision, payload={**decision.payload, "priority_score": "99.000000"})
    with pytest.raises(ValueError, match="decision"):
        module.strategy_source_refresh_route_optimizer_v10_payload(object())


def test_payload_helper_returns_json_ready_readonly_tamper_evident_payload() -> None:
    module = api()
    decision = route()
    payload = module.strategy_source_refresh_route_optimizer_v10_payload(decision)

    payload_text = repr(payload).lower()
    for forbidden in (
        "live_trading",
        "auth",
        "wallet",
        "account",
        "broker",
        "database",
        "submit_order",
        "place_order",
    ):
        assert forbidden not in payload_text
    assert payload["reason_codes"] == [
        "stale_source_count_high",
        "source_reliability_low",
        "resolution_urgency_high",
        "disagreement_rate_high",
        "specialist_queue_pressure_moderate",
        "priority_score_clamped",
        "refresh_route_specialist_expedited_refresh",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["validation_digest"] == decision.validation_digest
    assert validation_digest(payload) == decision.validation_digest
    assert_no_public_float_or_int(payload)


def test_payload_helper_rejects_unsafe_bypassed_payload_values() -> None:
    module = api()
    decision = route()

    object.__setattr__(
        decision,
        "payload",
        {
            **decision.payload,
            "public_reference": "wallet://private-source",
        },
    )

    with pytest.raises(ValueError, match="unsafe live surface value"):
        module.strategy_source_refresh_route_optimizer_v10_payload(decision)


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    lowered_source = source.lower()
    forbidden_literals = (
        "wallet",
        "private_key",
        "authentication",
        "credential",
        "submit_order",
        "cancel_order",
        "place_order",
        "execute_trade",
    )
    assert not any(token in lowered_source for token in forbidden_literals)

    decision = route()
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True
