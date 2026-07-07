from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.strategy_candidate_resolution_confidence_edge_buffer_v2"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_resolution_confidence_edge_buffer_v2.py"
)
OBSERVED_AT = datetime(2026, 7, 7, 13, 0, tzinfo=UTC)
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
            module.DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_CONFIDENCE_EDGE_BUFFER_V2_CONFIG_VERSION
        ),
        "pass_min_edge_buffer": d("0.020000"),
        "watch_min_edge_buffer": d("0.000000"),
        "watch_min_resolution_confidence_score": d("0.750000"),
        "block_min_resolution_confidence_score": d("0.500000"),
        "watch_min_source_hierarchy_score": d("0.750000"),
        "block_min_source_hierarchy_score": d("0.500000"),
        "watch_max_contradiction_severity": d("0.300000"),
        "block_max_contradiction_severity": d("0.700000"),
        "watch_max_settlement_lag_seconds": d("86400.000000"),
        "block_max_settlement_lag_seconds": d("259200.000000"),
        "watch_max_liquidity_exit_risk": d("0.300000"),
        "block_max_liquidity_exit_risk": d("0.700000"),
        "resolution_confidence_buffer_weight": d("0.050000"),
        "source_hierarchy_buffer_weight": d("0.030000"),
        "contradiction_buffer_weight": d("0.040000"),
        "settlement_lag_buffer_weight": d("0.020000"),
        "liquidity_exit_risk_buffer_weight": d("0.050000"),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionConfidenceEdgeBufferV2Config(**values)


def candidate_input(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "candidate_id": "candidate_resolution_edge_buffer_alpha",
        "market_slug": "market_resolution_edge_buffer",
        "observed_at": OBSERVED_AT,
        "candidate_edge": d("0.150000"),
        "resolution_confidence_score": d("0.900000"),
        "source_hierarchy_score": d("0.850000"),
        "contradiction_severity": d("0.100000"),
        "settlement_lag_seconds": d("43200.000000"),
        "taker_edge_cost": d("0.006000"),
        "spread_edge_cost": d("0.010000"),
        "slippage_edge_cost": d("0.004000"),
        "liquidity_exit_risk": d("0.100000"),
        "reason_codes": ("candidate_edge_input",),
    }
    values.update(overrides)
    return module.StrategyCandidateResolutionConfidenceEdgeBufferV2Input(**values)


def score(subject: object | None = None, cfg: object | None = None) -> Any:
    module = api()
    return module.score_strategy_candidate_resolution_confidence_edge_buffer_v2(
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


def test_scores_pass_watch_and_blocked_resolution_confidence_edge_buffer() -> None:
    passed = score()
    watched = score(
        candidate_input(
            candidate_id="candidate_resolution_edge_buffer_watch",
            candidate_edge=d("0.055000"),
        ),
    )
    blocked = score(
        candidate_input(
            candidate_id="candidate_resolution_edge_buffer_blocked",
            market_slug="market_resolution_edge_buffer_blocked",
            candidate_edge=d("0.080000"),
            resolution_confidence_score=d("0.620000"),
            source_hierarchy_score=d("0.600000"),
            contradiction_severity=d("0.800000"),
            settlement_lag_seconds=d("345600.000000"),
            taker_edge_cost=d("0.020000"),
            spread_edge_cost=d("0.015000"),
            slippage_edge_cost=d("0.010000"),
            liquidity_exit_risk=d("0.800000"),
        ),
    )

    assert is_dataclass(passed)
    assert passed.resolution_confidence_buffer == d("0.005000")
    assert passed.source_hierarchy_buffer == d("0.004500")
    assert passed.contradiction_buffer == d("0.004000")
    assert passed.settlement_lag_pressure_ratio == d("0.166667")
    assert passed.settlement_lag_buffer == d("0.003333")
    assert passed.liquidity_exit_buffer == d("0.005000")
    assert passed.total_risk_buffer == d("0.021833")
    assert passed.total_cost_buffer == d("0.020000")
    assert passed.required_edge_buffer == d("0.041833")
    assert passed.edge_buffer == d("0.108167")
    assert passed.edge_buffer_shortfall == ZERO
    assert passed.edge_buffer_score == d("100.000000")
    assert passed.edge_buffer_status == "pass"
    assert passed.candidate_decision == "paper_candidate"
    assert passed.reason_codes == (
        "candidate_edge_input",
        "strategy_candidate_resolution_confidence_edge_buffer_v2",
        "edge_buffer_pass",
        "resolution_confidence_clear",
        "source_hierarchy_clear",
        "contradiction_clear",
        "settlement_lag_clear",
        "cost_stack_applied",
        "liquidity_exit_clear",
        "edge_buffer_cleared",
    )
    assert passed.paper_only is True
    assert passed.report_only is True
    assert passed.readonly is True

    assert watched.edge_buffer == d("0.013167")
    assert watched.edge_buffer_score == d("65.835000")
    assert watched.edge_buffer_status == "watch"
    assert watched.candidate_decision == "manual_review"
    assert "edge_buffer_below_pass" in watched.reason_codes

    assert blocked.resolution_confidence_buffer == d("0.019000")
    assert blocked.source_hierarchy_buffer == d("0.012000")
    assert blocked.contradiction_buffer == d("0.032000")
    assert blocked.settlement_lag_pressure_ratio == d("1.000000")
    assert blocked.liquidity_exit_buffer == d("0.040000")
    assert blocked.total_risk_buffer == d("0.123000")
    assert blocked.total_cost_buffer == d("0.045000")
    assert blocked.required_edge_buffer == d("0.168000")
    assert blocked.edge_buffer == d("-0.088000")
    assert blocked.edge_buffer_shortfall == d("0.088000")
    assert blocked.edge_buffer_score == ZERO
    assert blocked.edge_buffer_status == "blocked"
    assert blocked.candidate_decision == "reject"
    assert "contradiction_block" in blocked.reason_codes
    assert "settlement_lag_block" in blocked.reason_codes
    assert "liquidity_exit_block" in blocked.reason_codes
    assert "edge_buffer_negative" in blocked.reason_codes


def test_payload_serializes_decimal_strings_utc_datetimes_and_revalidates_digest() -> None:
    module = api()
    result = score(
        candidate_input(
            observed_at=datetime(2026, 7, 7, 6, 0, tzinfo=timezone(timedelta(hours=-7))),
        ),
    )

    payload = result.payload
    assert payload == module.strategy_candidate_resolution_confidence_edge_buffer_v2_payload(
        result,
    )
    assert payload["observed_at"] == "2026-07-07T13:00:00+00:00"
    assert payload["candidate_edge"] == "0.150000"
    assert payload["required_edge_buffer"] == "0.041833"
    assert payload["edge_buffer"] == "0.108167"
    assert payload["reason_codes"] == list(result.reason_codes)
    assert payload["derived_validation_digest"] == result.derived_validation_digest
    assert len(result.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in result.derived_validation_digest)
    assert result.derived_validation_digest == score().derived_validation_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "Decimal" not in json.dumps(payload, allow_nan=False, sort_keys=True)
    assert_no_float_values(payload)

    object.__setattr__(result, "derived_validation_digest", "0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.strategy_candidate_resolution_confidence_edge_buffer_v2_payload(result)


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    cfg = config()
    subject = candidate_input()
    result = score(subject, cfg)

    assert is_dataclass(cfg)
    assert is_dataclass(subject)
    assert is_dataclass(result)
    assert module.StrategyCandidateResolutionConfidenceEdgeBufferV2Config.__dataclass_params__.frozen
    assert module.StrategyCandidateResolutionConfidenceEdgeBufferV2Input.__dataclass_params__.frozen
    assert module.StrategyCandidateResolutionConfidenceEdgeBufferV2Result.__dataclass_params__.frozen

    with pytest.raises(FrozenInstanceError):
        subject.market_slug = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.edge_buffer_status = "watch"  # type: ignore[misc]

    for instance in (cfg, subject, result):
        for field in fields(instance):
            value = getattr(instance, field.name)
            if type(value) is bool or field.name == "derived_validation_digest":
                continue
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not float
            assert type(value) is not int

    with pytest.raises(ValueError, match="candidate_edge must be exactly Decimal"):
        candidate_input(candidate_edge=100)
    with pytest.raises(ValueError, match="resolution_confidence_score must be exactly Decimal"):
        candidate_input(resolution_confidence_score=DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        candidate_input(observed_at=DatetimeSubclass(2026, 7, 7, 13, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        candidate_input(observed_at=datetime(2026, 7, 7, 13, 0))
    with pytest.raises(ValueError, match="liquidity_exit_risk must be <= 1.000000"):
        candidate_input(liquidity_exit_risk=d("1.000001"))
    with pytest.raises(ValueError, match="reason_codes must be unique"):
        candidate_input(reason_codes=("candidate_edge_input",) * 2)
    with pytest.raises(ValueError, match="paper_only must be True"):
        candidate_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(cfg, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="input"):
        score(object())

    rebuilt = module.StrategyCandidateResolutionConfidenceEdgeBufferV2Result(
        **field_values(result),
    )
    assert rebuilt == result


def test_config_and_result_consistency_validation_rejects_tampering() -> None:
    module = api()
    result = score()

    with pytest.raises(ValueError, match="watch_min_edge_buffer"):
        config(pass_min_edge_buffer=d("0.010000"), watch_min_edge_buffer=d("0.020000"))
    with pytest.raises(ValueError, match="block_min_resolution_confidence_score"):
        config(block_min_resolution_confidence_score=d("0.800000"))
    with pytest.raises(ValueError, match="watch_max_contradiction_severity"):
        config(watch_max_contradiction_severity=d("0.800000"))
    with pytest.raises(ValueError, match="watch_max_settlement_lag_seconds"):
        config(watch_max_settlement_lag_seconds=d("345600.000000"))
    with pytest.raises(ValueError, match="watch_max_liquidity_exit_risk"):
        config(watch_max_liquidity_exit_risk=d("0.800000"))

    with pytest.raises(ValueError, match="required_edge_buffer"):
        replace(result, required_edge_buffer=d("0.042000"))
    with pytest.raises(ValueError, match="edge_buffer_status"):
        replace(result, edge_buffer_status="watch")
    with pytest.raises(ValueError, match="candidate_decision"):
        replace(result, candidate_decision="reject")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.StrategyCandidateResolutionConfidenceEdgeBufferV2Result(
            **{
                **field_values(result),
                "derived_validation_digest": "0" * 64,
            },
        )


def test_rejects_unsafe_public_keys_and_values() -> None:
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
            module.reject_strategy_candidate_resolution_confidence_edge_buffer_v2_unsafe_payload(
                "unsafe-test",
                {f"{term}_field": "paper_report"},
            )
        with pytest.raises(ValueError, match="unsafe"):
            module.reject_strategy_candidate_resolution_confidence_edge_buffer_v2_unsafe_payload(
                "unsafe-test",
                {"safe_field": f"{term}_value"},
            )


def test_module_scope_has_no_io_float_or_forbidden_runtime_surface() -> None:
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
        "json",
        "typing",
    }
    assert module.__all__ == (
        "DEFAULT_STRATEGY_CANDIDATE_RESOLUTION_CONFIDENCE_EDGE_BUFFER_V2_CONFIG_VERSION",
        "EDGE_BUFFER_STATUSES",
        "EDGE_BUFFER_DECISIONS",
        "StrategyCandidateResolutionConfidenceEdgeBufferV2Config",
        "StrategyCandidateResolutionConfidenceEdgeBufferV2Input",
        "StrategyCandidateResolutionConfidenceEdgeBufferV2Result",
        "score_strategy_candidate_resolution_confidence_edge_buffer_v2",
        "strategy_candidate_resolution_confidence_edge_buffer_v2_payload",
        "reject_strategy_candidate_resolution_confidence_edge_buffer_v2_unsafe_payload",
    )
