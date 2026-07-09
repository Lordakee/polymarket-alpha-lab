from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_event_volatility_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    return module.ResearchStrategyEventVolatilityPriorityConfig(**overrides)


def event(
    private_event_reference: str,
    *,
    domain_id: str = "politics",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    probability_previous: Decimal = d("0.400000"),
    probability_current: Decimal = d("0.430000"),
    probability_velocity_24h: Decimal = d("0.020000"),
    evidence_update_count_24h: Decimal = d("1"),
    conflicting_evidence_count_24h: Decimal = d("0"),
    liquidity_depth_ratio: Decimal = d("0.900000"),
    spread_cost_ratio: Decimal = d("0.010000"),
    fee_cost_ratio: Decimal = d("0.005000"),
    resolution_at: datetime = GENERATED_AT + timedelta(days=30),
):
    module = api()
    return module.ResearchStrategyEventVolatilityPriorityInput(
        private_event_reference=private_event_reference,
        domain_id=domain_id,
        observed_at=observed_at,
        probability_previous=probability_previous,
        probability_current=probability_current,
        probability_velocity_24h=probability_velocity_24h,
        evidence_update_count_24h=evidence_update_count_24h,
        conflicting_evidence_count_24h=conflicting_evidence_count_24h,
        liquidity_depth_ratio=liquidity_depth_ratio,
        spread_cost_ratio=spread_cost_ratio,
        fee_cost_ratio=fee_cost_ratio,
        resolution_at=resolution_at,
    )


def build_report(*events, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_event_volatility_priority_report(
        events,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_event_volatility_report_prioritizes_fast_moving_probability_events() -> None:
    raw_block_ref = "private-market://candidate-42?token=secret"
    raw_watch_ref = "postgres://desk:pass@db/table/events?question=who-wins"
    raw_pass_ref = "https://example.invalid/market-slug/live-order-trade-text"
    inputs = (
        event(
            raw_pass_ref,
            domain_id="macro",
        ),
        event(
            raw_block_ref,
            probability_previous=d("0.200000"),
            probability_current=d("0.420000"),
            probability_velocity_24h=d("0.190000"),
            evidence_update_count_24h=d("9"),
            conflicting_evidence_count_24h=d("2"),
            liquidity_depth_ratio=d("0.350000"),
            spread_cost_ratio=d("0.070000"),
            fee_cost_ratio=d("0.030000"),
            resolution_at=GENERATED_AT + timedelta(hours=12),
        ),
        event(
            raw_watch_ref,
            domain_id="crypto",
            probability_previous=d("0.500000"),
            probability_current=d("0.570000"),
            probability_velocity_24h=d("0.040000"),
            evidence_update_count_24h=d("4"),
            conflicting_evidence_count_24h=d("0"),
            liquidity_depth_ratio=d("0.750000"),
            spread_cost_ratio=d("0.025000"),
            fee_cost_ratio=d("0.015000"),
            resolution_at=GENERATED_AT + timedelta(days=3),
        ),
    )

    report = build_report(*inputs)
    reversed_report = build_report(*reversed(inputs))

    assert report.status == "block"
    assert report.event_count == d("3")
    assert report.block_event_count == d("1")
    assert report.watch_event_count == d("1")
    assert report.pass_event_count == d("1")
    assert report.manual_research_event_count == d("2")
    assert report.manual_research_event_ratio == d("0.666667")
    assert report.max_manual_research_priority_score == d("1.000000")
    assert report.max_probability_volatility_score == d("0.220000")
    assert report.max_evidence_churn_score == d("1.000000")
    assert report.max_cost_drag_ratio == d("0.100000")
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.priority_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert tuple(len(row.event_reference_digest) for row in report.rows) == (64, 64, 64)
    assert tuple(row.domain_id for row in report.rows) == ("politics", "crypto", "macro")

    blocked = report.rows[0]
    assert blocked.probability_move_abs == d("0.220000")
    assert blocked.evidence_churn_score == d("1.000000")
    assert blocked.liquidity_reliability_gap_ratio == d("0.650000")
    assert blocked.cost_drag_ratio == d("0.100000")
    assert blocked.seconds_to_resolution == d("43200.000000")
    assert blocked.resolution_proximity_score == d("0.928571")
    assert blocked.reason_codes == (
        "event_volatility_priority_probability_volatility_block",
        "event_volatility_priority_evidence_churn_block",
        "event_volatility_priority_liquidity_reliability_block",
        "event_volatility_priority_cost_drag_block",
        "event_volatility_priority_resolution_proximity_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.probability_volatility_score == d("0.070000")
    assert watched.evidence_churn_score == d("0.500000")
    assert watched.reason_codes == (
        "event_volatility_priority_probability_volatility_watch",
        "event_volatility_priority_evidence_churn_watch",
        "event_volatility_priority_liquidity_reliability_watch",
        "event_volatility_priority_cost_drag_watch",
        "event_volatility_priority_resolution_proximity_watch",
    )
    assert report.rows[2].reason_codes == ("event_volatility_priority_clear",)

    payload = api().research_strategy_event_volatility_priority_report_payload(report)
    reversed_payload = api().research_strategy_event_volatility_priority_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["manual_research_priority_score"] == "1.000000"
    assert payload["rows"][0]["event_reference_digest"] == blocked.event_reference_digest
    assert _float_paths(payload) == ()
    payload_json = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "candidate-42",
        "market-slug",
        "question",
        "https://",
        "postgres://",
        "token",
        "wallet",
        "order",
        "trade",
        "live",
        "table/events",
    ):
        assert forbidden not in payload_json


def test_event_volatility_report_validates_report_only_shape_and_public_scope() -> None:
    module = api()

    assert module.STATUSES == ("pass", "watch", "block")
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVENT_VOLATILITY_PRIORITY_CONFIG_VERSION",
        "STATUSES",
        "ResearchStrategyEventVolatilityPriorityConfig",
        "ResearchStrategyEventVolatilityPriorityInput",
        "ResearchStrategyEventVolatilityPriorityReport",
        "ResearchStrategyEventVolatilityPriorityRow",
        "build_research_strategy_event_volatility_priority_report",
        "research_strategy_event_volatility_priority_report_digest",
        "research_strategy_event_volatility_priority_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(event("private://raw-candidate-wallet-token"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="probability_current must be a Decimal"):
        event("private://float", probability_current=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            event("private://zone"),
            generated_at=datetime(
                2026,
                7,
                8,
                8,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="private_event_reference values must be unique"):
        build_report(event("private://dup"), event("private://dup"))
    with pytest.raises(ValueError, match="resolution_at must not be before generated_at"):
        build_report(event("private://resolved", resolution_at=GENERATED_AT - timedelta(seconds=1)))
    with pytest.raises(ValueError, match="volatility_block_ratio"):
        config(volatility_watch_ratio=d("0.200000"), volatility_block_ratio=d("0.100000"))

    empty = build_report()
    assert empty.status == "pass"
    assert empty.reason_codes == ("event_volatility_priority_empty",)
    assert empty.event_count == d("0")
    assert empty.rows == ()

    payload = module.research_strategy_event_volatility_priority_report_payload(report)
    assert module.research_strategy_event_volatility_priority_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def test_payload_helper_rejects_digest_tampering_and_public_surface_leaks() -> None:
    module = api()
    report = build_report(event("private://safe-raw-market-token"))
    payload = module.research_strategy_event_volatility_priority_report_payload(report)

    tampered = dict(payload)
    tampered["event_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_event_volatility_priority_report_payload(tampered)

    recomputed_count = dict(payload)
    recomputed_count["event_count"] = "9"
    recomputed_count["derived_validation_digest"] = canonical_digest(recomputed_count)
    with pytest.raises(ValueError, match="event_count must match rows"):
        module.research_strategy_event_volatility_priority_report_payload(recomputed_count)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    downgraded["derived_validation_digest"] = canonical_digest(downgraded)
    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_event_volatility_priority_report_payload(downgraded)

    leaked_value = dict(payload)
    leaked_value["raw_reference"] = "https://example.invalid/market-slug?token=secret"
    leaked_value["derived_validation_digest"] = canonical_digest(leaked_value)
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_strategy_event_volatility_priority_report_payload(leaked_value)

    leaked_key = dict(payload)
    leaked_key["market_slug"] = "redacted"
    leaked_key["derived_validation_digest"] = canonical_digest(leaked_key)
    with pytest.raises(ValueError, match="unsafe public"):
        module.research_strategy_event_volatility_priority_report_payload(leaked_key)

    unexpected_key = dict(payload)
    unexpected_key["public_note"] = "redacted"
    unexpected_key["derived_validation_digest"] = canonical_digest(unexpected_key)
    with pytest.raises(ValueError, match="unexpected public field"):
        module.research_strategy_event_volatility_priority_report_payload(unexpected_key)

    shifted_time = dict(payload)
    shifted_time["generated_at"] = "2026-07-08T08:00:00-04:00"
    shifted_time["derived_validation_digest"] = canonical_digest(shifted_time)
    with pytest.raises(ValueError, match="canonical UTC ISO datetime"):
        module.research_strategy_event_volatility_priority_report_payload(shifted_time)

    numeric = dict(payload)
    numeric["event_count"] = 1
    numeric["derived_validation_digest"] = canonical_digest(numeric)
    with pytest.raises(ValueError, match="public numeric values"):
        module.research_strategy_event_volatility_priority_report_payload(numeric)


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()
