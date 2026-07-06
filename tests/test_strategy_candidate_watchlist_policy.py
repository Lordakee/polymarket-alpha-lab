from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import strategy_candidate_watchlist_policy as watchlist_module
from polymarket_alpha_lab.strategy_candidate_watchlist_policy import (
    StrategyCandidateWatchlistCandidate,
    StrategyCandidateWatchlistDecision,
    StrategyCandidateWatchlistPolicyConfig,
    classify_strategy_candidate_watchlist_policy,
    strategy_candidate_watchlist_policy_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyCandidateWatchlistPolicyConfig:
    values = {
        "config_version": "strategy-candidate-watchlist-policy-test-v0",
        "minimum_edge": d("0.030000"),
        "minimum_source_count": d("2.000000"),
        "minimum_liquidity_notional": d("1000.000000"),
        "price_review_minutes": d("30.000000"),
        "source_review_minutes": d("360.000000"),
        "liquidity_review_minutes": d("60.000000"),
        "resolution_review_minutes": d("720.000000"),
        "drop_review_minutes": d("0.000000"),
    }
    values.update(overrides)
    return StrategyCandidateWatchlistPolicyConfig(**values)


def candidate(**overrides: object) -> StrategyCandidateWatchlistCandidate:
    values = {
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "best_ask_price": d("0.560000"),
        "target_entry_price": d("0.540000"),
        "estimated_edge": d("0.050000"),
        "source_count": d("3.000000"),
        "available_liquidity_notional": d("2500.000000"),
        "resolution_is_clear": True,
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return StrategyCandidateWatchlistCandidate(**values)


def decide(
    candidate_state: StrategyCandidateWatchlistCandidate | object | None = None,
    policy_config: StrategyCandidateWatchlistPolicyConfig | object | None = None,
) -> StrategyCandidateWatchlistDecision:
    return classify_strategy_candidate_watchlist_policy(
        candidate_state or candidate(),
        policy_config or config(),
    )


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def assert_no_public_numeric_scalars(value: Any) -> None:
    if type(value) in (float, int, Decimal):
        raise AssertionError(f"unexpected public numeric scalar {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numeric_scalars(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_public_numeric_scalars(item)


def test_price_above_target_waits_for_price_with_short_review() -> None:
    decision = decide()

    assert decision.config_version == "strategy-candidate-watchlist-policy-test-v0"
    assert decision.candidate_id == "candidate-001"
    assert decision.market_slug == "fed-cuts-by-september"
    assert decision.outcome_name == "Yes"
    assert decision.watchlist_status == "wait_for_price"
    assert decision.next_review_minutes == d("30.000000")
    assert decision.reason_codes == (
        "strategy_candidate_watchlist_wait_for_price",
        "candidate_screened",
        "entry_price_above_target",
    )
    assert decision.paper_only is True
    assert decision.report_only is True
    assert decision.readonly is True


def test_missing_sources_liquidity_and_resolution_clarity_use_typed_wait_buckets() -> None:
    source = decide(
        candidate(source_count=d("1.000000")),
    )
    liquidity = decide(
        candidate(
            best_ask_price=d("0.530000"),
            available_liquidity_notional=d("250.000000"),
        ),
    )
    resolution = decide(
        candidate(
            best_ask_price=d("0.530000"),
            resolution_is_clear=False,
        ),
    )

    assert source.watchlist_status == "wait_for_source"
    assert source.next_review_minutes == d("360.000000")
    assert source.reason_codes == (
        "strategy_candidate_watchlist_wait_for_source",
        "candidate_screened",
        "source_count_below_minimum",
    )
    assert liquidity.watchlist_status == "wait_for_liquidity"
    assert liquidity.next_review_minutes == d("60.000000")
    assert liquidity.reason_codes == (
        "strategy_candidate_watchlist_wait_for_liquidity",
        "candidate_screened",
        "liquidity_below_minimum",
    )
    assert resolution.watchlist_status == "wait_for_resolution_clarity"
    assert resolution.next_review_minutes == d("720.000000")
    assert resolution.reason_codes == (
        "strategy_candidate_watchlist_wait_for_resolution_clarity",
        "candidate_screened",
        "resolution_clarity_missing",
    )


def test_drop_when_candidate_is_not_trackable_or_already_trade_ready() -> None:
    low_edge = decide(
        candidate(
            best_ask_price=d("0.530000"),
            estimated_edge=d("0.010000"),
        ),
    )
    trade_ready = decide(
        candidate(best_ask_price=d("0.530000")),
    )

    assert low_edge.watchlist_status == "drop"
    assert low_edge.next_review_minutes == d("0.000000")
    assert low_edge.reason_codes == (
        "strategy_candidate_watchlist_drop",
        "candidate_screened",
        "estimated_edge_below_minimum",
    )
    assert trade_ready.watchlist_status == "drop"
    assert trade_ready.reason_codes == (
        "strategy_candidate_watchlist_drop",
        "candidate_screened",
        "candidate_already_watchlist_complete",
    )


def test_outputs_are_frozen_typed_decimal_quantized_and_tuple_only() -> None:
    candidate_state = candidate(best_ask_price=d("0.5600001"))
    decision = decide(candidate_state)

    assert candidate_state.best_ask_price == d("0.560000")
    assert type(candidate_state.best_ask_price) is Decimal
    assert type(candidate_state.source_count) is Decimal
    assert type(decision.next_review_minutes) is Decimal
    assert type(decision.reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        decision.watchlist_status = "drop"  # type: ignore[misc]
    with pytest.raises(ValueError, match="best_ask_price must be a Decimal"):
        replace(candidate_state, best_ask_price=0.56)
    with pytest.raises(ValueError, match="source_count must be a Decimal"):
        replace(candidate_state, source_count=3)
    with pytest.raises(ValueError, match="resolution_is_clear must be a bool"):
        replace(candidate_state, resolution_is_clear=1)
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(candidate_state, reason_codes=["candidate_screened"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(candidate_state, reason_codes=("candidate_screened", "candidate_screened"))
    with pytest.raises(ValueError, match="watchlist_status"):
        replace(decision, watchlist_status="wait")
    with pytest.raises(ValueError, match="next_review_minutes"):
        replace(decision, next_review_minutes=d("-1.000000"))
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(decision, readonly=False)


def test_policy_rejects_wrong_public_types_subclasses_and_bad_config() -> None:
    with pytest.raises(ValueError, match="candidate_state"):
        decide(object())
    with pytest.raises(ValueError, match="config"):
        decide(policy_config=object())
    with pytest.raises(ValueError, match="minimum_edge must be a probability"):
        config(minimum_edge=d("1.000001"))
    with pytest.raises(ValueError, match="minimum_source_count must be positive"):
        config(minimum_source_count=d("0.000000"))
    with pytest.raises(ValueError, match="price_review_minutes must be positive"):
        config(price_review_minutes=d("0.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)


def test_policy_classes_reject_subclassing_surface() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(StrategyCandidateWatchlistPolicyConfig):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class CandidateSubclass(StrategyCandidateWatchlistCandidate):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class DecisionSubclass(StrategyCandidateWatchlistDecision):
            pass


def test_payload_uses_decimal_strings_flags_and_no_floats() -> None:
    decision = decide()

    payload = strategy_candidate_watchlist_policy_payload(decision)

    assert payload == {
        "config_version": "strategy-candidate-watchlist-policy-test-v0",
        "candidate_id": "candidate-001",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "watchlist_status": "wait_for_price",
        "next_review_minutes": "30.000000",
        "best_ask_price": "0.560000",
        "target_entry_price": "0.540000",
        "estimated_edge": "0.050000",
        "source_count": "3.000000",
        "available_liquidity_notional": "2500.000000",
        "resolution_is_clear": True,
        "reason_codes": [
            "strategy_candidate_watchlist_wait_for_price",
            "candidate_screened",
            "entry_price_above_target",
        ],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "derived_validation_digest": decision.derived_validation_digest,
    }
    assert_no_float_values(payload)
    assert_no_public_numeric_scalars(payload)

    with pytest.raises(ValueError, match="decision must be"):
        strategy_candidate_watchlist_policy_payload(object())


def test_decision_uses_tamper_evident_derived_validation_digest() -> None:
    decision = decide()

    assert len(decision.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in decision.derived_validation_digest)

    payload = strategy_candidate_watchlist_policy_payload(decision)
    assert payload["derived_validation_digest"] == decision.derived_validation_digest

    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(decision, estimated_edge=d("0.060000"))


def test_public_payload_rejects_missing_validation_and_unsafe_surface() -> None:
    payload = strategy_candidate_watchlist_policy_payload(decide())

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_candidate_watchlist_policy_payload(missing_digest)

    tampered = dict(payload)
    tampered["watchlist_status"] = "drop"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        strategy_candidate_watchlist_policy_payload(tampered)

    unsafe_key = dict(payload)
    unsafe_key["wallet_address"] = "redacted"
    with pytest.raises(ValueError, match="unsafe"):
        strategy_candidate_watchlist_policy_payload(unsafe_key)

    unsafe_value = dict(payload)
    unsafe_value["market_slug"] = "wallet transfer"
    with pytest.raises(ValueError, match="unsafe"):
        strategy_candidate_watchlist_policy_payload(unsafe_value)


def test_public_payload_rejects_live_auth_wallet_order_network_database_persist_surface() -> None:
    payload = strategy_candidate_watchlist_policy_payload(decide())

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            strategy_candidate_watchlist_policy_payload(unsafe_payload)

    unsafe_values = (
        "live mode enabled",
        "auth token configured",
        "wallet transfer configured",
        "submit order configured",
        "network request configured",
        "database writer configured",
        "persist report configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["outcome_name"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            strategy_candidate_watchlist_policy_payload(unsafe_payload)


def test_module_is_pure_and_has_no_network_db_order_or_io_surface() -> None:
    source = inspect.getsource(watchlist_module)
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
        "order",
        "trade",
    }
    forbidden_attr_fragments = (
        "auth",
        "broker",
        "cancel",
        "client",
        "connect",
        "db",
        "execute",
        "fetch",
        "network",
        "order",
        "persist",
        "request",
        "sign",
        "submit",
        "trade",
        "wallet",
        "write",
    )

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
        elif isinstance(node, ast.Attribute):
            lowered = node.attr.lower()
            assert not any(fragment in lowered for fragment in forbidden_attr_fragments)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            raise AssertionError("module must not contain float literals")
