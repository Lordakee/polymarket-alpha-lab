from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab import strategy_real_time_watchlist_priority_v2 as priority_module
from polymarket_alpha_lab.strategy_real_time_watchlist_priority_v2 import (
    StrategyRealTimeWatchlistPriorityV2Candidate,
    StrategyRealTimeWatchlistPriorityV2Config,
    StrategyRealTimeWatchlistPriorityV2Report,
    build_strategy_real_time_watchlist_priority_v2_report,
    strategy_real_time_watchlist_priority_v2_payload,
)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> StrategyRealTimeWatchlistPriorityV2Config:
    values: dict[str, object] = {
        "config_version": "strategy-real-time-watchlist-priority-v2-test-v0",
        "minimum_priority_score": d("0.100000"),
        "minimum_cost_adjusted_edge": d("0.010000"),
        "minimum_exit_liquidity_feasibility": d("0.500000"),
        "maximum_specialist_uncertainty": d("0.700000"),
        "maximum_information_age_seconds": d("3600.000000"),
        "near_resolution_horizon_hours": d("24.000000"),
        "probability_movement_weight": d("0.500000"),
        "information_staleness_weight": d("0.100000"),
        "source_contradiction_weight": d("0.200000"),
        "liquidity_exit_feasibility_weight": d("0.300000"),
        "resolution_horizon_weight": d("0.100000"),
        "specialist_uncertainty_weight": d("0.400000"),
    }
    values.update(overrides)
    return StrategyRealTimeWatchlistPriorityV2Config(**values)


def candidate(**overrides: object) -> StrategyRealTimeWatchlistPriorityV2Candidate:
    values: dict[str, object] = {
        "candidate_id": "alpha-candidate",
        "market_slug": "fed-cuts-by-september",
        "outcome_name": "Yes",
        "model_probability": d("0.670000"),
        "market_probability": d("0.600000"),
        "previous_market_probability": d("0.550000"),
        "estimated_cost": d("0.010000"),
        "information_age_seconds": d("1800.000000"),
        "source_contradiction_score": d("0.200000"),
        "exit_liquidity_notional": d("3000.000000"),
        "candidate_notional": d("1500.000000"),
        "hours_to_resolution": d("12.000000"),
        "specialist_uncertainty_score": d("0.200000"),
        "reason_codes": ("candidate_screened",),
    }
    values.update(overrides)
    return StrategyRealTimeWatchlistPriorityV2Candidate(**values)


def build_report(
    candidates: tuple[StrategyRealTimeWatchlistPriorityV2Candidate, ...] | None = None,
) -> StrategyRealTimeWatchlistPriorityV2Report:
    candidate_inputs = (candidate(),) if candidates is None else candidates
    return build_strategy_real_time_watchlist_priority_v2_report(
        candidate_inputs,
        config=config(),
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


def test_build_report_prioritizes_cost_adjusted_edge_and_context_signals() -> None:
    alpha = candidate()
    beta = candidate(
        candidate_id="beta-candidate",
        model_probability=d("0.600000"),
        market_probability=d("0.550000"),
        previous_market_probability=d("0.540000"),
        estimated_cost=d("0.020000"),
        information_age_seconds=d("900.000000"),
        source_contradiction_score=d("0.100000"),
        exit_liquidity_notional=d("500.000000"),
        candidate_notional=d("1000.000000"),
        hours_to_resolution=d("48.000000"),
        specialist_uncertainty_score=d("0.400000"),
    )
    gamma = candidate(
        candidate_id="gamma-candidate",
        model_probability=d("0.510000"),
        market_probability=d("0.540000"),
        previous_market_probability=d("0.520000"),
        estimated_cost=d("0.020000"),
        exit_liquidity_notional=d("100.000000"),
        candidate_notional=d("1000.000000"),
        specialist_uncertainty_score=d("0.900000"),
    )

    report = build_report((gamma, beta, alpha))

    assert report.candidate_count == d("3.000000")
    assert report.priority_review_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.report_status == "priority_review"
    assert tuple(row.candidate_id for row in report.rows) == (
        "alpha-candidate",
        "beta-candidate",
        "gamma-candidate",
    )

    alpha_row = report.rows[0]
    assert alpha_row.priority_rank == d("1.000000")
    assert alpha_row.priority_status == "priority_review"
    assert alpha_row.cost_adjusted_edge == d("0.060000")
    assert alpha_row.probability_movement == d("0.050000")
    assert alpha_row.absolute_probability_movement == d("0.050000")
    assert alpha_row.information_staleness_score == d("0.500000")
    assert alpha_row.source_contradiction_score == d("0.200000")
    assert alpha_row.exit_liquidity_feasibility == d("1.000000")
    assert alpha_row.resolution_horizon_score == d("0.500000")
    assert alpha_row.specialist_uncertainty_score == d("0.200000")
    assert alpha_row.priority_score == d("0.445000")
    assert alpha_row.reason_codes == (
        "strategy_real_time_watchlist_priority_v2_priority_review",
        "cost_adjusted_edge_positive",
        "probability_movement_observed",
        "information_staleness_observed",
        "source_contradiction_observed",
        "exit_feasibility_ready",
        "resolution_horizon_near",
        "specialist_uncertainty_observed",
        "candidate_screened",
    )

    assert report.rows[1].priority_status == "watch"
    assert report.rows[1].priority_score == d("0.070000")
    assert report.rows[2].priority_status == "blocked"
    assert report.rows[2].cost_adjusted_edge == d("-0.050000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_empty_report_and_payload_are_readonly_decimal_strings() -> None:
    report = build_report(())
    payload = strategy_real_time_watchlist_priority_v2_payload(report)

    assert report.report_status == "empty_watchlist"
    assert report.candidate_count == d("0.000000")
    assert report.rows == ()
    assert payload["candidate_count"] == "0.000000"
    assert payload["priority_review_count"] == "0.000000"
    assert payload["watch_count"] == "0.000000"
    assert payload["defer_count"] == "0.000000"
    assert payload["blocked_count"] == "0.000000"
    assert payload["top_priority_score"] == "0.000000"
    assert payload["top_cost_adjusted_edge"] == "0.000000"
    assert payload["rows"] == []
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert type(payload["derived_validation_digest"]) is str
    assert_no_public_numeric_scalars(payload)


def test_payload_contains_decimal_strings_rows_and_rejects_tampering() -> None:
    report = build_report()
    payload = strategy_real_time_watchlist_priority_v2_payload(report)

    assert payload["candidate_count"] == "1.000000"
    assert payload["top_priority_score"] == "0.445000"
    assert payload["top_cost_adjusted_edge"] == "0.060000"
    assert payload["rows"] == [
        {
            "priority_rank": "1.000000",
            "candidate_id": "alpha-candidate",
            "market_slug": "fed-cuts-by-september",
            "outcome_name": "Yes",
            "priority_status": "priority_review",
            "priority_score": "0.445000",
            "cost_adjusted_edge": "0.060000",
            "probability_movement": "0.050000",
            "absolute_probability_movement": "0.050000",
            "information_staleness_score": "0.500000",
            "source_contradiction_score": "0.200000",
            "exit_liquidity_feasibility": "1.000000",
            "resolution_horizon_score": "0.500000",
            "specialist_uncertainty_score": "0.200000",
            "model_probability": "0.670000",
            "market_probability": "0.600000",
            "previous_market_probability": "0.550000",
            "estimated_cost": "0.010000",
            "information_age_seconds": "1800.000000",
            "exit_liquidity_notional": "3000.000000",
            "candidate_notional": "1500.000000",
            "hours_to_resolution": "12.000000",
            "reason_codes": [
                "strategy_real_time_watchlist_priority_v2_priority_review",
                "cost_adjusted_edge_positive",
                "probability_movement_observed",
                "information_staleness_observed",
                "source_contradiction_observed",
                "exit_feasibility_ready",
                "resolution_horizon_near",
                "specialist_uncertainty_observed",
                "candidate_screened",
            ],
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert_no_public_numeric_scalars(payload)

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        strategy_real_time_watchlist_priority_v2_payload(missing_digest)

    tampered = dict(payload)
    tampered["candidate_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        strategy_real_time_watchlist_priority_v2_payload(tampered)

    tampered_rows = dict(payload)
    tampered_rows["rows"] = [dict(payload["rows"][0], priority_score="0.999999")]
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        strategy_real_time_watchlist_priority_v2_payload(tampered_rows)


def test_public_payload_rejects_unsafe_public_keys_and_values() -> None:
    payload = strategy_real_time_watchlist_priority_v2_payload(build_report())

    unsafe_keys = (
        "live_mode",
        "auth_token",
        "wallet_address",
        "order_id",
        "network_client",
        "database_url",
        "persist_path",
        "signing_key",
        "mutation_name",
        "buy_command",
        "sell_command",
        "trade_id",
    )
    for unsafe_key in unsafe_keys:
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "redacted"
        with pytest.raises(ValueError, match="unsafe"):
            strategy_real_time_watchlist_priority_v2_payload(unsafe_payload)

    unsafe_values = (
        "live mode configured",
        "auth token configured",
        "wallet transfer configured",
        "submit order configured",
        "network request configured",
        "database writer configured",
        "persist report configured",
        "signing key configured",
        "mutation endpoint configured",
        "buy signal configured",
        "sell signal configured",
        "trade command configured",
    )
    for unsafe_value in unsafe_values:
        unsafe_payload = dict(payload)
        unsafe_payload["rows"] = [dict(payload["rows"][0], market_slug=unsafe_value)]
        with pytest.raises(ValueError, match="unsafe"):
            strategy_real_time_watchlist_priority_v2_payload(unsafe_payload)


def test_frozen_exact_decimal_and_hard_flag_surface() -> None:
    report = build_report()
    candidate_state = candidate(model_probability=d("0.6700001"))

    assert candidate_state.model_probability == d("0.670000")
    assert type(candidate_state.model_probability) is Decimal
    assert type(report.rows[0].priority_score) is Decimal
    assert type(report.rows[0].reason_codes) is tuple
    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="model_probability must be a Decimal"):
        replace(candidate_state, model_probability=0.67)
    with pytest.raises(ValueError, match="model_probability must be a Decimal"):
        replace(candidate_state, model_probability=_DecimalSubclass("0.670000"))
    with pytest.raises(ValueError, match="reason_codes must be a tuple"):
        replace(candidate_state, reason_codes=["candidate_screened"])
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        replace(candidate_state, reason_codes=("candidate_screened", "candidate_screened"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest must match"):
        replace(report, top_priority_score=d("0.999999"))


def test_classes_reject_subclassing_and_wrong_input_types() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):

        class ConfigSubclass(StrategyRealTimeWatchlistPriorityV2Config):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class CandidateSubclass(StrategyRealTimeWatchlistPriorityV2Candidate):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):

        class ReportSubclass(StrategyRealTimeWatchlistPriorityV2Report):
            pass

    with pytest.raises(ValueError, match="candidates must be an iterable"):
        build_strategy_real_time_watchlist_priority_v2_report(
            "not candidates",
            config=config(),
        )
    with pytest.raises(ValueError, match="candidate must be"):
        build_strategy_real_time_watchlist_priority_v2_report(
            (object(),),
            config=config(),
        )
    with pytest.raises(ValueError, match="config must be"):
        build_strategy_real_time_watchlist_priority_v2_report(
            (candidate(),),
            config=object(),
        )


def test_module_is_pure_and_has_no_network_db_order_or_io_surface() -> None:
    source = inspect.getsource(priority_module)
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
        "write",
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


class _DecimalSubclass(Decimal):
    pass
