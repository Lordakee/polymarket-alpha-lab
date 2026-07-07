from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.strategy_candidate_liquidity_exit_capacity_score_v2"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_liquidity_exit_capacity_score_v2.py"
)
OBSERVED_AT = datetime(2026, 7, 7, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing score module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_EXIT_CAPACITY_SCORE_V2_CONFIG_VERSION
        ),
        "watch_min_exit_depth_to_required_capacity_ratio": d("1.250000"),
        "block_min_exit_depth_to_required_capacity_ratio": d("1.000000"),
        "watch_max_spread_ratio": d("0.030000"),
        "block_max_spread_ratio": d("0.060000"),
        "watch_min_seconds_until_market_close": d("172800.000000"),
        "block_min_seconds_until_market_close": d("21600.000000"),
        "watch_max_settlement_lag_seconds": d("86400.000000"),
        "block_max_settlement_lag_seconds": d("259200.000000"),
        "urgency_capacity_buffer_ratio": d("0.500000"),
        "close_proximity_capacity_buffer_ratio": d("0.500000"),
        "settlement_lag_capacity_buffer_ratio": d("0.250000"),
        "minimum_pass_score": d("75.000000"),
        "blocked_max_score": d("25.000000"),
    }
    values.update(overrides)
    return module.StrategyCandidateLiquidityExitCapacityScoreV2Config(**values)


def candidate_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "candidate_id": "candidate_liquidity_exit_capacity_v2",
        "market_slug": "market_liquidity_exit_capacity",
        "observed_at": OBSERVED_AT,
        "expected_position_notional": d("100.000000"),
        "book_depth_notional": d("300.000000"),
        "spread_ratio": d("0.010000"),
        "urgency_ratio": d("0.200000"),
        "seconds_until_market_close": d("604800.000000"),
        "settlement_lag_seconds": ZERO,
        "reason_codes": ("candidate_exit_capacity_input",),
    }
    values.update(overrides)
    return module.StrategyCandidateLiquidityExitCapacityScoreV2Input(**values)


def score(subject: object | None = None, cfg: object | None = None) -> Any:
    module = api()
    return module.score_strategy_candidate_liquidity_exit_capacity_v2(
        candidate_input() if subject is None else subject,
        config=config() if cfg is None else cfg,
    )


def field_values(instance: object) -> dict[str, object]:
    return {field.name: getattr(instance, field.name) for field in fields(instance)}


def assert_no_float_values(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError(f"unexpected float value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    if isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_values(item)


def test_scores_pass_watch_and_blocked_exit_capacity() -> None:
    passed = score()
    watched = score(
        candidate_input(
            candidate_id="candidate_watch",
            market_slug="market_watch",
            book_depth_notional=d("190.000000"),
            spread_ratio=d("0.040000"),
            urgency_ratio=d("0.500000"),
            seconds_until_market_close=d("86400.000000"),
            settlement_lag_seconds=d("172800.000000"),
        ),
    )
    blocked = score(
        candidate_input(
            candidate_id="candidate_blocked",
            market_slug="market_blocked",
            book_depth_notional=d("60.000000"),
            spread_ratio=d("0.070000"),
            urgency_ratio=d("1.000000"),
            seconds_until_market_close=d("3600.000000"),
            settlement_lag_seconds=d("345600.000000"),
        ),
    )

    assert is_dataclass(passed)
    assert passed.required_exit_capacity_notional == d("110.000000")
    assert passed.exit_depth_to_required_capacity_ratio == d("2.727273")
    assert passed.capacity_shortfall_notional == ZERO
    assert passed.depth_capacity_score == d("100.000000")
    assert passed.spread_score == d("83.333333")
    assert passed.urgency_score == d("80.000000")
    assert passed.close_proximity_score == d("100.000000")
    assert passed.settlement_lag_score == d("100.000000")
    assert passed.exit_capacity_score == d("94.666667")
    assert passed.exit_capacity_status == "pass"
    assert passed.capacity_decision == "paper_candidate"
    assert passed.reason_codes == (
        "candidate_exit_capacity_input",
        "strategy_candidate_liquidity_exit_capacity_score_v2",
        "exit_capacity_pass",
        "depth_capacity_sufficient",
        "spread_inside_limit",
        "urgency_pressure_applied",
        "close_proximity_clear",
        "settlement_lag_clear",
        "score_pass",
    )
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    assert watched.required_exit_capacity_notional == d("166.666675")
    assert watched.exit_depth_to_required_capacity_ratio == d("1.140000")
    assert watched.close_proximity_pressure_ratio == d("0.500000")
    assert watched.settlement_lag_pressure_ratio == d("0.666667")
    assert watched.depth_capacity_score == d("91.200000")
    assert watched.spread_score == d("33.333333")
    assert watched.exit_capacity_score == d("68.493333")
    assert watched.exit_capacity_status == "watch"
    assert watched.capacity_decision == "manual_review"
    assert watched.reason_codes == (
        "candidate_exit_capacity_input",
        "strategy_candidate_liquidity_exit_capacity_score_v2",
        "exit_capacity_watch",
        "depth_capacity_below_watch",
        "spread_watch",
        "urgency_pressure_applied",
        "close_proximity_watch",
        "settlement_lag_watch",
        "score_below_pass",
    )

    assert blocked.required_exit_capacity_notional == d("223.958350")
    assert blocked.exit_depth_to_required_capacity_ratio == d("0.267907")
    assert blocked.capacity_shortfall_notional == d("163.958350")
    assert blocked.depth_capacity_score == d("21.432560")
    assert blocked.spread_score == ZERO
    assert blocked.close_proximity_score == d("2.083300")
    assert blocked.settlement_lag_score == ZERO
    assert blocked.exit_capacity_score == d("11.996238")
    assert blocked.exit_capacity_status == "blocked"
    assert blocked.capacity_decision == "reject"
    assert blocked.reason_codes == (
        "candidate_exit_capacity_input",
        "strategy_candidate_liquidity_exit_capacity_score_v2",
        "exit_capacity_blocked",
        "depth_capacity_below_block",
        "spread_block",
        "urgency_pressure_applied",
        "close_proximity_block",
        "settlement_lag_block",
        "capacity_shortfall",
        "score_below_block",
    )


def test_payload_serializes_decimal_strings_utc_datetimes_and_revalidates_digest() -> None:
    module = api()
    result = score(
        candidate_input(
            observed_at=datetime(2026, 7, 7, 7, 0, tzinfo=timezone(timedelta(hours=-7))),
        ),
    )

    payload = result.payload
    assert payload == module.strategy_candidate_liquidity_exit_capacity_score_v2_payload(
        result,
    )
    assert payload["observed_at"] == "2026-07-07T14:00:00+00:00"
    assert payload["expected_position_notional"] == "100.000000"
    assert payload["required_exit_capacity_notional"] == "110.000000"
    assert payload["exit_capacity_score"] == "94.666667"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert len(result.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in result.derived_validation_digest)
    assert result.derived_validation_digest == score().derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_liquidity_exit_capacity_score_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    subject = candidate_input()
    result = score(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.StrategyCandidateLiquidityExitCapacityScoreV2Config.__dataclass_params__.frozen
    assert module.StrategyCandidateLiquidityExitCapacityScoreV2Input.__dataclass_params__.frozen
    assert module.StrategyCandidateLiquidityExitCapacityScoreV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.market_slug = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.exit_capacity_status = "watch"  # type: ignore[misc]

    for instance in (cfg, subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="expected_position_notional must be a Decimal"):
        candidate_input(expected_position_notional=100)
    with pytest.raises(ValueError, match="book_depth_notional must be a Decimal"):
        candidate_input(book_depth_notional=DecimalSubclass("100.000000"))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        candidate_input(observed_at=DatetimeSubclass(2026, 7, 7, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        candidate_input(observed_at=datetime(2026, 7, 7, 14, 0))
    with pytest.raises(ValueError, match="urgency_ratio must be <= 1"):
        candidate_input(urgency_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        candidate_input(reason_codes=("candidate_exit_capacity_input",) * 2)
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(cfg, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="input"):
        score(object())

    rebuilt = module.StrategyCandidateLiquidityExitCapacityScoreV2Result(
        **field_values(result),
    )
    assert rebuilt == result


def test_config_and_result_consistency_validation_rejects_tampering() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="block_min_exit_depth"):
        config(
            watch_min_exit_depth_to_required_capacity_ratio=d("1.000000"),
            block_min_exit_depth_to_required_capacity_ratio=d("1.500000"),
        )
    with pytest.raises(ValueError, match="watch_max_spread_ratio"):
        config(watch_max_spread_ratio=d("0.070000"))
    with pytest.raises(ValueError, match="block_min_seconds_until_market_close"):
        config(block_min_seconds_until_market_close=d("259200.000000"))
    with pytest.raises(ValueError, match="watch_max_settlement_lag_seconds"):
        config(watch_max_settlement_lag_seconds=d("345600.000000"))
    with pytest.raises(ValueError, match="blocked_max_score"):
        config(blocked_max_score=d("80.000000"))

    with pytest.raises(ValueError, match="required_exit_capacity_notional"):
        replace(result, required_exit_capacity_notional=d("111.000000"))
    with pytest.raises(ValueError, match="exit_capacity_status"):
        replace(result, exit_capacity_status="watch")
    with pytest.raises(ValueError, match="capacity_decision"):
        replace(result, capacity_decision="reject")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateLiquidityExitCapacityScoreV2Result(
            **{
                **field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )


def test_rejects_unsafe_public_payload_terms() -> None:
    module = api()
    unsafe_terms = (
        "live",
        "auth",
        "wallet",
        "order",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    )
    for term in unsafe_terms:
        with pytest.raises(ValueError, match="unsafe"):
            candidate_input(reason_codes=(f"{term}_surface",))
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_liquidity_exit_capacity_score_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_liquidity_exit_capacity_score_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_scope_has_no_io_float_or_live_runtime_surface() -> None:
    module = api()
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "supabase",
        "private_key",
        "submit_order",
        "cancel_order",
        "place_order",
        "create_order",
        "open(",
        "Path(",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source

    for term in (
        "live",
        "auth",
        "wallet",
        "network",
        "database",
        "persist",
        "signing",
        "mutation",
        "buy",
        "sell",
        "trade",
    ):
        assert term not in lowered

    tree = ast.parse(source)
    imported_modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"float", "open"}

    assert set(imported_modules) <= {
        "__future__",
        "dataclasses",
        "datetime",
        "decimal",
        "hashlib",
        "typing",
    }
    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_LIQUIDITY_EXIT_CAPACITY_SCORE_V2_CONFIG_VERSION",
        "EXIT_CAPACITY_STATUSES",
        "CAPACITY_DECISIONS",
        "StrategyCandidateLiquidityExitCapacityScoreV2Config",
        "StrategyCandidateLiquidityExitCapacityScoreV2Input",
        "StrategyCandidateLiquidityExitCapacityScoreV2Result",
        "score_strategy_candidate_liquidity_exit_capacity_v2",
        "strategy_candidate_liquidity_exit_capacity_score_v2_payload",
        "reject_strategy_candidate_liquidity_exit_capacity_score_v2_unsafe_payload",
    )
