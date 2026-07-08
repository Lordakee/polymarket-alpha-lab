from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_market_fee_regime_change_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "taker_fee_watch_delta_bps": d("1.000000"),
        "taker_fee_block_delta_bps": d("3.000000"),
        "spread_cost_watch_drift": d("0.005000"),
        "spread_cost_block_drift": d("0.015000"),
        "settlement_friction_watch_drift": d("0.005000"),
        "settlement_friction_block_drift": d("0.015000"),
        "cost_age_watch_seconds": d("3600.000000"),
        "cost_age_block_seconds": d("14400.000000"),
        "manual_recheck_watch_urgency": d("0.500000"),
        "manual_recheck_block_urgency": d("0.800000"),
    }
    values.update(overrides)
    return module.ResearchMarketFeeRegimeChangeWatchConfig(**values)


def cost_input(
    screening_key: str,
    *,
    prior_taker_fee_bps: Decimal = d("2.000000"),
    current_taker_fee_bps: Decimal = d("2.200000"),
    prior_spread_cost: Decimal = d("0.010000"),
    current_spread_cost: Decimal = d("0.011000"),
    prior_settlement_friction: Decimal = d("0.020000"),
    current_settlement_friction: Decimal = d("0.021000"),
    cost_observed_at: datetime = GENERATED_AT - timedelta(minutes=10),
    manual_recheck_urgency: Decimal = d("0.100000"),
) -> Any:
    module = api()
    return module.ResearchMarketFeeRegimeChangeWatchInput(
        screening_key=screening_key,
        prior_taker_fee_bps=prior_taker_fee_bps,
        current_taker_fee_bps=current_taker_fee_bps,
        prior_spread_cost=prior_spread_cost,
        current_spread_cost=current_spread_cost,
        prior_settlement_friction=prior_settlement_friction,
        current_settlement_friction=current_settlement_friction,
        cost_observed_at=cost_observed_at,
        manual_recheck_urgency=manual_recheck_urgency,
    )


def build_report(*inputs: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_market_fee_regime_change_watch_report(
        inputs,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def assert_no_numeric_payload_values(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError(f"public payload numeric was not a string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_numeric_payload_values(item)


def test_fee_regime_change_watch_report_aggregates_pass_watch_block_inputs() -> None:
    report = build_report(
        cost_input("clear-costs"),
        cost_input(
            "watch-costs",
            current_taker_fee_bps=d("3.500000"),
            current_spread_cost=d("0.016000"),
            current_settlement_friction=d("0.026000"),
            cost_observed_at=GENERATED_AT - timedelta(seconds=4000),
            manual_recheck_urgency=d("0.600000"),
        ),
        cost_input(
            "block-costs",
            current_taker_fee_bps=d("6.000000"),
            current_spread_cost=d("0.030000"),
            current_settlement_friction=d("0.040000"),
            cost_observed_at=GENERATED_AT - timedelta(hours=5),
            manual_recheck_urgency=d("0.900000"),
        ),
    )

    assert report.status == "block"
    assert report.screening_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.max_taker_fee_delta_bps == d("4.000000")
    assert report.max_spread_cost_drift == d("0.020000")
    assert report.max_settlement_friction_drift == d("0.020000")
    assert report.max_cost_age_seconds == d("18000.000000")
    assert report.max_manual_recheck_urgency == d("0.900000")
    assert tuple(row.screening_key for row in report.rows) == (
        "block-costs",
        "watch-costs",
        "clear-costs",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.rows[0].reason_codes == (
        "taker_fee_change_block",
        "spread_cost_drift_block",
        "settlement_friction_drift_block",
        "cost_timestamp_age_block",
        "manual_recheck_urgency_block",
    )
    assert report.rows[1].reason_codes == (
        "taker_fee_change_watch",
        "spread_cost_drift_watch",
        "settlement_friction_drift_watch",
        "cost_timestamp_age_watch",
        "manual_recheck_urgency_watch",
    )
    assert report.rows[2].reason_codes == ("fee_regime_change_clear",)
    assert report.reason_codes == (
        "taker_fee_change_block",
        "spread_cost_drift_block",
        "settlement_friction_drift_block",
        "cost_timestamp_age_block",
        "manual_recheck_urgency_block",
        "taker_fee_change_watch",
        "spread_cost_drift_watch",
        "settlement_friction_drift_watch",
        "cost_timestamp_age_watch",
        "manual_recheck_urgency_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_fee_regime_change_statuses_are_exactly_pass_watch_block() -> None:
    module = api()
    empty_report = build_report()
    pass_report = build_report(cost_input("clear-costs"))
    watch_report = build_report(
        cost_input("watch-costs", manual_recheck_urgency=d("0.500000")),
    )
    block_report = build_report(
        cost_input("block-costs", manual_recheck_urgency=d("0.800000")),
    )

    assert module.STATUSES == ("pass", "watch", "block")
    assert empty_report.status == "pass"
    assert empty_report.reason_codes == ("fee_regime_change_watch_empty",)
    assert pass_report.status == "pass"
    assert pass_report.rows[0].status == "pass"
    assert watch_report.status == "watch"
    assert watch_report.rows[0].status == "watch"
    assert block_report.status == "block"
    assert block_report.rows[0].status == "block"


def test_fee_regime_change_payload_is_deterministic_and_digest_verified() -> None:
    module = api()
    inputs = (
        cost_input("clear-costs"),
        cost_input(
            "watch-costs",
            current_taker_fee_bps=d("3.500000"),
            manual_recheck_urgency=d("0.600000"),
        ),
    )

    payload = module.research_market_fee_regime_change_watch_report_payload(
        build_report(*inputs),
    )
    reversed_payload = module.research_market_fee_regime_change_watch_report_payload(
        build_report(*reversed(inputs)),
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["screening_key"] == "watch-costs"
    assert payload["rows"][0]["taker_fee_delta_bps"] == "1.500000"
    assert payload["rows"][0]["cost_age_seconds"] == "600.000000"
    assert_no_numeric_payload_values(payload)
    assert json.dumps(payload, sort_keys=True)
    assert module.research_market_fee_regime_change_watch_report_payload(
        dict(payload),
    ) == payload

    tampered_payload = dict(payload)
    tampered_payload["status"] = "pass"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_market_fee_regime_change_watch_report_payload(tampered_payload)
    with pytest.raises(ValueError, match="public payload numerics"):
        module.research_market_fee_regime_change_watch_report_payload(
            {**payload, "screening_count": 2},
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.research_market_fee_regime_change_watch_report_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.research_market_fee_regime_change_watch_report_payload(
            {**payload, "wallet_address": "0xabc"},
        )


def test_fee_regime_change_report_is_frozen_decimal_only_and_tamper_evident() -> None:
    module = api()
    report = build_report(cost_input("clear-costs"))

    assert is_dataclass(config())
    assert is_dataclass(cost_input("clear-costs"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(ValueError, match="taker_fee_watch_delta_bps must be a Decimal"):
        config(taker_fee_watch_delta_bps=1)
    with pytest.raises(ValueError, match="spread_cost_watch_drift must be a Decimal"):
        config(spread_cost_watch_drift=_DecimalSubclass("0.005000"))
    with pytest.raises(ValueError, match="current_spread_cost must be a Decimal"):
        cost_input("bad-costs", current_spread_cost=0.011)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_market_fee_regime_change_watch_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="cost_observed_at must not be in the future"):
        build_report(cost_input("future-costs", cost_observed_at=GENERATED_AT))
    with pytest.raises(ValueError, match="manual_recheck_block_urgency must exceed"):
        config(manual_recheck_watch_urgency=d("0.800000"))
    with pytest.raises(ValueError, match="report_only"):
        replace(report, report_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(report, status="ready")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)


def test_fee_regime_change_module_is_pure_report_only_scope() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for fragment in (
        "auth",
        "broker",
        "database",
        "network",
        "order",
        "private_key",
        "recommendation",
        "signing",
        "sizing",
        "trade",
        "wallet",
    ):
        assert fragment not in lowered

    tree = ast.parse(source)
    forbidden_import_roots = {
        "builtins",
        "http",
        "io",
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
        "order",
        "trade",
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
